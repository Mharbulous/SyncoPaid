"""
Test script for end_time migration.

This script creates test events with missing end_time values,
runs the migration, and verifies the results.
"""

import tempfile
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add src to path so we can import timelawg
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from timelawg.database import Database
from timelawg.tracker import ActivityEvent


def test_end_time_migration():
    """Test the migrate_missing_end_times method."""

    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test_migration.db"

        print(f"Testing migration with database: {test_db_path}\n")

        # Create database
        db = Database(str(test_db_path))

        # Create test events WITHOUT end_time (simulating old data)
        print("Creating test events without end_time...")

        test_timestamp = datetime(2025, 12, 11, 9, 0, 0)

        with db._get_connection() as conn:
            cursor = conn.cursor()

            # Insert events directly to bypass the normal insert logic
            # This simulates old events created before end_time was implemented
            cursor.execute("""
                INSERT INTO events (timestamp, duration_seconds, end_time, app, title, is_idle)
                VALUES (?, ?, NULL, ?, ?, ?)
            """, (
                test_timestamp.isoformat(),
                300.0,  # 5 minutes
                "WINWORD.EXE",
                "Document.docx - Word",
                0
            ))

            cursor.execute("""
                INSERT INTO events (timestamp, duration_seconds, end_time, app, title, is_idle)
                VALUES (?, ?, NULL, ?, ?, ?)
            """, (
                (test_timestamp + timedelta(minutes=5)).isoformat(),
                600.0,  # 10 minutes
                "chrome.exe",
                "Google Chrome",
                0
            ))

            cursor.execute("""
                INSERT INTO events (timestamp, duration_seconds, end_time, app, title, is_idle)
                VALUES (?, ?, NULL, ?, ?, ?)
            """, (
                (test_timestamp + timedelta(minutes=15)).isoformat(),
                None,  # No duration (should not be updated)
                "notepad.exe",
                "Notepad",
                0
            ))

        print("✓ Created 3 test events (2 with duration, 1 without)\n")

        # Verify events have NULL end_time
        print("Checking events before migration:")
        events = db.get_events()
        for event in events:
            print(f"  Event {event['id']}: end_time = {event['end_time']}")

        assert all(e['end_time'] is None for e in events), "All events should have NULL end_time"
        print("✓ All events have NULL end_time\n")

        # Run migration
        print("Running migration...")
        updated_count = db.migrate_missing_end_times()
        print(f"✓ Migration completed: {updated_count} events updated\n")

        # Verify results
        print("Checking events after migration:")
        events = db.get_events()

        events_with_end_time = 0
        for event in events:
            print(f"  Event {event['id']}:")
            print(f"    timestamp: {event['timestamp']}")
            print(f"    duration_seconds: {event['duration_seconds']}")
            print(f"    end_time: {event['end_time']}")

            if event['end_time'] is not None:
                events_with_end_time += 1

                # Verify end_time is correct
                start = datetime.fromisoformat(event['timestamp'])
                end = datetime.fromisoformat(event['end_time'])
                expected_duration = event['duration_seconds']
                actual_duration = (end - start).total_seconds()

                print(f"    Calculated duration: {actual_duration}s")
                assert abs(actual_duration - expected_duration) < 0.01, \
                    f"Duration mismatch: expected {expected_duration}, got {actual_duration}"
                print(f"    ✓ Duration matches")
            else:
                print(f"    (No end_time - expected for event without duration)")
            print()

        # Verify 2 events were updated (the ones with duration)
        assert updated_count == 2, f"Expected 2 updates, got {updated_count}"
        assert events_with_end_time == 2, f"Expected 2 events with end_time, got {events_with_end_time}"

        print("✓ All tests passed!")
        print("\nTest Summary:")
        print(f"  - Created 3 test events with NULL end_time")
        print(f"  - Migration updated {updated_count} events")
        print(f"  - {events_with_end_time} events now have end_time")
        print(f"  - 1 event without duration still has NULL end_time (expected)")

        # Test idempotency - run migration again
        print("\nTesting idempotency (running migration again)...")
        updated_count_2 = db.migrate_missing_end_times()
        print(f"✓ Second migration updated {updated_count_2} events (should be 0)")

        assert updated_count_2 == 0, "Second migration should not update any events"
        print("✓ Migration is idempotent!")


if __name__ == "__main__":
    test_end_time_migration()
