# Narrative & Reporting - Integration Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 8.7 | **Created:** 2025-12-24 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Verify that narrative generation and review interface work together as a complete billing workflow, enabling lawyers to generate AI-powered billing narratives from tracked activities and review/correct them before finalization.

**Approach:** Create integration tests that exercise the complete narrative-to-review workflow across child story implementations (8.7.1 and 8.7.2). Validate that activities are grouped, narratives are generated following legal billing conventions, and the review UI allows editing/splitting/merging before export.

**Tech Stack:** Python pytest, src/syncopaid/narrative_generator.py, src/syncopaid/review_ui.py, existing billing.py and llm.py

---

## Story Context

**Title:** Narrative & Reporting
**Description:** Intelligent narrative generation and review interface

**Parent Story Completion Criteria:**
- [ ] All child stories (8.7.1, 8.7.2) are verified/implemented
- [ ] Integration tests pass for complete workflow
- [ ] Activity → Narrative → Review → Export pipeline works end-to-end

**Child Stories:**
| ID | Title | Status | Notes |
|----|-------|--------|-------|
| 8.7.1 | Intelligent Narrative Generation | active | Core narrative AI |
| 8.7.2 | Review and Correction Interface | active | UI for review |

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`
- [ ] Child stories 8.7.1 and 8.7.2 are at least 'implemented' stage

## Files Affected

| File | Change Type | Purpose |
|------|-------------|---------|
| `tests/integration/test_narrative_review_workflow.py` | Create | Integration tests for complete workflow |
| `src/syncopaid/narrative_generator.py` | Verify | Ensure ActivityGroup and NarrativeGenerator exist |
| `src/syncopaid/review_ui.py` | Verify | Ensure BillingEntryReview and split/merge work |
| `src/syncopaid/billing.py` | Verify | Ensure integration points exist |

## TDD Tasks

### Task 1: Create Integration Test Framework (~3 min)

**Files:**
- Create: `tests/integration/test_narrative_review_workflow.py`

**Context:** Set up the integration test file that will exercise the complete narrative-to-review workflow. This establishes the testing infrastructure for validating both child stories work together.

**Step 1 - RED:** Write failing test

```python
# tests/integration/test_narrative_review_workflow.py
"""Integration tests for narrative generation and review workflow."""
import pytest
from syncopaid.narrative_generator import ActivityGroup, NarrativeGenerator
from syncopaid.review_ui import BillingEntryReview


def test_activity_group_to_billing_entry():
    """ActivityGroup can be converted to BillingEntryReview for the review UI."""
    # Create an activity group (from 8.7.1)
    group = ActivityGroup(
        matter_code="SMITH-2024-001",
        activities=[
            {"app": "Outlook", "title": "RE: Settlement Offer", "timestamp": "2024-01-15T10:00:00"},
            {"app": "Outlook", "title": "RE: Settlement Offer", "timestamp": "2024-01-15T10:05:00"},
        ],
        total_minutes=12,
        activity_type="correspondence"
    )

    # Convert to billing entry for review (integration point)
    entry = BillingEntryReview.from_activity_group(
        group,
        narrative="Correspondence with opposing counsel re: settlement negotiations",
        event_ids=[1, 2],
        confidence=0.85
    )

    assert entry.matter_code == "SMITH-2024-001"
    assert entry.narrative == "Correspondence with opposing counsel re: settlement negotiations"
    assert entry.time_minutes == 12
    assert entry.confidence == 0.85
```

**Step 2 - Verify RED:**
```bash
pytest tests/integration/test_narrative_review_workflow.py::test_activity_group_to_billing_entry -v
```
Expected output: `FAILED` (from_activity_group method does not exist yet)

**Step 3 - GREEN:** Add factory method to BillingEntryReview

```python
# In src/syncopaid/review_ui.py - add to BillingEntryReview class
@classmethod
def from_activity_group(cls, group, narrative: str, event_ids: list, confidence: float = 0.0):
    """Create a BillingEntryReview from a NarrativeGenerator ActivityGroup."""
    from .narrative_generator import ActivityGroup
    return cls(
        event_ids=event_ids,
        matter_code=group.matter_code,
        matter_name=None,  # Lookup separately if needed
        narrative=narrative,
        time_minutes=group.total_minutes,
        start_time=group.activities[0].get("timestamp") if group.activities else None,
        end_time=group.activities[-1].get("timestamp") if group.activities else None,
        confidence=confidence
    )
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/integration/test_narrative_review_workflow.py::test_activity_group_to_billing_entry -v
```
Expected: `PASSED`

---

### Task 2: Test Narrative Generator to Review Pipeline (~5 min)

**Files:**
- Modify: `tests/integration/test_narrative_review_workflow.py`

**Context:** Verify that the NarrativeGenerator can produce output that the ReviewUI can consume. This tests the complete handoff between the two child stories.

**Step 1 - RED:** Write failing test

```python
# tests/integration/test_narrative_review_workflow.py (add to existing file)
from syncopaid.database import Database
from unittest.mock import MagicMock


