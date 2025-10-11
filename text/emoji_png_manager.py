"""
PNG-based emoji rendering manager for crisp, scalable emojis.
Replaces font-based emoji rendering with high-quality PNG overlays.
"""
import os
import requests
from pathlib import Path
from PIL import Image
from typing import Dict, Optional, Tuple
import hashlib


class EmojiPNGManager:
    """Manages emoji PNG files for overlay rendering"""
    
    def __init__(self, emoji_dir: str = "assets/emojis"):
        from content_manager.settings.settings_constants import BASE_DIR
        self.emoji_dir = BASE_DIR / emoji_dir
        self.emoji_dir.mkdir(parents=True, exist_ok=True)
        
        # Mapping of common emoji characters to their PNG filenames
        self.emoji_mapping = {
            "💔": "broken_heart.png",
            "💸": "money_bag.png",  # Using money bag for 💸 as close substitute
            "💰": "money_bag.png",
            "💵": "money_bag.png",
            "💴": "money_bag.png",
            "💶": "money_bag.png",
            "💷": "money_bag.png",
            "💳": "money_bag.png",
            # Add more mappings as needed
        }
    
    def get_emoji_png_path(self, emoji_char: str) -> Optional[str]:
        """Get the PNG file path for an emoji character"""
        if emoji_char in self.emoji_mapping:
            png_path = self.emoji_dir / self.emoji_mapping[emoji_char]
            if png_path.exists():
                return str(png_path)
        
        # Try to download emoji if not found
        return self._download_emoji_png(emoji_char)
    
    def _download_emoji_png(self, emoji_char: str) -> Optional[str]:
        """Download emoji PNG from Twemoji CDN"""
        try:
            # Get Unicode codepoint
            codepoint = f"{ord(emoji_char):x}"
            
            # Twemoji CDN URL
            url = f"https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/{codepoint}.png"
            
            # Download the emoji
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                # Save with a safe filename
                safe_name = f"emoji_{codepoint}.png"
                png_path = self.emoji_dir / safe_name
                
                with open(png_path, 'wb') as f:
                    f.write(response.content)
                
                # Update mapping for future use
                self.emoji_mapping[emoji_char] = safe_name
                
                print(f"Downloaded emoji PNG: {emoji_char} -> {png_path}")
                return str(png_path)
                
        except Exception as e:
            print(f"Failed to download emoji PNG for {emoji_char}: {e}")
        
        return None
    
    def render_emoji_overlay(self, 
                           base_image: Image.Image, 
                           emoji_char: str, 
                           size: int, 
                           position: Tuple[int, int],
                           alpha: float = 1.0) -> Image.Image:
        """Render an emoji as a PNG overlay on the base image"""
        
        png_path = self.get_emoji_png_path(emoji_char)
        if not png_path:
            print(f"No PNG available for emoji: {emoji_char}")
            return base_image
        
        try:
            # Load emoji PNG
            emoji_img = Image.open(png_path).convert("RGBA")
            
            # Resize emoji to target size
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
    
    def get_emoji_size_for_text(self, text_font_size: int, emoji_char: str) -> int:
        """Calculate appropriate emoji size to match text font size"""
        # Emojis typically look good at about 1.2x the text size for visual balance
        return int(text_font_size * 1.2)


# Global instance
emoji_png_manager = EmojiPNGManager()
