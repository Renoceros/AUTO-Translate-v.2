"""Centralized logging configuration with file rotation."""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logging(
    log_dir: Path = None,
    log_level: str = "INFO",
    console_level: str = "INFO",
    file_level: str = "DEBUG",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
):
    """
    Setup logging with file rotation and console output.

    Args:
        log_dir: Directory for log files (default: ./logs)
        log_level: Root logger level
        console_level: Console output level
        file_level: File output level (more detailed)
        max_bytes: Max size per log file before rotation
        backup_count: Number of backup files to keep
    """
    # Create logs directory
    if log_dir is None:
        log_dir = Path("./logs")
    log_dir.mkdir(exist_ok=True, parents=True)

    # Generate timestamped log filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"auto_translate_{timestamp}.log"
    latest_log = log_dir / "latest.log"

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler (colored if possible)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, console_level.upper()))
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation (detailed logs)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, file_level.upper()))
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Create symlink to latest log
    try:
        if latest_log.exists() or latest_log.is_symlink():
            latest_log.unlink()
        latest_log.symlink_to(log_file.name)
    except (OSError, NotImplementedError):
        # Symlinks not supported (Windows), just copy
        pass

    # Log startup message
    root_logger.info("=" * 80)
    root_logger.info(f"Logging initialized: {log_file}")
    root_logger.info(f"Console level: {console_level}, File level: {file_level}")
    root_logger.info("=" * 80)

    return log_file


def get_logger(name: str) -> logging.Logger:
    """
    Get logger for module.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def set_log_level(level: str, logger_name: str = None):
    """
    Change log level at runtime.

    Args:
        level: New log level (DEBUG, INFO, WARNING, ERROR)
        logger_name: Specific logger name, or None for root logger
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, level.upper()))
    logger.info(f"Log level changed to {level.upper()}")


# Convenience function for debug mode
def enable_debug_logging():
    """Enable DEBUG level for all loggers."""
    set_log_level("DEBUG")
    logging.info("Debug logging enabled")


def disable_debug_logging():
    """Disable DEBUG level, set to INFO."""
    set_log_level("INFO")
    logging.info("Debug logging disabled")