def test_narrative_generator_produces_reviewable_entries():
    """NarrativeGenerator output is compatible with ReviewUI."""
    # Mock database with activity events
    mock_db = MagicMock(spec=Database)
    mock_db.query_events_by_date_range.return_value = [
        {"id": 1, "app": "Outlook", "title": "RE: Contract Review", "timestamp": "2024-01-15T09:00:00", "matter_code": "JONES-2024"},
        {"id": 2, "app": "Outlook", "title": "RE: Contract Review", "timestamp": "2024-01-15T09:15:00", "matter_code": "JONES-2024"},
        {"id": 3, "app": "Word", "title": "Contract_v2.docx", "timestamp": "2024-01-15T09:30:00", "matter_code": "JONES-2024"},
    ]

    # Use NarrativeGenerator to group and generate narratives
    generator = NarrativeGenerator(db=mock_db)
    entries = generator.generate_billing_entries(date="2024-01-15")

    # Verify entries are valid for ReviewUI
    assert len(entries) > 0
    for entry in entries:
        assert isinstance(entry, BillingEntryReview)
        assert entry.narrative is not None
        assert entry.time_minutes > 0
        assert len(entry.event_ids) > 0
```

**Step 2 - Verify RED:**
```bash
pytest tests/integration/test_narrative_review_workflow.py::test_narrative_generator_produces_reviewable_entries -v
```
Expected: `FAILED` (NarrativeGenerator.generate_billing_entries may not exist)

**Step 3 - GREEN:** Implement integration method in NarrativeGenerator

```python
# In src/syncopaid/narrative_generator.py
def generate_billing_entries(self, date: str) -> list:
    """
    Generate billing entries for review from a specific date's activities.

    Args:
        date: Date string in YYYY-MM-DD format

    Returns:
        List of BillingEntryReview objects ready for the review UI
    """
    from .review_ui import BillingEntryReview

    # Query activities for the date
    events = self.db.query_events_by_date_range(date, date)

    # Group related activities
    groups = self.group_activities(events)

    # Generate narratives and convert to review entries
    entries = []
    for group in groups:
        narrative = self.generate_narrative(group)
        entry = BillingEntryReview.from_activity_group(
            group,
            narrative=narrative,
            event_ids=[e["id"] for e in group.activities],
            confidence=self._calculate_confidence(group)
        )
        entries.append(entry)

    return entries
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/integration/test_narrative_review_workflow.py::test_narrative_generator_produces_reviewable_entries -v
```
Expected: `PASSED`

---

### Task 3: Test Split Entry Workflow (~4 min)

**Files:**
- Modify: `tests/integration/test_narrative_review_workflow.py`

**Context:** Verify that entries can be split in the review UI, a key workflow for lawyers who need to bill different portions of time to different matters.

**Step 1 - RED:** Write failing test

```python
# tests/integration/test_narrative_review_workflow.py (add to existing file)
def test_split_entry_creates_two_reviewable_entries():
    """Splitting an entry produces two valid BillingEntryReview objects."""
    original = BillingEntryReview(
        event_ids=[1, 2, 3, 4],
        matter_code="SMITH-2024-001",
        narrative="Research and drafting for estate plan",
        time_minutes=60,
        start_time="2024-01-15T09:00:00",
        end_time="2024-01-15T10:00:00",
        confidence=0.8
    )

    # Split into two entries
    entry1, entry2 = original.split(
        split_point=2,  # After event_id 2
        narrative1="Research estate tax implications",
        narrative2="Draft trust amendment",
        time_split=(24, 36)  # 24 min and 36 min
    )

    # Verify both entries are valid
    assert entry1.event_ids == [1, 2]
    assert entry2.event_ids == [3, 4]
    assert entry1.time_minutes == 24
    assert entry2.time_minutes == 36
    assert entry1.narrative == "Research estate tax implications"
    assert entry2.narrative == "Draft trust amendment"
    assert entry1.matter_code == "SMITH-2024-001"
    assert entry2.matter_code == "SMITH-2024-001"
