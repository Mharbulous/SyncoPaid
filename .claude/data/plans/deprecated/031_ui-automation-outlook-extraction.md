# 031: UI Automation - Outlook Email Extraction

## Task
Implement actual Outlook email subject and sender extraction using pywinauto.

## Context
Replace the OutlookExtractor stub with real extraction logic that finds the subject and sender fields in Outlook (Legacy) using UI Automation.

## Scope
- Connect to Outlook process by PID
- Find subject control (AutomationId "Subject" or class "_WwG")
- Find sender/from control
- Return extracted values with timeout protection

## Key Files

| File | Purpose |
|------|---------|
| `src/syncopaid/ui_automation.py` | Implement OutlookExtractor.extract() |
| `tests/test_ui_automation.py` | Add mock test |

## Implementation

```python
# src/syncopaid/ui_automation.py - OutlookExtractor.extract()
def extract(self, window_info: Dict) -> Optional[Dict[str, str]]:
    if not PYWINAUTO_AVAILABLE:
        return None

    if 'OUTLOOK' not in window_info.get('app', '').upper():
        return None

    pid = window_info.get('pid')
    if not pid:
        return None

    try:
        app = Application(backend='uia').connect(
            process=pid, timeout=self.timeout_ms / 1000.0
        )
        main_window = app.window(pid=pid)

        # Try to find subject field
        subject_text = None
        try:
            subject_elem = main_window.child_window(
                auto_id="Subject", control_type="Edit"
            )
            subject_text = subject_elem.window_text()
        except Exception:
            try:
                subject_elem = main_window.child_window(
                    class_name="_WwG", found_index=0
                )
                subject_text = subject_elem.window_text()
            except Exception:
                pass

        # Try to find sender field
        sender_text = None
        try:
            sender_elem = main_window.child_window(
                auto_id="From", control_type="Edit"
            )
            sender_text = sender_elem.window_text()
        except Exception:
            pass

        if subject_text:
            result = {'email_subject': subject_text}
            if sender_text:
                result['sender'] = sender_text
            return result

        return None

    except TimeoutError:
        logging.debug(f"Outlook extraction timeout after {self.timeout_ms}ms")
        return None
    except Exception as e:
        logging.debug(f"Outlook extraction failed: {e}")
        return None
```

## Tests

```python
# tests/test_ui_automation.py (add)
def test_outlook_extractor_returns_subject_and_sender():
    from syncopaid.ui_automation import OutlookExtractor
    from unittest.mock import MagicMock, patch

    extractor = OutlookExtractor()

    with patch('syncopaid.ui_automation.Application') as mock_app:
        mock_window = MagicMock()
        mock_subject = MagicMock()
        mock_subject.window_text.return_value = "Re: Smith Case"
        mock_sender = MagicMock()
        mock_sender.window_text.return_value = "client@example.com"

        mock_window.child_window.side_effect = [mock_subject, mock_sender]
        mock_app.return_value.window.return_value = mock_window

        result = extractor.extract({
            'app': 'OUTLOOK.EXE',
            'title': 'Re: Smith Case - Outlook',
            'pid': 1234
        })

        assert result is not None
        assert result['email_subject'] == "Re: Smith Case"
        assert result['sender'] == "client@example.com"
```

## Verification

```bash
venv\Scripts\activate
python -m pytest tests/test_ui_automation.py::test_outlook_extractor_returns_subject_and_sender -v

# Manual test: Open Outlook, run tracker, check extracted metadata
```

## Dependencies
- Task 030 (tracker integration)

## Next Task
After this: `032_ui-automation-explorer-extraction.md`
