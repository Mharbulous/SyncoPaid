# Review and Correction Interface - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 8.7.2 | **Created:** 2025-12-24 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test -> verify RED -> Write code -> verify GREEN -> Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Enable lawyers to review, edit, split, merge, and approve AI-generated billing entries before finalizing them for billing export.

**Approach:** Enhance the existing `review_ui.py` skeleton to provide a full-featured review interface that displays AI-generated billing entries from the narrative generator (8.7.1), allows editing matter/narrative/time, supports splitting one entry into multiple and merging multiple into one, and tracks review status in the database.

**Tech Stack:** tkinter/ttk for UI, existing `Database` class, `BillingEntry` from `narrative_generator.py`, SQLite for review status tracking

---

## Story Context

**Title:** Review and Correction Interface
**Description:** As a lawyer who needs billing accuracy, I want to review AI-generated time entries before they're finalized, so that I can correct mistakes and ensure privilege-appropriate descriptions.

**Acceptance Criteria:**
- [ ] Shows list of AI-generated entries for selected date range
- [ ] Each entry displays: time period, client/matter suggestion, draft narrative, confidence level
- [ ] Can edit: client/matter, narrative, time duration
- [ ] Can split one entry into multiple
- [ ] Can merge multiple entries into one
- [ ] Can delete entries (non-billable time)
- [ ] Can mark entries as reviewed/approved

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`
- [ ] Story 8.7.1 (Intelligent Narrative Generation) should be complete for full integration, but this UI can be developed independently with mock data

## Files Affected

| File | Change Type | Purpose |
|------|-------------|---------|
| `tests/test_review_ui.py` | Create | Unit tests for review interface |
| `src/syncopaid/review_ui.py` | Modify | Enhanced review dialog with full functionality |
| `src/syncopaid/database_operations_review.py` | Create | Database operations for review status |
| `src/syncopaid/tray.py` | Modify | Add menu item to launch review dialog |

## TDD Tasks

### Task 1: Add BillingEntryReview Dataclass (~3 min)

**Files:**
- Modify: `tests/test_review_ui.py` (create)
- Modify: `src/syncopaid/review_ui.py`

**Context:** The existing `ReviewEntry` class is too simple. We need a richer `BillingEntryReview` dataclass that includes confidence level, time period (start/end), and status tracking. This becomes the core data structure for the review workflow.

**Step 1 - RED:** Write failing test

```python
# tests/test_review_ui.py
"""Tests for billing entry review interface."""
import pytest
from syncopaid.review_ui import BillingEntryReview


def test_billing_entry_review_creation():
    """BillingEntryReview holds complete entry data for review."""
    entry = BillingEntryReview(
        event_ids=[1, 2, 3],
        matter_code="SMITH-2024-001",
        matter_name="Smith Estate Planning",
        narrative="Review correspondence re: estate tax",
        time_minutes=18,
        start_time="2024-01-15T10:00:00",
        end_time="2024-01-15T10:18:00",
        confidence=0.85
    )

    assert entry.matter_code == "SMITH-2024-001"
    assert entry.matter_name == "Smith Estate Planning"
    assert entry.time_minutes == 18
    assert entry.time_hours == 0.3  # Calculated property
    assert entry.confidence == 0.85
    assert entry.status is None  # Not yet reviewed
    assert len(entry.event_ids) == 3


def test_billing_entry_review_defaults():
    """BillingEntryReview has sensible defaults."""
    entry = BillingEntryReview(
        event_ids=[1],
        narrative="Draft document"
    )

    assert entry.matter_code is None
    assert entry.matter_name is None
    assert entry.time_minutes == 0
    assert entry.confidence == 0.0
    assert entry.status is None
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_review_ui.py::test_billing_entry_review_creation -v
```
Expected output: `FAILED` (cannot import name 'BillingEntryReview')

**Step 3 - GREEN:** Write minimal implementation

```python
# src/syncopaid/review_ui.py (replace the ReviewEntry class at top)
"""Review UI for AI-generated billing entries."""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass, field
from .database import Database
from .billing import minutes_to_hours


@dataclass
class BillingEntryReview:
    """A billing entry pending review with full context.

    Attributes:
        event_ids: Source event IDs included in this entry
        matter_code: Client/matter code for billing
        matter_name: Human-readable matter name
        narrative: AI-generated billing narrative
        time_minutes: Duration in minutes (rounded to billing increment)
        start_time: ISO timestamp of activity start
        end_time: ISO timestamp of activity end
        confidence: AI confidence score (0.0-1.0)
        status: Review status ('approved', 'edited', 'deleted', None)
    """
    event_ids: List[int] = field(default_factory=list)
    matter_code: Optional[str] = None
    matter_name: Optional[str] = None
    narrative: str = ""
    time_minutes: int = 0
    start_time: str = ""
    end_time: str = ""
    confidence: float = 0.0
    status: Optional[str] = None

    @property
    def time_hours(self) -> float:
        """Convert minutes to decimal hours for billing."""
        return minutes_to_hours(self.time_minutes)