```

**Step 2 - Verify RED:**
```bash
pytest tests/integration/test_narrative_review_workflow.py::test_split_entry_creates_two_reviewable_entries -v
```
Expected: `FAILED` (split method may not exist or have wrong signature)

**Step 3 - GREEN:** Ensure split method works correctly

```python
# In src/syncopaid/review_ui.py - verify BillingEntryReview.split exists
def split(self, split_point: int, narrative1: str, narrative2: str,
          time_split: tuple) -> tuple:
    """
    Split this entry into two separate entries.

    Args:
        split_point: Index in event_ids where to split
        narrative1: Narrative for first entry
        narrative2: Narrative for second entry
        time_split: Tuple of (minutes1, minutes2)

    Returns:
        Tuple of two new BillingEntryReview objects
    """
    entry1 = BillingEntryReview(
        event_ids=self.event_ids[:split_point],
        matter_code=self.matter_code,
        matter_name=self.matter_name,
        narrative=narrative1,
        time_minutes=time_split[0],
        start_time=self.start_time,
        end_time=None,  # Will be calculated
        confidence=self.confidence
    )
    entry2 = BillingEntryReview(
        event_ids=self.event_ids[split_point:],
        matter_code=self.matter_code,
        matter_name=self.matter_name,
        narrative=narrative2,
        time_minutes=time_split[1],
        start_time=None,  # Will be calculated
        end_time=self.end_time,
        confidence=self.confidence
    )
    return entry1, entry2
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/integration/test_narrative_review_workflow.py::test_split_entry_creates_two_reviewable_entries -v
```
Expected: `PASSED`

---

### Task 4: Test Merge Entries Workflow (~4 min)

**Files:**
- Modify: `tests/integration/test_narrative_review_workflow.py`

**Context:** Verify that multiple entries can be merged in the review UI, allowing lawyers to combine related activities that were incorrectly split.

**Step 1 - RED:** Write failing test

```python
# tests/integration/test_narrative_review_workflow.py (add to existing file)
def test_merge_entries_combines_into_one():
    """Merging entries produces a single valid BillingEntryReview."""
    entry1 = BillingEntryReview(
        event_ids=[1, 2],
        matter_code="SMITH-2024-001",
        narrative="Phone call with client",
        time_minutes=18,
        confidence=0.9
    )
    entry2 = BillingEntryReview(
        event_ids=[3],
        matter_code="SMITH-2024-001",
        narrative="Email follow-up",
        time_minutes=6,
        confidence=0.85
    )

    # Merge the entries
    merged = BillingEntryReview.merge(
        [entry1, entry2],
        narrative="Client communication regarding estate planning conference call and follow-up"
    )

    assert merged.event_ids == [1, 2, 3]
    assert merged.time_minutes == 24
    assert merged.matter_code == "SMITH-2024-001"
    assert "Client communication" in merged.narrative
