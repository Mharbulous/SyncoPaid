# 004F: UI Automation - Explorer Folder Path Extraction

## Task
Implement actual Windows Explorer folder path extraction using pywinauto.

## Context
Replace the ExplorerExtractor stub with real extraction logic that finds the address bar in Windows Explorer.

## Scope
- Connect to Explorer process by PID
- Find address bar control (AutomationId "41477" or Edit class)
- Extract current folder path
- Return with timeout protection

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/ui_automation.py` | Implement ExplorerExtractor.extract() |
| `tests/test_ui_automation.py` | Add mock test |

## Implementation

```python
# src/syncopaid/ui_automation.py - ExplorerExtractor.extract()
def extract(self, window_info: Dict) -> Optional[Dict[str, str]]:
    if not PYWINAUTO_AVAILABLE:
        return None

    if 'explorer' not in window_info.get('app', '').lower():
        return None

    pid = window_info.get('pid')
    if not pid:
        return None

    try:
        app = Application(backend='uia').connect(
            process=pid, timeout=self.timeout_ms / 1000.0
        )
        main_window = app.window(pid=pid)

        folder_path = None
        try:
            # AutomationId "41477" is standard for Explorer address bar
            address_bar = main_window.child_window(
                auto_id="41477", control_type="Edit"
            )
            folder_path = address_bar.window_text()
        except Exception:
            try:
                address_bar = main_window.child_window(
                    control_type="Edit", class_name="Edit", found_index=0
                )
                folder_path = address_bar.window_text()
            except Exception:
                pass

        if folder_path:
            return {'folder_path': folder_path}

        return None

    except TimeoutError:
        logging.debug(f"Explorer extraction timeout after {self.timeout_ms}ms")
        return None
    except Exception as e:
        logging.debug(f"Explorer extraction failed: {e}")
        return None
```

## Tests

```python
# tests/test_ui_automation.py (add)
def test_explorer_extractor_returns_folder_path():
    from syncopaid.ui_automation import ExplorerExtractor
    from unittest.mock import MagicMock, patch

    extractor = ExplorerExtractor()

    with patch('syncopaid.ui_automation.Application') as mock_app:
        mock_window = MagicMock()
        mock_address_bar = MagicMock()
        mock_address_bar.window_text.return_value = "C:\\Cases\\Smith_v_Jones"

        mock_window.child_window.return_value = mock_address_bar
        mock_app.return_value.window.return_value = mock_window

        result = extractor.extract({
            'app': 'explorer.exe',
            'title': 'Smith_v_Jones',
            'pid': 5678
        })

        assert result is not None
        assert result['folder_path'] == "C:\\Cases\\Smith_v_Jones"
```

## Verification

```bash
venv\Scripts\activate
python -m pytest tests/test_ui_automation.py::test_explorer_extractor_returns_folder_path -v

# Manual test: Open Explorer, navigate folders, run tracker, check extracted metadata
```

## Final Verification

After completing all sub-plans (004A-004F):

```bash
python -m pytest -v  # All tests pass
python -m syncopaid  # Run app, test with Outlook and Explorer
```

## Dependencies
- Task 004E (Outlook extraction)

## Notes
This completes the UI Automation Integration feature (original story 8.3).

All acceptance criteria from the original plan should now be met:
- Extract email subject/sender from Outlook
- Extract folder path from Explorer
- Store in events table metadata column
- Graceful timeout handling
- Configurable per application
- Performance <100ms per extraction
