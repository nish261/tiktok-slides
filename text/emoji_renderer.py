"""
Apple emoji renderer - downloads Apple-style emoji PNGs from Emojipedia CDN
and pastes them onto PIL images for consistent iOS-style appearance.
"""
import re
import requests
import os
from typing import Optional, List, Tuple
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from pathlib import Path

# Apple emoji CDN (via jsDelivr from emoji-data repo)
EMOJI_BASE_URL = "https://cdn.jsdelivr.net/gh/iamcal/emoji-data@master/img-apple-160"

# Local cache directory
CACHE_DIR = Path(__file__).parent.parent / "assets" / "emoji_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Emoji regex - matches most common emoji ranges
EMOJI_REGEX = re.compile(
    r'['
    r'\U0001F600-\U0001F64F'    # Emoticons
    r'\U0001F300-\U0001F5FF'    # Misc Symbols and Pictographs
    r'\U0001F680-\U0001F6FF'    # Transport and Map
    r'\U0001F700-\U0001F77F'    # Alchemical Symbols
    r'\U0001F780-\U0001F7FF'    # Geometric Shapes Extended
    r'\U0001F800-\U0001F8FF'    # Supplemental Arrows-C
    r'\U0001F900-\U0001F9FF'    # Supplemental Symbols and Pictographs
    r'\U0001FA00-\U0001FA6F'    # Chess Symbols
    r'\U0001FA70-\U0001FAFF'    # Symbols and Pictographs Extended-A
    r'\U00002702-\U000027B0'    # Dingbats
    r'\U00002600-\U000026FF'    # Misc symbols
    r'\U0000231A-\U0000231B'    # Watch, Hourglass
    r'\U00002328'               # Keyboard
    r'\U000023CF'               # Eject
    r'\U000023E9-\U000023F3'    # Various
    r'\U000023F8-\U000023FA'    # Various
    r'\U00002934-\U00002935'    # Arrows
    r'\U000025AA-\U000025AB'    # Squares
    r'\U000025B6'               # Play
    r'\U000025C0'               # Reverse
    r'\U000025FB-\U000025FE'    # Squares
    r'\U00002614-\U00002615'    # Umbrella, Hot Beverage
    r'\U00002648-\U00002653'    # Zodiac
    r'\U0000267F'               # Wheelchair
    r'\U00002693'               # Anchor
    r'\U000026A1'               # High Voltage
    r'\U000026AA-\U000026AB'    # Circles
    r'\U000026BD-\U000026BE'    # Soccer, Baseball
    r'\U000026C4-\U000026C5'    # Snowman, Sun
    r'\U000026CE'               # Ophiuchus
    r'\U000026D4'               # No Entry
    r'\U000026EA'               # Church
    r'\U000026F2-\U000026F3'    # Fountain, Golf
    r'\U000026F5'               # Sailboat
    r'\U000026FA'               # Tent
    r'\U000026FD'               # Fuel Pump
    r'\U00002702'               # Scissors
    r'\U00002705'               # Check Mark
    r'\U00002708-\U0000270D'    # Various
    r'\U0000270F'               # Pencil
    r'\U00002712'               # Black Nib
    r'\U00002714'               # Check Mark
    r'\U00002716'               # X Mark
    r'\U0000271D'               # Latin Cross
    r'\U00002721'               # Star of David
    r'\U00002728'               # Sparkles
    r'\U00002733-\U00002734'    # Eight Spoked Asterisk
    r'\U00002744'               # Snowflake
    r'\U00002747'               # Sparkle
    r'\U0000274C'               # Cross Mark
    r'\U0000274E'               # Cross Mark
    r'\U00002753-\U00002755'    # Question Marks
    r'\U00002757'               # Exclamation Mark
    r'\U00002763-\U00002764'    # Heart Exclamation, Heart
    r'\U00002795-\U00002797'    # Plus, Minus, Divide
    r'\U000027A1'               # Right Arrow
    r'\U000027B0'               # Curly Loop
    r'\U000027BF'               # Double Curly Loop
    r'\U00002B05-\U00002B07'    # Arrows
    r'\U00002B1B-\U00002B1C'    # Squares
    r'\U00002B50'               # Star
    r'\U00002B55'               # Circle
    r'\U00003030'               # Wavy Dash
    r'\U0000303D'               # Part Alternation Mark
    r'\U00003297'               # Circled Ideograph Congratulation
    r'\U00003299'               # Circled Ideograph Secret
    r'\U0000FE0F'               # Variation Selector
    r']+'
)


def char_to_unicode_hex(char: str) -> str:
    """Convert emoji character(s) to hex code point(s) for CDN URL."""
    # Handle multi-codepoint emojis (like skin tones, flags, ZWJ sequences)
    code_points = []
    for c in char:
        cp = ord(c)
        # Skip variation selectors in the URL (they're implicit)
        if cp == 0xFE0F:
            continue
        if cp > 255:  # Only include non-ASCII
            code_points.append(f"{cp:x}")
    return "-".join(code_points) if code_points else ""


