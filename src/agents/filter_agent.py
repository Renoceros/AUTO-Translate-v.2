"""LLM-based garbage text filter agent."""
import asyncio
import json
import logging
from typing import List, Dict, Any

from anthropic import AsyncAnthropic

from src.config import Config


logger = logging.getLogger(__name__)


FILTER_AGENT_PROMPT_SINGLE = """You are a semantic text classifier for Korean manhwa (webcomics).

Your task: Classify OCR-extracted text as KEEP (essential dialogue/narration) or DROP (garbage).

Categories:
- dialogue: Character speech, essential to story
- narration: Story narration boxes
- sfx: Sound effects (e.g., "쾅!", "터터터")
- watermark: Site credits, copyright notices
- noise: OCR errors, artifacts

Guidelines:
- BE CONSERVATIVE: When in doubt, mark as KEEP
- False negatives (missing dialogue) are worse than false positives (keeping SFX)
- Consider context: short single syllables are often SFX
- Watermarks usually appear at top/bottom edges

Examples:
- "뭐야... 이게 대체 뭐야!" → KEEP (dialogue)
- "쿠르릉" → DROP (sfx)
- "© 2023 Manhwa Site" → DROP (watermark)
- "다음 화에 계속!" → DROP (site UI)
- "가장 빠른 웹툰제공사이트
   웹툰왕국뉴토끼469
   NEWTOKI469.COM" → DROP (watermark)
- "ㅋㅋㅋㅋ" → DROP (sfx)

Input:
{
  "text": "{{text}}",
  "box_width": {{width}},
  "box_height": {{height}},
  "position": "{{top|middle|bottom}}"
}

Output (JSON only):
{
  "decision": "KEEP" or "DROP",
  "category": "dialogue|narration|sfx|watermark|noise",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}
"""

FILTER_AGENT_PROMPT_BATCH = """You are a semantic text classifier for Korean manhwa (webcomics).

Your task: Classify multiple OCR-extracted text boxes as KEEP (essential dialogue/narration) or DROP (garbage).

Categories:
- dialogue: Character speech, essential to story
- narration: Story narration boxes
- sfx: Sound effects (e.g., "쾅!", "터터터")
- watermark: Site credits, copyright notices
- noise: OCR errors, artifacts

Guidelines:
- BE CONSERVATIVE: When in doubt, mark as KEEP
- False negatives (missing dialogue) are worse than false positives (keeping SFX)
- Consider context: short single syllables are often SFX
- Watermarks usually appear at top/bottom edges

Examples:
- "뭐야... 이게 대체 뭐야!" → KEEP (dialogue)
- "쿠르릉" → DROP (sfx)
- "© 2023 Manhwa Site" → DROP (watermark)
- "다음 화에 계속!" → DROP (site UI)
- "가장 빠른 웹툰제공사이트" → DROP (watermark)
- "ㅋㅋㅋㅋ" → DROP (sfx)

Input: Array of text boxes with IDs
Output: JSON array with same IDs, one decision per box

Output format (JSON array only):
[
  {
    "id": 0,
    "decision": "KEEP",
    "category": "dialogue",
    "confidence": 0.9,
    "reasoning": "Character speech"
  },
  {
    "id": 1,
    "decision": "DROP",
    "category": "sfx",
    "confidence": 0.85,
    "reasoning": "Sound effect"
  }
]
"""


