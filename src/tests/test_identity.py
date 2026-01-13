# tests/test_identity.py
from unittest.mock import patch, mock_open
from src.identity_manager import IdentityManager


def test_identity_structure():
    """Czy generator zwraca wszystkie wymagane pola?"""
    # Mockujemy sprawdzanie duplikatów (nie chcemy czytać plików z dysku)
    with patch.object(IdentityManager, 'check_duplicates', return_value=False):
        mgr = IdentityManager()
        data = mgr.generate()

    required = ["first_name", "last_name", "login", "password", "birth_day"]
    for field in required:
        assert field in data, f"Brakuje pola: {field}"

    # Login powinien być "czysty" (bez polskich znaków, małych liter)
    assert data["login"].islower()
    assert "ł" not in data["login"]


def test_check_duplicates_logic():
    """Czy funkcja poprawnie wykrywa istniejący login w pliku?"""
    # Symulujemy zawartość pliku bazy danych w pamięci RAM
    fake_db = "stary.login.123@interia.pl | haslo | ...\n"

    with patch("builtins.open", mock_open(read_data=fake_db)):
        with patch("os.path.exists", return_value=True):
            mgr = IdentityManager()
            # Ten login jest w "pliku" -> True
            assert mgr.check_duplicates("stary.login.123") is True
            # Tego nie ma -> False
            assert mgr.check_duplicates("nowy.unikalny") is False