def get_emoji_image_url(unicode_hex: str) -> str:
    """Get Apple emoji PNG URL from CDN."""
    return f"{EMOJI_BASE_URL}/{unicode_hex}.png"


def get_cached_emoji_path(unicode_hex: str) -> Path:
    """Get local cache path for emoji."""
    return CACHE_DIR / f"{unicode_hex}.png"


def download_emoji_image(char: str, size: int = 64) -> Optional[Image.Image]:
    """
    Download Apple emoji PNG from CDN and resize it.
    Uses local cache to avoid repeated downloads.
    """
    unicode_hex = char_to_unicode_hex(char)
    if not unicode_hex:
        return None

    cache_path = get_cached_emoji_path(unicode_hex)

    # Check cache first
    if cache_path.exists():
        try:
            emoji_img = Image.open(cache_path).convert("RGBA")
            return emoji_img.resize((size, size), Image.Resampling.LANCZOS)
        except Exception:
            pass  # Cache corrupted, re-download

    # Download from CDN
    url = get_emoji_image_url(unicode_hex)
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            emoji_img = Image.open(BytesIO(response.content)).convert("RGBA")
            # Save to cache
            emoji_img.save(cache_path, "PNG")
            return emoji_img.resize((size, size), Image.Resampling.LANCZOS)
    except Exception as e:
        print(f"Failed to download emoji {char}: {e}")

    return None


def split_text_and_emojis(text: str) -> List[Tuple[str, bool]]:
    """
    Split text into segments of regular text and emoji characters.
    Returns list of tuples: (segment, is_emoji)
    """
    segments = []
    last_end = 0

    for match in EMOJI_REGEX.finditer(text):
        # Add text before this emoji
        if match.start() > last_end:
            text_segment = text[last_end:match.start()]
            if text_segment:
                segments.append((text_segment, False))

        # Add the emoji
        segments.append((match.group(), True))
        last_end = match.end()

    # Add remaining text after last emoji
    if last_end < len(text):
        remaining = text[last_end:]
        if remaining:
            segments.append((remaining, False))

    # If no emojis found, return whole text
    if not segments:
        segments.append((text, False))

    return segments


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
    Draw text with Apple emoji support.

    Emojis are downloaded from Apple's CDN and pasted as images.
    Regular text is drawn with PIL.

    Args:
        image: PIL Image to draw on
        text: Text string (can include emojis)
        position: (x, y) tuple for text position (center anchor)
        font: PIL ImageFont
        fill: Text color
        outline_color: Outline color
        outline_width: Outline thickness (0 for no outline)

    Returns:
        Image with text drawn
    """
    draw = ImageDraw.Draw(image)

    # Split text into segments
    segments = split_text_and_emojis(text)

    # Calculate total width for centering
    total_width = 0
    emoji_size = int(font.size * 1.1)  # Slightly larger than font

    segment_widths = []
    for segment, is_emoji in segments:
        if is_emoji:
            # Each emoji character
            width = len([c for c in segment if ord(c) > 255 and ord(c) != 0xFE0F]) * emoji_size
            segment_widths.append(width)
            total_width += width
        else:
            bbox = font.getbbox(segment)
            width = bbox[2] - bbox[0]
            segment_widths.append(width)
            total_width += width

    # Start position (centered)
    x = int(position[0] - total_width / 2)
    y = int(position[1])

    # Draw each segment
    for i, (segment, is_emoji) in enumerate(segments):
        if is_emoji:
            # Draw each emoji character as Apple PNG
            for char in segment:
                if ord(char) <= 255 or ord(char) == 0xFE0F:
                    continue  # Skip ASCII and variation selectors

                emoji_img = download_emoji_image(char, size=emoji_size)

                if emoji_img:
                    # Calculate vertical position to align with text baseline
                    emoji_y = y - int(emoji_size * 0.1)  # Slight offset up

                    # Paste with alpha
                    image.paste(emoji_img, (int(x), int(emoji_y)), emoji_img)
                    x += emoji_size
                else:
                    # Fallback: draw native emoji as text
                    if outline_width > 0:
                        for dx in range(-outline_width, outline_width + 1):
                            for dy in range(-outline_width, outline_width + 1):
                                if dx != 0 or dy != 0:
                                    draw.text((x + dx, y + dy), char, font=font, fill=outline_color)
                    draw.text((x, y), char, font=font, fill=fill)
                    x += emoji_size
        else:
            # Draw regular text with outline
            if outline_width > 0:
                for dx in range(-outline_width, outline_width + 1):
                    for dy in range(-outline_width, outline_width + 1):
                        if dx != 0 or dy != 0:
                            draw.text((x + dx, y + dy), segment, font=font, fill=outline_color)

            draw.text((x, y), segment, font=font, fill=fill)
            x += segment_widths[i]

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
    Draw multiple lines of text with Apple emoji support.

    Args:
        image: PIL Image to draw on
        lines: List of text lines
        start_position: (x, y) tuple for first line center
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
