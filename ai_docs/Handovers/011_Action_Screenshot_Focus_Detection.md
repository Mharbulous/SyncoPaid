# Handover: Action Screenshot Focus Detection

## Task
Add window focus change detection to action screenshots. Currently in progress - partially implemented.

## What Was Accomplished
1. **Fixed action screenshots not saving** - Root cause was `pynput` not installed (`pip install pynput`)
2. **Added diagnostic logging** - INFO-level logs throughout the capture flow
3. **Fixed hwnd capture timing** - Now captures window handle in callback thread, not worker thread
4. **Fixed drag detection** - Added `drag_start_pos` tracking
5. **Added About menu** to View Time window (shows version + 7-digit commit ID)
6. **Started focus change detection** - Partially implemented, interrupted mid-edit

## Current State of Implementation
File: `lawtime/action_screenshot.py`

**Already added:**
- `total_focus_captures` statistic (line 120)
- Focus monitor state variables (lines 127-130):
  ```python
  self.last_focus_hwnd: Optional[int] = None
  self.focus_monitor_thread: Optional[threading.Thread] = None
  self.focus_monitor_running = False
  self.focus_poll_interval = 0.5
  ```
- Thread creation in `start()` (lines 160-167) - starts `_monitor_focus_changes`

**Still needed:**
1. Add `_monitor_focus_changes()` method - the actual polling loop
2. Update `stop()` to stop the focus monitor thread
3. Update `_capture_action_screenshot()` to handle 'focus' action type
4. Update `shutdown()` logging to include focus captures
5. Update `get_stats()` to include focus captures

## Implementation for `_monitor_focus_changes`
```python
def _monitor_focus_changes(self):
    """Background thread to detect window focus changes."""
    while self.focus_monitor_running:
        try:
            current_hwnd = win32gui.GetForegroundWindow()
            if current_hwnd and current_hwnd != self.last_focus_hwnd:
                if self.last_focus_hwnd is not None:
                    # Focus changed - capture screenshot
                    logging.info(f"Action screenshot: focus change detected ({self.last_focus_hwnd} -> {current_hwnd})")
                    self._capture_action_screenshot('focus')
                self.last_focus_hwnd = current_hwnd
        except Exception as e:
            logging.debug(f"Error in focus monitor: {e}")
        time.sleep(self.focus_poll_interval)
```

## Key Files
| File | Purpose |
|------|---------|
| `lawtime/action_screenshot.py` | Action screenshot worker - **edit this** |
| `lawtime/screenshot.py` | Periodic screenshot worker (reference for patterns) |
| `lawtime/__main__.py` | App coordinator, About menu already added |
| `lawtime/config.py` | Config with `action_screenshot_enabled` |

## User Requirements (from conversation)
1. **Capture on window focus change** - Yes (Alt+Tab, Win+Tab, taskbar, etc.)
2. **Capture on scroll** - No
3. **Deduplication** - Keep both if text changed; over-capture is OK for now
4. **Philosophy** - Over-capture now, refine later

## Edge Cases Discussed
- Alt+Tab, Win+1/2/3, virtual desktop switches need focus detection (no click)
- Taskbar click captures wrong window (captures old window being switched from)
- Double-click: first captured, second throttled (acceptable)

## Not Relevant
- `diagnose_screenshots.py` - Only checks periodic screenshots, not action
- `lawtime/tracker.py` - Handles periodic screenshot submission, not action
- `lawtime/exporter.py` - JSON export, unrelated

## Branch
`claude/fix-screenshot-actions-011QaRyPeGxK2U4gNFH1euEF`

## Test Command
```bash
cd ~/Git/TimeLogger
source venv/Scripts/activate
python -m lawtime
```

Watch for log: `Action screenshot: focus change detected`
