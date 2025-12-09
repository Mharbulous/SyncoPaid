"""
Data export module for generating JSON files from captured activities.

Exports activity data in a structured format suitable for processing by
external LLM tools for matter categorization and billing narrative generation.
"""

import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional

from .database import Database


class Exporter:
    """
    Handles exporting activity data to JSON format.
    
    Provides methods for:
    - Exporting date ranges to JSON
    - Formatting data for LLM processing
    - Generating summary statistics
    """
    
    def __init__(self, database: Database):
        """
        Initialize exporter with database connection.
        
        Args:
            database: Database instance to query events from
        """
        self.database = database
        logging.info("Exporter initialized")
    
    def export_to_json(
        self,
        output_path: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        include_idle: bool = True,
        pretty_print: bool = True
    ) -> Dict:
        """
        Export events to JSON file.
        
        Args:
            output_path: Path where JSON file will be saved
            start_date: ISO date string (YYYY-MM-DD) for range start
            end_date: ISO date string (YYYY-MM-DD) for range end
            include_idle: Whether to include idle events
            pretty_print: Whether to format JSON with indentation
            
        Returns:
            Dictionary containing export metadata (stats, file size, etc.)
        """
        # Query events from database
        events = self.database.get_events(
            start_date=start_date,
            end_date=end_date,
            include_idle=include_idle
        )
        
        # Calculate statistics
        total_duration = sum(e['duration_seconds'] for e in events)
        active_duration = sum(e['duration_seconds'] for e in events if not e['is_idle'])
        idle_duration = sum(e['duration_seconds'] for e in events if e['is_idle'])
        
        # Build export structure
        export_data = {
            "export_date": datetime.now().isoformat(),
            "date_range": {
                "start": start_date or "all",
                "end": end_date or "all"
            },
            "total_events": len(events),
            "total_duration_seconds": round(total_duration, 2),
            "active_duration_seconds": round(active_duration, 2),
            "idle_duration_seconds": round(idle_duration, 2),
            "include_idle": include_idle,
            "events": self._format_events_for_export(events)
        }
        
        # Write to file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            if pretty_print:
                json.dump(export_data, f, indent=2)
            else:
                json.dump(export_data, f)
        
        # Get file size
        file_size = output_path.stat().st_size
        
        logging.info(
            f"Exported {len(events)} events to {output_path} "
            f"({file_size:,} bytes)"
        )
        
        return {
            "file_path": str(output_path),
            "file_size_bytes": file_size,
            "events_exported": len(events),
            "date_range": export_data["date_range"],
            "total_duration_hours": round(total_duration / 3600, 2)
        }
    
    def _format_events_for_export(self, events: List[Dict]) -> List[Dict]:
        """
        Format events for JSON export.
        
        Removes internal database IDs and ensures consistent format.
        """
        formatted = []
        
        for event in events:
            formatted.append({
                "timestamp": event['timestamp'],
                "duration_seconds": event['duration_seconds'],
                "app": event['app'],
                "title": event['title'],
                "url": event['url'],
                "is_idle": event['is_idle']
            })
        
        return formatted
    
    def export_daily_summary(
        self,
        output_path: str,
        target_date: str
    ) -> Dict:
        """
        Export a summary for a specific day.
        
        Args:
            output_path: Path where JSON file will be saved
            target_date: ISO date string (YYYY-MM-DD)
            
        Returns:
            Export metadata
        """
        # Get daily summary from database
        summary = self.database.get_daily_summary(target_date)
        
        # Get events for the day
        events = self.database.get_events(
            start_date=target_date,
            end_date=target_date,
            include_idle=True
        )
        
        # Group events by application
        app_breakdown = self._calculate_app_breakdown(events)
        
        # Build summary structure
        summary_data = {
            "export_date": datetime.now().isoformat(),
            "date": target_date,
            "summary": {
                "total_events": summary['total_events'],
                "total_duration_hours": round(summary['total_duration_seconds'] / 3600, 2),
                "active_duration_hours": round(summary['active_duration_seconds'] / 3600, 2),
                "idle_duration_hours": round(summary['idle_duration_seconds'] / 3600, 2),
                "unique_applications": summary['unique_applications']
            },
            "application_breakdown": app_breakdown,
            "events": self._format_events_for_export(events)
        }
        
        # Write to file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(summary_data, f, indent=2)
        
        file_size = output_path.stat().st_size
        
        logging.info(f"Exported daily summary for {target_date} to {output_path}")
        
        return {
            "file_path": str(output_path),
            "file_size_bytes": file_size,
            "date": target_date,
            "total_events": summary['total_events']
        }
    
    def _calculate_app_breakdown(self, events: List[Dict]) -> List[Dict]:
        """
        Calculate time spent per application.
        
        Args:
            events: List of event dictionaries
            
        Returns:
            List of {app, duration_seconds, percentage} dictionaries
        """
        # Aggregate by app
        app_totals = {}
        total_duration = 0
        
        for event in events:
            if event['is_idle']:
                continue
            
            app = event['app'] or 'unknown'
            duration = event['duration_seconds']
            
            app_totals[app] = app_totals.get(app, 0) + duration
            total_duration += duration
        
        # Convert to list and calculate percentages
        breakdown = []
        for app, duration in sorted(app_totals.items(), key=lambda x: x[1], reverse=True):
            percentage = (duration / total_duration * 100) if total_duration > 0 else 0
            breakdown.append({
                "app": app,
                "duration_seconds": round(duration, 2),
                "duration_hours": round(duration / 3600, 2),
                "percentage": round(percentage, 1)
            })
        
        return breakdown
    
    def generate_llm_prompt_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> str:
        """
        Generate a JSON string optimized for LLM prompts.
        
        This produces a simplified, compact format ideal for including
        in Claude/GPT prompts for automatic categorization.
        
        Args:
            start_date: ISO date string (YYYY-MM-DD)
            end_date: ISO date string (YYYY-MM-DD)
            
        Returns:
            JSON string ready for LLM prompt
        """
        events = self.database.get_events(
            start_date=start_date,
            end_date=end_date,
            include_idle=False  # Exclude idle for LLM processing
        )
        
        # Simplified format for LLM
        llm_events = []
        for event in events:
            # Extract time only (not full timestamp)
            time_str = event['timestamp'].split('T')[1][:8]  # HH:MM:SS
            
            llm_events.append({
                "time": time_str,
                "duration_min": round(event['duration_seconds'] / 60, 1),
                "app": event['app'],
                "title": event['title']
            })
        
        return json.dumps(llm_events, indent=2)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def format_file_size(bytes: int) -> str:
    """Format file size in human-readable form."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} TB"


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
    
    print("Testing Exporter...\n")
    
    # Create test database with sample data
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = os.path.join(tmpdir, "test_lawtime.db")
        db = Database(test_db)
        
        # Create test events
        from .tracker import ActivityEvent
        
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
