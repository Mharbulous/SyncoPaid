# Vision Engine Config Schema - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Story ID:** 14.1 | **Created:** 2025-12-23 | **Stage:** `planned`
**Parent Plan:** 033_local-llm-engine-architecture.md (decomposed)

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

---

**Goal:** Add configuration schema support to VisionEngine for engine-specific settings.

**Approach:** Add a config_schema method to VisionEngine that engines can override to declare their configuration requirements.

**Tech Stack:** Python abc module, existing config system

---

## Story Context

**Title:** Local LLM Engine Architecture
**Description:** Plugin architecture for vision LLM engines enabling easy model swapping

**Acceptance Criteria (subset):**
- [ ] Configuration schema for engine-specific settings

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Sub-plan 033A completed (VisionEngine class exists)
- [ ] Baseline tests pass: `python -m pytest -v`

## Files Affected

| File | Change Type | Purpose |
|------|-------------|---------|
| `tests/test_vision_engine.py` | Modify | Add config schema tests |
| `src/syncopaid/vision_engine.py` | Modify | Add config_schema method |

## TDD Tasks

### Task 1: Add Configuration Schema for Engine Settings (~3 min)

**Files:**
- Modify: `tests/test_vision_engine.py`
- Modify: `src/syncopaid/vision_engine.py`

**Context:** Each engine may need specific settings (model path, precision, timeout). A configuration schema allows engines to declare their settings requirements.

**Step 1 - RED:** Write failing test

```python
# tests/test_vision_engine.py (append)

def test_engine_default_config_schema():
    """Base VisionEngine provides empty config schema."""
    from syncopaid.vision_engine import VisionEngine

    class MinimalEngine(VisionEngine):
        @property
        def name(self) -> str:
            return "Minimal"

        @property
        def model_id(self) -> str:
            return "test/minimal"

        def is_available(self) -> bool:
            return True

        def analyze(self, image_path, prompt=None):
            from syncopaid.vision_engine import AnalysisResult
            return AnalysisResult("test", "test", 1.0, "test")

    engine = MinimalEngine()
    # Base class should provide default empty schema
    assert engine.config_schema() == {}
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_vision_engine.py::test_engine_default_config_schema -v
```
Expected output: `FAILED` (VisionEngine has no config_schema method)

**Step 3 - GREEN:** Add config_schema to VisionEngine

```python
# src/syncopaid/vision_engine.py (add to VisionEngine class, after analyze method)

    def config_schema(self) -> dict:
        """Return configuration schema for this engine.

        Override in subclasses to define engine-specific settings.
        Schema format: {"setting_name": {"type": "str|int|float|bool", "default": value, "options": [...]}}

        Returns:
            Dict defining configuration options, empty by default
        """
        return {}
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_vision_engine.py -v
```
Expected output: `PASSED` (all tests pass)

**Step 5 - COMMIT:**
```bash
git add tests/test_vision_engine.py src/syncopaid/vision_engine.py && git commit -m "feat: add config_schema method for engine-specific settings"
```

---

## Final Verification

Run after all tasks complete:
```bash
python -m pytest tests/test_vision_engine.py -v
```

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`

## Notes

- This is sub-plan B of the vision engine architecture implementation
- Subsequent plan (033C) will add config defaults and get_available_engines helper
