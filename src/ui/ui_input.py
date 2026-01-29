"""UI input widgets."""
import streamlit as st
from typing import Dict, Any
from pathlib import Path
import tempfile


def render_input_section() -> Dict[str, Any]:
    """
    Render input section for URL or HTML upload and configuration.

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

    # Separator
    st.markdown("**— OR —**")

    # ZIP file upload
    uploaded_file = st.file_uploader(
        "Upload ZIP File (HTML + Images)",
        type=['zip'],
        help="Upload a ZIP containing the saved manhwa HTML and images folder."
    )

    # Extract ZIP and find HTML file
    html_file_path = None
    if uploaded_file is not None:
        import zipfile

        # Create temp directory for extraction
        temp_dir = Path(tempfile.gettempdir()) / "manhwa_uploads" / uploaded_file.name.replace('.zip', '')
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Save and extract ZIP
        zip_path = temp_dir.parent / uploaded_file.name
        zip_path.write_bytes(uploaded_file.read())

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # Find HTML file in extracted content
            html_files = list(temp_dir.glob("**/*.html")) + list(temp_dir.glob("**/*.htm"))

            if html_files:
                html_file_path = html_files[0]  # Use first HTML file found
                st.info(f"📦 Extracted: {uploaded_file.name} → {html_file_path.name}")
            else:
                st.error("No HTML file found in ZIP")
        except Exception as e:
            st.error(f"Failed to extract ZIP: {e}")

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
        "html_file": html_file_path,
        "target_lang": target_lang,
        "ocr_confidence": ocr_confidence,
        "debug_mode": debug_mode
    }
