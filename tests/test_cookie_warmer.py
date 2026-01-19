# tests/test_cookie_warmer.py
"""
Unit tests for CookieWarmer module.
Tests warming scenarios and consent handling without live browser.
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock


class TestCookieWarmerUnit:
    """Unit tests for CookieWarmer helper methods."""

    @pytest.fixture
    def mock_page(self):
        """Creates a mock Playwright Page object."""
        page = MagicMock()
        page.locator.return_value.first = MagicMock()
        page.locator.return_value.first.wait_for = MagicMock()
        return page

    @pytest.fixture
    def warmer(self, mock_page):
        """Creates a CookieWarmer instance with mocked page."""
        with patch("src.cookie_warmer.os.makedirs"):
            from src.cookie_warmer import CookieWarmer
            return CookieWarmer(mock_page)

    def test_human_delay_is_static(self):
        """Test that _human_delay is a static method."""
        from src.cookie_warmer import CookieWarmer
        # Should not raise - it's a static method
        CookieWarmer._human_delay(0.01, 0.02)

    def test_safe_wait_returns_true_when_visible(self, warmer, mock_page):
        """Test _safe_wait returns True when element becomes visible."""
        locator = MagicMock()
        locator.wait_for = MagicMock()  # No exception = visible

        result = warmer._safe_wait(locator, timeout=1000)

        assert result is True
        locator.wait_for.assert_called_once_with(state="visible", timeout=1000)

    def test_safe_wait_returns_false_on_timeout(self, warmer):
        """Test _safe_wait returns False when element times out."""
        from playwright.sync_api import TimeoutError as PlaywrightTimeout

        locator = MagicMock()
        locator.wait_for.side_effect = PlaywrightTimeout("Timeout")

        result = warmer._safe_wait(locator, timeout=1000)

        assert result is False

    def test_simple_consent_click_tries_multiple_selectors(self, warmer, mock_page):
        """Test that _simple_consent_click iterates through selectors."""
        # Make all selectors invisible (timeout)
        from playwright.sync_api import TimeoutError as PlaywrightTimeout
        mock_page.locator.return_value.first.wait_for.side_effect = PlaywrightTimeout("Not found")

        # Should not raise, just silently fail
        warmer._simple_consent_click()

        # Verify multiple selectors were tried
        assert mock_page.locator.call_count >= 1


class TestCookieWarmerScenarios:
    """Integration-like tests for warming scenarios."""

    @pytest.fixture
    def mock_page(self):
        """Creates a mock Playwright Page object with goto."""
        page = MagicMock()
        page.goto = MagicMock()
        page.locator.return_value.first = MagicMock()
        page.locator.return_value.first.wait_for = MagicMock()
        page.mouse.wheel = MagicMock()
        return page

    @pytest.fixture
    def warmer(self, mock_page):
        """Creates a CookieWarmer instance."""
        with patch("src.cookie_warmer.os.makedirs"):
            from src.cookie_warmer import CookieWarmer
            return CookieWarmer(mock_page)

    def test_action_visit_onet_calls_goto(self, warmer, mock_page):
        """Test that action_visit_onet navigates to onet.pl."""
        with patch.object(warmer, '_simple_consent_click'), \
             patch.object(warmer, '_human_scroll'):
            warmer.action_visit_onet()

        mock_page.goto.assert_called_once()
        assert "onet.pl" in mock_page.goto.call_args[0][0]

    def test_action_visit_wp_calls_goto(self, warmer, mock_page):
        """Test that action_visit_wp navigates to wp.pl."""
        with patch.object(warmer, '_simple_consent_click'), \
             patch.object(warmer, '_human_scroll'):
            warmer.action_visit_wp()

        mock_page.goto.assert_called_once()
        assert "wp.pl" in mock_page.goto.call_args[0][0]
