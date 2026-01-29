"""Vertical panel stitcher."""
import logging
from pathlib import Path
from typing import List, Tuple
import numpy as np
from PIL import Image

from src.config import Config


logger = logging.getLogger(__name__)


async def stitch_panels(panel_paths: List[Path], config: Config) -> Tuple[Path, List[Tuple[int, int, int]]]:
    """
    Stitch panels vertically into single image.

    Args:
        panel_paths: List of panel image paths (in order)
        config: Configuration

    Returns:
        Tuple of (stitched_image_path, coordinate_mapping)
        coordinate_mapping: List of (y_start, y_end, panel_index)
    """
    if not panel_paths:
        raise ValueError("No panels to stitch")

    logger.info(f"Stitching {len(panel_paths)} panels...")

    # Load all panels
    panels = []
    for path in panel_paths:
        try:
            img = Image.open(path)
            panels.append(img.convert("RGB"))
        except Exception as e:
            logger.error(f"Failed to load panel {path}: {e}")
            continue

    if not panels:
        raise ValueError("No valid panels loaded")

    # Find maximum width
    max_width = max(img.width for img in panels)
    logger.info(f"Max panel width: {max_width}px")

    # Calculate total height
    total_height = sum(img.height for img in panels)
    logger.info(f"Total stitched height: {total_height}px")

    # Create blank canvas
    stitched = Image.new("RGB", (max_width, total_height), color=(255, 255, 255))

    # Stitch panels with coordinate mapping
    coord_map = []
    current_y = 0

    for i, panel in enumerate(panels):
        # Center-align panel
        x_offset = (max_width - panel.width) // 2

        # Paste panel
        stitched.paste(panel, (x_offset, current_y))

        # Record coordinates
        y_start = current_y
        y_end = current_y + panel.height
        coord_map.append((y_start, y_end, i))

        current_y = y_end

    # Save stitched image
    output_dir = config.workspace_dir / "stitched"
    output_dir.mkdir(exist_ok=True, parents=True)
    output_path = output_dir / "full_chapter.png"

    stitched.save(output_path, "PNG")
    logger.info(f"Stitched image saved: {output_path}")

    # Log coordinate mapping
    if config.debug.save_artifacts:
        map_file = output_dir / "coordinate_map.txt"
        with open(map_file, 'w') as f:
            f.write("y_start,y_end,panel_index\n")
            for y_start, y_end, panel_idx in coord_map:
                f.write(f"{y_start},{y_end},{panel_idx}\n")

    return output_path, coord_map
