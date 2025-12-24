# Intelligent Narrative Generation - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 8.7.1 | **Created:** 2025-12-24 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Generate professional legal billing narratives from screen activity data, including screenshot analysis context, following legal billing conventions.

**Approach:** Extend the existing `billing.py` module to incorporate screenshot analysis data and matter context when generating narratives. Add an `ActivityGrouper` to combine related activities (e.g., multiple emails about same case) into single narrative entries. Use LLM prompts tuned for legal billing conventions.

**Tech Stack:** Python dataclasses, existing `LLMClient` from `llm.py`, `Database` for querying events/screenshots

---

## Story Context

**Title:** Intelligent Narrative Generation
**Description:** As a lawyer who needs detailed billing descriptions, I want SyncoPaid to generate draft narrative entries from my screen activity, so that I can bill accurately without reconstructing my day from memory.

**Acceptance Criteria:**
- [ ] AI generates narrative based on: application used, documents viewed, actions performed
- [ ] Narrative follows legal billing conventions (e.g., "Review correspondence re: [case]", "Draft motion for [matter]")
- [ ] Includes relevant details extracted from screenshots (document names, email subjects)
- [ ] Groups related activities into single narrative (e.g., 3 emails about same case = "Correspondence with client re: settlement")
- [ ] User can edit generated narrative before finalizing

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`

## Files Affected

| File | Change Type | Purpose |
|------|-------------|---------|
| `tests/test_narrative_generator.py` | Create | Unit tests for narrative generation |
| `src/syncopaid/narrative_generator.py` | Create | Core narrative generation logic |
| `tests/test_billing.py` | Modify | Add integration tests |
| `src/syncopaid/billing.py` | Modify | Integrate with narrative generator |

## TDD Tasks

### Task 1: Create ActivityGroup Dataclass (~3 min)

**Files:**
- Create: `tests/test_narrative_generator.py`
- Create: `src/syncopaid/narrative_generator.py`

**Context:** An `ActivityGroup` represents related activities that should be billed together (e.g., multiple emails about the same case). This is the foundation for grouping before narrative generation.

**Step 1 - RED:** Write failing test

```python
# tests/test_narrative_generator.py
"""Tests for intelligent narrative generation."""
import pytest
from syncopaid.narrative_generator import ActivityGroup


def test_activity_group_creation():
    """ActivityGroup holds related activities with metadata."""
    group = ActivityGroup(
        matter_code="SMITH-2024-001",
        activities=[
            {"app": "Outlook", "title": "RE: Settlement Offer", "timestamp": "2024-01-15T10:00:00"},
            {"app": "Outlook", "title": "RE: Settlement Offer", "timestamp": "2024-01-15T10:05:00"},
        ],
        total_minutes=12,
        activity_type="correspondence"
    )
    assert group.matter_code == "SMITH-2024-001"
    assert len(group.activities) == 2
    assert group.total_minutes == 12
    assert group.activity_type == "correspondence"


