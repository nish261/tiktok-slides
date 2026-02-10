"""DEAD SIMPLE TikTok Slides Generator - IT JUST WORKS"""
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from main import SlideManager
from content_manager.captions import CaptionsHelper
from generation.generate import Generator
import subprocess

st.set_page_config(page_title="TikTok Slides", layout="wide", page_icon="🎬")

# Initialize
if "base_path" not in st.session_state:
    st.session_state.base_path = Path("sample_content")
if "loaded" not in st.session_state:
    st.session_state.loaded = False
if "manager" not in st.session_state:
    st.session_state.manager = None

# Load content
if not st.session_state.loaded:
    try:
        sm = SlideManager(log_level='INFO')
        sm.load(str(st.session_state.base_path), strict=False)
        st.session_state.manager = sm
        st.session_state.loaded = True
    except Exception as e:
        st.error(f"Load failed: {e}")
        st.stop()

sm = st.session_state.manager

# HEADER
st.title("🎬 TikTok Slides Generator")

# STATS
col1, col2, col3 = st.columns(3)
content_types = list(sm.metadata.data.get("content_types", []))

with col1:
    st.metric("📁 Total Images", len(sm.metadata.data.get('images', {})))
with col2:
    for ct in content_types:
        count = len(sm.metadata.data['structure'][ct]['images'])
        st.metric(f"📁 {ct}", f"{count} images")
with col3:
    captions_path = sm.base_path / "captions.csv"
    if captions_path.exists():
        with open(captions_path, 'r') as f:
            rows = sum(1 for line in f) - 1
        st.metric("📝 Captions", f"{rows} rows")

st.markdown("---")

# SIMPLE TABS
tab1, tab2 = st.tabs(["🎬 GENERATE", "⚙️ SETTINGS"])

# TAB 1: GENERATE
with tab1:
    st.header("Generate Slides")

    col_a, col_b = st.columns(2)

    with col_a:
        variations = st.number_input("How many variations?", 1, 20, 3)

    with col_b:
        allow_dupes = st.checkbox("Allow duplicate images", False)

    st.markdown("")

    if st.button("🎬 GENERATE NOW", type="primary", use_container_width=True):
        try:
            with st.spinner(f"Generating {variations} variations..."):
                # Load captions
                captions_data = CaptionsHelper.get_captions(
                    sm.base_path / "captions.csv",
                    content_types=set(content_types),
                    products=sm.content_handler.products,
                    separator=","
                )

                # Generate
                generator = Generator(sm.base_path, sm.metadata, captions_data)
                output_path = generator.generate(variations, allow_dupes)

                st.success(f"✅ Done! Generated {variations} variations")
                st.balloons()

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📂 Open Output"):
                        subprocess.run(["open", str(output_path)])
                with col2:
                    st.code(f"python3 upload_to_gdrive.py {output_path}")

        except Exception as e:
            st.error(f"Failed: {e}")
            st.exception(e)

# TAB 2: SETTINGS
with tab2:
    st.header("Settings")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("📂 Folders")
        if st.button("Open slide1/"):
            subprocess.run(["open", str(sm.base_path / "slide1")])
        if st.button("Open slide2/"):
            subprocess.run(["open", str(sm.base_path / "slide2")])
        if st.button("Open captions.csv"):
            subprocess.run(["open", str(sm.base_path / "captions.csv")])

    with col2:
        st.subheader("🔄 Refresh")
        st.write("Added new images?")
        if st.button("Reload Everything"):
            (sm.base_path / "metadata.json").unlink(missing_ok=True)
            st.session_state.loaded = False
            st.rerun()

    with col3:
        st.subheader("📊 Stats")
        for ct in content_types:
            count = len(sm.metadata.data['structure'][ct]['images'])
            st.write(f"**{ct}:** {count} images")

st.markdown("---")
st.caption("Add images to folders → Edit captions.csv → Generate → Profit")
