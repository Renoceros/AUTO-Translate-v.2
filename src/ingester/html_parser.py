"""
HTML parser for extracting manhwa panel images from local HTML files.
"""

from pathlib import Path
from typing import List
import shutil
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


def parse_html_file(html_path: Path, config) -> List[Path]:
    """
    Parse HTML file and extract manhwa panel images.

    Args:
        html_path: Path to uploaded HTML file
        config: Config object (for workspace_dir)

    Returns:
        List[Path]: Paths to images in workspace/raw_panels/

    Raises:
        ValueError: If HTML is invalid or images not found
        FileNotFoundError: If HTML file doesn't exist
    """
    # Words to ignore in image filenames (case-insensitive)
    IGNORE_KEYWORDS = ['screenshot', 'samsung', 'logo', 'banner', 'icon']
    
    # 1. Validate HTML file exists
    if not html_path.exists():
        raise FileNotFoundError(f"HTML file not found: {html_path}")

    # 2. Read and parse HTML
    try:
        html_content = html_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        # Try with other encodings
        try:
            html_content = html_path.read_text(encoding='latin-1')
        except Exception as e:
            raise ValueError(f"Failed to read HTML file: {e}")

    # Parse HTML to extract image sources
    parser = ImageExtractor()
    try:
        parser.feed(html_content)
    except Exception as e:
        raise ValueError(f"Failed to parse HTML: {e}")

    img_sources = parser.image_sources

    if not img_sources:
        raise ValueError("No images found in HTML file")

    # 3. Filter to only png/jpg, then resolve paths and validate
    html_dir = html_path.parent
    image_paths = []
    missing_images = []

    for src in img_sources:
        # Skip data URIs, external URLs
        if src.startswith(('data:', 'http://', 'https://', '//')):
            continue

        # Filter by extension FIRST - only process .png and .jpg files
        src_lower = src.lower()
        if not (src_lower.endswith('.png') or src_lower.endswith('.jpg') or src_lower.endswith('.jpeg')):
            # Skip .gif, .webp, .svg, etc. - don't report as missing
            continue

        # Skip images with ignored keywords in filename
        filename_lower = Path(src).name.lower()
        if any(keyword in filename_lower for keyword in IGNORE_KEYWORDS):
            continue

        # Resolve relative path
        try:
            img_path = (html_dir / src).resolve()

            if img_path.exists() and img_path.is_file():
                image_paths.append(img_path)
            else:
                missing_images.append(src)
        except Exception:
            # Path resolution failed
            missing_images.append(src)

    # 4. Fail-fast if any images missing
    if missing_images:
        raise ValueError(
            f"Missing {len(missing_images)} images:\n" +
            "\n".join(f"  - {src}" for src in missing_images[:5]) +
            ("\n  ..." if len(missing_images) > 5 else "")
        )

    if not image_paths:
        raise ValueError("No valid local images found in HTML")

    # 5. Copy to workspace/raw_panels/
    output_dir = config.workspace_dir / "raw_panels"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Clear existing files
    for file in output_dir.glob("*.png"):
        file.unlink()
    for file in output_dir.glob("*.jpg"):
        file.unlink()
    for file in output_dir.glob("*.jpeg"):
        file.unlink()

    # Copy with standard naming
    panel_paths = []
    for i, img_path in enumerate(image_paths):
        suffix = img_path.suffix  # .png, .jpg, etc.
        dest_name = f"panel_{i:04d}{suffix}"
        dest_path = output_dir / dest_name

        shutil.copy2(img_path, dest_path)
        panel_paths.append(dest_path)

    return panel_paths