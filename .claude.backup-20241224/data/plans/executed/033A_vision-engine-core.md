# Vision Engine Core - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 14.1 | **Created:** 2025-12-23 | **Stage:** `planned`
**Parent Plan:** 033_local-llm-engine-architecture.md (decomposed)

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Create the abstract VisionEngine base class and engine registration mechanism.

**Approach:** Define an abstract base class `VisionEngine` with a consistent interface (image in, structured data out). Implement engine registration/discovery via a simple registry pattern.

**Tech Stack:** Python abc module, dataclasses, typing

---

## Story Context

**Title:** Local LLM Engine Architecture
**Description:** Plugin architecture for vision LLM engines enabling easy model swapping

**Acceptance Criteria (subset):**
- [ ] Abstract interface for vision LLM engines
- [ ] Engine registration/discovery mechanism
- [ ] Consistent input/output contract (image in, structured data out)

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`

## Files Affected

| File | Change Type | Purpose |
|------|-------------|---------|
| `tests/test_vision_engine.py` | Create | Unit tests for engine abstraction |
| `src/syncopaid/vision_engine.py` | Create | Abstract base class and registry |

## TDD Tasks

### Task 1: Create Abstract VisionEngine Interface (~3 min)

**Files:**
- Create: `tests/test_vision_engine.py`
- Create: `src/syncopaid/vision_engine.py`

**Context:** The abstract interface defines the contract all vision engines must follow. This enables swapping models (Moondream, LLaVA, etc.) without changing the analysis pipeline.

**Step 1 - RED:** Write failing test

```python
# tests/test_vision_engine.py
"""Tests for vision engine abstraction layer."""
import pytest
from pathlib import Path
from syncopaid.vision_engine import VisionEngine, AnalysisResult


def test_vision_engine_is_abstract():
    """VisionEngine cannot be instantiated directly."""
    with pytest.raises(TypeError):
        VisionEngine()


def test_analysis_result_dataclass():
    """AnalysisResult holds structured output from vision analysis."""
    result = AnalysisResult(
        description="User editing Word document",
        activity_type="document_editing",
        confidence=0.85,
        raw_output="User is editing a Word document..."
    )
    assert result.description == "User editing Word document"
    assert result.activity_type == "document_editing"
    assert result.confidence == 0.85
    assert result.raw_output == "User is editing a Word document..."
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_vision_engine.py -v
```
Expected output: `FAILED` (module syncopaid.vision_engine not found)

**Step 3 - GREEN:** Write minimal implementation

```python
# src/syncopaid/vision_engine.py
"""Abstract base class for vision LLM engines.

Defines the interface that all vision engines must implement,
enabling easy swapping of AI models (Moondream, LLaVA, etc.)
without changing the analysis pipeline.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class AnalysisResult:
    """Structured output from vision engine analysis.

    Attributes:
        description: Human-readable description of what the screenshot shows
        activity_type: Categorized activity (e.g., 'document_editing', 'web_browsing')
        confidence: Confidence score 0.0-1.0
        raw_output: Raw model output for debugging/logging
    """
    description: str
    activity_type: str
    confidence: float
    raw_output: str


class VisionEngine(ABC):
    """Abstract base class for vision LLM engines.

    All vision engines must implement the analyze() method
    to provide screenshot analysis capabilities.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the engine's display name (e.g., 'Moondream 2')."""
        pass

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Return the model identifier (e.g., 'vikhyatk/moondream2')."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this engine is available (dependencies installed, model downloaded)."""
        pass

    @abstractmethod
    def analyze(self, image_path: Path, prompt: Optional[str] = None) -> AnalysisResult:
        """Analyze a screenshot and return structured results.

        Args:
            image_path: Path to the screenshot image file
            prompt: Optional custom prompt (uses default if None)

        Returns:
            AnalysisResult with description, activity_type, confidence, raw_output
        """
        pass
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_vision_engine.py -v
```
Expected output: `PASSED` (both tests pass)

**Step 5 - COMMIT:**
```bash
git add tests/test_vision_engine.py src/syncopaid/vision_engine.py && git commit -m "feat: add abstract VisionEngine interface and AnalysisResult dataclass"
```

---

### Task 2: Add Engine Registration Mechanism (~3 min)

**Files:**
- Modify: `tests/test_vision_engine.py`
- Modify: `src/syncopaid/vision_engine.py`

**Context:** The registry pattern allows engines to register themselves on import, enabling auto-discovery of available engines without hardcoding.

**Step 1 - RED:** Write failing test

```python
# tests/test_vision_engine.py (append to existing file)

