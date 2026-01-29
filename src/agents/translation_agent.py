"""LLM-based translation agent."""
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional

from anthropic import AsyncAnthropic

from src.config import Config


logger = logging.getLogger(__name__)


TRANSLATION_AGENT_PROMPT_SINGLE = """You are a Korean→English manhwa translator.

Your task: Translate Korean dialogue preserving tone, context, and character voice.

Guidelines:
- Preserve emotional tone (casual, formal, dramatic, comedic)
- Maintain character naming consistency
- Use natural English (not overly literal)
- Keep similar length to original if possible
- For onomatopoeia (SFX), adapt to English equivalents or keep Korean

Context:
Previous dialogue: {{prev_dialogue}}
Current text: {{current_text}}
Next dialogue: {{next_dialogue}}

Character glossary (if available):
{{character_names}}

Input:
{
  "original": "{{korean_text}}",
  "context_before": ["...", "..."],
  "context_after": ["...", "..."]
}

Output (JSON only):
{
  "translated": "English translation",
  "tone": "casual|formal|dramatic|comedic",
  "notes": "translator notes (optional)"
}
"""

TRANSLATION_AGENT_PROMPT_BATCH = """You are a Korean→English manhwa translator.

Your task: Translate multiple Korean dialogue boxes preserving tone, context, and character voice across the entire conversation.

Guidelines:
- Preserve emotional tone (casual, formal, dramatic, comedic)
- Maintain character naming consistency throughout ALL translations
- Use natural English (not overly literal)
- Keep similar length to original if possible
- Consider the full conversation flow for better context
- Ensure consistency in terminology and character voices

Input: Array of text boxes with IDs (in reading order)
Output: JSON array with same IDs, one translation per box

Output format (JSON array only):
[
  {
    "id": 0,
    "translated": "English translation here",
    "tone": "casual"
  },
  {
    "id": 1,
    "translated": "Another translation",
    "tone": "formal"
  }
]
"""


