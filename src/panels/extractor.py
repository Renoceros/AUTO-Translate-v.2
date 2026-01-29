"""Panel image downloader."""
import asyncio
import logging
from pathlib import Path
from typing import List
import aiohttp
from PIL import Image
from io import BytesIO

from src.config import Config


logger = logging.getLogger(__name__)


async def download_image(session: aiohttp.ClientSession, url: str, output_path: Path, retry: int = 3) -> bool:
    """
    Download single image with retry logic.

    Args:
        session: aiohttp session
        url: Image URL
        output_path: Output file path
        retry: Number of retries

    Returns:
        True if download successful
    """
    for attempt in range(retry):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    content = await response.read()

                    # Validate image
                    try:
                        img = Image.open(BytesIO(content))
                        img.verify()

                        # Save image
                        with open(output_path, 'wb') as f:
                            f.write(content)

                        logger.debug(f"Downloaded: {output_path.name}")
                        return True

                    except Exception as e:
                        logger.warning(f"Invalid image from {url}: {e}")
                        return False

                else:
                    logger.warning(f"HTTP {response.status} for {url}")

        except Exception as e:
            logger.warning(f"Download attempt {attempt + 1} failed for {url}: {e}")
            if attempt < retry - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

    return False


async def extract_panels(panel_urls: List[str], config: Config) -> List[Path]:
    """
    Download all panel images in parallel.

    Args:
        panel_urls: List of image URLs
        config: Configuration

    Returns:
        List of downloaded image paths (in order)
    """
    output_dir = config.workspace_dir / "raw_panels"
    output_dir.mkdir(exist_ok=True, parents=True)

    # Clear existing panels
    for file in output_dir.glob("*.png"):
        file.unlink()
    for file in output_dir.glob("*.jpg"):
        file.unlink()

    logger.info(f"Downloading {len(panel_urls)} panels...")

    # Create tasks for parallel download
    async with aiohttp.ClientSession() as session:
        tasks = []

        for i, url in enumerate(panel_urls):
            # Determine file extension
            ext = ".png" if url.lower().endswith(".png") else ".jpg"
            output_path = output_dir / f"panel_{i:04d}{ext}"

            task = download_image(session, url, output_path)
            tasks.append((output_path, task))

        # Wait for all downloads
        results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)

        # Collect successful downloads
        downloaded_paths = []
        for (path, _), success in zip(tasks, results):
            if success and path.exists():
                downloaded_paths.append(path)

    logger.info(f"Successfully downloaded {len(downloaded_paths)}/{len(panel_urls)} panels")

    # Sort by filename to maintain order
    downloaded_paths.sort()

    return downloaded_paths
