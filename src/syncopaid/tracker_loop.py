"""
Main tracking loop implementation.

Provides TrackerLoop class that continuously monitors window activity,
detects idle periods, merges consecutive identical activities, and yields
events for storage.
"""

import time
import logging
from typing import Generator

from syncopaid.tracker_state import ActivityEvent
from syncopaid.tracker_windows import (
    get_active_window,
    get_idle_seconds,
    is_screensaver_active,
    is_workstation_locked
)
from syncopaid.tracker_loop_idle import IdleTracker
from syncopaid.tracker_loop_screenshots import ScreenshotScheduler
from syncopaid.tracker_loop_state import StateChangeDetector
from syncopaid.tracker_loop_events import EventFinalizer


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
        self.running = False

        # Delegate to specialized components
        self.idle_tracker = IdleTracker(minimum_idle_duration)
        self.screenshot_scheduler = ScreenshotScheduler(screenshot_worker, screenshot_interval) if screenshot_worker else None
        self.state_detector = StateChangeDetector(merge_threshold)
        self.event_finalizer = EventFinalizer(ui_automation_worker)

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

                # Handle idle state transitions
                resumption_event = self.idle_tracker.update_idle_state(is_idle, idle_seconds)
                if resumption_event:
                    yield resumption_event

                # Detect lock screen / screensaver
                is_locked_or_screensaver = is_workstation_locked() or is_screensaver_active()
                self.state_detector.log_lock_transitions(is_locked_or_screensaver)

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
                if self.screenshot_scheduler:
                    self.screenshot_scheduler.maybe_capture_screenshot(window, idle_seconds)

                # Check if state changed
                if self.state_detector.has_state_changed(state):
                    # Yield the completed event (if any)
                    completed_event = self.event_finalizer.finalize_event(
                        self.state_detector.current_event,
                        self.state_detector.event_start_time
                    )
                    if completed_event:
                        yield completed_event

                    # Start new event
                    self.state_detector.start_new_event(state)

                # Sleep until next poll
                time.sleep(self.poll_interval)

            except Exception as e:
                logging.error(f"Error in tracking loop: {e}")
                time.sleep(self.poll_interval)

        # Yield final event when stopped
        completed_event = self.event_finalizer.finalize_event(
            self.state_detector.current_event,
            self.state_detector.event_start_time
        )
        if completed_event:
            yield completed_event

        logging.info(
            f"Tracking stopped. Total events: {self.event_finalizer.total_events}, "
            f"Merged: {self.state_detector.merged_events}"
        )

    def stop(self):
        """Stop the tracking loop."""
        self.running = False
