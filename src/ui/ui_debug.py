"""UI debug tools."""
import streamlit as st
from pathlib import Path
from typing import List, Dict, Any
import cv2
import numpy as np
from PIL import Image, ImageDraw


def render_debug_section(config):
    """
    Render debug tools section.

    Args:
        config: Configuration object
    """
    st.header("Debug Tools")

    with st.expander("OCR Boxes Overlay"):
        render_ocr_overlay_tool(config)

    with st.expander("Filter Decisions"):
        render_filter_decisions(config)

    with st.expander("Translation Comparison"):
        render_translation_comparison(config)

    with st.expander("Artifacts"):
        render_artifacts_browser(config)


def render_ocr_overlay_tool(config):
    """
    Render OCR bounding boxes overlay on images.

    Args:
        config: Configuration object
    """
    st.subheader("OCR Boxes Overlay")

    # Load OCR data
    from src.storage.ocr_store import OCRStore

    store = OCRStore(config)
    boxes = store.load_boxes()

    if not boxes:
        st.info("No OCR data available")
        return

    st.write(f"Total OCR boxes: {len(boxes)}")

    # Load stitched image
    stitched_path = config.workspace_dir / "stitched" / "full_chapter.png"

    if not stitched_path.exists():
        st.warning("Stitched image not found")
        return

    # Draw boxes
    image = cv2.imread(str(stitched_path))
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    for box in boxes:
        x = box['x']
        y = box['y']
        w = box['w']
        h = box['h']

        # Draw rectangle
        cv2.rectangle(image, (x, y), (x + w, y + h), (255, 0, 0), 2)

        # Draw text
        cv2.putText(
            image,
            f"{box['confidence']:.2f}",
            (x, y - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 0, 0),
            1
        )

    # Display
    st.image(image, use_container_width=True)


def render_filter_decisions(config):
    """
    Display filter agent decisions.

    Args:
        config: Configuration object
    """
    st.subheader("Filter Decisions")

    from src.storage.ocr_store import OCRStore

    store = OCRStore(config)
    boxes = store.load_boxes()

    if not boxes:
        st.info("No OCR data available")
        return

    # Filter boxes with decisions
    kept = [b for b in boxes if b.get('filter_decision') == 'KEEP']
    dropped = [b for b in boxes if b.get('filter_decision') == 'DROP']

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Kept", len(kept))

    with col2:
        st.metric("Dropped", len(dropped))

    # Show dropped boxes
    if dropped:
        st.subheader("Dropped Boxes")
        for box in dropped:
            st.write(
                f"- **{box['text']}** "
                f"({box.get('filter_category', 'unknown')}) "
                f"- {box.get('filter_reasoning', '')}"
            )


def render_translation_comparison(config):
    """
    Display original vs translated text comparison.

    Args:
        config: Configuration object
    """
    st.subheader("Translation Comparison")

    from src.storage.ocr_store import OCRStore

    store = OCRStore(config)
    boxes = store.load_boxes()

    # Filter translated boxes
    translated = [b for b in boxes if 'translated' in b]

    if not translated:
        st.info("No translations available")
        return

    # Display as table
    for box in translated:
        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**KO:** {box['text']}")

        with col2:
            st.write(f"**EN:** {box.get('translated', '')}")

        st.caption(f"Tone: {box.get('tone', 'unknown')}")
        st.divider()


def render_artifacts_browser(config):
    """
    Browse workspace artifacts.

    Args:
        config: Configuration object
    """
    st.subheader("Workspace Artifacts")

    # List artifact directories
    artifact_dirs = [
        "raw_panels",
        "stitched",
        "splits",
        "ocr",
        "filtered",
        "inpainted",
        "rendered",
        "final"
    ]

    for dir_name in artifact_dirs:
        dir_path = config.workspace_dir / dir_name

        if dir_path.exists():
            files = list(dir_path.glob("*"))
            st.write(f"**{dir_name}**: {len(files)} files")
        else:
            st.write(f"**{dir_name}**: Not created yet")
