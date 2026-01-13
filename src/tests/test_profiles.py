# tests/test_profiles.py
from src.profile_manager import ProfileManager


def test_save_and_load_profile(tmp_path):
    """Test pełnego cyklu życia profilu na folderze tymczasowym."""

    # tmp_path to obiekt Path wskazujący na unikalny folder w /tmp
    mgr = ProfileManager(base_dir=str(tmp_path))

    # 1. Zapis
    # POPRAWKA: Symulujemy pełny obiekt storage_state (Słownik, a nie Lista)
    test_cookies = {
        "cookies": [{"name": "ciastko", "value": "smaczne"}],
        "origins": []
    }

    mgr.save_profile(test_cookies, metadata={"ua": "test-agent"})

    assert mgr.count_ready() == 1

    # 2. Odczyt (powinien przenieść plik do 'archive')
    profile = mgr.get_fresh_profile()

    assert profile is not None
    # Sprawdzamy czy to, co odczytaliśmy, jest tym samym co zapisaliśmy
    assert profile["cookies"] == test_cookies
    assert mgr.count_ready() == 0  # Folder ready powinien być pusty

    # Sprawdzamy czy plik trafił do archiwum
    assert len(list(mgr.used_dir.glob("*.json"))) == 1