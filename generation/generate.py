from config.logging import logger
import random
from text.generate_image import generate_image
from PIL import Image, ImageEnhance  # type: ignore
from typing import List, Optional, Union
from pathlib import Path


class Generator:
    def __init__(self, base_path: Path, metadata: dict, captions: dict):
        self.base_path = base_path
        self.metadata = metadata
        self.captions = captions
        self.default_output_path = self.base_path / "output"
        # Track cycling index for each content_type
        self.cycle_indices = {}

    def _validate_output_path(
        self, custom_output_path: Optional[Union[Path, str]] = None
    ) -> Path:
        """Validate and return the output path

        Args:
            custom_output_path: Optional custom output path

        Returns:
            Path: Valid output path (either custom or default)
        """
        if custom_output_path is None:
            output_path = self.default_output_path
        else:
            # Convert to Path if string
            output_path = (
                Path(custom_output_path)
                if isinstance(custom_output_path, str)
                else custom_output_path
            )

            # Validate the path exists
            if not output_path.exists():
                logger.warning(
                    f"Custom output path {output_path} does not exist. Using default: {self.default_output_path}"
                )
                output_path = self.default_output_path

        # Ensure output directory exists
        output_path.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Using output path: {output_path}")
        return output_path

    def _get_set_images(self, content_type: str, set_id: str) -> List[str]:
        """Get all images for a given set in a content type, sorted by index.

        Args:
            content_type: The content type folder to search in
            set_id: The set identifier

        Returns:
            List of image filenames belonging to the set, sorted by index
        """
        if not set_id:
            return []

        # Get all images for this content type
        all_images = self.metadata.data["structure"][content_type]["images"]

        # Filter for set images with matching set_id
        set_images = []
        for img_name in all_images:
            img_data = self.metadata.data["images"].get(img_name, {})
            if img_data.get("set_id") == set_id and img_data.get("content_type") == content_type:
                set_images.append((img_name, img_data.get("set_index", 0)))

        # Sort by set_index
        set_images.sort(key=lambda x: x[1])

        return [img_name for img_name, _ in set_images]

    def generate(
        self,
        variations: int = 2,
        allow_all_duplicates: bool = False,
        output_path: Optional[Union[Path, str]] = None,
    ):
        """Generate slide variations from captions.
        If the only product is "all" and prevent duplicates is True then it wont find any.
        just name the product something other than all since all is a reserved name

        Args:
            variations: Number of variations to generate
            allow_all_duplicates: If True, allows 'all' product to be used even for products with prevent_duplicates=true
            output_path: Optional custom output path. If invalid or None, uses default path
        """
        logger.info(f"Starting generation of {variations} variations")

        # Validate and get output path
        output_path = self._validate_output_path(output_path)

        # Check if CSV has set_id column
        has_set_id = self.captions.get("has_set_id", False)
        set_ids = self.captions.get("set_ids", [])
        is_sets_mode = self.captions.get("is_sets_mode", False)

        import gc

        gc_post_counter = (
            0  # count # of posts we have done. collect garbace every 5 rounds.
        )

        """
        Example header structure:
        Normal mode:
        Without set_id: ['product_hook', 'hook', 'product_filler', 'filler', ...]
        With set_id: ['set_id', 'product_hook', 'hook', 'product_filler', 'filler', ...]

        Sets mode (simplified):
        ['set_id', 'caption_1', 'caption_2', 'caption_3', ...]
        Images come from sets/{set_id}/ folder, sorted alphabetically
        """

        # Handle simplified sets mode differently
        if is_sets_mode:
            # Sets mode: headers are caption_1, caption_2, etc.
            logger.info("Using simplified sets mode (caption_1, caption_2, caption_3 format)")
            headers_map = None  # Not needed in sets mode
        else:
            # Normal mode: Account for set_id column offset
            header_offset = 1 if has_set_id else 0
            headers_map = {
                i: self.captions["headers"][header_offset + (i - 1) * 2].split("_")[1]
                for i in range(1, (len(self.captions["headers"]) - header_offset) // 2 + 1)
            }

        for variation_num in range(1, variations + 1):
            # Reset cycle indices for each variation
            self.cycle_indices = {}

            variation_path = output_path / f"variation{variation_num}"
            logger.info(f"Processing variation {variation_num}")

            # Process each row (post) in captions
            for post_num, row in enumerate(self.captions["captions"], 1):
                post_path = variation_path / f"post{post_num}"
                post_path.mkdir(
                    parents=True, exist_ok=True
                )  # Create directory once per post
                logger.info(f"Processing post {post_num}")

                # Get set_id for this row if it exists
                current_set_id = set_ids[post_num - 1] if has_set_id and post_num <= len(set_ids) else ""
                use_set = bool(current_set_id and current_set_id.strip())

                # SETS MODE: Simplified format (set_id, caption_1, caption_2, caption_3)
                if is_sets_mode and use_set:
                    logger.info(f"Processing set '{current_set_id}' in sets mode")

                    # Get images from sets/{set_id}/ folder
                    set_info = self.metadata.data.get("sets", {}).get(current_set_id)
                    if not set_info:
                        raise ValueError(f"Set '{current_set_id}' not found in sets/ folder")

                    set_images = set_info["images"]  # Already sorted alphabetically
                    set_path = Path(set_info["path"])

                    # Get captions from row (skip first column which is set_id)
                    captions = [cell.strip() for cell in row[1:] if cell.strip()]

                    if len(captions) != len(set_images):
                        raise ValueError(
                            f"Set '{current_set_id}' has {len(set_images)} images but {len(captions)} captions. "
                            f"They must match! Images: {set_images}, Captions: {captions}"
                        )

                    # Generate each slide
                    for idx, (image_name, caption) in enumerate(zip(set_images, captions), 1):
                        image_path = set_path / image_name
                        base_image = Image.open(image_path)

                        # Use default settings for now (could be enhanced later)
                        from text.generate_image import generate_image
                        image_settings = self._get_default_settings()
                        text_type = image_settings["base_settings"]["default_text_type"]

                        image = generate_image(
                            settings=image_settings,
                            text_type=text_type,
                            colour_index=random.randint(
                                0, len(image_settings["text_settings"][text_type]["colors"]) - 1
                            ),
                            image_path=str(image_path),
                            text=caption
                        )
                        base_image.close()

                        # Apply randomization
                        image = self._randomize_image_data(image)

                        # Save image with max quality
                        output_path_img = post_path / f"{idx}.png"
                        pnginfo = image.info.get("pnginfo")
                        if pnginfo:
                            image.save(output_path_img, format="PNG", compress_level=0, optimize=False, pnginfo=pnginfo)
                        else:
                            image.save(output_path_img, format="PNG", compress_level=0, optimize=False)
                        image.close()
                        logger.debug(f"Saved slide {idx} for post {post_num} in variation {variation_num}")

                    # Skip normal processing for this row
                    continue

                # NORMAL MODE: Original logic
                # Track used images for duplicate prevention
                used_images = {
                    content_type: {
                        product_info["name"]: []  # Use product name as key
                        for product_info in self.metadata.data["products"][content_type]
                    }
                    for content_type in self.metadata.data["content_types"]
                }

                # If using sets (old format), pre-load all set images for validation
                set_images_cache = {}
                if use_set and not is_sets_mode:
                    logger.info(f"Using image set: {current_set_id}")
                    for content_type in self.metadata.data["content_types"]:
                        set_images_cache[content_type] = self._get_set_images(content_type, current_set_id)
                        logger.debug(f"Found {len(set_images_cache[content_type])} images for set '{current_set_id}' in {content_type}")

                # Process each content piece in the row
                # Account for set_id column offset in row slicing
                row_offset = 1 if (has_set_id and not is_sets_mode) else 0
                for idx, (product, content) in enumerate(zip(row[row_offset::2], row[row_offset + 1::2]), 1):
                    content_type = headers_map[idx]

                    logger.debug(
                        f"Processing {content_type} with product {product} and text: {content}"
                    )

                    # Generate and save image (even if content is empty - will use raw image)
                    if not content:
                        logger.debug(f"Empty content for {content_type} - using raw image without text")
                        # Just load the raw image without adding text
                        content_path = self.base_path / content_type
                        available_images = self._get_available_images(
                            content_type, product, used_images, allow_all_duplicates
                        )
                        if not available_images:
                            raise ValueError(f"No available images for {content_type} - {product}")

                        # Use cycling to select image
                        if content_type not in self.cycle_indices:
                            self.cycle_indices[content_type] = 0
                        current_index = self.cycle_indices[content_type]
                        selected_image = available_images[current_index % len(available_images)]
                        self.cycle_indices[content_type] = (current_index + 1) % len(available_images)

                        image = Image.open(content_path / selected_image)
                    elif use_set:
                        # Use set image (sequential selection)
                        set_images = set_images_cache.get(content_type, [])
                        if not set_images:
                            raise ValueError(
                                f"Set '{current_set_id}' has no images for content type '{content_type}'. "
                                f"Expected images matching pattern: set_{current_set_id}_*.* in {content_type}/ folder"
                            )

                        # Use the first available set image (they're already sorted by index)
                        if len(set_images) < 1:
                            raise ValueError(
                                f"Set '{current_set_id}' needs at least 1 image for '{content_type}'"
                            )

                        selected_image_name = set_images[0]
                        content_path = self.base_path / content_type
                        base_image = Image.open(content_path / selected_image_name)

                        # Get settings and generate image with text
                        image_settings = self._get_image_settings(selected_image_name, content_type)
                        text_type = image_settings["base_settings"]["text_type"]

                        image = generate_image(
                            base_image=base_image,
                            text=content,
                            settings=image_settings["text_settings"][text_type],
                            text_type=text_type,
                            colour_index=random.randint(
                                0, len(image_settings["text_settings"][text_type]["colors"]) - 1
                            ),
                        )
                        base_image.close()
                    else:
                        # Use normal random selection
                        image = self._generate_single_image(
                            content_type=content_type,
                            product=product,
                            text=content,
                            used_images=used_images,
                            allow_all_duplicates=allow_all_duplicates,
                        )

                    # Note: Image is already fit to 9:16 frame inside generate_image()
                    # Only fit to frame here for raw images (empty content)
                    if not content:
                        image = self._fit_to_tiktok_frame(image)

                    # Apply slight randomization for metadata/hash uniqueness
                    image = self._randomize_image_data(image)

                    # Save image with MAXIMUM QUALITY (lossless PNG, no compression)
                    image_path = post_path / f"{idx}.png"
                    # PNG compression: 0 = no compression (fastest, largest file, best quality)
                    pnginfo = image.info.get("pnginfo")
                    if pnginfo:
                        image.save(image_path, format="PNG", compress_level=0, optimize=False, pnginfo=pnginfo)
                    else:
                        image.save(image_path, format="PNG", compress_level=0, optimize=False)
                    image.close()
                    logger.debug(
                        f"Saved image {idx} for post {post_num} in variation {variation_num}"
                    )

                gc_post_counter += 1
                if gc_post_counter % 5 == 0:  # Every 5 images
                    gc.collect()  # Force garbage collection

        # Return the actual output path used for reporting
        return output_path

    def _fit_to_tiktok_frame(self, image: Image.Image) -> Image.Image:
        """Place image inside a 1080x1920 (9:16) TikTok frame, scaled to fit and centered"""
        TIKTOK_WIDTH = 1080
        TIKTOK_HEIGHT = 1920

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
            frame.paste(resized, (x, y), resized)
        else:
            frame.paste(resized, (x, y))

        resized.close()
        return frame

    def _randomize_image_data(self, image: Image.Image) -> Image.Image:
        """Add random metadata to image WITHOUT changing any pixels - preserves original quality 100%"""
        from PIL import PngImagePlugin
        import time

        # Create metadata dict with random values (changes file hash without touching pixels)
        metadata = PngImagePlugin.PngInfo()
        metadata.add_text("timestamp", str(time.time()))
        metadata.add_text("random_id", str(random.randint(100000, 999999)))
        metadata.add_text("hash_seed", str(random.random()))

        # Store metadata in image info for saving
        image.info["pnginfo"] = metadata

        return image  # Return UNCHANGED image with only metadata added

    def _generate_single_image(
        self,
        content_type: str,
        product: str,
        text: str,
        used_images: dict,
        allow_all_duplicates: bool,
    ) -> Image.Image:
        """Generate a single image with text

        Args:
            content_type: Type of content (hook, content, cta)
            product: Product name
            text: Text to add to image
            used_images: Tracking dict for duplicate prevention
            allow_all_duplicates: If True, allows 'all' product to be used even for products
                                with prevent_duplicates=true
        """
        logger.debug(f"Generating image for {content_type} - {product}")

        # Get available images
        content_path = self.base_path / content_type
        available_images = self._get_available_images(
            content_type, product, used_images, allow_all_duplicates
        )

        # If no available images and prevent_duplicates is True, reset used images and try again (cycling)
        if not available_images and self._should_prevent_duplicates(content_type, product):
            logger.info(f"All images used for {content_type}/{product}, resetting to cycle through again")
            used_images[content_type][product] = []
            available_images = self._get_available_images(
                content_type, product, used_images, allow_all_duplicates
            )

        if not available_images:
            raise ValueError(f"No available images for {content_type} - {product}")

        # Initialize cycle index for this content_type if not exists
        if content_type not in self.cycle_indices:
            self.cycle_indices[content_type] = 0

        # Select image using cycling (round-robin) instead of random
        current_index = self.cycle_indices[content_type]
        selected_image = available_images[current_index % len(available_images)]

        # Increment cycle index for next time
        self.cycle_indices[content_type] = (current_index + 1) % len(available_images)

        if self._should_prevent_duplicates(content_type, product):
            used_images[content_type][product].append(selected_image)

        # Get image settings
        image_settings = self._get_image_settings(content_type, product, selected_image)
        text_type = image_settings["base_settings"]["default_text_type"]

        # Generate image
        logger.debug(f"Using image {selected_image} with text type {text_type}")
        return generate_image(
            settings=image_settings,
            text_type=text_type,
            colour_index=random.randint(
                0, len(image_settings["text_settings"][text_type]["colors"]) - 1
            ),
            image_path=str(content_path / selected_image),
            text=text,
        )

    def _get_available_images(
        self,
        content_type: str,
        product: str,
        used_images: dict,
        allow_all_duplicates: bool,
    ) -> List[str]:
        """Get list of available images for content type and product with improved duplicate handling"""
        logger.debug(f"\n=== Getting Available Images ===")
        logger.debug(f"Content Type: {content_type}")

        # Strip whitespace from product name
        product = product.strip() if product else product
        logger.debug(f"Product (after stripping whitespace): {product}")

        # Rest of the method remains the same
        all_images = self.metadata.data["structure"][content_type]["images"]
        logger.debug(f"Found images in metadata: {all_images}")

        if product == "all":
            logger.debug("Processing 'all' product case - returning ALL images in folder")
            # "all" means use ANY image in this content type, regardless of product assignment
            available = all_images.copy()
            logger.debug(f"Using all {len(available)} images from {content_type}")

            # For "all" product, we don't filter by product assignment
            # This allows cycling through ALL images in the folder

        else:
            logger.debug(f"Processing specific product: {product}")

            available = [
                img
                for img in all_images
                if self.metadata.data["images"][img]["product"] == product
            ]

            if self._should_prevent_duplicates(content_type, product):
                logger.debug(f"Applying duplicate prevention for {product}")
                logger.debug(f"Used images: {used_images[content_type][product]}")

                available = [
                    img
                    for img in available
                    if img not in used_images[content_type][product]
                ]

            logger.debug(f"Found {len(available)} available images")

        if not available:
            logger.warning(f"No available images found for {content_type} - {product}")

        return available

    def _should_prevent_duplicates(self, content_type: str, product: str) -> bool:
        """Check if duplicates should be prevented for this content type and product"""
        logger.debug(f"\n=== Checking Duplicate Prevention ===")
        logger.debug(f"Content Type: {content_type}")

        # Strip whitespace from product name
        product = product.strip() if product else product
        logger.debug(f"Product (after stripping whitespace): {product}")

        logger.debug(
            f"Products in metadata: {self.metadata.data['products'][content_type]}"
        )

        for prod_info in self.metadata.data["products"][content_type]:
            if prod_info["name"] == product:
                should_prevent = prod_info["prevent_duplicates"]
                logger.debug(f"Found product. Prevent duplicates: {should_prevent}")
                return should_prevent

        logger.debug("Product not found in metadata")
        return False

    def _get_image_settings(
        self, content_type: str, product: str, image_path: str
    ) -> dict:
        """Get settings for specific image, falling back through hierarchy as needed"""
        logger.debug(f"\n=== Getting Image Settings ===")
        logger.debug(f"Content Type: {content_type}")
        logger.debug(f"Product: {product}")
        logger.debug(f"Image path: {image_path}")

        # Extract filename from path
        image_name = Path(image_path).name
        logger.debug(f"Image name: {image_name}")

        try:
            # Get image metadata
            image_data = self.metadata.data["images"][image_name]
            settings_source = image_data["settings_source"]

            # Handle different settings sources
            if settings_source == "default":
                # Import default template for default settings
                from content_manager.settings.settings_constants import DEFAULT_TEMPLATE
                import json

                logger.debug(f"Loading default template from: {DEFAULT_TEMPLATE}")
                try:
                    with open(DEFAULT_TEMPLATE) as f:
                        return json.load(f)
                except (IOError, json.JSONDecodeError) as e:
                    logger.error(f"Failed to load default template: {str(e)}")
                    raise

            elif settings_source == "custom":
                if image_data["settings"] is None:
                    raise ValueError(
                        f"Image {image_name} has custom settings_source but no settings defined"
                    )
                return image_data["settings"]

            elif settings_source == "content":
                # Get content-level settings
                content_settings = self.metadata.data["settings"][content_type][
                    "content"
                ]
                if content_settings is None:
                    raise ValueError(
                        f"No content-level settings defined for {content_type}"
                    )
                return content_settings

            elif settings_source == "product":
                # Look for product settings
                for group, settings in self.metadata.data["settings"][
                    content_type
                ].items():
                    if group != "content":  # Skip content settings
                        products = {p.strip() for p in group[1:-1].split(",")}
                        if product in products and settings is not None:
                            return settings
                raise ValueError(
                    f"No product settings found for {product} in {content_type}"
                )

            else:
                raise ValueError(f"Invalid settings_source: {settings_source}")

        except Exception as e:
            logger.error(f"Error getting settings for {image_name}: {str(e)}")
            raise ValueError(f"Failed to get settings for {image_name}: {str(e)}")

    def _get_default_settings(self) -> dict:
        """Load default settings template for sets mode"""
        from content_manager.settings.settings_constants import DEFAULT_TEMPLATE
        import json

        logger.debug(f"Loading default template for sets mode: {DEFAULT_TEMPLATE}")
        try:
            with open(DEFAULT_TEMPLATE) as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load default template: {str(e)}")
            raise
