from PIL import Image
import os
import random
import shutil

# Correct paths relative to the tiktok-slides directory
folders = ['sample_content/fact', 'sample_content/proof']

for folder in folders:
    # Clear folder content but keep the folder itself if possible, or recreate
    if os.path.exists(folder):
        shutil.rmtree(folder)
    os.makedirs(folder)
    
    # Generate 5 unique images
    for i in range(5):
        # random color
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        img = Image.new('RGB', (800, 800), color=color)
        img.save(os.path.join(folder, f"gen_{i}.png"))
        print(f"Created {folder}/gen_{i}.png")