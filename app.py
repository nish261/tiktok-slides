"""TikTok Slides Generator - Full Interface Launcher"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from main import SlideManager

if __name__ == "__main__":
    sm = SlideManager(log_level='INFO')
    sm.load('sample_content', strict=False)
    sm.open_interface()
