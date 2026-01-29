"""OCR-based captcha solving."""
import logging
from pathlib import Path
from typing import Optional
import cv2
import numpy as np

logger = logging.getLogger(__name__)


async def detect_captcha(page) -> Optional[dict]:
    """
    Detect captcha on Playwright page.

    Args:
        page: Playwright page object

    Returns:
        Captcha info dict or None if no captcha found
    """
    # Common captcha selectors
    selectors = [
        "img.captcha_img",
        "img.captcha-img",
        "img[class*='captcha']",
        ".captcha_box img",
        "#captcha img",
        "img[alt*='captcha']",
    ]

    for selector in selectors:
        try:
            elem = await page.query_selector(selector)
            if elem:
                logger.info(f"Captcha detected with selector: {selector}")
                return {
                    "element": elem,
                    "selector": selector
                }
        except Exception:
            continue

    return None


async def solve_captcha(page, captcha_info: dict) -> bool:
    """
    Attempt to solve captcha using OCR.

    Args:
        page: Playwright page object
        captcha_info: Captcha detection info

    Returns:
        True if captcha solved successfully
    """
    try:
        # Screenshot captcha element
        captcha_elem = captcha_info["element"]
        screenshot_bytes = await captcha_elem.screenshot()

        # Save temporarily
        temp_path = Path("workspace/temp_captcha.png")
        temp_path.parent.mkdir(exist_ok=True, parents=True)

        with open(temp_path, "wb") as f:
            f.write(screenshot_bytes)

        # Preprocess image
        processed = preprocess_captcha(str(temp_path))

        # OCR with PaddleOCR (digits only)
        captcha_text = ocr_captcha(processed)

        if not captcha_text:
            logger.warning("Could not extract captcha text")
            return False

        logger.info(f"Extracted captcha text: {captcha_text}")

        # Find input field and submit button
        input_selectors = [
            "input[name*='captcha']",
            "input[id*='captcha']",
            "input[class*='captcha']",
            "input[type='text']",
        ]

        input_elem = None
        for selector in input_selectors:
            input_elem = await page.query_selector(selector)
            if input_elem:
                break

        if not input_elem:
            logger.warning("Could not find captcha input field")
            return False

        # Fill captcha
        await input_elem.fill(captcha_text)

        # Find and click submit button
        submit_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Submit')",
            "button:has-text('확인')",  # Korean "OK"
        ]

        for selector in submit_selectors:
            try:
                submit_btn = await page.query_selector(selector)
                if submit_btn:
                    await submit_btn.click()
                    logger.info("Captcha submitted")
                    return True
            except Exception:
                continue

        # If no submit button, try pressing Enter
        await input_elem.press("Enter")
        logger.info("Captcha submitted via Enter key")
        return True

    except Exception as e:
        logger.error(f"Captcha solving failed: {e}")
        return False


def preprocess_captcha(image_path: str) -> np.ndarray:
    """
    Preprocess captcha image for better OCR.

    Args:
        image_path: Path to captcha image

    Returns:
        Preprocessed image array
    """
    # Read image
    img = cv2.imread(image_path)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Threshold
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    # Denoise
    denoised = cv2.fastNlMeansDenoising(binary, None, 10, 7, 21)

    # Morphology operations
    kernel = np.ones((2, 2), np.uint8)
    morph = cv2.morphologyEx(denoised, cv2.MORPH_CLOSE, kernel)

    return morph


def ocr_captcha(image: np.ndarray) -> Optional[str]:
    """
    Run OCR on preprocessed captcha image.

    Args:
        image: Preprocessed captcha image

    Returns:
        Extracted text or None
    """
    try:
        from paddleocr import PaddleOCR

        # Initialize OCR (digits only)
        ocr = PaddleOCR(
            use_angle_cls=False,
            lang='en',
            use_gpu=False,
            show_log=False
        )

        # Run OCR
        result = ocr.ocr(image, cls=False)

        if not result or not result[0]:
            return None

        # Extract text (digits only)
        text = ""
        for line in result[0]:
            if len(line) >= 2:
                detected_text = line[1][0]
                # Filter only digits
                digits = "".join(c for c in detected_text if c.isdigit())
                text += digits

        return text if text else None

    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return None
