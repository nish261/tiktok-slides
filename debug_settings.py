import sys
from pathlib import Path
import json

# Setup paths
ROOT = Path.cwd() / "tiktok-slides"
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

try:
    from content_manager.metadata.metadata_editor import MetadataEditor
    from content_manager.settings.settings_constants import DEFAULT_TEMPLATE
    
    print(f"Checking template at: {DEFAULT_TEMPLATE}")
    
    if DEFAULT_TEMPLATE.exists():
        print("Template file exists.")
        with open(DEFAULT_TEMPLATE) as f:
            data = json.load(f)
            print("Successfully loaded JSON.")
            print(f"Keys: {list(data.keys())}")
    else:
        print("TEMPLATE FILE MISSING!")

    # Test metadata editor settings retrieval
    # Mock metadata dict
    mock_meta = {
        "content_types": ["hook", "cta"],
        "products": {},
        "images": {},
        "settings": {}
    }
    editor = MetadataEditor(mock_meta)
    settings = editor.get_settings("default")
    print("Editor retrieved settings successfully.")
    
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
