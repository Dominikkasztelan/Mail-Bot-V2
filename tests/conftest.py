# tests/conftest.py
import sys
from pathlib import Path


# 1. Dodajemy katalog główny projektu do ścieżki Pythona
# Dzięki temu w testach możemy robić "from src.identity_manager import ..."
# Rozwiązuje problem "ModuleNotFoundError"
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

# 2. Tutaj w przyszłości możemy dodać globalne mocki
# np. żeby żaden test przypadkiem nie wysłał requestu do prawdziwego API, jeśli zapomnimy go zmockować