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

**Reference Example:**
[I will upload an example CSV file showing the exact format]

---

## My Request:

[PASTE YOUR SPECIFIC REQUEST HERE]

Example requests:
- "Create a CSV with 20 variations using 2 slides. Slide 1 should have hooks about productivity, slide 2 should have CTAs about my course."
- "Create a CSV for a before/after transformation post with 3 slides. I want 5 different caption variations for the set."
- "Generate a CSV with hooks about travel and CTAs about booking. Add '@travelwithme' as a second caption on slide 2. 15 variations, 2 slides."

## PROMPT END

---

## How to Use:

1. **Copy the prompt above** (from "PROMPT START" to "PROMPT END")
2. **Upload the example CSV file** (`example_for_claude.csv`) to Claude
3. **Add your specific request** at the bottom
4. **Claude will generate** the exact CSV content you need
5. **Copy the output** and save as `.csv` file in your `sample_content/` folder
6. **Run generation:** `python -m generation.generate --base-path sample_content --captions-path sample_content/your_file.csv --variations 3`

## Tips:

- Be specific about how many slides you want (2-10)
- Tell Claude if you want multi-caption (with `||`)
- Mention if you want sets mode or regular random mode
- Provide example captions if you have a specific style
- Claude will create more variations if you ask for more rows
