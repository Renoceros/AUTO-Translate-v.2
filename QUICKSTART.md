# Quick Start Guide

Get up and running with AUTO-Translate v.2 in 5 minutes.

## 1. Install Dependencies

```bash
# Activate virtual environment (if not already active)
source ATvenv/bin/activate  # On Windows: ATvenv\Scripts\activate

# Install required packages
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

## 2. Set Up API Key

Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:
```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxx
```

Get your API key from: https://console.anthropic.com/

## 3. Run the Application

### Option A: Web UI (Recommended)

```bash
streamlit run app.py
```

This will open a browser window at `http://localhost:8501`

### Option B: Command Line

```bash
python cli.py "https://example.com/manhwa/chapter-1"
```

## 4. First Translation

1. **Enter URL**: Paste a manhwa chapter URL
2. **Adjust Settings** (optional):
   - OCR Confidence: 0.6 (default) - lower = more text detected
   - Target Language: English (default)
   - Debug Mode: Enable to see intermediate steps
3. **Click "Start Translation"**
4. **Wait** (~10 minutes for typical chapter)
5. **View Results** in the Results tab

## Test with Sample Chapter

If you don't have a manhwa URL handy, try these common manhwa platforms:
- Webtoon.com
- Kakao Webtoon
- Naver Webtoon
- Tappytoon

**Note**: Some sites may have Cloudflare protection. The system will prompt you to solve it manually.

## Common Issues

### "ANTHROPIC_API_KEY not found"
- Make sure `.env` file exists in project root
- Check that API key is correctly formatted (starts with `sk-ant-`)
- Restart the application after creating `.env`

### "ModuleNotFoundError"
- Make sure you're in the virtual environment
- Run `pip install -r requirements.txt` again

### Cloudflare Challenge
- The system will open a browser window automatically
- Solve the CAPTCHA/challenge manually
- Press Enter in the terminal to continue

### OCR Not Detecting Text
- Try lowering OCR confidence threshold (0.4-0.5)
- Check if image quality is good (high resolution)
- Enable debug mode to see OCR preprocessing

### Translation Taking Too Long
- First run downloads OCR models (~500MB) - this is one-time
- Subsequent runs are much faster
- Typical chapter takes ~10 minutes

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [config.yaml](config.yaml) for customization options
- Enable debug mode to understand each processing stage
- Browse workspace artifacts in `workspace/` directory

## Support

For issues, check the troubleshooting section in README.md or create an issue on GitHub.
