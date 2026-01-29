"""Test script for batch processing agents."""
import asyncio
import logging
from src.config import Config
from src.agents.filter_agent import filter_text_boxes
from src.agents.translation_agent import translate_text_boxes

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """Test batch processing with sample data."""
    print("=" * 60)
    print("Testing Batch Processing for Filter & Translation Agents")
    print("=" * 60)

    # Load config
    config = Config.load()

    print(f"\nConfiguration:")
    print(f"  Batch mode: {config.agents.use_batch_mode}")
    print(f"  Batch size: {config.agents.batch_size}")
    print(f"  Max tokens: {config.agents.max_tokens}")

    # Create test data - 15 Korean text boxes
    test_boxes = [
        {"text": "안녕하세요", "x": 100, "y": 50, "w": 80, "h": 30, "panel_index": 0},
        {"text": "뭐야... 이게 대체 뭐야!", "x": 200, "y": 100, "w": 150, "h": 40, "panel_index": 0},
        {"text": "쾅!", "x": 300, "y": 150, "w": 40, "h": 30, "panel_index": 0},
        {"text": "너는 누구니?", "x": 150, "y": 200, "w": 100, "h": 35, "panel_index": 0},
        {"text": "나는... 기억이 안 나.", "x": 180, "y": 250, "w": 120, "h": 35, "panel_index": 0},
        {"text": "가장 빠른 웹툰제공사이트\n웹툰왕국뉴토끼469", "x": 50, "y": 800, "w": 200, "h": 50, "panel_index": 0},
        {"text": "이상하네...", "x": 220, "y": 300, "w": 90, "h": 30, "panel_index": 0},
        {"text": "무슨 일이지?", "x": 170, "y": 350, "w": 95, "h": 32, "panel_index": 0},
        {"text": "터터터", "x": 400, "y": 400, "w": 50, "h": 25, "panel_index": 0},
        {"text": "조심해!", "x": 190, "y": 450, "w": 70, "h": 30, "panel_index": 0},
        {"text": "알겠어.", "x": 210, "y": 500, "w": 65, "h": 28, "panel_index": 0},
        {"text": "가자.", "x": 230, "y": 550, "w": 55, "h": 26, "panel_index": 0},
        {"text": "여기는 어디야?", "x": 160, "y": 600, "w": 110, "h": 33, "panel_index": 0},
        {"text": "모르겠어... 처음 보는 곳이야.", "x": 140, "y": 650, "w": 180, "h": 38, "panel_index": 0},
        {"text": "ㅋㅋㅋㅋ", "x": 350, "y": 700, "w": 45, "h": 24, "panel_index": 0},
    ]

    print(f"\nTest data: {len(test_boxes)} boxes")

    # Test 1: Filter Agent
    print("\n" + "-" * 60)
    print("TEST 1: Filter Agent")
    print("-" * 60)

    try:
        filtered = await filter_text_boxes(test_boxes, config)
        print(f"\nResults:")
        print(f"  Input boxes: {len(test_boxes)}")
        print(f"  Kept boxes: {len(filtered)}")
        print(f"  Dropped boxes: {len(test_boxes) - len(filtered)}")

        print(f"\nKept boxes:")
        for i, box in enumerate(filtered, 1):
            print(f"  {i}. '{box['text']}' - {box.get('filter_category', 'unknown')}")

        print(f"\nDropped boxes:")
        dropped = [box for box in test_boxes if box not in filtered]
        for i, box in enumerate(dropped, 1):
            print(f"  {i}. '{box['text']}'")

    except Exception as e:
        print(f"\nERROR in filter test: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test 2: Translation Agent
    print("\n" + "-" * 60)
    print("TEST 2: Translation Agent")
    print("-" * 60)

    try:
        translated = await translate_text_boxes(filtered, config)
        print(f"\nResults:")
        print(f"  Translated boxes: {len(translated)}")

        print(f"\nTranslations:")
        for i, box in enumerate(translated, 1):
            print(f"  {i}. '{box['text']}' → '{box.get('translated', 'N/A')}'")
            print(f"      Tone: {box.get('tone', 'unknown')}")

    except Exception as e:
        print(f"\nERROR in translation test: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "=" * 60)
    print("Tests completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
