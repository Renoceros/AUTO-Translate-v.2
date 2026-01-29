"""HTML export functionality for translated manhwa."""

import zipfile
import shutil
import tempfile
from pathlib import Path
from typing import List


def generate_html_viewer(title: str, num_pages: int) -> str:
    """
    Generate a standalone HTML viewer for manhwa with embedded CSS/JS.

    Args:
        title: Title to display in the viewer
        num_pages: Total number of pages

    Returns:
        Complete HTML string with embedded styles and scripts
    """
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: #1a1a1a;
            color: #e0e0e0;
            overflow-x: hidden;
        }}

        #header {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: rgba(26, 26, 26, 0.95);
            backdrop-filter: blur(10px);
            padding: 1rem 2rem;
            z-index: 1000;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        #header h1 {{
            font-size: 1.5rem;
            font-weight: 600;
            color: #ffffff;
        }}

        #progress {{
            font-size: 1rem;
            color: #a0a0a0;
            font-weight: 500;
        }}

        #current {{
            color: #4a9eff;
            font-weight: 700;
        }}

        #viewer {{
            margin-top: 80px;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding-bottom: 2rem;
        }}

        #viewer img {{
            width: 100%;
            max-width: 800px;
            height: auto;
            display: block;
            margin-bottom: 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }}

        #controls {{
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            display: flex;
            gap: 0.5rem;
            z-index: 1000;
        }}

        .control-btn {{
            background: rgba(74, 158, 255, 0.9);
            border: none;
            color: white;
            padding: 1rem;
            border-radius: 50%;
            cursor: pointer;
            font-size: 1.2rem;
            width: 50px;
            height: 50px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            transition: all 0.2s;
        }}

        .control-btn:hover {{
            background: rgba(74, 158, 255, 1);
            transform: scale(1.1);
        }}

        .control-btn:active {{
            transform: scale(0.95);
        }}

        #scroll-top {{
            display: none;
        }}

        #scroll-top.visible {{
            display: flex;
        }}

        /* Mobile responsive */
        @media (max-width: 768px) {{
            #header {{
                padding: 0.75rem 1rem;
                flex-direction: column;
                gap: 0.5rem;
            }}

            #header h1 {{
                font-size: 1.2rem;
            }}

            #progress {{
                font-size: 0.9rem;
            }}

            #viewer {{
                margin-top: 100px;
            }}

            #controls {{
                bottom: 1rem;
                right: 1rem;
            }}

            .control-btn {{
                width: 45px;
                height: 45px;
                font-size: 1rem;
            }}
        }}

        /* Loading indicator */
        .loading {{
            opacity: 0.5;
            transition: opacity 0.3s;
        }}

        .loaded {{
            opacity: 1;
        }}
    </style>
</head>
<body>
    <div id="header">
        <h1>{title}</h1>
        <div id="progress">
            Page <span id="current">1</span> / <span id="total">{num_pages}</span>
        </div>
    </div>

    <div id="viewer">"""

    # Generate image tags for all pages
    for i in range(num_pages):
        page_num = i + 1
        filename = f"page_{i:04d}.png"
        html_template += f'\n        <img src="img/{filename}" alt="Page {page_num}" loading="lazy" class="loading" data-page="{page_num}">'

    html_template += """
    </div>

    <div id="controls">
        <button id="scroll-top" class="control-btn" title="Scroll to top">↑</button>
    </div>

    <script>
        // Page tracking
        const images = document.querySelectorAll('#viewer img');
        const currentPageSpan = document.getElementById('current');
        const scrollTopBtn = document.getElementById('scroll-top');

        // Intersection Observer for page tracking
        const observerOptions = {
            root: null,
            rootMargin: '-50% 0px -50% 0px',
            threshold: 0
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const pageNum = entry.target.getAttribute('data-page');
                    currentPageSpan.textContent = pageNum;
                }
            });
        }, observerOptions);

        images.forEach(img => {
            observer.observe(img);

            // Add loaded class when image loads
            img.addEventListener('load', () => {
                img.classList.remove('loading');
                img.classList.add('loaded');
            });
        });

        // Scroll to top button
        window.addEventListener('scroll', () => {
            if (window.scrollY > 500) {
                scrollTopBtn.classList.add('visible');
            } else {
                scrollTopBtn.classList.remove('visible');
            }
        });

        scrollTopBtn.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            const viewportHeight = window.innerHeight;

            switch(e.key) {
                case 'ArrowDown':
                case ' ':
                    e.preventDefault();
                    window.scrollBy({
                        top: viewportHeight * 0.8,
                        behavior: 'smooth'
                    });
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    window.scrollBy({
                        top: -viewportHeight * 0.8,
                        behavior: 'smooth'
                    });
                    break;
                case 'Home':
                    e.preventDefault();
                    window.scrollTo({
                        top: 0,
                        behavior: 'smooth'
                    });
                    break;
                case 'End':
                    e.preventDefault();
                    window.scrollTo({
                        top: document.body.scrollHeight,
                        behavior: 'smooth'
                    });
                    break;
            }
        });

        // Prevent spacebar from triggering scroll when focusing buttons
        document.querySelectorAll('button').forEach(btn => {
            btn.addEventListener('keydown', (e) => {
                if (e.key === ' ') {
                    e.stopPropagation();
                }
            });
        });
    </script>
