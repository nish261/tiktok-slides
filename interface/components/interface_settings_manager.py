from pathlib import Path
import json
import streamlit as st  # type: ignore
from PIL import Image
from content_manager.settings.settings_constants import (
    DEFAULT_TEMPLATE,
    VALID_TEXT_TYPES,
    TIKTOK_WIDTH,
    TIKTOK_HEIGHT,
)
from typing import List, Dict, Any, Set
from content_manager.metadata.metadata_editor import MetadataEditor
from content_manager.metadata.metadata import Metadata
from content_manager.settings.settings_handler import Settings
from content_manager.captions import CaptionsHelper
from config.logging import logger


class InterfaceSettingsManager:
    """Manages interface settings and state

    Settings Levels (in order of priority):
    1. default
    2. content
    3. product
    4. custom
    """

    def __init__(
        self,
        base_path: Path,
        content_types: Set[str],
        products: Dict[str, Any],
        metadata: Metadata,
        metadata_data: Dict,
        metadata_editor: MetadataEditor,
        settings_handler: Settings,
        separator: str
    ):
        self.base_path = base_path
        self.content_types = content_types
        self.products = products
        self.separator = separator
        self.metadata = metadata
        self.metadata_data = metadata_data
        self.metadata_editor = metadata_editor
        self.settings_handler = settings_handler
        # Create font mapping on init
        self.fonts = {
            font_name: self.settings_handler.load_font(font_name)
            for font_name in self.settings_handler.list_fonts()
        }
        self.initialize_session_state()

    def add_tiktok_frame(self, img: Image.Image) -> Image.Image:
        """Add TikTok 9:16 frame around image with black bars.

        Centers the image on a 1080x1920 canvas, scaling if needed
        to fit while maintaining aspect ratio.
        """
        # Create black canvas at TikTok dimensions
        canvas = Image.new("RGBA", (TIKTOK_WIDTH, TIKTOK_HEIGHT), (0, 0, 0, 255))

        # Scale image to fit within canvas while maintaining aspect ratio
        img_w, img_h = img.size
        scale = min(TIKTOK_WIDTH / img_w, TIKTOK_HEIGHT / img_h)

        new_w = int(img_w * scale)
        new_h = int(img_h * scale)

        # Resize image
        resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # Center on canvas
        x = (TIKTOK_WIDTH - new_w) // 2
        y = (TIKTOK_HEIGHT - new_h) // 2

        # Paste (handle RGBA properly)
        if resized.mode == "RGBA":
            canvas.paste(resized, (x, y), resized)
        else:
            canvas.paste(resized, (x, y))

        return canvas

    def create_tiktok_base(self, image_path: str) -> str:
        """Create a TikTok-framed base image for text rendering.

        Opens the image, places it on 1080x1920 canvas, saves to temp file.
        Text will then be rendered on this full-size canvas.
        """
        import tempfile

        img = Image.open(image_path)
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        # Create the framed version
        framed = self.add_tiktok_frame(img)

        # Save to temp file
        temp_path = tempfile.mktemp(suffix=".png")
        framed.save(temp_path)

        return temp_path

    def add_new_slide(self, slide_name: str) -> tuple:
        """Create a new slide with folder, CSV columns, and metadata entries.

        Args:
            slide_name: Name for the new slide (e.g., "slide3")

        Returns:
            tuple: (success: bool, message: str)
        """
        import csv
        import os

        # Validate slide name
        slide_name = slide_name.strip().lower().replace(" ", "_")
        if not slide_name:
            return False, "Slide name cannot be empty"

        if slide_name in self.content_types:
            return False, f"Slide '{slide_name}' already exists"

        if not slide_name.replace("_", "").isalnum():
            return False, "Slide name must be alphanumeric (underscores allowed)"

        try:
            # 1. Create the folder
            slide_folder = self.base_path / slide_name
            slide_folder.mkdir(exist_ok=True)

            # 2. Update metadata.json
            # Add to content_types
            self.metadata_data["content_types"].append(slide_name)

            # Add to products
            self.metadata_data["products"][slide_name] = [{
                "name": "all",
                "prevent_duplicates": False,
                "current_count": 0,
                "min_occurrences": 1
            }]

            # Add to structure
            self.metadata_data["structure"][slide_name] = {
                "path": f"{self.base_path.name}/{slide_name}",
                "images": []
            }

            # Save metadata
            self.metadata.save()

            # 3. Update CSV with new columns
            csv_path = self.base_path / "captions.csv"
            if csv_path.exists():
                # Read existing CSV
                with open(csv_path, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    rows = list(reader)

                if rows:
                    # Add new columns to header
                    header = rows[0]
                    header.extend([f"product_{slide_name}", slide_name])

                    # Add empty values to existing rows
                    for row in rows[1:]:
                        row.extend(["all", ""])  # Default product and empty caption

                    # Write back
                    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerows(rows)

            # Update internal state
            self.content_types.add(slide_name)
            self.products[slide_name] = self.metadata_data["products"][slide_name]

            return True, f"Created slide '{slide_name}' successfully!"

        except Exception as e:
            return False, f"Error creating slide: {str(e)}"

    def delete_slide(self, slide_name: str) -> tuple:
        """Delete a slide and its associated data.

        Args:
            slide_name: Name of the slide to delete

        Returns:
            tuple: (success: bool, message: str)
        """
        import csv
        import shutil

        if slide_name not in self.content_types:
            return False, f"Slide '{slide_name}' does not exist"

        if len(self.content_types) <= 1:
            return False, "Cannot delete the last slide"

        try:
            # 1. Remove folder (move to past_images for safety)
            slide_folder = self.base_path / slide_name
            if slide_folder.exists():
                backup_folder = self.base_path / "past_images" / f"{slide_name}_deleted"
                backup_folder.mkdir(parents=True, exist_ok=True)
                shutil.move(str(slide_folder), str(backup_folder))

            # 2. Update metadata
            self.metadata_data["content_types"].remove(slide_name)
            del self.metadata_data["products"][slide_name]
            del self.metadata_data["structure"][slide_name]

            # Remove images associated with this slide
            images_to_remove = [
                img for img, data in self.metadata_data["images"].items()
                if data.get("content_type") == slide_name
            ]
            for img in images_to_remove:
                del self.metadata_data["images"][img]

            self.metadata.save()

            # 3. Update CSV - remove columns
            csv_path = self.base_path / "captions.csv"
            if csv_path.exists():
                with open(csv_path, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    rows = list(reader)

                if rows:
                    header = rows[0]
                    # Find column indices to remove
                    cols_to_remove = []
                    for i, col in enumerate(header):
                        if col == slide_name or col == f"product_{slide_name}":
                            cols_to_remove.append(i)

                    # Remove columns (in reverse order to preserve indices)
                    for row in rows:
                        for i in sorted(cols_to_remove, reverse=True):
                            if i < len(row):
                                del row[i]

                    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerows(rows)

            # Update internal state
            self.content_types.discard(slide_name)
            if slide_name in self.products:
                del self.products[slide_name]

            return True, f"Deleted slide '{slide_name}' (backed up to past_images)"

        except Exception as e:
            return False, f"Error deleting slide: {str(e)}"

    def initialize_session_state(self):
        """Initialize or reset the session state with required defaults"""
        # Find first non-empty content type and its first image
        first_image = None
        first_content_type = None
        
        # Look through all content types to find the first one with images
        for content_type in self.content_types:
            available_images = self.metadata_data["structure"][content_type]["images"]
            if available_images:
                first_content_type = content_type
                first_image = available_images[0]
                break
        
        # Initialize content type states
        if "settings_content_type" not in st.session_state:
            st.session_state.settings_content_type = first_content_type or next(iter(self.content_types))
            
        if "content_type" not in st.session_state:
            st.session_state.content_type = first_content_type or next(iter(self.content_types))
        
        # Initialize selected image
        if "selected_image" not in st.session_state or not st.session_state.selected_image:
            st.session_state.selected_image = first_image
        
        # Initialize nav index based on selected image
        if "nav_index" not in st.session_state:
            if first_image:
                content_type = st.session_state.content_type
                images = self.metadata_data["structure"][content_type]["images"]
                if st.session_state.selected_image in images:
                    st.session_state.nav_index = images.index(st.session_state.selected_image)
                else:
                    st.session_state.nav_index = 0
            else:
                st.session_state.nav_index = 0

        # Initialize product related states
        # This eliminates the duplicate initialization warning
        if "product" not in st.session_state:
            if st.session_state.selected_image:
                st.session_state.product = self.metadata_data["images"][st.session_state.selected_image].get("product")
            else:
                st.session_state.product = None
                
        # Initialize other required states
        if "selected_caption_idx" not in st.session_state:
            st.session_state.selected_caption_idx = 0
                
        if "top_bar_message" not in st.session_state:
            st.session_state.top_bar_message = ""
                
        if "top_bar_message_type" not in st.session_state:
            st.session_state.top_bar_message_type = "info"
            
        # Debug logging
        logger.debug(f"Initialized session state:")
        logger.debug(f"Content type: {st.session_state.content_type}")
        logger.debug(f"Selected image: {st.session_state.selected_image}")
        logger.debug(f"Nav index: {st.session_state.nav_index}")

    def render_type_selection(self):
        """Render content type and product selection with proper product filtering"""
        col1, col2 = st.columns(2)

        with col1:
            # Content type selection remains the same
            st.selectbox(
                label="Content Type Selection",
                options=self.content_types,
                key="settings_content_type",
                on_change=self.handle_content_type_change,
                label_visibility="visible",
            )

        with col2:
            # Get current image and its product
            current_image = st.session_state.get("selected_image")
            current_product = None
            if current_image:
                current_product = self.metadata_data["images"][current_image].get("product")

            # Get content type for product list
            content_type = st.session_state.settings_content_type
            
            # Get valid products for this content type from metadata
            valid_products = [
                p["name"] 
                for p in self.metadata_data["products"][content_type]
            ] if content_type in self.metadata_data["products"] else []
            
            # Create product list with "None" option
            product_list = ["None"] + valid_products
            
            # Find proper index for current product
            default_index = (
                product_list.index(current_product)
                if current_product in product_list
                else 0  # Default to "None" if current product not valid
            )
            
            def on_product_change():
                """Handle product selection change"""
                if not current_image:
                    return

                old_product = current_product
                new_product = st.session_state.settings_product
                
                # Handle "None" selection
                if new_product == "None":
                    new_product = None

                # Don't process if no change
                if old_product == new_product:
                    return

                # Validate the change
                is_valid, error_msg = self._validate_product_assignment(
                    content_type, new_product
                )
                if not is_valid:
                    st.error(error_msg)
                    # Reset to old value
                    st.session_state.settings_product = "None" if old_product is None else old_product
                    return

                # Handle the product assignment
                self._handle_product_assignment(old_product, new_product, content_type)

            # Product selection dropdown
            st.selectbox(
                label="Product Selection",
                options=product_list,
                index=default_index,
                key="settings_product",
                on_change=on_product_change,
                label_visibility="visible"
            )

    def render_base_settings(self, settings_data):
        """Render base settings controls"""
        current_settings = self.get_current_settings()
        if not current_settings:
            st.error("Could not retrieve current settings")
            return
            
        # Get base settings from the proper location
        base_settings = current_settings.get("base_settings", {})
        current_text_type = base_settings.get("default_text_type")
        logger.debug(f"{current_text_type=}")
        logger.debug(f"{base_settings=}")
        
        if not current_text_type:
            st.error("No text type found in current settings")
            return

        # Create expander label with current text type
        expander_label = f"Base Settings (Default: {current_text_type.title()})"

        with st.expander(expander_label, expanded=False):
            # Existing text type selection
            valid_types = list(VALID_TEXT_TYPES)
            index = (
                valid_types.index(current_text_type)
                if current_text_type in valid_types
                else 0
            )

            selected_type = st.selectbox(
                "Default Text Type",
                options=valid_types,
                index=index,
                label_visibility="visible",
            )

            if selected_type != current_text_type and st.button(
                "Update Text Type", use_container_width=True
            ):
                self.handle_text_type_change(selected_type)
                st.rerun()

            st.divider()
            # product level dupe changer. 
            self._product_level_duplicate_prevention_changer_base_settings()
            
            # Settings level selector
            st.divider()
            self._render_settings_level_selector()

    def render_text_settings(self, settings_data):
        """Render text type settings controls"""
        logger.trace("\n=== Text Settings Debug ===")
        logger.trace(f"Input settings_data: {settings_data}")

        with st.expander("Text Type Settings", expanded=True):
            if not settings_data:
                logger.trace("DEBUG: No settings data provided")
                st.error("No settings data available")
                return

            # Get current image and metadata
            current_image = st.session_state.get("selected_image")
            if not current_image:
                st.error("No image selected")
                return

            image_data = self.metadata_data["images"].get(current_image)
            if not image_data:
                st.error(f"No metadata found for image: {current_image}")
                return

            # Get settings source from image data
            settings_source = image_data.get("settings_source", "default")
            content_type = image_data.get("content_type")
            product = image_data.get("product")

            logger.debug(f"Settings resolution - Source: {settings_source}, Content: {content_type}, Product: {product}")

            # Get settings based on source priority (custom > product > content > default)
            # Be resilient if settings_source says 'custom' but settings are None
            if settings_source == "custom" and image_data.get("settings"):
                current_settings = {"settings": image_data["settings"]}
            elif settings_source == "product" and product:
                current_settings = self.metadata_editor.get_settings("product", product, content_type)
            elif settings_source == "content":
                current_settings = self.metadata_editor.get_settings("content_type", content_type)
            else:
                # Default is the fallback
                current_settings = self.metadata_editor.get_settings("default")

            # Fallback to passed data if retrieval fails
            if not current_settings or not current_settings.get("settings"):
                logger.warning("Falling back to passed settings_data in render_text_settings")
                current_settings = {"settings": settings_data}

            if not current_settings:
                st.error("No valid settings found")
                return

            settings = current_settings.get("settings", {})
            current_type = settings.get("base_settings", {}).get("default_text_type")
            
            if not current_type:
                logger.trace("DEBUG: No default text type found")
                st.error("No default text type set")
                return

            logger.debug(f"{settings_source=}")
            logger.debug(f"{current_settings=}")

            text_settings = settings.get("text_settings", {}).get(current_type, {})
            if not text_settings:
                logger.trace(f"DEBUG: No settings found for type {current_type}")
                st.error(f"No settings found for text type: {current_type}")
                return

            # Font Settings & Style Value Settings
            self._font_input(current_type, text_settings)

            # Position Settings
            position = text_settings["position"]
            self._render_position_settings(position, current_type)

            # Margins
            margins = text_settings["margins"]
            self._render_margin_settings(margins, current_type)

    def _render_color_pair(
        self, text_type: str, idx: int, color_keys: List[str], color_pair: Dict
    ) -> bool:
        """Render a single color pair with delete button in a horizontal layout"""
        # Create columns with better proportions for tighter layout
        cols = st.columns([1.5, 1.5, 0.8])  # Text color, Background color, Delete

        deleted = False

        # Render color pickers
        for i, key in enumerate(color_keys):
            with cols[i]:
                st.write(f"{key.title()} {idx + 1}")  # Add number to label
                # Ensure hex color is uppercase
                color_pair[key] = st.color_picker(
                    label=f"{key} {idx + 1}",
                    value=color_pair[key],
                    label_visibility="collapsed",
                    key=f"color_{text_type}_{idx}_{key}",
                ).upper()  # Convert hex to uppercase

        # Delete button with label
        with cols[2]:
            st.write(f"Delete {idx + 1}")  # Add number to delete label
            if st.button("🗑️", key=f"delete_color_{text_type}_{idx}"):
                logger.trace(f"\n=== Deleting Color Pair {idx + 1} ===")
                logger.trace(f"Removing: {color_pair}")
                deleted = True

        return deleted

    def render_color_settings(self, text_type: str):
        """Render and manage complete color settings UI for a text type"""
        # Create notification container at top

        logger.trace("\n=== Color Settings Debug ===")
        logger.trace(f"Text type: {text_type}")

        # Get current image and its settings level
        current_image = st.session_state.get("selected_image")
        image_data = self.metadata_data["images"][current_image]
        settings_source = image_data["settings_source"]
        content_type = image_data["content_type"]
        product = image_data.get("product")

        logger.trace(f"Current image: {current_image}")
        logger.trace(f"Settings source: {settings_source}")
        logger.trace(f"Content type: {content_type}")
        logger.trace(f"Product: {product}")

        # Get settings based on source level
        if settings_source == "custom":
            settings_data = self.metadata_editor.get_settings("custom", current_image)
        elif settings_source == "product" and product:
            settings_data = self.metadata_editor.get_settings(
                "product", product, content_type
            )
        elif settings_source == "content_type":
            settings_data = self.metadata_editor.get_settings(
                "content_type", content_type
            )
        else:
            settings_data = self.metadata_editor.get_settings("default")

        logger.trace(f"Settings data retrieved: {settings_data}")

        settings = settings_data.get("settings", {})
        if not settings:
            st.warning("No settings available")
            return

        text_settings = settings.get("text_settings", {})
        logger.trace(f"Text settings found: {text_settings}")

        # Rest of the function stays the same
        current_type_settings = text_settings.get(text_type, {})
        logger.trace(f"Current type settings: {current_type_settings}")

        colors = current_type_settings.get("colors", [])
        logger.trace(f"Colors found: {colors}")

        with st.expander("Color Settings", expanded=False):
            # Display existing color pairs
            to_delete = None
            for idx, color_pair in enumerate(colors):
                if self._render_color_pair(
                    text_type, idx, color_pair.keys(), color_pair
                ):
                    to_delete = idx

            if to_delete is not None:
                colors.pop(to_delete)
                self._save_color_settings(settings)
                st.rerun()

            # Action buttons in horizontal layout
            cols = st.columns([1, 1])  # Split bottom buttons into two columns
            with cols[0]:
                if st.button("Add Color Pair", key=f"add_color_{text_type}"):
                    if colors:
                        new_pair = {k: "#FFFFFF" for k in colors[0].keys()}
                        colors.append(new_pair)
                        logger.trace(f"\n=== Adding New Color Pair ===")
                        logger.trace(f"New pair: {new_pair}")
                        self._save_color_settings(settings)
                        st.rerun()

            with cols[1]:
                if st.button("Save Colors", key=f"save_colors_{text_type}"):
                    if self._save_color_settings(settings):
                        st.session_state.show_success = True
                        st.rerun()

        # Show success message if flag is set, then clear it
        if st.session_state.pop("show_success", False):
            st.success("Settings saved successfully")

    def _get_color_keys_for_type(self, text_type: str) -> list:
        """Get the required color keys based on text type from current settings"""
        settings_data = self.get_current_settings()
        if not settings_data:
            return []

        # Navigate to the correct settings level
        settings = settings_data.get("settings", {}).get("settings", {})
        text_settings = settings.get("text_settings", {}).get(text_type, {})

        # Get colors from current settings
        colors = text_settings.get("colors", [])
        if colors:
            # Get keys from first color entry
            return list(colors[0].keys())

        logger.trace(f"Warning: No existing color keys found for {text_type}")
        return []

    def _save_color_settings(self, settings_data: dict):
        """Save updated color settings to metadata"""
        try:
            current_image = st.session_state.selected_image
            if not current_image:
                st.error("No image selected")
                return False

            # Update metadata directly
            self.metadata_data["images"][current_image]["settings_source"] = "custom"
            self.metadata_data["images"][current_image]["settings"] = settings_data

            # Save metadata to disk
            self.metadata.save()
            st.success("Color settings saved successfully")
            return True

        except Exception as e:
            st.error(f"Failed to save color settings: {str(e)}")
            return False

    def render(self):
        """Render the settings interface with proper error handling"""

        with st.container():
            # Get current image with safety check
            current_image = st.session_state.get("selected_image")
            if not current_image:
                st.warning("Please select an image to edit settings")
                return

            try:
                # Get current settings and image data with safety checks
                current_settings = self.get_current_settings()
                
                # Safely get image data
                image_data = self.metadata_data["images"].get(current_image)
                if not image_data:
                    st.error(f"No metadata found for image: {current_image}")
                    return

                settings_source = image_data.get("settings_source", "default")
                logger.debug(f"RENDER DEBUG - Current image: {current_image}")
                logger.debug(f"RENDER DEBUG - Settings source: {settings_source}")
                logger.debug(f"RENDER DEBUG - Image data: {image_data}")
                logger.debug(f"RENDER DEBUG - Current settings: {current_settings}")

                if current_settings:
                    settings_data = current_settings  # The settings are already at the right level

                    self.render_type_selection()
                    self.render_base_settings(settings_data)
                    self.render_text_settings(settings_data)

                    # Get text type safely with proper fallback
                    text_type = settings_data.get("base_settings", {}).get(
                        "default_text_type", "plain"
                    )
                    if not text_type:
                        st.warning("No default text type set")
                        return

                    self.render_color_settings(text_type)
                    self.render_preview_expander(settings_data)

                    # Apply to all images in folder button
                    st.markdown("---")
                    st.markdown("### 📋 Bulk Apply Settings")
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write("Apply these settings to all images in this folder")
                    with col2:
                        if st.button("🔄 Apply to All", type="primary", key="apply_to_all_btn"):
                            self.apply_settings_to_all_in_folder()

                    # Slide Management Section
                    st.markdown("---")
                    with st.expander("📁 Slide Management", expanded=False):
                        st.markdown("**Current Slides:**")
                        for slide in sorted(self.content_types):
                            st.write(f"• {slide}")

                        st.markdown("---")
                        st.markdown("**➕ Add New Slide**")
                        new_slide_name = st.text_input(
                            "Slide Name",
                            placeholder="e.g., slide3",
                            key="new_slide_name_input"
                        )
                        if st.button("Create Slide", type="primary", key="create_slide_btn"):
                            if new_slide_name:
                                success, message = self.add_new_slide(new_slide_name)
                                if success:
                                    st.success(message)
                                    st.info("Refresh the page to see the new slide")
                                    st.rerun()
                                else:
                                    st.error(message)
                            else:
                                st.warning("Please enter a slide name")

                        st.markdown("---")
                        st.markdown("**🗑️ Delete Slide**")
                        if len(self.content_types) > 1:
                            slide_to_delete = st.selectbox(
                                "Select slide to delete",
                                options=sorted(self.content_types),
                                key="delete_slide_select"
                            )
                            st.warning(f"⚠️ This will move '{slide_to_delete}' folder to past_images")
                            if st.button("Delete Slide", type="secondary", key="delete_slide_btn"):
                                success, message = self.delete_slide(slide_to_delete)
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                        else:
                            st.info("Cannot delete - need at least one slide")

                    # Debug view of settings
                    with st.expander("Debug Settings View"):
                        st.json(settings_data)
                else:
                    st.warning("No settings available for the selected image")

            except Exception as e:
                logger.error(f"Error in render method: {str(e)}")
                st.error("An error occurred while rendering settings")

    def apply_settings_to_all_in_folder(self):
        """Apply current image's settings to all images in the same folder"""
        try:
            current_image = st.session_state.get("selected_image")
            if not current_image:
                st.error("No image selected")
                return

            # Get current image data and settings
            current_image_data = self.metadata_data["images"][current_image]
            content_type = current_image_data["content_type"]
            current_settings = current_image_data.get("settings")

            if not current_settings:
                st.error("Current image has no custom settings to apply")
                return

            # Get all images in the same folder
            all_images_in_folder = self.metadata_data["structure"][content_type]["images"]

            # Confirm with user
            with st.spinner(f"Applying settings to {len(all_images_in_folder)} images in {content_type}/..."):
                applied_count = 0

                for image_name in all_images_in_folder:
                    try:
                        # Apply the current settings to this image
                        self.metadata_editor.edit_image(
                            image_name=image_name,
                            data={
                                "settings_source": "custom",
                                "settings": current_settings.copy()
                            }
                        )

                        # Update local metadata
                        self.metadata_data["images"][image_name]["settings_source"] = "custom"
                        self.metadata_data["images"][image_name]["settings"] = current_settings.copy()

                        applied_count += 1

                    except Exception as e:
                        logger.error(f"Failed to apply settings to {image_name}: {str(e)}")
                        continue

                # Save metadata
                self.metadata.save()

                st.success(f"✅ Applied settings to {applied_count} images in {content_type}/ folder!")
                st.balloons()

        except Exception as e:
            logger.error(f"Error applying settings to all: {str(e)}")
            st.error(f"Failed to apply settings: {str(e)}")

    def get_current_settings(self):
        """Get settings and product info for current image based on settings level hierarchy"""
        if not self.metadata_editor:
            logger.error("ERROR: metadata_editor is None!")
            return None

        current_image = st.session_state.get("selected_image")
        if not current_image:
            logger.debug("No image selected")
            return None

        try:
            # Safely get image data with detailed logging
            image_data = self.metadata_data["images"].get(current_image)
            if not image_data:
                logger.error(f"No metadata found for image: {current_image}")
                return None

            settings_source = image_data.get("settings_source", "default")
            logger.debug(f"SETTINGS DEBUG - Image: {current_image}")
            logger.debug(f"SETTINGS DEBUG - Raw image data: {image_data}")
            logger.debug(f"SETTINGS DEBUG - Settings source: {settings_source}")

            # If settings_source is content, get content type settings
            if settings_source == "content":
                content_type = image_data.get("content_type")
                logger.debug(f"SETTINGS DEBUG - Getting content type settings for: {content_type}")
                content_settings = self.metadata_editor.get_settings("content_type", content_type)
                logger.debug(f"SETTINGS DEBUG - Content settings retrieved: {content_settings}")
                if content_settings:
                    return content_settings.get("settings")
                logger.error(f"No content type settings found for {content_type}")

            # If image has no settings, or settings_source is default, fall back
            if image_data.get("settings") is None or settings_source == "default":
                logger.debug("SETTINGS DEBUG - Getting default settings")
                default_result = self.metadata_editor.get_settings("default")
                logger.debug(f"SETTINGS DEBUG - Default settings result: {default_result}")
                
                if not default_result:
                    logger.error("Failed to get default settings")
                    return None
                    
                settings = default_result.get("settings")
                logger.debug(f"SETTINGS DEBUG - Extracted settings from default: {settings}")
                return settings

            # For all other cases, return the stored settings
            logger.debug(f"SETTINGS DEBUG - Returning stored settings: {image_data.get('settings')}")
            
            return image_data.get("settings")

        except Exception as e:
            print(f"CRITICAL ERROR in get_current_settings: {str(e)}")
            import traceback
            traceback.print_exc()
            logger.error(f"Error getting settings: {str(e)}")
            
            # Fallback to hardcoded default to keep app alive
            logger.warning("Using hardcoded fallback settings")
            return {
                "base_settings": {"default_text_type": "plain"},
                "text_settings": {
                    "plain": {
                        "font_size": 70,
                        "font": "assets.fonts.tiktokfont.ttf",
                        "style_type": "outline_width",
                        "style_value": 4,
                        "colors": [{"text": "#FFFFFF", "outline": "#000000"}],
                        "position": {"vertical": [0.45, 0.55], "horizontal": [0.45, 0.55], "vertical_jitter": 0.01, "horizontal_jitter": 0.02},
                        "margins": {"top": 0.05, "bottom": 0.05, "left": 0.1, "right": 0.1}
                    },
                    "highlight": {
                        "font_size": 70,
                        "font": "assets.fonts.tiktokfont.ttf",
                        "style_type": "corner_radius",
                        "style_value": 20,
                        "colors": [{"text": "#000000", "background": "#FFFFFF"}],
                        "position": {"vertical": [0.45, 0.55], "horizontal": [0.45, 0.55], "vertical_jitter": 0.01, "horizontal_jitter": 0.02},
                        "margins": {"top": 0.05, "bottom": 0.05, "left": 0.05, "right": 0.05}
                    }
                }
            }

    def handle_text_type_change(self, new_text_type: str):
        """Handle changing text type in settings"""
        logger.debug("\n=== Text Type Change Debug ===")
        logger.debug(f"1. Starting text type change to: {new_text_type}")

        current_image = st.session_state.selected_image
        if not current_image:
            logger.error("No image selected")
            return

        # Get current settings
        image_data = self.metadata_data["images"][current_image]
        settings_source = image_data["settings_source"]
        logger.debug(f"2. Current settings source: {settings_source}")

        # Get the settings we're currently using
        if settings_source == "content":
            content_type = image_data["content_type"]
            current_settings = self.metadata_data["settings"][content_type]["content"]
            logger.debug(f"3a. Using content settings for {content_type}")
        elif settings_source == "product":
            product = image_data["product"]
            content_type = image_data["content_type"]
            for group, settings in self.metadata_data["settings"][content_type].items():
                if group != "content":
                    products = {p.strip() for p in group[1:-1].split(",")}
                    if product in products:
                        current_settings = settings
                        break
            logger.debug(f"3b. Using product settings for {product}")
        else:
            current_settings = image_data.get("settings")
            logger.info("3c. Using custom/default settings")

        logger.debug(f"4. Current settings: {current_settings}")

        # Create a copy of current settings
        settings_data = current_settings.copy() if current_settings else {}
        logger.debug("5. Created settings copy")
        
        # Update settings with new text type
        if new_text_type not in settings_data.get("text_settings", {}):
            logger.debug(f"6. Adding new text type {new_text_type} settings")
            # Get default settings for new type
            default_settings = self.metadata_editor.get_settings(level="default")["settings"]
            default_type_settings = default_settings["text_settings"][new_text_type]
            settings_data.setdefault("text_settings", {})[new_text_type] = default_type_settings.copy()

        # Update default text type
        settings_data.setdefault("base_settings", {})["default_text_type"] = new_text_type
        logger.debug(f"7. Updated default text type to {new_text_type}")

        # Always switch to custom settings when making changes
        try:
            logger.debug("8. Applying changes...")
            self.metadata_editor.edit_image(
                image_name=current_image,
                data={"settings_source": "custom", "settings": settings_data},
            )
            logger.debug("9. Saved changes via metadata_editor")
            
            # Update local metadata_data
            self.metadata_data["images"][current_image]["settings_source"] = "custom"
            self.metadata_data["images"][current_image]["settings"] = settings_data
            logger.debug("10. Updated local metadata copy")

            self.metadata.save()
            logger.debug("11. Saved metadata to disk")

        except Exception as e:
            logger.error(f"ERROR during save: {str(e)}")
            st.error("Failed to save settings changes")
            return

        logger.debug("=== Text Type Change Complete ===\n")

    def add_color_picker(self, text_type: str, color_index: int):
        """Add color picker UI elements for a text type"""
        settings_data = self.get_current_settings()
        if not settings_data:
            return

        colors = settings_data["text_settings"][text_type]["colors"]
        if color_index >= len(colors):
            colors.append({})  # Add new color slot

        required_keys = VALID_TEXT_TYPES[text_type]["required_color_keys"]
        col1, col2 = st.columns(2)

        for key in required_keys:
            with col1:
                st.write(f"Color {color_index + 1} - {key}")
            with col2:
                colors[color_index][key] = st.color_picker(
                    f"Pick {key} color ###{color_index}",
                    value=colors[color_index].get(key, "#FFFFFF"),
                    key=f"color_{text_type}_{key}_{color_index}",
                )

    def _font_input(self, text_type: str, text_settings: Dict) -> None:
        """Render font selection dropdown and font size input in one row"""
        # Create columns with 3:2:2 ratio for font, size, and style
        cols = st.columns([4, 2, 2])

        # Get current font name from path
        current_font_name = text_settings["font"].split(".")[-2]
        settings_data = self.get_current_settings()

        # Font dropdown
        with cols[0]:
            selected_font = st.selectbox(
                "Font",
                options=list(self.fonts.keys()),
                index=list(self.fonts.keys()).index(current_font_name),
                key=f"font_select_{text_type}",
            )

            # Apply font change if needed
            if selected_font != current_font_name:
                logger.trace(f"\n=== Font Change ===")
                logger.trace(f"Old font: {text_settings['font']}")
                new_font = self.fonts[selected_font]
                logger.trace(f"New font: {new_font}")

                # Update settings with new font
                settings_data["text_settings"][text_type]["font"] = new_font

                # Apply changes via metadata editor
                image_name = st.session_state.get("selected_image")
                self.metadata_editor.edit_image(
                    image_name, {"settings": settings_data, "settings_source": "custom"}
                )
                self.metadata.save()
                st.rerun()

        # Font size input (keeping the same structure for consistency)
        with cols[1]:
            font_size = st.number_input(
                "Font Size",
                min_value=1.0,
                max_value=500.0,
                value=float(text_settings["font_size"]),
                step=0.5,
                format="%.1f",
                key=f"font_size_{text_type}",
            )

            if font_size != float(text_settings["font_size"]):
                logger.trace(f"\n=== Font Size Change ===")
                logger.trace(f"Old size: {text_settings['font_size']}")
                logger.trace(f"New size: {font_size}")

                # Update settings with new font size
                settings_data["text_settings"][text_type]["font_size"] = font_size
                image_name = st.session_state.get("selected_image")
                self.metadata_editor.edit_image(
                    image_name, {"settings": settings_data, "settings_source": "custom"}
                )
                self.metadata.save()
                st.rerun()

        # Style value input
        with cols[2]:
            style_type = text_settings["style_type"]
            style_value = text_settings["style_value"]
            style_label = style_type.replace("_", " ").title()

            new_style_value = st.number_input(
                style_label,
                min_value=0.0,
                max_value=100.0,
                value=float(style_value),
                step=0.5,
                format="%.1f",
                key=f"style_value_{text_type}",
            )

            if new_style_value != float(style_value):
                logger.trace(f"\n=== Style Value Change ===")
                logger.trace(f"Old value: {style_value}")
                logger.trace(f"New value: {new_style_value}")

                settings_data["text_settings"][text_type][
                    "style_value"
                ] = new_style_value
                image_name = st.session_state.get("selected_image")
                self.metadata_editor.edit_image(
                    image_name, {"settings": settings_data, "settings_source": "custom"}
                )
                self.metadata.save()
                st.rerun()

    def _render_position_settings(self, position: dict, current_type: str):
        """Render position settings UI and handle updates"""

        def update_position_setting(setting_name: str, new_value, old_value):
            """Helper function to update position settings"""
            
            if new_value != old_value:
                try:
                    logger.debug(f"\n=== Position Change Debug ===")
                    logger.debug(f"Old {setting_name}: {old_value}")
                    logger.debug(
                        f"New {setting_name}: {list(new_value) if isinstance(new_value, tuple) else new_value}"
                    )

                    settings_data = self.get_current_settings()
                    # logger.critical(f"update position setting {settings_data=}")  # TODO 
                    new_settings = settings_data.copy()
                    new_settings["text_settings"][current_type]["position"][
                        setting_name
                    ] = (list(new_value) if isinstance(new_value, tuple) else new_value)

                    self.settings_handler.settings_validator.validate_settings(new_settings)

                    settings_data = new_settings

                    image_name = st.session_state.get("selected_image")
                    logger.testing(f"Updating image: {image_name}")
                    logger.testing(f"New settings data: {settings_data}")

                    self.metadata_editor.edit_image(
                        image_name, {"settings": settings_data, "settings_source": "custom"}
                    )
                    st.session_state.top_bar_message = "changed settings !"
                    st.session_state.top_bar_message_type = "success"
                    self.metadata.save()
                    st.rerun()
                    
                except ValueError as e:
                    # Show error in top bar and don't update settings
                    st.session_state.top_bar_message = str(e)
                    st.session_state.top_bar_message_type = "error"
                    st.rerun()

        # Position and jitter controls in rows
        # Vertical controls
        vcol1, vcol2 = st.columns([0.7, 0.3])
        with vcol1:
            vertical_pos = st.slider(
                "Vertical Position",
                min_value=0.0,
                max_value=1.0,
                value=tuple(position["vertical"]),
                label_visibility="visible",
                key=f"vertical_pos_{current_type}",
            )
            update_position_setting("vertical", vertical_pos, tuple(position["vertical"]))
            
        with vcol2:
            vertical_jitter = st.number_input(
                "V Jitter",
                min_value=0.0,
                max_value=0.1,
                value=position["vertical_jitter"],
                label_visibility="visible",
                key=f"vertical_jitter_{current_type}",
            )
            update_position_setting(
                "vertical_jitter", vertical_jitter, position["vertical_jitter"]
            )

        # Horizontal controls
        hcol1, hcol2 = st.columns([0.7, 0.3])
        with hcol1:
            horizontal_pos = st.slider(
                "Horizontal Position",
                min_value=0.0,
                max_value=1.0,
                value=tuple(position["horizontal"]),
                label_visibility="visible",
                key=f"horizontal_pos_{current_type}",
            )
            update_position_setting(
                "horizontal", horizontal_pos, tuple(position["horizontal"])
            )
            
        with hcol2:
            horizontal_jitter = st.number_input(
                "H Jitter",
                min_value=0.0,
                max_value=0.1,
                value=position["horizontal_jitter"],
                label_visibility="visible",
                key=f"horizontal_jitter_{current_type}",
            )
            update_position_setting(
                "horizontal_jitter", horizontal_jitter, position["horizontal_jitter"]
            )

    def _render_margin_settings(self, margins: dict, current_type: str):
        """Render margin settings UI"""

        def update_margin_setting(setting_name: str, new_value_int, old_value):
            """Helper function to update margin settings"""
            # Convert integer input to float (divide by 100)
            new_value = new_value_int / 100.0
            old_value_int = int(old_value * 100)

            if new_value_int != old_value_int:
                logger.trace(f"\n=== Margin Change Debug ===")
                logger.trace(f"Old {setting_name}: {old_value} (from {old_value_int})")
                logger.trace(f"New {setting_name}: {new_value} (from {new_value_int})")

                settings_data = self.get_current_settings()
                settings_data["text_settings"][current_type]["margins"][
                    setting_name
                ] = new_value

                image_name = st.session_state.get("selected_image")
                logger.trace(f"Updating image: {image_name}")
                logger.trace(f"New settings data: {settings_data}")

                self.metadata_editor.edit_image(
                    image_name, {"settings": settings_data, "settings_source": "custom"}
                )
                self.metadata.save()
                st.rerun()

        # Create 4 equal columns
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            top_margin = st.number_input(
                "Top %",
                min_value=0,
                max_value=50,
                value=int(margins["top"] * 100),
                label_visibility="visible",
                key=f"margin_top_{current_type}",
            )
            update_margin_setting("top", top_margin, margins["top"])

        with col2:
            bottom_margin = st.number_input(
                "Bottom %",
                min_value=0,
                max_value=50,
                value=int(margins["bottom"] * 100),
                label_visibility="visible",
                key=f"margin_bottom_{current_type}",
            )
            update_margin_setting("bottom", bottom_margin, margins["bottom"])

        with col3:
            left_margin = st.number_input(
                "Left %",
                min_value=0,
                max_value=50,
                value=int(margins["left"] * 100),
                label_visibility="visible",
                key=f"margin_left_{current_type}",
            )
            update_margin_setting("left", left_margin, margins["left"])

        with col4:
            right_margin = st.number_input(
                "Right %",
                min_value=0,
                max_value=50,
                value=int(margins["right"] * 100),
                label_visibility="visible",
                key=f"margin_right_{current_type}",
            )
            update_margin_setting("right", right_margin, margins["right"])

    def _render_settings_level_selector(self):
        """Render UI for changing settings level"""
        # Get current settings info
        current_image = st.session_state.get("selected_image")
        if not current_image:
            return

        # Get current image metadata using our existing method
        settings_data = self.get_current_settings()
        if not settings_data:
            return

        # Get image info from settings data
        current_level = settings_data.get("settings_source", "default")
        content_type = settings_data.get("content_type")
        product = settings_data.get("product")

        # Get settings following the metadata structure:
        # settings -> content_type -> "content" -> actual settings
        content_type_settings = (
            self.metadata_editor.metadata.get("settings", {})  # settings dict
            .get(content_type, {})  # content type level
            .get("content")
        )  # actual settings

        levels_status = {
            "default": {"available": True, "reason": None},
            "content": {
                "available": bool(content_type and content_type_settings),
                "reason": (
                    "No content type settings exist"
                    if content_type
                    else "Image has no content type defined"
                ),
            },
            "product": {
                "available": bool(
                    product
                    and content_type
                    and self.metadata_editor.get_settings(
                        "product", product, content_type
                    )
                ),
                "reason": (
                    "No product settings exist"
                    if product
                    else "Image has no product defined"
                ),
            },
        }

        # Get current image metadata
        current_image = st.session_state.get("selected_image")
        image_data = self.metadata_editor.metadata["images"][current_image]
        image_content_type = image_data.get("content_type")
        image_product = image_data.get("product")

        # Debug both content type and product settings
        settings = self.metadata_editor.metadata.get("settings", {})
        logger.trace("\n=== Settings Structure Debug === {settings level selector}")
        logger.trace(f"{image_data=}")
        logger.trace(f"Image content type: {image_content_type}")
        logger.trace(f"Image product: {image_product}")

        # Get content type settings
        content_type_settings = settings.get(image_content_type, {})
        content_settings = content_type_settings.get("content", {})

        # Get product settings if product exists
        product_settings = None
        if image_product:
            product_key = f"[{image_product}]"
            product_settings = content_type_settings.get(product_key, {})

        logger.trace(f"Content type settings: {content_type_settings}")
        logger.trace(f"Content settings: {content_settings}")
        logger.trace(f"Product settings: {product_settings}")

        # Update levels status with proper checks
        levels_status = {
            "default": {"available": True, "reason": None},
            "content": {
                "available": bool(image_content_type and content_settings),
                "reason": (
                    "No content settings exist"
                    if image_content_type
                    else "Image has no content type defined"
                ),
            },
            "product": {
                "available": bool(image_product and product_settings),
                "reason": (
                    "No product settings exist"
                    if image_product
                    else "Image has no product defined"
                ),
            },
        }

        st.write("Change Settings Level")

        # Simplify the options creation
        options = ["default"]  # Always include default first
        if current_level != "content":
            options.append(
                f"content ({levels_status['content']['reason']})"
                if not levels_status["content"]["available"]
                else "content"
            )
        if current_level != "product":
            options.append(
                f"product ({levels_status['product']['reason']})"
                if not levels_status["product"]["available"]
                else "product"
            )

        target_level = st.selectbox(
            "Switch to:",
            options=options,
            index=None,  # No default selection
            label_visibility="collapsed",
        )

        # Only show button if a level is selected
        if target_level:
            # Extract the actual level from the label if it has a reason
            selected_level = target_level.split(" (")[0]

            if st.button(
                f"Confirm switch to {selected_level} settings",
                disabled=not levels_status[selected_level]["available"],
            ):
                current_image = st.session_state.get("selected_image")
                image_data = self.metadata_data["images"][current_image]
                content_type = image_data.get("content_type")
                product = image_data.get("product")
                
                # Get the settings for the new level BEFORE switching
                new_settings = None
                if selected_level == "default":
                    new_settings = self.metadata_editor.get_settings("default")
                elif selected_level == "content":
                    new_settings = self.metadata_editor.get_settings("content_type", content_type)
                elif selected_level == "product":
                    new_settings = self.metadata_editor.get_settings("product", product, content_type)
                
                # Only proceed if we got valid settings
                if new_settings and "settings" in new_settings:
                    self.metadata_editor.edit_image(
                        current_image, 
                        {
                            "settings": new_settings["settings"],
                            "settings_source": selected_level
                        }
                    )
                    self.metadata.save()
                    st.rerun()
                else:
                    st.error(f"Could not load settings for {selected_level} level")

    def _move_image_between_content_types(
        self, image_name: str, new_content_type: str
    ) -> None:
        """Move image file between content type folders and update metadata.

        Args:
            image_name: Name of image to move
            new_content_type: Destination content type folder
        """
        logger.trace("\n=== Moving Image Between Content Types ===")

        # Get current image data
        image_data = self.metadata_data["images"][image_name]
        old_content_type = image_data["content_type"]

        # Get paths
        old_path = self.base_path / old_content_type / image_name
        new_path = self.base_path / new_content_type / image_name

        logger.trace(
            f"Moving {image_name} from {old_content_type} to {new_content_type}"
        )
        logger.trace(f"Old path: {old_path}")
        logger.trace(f"New path: {new_path}")

        try:
            # Physically move the file
            old_path.rename(new_path)

            # Update metadata structure
            # Remove from old content type
            old_images = self.metadata_data["structure"][old_content_type]["images"]
            self.metadata_data["structure"][old_content_type]["images"] = [
                img for img in old_images if img != image_name
            ]

            # Add to new content type
            self.metadata_data["structure"][new_content_type]["images"].append(
                image_name
            )
            self.metadata_data["structure"][new_content_type]["images"].sort()

            # Update image metadata
            self.metadata_editor.edit_image(
                image_name=image_name,
                data={
                    "content_type": new_content_type,
                    "product": None,  # Reset product when changing content type
                    "settings_source": "default",  # Reset to default settings
                },
            )

            # Save metadata
            self.metadata.save()

            logger.trace("File moved and metadata updated successfully")

        except Exception as e:
            logger.error(f"Failed to move image: {str(e)}")
            st.error(f"Failed to move image: {str(e)}")
            raise

    def handle_content_type_change(self):
        """Enhanced content type change handler with improved state management"""
        current_image = st.session_state.selected_image
        new_content_type = st.session_state.settings_content_type
        
        if not current_image:
            return
        
        try:
            # Get current image data with validation
            image_data = self.metadata_data["images"][current_image]
            if not image_data:
                raise ValueError(f"No metadata found for image: {current_image}")
                
            old_content_type = image_data["content_type"]
            old_product = image_data.get("product")
            
            if old_content_type == new_content_type:
                return
            
            # Handle product count updates
            if old_product:
                logger.debug(f"Updating product count for {old_product}")
                # Decrement old product count
                self.metadata_editor._update_product_count(
                    old_content_type, old_product, increment=False
                )
            
            # Physical file move
            old_path = self.base_path / old_content_type / current_image
            new_path = self.base_path / new_content_type / current_image
            
            if not old_path.exists():
                raise FileNotFoundError(f"Source file not found: {old_path}")
                
            old_path.rename(new_path)
            
            # Update metadata structure
            old_images = self.metadata_data["structure"][old_content_type]["images"]
            new_images = self.metadata_data["structure"][new_content_type]["images"]
            
            if current_image in old_images:
                old_images.remove(current_image)
            if current_image not in new_images:
                new_images.append(current_image)
                new_images.sort()
                
            # Update image metadata
            self.metadata_data["images"][current_image].update({
                "content_type": new_content_type,
                "product": None,  # Reset product
                "settings_source": "default",
                "settings": None
            })
            
            # Update session state
            st.session_state.content_type = new_content_type
            st.session_state.settings_product = None
            st.session_state.product = None
            
            # Update navigation index
            try:
                new_index = new_images.index(current_image)
                st.session_state.nav_index = new_index
            except ValueError:
                st.session_state.nav_index = 0
                
            # Save changes
            self.metadata.save()
            
            # Set success message
            st.session_state.top_bar_message = f"Image moved to {new_content_type}"
            st.session_state.top_bar_message_type = "success"
            
        except Exception as e:
            error_msg = f"Failed to change content type: {str(e)}"
            logger.error(error_msg)
            st.session_state.top_bar_message = error_msg
            st.session_state.top_bar_message_type = "error"
            raise

    def _validate_product_assignment(
        self, content_type: str, product: str
    ) -> tuple[bool, str]:
        """Validate if a product can be assigned.
        Only checks if product exists in content type.
        """
        if not product:
            return True, ""

        # Only check if product exists
        if any(p["name"] == product for p in self.metadata_data["products"][content_type]):
            return True, ""
            
        return False, f"Product '{product}' not found in content type '{content_type}'"

    def _render_product_assignment(self):
        """Render product assignment UI controls"""
        current_image = st.session_state.get("selected_image")
        if not current_image:
            return

        image_data = self.metadata_data["images"][current_image]
        content_type = image_data["content_type"]
        current_product = image_data.get("product")
        error_msg = ""  # Initialize error_msg at the start!

        # Create columns for product selection and info
        col1, col2 = st.columns([3, 2])

        with col1:
            # Get available products for content type
            available_products = ["None"]  # Add None as first option
            products_info = {}  # Store product info for display

            for prod in self.metadata_data["products"][content_type]:
                name = prod["name"]
                if "current_count" not in prod:
                    prod["current_count"] = 0
                products_info[name] = {
                    "current": prod["current_count"],
                    "min": prod["min_occurrences"],
                }
                available_products.append(name)

            # Show product dropdown
            selected_product = st.selectbox(
                "Assign Product",
                options=available_products,
                index=(
                    available_products.index(current_product)
                    if current_product in available_products
                    else 0
                ),
                key=f"product_select_{current_image}",
            )

        # Show product info in second column
        with col2:
            if selected_product != "None":
                info = products_info.get(selected_product)
                if info:
                    st.write(f"Usage: {info['current']}/{info['min']}")

        # Only show assign button if selection changed
        if selected_product != (current_product or "None"):
            is_valid, error_msg = self._validate_product_assignment(
                content_type, selected_product if selected_product != "None" else None
            )

            if st.button(
                "Assign Product",
                disabled=not is_valid,
                use_container_width=True,
                key=f"assign_product_{current_image}",
            ):
                self._handle_product_assignment(
                    current_product, selected_product, content_type
                )
                st.rerun()

        if error_msg:
            st.error(error_msg)

    def _handle_product_assignment(
        self, old_product: str, new_product: str, content_type: str
    ):
        """Handle product assignment including count updates"""
        try:
            current_image = st.session_state.get("selected_image")
            if not current_image:
                return

            # Prevent setting product to None
            if new_product == "None":
                st.error("Cannot set product to None. Please select a valid product.")
                return

            # Just validate product exists
            is_valid, error_msg = self._validate_product_assignment(content_type, new_product)
            if not is_valid:
                st.error(error_msg)
                return

            # Handle count updates
            if old_product:
                self.metadata_editor._update_product_count(
                    content_type, old_product, increment=False
                )

            if new_product:
                self.metadata_editor._update_product_count(
                    content_type, new_product, increment=True
                )

            # Update image metadata
            self.metadata_editor.edit_image(current_image, {"product": new_product})
            
            # Save metadata
            self.metadata.save()
            
            # Set success message in top bar
            st.session_state.top_bar_message = f"Product updated to: {new_product or 'None'}"
            st.session_state.top_bar_message_type = "success"

        except Exception as e:
            st.session_state.top_bar_message = f"Failed to update product: {str(e)}"
            st.session_state.top_bar_message_type = "error"
            logger.error(f"Product assignment error: {str(e)}")
            # Attempt to rollback counts
            if old_product:
                self.metadata_editor._update_product_count(
                    content_type, old_product, increment=True
                )
            if new_product:
                self.metadata_editor._update_product_count(
                    content_type, new_product, increment=False
                )

    """
    def handle_content_type_change(self):
        "" "Updated content type change handler with product management" ""
        print("\n=== Content Type Change Handler ===")

        current_image = st.session_state.selected_image
        new_content_type = st.session_state.settings_content_type

        print(f"Current image: {current_image}")
        print(f"New content type: {new_content_type}")

        if not current_image:
            return

        try:
            # Get current image data
            image_data = self.metadata_data["images"][current_image]
            old_content_type = image_data["content_type"]
            old_product = image_data.get("product")

            if old_content_type == new_content_type:
                return

            # Handle product count if needed
            if old_product:
                print(f"Decrementing count for product {old_product}")
                self.metadata_editor._update_product_count(
                    old_content_type, old_product, increment=False
                )

            # Physical move and metadata updates remain the same
            old_path = self.base_path / old_content_type / current_image
            new_path = self.base_path / new_content_type / current_image
            old_path.rename(new_path)

            # Update metadata structure
            self.metadata_data["structure"][old_content_type]["images"].remove(
                current_image
            )
            self.metadata_data["structure"][new_content_type]["images"].append(
                current_image
            )
            self.metadata_data["structure"][new_content_type]["images"].sort()

            # Update image metadata - note product is reset to None
            self.metadata_data["images"][current_image].update(
                {
                    "content_type": new_content_type,
                    "product": None,  # Reset product when changing content type
                    "settings_source": "default",
                    "settings": None,
                }
            )

            # Update session states
            st.session_state.content_type = new_content_type
            st.session_state.settings_product = None
            st.session_state.product = None

            # Update nav index
            images = self.metadata_data["structure"][new_content_type]["images"]
            if current_image in images:
                st.session_state.nav_index = images.index(current_image)

            # Save metadata
            self.metadata.save()

            # st.success(f"Image moved to {new_content_type}")
            st.session_state.top_bar_message = f"Image moved to {new_content_type}"
            st.session_state.top_bar_message_type = "success"

        except Exception as e:
            print(f"ERROR: {str(e)}")
            logger.error(f"Failed to change content type: {str(e)}")
            st.error(f"Failed to change content type: {str(e)}")
        """

    def _product_level_duplicate_prevention_changer_base_settings(self):
        current_image = st.session_state.selected_image
        if current_image:
            image_data = self.metadata_data["images"][current_image]
            content_type = image_data["content_type"]
            product = image_data["product"]

            if product:
                # Create two columns for the state and button
                col1, col2 = st.columns([1, 2])

                # Get current state
                product_info = next(
                    (
                        p
                        for p in self.metadata_data["products"][content_type]
                        if p["name"] == product
                    ),
                    None,
                )
                current_state = (
                    product_info["prevent_duplicates"] if product_info else False
                )

                # Display current state in first column
                with col1:
                    st.write(f"Current: {current_state}")

                # Display toggle button in second column
                with col2:
                    if st.button("Toggle Duplicate Prevention"):
                        # Toggle logic here
                        if product_info:
                            product_info['prevent_duplicates'] = not current_state
                            self.metadata.save()  # Save changes
                            st.rerun()  # Force UI refresh
            else:
                st.button(
                    "Toggle Duplicate Prevention",
                    disabled=True,
                    help="Select a product first",
                )

    def get_available_captions(self, content_type: str, product: str, captions_data: dict) -> List[str]:
        """Get available captions based on product duplication rules
        
        Args:
            content_type: Type of content (hook, content, cta)
            product: Product name for the image (can be None)
            captions_data: Loaded captions data from CaptionsHelper
            
        Returns:
            List of available captions based on product rules
        """
        # Treat None/null products as 'all' by default
        effective_product = product if product else 'all'
        
        # Get product settings from metadata
        product_settings = next(
            (p for p in self.metadata_data['products'][content_type] 
            if p['name'] == effective_product),
            None
        )
        
        # If still no product settings found, try 'all' as fallback
        if not product_settings and effective_product != 'all':
            product_settings = next(
                (p for p in self.metadata_data['products'][content_type] 
                if p['name'] == 'all'),
                None
            )
            effective_product = 'all'
        
        if not product_settings:
            st.session_state.top_bar_message = f"No product settings found for '{effective_product}' in {content_type}"
            st.session_state.top_bar_message_type = "warning"
            return []
        
        prevent_duplicates = product_settings['prevent_duplicates']
        captions = []
        
        if prevent_duplicates:
            # Only show captions for this specific product
            captions.extend(captions_data['by_type'][content_type].get(effective_product, []))
        elif effective_product != 'all':
            # Show this product's captions
            captions.extend(captions_data['by_type'][content_type].get(effective_product, []))
        else:
            # Product is 'all' and duplicates allowed - show all captions except from prevent_duplicate products
            for prod, prod_captions in captions_data['by_type'][content_type].items():
                # Check if this product allows duplicates
                prod_settings = next(
                    (p for p in self.metadata_data['products'][content_type] 
                    if p['name'] == prod),
                    None
                )
                if prod_settings and not prod_settings['prevent_duplicates']:
                    captions.extend(prod_captions)
        
        return captions
    

    def render_preview_expander(self, settings_data):
        """Render preview expander with corrected content types and products access"""
        with st.expander("Preview Settings", expanded=True):
            # Check if an image is selected
            current_image = st.session_state.get('selected_image')
            if not current_image:
                st.warning("Please select an image to preview")
                return
                
            try:
                # Get image metadata with safety checks
                image_data = self.metadata_data["images"].get(current_image)
                if not image_data:
                    st.error(f"No metadata found for image: {current_image}")
                    return
                    
                content_type = image_data.get("content_type")
                if not content_type:
                    st.error("No content type found for image")
                    return
                    
                product = image_data.get("product")
                
                # Verify captions.csv exists
                captions_csv_path = self.base_path / "captions.csv"
                if not captions_csv_path.exists():
                    st.error("Captions file not found")
                    return
                
                # Get captions using the class's content_types and products
                try:
                    captions_data = CaptionsHelper.get_captions(
                        captions_csv_path,
                        content_types=self.content_types,  # Use class's content_types
                        products=self.products,  # Use class's products dictionary
                        separator=self.separator  # Pass separator to get_captions
                    )
                except Exception as e:
                    st.error(f"Error loading captions: {str(e)}")
                    logger.error(f"Caption loading error: {str(e)}")
                    return
                
                # Get available captions with safety checks
                captions = self.get_available_captions(content_type, product, captions_data)
                
                # Multi-caption UI (uses '||' delimiter supported by renderer)
                st.divider()
                col_a, col_b = st.columns([1, 2])
                with col_a:
                    # Check if metadata has extra captions to determine default state
                    has_extra_metadata = bool(image_data.get("extra_caption_settings"))
                    
                    # ALSO check if there's text in the session state for this image's extra captions
                    # This handles the case where user navigates back to an image they were editing
                    # (Note: session state keys for widgets are cleared on some navigations, but let's check metadata source string if we saved it)
                    # Actually, the best proxy is: Is there any extra caption text associated with this image?
                    # The text area below uses 'extra_captions_{current_image}' key.
                    
                    # Better logic: Default to TRUE if there are extra settings OR existing extra text.
                    # Getting the text value before the widget is created is tricky.
                    # But we can check if we loaded any extra text from metadata previously.
                    
                    # Simplified: If we found extra settings in the metadata, value=True.
                    # If we didn't, value=False.
                    # The previous fix (key=imagespecific) forces a reset to this calculated value.
                    
                    # The user's issue might be that they WANT it to be ON by default if they are adding text?
                    # Or maybe they unchecked it and the settings disappeared but they still wanted them?
                    
                    # Revert to standard session state persistence but with intelligent initialization?
                    # No, the "key=..." forces a re-render.
                    
                    # Let's verify what the user sees in the screenshot:
                    # Checkbox is OFF. Text area has "dsdfdsfsfsfsdf". settings are GONE.
                    # This means they have text but the mode is off.
                    # If they check the box, the settings will appear.
                    
                    # Maybe they want the mode to auto-check if they type text?
                    # Streamlit doesn't support cyclic dependencies easily.
                    
                    # Adjust default value logic:
                    # If there is text in the extra_captions box (which might be preserved by streamlit if key matches),
                    # we should default to True.
                    
                    # Let's try to peek at the session state for the text area key
                    extra_text_key = f"extra_captions_text_{current_image}"
                    existing_text = st.session_state.get(extra_text_key, "")

                    # Safely check for extra_captions in settings
                    settings = image_data.get("settings")
                    if not existing_text and settings and isinstance(settings, dict):
                        # Fallback if we saved text in settings (we don't currently save raw text there, just settings)
                        pass

                    default_value = has_extra_metadata or bool(existing_text)

                    use_multi = st.checkbox(
                        "Multi-caption mode",
                        value=default_value, 
                        key=f"multi_caption_mode_{current_image}",
                        help="Render multiple captions on the image. Each line below becomes an extra caption."
                    )
                    # Sync to session state for legacy access if needed
                    st.session_state.multi_caption_mode = use_multi
                with col_b:
                    extra_captions_text = st.text_area(
                        "Extra captions (one per line)",
                        value="",
                        height=90,
                        disabled=not use_multi,
                        help="Example:\nTop right note\nBottom note"
                    )
                
                # Separate settings for extra captions - ALWAYS ON when multi-caption is enabled
                extra_caption_settings = {}
                if use_multi:
                    st.markdown("---")
                    st.markdown("#### 📝 Caption 2 Settings (Independent)")
                    # Caption 2 has its own independent defaults - does NOT inherit from Caption 1
                    # Get text type for style label only
                    current_type = settings_data.get("base_settings", {}).get("default_text_type", "plain")
                    current_text_settings = settings_data.get("text_settings", {})
                    base_text_settings = current_text_settings.get(current_type, {})

                    # ===== FONT SETTINGS ROW =====
                    st.markdown("**Font & Style**")
                    col1, col2, col3 = st.columns([4, 2, 2])

                    with col1:
                        # Font selection - Independent default (tiktokfont)
                        extra_font = st.selectbox(
                            "Font",
                            options=list(self.fonts.keys()),
                            index=0,  # Always default to first font (tiktokfont)
                            key="extra_caption_font"
                        )
                        extra_caption_settings["font"] = self.fonts.get(extra_font)

                    with col2:
                        extra_font_size = st.number_input(
                            "Font Size",
                            min_value=1.0,
                            max_value=500.0,
                            value=50.0,  # Independent default
                            step=0.5,
                            format="%.1f",
                            key="extra_caption_font_size"
                        )
                        extra_caption_settings["font_size"] = extra_font_size

                    with col3:
                        # Get style type from Caption 1 for label, but use independent default value
                        style_label = base_text_settings.get("style_type", "outline_width").replace("_", " ").title()
                        extra_style_value = st.number_input(
                            style_label,
                            min_value=0.0,
                            max_value=100.0,
                            value=5.0,  # Independent default
                            step=0.5,
                            format="%.1f",
                            key="extra_caption_style_value"
                        )
                        extra_caption_settings["style_value"] = extra_style_value


                    # ===== POSITION SETTINGS =====
                    st.markdown("**Position**")

                    # Vertical position with slider - INDEPENDENT from Caption 1
                    vcol1, vcol2 = st.columns([0.7, 0.3])
                    with vcol1:
                        # Default to bottom (0.75) instead of inheriting Caption 1's position
                        default_v = (0.75, 0.75) if "extra_caption_v_pos" not in st.session_state else st.session_state.extra_caption_v_pos
                        if isinstance(default_v, list):
                            default_v = tuple(default_v)
                        extra_v_pos = st.slider(
                            "Vertical Position",
                            min_value=0.0,
                            max_value=1.0,
                            value=default_v,
                            key="extra_caption_v_pos"
                        )
                        extra_caption_settings["vertical_position"] = list(extra_v_pos)
                    with vcol2:
                        extra_v_jitter = st.number_input(
                            "V Jitter",
                            min_value=0.0,
                            max_value=0.1,
                            value=0.0,  # Independent default
                            step=0.01,
                            key="extra_caption_v_jitter"
                        )
                        extra_caption_settings["vertical_jitter"] = extra_v_jitter

                    # Horizontal position with slider - INDEPENDENT from Caption 1
                    hcol1, hcol2 = st.columns([0.7, 0.3])
                    with hcol1:
                        # Default to center (0.5) instead of inheriting Caption 1's position
                        default_h = (0.5, 0.5) if "extra_caption_h_pos" not in st.session_state else st.session_state.extra_caption_h_pos
                        if isinstance(default_h, list):
                            default_h = tuple(default_h)
                        extra_h_pos = st.slider(
                            "Horizontal Position",
                            min_value=0.0,
                            max_value=1.0,
                            value=default_h,
                            key="extra_caption_h_pos"
                        )
                        extra_caption_settings["horizontal_position"] = list(extra_h_pos)
                    with hcol2:
                        extra_h_jitter = st.number_input(
                            "H Jitter",
                            min_value=0.0,
                            max_value=0.1,
                            value=0.0,  # Independent default
                            step=0.01,
                            key="extra_caption_h_jitter"
                        )
                        extra_caption_settings["horizontal_jitter"] = extra_h_jitter


                    # ===== COLOR SETTINGS =====
                    st.markdown("**Colors**")
                    col_text, col_outline = st.columns(2)
                    with col_text:
                        extra_text_color = st.color_picker(
                            "Text Color",
                            value="#FFFFFF",
                            key="extra_caption_text_color"
                        )
                        extra_caption_settings["text_color"] = extra_text_color
                    with col_outline:
                        extra_outline_color = st.color_picker(
                            "Outline/BG Color",
                            value="#000000",
                            key="extra_caption_outline_color"
                        )
                        extra_caption_settings["outline_color"] = extra_outline_color

                    # ===== MARGINS =====
                    st.markdown("**Margins**")
                    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
                    with mcol1:
                        extra_margin_top = st.number_input("Top", min_value=0, max_value=500,
                            value=50, key="extra_margin_top")  # Independent default
                        extra_caption_settings["margin_top"] = extra_margin_top
                    with mcol2:
                        extra_margin_bottom = st.number_input("Bottom", min_value=0, max_value=500,
                            value=50, key="extra_margin_bottom")  # Independent default
                        extra_caption_settings["margin_bottom"] = extra_margin_bottom
                    with mcol3:
                        extra_margin_left = st.number_input("Left", min_value=0, max_value=500,
                            value=50, key="extra_margin_left")  # Independent default
                        extra_caption_settings["margin_left"] = extra_margin_left
                    with mcol4:
                        extra_margin_right = st.number_input("Right", min_value=0, max_value=500,
                            value=50, key="extra_margin_right")  # Independent default
                        extra_caption_settings["margin_right"] = extra_margin_right

                    st.markdown("---")

                # Store extra settings in session state for preview generation
                # Always use separate settings when multi-caption mode is on
                st.session_state.extra_caption_settings = extra_caption_settings if use_multi else None
                
                extra_parts = []
                if use_multi and extra_captions_text:
                    extra_parts = [ln.strip() for ln in extra_captions_text.splitlines() if ln.strip()]
                    print(f"\n📝 Extra parts created: {extra_parts}")
                elif use_multi:
                    print(f"\n⚠️  Multi-caption ON but no extra_captions_text")
                
                # Initialize caption selection if needed
                if "selected_caption_idx" not in st.session_state:
                    st.session_state.selected_caption_idx = 0
                    
                # Reset index if it's out of bounds
                if captions and st.session_state.selected_caption_idx >= len(captions):
                    st.session_state.selected_caption_idx = 0
                
                # Check if user clicked "Apply Position" - update settings and regenerate
                if st.session_state.get("apply_clicked_position", False) and st.session_state.get("clicked_position"):
                    clicked = st.session_state.clicked_position
                    x_pos = clicked["x"]
                    y_pos = clicked["y"]
                    target = clicked.get("target", "main")
                    
                    if target == "main":
                        # Update MAIN caption position in settings
                        current_type = settings_data.get('base_settings', {}).get('default_text_type', 'plain')
                        if current_type in settings_data.get('text_settings', {}):
                            # Set position to the clicked point (use same value for min and max for exact position)
                            settings_data['text_settings'][current_type]['position']['horizontal'] = [x_pos, x_pos]
                            settings_data['text_settings'][current_type]['position']['vertical'] = [y_pos, y_pos]
                            
                            # Save the updated settings
                            image_name = st.session_state.get("selected_image")
                            self.metadata_editor.edit_image(
                                image_name, {"settings": settings_data, "settings_source": "custom"}
                            )
                            self.metadata.save()
                            
                            st.success(f"✅ MAIN caption position: X={x_pos:.4f}, Y={y_pos:.4f}")
                    else:
                        # Update EXTRA caption position in session state
                        if st.session_state.get("extra_caption_settings") is None:
                            st.session_state.extra_caption_settings = {}
                        st.session_state.extra_caption_settings["horizontal_position"] = [x_pos, x_pos]
                        st.session_state.extra_caption_settings["vertical_position"] = [y_pos, y_pos]
                        
                        # CRITICAL: Also update the widget keys so the sliders reflect the change
                        st.session_state["extra_caption_h_pos"] = (x_pos, x_pos)
                        st.session_state["extra_caption_v_pos"] = (y_pos, y_pos)
                        
                        st.success(f"✅ EXTRA caption position: X={x_pos:.4f}, Y={y_pos:.4f}")
                        st.info("💡 Enable 'Separate settings for extra captions' to use this position")
                    
                    # Clear the apply flag but keep position for display
                    st.session_state.apply_clicked_position = False
                
                # TikTok frame toggle - DEFAULT ON
                show_tiktok_frame = st.checkbox(
                    "Show TikTok Frame (9:16)",
                    value=st.session_state.get("show_tiktok_frame", True),
                    help="Preview how it looks on TikTok with black bars"
                )
                st.session_state.show_tiktok_frame = show_tiktok_frame

                # Two columns for buttons
                col1, col2 = st.columns(2)

                # Generate button
                with col1:
                    generate_enabled = bool(captions)  # Only enable if we have captions
                    if st.button("Generate Preview", 
                                use_container_width=True,
                                disabled=not generate_enabled):
                        if captions:  # Double-check we have captions
                            try:
                                # Get selected caption
                                selected_caption = captions[st.session_state.selected_caption_idx]

                                # Merge with multi-caption parts using '||'
                                if extra_parts:
                                    merged = [selected_caption] + extra_parts
                                    selected_caption = " || ".join(merged)
                                    print(f"\n🔄 MERGED CAPTION: {selected_caption}")
                                    print(f"   Parts: {merged}")
                                else:
                                    print(f"\n⚠️  NO EXTRA PARTS - Single caption only: {selected_caption}")
                                
                                # Get current image path
                                image_path = self.base_path / st.session_state.content_type / current_image
                                
                                # Get text type from settings
                                text_type = settings_data.get('base_settings', {}).get('default_text_type', 'plain')
                                
                                # CRITICAL FIX: Ensure text_settings key exists in settings_data passed to generator
                                # If it's missing, construct it from the current UI state or base settings
                                if 'text_settings' not in settings_data:
                                    print("⚠️ 'text_settings' missing in settings_data, reconstructing...")
                                    settings_data['text_settings'] = {
                                        # Use the current_text_settings which holds the UI state
                                        # But wait, current_text_settings might be partial.
                                        # Let's map whatever we have.
                                        
                                        # Actually, current_text_settings was constructed earlier from settings_data.get('text_settings')
                                        # If settings_data was devoid of it, then current_text_settings is mostly empty.
                                        
                                        # We need to construct a valid text_settings dict structure
                                        "plain": {
                                            "font": settings_data.get("base_settings", {}).get("font", "tiktokfont"),
                                            "font_size": settings_data.get("base_settings", {}).get("font_size", 50),
                                            "colors": ["#FFFFFF"],
                                            "margins": {"top": 0.1, "bottom": 0.1, "left": 0.1, "right": 0.1},
                                            "position": {"vertical": 0.5, "horizontal": 0.5},
                                            # Add missing keys that generate_image expects
                                            "style_type": "outline_width",
                                            "style_value": 5
                                        }
                                    }
                                    
                                    # Override with any UI settings if available in scope?
                                    # current_text_settings is available in this scope? Yes, defined at top of render_settings_expander
                                    if 'current_text_settings' in locals() and current_text_settings:
                                        settings_data['text_settings'] = current_text_settings

                                # If TikTok frame mode: frame the image FIRST, then add text
                                # This way text is positioned relative to full 1080x1920
                                use_tiktok_frame = st.session_state.get("show_tiktok_frame", False)

                                if use_tiktok_frame:
                                    # Create framed base image first
                                    framed_path = self.create_tiktok_base(str(image_path))
                                    render_path = framed_path
                                else:
                                    render_path = str(image_path)

                                # Generate preview (text rendered on framed or original)
                                preview_image = self.generate_preview(
                                    settings_data=settings_data,
                                    text_type=text_type,
                                    colour_index=0,
                                    image_path=render_path,
                                    text=selected_caption
                                )

                                # Clean up temp file if we created one
                                if use_tiktok_frame:
                                    import os
                                    os.unlink(framed_path)

                                # Save preview image
                                # Always save previews as PNG to avoid JPEG RGBA errors
                                preview_dir = self.base_path / "preview"
                                preview_dir.mkdir(exist_ok=True)
                                from pathlib import Path as _P
                                preview_filename = f"{_P(current_image).stem}.png"
                                preview_path = preview_dir / preview_filename
                                to_save = preview_image
                                if to_save.mode != "RGBA":
                                    to_save = to_save.convert("RGBA")
                                to_save.save(str(preview_path))
                                
                                # Update session state with preview path
                                st.session_state.preview_image_path = str(preview_path)
                                
                                # Force rerun to update display
                                st.rerun()
                                
                            except Exception as e:
                                logger.error(f"Preview generation failed: {str(e)}")
                                st.error(f"Failed to generate preview: {str(e)}")

                # Reset button
                with col2:
                    if st.button("Reset Preview", use_container_width=True):
                        # Clear preview path from session state
                        if "preview_image_path" in st.session_state:
                            # Delete preview file if it exists
                            preview_path = Path(st.session_state.preview_image_path)
                            if preview_path.exists():
                                preview_path.unlink()
                            del st.session_state.preview_image_path
                            st.rerun()

                # Metadata Refresh Section
                st.divider()
                st.subheader("🔄 Metadata Management")

                col_refresh1, col_refresh2 = st.columns(2)
                with col_refresh1:
                    st.markdown("**Refresh metadata** when you add new images to folders")
                # Save button
                if st.button("Save Settings", type="primary", use_container_width=True):
                    # Update settings
                    image_metadata["settings"] = settings
                    image_metadata["settings_source"] = "custom"
                    
                    # Store extra caption settings in metadata if enabled
                    if use_separate_settings and extra_caption_settings:
                         if "extra_caption_settings" not in image_metadata:
                             image_metadata["extra_caption_settings"] = {}
                         image_metadata["extra_caption_settings"] = extra_caption_settings
                    elif "extra_caption_settings" in image_metadata and not use_separate_settings:
                         # Remove if disabled
                         del image_metadata["extra_caption_settings"]

                    # Save metadata
                    self.metadata_editor.save_metadata()
                    
                    st.success("Settings saved!")
                    st.session_state.settings_source = "custom"
                    st.rerun()

                # NEW: Apply to All Button
                st.markdown("---")
                if st.button(f"Apply to All Slides in '{content_type}'", type="secondary", use_container_width=True, help="Copy these settings (including Caption 2) to all images in this category"):
                    with st.spinner(f"Applying settings to all {len(self.metadata_data['structure'][content_type]['images'])} slides..."):
                        try:
                            # CRITICAL: Copy the COMPLETE settings_data structure
                            # settings_data contains: {"text_settings": {...}, "base_settings": {...}}
                            # We need to copy this entire structure, not just text_settings
                            import copy
                            settings_to_apply = copy.deepcopy(settings_data)

                            print(f"\n🔄 APPLY TO ALL DEBUG:")
                            print(f"Settings to apply keys: {settings_to_apply.keys()}")
                            if "text_settings" in settings_to_apply:
                                print(f"Text settings keys: {settings_to_apply['text_settings'].keys()}")
                                if "plain" in settings_to_apply["text_settings"]:
                                    plain_keys = settings_to_apply["text_settings"]["plain"].keys()
                                    print(f"Plain text settings: {plain_keys}")

                            # Get current multi-caption mode state
                            current_image = st.session_state.selected_image
                            use_multi_scope = st.session_state.get(f"multi_caption_mode_{current_image}", False)

                            # Get extra caption settings if multi-caption is enabled
                            extra_settings_scope = None
                            if use_multi_scope:
                                extra_settings_scope = st.session_state.get("extra_caption_settings")
                                print(f"Extra caption settings: {extra_settings_scope is not None}")
                            
                            # Iterate through all images in the category
                            category_images = self.metadata_data["structure"][content_type]["images"]
                            count = 0
                            
                            for img_name in category_images:
                                if img_name == current_image:
                                    continue # Skip current one as it's the source
                                
                                target_img_data = self.metadata_data["images"][img_name]

                                # Deep copy the complete settings structure (already imported copy above)
                                target_img_data["settings"] = copy.deepcopy(settings_to_apply)
                                target_img_data["settings_source"] = "custom"

                                # Copy extra caption settings if they exist
                                if extra_settings_scope:
                                    target_img_data["extra_caption_settings"] = copy.deepcopy(extra_settings_scope)
                                elif "extra_caption_settings" in target_img_data:
                                    # Remove extra caption settings if source image doesn't have them
                                    del target_img_data["extra_caption_settings"]
                                    
                                count += 1
                            
                            # Save ALL changes
                            self.metadata_editor.save_metadata()
                            
                            st.success(f"✅ Settings applied to {count} other slides in '{content_type}'!")
                            import time
                            time.sleep(1.5)
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Failed to apply settings: {str(e)}")
                            logger.error(f"Bulk apply error: {str(e)}")
                with col_refresh2:
                    if st.button("🔄 Refresh Metadata", use_container_width=True):
                        try:
                            # Delete metadata file
                            metadata_file = self.base_path / "metadata.json"
                            if metadata_file.exists():
                                metadata_file.unlink()
                                st.success("✅ Metadata deleted! Reloading page...")
                                st.rerun()
                            else:
                                st.warning("No metadata file found")
                        except Exception as e:
                            logger.error(f"Failed to refresh metadata: {str(e)}")
                            st.error(f"❌ Failed to refresh: {str(e)}")

                # Batch Generation Section
                st.divider()
                st.subheader("🎬 Batch Generation")

                # Controls
                col_gen1, col_gen2 = st.columns(2)
                with col_gen1:
                    variations = st.number_input(
                        "Number of variations",
                        min_value=1,
                        max_value=100,
                        value=2,
                        help="How many variations to generate from the captions"
                    )
                with col_gen2:
                    allow_dupes = st.checkbox(
                        "Allow duplicates for 'all' product",
                        value=True,
                        help="✅ ENABLE THIS for maximum variation! Rotates through all images, then cycles through again for more posts."
                    )

                # Generate button
                if st.button("Generate All Variations", type="primary", use_container_width=True):
                    with st.spinner("Generating slides..."):
                        try:
                            from generation.generate import Generator

                            # Load captions
                            captions_data = CaptionsHelper.get_captions(
                                self.base_path / "captions.csv",
                                content_types=self.content_types,
                                products=self.products,
                                separator=self.separator
                            )

                            # Generate
                            generator = Generator(self.base_path, self.metadata, captions_data)
                            output_path = generator.generate(variations, allow_dupes)

                            st.success(f"✅ Generated {variations} variations to {output_path}")

                            # Open folder button
                            col_open1, col_open2 = st.columns([1, 2])
                            with col_open1:
                                if st.button("Open Output Folder"):
                                    import subprocess
                                    subprocess.run(["open", str(output_path)])

                        except Exception as e:
                            logger.error(f"Generation failed: {str(e)}")
                            st.error(f"❌ Generation failed: {str(e)}")

                # Image Swap Section
                st.divider()
                st.subheader("🔄 Swap Images")
                st.caption("Upload new images to replace current ones. Old images are archived to `past_images/`")

                # Select which folder to swap
                swap_folder = st.selectbox(
                    "Select folder to swap",
                    options=list(self.content_types),
                    key="swap_folder_select"
                )

                # Show current image count
                current_count = len(self.metadata_data["structure"][swap_folder]["images"])
                st.info(f"📁 **{swap_folder}/** currently has **{current_count}** images")

                # File uploader
                uploaded_files = st.file_uploader(
                    "Upload new images",
                    type=["jpg", "jpeg", "png", "webp"],
                    accept_multiple_files=True,
                    key="swap_images_uploader"
                )

                if uploaded_files:
                    st.success(f"✅ {len(uploaded_files)} images ready to swap")

                    if st.button("🔄 Swap Images Now", type="primary", use_container_width=True):
                        try:
                            import shutil
                            from datetime import datetime

                            folder_path = self.base_path / swap_folder
                            archive_path = self.base_path / "past_images" / f"{swap_folder}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                            # Create archive folder
                            archive_path.mkdir(parents=True, exist_ok=True)

                            # Move old images to archive
                            moved_count = 0
                            for img_file in folder_path.iterdir():
                                if img_file.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                                    shutil.move(str(img_file), str(archive_path / img_file.name))
                                    moved_count += 1

                            # Save new images
                            saved_count = 0
                            for uploaded_file in uploaded_files:
                                save_path = folder_path / uploaded_file.name
                                with open(save_path, "wb") as f:
                                    f.write(uploaded_file.getbuffer())
                                saved_count += 1

                            # Delete metadata to force refresh
                            metadata_file = self.base_path / "metadata.json"
                            if metadata_file.exists():
                                metadata_file.unlink()

                            st.success(f"✅ Swapped! Archived {moved_count} → Added {saved_count} images")
                            st.info(f"📦 Old images saved to: `past_images/{archive_path.name}/`")
                            st.warning("⚠️ Reloading to refresh metadata...")
                            st.rerun()

                        except Exception as e:
                            logger.error(f"Image swap failed: {str(e)}")
                            st.error(f"❌ Swap failed: {str(e)}")

                # Delete Specific Image Section
                st.markdown("---")
                st.markdown("**🗑️ Delete Specific Image**")

                # Select folder
                delete_folder = st.selectbox(
                    "Select folder",
                    options=list(self.content_types),
                    key="delete_img_folder_select"
                )

                # Get images in selected folder
                folder_images = self.metadata_data["structure"][delete_folder]["images"]

                if folder_images:
                    # Dropdown to select image
                    image_to_delete = st.selectbox(
                        f"Select image to delete ({len(folder_images)} images)",
                        options=folder_images,
                        key="delete_img_select"
                    )

                    # Show preview of selected image
                    preview_path = self.base_path / delete_folder / image_to_delete
                    if preview_path.exists():
                        st.image(str(preview_path), width=200, caption=image_to_delete)

                    if st.button("🗑️ Delete Image", type="secondary", use_container_width=True, key="delete_single_img_btn"):
                        try:
                            import shutil
                            from datetime import datetime

                            # Move to past_images instead of permanent delete
                            archive_path = self.base_path / "past_images" / f"deleted_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            archive_path.mkdir(parents=True, exist_ok=True)

                            img_path = self.base_path / delete_folder / image_to_delete
                            if img_path.exists():
                                shutil.move(str(img_path), str(archive_path / image_to_delete))

                            # Remove from metadata
                            if image_to_delete in self.metadata_data["structure"][delete_folder]["images"]:
                                self.metadata_data["structure"][delete_folder]["images"].remove(image_to_delete)

                            if image_to_delete in self.metadata_data["images"]:
                                del self.metadata_data["images"][image_to_delete]

                            self.metadata.save()

                            st.success(f"✅ Deleted '{image_to_delete}' (backed up)")
                            st.rerun()

                        except Exception as e:
                            st.error(f"❌ Delete failed: {str(e)}")
                else:
                    st.info(f"No images in {delete_folder}")

                # Add Images Section
                st.markdown("---")
                st.markdown("**➕ Add Images**")

                add_to_folder = st.selectbox(
                    "Add to folder",
                    options=list(self.content_types),
                    key="add_img_folder_select"
                )

                uploaded_images = st.file_uploader(
                    "Upload images",
                    type=["jpg", "jpeg", "png", "webp"],
                    accept_multiple_files=True,
                    key="add_imgs_uploader"
                )

                if uploaded_images:
                    st.success(f"✅ {len(uploaded_images)} images ready to add")

                    if st.button(f"➕ Add {len(uploaded_images)} Images", type="primary", use_container_width=True, key="add_imgs_btn"):
                        try:
                            from PIL import Image as PILImage
                            folder_path = self.base_path / add_to_folder
                            added_count = 0

                            for uploaded_file in uploaded_images:
                                save_path = folder_path / uploaded_file.name

                                # Save the image
                                with open(save_path, "wb") as f:
                                    f.write(uploaded_file.getbuffer())

                                # Add to metadata structure
                                if uploaded_file.name not in self.metadata_data["structure"][add_to_folder]["images"]:
                                    self.metadata_data["structure"][add_to_folder]["images"].append(uploaded_file.name)

                                # Add image entry with default settings
                                if uploaded_file.name not in self.metadata_data["images"]:
                                    img = PILImage.open(save_path)
                                    self.metadata_data["images"][uploaded_file.name] = {
                                        "content_type": add_to_folder,
                                        "dimensions": {"width": img.size[0], "height": img.size[1]},
                                        "product": "all",
                                        "settings_source": "default"
                                    }

                                added_count += 1

                            self.metadata.save()

                            st.success(f"✅ Added {added_count} images to {add_to_folder}")
                            st.rerun()

                        except Exception as e:
                            st.error(f"❌ Add failed: {str(e)}")

                # Caption Editor Section
                st.divider()
                st.subheader("✏️ Caption Editor")

                # Load all captions from CSV for editing
                captions_path = self.base_path / "captions.csv"
                all_captions = []
                if captions_path.exists():
                    import csv
                    with open(captions_path, 'r') as f:
                        reader = csv.DictReader(f)
                        all_captions = list(reader)

                if all_captions:
                    # Initialize edit state
                    if "editing_caption_idx" not in st.session_state:
                        st.session_state.editing_caption_idx = None

                    # Detect caption column (could be 'caption' or content type name like 'slide1')
                    first_row = all_captions[0]
                    caption_col = None
                    for col in first_row.keys():
                        if col == "caption" or col in self.content_types:
                            if first_row.get(col):  # Has actual caption text
                                caption_col = col
                                break
                    if not caption_col:
                        caption_col = list(first_row.keys())[1] if len(first_row.keys()) > 1 else list(first_row.keys())[0]

                    st.caption(f"📝 {len(all_captions)} captions (column: {caption_col})")

                    # Display captions with edit/delete buttons
                    for idx, row in enumerate(all_captions):
                        caption_text = row.get(caption_col, "") or row.get("caption", "")
                        col1, col2, col3 = st.columns([6, 1, 1])

                        with col1:
                            if st.session_state.editing_caption_idx == idx:
                                # Edit mode
                                new_text = st.text_area(
                                    f"Caption {idx}",
                                    value=caption_text,
                                    key=f"edit_caption_{idx}",
                                    label_visibility="collapsed"
                                )
                                # Save button
                                if st.button("💾 Save", key=f"save_caption_{idx}"):
                                    all_captions[idx][caption_col] = new_text
                                    # Write back to CSV
                                    with open(captions_path, 'w', newline='') as f:
                                        writer = csv.DictWriter(f, fieldnames=all_captions[0].keys())
                                        writer.writeheader()
                                        writer.writerows(all_captions)
                                    st.session_state.editing_caption_idx = None
                                    st.success(f"Caption {idx} saved!")
                                    st.rerun()
                            else:
                                st.text(f"[{idx}] {caption_text[:80]}{'...' if len(caption_text) > 80 else ''}")

                        with col2:
                            if st.button("✏️", key=f"edit_btn_{idx}", help="Edit"):
                                st.session_state.editing_caption_idx = idx
                                st.rerun()

                        with col3:
                            if st.button("🗑️", key=f"del_btn_{idx}", help="Delete"):
                                all_captions.pop(idx)
                                with open(captions_path, 'w', newline='') as f:
                                    if all_captions:
                                        writer = csv.DictWriter(f, fieldnames=all_captions[0].keys())
                                        writer.writeheader()
                                        writer.writerows(all_captions)
                                    else:
                                        f.write("content_type,product,caption\n")
                                st.success(f"Caption {idx} deleted!")
                                st.rerun()

                    # Add new caption
                    st.markdown("---")
                    st.markdown("**Add New Caption**")
                    new_caption = st.text_area("New caption text", key="new_caption_text", height=80)
                    col_add1, col_add2 = st.columns([1, 1])
                    with col_add1:
                        add_content_type = st.selectbox("Content Type", list(self.content_types), key="add_caption_ct")
                    with col_add2:
                        add_product = st.text_input("Product (or 'all')", value="all", key="add_caption_product")

                    if st.button("➕ Add Caption", type="primary", use_container_width=True):
                        if new_caption.strip():
                            import csv
                            new_row = {
                                "content_type": add_content_type,
                                "product": add_product,
                                "caption": new_caption.strip()
                            }
                            all_captions.append(new_row)
                            with open(captions_path, 'w', newline='') as f:
                                writer = csv.DictWriter(f, fieldnames=["content_type", "product", "caption"])
                                writer.writeheader()
                                writer.writerows(all_captions)
                            st.success("Caption added!")
                            st.rerun()
                        else:
                            st.warning("Enter caption text first")

                else:
                    st.info("No captions.csv found. Add captions below:")
                    new_caption = st.text_area("Caption text", key="first_caption_text")
                    if st.button("Create captions.csv"):
                        import csv
                        with open(captions_path, 'w', newline='') as f:
                            writer = csv.DictWriter(f, fieldnames=["content_type", "product", "caption"])
                            writer.writeheader()
                            if new_caption.strip():
                                writer.writerow({"content_type": "slide1", "product": "all", "caption": new_caption.strip()})
                        st.success("Created captions.csv!")
                        st.rerun()
                
            except Exception as e:
                logger.error(f"Error in preview expander: {str(e)}")
                st.error(f"An error occurred while loading the preview: {str(e)}")

    def generate_preview(self, settings_data: dict, text_type: str, colour_index: int, 
                        image_path: str, text: str):
        """
        Wrapper function to generate preview images that can be reused across components
        
        Args:
            settings_data (dict): Complete settings dictionary
            text_type (str): Type of text (plain/highlight)
            colour_index (int): Index of color pair to use
            image_path (str): Path to source image
            text (str): Caption text to render
            
        Returns:
            PIL.Image: Generated preview image
        """
        try:
            from text.generate_image import generate_image
            
            # Inject extra caption settings from session state so they are available to the renderer
            if "extra_caption_settings" in st.session_state and st.session_state.extra_caption_settings:
                settings_data["extra_caption_settings"] = st.session_state.extra_caption_settings
            
            logger.trace(f"PREVIEW // About to call generate_image with settings: {settings_data}")
            
            result = generate_image(
                settings=settings_data,
                text_type=text_type,
                colour_index=colour_index,
                image_path=image_path,
                text=text
            )
            
            logger.trace("PREVIEW // generate_image call completed")
            return result
            
        except Exception as e:
            logger.error(f"Preview generation failed: {str(e)}")
            raise