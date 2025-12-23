# 031C: Night Processor App Integration
Story ID: 15.2

## Task
Integrate NightProcessor into the main SyncoPaidApp class.

## Context
This is the third and final sub-plan for Story 15.2 (Night Processing Mode). This wires the NightProcessor into the app lifecycle.

## Scope
- Import and instantiate NightProcessor in main_app_class.py
- Wire start/stop into app lifecycle
- Add helper methods for callback integration

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/main_app_class.py` | Integrate NightProcessor |

## Implementation

### 1. Import Statement

```python
# src/syncopaid/main_app_class.py - Add import at top
from syncopaid.night_processor import NightProcessor
```

### 2. Initialize in __init__

Add after screenshot_worker initialization:

```python
# Initialize night processor (if enabled)
self.night_processor = None
if self.config.night_processing_enabled:
    self.night_processor = NightProcessor(
        start_hour=self.config.night_processing_start_hour,
        end_hour=self.config.night_processing_end_hour,
        idle_threshold_minutes=self.config.night_processing_idle_minutes,
        batch_size=self.config.night_processing_batch_size,
        get_idle_seconds=self._get_current_idle_seconds,
        get_pending_count=self.database.get_pending_screenshot_count,
        process_batch=self._process_screenshot_batch,
        enabled=True
    )
```

### 3. Helper Methods

Add these methods to SyncoPaidApp:

```python
def _get_current_idle_seconds(self) -> float:
    """Get current idle time for night processor."""
    # Use tracker loop's idle tracker if available
    if hasattr(self, 'tracker_loop') and self.tracker_loop:
        return self.tracker_loop.get_idle_seconds()
    return 0.0

def _process_screenshot_batch(self, batch_size: int) -> int:
    """Process a batch of screenshots for night processor."""
    # Use screenshot analyzer if available
    if hasattr(self, 'screenshot_analyzer') and self.screenshot_analyzer:
        return self.screenshot_analyzer.process_batch(batch_size)
    return 0
```

### 4. Start in run()

Add after start_tracking call:

```python
# Start night processor
if self.night_processor:
    self.night_processor.start()
```

### 5. Stop in quit_app()

Add before screenshot_worker shutdown:

```python
# Stop night processor
if self.night_processor:
    self.night_processor.stop()
```

## Verification

```bash
venv\Scripts\activate
python -c "from syncopaid.main_app_class import SyncoPaidApp; print('Import OK')"
# Manual test: Run app briefly and check logs for "Night processor started"
```

## Dependencies
- 031A: Night Processing Config (config fields)
- 031B: Night Processor Module (NightProcessor class)
- 029: Automatic Screenshot Analysis (ScreenshotAnalyzer, database methods)

## Notes
- Night processor is optional - gracefully handles missing components
- Daemon thread ensures clean shutdown on app exit
- Uses existing tracker loop idle detection for efficiency