# Keep the old ReviewEntry for backwards compatibility
class ReviewEntry:
    """A billing entry pending review (legacy class)."""

    def __init__(self, event_id: int, matter: str, narrative: str, time_hours: float):
        self.event_id = event_id
        self.matter = matter
        self.narrative = narrative
        self.time_hours = time_hours
        self.status: Optional[str] = None  # 'approved', 'edited', 'skipped'
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_review_ui.py -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_review_ui.py src/syncopaid/review_ui.py && git commit -m "feat(review): add BillingEntryReview dataclass with confidence and time period"
```

---

### Task 2: Add Entry Edit Functionality (~4 min)

**Files:**
- Modify: `tests/test_review_ui.py`
- Modify: `src/syncopaid/review_ui.py`

**Context:** Users need to edit matter, narrative, and time duration. We add methods to `BillingEntryReview` that validate edits and track when edits occur.

**Step 1 - RED:** Write failing test

```python
# tests/test_review_ui.py (append to file)

def test_entry_edit_matter():
    """Can edit matter code and name."""
    entry = BillingEntryReview(
        event_ids=[1],
        matter_code="OLD-001",
        matter_name="Old Matter",
        narrative="Work done"
    )

    entry.update_matter("NEW-002", "New Matter")

    assert entry.matter_code == "NEW-002"
    assert entry.matter_name == "New Matter"
    assert entry.status == "edited"


def test_entry_edit_narrative():
    """Can edit narrative text."""
    entry = BillingEntryReview(
        event_ids=[1],
        narrative="Original narrative"
    )

    entry.update_narrative("Edited narrative with more detail")

    assert entry.narrative == "Edited narrative with more detail"
    assert entry.status == "edited"


def test_entry_edit_time():
    """Can edit time duration."""
    entry = BillingEntryReview(
        event_ids=[1],
        time_minutes=18
    )

    entry.update_time(30)

    assert entry.time_minutes == 30
    assert entry.time_hours == 0.5
    assert entry.status == "edited"


def test_entry_approve():
    """Can approve an entry."""
    entry = BillingEntryReview(event_ids=[1], narrative="Work")

    entry.approve()

    assert entry.status == "approved"


def test_entry_delete():
    """Can mark entry as deleted (non-billable)."""
    entry = BillingEntryReview(event_ids=[1], narrative="Lunch break")

    entry.mark_deleted()

    assert entry.status == "deleted"
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_review_ui.py::test_entry_edit_matter -v
```
Expected output: `FAILED` (AttributeError: 'BillingEntryReview' object has no attribute 'update_matter')

**Step 3 - GREEN:** Write minimal implementation

```python
# src/syncopaid/review_ui.py (add methods to BillingEntryReview class after time_hours property)

    def update_matter(self, code: Optional[str], name: Optional[str] = None) -> None:
        """Update matter code and name, marking as edited."""
        self.matter_code = code
        self.matter_name = name
        self.status = "edited"

    def update_narrative(self, narrative: str) -> None:
        """Update narrative text, marking as edited."""
        self.narrative = narrative
        self.status = "edited"

    def update_time(self, minutes: int) -> None:
        """Update time duration in minutes, marking as edited."""
        self.time_minutes = minutes
        self.status = "edited"

    def approve(self) -> None:
        """Mark entry as approved."""
        self.status = "approved"

    def mark_deleted(self) -> None:
        """Mark entry as deleted (non-billable time)."""
        self.status = "deleted"
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_review_ui.py -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_review_ui.py src/syncopaid/review_ui.py && git commit -m "feat(review): add edit, approve, and delete methods to BillingEntryReview"
```

---

### Task 3: Add Entry Split Functionality (~4 min)

**Files:**
- Modify: `tests/test_review_ui.py`
- Modify: `src/syncopaid/review_ui.py`

**Context:** Lawyers often need to split one activity into multiple billing entries (e.g., split 30 min of "general work" into 12 min for Client A and 18 min for Client B). The split function creates new entries from an existing one.

**Step 1 - RED:** Write failing test

```python
# tests/test_review_ui.py (append to file)

