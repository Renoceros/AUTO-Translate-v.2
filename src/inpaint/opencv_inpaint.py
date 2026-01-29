"""OpenCV-based inpainting."""
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any
import cv2
import numpy as np

from src.config import Config
from src.inpaint.mask_builder import build_mask_for_panel


logger = logging.getLogger(__name__)


def inpaint_image(
    image: np.ndarray,
    mask: np.ndarray,
    method: str = "telea",
    radius: int = 5
) -> np.ndarray:
    """
    Inpaint image using OpenCV.

    Args:
        image: Input image (BGR)
        mask: Binary mask (255 = inpaint)
        method: "telea" or "ns" (Navier-Stokes)
        radius: Inpainting radius

    Returns:
        Inpainted image
    """
    if method == "telea":
        inpainted = cv2.inpaint(image, mask, radius, cv2.INPAINT_TELEA)
    else:
        inpainted = cv2.inpaint(image, mask, radius, cv2.INPAINT_NS)

    return inpainted


async def inpaint_single_panel(
    panel_path: Path,
    boxes_for_panel: List[Dict[str, Any]],
    output_path: Path,
    config: Config
) -> Path:
    """
    Inpaint single panel image.

    Args:
        panel_path: Path to panel image
        boxes_for_panel: OCR boxes to inpaint
        output_path: Output path
        config: Configuration

    Returns:
        Output path
    """
    # Load image
    image = cv2.imread(str(panel_path))

    if image is None:
        logger.error(f"Failed to load panel: {panel_path}")
        return panel_path

    # Build mask
    mask = build_mask_for_panel(
        image.shape,
        boxes_for_panel,
        dilation=config.inpaint.mask_dilation
    )

    # Inpaint
    inpainted = inpaint_image(
        image,
        mask,
        method=config.inpaint.method,
        radius=config.inpaint.radius
    )

    # Save
    cv2.imwrite(str(output_path), inpainted)

    logger.debug(f"Inpainted: {output_path.name}")

    return output_path


async def inpaint_panels(
    split_paths: List[Path],
    all_ocr_boxes: List[Dict[str, Any]],
    config: Config
) -> List[Path]:
    """
    Inpaint all split panels using all OCR detections.

    Args:
        split_paths: List of split panel paths
        all_ocr_boxes: All OCR boxes (not just filtered ones)
        config: Configuration

    Returns:
        List of inpainted panel paths

    Note:
        Uses all OCR boxes to ensure ALL detected text is removed,
        regardless of filter decisions. This prevents Korean text
        from remaining visible in the final output.
    """
    logger.info(f"Inpainting {len(split_paths)} panels with {len(all_ocr_boxes)} OCR detections...")
    logger.info(
        f"Using method={config.inpaint.method}, "
        f"radius={config.inpaint.radius}, "
        f"mask_dilation={config.inpaint.mask_dilation}"
    )

    output_dir = config.workspace_dir / "inpainted"
    output_dir.mkdir(exist_ok=True, parents=True)

    # Group boxes by panel index
    boxes_by_panel = {}
    for box in all_ocr_boxes:
        panel_idx = box.get('panel_index', 0)
        if panel_idx not in boxes_by_panel:
            boxes_by_panel[panel_idx] = []
        boxes_by_panel[panel_idx].append(box)

    # Inpaint each panel
    inpainted_paths = []

    for i, panel_path in enumerate(split_paths):
        output_path = output_dir / f"panel_{i:04d}.png"
        boxes_for_panel = boxes_by_panel.get(i, [])

        if not boxes_for_panel:
            # No text to inpaint, just copy
            import shutil
            shutil.copy(panel_path, output_path)
            logger.debug(f"No text in panel {i}, copying...")
        else:
            # Inpaint
            logger.debug(f"Inpainting panel {i} with {len(boxes_for_panel)} text boxes")
            await inpaint_single_panel(panel_path, boxes_for_panel, output_path, config)

        inpainted_paths.append(output_path)

    logger.info(f"Inpainting complete: {len(inpainted_paths)} panels")

    return inpainted_paths
