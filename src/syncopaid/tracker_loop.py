"""
Main tracking loop implementation.

Provides TrackerLoop class that continuously monitors window activity,
detects idle periods, merges consecutive identical activities, and yields
events for storage.
"""

import time
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Generator

from syncopaid.tracker_state import (
    ActivityEvent,
    IdleResumptionEvent,
    STATE_ACTIVE,
    STATE_INACTIVE,
    STATE_OFF
)
from syncopaid.tracker_windows import (
    get_active_window,
    get_idle_seconds,
    is_screensaver_active,
    is_workstation_locked,
    WINDOWS_APIS_AVAILABLE
)
from syncopaid.tracker_screenshot import submit_screenshot


class TrackerLoop:
    """
    Main tracking loop that captures window activity and generates events.

    This class manages the core tracking logic:
    - Polls active window at configurable interval
    - Detects idle periods
    - Merges consecutive identical activities
    - Yields ActivityEvent objects for storage
    - Submits periodic screenshots (if enabled)

    Configuration:
        poll_interval: How often to check active window (seconds)
        idle_threshold: Seconds before marking as idle
        merge_threshold: Max gap to merge identical windows (seconds)
        screenshot_worker: Optional ScreenshotWorker for capturing screenshots
        screenshot_interval: Seconds between screenshot attempts
    """

    def __init__(
        self,
        poll_interval: float = 1.0,
        idle_threshold: float = 180.0,
        merge_threshold: float = 2.0,
        screenshot_worker=None,
        screenshot_interval: float = 10.0,
        minimum_idle_duration: float = 180.0,
        ui_automation_worker=None
    ):
        self.poll_interval = poll_interval
        self.idle_threshold = idle_threshold
        self.merge_threshold = merge_threshold
        self.screenshot_worker = screenshot_worker
        self.screenshot_interval = screenshot_interval
        self.minimum_idle_duration = minimum_idle_duration
        self.ui_automation_worker = ui_automation_worker

        # State tracking for event merging
        self.current_event: Optional[Dict] = None
        self.event_start_time: Optional[datetime] = None

        # Idle resumption tracking
        self.was_idle: bool = False
        self.last_idle_resumption_time: Optional[datetime] = None

        # Lock screen / screensaver tracking
        self._was_locked: bool = False

        # Screenshot timing
        self.last_screenshot_time: float = 0

        self.running = False

        # Statistics
        self.total_events = 0
        self.merged_events = 0

        logging.info(
            f"TrackerLoop initialized: "
            f"poll={poll_interval}s, idle_threshold={idle_threshold}s, "
            f"merge_threshold={merge_threshold}s, "
            f"minimum_idle_duration={minimum_idle_duration}s, "
            f"screenshot_enabled={screenshot_worker is not None}"
        )

    def start(self) -> Generator[ActivityEvent, None, None]:
        """
        Start the tracking loop.

        Yields:
            ActivityEvent objects when activities change or complete.

        This is a generator that runs indefinitely until stop() is called.
        Each yielded event is ready to be stored in the database.
        """
        self.running = True
        logging.info("Tracking started")

        while self.running:
            try:
                # Get current state
                window = get_active_window()
                idle_seconds = get_idle_seconds()
                is_idle = idle_seconds >= self.idle_threshold

                # Detect idle→active transition for resumption events
                if self.was_idle and not is_idle:
                    # User just resumed after idle period
                    if hasattr(self, '_peak_idle_seconds') and self._peak_idle_seconds >= self.minimum_idle_duration:
                        # Check if enough time passed since last resumption (prevent duplicates)
                        should_emit = True
                        if self.last_idle_resumption_time:
                            time_since_last = (datetime.now(timezone.utc) - self.last_idle_resumption_time).total_seconds()
                            # Only emit if at least 60 seconds passed since last resumption
                            # This prevents rapid fire events from flaky idle detection
                            if time_since_last < 60.0:
                                should_emit = False
                                logging.debug(f"Suppressing duplicate resumption event (last: {time_since_last:.1f}s ago)")

                        if should_emit:
                            idle_minutes = self._peak_idle_seconds / 60.0
                            resumption_event = IdleResumptionEvent(
                                resumption_timestamp=datetime.now(timezone.utc).isoformat(),
                                idle_duration=self._peak_idle_seconds
                            )
                            logging.info(f"User resumed after {idle_minutes:.1f} minutes idle")
                            self.last_idle_resumption_time = datetime.now(timezone.utc)
                            yield resumption_event

                        # Always reset peak after processing transition
                        self._peak_idle_seconds = 0.0

                # Track idle state for next iteration
                if is_idle and not self.was_idle:
                    # Just became idle - start tracking peak
                    self._peak_idle_seconds = idle_seconds
                    logging.debug(f"User went idle (idle_seconds={idle_seconds:.1f}s)")
                elif is_idle:
                    # Still idle - update peak
                    self._peak_idle_seconds = max(getattr(self, '_peak_idle_seconds', 0.0), idle_seconds)

                self.was_idle = is_idle

                # Detect lock screen / screensaver
                is_locked_or_screensaver = is_workstation_locked() or is_screensaver_active()

                # Log lock/screensaver transitions for debugging
                if is_locked_or_screensaver:
                    if not self._was_locked:
                        if is_workstation_locked():
                            logging.info("Workstation locked - switching to STATE_OFF")
                        else:
                            logging.info("Screensaver active - switching to STATE_OFF")
                        self._was_locked = True
                else:
                    if self._was_locked:
                        logging.info("Workstation unlocked/screensaver deactivated - resuming tracking")
                        self._was_locked = False

                # Create state dict for comparison
                state = {
                    'app': window['app'],
                    'title': window['title'],
                    'url': window.get('url'),  # Extracted context (URL, subject, or filepath)
                    'cmdline': window.get('cmdline'),  # Process command line arguments
                    'is_idle': is_idle,
                    'is_locked_or_screensaver': is_locked_or_screensaver,
                    'window_info': window  # For UI automation extraction
                }

                # Submit screenshot if enabled and interval elapsed
                # Note: We only check if screenshot_worker exists. The worker itself
                # handles platform-specific checks (WINDOWS_APIS_AVAILABLE) internally.
                if self.screenshot_worker:
                    current_time = time.time()
                    time_since_last = current_time - self.last_screenshot_time

                    # Log diagnostic info on first screenshot attempt
                    if not hasattr(self, '_screenshot_diagnostic_logged'):
                        logging.info(
                            f"Screenshot capture enabled: interval={self.screenshot_interval}s, "
                            f"tracker_apis_available={WINDOWS_APIS_AVAILABLE}"
                        )
                        self._screenshot_diagnostic_logged = True

                    if time_since_last >= self.screenshot_interval:
                        logging.debug(f"Triggering screenshot capture (elapsed: {time_since_last:.1f}s)")
                        submit_screenshot(self.screenshot_worker, window, idle_seconds)
                        self.last_screenshot_time = current_time

                # Check if state changed
                if self._has_state_changed(state):
                    # Yield the completed event (if any)
                    if self.current_event is not None:
                        completed_event = self._finalize_current_event()
                        if completed_event:
                            yield completed_event

                    # Start new event
                    self.current_event = state
                    self.event_start_time = datetime.now(timezone.utc)

                # Sleep until next poll
                time.sleep(self.poll_interval)

            except Exception as e:
                logging.error(f"Error in tracking loop: {e}")
                time.sleep(self.poll_interval)

        # Yield final event when stopped
        if self.current_event is not None:
            completed_event = self._finalize_current_event()
            if completed_event:
                yield completed_event

        logging.info(
            f"Tracking stopped. Total events: {self.total_events}, "
            f"Merged: {self.merged_events}"
        )

    def stop(self):
        """Stop the tracking loop."""
        self.running = False

    def _has_state_changed(self, new_state: Dict) -> bool:
        """
        Check if the current state is different from the tracked state.

        Considers the merge_threshold: if user briefly switches windows
        but returns within merge_threshold seconds, treat as continuous.
        """
        if self.current_event is None:
            return True

        # Check if core attributes changed
        if (new_state['app'] != self.current_event['app'] or
            new_state['title'] != self.current_event['title'] or
            new_state['is_idle'] != self.current_event['is_idle'] or
            new_state.get('is_locked_or_screensaver', False) != self.current_event.get('is_locked_or_screensaver', False)):

            # State changed - check if within merge threshold
            if self.event_start_time:
                elapsed = (datetime.now(timezone.utc) - self.event_start_time).total_seconds()
                if elapsed < self.merge_threshold:
                    # Too quick - might be accidental switch, merge it
                    self.merged_events += 1
                    return False

            return True

        return False

    def _finalize_current_event(self) -> Optional[ActivityEvent]:
        """
        Convert the current tracked event into an ActivityEvent object.

        Returns None if the event is too short or invalid.
        """
        if not self.current_event or not self.event_start_time:
            return None

        # Calculate duration and end time
        end_time = datetime.now(timezone.utc)
        duration = (end_time - self.event_start_time).total_seconds()

        # Skip events that are too short (< 0.5 seconds)
        if duration < 0.5:
            return None

        # Determine state: locked/screensaver > idle > active
        if self.current_event.get('is_locked_or_screensaver', False):
            event_state = STATE_OFF
        elif self.current_event.get('is_idle', False):
            event_state = STATE_INACTIVE
        else:
            event_state = STATE_ACTIVE

        # Extract metadata if UI automation worker is configured
        metadata = None
        if self.ui_automation_worker and 'window_info' in self.current_event:
            metadata = self.ui_automation_worker.extract(self.current_event['window_info'])

        # Create event with start time, duration, end time, and state
        event = ActivityEvent(
            timestamp=self.event_start_time.isoformat(),
            duration_seconds=round(duration, 2),
            app=self.current_event['app'],
            title=self.current_event['title'],
            end_time=end_time.isoformat(),
            url=self.current_event.get('url'),  # Extracted context (URL, subject, or filepath)
            cmdline=self.current_event.get('cmdline'),  # Process command line arguments
            is_idle=self.current_event['is_idle'],
            state=event_state,
            metadata=metadata
        )

        self.total_events += 1
        return event
