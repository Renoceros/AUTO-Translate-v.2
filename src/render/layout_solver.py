"""Text layout and fitting solver."""
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


def wrap_text(
    text: str,
    max_chars_per_line: int
) -> List[str]:
    """
    Wrap text to fit within max characters per line.

    Args:
        text: Text to wrap
        max_chars_per_line: Maximum characters per line

    Returns:
        List of text lines
    """
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + word + " "

        if len(test_line) <= max_chars_per_line:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line.strip())
            current_line = word + " "

    if current_line:
        lines.append(current_line.strip())

    return lines if lines else [text]


def fit_text_to_box(
    text: str,
    box_width: int,
    box_height: int,
    initial_font_size: int,
    min_font_size: int = 12
) -> Tuple[List[str], int]:
    """
    Fit text into bounding box with adaptive font sizing.

    Args:
        text: Text to fit
        box_width: Width of box
        box_height: Height of box
        initial_font_size: Starting font size
        min_font_size: Minimum allowed font size

    Returns:
        Tuple of (wrapped_lines, final_font_size)
    """
    font_size = initial_font_size

    while font_size >= min_font_size:
        # Estimate characters per line
        avg_char_width = font_size * 0.6
        chars_per_line = max(1, int(box_width / avg_char_width))

        # Wrap text
        lines = wrap_text(text, chars_per_line)

        # Estimate height
        line_height = font_size * 1.2
        total_height = len(lines) * line_height

        # Check if fits
        if total_height <= box_height:
            return lines, font_size

        # Reduce font size
        font_size -= 2

    # If can't fit even at minimum, return with min font size
    avg_char_width = min_font_size * 0.6
    chars_per_line = max(1, int(box_width / avg_char_width))
    lines = wrap_text(text, chars_per_line)

    logger.warning(f"Text may overflow box: '{text[:30]}...'")

    return lines, min_font_size


def center_text_in_box(
    text_width: int,
    text_height: int,
    box_width: int,
    box_height: int
) -> Tuple[int, int]:
    """
    Calculate centered position for text in box.

    Args:
        text_width: Width of rendered text
        text_height: Height of rendered text
        box_width: Width of bounding box
        box_height: Height of bounding box

    Returns:
        (x_offset, y_offset) from box origin
    """
    x_offset = (box_width - text_width) // 2
    y_offset = (box_height - text_height) // 2

    # Ensure non-negative
    x_offset = max(0, x_offset)
    y_offset = max(0, y_offset)

    return (x_offset, y_offset)
