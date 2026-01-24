"""Simple, easy-to-use interface for TikTok Slides Generator"""
import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main import SlideManager
from content_manager.captions import CaptionsHelper
from generation.generate import Generator
from PIL import Image
import subprocess

st.set_page_config(page_title="TikTok Slides Generator", layout="wide", page_icon="🎬")

# Initialize session state
if "base_path" not in st.session_state:
    st.session_state.base_path = Path("sample_content")
if "loaded" not in st.session_state:
    st.session_state.loaded = False
if "manager" not in st.session_state:
    st.session_state.manager = None

def load_content():
    """Load content and metadata"""
    try:
        sm = SlideManager(log_level='INFO')
        result = sm.load(str(st.session_state.base_path), strict=False)
        if result:
            st.session_state.manager = sm
            st.session_state.loaded = True
            return True, f"✅ Loaded {len(sm.metadata.data.get('images', {}))} images"
        else:
            return False, "❌ Failed to load content"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

# Header
st.title("🎬 TikTok Slides Generator")
st.markdown("### Easy slide creation for TikTok, Instagram Reels & YouTube Shorts")

# Load content if not loaded
if not st.session_state.loaded:
    with st.spinner("Loading content..."):
        success, message = load_content()
        if success:
            st.success(message)
        else:
            st.error(message)
            st.stop()

sm = st.session_state.manager

# Main tabs
tab1, tab2, tab3 = st.tabs(["📸 1. Preview & Test", "🎬 2. Generate Slides", "⚙️ 3. Settings"])

# TAB 1: PREVIEW & TEST
with tab1:
    st.header("Step 1: Preview Your Slides")
    st.markdown("**Test how text looks on your images before generating**")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📁 Select Image")

        # Content type selection
        content_types = list(sm.metadata.data.get("content_types", []))
        content_type = st.selectbox("Folder", content_types, key="preview_content_type")

        # Get images for selected content type
        images = sm.metadata.data["structure"][content_type]["images"]
        selected_image = st.selectbox("Image", images, key="preview_image")

        # Show original image
        if selected_image:
            image_path = sm.base_path / content_type / selected_image
            st.image(str(image_path), caption=f"{content_type}/{selected_image}", use_column_width=True)

    with col2:
        st.subheader("✏️ Test Text")

        # Load captions
        captions_path = sm.base_path / "captions.csv"
        if captions_path.exists():
            captions_data = CaptionsHelper.get_captions(
                captions_path,
                content_types=set(content_types),
                products=sm.content_handler.products,
                separator=","
            )

            # Get captions for this content type
            all_captions = []
            for row in captions_data["captions"]:
                for i, header in enumerate(captions_data["headers"]):
                    if header == content_type and i < len(row):
                        if row[i]:
                            all_captions.append(row[i])

            if all_captions:
                test_text = st.selectbox("Choose caption to test", all_captions, key="test_caption")
            else:
                test_text = st.text_input("Type custom text", "Your text here", key="custom_test")
        else:
            test_text = st.text_input("Type custom text", "Your text here", key="custom_test2")

        st.markdown("---")
        st.markdown("**Text Position**")

        col_margin1, col_margin2 = st.columns(2)
        with col_margin1:
            margin_top = st.slider("Top spacing", 0, 500, 100, key="margin_top")
            margin_left = st.slider("Left spacing", 0, 200, 50, key="margin_left")
        with col_margin2:
            margin_bottom = st.slider("Bottom spacing", 0, 500, 100, key="margin_bottom")
            margin_right = st.slider("Right spacing", 0, 200, 50, key="margin_right")

        if st.button("🔍 Preview Text on Image", type="primary", use_container_width=True):
            with st.spinner("Generating preview..."):
                try:
                    from text.generate_image import generate_image

                    # Get image dimensions for margin calculations
                    img = Image.open(image_path)
                    img_width, img_height = img.size

                    # Build settings in correct format
                    settings = {
                        "text_settings": {
                            "plain": {
                                "font_size": 70,
                                "font": "assets.fonts.tiktokfont.ttf",
                                "style_type": "outline_width",
                                "style_value": 3,
                                "colors": [{"text": "#FFFFFF", "outline": "#000000"}],
                                "margins": {
                                    "top": margin_top / img_height,
                                    "bottom": margin_bottom / img_height,
                                    "left": margin_left / img_width,
                                    "right": margin_right / img_width
                                },
                                "position": {
                                    "vertical": [0.5, 0.5],
                                    "horizontal": [0.5, 0.5],
                                    "vertical_jitter": 0.0,
                                    "horizontal_jitter": 0.0
                                }
                            }
                        }
                    }

                    # Generate - pass image_path as string, not Image object
                    result_img = generate_image(settings, "plain", 0, str(image_path), test_text)

                    # Save preview
                    preview_path = sm.base_path / "preview_temp.png"
                    result_img.save(preview_path)

                    st.image(str(preview_path), caption="Preview", use_column_width=True)
                    st.success("✅ Preview generated!")

                except Exception as e:
                    st.error(f"❌ Preview failed: {str(e)}")

