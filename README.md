# AUTO-Translate v.2

**Automated Manhwa Translation System**

A complete Python pipeline to crawl Korean manhwa chapters, OCR text, filter and translate with Claude AI, and re-render translated English text back into images.

## Features

- **Web Crawling**: Automated chapter crawling with Playwright/Selenium
- **OCR**: Dual-engine (PaddleOCR + EasyOCR) with enhanced preprocessing
- **Smart Splitting**: Intelligent panel splitting that avoids cutting through text
- **LLM Filtering**: Claude AI-based garbage text detection (SFX, watermarks)
- **LLM Translation**: Context-aware Korean→English translation
- **Inpainting**: Clean removal of original text using OpenCV
- **Text Rendering**: Automatic font matching and text rendering
- **Streamlit UI**: Interactive web interface with progress tracking and debugging tools

## Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Setup

1. Clone the repository:
```bash
cd AUTO-Translate-v.2
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:
```bash
playwright install chromium
```

5. Create `.env` file with your Anthropic API key:
```bash
cp .env.example .env
# Edit .env and add your API key:
# ANTHROPIC_API_KEY=your_actual_api_key_here
```

6. (Optional) Download fonts:
- Place Korean-compatible fonts (e.g., NanumGothic.ttf) in `fonts/` directory
- Update `config.yaml` if using different font

## Usage

### Streamlit UI (Recommended)

Launch the interactive web interface:

```bash
streamlit run app.py
```

Then:
1. Enter manhwa chapter URL
2. Adjust settings if needed (OCR threshold, target language)
3. Click "Start Translation"
4. View results in the Results tab

### Command Line Interface

Run translation from command line:

```bash
python cli.py "https://example.com/manhwa/chapter-1"
```

Options:
- `--config PATH`: Specify custom config file
- `--debug`: Enable debug mode

## Configuration

Edit `config.yaml` to customize:

- **OCR Settings**: Engine selection, confidence threshold
- **Crawler Settings**: Browser choice, timeout, scroll behavior
- **Panel Filter**: Size limits, aspect ratio, excluded keywords
- **Smart Split**: Max sub-panels, margin from text
- **LLM Settings**: Model selection, temperature
- **Translation**: Target language, context window size
- **Debug**: Artifact saving, debug mode

## Project Structure

```
AUTO-Translate-v.2/
├── src/
│   ├── config.py              # Configuration management
│   ├── pipeline.py            # Main orchestration
│   ├── crawler/               # Web crawling
│   ├── panels/                # Panel extraction & stitching
│   ├── ocr/                   # OCR engine
│   ├── split/                 # Smart splitting
│   ├── storage/               # Data persistence
│   ├── agents/                # LLM agents
│   ├── inpaint/               # Text inpainting
│   ├── render/                # Text rendering
│   └── ui/                    # Streamlit UI
├── workspace/                 # Runtime artifacts
├── fonts/                     # Font files
├── app.py                     # Streamlit entry point
├── cli.py                     # CLI entry point
├── config.yaml                # Configuration
└── .env                       # API keys
```

## How It Works

### 1. Crawling
- Navigate to manhwa chapter URL
- Handle Cloudflare challenges (manual authentication)
- Scroll to load all panels
- Extract panel image URLs using heuristics

### 2. Panel Processing
- Download panels in parallel
- Stitch vertically with coordinate mapping
- Run OCR pass #1 to identify text regions

### 3. Smart Splitting
- Find whitespace lines between panels
- Filter safe cut lines (avoid cutting through text)
- Split into manageable sub-panels

### 4. OCR Pass #2
- Run OCR on each sub-panel
- Extract text with bounding boxes
- Store results with confidence scores

### 5. LLM Filtering
- Classify text as KEEP (dialogue) or DROP (SFX/watermark)
- Conservative approach: prefer false positives over false negatives
- Batch processing to reduce API calls

### 6. Translation
- Translate filtered text with context
- Preserve tone and character voice
- Maintain naming consistency

### 7. Inpainting
- Build masks from text bounding boxes
- Use OpenCV Telea algorithm to remove original text
- Preserve background artwork

### 8. Text Rendering
- Estimate font properties from original boxes
- Fit translated text with adaptive sizing
- Render with outlines (manhwa style)

### 9. Composition
- Bake rendered text into panels
- Save final translated images

## Troubleshooting

### Cloudflare Challenge

If you encounter Cloudflare challenges:
1. The system will automatically open a browser window
2. Solve the challenge manually
3. Press Enter in the terminal to continue

### OCR Issues

If OCR accuracy is poor:
- Try adjusting `ocr.confidence_threshold` in `config.yaml`
- Check image quality (low resolution affects OCR)
- Enable debug mode to inspect preprocessed images

### API Rate Limits

If you hit Anthropic API rate limits:
- Reduce batch size in agent modules
- Add longer delays between batches
- Use a higher tier API plan

### Missing Fonts

If text rendering fails:
- Ensure font file exists at path specified in `config.yaml`
- Download NanumGothic or similar Korean-compatible font
- System will fall back to default font if specified font is missing

## Debugging

Enable debug mode in UI or CLI to:
- View OCR bounding boxes overlay
- See filter agent decisions
- Compare original vs translated text
- Browse all intermediate artifacts

Debug artifacts are saved to `workspace/` subdirectories.

## Limitations

- **Academic use only**: This tool is for research and educational purposes
- **Manual Cloudflare solving**: Cannot automatically bypass Cloudflare challenges
- **Simple captcha only**: Only handles basic numeric captchas
- **Font matching**: Best-effort font estimation (not perfect matching)
- **Text length**: Very long translations may overflow boxes

## Performance

Typical processing time for 50-panel chapter:
- Crawling: 1-2 minutes
- Panel download: 30 seconds
- OCR: 2-3 minutes
- LLM filtering + translation: 3-5 minutes
- Inpainting + rendering: 1-2 minutes

**Total: ~10 minutes per chapter**

## Dependencies

Key libraries:
- `streamlit`: Web UI framework
- `playwright`: Browser automation
- `paddleocr`: Primary OCR engine
- `easyocr`: Fallback OCR engine
- `opencv-python`: Image processing & inpainting
- `pillow`: Image manipulation
- `anthropic`: Claude API client
- `pydantic`: Configuration validation

See `requirements.txt` for complete list.

## Contributing

This is an academic research project. Feel free to:
- Report bugs via GitHub issues
- Suggest improvements
- Fork for your own research

## License

Academic and non-commercial use only.

## Disclaimer

This tool is designed for educational and research purposes. Users are responsible for complying with copyright laws and website terms of service when using this software.

## Acknowledgments

- PaddleOCR for excellent Korean OCR
- Anthropic Claude for LLM capabilities
- OpenCV for inpainting algorithms
- Streamlit for easy UI development
