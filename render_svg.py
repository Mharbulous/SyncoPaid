"""
Render SVG to PNG using Edge browser (headless).
This handles mesh gradients that aren't supported by pure Python libraries.
"""

import sys
import time
from pathlib import Path

try:
    from selenium import webdriver
    from selenium.webdriver.edge.service import Service
    from selenium.webdriver.edge.options import Options
except ImportError:
    print("Installing selenium...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium"])
    from selenium import webdriver
    from selenium.webdriver.edge.service import Service
    from selenium.webdriver.edge.options import Options

from PIL import Image
from io import BytesIO
import base64


def render_svg_to_png():
    src_dir = Path(__file__).parent / "src" / "syncopaid"
    svg_path = src_dir / "stopwatch-pictogram.svg"
    png_path = src_dir / "stopwatch-pictogram.png"

    if not svg_path.exists():
        print(f"ERROR: SVG file not found: {svg_path}")
        return False

    print(f"Rendering {svg_path} using Edge browser...")

    # Configure Edge in headless mode
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=512,512")

    try:
        driver = webdriver.Edge(options=options)
    except Exception as e:
        print(f"ERROR: Could not start Edge browser: {e}")
        print("Make sure Microsoft Edge is installed.")
        return False

    try:
        # Load the SVG file
        svg_url = f"file:///{svg_path.as_posix()}"
        driver.get(svg_url)

        # Wait for rendering (mesh gradient polyfill needs time)
        time.sleep(2)

        # Take a screenshot
        screenshot = driver.get_screenshot_as_png()

        # Convert to PIL Image
        img = Image.open(BytesIO(screenshot))

        # The SVG is 344x406, we need to crop/resize to square
        # Find the actual content (non-transparent area)
        img = img.convert('RGBA')

        # Get bounding box of non-transparent pixels
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)

        # Make it square by adding padding
        max_dim = max(img.size)
        square = Image.new('RGBA', (max_dim, max_dim), (0, 0, 0, 0))
        offset = ((max_dim - img.width) // 2, (max_dim - img.height) // 2)
        square.paste(img, offset)

        # Resize to 256x256
        square = square.resize((256, 256), Image.Resampling.LANCZOS)

        # Save as PNG
        square.save(png_path, 'PNG')
        print(f"Created: {png_path}")

        return True

    finally:
        driver.quit()


if __name__ == "__main__":
    success = render_svg_to_png()
    sys.exit(0 if success else 1)
