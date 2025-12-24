# 031A: Night Processing Config Settings
Story ID: 15.2

## Task
Add night processing configuration settings to the config system.

## Context
This is the first sub-plan for Story 15.2 (Night Processing Mode). This task adds the necessary configuration fields before creating the NightProcessor module.

## Scope
- Add 5 config defaults to config_defaults.py
- Add 5 dataclass fields to config_dataclass.py

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/config_defaults.py` | Add night processing settings |
| `src/syncopaid/config_dataclass.py` | Add config fields |

## Implementation

### 1. Config Defaults

```python
# src/syncopaid/config_defaults.py - Add to DEFAULT_CONFIG dict
"night_processing_enabled": True,
"night_processing_start_hour": 18,  # 6 PM
"night_processing_end_hour": 8,     # 8 AM
"night_processing_idle_minutes": 30,
"night_processing_batch_size": 50,
```

### 2. Config Dataclass Fields

```python
# src/syncopaid/config_dataclass.py - Add fields to SyncoPaidConfig
night_processing_enabled: bool = True
night_processing_start_hour: int = 18
night_processing_end_hour: int = 8
night_processing_idle_minutes: int = 30
night_processing_batch_size: int = 50
```

## Verification

```bash
venv\Scripts\activate
python -c "from syncopaid.config_defaults import DEFAULT_CONFIG; assert 'night_processing_enabled' in DEFAULT_CONFIG; print('Defaults OK')"
python -c "from syncopaid.config_dataclass import SyncoPaidConfig; c = SyncoPaidConfig(); assert c.night_processing_enabled == True; print('Dataclass OK')"
python -m syncopaid.config  # Verify new settings appear
```

## Dependencies
None - standalone config task

## Notes
- Sets up config infrastructure for NightProcessor module (031B)
- No tests required for simple config additions
