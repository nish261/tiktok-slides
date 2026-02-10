"""TikTok Slides Generator - WITH CREATIVE CONTROLS"""
import streamlit as st
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main import SlideManager
from content_manager.captions import CaptionsHelper
from generation.generate import Generator
from text.plain_text import draw_plain_image
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
st.markdown("### With Full Creative Controls")

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

# Show quick stats
col_stat1, col_stat2, col_stat3 = st.columns(3)
with col_stat1:
    st.metric("Total Images", len(sm.metadata.data.get('images', {})))
with col_stat2:
    captions_path = sm.base_path / "captions.csv"
    if captions_path.exists():
        with open(captions_path, 'r') as f:
            num_rows = sum(1 for line in f) - 1
        st.metric("Caption Rows", num_rows)
    else:
        st.metric("Caption Rows", "No CSV")
with col_stat3:
    content_types = list(sm.metadata.data.get("content_types", []))
    st.metric("Folders", len(content_types))

st.markdown("---")

# TABS
tab1, tab2, tab3 = st.tabs(["🎨 Creative Editor", "🎬 Generate", "⚙️ Settings"])

# TAB 1: CREATIVE EDITOR
with tab1:
    st.header("🎨 Creative Editor - Preview & Control Text")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("📸 Select Image")

        # Content type selection
        content_type = st.selectbox("Folder", content_types, key="preview_content_type")

        # Get images for selected content type
        images = sm.metadata.data["structure"][content_type]["images"]
        selected_image = st.selectbox("Image", images, key="preview_image")

        # Show original image
        if selected_image:
            image_path = sm.base_path / content_type / selected_image
            st.image(str(image_path), caption="Original", use_column_width=True)

    with col_right:
        st.subheader("✏️ Text & Style")

        # Test text input
        test_text = st.text_area("Text to add", "Your text here\nline 2", height=100)

        st.markdown("---")
        st.markdown("**📐 Position**")

        col_pos1, col_pos2 = st.columns(2)
        with col_pos1:
            vertical_pos = st.slider("Vertical (0=top, 1=bottom)", 0.0, 1.0, 0.5, 0.01)
        with col_pos2:
            horizontal_pos = st.slider("Horizontal (0=left, 1=right)", 0.0, 1.0, 0.5, 0.01)

        st.markdown("---")
        st.markdown("**🎨 Style**")

        col_style1, col_style2 = st.columns(2)
        with col_style1:
            font_size = st.slider("Font Size", 20, 150, 70, 5)
            outline_width = st.slider("Outline Width", 0, 15, 3, 1)
        with col_style2:
            text_color = st.color_picker("Text Color", "#FFFFFF")
            outline_color = st.color_picker("Outline Color", "#000000")

        st.markdown("---")
        st.markdown("**📏 Margins (spacing from edges)**")

        col_margin1, col_margin2 = st.columns(2)
        with col_margin1:
            margin_top = st.slider("Top Margin", 0, 500, 100, 10)
            margin_left = st.slider("Left Margin", 0, 300, 50, 10)
        with col_margin2:
            margin_bottom = st.slider("Bottom Margin", 0, 500, 100, 10)
            margin_right = st.slider("Right Margin", 0, 300, 50, 10)

        st.markdown("---")

        if st.button("🔍 PREVIEW", type="primary", use_container_width=True):
            with st.spinner("Generating preview..."):
                try:
                    # Load image
                    img = Image.open(image_path)
                    width, height = img.size

                    # Calculate pixel margins
                    margins = {
                        "top": margin_top,
                        "bottom": margin_bottom,
                        "left": margin_left,
                        "right": margin_right
                    }

                    # Calculate max width
                    max_width = width - margin_left - margin_right

                    # Get font path
                    font_path = str(Path(__file__).parent / "assets" / "fonts" / "tiktokfont.ttf")

                    # Generate preview using plain text renderer
                    result = draw_plain_image(
                        image=img,
                        width=width,
                        height=height,
                        text=test_text,
                        font_size=font_size,
                        font_path=font_path,
                        max_width=max_width,
                        width_center_position=horizontal_pos,
                        height_center_position=vertical_pos,
                        margins=margins,
                        text_color=text_color,
                        outline_color=outline_color,
                        outline_width=outline_width
                    )

                    # Save and display
                    preview_path = sm.base_path / "preview_temp.png"
                    result.save(preview_path)

                    st.image(str(preview_path), caption="✨ Preview", use_column_width=True)
                    st.success("✅ Preview generated!")

                    # Save settings reminder
                    st.info("💾 **To use these settings:** Update your default template in settings, or generate with current defaults")

                except Exception as e:
                    st.error(f"❌ Preview failed: {str(e)}")
                    with st.expander("Debug"):
                        st.exception(e)

