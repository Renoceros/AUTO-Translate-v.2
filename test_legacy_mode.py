"""Test legacy single-box mode."""
import asyncio
import logging
from src.config import Config
from src.agents.filter_agent import filter_text_boxes

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """Test legacy mode with small dataset."""
    print("=" * 60)
    print("Testing Legacy Single-Box Mode")
    print("=" * 60)

    # Load config and disable batch mode
    config = Config.load()
    config.agents.use_batch_mode = False

    print(f"\nConfiguration:")
    print(f"  Batch mode: {config.agents.use_batch_mode}")

    # Small test dataset (5 boxes to avoid too many API calls)
    test_boxes = [
        {"text": "안녕하세요", "x": 100, "y": 50, "w": 80, "h": 30, "panel_index": 0},
        {"text": "뭐야!", "x": 200, "y": 100, "w": 60, "h": 35, "panel_index": 0},
        {"text": "쾅!", "x": 300, "y": 150, "w": 40, "h": 30, "panel_index": 0},
        {"text": "웹툰왕국", "x": 50, "y": 800, "w": 100, "h": 25, "panel_index": 0},
        {"text": "조심해!", "x": 190, "y": 450, "w": 70, "h": 30, "panel_index": 0},
    ]

    print(f"\nTest data: {len(test_boxes)} boxes")

    try:
        filtered = await filter_text_boxes(test_boxes, config)
        print(f"\nResults:")
        print(f"  Input boxes: {len(test_boxes)}")
        print(f"  Kept boxes: {len(filtered)}")

        print(f"\nKept boxes:")
        for i, box in enumerate(filtered, 1):
            print(f"  {i}. '{box['text']}' - {box.get('filter_category', 'unknown')}")

        print("\n" + "=" * 60)
        print("Legacy mode test completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
