from PIL import Image, ImageDraw, ImageFont
try:
    # Emoji rendering helper; falls back to Pillow if unavailable
    from pilmoji import Pilmoji  # type: ignore
    from pilmoji.source import GoogleEmojiSource  # type: ignore
    _HAS_PILMOJI = True
except Exception:  # pragma: no cover - optional dependency
    Pilmoji = None  # type: ignore
    GoogleEmojiSource = None  # type: ignore
    _HAS_PILMOJI = False
import logging
import random
from .emoji_utils import parse_text_with_emojis, load_fonts

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
    """Draw plain text with outline on an image

    Args:
        image: The base image to draw on
        width: Width of the image
        height: Height of the image
        text: Text to render
        font_size: Font size to use
        font_path: Path to font file
        max_width: Maximum width for text wrapping
        width_center_position: X position for text center (0-1)
        height_center_position: Y position for text center (0-1)
        outline_width: Width of the text outline
        text_color: Color of the main text
        outline_color: Color of the text outline
        highlight_padding: Ignored for plain text

    Returns:
        PIL.Image: The image with text drawn on it
    """
    logger.critical(f"PLAIN // Drawing plain text")
    logger.critical(f"PLAIN // Text: {text}")
    logger.critical(f"PLAIN // Font: {font_path}, Size: {font_size}")
    logger.critical(f"PLAIN // Position: w={width_center_position}, h={height_center_position}")
    logger.critical(f"PLAIN // Colors - Text: {text_color}, Outline: {outline_color}")
    logger.critical(f"PLAIN // Margins: {margins}")

    # First upscale the base image with LANCZOS
    scale = 2
    base = image.copy().convert("RGBA")
    base = base.resize((width * scale, height * scale), Image.Resampling.LANCZOS)
    
    # Print original image metadata
    logger.critical("Original Image Metadata:")
    if hasattr(image, 'info'):
        for k, v in image.info.items():
            logger.critical(f"{k}: {v}")

    # Create high-res text layer
    scaled_width = width * scale
    scaled_height = height * scale
    scaled_font_size = font_size * scale

    text_layer = Image.new("RGBA", (scaled_width, scaled_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)

    # Load both text and emoji fonts at higher resolution
    text_font, emoji_font = load_fonts(font_path, scaled_font_size)

    # Scale other parameters
    scaled_max_width = max_width * scale
    scaled_margins = {k: v * scale for k, v in margins.items()}
    scaled_outline_width = outline_width * scale

    # Rest of the position calculations, but scaled
    lines = wrap_text(draw, text, text_font, scaled_max_width)
    line_spacing = scaled_font_size * 1.2
    total_height = len(lines) * line_spacing

    # Calculate y position with scaling
    y = int(scaled_height * (1 - height_center_position) - total_height/2)
    y = max(
        scaled_margins["top"],
        min(
            scaled_height - scaled_margins["bottom"] - total_height,
            y
        )
    )

    # Draw text at higher resolution using Pilmoji
    for i, line in enumerate(lines):
        # Calculate total line width for centering
        bbox = draw.textbbox((0, 0), line, font=text_font)
        total_width = bbox[2] - bbox[0]
        
        x = int(scaled_width * width_center_position)
        line_x = x - (total_width // 2)
        line_y = y + (i * line_spacing)

        try:
            # Use pilmoji for mixed text+emoji rendering
            from .emoji_pilmoji_renderer import pilmoji_renderer
            
            # Create a temporary image for this line to use with pilmoji
            temp_img = Image.new('RGBA', (scaled_width, scaled_font_size + 20), (0, 0, 0, 0))
            
            # Render the line with pilmoji
            temp_img = pilmoji_renderer.render_mixed_text(
                temp_img, 
                line, 
                text_font, 
                (0, 0), 
                fill=text_color
            )
            
            # Paste the rendered line onto the text layer
            text_layer.paste(temp_img, (line_x, line_y), temp_img)
            print(f"PLAIN // Successfully rendered mixed text with pilmoji: {line[:50]}...")
            
        except Exception as e:
            print(f"PLAIN // Pilmoji rendering failed: {e}, using fallback")
            # Fallback to segment-based rendering
            segments = parse_text_with_emojis(line)
            current_x = line_x
            
            for segment, is_emoji in segments:
                if is_emoji:
                    # Render emoji as PNG overlay using simple renderer
                    from .emoji_renderer_simple import simple_emoji_renderer
                    emoji_size = int(scaled_font_size * 1.2)  # Slightly larger than text
                    
                    # Calculate position for emoji (center aligned with text)
                    emoji_y = line_y - int(emoji_size * 0.1)  # Slight adjustment for visual alignment
                    
                    try:
                        # Use the simple renderer to overlay the emoji
                        text_layer = simple_emoji_renderer.render_emoji_overlay(
                            text_layer, segment, emoji_size, (current_x, emoji_y)
                        )
                        print(f"PLAIN // Successfully rendered emoji PNG for {segment}")
                        
                        # Advance position by emoji width
                        current_x += emoji_size
                        continue
                    except Exception as e2:
                        print(f"PLAIN // Failed to render emoji PNG {segment}: {e2}")
                        # Fallback to text rendering
                        font = emoji_font
                else:
                    # Use text font for regular text
                    font = text_font
                
                # Draw outline first if needed
                if scaled_outline_width > 0:
                    for adj_x in range(-scaled_outline_width, scaled_outline_width + 1):
                        for adj_y in range(-scaled_outline_width, scaled_outline_width + 1):
                            if adj_x != 0 or adj_y != 0:
                                draw.text((current_x + adj_x, line_y + adj_y), segment, font=font, fill=outline_color)
                
                # Draw main text
                draw.text((current_x, line_y), segment, font=font, fill=text_color)
                
                # Calculate width of segment and advance position
                bbox = draw.textbbox((0, 0), segment, font=font)
                segment_width = bbox[2] - bbox[0]
                current_x += segment_width

    # Scale back down with high-quality resampling
    text_layer = text_layer.resize((width, height), Image.Resampling.LANCZOS)
    base_resized = base.resize((width, height), Image.Resampling.LANCZOS)
    if base_resized.mode != "RGBA":
        base_resized = base_resized.convert("RGBA")
    result = Image.alpha_composite(base_resized, text_layer)

    # Print final image metadata
    logger.critical("Final Image Metadata:")
    if hasattr(result, 'info'):
        for k, v in result.info.items():
            logger.critical(f"{k}: {v}")

    return result


def draw_mixed_text_line(draw, line, x, y, text_font, emoji_font, text_color, outline_color, outline_width):
    """Draw a single line of text with mixed fonts for emojis and regular text"""
    current_x = x
    segments = parse_text_with_emojis(line)
    
    # Log font information
    logger.info(f"Drawing line: '{line}'")
    logger.info(f"Text font path: {getattr(text_font, 'path', 'No path attr')}")
    logger.info(f"Emoji font path: {getattr(emoji_font, 'path', 'No path attr')}")
    logger.info(f"Parsed segments: {segments}")
    
    for segment, is_emoji in segments:
        font = emoji_font if is_emoji else text_font
        logger.info(f"Drawing segment: '{segment}' (is_emoji: {is_emoji}) with font: {getattr(font, 'path', 'No path attr')}")
        print(f"DEBUG: Drawing segment '{segment}' (is_emoji: {is_emoji}) with font: {getattr(font, 'path', 'No path attr')}")
        
        # Use Pilmoji for emoji segments if available, otherwise fallback to regular draw
        if _HAS_PILMOJI and is_emoji:
            print(f"DEBUG: Attempting to use Pilmoji for emoji: '{segment}'")
            try:
                pilmoji = Pilmoji(draw.im, source=TwemojiSource)

                # Draw outline for emoji (simpler approach)
                if outline_width > 0:
                    # Draw outline by drawing emoji multiple times with offset
                    for adj_x in range(-outline_width, outline_width + 1):
                        for adj_y in range(-outline_width, outline_width + 1):
                            if adj_x != 0 or adj_y != 0:
                                pilmoji.text((current_x + adj_x, y + adj_y), segment, font=emoji_font, fill=outline_color)

                # Draw main emoji with embedded color support
                pilmoji.text((current_x, y), segment, font=emoji_font, fill=text_color, embedded_color=True)

            except Exception as e:
                print(f"Pilmoji failed for emoji '{segment}', falling back to regular draw: {e}")
                print(f"DEBUG: Using fallback font drawing for emoji: '{segment}'")
                # Fallback to regular drawing with outline
                for adj_x in range(-outline_width, outline_width + 1):
                    for adj_y in range(-outline_width, outline_width + 1):
                        draw.text(
                            (current_x + adj_x, y + adj_y),
                            segment,
                            font=font,
                            fill=outline_color,
                        )

                draw.text((current_x, y), segment, font=font, fill=text_color)
        else:
            # Regular text or emoji - draw with outline
            if is_emoji:
                print(f"DEBUG: Drawing emoji '{segment}' with regular font (Pilmoji not available)")
            for adj_x in range(-outline_width, outline_width + 1):
                for adj_y in range(-outline_width, outline_width + 1):
                    draw.text(
                        (current_x + adj_x, y + adj_y),
                        segment,
                        font=font,
                        fill=outline_color,
                    )

            # Draw main text with PNG-based emoji overlay
            if is_emoji:
                # Use PNG overlay for crisp, properly-sized emojis
                # Use font size for emoji width calculation
                emoji_size = text_font.size
                
                # Calculate position to align emoji with text baseline
                emoji_y = int(y - (emoji_size * 0.2))  # Adjust for visual alignment
                emoji_position = (int(current_x), emoji_y)
                
                # Render emoji as PNG overlay
                # Skip PNG overlay rendering - use Pilmoji instead
                pass
                
                # Update current_x to account for emoji width
                current_x += emoji_size
            else:
                draw.text(
                    (current_x, y),
                    segment,
                    font=font,
                    fill=text_color,
                )
                
                # Calculate width of this segment to position next segment
                bbox = draw.textbbox((0, 0), segment, font=font)
                segment_width = bbox[2] - bbox[0]
                current_x += segment_width


def wrap_text(draw, text, font, max_width):
    """Helper function to wrap text, treating each \n as a line break"""
    lines = []

    # Split by \n first to honor all line breaks
    paragraphs = text.split("\\n")

    for paragraph in paragraphs:
        if not paragraph.strip():
            lines.append("")
            continue

        # Now wrap the words within each paragraph
        words = paragraph.strip().split()
        current_line = ""

        for word in words:
            test_line = current_line + " " + word if current_line else word
            bbox = draw.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]

            if line_width <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word

        lines.append(current_line)  # Add last line of paragraph

    return lines
