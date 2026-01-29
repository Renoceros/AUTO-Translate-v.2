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
        boxes: List of OCR boxes to mask (supports both polygon and xywh)
        dilation: Pixels to dilate mask (to ensure full coverage)

    Returns:
        Binary mask (255 = inpaint, 0 = keep)
    """
    height, width = image_shape[:2]

    # Create blank mask
    mask = np.zeros((height, width), dtype=np.uint8)

    # Draw boxes
    for box in boxes:
        # Prefer polygon if available (more accurate)
        if 'polygon' in box and box['polygon'] and len(box['polygon']) >= 3:
            # Use polygon for more accurate mask
            polygon = box['polygon']
            pts = np.array(polygon, dtype=np.int32)

            # Ensure coordinates are valid
            pts[:, 0] = np.clip(pts[:, 0], 0, width - 1)
            pts[:, 1] = np.clip(pts[:, 1], 0, height - 1)

            # Fill polygon
            cv2.fillPoly(mask, [pts], 255)
        else:
            # Fallback to rectangle
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
