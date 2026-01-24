# Quick Usage Guide

## Adding New Images

When you add new images to folders (slide1/, slide2/, etc.):

### Option 1: Delete metadata and reload
```bash
rm sample_content/metadata.json
# Then refresh browser
```

### Option 2: Use Python
```python
from main import SlideManager

sm = SlideManager()
sm.load('sample_content', strict=True)  # This regenerates metadata
```

### Option 3: Restart Streamlit
```bash
# Kill the current process
# Re-run: python3 -m streamlit run interface/main.py -- sample_content ...
```

## Manual Text Placement

Currently text position is controlled by:
- **Margins**: `margin_top`, `margin_bottom`, `margin_left`, `margin_right` (pixels)
- **Position**: `top`, `center`, `bottom`

### Current Workflow:
1. Select image in Streamlit
2. Choose a caption
3. Click "Generate Preview"
4. Adjust margin sliders until text is where you want
5. Preview updates in real-time

### Coming Soon: Click-to-Place
A visual interface where you can:
- Click on image to set text position
- Drag to define text area
- See bounding box overlay

## Image Sets Usage

### Setup
1. Name images with pattern: `set_{id}_{index}.ext`
   ```
   slide1/set_beach_1.png
   slide2/set_beach_1.png
   slide1/set_promo_1.jpg
   slide2/set_promo_1.jpg
   ```

2. Add `set_id` column to CSV:
   ```csv
   set_id,product_slide1,slide1,product_slide2,slide2
   set_beach,beach,Hook text,beach,CTA text
   "",all,Regular,all,Normal CTA
   ```

3. Generate in Streamlit UI using "Generate All Variations" button

## Generating Slides

### Via Streamlit (NEW!)
1. Open http://localhost:8502
2. Scroll to "🎬 Batch Generation"
3. Set variations (1-10)
4. Click "Generate All Variations"
5. Click "Open Output Folder" to see results

### Via Python
```python
from main import SlideManager

sm = SlideManager()
sm.load('sample_content', strict=True)
sm.generate(variations=2)
```

## Troubleshooting

### Images not showing
- Delete `metadata.json`
- Reload in Streamlit

### Preview not working
- Check image is selected
- Check caption exists
- Check console for errors

### Generation fails
- Run validation: `sm.validate(strict=True)`
- Check for missing images
- Ensure CSV format is correct
