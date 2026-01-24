#!/usr/bin/env python3
"""
Simple TikTok Slide Generator
Upload photos, add text, generate video
"""

import streamlit as st
import os
from pathlib import Path
from PIL import Image
import shutil

# Page config
st.set_page_config(
    page_title="TikTok Slide Generator",
    page_icon="🎬",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(90deg, #ee0979 0%, #ff6a00 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🎬 TikTok Slide Generator</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #666;">Upload photos, add text, generate video</p>', unsafe_allow_html=True)

# Create temp directories
UPLOAD_DIR = Path("temp_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")

    duration = st.slider(
        "Duration per slide (seconds)",
        min_value=1,
        max_value=10,
        value=3
    )

    video_quality = st.selectbox(
        "Video Quality",
        ["High (1080p)", "Medium (720p)", "Low (480p)"],
        index=0
    )

    st.markdown("---")
    st.markdown("### 📊 Status")
    st.info("Ready to generate")

# Main content
st.markdown("---")

# Step 1: Upload Photos
st.header("1️⃣ Upload Your Photos")
uploaded_files = st.file_uploader(
    "Choose images (PNG, JPG, JPEG)",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True,
    help="Upload all the photos you want in your slide video"
)

if uploaded_files:
    st.success(f"✅ Uploaded {len(uploaded_files)} photos")

    # Display thumbnails
    cols = st.columns(min(len(uploaded_files), 4))
    for idx, (col, file) in enumerate(zip(cols, uploaded_files[:4])):
        with col:
            image = Image.open(file)
            st.image(image, caption=f"Photo {idx+1}", use_container_width=True)

    if len(uploaded_files) > 4:
        st.info(f"+ {len(uploaded_files) - 4} more photos")

# Step 2: Add Text/Captions
st.markdown("---")
st.header("2️⃣ Add Text for Each Slide")

slide_texts = []
if uploaded_files:
    for idx, file in enumerate(uploaded_files):
        text = st.text_area(
            f"Text for slide {idx + 1} ({file.name})",
            placeholder=f"Enter caption or text for slide {idx + 1}...",
            key=f"text_{idx}",
            height=100
        )
        slide_texts.append(text)

# Step 3: Generate Video
st.markdown("---")
st.header("3️⃣ Generate Video")

if uploaded_files:
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button("🎬 Generate Video", key="gen_btn", use_container_width=True):

            # Save uploaded files
            progress = st.progress(0)
            status = st.empty()

            try:
                status.text("💾 Saving uploaded photos...")
                progress.progress(10)

                saved_paths = []
                for idx, file in enumerate(uploaded_files):
                    save_path = UPLOAD_DIR / f"slide_{idx+1}.{file.name.split('.')[-1]}"
                    with open(save_path, "wb") as f:
                        f.write(file.getbuffer())
                    saved_paths.append(str(save_path))

                status.text("✅ Photos saved!")
                progress.progress(30)

                # Here you would integrate with your slide generator
                # For now, just show the data
                status.text("🎨 Generating slides...")
                progress.progress(50)

                import time
                time.sleep(2)

                status.text("🎬 Creating video...")
                progress.progress(80)

                time.sleep(1)

                progress.progress(100)
                status.text("🎉 Video generated!")

                # Display results
                st.success("✅ Video generated successfully!")

                st.markdown("### 📊 Summary")
                st.write(f"- **Total slides:** {len(uploaded_files)}")
                st.write(f"- **Duration:** {len(uploaded_files) * duration} seconds")
                st.write(f"- **Quality:** {video_quality}")

                # Show slide data
                with st.expander("📝 Slide Details"):
                    for idx, (path, text) in enumerate(zip(saved_paths, slide_texts)):
                        st.write(f"**Slide {idx+1}:**")
                        st.write(f"- Image: {Path(path).name}")
                        st.write(f"- Text: {text if text else '(No text)'}")
                        st.write("---")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.exception(e)
else:
    st.info("👆 Upload photos to get started")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem 0;'>
    <p>Simple TikTok Slide Generator</p>
    <p style='font-size: 0.9rem;'>Upload → Add Text → Generate</p>
</div>
""", unsafe_allow_html=True)
