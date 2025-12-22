"""
SyncoPaid - Display and UI methods.

Contains methods for showing dialogs, statistics, and other UI elements.
"""

from syncopaid.config import print_config
from syncopaid.database import format_duration
from syncopaid.main_ui_windows import show_main_window
from syncopaid.main_ui_export_dialog import show_export_dialog


def show_export_dialog_wrapper(app):
    """
    Show dialog for exporting data.

    Args:
        app: SyncoPaidApp instance with exporter and database
    """
    show_export_dialog(app.exporter, app.database)


def show_main_window_wrapper(app):
    """
    Show main application window displaying activity from the past 24 hours.

    Args:
        app: SyncoPaidApp instance with database, tray, quit_app
    """
    show_main_window(app.database, app.tray, app.quit_app)


def show_settings_dialog(app):
    """
    Show settings dialog.

    Args:
        app: SyncoPaidApp instance with config and config_manager
    """
    # For MVP, just print current settings to console
    # Can be enhanced with a proper GUI later
    print("\n" + "="*60)
    print_config(app.config)
    print("\nTo modify settings, edit:")
    print(f"  {app.config_manager.config_path}")
    print("="*60 + "\n")


def show_statistics(app):
    """
    Display database statistics.

    Args:
        app: SyncoPaidApp instance with database
    """
    stats = app.database.get_statistics()

    print("\n" + "="*60)
    print("SyncoPaid Statistics")
    print("="*60)
    print(f"Total events captured: {stats['total_events']}")
    print(f"Active time: {format_duration(stats['active_duration_seconds'])}")
    print(f"Idle time: {format_duration(stats['idle_duration_seconds'])}")

    if stats['first_event']:
        print(f"First event: {stats['first_event'][:19]}")
        print(f"Last event: {stats['last_event'][:19]}")
        print(f"Days tracked: {stats['date_range_days']}")

    print("="*60 + "\n")
