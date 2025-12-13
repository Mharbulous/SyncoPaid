# SyncoPaid - Quick Start Guide

Get up and running in 5 minutes.

## Prerequisites

- Windows 11
- Python 3.11+ installed ([python.org](https://www.python.org/downloads/))
- Git (optional, for cloning)

## Installation

1. **Get the code**
   ```bash
   cd C:\Users\YourName\Git
   # (or wherever you keep projects)
   ```

2. **Create virtual environment**
   ```bash
   cd SyncoPaid
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Quick Test

Verify everything works:

```bash
# Test window tracking (switch windows to see output)
python -m SyncoPaid.tracker

# Should print window titles as you switch between apps
```

## Run the App

```bash
python -m SyncoPaid
```

You should see:
- Welcome message in console
- Green icon in system tray (look for "^" overflow area)
- "✓ Tracking started" message

## Use the App

**Right-click the tray icon** to access:
- ⏸ **Pause** - Stop tracking temporarily
- 📤 **Export Data** - Save today's activities to JSON
- ❌ **Quit** - Exit the app

## Export & Process with LLM

1. Work for a few hours with tracking running
2. Right-click tray → Export Data
3. Save as `activity_2025-12-09.json`
4. Open Claude or ChatGPT
5. Paste this prompt:

```
Analyze my work activities and group them by client matter. 
For each matter, calculate total time in 0.1-hour increments 
and generate a billing narrative.

[paste your exported JSON here]

My active matters:
- Smith v. Jones (Contract dispute)
- Johnson Estate (Probate)
```

## File Locations

After first run, files are created at:

```
%LOCALAPPDATA%\SyncoPaid\
├── SyncoPaid.db      # Activity database (DO NOT SHARE - contains your work data)
└── config.json     # Settings (can edit manually)
```

## Tips

1. **File Naming** - Use consistent patterns like `ClientName_DocType.docx` so the LLM can categorize better

2. **Legacy Outlook** - For better email tracking: Help → Revert to Legacy Outlook

3. **Privacy** - All data stays LOCAL. Never uploaded anywhere.

4. **Idle Detection** - Automatically excludes lunch breaks (180 seconds = 3 minutes of inactivity)

## Troubleshooting

**Icon not visible?**
→ Click "^" in system tray, or Settings → Taskbar → Show SyncoPaid icon

**"python not recognized"?**
→ Reinstall Python from python.org with "Add to PATH" checked

**Import errors?**
→ Make sure you're in the virtual environment (you should see `(venv)` in your prompt)

## Next Steps

- Run overnight to test stability
- Export and try categorizing with Claude
- Adjust config in `%LOCALAPPDATA%\SyncoPaid\config.json` if needed
- Read README.md for detailed documentation

## Support

Questions? Open an issue on GitHub or check README.md for detailed docs.

---

**Remember**: This is YOUR data on YOUR machine. Review tracked time before billing clients.
