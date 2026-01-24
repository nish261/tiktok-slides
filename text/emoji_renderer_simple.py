"""
Simple, reliable emoji renderer that works without external dependencies.
Uses system emoji fonts and creates PNG overlays directly.
"""
import os
import hashlib
import urllib.request
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Optional

from content_manager.settings.settings_constants import BASE_DIR


class SimpleEmojiRenderer:
    """Simple emoji renderer that works reliably on all systems"""
    
    def __init__(self, emoji_dir: str = "assets/emojis"):
        self.emoji_dir = BASE_DIR / emoji_dir
        self.emoji_dir.mkdir(parents=True, exist_ok=True)
        
    def _emoji_to_twemoji_path(self, emoji_char: str) -> str:
        """Convert emoji string to twemoji-style codepoint sequence"""
        cps = [f"{ord(ch):x}" for ch in emoji_char]
        return "-".join(cps)
    
    def _download_url(self, url: str, dest: Path, retries: int = 2) -> bool:
        """Download a URL to a file with retries"""
        try:
            for attempt in range(retries):
                try:
                    with urllib.request.urlopen(url, timeout=15) as resp:
                        if resp.status != 200:
                            raise Exception(f"HTTP {resp.status}")
                        data = resp.read()
                        dest.write_bytes(data)
                        return True
                except Exception:
                    time.sleep(0.5 + attempt)
            return False
        except Exception:
            return False
    
    def _extract_apple_emoji(self, emoji_char: str, font_size: int, png_path: Path) -> bool:
        """Extract Apple Color Emoji bitmap data and create PNG"""
        try:
            # Apple Color Emoji font path
            apple_font_path = "/System/Library/Fonts/Apple Color Emoji.ttc"
            if not os.path.exists(apple_font_path):
                return False
            
            # Load Apple Color Emoji at a LARGER size for better quality
            # Apple Color Emoji has bitmaps at sizes like 20, 32, 40, 48, 64, 96, 160
            # Use 160 so we scale DOWN (not up) for crisp results
            native_size = 160
            font = ImageFont.truetype(apple_font_path, native_size)
            
            # Create temporary image sized for the native emoji
            temp_size = native_size * 2
            temp_img = Image.new('RGBA', (temp_size, temp_size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(temp_img)
            
            # Get text bounding box
            bbox = draw.textbbox((0, 0), emoji_char, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Center the emoji
            x = (temp_size - text_width) // 2
            y = (temp_size - text_height) // 2
            
            # Draw with embedded_color=True to get color bitmap
            draw.text((x, y), emoji_char, font=font, fill=(0, 0, 0, 255), embedded_color=True)
            
            # Get bounding box of non-transparent pixels
            bbox = temp_img.getbbox()
            if bbox:
                # Crop to content
                cropped = temp_img.crop(bbox)
                
                # Resize to target size - LANCZOS is great for downscaling
                final_img = cropped.resize((font_size, font_size), Image.Resampling.LANCZOS)
                
                # Save as PNG
                final_img.save(png_path, "PNG")
                return True
            
            return False
            
        except Exception as e:
            print(f"Apple emoji extraction failed for {emoji_char}: {e}")
            return False
        
        
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
        """Create emoji PNG - prioritize Twemoji for high quality, Apple as fallback"""
        try:
            print(f"Creating emoji PNG for {emoji_char}...")
            
            # PRIORITY 1: Try Twemoji first (high-res 72x72 PNGs, looks great when scaled)
            codepath = self._emoji_to_twemoji_path(emoji_char)
            twemoji_url = f"https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/72x72/{codepath}.png"
            
            tmp_dl = png_path.with_suffix(".twemoji.tmp")
            ok = self._download_url(twemoji_url, tmp_dl)
            if ok:
                # Open and resize to desired font_size
                img = Image.open(tmp_dl).convert("RGBA")
                final_img = img.resize((font_size, font_size), Image.Resampling.LANCZOS)
                final_img.save(png_path, "PNG")
                try:
                    tmp_dl.unlink()
                except Exception:
                    pass
                print(f"Successfully created Twemoji PNG for {emoji_char}")
                return str(png_path)
            
            print(f"Twemoji download failed for {emoji_char}, trying Apple extraction...")
            
            # PRIORITY 2: Fallback to Apple extraction (lower quality but works offline)
            apple_result = self._extract_apple_emoji(emoji_char, font_size, png_path)
            if apple_result:
                print(f"Successfully created Apple emoji PNG for {emoji_char}")
                return str(png_path)
            
            # PRIORITY 3: Final fallback to monochrome
            print(f"Apple emoji extraction failed, trying monochrome fallback...")
            return self._create_monochrome_emoji(emoji_char, font_size, png_path)
                
        except Exception as e:
            print(f"Failed to create emoji PNG for {emoji_char}: {e}")
            return self._create_monochrome_emoji(emoji_char, font_size, png_path)
    
    def _create_monochrome_emoji(self, emoji_char: str, font_size: int, png_path: Path) -> Optional[str]:
        """Fallback: Create monochrome emoji using system fonts"""
        try:
            temp_size = max(256, font_size * 3)
            temp_img = Image.new('RGBA', (temp_size, temp_size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(temp_img)

            emoji_fonts = [
                "/System/Library/Fonts/Apple Color Emoji.ttc",
                "/System/Library/Fonts/Supplemental/Apple Color Emoji.ttc",
                "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
                "/Windows/Fonts/seguiemj.ttf",
            ]

            font = None
            for font_path in emoji_fonts:
                try:
                    if os.path.exists(font_path):
                        emoji_font_size = 20 if "Apple Color Emoji" in font_path else font_size
                        font = ImageFont.truetype(font_path, emoji_font_size)
                        break
                except Exception:
                    continue

            if font:
                bbox = draw.textbbox((0, 0), emoji_char, font=font)
                w = bbox[2] - bbox[0]
                h = bbox[3] - bbox[1]
                x = (temp_size - w) // 2
                y = (temp_size - h) // 2
                draw.text((x, y), emoji_char, font=font, fill=(0,0,0,255))
                bbox2 = temp_img.getbbox()
                if bbox2:
                    cropped = temp_img.crop(bbox2)
                    final_img = cropped.resize((font_size, font_size), Image.Resampling.LANCZOS)
                    final_img.save(png_path, "PNG")
                    print(f"Created monochrome emoji PNG for {emoji_char} (fallback)")
                    return str(png_path)
            
            return None
                
        except Exception as e:
            print(f"Failed to create monochrome emoji PNG for {emoji_char}: {e}")
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
            x, y = int(x), int(y)  # Convert floats to integers
            base_image.paste(emoji_img, (x, y), emoji_img if emoji_img.mode == 'RGBA' else None)
            
            return base_image
            
        except Exception as e:
            print(f"Failed to render emoji overlay for {emoji_char}: {e}")
            return base_image


# Global instance
simple_emoji_renderer = SimpleEmojiRenderer()
