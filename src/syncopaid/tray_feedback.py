"""
System tray visual feedback for user actions.

Handles left-click time marker recording with visual feedback
(brief icon color change to orange) and audio feedback (mechanical click sound).
"""

import logging
import threading
from pathlib import Path
from typing import Callable, Optional

try:
    import pystray
    from syncopaid.tray_icons import create_icon_image, get_resource_path
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    get_resource_path = None

# Check for winsound (Windows built-in, no external dependencies)
try:
    import winsound
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False
    logging.debug("winsound not available (not on Windows)")


class TrayFeedbackHandler:
    """
    Handles visual feedback for tray icon interactions.

    Provides:
    - Icon flash animation (brief color change to orange)
    - Audio feedback (mechanical click sound)
    - Feedback state management (prevent overlapping animations)
    """

    def __init__(self):
        """Initialize feedback handler."""
        self.icon: Optional[pystray.Icon] = None
        self._feedback_in_progress = False  # Prevent overlapping feedback
        self.on_time_marker: Optional[Callable] = None

    def _get_current_state(self) -> str:
        """Override in parent class to get actual state."""
        return "on"

    def _play_click_sound(self):
        """
        Play the mechanical click sound asynchronously.

        Uses winsound.SND_ASYNC for non-blocking playback.
        """
        if not SOUND_AVAILABLE:
            return

        if not get_resource_path:
            return

        click_sound_path = get_resource_path("assets/mechanical-click.wav")
        if not click_sound_path.exists():
            logging.warning(f"Click sound file not found: {click_sound_path}")
            return

        try:
            # SND_ASYNC plays sound asynchronously (non-blocking)
            # SND_FILENAME specifies the parameter is a filename
            winsound.PlaySound(
                str(click_sound_path),
                winsound.SND_FILENAME | winsound.SND_ASYNC
            )
        except Exception as e:
            logging.debug(f"Error playing click sound: {e}")

    def record_time_marker(self, icon=None, item=None):
        """
        Handle left-click: record a time marker with visual/audio feedback.

        This records a task transition/interruption timestamp and provides
        brief visual feedback (icon briefly turns orange) and audio feedback
        (mechanical click sound).
        """
        if not TRAY_AVAILABLE:
            return

        # Prevent overlapping feedback animations
        if self._feedback_in_progress:
            return

        self._feedback_in_progress = True
        logging.info("User recorded time marker via left-click")

        try:
            # Play click sound (non-blocking)
            self._play_click_sound()

            # Call the time marker callback to record in database
            if self.on_time_marker:
                self.on_time_marker()

            # Show visual feedback: briefly flash orange icon
            if self.icon:
                # Save current state to restore later
                original_state = self._get_current_state()

                # Show orange icon as feedback (no notification)
                self.icon.icon = create_icon_image("feedback")

                # Schedule icon reset after 1 second
                def reset_icon():
                    try:
                        if self.icon:
                            self.icon.icon = create_icon_image(original_state)
                    except Exception as e:
                        logging.debug(f"Error resetting icon: {e}")
                    finally:
                        self._feedback_in_progress = False

                timer = threading.Timer(1.0, reset_icon)
                timer.daemon = True
                timer.start()
            else:
                self._feedback_in_progress = False

        except Exception as e:
            logging.error(f"Error recording time marker: {e}", exc_info=True)
            self._feedback_in_progress = False
