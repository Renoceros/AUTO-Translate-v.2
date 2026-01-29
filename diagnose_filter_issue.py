"""Diagnostic script to understand filter behavior."""
import asyncio
import logging
import csv
from pathlib import Path
from src.config import Config
from src.agents.filter_agent import classify_box_batch, classify_single_box
from anthropic import AsyncAnthropic

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """Compare batch vs single-box filtering."""
    print("=" * 60)
    print("Filter Agent Diagnostic")
    print("=" * 60)

    config = Config.load()
    client = AsyncAnthropic(api_key=config.anthropic_api_key)

    # Load actual OCR boxes from recent run
    ocr_file = Path("workspace/ocr/ocr_boxes.csv")

    if not ocr_file.exists():
        print(f"ERROR: {ocr_file} not found")
        return

    # Read OCR boxes
    boxes = []
    with open(ocr_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            boxes.append({
                'text': row['text'],
                'x': float(row['x']),
                'y': float(row['y']),
                'w': float(row['w']),
                'h': float(row['h']),
                'panel_index': int(row['panel_index'])
            })

    if len(boxes) < 2:
        print("Not enough OCR data for testing")
        return

    print(f"\nLoaded {len(boxes)} OCR boxes from {ocr_file}")

    # Take a sample for testing
    sample_boxes = boxes[:20] if len(boxes) > 20 else boxes

    print(f"Testing with {len(sample_boxes)} boxes:")
    for i, box in enumerate(sample_boxes):
        print(f"  {i+1}. '{box['text']}'")

    # Calculate image height
    image_height = max(box['y'] + box['h'] for box in sample_boxes) + 100

    # Test 1: Batch mode
    print("\n" + "-" * 60)
    print("TEST 1: Batch Mode")
    print("-" * 60)

    batch_results = await classify_box_batch(client, sample_boxes, config, image_height)

    batch_kept = [box for box in batch_results if box.get('filter_decision') == 'KEEP']
    batch_dropped = [box for box in batch_results if box.get('filter_decision') == 'DROP']

    print(f"\nResults: {len(batch_kept)} KEEP, {len(batch_dropped)} DROP")
    print(f"\nKept boxes:")
    for box in batch_kept:
        print(f"  - '{box['text']}' [{box.get('filter_category')}]")

    print(f"\nDropped boxes:")
    for box in batch_dropped:
        print(f"  - '{box['text']}' [{box.get('filter_category')}] - {box.get('filter_reasoning', 'no reason')}")

    # Test 2: Single-box mode (first 5 boxes only to save API calls)
    print("\n" + "-" * 60)
    print("TEST 2: Single-Box Mode (first 5 boxes)")
    print("-" * 60)

    single_results = []
    for box in sample_boxes[:5]:
        result = await classify_single_box(client, box, config, image_height)
        single_results.append(result)

    single_kept = [box for box in single_results if box.get('filter_decision') == 'KEEP']
    single_dropped = [box for box in single_results if box.get('filter_decision') == 'DROP']

    print(f"\nResults: {len(single_kept)} KEEP, {len(single_dropped)} DROP")
    print(f"\nKept boxes:")
    for box in single_kept:
        print(f"  - '{box['text']}' [{box.get('filter_category')}]")

    print(f"\nDropped boxes:")
    for box in single_dropped:
        print(f"  - '{box['text']}' [{box.get('filter_category')}] - {box.get('filter_reasoning', 'no reason')}")

    # Compare
    print("\n" + "=" * 60)
    print("COMPARISON")
    print("=" * 60)
    print(f"Batch mode keep rate: {len(batch_kept)}/{len(sample_boxes)} = {100*len(batch_kept)/len(sample_boxes):.1f}%")
    print(f"Single mode keep rate: {len(single_kept)}/5 = {100*len(single_kept)/5:.1f}%")

if __name__ == "__main__":
    asyncio.run(main())