def test_engine_registry_starts_empty():
    """Engine registry starts with no registered engines."""
    from syncopaid.vision_engine import get_registered_engines, _registry
    _registry.clear()  # Reset for test isolation
    assert get_registered_engines() == {}


def test_register_engine():
    """Engines can be registered by name."""
    from syncopaid.vision_engine import register_engine, get_registered_engines, _registry
    _registry.clear()  # Reset for test isolation

    class MockEngine(VisionEngine):
        @property
        def name(self) -> str:
            return "Mock Engine"

        @property
        def model_id(self) -> str:
            return "mock/engine"

        def is_available(self) -> bool:
            return True

        def analyze(self, image_path, prompt=None):
            return AnalysisResult("mock", "mock", 1.0, "mock")

    register_engine("mock", MockEngine)
    engines = get_registered_engines()

    assert "mock" in engines
    assert engines["mock"] == MockEngine


def test_get_engine_by_name():
    """Can retrieve and instantiate engine by name."""
    from syncopaid.vision_engine import register_engine, get_engine, _registry
    _registry.clear()

    class MockEngine(VisionEngine):
        @property
        def name(self) -> str:
            return "Mock Engine"

        @property
        def model_id(self) -> str:
            return "mock/engine"

        def is_available(self) -> bool:
            return True

        def analyze(self, image_path, prompt=None):
            return AnalysisResult("mock", "mock", 1.0, "mock")

    register_engine("mock", MockEngine)
    engine = get_engine("mock")

    assert isinstance(engine, MockEngine)
    assert engine.name == "Mock Engine"


def test_get_nonexistent_engine_returns_none():
    """Getting a non-registered engine returns None."""
    from syncopaid.vision_engine import get_engine, _registry
    _registry.clear()

    assert get_engine("nonexistent") is None
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_vision_engine.py::test_engine_registry_starts_empty -v
```
Expected output: `FAILED` (no function get_registered_engines)

**Step 3 - GREEN:** Add registry functions to vision_engine.py

```python
# src/syncopaid/vision_engine.py (append after VisionEngine class)

from typing import Dict, Type

# Engine registry - maps engine names to their classes
_registry: Dict[str, Type[VisionEngine]] = {}


def register_engine(name: str, engine_class: Type[VisionEngine]) -> None:
    """Register a vision engine class.

    Args:
        name: Unique identifier for the engine (e.g., 'moondream2')
        engine_class: The VisionEngine subclass to register
    """
    _registry[name] = engine_class


def get_registered_engines() -> Dict[str, Type[VisionEngine]]:
    """Get all registered engine classes.

    Returns:
        Dict mapping engine names to their classes
    """
    return _registry.copy()


def get_engine(name: str) -> Optional[VisionEngine]:
    """Get an instantiated engine by name.

    Args:
        name: The registered engine name

    Returns:
        Instantiated engine or None if not found
    """
    engine_class = _registry.get(name)
    if engine_class is None:
        return None
    return engine_class()
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_vision_engine.py -v
```
Expected output: `PASSED` (all tests pass)

**Step 5 - COMMIT:**
```bash
git add tests/test_vision_engine.py src/syncopaid/vision_engine.py && git commit -m "feat: add engine registration and discovery mechanism"
```

---

## Final Verification

Run after all tasks complete:
```bash
python -m pytest tests/test_vision_engine.py -v
python -c "from syncopaid.vision_engine import VisionEngine, AnalysisResult, get_registered_engines; print('Vision engine module loads successfully')"
```

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`

## Notes

- This is sub-plan A of the vision engine architecture implementation
- Subsequent plans (033B, 033C) will add config schema and helpers
