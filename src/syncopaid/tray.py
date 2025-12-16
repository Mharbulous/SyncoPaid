"""
System tray UI module for SyncoPaid.

Provides a minimal system tray interface with:
- State-specific icons:
  - stopwatch-pictogram-green = tracking active
  - stopwatch-pictogram-orange = user manually paused (with ❚❚ overlay)
  - stopwatch-pictogram-faded = no activity for 5min (with 💤 overlay)
- Right-click menu with Start/Pause, View Time, Start with Windows, About
- Notifications for key events
"""

import logging
import threading
from typing import Callable, Optional, TYPE_CHECKING
from pathlib import Path

# Platform detection
import sys
WINDOWS = sys.platform == 'win32'

# Windows registry for startup management
if WINDOWS:
    import winreg

# Version info
try:
    from syncopaid import __product_version__
except ImportError:
    __product_version__ = "1.0.0"  # Fallback if not yet generated

try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    Image = None  # Dummy for type hints
    ImageDraw = None
    logging.warning("pystray not available. Install with: pip install pystray Pillow")


# ============================================================================
# PYINSTALLER RESOURCE PATH HELPER
# ============================================================================

def get_resource_path(relative_path: str) -> Path:
    """
    Get absolute path to resource, works for dev and for PyInstaller.

    In development: uses __file__ to locate resources relative to source
    In PyInstaller exe: uses sys._MEIPASS to locate bundled resources

    Args:
        relative_path: Path relative to syncopaid package (e.g., "assets/icon.ico")

    Returns:
        Absolute Path to the resource
    """
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        base_path = Path(sys._MEIPASS)
        return base_path / "syncopaid" / relative_path
    else:
        # Running in development
        return Path(__file__).parent / relative_path


# ============================================================================
# WINDOWS STARTUP REGISTRY HELPERS
# ============================================================================

def is_startup_enabled() -> bool:
    """
    Check if the application is set to start with Windows.

    Returns:
        True if startup is enabled, False otherwise.
    """
    if not WINDOWS:
        return False

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ
        )
        try:
            value, _ = winreg.QueryValueEx(key, "SyncoPaid")
            winreg.CloseKey(key)
            return bool(value)
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
    except Exception as e:
        logging.error(f"Error checking startup status: {e}")
        return False


def _get_canonical_exe_path() -> str:
    """
    Get the canonical executable path for registry startup.

    If running as an old executable name (e.g., TimeLawg.exe) but
    SyncoPaid.exe exists in the same directory, returns the path
    to SyncoPaid.exe instead. This enables seamless migration when
    both files are deployed to a shared location.

    Returns:
        Path to SyncoPaid.exe if available, otherwise current executable.
    """
    current_exe = Path(sys.executable)
    current_name = current_exe.name.lower()

    # If already running as SyncoPaid.exe, use current path
    if current_name == 'syncopaid.exe':
        return str(current_exe)

    # Check if SyncoPaid.exe exists in the same directory
    syncopaid_exe = current_exe.parent / 'SyncoPaid.exe'
    if syncopaid_exe.exists():
        logging.info(f"Migration: using {syncopaid_exe} instead of {current_exe}")
        return str(syncopaid_exe)

    # Fall back to current executable
    return str(current_exe)


def enable_startup() -> bool:
    """
    Enable the application to start with Windows.

    Adds a registry entry pointing to SyncoPaid.exe. If running as an
    old executable (e.g., TimeLawg.exe), will point to SyncoPaid.exe
    in the same directory if it exists.

    Returns:
        True if successful, False otherwise.
    """
    if not WINDOWS:
        logging.warning("Startup management only available on Windows")
        return False

    try:
        # Get the current executable path
        exe_path = sys.executable

        # Only enable startup for compiled executables, not python.exe
        if exe_path.lower().endswith(('python.exe', 'pythonw.exe')):
            logging.info("Running in development mode - startup not enabled")
            return False

        # Get canonical path (migrates to SyncoPaid.exe if available)
        exe_path = _get_canonical_exe_path()

        # Open/create the registry key
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )

        # Set the value
        winreg.SetValueEx(key, "SyncoPaid", 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)

        logging.info(f"Startup enabled: {exe_path}")
        return True

    except Exception as e:
        logging.error(f"Error enabling startup: {e}")
        return False


def disable_startup() -> bool:
    """
    Disable the application from starting with Windows.

    Removes the registry entry.

    Returns:
        True if successful, False otherwise.
    """
    if not WINDOWS:
        logging.warning("Startup management only available on Windows")
        return False

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )

        try:
            winreg.DeleteValue(key, "SyncoPaid")
            winreg.CloseKey(key)
            logging.info("Startup disabled")
            return True
        except FileNotFoundError:
            # Value doesn't exist - that's fine
            winreg.CloseKey(key)
            return True

    except Exception as e:
        logging.error(f"Error disabling startup: {e}")
        return False