# TAB 2: GENERATE SLIDES
with tab2:
    st.header("Step 2: Generate All Slides")
    st.markdown("**Batch generate slides from your CSV captions**")

    col_gen1, col_gen2, col_gen3 = st.columns([2, 1, 1])

    with col_gen1:
        st.info("""
        **What happens when you generate:**
        1. Reads all captions from `captions.csv`
        2. Adds text to images automatically
        3. Creates multiple variations
        4. Saves to `output/variation1/`, `output/variation2/`, etc.
        """)

    with col_gen2:
        variations = st.number_input(
            "Number of variations",
            min_value=1,
            max_value=10,
            value=2,
            help="How many different sets to create"
        )

    with col_gen3:
        allow_dupes = st.checkbox(
            "Allow duplicate images",
            value=False,
            help="Use same image multiple times if needed"
        )

    st.markdown("---")

    if st.button("🎬 Generate All Slides", type="primary", use_container_width=True):
        with st.spinner(f"Generating {variations} variations..."):
            try:
                # Load captions
                captions_data = CaptionsHelper.get_captions(
                    sm.base_path / "captions.csv",
                    content_types=set(sm.metadata.data["content_types"]),
                    products=sm.content_handler.products,
                    separator=","
                )

                # Generate
                generator = Generator(sm.base_path, sm.metadata, captions_data)
                output_path = generator.generate(variations, allow_dupes)

                st.success(f"✅ Generated {variations} variations!")
                st.balloons()

                # Show output location
                st.markdown(f"**Saved to:** `{output_path}`")

                # Open folder button
                if st.button("📂 Open Output Folder"):
                    subprocess.run(["open", str(output_path)])

            except Exception as e:
                st.error(f"❌ Generation failed: {str(e)}")
                st.exception(e)

# TAB 3: SETTINGS
with tab3:
    st.header("Step 3: Advanced Settings")

    col_set1, col_set2 = st.columns(2)

    with col_set1:
        st.subheader("📂 Content Management")

        # Refresh metadata
        st.markdown("**Add new images?** Click refresh after adding files to folders")
        if st.button("🔄 Refresh & Reload", use_container_width=True):
            metadata_file = sm.base_path / "metadata.json"
            if metadata_file.exists():
                metadata_file.unlink()
            st.session_state.loaded = False
            st.rerun()

        # Show stats
        st.markdown("---")
        st.markdown("**Current Content:**")
        st.write(f"- Total images: {len(sm.metadata.data.get('images', {}))}")
        st.write(f"- Content types: {', '.join(sm.metadata.data.get('content_types', []))}")

        # Show images per type
        for ct in sm.metadata.data.get('content_types', []):
            img_count = len(sm.metadata.data['structure'][ct]['images'])
            st.write(f"- {ct}: {img_count} images")

    with col_set2:
        st.subheader("📝 CSV Format")

        st.markdown("""
        **Your captions.csv format:**
        ```csv
        product_slide1,slide1,product_slide2,slide2
        all,Hook text here,all,CTA text here
        all,Another hook,all,Another CTA
        ```

        **For image sets:**
        ```csv
        set_id,product_slide1,slide1,product_slide2,slide2
        set_beach,all,Beach hook,all,Beach CTA
        "",all,Normal hook,all,Normal CTA
        ```

        **Tips:**
        - Each row = one post
        - `all` = use any image from folder
        - Set images: name like `set_beach_1.png`
        """)

# Footer
st.markdown("---")
st.markdown("**Quick Help:** Add images to folders → Refresh → Preview → Generate ✨")
