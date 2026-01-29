"""Configuration management module."""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator


class OCRConfig(BaseModel):
    """OCR engine configuration."""
    primary_engine: str = "paddleocr"
    fallback_engine: str = "easyocr"
    confidence_threshold: float = 0.6
    languages: list[str] = ["ko", "en"]


class CrawlerConfig(BaseModel):
    """Web crawler configuration."""
    browser: str = "playwright"
    page_timeout: int = 30
    scroll_pause: float = 2.0
    max_scrolls: int = 50


class PanelFilterConfig(BaseModel):
    """Panel filtering heuristics."""
    min_width: int = 300
    min_height: int = 400
    min_aspect_ratio: float = 0.5
    max_aspect_ratio: float = 3.0
    excluded_keywords: list[str] = ["avatar", "emoji", "icon", "banner", "ad"]


class SmartSplitConfig(BaseModel):
    """Smart split algorithm configuration."""
    max_subpanels: int = 100
    min_margin_from_text: int = 50
    min_whitespace_height: int = 20


class LLMConfig(BaseModel):
    """LLM API configuration."""
    model: str = "claude-3-5-sonnet-20241022"
    temperature: float = 0.2
    max_tokens: int = 1024


class TranslationConfig(BaseModel):
    """Translation settings."""
    target_language: str = "en"
    source_language: str = "ko"
    context_window_size: int = 3


class StorageConfig(BaseModel):
    """Data storage configuration."""
    backend: str = "csv"


class FontConfig(BaseModel):
    """Font rendering configuration."""
    default: str = "./fonts/NanumGothic.ttf"
    size_multiplier: float = 0.8


class DebugConfig(BaseModel):
    """Debug settings."""
    save_artifacts: bool = True
    debug_mode: bool = False


class Config(BaseModel):
    """Main configuration class."""
    ocr: OCRConfig = Field(default_factory=OCRConfig)
    crawler: CrawlerConfig = Field(default_factory=CrawlerConfig)
    panel_filter: PanelFilterConfig = Field(default_factory=PanelFilterConfig)
    smart_split: SmartSplitConfig = Field(default_factory=SmartSplitConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    translation: TranslationConfig = Field(default_factory=TranslationConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    fonts: FontConfig = Field(default_factory=FontConfig)
    debug: DebugConfig = Field(default_factory=DebugConfig)

    # API keys
    anthropic_api_key: Optional[str] = None

    # Paths
    workspace_dir: Path = Path("./workspace")

    @validator("anthropic_api_key", always=True)
    def validate_api_key(cls, v):
        """Validate Anthropic API key is present."""
        if not v:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. Please set it in .env file."
            )
        return v

    @classmethod
    def load(cls, config_path: str = "config.yaml") -> "Config":
        """
        Load configuration from YAML file and environment variables.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            Config instance
        """
        # Load environment variables from .env
        load_dotenv()

        # Load YAML configuration
        config_data: Dict[str, Any] = {}
        config_file = Path(config_path)

        if config_file.exists():
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f) or {}

        # Add API key from environment
        config_data["anthropic_api_key"] = os.getenv("ANTHROPIC_API_KEY")

        return cls(**config_data)

    def ensure_workspace(self):
        """Create workspace directory structure."""
        subdirs = [
            "raw_panels",
            "stitched",
            "splits",
            "ocr",
            "filtered",
            "inpainted",
            "rendered",
            "final"
        ]

        for subdir in subdirs:
            (self.workspace_dir / subdir).mkdir(parents=True, exist_ok=True)


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = Config.load()
        _config.ensure_workspace()
    return _config


def set_config(config: Config):
    """Set global configuration instance."""
    global _config
    _config = config
