# Multi-Caption Guide

## Using Multiple Captions in Your Slides

You can add a second caption to any slide using the `||` (double pipe) delimiter in your CSV file.

### How It Works

Simply add `||` in any CSV cell to split it into two captions:

```csv
product_slide1,slide1,product_slide2,slide2
all,Main caption || Extra caption,all,Main CTA || Bottom note
all,Single caption only,all,Another single one
```

### Example

**CSV:**
```csv
product_slide1,slide1,product_slide2,slide2
all,(I like chocolate) || @username,all,Shop now || Limited time
```

**Result:**
- **Slide 1:** Shows "(I like chocolate)" at Caption 1 position + "@username" at Caption 2 position
- **Slide 2:** Shows "Shop now" at Caption 1 position + "Limited time" at Caption 2 position

### Caption Settings

**Caption 1 (Main):**
- Position, font, colors, margins set in the UI or metadata
- Controls the first text before `||`

**Caption 2 (Extra):**
- Independent position, font, colors, margins
- Set in the UI under "Caption 2 Settings (Independent)" section
- Controls the text after `||`

### UI vs CSV

You can use multi-captions in **two ways**:

1. **CSV Method** (this guide): Use `||` in CSV cells for batch generation
2. **UI Method**: Enable "Multi-caption mode" checkbox and type extra text in the text area

Both methods work the same way!

### Tips

- Caption 2 settings are **per-image** (not per-caption-text)
- Use "Apply to All Slides" to copy Caption 2 settings across all images in a category
- Leave cells without `||` for single-caption slides
- The `||` delimiter works in any CSV column (slide1, slide2, etc.)

### Examples

**Social media handle:**
```csv
all,Product review || @yourhandle,all,Buy now || Link in bio
```

**Contextual notes:**
```csv
all,Amazing results,all,Shop now || Only today
all,Before vs After,all,Get yours || 50% off
```

**Tiered messaging:**
```csv
all,Watch this || You won't believe it,all,Shop now || Free shipping
```

## That's it!

No special configuration needed - just use `||` in your CSV and it works! 🎉
