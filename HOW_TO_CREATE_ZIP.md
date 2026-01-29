# How to Create ZIP for Upload

## Quick Guide

### Step 1: Save the Manhwa Page

In your browser (Chrome, Firefox, Edge):
1. Navigate to the manhwa chapter
2. Press `Ctrl+S` (or `Cmd+S` on Mac)
3. Choose "Save as type": **Webpage, Complete**
4. Save it

This creates:
```
chapter.html              ← The HTML file
chapter_files/            ← Folder with all images
  ├── image_001.jpg
  ├── image_002.jpg
  └── ...
```

### Step 2: Create the ZIP

#### Windows
1. Select both the `.html` file AND the `_files` folder
2. Right-click → "Send to" → "Compressed (zipped) folder"
3. Done! You have `chapter.zip`

#### Mac
1. Select both the `.html` file AND the `_files` folder
2. Right-click → "Compress 2 items"
3. Done! You have `Archive.zip` (rename it if you want)

#### Linux
```bash
zip -r chapter.zip chapter.html chapter_files/
```

### Step 3: Upload in UI

1. Run `streamlit run app.py`
2. Click "Upload ZIP File (HTML + Images)"
3. Select your `chapter.zip`
4. Click "Start Translation"

## What the ZIP Should Contain

```
chapter.zip
├── chapter.html                  ← Main HTML file
└── chapter_files/                ← Images folder (exactly as saved)
    ├── image_001.jpg
    ├── image_002.jpg
    ├── image_003.png
    └── ...
```

**Important:**
- Keep the folder structure exactly as the browser saved it
- Don't rename the `_files` folder
- Include both the HTML and the images folder in the ZIP

## Troubleshooting

### "No HTML file found in ZIP"
- Make sure the `.html` file is in the ZIP
- Check you didn't accidentally ZIP only the images folder

### "Missing N images"
- The `_files` folder must be in the ZIP
- Don't move or rename files after saving from browser
- Make sure the ZIP contains the full folder structure

### Example: Correct Structure

Save page as "chapter_42.html" creates:
```
chapter_42.html
chapter_42_files/
  ├── img1.jpg
  └── img2.png
```

ZIP should contain:
```
chapter_42.zip
├── chapter_42.html
└── chapter_42_files/
    ├── img1.jpg
    └── img2.png
```

## CLI Usage

```bash
# Create ZIP
zip -r chapter.zip chapter.html chapter_files/

# Run translation
python cli.py --zip chapter.zip
```
