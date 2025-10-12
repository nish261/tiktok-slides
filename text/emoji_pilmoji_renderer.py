"""
Pilmoji-based emoji renderer for reliable emoji rendering.
Uses pilmoji library to render mixed text+emoji content.
"""
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Optional

try:
    from pilmoji import Pilmoji
    _HAS_PILMOJI = True
except ImportError:
    Pilmoji = None
    _HAS_PILMOJI = False

from content_manager.settings.settings_constants import BASE_DIR


class PilmojiRenderer:
    """Pilmoji-based emoji renderer that handles mixed text+emoji"""
    
    def __init__(self):
        if not _HAS_PILMOJI:
            print("Warning: pilmoji not available, emoji rendering will fall back to system fonts")
    
    def render_mixed_text(self, 
                         base_image: Image.Image,
                         text: str,
                         font: ImageFont.FreeTypeFont,
                         position: tuple[int, int],
                         fill: str = (0, 0, 0, 255),
                         spacing: int = 4) -> Image.Image:
        """Render mixed text+emoji using pilmoji"""
        
        if not _HAS_PILMOJI:
            # Fallback to regular text rendering
            draw = ImageDraw.Draw(base_image)
            draw.text(position, text, font=font, fill=fill)
            return base_image
        
        try:
            # Use pilmoji for mixed text+emoji rendering
            with Pilmoji(base_image) as pilmoji:
                # Convert float positions to integers
                x, y = position
                int_position = (int(x), int(y))
                pilmoji.text(int_position, text, font=font, fill=fill, spacing=spacing)
            
            return base_image
            
        except Exception as e:
            print(f"Pilmoji rendering failed: {e}, falling back to regular text")
            # Fallback to regular text rendering
            draw = ImageDraw.Draw(base_image)
            draw.text(position, text, font=font, fill=fill)
            return base_image
    
    def render_multiline_mixed_text(self,
                                   base_image: Image.Image,
                                   text: str,
                                   font: ImageFont.FreeTypeFont,
                                   position: tuple[int, int],
                                   max_width: int,
                                   fill: str = (0, 0, 0, 255),
                                   line_spacing: int = 20) -> Image.Image:
        """Render multiline mixed text+emoji using pilmoji"""
        
        if not _HAS_PILMOJI:
            # Fallback to regular multiline text rendering
            draw = ImageDraw.Draw(base_image)
            lines = self._wrap_text(draw, text, font, max_width)
            
            x, y = position
            for line in lines:
                draw.text((x, y), line, font=font, fill=fill)
                y += font.size + line_spacing
            
            return base_image
        
        try:
            # Use pilmoji for mixed text+emoji rendering
            with Pilmoji(base_image) as pilmoji:
                lines = self._wrap_text(pilmoji, text, font, max_width)
                
                x, y = position
                x, y = int(x), int(y)  # Convert to integers
                for line in lines:
                    pilmoji.text((x, y), line, font=font, fill=fill)
                    y += font.size + line_spacing
            
            return base_image
            
        except Exception as e:
            print(f"Pilmoji multiline rendering failed: {e}, falling back to regular text")
            # Fallback to regular multiline text rendering
            draw = ImageDraw.Draw(base_image)
            lines = self._wrap_text(draw, text, font, max_width)
            
            x, y = position
            for line in lines:
                draw.text((x, y), line, font=font, fill=fill)
                y += font.size + line_spacing
            
            return base_image
    
    def _wrap_text(self, draw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
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
                
                # Use textlength for newer PIL versions
                if hasattr(draw, 'textlength'):
                    line_width = draw.textlength(test_line, font=font)
                else:
                    # Fallback for older PIL versions
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


# Global instance
pilmoji_renderer = PilmojiRenderer()
