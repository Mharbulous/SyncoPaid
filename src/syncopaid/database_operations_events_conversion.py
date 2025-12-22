"""
Database row conversion utilities for activity events.

Provides:
- Convert database rows to dictionaries with backward compatibility
"""

import json
import logging
from typing import List, Dict


class EventConversionMixin:
    """
    Mixin providing event row-to-dictionary conversion.

    Handles backward compatibility for older database schemas.
    """

    def _rows_to_dicts(self, rows) -> List[Dict]:
        """
        Convert database rows to dictionaries with backward compatibility.

        Args:
            rows: Database rows with row factory

        Returns:
            List of event dictionaries
        """
        events = []
        for row in rows:
            # Derive state from is_idle if column doesn't exist (backward compatibility)
            if 'state' in row.keys() and row['state']:
                state = row['state']
            else:
                state = 'Inactive' if row['is_idle'] else 'Active'

            # Deserialize metadata JSON if present
            metadata = None
            if 'metadata' in row.keys() and row['metadata']:
                metadata = json.loads(row['metadata'])

            # Get cmdline field if it exists (backward compatibility)
            cmdline = row['cmdline'] if 'cmdline' in row.keys() else None

            # Get interaction_level with fallback for older records
            if 'interaction_level' in row.keys() and row['interaction_level']:
                interaction_level = row['interaction_level']
            else:
                interaction_level = 'passive'

            events.append({
                'id': row['id'],
                'timestamp': row['timestamp'],
                'duration_seconds': row['duration_seconds'],
                'end_time': row['end_time'] if 'end_time' in row.keys() else None,
                'app': row['app'],
                'title': row['title'],
                'url': row['url'],
                'cmdline': cmdline,
                'is_idle': bool(row['is_idle']),
                'state': state,
                'metadata': metadata,
                'interaction_level': interaction_level,
                'matter_id': row['matter_id'] if 'matter_id' in row.keys() else None,
                'confidence': row['confidence'] if 'confidence' in row.keys() else 0,
                'flagged_for_review': bool(row['flagged_for_review']) if 'flagged_for_review' in row.keys() else False
            })

        return events
