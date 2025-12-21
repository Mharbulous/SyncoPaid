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
    - Detects transitions and triggers prompts (if enabled)

    Configuration:
        poll_interval: How often to check active window (seconds)
        idle_threshold: Seconds before marking as idle
        merge_threshold: Max gap to merge identical windows (seconds)
        screenshot_worker: Optional ScreenshotWorker for capturing screenshots
        screenshot_interval: Seconds between screenshot attempts
        transition_detector: Optional TransitionDetector for detecting task switches
        transition_callback: Callback to record transitions in database
        prompt_enabled: Whether to show prompts at transitions
    """

    # Minimum seconds between transition prompts
    PROMPT_COOLDOWN = 600  # 10 minutes

    def __init__(
        self,
        poll_interval: float = 1.0,
        idle_threshold: float = 180.0,
        merge_threshold: float = 2.0,
        screenshot_worker=None,
        screenshot_interval: float = 10.0,
        minimum_idle_duration: float = 180.0,
        ui_automation_worker=None,
        transition_detector=None,
        transition_callback=None,
        prompt_enabled: bool = True,
        interaction_threshold: float = 5.0
    ):
        self.poll_interval = poll_interval
        self.idle_threshold = idle_threshold
        self.interaction_threshold = interaction_threshold
        self.running = False

        # Delegate to specialized components
        self.idle_tracker = IdleTracker(minimum_idle_duration)
        self.screenshot_scheduler = ScreenshotScheduler(screenshot_worker, screenshot_interval) if screenshot_worker else None
        self.state_detector = StateChangeDetector(merge_threshold)
        self.event_finalizer = EventFinalizer(ui_automation_worker)

        # Interaction level tracking
        self.last_typing_time = None
        self.last_click_time = None

        # Transition detection
        self.transition_detector = transition_detector
        self.transition_callback = transition_callback
        self.prompt_enabled = prompt_enabled
        self.prev_window_state = None
        self._last_prompt_time = 0  # Cooldown tracking

        logging.info(
            f"TrackerLoop initialized: "
            f"poll={poll_interval}s, idle_threshold={idle_threshold}s, "
            f"merge_threshold={merge_threshold}s, "
            f"minimum_idle_duration={minimum_idle_duration}s, "
            f"screenshot_enabled={screenshot_worker is not None}, "
            f"transition_detection={transition_detector is not None}"
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

                # Check for transitions (if enabled)
                self._check_for_transitions(state, idle_seconds)

                # Update previous state for next iteration
                self.prev_window_state = state.copy()

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

    def _check_for_transitions(self, state: dict, idle_seconds: float):
        """
        Check for transition points and optionally show prompt.

        Args:
            state: Current window state dict
            idle_seconds: Current idle time in seconds
        """
        if not self.transition_detector:
            return

        # Get previous state info
        prev_app = self.prev_window_state['app'] if self.prev_window_state else None
        prev_title = self.prev_window_state['title'] if self.prev_window_state else None

        # Check if this is a transition
        is_trans = self.transition_detector.is_transition(
            app=state['app'],
            title=state['title'],
            prev_app=prev_app,
            prev_title=prev_title,
            idle_seconds=idle_seconds
        )

        if not is_trans:
            return

        transition_type = self.transition_detector.last_transition_type
        logging.info(f"Transition detected: {transition_type}")

        # Record transition in database
        if self.transition_callback:
            from datetime import datetime, timezone
            self.transition_callback(
                timestamp=datetime.now(timezone.utc).isoformat(),
                transition_type=transition_type,
                context={"app": state['app'], "title": state['title']},
                user_response=None
            )

        # Check cooldown before showing prompt
        current_time = time.time()
        if current_time - self._last_prompt_time < self.PROMPT_COOLDOWN:
            logging.debug(f"Skipping prompt due to cooldown")
            return

        # Show prompt if enabled (in background thread)
        if self.prompt_enabled:
            self._show_prompt_async(state, transition_type)
            self._last_prompt_time = current_time

    def _show_prompt_async(self, state: dict, transition_type: str):
        """
        Show transition prompt in background thread.

        Args:
            state: Current window state dict
            transition_type: Type of transition detected
        """
        import threading
        from datetime import datetime, timezone

        def show_prompt():
            try:
                from syncopaid.prompt import TransitionPrompt
                prompt = TransitionPrompt()
                response = prompt.show(transition_type)

                # Update transition record with user response
                if response and self.transition_callback:
                    self.transition_callback(
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        transition_type=transition_type,
                        context={"app": state['app'], "title": state['title']},
                        user_response=response
                    )
                    logging.info(f"User response to transition prompt: {response}")

            except Exception as e:
                logging.error(f"Error showing transition prompt: {e}")

        threading.Thread(target=show_prompt, daemon=True).start()
