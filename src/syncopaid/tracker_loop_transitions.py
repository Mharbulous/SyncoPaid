"""
Transition detection and prompt handling for tracking loop.

Detects task transitions and optionally shows prompts to users.
"""

import time
import logging
import threading
from datetime import datetime, timezone


class TransitionHandler:
    """
    Handles transition detection and prompt display.

    Detects when users switch between tasks and can show prompts
    asking about the nature of the work being done.
    """

    # Minimum seconds between transition prompts
    PROMPT_COOLDOWN = 600  # 10 minutes

    # Don't show popup if user has been idle for this long
    IDLE_THRESHOLD_SECONDS = 60  # 1 minute

    def __init__(
        self,
        transition_detector=None,
        transition_callback=None,
        prompt_enabled: bool = True
    ):
        """
        Initialize the transition handler.

        Args:
            transition_detector: Optional TransitionDetector for detecting task switches
            transition_callback: Callback to record transitions in database
            prompt_enabled: Whether to show prompts at transitions
        """
        self.transition_detector = transition_detector
        self.transition_callback = transition_callback
        self.prompt_enabled = prompt_enabled
        self.prev_window_state = None
        self._last_prompt_time = 0  # Cooldown tracking

        # Deferred popup tracking
        self._deferred_popup = None  # (state, transition_type) if popup is waiting
        self._was_idle = False  # Track if user was idle in previous check

        if transition_detector:
            logging.info(f"TransitionHandler initialized with prompts {'enabled' if prompt_enabled else 'disabled'}")

    def check_for_transitions(self, state: dict, idle_seconds: float):
        """
        Check for transition points and optionally show prompt.

        Args:
            state: Current window state dict
            idle_seconds: Current idle time in seconds
        """
        # Check for user returning from idle - show deferred popup
        is_currently_idle = idle_seconds >= self.IDLE_THRESHOLD_SECONDS
        user_just_returned = self._was_idle and not is_currently_idle
        self._was_idle = is_currently_idle

        if user_just_returned and self._deferred_popup:
            deferred_state, deferred_type = self._deferred_popup
            self._deferred_popup = None
            logging.info(f"User returned from idle, showing deferred popup: {deferred_type}")
            self._try_show_popup(deferred_state, deferred_type)

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

        # Show prompt if enabled
        if self.prompt_enabled:
            self._try_show_popup(state, transition_type)

    def update_previous_state(self, state: dict):
        """
        Update the previous window state for next iteration.

        Args:
            state: Current window state dict
        """
        self.prev_window_state = state.copy()

    def _try_show_popup(self, state: dict, transition_type: str):
        """
        Try to show a popup, handling idle state and existing popups.

        If user is idle, defers the popup until they return.
        If a popup is already showing, the request is ignored.

        Args:
            state: Current window state dict
            transition_type: Type of transition detected
        """
        from syncopaid.prompt import is_popup_showing
        from syncopaid.tracker_windows_idle import get_idle_seconds

        # Check if popup is already showing
        if is_popup_showing():
            logging.debug("Popup already showing, skipping new popup")
            return

        # Check if user is currently idle
        idle_seconds = get_idle_seconds()
        if idle_seconds >= self.IDLE_THRESHOLD_SECONDS:
            # User is idle, defer the popup
            self._deferred_popup = (state.copy(), transition_type)
            logging.info(f"User is idle ({idle_seconds:.0f}s), deferring popup until return")
            return

        # User is active and no popup showing - show the popup
        self._show_prompt_async(state, transition_type)
        self._last_prompt_time = time.time()

    def _show_prompt_async(self, state: dict, transition_type: str):
        """
        Show transition prompt in background thread.

        Args:
            state: Current window state dict
            transition_type: Type of transition detected
        """
        def show_prompt():
            try:
                from syncopaid.prompt import TransitionPrompt
                prompt = TransitionPrompt()
                response = prompt.show(transition_type)

                # Handle auto-closed popups - re-queue for later
                if response == "auto_closed":
                    logging.info("Popup auto-closed due to inactivity, will show again on user return")
                    self._deferred_popup = (state.copy(), transition_type)
                    return

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
