"""Image preprocessing for better OCR."""
import logging
import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def preprocess_for_ocr(image: np.ndarray) -> np.ndarray:
    """
    Enhance image for better OCR results.

    Applies CLAHE, bilateral filtering, and morphology operations.

    Args:
        image: Input image (BGR or grayscale)

    Returns:
        Preprocessed image
    """
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Bilateral filter (reduces noise while preserving edges)
    filtered = cv2.bilateralFilter(enhanced, 9, 75, 75)

    # Morphology operations to enhance text
    kernel = np.ones((2, 2), np.uint8)
    morph = cv2.morphologyEx(filtered, cv2.MORPH_CLOSE, kernel)

    return morph


def preprocess_pil_image(pil_image: Image.Image) -> np.ndarray:
    """
    Preprocess PIL image for OCR.

    Args:
        pil_image: PIL Image object

    Returns:
        Preprocessed numpy array
    """
    # Convert PIL to numpy
    img_array = np.array(pil_image)

    # Convert RGB to BGR for OpenCV
    if len(img_array.shape) == 3 and img_array.shape[2] == 3:
        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

    # Preprocess
    processed = preprocess_for_ocr(img_array)

    return processed


def adaptive_threshold(image: np.ndarray) -> np.ndarray:
    """
    Apply adaptive thresholding for better text extraction.

    Args:
        image: Grayscale image

    Returns:
        Binary image
    """
    # Adaptive threshold
    binary = cv2.adaptiveThreshold(
        image,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )

    return binary


def enhance_colored_text(image: np.ndarray) -> np.ndarray:
    """
    Enhance colored/stylized text for better OCR.

    Args:
        image: Input BGR image

    Returns:
        Enhanced image
    """
    # Convert to HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Split channels
    h, s, v = cv2.split(hsv)

    # Enhance saturation and value
    s = cv2.equalizeHist(s)
    v = cv2.equalizeHist(v)

    # Merge and convert back
    enhanced_hsv = cv2.merge([h, s, v])
    enhanced = cv2.cvtColor(enhanced_hsv, cv2.COLOR_HSV2BGR)

    return enhanced
