# 004C: UI Automation - Configuration Settings

## Task
Add configuration flags to enable/disable UI automation per application.

## Context
Users should be able to enable/disable UI automation extraction globally and per-application (Outlook, Explorer) via config.json.

## Scope
- Add ui_automation_enabled to DEFAULT_CONFIG
- Add ui_automation_outlook_enabled to DEFAULT_CONFIG
- Add ui_automation_explorer_enabled to DEFAULT_CONFIG
- Update Config dataclass

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/config.py` | Add new config fields |
| `tests/test_config.py` | Test new defaults |

## Implementation

### Step 1: Add to DEFAULT_CONFIG

```python
# src/syncopaid/config.py - add to DEFAULT_CONFIG dict
"ui_automation_enabled": True,
"ui_automation_outlook_enabled": True,
"ui_automation_explorer_enabled": True,
```

### Step 2: Add to Config dataclass

```python
# src/syncopaid/config.py - add fields to Config class
ui_automation_enabled: bool = True
ui_automation_outlook_enabled: bool = True
ui_automation_explorer_enabled: bool = True
```

## Tests

```python
# tests/test_config.py (add)
def test_ui_automation_config_defaults():
    import tempfile
    from pathlib import Path
    from syncopaid.config import ConfigManager

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test_config.json"
        manager = ConfigManager(config_path=config_path)

        assert manager.config.ui_automation_enabled == True
        assert manager.config.ui_automation_outlook_enabled == True
        assert manager.config.ui_automation_explorer_enabled == True
```

## Verification

```bash
venv\Scripts\activate
python -m pytest tests/test_config.py::test_ui_automation_config_defaults -v
python -m syncopaid.config  # Verify module runs
```

## Dependencies
- Task 004B (module creation)

## Next Task
After this: `004D_ui-automation-tracker-integration.md`
