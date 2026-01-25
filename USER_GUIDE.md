# TikTok Slides Generator - Complete User Guide

Welcome to the TikTok Slides Generator! This tool helps you create professional TikTok carousel posts by combining your images with custom text overlays.

---

## 🚀 Quick Start

### Starting the App

```bash
python3 run_slides_app.py
```

This will:
- Open your content folders (slide1/, slide2/, etc.)
- Open captions.csv for editing
- Launch the web interface at http://localhost:8501

---

## 📁 Folder Structure

```
sample_content/
  ├── slide1/          # Images for first slide
  ├── slide2/          # Images for second slide
  ├── slide3/          # Images for third slide (optional)
  ├── ...              # Up to slide10/
  ├── sets/            # Image sequences (optional)
  │   └── my_set/      # Specific images that stay together
  ├── captions.csv     # Your caption combinations
  ├── metadata.json    # Auto-generated, don't edit manually
  └── prompt/          # Claude AI prompt examples
```

---

## 🖼️ Using the Interface

### Left Panel: Image Selection
1. **Content Type Dropdown** - Select which slide folder (slide1, slide2, etc.)
2. **Product Dropdown** - Filter by product category (default: "all")
3. **Image List** - Click any image to preview and edit

### Middle Panel: Preview
- Shows your selected image with text overlay
- Click image to set caption position visually
- Updates in real-time as you change settings

### Right Panel: Settings

#### Caption Settings
- **Main Caption Text** - Your primary text for this slide
- **Font** - Choose from available fonts (tiktokfont recommended)
- **Font Size** - Adjust text size (default: 50)
- **Text Color** - Pick your text color
- **Style Type** - Choose outline, shadow, or background
- **Style Value** - Thickness/intensity of the effect

#### Multi-Caption Mode
- **Enable Multi-caption** - Add a second independent caption
- **Extra Captions Text** - Type your second caption (one per line)
- **Caption 2 Settings** - Completely separate controls for:
  - Font, size, color
  - Position (vertical/horizontal)
  - Margins
  - Style/effects

#### Position Controls
- **📍 Caption 1 (Main)** - Click to set position by clicking preview image
- **📍 Caption 2 (Extra)** - Click to set position for second caption
- **Sliders** - Fine-tune vertical/horizontal position
- **Margins** - Add padding (top, bottom, left, right)

#### Buttons
- **Generate Preview** - Apply settings and see result
- **Apply to All Slides in 'slideX'** - Copy settings to all images in current folder
- **Reset Preview** - Clear settings and start over

---

## 📝 Creating Captions

### Method 1: Simple CSV (2 Slides)

**File:** `sample_content/captions.csv`

```csv
product_slide1,slide1,product_slide2,slide2
all,Stop scrolling,all,Link in bio
all,5 tips you need,all,Follow for more
all,This changed my life,all,Try it yourself
```

**Format:**
- `product_slideX` - Product category (use "all" for any)
- `slideX` - Caption text for that slide
- Each row = one complete post

### Method 2: Multi-Caption with ||

```csv
product_slide1,slide1,product_slide2,slide2
all,Hook text || @username,all,CTA text || Limited time
```

**The `||` delimiter creates TWO captions on the same slide:**
- "Hook text" appears at Caption 1 position
- "@username" appears at Caption 2 position (completely independent)

### Method 3: Image Sets

**Folder:** `sample_content/sets/my_photos/`
```
1.jpg
2.jpg
3.jpg
```

**CSV:** `sample_content/prompt/captions_sets.csv`
```csv
set_id,caption_1,caption_2,caption_3
my_photos,First slide,Second slide,Third slide
my_photos,Different hook,Different middle,Different CTA
```

**Each row uses the SAME images (1.jpg, 2.jpg, 3.jpg) with different captions.**

---

## 🎬 Generating Posts

### Option 1: Command Line

```bash
python -m generation.generate \
  --base-path sample_content \
  --captions-path sample_content/captions.csv \
  --variations 3
```

**Parameters:**
- `--base-path` - Your content folder
- `--captions-path` - Path to your CSV file
- `--variations` - How many times to generate each caption row (default: 1)

### Option 2: Custom Settings Per Image

1. Open the app: `python3 run_slides_app.py`
2. Select image from left panel
3. Adjust settings in right panel
4. Click "Generate Preview" to test
5. Click "Apply to All Slides" if you want same settings everywhere
6. Repeat for each image
7. Run generation command

**Output:** `output/variationX/postY/1.png, 2.png, 3.png...`

---

## 🎨 Complete Workflow Example

### Scenario: Create 10 TikTok Posts (2 slides each)

**Step 1: Prepare Images**
```bash
# Add 5-10 images to each folder
sample_content/slide1/  ← Hook images
sample_content/slide2/  ← CTA images
```

**Step 2: Create Captions**

Use Claude AI to generate captions:
1. Go to claude.ai
2. Upload `sample_content/prompt/example_2_slides.csv`
3. Copy prompt from `sample_content/prompt/CLAUDE_PROMPT_CSV_GENERATOR.md`
4. Request: "Create 10 variations about fitness. Slide 1 = hooks, Slide 2 = CTAs with '@fitking'"
5. Save output as `sample_content/fitness_batch1.csv`

**Step 3: Customize Look (Optional)**
```bash
python3 run_slides_app.py
```
- Style one image from slide1/
- Click "Apply to All Slides in 'slide1'"
- Repeat for slide2/