def test_entry_split_two_ways():
    """Can split entry into two parts."""
    original = BillingEntryReview(
        event_ids=[1, 2],
        matter_code="MIXED-001",
        narrative="Work on multiple matters",
        time_minutes=30,
        start_time="2024-01-15T10:00:00",
        end_time="2024-01-15T10:30:00"
    )

    parts = original.split([
        {"matter_code": "CLIENT-A", "matter_name": "Client A Matter", "time_minutes": 12, "narrative": "Work for Client A"},
        {"matter_code": "CLIENT-B", "matter_name": "Client B Matter", "time_minutes": 18, "narrative": "Work for Client B"},
    ])

    assert len(parts) == 2
    assert parts[0].matter_code == "CLIENT-A"
    assert parts[0].time_minutes == 12
    assert parts[1].matter_code == "CLIENT-B"
    assert parts[1].time_minutes == 18
    # Original event_ids shared across splits
    assert parts[0].event_ids == [1, 2]
    assert parts[1].event_ids == [1, 2]
    # Original marked as split
    assert original.status == "split"


def test_entry_split_validates_total_time():
    """Split parts must not exceed original time."""
    original = BillingEntryReview(
        event_ids=[1],
        time_minutes=30
    )

    with pytest.raises(ValueError, match="exceeds original"):
        original.split([
            {"time_minutes": 20, "narrative": "Part 1"},
            {"time_minutes": 20, "narrative": "Part 2"},  # 40 > 30
        ])
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_review_ui.py::test_entry_split_two_ways -v
```
Expected output: `FAILED` (AttributeError: 'BillingEntryReview' object has no attribute 'split')

**Step 3 - GREEN:** Write minimal implementation

```python
# src/syncopaid/review_ui.py (add method to BillingEntryReview class)

    def split(self, parts: List[Dict]) -> List['BillingEntryReview']:
        """Split this entry into multiple entries.

        Args:
            parts: List of dicts with keys: matter_code, matter_name (optional),
                   time_minutes, narrative

        Returns:
            List of new BillingEntryReview objects

        Raises:
            ValueError: If parts' total time exceeds original
        """
        total_split_time = sum(p.get('time_minutes', 0) for p in parts)
        if total_split_time > self.time_minutes:
            raise ValueError(f"Split time ({total_split_time}) exceeds original ({self.time_minutes})")

        new_entries = []
        for part in parts:
            entry = BillingEntryReview(
                event_ids=self.event_ids.copy(),
                matter_code=part.get('matter_code'),
                matter_name=part.get('matter_name'),
                narrative=part.get('narrative', ''),
                time_minutes=part.get('time_minutes', 0),
                start_time=self.start_time,
                end_time=self.end_time,
                confidence=self.confidence,
                status="edited"
            )
            new_entries.append(entry)

        self.status = "split"
        return new_entries
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_review_ui.py -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_review_ui.py src/syncopaid/review_ui.py && git commit -m "feat(review): add entry split functionality"
```

---

### Task 4: Add Entry Merge Functionality (~4 min)

**Files:**
- Modify: `tests/test_review_ui.py`
- Modify: `src/syncopaid/review_ui.py`

**Context:** Lawyers may want to merge multiple related entries into one (e.g., 3 emails about the same case become one "correspondence" entry). The merge function combines entries and their event IDs.

**Step 1 - RED:** Write failing test

```python
# tests/test_review_ui.py (append to file)

def test_merge_entries():
    """Can merge multiple entries into one."""
    from syncopaid.review_ui import merge_entries

    entries = [
        BillingEntryReview(
            event_ids=[1],
            matter_code="SMITH-001",
            narrative="Email to client",
            time_minutes=6,
            start_time="2024-01-15T10:00:00",
            end_time="2024-01-15T10:06:00"
        ),
        BillingEntryReview(
            event_ids=[2],
            matter_code="SMITH-001",
            narrative="Reply from client",
            time_minutes=6,
            start_time="2024-01-15T10:10:00",
            end_time="2024-01-15T10:16:00"
        ),
        BillingEntryReview(
            event_ids=[3],
            matter_code="SMITH-001",
            narrative="Follow-up email",
            time_minutes=6,
            start_time="2024-01-15T10:20:00",
            end_time="2024-01-15T10:26:00"
        ),
    ]

    merged = merge_entries(entries, narrative="Client correspondence re: estate planning")

    assert merged.event_ids == [1, 2, 3]
    assert merged.time_minutes == 18  # Sum of all
    assert merged.matter_code == "SMITH-001"  # Same matter
    assert merged.narrative == "Client correspondence re: estate planning"
    assert merged.start_time == "2024-01-15T10:00:00"  # Earliest
    assert merged.end_time == "2024-01-15T10:26:00"  # Latest
    assert merged.status == "edited"


