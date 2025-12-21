# Context Extraction: Tracker Integration - Implementation Plan

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

**Goal:** Integrate context extraction into tracker.py to populate ActivityEvent.url field.
**Approach:** Import extract_context, call in get_active_window(), add to state dict, include in ActivityEvent.
**Tech Stack:** Existing tracker.py, context_extraction.py module

---

**Story ID:** 1.6.5 | **Created:** 2025-12-21 | **Stage:** `planned`

---

## Story Context

**Title:** Tracker Integration for Context Extraction

**Description:** **As a** lawyer using AI to categorize my time
**I want** extracted context automatically included in activity events
**So that** the AI has rich data for accurate matter matching

**Acceptance Criteria:**
- [ ] get_active_window() returns 'url' key with extracted context
- [ ] TrackerLoop state dict includes url field
- [ ] ActivityEvent includes extracted context in url field
- [ ] Debug logging for extraction attempts

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Story 1.6.4 (unified extract_context) completed
- [ ] `src/syncopaid/context_extraction.py` has extract_context function

## TDD Tasks

### Task 1: Integrate context extraction into get_active_window (~3 min)

**Files:**
- **Modify:** `test_context_extraction.py` (append integration test)
- **Modify:** `src/syncopaid/tracker.py` (lines 129-171, get_active_window function)

**Context:** Import extract_context and call it in get_active_window() to populate a 'url' key in the returned dict.

**Step 1 - RED:** Write failing integration test
```python
# test_context_extraction.py (add to end of file)

def test_integration_get_active_window_populates_url():
    """Test that get_active_window includes extracted context in 'url' field."""
    from syncopaid.tracker import get_active_window

    # Note: This will return mock data on non-Windows platforms
    result = get_active_window()

    # Verify the result includes 'url' key (may be None)
    assert 'url' in result
    assert isinstance(result.get('url'), (str, type(None)))
    print("Integration test passed: get_active_window includes 'url' field")

# Update main block
if __name__ == "__main__":
    print("Running context extraction tests...")
    # ... existing tests ...
    test_integration_get_active_window_populates_url()
    print("All tests passed!")
```

**Step 2 - Verify RED:**
```bash
python test_context_extraction.py
```
Expected output: Test fails because 'url' key missing from get_active_window result

**Step 3 - GREEN:** Integrate into tracker.py
```python
# src/syncopaid/tracker.py
# Find the imports section (around line 1-20) and add:
from syncopaid.context_extraction import extract_context

# Then modify get_active_window function return statements to include url:
# In the mock data section (non-Windows):
        url = extract_context(app, title)
        return {"app": app, "title": title, "pid": 0, "url": url}

# In the Windows section, before the return:
        # Extract contextual information
        url = extract_context(process, title)
        return {"app": process, "title": title, "pid": pid, "url": url}

# In the exception handler:
        return {"app": None, "title": None, "pid": None, "url": None}
```

**Step 4 - Verify GREEN:**
```bash
python test_context_extraction.py
```
Expected output: `All tests passed!`

**Step 5 - COMMIT:**
```bash
git add test_context_extraction.py src/syncopaid/tracker.py && git commit -m "feat: integrate context extraction into get_active_window"
```

---

### Task 2: Add url to TrackerLoop state dict (~2 min)

**Files:**
- **Modify:** `src/syncopaid/tracker.py` (lines 270-283, state dict construction)

**Context:** TrackerLoop.start() creates state dict from window info. Add 'url' field so it flows through to ActivityEvent.

**Step 1 - RED:** Verify current behavior
```bash
python -m syncopaid.tracker
```
Expected: Tracker runs for 30s, prints events. Check if 'url' field appears in output.

**Step 2 - GREEN:** Add url to state dict
```python
# src/syncopaid/tracker.py
# Find the state dict creation around line 275-282 in TrackerLoop.start()
# Change to:

                state = {
                    'app': window['app'],
                    'title': window['title'],
                    'url': window.get('url'),  # Extracted context (URL, subject, or filepath)
                    'is_idle': is_idle
                }
```

**Step 3 - Verify GREEN:**
```bash
python -m syncopaid.tracker
```
Expected: Tracker runs, events now show url field populated when context is extracted.

**Step 4 - COMMIT:**
```bash
git add src/syncopaid/tracker.py && git commit -m "feat: include url field in TrackerLoop state dict"
```

---

### Task 3: Add debug logging for extraction (~2 min)

**Files:**
- **Modify:** `src/syncopaid/tracker.py` (in get_active_window function)

**Context:** Log when context extraction is attempted and results, to help debug parsing issues.

**Step 1 - GREEN:** Add debug logging
```python
# src/syncopaid/tracker.py
# Update get_active_window function where extract_context is called:

        # Extract contextual information
        url = extract_context(process, title)
        if url:
            logging.debug(f"Extracted context from {process}: {url[:50]}...")
        elif process and title:
            logging.debug(f"No context extracted from {process}: {title[:50]}...")
```

**Step 2 - Verify GREEN:**
```bash
python -c "import logging; logging.basicConfig(level=logging.DEBUG); from syncopaid.tracker import get_active_window; print(get_active_window())"
```
Expected: Debug logs show extraction attempts and results.

**Step 3 - COMMIT:**
```bash
git add src/syncopaid/tracker.py && git commit -m "feat: add debug logging for context extraction"
```

---

## Final Verification

Run after all tasks complete:
```bash
python test_context_extraction.py    # All unit tests pass
python -m syncopaid.tracker          # Tracker runs, url field populated
```

**Manual verification:**
1. Open Chrome and navigate to a URL → verify URL extracted
2. Open Outlook with an email → verify subject extracted
3. Open Word with a document → verify filepath extracted

## Rollback

If issues arise: `git log --oneline -10` to find commits, revert in reverse order.

## Notes

**Dependencies:**
- Requires Story 1.6.4 (unified extract_context function) completed
- This completes the Enhanced Context Extraction feature (Story 1.6)
