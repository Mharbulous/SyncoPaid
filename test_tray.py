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
        "SyncoPaid_test",
        create_icon("green"),
        "SyncoPaid Test",
        menu=pystray.Menu(
            pystray.MenuItem("Status", on_status),
            pystray.MenuItem("Quit", on_quit)
        )
    )

    icon.run()