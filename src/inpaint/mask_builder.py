"""Build inpainting masks from OCR boxes."""
import logging
from typing import List, Dict, Any
import numpy as np
import cv2

logger = logging.getLogger(__name__)


def build_mask_for_panel(
    image_shape: tuple,
    boxes: List[Dict[str, Any]],
    dilation: int = 5
) -> np.ndarray:
    """
    Build binary mask for text regions.

    Args:
        image_shape: (height, width) of image
        boxes: List of OCR boxes to mask
        dilation: Pixels to dilate mask (to ensure full coverage)

    Returns:
        Binary mask (255 = inpaint, 0 = keep)
    """
    height, width = image_shape[:2]

    # Create blank mask
    mask = np.zeros((height, width), dtype=np.uint8)

    # Draw boxes
    for box in boxes:
        x = int(box['x'])
        y = int(box['y'])
        w = int(box['w'])
        h = int(box['h'])

        # Ensure coordinates are valid
        x = max(0, x)
        y = max(0, y)
        w = min(w, width - x)
        h = min(h, height - y)

        # Fill rectangle
        cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)

    # Dilate mask slightly
    if dilation > 0:
        kernel = np.ones((dilation, dilation), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=1)

    return mask


def merge_overlapping_masks(mask1: np.ndarray, mask2: np.ndarray) -> np.ndarray:
    """
    Merge two masks using OR operation.

    Args:
        mask1: First mask
        mask2: Second mask

    Returns:
        Merged mask
    """
    return cv2.bitwise_or(mask1, mask2)
