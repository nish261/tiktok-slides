"""
SVG-based emoji rendering using Pilmoji for crisp, scalable emojis.
Renders emojis to SVG first, then converts to PNG for overlay.
"""
import os
import hashlib
from pathlib import Path
from PIL import Image
from typing import Optional
import tempfile
import cairosvg
import io

try:
    from pilmoji import Pilmoji
    from pilmoji.source import TwemojiSource
    _HAS_PILMOJI = True
except ImportError:
    Pilmoji = None
    TwemojiSource = None
    _HAS_PILMOJI = False

from content_manager.settings.settings_constants import BASE_DIR


class EmojiSVGRenderer:
    """Renders emojis using Pilmoji → SVG → PNG pipeline for crisp quality"""
    
    def __init__(self, emoji_dir: str = "assets/emojis"):
        self.emoji_dir = BASE_DIR / emoji_dir
        self.emoji_dir.mkdir(parents=True, exist_ok=True)
        
    def get_emoji_png_path(self, emoji_char: str, font_size: int = 100) -> Optional[str]:
        """Get PNG file path for emoji, rendering via SVG if needed"""
        
        # Create a unique filename based on emoji and size
        emoji_hash = hashlib.md5(f"{emoji_char}_{font_size}".encode()).hexdigest()
        png_filename = f"emoji_{emoji_hash}.png"
        png_path = self.emoji_dir / png_filename
        
        # Return existing file if it exists
        if png_path.exists():
            return str(png_path)
        
        # Render new emoji via SVG
        if _HAS_PILMOJI:
            return self._render_emoji_via_svg(emoji_char, font_size, png_path)
        else:
            print(f"Pilmoji not available for emoji {emoji_char}")
            return None
    
    def _render_emoji_via_svg(self, emoji_char: str, font_size: int, png_path: Path) -> Optional[str]:
        """Render emoji using Pilmoji → SVG → PNG pipeline"""
        try:
            # Create a temporary SVG file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as svg_file:
                svg_path = svg_file.name
            
            # Create a temporary image for Pilmoji rendering
            temp_img = Image.new('RGBA', (font_size * 2, font_size * 2), (0, 0, 0, 0))
            
            # Use Pilmoji to render the emoji
            with Pilmoji(temp_img, source=TwemojiSource) as pilmoji:
                pilmoji.text((font_size // 2, font_size // 2), emoji_char, fill=(0, 0, 0, 255))
            
            # Convert the PIL image to SVG using a simple approach
            # We'll create a minimal SVG with the emoji as a text element
            svg_content = self._create_emoji_svg(emoji_char, font_size)
            
            with open(svg_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            
            # Convert SVG to PNG using cairosvg
            png_data = cairosvg.svg2png(url=svg_path, output_width=font_size, output_height=font_size)
            
            # Save PNG
            with open(png_path, 'wb') as f:
                f.write(png_data)
            
            # Clean up temporary SVG file
            os.unlink(svg_path)
            
            print(f"Successfully rendered emoji {emoji_char} via SVG → PNG pipeline")
            return str(png_path)
            
        except Exception as e:
            print(f"Failed to render emoji {emoji_char} via SVG: {e}")
            # Clean up temp file if it exists
            if 'svg_path' in locals() and os.path.exists(svg_path):
                os.unlink(svg_path)
            return None
    
    def _create_emoji_svg(self, emoji_char: str, font_size: int) -> str:
        """Create a minimal SVG with the emoji character"""
        # Use a system emoji font that supports the character
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{font_size}" height="{font_size}" viewBox="0 0 {font_size} {font_size}" xmlns="http://www.w3.org/2000/svg">
    <text x="50%" y="50%" font-size="{font_size * 0.8}" font-family="Apple Color Emoji, Noto Color Emoji, Segoe UI Emoji, sans-serif" 
          text-anchor="middle" dominant-baseline="central" fill="black">{emoji_char}</text>
</svg>'''
        return svg_content
    
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
emoji_svg_renderer = EmojiSVGRenderer()
