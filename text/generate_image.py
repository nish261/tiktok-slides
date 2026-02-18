from PIL import Image
from typing import Dict, Any
from content_manager.settings.settings_constants import VALID_TEXT_TYPES, BASE_DIR, REFERENCE_WIDTH, REFERENCE_HEIGHT
from text.highlight_text import draw_highlight_image
from text.plain_text import draw_plain_image  # We'll create this later
import random
from config.logging import logger

# TikTok standard dimensions
TIKTOK_WIDTH = 1080
TIKTOK_HEIGHT = 1920


def fit_to_tiktok_frame(image: Image.Image) -> Image.Image:
    """Place image inside a 1080x1920 (9:16) TikTok frame, scaled to fit and centered.

    This is called BEFORE text rendering to ensure consistent font sizes.
    """
    # Create black background (TikTok's default)
    frame = Image.new("RGB", (TIKTOK_WIDTH, TIKTOK_HEIGHT), (0, 0, 0))

    # Get original dimensions
    orig_width, orig_height = image.size

    # Calculate scale to fit within frame while maintaining aspect ratio
    scale_w = TIKTOK_WIDTH / orig_width
    scale_h = TIKTOK_HEIGHT / orig_height
    scale = min(scale_w, scale_h)  # Use smaller scale to fit entirely

    # Calculate new dimensions
    new_width = int(orig_width * scale)
    new_height = int(orig_height * scale)

    # Resize image with high quality
    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Calculate position to center
    x = (TIKTOK_WIDTH - new_width) // 2
    y = (TIKTOK_HEIGHT - new_height) // 2

    # Paste onto frame (handle RGBA)
    if resized.mode == "RGBA":
        frame = frame.convert("RGBA")
        frame.paste(resized, (x, y), resized)
    else:
        frame.paste(resized, (x, y))

    resized.close()
    return frame


def scale_for_image(value: int, image_height: int) -> int:
    """Scale a value (like font size) from TikTok reference to actual image size.

    Settings are defined for 1080x1920 (TikTok standard).
    This scales them proportionally for any image size.
    """
    scale_factor = image_height / REFERENCE_HEIGHT
    return int(value * scale_factor)


# Map text types to their rendering functions
TEXT_RENDERERS = {
    "highlight": draw_highlight_image,
    "plain": draw_plain_image  # Will implement later
}

# Map color keys to parameter names for each text type
COLOR_PARAM_MAPPING = {
    "highlight": {
        "text": "text_color",
        "background": "background_color"
    },
    "plain": {
        "text": "text_color",
        "outline": "outline_color"
    }
}

