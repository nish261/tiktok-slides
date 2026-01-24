from pathlib import Path
import streamlit as st
from typing import Set, Dict, Any
from config.logging import logger
from content_manager.settings.settings_constants import VALID_IMAGE_EXTENSIONS
from content_manager.metadata.metadata import Metadata
from content_manager.metadata.metadata_editor import MetadataEditor
from PIL import Image

# Try to import streamlit-image-coordinates for click positioning
try:
    from streamlit_image_coordinates import streamlit_image_coordinates
    HAS_IMAGE_COORDINATES = True
except ImportError:
    HAS_IMAGE_COORDINATES = False

class ImageManager:
    """Simple image display manager"""
    
    def __init__(self, base_path: Path, content_types: Set[str], products: Dict[str, Any], 
                 metadata: Metadata, metadata_data: Dict, metadata_editor: MetadataEditor):
        self.base_path = base_path
        self.content_types = content_types
        self.products = products
        self.metadata = metadata
        self.valid_extensions = VALID_IMAGE_EXTENSIONS
        self.metadata_data = metadata_data
        self.metadata_editor = metadata_editor
        self.initialize_state()
        
    def initialize_state(self):
        """Initialize image display state"""
        if "current_image" not in st.session_state:
            st.session_state.current_image = None
            
        if "image_settings" not in st.session_state:
            st.session_state.image_settings = None
            
        if "click_position_mode" not in st.session_state:
            st.session_state.click_position_mode = False
            
        if "clicked_position" not in st.session_state:
            st.session_state.clicked_position = None
    
    def display_image(self, image_path: Path):
        """Display a single image"""
        if not image_path.exists():
            st.error(f"Image not found: {image_path}")
            return
            
        if image_path.suffix not in self.valid_extensions:
            st.error(f"Invalid image type: {image_path.suffix}")
            return
            
        try:
            st.image(str(image_path))
        except Exception as e:
            st.error(f"Error displaying image: {e}")

    def render_image(self):
        """Render the current image with safety checks and optional click positioning"""
        # Verify required session state exists
        if not all(key in st.session_state for key in ['content_type', 'selected_image']):
            st.error("Required session state not initialized")
            return
            
        if not st.session_state.content_type or not st.session_state.selected_image:
            st.warning("Please select an image to display")
            return
            
        try:
            # Check if a preview image exists
            if "preview_image_path" in st.session_state:
                image_path = Path(st.session_state.preview_image_path)
                if not image_path.exists():
                    # If preview doesn't exist, fall back to original
                    image_path = self.base_path / st.session_state.content_type / st.session_state.selected_image
                logger.debug(f"Using preview image path: {image_path}")
            else:
                # Use original image path
                image_path = self.base_path / st.session_state.content_type / st.session_state.selected_image
                logger.debug(f"Using original image path: {image_path}")
            
            # Check if we're in click position mode and have the library
            if st.session_state.get("click_position_mode", False) and HAS_IMAGE_COORDINATES:
                # Load image and get dimensions
                img = Image.open(str(image_path))
                orig_width, orig_height = img.size
                
                # Resize image to fit container properly while maintaining aspect ratio
                # Increased width for better visibility, standard column is ~700px
                display_width = 600  
                aspect_ratio = orig_height / orig_width
                display_height = int(display_width * aspect_ratio)
                img_resized = img.resize((display_width, display_height), Image.Resampling.LANCZOS)
                
                # Which caption are we positioning?
                target_caption = st.session_state.get("position_target", "main")
                if target_caption == "main":
                    st.info("👆 **Click to set MAIN CAPTION position** (Caption 1)")
                else:
                    st.info("👆 **Click to set EXTRA CAPTION position** (Caption 2)")
                
                # Display clickable image
                coords = streamlit_image_coordinates(
                    img_resized,
                    key=f"position_picker_{target_caption}",
                    width=display_width,  # Explicitly set width to match our resized image
                )
                
                # If clicked, calculate normalized position with high precision
                if coords is not None:
                    # Check for potential bounds errors
                    click_x = max(0, min(coords["x"], display_width))
                    click_y = max(0, min(coords["y"], display_height))
                    
                    x_norm = round(click_x / display_width, 4)
                    y_norm = round(click_y / display_height, 4)
                    
                    # Store the clicked position with target info
                    st.session_state.clicked_position = {
                        "x": x_norm,
                        "y": y_norm,
                        "raw_x": coords["x"],
                        "raw_y": coords["y"],
                        "img_width": orig_width,
                        "img_height": orig_height,
                        "target": target_caption
                    }
                    
                    st.success(f"📍 **{target_caption.upper()}** position: X={x_norm:.4f}, Y={y_norm:.4f}")
                    st.caption(f"Click: ({coords['x']}, {coords['y']}) → Original: ({int(x_norm * orig_width)}, {int(y_norm * orig_height)}) of {orig_width}x{orig_height}")
                
                # Show Apply button
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Apply Position", use_container_width=True):
                        if st.session_state.clicked_position:
                            # Position will be applied through settings update
                            st.session_state.apply_clicked_position = True
                            st.session_state.click_position_mode = False
                            st.rerun()
                with col2:
                    if st.button("❌ Cancel", use_container_width=True):
                        st.session_state.click_position_mode = False
                        st.session_state.clicked_position = None
                        st.rerun()
            else:
                # Normal image display
                try:
                    st.image(str(image_path), use_column_width=True)
                except TypeError:
                    st.image(str(image_path))
                
                # Show position buttons if library is available and preview exists
                if HAS_IMAGE_COORDINATES and "preview_image_path" in st.session_state:
                    st.markdown("**📍 Set Caption Position:**")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("📍 Caption 1 (Main)", use_container_width=True, key="pos_main"):
                            st.session_state.click_position_mode = True
                            st.session_state.position_target = "main"
                            st.rerun()
                    with col2:
                        if st.button("📍 Caption 2 (Extra)", use_container_width=True, key="pos_extra"):
                            st.session_state.click_position_mode = True
                            st.session_state.position_target = "extra"
                            st.rerun()
            
        except Exception as e:
            logger.error(f"Error displaying image: {str(e)}")
            st.error("Failed to display image")