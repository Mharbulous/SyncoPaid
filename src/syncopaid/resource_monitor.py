"""
Resource monitoring module for adaptive throttling.

Tracks CPU%, memory, battery, and thread count to enable
intelligent throttling when system resources are constrained.
"""

import logging
import os
import psutil

logger = logging.getLogger(__name__)


class ResourceMonitor:
    """
    Monitor system and process resources for adaptive throttling.

    Tracks:
    - Process CPU usage percentage
    - Process memory usage in MB
    - System battery percentage (if available)
    - Thread count

    Provides thresholds for triggering throttled behavior.
    """

    def __init__(
        self,
        cpu_threshold: float = 80.0,
        memory_threshold_mb: int = 200,
        battery_threshold: int = 20,
        monitoring_interval_seconds: float = 60.0
    ):
        """
        Initialize resource monitor.

        Args:
            cpu_threshold: CPU % above which to throttle (default: 80%)
            memory_threshold_mb: Memory MB above which to clear cache (default: 200)
            battery_threshold: Battery % below which to throttle (default: 20%)
            monitoring_interval_seconds: How often to check resources (default: 60s)
        """
        self.cpu_threshold = cpu_threshold
        self.memory_threshold_mb = memory_threshold_mb
        self.battery_threshold = battery_threshold
        self.monitoring_interval = monitoring_interval_seconds

        # Get current process for self-monitoring
        self._process = psutil.Process(os.getpid())

        # Initialize CPU monitoring (first call returns 0, need to prime it)
        try:
            self._process.cpu_percent()
        except Exception:
            pass

        logger.info(
            f"ResourceMonitor initialized: cpu_threshold={cpu_threshold}%, "
            f"memory_threshold={memory_threshold_mb}MB, battery_threshold={battery_threshold}%"
        )

        # Statistics tracking
        self._peak_cpu = 0.0
        self._peak_memory_mb = 0.0
        self._total_cpu = 0.0
        self._total_memory_mb = 0.0
        self._samples_count = 0

    def get_current_metrics(self) -> dict:
        """
        Get current resource metrics.

        Returns:
            dict with keys: cpu_percent, memory_mb, battery_percent, thread_count
        """
        metrics = {
            'cpu_percent': 0.0,
            'memory_mb': 0.0,
            'battery_percent': 100,  # Default to 100 if no battery
            'thread_count': 0
        }

        try:
            # Process CPU %
            metrics['cpu_percent'] = self._process.cpu_percent()

            # Process memory in MB
            memory_info = self._process.memory_info()
            metrics['memory_mb'] = memory_info.rss / (1024 * 1024)

            # Thread count
            metrics['thread_count'] = self._process.num_threads()

            # Battery (may not be available on desktops)
            battery = psutil.sensors_battery()
            if battery:
                metrics['battery_percent'] = battery.percent

        except Exception as e:
            logger.warning(f"Error getting resource metrics: {e}")

        return metrics

    def should_throttle_polling(self) -> bool:
        """
        Check if window polling should be throttled (slowed down).

        Throttle when system CPU > 80% to reduce impact on foreground apps.

        Returns:
            True if polling should be slowed from 1s to 5s
        """
        try:
            # Use system CPU, not just our process
            system_cpu = psutil.cpu_percent(interval=0)
            return system_cpu > self.cpu_threshold
        except Exception as e:
            logger.warning(f"Error checking CPU for throttling: {e}")
            return False

    def should_skip_screenshot(self) -> bool:
        """
        Check if screenshots should be skipped.

        Skip when:
        - System CPU > 90% (screenshots are resource-intensive)
        - Battery < 20% (save power)

        Returns:
            True if screenshots should be skipped
        """
        try:
            # Check system CPU (higher threshold than polling)
            system_cpu = psutil.cpu_percent(interval=0)
            if system_cpu > 90:
                logger.debug(f"Skipping screenshot: CPU at {system_cpu}%")
                return True

            # Check battery
            battery = psutil.sensors_battery()
            if battery and not battery.power_plugged and battery.percent < self.battery_threshold:
                logger.debug(f"Skipping screenshot: Battery at {battery.percent}%")
                return True

            return False
        except Exception as e:
            logger.warning(f"Error checking screenshot skip conditions: {e}")
            return False

    def should_clear_cache(self) -> bool:
        """
        Check if screenshot cache should be cleared.

        Clear when app memory usage exceeds threshold (default 200MB).

        Returns:
            True if cache should be cleared
        """
        try:
            memory_info = self._process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            return memory_mb > self.memory_threshold_mb
        except Exception as e:
            logger.warning(f"Error checking memory for cache clear: {e}")
            return False

    def record_metrics(self) -> dict:
        """
        Record current metrics for statistics tracking.

        Updates peak/average values. Should be called periodically
        (e.g., every 60 seconds).

        Returns:
            Current metrics dict
        """
        metrics = self.get_current_metrics()

        # Update peaks
        if metrics['cpu_percent'] > self._peak_cpu:
            self._peak_cpu = metrics['cpu_percent']
        if metrics['memory_mb'] > self._peak_memory_mb:
            self._peak_memory_mb = metrics['memory_mb']

        # Update totals for averaging
        self._total_cpu += metrics['cpu_percent']
        self._total_memory_mb += metrics['memory_mb']
        self._samples_count += 1

        logger.debug(
            f"Resource metrics: CPU={metrics['cpu_percent']:.1f}%, "
            f"Memory={metrics['memory_mb']:.1f}MB, "
            f"Battery={metrics['battery_percent']}%, "
            f"Threads={metrics['thread_count']}"
        )

        return metrics

    def get_statistics(self) -> dict:
        """
        Get resource usage statistics.

        Returns:
            dict with peak and average values
        """
        if self._samples_count == 0:
            return {
                'peak_cpu': 0.0,
                'peak_memory_mb': 0.0,
                'avg_cpu': 0.0,
                'avg_memory_mb': 0.0,
                'samples_count': 0
            }

        return {
            'peak_cpu': self._peak_cpu,
            'peak_memory_mb': self._peak_memory_mb,
            'avg_cpu': self._total_cpu / self._samples_count,
            'avg_memory_mb': self._total_memory_mb / self._samples_count,
            'samples_count': self._samples_count
        }

    def get_idle_poll_interval(self, idle_seconds: float, base_interval: float = 1.0) -> float:
        """
        Get poll interval adjusted for idle time.

        During extended idle (>10 minutes), reduce polling from 1s to 10s
        to save resources when user is away.

        Args:
            idle_seconds: Current idle time in seconds
            base_interval: Normal poll interval (default 1.0s)

        Returns:
            Adjusted poll interval in seconds
        """
        # Extended idle threshold: 10 minutes
        EXTENDED_IDLE_THRESHOLD = 600  # 10 * 60 seconds
        IDLE_POLL_INTERVAL = 10.0

        if idle_seconds > EXTENDED_IDLE_THRESHOLD:
            return IDLE_POLL_INTERVAL

        return base_interval