def generate_image(settings: Dict[str, Any], text_type: str, colour_index: int, image_path: str, text: str) -> Image.Image:
    """Calculate settings and apply text to image.

    IMPORTANT: Image is fit to 9:16 TikTok frame (1080x1920) FIRST,
    then text is drawn. This ensures consistent font sizes across all images.
    """
    logger.debug(f"GENERATE // Text type: {text_type}")
    logger.debug(f"GENERATE // Settings for text type: {settings['text_settings'][text_type]}")

    if text_type not in VALID_TEXT_TYPES:
        raise ValueError(f"Invalid text type: {text_type}")
    logger.debug(f"GENERATE IMAGE CALLED WITH TEXT: {text}")

    # Get common settings
    # font_path access removed as it causes KeyError and is calculated later as resolved_font_path
    text_settings = settings["text_settings"][text_type]
    logger.debug(f"generate image // settings: {settings}")

    # Load original image and fit to 9:16 TikTok frame FIRST
    # This ensures consistent font sizing regardless of original image dimensions
    original_image = Image.open(image_path)
    image = fit_to_tiktok_frame(original_image)
    original_image.close()

    # Now image is always 1080x1920
    width, height = image.size  # Will be 1080x1920
    
    # Calculate margins and usable area
    margins = text_settings["margins"]
    logger.debug(f"Raw margins from settings: {margins}")
    
    margin_left = int(width * margins["left"])
    margin_right = int(width * margins["right"])
    margin_top = int(height * margins["top"])
    margin_bottom = int(height * margins["bottom"])
    
    logger.debug(f"Calculated pixel margins - Left: {margin_left}, Right: {margin_right}, Top: {margin_top}, Bottom: {margin_bottom}")
    logger.debug(f"Image dimensions - Width: {width}, Height: {height}")
    
    max_width = int(width - margin_left - margin_right)
    logger.debug(f"Max width after margins: {max_width}")
    
    # Calculate position with jitter
    position = text_settings["position"]
    
    # helper for safe range extraction
    def get_pos_value(pos_data):
        if isinstance(pos_data, (list, tuple)) and len(pos_data) >= 2:
            return random.uniform(pos_data[0], pos_data[1])
        elif isinstance(pos_data, (list, tuple)) and len(pos_data) == 1:
            return float(pos_data[0])
        else:
            return float(pos_data)

    v_pos = get_pos_value(position["vertical"])
    v_jitter = random.uniform(-position["vertical_jitter"], position["vertical_jitter"])
    height_center_position = v_pos + v_jitter
    
    h_pos = get_pos_value(position["horizontal"])
    h_jitter = random.uniform(-position["horizontal_jitter"], position["horizontal_jitter"])
    width_center_position = h_pos + h_jitter
    
    # Keep within margins using pixel values
    original_height_pos = height_center_position
    original_width_pos = width_center_position
    
    height_center_position = max(margin_top/height, min(1 - margin_bottom/height, height_center_position))
    width_center_position = max(margin_left/width, min(1 - margin_right/width, width_center_position))
    
    logger.debug(f"Position adjustments:")
    logger.debug(f"Height - Original: {original_height_pos:.3f}, After margins: {height_center_position:.3f}")
    logger.debug(f"Width - Original: {original_width_pos:.3f}, After margins: {width_center_position:.3f}")
    
    # Pass calculated pixel margins instead of ratios
    calculated_margins = {
        "top": margin_top,
        "bottom": margin_bottom,
        "left": margin_left,
        "right": margin_right
    }
    
    # Basic settings that apply to both text types
    # Resolve absolute font path inside the package (avoids CWD issues)
    resolved_font_path = str((BASE_DIR / text_settings["font"].replace("assets.fonts.", "assets/fonts/")).resolve())

    # Scale font size relative to TikTok reference (1080x1920)
    # So a font_size of 70 on 1920px height stays proportional on any image
    scaled_font_size = scale_for_image(text_settings["font_size"], height)
    logger.debug(f"Font scaling: {text_settings['font_size']} @ 1920px -> {scaled_font_size} @ {height}px")

    common_settings = {
        "image": image,
        "width": width,
        "height": height,
        "text": text,
        "font_size": scaled_font_size,
        "font_path": resolved_font_path,
        "max_width": max_width,
        "width_center_position": width_center_position,
        "height_center_position": height_center_position,
        "margins": calculated_margins
    }
    
    # Get colors for current index
    colors = text_settings["colors"][colour_index]
    param_mapping = COLOR_PARAM_MAPPING[text_type]
    style_settings = {}
    
    # Map colors using the param mapping
    for key in VALID_TEXT_TYPES[text_type]["required_color_keys"]:
        if key not in colors:
            raise KeyError(f"Missing required color key '{key}' for text type '{text_type}'")
        style_settings[param_mapping[key]] = colors[key]
    
    # Add style-specific settings (also scaled to image size)
    scaled_style_value = scale_for_image(text_settings["style_value"], height)

    if text_type == "plain":
        style_settings["outline_width"] = scaled_style_value
        logger.trace("GENERATE // Drawing plain text")
        logger.trace(f"GENERATE // Font: {text_settings['font']}")
        logger.trace(f"GENERATE // Font size: {text_settings['font_size']} -> scaled: {scaled_font_size}")
        logger.trace(f"GENERATE // Style type: {text_settings['style_type']}")
        logger.trace(f"GENERATE // Style value: {text_settings['style_value']} -> scaled: {scaled_style_value}")
        logger.trace(f"GENERATE // Colors: {colors}")
    elif text_type == "highlight":
        style_settings["corner_radius"] = scaled_style_value
        logger.trace("GENERATE // Drawing highlight text")
        
    logger.debug(f"Using image {image_path} with text type {text_type}")
    logger.debug(f"Style settings for {text_type}: {style_settings}")
    
    # Merge settings and render
    renderer = TEXT_RENDERERS[text_type]
    final_settings = {**common_settings, **style_settings}
    
    # NEW: Multi-caption support using '||' delimiter.
    # Example: "Top caption || Bottom caption"
    # Renders multiple captions with separate positions for each.
    parts = [p.strip() for p in text.split("||")] if "||" in text else [text]
    if len(parts) == 1:
        return renderer(**final_settings)
    
    # Render multiple captions with separate positions
    extra_settings = settings.get("extra_caption_settings")
    
    img = image
    for idx, part in enumerate(parts):
        # Deep copy to prevent sharing mutable dicts like margins between captions
        local_settings = dict(final_settings)
        local_settings["margins"] = dict(final_settings["margins"])  # Deep copy margins!
        local_settings["image"] = img
        local_settings["text"] = part
        
        if idx > 0:
            print(f"\n{'='*60}")
            print(f"CAPTION {idx+1} DEBUG")
            print(f"{'='*60}")
            print(f"Extra settings exists: {extra_settings is not None}")
            if extra_settings:
                print(f"Vertical position from settings: {extra_settings.get('vertical_position')}")
                print(f"Horizontal position from settings: {extra_settings.get('horizontal_position')}")
            print(f"Position BEFORE applying extras:")
            print(f"  Width: {local_settings.get('width_center_position')}")
            print(f"  Height: {local_settings.get('height_center_position')}")
            
        if idx > 0 and extra_settings:
            # === EXTRA CAPTION HANDLING ===
            # Explicitly reset positions to defaults to prevent inheriting from Main Caption
            local_settings["width_center_position"] = 0.5
            local_settings["height_center_position"] = 0.5
            
            # We treat this exactly like a standard separate caption
            
            # 1. Vertical Position
            if "vertical_position" in extra_settings:
                v_data = extra_settings["vertical_position"]
                v_jitter = extra_settings.get("vertical_jitter", 0.0)

                # Handle range or single value
                if isinstance(v_data, (list, tuple)) and len(v_data) >= 2:
                    v_pos = random.uniform(v_data[0], v_data[1])
                else:
                    v_pos = float(v_data) if not isinstance(v_data, (list, tuple)) else v_data[0]

                # Apply jitter
                v_jitter_val = random.uniform(-v_jitter, v_jitter)
                final_v_pos = v_pos + v_jitter_val
                local_settings["height_center_position"] = final_v_pos
                print(f"✅ Applied vertical position: {v_data} -> {v_pos:.4f} + jitter {v_jitter_val:.4f} = {final_v_pos:.4f}")

            # 2. Horizontal Position
            if "horizontal_position" in extra_settings:
                h_data = extra_settings["horizontal_position"]
                h_jitter = extra_settings.get("horizontal_jitter", 0.0)

                # Handle range or single value
                if isinstance(h_data, (list, tuple)) and len(h_data) >= 2:
                    h_pos = random.uniform(h_data[0], h_data[1])
                else:
                    h_pos = float(h_data) if not isinstance(h_data, (list, tuple)) else h_data[0]

                # Apply jitter
                h_jitter_val = random.uniform(-h_jitter, h_jitter)
                final_h_pos = h_pos + h_jitter_val
                local_settings["width_center_position"] = final_h_pos
                print(f"✅ Applied horizontal position: {h_data} -> {h_pos:.4f} + jitter {h_jitter_val:.4f} = {final_h_pos:.4f}")
            else:
                # If no horizontal position specified for extra, default to 0.5 (Center)
                # Do NOT inherit from main caption
                local_settings["width_center_position"] = 0.5
                print(f"⚠️  No horizontal position in extra_settings, using default 0.5")

            # 3. Apply Font Settings
            if "font" in extra_settings:
                # Handle path resolution if needed
                try:
                    from pathlib import Path
                    # re-import here to be safe, though should be top level ideally
                    # Fix: Make sure BASE_DIR is defined before use
                    current_file_path = Path(__file__).resolve()
                    base_dir = current_file_path.parent.parent
                    
                    font_setting = extra_settings["font"]
                    # Calculate path similar to how it is done in main settings
                    if "assets.fonts." in font_setting:
                         rel_path = font_setting.replace("assets.fonts.", "assets/fonts/")
                         resolved_font = str((base_dir / rel_path).resolve())
                         local_settings["font_path"] = resolved_font
                    else:
                         local_settings["font_path"] = font_setting
                except Exception as e:
                    logger.error(f"Failed to resolve font path for extra caption: {e}")
                    # Fallback if path manipulation fails
                    pass
            
            if "font_size" in extra_settings:
                local_settings["font_size"] = extra_settings["font_size"]
            
            # 4. Apply Colors & Styles
            if text_type == "plain":
                if "text_color" in extra_settings:
                    local_settings["text_color"] = extra_settings["text_color"]
                if "outline_color" in extra_settings:
                    local_settings["outline_color"] = extra_settings["outline_color"]
                if "style_value" in extra_settings:
                    local_settings["outline_width"] = extra_settings["style_value"]
            elif text_type == "highlight":
                if "text_color" in extra_settings:
                    local_settings["text_color"] = extra_settings["text_color"]
                if "outline_color" in extra_settings:
                    local_settings["background_color"] = extra_settings["outline_color"]
                if "style_value" in extra_settings:
                    local_settings["corner_radius"] = extra_settings["style_value"]
            
            # 5. Apply Margins
            if "margin_top" in extra_settings:
                local_settings["margins"]["top"] = extra_settings["margin_top"]
            if "margin_bottom" in extra_settings:
                local_settings["margins"]["bottom"] = extra_settings["margin_bottom"]
            if "margin_left" in extra_settings:
                local_settings["margins"]["left"] = extra_settings["margin_left"]
            if "margin_right" in extra_settings:
                local_settings["margins"]["right"] = extra_settings["margin_right"]

        # DEBUG: Log final applied settings for extra captions
        if idx > 0:
            # Fallback if "Separate settings" is OFF:
            # Shift extra captions down automatically so they don't overlap
            if not extra_settings:
                current_y = local_settings.get("height_center_position", 0.5)
                # Add 15% height offset per caption index
                local_settings["height_center_position"] = min(0.95, current_y + (0.15 * idx))
                print(f"⚠️  No extra_settings - auto-offset applied: {local_settings['height_center_position']}")

            print(f"\nFINAL SETTINGS FOR CAPTION {idx+1}:")
            print(f"  Width position: {local_settings.get('width_center_position'):.4f}")
            print(f"  Height position: {local_settings.get('height_center_position'):.4f}")
            print(f"  Font size: {local_settings.get('font_size')}")
            print(f"  Text color: {local_settings.get('text_color')}")
            print(f"  Margins: {local_settings.get('margins')}")
            print(f"{'='*60}\n")
        
        img = renderer(**local_settings)
    
    return img