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
                img_width, img_height = img.size
                
                # Show instruction
                st.info("👆 **Click on the image to set text position**")
                
                # Display clickable image
                coords = streamlit_image_coordinates(
                    img,
                    key="position_picker"
                )
                
                # If clicked, calculate normalized position
                if coords is not None:
                    x_norm = coords["x"] / img_width
                    y_norm = coords["y"] / img_height
                    
                    # Store the clicked position
                    st.session_state.clicked_position = {
                        "x": x_norm,
                        "y": y_norm,
                        "raw_x": coords["x"],
                        "raw_y": coords["y"],
                        "img_width": img_width,
                        "img_height": img_height
                    }
                    
                    st.success(f"📍 Position set to: ({x_norm:.2f}, {y_norm:.2f})")
                    st.caption(f"Pixel: ({coords['x']}, {coords['y']}) of ({img_width}x{img_height})")
                
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
                
                # Show "Set Position" button if library is available and preview exists
                if HAS_IMAGE_COORDINATES and "preview_image_path" in st.session_state:
                    if st.button("📍 Click to Set Position", use_container_width=True):
                        st.session_state.click_position_mode = True
                        st.rerun()
            
        except Exception as e:
            logger.error(f"Error displaying image: {str(e)}")
            st.error("Failed to display image")