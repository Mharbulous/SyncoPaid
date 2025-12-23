# 027C: AI Learning Database - Pattern Expiration and Export

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 3.6 | **Created:** 2025-12-23 | **Stage:** `planned`
**Parent Plan:** 027_ai-learning-database.md (decomposed)
**Depends On:** 027B_ai-learning-correction-logic.md (must be completed first)

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Implement pattern expiration (90-day archive) and JSON export for LLM context.
**Approach:** Add archive_stale_patterns, get_all_patterns, and export_patterns_json methods.
**Tech Stack:** SQLite, Python sqlite3 module, JSON

---

## Story Context

**Title:** AI Learning Database for Categorization Patterns
**Description:** Store user corrections when they change AI categorization suggestions, building matter-specific patterns (app, URL, title) that improve categorization accuracy over time.

This sub-plan covers maintenance and export:
- [ ] Pattern expiration: archive patterns not used in 90 days to prevent stale suggestions
- [ ] Export patterns in JSON export for external AI/LLM context
- [ ] Privacy: patterns stored locally only, never leave device (export is user-controlled)

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Sub-plan 027B completed - correction recording and confidence adjustment work
- [ ] Tests pass: `python -m pytest tests/test_categorization_patterns.py -v`

## TDD Tasks

### Task 1: Implement pattern expiration (90-day archive) (~3 min)

**Files:**
- Modify: `src/syncopaid/database_patterns.py`
- Test: `tests/test_categorization_patterns.py`

**Context:** Patterns not used in 90 days should be archived to prevent stale suggestions from affecting categorization.

**Step 1 - RED:** Write failing tests
```python
# tests/test_categorization_patterns.py (ADD to existing file)
from datetime import datetime, timedelta

def test_archive_stale_patterns():
    """Test archiving patterns not used in 90 days."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        client_id = db.insert_client(name="Test Client")
        matter_id = db.insert_matter("2024-001", client_id, "Test matter")

        # Insert pattern with old last_used_at
        db.insert_pattern(matter_id, app_pattern="old_app.exe")

        # Manually set last_used_at to 100 days ago
        conn = sqlite3.connect(db_path)
        old_date = (datetime.now() - timedelta(days=100)).isoformat()
        conn.execute("UPDATE categorization_patterns SET last_used_at = ?", (old_date,))
        conn.commit()
        conn.close()

        # Run expiration
        archived_count = db.archive_stale_patterns(days=90)

        assert archived_count == 1

        # Pattern should not appear in normal queries
        patterns = db.get_patterns_for_matter(matter_id)
        assert len(patterns) == 0

        # But should appear if including archived
        patterns = db.get_patterns_for_matter(matter_id, include_archived=True)
        assert len(patterns) == 1
        assert patterns[0]['is_archived'] == 1
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_categorization_patterns.py::test_archive_stale_patterns -v
```
Expected output: `FAILED`

**Step 3 - GREEN:** Add expiration method
```python
# src/syncopaid/database_patterns.py (ADD to PatternsDatabaseMixin class)

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
```

Also add the timedelta import at the top of the file:
```python
from datetime import datetime, timedelta
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_categorization_patterns.py -v
```
Expected output: All tests `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/database_patterns.py tests/test_categorization_patterns.py && git commit -m "feat: add pattern expiration for stale pattern archival"
```

---

### Task 2: Add patterns to JSON export (~4 min)

**Files:**
- Modify: `src/syncopaid/database_patterns.py`
- Test: `tests/test_categorization_patterns.py`

**Context:** Patterns should be exportable in JSON for external AI/LLM context. The Exporter class handles JSON exports (lines 43-113 in exporter.py). We add a method to export patterns separately.

**Step 1 - RED:** Write failing tests
```python
# tests/test_categorization_patterns.py (ADD to existing file)
import json

def test_export_patterns_for_llm():
    """Test exporting patterns in LLM-friendly JSON format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        client_id = db.insert_client(name="Test Client")
        matter_id = db.insert_matter("2024-001", client_id, "Contract review")

        db.insert_pattern(matter_id, app_pattern="WINWORD.EXE", confidence_score=0.95)
        db.insert_pattern(matter_id, url_pattern="*canlii.org*", confidence_score=0.8)

        # Export patterns
        patterns_json = db.export_patterns_json()
        patterns = json.loads(patterns_json)

        assert 'patterns' in patterns
        assert len(patterns['patterns']) == 2
        assert any(p['app_pattern'] == 'WINWORD.EXE' for p in patterns['patterns'])


def test_get_all_active_patterns():
    """Test retrieving all active patterns for export."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        client_id = db.insert_client(name="Test Client")
        matter_a = db.insert_matter("2024-001", client_id, "Matter A")
        matter_b = db.insert_matter("2024-002", client_id, "Matter B")

        db.insert_pattern(matter_a, app_pattern="app1.exe")
        db.insert_pattern(matter_b, app_pattern="app2.exe")

        all_patterns = db.get_all_patterns()
        assert len(all_patterns) == 2
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_categorization_patterns.py::test_export_patterns_for_llm -v
```
Expected output: `FAILED`

**Step 3 - GREEN:** Add export methods
```python
# src/syncopaid/database_patterns.py (ADD to PatternsDatabaseMixin class)
# Also add json import at top of file: import json

    def get_all_patterns(self, include_archived: bool = False) -> List[Dict]:
        """
        Get all patterns across all matters.

        Args:
            include_archived: Whether to include archived patterns

        Returns:
            List of all pattern dictionaries with matter info
        """
        with self._get_connection() as conn:
            conn.row_factory = self._dict_factory
            cursor = conn.cursor()

            archive_filter = "" if include_archived else "WHERE cp.is_archived = 0"

            cursor.execute(f"""
                SELECT cp.*, m.matter_number, m.description as matter_description,
                       c.name as client_name
                FROM categorization_patterns cp
                JOIN matters m ON cp.matter_id = m.id
                LEFT JOIN clients c ON m.client_id = c.id
                {archive_filter}
                ORDER BY cp.confidence_score DESC, cp.match_count DESC
            """)
            return cursor.fetchall()

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
                    "matter_number": p['matter_number'],
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
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_categorization_patterns.py -v
```
Expected output: All tests `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/database_patterns.py tests/test_categorization_patterns.py && git commit -m "feat: add pattern export for LLM context"
```

---

## Final Verification

Run after all tasks complete:
```bash
python -m pytest tests/test_categorization_patterns.py -v  # All pattern tests pass
python -m pytest tests/test_matter_client.py -v             # Existing tests still pass
python -m pytest tests/test_database.py -v                   # Database tests pass
python -m syncopaid.database                                  # Module runs without error
```

## Rollback

If issues arise: `git log --oneline -5` to find commit, then `git revert <hash>`

## Notes

- This is sub-plan C of 3 (027A, 027B, 027C) - FINAL sub-plan for story 3.6
- Archived patterns are soft-deleted and can be restored if needed
- The `export_patterns_json()` method produces local-only output for user's external AI tools
- All pattern storage is local - no data leaves the device

## Dependencies

- Requires sub-plan 027B completed
- Future: Story 15.1 (Automatic Screenshot Analysis) can use patterns for initial categorization hints
