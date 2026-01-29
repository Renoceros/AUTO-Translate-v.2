"""Browser abstraction for web crawling."""
import asyncio
import logging
import webbrowser
from abc import ABC, abstractmethod
from typing import List, Optional
from pathlib import Path

from src.config import Config


logger = logging.getLogger(__name__)


class BrowserDriver(ABC):
    """Abstract browser driver interface."""

    @abstractmethod
    async def navigate(self, url: str):
        """Navigate to URL."""
        pass

    @abstractmethod
    async def scroll_to_bottom(self):
        """Scroll to bottom of page."""
        pass

    @abstractmethod
    async def extract_panel_urls(self) -> List[str]:
        """Extract panel image URLs from page."""
        pass

    @abstractmethod
    async def close(self):
        """Close browser."""
        pass


class PlaywrightDriver(BrowserDriver):
    """Playwright browser driver."""

    def __init__(self, config: Config):
        self.config = config
        self.browser = None
        self.page = None
        self._playwright = None

    async def _init_browser(self):
        """Initialize Playwright browser."""
        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(headless=False)
        self.page = await self.browser.new_page()
        self.page.set_default_timeout(self.config.crawler.page_timeout * 1000)

    async def navigate(self, url: str):
        """Navigate to URL and handle Cloudflare."""
        if not self.page:
            await self._init_browser()

        logger.info(f"Navigating to {url}")
        await self.page.goto(url, wait_until="domcontentloaded")

        # Check for Cloudflare challenge
        await asyncio.sleep(2)
        content = await self.page.content()

        if "cloudflare" in content.lower() or "challenge" in content.lower():
            logger.warning("Cloudflare challenge detected!")
            logger.warning("Opening browser for manual authentication...")

            # Open browser for user to solve
            webbrowser.open(url)

            # Wait for user confirmation
            input("Press Enter after solving Cloudflare challenge...")

            # Reload page
            await self.page.reload(wait_until="domcontentloaded")

    async def scroll_to_bottom(self):
        """Scroll to bottom to load all panels."""
        logger.info("Scrolling to load all panels...")

        prev_height = 0
        scroll_count = 0

        while scroll_count < self.config.crawler.max_scrolls:
            # Get current height
            current_height = await self.page.evaluate("document.body.scrollHeight")

            if current_height == prev_height:
                logger.info("Reached bottom of page")
                break

            # Scroll down
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(self.config.crawler.scroll_pause)

            prev_height = current_height
            scroll_count += 1

        logger.info(f"Scrolled {scroll_count} times")

    async def extract_panel_urls(self) -> List[str]:
        """Extract panel URLs using asset filter."""
        from src.crawler.asset_filter import extract_panel_urls_from_page

        return await extract_panel_urls_from_page(self.page, self.config)

    async def close(self):
        """Close browser."""
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()


class SeleniumDriver(BrowserDriver):
    """Selenium browser driver (fallback)."""

    def __init__(self, config: Config):
        self.config = config
        self.driver = None

    def _init_driver(self):
        """Initialize Selenium driver."""
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        options = Options()
        # Don't use headless for Cloudflare
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])

        self.driver = webdriver.Chrome(options=options)
        self.driver.set_page_load_timeout(self.config.crawler.page_timeout)

    async def navigate(self, url: str):
        """Navigate to URL."""
        if not self.driver:
            self._init_driver()

        logger.info(f"Navigating to {url}")
        self.driver.get(url)

        # Check for Cloudflare
        await asyncio.sleep(2)
        if "cloudflare" in self.driver.page_source.lower():
            logger.warning("Cloudflare detected! Please solve manually...")
            input("Press Enter after solving Cloudflare challenge...")

    async def scroll_to_bottom(self):
        """Scroll to bottom."""
        from selenium.webdriver.common.by import By

        prev_height = 0
        scroll_count = 0

        while scroll_count < self.config.crawler.max_scrolls:
            current_height = self.driver.execute_script("return document.body.scrollHeight")

            if current_height == prev_height:
                break

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(self.config.crawler.scroll_pause)

            prev_height = current_height
            scroll_count += 1

        logger.info(f"Scrolled {scroll_count} times")

    async def extract_panel_urls(self) -> List[str]:
        """Extract panel URLs."""
        from src.crawler.asset_filter import extract_panel_urls_selenium

        return await extract_panel_urls_selenium(self.driver, self.config)

    async def close(self):
        """Close browser."""
        if self.driver:
            self.driver.quit()


async def crawl_chapter(url: str, config: Config) -> List[str]:
    """
    Crawl manhwa chapter and extract panel URLs.

    Args:
        url: Chapter URL
        config: Configuration

    Returns:
        List of panel image URLs
    """
    # Try Playwright first
    driver_cls = PlaywrightDriver if config.crawler.browser == "playwright" else SeleniumDriver

    driver = driver_cls(config)

    try:
        await driver.navigate(url)
        await driver.scroll_to_bottom()
        panel_urls = await driver.extract_panel_urls()

        logger.info(f"Extracted {len(panel_urls)} panel URLs")
        return panel_urls

    finally:
        await driver.close()
