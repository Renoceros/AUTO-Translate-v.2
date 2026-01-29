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
    """OCR result box with polygon support."""

    def __init__(
        self,
        x: int = None,
        y: int = None,
        w: int = None,
        h: int = None,
        text: str = "",
        confidence: float = 0.0,
        panel_index: int = 0,
        polygon: List[List[int]] = None
    ):
        """
        Initialize OCR box.

        Args:
            x, y, w, h: Bounding box (optional if polygon provided)
            text: OCR text
            confidence: Detection confidence
            panel_index: Panel index
            polygon: List of [x, y] points (4 points for quadrilateral)
        """
        self.text = text
        self.confidence = confidence
        self.panel_index = panel_index
        self._polygon = polygon

        # If polygon provided, compute bounding box from it
        if polygon is not None and len(polygon) >= 4:
            x_coords = [p[0] for p in polygon]
            y_coords = [p[1] for p in polygon]
            self._x = int(min(x_coords))
            self._y = int(min(y_coords))
            self._w = int(max(x_coords) - self._x)
            self._h = int(max(y_coords) - self._y)
        else:
            # Use provided xywh
            self._x = x if x is not None else 0
            self._y = y if y is not None else 0
            self._w = w if w is not None else 0
            self._h = h if h is not None else 0

    @property
    def x(self) -> int:
        """Get x coordinate."""
        return self._x

    @property
    def y(self) -> int:
        """Get y coordinate."""
        return self._y

    @property
    def w(self) -> int:
        """Get width."""
        return self._w

    @property
    def h(self) -> int:
        """Get height."""
        return self._h

    @property
    def polygon(self) -> Optional[List[List[int]]]:
        """Get polygon points (if available)."""
        return self._polygon

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "x": self.x,
            "y": self.y,
            "w": self.w,
            "h": self.h,
            "text": self.text,
            "confidence": self.confidence,
            "panel_index": self.panel_index
        }
        if self._polygon is not None:
            result["polygon"] = self._polygon
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OCRBox":
        """Create from dictionary."""
        return cls(
            x=data.get("x"),
            y=data.get("y"),
            w=data.get("w"),
            h=data.get("h"),
            text=data["text"],
            confidence=data["confidence"],
            panel_index=data.get("panel_index", 0),
            polygon=data.get("polygon")
        )


class OCREngine:
    """OCR engine with PaddleOCR primary and EasyOCR fallback."""

    def __init__(self, config: Config):
        self.config = config
        self._paddle_ocr = None
        self._easy_ocr = None

    def _init_paddle_ocr(self):
        """Initialize PaddleX OCR pipeline."""
        if self._paddle_ocr is None:
            try:
                from paddlex import create_pipeline

                logger.info("Initializing PaddleX OCR pipeline...")
                self._paddle_ocr = create_pipeline(pipeline="OCR")
                logger.info("PaddleX OCR pipeline initialized")

            except Exception as e:
                logger.error(f"Failed to initialize PaddleX: {e}")
                raise

    def _init_easy_ocr(self):
        """Initialize EasyOCR as fallback."""
        if self._easy_ocr is None:
            try:
                import easyocr

                logger.info("Initializing EasyOCR...")
                self._easy_ocr = easyocr.Reader(['ko', 'en'], gpu=True)
                logger.info("EasyOCR initialized")

            except Exception as e:
                logger.error(f"Failed to initialize EasyOCR: {e}")
                raise

    def run_paddle_ocr(self, image: np.ndarray) -> List[OCRBox]:
        """
        Run PaddleX OCR on image.

        Args:
            image: Image as numpy array

        Returns:
            List of OCR boxes
        """
        self._init_paddle_ocr()

        try:
            # Preprocess image
            preprocessed = preprocess_for_ocr(image)

            # Save to temp file (PaddleX requires file path)
            import tempfile
            import os
            from PIL import Image as PILImage

            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name
                PILImage.fromarray(preprocessed).save(tmp_path)

            try:
                # Run OCR with PaddleX
                output = self._paddle_ocr.predict(
                    input=tmp_path,
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    use_textline_orientation=False
                )

                if not output:
                    logger.warning("PaddleX OCR returned no results")
                    return []

                # Parse PaddleX result format (based on official docs)
                # Temp file must exist during iteration as predict() returns lazy generator
                boxes = []
                for result in output:
                    # According to docs: dt_polys, rec_texts, rec_scores
                    if hasattr(result, 'dt_polys') and hasattr(result, 'rec_texts') and hasattr(result, 'rec_scores'):
                        # Iterate through detected text regions
                        for bbox, text, score in zip(result.dt_polys, result.rec_texts, result.rec_scores):
                            # bbox is numpy array of shape (4, 2) with dtype int16
                            # Convert to list of [x, y] points
                            polygon = [[int(p[0]), int(p[1])] for p in bbox]

                            confidence = float(score)

                            # Clean text
                            text = clean_ocr_text(text)

                            if text:
                                # Create OCRBox with polygon (xywh computed automatically)
                                boxes.append(OCRBox(
                                    text=text,
                                    confidence=confidence,
                                    polygon=polygon
                                ))

                logger.info(f"PaddleX OCR detected {len(boxes)} text boxes")
                return boxes

            finally:
                # Clean up temp file AFTER consuming all results from generator
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            logger.error(f"PaddleX OCR failed: {e}")
            logger.exception(e)  # Log full traceback for debugging
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

                # Convert to list of [x, y] points (polygon)
                polygon = [[int(p[0]), int(p[1])] for p in bbox]

                text = clean_ocr_text(text)

                if text:
                    # Create OCRBox with polygon (xywh computed automatically)
                    boxes.append(OCRBox(
                        text=text,
                        confidence=confidence,
                        polygon=polygon
                    ))

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
