import sqlite3
import subprocess
from datetime import datetime

conn = sqlite3.connect('.claude/data/story-tree.db')
cursor = conn.cursor()

# Define stories
stories = [
    {
        'id': '1.1',
        'title': 'Window Activity Tracking System',
        'description': '''As a civil litigation lawyer
I want automatic tracking of active windows and applications at second-level precision
So that I can accurately bill clients for time spent on their cases

Acceptance Criteria:
- Polls active window every 1 second via Windows API (GetForegroundWindow)
- Captures application name and window title
- Detects user idle time (keyboard/mouse inactivity)
- Merges consecutive identical events within threshold (default 2 seconds)
- Generates ActivityEvent instances with timestamp, duration, app, title, idle status
- Handles multi-monitor setups correctly

Related context: Commits db8305c (focus change detection), 29595a2 (delete log entries), e98fd8e (multi-monitor fix), 531a5b9 (end_time tracking). Module: src/SyncoPaid/tracker.py''',
        'capacity': 8,
        'stage': 'concept'
    },
    {
        'id': '1.2',
        'title': 'Screenshot Capture & Deduplication',
        'description': '''As a civil litigation lawyer
I want periodic screenshot capture with intelligent deduplication
So that I have visual evidence of my work without consuming excessive storage

Acceptance Criteria:
- Captures screenshots at configurable intervals (default 10 seconds)
- Uses perceptual hashing (dHash) to detect duplicate/similar screenshots
- Context-aware similarity thresholds (strict for window changes, permissive for same window)
- Overwrites near-identical screenshots to save storage
- Saves screenshots organized by date (YYYY-MM-DD folders)
- Supports action-based screenshots (clicks, key presses, drag operations)
- Handles multi-monitor coordinate systems correctly
- Applies JPEG quality and dimension constraints

Related context: Commits e98fd8e (MSS library), b082e8b (filename sanitization), df69b65 (context-aware thresholds), 8ed8285 (action screenshots). Modules: src/SyncoPaid/screenshot.py, src/SyncoPaid/action_screenshot.py''',
        'capacity': 10,
        'stage': 'concept'
    },
    {
        'id': '1.3',
        'title': 'Data Management & Export',
        'description': '''As a civil litigation lawyer
I want reliable data storage and export functionality
So that I can process my time logs with LLM tools for billing categorization

Acceptance Criteria:
- Stores activity events in SQLite database with start_time, duration, end_time
- Links screenshots to events in database
- Exports data to JSON format optimized for LLM processing
- Supports date range filtering for exports
- Provides delete operations for log entries (single and bulk)
- Maintains data integrity during concurrent operations
- Preserves attorney-client privilege (all data local, no cloud sync)
- Calculates activity statistics and totals

Related context: Commits 29595a2 (delete log entries), 876c6ac (update totals), f23b249 (delete_events_by_ids), 531a5b9 (end_time tracking). Modules: src/SyncoPaid/database.py, src/SyncoPaid/exporter.py''',
        'capacity': 7,
        'stage': 'concept'
    },
    {
        'id': '1.4',
        'title': 'User Interface & Controls',
        'description': '''As a civil litigation lawyer
I want a system tray interface with intuitive controls
So that I can easily start/pause tracking and view my time logs

Acceptance Criteria:
- System tray icon shows tracking status
- Menu provides Start/Pause toggle
- View Time opens window displaying all logged events
- View Time window supports multi-select (Ctrl+click, Shift+click)
- Command field accepts text commands (quit, screenshots, periodic, actions)
- Start with Windows toggle in tray menu
- About dialog displays version and commit ID
- View Captured Images button opens screenshot folders
- Treeview displays start time, duration, end time, application, and title

Related context: Commits b960361 (command field), 1409acc (Start with Windows), 5873af4 (remove quit), 36786be (View Images button), 36bb125 (About menu). Modules: src/SyncoPaid/tray.py, view_time_window.py''',
        'capacity': 9,
        'stage': 'concept'
    },
    {
        'id': '1.5',
        'title': 'Configuration & Settings Management',
        'description': '''As a civil litigation lawyer
I want configurable tracking behavior and thresholds
So that I can customize the tool to match my workflow and storage constraints

Acceptance Criteria:
- Centralized configuration file (%LOCALAPPDATA%\\SyncoPaid\\config.json)
- Configurable poll interval for window tracking (default 1 second)
- Configurable idle threshold (default 180 seconds)
- Configurable event merge threshold (default 2 seconds)
- Screenshot settings (enabled/disabled, interval, quality, max dimension)
- Action screenshot settings (enabled/disabled, throttle, quality)
- Context-aware similarity thresholds for deduplication
- Start tracking on launch option
- Settings persist across application restarts
- Validation of configuration values with sensible defaults

Related context: Commits df69b65 (context-aware thresholds), 8ed8285 (action screenshot config), 4e47aa8 (lastUpdated fields). Module: src/SyncoPaid/config.py''',
        'capacity': 6,
        'stage': 'concept'
    },
    {
        'id': '1.6',
        'title': 'Build, Packaging & Distribution',
        'description': '''As a SyncoPaid developer
I want automated build and packaging system
So that I can distribute executable versions to users with proper versioning

Acceptance Criteria:
- Automatic version generation from VERSION file + git commit hash
- Windows executable metadata (FileVersion, ProductVersion, Copyright)
- PyInstaller configuration with proper hidden imports
- Single-file executable output (no console window)
- Build scripts for Windows (build.bat) and Git Bash (build.sh)
- Virtual environment validation before build
- Clean build artifacts between builds
- Icon embedding in executable
- Version displayed in system tray tooltip and About dialog

Related context: Commits ab5856b (automatic version), cc75360 (commit count), 5e39595 (fix build script), c28e804 (compilation testing). Files: build.sh, build.bat, generate_version.py, SyncoPaid.spec''',
        'capacity': 5,
        'stage': 'concept'
    }
]

# Insert each story
for story in stories:
    # Insert story node
    cursor.execute('''
        INSERT INTO story_nodes (id, title, description, capacity, stage, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
    ''', (story['id'], story['title'], story['description'], story['capacity'], story['stage']))

    # Add to closure table (self + ancestor relationships)
    cursor.execute('''
        INSERT INTO story_paths (ancestor_id, descendant_id, depth)
        SELECT ancestor_id, ?, depth + 1
        FROM story_paths WHERE descendant_id = 'root'
        UNION ALL SELECT ?, ?, 0
    ''', (story['id'], story['id'], story['id']))

    print(f'Inserted story {story["id"]}: {story["title"]}')

# Update metadata
cursor.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('lastUpdated', datetime('now'))")

# Get newest commit hash from git
try:
    result = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True)
    commit_hash = result.stdout.strip()
    cursor.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('lastAnalyzedCommit', ?)", (commit_hash,))
    print(f'\nUpdated lastAnalyzedCommit to: {commit_hash[:7]}')
except Exception as e:
    print(f'\nCould not get git commit hash: {e}')

conn.commit()
conn.close()

print('\nDatabase updated successfully!')
