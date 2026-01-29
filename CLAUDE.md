# AUTO-Translate v.2

## What
Automated Korean→English manhwa translation pipeline. Crawls chapters, OCRs text, filters/translates with Claude AI, inpaints original text, re-renders translations.

**Status**: Academic research project, fully implemented

## Why
End-to-end ML pipeline combining CV (OCR, inpainting) + NLP (translation) + web automation. Innovation: stitch-then-split preserves dialogue context while avoiding cutting through text.

## Tech Stack
- **Python 3.9+** | **Streamlit** (UI) | **AsyncIO** (concurrency)
- **Playwright** + Selenium (crawling) | **aiohttp** (HTTP)
- **PaddleOCR** + EasyOCR (Korean OCR) | **OpenCV** (inpainting) | **Pillow** (images)
- **Anthropic Claude API** (LLM) | **Pydantic** (config validation)

## Project Structure

**Source**: `src/`
- `config.py` - Pydantic configuration models
- `pipeline.py:50-200` - Main Pipeline orchestrator (11 stages)
- `crawler/` - Playwright/Selenium automation, captcha solving
- `ingester/` - HTML file parsing and image extraction
- `panels/` - Download, stitching with coordinate mapping
- `ocr/` - Dual engines (PaddleOCR→EasyOCR), preprocessing
- `split/smart_split.py:40-150` - Whitespace detection, safe cutting
- `storage/` - CSV persistence for OCR metadata
- `agents/` - Filter agent (dialogue vs SFX) + translation agent
- `inpaint/` - OpenCV Telea/Navier-Stokes text removal
- `render/` - Font estimation, layout solving, PIL rendering
- `ui/` - Streamlit tabs (Process, Results, Debug)

**Artifacts**: `workspace/{raw_panels,stitched,splits,ocr,inpainted,rendered,final}/` (gitignored)

**Entry points**: `app.py` (UI), `cli.py` (CLI)

## Key Files
- `src/config.py:60-120` - Config validation
- `src/crawler/browser.py:80-150` - Browser drivers
- `src/ingester/html_parser.py` - HTML parsing and image extraction
- `src/ocr/engine.py:70-180` - OCR strategy pattern
- `src/agents/filter_agent.py:30-180` - LLM classifier
- `src/agents/translation_agent.py:30-170` - LLM translator
- `src/render/text_renderer.py:30-140` - Text rendering

## Build & Run

**Setup**:
```bash
./setup.sh  # Or: pip install -r requirements.txt && playwright install chromium
cp .env.example .env  # Add ANTHROPIC_API_KEY=your_key
```

**Run**:
```bash
streamlit run app.py  # UI (recommended)
python cli.py "https://manhwa-url.com/chapter-1"  # CLI with URL
python cli.py --html saved_chapter.html  # CLI with HTML file
python test_installation.py  # Verify setup
```

**Config**: `config.yaml` (OCR threshold, browser, LLM model, etc.) + `.env` (API key)

## Pipeline Flow

**From URL**: 1. Crawl → 2. Download → 3. Stitch → ... → 11. Compose
**From HTML**: 1-2. HTML Ingestion (extract images) → 3. Stitch → ... → 11. Compose

Full pipeline: 1. Crawl/Ingest → 2. Download/Extract → 3. Stitch → 4. OCR #1 (text detection) → 5. Smart split → 6. OCR #2 (extraction) → 7. Filter (KEEP/DROP) → 8. Translate → 9. Inpaint → 10. Render → 11. Compose

**Runtime**: ~10 min/50-panel chapter (URL mode), ~8 min (HTML mode, skips crawling)

## Common Operations

**View artifacts**: `ls workspace/{stitched,splits,final}/` | `cat workspace/ocr/ocr_boxes.csv`

**Debug mode**: Set `debug.debug_mode: true` in `config.yaml` or use UI checkbox

**Adjust OCR**: Set `ocr.confidence_threshold: 0.4` in `config.yaml` (lower = more text)

## Additional Documentation

**Architecture**: `.claude/docs/architectural_patterns.md`
- Design patterns: Pipeline, Strategy, Repository, Observer, Two-Pass Processing
- Async/await conventions, fallback chains, batch processing
- Extension points for new engines/stages

**User docs**: `README.md` (complete), `QUICKSTART.md` (5-min start), `IMPLEMENTATION_SUMMARY.md` (technical)

**Developer**: `DEVELOPMENT.md` (extension examples, testing, debugging)

## Conventions

**File refs**: Use `file:line` format (e.g., `src/config.py:60-120`)

**Async**: All I/O uses `async def`/`await`. Blocking wrapped: `await loop.run_in_executor(None, func)`

**Errors**: Fail gracefully, log, continue with fallback. See `.claude/docs/architectural_patterns.md`

**Config injection**: All modules accept `Config`. Global: `from src.config import get_config`

**Progress**: Callback pattern at `src/pipeline.py:40-50`

## Troubleshooting
See `README.md` Troubleshooting section or `QUICKSTART.md` Common Issues.

**Debug workflow**: Enable debug mode → check `workspace/` → view logs → use UI Debug tab

## Git Workflow
For "bug fix" or "feature addition" prompts: create new branch first.
