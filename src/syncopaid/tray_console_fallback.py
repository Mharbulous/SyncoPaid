"""
Console fallback interface for when system tray is unavailable.

Provides a command-line interface as an alternative to the GUI tray icon.
"""


class TrayConsoleFallback:
    """Mixin class providing console fallback functionality for TrayIcon."""

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
        print("  open   - Open main window")
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

                elif cmd == "open":
                    print("📊 Opening SyncoPaid...")
                    self.on_open()

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
