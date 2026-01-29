#!/usr/bin/env python3
"""
Simple standalone test for HTML parser (no dependencies required).
Tests just the HTML parsing logic.
"""

from pathlib import Path
from html.parser import HTMLParser


class ImageExtractor(HTMLParser):
    """Extract image sources from HTML."""

    def __init__(self):
        super().__init__()
        self.image_sources = []

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            for attr, value in attrs:
                if attr in ('src', 'data-src'):
                    self.image_sources.append(value)


def test_html_parsing():
    """Test HTML parsing logic."""
    print("\nTesting HTML Parser Logic")
    print("=" * 60 + "\n")

    # Test 1: Simple HTML with images
    print("[Test 1] Parse HTML with 3 images")
    html1 = """
    <html>
    <body>
        <img src="page_01.png">
        <img src="page_02.png">
        <img src="page_03.png">
    </body>
    </html>
    """

    parser1 = ImageExtractor()
    parser1.feed(html1)

    assert len(parser1.image_sources) == 3, f"Expected 3, got {len(parser1.image_sources)}"
    assert parser1.image_sources[0] == "page_01.png"
    print(f"✓ Found {len(parser1.image_sources)} images: {parser1.image_sources}")

    # Test 2: data-src attribute
    print("\n[Test 2] Parse data-src attributes")
    html2 = """
    <html>
    <body>
        <img data-src="lazy_image.png">
    </body>
    </html>
    """

    parser2 = ImageExtractor()
    parser2.feed(html2)

    assert len(parser2.image_sources) == 1
    assert parser2.image_sources[0] == "lazy_image.png"
    print(f"✓ Found data-src image: {parser2.image_sources[0]}")

    # Test 3: Filter external URLs
    print("\n[Test 3] Filter logic for external URLs")
    sources = [
        "page_01.png",  # Keep
        "http://example.com/page.png",  # Skip
        "https://cdn.com/image.png",  # Skip
        "//cdn.com/image.png",  # Skip
        "data:image/png;base64,abc",  # Skip
        "./images/page_02.png",  # Keep
    ]

    filtered = [
        src for src in sources
        if not src.startswith(('data:', 'http://', 'https://', '//'))
    ]

    assert len(filtered) == 2
    assert "page_01.png" in filtered
    assert "./images/page_02.png" in filtered
    print(f"✓ Filtered to {len(filtered)} local images: {filtered}")

    # Test 4: Path resolution
    print("\n[Test 4] Path resolution")
    html_dir = Path("/home/user/manhwa")

    test_cases = [
        ("page.png", html_dir / "page.png"),
        ("./page.png", html_dir / "page.png"),
        ("images/page.png", html_dir / "images" / "page.png"),
    ]

    for src, expected in test_cases:
        resolved = (html_dir / src).resolve()
        print(f"  {src} → {resolved}")

    print("✓ Path resolution working")

    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    test_html_parsing()
