#!/usr/bin/env python3
"""
Test script for HTML upload feature.

This creates a sample HTML file with test images and verifies the ingester works correctly.
"""

import sys
from pathlib import Path
from PIL import Image

from src.config import get_config
from src.ingester import parse_html_file


def create_test_data(test_dir: Path):
    """Create test HTML and images."""
    test_dir.mkdir(parents=True, exist_ok=True)

    # Create test images
    print("Creating test images...")
    for i in range(1, 4):
        img = Image.new('RGB', (800, 1200), color=(i * 60, 100, 200))
        img.save(test_dir / f"page_{i:02d}.png")
        print(f"  Created page_{i:02d}.png")

    # Create test HTML
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Test Manhwa Chapter</title>
</head>
<body>
    <h1>Test Chapter</h1>
    <div class="pages">
        <img src="page_01.png" alt="Page 1">
        <img src="page_02.png" alt="Page 2">
        <img src="page_03.png" alt="Page 3">
    </div>
</body>
</html>
"""
    html_path = test_dir / "test_manhwa.html"
    html_path.write_text(html_content)
    print(f"  Created test_manhwa.html")

    return html_path


def test_html_parser():
    """Test HTML parsing and image extraction."""
    print("\n" + "="*60)
    print("Testing HTML Upload Feature")
    print("="*60 + "\n")

    # Setup test directory
    test_dir = Path("test_html_data")
    print(f"Test directory: {test_dir.absolute()}\n")

    # Create test data
    html_path = create_test_data(test_dir)

    # Test 1: Valid HTML with all images present
    print("\n[Test 1] Valid HTML with all images present")
    print("-" * 60)
    try:
        config = get_config()
        panel_paths = parse_html_file(html_path, config)

        print(f"✓ Successfully extracted {len(panel_paths)} images")
        print(f"✓ Images copied to: {config.workspace_dir / 'raw_panels'}")

        for i, path in enumerate(panel_paths, 1):
            print(f"  {i}. {path.name} ({path.stat().st_size} bytes)")

        assert len(panel_paths) == 3, f"Expected 3 images, got {len(panel_paths)}"
        print("\n✓ Test 1 PASSED\n")

    except Exception as e:
        print(f"\n✗ Test 1 FAILED: {e}\n")
        return False

    # Test 2: Missing image
    print("\n[Test 2] HTML with missing image")
    print("-" * 60)
    try:
        # Create HTML with missing image
        html_missing = test_dir / "test_missing.html"
        html_missing.write_text("""<!DOCTYPE html>
<html><body>
<img src="page_01.png">
<img src="missing_page.png">
<img src="page_02.png">
</body></html>
""")

        panel_paths = parse_html_file(html_missing, config)
        print(f"\n✗ Test 2 FAILED: Should have raised ValueError for missing image\n")
        return False

    except ValueError as e:
        if "Missing" in str(e):
            print(f"✓ Correctly detected missing image")
            print(f"✓ Error message: {str(e)[:100]}...")
            print("\n✓ Test 2 PASSED\n")
        else:
            print(f"\n✗ Test 2 FAILED: Wrong error: {e}\n")
            return False

    except Exception as e:
        print(f"\n✗ Test 2 FAILED: Unexpected error: {e}\n")
        return False

    # Test 3: No images in HTML
    print("\n[Test 3] HTML with no images")
    print("-" * 60)
    try:
        html_empty = test_dir / "test_empty.html"
        html_empty.write_text("<html><body><h1>No images here</h1></body></html>")

        panel_paths = parse_html_file(html_empty, config)
        print(f"\n✗ Test 3 FAILED: Should have raised ValueError for no images\n")
        return False

    except ValueError as e:
        if "No images found" in str(e):
            print(f"✓ Correctly detected no images")
            print(f"✓ Error message: {e}")
            print("\n✓ Test 3 PASSED\n")
        else:
            print(f"\n✗ Test 3 FAILED: Wrong error: {e}\n")
            return False

    except Exception as e:
        print(f"\n✗ Test 3 FAILED: Unexpected error: {e}\n")
        return False

    # Cleanup
    print("\n" + "="*60)
    print("Cleanup")
    print("="*60)
    print(f"\nTest data kept at: {test_dir.absolute()}")
    print("You can manually inspect the files or delete the directory.\n")

    return True


if __name__ == "__main__":
    print("\nHTML Upload Feature Test Script")
    print("This script tests the HTML ingestion module\n")

    try:
        success = test_html_parser()

        if success:
            print("\n" + "="*60)
            print("ALL TESTS PASSED ✓")
            print("="*60 + "\n")
            sys.exit(0)
        else:
            print("\n" + "="*60)
            print("SOME TESTS FAILED ✗")
            print("="*60 + "\n")
            sys.exit(1)

    except Exception as e:
        print(f"\n✗ Test suite failed with error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