async def translate_single_box(
    client: AsyncAnthropic,
    box: Dict[str, Any],
    context_boxes: List[Dict[str, Any]],
    config: Config
) -> Dict[str, Any]:
    """
    Translate single OCR box with context.

    Args:
        client: Anthropic client
        box: OCR box to translate
        context_boxes: All boxes for context
        config: Configuration

    Returns:
        Box with translation added
    """
    # Find context boxes (±N boxes around current)
    box_idx = context_boxes.index(box)
    window_size = config.translation.context_window_size

    context_before = []
    for i in range(max(0, box_idx - window_size), box_idx):
        context_before.append(context_boxes[i]['text'])

    context_after = []
    for i in range(box_idx + 1, min(len(context_boxes), box_idx + window_size + 1)):
        context_after.append(context_boxes[i]['text'])

    # Build prompt
    user_message = json.dumps({
        "original": box['text'],
        "context_before": context_before,
        "context_after": context_after
    }, ensure_ascii=False)

    try:
        response = await client.messages.create(
            model=config.llm.model,
            max_tokens=config.llm.max_tokens,
            temperature=config.llm.temperature,
            system=TRANSLATION_AGENT_PROMPT_SINGLE,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        # Parse response
        response_text = response.content[0].text

        # Extract JSON
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract from code block
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                logger.warning(f"Failed to parse translation response: {response_text}")
                # Fallback: use original text
                result = {
                    "translated": box['text'],
                    "tone": "unknown",
                    "notes": "Failed to parse response"
                }

        return {
            **box,
            "translated": result["translated"],
            "tone": result.get("tone", "unknown"),
            "translation_notes": result.get("notes", "")
        }

    except Exception as e:
        logger.error(f"Translation failed for box: {e}")
        return {
            **box,
            "translated": box['text'],  # Fallback to original
            "tone": "unknown",
            "translation_notes": f"Error: {str(e)}"
        }


async def translate_box_batch(
    client: AsyncAnthropic,
    boxes: List[Dict[str, Any]],
    config: Config
) -> List[Dict[str, Any]]:
    """
    Translate multiple OCR boxes with single LLM call.

    Args:
        client: Anthropic client
        boxes: List of OCR box dictionaries (in reading order)
        config: Configuration

    Returns:
        List of translation results with same indices
    """
    if not boxes:
        return []

    # Build batch input with all boxes for full context
    batch_input = []
    for idx, box in enumerate(boxes):
        batch_input.append({
            "id": idx,
            "original": box['text']
        })

    user_message = json.dumps(batch_input, ensure_ascii=False)

    try:
        response = await client.messages.create(
            model=config.llm.model,
            max_tokens=config.agents.max_tokens,
            temperature=config.llm.temperature,
            system=TRANSLATION_AGENT_PROMPT_BATCH,
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
                logger.warning(f"Failed to parse batch translation response, falling back to single-box processing")
                # Fall back to single-box processing
                return await _translate_boxes_individually(client, boxes, config)

        # Match results back to boxes by ID
        results_by_id = {r["id"]: r for r in results}

        translated_boxes = []
        for idx, box in enumerate(boxes):
            result = results_by_id.get(idx)
            if result:
                translated_boxes.append({
                    **box,
                    "translated": result["translated"],
                    "tone": result.get("tone", "unknown"),
                    "translation_notes": result.get("notes", "")
                })
            else:
                # Fallback if ID missing
                logger.warning(f"Missing translation for box ID {idx}, using original text")
                translated_boxes.append({
                    **box,
                    "translated": box['text'],
                    "tone": "unknown",
                    "translation_notes": "Missing from batch response"
                })

        return translated_boxes

    except Exception as e:
        logger.error(f"Batch translation failed: {e}, falling back to single-box processing")
        # Fall back to individual processing
        return await _translate_boxes_individually(client, boxes, config)


async def _translate_boxes_individually(
    client: AsyncAnthropic,
    boxes: List[Dict[str, Any]],
    config: Config
) -> List[Dict[str, Any]]:
    """
    Translate boxes individually as fallback.

    Args:
        client: Anthropic client
        boxes: List of OCR boxes
        config: Configuration

    Returns:
        Translated boxes
    """
    tasks = [
        translate_single_box(client, box, boxes, config)
        for box in boxes
    ]
    return await asyncio.gather(*tasks)


async def translate_text_boxes(
    filtered_boxes: List[Dict[str, Any]],
    config: Config
) -> List[Dict[str, Any]]:
    """
    Translate filtered OCR boxes using LLM agent.

    Args:
        filtered_boxes: List of filtered OCR boxes
        config: Configuration

    Returns:
        Boxes with translations added
    """
    if not filtered_boxes:
        return []

    logger.info(f"Translating {len(filtered_boxes)} text boxes...")

    # Initialize Anthropic client
    client = AsyncAnthropic(api_key=config.anthropic_api_key)

    translated_boxes = []

    if config.agents.use_batch_mode:
        # Batch processing mode - process multiple boxes per API call
        batch_size = config.agents.batch_size
        num_batches = (len(filtered_boxes) + batch_size - 1) // batch_size

        logger.info(f"Processing {len(filtered_boxes)} boxes in {num_batches} batch(es) of up to {batch_size}")

        for i in range(0, len(filtered_boxes), batch_size):
            batch = filtered_boxes[i:i + batch_size]
            batch_num = i // batch_size + 1

            logger.info(f"Translating batch {batch_num}/{num_batches} ({len(batch)} boxes)")

            batch_results = await translate_box_batch(client, batch, config)
            translated_boxes.extend(batch_results)

            # Small delay between batches to avoid rate limits
            if i + batch_size < len(filtered_boxes):
                await asyncio.sleep(0.5)

        logger.info(f"Translated {len(filtered_boxes)} boxes in {num_batches} API call(s)")

    else:
        # Legacy single-box mode
        logger.info("Using legacy single-box mode")
        batch_size = 5

        for i in range(0, len(filtered_boxes), batch_size):
            batch = filtered_boxes[i:i + batch_size]

            tasks = [
                translate_single_box(client, box, filtered_boxes, config)
                for box in batch
            ]

            batch_results = await asyncio.gather(*tasks)
            translated_boxes.extend(batch_results)

            # Small delay between batches
            if i + batch_size < len(filtered_boxes):
                await asyncio.sleep(1)

    logger.info(f"Translation complete: {len(translated_boxes)} boxes")

    # Log translations
    for box in translated_boxes:
        logger.debug(
            f"'{box['text']}' → '{box.get('translated', '')}' "
            f"[{box.get('tone', 'unknown')}]"
        )

    return translated_boxes
