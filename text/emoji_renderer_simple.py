"""
Simple, reliable emoji renderer that works without external dependencies.
Uses system emoji fonts and creates PNG overlays directly.
"""
import os
import hashlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Optional

from content_manager.settings.settings_constants import BASE_DIR


class SimpleEmojiRenderer:
    """Simple emoji renderer that works reliably on all systems"""
    
    def __init__(self, emoji_dir: str = "assets/emojis"):
        self.emoji_dir = BASE_DIR / emoji_dir
        self.emoji_dir.mkdir(parents=True, exist_ok=True)
        
    def get_emoji_png_path(self, emoji_char: str, font_size: int = 100) -> Optional[str]:
        """Get PNG file path for emoji, creating it if needed"""
        
        # Create a unique filename based on emoji and size
        emoji_hash = hashlib.md5(f"{emoji_char}_{font_size}".encode()).hexdigest()
        png_filename = f"emoji_{emoji_hash}.png"
        png_path = self.emoji_dir / png_filename
        
        # Return existing file if it exists
        if png_path.exists():
            return str(png_path)
        
        # Create new emoji PNG
        return self._create_emoji_png(emoji_char, font_size, png_path)
    
    def _create_emoji_png(self, emoji_char: str, font_size: int, png_path: Path) -> Optional[str]:
        """Create emoji PNG using system fonts"""
        try:
            # Create a larger temporary image for rendering
            temp_size = font_size * 3
            temp_img = Image.new('RGBA', (temp_size, temp_size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(temp_img)
            
            # Try different emoji fonts in order of preference
            emoji_fonts = [
                "/System/Library/Fonts/Apple Color Emoji.ttc",  # macOS
                "/System/Library/Fonts/Supplemental/Apple Color Emoji.ttc",  # macOS alternative
                "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",  # Linux
                "/Windows/Fonts/seguiemj.ttf",  # Windows
            ]
            
            font_loaded = False
            for font_path in emoji_fonts:
                try:
                    if os.path.exists(font_path):
                        # Apple Color Emoji needs size 20, others can use requested size
                        if "Apple Color Emoji" in font_path:
                            emoji_font_size = 20
                        else:
                            emoji_font_size = font_size
                        
                        font = ImageFont.truetype(font_path, emoji_font_size)
                        font_loaded = True
                        print(f"Loaded emoji font: {font_path}")
                        break
                except Exception as e:
                    print(f"Failed to load {font_path}: {e}")
                    continue
            
            if not font_loaded:
                print(f"No emoji font available for {emoji_char}")
                return None
            
            # Draw emoji in center of temporary image
            text_bbox = draw.textbbox((0, 0), emoji_char, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            x = (temp_size - text_width) // 2
            y = (temp_size - text_height) // 2
            
            # Draw the emoji
            draw.text((x, y), emoji_char, font=font, fill=(0, 0, 0, 255))
            
            # Get bounding box of non-transparent pixels
            bbox = temp_img.getbbox()
            if bbox:
                # Crop to content
                cropped = temp_img.crop(bbox)
                
                # Resize to target size
                final_img = cropped.resize((font_size, font_size), Image.Resampling.LANCZOS)
            else:
                # If no content detected, create a minimal transparent image
                final_img = Image.new('RGBA', (font_size, font_size), (0, 0, 0, 0))
            
            # Save PNG
            final_img.save(png_path, 'PNG')
            
            print(f"Successfully created emoji PNG for {emoji_char}")
            return str(png_path)
            
        except Exception as e:
            print(f"Failed to create emoji PNG for {emoji_char}: {e}")
            return None
    
    def render_emoji_overlay(self, 
                           base_image: Image.Image, 
                           emoji_char: str, 
                           size: int, 
                           position: tuple[int, int],
                           alpha: float = 1.0) -> Image.Image:
        """Render an emoji as a PNG overlay on the base image"""
        
        png_path = self.get_emoji_png_path(emoji_char, size)
        if not png_path:
            print(f"No PNG available for emoji: {emoji_char}")
            return base_image
        
        try:
            # Load emoji PNG
            emoji_img = Image.open(png_path).convert("RGBA")
            
            # Resize emoji to target size if needed
            if emoji_img.size != (size, size):
                emoji_img = emoji_img.resize((size, size), Image.Resampling.LANCZOS)
            
            # Apply alpha if needed
            if alpha < 1.0:
                alpha_mask = Image.new("L", emoji_img.size, int(255 * alpha))
                emoji_img.putalpha(alpha_mask)
            
            # Paste emoji onto base image
            x, y = position
            base_image.paste(emoji_img, (x, y), emoji_img if emoji_img.mode == 'RGBA' else None)
            
            return base_image
            
        except Exception as e:
            print(f"Failed to render emoji overlay for {emoji_char}: {e}")
            return base_image


# Global instance
simple_emoji_renderer = SimpleEmojiRenderer()
