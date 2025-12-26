"""
SyncoPaid - Tracking control methods.

Contains methods for starting, pausing, and managing the tracking loop.
"""

import logging
import threading


def start_tracking(app):
    """
    Start the tracking loop in a background thread.

    Args:
        app: SyncoPaidApp instance with tracker, action_screenshot_worker, etc.
    """
    if app.is_tracking:
        logging.warning("Tracking already running")
        return

    app.is_tracking = True
    app.tracking_thread = threading.Thread(
        target=lambda: _run_tracking_loop(app),
        daemon=True
    )
    app.tracking_thread.start()

    # Start action screenshot worker
    if app.action_screenshot_worker:
        app.action_screenshot_worker.start()

    # Start click recorder
    if app.click_recorder:
        app.click_recorder.start()

    logging.info("Tracking started")
    print("[OK] Tracking started")


def pause_tracking(app):
    """
    Pause the tracking loop.

    Args:
        app: SyncoPaidApp instance with tracker, action_screenshot_worker, etc.
    """
    if not app.is_tracking:
        logging.warning("Tracking not running")
        return

    app.is_tracking = False
    app.tracker.stop()

    # Stop action screenshot worker
    if app.action_screenshot_worker:
        app.action_screenshot_worker.stop()

    # Stop click recorder
    if app.click_recorder:
        app.click_recorder.stop()

    logging.info("Tracking paused")
    print("[PAUSED] Tracking paused")


def _run_tracking_loop(app):
    """
    Run the tracking loop and store events in database.

    This runs in a background thread and continuously captures
    activity events, storing them to the database.

    Args:
        app: SyncoPaidApp instance with tracker, matcher, database
    """
    logging.info("Tracking loop thread started")

    try:
        for event in app.tracker.start():
            # Categorize activity before insertion
            categorization = app.matcher.categorize_activity(
                app=event.app,
                title=event.title,
                url=event.url,
                path=None
            )

            # Store event in database with categorization
            event_id = app.database.insert_event(
                event,
                matter_id=categorization.matter_id,
                confidence=categorization.confidence,
                flagged_for_review=categorization.flagged_for_review
            )

            # Log to console (optional - can be disabled for production)
            if not event.is_idle:
                logging.debug(
                    f"Captured: {event.app} - {event.title[:40]} "
                    f"({event.duration_seconds:.1f}s)"
                )

    except Exception as e:
        logging.error(f"Error in tracking loop: {e}", exc_info=True)

    finally:
        logging.info("Tracking loop thread ended")
