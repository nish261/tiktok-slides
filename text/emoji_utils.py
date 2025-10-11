"""
Utility functions for handling emoji rendering with mixed fonts.
"""
import re
from typing import List, Tuple, Union
from PIL import ImageFont


def is_emoji(char: str) -> bool:
    """
    Check if a character is an emoji.
    
    Args:
        char: Single character to check
        
    Returns:
        bool: True if the character is an emoji
    """
    # Unicode ranges for emojis (comprehensive list)
    emoji_ranges = [
        (0x1F600, 0x1F64F),  # Emoticons
        (0x1F300, 0x1F5FF),  # Misc Symbols and Pictographs
        (0x1F680, 0x1F6FF),  # Transport and Map
        (0x1F1E0, 0x1F1FF),  # Regional indicator symbols (flags)
        (0x2600, 0x26FF),    # Miscellaneous symbols
        (0x2700, 0x27BF),    # Dingbats
        (0xFE00, 0xFE0F),    # Variation Selectors
        (0x1F900, 0x1F9FF),  # Supplemental Symbols and Pictographs
        (0x1F018, 0x1F0F5),  # Playing cards
        (0x1F200, 0x1F2FF),  # Enclosed characters
        (0x1FA70, 0x1FAFF),  # Symbols and Pictographs Extended-A
        (0x1F004, 0x1F0CF),  # Mahjong Tiles
        (0x1F170, 0x1F251),  # Enclosed Alphanumeric Supplement
        (0x1F780, 0x1F7FF),  # Geometric Shapes Extended
        (0x1F800, 0x1F8FF),  # Supplemental Arrows-C
        (0x1F000, 0x1F02F),  # Mahjong Tiles
        (0x1F030, 0x1F09F),  # Domino Tiles
        (0x1F0A0, 0x1F0FF),  # Playing Cards
        (0x1F100, 0x1F1FF),  # Enclosed Alphanumeric Supplement
        (0x1F300, 0x1F5FF),  # Miscellaneous Symbols and Pictographs
        (0x1F600, 0x1F64F),  # Emoticons
        (0x1F650, 0x1F67F),  # Ornamental Dingbats
        (0x1F680, 0x1F6FF),  # Transport and Map Symbols
        (0x1F700, 0x1F77F),  # Alchemical Symbols
        (0x1F780, 0x1F7FF),  # Geometric Shapes Extended
        (0x1F800, 0x1F8FF),  # Supplemental Arrows-C
        (0x1F900, 0x1F9FF),  # Supplemental Symbols and Pictographs
        (0x1FA00, 0x1FA6F),  # Chess Symbols
        (0x1FA70, 0x1FAFF),  # Symbols and Pictographs Extended-A
        (0x1FB00, 0x1FBFF),  # Symbols for Legacy Computing
        (0x1FC00, 0x1FCFF),  # Symbols for Legacy Computing
        (0x1FD00, 0x1FDFF),  # Symbols for Legacy Computing
        (0x1FE00, 0x1FEFF),  # Symbols for Legacy Computing
        (0x1FF00, 0x1FFFF),  # Symbols for Legacy Computing
    ]
    
    code_point = ord(char)
    return any(start <= code_point <= end for start, end in emoji_ranges)


