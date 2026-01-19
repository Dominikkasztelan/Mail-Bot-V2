# tests/test_solver.py
import pytest
from unittest.mock import MagicMock, patch, mock_open
from src.captcha_solver import CaptchaSolver


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
    # 1. Programujemy odpowiedź mocka
    mock_response = MagicMock()
    mock_response.text = "```json\n[1, 5]\n```"  # Symulujemy format Markdown

    mock_instance = mock_genai_client.return_value
    mock_instance.models.generate_content.return_value = mock_response

    # 2. Odpalamy solver (bez prawdziwego Page i bez pliku)
    with patch("builtins.open", mock_open(read_data=b"img")):
        solver = CaptchaSolver(page=MagicMock())
        solver.api_keys = ["test_key"]  # Override kluczy

        # Testujemy prywatną metodę parsującą (bo to ona zawiera logikę)
        result = solver._solve_grid("dummy.png", "instrukcja")

    # 3. Sprawdzamy wynik
    assert result == [1, 5]


def test_solver_handles_garbage_response(mock_genai_client):
    """
    Scenariusz: Gemini zwraca bzdury zamiast JSONa.
    Oczekujemy: Pustej listy (zamiast wywalenia programu).
    """
    mock_response = MagicMock()
    mock_response.text = "I cannot help with that."

    mock_instance = mock_genai_client.return_value
    mock_instance.models.generate_content.return_value = mock_response

    with patch("builtins.open", mock_open(read_data=b"img")):
        solver = CaptchaSolver(page=MagicMock())
        solver.api_keys = ["test_key"]
        result = solver._solve_grid("dummy.png", "instrukcja")

    assert result == []