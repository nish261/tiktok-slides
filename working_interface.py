"""Simple, working interface for TikTok Slides Generator"""
import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main import SlideManager
from content_manager.captions import CaptionsHelper
from generation.generate import Generator
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

# Show quick stats
col_stat1, col_stat2, col_stat3 = st.columns(3)
with col_stat1:
    st.metric("Total Images", len(sm.metadata.data.get('images', {})))
with col_stat2:
    captions_path = sm.base_path / "captions.csv"
    if captions_path.exists():
        with open(captions_path, 'r') as f:
            num_rows = sum(1 for line in f) - 1  # Subtract header
        st.metric("Caption Rows", num_rows)
    else:
        st.metric("Caption Rows", "No CSV")
with col_stat3:
    content_types = list(sm.metadata.data.get("content_types", []))
    st.metric("Folders", len(content_types))

st.markdown("---")

# Main content - simplified to just generation
st.header("🎬 Generate Your Slides")

col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("""
    **How it works:**
    1. Reads captions from `captions.csv`
    2. Randomly picks images from your slide1/ and slide2/ folders
    3. Adds text to slide1 (slide2 has no text if empty in CSV)
    4. Creates variations with slightly different metadata
    5. Saves to `output/variation1/`, `variation2/`, etc.

    **Each variation** has all your posts with different random image combinations!
    """)

with col2:
    # Show folder contents
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
        help="How many different sets of posts to create (each with all your captions)"
    )

with col_gen2:
    allow_dupes = st.checkbox(
        "🔄 Allow Duplicate Images",
        value=False,
        help="If unchecked, will try to use different images for each post within a variation"
    )

# Big generate button
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
        status_text.text(f"Generating {variations} variations × {num_posts} posts each...")
        progress_bar.progress(0.4)

        # Generate
        generator = Generator(sm.base_path, sm.metadata, captions_data)
        output_path = generator.generate(variations, allow_dupes)

        progress_bar.progress(1.0)
        status_text.text("✅ Generation complete!")

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
        status_text.text("❌ Generation failed")
        st.error(f"**Error:** {str(e)}")

        # Show helpful debug info
        with st.expander("🔍 Debug Info"):
            st.exception(e)
            st.write("**Captions CSV path:**", sm.base_path / "captions.csv")
            st.write("**Base path:**", sm.base_path)
            st.write("**Content types:**", content_types)

# Management section
st.markdown("---")
st.header("⚙️ Settings & Management")

col_mgmt1, col_mgmt2, col_mgmt3 = st.columns(3)

with col_mgmt1:
    st.subheader("📁 File Management")

    if st.button("📂 Open slide1/ folder"):
        subprocess.run(["open", str(sm.base_path / "slide1")])

    if st.button("📂 Open slide2/ folder"):
        subprocess.run(["open", str(sm.base_path / "slide2")])

    if st.button("📝 Open captions.csv"):
        subprocess.run(["open", str(sm.base_path / "captions.csv")])

with col_mgmt2:
    st.subheader("🔄 Refresh")

    st.markdown("Added new images? Click refresh:")
    if st.button("🔄 Reload Everything"):
        metadata_file = sm.base_path / "metadata.json"
        if metadata_file.exists():
            metadata_file.unlink()
        st.session_state.loaded = False
        st.rerun()

with col_mgmt3:
    st.subheader("📋 CSV Format")

    st.markdown("""
    ```csv
    product_slide1,slide1,product_slide2,slide2
    all,Text for slide 1,all,""
    all,More text,all,""
    ```
    - Each row = 1 post
    - `all` = random image
    - Empty `""` = no text overlay
    """)

# Footer
st.markdown("---")
st.caption("💡 TikTok Slides Generator - Add images → Edit CSV → Generate → Upload to Drive")
