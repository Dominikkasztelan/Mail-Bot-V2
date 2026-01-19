# tests/test_solver.py
import pytest
from unittest.mock import MagicMock, patch, mock_open
from src.captcha_solver import CaptchaSolver
from playwright.sync_api import TimeoutError as PlaywrightTimeout

# Fikstura: Przygotowuje "fałszywego" klienta Google przed każdym testem
@pytest.fixture
def mock_genai_client():
    with patch("src.captcha_solver.genai.Client") as MockClient:
        yield MockClient

def test_solver_parses_json_correctly(mock_genai_client):
    """
    Scenariusz: Gemini zwraca poprawny JSON [1, 5].
    Oczekujemy: Metoda zwraca listę pythonową [1, 5].
    """
    mock_response = MagicMock()
    mock_response.text = "```json\n[1, 5]\n```"
    mock_instance = mock_genai_client.return_value
    mock_instance.models.generate_content.return_value = mock_response

    with patch("builtins.open", mock_open(read_data=b"img")):
        with patch.object(CaptchaSolver, "__init__", lambda self, page: None):
            solver = CaptchaSolver(None)
            solver.api_keys = ["test_key"]
            solver.model_name = "gemini-1.5-flash"
            
            result = solver._solve_grid("dummy.png", "instrukcja")

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

def test_is_solved_or_detached_true(mock_genai_client):
    """Test detection of detached frame."""
    mock_frame = MagicMock()
    mock_frame.is_detached.return_value = True
    
    with patch("src.captcha_solver.API_KEYS", {"GEMINI": ["key"]}):
         solver = CaptchaSolver(MagicMock())
         assert solver._is_solved_or_detached(mock_frame) is True