**Step 4: Generate**
```bash
python -m generation.generate \
  --base-path sample_content \
  --captions-path sample_content/fitness_batch1.csv \
  --variations 3
```

**Result:** 30 complete posts (10 caption combos × 3 variations)

---

## 🔥 Advanced Features

### Before/After Transformations (Sets Mode)

**Setup:**
```bash
sample_content/sets/transformation/
  ├── before.jpg
  ├── during.jpg
  └── after.jpg
```

**CSV:**
```csv
set_id,caption_1,caption_2,caption_3
transformation,Where I started,30 days in,Final results
transformation,Day 1 struggle,Getting easier,Made it!
transformation,Before the change,During the grind,After 90 days
```

**Generate:**
```bash
python -m generation.generate \
  --base-path sample_content \
  --captions-path sample_content/transformations.csv \
  --variations 2
```

**Result:** 6 posts (3 rows × 2 variations), each using the same 3 images with different captions.

### Multi-Caption in UI

1. Open app
2. Select an image
3. Enable "Multi-caption mode"
4. Type extra captions (one per line):
   ```
   @username
   Limited stock
   ```
5. Click "📍 Caption 2 (Extra)"
6. Click on preview image where you want Caption 2
7. Adjust Caption 2 settings independently
8. Generate preview

**Caption 1 and Caption 2 are COMPLETELY SEPARATE:**
- Different positions
- Different fonts, sizes, colors
- Different outlines/shadows/backgrounds
- Different margins

### Maximum Slides (10-Slide Carousel)

**CSV:**
```csv
product_slide1,slide1,product_slide2,slide2,product_slide3,slide3,product_slide4,slide4,product_slide5,slide5,product_slide6,slide6,product_slide7,slide7,product_slide8,slide8,product_slide9,slide9,product_slide10,slide10
all,Top 10 tips,all,#1: Wake early,all,#2: Exercise,all,#3: Read daily,all,#4: Meal prep,all,#5: Track money,all,#6: Say no,all,#7: Journal,all,#8: Call family,all,#9: Rest well,all,#10: Stay consistent
```

---

## 💡 Pro Tips

### Speed Up Workflow
1. **Use Claude to generate 50+ caption variations in seconds**
   - Upload example CSV that matches your slide count
   - Provide topic and style
   - Get ready-to-use CSV file

2. **Create one perfect styled image, apply to all**
   - Don't style every image individually
   - Use "Apply to All Slides"
   - Saves hours

3. **Use sets for story sequences**
   - Before/after
   - Step-by-step tutorials
   - Day 1-7 progress posts

### Quality Tips
1. **Font size 50-70 works best** for mobile viewing
2. **Use outline (5px) or background** for text readability
3. **Keep captions short** - 5-10 words max per slide
4. **Position Caption 1 top (0.3)** and Caption 2 bottom (0.75)** for @username

### Batch Production
**Goal: 100 posts in 30 minutes**
1. Drop 20 images in slide1/, 20 in slide2/
2. Generate 100-row CSV with Claude AI
3. Run generation: `--variations 1`
4. Result: 100 unique posts ready to upload

---

## 🐛 Troubleshooting

### "Validation error: Invalid file in base folder"
**Fix:** Move non-image files to `prompt/` folder or delete them

### "Set 'my_set' not found"
**Fix:** Make sure folder exists at `sample_content/sets/my_set/`

### "Set has X images but Y captions"
**Fix:** Count images in set folder, add/remove CSV columns to match

### Preview not showing
**Fix:** Click "Generate Preview" button after changing settings

### Caption 2 overlapping Caption 1
**Fix:** Enable "Multi-caption mode" and use independent position sliders

### App won't start
**Fix:**
```bash
pkill -f streamlit
python3 run_slides_app.py
```

---

## 📚 File Reference

### Must-Read Guides
- `MULTI_CAPTION_GUIDE.md` - How to use || delimiter
- `IMAGE_SETS_GUIDE.md` - How to create image sets
- `SESSION_SUMMARY.md` - All features overview

### Claude AI Helpers
- `sample_content/prompt/CLAUDE_PROMPT_CSV_GENERATOR.md` - The prompt
- `sample_content/prompt/QUICK_START_CLAUDE_CSV.md` - Step-by-step
- `sample_content/prompt/example_X_slides.csv` - Examples for 2, 4, 6, 10 slides

---

## 🎯 Quick Reference

### Start App
```bash
python3 run_slides_app.py
```

### Generate Posts
```bash
python -m generation.generate \
  --base-path sample_content \
  --captions-path sample_content/captions.csv \
  --variations 3
```

### CSV Formats

**Regular (Random Images):**
```csv
product_slide1,slide1,product_slide2,slide2
all,Hook,all,CTA
```

**Sets (Specific Images):**
```csv
set_id,caption_1,caption_2
my_set,First,Second
```

**Multi-Caption:**
```csv
product_slide1,slide1,product_slide2,slide2
all,Main || Extra,all,CTA || @username
```

---

## 🚀 Next Steps

1. **Add your images** to slide1/, slide2/ folders
2. **Create captions** using Claude AI + example CSVs
3. **Customize styling** (optional) in the web interface
4. **Generate posts** with the command line
5. **Upload to TikTok** and go viral!

**Need help?** Check the guides in the repo or create an issue on GitHub.

Happy creating! 🎬✨
