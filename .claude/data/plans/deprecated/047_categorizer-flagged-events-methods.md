# 047: Activity-to-Matter Matching - Flagged Events Methods

## Task
Add database methods for retrieving and updating flagged events.

## Context
Users need to retrieve events that are flagged for review and update their categorization after manual review.

## Scope
- get_flagged_events() - retrieves events where flagged_for_review=True
- update_event_categorization() - updates matter assignment and clears flag

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/database.py` | Add methods |
| `tests/test_categorizer.py` | Add tests |

## Implementation

### get_flagged_events

```python
# src/syncopaid/database.py (add)
def get_flagged_events(
    self,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Dict]:
    """Get events flagged for manual review."""
    with self._get_connection() as conn:
        cursor = conn.cursor()

        query = "SELECT * FROM events WHERE flagged_for_review = 1"
        params = []

        if start_date:
            query += " AND timestamp >= ?"
            params.append(f"{start_date}T00:00:00")

        query += " ORDER BY timestamp ASC"

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query, params)

        events = []
        for row in cursor.fetchall():
            state = row['state'] if 'state' in row.keys() and row['state'] else ('Inactive' if row['is_idle'] else 'Active')
            events.append({
                'id': row['id'],
                'timestamp': row['timestamp'],
                'duration_seconds': row['duration_seconds'],
                'app': row['app'],
                'title': row['title'],
                'matter_id': row['matter_id'] if 'matter_id' in row.keys() else None,
                'confidence': row['confidence'] if 'confidence' in row.keys() else 0,
                'flagged_for_review': True,
            })

        return events
```

### update_event_categorization

```python
# src/syncopaid/database.py (add)
def update_event_categorization(
    self,
    event_id: int,
    matter_id: Optional[int] = None,
    confidence: int = 100,
    flagged_for_review: bool = False
):
    """Update categorization of an existing event."""
    with self._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE events
            SET matter_id = ?, confidence = ?, flagged_for_review = ?
            WHERE id = ?
        """, (matter_id, confidence, 1 if flagged_for_review else 0, event_id))

        logging.info(f"Updated categorization for event {event_id}")
```

### Tests

```python
# tests/test_categorizer.py (add)
def test_get_flagged_events():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Database(str(Path(tmpdir) / "test.db"))
        from syncopaid.tracker import ActivityEvent

        # High confidence - not flagged
        db.insert_event(
            ActivityEvent(timestamp="2025-12-19T10:00:00", duration_seconds=60, app="test", title="High"),
            confidence=90, flagged_for_review=False
        )
        # Low confidence - flagged
        db.insert_event(
            ActivityEvent(timestamp="2025-12-19T10:01:00", duration_seconds=60, app="test", title="Low"),
            confidence=50, flagged_for_review=True
        )

        flagged = db.get_flagged_events()
        assert len(flagged) == 1
        assert flagged[0]['title'] == "Low"


def test_update_event_categorization():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Database(str(Path(tmpdir) / "test.db"))
        from syncopaid.tracker import ActivityEvent

        matter_id = db.insert_matter(matter_number="REVIEW", description="Test")
        event_id = db.insert_event(
            ActivityEvent(timestamp="2025-12-19T10:00:00", duration_seconds=60, app="test", title="Needs review"),
            confidence=50, flagged_for_review=True
        )

        db.update_event_categorization(event_id, matter_id=matter_id, confidence=100)

        events = db.get_events()
        assert events[0]['matter_id'] == matter_id
        assert events[0]['confidence'] == 100
        assert events[0]['flagged_for_review'] is False
```

## Verification

```bash
pytest tests/test_categorizer.py -v
```

## Dependencies
- Task 046 (database schema)

## Next Task
After this: `048_categorizer-app-integration.md`
