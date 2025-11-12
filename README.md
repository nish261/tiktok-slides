### TikTok Slides Generator

Create batches of slide images for short-form content from a simple folder + CSV setup. Validate your content, preview and edit with a Streamlit interface, and export organized variations ready for TikTok/Shorts/Reels.

---

## Features
- **Strict content validation**: catches missing folders, bad headers, and mismatched products before generation.
- **Streamlit editor**: review metadata, tweak settings, and preview images interactively.
- **Emoji-aware text rendering**: robust fallback mechanisms for platform emoji differences.
- **Duplicate prevention controls**: per-product duplicate logic with an override.
- **Deterministic folder outputs**: variation/post structure ready for scheduling tools.
- **Simple Python API**: load → validate → edit (optional) → generate.

---

## Requirements
- Python 3.11 or 3.12 recommended.
  - Note: Python 3.13 can work, but some scientific stacks are not installed (see comment in `requirements.txt`).
- Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r tiktok_slides/requirements.txt
```

---

## Quickstart
Use the included sample to verify everything is working:

```python
from tiktok_slides.main import SlideManager

content_path = "tiktok_slides/sample_content"  # change to your content root

sm = SlideManager(log_level="INFO")
sm.load(content_path, strict=True, separator=",")  # validates and loads captions/metadata
# sm.open_interface()  # optional: launches Streamlit UI for visual review
sm.generate(variations=2, allow_all_duplicates=False)
```

Outputs will be written under `<content_path>/output/variation{n}/post{m}/`.

---

## Content folder layout
Point the manager at a folder that looks like:

```
your_content/
  captions.csv
  metadata.json
  hook/
    ...images...
  story/
    ...images...
  cta/
    ...images...
```

- The set of content types (e.g., `hook`, `story`, `cta`) comes from your `metadata.json`.
- Images should live under each content-type folder and be referenced in metadata.
- Products and duplicate-prevention behavior are configured in `metadata.json` and settings.

You can use `tiktok_slides/sample_content` as a reference.

---

## Captions CSV format
Headers alternate between product and text for each content type:

```
product_hook,hook,product_story,story,product_cta,cta
all,This is a great tip!,all,Do this next...,all,Follow for more
productA,Another hook,productB,Middle content,productC,Call to action
```

- `product_*` columns select which product’s pool of images to use for that content type.
- Use `"all"` to draw from all matching products (respecting duplicate-prevention unless you override).
- The separator defaults to `,` but can be changed via `separator` when calling `load(...)`.

---

## Streamlit interface (optional but recommended)
The interface lets you:
- Browse metadata and products
- Preview image selections
- Adjust settings via templates and product/content overrides

Launch it using the manager (handles arguments for you):

```python
from tiktok_slides.main import SlideManager
sm = SlideManager()
sm.load("tiktok_slides/sample_content")
sm.open_interface()
```

Under the hood this runs Streamlit with the required arguments:
- `tiktok_slides/interface/main.py` expects `<base_path> <content_types> <products> <separator>`.

---

## Output structure
By default, images are saved under your content folder:

```
your_content/
  output/
    variation1/
      post1/
        1.png
        2.png
        3.png
      post2/
        ...
    variation2/
      ...
```

You can pass a custom `output_path` to `generate(...)`. If it doesn’t exist, the default is used.

---

## Useful API surface
- `SlideManager.load(path, strict=True, separator=",")`  
  Validate and load content. In strict mode, warnings are treated as errors.
- `SlideManager.validate(strict=True)`  
  Re-validate without reloading files (honors last used `separator`).
- `SlideManager.open_interface()`  
  Launch Streamlit UI for interactive review.
- `SlideManager.generate(variations=2, allow_all_duplicates=False, output_path=None)`  
  Generate images into organized variation/post folders.
- `SlideManager.print_content_structure(format="raw"|"standard")`  
  Inspect discovered products/content-types.

---

## Troubleshooting
- “Validation failed”  
  - Run `load(..., strict=False)` to see detailed warnings vs. errors.
  - Ensure `captions.csv` headers alternate correctly and match your content types.
  - Confirm `metadata.json` lists the same content types and that image references exist.
- “No available images for <content_type> - <product>”  
  - Add images for that product/content type, or change the CSV to a product that exists.
  - If using `all` and products have `prevent_duplicates=true`, either add more images or pass `allow_all_duplicates=True` to `generate(...)`.
- Emoji not rendering as expected  
  - The project includes PNG/SVG fallback renderers and font assets; ensure dependencies from `requirements.txt` are installed.

---

## Development
- Run tests:

```bash
pytest -q
```

- Key modules:
  - `tiktok_slides/content_manager/` — validation, metadata, settings
  - `tiktok_slides/generation/generate.py` — core image generation
  - `tiktok_slides/text/` — text and emoji rendering
  - `tiktok_slides/interface/` — Streamlit UI
  - `tiktok_slides/tools/` — utilities (reports, renaming, conversions)

---

## License
See `tiktok_slides/LICENSE`.
