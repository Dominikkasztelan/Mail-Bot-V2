# tests/test_registration.py
from unittest.mock import MagicMock, patch

import pytest

from src.registration_page import RegistrationPage


class TestRegistrationPageUnit:
    @pytest.fixture
    def mock_page(self):
        page = MagicMock()
        page.get_by_role.return_value = MagicMock()
        page.locator.return_value.first = MagicMock()
        return page

    @pytest.fixture
    def reg_page(self, mock_page):
        # Prevent CaptchaSolver init from looking for keys or page issues
        with patch("src.registration_page.CaptchaSolver") as MockSolver:
            return RegistrationPage(mock_page)

    def test_generate_login_variant_logic(self, reg_page):
        """Test the logic for generating login variants without side effects."""
        base = "jan.kowalski"

        # Attempt 0 -> base if short enough
        variant_0 = reg_page._generate_login_variant(base, 0)
        assert variant_0 == "jan.kowalski"

        # Attempt 0 -> base + suffix if too long (mock len > 20 simulation)
        long_base = "a" * 25
        variant_long = reg_page._generate_login_variant(long_base, 0)
        assert len(variant_long) > 25
        assert "." in variant_long

        # Attempt > 0 -> base + suffix
        variant_1 = reg_page._generate_login_variant(base, 1)
        assert base in variant_1
        assert "." in variant_1
        assert variant_1 != base

    def test_ensure_unique_identity_success_first_try(self, reg_page):
        """Test flow when first login is available."""
        # Setup mocks
        reg_page.input_login = MagicMock()
        reg_page._check_availability = MagicMock(return_value=True)
        reg_page._select_domain = MagicMock(return_value=True)

        identity = {"login": "test.user", "domain": "interia.pl"}

        reg_page._ensure_unique_identity(identity)

        # Verify
        reg_page._check_availability.assert_called()
        assert identity['login'] == "test.user"

    def test_ensure_unique_identity_retries(self, reg_page):
        """Test flow when first login is taken, second available."""
        reg_page.input_login = MagicMock()
        # First return False (taken), then True (available)
        reg_page._check_availability = MagicMock(side_effect=[False, True])
        reg_page._select_domain = MagicMock(return_value=True)

        identity = {"login": "taken.login", "domain": "interia.pl"}

        reg_page._ensure_unique_identity(identity)

        assert reg_page._check_availability.call_count == 2
        assert identity['login'] != "taken.login"  # Should have suffix
