"""Main pipeline orchestration."""
import asyncio
import logging
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from enum import Enum

from src.config import Config, get_config


class PipelineStage(Enum):
    """Pipeline execution stages."""
    INIT = "init"
    CRAWL = "crawl"
    EXTRACT = "extract"
    STITCH = "stitch"
    OCR_PASS1 = "ocr_pass1"
    SPLIT = "split"
    OCR_PASS2 = "ocr_pass2"
    FILTER = "filter"
    TRANSLATE = "translate"
    INPAINT = "inpaint"
    RENDER = "render"
    COMPOSE = "compose"
    COMPLETE = "complete"


class PipelineState:
    """Pipeline execution state."""
    def __init__(self):
        self.current_stage: PipelineStage = PipelineStage.INIT
        self.progress: float = 0.0
        self.message: str = ""
        self.error: Optional[str] = None
        self.artifacts: Dict[str, Any] = {}

    def update(self, stage: PipelineStage, progress: float, message: str):
        """Update pipeline state."""
        self.current_stage = stage
        self.progress = progress
        self.message = message
        logging.info(f"[{stage.value}] {progress:.1f}% - {message}")


class Pipeline:
    """
    Main pipeline orchestrator.

    Manages sequential execution of all translation stages with
    error handling, progress tracking, and state persistence.
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize pipeline.

        Args:
            config: Configuration instance (uses global config if None)
        """
        self.config = config or get_config()
        self.state = PipelineState()
        self.progress_callback: Optional[Callable[[PipelineState], None]] = None

        # Setup logging
        logging.basicConfig(
            level=logging.DEBUG if self.config.debug.debug_mode else logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def set_progress_callback(self, callback: Callable[[PipelineState], None]):
        """Set callback function for progress updates."""
        self.progress_callback = callback

    def _notify_progress(self, stage: PipelineStage, progress: float, message: str):
        """Notify progress update."""
        self.state.update(stage, progress, message)
        if self.progress_callback:
            self.progress_callback(self.state)

    async def run_async(self, url: Optional[str] = None, html_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Run pipeline asynchronously.

        Args:
            url: Manhwa chapter URL (optional)
            html_path: Path to HTML file (optional)

        Returns:
            Dictionary with pipeline results and artifacts

        Raises:
            ValueError: If neither or both inputs provided
        """
        try:
            # Validate inputs (XOR: one and only one)
            if url and html_path:
                raise ValueError("Provide either URL or HTML file, not both")
            if not url and not html_path:
                raise ValueError("Must provide URL or HTML file")

            self._notify_progress(PipelineStage.INIT, 0, "Initializing pipeline...")

            # Ensure workspace exists
            self.config.ensure_workspace()

            # Stage 1-2: Conditional execution (Crawl/Extract OR HTML Ingestion)
            if url:
                # Normal web crawling
                self._notify_progress(PipelineStage.CRAWL, 5, "Crawling chapter page...")
                panel_urls = await self._crawl_chapter(url)
                self.state.artifacts["panel_urls"] = panel_urls
                self.logger.info(f"Found {len(panel_urls)} panels")

                self._notify_progress(PipelineStage.EXTRACT, 15, "Downloading panels...")
                panel_paths = await self._extract_panels(panel_urls)
                self.state.artifacts["panel_paths"] = panel_paths
            else:
                # HTML ingestion
                self._notify_progress(PipelineStage.EXTRACT, 10, "Extracting images from HTML...")
                from src.ingester import parse_html_file
                panel_paths = parse_html_file(html_path, self.config)
                self.state.artifacts["panel_paths"] = panel_paths
                self.state.artifacts["html_source"] = str(html_path)
                self.logger.info(f"Extracted {len(panel_paths)} images from HTML")

            # Stage 3: Stitch panels
            self._notify_progress(PipelineStage.STITCH, 25, "Stitching panels...")
            stitched_path, coord_map = await self._stitch_panels(panel_paths)
            self.state.artifacts["stitched_path"] = stitched_path
            self.state.artifacts["coord_map"] = coord_map

            # Stage 4: OCR Pass 1 (on stitched image)
            self._notify_progress(PipelineStage.OCR_PASS1, 35, "Running OCR pass 1...")
            ocr_boxes_pass1 = await self._run_ocr_pass1(stitched_path)
            self.state.artifacts["ocr_boxes_pass1"] = ocr_boxes_pass1
            self.logger.info(f"OCR Pass 1 found {len(ocr_boxes_pass1)} text boxes")

            # Stage 5: Smart split
            self._notify_progress(PipelineStage.SPLIT, 45, "Smart splitting panels...")
            split_paths = await self._smart_split(stitched_path, ocr_boxes_pass1)
            self.state.artifacts["split_paths"] = split_paths

            # Stage 6: OCR Pass 2 (on split panels)
            self._notify_progress(PipelineStage.OCR_PASS2, 55, "Running OCR pass 2...")
            ocr_boxes_pass2 = await self._run_ocr_pass2(split_paths)
            self.state.artifacts["ocr_boxes_pass2"] = ocr_boxes_pass2
            self.logger.info(f"OCR Pass 2 found {len(ocr_boxes_pass2)} text boxes")

            # Stage 7: Filter with LLM
            self._notify_progress(PipelineStage.FILTER, 65, "Filtering text with LLM...")
            filtered_boxes = await self._filter_text(ocr_boxes_pass2)
            self.state.artifacts["filtered_boxes"] = filtered_boxes
            self.logger.info(f"Kept {len(filtered_boxes)} text boxes after filtering")

            # Stage 8: Translate with LLM
            self._notify_progress(PipelineStage.TRANSLATE, 75, "Translating text...")
            translated_boxes = await self._translate_text(filtered_boxes)
            self.state.artifacts["translated_boxes"] = translated_boxes

            # Stage 9: Inpaint
            self._notify_progress(PipelineStage.INPAINT, 85, "Inpainting original text...")
            inpainted_paths = await self._inpaint_panels(split_paths, ocr_boxes_pass2)
            self.state.artifacts["inpainted_paths"] = inpainted_paths

            # Stage 10: Render
            self._notify_progress(PipelineStage.RENDER, 90, "Rendering translated text...")
            rendered_paths = await self._render_text(inpainted_paths, translated_boxes)
            self.state.artifacts["rendered_paths"] = rendered_paths

            # Stage 11: Compose final images
            self._notify_progress(PipelineStage.COMPOSE, 95, "Composing final images...")
            final_paths = await self._compose_final(rendered_paths)
            self.state.artifacts["final_paths"] = final_paths

            self._notify_progress(PipelineStage.COMPLETE, 100, "Pipeline complete!")

            return {
                "status": "success",
                "artifacts": self.state.artifacts
            }

        except Exception as e:
            self.logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
            self.state.error = str(e)
            return {
                "status": "error",
                "error": str(e),
                "artifacts": self.state.artifacts
            }

    def run(self, url: Optional[str] = None, html_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Run pipeline synchronously.

        Args:
            url: Manhwa chapter URL (optional)
            html_path: Path to HTML file (optional)

        Returns:
            Dictionary with pipeline results and artifacts
        """
        return asyncio.run(self.run_async(url=url, html_path=html_path))

    # Stage implementations (to be filled by module imports)

    async def _crawl_chapter(self, url: str):
        """Crawl chapter and extract panel URLs."""
        from src.crawler.browser import crawl_chapter
        return await crawl_chapter(url, self.config)

    async def _extract_panels(self, panel_urls: list[str]):
        """Download panel images."""
        from src.panels.extractor import extract_panels
        return await extract_panels(panel_urls, self.config)

    async def _stitch_panels(self, panel_paths: list[Path]):
        """Stitch panels vertically."""
        from src.panels.stitcher import stitch_panels
        return await stitch_panels(panel_paths, self.config)

    async def _run_ocr_pass1(self, stitched_path: Path):
        """Run OCR on stitched image."""
        from src.ocr.engine import run_ocr
        return await run_ocr(stitched_path, self.config)

    async def _smart_split(self, stitched_path: Path, ocr_boxes: list):
        """Smart split stitched image."""
        from src.split.smart_split import smart_split
        return await smart_split(stitched_path, ocr_boxes, self.config)

    async def _run_ocr_pass2(self, split_paths: list[Path]):
        """Run OCR on split panels."""
        from src.ocr.engine import run_ocr_batch
        return await run_ocr_batch(split_paths, self.config)

    async def _filter_text(self, ocr_boxes: list):
        """Filter text with LLM."""
        from src.agents.filter_agent import filter_text_boxes
        return await filter_text_boxes(ocr_boxes, self.config)

    async def _translate_text(self, filtered_boxes: list):
        """Translate text with LLM."""
        from src.agents.translation_agent import translate_text_boxes
        return await translate_text_boxes(filtered_boxes, self.config)

    async def _inpaint_panels(self, split_paths: list[Path], all_ocr_boxes: list):
        """Inpaint original text from all OCR detections."""
        from src.inpaint.opencv_inpaint import inpaint_panels
        return await inpaint_panels(split_paths, all_ocr_boxes, self.config)

    async def _render_text(self, inpainted_paths: list[Path], translated_boxes: list):
        """Render translated text."""
        from src.render.text_renderer import render_text_batch
        return await render_text_batch(inpainted_paths, translated_boxes, self.config)

    async def _compose_final(self, rendered_paths: list[Path]):
        """Compose final images."""
        from src.render.composer import compose_final_images
        return await compose_final_images(rendered_paths, self.config)
