"""
Console test mode utilities for TrackerLoop.

Provides standalone testing functionality for the tracking system,
allowing quick verification of window tracking without the full application.
"""

import time
import logging

from syncopaid.tracker_windows import WINDOWS_APIS_AVAILABLE


def run_console_test(tracker_class, duration_seconds: int = 30):
    """
    Run tracker in console test mode for demonstration/debugging.

    Args:
        tracker_class: TrackerLoop class to instantiate
        duration_seconds: How long to run the test (default 30s)

    Returns:
        List of ActivityEvent objects captured during the test
    """
    print("=" * 70)
    print("SyncoPaid - Console Test Mode")
    print("=" * 70)
    print(f"Running for {duration_seconds} seconds...")
    print("Switch between windows to see tracking in action.\n")

    if not WINDOWS_APIS_AVAILABLE:
        print("⚠ Warning: Running with MOCK DATA (not on Windows)\n")

    tracker = tracker_class(
        poll_interval=1.0,
        idle_threshold=180.0,
        merge_threshold=2.0
    )

    events = []
    start_time = time.time()

    print(f"{'Timestamp':<20} {'Duration':<10} {'App':<20} {'Title':<40}")
    print("-" * 90)

    try:
        for event in tracker.start():
            # Store event
            events.append(event)

            # Display event
            ts = event.timestamp.split('T')[1][:8]  # Just show time
            status = "💤 IDLE" if event.is_idle else "✓"
            print(
                f"{ts:<20} "
                f"{event.duration_seconds:>6.1f}s   "
                f"{(event.app or 'unknown')[:18]:<20} "
                f"{(event.title or 'untitled')[:38]:<40}"
            )

            # Check if duration exceeded
            if time.time() - start_time >= duration_seconds:
                tracker.stop()
                break

    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        tracker.stop()

    # Summary
    print("\n" + "=" * 70)
    print(f"Test complete: {len(events)} events captured")
    print(f"Total active time: {sum(e.duration_seconds for e in events if not e.is_idle):.1f}s")
    print(f"Total idle time: {sum(e.duration_seconds for e in events if e.is_idle):.1f}s")
    print(f"Events merged: {tracker.merged_events}")
    print("=" * 70)

    return events
