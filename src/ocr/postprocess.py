"""OCR result post-processing."""
import logging
import re

logger = logging.getLogger(__name__)


def clean_ocr_text(text: str) -> str:
    """
    Clean OCR output text.

    Args:
        text: Raw OCR text

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Remove extra whitespace
    cleaned = " ".join(text.split())

    # Remove common OCR artifacts
    cleaned = re.sub(r'[|~`]', '', cleaned)

    # Fix common Korean OCR errors (if needed)
    # Add specific fixes here

    return cleaned.strip()


def filter_by_confidence(ocr_boxes: list, threshold: float) -> list:
    """
    Filter OCR boxes by confidence threshold.

    Args:
        ocr_boxes: List of OCR box dictionaries
        threshold: Minimum confidence (0.0-1.0)

    Returns:
        Filtered list of OCR boxes
    """
    filtered = [
        box for box in ocr_boxes
        if box.get("confidence", 0) >= threshold
    ]

    logger.info(f"Filtered {len(ocr_boxes)} -> {len(filtered)} boxes (threshold={threshold})")

    return filtered


def merge_nearby_boxes(ocr_boxes: list, max_distance: int = 10) -> list:
    """
    Merge OCR boxes that are close together (same text bubble).

    Args:
        ocr_boxes: List of OCR box dictionaries
        max_distance: Maximum vertical distance to merge

    Returns:
        Merged list of OCR boxes
    """
    if not ocr_boxes:
        return []

    # Sort by y-coordinate
    sorted_boxes = sorted(ocr_boxes, key=lambda b: b["y"])

    merged = []
    current_group = [sorted_boxes[0]]

    for box in sorted_boxes[1:]:
        prev_box = current_group[-1]

        # Check if boxes are close vertically
        vertical_distance = abs(box["y"] - (prev_box["y"] + prev_box["h"]))

        if vertical_distance <= max_distance:
            # Add to current group
            current_group.append(box)
        else:
            # Merge current group and start new one
            merged.append(merge_box_group(current_group))
            current_group = [box]

    # Merge last group
    if current_group:
        merged.append(merge_box_group(current_group))

    logger.info(f"Merged {len(ocr_boxes)} -> {len(merged)} boxes")

    return merged


def merge_box_group(boxes: list) -> dict:
    """
    Merge a group of boxes into single box.

    Args:
        boxes: List of OCR boxes to merge

    Returns:
        Merged box dictionary
    """
    if len(boxes) == 1:
        return boxes[0]

    # Calculate bounding box from all boxes (whether they have polygons or not)
    min_x = min(b["x"] for b in boxes)
    min_y = min(b["y"] for b in boxes)
    max_x = max(b["x"] + b["w"] for b in boxes)
    max_y = max(b["y"] + b["h"] for b in boxes)

    # Concatenate text
    merged_text = " ".join(b["text"] for b in boxes)

    # Average confidence
    avg_confidence = sum(b.get("confidence", 0) for b in boxes) / len(boxes)

    # Create merged box with rectangular polygon
    merged_polygon = [
        [min_x, min_y],
        [max_x, min_y],
        [max_x, max_y],
        [min_x, max_y]
    ]

    return {
        "x": min_x,
        "y": min_y,
        "w": max_x - min_x,
        "h": max_y - min_y,
        "text": merged_text,
        "confidence": avg_confidence,
        "polygon": merged_polygon
    }
