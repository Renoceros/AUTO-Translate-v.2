"""Panel extraction heuristics."""
import logging
from typing import List
from urllib.parse import urlparse

from src.config import Config


logger = logging.getLogger(__name__)


async def extract_panel_urls_from_page(page, config: Config) -> List[str]:
    """
    Extract panel URLs from Playwright page using multi-strategy approach.

    Args:
        page: Playwright page object
        config: Configuration

    Returns:
        List of unique panel URLs
    """
    candidates = []

    # Strategy 1: Try common selectors
    selectors = [
        "img.webtoon-panel",
        "img.comic-page",
        "img.chapter-img",
        "div[class*='viewer'] img",
        "div[class*='reader'] img",
        "img[data-panel-id]",
        "img[data-index]",
        ".viewer-img img",
        "#comic-viewer img",
    ]

    for selector in selectors:
        try:
            elements = await page.query_selector_all(selector)
            for elem in elements:
                url = await elem.get_attribute("src")
                if not url:
                    url = await elem.get_attribute("data-src")

                if url:
                    # Get element dimensions
                    box = await elem.bounding_box()
                    if box:
                        candidates.append({
                            "url": url,
                            "width": box["width"],
                            "height": box["height"]
                        })
        except Exception as e:
            logger.debug(f"Selector {selector} failed: {e}")
            continue

    logger.info(f"Found {len(candidates)} candidate images")

    # Strategy 2: Size filtering
    filtered = []
    for candidate in candidates:
        width = candidate["width"]
        height = candidate["height"]

        if width < config.panel_filter.min_width or height < config.panel_filter.min_height:
            continue

        aspect_ratio = width / height if height > 0 else 0
        if aspect_ratio < config.panel_filter.min_aspect_ratio or \
           aspect_ratio > config.panel_filter.max_aspect_ratio:
            continue

        filtered.append(candidate)

    logger.info(f"After size filtering: {len(filtered)} images")

    # Strategy 3: Keyword exclusion
    excluded_keywords = config.panel_filter.excluded_keywords
    final_candidates = []

    for candidate in filtered:
        url_lower = candidate["url"].lower()

        # Check if URL contains excluded keywords
        if any(keyword in url_lower for keyword in excluded_keywords):
            continue

        final_candidates.append(candidate["url"])

    logger.info(f"After keyword filtering: {len(final_candidates)} images")

    # Strategy 4: Deduplication
    seen = set()
    unique_urls = []

    for url in final_candidates:
        # Normalize URL (remove query params for deduplication)
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        if base_url not in seen:
            seen.add(base_url)
            unique_urls.append(url)

    logger.info(f"After deduplication: {len(unique_urls)} unique panels")

    return unique_urls


async def extract_panel_urls_selenium(driver, config: Config) -> List[str]:
    """
    Extract panel URLs from Selenium driver.

    Args:
        driver: Selenium WebDriver
        config: Configuration

    Returns:
        List of unique panel URLs
    """
    from selenium.webdriver.common.by import By

    candidates = []

    # Try common selectors
    selectors = [
        (By.CSS_SELECTOR, "img.webtoon-panel"),
        (By.CSS_SELECTOR, "img.comic-page"),
        (By.CSS_SELECTOR, "img.chapter-img"),
        (By.CSS_SELECTOR, "div[class*='viewer'] img"),
        (By.CSS_SELECTOR, "div[class*='reader'] img"),
        (By.CSS_SELECTOR, "img[data-panel-id]"),
        (By.CSS_SELECTOR, "img[data-index]"),
    ]

    for by, selector in selectors:
        try:
            elements = driver.find_elements(by, selector)
            for elem in elements:
                url = elem.get_attribute("src") or elem.get_attribute("data-src")

                if url:
                    size = elem.size
                    candidates.append({
                        "url": url,
                        "width": size["width"],
                        "height": size["height"]
                    })
        except Exception as e:
            logger.debug(f"Selector {selector} failed: {e}")
            continue

    # Apply same filtering as Playwright version
    filtered = []
    for candidate in candidates:
        width = candidate["width"]
        height = candidate["height"]

        if width < config.panel_filter.min_width or height < config.panel_filter.min_height:
            continue

        aspect_ratio = width / height if height > 0 else 0
        if aspect_ratio < config.panel_filter.min_aspect_ratio or \
           aspect_ratio > config.panel_filter.max_aspect_ratio:
            continue

        filtered.append(candidate)

    # Keyword exclusion
    excluded_keywords = config.panel_filter.excluded_keywords
    final_candidates = []

    for candidate in filtered:
        url_lower = candidate["url"].lower()
        if not any(keyword in url_lower for keyword in excluded_keywords):
            final_candidates.append(candidate["url"])

    # Deduplication
    seen = set()
    unique_urls = []

    for url in final_candidates:
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        if base_url not in seen:
            seen.add(base_url)
            unique_urls.append(url)

    logger.info(f"Extracted {len(unique_urls)} unique panel URLs")
    return unique_urls
