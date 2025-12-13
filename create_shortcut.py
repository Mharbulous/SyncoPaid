"""
Create a Windows desktop shortcut with custom icon for TimeLawg.
Run this script once from the activated venv to create the shortcut.
"""
import os
from pathlib import Path
from PIL import Image

# Paths
PROJECT_DIR = Path(__file__).parent
ICON_PNG = PROJECT_DIR / "OrangeClockScale.png"
ICON_ICO = PROJECT_DIR / "TimeLawg.ico"
DESKTOP = Path(os.environ["USERPROFILE"]) / "OneDrive - Logica Law" / "Desktop"
SHORTCUT_PATH = DESKTOP / "TimeLawg.lnk"
BAT_PATH = PROJECT_DIR / "launch_timelawg.bat"

def create_ico():
    """Convert PNG to ICO with multiple sizes."""
    print(f"Converting {ICON_PNG} to ICO format...")
    img = Image.open(ICON_PNG)

    # Create multiple sizes for ICO
    sizes = [(256, 256), (64, 64), (48, 48), (32, 32), (16, 16)]
    img.save(ICON_ICO, format='ICO', sizes=sizes)
    print(f"Created: {ICON_ICO}")

def create_bat():
    """Create the launcher batch file."""
    bat_content = f'''@echo off
cd /d {PROJECT_DIR}
call venv\\Scripts\\activate
start /min pythonw -m timelawg
'''
    BAT_PATH.write_text(bat_content)
    print(f"Created: {BAT_PATH}")

def create_shortcut():
    """Create Windows shortcut with custom icon."""
    try:
        import win32com.client
    except ImportError:
        print("ERROR: pywin32 not available. Run from activated venv.")
        return False

    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(str(SHORTCUT_PATH))
    shortcut.TargetPath = str(BAT_PATH)
    shortcut.WorkingDirectory = str(PROJECT_DIR)
    shortcut.IconLocation = str(ICON_ICO)
    shortcut.Description = "TimeLawg - Automatic time tracking for lawyers"
    shortcut.WindowStyle = 7  # Minimized
    shortcut.save()
    print(f"Created shortcut: {SHORTCUT_PATH}")
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("TimeLawg Desktop Shortcut Creator")
    print("=" * 50)

    # Remove old bat file if exists
    old_bat = DESKTOP / "LawTime V0.1.0.bat"
    if old_bat.exists():
        old_bat.unlink()
        print(f"Removed old: {old_bat}")

    create_ico()
    create_bat()

    if create_shortcut():
        print("\n✓ Desktop shortcut created successfully!")
        print("  Double-click 'TimeLawg' on your desktop to launch.")
    else:
        print("\n✗ Failed to create shortcut")
