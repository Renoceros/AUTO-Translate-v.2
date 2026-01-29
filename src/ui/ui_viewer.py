"""UI image viewer."""
import streamlit as st
from pathlib import Path
from typing import List, Optional
from PIL import Image


def render_image_comparison(
    original_path: Optional[Path],
    translated_path: Optional[Path]
):
    """
    Render before/after image comparison.

    Args:
        original_path: Path to original image
        translated_path: Path to translated image
    """
    st.header("Comparison")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Original")
        if original_path and original_path.exists():
            st.image(str(original_path), use_container_width=True)
        else:
            st.info("Original image not available")

    with col2:
        st.subheader("Translated")
        if translated_path and translated_path.exists():
            st.image(str(translated_path), use_container_width=True)
        else:
            st.info("Translated image not available")


def render_gallery(image_paths: List[Path]):
    """
    Render gallery of final translated images in single column.

    Args:
        image_paths: List of image paths
    """
    st.header("Final Gallery")

    if not image_paths:
        st.info("No images to display")
        return

    # Display images in single column with no gaps
    st.markdown("""
    <style>
    /* Remove gaps between images */
    .stImage {
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }
    /* Style for page numbers */
    .page-number {
        display: inline-block;
        width: 60px;
        font-size: 14px;
        font-weight: bold;
        color: #666;
        text-align: right;
        padding-right: 10px;
        vertical-align: top;
    }
    </style>
    """, unsafe_allow_html=True)

    # Display each image with number on the left
    for idx, image_path in enumerate(image_paths):
        # Create two columns: narrow one for number, wide one for image
        col1, col2 = st.columns([0.08, 0.92], gap="small")

        with col1:
            st.markdown(f'<div class="page-number">#{idx + 1}</div>', unsafe_allow_html=True)

        with col2:
            st.image(str(image_path), use_container_width=True)


def render_single_image_viewer(image_path: Path):
    """
    Render single image with zoom controls.

    Args:
        image_path: Path to image
    """
    if not image_path.exists():
        st.error(f"Image not found: {image_path}")
        return

    # Load image
    img = Image.open(image_path)

    # Display with zoom
    zoom_level = st.slider("Zoom", min_value=25, max_value=200, value=100, step=25)

    # Calculate new size
    new_width = int(img.width * zoom_level / 100)
    new_height = int(img.height * zoom_level / 100)

    # Resize and display
    if zoom_level != 100:
        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        st.image(img_resized)
    else:
        st.image(img)
