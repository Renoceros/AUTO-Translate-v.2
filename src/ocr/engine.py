"""OCR engine wrapper for PaddleOCR and EasyOCR."""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import asyncio
import numpy as np
from PIL import Image
import cv2

from src.config import Config
from src.ocr.preprocess import preprocess_for_ocr, preprocess_pil_image
from src.ocr.postprocess import clean_ocr_text, filter_by_confidence


logger = logging.getLogger(__name__)


class OCRBox:
    """OCR result box."""

    def __init__(self, x: int, y: int, w: int, h: int, text: str, confidence: float, panel_index: int = 0):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.text = text
        self.confidence = confidence
        self.panel_index = panel_index

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "x": self.x,
            "y": self.y,
            "w": self.w,
            "h": self.h,
            "text": self.text,
            "confidence": self.confidence,
            "panel_index": self.panel_index
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OCRBox":
        """Create from dictionary."""
        return cls(
            x=data["x"],
            y=data["y"],
            w=data["w"],
            h=data["h"],
            text=data["text"],
            confidence=data["confidence"],
            panel_index=data.get("panel_index", 0)
        )


class OCREngine:
    """OCR engine with PaddleOCR primary and EasyOCR fallback."""

    def __init__(self, config: Config):
        self.config = config
        self._paddle_ocr = None
        self._easy_ocr = None

    def _init_paddle_ocr(self):
        """Initialize PaddleOCR."""
        if self._paddle_ocr is None:
            try:
                from paddleocr import PaddleOCR

                logger.info("Initializing PaddleOCR...")
                self._paddle_ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang='korean',
                    use_gpu=False,
                    show_log=False
                )
                logger.info("PaddleOCR initialized")

            except Exception as e:
                logger.error(f"Failed to initialize PaddleOCR: {e}")
                raise

    def _init_easy_ocr(self):
        """Initialize EasyOCR as fallback."""
        if self._easy_ocr is None:
            try:
                import easyocr

                logger.info("Initializing EasyOCR...")
                self._easy_ocr = easyocr.Reader(['ko', 'en'], gpu=False)
                logger.info("EasyOCR initialized")

            except Exception as e:
                logger.error(f"Failed to initialize EasyOCR: {e}")
                raise

    def run_paddle_ocr(self, image: np.ndarray) -> List[OCRBox]:
        """
        Run PaddleOCR on image.

        Args:
            image: Image as numpy array

        Returns:
            List of OCR boxes
        """
        self._init_paddle_ocr()

        try:
            # Preprocess image
            preprocessed = preprocess_for_ocr(image)

            # Run OCR
            result = self._paddle_ocr.ocr(preprocessed, cls=True)

            if not result or not result[0]:
                logger.warning("PaddleOCR returned no results")
                return []

            # Parse results
            boxes = []
            for line in result[0]:
                if len(line) < 2:
                    continue

                # Extract bounding box
                bbox = line[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                text_info = line[1]  # (text, confidence)

                # Calculate box coordinates
                x_coords = [p[0] for p in bbox]
                y_coords = [p[1] for p in bbox]

                x = int(min(x_coords))
                y = int(min(y_coords))
                w = int(max(x_coords) - x)
                h = int(max(y_coords) - y)

                text = text_info[0]
                confidence = float(text_info[1])

                # Clean text
                text = clean_ocr_text(text)

                if text:
                    boxes.append(OCRBox(x, y, w, h, text, confidence))

            logger.info(f"PaddleOCR detected {len(boxes)} text boxes")
            return boxes

        except Exception as e:
            logger.error(f"PaddleOCR failed: {e}")
            return []

    def run_easy_ocr(self, image: np.ndarray) -> List[OCRBox]:
        """
        Run EasyOCR on image (fallback).

        Args:
            image: Image as numpy array

        Returns:
            List of OCR boxes
        """
        self._init_easy_ocr()

        try:
            # Preprocess
            preprocessed = preprocess_for_ocr(image)

            # Run OCR
            result = self._easy_ocr.readtext(preprocessed)

            boxes = []
            for detection in result:
                bbox = detection[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                text = detection[1]
                confidence = float(detection[2])

                # Calculate box
                x_coords = [p[0] for p in bbox]
                y_coords = [p[1] for p in bbox]

                x = int(min(x_coords))
                y = int(min(y_coords))
                w = int(max(x_coords) - x)
                h = int(max(y_coords) - y)

                text = clean_ocr_text(text)

                if text:
                    boxes.append(OCRBox(x, y, w, h, text, confidence))

            logger.info(f"EasyOCR detected {len(boxes)} text boxes")
            return boxes

        except Exception as e:
            logger.error(f"EasyOCR failed: {e}")
            return []

    def run(self, image_path: Path) -> List[OCRBox]:
        """
        Run OCR on image file.

        Args:
            image_path: Path to image

        Returns:
            List of OCR boxes
        """
        # Load image
        image = cv2.imread(str(image_path))

        if image is None:
            logger.error(f"Failed to load image: {image_path}")
            return []

        # Try primary engine
        if self.config.ocr.primary_engine == "paddleocr":
            boxes = self.run_paddle_ocr(image)

            # Fallback to EasyOCR if PaddleOCR fails
            if not boxes and self.config.ocr.fallback_engine == "easyocr":
                logger.info("Falling back to EasyOCR...")
                boxes = self.run_easy_ocr(image)

        else:
            # Use EasyOCR as primary
            boxes = self.run_easy_ocr(image)

            if not boxes and self.config.ocr.fallback_engine == "paddleocr":
                logger.info("Falling back to PaddleOCR...")
                boxes = self.run_paddle_ocr(image)

        # Filter by confidence
        boxes = [
            box for box in boxes
            if box.confidence >= self.config.ocr.confidence_threshold
        ]

        return boxes


async def run_ocr(image_path: Path, config: Config) -> List[Dict[str, Any]]:
    """
    Run OCR on single image (async wrapper).

    Args:
        image_path: Path to image
        config: Configuration

    Returns:
        List of OCR box dictionaries
    """
    engine = OCREngine(config)

    # Run in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    boxes = await loop.run_in_executor(None, engine.run, image_path)

    return [box.to_dict() for box in boxes]


async def run_ocr_batch(image_paths: List[Path], config: Config) -> List[Dict[str, Any]]:
    """
    Run OCR on multiple images.

    Args:
        image_paths: List of image paths
        config: Configuration

    Returns:
        List of all OCR boxes with panel_index set
    """
    engine = OCREngine(config)
    all_boxes = []

    for panel_index, image_path in enumerate(image_paths):
        logger.info(f"Running OCR on panel {panel_index + 1}/{len(image_paths)}")

        # Run OCR
        loop = asyncio.get_event_loop()
        boxes = await loop.run_in_executor(None, engine.run, image_path)

        # Set panel index
        for box in boxes:
            box.panel_index = panel_index
            all_boxes.append(box.to_dict())

    logger.info(f"OCR complete: {len(all_boxes)} total text boxes")

    return all_boxes
