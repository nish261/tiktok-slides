# TikTok Slides CSV Generator - Claude AI Prompt

Generate CSV files for your TikTok Slides Generator using Claude AI.

---

## 🚀 Quick Start

### Step 1: Open Claude
Go to **claude.ai** or your Claude interface

### Step 2: Upload Example File
Choose the example that matches your needs:
- **2 slides (hook + CTA)?** → Upload `example_2_slides.csv`
- **4 slides (tips, tutorials)?** → Upload `example_4_slides.csv`
- **6 slides (stories, guides)?** → Upload `example_6_slides.csv`
- **10 slides (countdowns, lists)?** → Upload `example_10_slides_max.csv`
- **Image sets (before/after)?** → Upload `example_sets_3_slides.csv`

### Step 3: Copy & Paste This Prompt

---

## 📝 THE PROMPT (Copy from here ↓)

```
I need you to generate a CSV file for my TikTok Slides Generator tool.

**Context:**
I have a batch image generation tool that creates TikTok carousel posts. It needs a specific CSV format to work.

**CSV Format Rules:**

1. **Regular Mode (Random Image Selection):**
   - Headers: product_slide1,slide1,product_slide2,slide2,... (up to 10 slides)
   - Each row = one post variation
   - "all" in product column = use any image from that slide folder
   - Example:
     product_slide1,slide1,product_slide2,slide2
     all,Hook text,all,CTA text
     all,Different hook,all,Different CTA

2. **Image Sets Mode (Specific Image Sequences):**
   - Headers: set_id,caption_1,caption_2,caption_3,...
   - set_id = folder name in sets/ directory
   - Each row = one post variation using the same set of images
   - Example:
     set_id,caption_1,caption_2,caption_3
     beach_photos,Day 1,Day 2,Day 3
     beach_photos,Different caption 1,Different caption 2,Different caption 3

3. **Multi-Caption Support:**
   - Use || (double pipe) to add multiple captions to one slide
   - Works in both regular and sets mode
   - Example: Hook text || @username creates two separate captions on the same slide
   - Caption 1 and Caption 2 have completely independent positioning/styling

**What I'll Provide You:**
- List of captions I want to use OR topic/style
- Number of slides per post (2-10)
- Whether to use regular mode or sets mode
- (Optional) Multi-caption requirements

**What You Should Give Me:**
- Complete CSV file content (ready to copy/paste)
- Clear indication of which mode it's using
- Any assumptions you made
- If sets mode: what to name the image folders

**IMPORTANT:** Match the EXACT format of the example CSV I uploaded. Include ALL column headers (product_slide1,slide1,product_slide2,slide2, etc.)

---

My Request:

[PASTE YOUR REQUEST HERE - See examples below]
```

## 📝 THE PROMPT (Copy to here ↑)

---

## 💡 Example Requests

### Example 1: Simple 2-Slide Posts
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

### Example 2: Multi-Caption with Username
```
Create a CSV with 15 variations using 2 slides.

Slide 1: Product hooks + add "@myproduct" as second caption on each
Slide 2: CTAs + add "Limited stock" as second caption on each

Make it about skincare products.
```

### Example 3: Tutorial Format (4 Slides)
```
Create a CSV with 10 variations using 4 slides.

Format: Introduction → Tip 1 → Tip 2 → Call to action

Topic: Productivity hacks for remote workers
```

### Example 4: Image Sets (Before/After)
```
Create a CSV in SETS MODE with 3 slides for a fitness transformation.

I have a folder called "transformation_march" with 3 photos.

Create 10 different caption variations for:
- Slide 1: Before state
- Slide 2: During/progress
- Slide 3: After results

Make them motivational and relatable.
```

### Example 5: 10-Slide Countdown
```
Create a CSV with 5 variations using 10 slides.

Format: Top 10 countdown list about morning routine habits

Add "@productivityking" as a second caption on slide 10.
```

---

## 📋 Format Reference

