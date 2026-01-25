# Claude Prompt: TikTok Slides CSV Generator

Copy and paste this prompt to Claude when you want to generate a CSV file for the TikTok Slides Generator.

---

## PROMPT START

I need you to generate a CSV file for my TikTok Slides Generator tool.

**Context:**
I have a batch image generation tool that creates TikTok carousel posts. It needs a specific CSV format to work.

**CSV Format Rules:**

1. **Regular Mode (Random Image Selection):**
   - Headers: `product_slide1,slide1,product_slide2,slide2,...` (up to 10 slides)
   - Each row = one post variation
   - "all" in product column = use any image from that slide folder
   - Example:
     ```csv
     product_slide1,slide1,product_slide2,slide2
     all,Hook text,all,CTA text
     all,Different hook,all,Different CTA
     ```

2. **Image Sets Mode (Specific Image Sequences):**
   - Headers: `set_id,caption_1,caption_2,caption_3,...`
   - set_id = folder name in `sets/` directory
   - Each row = one post variation using the same set of images
   - Example:
     ```csv
     set_id,caption_1,caption_2,caption_3
     beach_photos,Day 1,Day 2,Day 3
     beach_photos,Different caption 1,Different caption 2,Different caption 3
     ```

3. **Multi-Caption Support:**
   - Use `||` (double pipe) to add multiple captions to one slide
   - Works in both regular and sets mode
   - Example: `Hook text || @username` creates two separate captions on the same slide
   - Caption 1 and Caption 2 have completely independent positioning/styling

**What I'll Provide You:**
- List of captions I want to use
- Number of slides per post (2-10)
- Whether to use regular mode or sets mode
- (Optional) Multi-caption requirements

**What You Should Give Me:**
- Complete CSV file content (ready to copy/paste)
- Clear indication of which mode it's using
- Any assumptions you made
- If sets mode: what to name the image folders

**Reference Examples Available:**
- `example_2_slides.csv` - Simple 2-slide format with multi-caption examples
- `example_4_slides.csv` - Medium complexity with 4 slides
- `example_6_slides.csv` - Advanced 6-slide carousel
- `example_10_slides_max.csv` - Maximum 10-slide format
- `example_sets_3_slides.csv` - Sets mode with 3-slide sequences

**Upload one or more examples based on your needs!**

---

## My Request:

[PASTE YOUR SPECIFIC REQUEST HERE]

Example requests:
- "Create a CSV with 20 variations using 2 slides. Slide 1 should have hooks about productivity, slide 2 should have CTAs about my course."
- "Create a CSV with 4 slides for a tutorial format. I want 15 variations."
- "Create a CSV for a before/after transformation post with 3 slides using SETS MODE. I want 5 different caption variations for the set."
- "Generate a CSV with 6 slides about travel tips. Add '@travelwithme' as a second caption on the last slide. 10 variations."
- "Make a 10-slide countdown format with hooks about fitness transformation. 5 variations."

## PROMPT END

---

## How to Use:

1. **Copy the prompt above** (from "PROMPT START" to "PROMPT END")
2. **Upload example CSV file(s)** to Claude based on what you need:
   - 2 slides? → Upload `example_2_slides.csv`
   - 4 slides? → Upload `example_4_slides.csv`
   - 6 slides? → Upload `example_6_slides.csv`
   - 10 slides? → Upload `example_10_slides_max.csv`
   - Sets mode? → Upload `example_sets_3_slides.csv`
3. **Add your specific request** at the bottom
4. **Claude will generate** the exact CSV content you need
5. **Copy the output** and save as `.csv` file in your `sample_content/` folder
6. **Run generation:** `python -m generation.generate --base-path sample_content --captions-path sample_content/your_file.csv --variations 3`

## Tips:

- Upload the example file that matches your desired number of slides (2, 4, 6, or 10)
- Be specific about how many variations (rows) you want
- Tell Claude if you want multi-caption (with `||`)
- Mention if you want sets mode or regular random mode
- Provide example captions if you have a specific style
- Claude will match the format of whichever example you upload
