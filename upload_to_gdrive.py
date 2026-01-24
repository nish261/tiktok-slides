#!/usr/bin/env python3
"""
Auto-upload generated slides to Google Drive
"""
import subprocess
import sys
from pathlib import Path

def upload_to_gdrive(local_path: str, gdrive_folder: str = "TikTok Slides"):
    """
    Upload a folder to Google Drive using rclone

    Args:
        local_path: Path to the folder to upload (e.g., "sample_content/output")
        gdrive_folder: Name of the Google Drive folder to upload to
    """
    local_path = Path(local_path)

    if not local_path.exists():
        print(f"❌ Error: Path {local_path} does not exist")
        return False

    print(f"📤 Uploading {local_path} to Google Drive/{gdrive_folder}...")

    try:
        # Use rclone to copy the folder to Google Drive
        # The "gdrive:" remote must be configured first (see setup instructions below)
        result = subprocess.run([
            "rclone",
            "copy",
            str(local_path),
            f"gdrive:{gdrive_folder}/{local_path.name}",
            "--progress"
        ], check=True, capture_output=False)

        print(f"✅ Successfully uploaded to Google Drive/{gdrive_folder}/{local_path.name}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Upload failed: {e}")
        print("\n💡 Make sure you've configured rclone with Google Drive:")
        print("   Run: rclone config")
        print("   Then follow the prompts to add 'gdrive' as a remote")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 upload_to_gdrive.py <path_to_folder> [gdrive_folder_name]")
        print("Example: python3 upload_to_gdrive.py sample_content/output/variation1")
        sys.exit(1)

    local_path = sys.argv[1]
    gdrive_folder = sys.argv[2] if len(sys.argv) > 2 else "TikTok Slides"

    upload_to_gdrive(local_path, gdrive_folder)
