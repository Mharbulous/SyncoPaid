# LawTime Tracker — Setup Guide

This guide walks you through everything needed before starting development with Claude Code.

---

## Prerequisites

Before starting, confirm you have:

- [ ] Windows 11 (the target platform)
- [ ] Python 3.11+ installed ([python.org/downloads](https://www.python.org/downloads/))
- [ ] Git installed ([git-scm.com](https://git-scm.com/download/win))
- [ ] A code editor (VS Code recommended)
- [ ] Claude Code CLI installed

### Verify Python installation

Open PowerShell or Command Prompt:

```powershell
python --version
# Should show: Python 3.11.x or higher

pip --version
# Should show pip version and python path
```

If `python` isn't recognized, you may need to use `py` instead, or add Python to your PATH.

---

## Step 1: Create the GitHub Repository

### Option A: Create on GitHub first (recommended)

1. Go to [github.com/new](https://github.com/new)
2. Repository name: `lawtime-tracker`
3. Description: "Windows 11 activity tracker for legal time billing"
4. Select **Private** (contains your work patterns)
5. Check **Add a README file**
6. Add .gitignore: Select **Python**
7. License: **MIT** (or leave blank for private use)
8. Click **Create repository**

Then clone locally:

```powershell
cd C:\Users\YourName\Projects  # or wherever you keep projects
git clone https://github.com/YourUsername/lawtime-tracker.git
cd lawtime-tracker
```

### Option B: Create locally first

```powershell
mkdir lawtime-tracker
cd lawtime-tracker
git init
```

Create `.gitignore` manually:

```
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Virtual environment
venv/
.venv/
env/

# IDE
.vscode/
.idea/

# Database (contains personal activity data)
*.db

# Exports (contains personal activity data)
exports/

# Distribution
dist/
build/
*.egg-info/

# Local config with personal paths
config.local.json
```

---

## Step 2: Set Up Python Virtual Environment

Always use a virtual environment to isolate dependencies:

```powershell
# Create virtual environment
python -m venv venv

# Activate it (PowerShell)
.\venv\Scripts\Activate.ps1

# If you get an execution policy error, run this first:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Activate it (Command Prompt)
.\venv\Scripts\activate.bat
```

Your prompt should now show `(venv)` prefix.

### Install core dependencies

```powershell
pip install pywin32 psutil pystray Pillow
```

Create `requirements.txt`:

```
pywin32>=306
psutil>=5.9.0
pystray>=0.19.0
Pillow>=10.0.0
```

Save it:

```powershell
pip freeze > requirements.txt
```

---

## Step 3: Verify Core APIs Work

This is critical. Before writing any app code, confirm the Windows APIs work on your machine.

### Test 1: Window title capture

Create `test_window.py`:

```python
"""Test window title capture on Windows 11."""
import win32gui
import win32process
import psutil
import time

def get_active_window():
    """Get the currently active window's info."""
    hwnd = win32gui.GetForegroundWindow()
    title = win32gui.GetWindowText(hwnd)
    
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    try:
        process = psutil.Process(pid).name()
    except psutil.NoSuchProcess:
        process = "unknown"
    
    return {
        "title": title,
        "app": process,
        "pid": pid
    }

if __name__ == "__main__":
    print("Window tracking test - switch between windows to see output")
    print("Press Ctrl+C to stop\n")
    
    last_title = None
    try:
        while True:
            window = get_active_window()
            if window["title"] != last_title:
                print(f"[{window['app']}] {window['title']}")
                last_title = window["title"]
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nTest complete.")
```

Run it:

```powershell
python test_window.py
```

**Expected behavior:** As you click between windows (browser, Word, Outlook, etc.), it should print the window title and application name. Try opening a Word document—you should see the filename in the title.

**If it fails:** You may need to run as Administrator, or pywin32 may need post-install setup:

```powershell
python -m pywin32_postinstall -install
```

### Test 2: Idle detection

Create `test_idle.py`:

```python
"""Test idle detection on Windows 11."""
from ctypes import Structure, windll, c_uint, sizeof, byref
import time

class LASTINPUTINFO(Structure):
    _fields_ = [('cbSize', c_uint), ('dwTime', c_uint)]

def get_idle_seconds():
    """Get seconds since last keyboard/mouse input."""
    info = LASTINPUTINFO()
    info.cbSize = sizeof(info)
    windll.user32.GetLastInputInfo(byref(info))
    millis = windll.kernel32.GetTickCount() - info.dwTime
    return millis / 1000.0

if __name__ == "__main__":
    print("Idle detection test - stop moving mouse/typing to see idle time increase")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            idle = get_idle_seconds()
            print(f"Idle: {idle:.1f} seconds", end="\r")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n\nTest complete.")
```

Run it:

```powershell
python test_idle.py
```

**Expected behavior:** The idle counter increases when you stop moving the mouse and typing. Any input resets it to near zero.

### Test 3: System tray icon

Create `test_tray.py`:

```python
"""Test system tray icon on Windows 11."""
import pystray
from PIL import Image, ImageDraw

def create_icon(color="green"):
    """Create a simple colored circle icon."""
    size = 64
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    colors = {
        "green": (34, 197, 94),
        "yellow": (234, 179, 8),
        "red": (239, 68, 68)
    }
    fill = colors.get(color, colors["green"])
    
    draw.ellipse([4, 4, size-4, size-4], fill=fill)
    return image

def on_quit(icon, item):
    icon.stop()

def on_status(icon, item):
    print("Status clicked!")

if __name__ == "__main__":
    print("System tray test - look for green icon in system tray")
    print("Right-click the icon to see menu, select Quit to exit\n")
    
    icon = pystray.Icon(
        "lawtime_test",
        create_icon("green"),
        "LawTime Test",
        menu=pystray.Menu(
            pystray.MenuItem("Status", on_status),
            pystray.MenuItem("Quit", on_quit)
        )
    )
    
    icon.run()
```

Run it:

```powershell
python test_tray.py
```

**Expected behavior:** A green circle appears in your system tray. Right-click shows a menu with "Status" and "Quit" options.

**Note:** On Windows 11, you may need to click the "^" overflow arrow in the system tray to see the icon.

---

## Step 4: Create Project Structure

Once all tests pass, set up the project structure:

```powershell
# From the lawtime-tracker directory
mkdir lawtime
New-Item lawtime\__init__.py -ItemType File
New-Item lawtime\__main__.py -ItemType File
New-Item lawtime\tracker.py -ItemType File
New-Item lawtime\database.py -ItemType File
New-Item lawtime\exporter.py -ItemType File
New-Item lawtime\tray.py -ItemType File
New-Item lawtime\config.py -ItemType File
```

Your directory should look like:

```
lawtime-tracker/
├── .gitignore
├── README.md
├── requirements.txt
├── venv/                  # Not committed to git
├── test_window.py         # Keep for debugging
├── test_idle.py           # Keep for debugging
├── test_tray.py           # Keep for debugging
└── lawtime/
    ├── __init__.py
    ├── __main__.py        # Entry point
    ├── tracker.py         # Window capture + idle detection loop
    ├── database.py        # SQLite operations
    ├── exporter.py        # JSON export
    ├── tray.py            # System tray UI
    └── config.py          # Settings management
```

### Create minimal __main__.py

```python
"""LawTime Tracker - Entry point."""

def main():
    print("LawTime Tracker")
    print("===============")
    print("This is a placeholder. Implementation coming soon.")

if __name__ == "__main__":
    main()
```

Test it runs:

```powershell
python -m lawtime
```

---

## Step 5: Commit Initial Setup

```powershell
git add .
git commit -m "Initial project setup with verified dependencies"
git push origin main  # If using GitHub
```

---

## Step 6: Prepare for Claude Code

### Copy the PRD into the project

Save `LawTime_Tracker_PRD.md` into your project root. This gives Claude Code the full context.

### Recommended Claude Code workflow

1. **Start with one module at a time.** Don't ask Claude Code to build everything at once.

2. **Suggested order:**
   ```
   1. tracker.py    → Core capture loop (builds on test_window.py and test_idle.py)
   2. database.py   → SQLite storage
   3. config.py     → Settings management  
   4. exporter.py   → JSON export
   5. tray.py       → System tray UI
   6. __main__.py   → Wire everything together
   ```

3. **Example first prompt for Claude Code:**
   ```
   Read the PRD at LawTime_Tracker_PRD.md. 
   
   Build tracker.py with these requirements:
   - get_active_window() function (I've verified this works in test_window.py)
   - get_idle_seconds() function (I've verified this works in test_idle.py)  
   - A TrackerLoop class that:
     - Polls every 1 second
     - Detects when window changes
     - Detects when user goes idle (180 second threshold)
     - Merges consecutive identical window states
     - Yields events that can be stored in a database
   
   Don't implement the database yet - just yield/return the event dicts.
   Include a simple test mode that prints events to console.
   ```

4. **Test each module before moving to the next.** Run it, verify it works, commit.

---

## Troubleshooting

### "python" not recognized

Use `py` instead, or add Python to PATH:
1. Search "Environment Variables" in Windows
2. Edit PATH
3. Add `C:\Users\YourName\AppData\Local\Programs\Python\Python311\` (adjust for your version)

### pywin32 import errors

Run the post-install script:
```powershell
python -m pywin32_postinstall -install
```

### System tray icon not visible

Windows 11 hides overflow icons by default. Click the "^" in the system tray, or:
1. Right-click taskbar → Taskbar settings
2. Other system tray icons → Turn on your app

### Permission errors accessing windows

Some applications (especially admin-level ones) may not report window titles to non-admin processes. Run PowerShell as Administrator if needed during testing.

### Virtual environment not activating

PowerShell execution policy may block scripts:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## Quick Reference

### Activate virtual environment
```powershell
.\venv\Scripts\Activate.ps1
```

### Run the app
```powershell
python -m lawtime
```

### Run tests
```powershell
python test_window.py
python test_idle.py
python test_tray.py
```

### Install new dependency
```powershell
pip install package-name
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Add package-name dependency"
```

### Common git commands
```powershell
git status                    # See what's changed
git add .                     # Stage all changes
git commit -m "Description"   # Commit with message
git push                      # Push to GitHub
git pull                      # Get latest from GitHub
```

---

## Next Steps

Once setup is complete and all tests pass:

1. Open Claude Code in the `lawtime-tracker` directory
2. Start with the first module (tracker.py)
3. Test → Commit → Move to next module
4. Refer to the PRD for data models and requirements

Good luck with the build!
