# 027B: AI Learning Database - Correction Recording and Confidence

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 3.6 | **Created:** 2025-12-23 | **Stage:** `planned`
**Parent Plan:** 027_ai-learning-database.md (decomposed)
**Depends On:** 027A_ai-learning-schema-crud.md (must be completed first)

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Implement user correction recording and confidence adjustment for contradicting patterns.
**Approach:** Add record_correction and record_correction_with_contradiction methods to PatternsDatabaseMixin.
**Tech Stack:** SQLite, Python sqlite3 module

---

## Story Context

**Title:** AI Learning Database for Categorization Patterns
**Description:** Store user corrections when they change AI categorization suggestions, building matter-specific patterns (app, URL, title) that improve categorization accuracy over time.

This sub-plan covers correction logic:
- [ ] Store user corrections: when user changes activity from AI suggestion to different matter, record the pattern
- [ ] Confidence scoring: increase confidence when pattern matches repeatedly, decrease when corrections contradict it

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Sub-plan 027A completed - categorization_patterns table and CRUD operations exist
- [ ] Tests pass: `python -m pytest tests/test_categorization_patterns.py -v`

## TDD Tasks

### Task 1: Implement user correction recording (~4 min)

**Files:**
- Modify: `src/syncopaid/database_patterns.py`
- Test: `tests/test_categorization_patterns.py`

**Context:** When a user corrects an AI categorization (changes activity from one matter to another), we record the activity's attributes as a new pattern for the corrected matter.

**Step 1 - RED:** Write failing tests
```python
# tests/test_categorization_patterns.py (ADD to existing file)

def test_record_user_correction():
    """Test recording a user correction creates appropriate pattern."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        client_id = db.insert_client(name="Test Client")
        matter_id = db.insert_matter("2024-001", client_id, "Contract review")

        # User corrects: activity was misclassified, should be matter 2024-001
        pattern_id = db.record_correction(
            matter_id=matter_id,
            app="WINWORD.EXE",
            url=None,
            title="Smith Contract Draft.docx - Word"
        )

        assert pattern_id > 0

        # Pattern should now match similar activities
        matches = db.find_matching_patterns(app="WINWORD.EXE")
        assert len(matches) == 1
        assert matches[0]['matter_id'] == matter_id


def test_duplicate_correction_increases_confidence():
    """Test that repeated corrections increase pattern confidence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        client_id = db.insert_client(name="Test Client")
        matter_id = db.insert_matter("2024-001", client_id, "Contract review")

        # First correction
        db.record_correction(matter_id, app="WINWORD.EXE")
        patterns = db.get_patterns_for_matter(matter_id)
        initial_confidence = patterns[0]['confidence_score']
        initial_count = patterns[0]['match_count']

        # Same correction again - should reinforce pattern
        db.record_correction(matter_id, app="WINWORD.EXE")
        patterns = db.get_patterns_for_matter(matter_id)

        assert patterns[0]['match_count'] > initial_count
        assert patterns[0]['confidence_score'] >= initial_confidence
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_categorization_patterns.py::test_record_user_correction -v
```
Expected output: `FAILED`

**Step 3 - GREEN:** Add correction recording method
```python
# src/syncopaid/database_patterns.py (ADD to PatternsDatabaseMixin class)

    def record_correction(
        self,
        matter_id: int,
        app: Optional[str] = None,
        url: Optional[str] = None,
        title: Optional[str] = None
    ) -> int:
        """
        Record a user correction to create or reinforce a pattern.

        When user corrects AI categorization, record the activity's attributes
        as a pattern for the correct matter. If pattern already exists,
        increase confidence and match count.

        Args:
            matter_id: Correct matter ID (what user selected)
            app: Application name of the activity
            url: URL of the activity (if any)
            title: Window title of the activity

        Returns:
            ID of the created or updated pattern
        """
        if not any([app, url, title]):
            raise ValueError("At least one attribute (app, url, or title) is required")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()

            # Check if pattern already exists
            cursor.execute("""
                SELECT id, match_count, confidence_score
                FROM categorization_patterns
                WHERE matter_id = ?
                AND (app_pattern = ? OR (app_pattern IS NULL AND ? IS NULL))
                AND (url_pattern = ? OR (url_pattern IS NULL AND ? IS NULL))
                AND (title_pattern = ? OR (title_pattern IS NULL AND ? IS NULL))
                AND is_archived = 0
            """, (matter_id, app, app, url, url, title, title))

            existing = cursor.fetchone()

            if existing:
                # Reinforce existing pattern
                pattern_id, match_count, confidence = existing
                new_count = match_count + 1
                # Increase confidence slightly, max 1.0
                new_confidence = min(1.0, confidence + 0.05)

                cursor.execute("""
                    UPDATE categorization_patterns
                    SET match_count = ?, confidence_score = ?, last_used_at = ?
                    WHERE id = ?
                """, (new_count, new_confidence, now, pattern_id))
                conn.commit()
                logging.info(f"Reinforced pattern {pattern_id}: count={new_count}, confidence={new_confidence:.2f}")
                return pattern_id
            else:
                # Create new pattern
                cursor.execute("""
                    INSERT INTO categorization_patterns
                    (matter_id, app_pattern, url_pattern, title_pattern, confidence_score, last_used_at)
                    VALUES (?, ?, ?, ?, 1.0, ?)
                """, (matter_id, app, url, title, now))
                conn.commit()
                pattern_id = cursor.lastrowid
                logging.info(f"Created new pattern {pattern_id} for matter {matter_id}")
                return pattern_id
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_categorization_patterns.py -v
```
Expected output: All tests `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/database_patterns.py tests/test_categorization_patterns.py && git commit -m "feat: add user correction recording for AI learning"
```

