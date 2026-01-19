# src/captcha_solver.py
import time
import random
import json
import re
from typing import List, Optional, Any, Union

from playwright.sync_api import Frame, Locator, Page, TimeoutError as PlaywrightTimeout, Error as PlaywrightError
from google import genai
from google.genai import types

from src.config import API_KEYS, RETRY_LIMITS, DELAYS
from src.logger_config import get_logger
from src.exceptions import CaptchaSolveError

logger = get_logger(__name__)


class CaptchaSolver:
    """
    Production-Ready Solver using Google Gemini Vision (API v1.0+) for solving ReCaptchas.

    Features:
    - Unified Imports (google-genai)
    - Robust JSON Parsing (JSON Mode)
    - Safe Clicking (Bounding Box Check)
    - Key Rotation
    - In-Memory Processing (No disk I/O)
    - Type Safety
    """

    def __init__(self, page: Optional[Page] = None):
        """
        Initialize the CaptchaSolver.

        Args:
            page (Optional[Page]): The Playwright Page object.
        """
        self.page = page
        self.api_keys: List[str] = API_KEYS.get("GEMINI", [])

        if not self.api_keys:
            logger.critical("❌ No Gemini API keys found in .env! Solver will not function.")
            raise ValueError("CRITICAL: Missing GEMINI_API_KEY")

        logger.info(f"🔧 Loaded {len(self.api_keys)} Gemini API keys.")

        # Vision-optimized model
        self.model_name = "gemini-1.5-flash"

    def _get_client(self) -> genai.Client:
        """Create a client with a random key (rotation per request)."""
        return genai.Client(api_key=random.choice(self.api_keys))

    def solve_loop(self, frame: Frame) -> bool:
        """
        Main loop handling the Captcha solving process within a frame.

        Args:
            frame (Frame): The Playwright Frame containing the captcha.

        Returns:
            bool: True if solved successfully, False otherwise.
        """
        logger.info("🤖 Starting Captcha solving loop...")
        max_total_attempts = RETRY_LIMITS["CAPTCHA_ATTEMPTS"]

        for i in range(max_total_attempts):
            if self._is_solved_or_detached(frame):
                return True

            target = self._find_captcha_target(frame)

            if not target:
                if self._handle_fallback_actions(frame, i):
                    continue
                # Short wait before retrying logic loop
                self.page.wait_for_timeout(1000) if self.page else time.sleep(1)
                continue

            # Attempt one round of solving
            if self._attempt_solve_round(frame, target, i):
                pass
            else:
                self._click_reload_or_skip(frame)

        return False

    def _is_solved_or_detached(self, frame: Frame) -> bool:
        """Check if the captcha frame is detached or hidden (indicating success)."""
        try:
            if frame.is_detached() or not frame.locator("body").is_visible():
                logger.info("✅ Captcha frame detached or hidden - assuming success.")
                return True
        except (PlaywrightTimeout, PlaywrightError):
            return True
        return False

    def _find_captcha_target(self, frame: Frame) -> Optional[Locator]:
        """Find the main captcha image or target area."""
        target_selectors = ["#rc-imageselect-target", ".rc-imageselect-payload", "table", "body"]
        for selector in target_selectors:
            loc = frame.locator(selector).first
            try:
                # Wait for visibility with specific timeouts
                timeout = 2000 if selector == "body" else 4000
                loc.wait_for(state="visible", timeout=timeout)

                # Check for empty body to avoid white screenshots
                if selector == "body":
                    box = loc.bounding_box()
                    if box and box['height'] < 50:
                        continue

                return loc
            except PlaywrightTimeout:
                continue
        return None

    def _attempt_solve_round(self, frame: Frame, target: Locator, attempt_idx: int) -> bool:
        """Execute one round of: Screenshot -> Gemini -> Click -> Verify."""
        try:
            image_bytes = self._take_screenshot(target)
            if not image_bytes:
                 return False

            instruction = self._get_instruction(frame)

            tiles_to_click = self._solve_grid(image_bytes, instruction)
            if not tiles_to_click:
                logger.warning("⚠️ Gemini returned empty list.")
                return False

            self._click_tiles(frame, target, tiles_to_click)
            self._confirm_solution(frame)
            return True

        except PlaywrightError as e:
            logger.error(f"❌ Error during solve round: {e}")
            return False

    def _take_screenshot(self, target: Locator) -> Optional[bytes]:
        """Take a screenshot of the target element in memory."""
        try:
            return target.screenshot(type='png')
        except Exception as e:
             logger.error(f"❌ Failed to take screenshot: {e}")
             return None

    def _get_instruction(self, frame: Frame) -> str:
        """Extract instructions from the Captcha frame."""
        try:
            instruction_el = frame.locator(
                "strong, .rc-imageselect-desc-no-canonical, #rc-imageselect-instructions"
            ).first
            if instruction_el.is_visible():
                instruction = instruction_el.inner_text()
                logger.info(f"🧩 Challenge: '{instruction}'")
                return instruction
        except PlaywrightError:
            pass
        return "Select all matching images"

    def _click_tiles(self, frame: Frame, target: Locator, tiles_idx: List[int]) -> None:
        """Click the specified tiles with human-like delays."""
        logger.info(f"👉 Clicking tiles: {tiles_idx}")

        tiles = target.locator("td, .rc-imageselect-tile")
        if tiles.count() == 0:
            tiles = frame.locator("td, .rc-imageselect-tile")

        count = tiles.count()
        for index in tiles_idx:
            idx_zero_based = index - 1
            if idx_zero_based < count:
                tile = tiles.nth(idx_zero_based)
                self._safe_click_tile(tile)
                # Random delay between clicks
                time.sleep(random.uniform(DELAYS.get("HUMAN_TYPE_MIN", 0.15), DELAYS.get("HUMAN_TYPE_MAX", 0.4)))

        # Wait for potential animation/loading
        time.sleep(1)

    def _confirm_solution(self, frame: Frame) -> None:
        """Click the Verify button."""
        verify_btn = frame.locator("#recaptcha-verify-button, .rc-button-default").first
        if verify_btn.is_visible():
            verify_btn.click()
            # Wait for response (spinner or result)
            self.page.wait_for_timeout(2000) if self.page else time.sleep(2)

    def _handle_fallback_actions(self, frame: Frame, attempt_idx: int) -> bool:
        """Handle initial checkbox or reload button."""
        # A) Checkbox "I'm not a robot"
        checkbox = frame.locator(".recaptcha-checkbox-border, #recaptcha-anchor")
        if checkbox.is_visible():
            logger.info("👉 Checkbox visible, clicking...")
            checkbox.click()
            self.page.wait_for_timeout(2000) if self.page else time.sleep(2)
            return True

        # B) Reload Button (e.g. network error)
        reload_btn = frame.locator("#recaptcha-reload-button, .rc-button-reload").first
        if reload_btn.is_visible():
            logger.warning("⚠️ Reload button visible, clicking.")
            reload_btn.click()
            self.page.wait_for_timeout(2000) if self.page else time.sleep(2)
            return True

        # C) Nothing found
        logger.warning(f"⚠️ No image or controls found (attempt {attempt_idx + 1}).")
        return False

    def _click_reload_or_skip(self, frame: Frame) -> None:
        """Click Skip or Reload if stuck."""
        try:
            reload_btn = frame.locator("#recaptcha-reload-button, .rc-button-reload").first
            if reload_btn.is_visible():
                reload_btn.click()
                return

            skip_btn = frame.get_by_role("button", name="Pomiń") # 'Pomiń' is Polish for Skip
            if skip_btn.is_visible():
                skip_btn.click()
        except PlaywrightError:
            pass

    def _safe_click_tile(self, tile_locator: Locator) -> None:
        """
        Click a tile safely with random offset within the bounding box.
        Prevents clicking (0,0) or outside elements.
        """
        try:
            box = tile_locator.bounding_box()
            if box:
                width = box['width']
                height = box['height']

                # Margin 5px
                if width > 10 and height > 10:
                    safe_x = random.uniform(5, width - 5)
                    safe_y = random.uniform(5, height - 5)
                    tile_locator.click(position={"x": safe_x, "y": safe_y})
                else:
                    tile_locator.click(force=True)
            else:
                tile_locator.click(force=True)
        except PlaywrightError as e:
            logger.warning(f"⚠️ Tile click error: {e}")

    def _solve_grid(self, image_bytes: bytes, instruction: str) -> List[int]:
        """
        Send image bytes to Gemini and return list of tile indices.
        Uses JSON mode validation.
        """
        prompt = f"""
        Task: Identify tiles containing: "{instruction}".
        Format: Return ONLY a raw JSON list of integers (1-based index).
        Grid: Assume standard 3x3 or 4x4.
        Example: [1, 5, 9]
        NO MARKDOWN, NO EXPLANATIONS.
        """

        for attempt in range(RETRY_LIMITS.get("GEMINI_API_RETRIES", 3)):
            try:
                client = self._get_client()

                response = client.models.generate_content(
                    model=self.model_name,
                    contents=[
                        types.Content(
                            parts=[
                                types.Part.from_text(text=prompt),
                                types.Part.from_bytes(data=image_bytes, mime_type="image/png")
                            ]
                        )
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.1
                    )
                )

                text_resp = response.text
                if not text_resp:
                    continue

                # Clean potential markdown
                clean_json = text_resp.strip()
                if "```" in clean_json:
                     # Remove code blocks
                    clean_json = clean_json.replace("```json", "").replace("```", "")
                
                # Additional cleanup for safety
                clean_json = clean_json.strip()
                
                # Check if it starts/ends with boolean-like chars if model hallucinated logic
                if not clean_json.startswith("["):
                     # try to find list
                     match = re.search(r'\[.*\]', clean_json, re.DOTALL)
                     if match:
                         clean_json = match.group(0)

                result = json.loads(clean_json)

                if isinstance(result, list):
                    return [x for x in result if isinstance(x, int)]

            except (json.JSONDecodeError, KeyError, AttributeError, Exception) as e:
                logger.warning(f"⚠️ Gemini API Error ({attempt + 1}): {e}")
                time.sleep(1)
                continue

        return []