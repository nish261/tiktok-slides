from PIL import Image, ImageDraw
import os
import random

folders = ['tiktok-slides/sample_content/fact', 'tiktok-slides/sample_content/proof']

for folder in folders:
    if not os.path.exists(folder):
        continue
    for filename in os.listdir(folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            filepath = os.path.join(folder, filename)
            try:
                img = Image.open(filepath)
                draw = ImageDraw.Draw(img)
                # Draw a tiny 1x1 rectangle with a random color at a random position
                # to change the image hash without visually affecting it much
                x = random.randint(0, img.width - 1)
                y = random.randint(0, img.height - 1)
                color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                draw.point((x, y), fill=color)
                
                img.save(filepath)
                print(f"Modified {filepath}")
            except Exception as e:
                print(f"Failed to modify {filepath}: {e}")