</body>
</html>"""

    return html_template


def create_zip_package(final_paths: List[Path], output_path: Path, title: str = "Translated Manhwa") -> Path:
    """
    Create a ZIP package containing translated images and HTML viewer.

    Args:
        final_paths: List of paths to final translated images
        output_path: Path where the ZIP file should be created
        title: Title to display in the HTML viewer

    Returns:
        Path to the created ZIP file

    Raises:
        ValueError: If final_paths is empty
        IOError: If file operations fail
    """
    if not final_paths:
        raise ValueError("No images provided for ZIP package")

    # Create temporary directory for assembly
    temp_dir = None
    try:
        temp_dir = Path(tempfile.mkdtemp(prefix="manhwa_export_"))
        img_dir = temp_dir / "img"
        img_dir.mkdir(parents=True, exist_ok=True)

        # Copy images to temp directory with standardized names
        for i, img_path in enumerate(final_paths):
            if not img_path.exists():
                raise IOError(f"Image file not found: {img_path}")

            dest_filename = f"page_{i:04d}.png"
            dest_path = img_dir / dest_filename
            shutil.copy2(img_path, dest_path)

        # Generate HTML viewer
        num_pages = len(final_paths)
        html_content = generate_html_viewer(title, num_pages)
        html_path = temp_dir / "index.html"
        html_path.write_text(html_content, encoding="utf-8")

        # Create ZIP file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add HTML file
            zipf.write(html_path, "index.html")

            # Add all images
            for img_file in img_dir.iterdir():
                zipf.write(img_file, f"img/{img_file.name}")

        return output_path

    finally:
        # Cleanup temporary directory
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


def create_zip_package_in_memory(final_paths: List[Path], title: str = "Translated Manhwa") -> bytes:
    """
    Create a ZIP package in memory and return as bytes.
    Useful for Streamlit download_button which accepts bytes.

    Args:
        final_paths: List of paths to final translated images
        title: Title to display in the HTML viewer

    Returns:
        ZIP file content as bytes

    Raises:
        ValueError: If final_paths is empty
        IOError: If file operations fail
    """
    if not final_paths:
        raise ValueError("No images provided for ZIP package")

    # Create temporary directory for assembly
    temp_dir = None
    try:
        temp_dir = Path(tempfile.mkdtemp(prefix="manhwa_export_"))
        img_dir = temp_dir / "img"
        img_dir.mkdir(parents=True, exist_ok=True)

        # Copy images to temp directory with standardized names
        for i, img_path in enumerate(final_paths):
            if not img_path.exists():
                raise IOError(f"Image file not found: {img_path}")

            dest_filename = f"page_{i:04d}.png"
            dest_path = img_dir / dest_filename
            shutil.copy2(img_path, dest_path)

        # Generate HTML viewer
        num_pages = len(final_paths)
        html_content = generate_html_viewer(title, num_pages)
        html_path = temp_dir / "index.html"
        html_path.write_text(html_content, encoding="utf-8")

        # Create ZIP file in memory
        zip_path = temp_dir / "manhwa_package.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add HTML file
            zipf.write(html_path, "index.html")

            # Add all images
            for img_file in img_dir.iterdir():
                zipf.write(img_file, f"img/{img_file.name}")

        # Read ZIP file into memory
        return zip_path.read_bytes()

    finally:
        # Cleanup temporary directory
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
