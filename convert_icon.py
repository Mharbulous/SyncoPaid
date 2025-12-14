"""
Convert stopwatch-pictogram to three icon states:

1. SyncoPaid-On.ico - Normal tracking, regular stopwatch icon
2. SyncoPaid-Paused.ico - User paused, stopwatch with "||" pause symbol overlay
3. SyncoPaid-Inactive.ico - No activity for 5min, faded icon with sleeping emoji
"""

import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Installing Pillow...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image, ImageDraw, ImageFont


def find_emoji_font(size):
    """Find a font that supports emoji on Windows."""
    font_paths = [
        "C:/Windows/Fonts/seguiemj.ttf",  # Segoe UI Emoji
        "C:/Windows/Fonts/segoe ui emoji.ttf",
    ]
    for font_path in font_paths:
        try:
            return ImageFont.truetype(font_path, size)
        except:
            continue
    return None


def find_bold_font(size):
    """Find a bold font for the pause symbol."""
    font_paths = [
        "C:/Windows/Fonts/arialbd.ttf",  # Arial Bold
        "C:/Windows/Fonts/segoeui.ttf",  # Segoe UI
        "C:/Windows/Fonts/arial.ttf",    # Arial
    ]
    for font_path in font_paths:
        try:
            return ImageFont.truetype(font_path, size)
        except:
            continue
    return ImageFont.load_default()


def draw_pause_symbol(image, size, Image, ImageDraw):
    """Draw pause symbol (two vertical bars) in center of icon."""
    overlay = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Bar dimensions scale with icon size
    bar_width = max(2, size // 8)
    bar_height = max(4, size // 3)
    gap = max(2, size // 12)

    # Center position
    center_x = size // 2
    center_y = size // 2

    # Calculate bar positions
    left_bar_x = center_x - gap // 2 - bar_width
    right_bar_x = center_x + gap // 2
    bar_top = center_y - bar_height // 2
    bar_bottom = center_y + bar_height // 2

    # Draw dark outline for visibility
    outline_color = (0, 0, 0, 255)
    outline_width = max(1, size // 32)
    for offset_x in range(-outline_width, outline_width + 1):
        for offset_y in range(-outline_width, outline_width + 1):
            if offset_x != 0 or offset_y != 0:
                draw.rectangle(
                    [left_bar_x + offset_x, bar_top + offset_y,
                     left_bar_x + bar_width + offset_x, bar_bottom + offset_y],
                    fill=outline_color
                )
                draw.rectangle(
                    [right_bar_x + offset_x, bar_top + offset_y,
                     right_bar_x + bar_width + offset_x, bar_bottom + offset_y],
                    fill=outline_color
                )

    # Draw white pause bars
    bar_color = (255, 255, 255, 255)
    draw.rectangle(
        [left_bar_x, bar_top, left_bar_x + bar_width, bar_bottom],
        fill=bar_color
    )
    draw.rectangle(
        [right_bar_x, bar_top, right_bar_x + bar_width, bar_bottom],
        fill=bar_color
    )

    return Image.alpha_composite(image, overlay)


def draw_sleep_emoji(image, size, Image, ImageDraw, ImageFont):
    """Draw sleeping emoji in bottom-right corner at full opacity."""
    emoji_layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(emoji_layer)

    # Font size scales with icon size
    font_size = max(8, size // 2)
    emoji_font = find_emoji_font(font_size)

    if emoji_font:
        emoji = "\U0001F4A4"  # Sleeping zzz symbol
    else:
        # Fallback to text if emoji font not available
        emoji = "Zzz"
        emoji_font = find_bold_font(font_size)

    # Get text bounding box
    bbox = draw.textbbox((0, 0), emoji, font=emoji_font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Position in bottom-right corner
    padding = max(1, size // 16)
    x = size - text_width - padding
    y = size - text_height - padding

    # Draw white outline for visibility
    outline_color = (255, 255, 255, 255)
    for ox in [-2, -1, 0, 1, 2]:
        for oy in [-2, -1, 0, 1, 2]:
            if abs(ox) + abs(oy) <= 2 and (ox != 0 or oy != 0):
                draw.text((x + ox, y + oy), emoji, font=emoji_font, fill=outline_color)

    # Draw the emoji/text in dark blue
    draw.text((x, y), emoji, font=emoji_font, fill=(50, 50, 150, 255))

    return Image.alpha_composite(image, emoji_layer)


def save_ico(images, ico_path, ico_sizes):
    """Save images as ICO file with all sizes."""
    images_sorted = sorted(images, key=lambda x: x.size[0], reverse=True)
    images_sorted[0].save(
        ico_path,
        format='ICO',
        sizes=[(s, s) for s in ico_sizes],
        append_images=images_sorted[1:]
    )


def convert_png_to_ico():
    src_dir = Path(__file__).parent / "src" / "syncopaid"
    svg_path = src_dir / "stopwatch-pictogram.svg"
    png_path = src_dir / "stopwatch-pictogram.png"
    on_ico_path = src_dir / "SyncoPaid-On.ico"
    paused_ico_path = src_dir / "SyncoPaid-Paused.ico"
    inactive_ico_path = src_dir / "SyncoPaid-Inactive.ico"

    # ICO sizes to include (Windows uses various sizes)
    ico_sizes = [16, 24, 32, 48, 64, 128, 256]

    # Check for PNG first
    if not png_path.exists():
        print(f"ERROR: PNG file not found: {png_path}")
        print()
        print("Run 'python render_svg.py' first to create the PNG from SVG.")
        return False

    print(f"Loading {png_path}...")
    base_image = Image.open(png_path).convert('RGBA')

    # Ensure it's 256x256
    if base_image.size != (256, 256):
        base_image = base_image.resize((256, 256), Image.Resampling.LANCZOS)

    # =========================================================================
    # 1. Create "On" ICO - regular stopwatch icon
    # =========================================================================
    on_images = []
    for size in ico_sizes:
        resized = base_image.resize((size, size), Image.Resampling.LANCZOS)
        on_images.append(resized)

    save_ico(on_images, on_ico_path, ico_sizes)
    print(f"Created: {on_ico_path}")

    # =========================================================================
    # 2. Create "Paused" ICO - full opacity icon with || pause symbol
    # =========================================================================
    paused_images = []
    for size in ico_sizes:
        resized = base_image.resize((size, size), Image.Resampling.LANCZOS).copy()
        with_pause = draw_pause_symbol(resized, size, Image, ImageDraw)
        paused_images.append(with_pause)

    save_ico(paused_images, paused_ico_path, ico_sizes)
    print(f"Created: {paused_ico_path}")

    # =========================================================================
    # 3. Create "Inactive" ICO - faded icon with sleeping emoji
    # =========================================================================
    inactive_images = []
    for size in ico_sizes:
        resized = base_image.resize((size, size), Image.Resampling.LANCZOS).copy()

        # Make the icon faded/translucent (40% opacity)
        r, g, b, a = resized.split()
        a = a.point(lambda x: int(x * 0.4))
        faded = Image.merge('RGBA', (r, g, b, a))

        # Add sleeping emoji overlay at full opacity
        with_emoji = draw_sleep_emoji(faded, size, Image, ImageDraw, ImageFont)
        inactive_images.append(with_emoji)

    save_ico(inactive_images, inactive_ico_path, ico_sizes)
    print(f"Created: {inactive_ico_path}")

    print("\nDone! All three icons have been created.")
    return True


if __name__ == "__main__":
    success = convert_png_to_ico()
    sys.exit(0 if success else 1)
