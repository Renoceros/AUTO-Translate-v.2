# Development Guide

Guide for developers who want to extend or modify AUTO-Translate v.2.

## Architecture Overview

### Modular Design

The system is organized into independent modules that can be tested and improved separately:

```
Pipeline Orchestrator (pipeline.py)
    ↓
┌────────────────────────────────────────────┐
│  Stage 1: Crawler (crawler/)              │
│  Stage 2: Panel Extraction (panels/)      │
│  Stage 3: OCR (ocr/)                      │
│  Stage 4: Smart Split (split/)            │
│  Stage 5: LLM Agents (agents/)            │
│  Stage 6: Inpainting (inpaint/)           │
│  Stage 7: Rendering (render/)             │
│  Stage 8: UI (ui/)                        │
└────────────────────────────────────────────┘
```

Each module can be improved independently without affecting others.

## Module Details

### 1. Configuration (`src/config.py`)

**Purpose**: Centralized configuration management

**Key Classes**:
- `Config`: Main configuration container
- `OCRConfig`, `CrawlerConfig`, etc.: Sub-configurations

**Extension Points**:
- Add new configuration sections
- Add validation rules
- Support additional storage backends

**Example**:
```python
from src.config import get_config

config = get_config()
print(config.ocr.primary_engine)
```

### 2. Crawler (`src/crawler/`)

**Purpose**: Web scraping and panel URL extraction

**Key Files**:
- `browser.py`: Browser abstraction (Playwright/Selenium)
- `asset_filter.py`: Panel detection heuristics
- `captcha_solver.py`: Captcha handling

**Extension Points**:
- Add new browser drivers
- Improve panel detection algorithms
- Add support for more captcha types
- Handle different website structures

**Example**:
```python
from src.crawler.browser import crawl_chapter
from src.config import get_config

urls = await crawl_chapter("https://...", get_config())
```

### 3. OCR (`src/ocr/`)

**Purpose**: Text extraction from images

**Key Files**:
- `engine.py`: OCR engine wrapper
- `preprocess.py`: Image enhancement
- `postprocess.py`: Result cleaning

**Extension Points**:
- Add new OCR engines (Tesseract, Google Vision, etc.)
- Improve preprocessing for different art styles
- Add language-specific optimizations
- Implement text region detection

**Example**:
```python
from src.ocr.engine import OCREngine
from src.config import get_config

engine = OCREngine(get_config())
boxes = engine.run(image_path)
```

### 4. LLM Agents (`src/agents/`)

**Purpose**: AI-based filtering and translation

**Key Files**:
- `filter_agent.py`: Text classification
- `translation_agent.py`: Translation with context

**Extension Points**:
- Improve prompts for better accuracy
- Add support for other LLM providers (OpenAI, Cohere)
- Implement caching for repeated translations
- Add translation memory
- Fine-tune on manhwa-specific data

**Example**:
```python
from src.agents.translation_agent import translate_text_boxes
from src.config import get_config

translated = await translate_text_boxes(ocr_boxes, get_config())
```

### 5. Rendering (`src/render/`)

**Purpose**: Text rendering onto images

**Key Files**:
- `font_estimator.py`: Font property estimation
- `layout_solver.py`: Text fitting
- `text_renderer.py`: PIL-based rendering

**Extension Points**:
- ML-based font matching
- Better text fitting algorithms
- Support for vertical text
- Speech bubble detection
- Background color analysis for text color

**Example**:
```python
from src.render.text_renderer import render_text_batch
from src.config import get_config

rendered = await render_text_batch(images, boxes, get_config())
```

## Adding New Features

### Example 1: Add New OCR Engine

1. Create new engine class in `src/ocr/engine.py`:

```python
class TesseractEngine:
    def run(self, image: np.ndarray) -> List[OCRBox]:
        import pytesseract
        # Implementation
        pass
```

2. Update `OCREngine.run()` to use new engine:

```python
def run(self, image_path: Path) -> List[OCRBox]:
    if self.config.ocr.primary_engine == "tesseract":
        return self.run_tesseract(image)
    # ... existing code
```

3. Update `config.yaml`:

```yaml
ocr:
  primary_engine: tesseract
```

### Example 2: Add Translation Memory

1. Create new module `src/storage/translation_memory.py`:

```python
class TranslationMemory:
    def __init__(self, db_path: str):
        self.db = {}  # Or use SQLite

    def lookup(self, source: str) -> Optional[str]:
        return self.db.get(source)

    def store(self, source: str, target: str):
        self.db[source] = target
```

2. Integrate into translation agent:

