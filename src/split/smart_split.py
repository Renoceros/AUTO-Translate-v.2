"""Smart split algorithm to avoid cutting through text."""
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any
import numpy as np
from PIL import Image
import cv2

from src.config import Config


logger = logging.getLogger(__name__)


def find_whitespace_lines(image: np.ndarray, min_height: int = 20) -> List[int]:
    """
    Find horizontal whitespace lines in image.

    Args:
        image: Image array
        min_height: Minimum whitespace height in pixels

    Returns:
        List of y-coordinates for whitespace lines
    """
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    height = gray.shape[0]

    # Find rows that are mostly white
    whitespace_rows = []

    for y in range(height):
        row = gray[y, :]
        # Consider row as whitespace if >95% of pixels are white (>240)
        white_ratio = np.sum(row > 240) / len(row)

        if white_ratio > 0.95:
            whitespace_rows.append(y)

    # Group consecutive whitespace rows
    if not whitespace_rows:
        return []

    whitespace_sections = []
    current_section_start = whitespace_rows[0]
    prev_y = whitespace_rows[0]

    for y in whitespace_rows[1:]:
        if y - prev_y > 1:
            # New section
            section_height = prev_y - current_section_start + 1
            if section_height >= min_height:
                # Use middle of whitespace section
                whitespace_sections.append((current_section_start + prev_y) // 2)

            current_section_start = y

        prev_y = y

    # Add last section
    section_height = prev_y - current_section_start + 1
    if section_height >= min_height:
        whitespace_sections.append((current_section_start + prev_y) // 2)

    logger.info(f"Found {len(whitespace_sections)} whitespace sections")

    return whitespace_sections


def is_safe_cut(cut_y: int, ocr_boxes: List[Dict[str, Any]], min_margin: int) -> bool:
    """
    Check if cut line is safe (doesn't intersect or too close to text).

    Args:
        cut_y: Y-coordinate of proposed cut
        ocr_boxes: List of OCR boxes
        min_margin: Minimum margin from text in pixels

    Returns:
        True if cut is safe
    """
    for box in ocr_boxes:
        box_top = box["y"]
        box_bottom = box["y"] + box["h"]

        # Check if cut intersects box
        if box_top <= cut_y <= box_bottom:
            return False

        # Check if cut is too close to box
        if abs(cut_y - box_top) < min_margin:
            return False
        if abs(cut_y - box_bottom) < min_margin:
            return False

    return True


def select_balanced_cuts(safe_cuts: List[int], max_subpanels: int) -> List[int]:
    """
    Select balanced cuts to limit number of sub-panels.

    Args:
        safe_cuts: List of safe cut y-coordinates
        max_subpanels: Maximum number of sub-panels

    Returns:
        Selected cuts
    """
    if len(safe_cuts) + 1 <= max_subpanels:
        return safe_cuts

    # Select evenly spaced cuts
    step = len(safe_cuts) / (max_subpanels - 1)
    selected = []

    for i in range(max_subpanels - 1):
        idx = int(i * step)
        selected.append(safe_cuts[idx])

    return selected


async def smart_split(
    stitched_path: Path,
    ocr_boxes: List[Dict[str, Any]],
    config: Config
) -> List[Path]:
    """
    Smart split stitched image at safe cut lines.

    Args:
        stitched_path: Path to stitched image
        ocr_boxes: OCR boxes from pass 1
        config: Configuration

    Returns:
        List of split image paths
    """
    logger.info("Running smart split algorithm...")

    # Load stitched image
    image = Image.open(stitched_path)
    img_array = np.array(image)
    height = img_array.shape[0]

    logger.info(f"Image dimensions: {image.width}x{height}")

    # Step 1: Find whitespace lines
    whitespace_lines = find_whitespace_lines(
        img_array,
        min_height=config.smart_split.min_whitespace_height
    )

    if not whitespace_lines:
        logger.warning("No whitespace lines found, will not split")
        # Return original image as single panel
        output_dir = config.workspace_dir / "splits"
        output_dir.mkdir(exist_ok=True, parents=True)
        output_path = output_dir / "panel_0000.png"
        image.save(output_path)
        return [output_path]

    # Step 2: Filter safe cuts
    safe_cuts = []
    for y in whitespace_lines:
        if is_safe_cut(y, ocr_boxes, config.smart_split.min_margin_from_text):
            safe_cuts.append(y)

    logger.info(f"Found {len(safe_cuts)} safe cut lines")

    if not safe_cuts:
        logger.warning("No safe cuts found, will not split")
        output_dir = config.workspace_dir / "splits"
        output_dir.mkdir(exist_ok=True, parents=True)
        output_path = output_dir / "panel_0000.png"
        image.save(output_path)
        return [output_path]

    # Step 3: Balance cuts
    if len(safe_cuts) + 1 > config.smart_split.max_subpanels:
        logger.info(f"Limiting to {config.smart_split.max_subpanels} sub-panels")
        safe_cuts = select_balanced_cuts(safe_cuts, config.smart_split.max_subpanels)

    logger.info(f"Using {len(safe_cuts)} cut lines for {len(safe_cuts) + 1} sub-panels")

    # Step 4: Split image
    output_dir = config.workspace_dir / "splits"
    output_dir.mkdir(exist_ok=True, parents=True)

    split_paths = []
    prev_y = 0

    for i, cut_y in enumerate(safe_cuts):
        # Crop sub-panel
        sub_panel = image.crop((0, prev_y, image.width, cut_y))

        # Save
        output_path = output_dir / f"panel_{i:04d}.png"
        sub_panel.save(output_path)
        split_paths.append(output_path)

        prev_y = cut_y

    # Add last panel
    last_panel = image.crop((0, prev_y, image.width, height))
    output_path = output_dir / f"panel_{len(safe_cuts):04d}.png"
    last_panel.save(output_path)
    split_paths.append(output_path)

    logger.info(f"Split into {len(split_paths)} sub-panels")

    # Save cut coordinates if debug mode
    if config.debug.save_artifacts:
        cuts_file = output_dir / "cut_coordinates.txt"
        with open(cuts_file, 'w') as f:
            f.write("y_coordinate\n")
            for cut_y in safe_cuts:
                f.write(f"{cut_y}\n")

    return split_paths
