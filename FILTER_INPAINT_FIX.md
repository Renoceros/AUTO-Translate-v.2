# Filter & Inpainting Bug Fixes

## Issues Identified

### Issue #1: Inpainting Only Processed Filtered Boxes (CRITICAL)
**Symptom:** Final images still show Korean text that should have been removed

**Root Cause:**
```python
# OLD CODE (src/pipeline.py:163)
inpainted_paths = await self._inpaint_panels(split_paths, filtered_boxes)
```

The pipeline passed `filtered_boxes` to inpainting instead of `ocr_boxes_pass2`. This meant:
1. OCR detects 183 text boxes
2. Filter keeps only 21 boxes (drops 162)
3. **Inpainting only removes the 21 kept boxes**
4. **162 Korean text boxes remain visible in final output!**

**Fix:**
```python
# NEW CODE (src/pipeline.py:163)
inpainted_paths = await self._inpaint_panels(split_paths, ocr_boxes_pass2)
```

Now inpainting uses ALL OCR detections, ensuring all detected Korean text is removed regardless of filter decisions.

**Files Modified:**
- `src/pipeline.py:163` - Pass `ocr_boxes_pass2` instead of `filtered_boxes`
- `src/pipeline.py:247` - Update function signature
- `src/inpaint/opencv_inpaint.py:90-122` - Update to use `all_ocr_boxes`

### Issue #2: Batch Filter Too Aggressive
**Symptom:** Only 21/183 boxes kept (11% keep rate) vs 103/142 (72%) in single-box mode

**Root Cause:**
The batch prompt was less explicit about being conservative, causing the LLM to be more aggressive when seeing multiple boxes at once.

**Impact:**
- Many dialogue boxes were incorrectly dropped as SFX
- Only 21 translations rendered instead of ~130
- Most panels had blank inpainted areas instead of English text

**Fix:**
Updated `FILTER_AGENT_PROMPT_BATCH` in `src/agents/filter_agent.py:58` to:
- Add "CRITICAL: BE EXTREMELY CONSERVATIVE!" warning
- Require 90%+ confidence to DROP
- Add more KEEP examples (short dialogue like "안녕", "그래", "아!")
- Emphasize "When in doubt, KEEP IT!"
- Better explain edge cases

**Expected Result:**
Keep rate should increase from 11% to 60-80%, closer to single-box mode.

## How the Pipeline Works (Fixed)

### Correct Flow:
1. **OCR Pass 2**: Detects all text → 183 boxes
2. **Filter**: Keeps dialogue/narration → ~130 boxes (with fixed prompt)
3. **Translation**: Translates kept boxes → ~130 English translations
4. **Inpainting**: Removes ALL 183 Korean text boxes (uses ocr_boxes_pass2)
5. **Rendering**: Renders ~130 English translations
6. **Result**: Clean panels with English text, no Korean text visible

### Why This Design is Correct:
- **Inpainting removes everything**: Ensures no Korean text remains
- **Rendering only adds filtered translations**: Only puts back what's important
- **Graceful degradation**: If filter is too aggressive, you get blank spaces instead of Korean text
- **If filter is too lenient**: A few SFX get translated (minor issue)

## Testing the Fixes

### Test 1: Verify Inpainting Uses All Boxes

```bash
# Run the pipeline on a test chapter
streamlit run app.py

# Check the logs
grep "Inpainting.*with.*OCR detections" logs/*.log

# Should see: "Inpainting 100 panels with 183 OCR detections..."
# NOT: "Inpainting 100 panels..." (old behavior without count)
```

### Test 2: Verify Filter Keep Rate Improved

```bash
# Run the pipeline and check logs
grep "Kept.*boxes after filtering" logs/*.log

# OLD: Kept 21/183 boxes (11%)
# NEW: Should keep 100-150/183 boxes (60-80%)
```

### Test 3: Check Final Output

```bash
# View final images
ls workspace/final/*.png

# Images should have:
# ✅ NO Korean text visible (all inpainted)
# ✅ English translations rendered
# ✅ Some panels may have blank spaces if filter dropped them (acceptable)
```

## Configuration Options

If filter is still too aggressive or lenient, adjust in `config.yaml`:

```yaml
agents:
  batch_size: 40        # Reduce to 20 if filter still too aggressive
  max_tokens: 4096
  use_batch_mode: true  # Set false to use single-box mode (slower but more conservative)
```

### Recommended Settings:

**For maximum quality (slower):**
```yaml
agents:
  batch_size: 20        # Smaller batches, more conservative
  use_batch_mode: true
```

**For debugging:**
```yaml
agents:
  use_batch_mode: false  # Single-box mode (72% keep rate proven)
```

## Verification Steps

1. **Clear workspace**: `rm -rf workspace/*`
2. **Run pipeline**: Process a test chapter
3. **Check logs**:
   ```bash
   tail -100 logs/auto_translate_*.log | grep -E "(Inpainting|Kept|Translated)"
   ```
4. **Expected output**:
   ```
   Inpainting 100 panels with 183 OCR detections...
   Kept 130/183 boxes after filtering
   Translated 130 boxes in 4 API call(s)
   ```
5. **Visual check**: Open `workspace/final/` and verify no Korean text visible

## Rollback (If Needed)

If the fixes cause issues, revert to single-box mode:

```yaml
# config.yaml
agents:
  use_batch_mode: false
```

This will use the proven single-box mode (72% keep rate, slower but reliable).

## Summary of Changes

### Files Modified:
1. **src/pipeline.py** (lines 163, 247)
   - Inpainting now uses all OCR boxes

2. **src/inpaint/opencv_inpaint.py** (lines 90-122)
   - Updated function signature and logging
   - Now accepts `all_ocr_boxes` instead of `filtered_boxes`

3. **src/agents/filter_agent.py** (lines 58-103)
   - Improved batch prompt to be more conservative
   - Added more KEEP examples
   - Emphasized "when in doubt, KEEP"

### Expected Improvements:
- ✅ All Korean text removed (inpainting uses all OCR boxes)
- ✅ Filter keep rate increases from 11% to 60-80%
- ✅ More dialogue translated and rendered
- ✅ Final output cleaner with proper English text

## Troubleshooting

**Q: Still seeing Korean text in final output?**
A: Check if OCR is detecting the text. Run:
```bash
grep "OCR Pass 2 found" logs/*.log
```
If text isn't detected by OCR, it won't be inpainted.

**Q: Filter still too aggressive (dropping dialogue)?**
A: Try:
1. Reduce `batch_size` to 20 in config.yaml
2. Or set `use_batch_mode: false` for single-box mode

**Q: Too many SFX getting translated?**
A: This is the tradeoff for being conservative. Better than missing dialogue.
Can manually review and adjust prompt examples for your specific manhwa style.

**Q: Blank spaces where text used to be?**
A: This means:
- Text was detected by OCR ✅
- Text was inpainted ✅
- But filter dropped it ❌
- Solution: Adjust filter to be more conservative (see above)
