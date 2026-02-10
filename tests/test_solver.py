# tests/test_solver.py
from unittest.mock import MagicMock, patch

import pytest

from src.captcha_solver import CaptchaSolver


# Fixture: Prepares a "fake" Client before each test
@pytest.fixture
def mock_genai_client():
    with patch("src.captcha_solver.genai.Client") as mock_client:
        yield mock_client

def test_solver_parses_json_correctly(mock_genai_client):
    """
    Scenario: Gemini returns correct JSON [1, 5].
    Expectation: Method returns python list [1, 5].
    """
    mock_response = MagicMock()
    mock_response.text = "```json\n[1, 5]\n```"
    mock_instance = mock_genai_client.return_value
    mock_instance.models.generate_content.return_value = mock_response

    # We patch __init__ to avoid real API key validation during test instantiation
    with patch.object(CaptchaSolver, "__init__", lambda self, page: None):
        solver = CaptchaSolver(None)
        solver.api_keys = ["test_key"]
        solver.model_name = "gemini-1.5-flash"
        solver._get_client = MagicMock(return_value=mock_instance)

        # Pass bytes instead of filename
        result = solver._solve_grid(b"fake_image_bytes", "instrukcja")

    assert result == [1, 5]

def test_find_captcha_target_found(mock_genai_client):
    """Test finding a valid captcha target."""
    mock_frame = MagicMock()
    mock_locator = MagicMock()
    mock_locator.wait_for.return_value = None # success
    mock_frame.locator.return_value.first = mock_locator

    with patch("src.captcha_solver.API_KEYS", {"GEMINI": ["key"]}):
        solver = CaptchaSolver(MagicMock())
        result = solver._find_captcha_target(mock_frame)

    assert result == mock_locator

def test_is_solved_or_detached_true():
    """Test detection of detached frame."""
    mock_frame = MagicMock()
    mock_frame.is_detached.return_value = True

    with patch("src.captcha_solver.API_KEYS", {"GEMINI": ["key"]}):
         solver = CaptchaSolver(MagicMock())
         assert solver._is_solved_or_detached(mock_frame) is True
