import sys
import os
import subprocess
import time
import json
from pathlib import Path

# Add current directory to python path to allow imports from local modules
sys.path.append(os.getcwd())

from main import SlideManager

print("📂 Opening folders and files for editing...")

# Define paths
sample_content_path = Path("sample_content")
captions_csv = sample_content_path / "captions.csv"
metadata_json = sample_content_path / "metadata.json"

# Open the CSV file in default editor
if captions_csv.exists():
    print(f"   ✓ Opening captions.csv")
    subprocess.Popen(["open", str(captions_csv)])
else:
    print(f"   ⚠ captions.csv not found at {captions_csv}")

# Dynamically open all content type folders based on metadata
if metadata_json.exists():
    try:
        with open(metadata_json, 'r') as f:
            metadata = json.load(f)
            content_types = metadata.get("content_types", [])

        for content_type in content_types:
            folder = sample_content_path / content_type
            if folder.exists() and folder.is_dir():
                print(f"   ✓ Opening {content_type}/ folder")
                subprocess.Popen(["open", str(folder)])
            else:
                print(f"   ⚠ {content_type}/ folder not found at {folder}")
    except Exception as e:
        print(f"   ⚠ Could not read metadata.json: {e}")
        print(f"   ℹ️  Opening default folders instead...")
        # Fallback to common folders if metadata can't be read
        for folder_name in ["hook", "cta", "content", "filler"]:
            folder = sample_content_path / folder_name
            if folder.exists() and folder.is_dir():
                print(f"   ✓ Opening {folder_name}/ folder")
                subprocess.Popen(["open", str(folder)])
else:
    print(f"   ⚠ metadata.json not found, opening default folders...")
    # Fallback to common folders
    for folder_name in ["hook", "cta", "content", "filler"]:
        folder = sample_content_path / folder_name
        if folder.exists() and folder.is_dir():
            print(f"   ✓ Opening {folder_name}/ folder")
            subprocess.Popen(["open", str(folder)])

# Give a moment for folders/files to open
print("\n⏳ Waiting 2 seconds for files to open...")
time.sleep(2)

print("\n🚀 Starting Slide Manager interface...")
print("=" * 50)

# Initialize manager
sm = SlideManager(log_level="INFO")

# Load the sample content
# Since we are running from the 'tiktok-slides' directory, the path is just 'sample_content'
sm.load("sample_content", strict=False, separator=",")

# Open the interface
sm.open_interface()