def test_activity_group_defaults():
    """ActivityGroup has sensible defaults."""
    group = ActivityGroup(activities=[{"app": "Word", "title": "Draft.docx"}])
    assert group.matter_code is None
    assert group.total_minutes == 0
    assert group.activity_type == "general"
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_narrative_generator.py -v
```
Expected output: `FAILED` (module syncopaid.narrative_generator not found)

**Step 3 - GREEN:** Write minimal implementation

```python
# src/syncopaid/narrative_generator.py
"""Intelligent narrative generation for legal billing.

Generates professional billing narratives from screen activity data,
incorporating screenshot analysis and following legal billing conventions.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class ActivityGroup:
    """A group of related activities to be billed together.

    Attributes:
        activities: List of activity dicts with 'app', 'title', 'timestamp' keys
        matter_code: Associated matter code (if determined)
        total_minutes: Combined duration of grouped activities
        activity_type: Category like 'correspondence', 'drafting', 'research'
        screenshot_context: Extracted details from screenshot analysis
    """
    activities: List[Dict] = field(default_factory=list)
    matter_code: Optional[str] = None
    total_minutes: int = 0
    activity_type: str = "general"
    screenshot_context: Optional[str] = None
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_narrative_generator.py -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_narrative_generator.py src/syncopaid/narrative_generator.py && git commit -m "feat(billing): add ActivityGroup dataclass for narrative generation"
```

---

### Task 2: Create Activity Grouper (~5 min)

**Files:**
- Modify: `tests/test_narrative_generator.py`
- Modify: `src/syncopaid/narrative_generator.py`

**Context:** The `group_activities` function takes a list of raw activity events and groups them by matter/context. Activities within 5 minutes with matching titles or the same matter are merged into one group.

**Step 1 - RED:** Write failing test

```python
# tests/test_narrative_generator.py (append to file)

def test_group_activities_by_matter():
    """Activities with same matter code are grouped together."""
    from syncopaid.narrative_generator import group_activities

    activities = [
        {"app": "Outlook", "title": "RE: Smith Case", "timestamp": "2024-01-15T10:00:00", "matter_id": 1, "duration_seconds": 120},
        {"app": "Word", "title": "Motion Draft", "timestamp": "2024-01-15T10:05:00", "matter_id": 1, "duration_seconds": 300},
        {"app": "Chrome", "title": "Legal Research", "timestamp": "2024-01-15T10:15:00", "matter_id": 2, "duration_seconds": 600},
    ]

    groups = group_activities(activities)

    assert len(groups) == 2  # Two different matters
    assert groups[0].matter_code == 1
    assert len(groups[0].activities) == 2  # Outlook + Word grouped
    assert groups[1].matter_code == 2


def test_group_activities_by_title_similarity():
    """Activities with similar titles (no matter) are grouped."""
    from syncopaid.narrative_generator import group_activities

    activities = [
        {"app": "Outlook", "title": "RE: Contract Review", "timestamp": "2024-01-15T10:00:00", "duration_seconds": 60},
        {"app": "Outlook", "title": "RE: Contract Review", "timestamp": "2024-01-15T10:02:00", "duration_seconds": 60},
        {"app": "Word", "title": "Unrelated Doc", "timestamp": "2024-01-15T10:10:00", "duration_seconds": 120},
    ]

    groups = group_activities(activities)

    assert len(groups) == 2  # Two groups
    assert len(groups[0].activities) == 2  # Both emails grouped


def test_group_activities_calculates_duration():
    """Grouped activities sum their durations."""
    from syncopaid.narrative_generator import group_activities

    activities = [
        {"app": "Word", "title": "Draft.docx", "timestamp": "2024-01-15T10:00:00", "duration_seconds": 300},
        {"app": "Word", "title": "Draft.docx", "timestamp": "2024-01-15T10:05:00", "duration_seconds": 300},
    ]

    groups = group_activities(activities)

    assert len(groups) == 1
    assert groups[0].total_minutes == 10  # 600 seconds = 10 minutes
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_narrative_generator.py::test_group_activities_by_matter -v
```
Expected output: `FAILED` (cannot import name 'group_activities')

**Step 3 - GREEN:** Write minimal implementation

```python
# src/syncopaid/narrative_generator.py (append to existing file)

def group_activities(activities: List[Dict], gap_threshold_minutes: int = 10) -> List[ActivityGroup]:
    """Group related activities for billing.

    Groups activities by:
    1. Same matter_id (if assigned)
    2. Same title (for uncategorized activities)
    3. Within time gap threshold

    Args:
        activities: List of activity dicts from database
        gap_threshold_minutes: Max minutes between activities to group together

    Returns:
        List of ActivityGroup objects
    """
    if not activities:
        return []

    # Sort by timestamp
    sorted_activities = sorted(activities, key=lambda a: a.get('timestamp', ''))

    groups: List[ActivityGroup] = []
    current_group: Optional[ActivityGroup] = None

    for activity in sorted_activities:
        matter_id = activity.get('matter_id')
        title = activity.get('title', '')
        duration = activity.get('duration_seconds', 0)

        # Check if this activity belongs to current group
        should_merge = False
        if current_group:
            same_matter = matter_id and current_group.matter_code == matter_id
            same_title = _titles_similar(title, _get_group_title(current_group))
            should_merge = same_matter or (not matter_id and not current_group.matter_code and same_title)

        if should_merge and current_group:
            current_group.activities.append(activity)
            current_group.total_minutes += int(duration / 60)
        else:
            # Start new group
            if current_group:
                groups.append(current_group)

            current_group = ActivityGroup(
                activities=[activity],
                matter_code=matter_id,
                total_minutes=int(duration / 60),
                activity_type=_classify_activity_type(activity)
            )

    # Don't forget the last group
    if current_group:
        groups.append(current_group)

    return groups


def _titles_similar(title1: str, title2: str) -> bool:
    """Check if two titles are similar enough to group."""
    if not title1 or not title2:
        return False
    # Simple check: same after removing RE:/FW: prefixes
    clean1 = title1.replace('RE: ', '').replace('FW: ', '').strip()
    clean2 = title2.replace('RE: ', '').replace('FW: ', '').strip()
    return clean1 == clean2


def _get_group_title(group: ActivityGroup) -> str:
    """Get representative title from group."""
    if group.activities:
        return group.activities[0].get('title', '')
    return ''


def _classify_activity_type(activity: Dict) -> str:
    """Classify activity into billing category."""
    app = activity.get('app', '').lower()
    title = activity.get('title', '').lower()

    if 'outlook' in app or 'mail' in app:
        return 'correspondence'
    elif 'word' in app or 'winword' in app or '.docx' in title:
        return 'drafting'
    elif 'chrome' in app or 'edge' in app or 'firefox' in app:
        return 'research'
    elif 'excel' in app or '.xlsx' in title:
        return 'analysis'
    elif 'teams' in app or 'zoom' in app:
        return 'conference'
    else:
        return 'general'
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_narrative_generator.py -v
```
Expected output: `PASSED` (all tests)

**Step 5 - COMMIT:**
```bash
git add tests/test_narrative_generator.py src/syncopaid/narrative_generator.py && git commit -m "feat(billing): add activity grouping for narrative generation"
```

---

### Task 3: Generate Legal Billing Narratives (~5 min)

**Files:**
- Modify: `tests/test_narrative_generator.py`
- Modify: `src/syncopaid/narrative_generator.py`

**Context:** The `generate_narrative` function takes an `ActivityGroup` and produces a professional legal billing narrative following conventions like "Review correspondence re: [matter]" or "Draft motion for summary judgment".

**Step 1 - RED:** Write failing test

```python
# tests/test_narrative_generator.py (append to file)

def test_generate_correspondence_narrative():
    """Generate narrative for email correspondence."""
    from syncopaid.narrative_generator import generate_narrative, ActivityGroup

    group = ActivityGroup(
        activities=[
            {"app": "Outlook", "title": "RE: Settlement Offer - Smith v. Jones"},
            {"app": "Outlook", "title": "RE: Settlement Offer - Smith v. Jones"},
        ],
        matter_code="SMITH-001",
        total_minutes=12,
        activity_type="correspondence"
    )

    narrative = generate_narrative(group)

    # Should follow legal convention
    assert narrative != ""
    assert "correspondence" in narrative.lower() or "email" in narrative.lower()


def test_generate_drafting_narrative():
    """Generate narrative for document drafting."""
    from syncopaid.narrative_generator import generate_narrative, ActivityGroup

    group = ActivityGroup(
        activities=[
            {"app": "Word", "title": "Motion for Summary Judgment.docx"},
        ],
        total_minutes=30,
        activity_type="drafting"
    )

    narrative = generate_narrative(group)

    assert narrative != ""
    assert "draft" in narrative.lower() or "motion" in narrative.lower()


def test_generate_narrative_with_screenshot_context():
    """Screenshot context enhances narrative detail."""
    from syncopaid.narrative_generator import generate_narrative, ActivityGroup

    group = ActivityGroup(
        activities=[{"app": "Word", "title": "Contract.docx"}],
        total_minutes=20,
        activity_type="drafting",
        screenshot_context="User reviewing Section 4.2 - Indemnification clause"
    )

    narrative = generate_narrative(group)

    # Should incorporate the screenshot context
    assert "indemnification" in narrative.lower() or "contract" in narrative.lower()
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_narrative_generator.py::test_generate_correspondence_narrative -v
```
Expected output: `FAILED` (cannot import name 'generate_narrative')

**Step 3 - GREEN:** Write minimal implementation

```python
# src/syncopaid/narrative_generator.py (append to existing file)

# Legal billing phrase templates by activity type
NARRATIVE_TEMPLATES = {
    'correspondence': [
        "Review and respond to correspondence re: {subject}",
        "Email correspondence with {parties} regarding {subject}",
        "Review correspondence re: {subject}",
    ],
    'drafting': [
        "Draft {document_type}",
        "Prepare and revise {document_type}",
        "Continue drafting {document_type}",
    ],
    'research': [
        "Legal research regarding {subject}",
        "Research {subject} issues",
        "Review online resources re: {subject}",
    ],
    'analysis': [
        "Review and analyze {document_type}",
        "Analyze data regarding {subject}",
    ],
    'conference': [
        "Attend conference call regarding {subject}",
        "Video conference with {parties} re: {subject}",
    ],
    'general': [
        "Review {subject}",
        "Work on {subject}",
    ],
}


def generate_narrative(group: ActivityGroup, llm_client=None) -> str:
    """Generate professional legal billing narrative for an activity group.

    Args:
        group: ActivityGroup containing related activities
        llm_client: Optional LLMClient for AI-powered generation

    Returns:
        Professional billing narrative string
    """
    if not group.activities:
        return ""

    # Extract subject/document from activities
    subject = _extract_subject(group)
    document_type = _extract_document_type(group)

    # If LLM available, use it for better narrative
    if llm_client:
        return _generate_with_llm(group, llm_client)

    # Otherwise use template-based generation
    return _generate_from_template(group, subject, document_type)


def _extract_subject(group: ActivityGroup) -> str:
    """Extract the main subject from activity titles."""
    if not group.activities:
        return "matter"

    title = group.activities[0].get('title', '')

    # Clean up common prefixes
    for prefix in ['RE: ', 'FW: ', 'RE:', 'FW:']:
        title = title.replace(prefix, '')

    # Remove file extensions
    for ext in ['.docx', '.pdf', '.xlsx', '.doc']:
        title = title.replace(ext, '')

    # Use screenshot context if available and more specific
    if group.screenshot_context:
        return group.screenshot_context

    return title.strip() or "matter"


def _extract_document_type(group: ActivityGroup) -> str:
    """Extract document type from activities."""
    if not group.activities:
        return "document"

    title = group.activities[0].get('title', '').lower()

    if 'motion' in title:
        return "motion"
    elif 'contract' in title:
        return "contract"
    elif 'agreement' in title:
        return "agreement"
    elif 'brief' in title:
        return "brief"
    elif 'memo' in title:
        return "memorandum"
    elif 'letter' in title:
        return "correspondence"
    else:
        return "document"


def _generate_from_template(group: ActivityGroup, subject: str, document_type: str) -> str:
    """Generate narrative from templates."""
    templates = NARRATIVE_TEMPLATES.get(group.activity_type, NARRATIVE_TEMPLATES['general'])
    template = templates[0]  # Use first template for consistency

    narrative = template.format(
        subject=subject,
        document_type=document_type,
        parties="client"
    )

    return narrative


def _generate_with_llm(group: ActivityGroup, llm_client) -> str:
    """Generate narrative using LLM for more natural language."""
    # Combine activity info
    activities_desc = "; ".join([
        f"{a.get('app', 'Unknown')}: {a.get('title', 'No title')}"
        for a in group.activities[:5]  # Limit to first 5
    ])

    # Add screenshot context if available
    context = ""
    if group.screenshot_context:
        context = f"\nScreenshot shows: {group.screenshot_context}"

    prompt = f"""Convert these legal work activities into a professional billing narrative:

