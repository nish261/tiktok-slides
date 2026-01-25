# TikTok Slides CSV Generator - Claude AI Prompt

Generate unlimited CSV files for your TikTok Slides Generator using Claude AI.

---

## 🚀 How to Use

### Step 1: Open Claude
Go to **claude.ai**

### Step 2: Upload Example
Upload **example_2_slides.csv** (in this folder)

### Step 3: Copy & Paste This Prompt

---

## 📝 THE PROMPT (Copy Everything Below)

```
I need you to generate a CSV file for my TikTok Slides Generator tool.

You'll see an example CSV I uploaded. Match that EXACT format with these rules:

**CSV Format:**
- Headers: product_slide1,slide1,product_slide2,slide2,product_slide3,slide3,... (up to slide10)
- Each row = one complete post
- "all" in product columns = use any image
- Use || (double pipe) for multiple captions on same slide
  Example: "Hook text || @username" = two separate captions on one slide

**What I'll Give You:**
- Topic or niche
- How many variations (rows) I want
- How many slides per post (2-10)
- (Optional) Multi-caption requirements

**What You Give Me:**
- Complete CSV ready to copy/paste
- Match the format EXACTLY (include ALL column headers)

---

My Request:

[PASTE YOUR REQUEST HERE]
```

---

## 💡 Example Requests

**Simple 2-Slide Posts:**
```
Create 30 variations with 2 slides about fitness.
Slide 1 = hooks about weight loss
Slide 2 = CTAs with "Link in bio"
```

**With Username:**
```
Create 25 variations with 2 slides about productivity.
Slide 1 = hooks
Slide 2 = CTAs + add "@productivityking" as second caption using ||
```

**4-Slide Tutorial:**
```
Create 15 variations with 4 slides.
Format: Intro → Tip 1 → Tip 2 → CTA
Topic: Morning routines
```

**10-Slide Countdown:**
```
Create 10 variations with 10 slides.
Format: Top 10 list about healthy habits
Add "@healthking" on slide 10 using ||
```

---

## 📋 Format Reference

**Regular (2 slides):**
```csv
product_slide1,slide1,product_slide2,slide2
all,Hook text,all,CTA text
```

**With Multi-Caption:**
```csv
product_slide1,slide1,product_slide2,slide2
all,Hook || @username,all,Buy now || Limited time
```

**More Slides (just add more columns):**
```csv
product_slide1,slide1,product_slide2,slide2,product_slide3,slide3,product_slide4,slide4
all,Intro,all,Tip 1,all,Tip 2,all,CTA
```

---

## 🎯 Complete Workflow

1. **Upload** example_2_slides.csv to Claude
2. **Copy** the prompt above
3. **Paste** and add your request
4. **Claude generates** the CSV
5. **Copy output** → Save as `sample_content/my_captions.csv`
6. **Run:**
   ```bash
   python -m generation.generate \
     --base-path sample_content \
     --captions-path sample_content/my_captions.csv \
     --variations 3
   ```

**Done!** 🎉

---

## ⚡ Pro Tips

- Ask for 50-100 variations for variety
- Use || for @username, second lines, CTAs
- Match your slide count (2-10) to your images
- Be specific: "about fitness" gets better results than "random"

---

**That's it!** One prompt, one example, unlimited CSV files. 🚀
