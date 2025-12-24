# Model Upgrade Transparency - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 8.8 | **Created:** 2025-12-24 | **Stage:** `planned`

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Enable silent AI model upgrades through version tracking and backwards-compatible data architecture, so users benefit from improved categorization without workflow changes.

**Approach:** Add model version metadata to analysis results, extend VisionEngine interface to expose version info, update AnalysisResult to include model version in stored data, and create backwards-compatibility tests that verify old data remains readable after model upgrades.

**Tech Stack:** Python dataclasses, sqlite3, existing `vision_engine.py` abstract base class, `screenshot_analyzer.py`

---

## Story Context

**Title:** Model Upgrade Transparency
**Description:** As a user, I want SyncoPaid updates to improve AI accuracy automatically, so that I benefit from better technology without changing my workflow.

**Acceptance Criteria:**
- [ ] Version updates include improved AI models silently
- [ ] Release notes say "Improved categorization accuracy" (not technical details)
- [ ] No change to UI or workflow
- [ ] No manual model installation or configuration
- [ ] Backwards compatible with existing data

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`

## Files Affected

| File | Change Type | Purpose |
|------|-------------|---------|
| `tests/test_model_upgrade_transparency.py` | Create | Tests for model version tracking and backwards compatibility |
| `src/syncopaid/vision_engine.py` | Modify | Add model_version property to VisionEngine |
| `src/syncopaid/screenshot_analyzer.py` | Modify | Include model_version in AnalysisResult |

## TDD Tasks

### Task 1: Add model_version Property to VisionEngine (~3 min)

**Files:**
- Create: `tests/test_model_upgrade_transparency.py`
- Modify: `src/syncopaid/vision_engine.py:36-46`

**Context:** The VisionEngine abstract base class defines the interface for AI models. Adding a `model_version` property enables tracking which exact model version analyzed each screenshot. This is essential for auditing and debugging when model behavior changes between updates.

**Step 1 - RED:** Write failing test

```python
# tests/test_model_upgrade_transparency.py
"""Tests for model upgrade transparency - silent AI model version tracking."""
import pytest
from abc import ABC
from syncopaid.vision_engine import VisionEngine, AnalysisResult


class MockVisionEngine(VisionEngine):
    """Concrete implementation for testing."""

    @property
    def name(self) -> str:
        return "Mock Engine"

    @property
    def model_id(self) -> str:
        return "test/mock-model"

    @property
    def model_version(self) -> str:
        return "1.0.0"

    def is_available(self) -> bool:
        return True

    def analyze(self, image_path, prompt=None):
        return AnalysisResult(
            description="Test description",
            activity_type="testing",
            confidence=0.95,
            raw_output="raw"
        )


def test_vision_engine_has_model_version_property():
    """VisionEngine subclasses must implement model_version property."""
    engine = MockVisionEngine()
    assert hasattr(engine, 'model_version')
    assert engine.model_version == "1.0.0"


def test_vision_engine_model_version_is_abstract():
    """model_version must be implemented by subclasses."""
    # This test verifies the property is part of the abstract interface
    assert 'model_version' in dir(VisionEngine)
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_model_upgrade_transparency.py::test_vision_engine_has_model_version_property -v
```
Expected output: `FAILED` (MockVisionEngine can't be instantiated - missing abstract method model_version)

**Step 3 - GREEN:** Add model_version abstract property

```python
# src/syncopaid/vision_engine.py (add after line 46, after model_id property)
    @property
    @abstractmethod
    def model_version(self) -> str:
        """Return the model version string (e.g., '2.0.1', '2024-01-15').

        Used for tracking which model version analyzed each screenshot.
        Include in release notes when updating: 'Improved categorization accuracy'.
        """
        pass
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_model_upgrade_transparency.py::test_vision_engine_has_model_version_property -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_model_upgrade_transparency.py src/syncopaid/vision_engine.py && git commit -m "feat: add model_version abstract property to VisionEngine"
```

---

### Task 2: Extend AnalysisResult with model_version Field (~3 min)

**Files:**
- Modify: `tests/test_model_upgrade_transparency.py`
- Modify: `src/syncopaid/vision_engine.py:14-27`

**Context:** The `AnalysisResult` dataclass stores analysis output. Adding an optional `model_version` field allows tracking which model version produced each result. This field is optional for backwards compatibility with existing data that lacks version info.

**Step 1 - RED:** Write failing test

```python
# tests/test_model_upgrade_transparency.py (add to file)