### Regular Mode (Random Images)
```csv
product_slide1,slide1,product_slide2,slide2
all,Hook text,all,CTA text
all,Different hook,all,Different CTA
```
- Uses random images from slide1/, slide2/ folders
- "all" = any product category
- Different random images each time you generate

### Sets Mode (Specific Image Sequences)
```csv
set_id,caption_1,caption_2,caption_3
my_photos,First slide,Second slide,Third slide
my_photos,Different hook,Different middle,Different CTA
```
- Images must be in sets/my_photos/ folder (1.jpg, 2.jpg, 3.jpg)
- Same images used for each row, different captions
- Perfect for before/after, tutorials, story sequences

### Multi-Caption (Two Captions Per Slide)
```csv
product_slide1,slide1,product_slide2,slide2
all,Main text || @username,all,CTA || Limited time
all,Hook || Second line,all,Buy now || Follow me
```
- || separates captions on the same slide
- Caption 1 and Caption 2 positioned independently
- Works in both regular and sets mode

---

## 🎯 Pro Tips

**For More Variations:**
- "Create 50 variations" → Claude generates 50 rows

**For Specific Niches:**
- "Make them about fitness/tech/beauty/travel" → Claude adapts the style

**For Specific Tone:**
- "Make them funny/serious/motivational/educational" → Claude adjusts the copy

**For Pattern Matching:**
- Provide 3-5 example captions you like → Claude matches the style

**For Multi-Language:**
- "Create captions in Spanish/French/etc." → Claude translates

**For Engagement:**
- Ask for hooks with "POV:", "Stop scrolling", "Watch till end", etc.

---

## 🔄 Complete Workflow

1. **Upload example CSV** to Claude (example_2_slides.csv, example_4_slides.csv, etc.)
2. **Copy the prompt** above (from "I need you to generate..." to end)
3. **Add your request** in the "My Request:" section
4. **Claude generates** the complete CSV
5. **Copy the output** from Claude
6. **Save as file:** `sample_content/my_captions.csv`
7. **Run generation:**
   ```bash
   python -m generation.generate \
     --base-path sample_content \
     --captions-path sample_content/my_captions.csv \
     --variations 3
   ```

**Result:** Ready-to-upload TikTok carousel posts!

---

## 📊 Real Example

**You upload:** `example_2_slides.csv`

**You paste the prompt and add:**
```
Create 30 variations about productivity tips.
Slide 1 = hooks about waking up early
Slide 2 = CTAs with "Follow @productivityking"
```

**Claude outputs:**
```csv
product_slide1,slide1,product_slide2,slide2
all,Stop hitting snooze,all,Follow @productivityking
all,5 AM club changed my life,all,Follow @productivityking
all,Wake up before your competition,all,Follow @productivityking
... (27 more rows)
```

**You save as:** `sample_content/productivity_batch1.csv`

**You generate:** 90 posts (30 rows × 3 variations)

**Done!** 🎉

---

## 🎓 Tips for Best Results

1. **Be specific about quantity** - "Create 25 variations" is clearer than "create many"
2. **Mention slide count** - "using 4 slides" helps Claude match the format
3. **Describe the topic** - "about fitness" gives better captions than no context
4. **Request multi-caption explicitly** - "Add @username as second caption on slide 2"
5. **Use the right example** - Upload example file that matches your desired slide count

---

## ⚡ Speed Workflow

**Goal: 100 Posts in 15 Minutes**

1. Drop 20 images in slide1/, 20 in slide2/
2. Upload `example_2_slides.csv` to Claude
3. Paste prompt: "Create 100 variations about [topic]. Slide 1 = hooks, Slide 2 = CTAs"
4. Copy CSV output → Save as file
5. Run: `python -m generation.generate --base-path sample_content --captions-path sample_content/batch.csv --variations 1`

**Result:** 100 unique posts ready to schedule!

---

**Happy generating!** 🚀✨