```python
# In translation_agent.py
async def translate_single_box(client, box, context, config):
    tm = TranslationMemory("workspace/tm.db")

    # Check translation memory first
    cached = tm.lookup(box['text'])
    if cached:
        return {**box, "translated": cached}

    # ... existing translation code

    # Store new translation
    tm.store(box['text'], result['translated'])
```

### Example 3: Add New UI Tab

1. Create new UI module `src/ui/ui_editor.py`:

```python
import streamlit as st

def render_translation_editor(translations):
    st.header("Translation Editor")

    for i, trans in enumerate(translations):
        edited = st.text_area(
            f"Box {i}",
            value=trans['translated'],
            key=f"edit_{i}"
        )
        trans['translated'] = edited
```

2. Add tab in `src/ui/app.py`:

```python
tab1, tab2, tab3, tab4 = st.tabs(["Process", "Results", "Editor", "Debug"])

with tab4:
    from src.ui.ui_editor import render_translation_editor
    render_translation_editor(translations)
```

## Testing

### Unit Testing

Create tests for individual modules:

```python
# tests/test_ocr.py
import pytest
from src.ocr.engine import OCREngine
from src.config import Config

def test_ocr_engine():
    config = Config.load()
    engine = OCREngine(config)

    # Test with sample image
    boxes = engine.run(Path("tests/fixtures/sample.png"))
    assert len(boxes) > 0
    assert boxes[0].confidence > 0.5
```

### Integration Testing

Test full pipeline:

```python
# tests/test_pipeline.py
from src.pipeline import Pipeline
from src.config import Config

def test_full_pipeline():
    config = Config.load()
    pipeline = Pipeline(config)

    result = pipeline.run("https://test-url.com")
    assert result["status"] == "success"
    assert len(result["artifacts"]["final_paths"]) > 0
```

### Manual Testing

```bash
# Test specific module
python -m src.ocr.engine tests/fixtures/sample.png

# Test with debug mode
python cli.py "https://test-url.com" --debug
```

## Performance Optimization

### 1. Parallel Processing

Use asyncio for concurrent operations:

```python
# Instead of sequential
for url in urls:
    download(url)

# Use parallel
await asyncio.gather(*[download(url) for url in urls])
```

### 2. Caching

Add caching for expensive operations:

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def ocr_cached(image_hash):
    return run_ocr(image_hash)
```

### 3. Batch Processing

Batch LLM requests to reduce API calls:

```python
# Instead of one-by-one
for box in boxes:
    translate(box)

# Batch multiple boxes
batches = [boxes[i:i+10] for i in range(0, len(boxes), 10)]
for batch in batches:
    translate_batch(batch)
```

## Debugging

### Enable Debug Mode

```python
# In config.yaml
debug:
  save_artifacts: true
  debug_mode: true
```

### View Intermediate Artifacts

```bash
# OCR results
cat workspace/ocr/ocr_boxes.csv

# View split images
ls workspace/splits/

# View final images
ls workspace/final/
```

### Add Logging

```python
import logging

logger = logging.getLogger(__name__)
logger.debug("Processing box: %s", box)
logger.info("OCR found %d boxes", len(boxes))
logger.warning("Low confidence: %f", confidence)
logger.error("Failed to process: %s", error)
```

## Common Issues

### 1. Memory Issues

For large images:
- Process in chunks
- Use image downsampling
- Clear GPU cache after each batch

### 2. API Rate Limits

- Add exponential backoff
- Implement request queuing
- Use batch endpoints when available

### 3. OCR Accuracy

- Tune preprocessing parameters
- Try different OCR engines
- Increase image resolution
- Use ensemble methods (multiple engines)

## Code Style

Follow these conventions:

### Naming
- Classes: `PascalCase`
- Functions: `snake_case`
- Constants: `UPPER_CASE`
- Private: `_leading_underscore`

### Docstrings
```python
def function_name(param: type) -> return_type:
    """
    Brief description.

    Args:
        param: Parameter description

    Returns:
        Return value description
    """
    pass
```

### Type Hints
Always use type hints:
```python
from typing import List, Dict, Optional

def process(data: List[Dict[str, Any]]) -> Optional[str]:
    pass
```

## Contribution Workflow

1. Create feature branch
2. Implement changes
3. Add tests
4. Update documentation
5. Test locally
6. Submit pull request

## Resources

- **PaddleOCR**: https://github.com/PaddlePaddle/PaddleOCR
- **Anthropic API**: https://docs.anthropic.com/
- **Playwright**: https://playwright.dev/python/
- **OpenCV**: https://docs.opencv.org/
- **Streamlit**: https://docs.streamlit.io/

## Support

For questions or issues:
- Check documentation first
- Search existing issues
- Create detailed bug reports
- Include logs and configs
