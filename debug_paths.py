import sys
import os
from pathlib import Path

# Add the current directory to sys.path to emulate the app environment
sys.path.append(os.getcwd())

try:
    from content_manager.settings.settings_constants import DEFAULT_TEMPLATE
    print(f"DEFAULT_TEMPLATE resolved to: {DEFAULT_TEMPLATE}")
    print(f"Exists: {DEFAULT_TEMPLATE.exists()}")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