async def classify_single_box(
    client: AsyncAnthropic,
    box: Dict[str, Any],
    config: Config,
    image_height: int
) -> Dict[str, Any]:
    """
    Classify single OCR box with LLM.

    Args:
        client: Anthropic client
        box: OCR box dictionary
        config: Configuration
        image_height: Total image height for position calculation

    Returns:
        Classification result
    """
    # Determine position
    y_ratio = box['y'] / image_height
    if y_ratio < 0.2:
        position = "top"
    elif y_ratio > 0.8:
        position = "bottom"
    else:
        position = "middle"

    # Build prompt
    user_message = json.dumps({
        "text": box['text'],
        "box_width": box['w'],
        "box_height": box['h'],
        "position": position
    }, ensure_ascii=False)

    try:
        response = await client.messages.create(
            model=config.llm.model,
            max_tokens=config.llm.max_tokens,
            temperature=config.llm.temperature,
            system=FILTER_AGENT_PROMPT_SINGLE,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        # Parse response
        response_text = response.content[0].text

        # Extract JSON from response
        try:
            # Try to parse as JSON
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code block
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                logger.warning(f"Failed to parse filter response: {response_text}")
                # Conservative fallback: KEEP
                result = {
                    "decision": "KEEP",
                    "category": "dialogue",
                    "confidence": 0.5,
                    "reasoning": "Failed to parse response, keeping conservatively"
                }

        return {
            **box,
            "filter_decision": result["decision"],
            "filter_category": result["category"],
            "filter_confidence": result["confidence"],
            "filter_reasoning": result.get("reasoning", "")
        }

    except Exception as e:
        logger.error(f"Filter agent failed for box: {e}")
        # Conservative fallback
        return {
            **box,
            "filter_decision": "KEEP",
            "filter_category": "dialogue",
            "filter_confidence": 0.5,
            "filter_reasoning": f"Error: {str(e)}"
        }


async def classify_box_batch(
    client: AsyncAnthropic,
    boxes: List[Dict[str, Any]],
    config: Config,
    image_height: int
) -> List[Dict[str, Any]]:
    """
    Classify multiple OCR boxes with single LLM call.

    Args:
        client: Anthropic client
        boxes: List of OCR box dictionaries
        config: Configuration
        image_height: Total image height for position calculation

    Returns:
        List of classification results with same indices
    """
    if not boxes:
        return []

    # Build batch input
    batch_input = []
    for idx, box in enumerate(boxes):
        # Determine position
        y_ratio = box['y'] / image_height
        if y_ratio < 0.2:
            position = "top"
        elif y_ratio > 0.8:
            position = "bottom"
        else:
            position = "middle"

        batch_input.append({
            "id": idx,
            "text": box['text'],
            "box_width": box['w'],
            "box_height": box['h'],
            "position": position
        })

    user_message = json.dumps(batch_input, ensure_ascii=False)

    try:
        response = await client.messages.create(
            model=config.llm.model,
            max_tokens=config.agents.max_tokens,
            temperature=config.llm.temperature,
            system=FILTER_AGENT_PROMPT_BATCH,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        # Parse response
        response_text = response.content[0].text

        # Extract JSON from response
        try:
            # Try to parse as JSON array
            results = json.loads(response_text)
            if not isinstance(results, list):
                raise ValueError("Expected JSON array")
        except (json.JSONDecodeError, ValueError):
            # Try to extract JSON from markdown code block
            import re
            json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', response_text, re.DOTALL)
            if json_match:
                results = json.loads(json_match.group(1))
            else:
                logger.warning(f"Failed to parse batch filter response, falling back to single-box processing")
                # Fall back to single-box processing
                return await _process_boxes_individually(client, boxes, config, image_height)

        # Match results back to boxes by ID
        results_by_id = {r["id"]: r for r in results}

        classified_boxes = []
        for idx, box in enumerate(boxes):
            result = results_by_id.get(idx)
            if result:
                classified_boxes.append({
                    **box,
                    "filter_decision": result["decision"],
                    "filter_category": result["category"],
                    "filter_confidence": result["confidence"],
                    "filter_reasoning": result.get("reasoning", "")
                })
            else:
                # Conservative fallback if ID missing
                logger.warning(f"Missing result for box ID {idx}, keeping conservatively")
                classified_boxes.append({
                    **box,
                    "filter_decision": "KEEP",
                    "filter_category": "dialogue",
                    "filter_confidence": 0.5,
                    "filter_reasoning": "Missing from batch response"
                })

        return classified_boxes

    except Exception as e:
        logger.error(f"Batch filter failed: {e}, falling back to single-box processing")
        # Fall back to individual processing
        return await _process_boxes_individually(client, boxes, config, image_height)


async def _process_boxes_individually(
    client: AsyncAnthropic,
    boxes: List[Dict[str, Any]],
    config: Config,
    image_height: int
) -> List[Dict[str, Any]]:
    """
    Process boxes individually as fallback.

    Args:
        client: Anthropic client
        boxes: List of OCR boxes
        config: Configuration
        image_height: Image height

    Returns:
        Classified boxes
    """
    tasks = [
        classify_single_box(client, box, config, image_height)
        for box in boxes
    ]
    return await asyncio.gather(*tasks)


async def filter_text_boxes(
    ocr_boxes: List[Dict[str, Any]],
    config: Config
) -> List[Dict[str, Any]]:
    """
    Filter OCR boxes using LLM agent.

    Args:
        ocr_boxes: List of OCR boxes
        config: Configuration

    Returns:
        Filtered list (only KEEP boxes)
    """
    if not ocr_boxes:
        return []

    logger.info(f"Filtering {len(ocr_boxes)} OCR boxes with LLM...")

    # Initialize Anthropic client
    client = AsyncAnthropic(api_key=config.anthropic_api_key)

    # Calculate image height (approximate from boxes)
    image_height = max(box['y'] + box['h'] for box in ocr_boxes) if ocr_boxes else 1000

    classified_boxes = []

    if config.agents.use_batch_mode:
        # Batch processing mode - process multiple boxes per API call
        batch_size = config.agents.batch_size
        num_batches = (len(ocr_boxes) + batch_size - 1) // batch_size

        logger.info(f"Processing {len(ocr_boxes)} boxes in {num_batches} batch(es) of up to {batch_size}")

        for i in range(0, len(ocr_boxes), batch_size):
            batch = ocr_boxes[i:i + batch_size]
            batch_num = i // batch_size + 1

            logger.info(f"Processing batch {batch_num}/{num_batches} ({len(batch)} boxes)")

            batch_results = await classify_box_batch(client, batch, config, image_height)
            classified_boxes.extend(batch_results)

            # Small delay between batches to avoid rate limits
            if i + batch_size < len(ocr_boxes):
                await asyncio.sleep(0.5)

        logger.info(f"Filtered {len(ocr_boxes)} boxes in {num_batches} API call(s)")

    else:
        # Legacy single-box mode
        logger.info("Using legacy single-box mode")
        batch_size = 5  # Process 5 at a time to avoid rate limits

        for i in range(0, len(ocr_boxes), batch_size):
            batch = ocr_boxes[i:i + batch_size]

            tasks = [
                classify_single_box(client, box, config, image_height)
                for box in batch
            ]

            batch_results = await asyncio.gather(*tasks)
            classified_boxes.extend(batch_results)

            # Small delay between batches
            if i + batch_size < len(ocr_boxes):
                await asyncio.sleep(1)

    # Filter KEEP only
    kept_boxes = [
        box for box in classified_boxes
        if box.get("filter_decision") == "KEEP"
    ]

    logger.info(f"Kept {len(kept_boxes)}/{len(ocr_boxes)} boxes after filtering")

    # Log dropped boxes
    dropped_boxes = [
        box for box in classified_boxes
        if box.get("filter_decision") == "DROP"
    ]

    for box in dropped_boxes:
        logger.debug(
            f"Dropped: '{box['text']}' - "
            f"{box.get('filter_category')} "
            f"({box.get('filter_confidence', 0):.2f})"
        )

    return kept_boxes
