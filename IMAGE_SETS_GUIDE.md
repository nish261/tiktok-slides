# Image Sets Guide - Simplified Subfolder Approach

## What Are Image Sets?

Image sets let you keep specific images together as one post. Instead of randomly selecting images, you decide exactly which 2-10 images appear together in sequence.

## How to Use

### 1. Create a Subfolder in `sets/`

```
sample_content/
  sets/
    beach_vacation/      ← Your set name
    product_demo/        ← Another set
  slide1/               ← Keep for random images
  slide2/
```

### 2. Drop Images Into the Subfolder

**Any filenames work!** Images are sorted alphabetically.

```
sets/beach_vacation/
  IMG_5432.jpg         ← Will be slide 1 (alphabetically first)
  IMG_5433.jpg         ← Will be slide 2
  IMG_5434.jpg         ← Will be slide 3
```

Or:

```
sets/product_demo/
  1.webp              ← Will be slide 1
  2.webp              ← Will be slide 2
```

**Pro tip:** Name files `1.jpg`, `2.jpg`, `3.jpg` for easy control over order!

### 3. Create CSV with Sets Format

**File:** `captions_sets.csv`

```csv
set_id,caption_1,caption_2,caption_3
beach_vacation,Day 1 at beach,Sunset view,Beach selfie
product_demo,Check this out,Buy now,
```

**Format:**
- First column: `set_id` (matches folder name in `sets/`)
- Other columns: `caption_1`, `caption_2`, `caption_3`, etc.
- Number of caption columns must match number of images in the set

### 4. Generate

```bash
python -m generation.generate \
  --base-path sample_content \
  --captions-path sample_content/captions_sets.csv \
  --variations 3
```

**Output:**

```
output/
  variation1/
    post1/
      1.png  ← beach_vacation/IMG_5432.jpg + "Day 1 at beach"
      2.png  ← beach_vacation/IMG_5433.jpg + "Sunset view"
      3.png  ← beach_vacation/IMG_5434.jpg + "Beach selfie"
    post2/
      1.png  ← product_demo/1.webp + "Check this out"
      2.png  ← product_demo/2.webp + "Buy now"
```

## Example

**Folder structure:**

```
sets/
  vacation_photos/
    A_morning.jpg
    B_afternoon.jpg
    C_evening.jpg
```

**CSV:**

```csv
set_id,caption_1,caption_2,caption_3
vacation_photos,Morning coffee,Beach time,Sunset dinner
vacation_photos,Another day,Different caption,End of day
```

**Creates 2 posts:**
- Post 1: 3 slides with first set of captions
- Post 2: 3 slides with second set of captions (reuses same images)

## Rules

✅ **DO:**
- Use any image filenames (they'll be sorted alphabetically)
- Create as many sets as you want
- Mix sets mode with regular captions (different CSV files)
- Name folders anything (letters, numbers, underscores)

❌ **DON'T:**
- Mismatch caption count with image count (will error)
- Use special characters in folder names (stick to letters, numbers, underscore)
- Put subfolders inside sets/{set_name}/ (only images!)

## Comparison: Sets vs Regular

### Regular Mode (Random)
```csv
product_slide1,slide1,product_slide2,slide2
all,Hook text,all,CTA text
```
- Randomly picks images from `slide1/` and `slide2/`
- Different images each time
- Good for variety

### Sets Mode (Specific)
```csv
set_id,caption_1,caption_2
my_set,Hook text,CTA text
```
- Uses exact images from `sets/my_set/`
- Same images every time
- Good for stories/sequences

## Troubleshooting

**Error: "Set 'my_set' not found in sets/ folder"**
→ Make sure folder exists at `sample_content/sets/my_set/`

**Error: "Set has X images but Y captions. They must match!"**
→ Count your images in the set folder, add/remove caption columns to match

**Images in wrong order**
→ Rename files: `1.jpg`, `2.jpg`, `3.jpg` to control order

## That's It!

1. Create folder in `sets/`
2. Drop images in
3. Add row to CSV with matching captions
4. Generate!

No file renaming, no complex setup - just drop and go! 🚀
