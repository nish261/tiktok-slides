import json
from pathlib import Path

metadata_path = Path("tiktok-slides/sample_content/metadata.json")

if metadata_path.exists():
    with open(metadata_path, 'r') as f:
        data = json.load(f)
    
    print(f"Resetting metadata for {len(data.get('images', {}))} images...")
    
    # Force reset all images to default settings
    for img_name, img_data in data.get("images", {}).items():
        img_data["settings_source"] = "default"
        img_data["settings"] = None
        # Ensure product is valid or 'all'
        if not img_data.get("product"):
            img_data["product"] = "all"

    with open(metadata_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print("Metadata reset to clean state.")
else:
    print("Metadata file not found!")
