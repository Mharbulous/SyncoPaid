# Configurable Idle Threshold - Implementation Plan

> **TDD Required:** Each task (~2-5 min): Write test → verify RED → Write code → verify GREEN → Commit
> **Zero Context:** This plan assumes the implementer knows nothing about the codebase.

**Goal:** Add validation for idle threshold configuration (10-600 seconds range) with warning logs and fallback.
**Approach:** Add a validation function in config.py that enforces min/max bounds, logs warnings for invalid values, and falls back to default. Update Config.from_dict() to use validation.
**Tech Stack:** Python 3.11, pytest, syncopaid.config module

---

**Story ID:** 1.2.3 | **Created:** 2025-12-20 | **Stage:** `planned`

---

## Story Context

**Title:** Configurable Idle Threshold
**Description:** Allow users to configure idle detection threshold via config.json with range validation (10-600 seconds).

**Acceptance Criteria:**
- [ ] Config file includes idle_threshold_seconds setting with default (already exists: 180s)
- [ ] TrackerLoop reads threshold from ConfigManager on initialization (already exists)
- [ ] Setting can be updated via config.json and applies on app restart (already exists)
- [ ] Threshold range validation: minimum 10s, maximum 600s (10 min)
- [ ] Invalid values log warning and fallback to default

## Prerequisites

- [ ] venv activated: `venv\Scripts\activate`
- [ ] Baseline tests pass: `python -m pytest -v`

## TDD Tasks

### Task 1: Add test for valid idle threshold range (~3 min)

**Files:**
- **Create:** `tests/test_config_validation.py`

**Context:** We need to ensure that idle_threshold_seconds values within valid range (10-600) are accepted without modification. This test establishes the valid case before we add validation.

**Step 1 - RED:** Write failing test
```python
# tests/test_config_validation.py
"""Tests for configuration validation."""

import pytest
from syncopaid.config import Config


def test_idle_threshold_valid_range_accepted():
    """Valid idle threshold values (10-600s) should be accepted as-is."""
    # Test minimum valid value
    config = Config.from_dict({'idle_threshold_seconds': 10})
    assert config.idle_threshold_seconds == 10

    # Test maximum valid value
    config = Config.from_dict({'idle_threshold_seconds': 600})
    assert config.idle_threshold_seconds == 600

    # Test middle value
    config = Config.from_dict({'idle_threshold_seconds': 180})
    assert config.idle_threshold_seconds == 180
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_config_validation.py::test_idle_threshold_valid_range_accepted -v
```
Expected output: `PASSED` (this tests existing behavior, so it should pass)

**Step 3 - GREEN:** No code changes needed - this validates existing behavior works.

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_config_validation.py::test_idle_threshold_valid_range_accepted -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_config_validation.py && git commit -m "test: add baseline test for valid idle threshold range"
```

---

### Task 2: Add test for idle threshold below minimum (~3 min)

**Files:**
- **Modify:** `tests/test_config_validation.py`

**Context:** Values below 10 seconds should be rejected with a warning logged and fallback to default (180s). This test will fail until we add validation.

**Step 1 - RED:** Write failing test
```python
# tests/test_config_validation.py (add to existing file)
import logging


def test_idle_threshold_below_minimum_falls_back_to_default(caplog):
    """Idle threshold below 10s should fallback to default with warning."""
    with caplog.at_level(logging.WARNING):
        config = Config.from_dict({'idle_threshold_seconds': 5})

    # Should fallback to default (180s)
    assert config.idle_threshold_seconds == 180.0

    # Should log warning
    assert any('idle_threshold_seconds' in record.message.lower()
               for record in caplog.records)
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_config_validation.py::test_idle_threshold_below_minimum_falls_back_to_default -v
```
Expected output: `FAILED` (test should fail because value 5 is accepted without validation)

**Step 3 - GREEN:** Add validation function to config.py

```python
# src/syncopaid/config.py (add after DEFAULT_CONFIG, around line 40)

# Validation constants
IDLE_THRESHOLD_MIN = 10.0
IDLE_THRESHOLD_MAX = 600.0
IDLE_THRESHOLD_DEFAULT = 180.0


def validate_idle_threshold(value: float) -> float:
    """
    Validate idle_threshold_seconds value.

    Args:
        value: The idle threshold value to validate

    Returns:
        The validated value, or default if invalid

    Valid range: 10-600 seconds (10 seconds to 10 minutes)
    Invalid values log a warning and return the default (180s).
    """
    try:
        value = float(value)
    except (TypeError, ValueError):
        logging.warning(
            f"Invalid idle_threshold_seconds value '{value}': not a number. "
            f"Using default: {IDLE_THRESHOLD_DEFAULT}s"
        )
        return IDLE_THRESHOLD_DEFAULT

    if value < IDLE_THRESHOLD_MIN:
        logging.warning(
            f"idle_threshold_seconds value {value}s is below minimum ({IDLE_THRESHOLD_MIN}s). "
            f"Using default: {IDLE_THRESHOLD_DEFAULT}s"
        )
        return IDLE_THRESHOLD_DEFAULT

    if value > IDLE_THRESHOLD_MAX:
        logging.warning(
            f"idle_threshold_seconds value {value}s exceeds maximum ({IDLE_THRESHOLD_MAX}s). "
            f"Using default: {IDLE_THRESHOLD_DEFAULT}s"
        )
        return IDLE_THRESHOLD_DEFAULT

    return value