---

### Task 2: Implement confidence adjustment on contradictions (~4 min)

**Files:**
- Modify: `src/syncopaid/database_patterns.py`
- Test: `tests/test_categorization_patterns.py`

**Context:** When a user corrects an activity to a *different* matter than an existing pattern suggests, we should decrease confidence of the old pattern.

**Step 1 - RED:** Write failing tests
```python
# tests/test_categorization_patterns.py (ADD to existing file)

def test_contradicting_correction_decreases_confidence():
    """Test that contradicting corrections decrease old pattern confidence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))

        client_id = db.insert_client(name="Test Client")
        matter_a = db.insert_matter("2024-001", client_id, "Matter A")
        matter_b = db.insert_matter("2024-002", client_id, "Matter B")

        # Initial pattern: WINWORD.EXE -> Matter A
        db.insert_pattern(matter_a, app_pattern="WINWORD.EXE", confidence_score=0.9)

        # User correction: same app but different matter
        db.record_correction_with_contradiction(
            correct_matter_id=matter_b,
            app="WINWORD.EXE"
        )

        # Old pattern confidence should decrease
        patterns_a = db.get_patterns_for_matter(matter_a)
        assert patterns_a[0]['confidence_score'] < 0.9
        assert patterns_a[0]['correction_count'] > 0

        # New pattern for matter B should exist
        patterns_b = db.get_patterns_for_matter(matter_b)
        assert len(patterns_b) == 1
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_categorization_patterns.py::test_contradicting_correction_decreases_confidence -v
```
Expected output: `FAILED`

**Step 3 - GREEN:** Add contradiction handling
```python
# src/syncopaid/database_patterns.py (ADD to PatternsDatabaseMixin class)

    def record_correction_with_contradiction(
        self,
        correct_matter_id: int,
        app: Optional[str] = None,
        url: Optional[str] = None,
        title: Optional[str] = None
    ) -> int:
        """
        Record a user correction that may contradict existing patterns.

        This is the primary method for handling user corrections. It:
        1. Finds any existing patterns that match these attributes
        2. Decreases confidence of patterns pointing to OTHER matters
        3. Creates/reinforces pattern for the correct matter

        Args:
            correct_matter_id: The matter user selected as correct
            app: Application name of the activity
            url: URL of the activity (if any)
            title: Window title of the activity

        Returns:
            ID of the created or reinforced pattern
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()

            # Find existing patterns that match these attributes but point elsewhere
            contradicting_patterns = []
            if app:
                cursor.execute("""
                    SELECT id, confidence_score, correction_count
                    FROM categorization_patterns
                    WHERE app_pattern = ? AND matter_id != ? AND is_archived = 0
                """, (app, correct_matter_id))
                contradicting_patterns.extend(cursor.fetchall())

            # Decrease confidence of contradicting patterns
            for pattern_id, confidence, corrections in contradicting_patterns:
                new_confidence = max(0.1, confidence - 0.1)  # Min 0.1
                new_corrections = corrections + 1
                cursor.execute("""
                    UPDATE categorization_patterns
                    SET confidence_score = ?, correction_count = ?, last_used_at = ?
                    WHERE id = ?
                """, (new_confidence, new_corrections, now, pattern_id))
                logging.info(f"Decreased confidence of pattern {pattern_id} to {new_confidence:.2f}")

            conn.commit()

        # Now record the correct pattern (will create or reinforce)
        return self.record_correction(correct_matter_id, app, url, title)
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_categorization_patterns.py -v
```
Expected output: All tests `PASSED`

**Step 5 - COMMIT:**
```bash
git add src/syncopaid/database_patterns.py tests/test_categorization_patterns.py && git commit -m "feat: add confidence adjustment for contradicting corrections"
```

---

## Final Verification

Run after all tasks complete:
```bash
python -m pytest tests/test_categorization_patterns.py -v  # All pattern tests pass
python -m pytest tests/test_database.py -v                  # Database tests pass
```

## Rollback

If issues arise: `git log --oneline -5` to find commit, then `git revert <hash>`

## Notes

- This is sub-plan B of 3 (027A, 027B, 027C)
- Confidence scores range from 0.1 (very low) to 1.0 (certain)
- record_correction_with_contradiction is the primary method for UI integration

## Dependencies

- Requires sub-plan 027A completed
- Future: Story 15.5 (Review and Correction Interface) will call record_correction_with_contradiction()