# TAB 2: GENERATE
with tab2:
    st.header("🎬 Generate All Slides")

    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("""
        **How it works:**
        1. Reads captions from `captions.csv`
        2. Randomly picks images from your folders
        3. Adds text to slide1 (slide2 has no text if empty in CSV)
        4. Creates variations with slightly different metadata
        5. Saves to `output/variation1/`, `variation2/`, etc.
        """)

    with col2:
        st.markdown("**Your Folders:**")
        for ct in content_types:
            img_count = len(sm.metadata.data['structure'][ct]['images'])
            st.write(f"📁 {ct}: **{img_count}** images")

    st.markdown("---")

    # Generation settings
    col_gen1, col_gen2 = st.columns([2, 2])

    with col_gen1:
        variations = st.number_input(
            "🔢 Number of Variations",
            min_value=1,
            max_value=20,
            value=3,
            help="How many different sets to create"
        )

    with col_gen2:
        allow_dupes = st.checkbox(
            "🔄 Allow Duplicate Images",
            value=False,
            help="Use same image multiple times if needed"
        )

    # Generate button
    st.markdown("")
    if st.button("🎬 GENERATE SLIDES", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            status_text.text("Loading captions...")
            progress_bar.progress(0.2)

            # Load captions
            captions_data = CaptionsHelper.get_captions(
                sm.base_path / "captions.csv",
                content_types=set(sm.metadata.data["content_types"]),
                products=sm.content_handler.products,
                separator=","
            )

            num_posts = len(captions_data["captions"])
            status_text.text(f"Generating {variations} variations × {num_posts} posts...")
            progress_bar.progress(0.4)

            # Generate
            generator = Generator(sm.base_path, sm.metadata, captions_data)
            output_path = generator.generate(variations, allow_dupes)

            progress_bar.progress(1.0)
            status_text.text("✅ Complete!")

            st.success(f"🎉 Generated {variations} variations × {num_posts} posts = **{variations * num_posts} total slides**!")
            st.balloons()

            # Show output
            st.markdown(f"**📂 Saved to:** `{output_path}`")

            col_btn1, col_btn2, col_btn3 = st.columns(3)

            with col_btn1:
                if st.button("📂 Open Output Folder"):
                    subprocess.run(["open", str(output_path)])

            with col_btn2:
                if st.button("📤 Upload to Google Drive"):
                    st.info("Run: `python3 upload_to_gdrive.py sample_content/output`")

            with col_btn3:
                if st.button("🔄 Regenerate"):
                    st.rerun()

        except Exception as e:
            status_text.text("❌ Failed")
            st.error(f"**Error:** {str(e)}")
            with st.expander("🔍 Debug"):
                st.exception(e)

# TAB 3: SETTINGS
with tab3:
    st.header("⚙️ Settings & Management")

    col_mgmt1, col_mgmt2, col_mgmt3 = st.columns(3)

    with col_mgmt1:
        st.subheader("📁 Quick Access")

        if st.button("📂 Open slide1/ folder"):
            subprocess.run(["open", str(sm.base_path / "slide1")])

        if st.button("📂 Open slide2/ folder"):
            subprocess.run(["open", str(sm.base_path / "slide2")])

        if st.button("📝 Open captions.csv"):
            subprocess.run(["open", str(sm.base_path / "captions.csv")])

    with col_mgmt2:
        st.subheader("🔄 Refresh")

        st.markdown("Added new images?")
        if st.button("🔄 Reload Everything"):
            metadata_file = sm.base_path / "metadata.json"
            if metadata_file.exists():
                metadata_file.unlink()
            st.session_state.loaded = False
            st.rerun()

    with col_mgmt3:
        st.subheader("📊 Current Stats")

        st.write(f"**Total images:** {len(sm.metadata.data.get('images', {}))}")
        for ct in content_types:
            img_count = len(sm.metadata.data['structure'][ct]['images'])
            st.write(f"**{ct}:** {img_count} images")

    st.markdown("---")
    st.markdown("### 📋 CSV Format Reference")

    st.code("""product_slide1,slide1,product_slide2,slide2
all,Text for slide 1,all,""
all,More text,all,""

# Each row = 1 post
# 'all' = random image
# Empty "" = no text overlay""", language="csv")

# Footer
st.markdown("---")
st.caption("💡 Preview text style → Generate slides → Upload to Drive")