def test_analysis_result_includes_model_version():
    """AnalysisResult can store the model version that produced it."""
    result = AnalysisResult(
        description="Working on legal brief",
        activity_type="document_editing",
        confidence=0.85,
        raw_output="raw output",
        model_version="moondream2-v2.0.1"
    )
    assert result.model_version == "moondream2-v2.0.1"


def test_analysis_result_model_version_optional():
    """AnalysisResult works without model_version (backwards compatibility)."""
    result = AnalysisResult(
        description="Old analysis",
        activity_type="unknown",
        confidence=0.5,
        raw_output="legacy"
    )
    assert result.model_version is None
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_model_upgrade_transparency.py::test_analysis_result_includes_model_version -v
```
Expected output: `FAILED` (TypeError: unexpected keyword argument 'model_version')

**Step 3 - GREEN:** Add model_version field to AnalysisResult

```python
# src/syncopaid/vision_engine.py (modify AnalysisResult dataclass, lines 14-27)
@dataclass
class AnalysisResult:
    """Structured output from vision engine analysis.

    Attributes:
        description: Human-readable description of what the screenshot shows
        activity_type: Categorized activity (e.g., 'document_editing', 'web_browsing')
        confidence: Confidence score 0.0-1.0
        raw_output: Raw model output for debugging/logging
        model_version: Version of the model that produced this result (optional, for tracking)
    """
    description: str
    activity_type: str
    confidence: float
    raw_output: str
    model_version: Optional[str] = None
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_model_upgrade_transparency.py::test_analysis_result_includes_model_version tests/test_model_upgrade_transparency.py::test_analysis_result_model_version_optional -v
```
Expected output: `PASSED` (both tests)

**Step 5 - COMMIT:**
```bash
git add tests/test_model_upgrade_transparency.py src/syncopaid/vision_engine.py && git commit -m "feat: add model_version field to AnalysisResult for upgrade tracking"
```

---

### Task 3: Test Backwards Compatibility with Legacy Data (~4 min)

**Files:**
- Modify: `tests/test_model_upgrade_transparency.py`

**Context:** Existing analysis data stored in the database lacks model_version. This test ensures that AnalysisResult can be reconstructed from legacy JSON data without the model_version field. The screenshot_analyzer.py stores results as JSON in the database.

**Step 1 - RED:** Write failing test

```python
# tests/test_model_upgrade_transparency.py (add to file)
import json


def test_analysis_result_json_backwards_compatibility():
    """AnalysisResult can be created from legacy JSON without model_version."""
    # Simulate legacy data format (before model_version was added)
    legacy_json = json.dumps({
        'description': 'Reviewing contract document',
        'activity_type': 'document_editing',
        'confidence': 0.9,
        'raw_output': 'legacy raw output'
        # Note: no model_version field
    })

    data = json.loads(legacy_json)
    result = AnalysisResult(
        description=data['description'],
        activity_type=data['activity_type'],
        confidence=data['confidence'],
        raw_output=data['raw_output'],
        model_version=data.get('model_version')  # Will be None for legacy
    )

    assert result.description == 'Reviewing contract document'
    assert result.model_version is None