def test_merge_entries_averages_confidence():
    """Merged entry has average confidence."""
    from syncopaid.review_ui import merge_entries

    entries = [
        BillingEntryReview(event_ids=[1], narrative="A", confidence=0.9),
        BillingEntryReview(event_ids=[2], narrative="B", confidence=0.7),
    ]

    merged = merge_entries(entries)

    assert merged.confidence == 0.8  # Average


def test_merge_requires_multiple_entries():
    """Merge requires at least 2 entries."""
    from syncopaid.review_ui import merge_entries

    with pytest.raises(ValueError, match="at least 2"):
        merge_entries([BillingEntryReview(event_ids=[1])])
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_review_ui.py::test_merge_entries -v
```
Expected output: `FAILED` (cannot import name 'merge_entries')

**Step 3 - GREEN:** Write minimal implementation

```python
# src/syncopaid/review_ui.py (add function after BillingEntryReview class)

def merge_entries(
    entries: List[BillingEntryReview],
    narrative: Optional[str] = None,
    matter_code: Optional[str] = None
) -> BillingEntryReview:
    """Merge multiple entries into one.

    Args:
        entries: List of entries to merge (at least 2)
        narrative: Optional override narrative (else combines originals)
        matter_code: Optional override matter code (else uses first)

    Returns:
        New merged BillingEntryReview

    Raises:
        ValueError: If fewer than 2 entries provided
    """
    if len(entries) < 2:
        raise ValueError("Merge requires at least 2 entries")

    # Combine event IDs
    all_event_ids = []
    for entry in entries:
        all_event_ids.extend(entry.event_ids)

    # Sum time
    total_minutes = sum(e.time_minutes for e in entries)

    # Get time range
    start_times = [e.start_time for e in entries if e.start_time]
    end_times = [e.end_time for e in entries if e.end_time]

    # Average confidence
    confidences = [e.confidence for e in entries if e.confidence > 0]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    # Use provided or derive from entries
    final_narrative = narrative or "; ".join(e.narrative for e in entries if e.narrative)
    final_matter = matter_code or entries[0].matter_code
    final_matter_name = entries[0].matter_name if not matter_code else None

    merged = BillingEntryReview(
        event_ids=all_event_ids,
        matter_code=final_matter,
        matter_name=final_matter_name,
        narrative=final_narrative,
        time_minutes=total_minutes,
        start_time=min(start_times) if start_times else "",
        end_time=max(end_times) if end_times else "",
        confidence=round(avg_confidence, 2),
        status="edited"
    )

    # Mark original entries as merged
    for entry in entries:
        entry.status = "merged"

    return merged
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_review_ui.py -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_review_ui.py src/syncopaid/review_ui.py && git commit -m "feat(review): add entry merge functionality"
```

---

### Task 5: Create Enhanced Review Dialog UI (~5 min)

**Files:**
- Modify: `tests/test_review_ui.py`
- Modify: `src/syncopaid/review_ui.py`

**Context:** The existing `ReviewUI` class is a skeleton. We enhance it to display the full entry list, show confidence indicators, and provide buttons for all operations (approve, edit, split, merge, delete).

**Step 1 - RED:** Write failing test

```python
# tests/test_review_ui.py (append to file)

def test_review_dialog_loads_entries():
    """Review dialog loads and displays entries."""
    from syncopaid.review_ui import ReviewDialog

    entries = [
        BillingEntryReview(
            event_ids=[1],
            matter_code="SMITH-001",
            matter_name="Smith Case",
            narrative="Legal research",
            time_minutes=30,
            confidence=0.85
        ),
        BillingEntryReview(
            event_ids=[2],
            matter_code="JONES-002",
            narrative="Document review",
            time_minutes=18,
            confidence=0.65
        ),
    ]

    # Test without GUI (headless)
    dialog = ReviewDialog(entries=entries, headless=True)

    assert dialog.entry_count == 2
    assert dialog.pending_count == 2  # Both pending initially
    assert dialog.approved_count == 0


def test_review_dialog_approve_all():
    """Can approve all entries at once."""
    from syncopaid.review_ui import ReviewDialog

    entries = [
        BillingEntryReview(event_ids=[1], narrative="Work 1"),
        BillingEntryReview(event_ids=[2], narrative="Work 2"),
    ]

    dialog = ReviewDialog(entries=entries, headless=True)
    dialog.approve_all()

    assert dialog.approved_count == 2
    assert all(e.status == "approved" for e in entries)


