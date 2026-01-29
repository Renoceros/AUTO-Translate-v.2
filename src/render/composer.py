"""Compose final translated images."""
import asyncio
import logging
from pathlib import Path
from typing import List
import cv2
from PIL import Image

from src.config import Config


logger = logging.getLogger(__name__)


async def compose_final_images(
    rendered_paths: List[Path],
    config: Config
) -> List[Path]:
    """
    Compose final translated chapter images.

    For now, this simply copies rendered panels to final directory.
    Could be extended to reassemble into original panel structure.

    Args:
        rendered_paths: List of rendered panel paths
        config: Configuration

    Returns:
        List of final image paths
    """
    logger.info(f"Composing final images from {len(rendered_paths)} panels...")

    output_dir = config.workspace_dir / "final"
    output_dir.mkdir(exist_ok=True, parents=True)

    final_paths = []

    # Copy rendered panels to final directory
    import shutil

    for i, rendered_path in enumerate(rendered_paths):
        output_path = output_dir / f"page_{i:04d}.png"
        shutil.copy(rendered_path, output_path)
        final_paths.append(output_path)
        logger.debug(f"Finalized: {output_path.name}")

    logger.info(f"Composition complete: {len(final_paths)} final images")

    return final_paths


async def reassemble_full_chapter(
    rendered_paths: List[Path],
    config: Config,
    output_name: str = "full_chapter_translated.png"
) -> Path:
    """
    Reassemble rendered panels into single full chapter image.

    Args:
        rendered_paths: List of rendered panel paths
        config: Configuration
        output_name: Output filename

    Returns:
        Path to reassembled image
    """
    logger.info("Reassembling full chapter image...")

    # Load all panels
    panels = []
    for path in rendered_paths:
        try:
            img = Image.open(path)
            panels.append(img.convert("RGB"))
        except Exception as e:
            logger.error(f"Failed to load panel {path}: {e}")
            continue

    if not panels:
        raise ValueError("No panels to reassemble")

    # Find max width
    max_width = max(img.width for img in panels)

    # Calculate total height
    total_height = sum(img.height for img in panels)

    # Create canvas
    full_image = Image.new("RGB", (max_width, total_height), color=(255, 255, 255))

    # Stitch panels
    current_y = 0
    for panel in panels:
        # Center-align
        x_offset = (max_width - panel.width) // 2
        full_image.paste(panel, (x_offset, current_y))
        current_y += panel.height

    # Save
    output_path = config.workspace_dir / "final" / output_name
    full_image.save(output_path, "PNG")

    logger.info(f"Full chapter saved: {output_path}")

    return output_path