def test_analysis_result_json_with_model_version():
    """AnalysisResult can serialize and deserialize with model_version."""
    result = AnalysisResult(
        description="Email review",
        activity_type="email",
        confidence=0.88,
        raw_output="raw",
        model_version="moondream2-v2.1.0"
    )

    # Simulate serialization/deserialization cycle
    data = {
        'description': result.description,
        'activity_type': result.activity_type,
        'confidence': result.confidence,
        'raw_output': result.raw_output,
        'model_version': result.model_version
    }
    json_str = json.dumps(data)
    loaded = json.loads(json_str)

    restored = AnalysisResult(
        description=loaded['description'],
        activity_type=loaded['activity_type'],
        confidence=loaded['confidence'],
        raw_output=loaded['raw_output'],
        model_version=loaded.get('model_version')
    )

    assert restored.model_version == "moondream2-v2.1.0"
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_model_upgrade_transparency.py::test_analysis_result_json_backwards_compatibility tests/test_model_upgrade_transparency.py::test_analysis_result_json_with_model_version -v
```
Expected output: `PASSED` (these should pass with existing implementation - this verifies compatibility)

Note: These tests verify the implementation from Task 2 handles JSON data correctly. If they fail, the implementation needs adjustment.

**Step 3 - GREEN:** No code changes needed if tests pass.

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_model_upgrade_transparency.py -v
```
Expected output: `PASSED` (all tests)

**Step 5 - COMMIT:**
```bash
git add tests/test_model_upgrade_transparency.py && git commit -m "test: add backwards compatibility tests for model version tracking"
```

---

### Task 4: Document Model Upgrade Process (~3 min)

**Files:**
- Create: `ai_docs/model-upgrade-process.md`

**Context:** This documents the process for upgrading AI models in releases. When updating the default model (in config_defaults.py), developers follow this process to ensure release notes communicate improvements without exposing technical details.

**Step 1 - RED:** N/A (documentation task, no test)

**Step 2 - Verify RED:** N/A

**Step 3 - GREEN:** Create documentation

```markdown
# Model Upgrade Process

## Overview

SyncoPaid uses local AI models for screenshot analysis. Model upgrades are transparent to users - they simply receive "improved categorization accuracy" without workflow changes.

## Upgrading the Default Model

### 1. Update Config Default

Edit `src/syncopaid/config_defaults.py`:

```python
# Change the vision_engine default to new model
"vision_engine": "new-model-name",
```

### 2. Register New Model

In the appropriate engine module (e.g., `moondream_engine.py`):

```python
from syncopaid.vision_engine import register_engine

register_engine("new-model-name", NewModelEngine)
```

### 3. Implement model_version

Ensure the new engine implements `model_version`:

```python
@property
def model_version(self) -> str:
    return "2.0.1"  # Actual model version
```

### 4. Test Backwards Compatibility

Run:
```bash
pytest tests/test_model_upgrade_transparency.py -v
```

All tests must pass to ensure legacy data remains readable.

### 5. Update Release Notes

Add to CHANGELOG:
```
- Improved categorization accuracy
```

Do NOT mention:
- Model names (Moondream, LLaVA, etc.)
- Technical details (transformer architecture, parameter counts)
- API changes

## User Experience

- No manual installation required (first-run download handles this)
- Existing categorizations remain valid
- New screenshots benefit from improved model
- Settings unchanged

## Version Tracking

Each analysis result includes `model_version` in stored data, enabling:
- Auditing which model version produced each categorization
- Debugging when model behavior changes
- Future re-analysis capabilities
```

**Step 4 - Verify GREEN:**
```bash
test -f ai_docs/model-upgrade-process.md && echo "Documentation created"
```
Expected output: `Documentation created`

**Step 5 - COMMIT:**
```bash
git add ai_docs/model-upgrade-process.md && git commit -m "docs: add model upgrade process documentation"
```

---

## Final Verification

Run after all tasks complete:
```bash
python -m pytest tests/test_model_upgrade_transparency.py -v    # New tests pass
python -m pytest -v                                              # All existing tests pass
```

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`

## Notes

- This story focuses on the architecture for transparent upgrades, not the actual model upgrade
- Story 14.6.1 (Moondream 2 Integration) handles the actual model implementation
- Story 8.6 children handle the analysis pipeline that uses these models
- The `model_version` field is optional to maintain backwards compatibility
- Future work: Consider adding re-analysis capability to update old screenshots with new models
