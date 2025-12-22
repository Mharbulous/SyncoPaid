"""
Standalone tests for the Exporter module.

Run with: python -m syncopaid.exporter_tests
"""

import json
import logging
import tempfile
import os

from .database import Database
from .exporter import Exporter
from .exporter_formatting import format_file_size
from .tracker import ActivityEvent


def run_exporter_tests():
    """Run comprehensive tests of the Exporter class."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("Testing Exporter...\n")

    # Create test database with sample data
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = os.path.join(tmpdir, "test_lawtime.db")
        db = Database(test_db)

        # Create test events
        test_events = [
            ActivityEvent(
                timestamp="2025-12-09T09:00:00",
                duration_seconds=1200.0,
                app="WINWORD.EXE",
                title="Smith-Contract-v2.docx - Word",
                is_idle=False
            ),
            ActivityEvent(
                timestamp="2025-12-09T09:20:00",
                duration_seconds=900.0,
                app="chrome.exe",
                title="CanLII - 2024 BCSC 1234 - Google Chrome",
                is_idle=False
            ),
            ActivityEvent(
                timestamp="2025-12-09T09:35:00",
                duration_seconds=600.0,
                app="OUTLOOK.EXE",
                title="RE: Smith v. Jones - Outlook",
                is_idle=False
            ),
            ActivityEvent(
                timestamp="2025-12-09T09:45:00",
                duration_seconds=1800.0,
                app=None,
                title=None,
                is_idle=True
            ),
        ]

        db.insert_events_batch(test_events)

        # Create exporter
        exporter = Exporter(db)

        # Test full export
        print("1. Exporting all events...")
        export_path = os.path.join(tmpdir, "export_full.json")
        result = exporter.export_to_json(
            output_path=export_path,
            start_date="2025-12-09",
            end_date="2025-12-09"
        )
        print(f"   ✓ Exported to: {result['file_path']}")
        print(f"   ✓ File size: {format_file_size(result['file_size_bytes'])}")
        print(f"   ✓ Events: {result['events_exported']}")
        print(f"   ✓ Total hours: {result['total_duration_hours']}")

        # Test daily summary
        print("\n2. Exporting daily summary...")
        summary_path = os.path.join(tmpdir, "summary_2025-12-09.json")
        result = exporter.export_daily_summary(
            output_path=summary_path,
            target_date="2025-12-09"
        )
        print(f"   ✓ Exported to: {result['file_path']}")

        # Show sample JSON content
        print("\n3. Sample JSON content:")
        with open(export_path, 'r') as f:
            data = json.load(f)
        print(f"   Date range: {data['date_range']}")
        print(f"   Total events: {data['total_events']}")
        print(f"   Active time: {data['active_duration_seconds']/3600:.2f}h")
        print(f"   First event: {data['events'][0]['timestamp']}")

        # Test LLM prompt format
        print("\n4. LLM prompt format:")
        llm_data = exporter.generate_llm_prompt_data(
            start_date="2025-12-09",
            end_date="2025-12-09"
        )
        print(llm_data)

    print("\n✓ Exporter tests complete")


if __name__ == "__main__":
    run_exporter_tests()