def _migrate_old_startup_entry() -> bool:
    """
    Migrate old TimeLawg registry entry to SyncoPaid.

    Removes the old "TimeLawg" entry if it exists.

    Returns:
        True if migration was performed, False otherwise.
    """
    if not WINDOWS:
        return False

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE | winreg.KEY_READ
        )

        try:
            # Check if old entry exists
            winreg.QueryValueEx(key, "TimeLawg")
            # If we get here, old entry exists - delete it
            winreg.DeleteValue(key, "TimeLawg")
            winreg.CloseKey(key)
            logging.info("Migrated: removed old TimeLawg registry entry")
            return True
        except FileNotFoundError:
            # Old entry doesn't exist - nothing to migrate
            winreg.CloseKey(key)
            return False

    except Exception as e:
        logging.error(f"Error migrating old startup entry: {e}")
        return False


def sync_startup_registry(start_on_boot: bool) -> bool:
    """
    Sync the Windows startup registry entry to match the config setting.

    This should be called on every app startup to ensure:
    1. Old TimeLawg entries are migrated
    2. Registry matches the user's saved preference
    3. Executable path is current (handles moves/renames)

    Args:
        start_on_boot: The user's preference from config

    Returns:
        True if registry now matches the desired state, False on error.
    """
    if not WINDOWS:
        return False

    # First, migrate any old TimeLawg entry
    _migrate_old_startup_entry()

    # Now sync registry to match config
    if start_on_boot:
        return enable_startup()
    else:
        return disable_startup()


