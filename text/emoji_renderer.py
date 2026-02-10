"""
Clean, simple emoji renderer using pilmoji (Twemoji).
Just works - no complex fallbacks.
"""
from PIL import Image, ImageDraw, ImageFont

try:
    from pilmoji import Pilmoji
    from pilmoji.source import Twemoji
    HAS_PILMOJI = True
except ImportError:
    HAS_PILMOJI = False
    Pilmoji = None
    Twemoji = None


def draw_text_with_emoji(
    image: Image.Image,
    text: str,
    position: tuple,
    font: ImageFont.FreeTypeFont,
    fill: str = "#FFFFFF",
    outline_color: str = "#000000",
    outline_width: int = 0,
) -> Image.Image:
    """
    Draw text with emoji support using pilmoji.

    Args:
        image: PIL Image to draw on
        text: Text string (can include emojis)
        position: (x, y) tuple for text position
        font: PIL ImageFont
        fill: Text color
        outline_color: Outline color
        outline_width: Outline thickness (0 for no outline)

    Returns:
        Image with text drawn
    """
    x, y = int(position[0]), int(position[1])

    if HAS_PILMOJI:
        try:
            # Draw outline first by rendering text multiple times
            if outline_width > 0:
                with Pilmoji(image, source=Twemoji) as pilmoji:
                    for dx in range(-outline_width, outline_width + 1):
                        for dy in range(-outline_width, outline_width + 1):
                            if dx != 0 or dy != 0:
                                pilmoji.text((x + dx, y + dy), text, font=font, fill=outline_color)

            # Draw main text with emojis
            with Pilmoji(image, source=Twemoji) as pilmoji:
                pilmoji.text((x, y), text, font=font, fill=fill)

            return image

        except Exception as e:
            print(f"Pilmoji rendering failed: {e}, falling back to basic text")

    # Fallback: basic text rendering (no emoji support)
    draw = ImageDraw.Draw(image)

    if outline_width > 0:
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), text, font=font, fill=outline_color)

    draw.text((x, y), text, font=font, fill=fill)
    return image


def draw_multiline_text_with_emoji(
    image: Image.Image,
    lines: list,
    start_position: tuple,
    font: ImageFont.FreeTypeFont,
    line_spacing: int,
    fill: str = "#FFFFFF",
    outline_color: str = "#000000",
    outline_width: int = 0,
) -> Image.Image:
    """
    Draw multiple lines of text with emoji support.

    Args:
        image: PIL Image to draw on
        lines: List of text lines
        start_position: (x, y) tuple for first line
        font: PIL ImageFont
        line_spacing: Pixels between lines
        fill: Text color
        outline_color: Outline color
        outline_width: Outline thickness

    Returns:
        Image with text drawn
    """
    x, y = int(start_position[0]), int(start_position[1])

    for line in lines:
        image = draw_text_with_emoji(
            image, line, (x, y), font, fill, outline_color, outline_width
        )
        y += line_spacing

    return image
