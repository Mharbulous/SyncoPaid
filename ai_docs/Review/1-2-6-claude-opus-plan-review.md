# Plan Review: Screenshot Retention & Cleanup Policy (1-2-6)

**Plan File:** `ai_docs/Plans/1-2-6-screenshot-retention-cleanup.md`
**Reviewer:** Claude Opus 4.5
**Review Date:** 2025-12-16

---

## Overall Assessment: Good plan with some issues to address

---

## Strengths

1. **Clear TDD structure** - Each task follows RED → GREEN → COMMIT cycle properly
2. **Well-scoped tasks** - 8 focused tasks that build on each other
3. **Good test examples** - Concrete test code with clear assertions
4. **Acceptance criteria mapped** - All AC items are checked and covered
5. **Edge cases documented** - Empty folders, malformed names, etc.

---

## Issues & Concerns

### Issue 1: One-clear-month logic has edge case bug

The cutoff calculation in Task 1:
```python
cutoff = (reference_date.replace(day=1) - timedelta(days=1)).replace(day=1)
```
On Dec 16, this yields Nov 1 cutoff. But the requirement says "on Dec 1, archive October" (i.e., skip November entirely). The test case expects Oct folders to be archivable on Dec 16, which is **TWO** clear months, not one.

**Recommendation:** Clarify: Is the intent "one clear month" (Nov archivable on Dec 16) or "two clear months" (only Oct archivable)?

---

### Issue 2: Error dialog oversimplified

Task 6 spec says retry options: "Now / 5 minutes / 1 hour / Tomorrow / Next startup" but the implementation only uses `askretrycancel()` which gives 2 options (Retry/Cancel).

**Recommendation:** Use a custom dialog or `askquestion()` with actual 5 options as specified in AC.

---

### Issue 3: Missing file types in zip creation

```python
for file in folder_path.rglob("*.jpg"):
```
This only zips JPG files. Screenshots might be PNG or other formats depending on capture settings.

**Recommendation:** Use `rglob("*")` or explicitly handle all image types.

---

### Issue 4: Thread safety concern

`last_run_date` is accessed from multiple threads without locking:
- Main thread sets it in `run_once()`
- Background thread reads it in `_background_loop()`

**Recommendation:** Add `threading.Lock` or use thread-safe approach.

---

### Issue 5: Test for Task 5 is incomplete

```python
def test_archive_worker_startup():
    archiver = ArchiveWorker(screenshot_dir, archive_dir)
    archiver.run_once()
    assert mock_archive_month.called  # mock_archive_month undefined!
```
The mock is referenced but never created.

**Recommendation:** Add proper mocker setup or fixture.

---

### Issue 6: Config not integrated

Task 8 adds config options but Tasks 5/7 don't use `config.archive_enabled` or `archive_check_interval_hours`. The archiver will run regardless of config settings.

**Recommendation:** Add Task 8.5 to wire config into ArchiveWorker.

---

## Missing Items

| Item | Severity |
|------|----------|
| No handling for existing partial zip (resume interrupted archive) | Medium |
| No logging of archive sizes/compression ratios | Low |
| No progress indication for large archives | Low |
| Integration test doesn't verify background scheduler | Medium |

---

## Suggested Task Order Change

Current order is logical, but consider:
- Move **Task 8 (Config)** earlier (after Task 1) so archiver respects `archive_enabled` from the start
- Add task to verify config integration before final verification

---

## Verdict

| Category | Rating |
|----------|--------|
| Completeness | 7/10 |
| Technical Accuracy | 6/10 |
| TDD Quality | 8/10 |
| Implementation Readiness | 6/10 |

**Recommendation:** Address the 6 issues above before implementation. The one-clear-month logic and error dialog need clarification/rework. Otherwise solid plan structure.