class TrayIcon:
    """
    System tray icon manager.

    Provides a simple interface for controlling the tracker with three states:
    - stopwatch-pictogram-green = tracking active
    - stopwatch-pictogram-orange + ❚❚ overlay = user manually paused
    - stopwatch-pictogram-faded + 💤 overlay = no activity for 5min

    Menu options:
    - Start/Pause Tracking
    - View Time...
    - Start with Windows
    - About
    - Quit
    """

    def __init__(
        self,
        on_start: Optional[Callable] = None,
        on_pause: Optional[Callable] = None,
        on_view_time: Optional[Callable] = None,
        on_quit: Optional[Callable] = None,
        config_manager=None
    ):
        """
        Initialize system tray icon.

        Args:
            on_start: Callback for "Start Tracking" menu item
            on_pause: Callback for "Pause Tracking" menu item
            on_view_time: Callback for "View Time" menu item
            on_quit: Callback for "Quit" menu item
            config_manager: ConfigManager instance for persisting settings
        """
        self.on_start = on_start or (lambda: None)
        self.on_pause = on_pause or (lambda: None)
        self.on_view_time = on_view_time or (lambda: None)
        self.on_quit = on_quit or (lambda: None)
        self.config_manager = config_manager

        self.icon: Optional[pystray.Icon] = None
        self.is_tracking = True
        self.is_inactive = False  # True when no activity for 5 minutes

        if not TRAY_AVAILABLE:
            logging.error("System tray not available - pystray not installed")
    
    def create_icon_image(self, state: str = "on") -> Optional["Image.Image"]:
        """
        Create system tray icon using state-specific icon files.

        Args:
            state: One of "on" (tracking), "paused" (user paused), "inactive" (no activity)

        Returns:
            PIL Image object for the icon
        """
        if not TRAY_AVAILABLE:
            return None

        size = 64

        # Select icon file based on state
        # Active (on): green stopwatch
        # Paused: orange stopwatch (user clicked pause)
        # Inactive: faded stopwatch with sleep emoji overlay (5min idle)
        if state == "inactive":
            ico_path = get_resource_path("assets/stopwatch-pictogram-faded.ico")
        elif state == "paused":
            ico_path = get_resource_path("assets/stopwatch-pictogram-orange.ico")
        else:  # "on" or default
            ico_path = get_resource_path("assets/stopwatch-pictogram-green.ico")

        image = None
        if ico_path.exists():
            try:
                # Open ICO and get the best size for system tray
                ico = Image.open(ico_path)
                # ICO files contain multiple sizes; resize to target
                image = ico.convert('RGBA')
                image = image.resize((size, size), Image.Resampling.LANCZOS)
            except Exception as e:
                logging.warning(f"Could not load ICO icon: {e}")

        if image is None:
            # Fallback to blank canvas if no icon found
            image = Image.new('RGBA', (size, size), (0, 0, 0, 0))

        # Add overlays based on state
        if state == "inactive":
            image = self._add_sleep_overlay(image)
        elif state == "paused":
            image = self._add_pause_overlay(image)

        return image

    def _add_sleep_overlay(self, image: "Image.Image") -> "Image.Image":
        """
        Add a 💤 overlay to the icon for inactive state.

        Args:
            image: Base icon image

        Returns:
            Image with sleep overlay composited
        """
        from PIL import ImageFont

        size = image.size[0]
        overlay_size = size // 2  # Sleep emoji takes up half the icon

        # Create overlay with sleep emoji
        overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Try to use Windows emoji font, fall back to text "zzz"
        emoji_text = "💤"
        fallback_text = "zzz"

        try:
            # Windows has Segoe UI Emoji font
            font = ImageFont.truetype("seguiemj.ttf", overlay_size)
            text = emoji_text
        except Exception:
            try:
                # Fallback to any available font
                font = ImageFont.truetype("arial.ttf", overlay_size // 2)
                text = fallback_text
            except Exception:
                # Last resort: default font
                font = ImageFont.load_default()
                text = fallback_text

        # Position in bottom-right corner
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = size - text_width - 2
        y = size - text_height - 2

        # Draw with slight shadow for visibility
        draw.text((x + 1, y + 1), text, font=font, fill=(0, 0, 0, 128))
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))

        # Composite overlay onto base image
        return Image.alpha_composite(image, overlay)

    def _add_pause_overlay(self, image: "Image.Image") -> "Image.Image":
        """
        Add a ❚❚ overlay to the icon for paused state.

        Args:
            image: Base icon image

        Returns:
            Image with pause overlay composited
        """
        from PIL import ImageFont

        size = image.size[0]
        overlay_size = size // 2

        # Create overlay with pause symbol
        overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        text = "❚❚"

        try:
            # Use a font that renders the pause bars well
            font = ImageFont.truetype("arial.ttf", overlay_size)
        except Exception:
            font = ImageFont.load_default()

        # Position in bottom-right corner
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = size - text_width - 2
        y = size - text_height - 2

        # Draw with shadow for visibility
        draw.text((x + 1, y + 1), text, font=font, fill=(0, 0, 0, 128))
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))

        # Composite overlay onto base image
        return Image.alpha_composite(image, overlay)

    def _get_current_state(self) -> str:
        """Get the current icon state based on tracking and inactive flags."""
        if not self.is_tracking:
            return "paused"
        elif self.is_inactive:
            return "inactive"
        else:
            return "on"
    
    def update_icon_status(self, is_tracking: bool):
        """
        Update icon based on tracking status (user pause/unpause).

        Args:
            is_tracking: True if tracking, False if user paused
        """
        self.is_tracking = is_tracking
        if is_tracking:
            self.is_inactive = False  # Clear inactive when user resumes

        self._refresh_icon()

    def set_inactive(self, inactive: bool):
        """
        Set inactive state (no activity detected for 5 minutes).

        This shows the faded icon with sleep emoji. Only applies when
        is_tracking is True (user hasn't manually paused).

        Args:
            inactive: True if no activity detected, False when activity resumes
        """
        if self.is_inactive != inactive:
            self.is_inactive = inactive
            if self.is_tracking:  # Only update if not manually paused
                self._refresh_icon()
                if inactive:
                    logging.info("User inactive - showing sleep icon")
                else:
                    logging.info("User active - showing normal icon")

    def _refresh_icon(self):
        """Refresh the icon based on current state."""
        if self.icon:
            state = self._get_current_state()
            self.icon.icon = self.create_icon_image(state)
            # Update tooltip to reflect state
            if state == "paused":
                self.icon.title = f"SyncoPaid v{__product_version__} - Paused"
            elif state == "inactive":
                self.icon.title = f"SyncoPaid v{__product_version__} - Inactive"
            else:
                self.icon.title = f"SyncoPaid v{__product_version__}"
    
    def _create_menu(self):
        """Create the right-click menu."""
        if not TRAY_AVAILABLE:
            return None

        return pystray.Menu(
            pystray.MenuItem(
                lambda text: "⏸ Pause Tracking" if self.is_tracking else "▶ Start Tracking",
                self._toggle_tracking,
                default=True
            ),
            pystray.MenuItem("📊 View Time...", self._handle_view_time),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "🚀 Start with Windows",
                self._toggle_startup,
                checked=lambda item: is_startup_enabled()
            ),
            pystray.MenuItem("ℹ About", self._handle_about)
            # Quit option removed - use command field with "quit" command
        )
    
    def _toggle_tracking(self, icon, item):
        """Handle Start/Pause tracking menu item."""
        if self.is_tracking:
            logging.info("User paused tracking from tray menu")
            self.on_pause()
            self.is_tracking = False
        else:
            logging.info("User started tracking from tray menu")
            self.on_start()
            self.is_tracking = True
            self.is_inactive = False  # Clear inactive when user resumes

        self._refresh_icon()
    
    def _handle_view_time(self, icon, item):
        """Handle View Time menu item."""
        logging.info("User clicked View Time from tray menu")
        self.on_view_time()

    def _toggle_startup(self, icon, item):
        """Handle Start with Windows toggle."""
        current_state = is_startup_enabled()
        new_state = not current_state

        if new_state:
            # Enable startup
            success = enable_startup()
            if success:
                logging.info("User enabled startup from tray menu")
            else:
                logging.error("Failed to enable startup")
        else:
            # Disable startup
            success = disable_startup()
            if success:
                logging.info("User disabled startup from tray menu")
            else:
                logging.error("Failed to disable startup")

        # Save the setting to config so it persists
        if success and self.config_manager:
            self.config_manager.update(start_on_boot=new_state)
            logging.info(f"Saved start_on_boot={new_state} to config")

        # Force menu update to reflect new state
        if self.icon:
            self.icon.update_menu()

    def _handle_about(self, icon, item):
        """Handle About menu item."""
        logging.info("User clicked About from tray menu")
        # TODO: Show about dialog
        print("\n" + "="*50)
        print(f"SyncoPaid v{__product_version__}")
        print("Windows 11 automatic time tracking for lawyers")
        print("="*50 + "\n")
    
    def _handle_quit(self, icon, item):
        """Handle Quit menu item."""
        logging.info("User quit from tray menu")
        # Stop the tray icon first to release the event loop
        if self.icon:
            self.icon.stop()
        # Then run cleanup callback (which may call sys.exit)
        self.on_quit()
    
    def run(self):
        """
        Start the system tray icon.
        
        This is a blocking call that runs the tray icon event loop.
        Should be called from the main thread.
        """
        if not TRAY_AVAILABLE:
            logging.error("Cannot run system tray - pystray not available")
            # Fallback: run a simple console interface
            self._run_console_fallback()
            return
        
        self.icon = pystray.Icon(
            "SyncoPaid_tracker",
            self.create_icon_image(self._get_current_state()),
            f"SyncoPaid v{__product_version__}",
            menu=self._create_menu()
        )
        
        logging.info("System tray icon starting...")
        self.icon.run()
    
    def _run_console_fallback(self):
        """
        Fallback console interface when system tray is unavailable.
        
        Provides basic commands: start, pause, export, quit.
        """
        print("\n" + "="*60)
        print("SyncoPaid Tracker - Console Mode")
        print("(System tray not available)")
        print("="*60)
        print("\nCommands:")
        print("  start  - Start tracking")
        print("  pause  - Pause tracking")
        print("  view   - View time (last 24h)")
        print("  quit   - Quit application")
        print("\n")
        
        while True:
            try:
                cmd = input("SyncoPaid> ").strip().lower()
                
                if cmd == "start":
                    print("▶ Starting tracking...")
                    self.is_tracking = True
                    self.on_start()
                
                elif cmd == "pause":
                    print("⏸ Pausing tracking...")
                    self.is_tracking = False
                    self.on_pause()
                
                elif cmd == "view":
                    print("📊 View time...")
                    self.on_view_time()
                
                elif cmd == "quit" or cmd == "exit":
                    print("❌ Quitting...")
                    self.on_quit()
                    break
                
                else:
                    print(f"Unknown command: {cmd}")
            
            except (KeyboardInterrupt, EOFError):
                print("\n❌ Quitting...")
                self.on_quit()
                break
    
    def stop(self):
        """Stop the system tray icon."""
        if self.icon:
            self.icon.stop()


# ============================================================================
# MAIN - FOR STANDALONE TESTING
# ============================================================================

if __name__ == "__main__":
    import time
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("Testing TrayIcon...\n")
    
    # Test callbacks
    def on_start():
        print("✓ Start callback triggered")
    
    def on_pause():
        print("✓ Pause callback triggered")
    
    def on_view_time():
        print("✓ View Time callback triggered")
        print("  (In real app: would open view time window)")

    def on_quit():
        print("✓ Quit callback triggered")
        print("  (In real app: would clean up and exit)")

    # Create tray icon
    tray = TrayIcon(
        on_start=on_start,
        on_pause=on_pause,
        on_view_time=on_view_time,
        on_quit=on_quit
    )
    
    if TRAY_AVAILABLE:
        print("Starting system tray icon...")
        print("Right-click the icon in your system tray to test the menu.")
        print("Select 'Quit' to exit.\n")
        tray.run()
    else:
        print("⚠ pystray not available - starting console fallback...")
        tray.run()
