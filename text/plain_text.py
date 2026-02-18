"""Plain text renderer with emoji support using pilmoji."""
from PIL import Image, ImageDraw, ImageFont
import logging

from .emoji_renderer import draw_text_with_emoji

logger = logging.getLogger(__name__)


def draw_plain_image(
    image: Image.Image,
    width: int,
    height: int,
    text: str,
    font_size: int,
    font_path: str,
    max_width: int,
    width_center_position: float,
    height_center_position: float,
    outline_width: int,
    text_color: str,
    outline_color: str,
    margins: dict,
) -> Image.Image:
    """Draw plain text with outline on an image.

    Args:
        image: The base image to draw on
        width: Width of the image
        height: Height of the image
        text: Text to render
        font_size: Font size to use
        font_path: Path to font file
        max_width: Maximum width for text wrapping
        width_center_position: X position for text (0-1)
        height_center_position: Y position for text (0-1)
        outline_width: Width of the text outline
        text_color: Color of the main text
        outline_color: Color of the text outline
        margins: Margin dict (not used currently)

    Returns:
        PIL.Image: The image with text drawn on it
    """
    print(f"PLAIN // Drawing: {text[:50]}...")
    print(f"PLAIN // Font: {font_path}, Size: {font_size}")
    print(f"PLAIN // Position: x={width_center_position:.2f}, y={height_center_position:.2f}")

    # Upscale for crisp text
    scale = 2
    base = image.copy().convert("RGBA")
    base = base.resize((width * scale, height * scale), Image.Resampling.LANCZOS)

    scaled_width = width * scale
    scaled_height = height * scale
    scaled_font_size = int(font_size * scale)
    scaled_max_width = int(max_width * scale)
    scaled_outline_width = int(outline_width * scale)

    # Create text layer
    text_layer = Image.new("RGBA", (scaled_width, scaled_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)

    # Load font
    font = ImageFont.truetype(font_path, scaled_font_size)

    # Wrap text
    lines = wrap_text(draw, text, font, scaled_max_width)
    line_spacing = int(scaled_font_size * 1.2)
    total_text_height = len(lines) * line_spacing

    # Calculate position - center the text block at the specified position
    x = int(scaled_width * width_center_position)
    y_center = int(scaled_height * height_center_position)

    # Offset y so text block is centered at the position
    y_start = y_center - (total_text_height // 2)

    # === OVERFLOW PROTECTION ===
    # Scale margins for bounds checking
    scaled_margin_top = margins.get("top", 0) * scale
    scaled_margin_bottom = margins.get("bottom", 0) * scale

    # Calculate safe bounds
    safe_top = int(scaled_margin_top)
    safe_bottom = int(scaled_height - scaled_margin_bottom)

    # Clamp y_start to stay within safe bounds
    if y_start < safe_top:
        y_start = safe_top
    if y_start + total_text_height > safe_bottom:
        y_start = safe_bottom - total_text_height

    print(f"PLAIN // Text block: {len(lines)} lines, total height={total_text_height}")
    print(f"PLAIN // Center at y={y_center}, starting at y={y_start}")

    # Scale margins for text layer (use different names to avoid shadowing)
    text_margin_left = margins.get("left", 0) * scale
    text_margin_right = margins.get("right", 0) * scale

    # Draw each line with emoji support
    for i, line in enumerate(lines):
        line_y = y_start + (i * line_spacing)

        text_layer = draw_text_with_emoji(
            text_layer,
            line,
            (x, line_y),
            font,
            fill=text_color,
            outline_color=outline_color,
            outline_width=scaled_outline_width,
            margin_left=int(text_margin_left),
            margin_right=int(text_margin_right),
        )
        print(f"PLAIN // Rendered line {i}: {line[:40]}...")

    # Scale back down
    text_layer = text_layer.resize((width, height), Image.Resampling.LANCZOS)
    base_resized = base.resize((width, height), Image.Resampling.LANCZOS)

    if base_resized.mode != "RGBA":
        base_resized = base_resized.convert("RGBA")

    result = Image.alpha_composite(base_resized, text_layer)
    return result


def wrap_text(draw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list:
    """Wrap text to fit within max_width."""
    lines = []

    # Split by explicit newlines first
    paragraphs = text.split("\\n")

    for paragraph in paragraphs:
        if not paragraph.strip():
            lines.append("")
            continue

        words = paragraph.strip().split()
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()
            bbox = draw.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]

            if line_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

    return lines