def test_review_dialog_get_reviewed_entries():
    """Can get list of reviewed entries."""
    from syncopaid.review_ui import ReviewDialog

    entries = [
        BillingEntryReview(event_ids=[1], narrative="Work 1"),
        BillingEntryReview(event_ids=[2], narrative="Work 2"),
        BillingEntryReview(event_ids=[3], narrative="Lunch"),
    ]

    dialog = ReviewDialog(entries=entries, headless=True)
    entries[0].approve()
    entries[1].approve()
    entries[2].mark_deleted()

    reviewed = dialog.get_reviewed_entries()

    assert len(reviewed) == 2  # Only approved, not deleted
    assert all(e.status == "approved" for e in reviewed)
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_review_ui.py::test_review_dialog_loads_entries -v
```
Expected output: `FAILED` (cannot import name 'ReviewDialog')

**Step 3 - GREEN:** Write minimal implementation

```python
# src/syncopaid/review_ui.py (add class after merge_entries function)

class ReviewDialog:
    """Enhanced dialog for reviewing AI-generated billing entries.

    Provides full review workflow with:
    - List view of all entries
    - Edit, split, merge, delete operations
    - Approve individual or all entries
    - Confidence indicators
    """

    def __init__(
        self,
        parent=None,
        entries: Optional[List[BillingEntryReview]] = None,
        db: Optional[Database] = None,
        headless: bool = False
    ):
        """Initialize review dialog.

        Args:
            parent: Parent tkinter window (None for headless)
            entries: List of entries to review
            db: Database for persisting changes
            headless: If True, skip GUI creation (for testing)
        """
        self.entries = entries or []
        self.db = db
        self.selected_indices: List[int] = []

        if parent and not headless:
            self._create_window(parent)

    @property
    def entry_count(self) -> int:
        """Total number of entries."""
        return len(self.entries)

    @property
    def pending_count(self) -> int:
        """Number of entries not yet reviewed."""
        return sum(1 for e in self.entries if e.status is None)

    @property
    def approved_count(self) -> int:
        """Number of approved entries."""
        return sum(1 for e in self.entries if e.status in ("approved", "edited"))

    def approve_all(self) -> None:
        """Approve all pending entries."""
        for entry in self.entries:
            if entry.status is None:
                entry.approve()

    def get_reviewed_entries(self) -> List[BillingEntryReview]:
        """Get entries that have been approved or edited (not deleted)."""
        return [e for e in self.entries if e.status in ("approved", "edited")]

    def _create_window(self, parent):
        """Create the review dialog window with full UI."""
        self.window = tk.Toplevel(parent)
        self.window.title("Review AI-Generated Billing Entries")
        self.window.geometry("900x600")

        # Main container
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Entry list (left side)
        list_frame = ttk.LabelFrame(main_frame, text="Entries to Review", padding=5)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Treeview for entries
        columns = ("status", "time", "matter", "narrative", "confidence")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="extended")

        self.tree.heading("status", text="Status")
        self.tree.heading("time", text="Time")
        self.tree.heading("matter", text="Matter")
        self.tree.heading("narrative", text="Narrative")
        self.tree.heading("confidence", text="Conf")

        self.tree.column("status", width=80)
        self.tree.column("time", width=60)
        self.tree.column("matter", width=120)
        self.tree.column("narrative", width=300)
        self.tree.column("confidence", width=50)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Populate tree
        self._refresh_tree()

        # Edit panel (right side)
        edit_frame = ttk.LabelFrame(main_frame, text="Edit Selected", padding=10)
        edit_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        # Matter field
        ttk.Label(edit_frame, text="Matter:").grid(row=0, column=0, sticky=tk.W)
        self.matter_var = tk.StringVar()
        ttk.Entry(edit_frame, textvariable=self.matter_var, width=30).grid(row=0, column=1, pady=2)

        # Time field
        ttk.Label(edit_frame, text="Time (min):").grid(row=1, column=0, sticky=tk.W)
        self.time_var = tk.StringVar()
        ttk.Entry(edit_frame, textvariable=self.time_var, width=10).grid(row=1, column=1, sticky=tk.W, pady=2)

        # Narrative field
        ttk.Label(edit_frame, text="Narrative:").grid(row=2, column=0, sticky=tk.NW)
        self.narrative_text = tk.Text(edit_frame, height=4, width=30)
        self.narrative_text.grid(row=2, column=1, pady=2)

        # Action buttons
        btn_frame = ttk.Frame(edit_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Button(btn_frame, text="Approve", command=self._approve_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Save Edit", command=self._save_edit).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Delete", command=self._delete_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Split...", command=self._show_split_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Merge", command=self._merge_selected).pack(side=tk.LEFT, padx=2)

        # Bottom buttons
        bottom_frame = ttk.Frame(self.window, padding=10)
        bottom_frame.pack(fill=tk.X)

        ttk.Button(bottom_frame, text="Approve All", command=self._approve_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Done", command=self._on_done).pack(side=tk.RIGHT, padx=5)

        # Progress label
        self.progress_var = tk.StringVar()
        ttk.Label(bottom_frame, textvariable=self.progress_var).pack(side=tk.RIGHT, padx=20)
        self._update_progress()

        # Bind selection
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        self.window.transient(parent)
        self.window.grab_set()

    def _refresh_tree(self):
        """Refresh the treeview with current entry data."""
        if not hasattr(self, 'tree'):
            return

        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add entries
        for i, entry in enumerate(self.entries):
            status = entry.status or "pending"
            conf_str = f"{int(entry.confidence * 100)}%" if entry.confidence else "-"
            narrative_preview = entry.narrative[:50] + "..." if len(entry.narrative) > 50 else entry.narrative

            self.tree.insert("", tk.END, iid=str(i), values=(
                status,
                f"{entry.time_minutes}m",
                entry.matter_code or "-",
                narrative_preview,
                conf_str
            ))

    def _update_progress(self):
        """Update progress label."""
        if hasattr(self, 'progress_var'):
            self.progress_var.set(f"Reviewed: {self.approved_count}/{self.entry_count}")

    def _on_select(self, event):
        """Handle tree selection change."""
        selection = self.tree.selection()
        if selection:
            idx = int(selection[0])
            entry = self.entries[idx]
            self.matter_var.set(entry.matter_code or "")
            self.time_var.set(str(entry.time_minutes))
            self.narrative_text.delete("1.0", tk.END)
            self.narrative_text.insert("1.0", entry.narrative)

    def _approve_selected(self):
        """Approve selected entries."""
        for item in self.tree.selection():
            idx = int(item)
            self.entries[idx].approve()
        self._refresh_tree()
        self._update_progress()

    def _save_edit(self):
        """Save edits to selected entry."""
        selection = self.tree.selection()
        if not selection:
            return

        idx = int(selection[0])
        entry = self.entries[idx]

        entry.update_matter(self.matter_var.get() or None)
        try:
            entry.update_time(int(self.time_var.get()))
        except ValueError:
            pass
        entry.update_narrative(self.narrative_text.get("1.0", tk.END).strip())

        self._refresh_tree()
        self._update_progress()

    def _delete_selected(self):
        """Mark selected entries as deleted."""
        for item in self.tree.selection():
            idx = int(item)
            self.entries[idx].mark_deleted()
        self._refresh_tree()
        self._update_progress()

    def _show_split_dialog(self):
        """Show dialog to split selected entry."""
        selection = self.tree.selection()
        if len(selection) != 1:
            messagebox.showwarning("Split", "Select exactly one entry to split.")
            return
        # TODO: Implement split dialog in future task
        messagebox.showinfo("Split", "Split dialog coming in next iteration.")

    def _merge_selected(self):
        """Merge selected entries."""
        selection = self.tree.selection()
        if len(selection) < 2:
            messagebox.showwarning("Merge", "Select at least 2 entries to merge.")
            return

        indices = [int(item) for item in selection]
        entries_to_merge = [self.entries[i] for i in indices]

        try:
            merged = merge_entries(entries_to_merge)

            # Remove merged entries (in reverse to preserve indices)
            for i in sorted(indices, reverse=True):
                del self.entries[i]

            # Add merged entry
            self.entries.append(merged)
            self._refresh_tree()
            self._update_progress()
        except ValueError as e:
            messagebox.showerror("Merge Error", str(e))

    def _approve_all(self):
        """Approve all pending entries."""
        self.approve_all()
        self._refresh_tree()
        self._update_progress()

    def _on_done(self):
        """Handle done button click."""
        if hasattr(self, 'window'):
            self.window.destroy()
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_review_ui.py -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_review_ui.py src/syncopaid/review_ui.py && git commit -m "feat(review): add enhanced ReviewDialog with full review workflow"
```

---

### Task 6: Add Database Review Status Persistence (~4 min)

**Files:**
- Create: `tests/test_review_database.py`
- Create: `src/syncopaid/database_operations_review.py`

**Context:** The review status needs to persist so users can resume reviews and see which entries have been approved. We add database operations to save and load review status.

**Step 1 - RED:** Write failing test

```python
# tests/test_review_database.py
"""Tests for review status database operations."""
import pytest
import sqlite3
import tempfile
import os
from syncopaid.database_operations_review import ReviewStatusMixin


class MockDatabase(ReviewStatusMixin):
    """Mock database for testing."""

    def __init__(self, db_path):
        self.db_path = db_path
        self._setup_schema()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _setup_schema(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS review_status (
                    event_id INTEGER PRIMARY KEY,
                    status TEXT NOT NULL,
                    edited_narrative TEXT,
                    edited_matter_code TEXT,
                    edited_time_minutes INTEGER,
                    reviewed_at TEXT NOT NULL
                )
            """)


@pytest.fixture
def db():
    """Create temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    database = MockDatabase(path)
    yield database
    os.unlink(path)


def test_save_review_status(db):
    """Can save review status for events."""
    db.save_review_status(
        event_ids=[1, 2, 3],
        status="approved",
        narrative="Edited narrative",
        matter_code="SMITH-001",
        time_minutes=18
    )

    statuses = db.get_review_statuses([1, 2, 3])

    assert len(statuses) == 3
    assert all(s['status'] == 'approved' for s in statuses)
    assert all(s['edited_narrative'] == 'Edited narrative' for s in statuses)


def test_get_pending_events(db):
    """Can get events that haven't been reviewed."""
    # Save some as reviewed
    db.save_review_status(event_ids=[1, 2], status="approved")

    # Check which are pending
    pending = db.get_pending_review_event_ids([1, 2, 3, 4, 5])

    assert pending == [3, 4, 5]


def test_clear_review_status(db):
    """Can clear review status for events."""
    db.save_review_status(event_ids=[1, 2], status="approved")

    db.clear_review_status([1])

    statuses = db.get_review_statuses([1, 2])
    assert len(statuses) == 1
    assert statuses[0]['event_id'] == 2
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_review_database.py -v
```
Expected output: `FAILED` (cannot import 'ReviewStatusMixin')

**Step 3 - GREEN:** Write minimal implementation

```python
# src/syncopaid/database_operations_review.py
"""Database operations for review status tracking."""
from typing import List, Dict, Optional
from datetime import datetime


class ReviewStatusMixin:
    """Mixin providing review status persistence operations.

    Requires _get_connection() method from Database class.
    """

    def save_review_status(
        self,
        event_ids: List[int],
        status: str,
        narrative: Optional[str] = None,
        matter_code: Optional[str] = None,
        time_minutes: Optional[int] = None
    ) -> None:
        """Save review status for events.

        Args:
            event_ids: List of event IDs to update
            status: Status string ('approved', 'edited', 'deleted')
            narrative: Optional edited narrative
            matter_code: Optional edited matter code
            time_minutes: Optional edited time in minutes
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Ensure table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS review_status (
                    event_id INTEGER PRIMARY KEY,
                    status TEXT NOT NULL,
                    edited_narrative TEXT,
                    edited_matter_code TEXT,
                    edited_time_minutes INTEGER,
                    reviewed_at TEXT NOT NULL
                )
            """)

            reviewed_at = datetime.now().isoformat()

            for event_id in event_ids:
                cursor.execute("""
                    INSERT OR REPLACE INTO review_status
                    (event_id, status, edited_narrative, edited_matter_code,
                     edited_time_minutes, reviewed_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (event_id, status, narrative, matter_code, time_minutes, reviewed_at))

            conn.commit()

    def get_review_statuses(self, event_ids: List[int]) -> List[Dict]:
        """Get review statuses for specified events.

        Args:
            event_ids: List of event IDs to query

        Returns:
            List of status dicts with keys: event_id, status, edited_narrative,
            edited_matter_code, edited_time_minutes, reviewed_at
        """
        if not event_ids:
            return []

        with self._get_connection() as conn:
            cursor = conn.cursor()

            placeholders = ','.join('?' * len(event_ids))
            cursor.execute(f"""
                SELECT event_id, status, edited_narrative, edited_matter_code,
                       edited_time_minutes, reviewed_at
                FROM review_status
                WHERE event_id IN ({placeholders})
            """, event_ids)

            return [dict(row) for row in cursor.fetchall()]

    def get_pending_review_event_ids(self, event_ids: List[int]) -> List[int]:
        """Get event IDs that haven't been reviewed yet.

        Args:
            event_ids: List of event IDs to check

        Returns:
            List of event IDs without review status
        """
        if not event_ids:
            return []

        reviewed = {s['event_id'] for s in self.get_review_statuses(event_ids)}
        return [eid for eid in event_ids if eid not in reviewed]

    def clear_review_status(self, event_ids: List[int]) -> None:
        """Clear review status for specified events.

        Args:
            event_ids: List of event IDs to clear
        """
        if not event_ids:
            return

        with self._get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ','.join('?' * len(event_ids))
            cursor.execute(f"""
                DELETE FROM review_status
                WHERE event_id IN ({placeholders})
            """, event_ids)
            conn.commit()
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_review_database.py -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_review_database.py src/syncopaid/database_operations_review.py && git commit -m "feat(review): add database persistence for review status"
```

---

### Task 7: Integrate Review Dialog into Tray Menu (~3 min)

**Files:**
- Modify: `tests/test_review_ui.py`
- Modify: `src/syncopaid/tray.py`

**Context:** Users launch the review dialog from the system tray menu. We add a menu item that loads pending entries and opens the dialog.

**Step 1 - RED:** Write failing test

```python
# tests/test_review_ui.py (append to file)

def test_launch_review_function():
    """launch_review_dialog creates dialog with entries from database."""
    from syncopaid.review_ui import launch_review_dialog
    from unittest.mock import Mock, patch

    # Mock database
    mock_db = Mock()
    mock_db.get_events.return_value = [
        {"id": 1, "app": "Word", "title": "Doc.docx", "timestamp": "2024-01-15T10:00:00", "duration_seconds": 1800}
    ]
    mock_db.get_pending_review_event_ids.return_value = [1]
    mock_db.get_screenshots.return_value = []

    # Test headless launch
    with patch('syncopaid.review_ui.ReviewDialog') as mock_dialog:
        launch_review_dialog(db=mock_db, start_date="2024-01-15", headless=True)

        # Verify dialog was created with entries
        mock_dialog.assert_called_once()
        call_kwargs = mock_dialog.call_args[1]
        assert 'entries' in call_kwargs
        assert call_kwargs['headless'] is True
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_review_ui.py::test_launch_review_function -v
```
Expected output: `FAILED` (cannot import name 'launch_review_dialog')

**Step 3 - GREEN:** Write minimal implementation

```python
# src/syncopaid/review_ui.py (add function at end of file)

def launch_review_dialog(
    parent=None,
    db=None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    headless: bool = False
) -> Optional[ReviewDialog]:
    """Launch the review dialog with entries from database.

    Loads events for the date range, filters to those not yet reviewed,
    groups into billing entries, and opens the review dialog.

    Args:
        parent: Parent tkinter window
        db: Database instance
        start_date: Start date for entries (default: today)
        end_date: End date for entries
        headless: If True, skip GUI (for testing)

    Returns:
        ReviewDialog instance (or None if no entries)
    """
    from datetime import date

    if not db:
        return None

    # Default to today if no date specified
    if not start_date:
        start_date = date.today().isoformat()

    # Get events for date range
    events = db.get_events(start_date=start_date, end_date=end_date, include_idle=False)

    if not events:
        if not headless:
            messagebox.showinfo("Review", "No events found for the selected date range.")
        return None

    # Filter to pending (not yet reviewed)
    event_ids = [e.get('id') for e in events if e.get('id')]

    # Check if db has review status methods
    if hasattr(db, 'get_pending_review_event_ids'):
        pending_ids = set(db.get_pending_review_event_ids(event_ids))
        events = [e for e in events if e.get('id') in pending_ids]

    if not events:
        if not headless:
            messagebox.showinfo("Review", "All events have been reviewed.")
        return None

    # Convert to BillingEntryReview objects
    entries = []
    for event in events:
        entry = BillingEntryReview(
            event_ids=[event.get('id')] if event.get('id') else [],
            matter_code=str(event.get('matter_id')) if event.get('matter_id') else None,
            narrative=f"{event.get('app', 'Unknown')}: {event.get('title', 'No title')}",
            time_minutes=int(event.get('duration_seconds', 0) / 60),
            start_time=event.get('timestamp', ''),
            end_time=event.get('end_time', event.get('timestamp', '')),
            confidence=float(event.get('confidence', 0)) if event.get('confidence') else 0.0
        )
        entries.append(entry)

    return ReviewDialog(parent=parent, entries=entries, db=db, headless=headless)
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_review_ui.py -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_review_ui.py src/syncopaid/review_ui.py && git commit -m "feat(review): add launch_review_dialog function for tray integration"
```

---

## Final Verification

Run after all tasks complete:
```bash
python -m pytest tests/test_review_ui.py tests/test_review_database.py -v  # All review tests pass
python -m pytest -v                                                         # All tests pass
python -c "from syncopaid.review_ui import ReviewDialog, launch_review_dialog; print('Import OK')"
```

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`

## Notes

- The split dialog (Task 5 placeholder) can be implemented as a follow-up enhancement
- The `launch_review_dialog` function currently creates individual entries per event; when 8.7.1 (Intelligent Narrative Generation) is complete, it should use `generate_billing_entries` instead for grouped entries
- Tray menu integration requires adding a menu item in `tray.py` that calls `launch_review_dialog` - this can be done in a simple follow-up patch
- The confidence display uses percentage (0-100%) for user-friendliness
- Merge operation requires at least 2 entries selected; split requires exactly 1
