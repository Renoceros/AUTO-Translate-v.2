# HTML Upload Feature Guide

## Overview

The HTML upload feature allows you to skip web crawling by uploading a saved manhwa HTML file directly. This is useful when:
- The website has difficult captchas or anti-bot measures
- You want to translate an offline/saved chapter
- You're testing the pipeline without hitting the source website repeatedly

## How to Save a Manhwa Page

### Method 1: Chrome/Edge/Brave

1. Navigate to the manhwa chapter you want to translate
2. Press `Ctrl+S` (Windows/Linux) or `Cmd+S` (Mac)
3. In the save dialog:
   - **Save as type**: Select "Webpage, Complete"
   - **Filename**: Give it a descriptive name (e.g., `chapter_42.html`)
4. Click "Save"

This will create:
- `chapter_42.html` - The HTML file
- `chapter_42_files/` - A folder with all images

### Method 2: Firefox

1. Navigate to the manhwa chapter
2. Press `Ctrl+S` or `Cmd+S`
3. In the save dialog:
   - **Save as type**: Select "Web Page, complete"
4. Click "Save"

This creates similar structure to Chrome.

### Method 3: Safari

1. Navigate to the manhwa chapter
2. File → Save As...
3. **Format**: Web Archive (or "Page Source" + manually save images)

## Using HTML Upload in the UI

### Streamlit Interface

1. Launch the app:
   ```bash
   streamlit run app.py
   ```

2. In the "Input" section:
   - Leave the "Manhwa Chapter URL" field **empty**
   - Click "Browse files" under "— OR —"
   - Select your saved HTML file
   - You'll see: "📄 Uploaded: chapter_42.html"

3. Configure settings (optional):
   - Target Language
   - OCR Confidence Threshold
   - Debug Mode

4. Click "Start Translation"

5. The pipeline will:
   - Extract images from the HTML file
   - Look for images in the same folder as the HTML
   - Skip the crawling stage
   - Process images through OCR → Translation → Rendering

### Command Line Interface

```bash
# Using HTML file
python cli.py --html /path/to/chapter_42.html

# With debug mode
python cli.py --html /path/to/chapter_42.html --debug
```

## File Structure Requirements

The HTML file and images must be in the correct locations:

```
manhwa_folder/
├── chapter_42.html           ← Upload this file
└── chapter_42_files/          ← Images must be here
    ├── page_01.png
    ├── page_02.png
    └── ...
```

Or flat structure:
```
manhwa_folder/
├── chapter_42.html           ← Upload this file
├── page_01.png               ← Images in same folder
├── page_02.png
└── ...
```

## Supported Image Formats

- PNG (`.png`)
- JPEG (`.jpg`, `.jpeg`)
- GIF (`.gif`)
- WebP (`.webp`)

## Troubleshooting

### Error: "No images found in HTML file"

**Cause**: The HTML doesn't contain any `<img>` tags

**Solution**:
- Make sure you saved as "Webpage, Complete" not just "HTML Only"
- Check if the website uses JavaScript to load images (dynamic loading)
- Try saving from a different browser

### Error: "Missing N images: ..."

**Cause**: The HTML references images that aren't in the folder

**Solutions**:
1. Make sure you uploaded the HTML file, not just the images folder
2. Keep the HTML and images folder together
3. Don't rename the images folder after saving
4. Check if the save process completed successfully

Example error:
```
Missing 3 images:
  - chapter_42_files/page_05.png
  - chapter_42_files/page_06.png
  - chapter_42_files/page_07.png
```

This means these 3 image files are referenced in the HTML but not found on disk.

### Error: "Provide either URL or HTML file, not both"

**Cause**: You filled in both the URL field and uploaded an HTML file

**Solution**:
- Clear the URL field, OR
- Remove the uploaded file (click the X)
- Use only one input method

### Images Not Loading in Browser

**Cause**: Relative paths broken after moving files

**Solution**:
- Don't move the HTML file away from its images folder
- If you must move, move both together
- Keep the original folder structure

## Advanced: Manual HTML Creation

You can create your own HTML file if you already have the images:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Chapter 42</title>
</head>
<body>
    <img src="page_01.png">
    <img src="page_02.png">
    <img src="page_03.png">
    <!-- Add more images -->
</body>
</html>
```

Save this as `chapter.html` in the same folder as your images.

## Performance Comparison

| Input Method | Time (50 panels) | Network | Notes |
|--------------|------------------|---------|-------|
| URL Crawling | ~10 minutes | Required | May encounter captchas |
| HTML Upload  | ~8 minutes  | None | Faster, no crawling overhead |

## FAQ

**Q: Can I upload MHTML files?**
A: Not yet. Use "Webpage, Complete" format which creates separate HTML + images.

**Q: What if images are on a CDN (external URLs)?**
A: The ingester skips external URLs. Save the page properly with "Webpage, Complete" to download images locally.

**Q: Can I upload multiple chapters at once?**
A: Not currently. Process one chapter at a time.

**Q: Where are the images copied to?**
A: They're copied to `workspace/raw_panels/` with standardized names (`panel_0000.png`, etc.)

**Q: Can I reuse the same HTML file?**
A: Yes! The HTML file isn't modified, only read.

## Technical Details

### What the Ingester Does

1. Reads HTML file using Python's `html.parser`
2. Extracts all `<img src="...">` and `<img data-src="...">` attributes
3. Filters out external URLs and data URIs
4. Resolves relative paths to absolute paths
5. Validates all images exist on disk
6. Copies images to `workspace/raw_panels/` with sequential naming
7. Returns list of image paths to the pipeline

### Security

- Path traversal prevention: Uses `.resolve()` to normalize paths
- Only accepts local file paths (no external URLs)
- Validates file extensions
- Streamlit enforces 200MB upload limit by default

### Limitations

- HTML must be uploaded through Streamlit UI (not command line browse)
- Images must be accessible on local filesystem
- No support for lazy-loaded images (JavaScript-based)
- No support for embedded base64 images (data URIs)

## Examples

### Example 1: Basic Usage

```bash
# Save chapter from website
# Upload chapter_1.html in UI
# Images automatically extracted from chapter_1_files/
```

### Example 2: CLI Usage

```bash
# Using absolute path
python cli.py --html /home/user/manhwa/chapter_42.html

# Using relative path
python cli.py --html ./saved_chapters/chapter_42.html
```

### Example 3: Testing

```bash
# Run the test suite
python3 test_html_parser_simple.py
```

## See Also

- [README.md](README.md) - Main documentation
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [src/ingester/html_parser.py](src/ingester/html_parser.py) - Implementation