def replace_emojis_with_symbols(text: str) -> str:
    """
    Replace common emojis with Unicode symbols that work better with regular fonts.
    
    Args:
        text: Input text string
        
    Returns:
        Text with emojis replaced by Unicode symbols
    """
    emoji_replacements = {
        '💔': '♡',  # Broken heart -> outline heart
        '😭': 'T_T',  # Crying -> text representation
        '💅': '💅',  # Nail polish -> keep as is (works in most fonts)
        '💸': '$',  # Money with wings -> dollar sign
        '🤷‍♀️': '?',  # Woman shrugging -> question mark
        '✨': '*',  # Sparkles -> asterisk
        '🔥': 'FIRE',  # Fire -> text
        '💯': '100',  # Hundred -> text
        '❤️': '♥',  # Red heart -> filled heart
        '💖': '♥',  # Sparkling heart -> filled heart
        '💕': '♥',  # Two hearts -> filled heart
        '💗': '♥',  # Growing heart -> filled heart
        '💘': '♥',  # Heart with arrow -> filled heart
        '💙': '♥',  # Blue heart -> filled heart
        '💚': '♥',  # Green heart -> filled heart
        '💛': '♥',  # Yellow heart -> filled heart
        '💜': '♥',  # Purple heart -> filled heart
        '🖤': '♥',  # Black heart -> filled heart
        '🤍': '♡',  # White heart -> outline heart
        '💓': '♥',  # Beating heart -> filled heart
        '💝': '♥',  # Heart with ribbon -> filled heart
        '💞': '♥',  # Revolving hearts -> filled heart
        '💟': '♥',  # Heart decoration -> filled heart
    }
    
    result = text
    for emoji, replacement in emoji_replacements.items():
        result = result.replace(emoji, replacement)
    
    return result


def parse_text_with_emojis(text: str) -> List[Tuple[str, bool]]:
    """
    Parse text into segments of regular text and emojis.
    
    Args:
        text: Input text string
        
    Returns:
        List of tuples (text_segment, is_emoji)
    """
    segments = []
    current_segment = ""
    current_type = None  # None, True (emoji), False (text)
    
    for char in text:
        char_is_emoji = is_emoji(char)
        
        if current_type is None:
            # First character
            current_type = char_is_emoji
            current_segment = char
        elif current_type == char_is_emoji:
            # Same type as previous character
            current_segment += char
        else:
            # Type changed, save current segment and start new one
            segments.append((current_segment, current_type))
            current_segment = char
            current_type = char_is_emoji
    
    # Add the last segment
    if current_segment:
        segments.append((current_segment, current_type))
    
    return segments


def get_emoji_font_path() -> str:
    """
    Get the path to the emoji font.
    
    Returns:
        str: Path to system emoji font
    """
    from pathlib import Path
    from content_manager.settings.settings_constants import BASE_DIR
    
    # Try system Apple Color Emoji first (works on macOS)
    apple_emoji = "/System/Library/Fonts/Apple Color Emoji.ttc"
    if Path(apple_emoji).exists():
        return apple_emoji
    
    # Fallback to NotoColorEmoji.ttf
    emoji_font_path = BASE_DIR / "assets" / "fonts" / "NotoColorEmoji.ttf"
    return str(emoji_font_path.resolve())


def load_fonts(text_font_path: str, font_size: int) -> Tuple[ImageFont.FreeTypeFont, ImageFont.FreeTypeFont]:
    """
    Load both text and emoji fonts.
    
    Args:
        text_font_path: Path to the main text font
        font_size: Font size
        
    Returns:
        Tuple of (text_font, emoji_font)
    """
    from pathlib import Path
    from content_manager.settings.settings_constants import BASE_DIR
    
    # Load text font (TikTok style)
    text_font = ImageFont.truetype(text_font_path, font_size)
    
    # Try to load NotoColorEmoji.ttf first (best emoji support)
    noto_emoji_path = BASE_DIR / "assets" / "fonts" / "NotoColorEmoji.ttf"
    
    # Force Apple Color Emoji for color emoji support
    emoji_font_options = [
        "/System/Library/Fonts/Apple Color Emoji.ttc",  # Color emoji support
    ]
    
    emoji_font = None
    
    for emoji_font_path in emoji_font_options:
        try:
            if Path(emoji_font_path).exists():
                # Apple Color Emoji must be size 20, we'll scale it later
                if "Apple Color Emoji" in emoji_font_path:
                    emoji_size = 20
                else:
                    emoji_size = font_size
                emoji_font = ImageFont.truetype(emoji_font_path, emoji_size)
                print(f"Successfully loaded emoji font: {emoji_font_path}")
                break
        except Exception as e:
            print(f"Could not load {emoji_font_path}: {e}")
            continue
    
    # If all emoji fonts failed, fallback to text font
    if emoji_font is None:
        print("Warning: Could not load any emoji font, using text font for emojis")
        emoji_font = text_font
    
    return text_font, emoji_font
