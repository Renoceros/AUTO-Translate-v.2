"""Main Streamlit application."""
import asyncio
import streamlit as st
from pathlib import Path

from src.config import Config, get_config
from src.pipeline import Pipeline, PipelineStage
from src.ui.ui_input import render_input_section
from src.ui.ui_progress import render_progress_section, update_progress_display
from src.ui.ui_viewer import render_gallery, render_image_comparison
from src.ui.ui_debug import render_debug_section


def main():
    """Main Streamlit app."""
    st.set_page_config(
        page_title="AUTO-Translate v.2",
        page_icon="📖",
        layout="wide"
    )

    st.title("AUTO-Translate v.2")
    st.markdown("*Automated Manhwa Translation System*")

    # Initialize session state
    if 'pipeline_running' not in st.session_state:
        st.session_state.pipeline_running = False

    if 'pipeline_complete' not in st.session_state:
        st.session_state.pipeline_complete = False

    if 'final_paths' not in st.session_state:
        st.session_state.final_paths = []

    # Load configuration
    try:
        config = get_config()
    except ValueError as e:
        st.error(str(e))
        st.info("Please create a .env file with your ANTHROPIC_API_KEY")
        st.stop()

    # Sidebar
    with st.sidebar:
        st.header("About")
        st.markdown("""
        This system automatically translates Korean manhwa chapters to English.

        **Features:**
        - Web crawling with Playwright
        - OCR with PaddleOCR/EasyOCR
        - LLM-based filtering & translation
        - Smart text inpainting
        - Automated text rendering

        **Academic Use Only**
        """)

        st.divider()

        if st.button("Clear Workspace"):
            import shutil
            workspace = config.workspace_dir
            if workspace.exists():
                shutil.rmtree(workspace)
                workspace.mkdir()
                st.success("Workspace cleared!")
                st.rerun()

    # Main content
    tab1, tab2, tab3 = st.tabs(["Process", "Results", "Debug"])

    with tab1:
        # Input section
        user_inputs = render_input_section()

        # Run button
        if st.button("Start Translation", type="primary", disabled=st.session_state.pipeline_running):
            if not user_inputs["url"]:
                st.error("Please enter a chapter URL")
            else:
                # Update config with user overrides
                config.translation.target_language = user_inputs["target_lang"]
                config.ocr.confidence_threshold = user_inputs["ocr_confidence"]
                config.debug.debug_mode = user_inputs["debug_mode"]

                # Run pipeline
                st.session_state.pipeline_running = True
                st.session_state.pipeline_complete = False

                # Progress section
                progress_container = st.container()

                with progress_container:
                    st.header("Processing...")
                    progress_bar = st.progress(0.0)
                    status_text = st.empty()

                    # Create pipeline
                    pipeline = Pipeline(config)

                    # Progress callback
                    def update_progress(state):
                        progress_bar.progress(state.progress / 100.0)
                        status_text.text(f"{state.current_stage.value}: {state.message}")

                    pipeline.set_progress_callback(update_progress)

                    # Run pipeline
                    try:
                        result = pipeline.run(user_inputs["url"])

                        if result["status"] == "success":
                            st.success("Translation complete!")
                            st.session_state.pipeline_complete = True
                            st.session_state.final_paths = result["artifacts"].get("final_paths", [])
                        else:
                            st.error(f"Pipeline failed: {result.get('error', 'Unknown error')}")

                    except Exception as e:
                        st.error(f"Error: {str(e)}")

                    finally:
                        st.session_state.pipeline_running = False

    with tab2:
        st.header("Results")

        if not st.session_state.pipeline_complete:
            st.info("Run the translation process first")
        else:
            # Show results
            final_paths = st.session_state.final_paths

            if final_paths:
                # Gallery view
                render_gallery(final_paths)

                # Download button
                if len(final_paths) > 0:
                    st.download_button(
                        "Download First Page",
                        data=open(final_paths[0], "rb").read(),
                        file_name=final_paths[0].name,
                        mime="image/png"
                    )

                # Comparison view
                st.divider()
                original_dir = config.workspace_dir / "raw_panels"
                if original_dir.exists():
                    original_files = sorted(list(original_dir.glob("*.png")) + list(original_dir.glob("*.jpg")))
                    if original_files and final_paths:
                        render_image_comparison(original_files[0], final_paths[0])

            else:
                st.warning("No final images generated")

    with tab3:
        if config.debug.debug_mode:
            render_debug_section(config)
        else:
            st.info("Enable debug mode in settings to see debug tools")


if __name__ == "__main__":
    main()
