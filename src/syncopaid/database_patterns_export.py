"""
Database operations for pattern maintenance and export.

Handles archiving stale patterns and exporting pattern data in JSON format
for use with external LLM tools.
"""

import json
import logging
from typing import List, Dict
from datetime import datetime, timedelta


class PatternsExportMixin:
    """
    Mixin providing pattern maintenance and export operations.

    Requires _get_connection() and get_all_patterns() methods.
    """

    def archive_stale_patterns(self, days: int = 90) -> int:
        """
        Archive patterns that haven't been used in the specified number of days.

        Archived patterns are excluded from matching but retained for analysis.

        Args:
            days: Number of days of inactivity before archiving (default: 90)

        Returns:
            Number of patterns archived
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            cursor.execute("""
                UPDATE categorization_patterns
                SET is_archived = 1
                WHERE is_archived = 0
                AND last_used_at < ?
            """, (cutoff_date,))

            archived = cursor.rowcount
            conn.commit()

            if archived > 0:
                logging.info(f"Archived {archived} stale patterns (unused for {days}+ days)")

            return archived

    def export_patterns_json(self, include_archived: bool = False) -> str:
        """
        Export all patterns in JSON format for LLM context.

        Format is optimized for including in AI prompts for categorization.
        Privacy: This export is local-only, for user's external AI tools.

        Args:
            include_archived: Whether to include archived patterns

        Returns:
            JSON string with patterns data
        """
        patterns = self.get_all_patterns(include_archived)

        # Format for LLM consumption
        export_data = {
            "export_date": datetime.now().isoformat(),
            "pattern_count": len(patterns),
            "patterns": [
                {
                    "matter_description": p['matter_description'],
                    "client_name": p.get('client_name'),
                    "app_pattern": p['app_pattern'],
                    "url_pattern": p['url_pattern'],
                    "title_pattern": p['title_pattern'],
                    "confidence": p['confidence_score'],
                    "match_count": p['match_count']
                }
                for p in patterns
            ]
        }

        return json.dumps(export_data, indent=2)
