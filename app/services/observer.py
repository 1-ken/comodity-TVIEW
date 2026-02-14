import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from playwright.async_api import async_playwright, Browser, Page

from app.core.paths import CONFIG_PATH

logger = logging.getLogger(__name__)


class SiteObserver:
    def __init__(
        self,
        url: str,
        table_selector: str,
        pair_cell_selector: str,
        wait_selector: str = "body",
        inject_mutation_observer: bool = True,
        price_column_index: int = 3,
    ) -> None:
        self.url = url
        self.table_selector = table_selector
        self.pair_cell_selector = pair_cell_selector
        self.wait_selector = wait_selector
        self.inject_mutation_observer = inject_mutation_observer
        self.price_column_index = price_column_index

        self._pw = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        # Track gold price to detect stalled data feed
        self._last_gold_price: Optional[str] = None
        self._last_gold_update_time: Optional[float] = None
        self._gold_stall_timeout: float = 30.0  # seconds before refresh if gold hasn't changed

    async def startup(self) -> None:
        """Initialize the browser and navigate to the target URL."""
        try:
            logger.info("Starting browser and navigating to %s", self.url)
            self._pw = await async_playwright().start()
            self.browser = await self._pw.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-web-resources",
                    "--disable-extensions",
                ],
            )
            context = await self.browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                locale="en-US",
                viewport={"width": 1920, "height": 1080},
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                },
            )
            # Override navigator.webdriver flag
            await context.add_init_script(
                """{
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            }"""
            )
            self.page = await context.new_page()
            # Block the disruptive promo video and heavy assets
            await self.page.route(
                "**/*",
                lambda route: (
                    route.abort()
                    if (
                        "join-for-free" in route.request.url
                        or "promo" in route.request.url
                        or route.request.resource_type in {"image", "font", "media"}
                    )
                    else route.continue_()
                ),
            )

            # Use longer timeout and handle navigation better
            try:
                await self.page.goto(self.url, wait_until="domcontentloaded", timeout=60000)
            except Exception as e:
                logger.warning("Navigation error (continuing): %s", e)

            # Wait a bit for dynamic content to load
            await self.page.wait_for_timeout(2000)

            # Check for and handle cookie consent popup (Yahoo Finance)
            await self._handle_cookie_consent()

            # Don't wait for networkidle - modern sites never reach it
            # Instead, wait for the specific table element to appear
            try:
                await self.page.wait_for_selector(self.wait_selector, timeout=30000)
            except Exception as e:
                logger.warning("Wait selector timeout: %s. Continuing anyway...", e)
                # Still try to fall back to table selector
                try:
                    await self.page.wait_for_selector(self.table_selector, timeout=10000)
                except Exception as e2:
                    logger.warning("Table selector also not found: %s. Proceeding with extraction...", e2)
                    # Take a screenshot for debugging
                    try:
                        screenshot_path = f"debug_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                        await self.page.screenshot(path=screenshot_path, full_page=True)
                        logger.info("Screenshot saved to %s", screenshot_path)
                    except Exception as e3:
                        logger.error("Failed to take screenshot: %s", e3)
                    # Log page content for debugging
                    try:
                        content = await self.page.content()
                        logger.info("Page HTML length: %s characters", len(content))
                        logger.info("Page title: %s", await self.page.title())
                        # Check if we got an error page or captcha
                        if "captcha" in content.lower() or "access denied" in content.lower():
                            logger.error("Page appears to show captcha or access denied message")
                    except Exception as e4:
                        logger.error("Failed to get page content: %s", e4)
            logger.info("Browser started successfully")

            if self.inject_mutation_observer:
                await self.page.evaluate(
                    """
                    () => {
                        window.__changes = [];
                        const observer = new MutationObserver(mutations => {
                            mutations.forEach(m => window.__changes.push(m.type));
                        });
                        observer.observe(document.body, { childList: true, subtree: true });
                        window.__observer = observer;

                        // Guard: remove disruptive promo video/overlay whenever it appears
                        const killPromo = () => {
                            const targets = document.querySelectorAll(
                              'video.video-wH0t6WRN, video[src*="join-for-free"], [class*="join-for-free"]'
                            );
                            targets.forEach(node => {
                                const modal = node.closest('[role="dialog"], .overlay, .popup, [class*="modal"], [class*="overlay"]');
                                (modal || node).remove();
                            });
                        };
                        killPromo();
                        const promoObserver = new MutationObserver(killPromo);
                        promoObserver.observe(document.body, { childList: true, subtree: true });
                        window.__promoObserver = promoObserver;
                    }
                    """
                )
        except Exception as e:
            logger.error("Failed to start browser: %s", e)
            raise

    async def _handle_cookie_consent(self) -> None:
        """Handle cookie consent popup if it appears on page load."""
        if not self.page:
            return

        try:
            # Wait briefly for the consent popup to appear
            # Try multiple possible selectors for the "Accept all" button
            selectors = [
                'button[name="agree"][value="agree"]',  # Yahoo Finance specific
                "button.accept-all",
                "button.consent_reject_all_2",
                'button:has-text("Accepter tout")',  # French version
                'button:has-text("Accept all")',  # English version
            ]

            for selector in selectors:
                try:
                    # Check if the button exists with a short timeout
                    consent_button = await self.page.wait_for_selector(
                        selector,
                        timeout=3000,
                        state="visible",
                    )

                    if consent_button:
                        logger.info("Cookie consent popup detected, clicking accept button: %s", selector)
                        await consent_button.click()
                        # Wait a moment for the popup to disappear
                        await self.page.wait_for_timeout(1000)
                        logger.info("Cookie consent accepted successfully")
                        return

                except Exception:
                    # This selector didn't match, try the next one
                    continue

            logger.debug("No cookie consent popup detected, continuing with normal flow")

        except Exception as e:
            logger.warning("Error while handling cookie consent: %s. Continuing anyway...", e)

    async def _detect_and_close_popup(self) -> bool:
        """
        Detect and close any visible popup/modal overlays that might block data extraction.
        Returns True if a popup was detected and closed, False otherwise.
        """
        if not self.page:
            return False

        try:
            # List of common popup selectors to try
            popup_selectors = [
                # Generic modal/overlay patterns
                'div[role="dialog"]',
                'div[role="alertdialog"]',
                ".modal",
                ".popup",
                ".overlay",
                "[class*='modal']",
                "[class*='popup']",
                "[class*='overlay']",
                "[class*='dialog']",

                # Specific close button patterns
                'button[aria-label*="close"]',
                'button[aria-label*="Close"]',
                'button[aria-label*="dismiss"]',
                "button.close",
                "button.btn-close",
                "[class*='close-button']",
                "[class*='dismiss']",

                # ESC key or click on overlay
                ".backdrop",
                ".dimmed",
                "[class*='backdrop']",
            ]

            for selector in popup_selectors:
                try:
                    # Check if element exists and is visible
                    element = await self.page.query_selector(selector)
                    if element:
                        is_visible = await element.is_visible()
                        if is_visible:
                            logger.info("Popup detected: %s", selector)

                            # Try to find close button within popup
                            close_button_selectors = [
                                'button[aria-label*="close"]',
                                'button[aria-label*="dismiss"]',
                                "button.close",
                                "button.btn-close",
                                "[class*='close']",
                                'span[aria-label*="close"]',
                            ]

                            for close_sel in close_button_selectors:
                                try:
                                    close_btn = await element.query_selector(close_sel)
                                    if close_btn and await close_btn.is_visible():
                                        logger.info("Found close button: %s, clicking...", close_sel)
                                        await close_btn.click()
                                        await self.page.wait_for_timeout(500)
                                        logger.info("Popup closed successfully")
                                        return True
                                except Exception:
                                    continue

                            # If no close button found, try pressing Escape key
                            try:
                                logger.info("No close button found, trying Escape key...")
                                await self.page.keyboard.press("Escape")
                                await self.page.wait_for_timeout(500)
                                logger.info("Escape key pressed")
                                return True
                            except Exception as e:
                                logger.debug("Escape key failed: %s", e)

                            # If still visible, try clicking outside (on backdrop)
                            try:
                                logger.info("Trying to click backdrop...")
                                backdrop = await self.page.query_selector('[class*="backdrop"], .overlay, .dimmed')
                                if backdrop:
                                    await backdrop.click()
                                    await self.page.wait_for_timeout(500)
                                    logger.info("Backdrop clicked")
                                    return True
                            except Exception as e:
                                logger.debug("Backdrop click failed: %s", e)

                            # Last resort: try removing the element from DOM
                            try:
                                logger.info("Removing popup from DOM...")
                                await self.page.evaluate(
                                    f"""
                                    (() => {{
                                        const elem = document.querySelector('{selector}');
                                        if (elem) {{
                                            elem.remove();
                                            console.log('Popup removed');
                                        }}
                                    }})()
                                """
                                )
                                await self.page.wait_for_timeout(500)
                                logger.info("Popup removed from DOM")
                                return True
                            except Exception as e:
                                logger.debug("DOM removal failed: %s", e)

                except Exception as e:
                    logger.debug("Error checking selector %s: %s", selector, e)
                    continue

            return False

        except Exception as e:
            logger.warning("Error in popup detection: %s", e)
            return False

    async def shutdown(self) -> None:
        """Clean up browser resources."""
        logger.info("Shutting down browser")
        try:
            if self.browser:
                await self.browser.close()
        except Exception as e:
            logger.error("Error closing browser: %s", e)
        finally:
            if self._pw:
                try:
                    await self._pw.stop()
                except Exception as e:
                    logger.error("Error stopping playwright: %s", e)

    async def _extract_pair_cells_text(self) -> List[str]:
        if not self.page:
            return []
        js = f"""
        (() => {{
            const table = document.querySelector('{self.table_selector}');
            if (!table) return [];
            const cells = table.querySelectorAll('{self.pair_cell_selector}');
            return Array.from(cells).map(td => td.textContent.trim()).filter(Boolean);
        }})()
        """
        texts: List[str] = await self.page.evaluate(js)
        return texts

    async def _extract_pairs_with_prices(self) -> List[Dict[str, str]]:
        """Extract currency pairs with their current prices from the table."""
        if not self.page:
            return []
        js = f"""
        (() => {{
            const table = document.querySelector('{self.table_selector}');
            if (!table) return [];
            const rows = table.querySelectorAll('tbody tr');
            return Array.from(rows).map(row => {{
                const cells = row.querySelectorAll('td');
                const priceIndex = {self.price_column_index};
                if (cells.length <= priceIndex) return null;

                // Get pair name from first column that contains .symbol or second column
                let pairText = '';
                const symbolEl = cells[0]?.querySelector('.symbol');
                if (symbolEl) {{
                    pairText = symbolEl.textContent.trim();
                }} else {{
                    pairText = cells[1]?.textContent.trim() || '';
                }}

                const priceText = cells[priceIndex]?.textContent.trim() || '';
                // Extract just the price (first number before any +/- change)
                const priceMatch = priceText.match(/^([\d,\.]+)/);
                return {{
                    pair: pairText,
                    price: priceMatch ? priceMatch[1] : priceText
                }};
            }}).filter(item => item && item.pair && item.price);
        }})()
        """
        pairs_data: List[Dict[str, str]] = await self.page.evaluate(js)
        return pairs_data

    @staticmethod
    def _parse_majors_from_texts(texts: List[str], majors: List[str]) -> List[str]:
        majors_set = set(m.upper() for m in majors)
        found = set()
        for txt in texts:
            # Extract 3-letter codes split by common separators
            tokens = re.split(r"[\s/\-:]+", txt.upper())
            for tok in tokens:
                if len(tok) == 3 and tok.isalpha() and tok in majors_set:
                    found.add(tok)
        return sorted(found)

    async def snapshot(self, majors: List[str]) -> Dict[str, Any]:
        if not self.page:
            raise RuntimeError("Observer not started. Call startup() first.")

        try:
            # Get all symbol elements from the new TradingView-like structure
            symbol_elements = await self.page.query_selector_all(".symbol-RsFlttSS")
            pairs_with_prices = []

            for symbol_elem in symbol_elements:
                try:
                    # Extract symbol name
                    name_elem = await symbol_elem.query_selector(".symbolNameText-RsFlttSS")
                    if not name_elem:
                        continue

                    pair = await name_elem.text_content()
                    pair = pair.strip() if pair else ""

                    if not pair:
                        continue

                    # Extract price from the last price cell
                    price_container = await symbol_elem.query_selector(".last-RsFlttSS .inner-RsFlttSS")
                    if price_container:
                        price = await price_container.text_content()
                        # Clean up price - remove any HTML entities and extra whitespace
                        price = price.strip() if price else "0"
                        # Handle multi-line prices and normalize
                        price = re.sub(r"\s+", "", price)  # Remove all whitespace
                        pairs_with_prices.append({"pair": pair, "price": price})
                except Exception as e:
                    logger.debug("Error extracting symbol data: %s", e)
                    continue

            if not pairs_with_prices:
                try:
                    title = await self.page.title()
                    logger.warning(
                        "Snapshot returned no pairs; page title=%s, url=%s",
                        title,
                        self.page.url,
                    )
                except Exception:
                    logger.warning("Snapshot returned no pairs and title fetch failed")

            texts = [item["pair"] for item in pairs_with_prices]
            majors_found = self._parse_majors_from_texts(texts, majors)

            # For commodities and forex, include all pairs (don't filter by majors)
            # Filter pairs to only include those with majors if we found any majors
            if majors_found:
                major_pairs = [
                    item for item in pairs_with_prices if any(m.upper() in item["pair"].upper() for m in majors_found)
                ]
            else:
                # If no majors found, include all pairs (for commodities)
                major_pairs = pairs_with_prices

            title = await self.page.title()
            changes: List[str] = await self.page.evaluate("() => (window.__changes || []).splice(0)")

            # Check if gold price has changed (gold is most volatile, good indicator of live data)
            await self._check_gold_stall(major_pairs)

            return {
                "title": title,
                "majors": majors_found if majors_found else texts[:5],  # Include pair samples as "majors" if no majors found
                "pairs": major_pairs,
                "pairsSample": texts[:10],
                "changes": changes,
                "ts": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error("Error getting snapshot: %s", e)
            return {
                "title": "Error",
                "majors": [],
                "pairs": [],
                "pairsSample": [],
                "changes": [],
                "ts": datetime.now().isoformat(),
                "error": str(e),
            }

    async def _check_gold_stall(self, pairs_data: List[Dict[str, str]]) -> None:
        """Check if monitored pair (gold/bitcoin) price has stalled; refresh page if stalled for 30 seconds.
        
        On weekends (Saturday/Sunday), monitor BITCOIN price volatility instead of GOLD,
        since forex markets are closed and gold is a better indicator during those times.
        """
        if not self.page:
            return

        import time

        current_time = time.time()

        # Determine which pair to monitor based on day of week
        # Monday=0, ..., Friday=4, Saturday=5, Sunday=6
        is_weekend = datetime.now().weekday() >= 5
        monitoring_pair = "BITCOIN" if is_weekend else "GOLD"

        # Find monitoring pair price in current data
        pair_price = None
        for item in pairs_data:
            if item.get("pair", "").upper() == monitoring_pair:
                pair_price = item.get("price", "")
                break

        if pair_price:
            # Check if price has changed
            if pair_price != self._last_gold_price:
                # Price changed - update tracking
                logger.debug(
                    "%s price updated: %s -> %s",
                    monitoring_pair,
                    self._last_gold_price,
                    pair_price,
                )
                self._last_gold_price = pair_price
                self._last_gold_update_time = current_time
            else:
                # Price hasn't changed - check timeout
                if self._last_gold_update_time is not None:
                    time_since_update = current_time - self._last_gold_update_time
                    if time_since_update >= self._gold_stall_timeout:
                        logger.warning(
                            "%s price unchanged for %ss (threshold: %ss); refreshing page",
                            monitoring_pair,
                            f"{time_since_update:.1f}",
                            f"{self._gold_stall_timeout}",
                        )
                        await self._recover_from_gold_stall()
                else:
                    # First time seeing this price
                    self._last_gold_update_time = current_time
        else:
            # Monitoring pair not found in data - just update timestamp to prevent false triggers
            if self._last_gold_update_time is None:
                self._last_gold_update_time = current_time

    async def _recover_from_gold_stall(self) -> None:
        """Force a page refresh when gold price hasn't changed for the timeout period."""
        if not self.page:
            return

        logger.info("Refreshing page due to stalled gold data...")
        try:
            await self.page.reload(wait_until="domcontentloaded", timeout=60000)
            await self.page.wait_for_timeout(2000)
            await self._handle_cookie_consent()
            # Reset gold tracking after recovery
            self._last_gold_price = None
            self._last_gold_update_time = None
            logger.info("Page refreshed successfully")
        except Exception as e:
            logger.error("Recovery reload failed: %s", e)


async def observe_once_from_config(config_path: str) -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    observer = SiteObserver(
        url=cfg.get("url", "https://example.com"),
        table_selector=cfg.get("tableSelector", "#pairs-table"),
        pair_cell_selector=cfg.get("pairCellSelector", "tbody tr td:first-child"),
        wait_selector=cfg.get("waitSelector", "body"),
        inject_mutation_observer=bool(cfg.get("injectMutationObserver", True)),
    )

    try:
        await observer.startup()
        data = await observer.snapshot(cfg.get("majors", []))
        return data
    finally:
        await observer.shutdown()


if __name__ == "__main__":
    # Quick manual test: prints a single snapshot

    async def _main():
        data = await observe_once_from_config(str(CONFIG_PATH))
        print(json.dumps(data, indent=2))

    asyncio.run(_main())
