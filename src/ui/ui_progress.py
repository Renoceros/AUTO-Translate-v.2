"""UI progress visualization."""
import streamlit as st
from src.pipeline import PipelineState, PipelineStage


def render_progress_section(state: PipelineState):
    """
    Render progress bars and status messages.

    Args:
        state: Pipeline state object
    """
    st.header("Progress")

    # Overall progress bar
    progress_bar = st.progress(state.progress / 100.0)

    # Stage indicator
    stage_text = st.empty()
    stage_text.text(f"Stage: {state.current_stage.value} - {state.message}")

    # Error display
    if state.error:
        st.error(f"Error: {state.error}")

    return progress_bar, stage_text


def update_progress_display(
    progress_bar,
    stage_text,
    state: PipelineState
):
    """
    Update progress display elements.

    Args:
        progress_bar: Streamlit progress bar
        stage_text: Streamlit text element
        state: Pipeline state
    """
    progress_bar.progress(state.progress / 100.0)
    stage_text.text(f"Stage: {state.current_stage.value} - {state.message}")