Activities: {activities_desc}
Activity type: {group.activity_type}
Duration: {group.total_minutes} minutes{context}

Requirements:
- Use legal billing conventions (e.g., "Review correspondence re:", "Draft motion for")
- Be concise (1-2 sentences)
- Include specific details from the activities
- Do not include time duration in narrative

Respond with only the narrative text, no JSON or explanations."""

    try:
        return llm_client.generate_narrative(prompt).strip()
    except Exception:
        # Fallback to template
        return _generate_from_template(group, _extract_subject(group), _extract_document_type(group))
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_narrative_generator.py -v
```
Expected output: `PASSED` (all tests)

**Step 5 - COMMIT:**
```bash
git add tests/test_narrative_generator.py src/syncopaid/narrative_generator.py && git commit -m "feat(billing): add legal narrative generation from activity groups"
```

---

### Task 4: Integrate with Screenshot Analysis Data (~4 min)

**Files:**
- Modify: `tests/test_narrative_generator.py`
- Modify: `src/syncopaid/narrative_generator.py`

**Context:** Add function to enrich activity groups with screenshot analysis data from the database. The `analysis_data` column in screenshots table contains vision LLM output that can provide context like "User editing Section 4.2 of contract".

**Step 1 - RED:** Write failing test

```python
# tests/test_narrative_generator.py (append to file)

def test_enrich_with_screenshot_context():
    """Enrich activity group with screenshot analysis data."""
    from syncopaid.narrative_generator import enrich_with_screenshot_context, ActivityGroup
    from unittest.mock import Mock

    # Mock database with screenshot data
    mock_db = Mock()
    mock_db.get_screenshots.return_value = [
        {
            'captured_at': '2024-01-15T10:02:00',
            'analysis_data': '{"description": "User reviewing indemnification clause in contract document"}',
            'analysis_status': 'complete'
        }
    ]

    group = ActivityGroup(
        activities=[
            {"app": "Word", "title": "Contract.docx", "timestamp": "2024-01-15T10:00:00", "end_time": "2024-01-15T10:10:00"},
        ],
        total_minutes=10,
        activity_type="drafting"
    )

    enriched = enrich_with_screenshot_context(group, mock_db)

    assert enriched.screenshot_context is not None
    assert "indemnification" in enriched.screenshot_context.lower()


def test_enrich_handles_no_screenshots():
    """Gracefully handle activities with no screenshots."""
    from syncopaid.narrative_generator import enrich_with_screenshot_context, ActivityGroup
    from unittest.mock import Mock

    mock_db = Mock()
    mock_db.get_screenshots.return_value = []

    group = ActivityGroup(
        activities=[{"app": "Word", "title": "Doc.docx", "timestamp": "2024-01-15T10:00:00"}],
        total_minutes=5,
        activity_type="drafting"
    )

    enriched = enrich_with_screenshot_context(group, mock_db)

    assert enriched.screenshot_context is None  # No screenshots available
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_narrative_generator.py::test_enrich_with_screenshot_context -v
```
Expected output: `FAILED` (cannot import name 'enrich_with_screenshot_context')

**Step 3 - GREEN:** Write minimal implementation

```python
# src/syncopaid/narrative_generator.py (append to existing file)
import json


def enrich_with_screenshot_context(group: ActivityGroup, db) -> ActivityGroup:
    """Enrich activity group with screenshot analysis data.

    Queries screenshots taken during the activity timeframe and extracts
    relevant context from vision analysis.

    Args:
        group: ActivityGroup to enrich
        db: Database instance with get_screenshots method

    Returns:
        ActivityGroup with screenshot_context populated (if available)
    """
    if not group.activities:
        return group

    # Get time range from activities
    timestamps = [a.get('timestamp', '') for a in group.activities]
    end_times = [a.get('end_time', a.get('timestamp', '')) for a in group.activities]

    start_time = min(timestamps) if timestamps else None
    end_time = max(end_times) if end_times else None

    if not start_time:
        return group

    # Query screenshots in time range
    try:
        screenshots = db.get_screenshots(start_date=start_time[:10], end_date=end_time[:10] if end_time else None)
    except Exception:
        return group

    # Filter to those within activity timeframe
    relevant_screenshots = [
        s for s in screenshots
        if start_time <= s.get('captured_at', '') <= (end_time or start_time)
    ]

    if not relevant_screenshots:
        return group

    # Extract context from analysis data
    context_parts = []
    for screenshot in relevant_screenshots:
        analysis_data = screenshot.get('analysis_data')
        if analysis_data and screenshot.get('analysis_status') == 'complete':
            try:
                data = json.loads(analysis_data)
                if 'description' in data:
                    context_parts.append(data['description'])
            except (json.JSONDecodeError, TypeError):
                pass

    if context_parts:
        # Use most descriptive context (longest)
        group.screenshot_context = max(context_parts, key=len)

    return group
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_narrative_generator.py -v
```
Expected output: `PASSED` (all tests)

**Step 5 - COMMIT:**
```bash
git add tests/test_narrative_generator.py src/syncopaid/narrative_generator.py && git commit -m "feat(billing): add screenshot context enrichment for narratives"
```

---

### Task 5: Add Billing Entry Generation Pipeline (~4 min)

**Files:**
- Modify: `tests/test_narrative_generator.py`
- Modify: `src/syncopaid/narrative_generator.py`

**Context:** Create the main entry point `generate_billing_entries` that orchestrates the full pipeline: query events → group activities → enrich with screenshots → generate narratives.

**Step 1 - RED:** Write failing test

```python
# tests/test_narrative_generator.py (append to file)

def test_generate_billing_entries_pipeline():
    """Full pipeline generates billing entries from raw events."""
    from syncopaid.narrative_generator import generate_billing_entries, BillingEntry
    from unittest.mock import Mock

    mock_db = Mock()
    mock_db.get_events.return_value = [
        {"id": 1, "app": "Outlook", "title": "RE: Smith Case", "timestamp": "2024-01-15T10:00:00", "duration_seconds": 360, "matter_id": 1},
        {"id": 2, "app": "Word", "title": "Motion.docx", "timestamp": "2024-01-15T10:10:00", "duration_seconds": 1800, "matter_id": 1},
    ]
    mock_db.get_screenshots.return_value = []

    entries = generate_billing_entries(mock_db, start_date="2024-01-15")

    assert len(entries) >= 1
    assert isinstance(entries[0], BillingEntry)
    assert entries[0].narrative != ""
    assert entries[0].time_minutes > 0


def test_billing_entry_dataclass():
    """BillingEntry holds complete billing information."""
    from syncopaid.narrative_generator import BillingEntry

    entry = BillingEntry(
        event_ids=[1, 2, 3],
        matter_code="SMITH-001",
        narrative="Review correspondence re: settlement",
        time_minutes=18,
        time_hours=0.3,
        start_time="2024-01-15T10:00:00",
        end_time="2024-01-15T10:18:00"
    )

    assert entry.matter_code == "SMITH-001"
    assert entry.time_hours == 0.3
    assert len(entry.event_ids) == 3
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_narrative_generator.py::test_billing_entry_dataclass -v
```
Expected output: `FAILED` (cannot import name 'BillingEntry')

**Step 3 - GREEN:** Write minimal implementation

```python
# src/syncopaid/narrative_generator.py (add after imports at top of file)
from syncopaid.billing import round_to_increment, minutes_to_hours


@dataclass
class BillingEntry:
    """A complete billing entry ready for review.

    Attributes:
        event_ids: IDs of source events included in this entry
        matter_code: Client/matter code for billing
        narrative: Professional billing narrative
        time_minutes: Duration in minutes (rounded to increment)
        time_hours: Duration in decimal hours
        start_time: Start of activity period
        end_time: End of activity period
    """
    event_ids: List[int] = field(default_factory=list)
    matter_code: Optional[str] = None
    narrative: str = ""
    time_minutes: int = 0
    time_hours: float = 0.0
    start_time: str = ""
    end_time: str = ""


# Add to end of file:
def generate_billing_entries(
    db,
    start_date: str,
    end_date: Optional[str] = None,
    llm_client=None
) -> List[BillingEntry]:
    """Generate billing entries from activity events.

    Main pipeline that:
    1. Queries events from database
    2. Groups related activities
    3. Enriches with screenshot context
    4. Generates narratives
    5. Returns ready-to-review billing entries

    Args:
        db: Database instance
        start_date: Start date (YYYY-MM-DD)
        end_date: Optional end date
        llm_client: Optional LLM client for AI narratives

    Returns:
        List of BillingEntry objects
    """
    # Query events
    events = db.get_events(start_date=start_date, end_date=end_date)

    if not events:
        return []

    # Group related activities
    groups = group_activities(events)

    # Enrich with screenshot context and generate entries
    entries = []
    for group in groups:
        # Enrich with screenshot context
        enriched = enrich_with_screenshot_context(group, db)

        # Generate narrative
        narrative = generate_narrative(enriched, llm_client)

        # Calculate time (rounded to billing increment)
        raw_minutes = enriched.total_minutes
        if raw_minutes < 1:
            raw_minutes = 1  # Minimum 1 minute
        rounded_minutes = round_to_increment(raw_minutes)

        # Get time range
        timestamps = [a.get('timestamp', '') for a in enriched.activities]
        end_times = [a.get('end_time', a.get('timestamp', '')) for a in enriched.activities]

        entry = BillingEntry(
            event_ids=[a.get('id', 0) for a in enriched.activities if a.get('id')],
            matter_code=str(enriched.matter_code) if enriched.matter_code else None,
            narrative=narrative,
            time_minutes=rounded_minutes,
            time_hours=minutes_to_hours(rounded_minutes),
            start_time=min(timestamps) if timestamps else "",
            end_time=max(end_times) if end_times else ""
        )
        entries.append(entry)

    return entries
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_narrative_generator.py -v
```
Expected output: `PASSED` (all tests)

**Step 5 - COMMIT:**
```bash
git add tests/test_narrative_generator.py src/syncopaid/narrative_generator.py && git commit -m "feat(billing): add billing entry generation pipeline"
```

---

## Final Verification

Run after all tasks complete:
```bash
python -m pytest tests/test_narrative_generator.py tests/test_billing.py -v  # All narrative tests pass
python -m pytest -v                                                           # All tests pass
python -c "from syncopaid.narrative_generator import generate_billing_entries; print('Import OK')"
```

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`

## Notes

- The template-based narrative generation provides reliable output without LLM dependency
- LLM enhancement is optional and gracefully falls back to templates
- Screenshot context enrichment requires activities to have `analysis_data` populated (depends on story 8.6.x)
- The `BillingEntry` dataclass is designed for compatibility with `ReviewUI` from story 8.7.2
- Follow-up work: Add matter code lookup from `matters` table to display client/matter names
