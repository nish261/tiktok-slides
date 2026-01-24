#!/usr/bin/env python3
"""
Easy TikTok Slide Generator
Upload photos, add text, generate video
"""

import streamlit as st
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import tempfile

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
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #ee0979 0%, #ff6a00 100%);
        color: white;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-size: 1.1rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🎬 TikTok Slide Generator</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #666;">Upload photos, add text, generate video</p>', unsafe_allow_html=True)

# Create output directory
OUTPUT_DIR = Path("output_videos")
OUTPUT_DIR.mkdir(exist_ok=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")

    duration = st.slider(
        "Duration per slide (seconds)",
        min_value=1,
        max_value=10,
        value=3
    )

    # Video format
    video_format = st.radio(
        "Video Format",
        ["Vertical (9:16) - TikTok/Reels", "Horizontal (16:9) - YouTube"],
        index=0
    )

    is_vertical = "Vertical" in video_format

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
st.header("2️⃣ Add Text for Each Slide (Optional)")

slide_texts = []
if uploaded_files:
    for idx, file in enumerate(uploaded_files):
        text = st.text_area(
            f"Text for slide {idx + 1} ({file.name})",
            placeholder=f"Enter caption or text for slide {idx + 1}... (optional)",
            key=f"text_{idx}",
            height=80
        )
        slide_texts.append(text)

# Step 3: Generate Video
st.markdown("---")
st.header("3️⃣ Generate Video")

if uploaded_files:
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button("🎬 Generate Video", key="gen_btn"):

            progress = st.progress(0)
            status = st.empty()

            try:
                from moviepy.editor import ImageClip, TextClip, CompositeVideoClip, concatenate_videoclips
                import numpy as np

                status.text("💾 Processing images...")
                progress.progress(10)

                clips = []

                for idx, (file, text) in enumerate(zip(uploaded_files, slide_texts)):
                    status.text(f"🎨 Creating slide {idx+1}/{len(uploaded_files)}...")
                    progress_val = 10 + int((idx / len(uploaded_files)) * 70)
                    progress.progress(progress_val)

                    # Load image
                    img = Image.open(file)

                    # Resize to target dimensions
                    if is_vertical:
                        target_width, target_height = 1080, 1920  # 9:16
                    else:
                        target_width, target_height = 1920, 1080  # 16:9

                    # Resize and crop to fill frame
                    img_ratio = img.width / img.height
                    target_ratio = target_width / target_height

                    if img_ratio > target_ratio:
                        # Image is wider, fit to height
                        new_height = target_height
                        new_width = int(img.width * (new_height / img.height))
                    else:
                        # Image is taller, fit to width
                        new_width = target_width
                        new_height = int(img.height * (new_width / img.width))

                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                    # Crop to center
                    left = (img.width - target_width) // 2
                    top = (img.height - target_height) // 2
                    img = img.crop((left, top, left + target_width, top + target_height))

                    # Convert to numpy array for MoviePy
                    img_array = np.array(img)

                    # Create video clip from image
                    clip = ImageClip(img_array, duration=duration)

                    # Add text overlay if provided
                    if text.strip():
                        txt_clip = TextClip(
                            text,
                            fontsize=70 if is_vertical else 60,
                            color='white',
                            font='Arial-Bold',
                            size=(target_width - 100, None),
                            method='caption',
                            align='center'
                        ).set_position(('center', 'top')).set_duration(duration)

                        # Add background to text
                        clip = CompositeVideoClip([clip, txt_clip])

                    clips.append(clip)

                status.text("🎬 Combining slides into video...")
                progress.progress(85)

                # Concatenate all clips
                final_video = concatenate_videoclips(clips, method="compose")

                # Save video
                output_filename = f"tiktok_slides_{len(uploaded_files)}_slides.mp4"
                output_path = OUTPUT_DIR / output_filename

                status.text("💾 Saving video...")
                progress.progress(90)

                final_video.write_videofile(
                    str(output_path),
                    fps=24,
                    codec='libx264',
                    audio_codec='aac',
                    logger=None
                )

                # Clean up
                for clip in clips:
                    clip.close()
                final_video.close()

                progress.progress(100)
                status.text("🎉 Video generated!")

                # Display results
                st.success("✅ Video generated successfully!")

                st.markdown("### 📊 Summary")
                st.write(f"- **Total slides:** {len(uploaded_files)}")
                st.write(f"- **Duration:** {len(uploaded_files) * duration} seconds")
                st.write(f"- **Format:** {video_format}")
                st.write(f"- **Resolution:** {'1080x1920' if is_vertical else '1920x1080'}")

                # Show video
                st.markdown("### 🎥 Your Video")
                st.video(str(output_path))

                # Download button
                with open(output_path, 'rb') as f:
                    st.download_button(
                        label="⬇️ Download Video",
                        data=f.read(),
                        file_name=output_filename,
                        mime="video/mp4"
                    )

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
else:
    st.info("👆 Upload photos to get started")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem 0;'>
    <p>Easy TikTok Slide Generator</p>
    <p style='font-size: 0.9rem;'>Upload → Add Text → Generate</p>
</div>
""", unsafe_allow_html=True)
