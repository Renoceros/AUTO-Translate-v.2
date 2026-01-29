"""UI input widgets."""
import streamlit as st
from typing import Dict, Any


def render_input_section() -> Dict[str, Any]:
    """
    Render input section for URL and configuration.

    Returns:
        Dictionary with user inputs
    """
    st.header("Input")

    # URL input
    url = st.text_input(
        "Manhwa Chapter URL",
        placeholder="https://example.com/manhwa/chapter-1",
        help="Enter the URL of the manhwa chapter to translate"
    )

    # Configuration overrides
    with st.expander("Advanced Settings"):
        target_lang = st.selectbox(
            "Target Language",
            options=["en", "es", "fr", "de"],
            index=0,
            help="Language to translate to"
        )

        ocr_confidence = st.slider(
            "OCR Confidence Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.6,
            step=0.05,
            help="Minimum confidence for OCR results (lower = more results)"
        )

        debug_mode = st.checkbox(
            "Debug Mode",
            value=False,
            help="Save intermediate artifacts for debugging"
        )

    return {
        "url": url,
        "target_lang": target_lang,
        "ocr_confidence": ocr_confidence,
        "debug_mode": debug_mode
    }