```

**Step 2 - Verify RED:**
```bash
pytest tests/integration/test_narrative_review_workflow.py::test_merge_entries_combines_into_one -v
```
Expected: `FAILED` (merge class method may not exist)

**Step 3 - GREEN:** Ensure merge class method works

```python
# In src/syncopaid/review_ui.py - verify BillingEntryReview.merge exists
@classmethod
def merge(cls, entries: list, narrative: str):
    """
    Merge multiple entries into a single entry.

    Args:
        entries: List of BillingEntryReview objects to merge
        narrative: Combined narrative for merged entry

    Returns:
        New BillingEntryReview with combined data
    """
    if not entries:
        raise ValueError("Cannot merge empty list of entries")

    all_event_ids = []
    total_minutes = 0
    for entry in entries:
        all_event_ids.extend(entry.event_ids)
        total_minutes += entry.time_minutes

    # Use matter from first entry (should all be same)
    return cls(
        event_ids=all_event_ids,
        matter_code=entries[0].matter_code,
        matter_name=entries[0].matter_name,
        narrative=narrative,
        time_minutes=total_minutes,
        start_time=entries[0].start_time,
        end_time=entries[-1].end_time,
        confidence=min(e.confidence for e in entries)  # Conservative
    )
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/integration/test_narrative_review_workflow.py::test_merge_entries_combines_into_one -v
```
Expected: `PASSED`

---

### Task 5: End-to-End Workflow Test (~5 min)

**Files:**
- Modify: `tests/integration/test_narrative_review_workflow.py`

**Context:** Create a comprehensive test that exercises the entire workflow: activity grouping → narrative generation → review/edit → approval → export-ready format.

**Step 1 - RED:** Write failing test

```python
# tests/integration/test_narrative_review_workflow.py (add to existing file)
def test_full_workflow_activities_to_approved_entries():
    """Complete workflow from raw activities to approved billing entries."""
    # Simulate a day's activities
    raw_activities = [
        {"id": 1, "app": "Outlook", "title": "RE: Discovery Requests", "timestamp": "2024-01-15T09:00:00", "matter_code": "JONES-2024", "duration_mins": 5},
        {"id": 2, "app": "Outlook", "title": "RE: Discovery Requests", "timestamp": "2024-01-15T09:10:00", "matter_code": "JONES-2024", "duration_mins": 8},
        {"id": 3, "app": "Word", "title": "Response to Discovery.docx", "timestamp": "2024-01-15T09:20:00", "matter_code": "JONES-2024", "duration_mins": 45},
        {"id": 4, "app": "Chrome", "title": "Legal Research - Westlaw", "timestamp": "2024-01-15T10:30:00", "matter_code": "SMITH-2024", "duration_mins": 30},
    ]

    # Mock database
    mock_db = MagicMock(spec=Database)
    mock_db.query_events_by_date_range.return_value = raw_activities

    # Step 1: Generate entries
    generator = NarrativeGenerator(db=mock_db)
    entries = generator.generate_billing_entries(date="2024-01-15")

    # Should group by matter
    jones_entries = [e for e in entries if e.matter_code == "JONES-2024"]
    smith_entries = [e for e in entries if e.matter_code == "SMITH-2024"]

    assert len(jones_entries) >= 1  # Email + Word grouped or separate
    assert len(smith_entries) == 1  # Research alone

    # Step 2: Review and approve
    for entry in entries:
        entry.status = "approved"

    # Step 3: Verify export-ready format
    for entry in entries:
        assert entry.status == "approved"
        assert entry.matter_code is not None
        assert entry.narrative is not None
        assert entry.time_minutes > 0
        assert entry.time_hours > 0  # Calculated property
```

**Step 2 - Verify RED:**
```bash
pytest tests/integration/test_narrative_review_workflow.py::test_full_workflow_activities_to_approved_entries -v
```
Expected: `FAILED` (various integration issues)

**Step 3 - GREEN:** Fix any integration issues discovered

This test may reveal integration gaps between 8.7.1 and 8.7.2 implementations. Fix them iteratively.

**Step 4 - Verify GREEN:**
```bash
pytest tests/integration/test_narrative_review_workflow.py -v
```
Expected: All tests `PASSED`

---

### Task 6: Verify All Integration Tests Pass (~2 min)

**Files:**
- `tests/integration/test_narrative_review_workflow.py`

**Context:** Final verification that all integration tests pass and the complete workflow is functional.

**Commands:**
```bash
# Run all integration tests
pytest tests/integration/test_narrative_review_workflow.py -v

# Run full test suite to ensure no regressions
python -m pytest -v
```

**Expected:** All tests pass. If any fail, investigate and fix before marking complete.

---

## Final Checklist

- [ ] All 6 tasks completed
- [ ] Integration tests pass: `pytest tests/integration/test_narrative_review_workflow.py -v`
- [ ] Full test suite passes: `python -m pytest -v`
- [ ] Child stories 8.7.1 and 8.7.2 are at 'implemented' or 'verifying' stage
- [ ] Narrative → Review → Export pipeline works end-to-end

## Definition of Done

Story 8.7 is complete when:
1. Both child stories (8.7.1, 8.7.2) are verified
2. Integration tests demonstrate cohesive workflow
3. A lawyer can: generate narratives from activities, review/edit in UI, split/merge as needed, approve and export
