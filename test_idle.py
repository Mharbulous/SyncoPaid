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
        