```

Then update `Config.from_dict()` method (around line 96-103):

```python
# src/syncopaid/config.py - modify from_dict method
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Create config from dictionary."""
        # Filter only known fields
        valid_fields = {
            k: v for k, v in data.items()
            if k in cls.__dataclass_fields__
        }

        # Apply validation for idle_threshold_seconds
        if 'idle_threshold_seconds' in valid_fields:
            valid_fields['idle_threshold_seconds'] = validate_idle_threshold(
                valid_fields['idle_threshold_seconds']
            )

        return cls(**valid_fields)
```

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_config_validation.py::test_idle_threshold_below_minimum_falls_back_to_default -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_config_validation.py src/syncopaid/config.py && git commit -m "feat: add validation for idle threshold below minimum"
```

---

### Task 3: Add test for idle threshold above maximum (~2 min)

**Files:**
- **Modify:** `tests/test_config_validation.py`

**Context:** Values above 600 seconds should also be rejected with warning and fallback. This tests the upper bound.

**Step 1 - RED:** Write failing test
```python
# tests/test_config_validation.py (add to existing file)

def test_idle_threshold_above_maximum_falls_back_to_default(caplog):
    """Idle threshold above 600s should fallback to default with warning."""
    with caplog.at_level(logging.WARNING):
        config = Config.from_dict({'idle_threshold_seconds': 700})

    # Should fallback to default (180s)
    assert config.idle_threshold_seconds == 180.0

    # Should log warning
    assert any('idle_threshold_seconds' in record.message.lower()
               for record in caplog.records)
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_config_validation.py::test_idle_threshold_above_maximum_falls_back_to_default -v
```
Expected output: `PASSED` (validation already handles this case from Task 2)

**Step 3 - GREEN:** No additional code needed - Task 2 already implemented max validation.

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_config_validation.py::test_idle_threshold_above_maximum_falls_back_to_default -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_config_validation.py && git commit -m "test: add test for idle threshold above maximum"
```

---

### Task 4: Add test for non-numeric idle threshold value (~2 min)

**Files:**
- **Modify:** `tests/test_config_validation.py`

**Context:** Non-numeric values (strings, None) should be handled gracefully with fallback and warning.

**Step 1 - RED:** Write failing test
```python
# tests/test_config_validation.py (add to existing file)

def test_idle_threshold_non_numeric_falls_back_to_default(caplog):
    """Non-numeric idle threshold should fallback to default with warning."""
    with caplog.at_level(logging.WARNING):
        config = Config.from_dict({'idle_threshold_seconds': 'invalid'})

    # Should fallback to default (180s)
    assert config.idle_threshold_seconds == 180.0

    # Should log warning
    assert any('idle_threshold_seconds' in record.message.lower()
               for record in caplog.records)
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_config_validation.py::test_idle_threshold_non_numeric_falls_back_to_default -v
```
Expected output: `PASSED` (validation already handles this from Task 2)

**Step 3 - GREEN:** No additional code needed - Task 2 already handles type conversion.

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_config_validation.py::test_idle_threshold_non_numeric_falls_back_to_default -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_config_validation.py && git commit -m "test: add test for non-numeric idle threshold values"
```

---

### Task 5: Verify validation works via ConfigManager load (~3 min)

**Files:**
- **Modify:** `tests/test_config_validation.py`

**Context:** Ensure validation also applies when loading config from file via ConfigManager, not just from_dict().

**Step 1 - RED:** Write failing test
```python
# tests/test_config_validation.py (add to existing file)
import tempfile
import json
from pathlib import Path
from syncopaid.config import ConfigManager


def test_config_manager_validates_idle_threshold_on_load(caplog, tmp_path):
    """ConfigManager should validate idle_threshold when loading from file."""
    # Create config file with invalid value
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({'idle_threshold_seconds': 5}))

    with caplog.at_level(logging.WARNING):
        manager = ConfigManager(config_path=config_file)

    # Should fallback to default
    assert manager.config.idle_threshold_seconds == 180.0

    # Should have logged warning
    assert any('idle_threshold_seconds' in record.message.lower()
               for record in caplog.records)
```

**Step 2 - Verify RED:**
```bash
pytest tests/test_config_validation.py::test_config_manager_validates_idle_threshold_on_load -v
```
Expected output: `PASSED` (ConfigManager.load() uses Config.from_dict() which now validates)

**Step 3 - GREEN:** No additional code needed - ConfigManager already uses from_dict().

**Step 4 - Verify GREEN:**
```bash
pytest tests/test_config_validation.py::test_config_manager_validates_idle_threshold_on_load -v
```
Expected output: `PASSED`

**Step 5 - COMMIT:**
```bash
git add tests/test_config_validation.py && git commit -m "test: verify ConfigManager validates idle threshold on load"
```

---

## Final Verification

Run after all tasks complete:
```bash
python -m pytest -v                    # All tests pass
python -m syncopaid.config             # Module runs without error
```

## Rollback

If issues arise: `git log --oneline -10` to find commit, then `git revert <hash>`

## Notes

- The story description mentions "30s default" but current codebase uses 180s (3 minutes). This plan uses 180s as it's more realistic for legal billing (aligns with minimum_idle_duration).
- Validation is applied in `Config.from_dict()` which is used by both direct instantiation and file loading via ConfigManager.
- Edge case: If user sets exactly 10s or 600s, those values are accepted (inclusive bounds).
- The validation constants (IDLE_THRESHOLD_MIN/MAX/DEFAULT) are defined at module level for easy adjustment if requirements change.
