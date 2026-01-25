# Quick Start: Generate CSV Files with Claude

Use Claude to automatically generate CSV files for your TikTok Slides Generator.

## Files You Need

1. **CLAUDE_PROMPT_CSV_GENERATOR.md** - The prompt to use with Claude
2. **Example files to upload to Claude:**
   - `example_for_claude.csv` - Regular 2-slide format with multi-captions
   - `example_sets_for_claude.csv` - Sets mode format (3 slides)
   - `example_advanced_for_claude.csv` - Advanced 4-slide format

## How to Use

### Step 1: Open Claude
Go to claude.ai or your Claude interface

### Step 2: Upload Example Files
Upload one or more example CSV files depending on what you need:
- **2 slides, random images?** → Upload `example_for_claude.csv`
- **Image sets (before/after)?** → Upload `example_sets_for_claude.csv`
- **4+ slides?** → Upload `example_advanced_for_claude.csv`

### Step 3: Copy the Prompt
Open `CLAUDE_PROMPT_CSV_GENERATOR.md` and copy the prompt from "PROMPT START" to "PROMPT END"

### Step 4: Add Your Request
Paste the prompt and add your specific request at the bottom. Examples:

**Example 1: Simple Hook + CTA**
```
Create a CSV with 25 variations using 2 slides.

Slide 1 captions (hooks):
- Stop scrolling if you want abs
- This exercise changed my body
- 30 day transformation incoming
- POV: You finally got fit
- (Use similar style, create more variations)

Slide 2 captions (CTAs):
- Link in bio
- Follow for more
- Save this
- Try it yourself
```

**Example 2: Multi-Caption with Username**
```
Create a CSV with 15 variations using 2 slides.

Slide 1: Product hooks + add "@myproduct" as second caption on each
Slide 2: CTAs + add "Limited stock" as second caption on each

Make it about skincare products.
```

**Example 3: Image Sets (Before/After)**
```
Create a CSV in SETS MODE with 3 slides for a fitness transformation.

I have a folder called "transformation_march" with 3 photos.

Create 10 different caption variations for:
- Slide 1: Before state
- Slide 2: During/progress
- Slide 3: After results

Make them motivational and relatable.
```

### Step 5: Claude Generates the CSV
Claude will output something like:

```csv
product_slide1,slide1,product_slide2,slide2
all,Stop scrolling if you want abs,all,Link in bio
all,This exercise changed my body,all,Follow for more
all,30 day transformation incoming,all,Save this
...
```

### Step 6: Save and Use

1. **Copy the CSV output** from Claude
2. **Save it as a file:** `sample_content/my_captions.csv`
3. **Run generation:**
   ```bash
   python -m generation.generate \
     --base-path sample_content \
     --captions-path sample_content/my_captions.csv \
     --variations 3
   ```

## Format Reference

### Regular Mode (Random Images)
```csv
product_slide1,slide1,product_slide2,slide2
all,Hook text,all,CTA text
```
- Uses random images from `slide1/`, `slide2/` folders
- "all" = any product category

### Sets Mode (Specific Image Sequences)
```csv
set_id,caption_1,caption_2,caption_3
my_photos,First slide,Second slide,Third slide
```
- Images must be in `sets/my_photos/` folder (1.jpg, 2.jpg, 3.jpg)
- Same images used for each row, different captions

### Multi-Caption (Two Captions Per Slide)
```csv
product_slide1,slide1,product_slide2,slide2
all,Main text || @username,all,CTA || Limited time
```
- `||` separates captions on the same slide
- Caption 1 and Caption 2 are positioned independently

## Pro Tips

**For More Variations:**
"Create 50 variations" → Claude will generate 50 rows

**For Specific Niches:**
"Make them about fitness/tech/beauty/travel/etc." → Claude adapts the style

**For Specific Tone:**
"Make them funny/serious/motivational/educational" → Claude adjusts the copy

**For Pattern Matching:**
Provide 3-5 example captions you like, Claude will match the style

**For Multi-Language:**
"Create captions in Spanish/French/etc." → Claude translates

## Example Workflow

1. You have 10 photos in `slide1/` and 10 photos in `slide2/`
2. Upload `example_for_claude.csv` to Claude
3. Prompt: "Create 30 variations about productivity tips. Slide 1 = hooks, Slide 2 = CTAs with 'Follow @productivityking'"
4. Claude generates 30-row CSV
5. Copy → Save as `productivity_batch_1.csv`
6. Generate → Get 30 different posts with random image combinations

**Result:** 30 unique TikTok carousel posts ready to upload!
