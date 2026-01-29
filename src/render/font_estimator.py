"""Estimate font properties from original text box."""
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


def estimate_font_size(box_height: int, size_multiplier: float = 0.8) -> int:
    """
    Estimate font size from box height.

    Args:
        box_height: Height of text bounding box
        size_multiplier: Multiplier for font size (default 0.8)

    Returns:
        Estimated font size in pixels
    """
    font_size = int(box_height * size_multiplier)

    # Clamp to reasonable range
    font_size = max(12, min(font_size, 100))

    return font_size


def estimate_font_properties(box: Dict) -> Dict[str, any]:
    """
    Estimate font properties from OCR box.

    Args:
        box: OCR box dictionary

    Returns:
        Dictionary with font properties
    """
    height = box['h']
    width = box['w']

    # Estimate font size
    font_size = estimate_font_size(height)

    # Heuristic: tall text might be bold
    aspect_ratio = width / height if height > 0 else 1.0
    is_bold = aspect_ratio > 2.0  # Wide text might be bold

    # Default to sans-serif for manhwa
    font_family = "sans-serif"

    # Text color: default to black, but could be white for dark backgrounds
    # (would need background analysis for accuracy)
    text_color = (0, 0, 0)  # Black
    outline_color = (255, 255, 255)  # White outline

    return {
        "font_size": font_size,
        "is_bold": is_bold,
        "font_family": font_family,
        "text_color": text_color,
        "outline_color": outline_color,
        "has_outline": True  # Manhwa typically has outlined text
    }


def calculate_text_dimensions(
    text: str,
    font_size: int,
    max_width: int
) -> Tuple[int, int]:
    """
    Calculate text dimensions with word wrapping.

    Args:
        text: Text to render
        font_size: Font size
        max_width: Maximum width

    Returns:
        (width, height) tuple
    """
    # Simple heuristic: assume average character width is 0.6 * font_size
    avg_char_width = font_size * 0.6
    chars_per_line = max(1, int(max_width / avg_char_width))

    # Estimate number of lines needed
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        if len(current_line) + len(word) + 1 <= chars_per_line:
            current_line += word + " "
        else:
            if current_line:
                lines.append(current_line.strip())
            current_line = word + " "

    if current_line:
        lines.append(current_line.strip())

    num_lines = len(lines) if lines else 1

    # Calculate dimensions
    height = num_lines * int(font_size * 1.2)  # Line height = font_size * 1.2
    width = max_width

    return (width, height)
