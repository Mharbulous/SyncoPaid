"""
System tray UI module for LawTime Tracker.

Provides a minimal system tray interface with:
- Status indicator icon (green=tracking, yellow=paused)
- Right-click menu with Start/Pause, Export, Settings, Quit
- Notifications for key events
"""

import logging
import threading
from typing import Callable, Optional
from pathlib import Path

# Platform detection
import sys
WINDOWS = sys.platform == 'win32'

try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    logging.warning("pystray not available. Install with: pip install pystray Pillow")


class TrayIcon:
    """
    System tray icon manager.
    
    Provides a simple interface for controlling the tracker:
    - Green icon = tracking active
    - Yellow icon = tracking paused
    - Red icon = error/stopped
    
    Menu options:
    - Start/Pause Tracking
    - Export Data...
    - Settings...
    - About
    - Quit
    """
    
    def __init__(
        self,
        on_start: Optional[Callable] = None,
        on_pause: Optional[Callable] = None,
        on_export: Optional[Callable] = None,
        on_settings: Optional[Callable] = None,
        on_quit: Optional[Callable] = None
    ):
        """
        Initialize system tray icon.
        
        Args:
            on_start: Callback for "Start Tracking" menu item
            on_pause: Callback for "Pause Tracking" menu item
            on_export: Callback for "Export Data" menu item
            on_settings: Callback for "Settings" menu item
            on_quit: Callback for "Quit" menu item
        """
        self.on_start = on_start or (lambda: None)
        self.on_pause = on_pause or (lambda: None)
        self.on_export = on_export or (lambda: None)
        self.on_settings = on_settings or (lambda: None)
        self.on_quit = on_quit or (lambda: None)
        
        self.icon: Optional[pystray.Icon] = None
        self.is_tracking = True
        
        if not TRAY_AVAILABLE:
            logging.error("System tray not available - pystray not installed")
    
    def create_icon_image(self, color: str = "green") -> Optional[Image.Image]:
        """
        Create a simple colored circle icon.
        
        Args:
            color: Icon color - "green" (tracking), "yellow" (paused), "red" (error)
            
        Returns:
            PIL Image object for the icon
        """
        if not TRAY_AVAILABLE:
            return None
        
        size = 64
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Color mapping
        colors = {
            "green": (34, 197, 94),    # Tracking active
            "yellow": (234, 179, 8),   # Paused
            "red": (239, 68, 68)       # Error/stopped
        }
        fill = colors.get(color, colors["green"])
        
        # Draw circle
        draw.ellipse([4, 4, size-4, size-4], fill=fill)
        
        # Add small "L" text for "LawTime"
        font_size = 32
        draw.text((size//2 - 8, size//2 - 12), "L", fill=(255, 255, 255))
        
        return image
    
    def update_icon_status(self, is_tracking: bool):
        """
        Update icon color based on tracking status.
        
        Args:
            is_tracking: True if tracking, False if paused
        """
        self.is_tracking = is_tracking
        
        if self.icon:
            color = "green" if is_tracking else "yellow"
            self.icon.icon = self.create_icon_image(color)
            self.icon.title = f"LawTime - {'Tracking' if is_tracking else 'Paused'}"
    
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
            pystray.MenuItem("📤 Export Data...", self._handle_export),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("⚙ Settings...", self._handle_settings),
            pystray.MenuItem("ℹ About", self._handle_about),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("❌ Quit", self._handle_quit)
        )
    
    def _toggle_tracking(self, icon, item):
        """Handle Start/Pause tracking menu item."""
        if self.is_tracking:
            logging.info("User paused tracking from tray menu")
            self.on_pause()
        else:
            logging.info("User started tracking from tray menu")
            self.on_start()
        
        # Update icon
        self.is_tracking = not self.is_tracking
        self.update_icon_status(self.is_tracking)
    
    def _handle_export(self, icon, item):
        """Handle Export Data menu item."""
        logging.info("User clicked Export Data from tray menu")
        self.on_export()
    
    def _handle_settings(self, icon, item):
        """Handle Settings menu item."""
        logging.info("User clicked Settings from tray menu")
        self.on_settings()
    
    def _handle_about(self, icon, item):
        """Handle About menu item."""
        logging.info("User clicked About from tray menu")
        # TODO: Show about dialog
        print("\n" + "="*50)
        print("LawTime Tracker v0.1.0")
        print("Windows 11 automatic time tracking for lawyers")
        print("="*50 + "\n")
    
    def _handle_quit(self, icon, item):
        """Handle Quit menu item."""
        logging.info("User quit from tray menu")
        self.on_quit()
        if self.icon:
            self.icon.stop()
    
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
            "lawtime_tracker",
            self.create_icon_image("green"),
            "LawTime - Tracking",
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
        print("LawTime Tracker - Console Mode")
        print("(System tray not available)")
        print("="*60)
        print("\nCommands:")
        print("  start  - Start tracking")
        print("  pause  - Pause tracking")
        print("  export - Export data")
        print("  quit   - Quit application")
        print("\n")
        
        while True:
            try:
                cmd = input("lawtime> ").strip().lower()
                
                if cmd == "start":
                    print("▶ Starting tracking...")
                    self.is_tracking = True
                    self.on_start()
                
                elif cmd == "pause":
                    print("⏸ Pausing tracking...")
                    self.is_tracking = False
                    self.on_pause()
                
                elif cmd == "export":
                    print("📤 Exporting data...")
                    self.on_export()
                
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
    
    def on_export():
        print("✓ Export callback triggered")
        print("  (In real app: would open export dialog)")
    
    def on_settings():
        print("✓ Settings callback triggered")
        print("  (In real app: would open settings dialog)")
    
    def on_quit():
        print("✓ Quit callback triggered")
        print("  (In real app: would clean up and exit)")
    
    # Create tray icon
    tray = TrayIcon(
        on_start=on_start,
        on_pause=on_pause,
        on_export=on_export,
        on_settings=on_settings,
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
