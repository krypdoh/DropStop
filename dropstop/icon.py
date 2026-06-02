import math
from PIL import Image, ImageDraw, ImageFont


def _octagon_vertices(cx, cy, radius):
    """
    Compute octagon vertices in stop-sign orientation (flat on top and bottom).
    Vertices start at top-right and go clockwise.
    """
    vertices = []
    for i in range(8):
        # Start at -67.5 degrees (top-right vertex) and go every 45 degrees clockwise
        # This gives flat edges on top and bottom, like a real stop sign
        angle_deg = -67.5 + i * 45
        angle_rad = math.radians(angle_deg)
        x = cx + radius * math.cos(angle_rad)
        y = cy + radius * math.sin(angle_rad)
        vertices.append((x, y))
    return vertices


def _draw_octagon_icon(size=256, color="red"):
    """
    Draw a stop-sign shaped icon: colored octagon with white border and white 'D'.
    Oriented like a real stop sign (flat edges on top and bottom).

    Args:
        size: Image dimensions (square).
        color: Fill color - "red" for paused/exe icon, "green" for running.

    Returns:
        PIL.Image.Image (RGBA)
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    center = size / 2

    # Outer octagon (white border) - stop sign orientation
    outer_radius = size * 0.47
    outer_verts = _octagon_vertices(center, center, outer_radius)
    draw.polygon(outer_verts, fill="white")

    # Inner octagon (colored fill)
    inner_radius = outer_radius * 0.87
    inner_verts = _octagon_vertices(center, center, inner_radius)
    draw.polygon(inner_verts, fill=color)

    # Draw the letter "D" centered (nudge down slightly for visual centering)
    font_size = int(size * 0.50)
    try:
        font = ImageFont.truetype("arialbd.ttf", font_size)
    except OSError:
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()

    # Offset down by ~3% to visually center the capital D
    text_y = center + size * 0.03
    draw.text(
        (center, text_y),
        "D",
        fill="white",
        font=font,
        anchor="mm",
    )

    return img


def generate_icon(color="red", size=256):
    """Generate a DropStop icon as a PIL Image."""
    return _draw_octagon_icon(size=size, color=color)


def generate_running_icon(size=64):
    """Green octagon icon for 'Dropbox running' state."""
    return _draw_octagon_icon(size=size, color="#228B22")


def generate_paused_icon(size=64):
    """Red octagon icon for 'Dropbox paused' state."""
    return _draw_octagon_icon(size=size, color="#CC0000")


def save_ico(path="dropstop.ico", color="red"):
    """Generate and save a multi-resolution .ico file (red, for .exe icon)."""
    # Generate at the largest size, Pillow will downscale for smaller sizes
    img = _draw_octagon_icon(size=256, color=color)
    img.save(path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


if __name__ == "__main__":
    # Generate the .ico file for building the .exe
    save_ico("dropstop.ico", color="#CC0000")
    print("Generated dropstop.ico")
