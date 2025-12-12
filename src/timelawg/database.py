"""
Database module for persistent storage of activity events.

Uses SQLite to store events locally with the following schema:
- events table with timestamp, duration, app, title, url, is_idle
- Indices on timestamp and app for efficient querying

All operations are local-only (no network access) to preserve
attorney-client privilege.
"""

import sqlite3
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date, timedelta
from pathlib import Path
from contextlib import contextmanager

from .tracker import ActivityEvent


class Database:
    """
    SQLite database manager for activity events.
    
    Provides methods for:
    - Initializing database schema
    - Inserting captured events
    - Querying events by date range
    - Deleting events by date range
    - Database statistics
    """
    
    def __init__(self, db_path: str):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file. Parent directory will
                    be created if it doesn't exist.
        """
        self.db_path = Path(db_path)
        
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize schema
        self._init_schema()
        
        logging.info(f"Database initialized: {self.db_path}")
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logging.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _init_schema(self):
        """
        Create database schema if it doesn't exist.

        Schema includes:
        - events table with all activity fields
        - screenshots table with captured screenshots metadata
        - Indices on timestamp and app for query performance
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Create events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    duration_seconds REAL,
                    end_time TEXT,
                    app TEXT,
                    title TEXT,
                    url TEXT,
                    is_idle INTEGER DEFAULT 0
                )
            """)

            # Migration: Add end_time column if it doesn't exist (for existing databases)
            cursor.execute("PRAGMA table_info(events)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'end_time' not in columns:
                cursor.execute("ALTER TABLE events ADD COLUMN end_time TEXT")
                logging.info("Database migration: Added end_time column to events table")

            # Migration: Add state column if it doesn't exist
            if 'state' not in columns:
                cursor.execute("ALTER TABLE events ADD COLUMN state TEXT DEFAULT 'Active'")
                logging.info("Database migration: Added state column to events table")

                # Backfill existing data: set state based on is_idle
                cursor.execute("""
                    UPDATE events
                    SET state = CASE WHEN is_idle = 1 THEN 'Inactive' ELSE 'Active' END
                    WHERE state IS NULL
                """)
                logging.info("Database migration: Backfilled state column from is_idle")

            # Create indices for query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON events(timestamp)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_app
                ON events(app)
            """)

            # Create screenshots table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS screenshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    captured_at TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    window_app TEXT,
                    window_title TEXT,
                    dhash TEXT
                )
            """)

            # Create index for screenshots timestamp queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_screenshots_time
                ON screenshots(captured_at)
            """)

            logging.info("Database schema initialized")
    
    def insert_event(self, event: ActivityEvent) -> int:
        """
        Insert a single activity event into the database.

        Args:
            event: ActivityEvent object to store

        Returns:
            The ID of the inserted event
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get optional fields (may be None for older code paths)
            end_time = getattr(event, 'end_time', None)
            state = getattr(event, 'state', 'Active')

            cursor.execute("""
                INSERT INTO events (timestamp, duration_seconds, end_time, app, title, url, is_idle, state)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.timestamp,
                event.duration_seconds,
                end_time,
                event.app,
                event.title,
                event.url,
                1 if event.is_idle else 0,
                state
            ))

            return cursor.lastrowid
    
    def insert_events_batch(self, events: List[ActivityEvent]) -> int:
        """
        Insert multiple events in a single transaction (more efficient).

        Args:
            events: List of ActivityEvent objects

        Returns:
            Number of events inserted
        """
        if not events:
            return 0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.executemany("""
                INSERT INTO events (timestamp, duration_seconds, end_time, app, title, url, is_idle, state)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                (e.timestamp, e.duration_seconds, getattr(e, 'end_time', None),
                 e.app, e.title, e.url, 1 if e.is_idle else 0, getattr(e, 'state', 'Active'))
                for e in events
            ])

            return len(events)
    
    def get_events(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        include_idle: bool = True,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Query events with optional filtering.
        
        Args:
            start_date: ISO date string (YYYY-MM-DD) for range start (inclusive)
            end_date: ISO date string (YYYY-MM-DD) for range end (inclusive)
            include_idle: Whether to include idle events (default True)
            limit: Maximum number of events to return
            
        Returns:
            List of event dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Build query with filters
            query = "SELECT * FROM events WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(f"{start_date}T00:00:00")
            
            if end_date:
                query += " AND timestamp < ?"
                # Add one day to make end_date inclusive
                end_datetime = datetime.fromisoformat(end_date)
                next_day = end_datetime.replace(hour=23, minute=59, second=59)
                params.append(next_day.isoformat())
            
            if not include_idle:
                query += " AND is_idle = 0"
            
            query += " ORDER BY timestamp ASC"
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query, params)

            # Convert rows to dictionaries
            events = []
            for row in cursor.fetchall():
                # Derive state from is_idle if column doesn't exist (backward compatibility)
                if 'state' in row.keys() and row['state']:
                    state = row['state']
                else:
                    state = 'Inactive' if row['is_idle'] else 'Active'

                events.append({
                    'id': row['id'],
                    'timestamp': row['timestamp'],
                    'duration_seconds': row['duration_seconds'],
                    'end_time': row['end_time'] if 'end_time' in row.keys() else None,
                    'app': row['app'],
                    'title': row['title'],
                    'url': row['url'],
                    'is_idle': bool(row['is_idle']),
                    'state': state
                })

            return events
    
    def delete_events(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> int:
        """
        Delete events within a date range.
        
        CAUTION: This permanently removes data. Use carefully.
        
        Args:
            start_date: ISO date string (YYYY-MM-DD) for range start (inclusive)
            end_date: ISO date string (YYYY-MM-DD) for range end (inclusive)
            
        Returns:
            Number of events deleted
        """
        if not start_date and not end_date:
            raise ValueError("Must specify at least start_date or end_date")
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Build delete query
            query = "DELETE FROM events WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(f"{start_date}T00:00:00")
            
            if end_date:
                query += " AND timestamp < ?"
                end_datetime = datetime.fromisoformat(end_date)
                next_day = end_datetime.replace(hour=23, minute=59, second=59)
                params.append(next_day.isoformat())
            
            cursor.execute(query, params)
            deleted_count = cursor.rowcount

            logging.warning(f"Deleted {deleted_count} events from database")
            return deleted_count

    def delete_events_by_ids(self, event_ids: List[int]) -> int:
        """
        Delete specific events by their IDs.

        Args:
            event_ids: List of event IDs to delete

        Returns:
            Number of events deleted
        """
        if not event_ids:
            return 0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Use parameterized query with placeholders
            placeholders = ','.join('?' * len(event_ids))
            query = f"DELETE FROM events WHERE id IN ({placeholders})"

            cursor.execute(query, event_ids)
            deleted_count = cursor.rowcount

            logging.warning(f"Deleted {deleted_count} events by ID from database")
            return deleted_count

    def get_statistics(self) -> Dict:
        """
        Get database statistics.
        
        Returns:
            Dictionary with:
            - total_events: Total number of events
            - total_duration_seconds: Sum of all durations
            - active_duration_seconds: Sum of non-idle durations
            - idle_duration_seconds: Sum of idle durations
            - first_event: Timestamp of earliest event
            - last_event: Timestamp of most recent event
            - date_range_days: Number of days covered
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get counts and durations
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_events,
                    SUM(duration_seconds) as total_duration,
                    SUM(CASE WHEN is_idle = 0 THEN duration_seconds ELSE 0 END) as active_duration,
                    SUM(CASE WHEN is_idle = 1 THEN duration_seconds ELSE 0 END) as idle_duration,
                    MIN(timestamp) as first_event,
                    MAX(timestamp) as last_event
                FROM events
            """)
            
            row = cursor.fetchone()
            
            # Calculate date range
            date_range_days = 0
            if row['first_event'] and row['last_event']:
                first = datetime.fromisoformat(row['first_event'])
                last = datetime.fromisoformat(row['last_event'])
                date_range_days = (last - first).days + 1
            
            return {
                'total_events': row['total_events'] or 0,
                'total_duration_seconds': row['total_duration'] or 0.0,
                'active_duration_seconds': row['active_duration'] or 0.0,
                'idle_duration_seconds': row['idle_duration'] or 0.0,
                'first_event': row['first_event'],
                'last_event': row['last_event'],
                'date_range_days': date_range_days
            }
    
    def get_daily_summary(self, target_date: str) -> Dict:
        """
        Get summary statistics for a specific day.

        Args:
            target_date: ISO date string (YYYY-MM-DD)

        Returns:
            Dictionary with daily statistics
        """
        events = self.get_events(start_date=target_date, end_date=target_date)

        total_duration = sum(e['duration_seconds'] for e in events)
        active_duration = sum(e['duration_seconds'] for e in events if not e['is_idle'])
        idle_duration = sum(e['duration_seconds'] for e in events if e['is_idle'])

        # Count unique apps
        unique_apps = len(set(e['app'] for e in events if e['app']))

        return {
            'date': target_date,
            'total_events': len(events),
            'total_duration_seconds': total_duration,
            'active_duration_seconds': active_duration,
            'idle_duration_seconds': idle_duration,
            'unique_applications': unique_apps
        }

    def insert_screenshot(
        self,
        captured_at: str,
        file_path: str,
        window_app: Optional[str] = None,
        window_title: Optional[str] = None,
        dhash: Optional[str] = None
    ) -> int:
        """
        Insert a screenshot record into the database.

        Args:
            captured_at: ISO timestamp when screenshot was captured
            file_path: Path to the saved screenshot file
            window_app: Application name when screenshot was taken
            window_title: Window title when screenshot was taken
            dhash: Perceptual hash (dHash) of the screenshot for deduplication

        Returns:
            The ID of the inserted screenshot record
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO screenshots (captured_at, file_path, window_app, window_title, dhash)
                VALUES (?, ?, ?, ?, ?)
            """, (captured_at, file_path, window_app, window_title, dhash))

            return cursor.lastrowid

    def update_screenshot(
        self,
        screenshot_id: int,
        file_path: Optional[str] = None,
        dhash: Optional[str] = None
    ):
        """
        Update an existing screenshot record (used when overwriting).

        Args:
            screenshot_id: ID of the screenshot record to update
            file_path: New file path (if changed)
            dhash: New perceptual hash (if changed)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            updates = []
            params = []

            if file_path is not None:
                updates.append("file_path = ?")
                params.append(file_path)

            if dhash is not None:
                updates.append("dhash = ?")
                params.append(dhash)

            if not updates:
                return

            params.append(screenshot_id)
            query = f"UPDATE screenshots SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)

    def get_screenshots(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Query screenshots with optional filtering.

        Args:
            start_date: ISO date string (YYYY-MM-DD) for range start (inclusive)
            end_date: ISO date string (YYYY-MM-DD) for range end (inclusive)
            limit: Maximum number of screenshots to return

        Returns:
            List of screenshot dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Build query with filters
            query = "SELECT * FROM screenshots WHERE 1=1"
            params = []

            if start_date:
                query += " AND captured_at >= ?"
                params.append(f"{start_date}T00:00:00")

            if end_date:
                query += " AND captured_at < ?"
                end_datetime = datetime.fromisoformat(end_date)
                next_day = end_datetime.replace(hour=23, minute=59, second=59)
                params.append(next_day.isoformat())

            query += " ORDER BY captured_at DESC"

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query, params)

            # Convert rows to dictionaries
            screenshots = []
            for row in cursor.fetchall():
                screenshots.append({
                    'id': row['id'],
                    'captured_at': row['captured_at'],
                    'file_path': row['file_path'],
                    'window_app': row['window_app'],
                    'window_title': row['window_title'],
                    'dhash': row['dhash']
                })

            return screenshots

    def get_latest_screenshot(self) -> Optional[Dict]:
        """
        Get the most recent screenshot record.

        Returns:
            Screenshot dictionary or None if no screenshots exist
        """
        screenshots = self.get_screenshots(limit=1)
        return screenshots[0] if screenshots else None

    def migrate_missing_end_times(self) -> int:
        """
        Migrate events that are missing end_time by calculating it from
        timestamp + duration_seconds.

        This migration is safe to run multiple times (idempotent).

        Returns:
            Number of events updated with calculated end_time
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Find all events where end_time is NULL but duration_seconds is not NULL
            cursor.execute("""
                SELECT id, timestamp, duration_seconds
                FROM events
                WHERE end_time IS NULL
                AND duration_seconds IS NOT NULL
            """)

            events_to_update = cursor.fetchall()
            updated_count = 0

            for row in events_to_update:
                event_id = row['id']
                timestamp_str = row['timestamp']
                duration_seconds = row['duration_seconds']

                try:
                    # Parse timestamp and add duration
                    start_time = datetime.fromisoformat(timestamp_str)
                    end_time = start_time + timedelta(seconds=duration_seconds)
                    end_time_str = end_time.isoformat()

                    # Update the event with calculated end_time
                    cursor.execute(
                        "UPDATE events SET end_time = ? WHERE id = ?",
                        (end_time_str, event_id)
                    )
                    updated_count += 1

                except Exception as e:
                    logging.warning(f"Could not calculate end_time for event {event_id}: {e}")
                    continue

            if updated_count > 0:
                logging.info(f"Migration: Populated end_time for {updated_count} events")

            return updated_count


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string like "2h 15m" or "45m" or "30s"
    """
    if seconds < 60:
        return f"{int(seconds)}s"
    
    minutes = int(seconds / 60)
    if minutes < 60:
        return f"{minutes}m"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if remaining_minutes == 0:
        return f"{hours}h"
    
    return f"{hours}h {remaining_minutes}m"


# ============================================================================
# MAIN - FOR STANDALONE TESTING
# ============================================================================

if __name__ == "__main__":
    import tempfile
    import os
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create test database
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = os.path.join(tmpdir, "test_lawtime.db")
        print(f"Testing database: {test_db}\n")
        
        db = Database(test_db)
        
        # Create test events
        from .tracker import ActivityEvent
        
        test_events = [
            ActivityEvent(
                timestamp="2025-12-09T09:00:00",
                duration_seconds=300.0,
                app="WINWORD.EXE",
                title="Smith-Contract-v2.docx - Word",
                is_idle=False
            ),
            ActivityEvent(
                timestamp="2025-12-09T09:05:00",
                duration_seconds=600.0,
                app="chrome.exe",
                title="CanLII - 2024 BCSC 1234 - Google Chrome",
                is_idle=False
            ),
            ActivityEvent(
                timestamp="2025-12-09T09:15:00",
                duration_seconds=1800.0,
                app=None,
                title=None,
                is_idle=True
            ),
        ]
        
        # Insert test events
        print("Inserting test events...")
        count = db.insert_events_batch(test_events)
        print(f"✓ Inserted {count} events\n")
        
        # Query events
        print("Querying events...")
        events = db.get_events(start_date="2025-12-09")
        for event in events:
            idle_marker = "💤" if event['is_idle'] else "✓"
            duration_str = format_duration(event['duration_seconds'])
            print(f"  {idle_marker} {event['timestamp'][:19]} - {duration_str} - {event['app']} - {event['title']}")
        
        # Get statistics
        print("\nDatabase statistics:")
        stats = db.get_statistics()
        print(f"  Total events: {stats['total_events']}")
        print(f"  Active time: {format_duration(stats['active_duration_seconds'])}")
        print(f"  Idle time: {format_duration(stats['idle_duration_seconds'])}")
        
        # Get daily summary
        print("\nDaily summary for 2025-12-09:")
        summary = db.get_daily_summary("2025-12-09")
        print(f"  Events: {summary['total_events']}")
        print(f"  Active: {format_duration(summary['active_duration_seconds'])}")
        print(f"  Idle: {format_duration(summary['idle_duration_seconds'])}")
        
        print("\n✓ Database tests complete")
