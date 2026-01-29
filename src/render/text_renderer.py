"""Render translated text onto images."""
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from src.config import Config
from src.render.font_estimator import estimate_font_properties
from src.render.layout_solver import fit_text_to_box


logger = logging.getLogger(__name__)


def render_text_on_image(
    image: np.ndarray,
    box: Dict[str, Any],
    font_path: str,
    config: Config
) -> np.ndarray:
    """
    Render translated text onto image.

    Args:
        image: Input image (BGR)
        box: OCR box with translation
        font_path: Path to font file
        config: Configuration

    Returns:
        Image with rendered text
    """
    # Convert BGR to RGB for PIL
    pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_image)

    # Get translation
    text = box.get('translated', box.get('text', ''))

    # Estimate font properties
    font_props = estimate_font_properties(box)
    initial_font_size = font_props['font_size']

    # Fit text to box
    lines, font_size = fit_text_to_box(
        text,
        box['w'],
        box['h'],
        initial_font_size,
        min_font_size=12
    )

    # Load font
    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception as e:
        logger.warning(f"Failed to load font {font_path}: {e}, using default")
        font = ImageFont.load_default()

    # Calculate text position
    x = box['x']
    y = box['y']

    line_height = int(font_size * 1.2)

    # Render each line
    for i, line in enumerate(lines):
        line_y = y + i * line_height

        # Get text bounding box for centering
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]

        # Center horizontally in box
        line_x = x + (box['w'] - text_width) // 2

        # Draw text with outline (common in manhwa)
        if font_props.get('has_outline', True):
            # Draw outline
            outline_color = font_props['outline_color']
            for offset_x in [-2, -1, 0, 1, 2]:
                for offset_y in [-2, -1, 0, 1, 2]:
                    if offset_x != 0 or offset_y != 0:
                        draw.text(
                            (line_x + offset_x, line_y + offset_y),
                            line,
                            font=font,
                            fill=outline_color
                        )

        # Draw main text
        text_color = font_props['text_color']
        draw.text((line_x, line_y), line, font=font, fill=text_color)

    # Convert back to BGR
    result = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    return result


async def render_text_batch(
    inpainted_paths: List[Path],
    translated_boxes: List[Dict[str, Any]],
    config: Config
) -> List[Path]:
    """
    Render translated text on all panels.

    Args:
        inpainted_paths: List of inpainted panel paths
        translated_boxes: Translated OCR boxes
        config: Configuration

    Returns:
        List of rendered panel paths
    """
    logger.info(f"Rendering translated text on {len(inpainted_paths)} panels...")

    output_dir = config.workspace_dir / "rendered"
    output_dir.mkdir(exist_ok=True, parents=True)

    # Get font path
    font_path = config.fonts.default

    if not Path(font_path).exists():
        logger.warning(f"Font not found: {font_path}, will use default")
        font_path = None

    # Group boxes by panel
    boxes_by_panel = {}
    for box in translated_boxes:
        panel_idx = box.get('panel_index', 0)
        if panel_idx not in boxes_by_panel:
            boxes_by_panel[panel_idx] = []
        boxes_by_panel[panel_idx].append(box)

    # Render each panel
    rendered_paths = []

    for i, inpainted_path in enumerate(inpainted_paths):
        output_path = output_dir / f"panel_{i:04d}.png"

        # Load image
        image = cv2.imread(str(inpainted_path))

        if image is None:
            logger.error(f"Failed to load inpainted panel: {inpainted_path}")
            continue

        # Get boxes for this panel
        boxes_for_panel = boxes_by_panel.get(i, [])

        if not boxes_for_panel:
            # No text to render, just copy
            import shutil
            shutil.copy(inpainted_path, output_path)
            logger.debug(f"No text to render in panel {i}, copying...")
        else:
            # Render text
            logger.debug(f"Rendering {len(boxes_for_panel)} text boxes on panel {i}")

            for box in boxes_for_panel:
                if font_path:
                    image = render_text_on_image(image, box, font_path, config)
                else:
                    logger.warning(f"Skipping text render (no font): {box.get('translated', '')}")

            # Save
            cv2.imwrite(str(output_path), image)

        rendered_paths.append(output_path)

    logger.info(f"Rendering complete: {len(rendered_paths)} panels")

    return rendered_paths
