"""
SyncoPaid - Application initialization helpers.

Contains component initialization logic for the main application.
"""

import logging

from syncopaid.config import ConfigManager
from syncopaid.database import Database
from syncopaid.exporter import Exporter
from syncopaid.screenshot import ScreenshotWorker, get_screenshot_directory
from syncopaid.action_screenshot import ActionScreenshotWorker, get_action_screenshot_directory
from syncopaid.archiver import ArchiveWorker
from syncopaid.categorizer import ActivityMatcher
from syncopaid.tracker import TrackerLoop
from syncopaid.click_recorder import ClickRecorder


def initialize_screenshot_worker(config, database, resource_monitor=None):
    """
    Initialize screenshot worker if enabled in config.

    Args:
        config: Application configuration object
        database: Database instance for callbacks
        resource_monitor: Optional ResourceMonitor instance for throttling

    Returns:
        ScreenshotWorker instance or None if disabled
    """
    if not config.screenshot_enabled:
        return None

    screenshot_dir = get_screenshot_directory()
    worker = ScreenshotWorker(
        screenshot_dir=screenshot_dir,
        db_insert_callback=database.insert_screenshot,
        threshold_identical=config.screenshot_threshold_identical,
        threshold_significant=config.screenshot_threshold_significant,
        threshold_identical_same_window=config.screenshot_threshold_identical_same_window,
        threshold_identical_different_window=config.screenshot_threshold_identical_different_window,
        quality=config.screenshot_quality,
        max_dimension=config.screenshot_max_dimension,
        resource_monitor=resource_monitor
    )
    logging.info("Screenshot worker initialized")
    return worker


def initialize_action_screenshot_worker(config, database):
    """
    Initialize action screenshot worker if enabled in config.

    Args:
        config: Application configuration object
        database: Database instance for callbacks

    Returns:
        ActionScreenshotWorker instance or None if disabled
    """
    if not config.action_screenshot_enabled:
        return None

    action_screenshot_dir = get_action_screenshot_directory()
    worker = ActionScreenshotWorker(
        screenshot_dir=action_screenshot_dir,
        db_insert_callback=database.insert_screenshot,
        quality=config.action_screenshot_quality,
        max_dimension=config.action_screenshot_max_dimension,
        throttle_seconds=config.action_screenshot_throttle_seconds,
        enabled=True
    )
    logging.info("Action screenshot worker initialized")
    return worker


def initialize_archiver():
    """
    Initialize archiver worker for screenshot management.

    Returns:
        ArchiveWorker instance
    """
    screenshot_base_dir = get_screenshot_directory().parent
    archive_dir = screenshot_base_dir / "archives"
    archiver = ArchiveWorker(screenshot_base_dir, archive_dir)
    archiver.run_once()  # Run on startup
    archiver.start_background()  # Schedule monthly checks
    logging.info("Screenshot archiver initialized")
    return archiver


def initialize_transition_detector(config):
    """
    Initialize transition detector if enabled in config.

    Args:
        config: Application configuration object

    Returns:
        TransitionDetector instance or None if disabled
    """
    if not config.transition_prompt_enabled:
        return None

    from syncopaid.transition_detector import TransitionDetector
    detector = TransitionDetector()
    logging.info("Transition detector initialized")
    return detector


def initialize_activity_matcher(database, config):
    """
    Initialize activity matcher for categorization.

    Args:
        database: Database instance
        config: Application configuration object

    Returns:
        ActivityMatcher instance
    """
    matcher = ActivityMatcher(
        database,
        confidence_threshold=config.categorization_confidence_threshold
    )
    logging.info("Activity matcher initialized")
    return matcher


def initialize_tracker_loop(config, screenshot_worker, transition_detector, database, resource_monitor=None):
    """
    Initialize the tracker loop.

    Args:
        config: Application configuration object
        screenshot_worker: ScreenshotWorker instance or None
        transition_detector: TransitionDetector instance or None
        database: Database instance for callbacks
        resource_monitor: Optional ResourceMonitor instance for throttling

    Returns:
        TrackerLoop instance
    """
    tracker = TrackerLoop(
        poll_interval=config.poll_interval_seconds,
        idle_threshold=config.idle_threshold_seconds,
        merge_threshold=config.merge_threshold_seconds,
        screenshot_worker=screenshot_worker,
        screenshot_interval=config.screenshot_interval_seconds,
        minimum_idle_duration=config.minimum_idle_duration_seconds,
        transition_detector=transition_detector,
        transition_callback=database.insert_transition if transition_detector else None,
        prompt_enabled=config.transition_prompt_enabled,
        resource_monitor=resource_monitor
    )
    return tracker


def initialize_click_recorder(database):
    """
    Initialize the click recorder.

    Args:
        database: Database instance for storing click events

    Returns:
        ClickRecorder instance
    """
    def on_click_event(event):
        """Callback to store click events in the database."""
        database.insert_event(event)
        logging.debug(f"Click event stored: {event.timestamp}")

    recorder = ClickRecorder(
        event_callback=on_click_event,
        enabled=True
    )
    logging.info("Click recorder initialized")
    return recorder
