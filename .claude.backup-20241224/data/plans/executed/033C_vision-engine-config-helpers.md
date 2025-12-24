# Vision Engine Config & Helpers - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 14.1 | **Created:** 2025-12-23 | **Stage:** `planned`
**Parent Plan:** 033_local-llm-engine-architecture.md (decomposed)

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Add vision engine config defaults and helper function to list available engines.

**Approach:** Add default settings for vision engine selection to the main config. Add get_available_engines helper to filter to engines that are ready to use.

**Tech Stack:** Python, existing config system

---

## Story Context

**Title:** Local LLM Engine Architecture
**Description:** Plugin architecture for vision LLM engines enabling easy model swapping

**Acceptance Criteria (subset):**
- [ ] Configuration schema for engine-specific settings
- [ ] Unit tests for engine abstraction layer

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Sub-plans 033A, 033B completed
- [ ] Baseline tests pass: `python -m pytest -v`

## Files Affected

| File | Change Type | Purpose |
|------|-------------|---------|
| `tests/test_config.py` | Modify | Add vision engine config tests |
| `src/syncopaid/config_defaults.py` | Modify | Add vision engine settings |
| `tests/test_vision_engine.py` | Modify | Add get_available_engines test |
| `src/syncopaid/vision_engine.py` | Modify | Add get_available_engines helper |

## TDD Tasks

### Task 1: Add Vision Engine Config Defaults (~2 min)

**Files:**
- Modify: `tests/test_config.py`
- Modify: `src/syncopaid/config_defaults.py`

**Context:** Add default settings for vision engine selection to the main config, allowing users to choose which engine to use.

**Step 1 - RED:** Write failing test

```python
# tests/test_config.py (find existing config tests and add)
# Add this test near other DEFAULT_CONFIG tests

def test_vision_engine_defaults_exist():
    """Vision engine settings exist in DEFAULT_CONFIG."""
    from syncopaid.config_defaults import DEFAULT_CONFIG

    assert "vision_engine" in DEFAULT_CONFIG
    assert "vision_engine_enabled" in DEFAULT_CONFIG
    assert DEFAULT_CONFIG["vision_engine_enabled"] is False  # Disabled by default until models downloaded
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_config.py::test_vision_engine_defaults_exist -v
```
Expected output: `FAILED` (vision_engine not in DEFAULT_CONFIG)

**Step 3 - GREEN:** Add vision engine settings to config_defaults.py

```python
# src/syncopaid/config_defaults.py (add after night_processing settings, before closing brace)
    # Vision engine settings (local LLM for screenshot analysis)
    "vision_engine_enabled": False,  # Disabled until model downloaded
    "vision_engine": "moondream2",   # Default engine (when available)
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_config.py::test_vision_engine_defaults_exist -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_config.py src/syncopaid/config_defaults.py && git commit -m "feat: add vision engine config defaults"
```

---

### Task 2: Add get_available_engines Helper (~2 min)

**Files:**
- Modify: `tests/test_vision_engine.py`
- Modify: `src/syncopaid/vision_engine.py`

**Context:** Convenience function to list only engines that are actually usable (have dependencies installed and models downloaded).

**Step 1 - RED:** Write failing test

```python
# tests/test_vision_engine.py (append)

def test_get_available_engines():
    """get_available_engines returns only engines where is_available() is True."""
    from syncopaid.vision_engine import (
        register_engine, get_available_engines, VisionEngine, AnalysisResult, _registry
    )
    _registry.clear()

    class AvailableEngine(VisionEngine):
        @property
        def name(self) -> str:
            return "Available"

        @property
        def model_id(self) -> str:
            return "test/available"

        def is_available(self) -> bool:
            return True

        def analyze(self, image_path, prompt=None):
            return AnalysisResult("test", "test", 1.0, "test")

    class UnavailableEngine(VisionEngine):
        @property
        def name(self) -> str:
            return "Unavailable"

        @property
        def model_id(self) -> str:
            return "test/unavailable"

        def is_available(self) -> bool:
            return False

        def analyze(self, image_path, prompt=None):
            return AnalysisResult("test", "test", 1.0, "test")

    register_engine("available", AvailableEngine)
    register_engine("unavailable", UnavailableEngine)

    available = get_available_engines()
    assert "available" in available
    assert "unavailable" not in available
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_vision_engine.py::test_get_available_engines -v
```
Expected output: `FAILED` (no function get_available_engines)

**Step 3 - GREEN:** Add get_available_engines function

```python
# src/syncopaid/vision_engine.py (add after get_engine function)

def get_available_engines() -> Dict[str, Type[VisionEngine]]:
    """Get engines that are currently available for use.

    Returns:
        Dict mapping engine names to classes, filtered to only available engines
    """
    available = {}
    for name, engine_class in _registry.items():
        try:
            engine = engine_class()
            if engine.is_available():
                available[name] = engine_class
        except Exception:
            # Skip engines that fail to instantiate
            pass
    return available
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_vision_engine.py -v
```
Expected output: `PASSED` (all tests pass)

**Step 5 - COMMIT:**
```bash
git add tests/test_vision_engine.py src/syncopaid/vision_engine.py && git commit -m "feat: add get_available_engines helper function"
```

---

## Final Verification

Run after all tasks complete:
```bash
python -m pytest -v                          # All tests pass
python -c "from syncopaid.vision_engine import VisionEngine, AnalysisResult, get_registered_engines; print('Vision engine module loads successfully')"
```

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`

## Notes

- This is sub-plan C of the vision engine architecture implementation
- This completes story 14.1 - the foundation for stories 14.2 (Hardware Detection), 14.5 (Model Download), and 14.6.1 (Moondream 2 Integration)
- The cloud LLM (existing llm.py) remains separate - this is for local models only
- Engine implementations (Moondream, LLaVA, etc.) will be added in subsequent stories
- The `is_available()` pattern allows graceful degradation when dependencies aren't installed
