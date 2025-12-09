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