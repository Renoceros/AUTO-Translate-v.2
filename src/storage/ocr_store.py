"""OCR metadata storage (CSV/SQLite)."""
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.config import Config


logger = logging.getLogger(__name__)


class OCRStore:
    """OCR box metadata storage."""

    def __init__(self, config: Config):
        self.config = config
        self.csv_path = config.workspace_dir / "ocr" / "ocr_boxes.csv"

        # Ensure directory exists
        self.csv_path.parent.mkdir(exist_ok=True, parents=True)

    def save_boxes(self, boxes: List[Dict[str, Any]], image_id: str = "stitched"):
        """
        Save OCR boxes to CSV.

        Args:
            boxes: List of OCR box dictionaries
            image_id: Image identifier
        """
        # Write CSV
        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'image_id', 'box_id', 'x', 'y', 'w', 'h',
                'text', 'confidence', 'panel_index'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for i, box in enumerate(boxes):
                writer.writerow({
                    'image_id': image_id,
                    'box_id': i,
                    'x': box['x'],
                    'y': box['y'],
                    'w': box['w'],
                    'h': box['h'],
                    'text': box['text'],
                    'confidence': box['confidence'],
                    'panel_index': box.get('panel_index', 0)
                })

        logger.info(f"Saved {len(boxes)} OCR boxes to {self.csv_path}")

    def load_boxes(self, image_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Load OCR boxes from CSV.

        Args:
            image_id: Optional image ID filter

        Returns:
            List of OCR box dictionaries
        """
        if not self.csv_path.exists():
            logger.warning(f"OCR store not found: {self.csv_path}")
            return []

        boxes = []

        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                if image_id and row['image_id'] != image_id:
                    continue

                box = {
                    'image_id': row['image_id'],
                    'box_id': int(row['box_id']),
                    'x': int(row['x']),
                    'y': int(row['y']),
                    'w': int(row['w']),
                    'h': int(row['h']),
                    'text': row['text'],
                    'confidence': float(row['confidence']),
                    'panel_index': int(row['panel_index'])
                }
                boxes.append(box)

        logger.info(f"Loaded {len(boxes)} OCR boxes from {self.csv_path}")
        return boxes

    def query_by_panel(self, panel_index: int) -> List[Dict[str, Any]]:
        """
        Query boxes by panel index.

        Args:
            panel_index: Panel index to filter

        Returns:
            List of OCR boxes for panel
        """
        all_boxes = self.load_boxes()
        return [box for box in all_boxes if box['panel_index'] == panel_index]

    def filter_by_confidence(self, min_confidence: float) -> List[Dict[str, Any]]:
        """
        Filter boxes by confidence threshold.

        Args:
            min_confidence: Minimum confidence

        Returns:
            Filtered boxes
        """
        all_boxes = self.load_boxes()
        return [box for box in all_boxes if box['confidence'] >= min_confidence]
