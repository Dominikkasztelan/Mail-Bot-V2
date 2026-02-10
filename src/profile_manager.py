import json
import os
import time
import uuid
from pathlib import Path

from src.logger_config import get_logger

logger = get_logger("ProfileManager")


class ProfileManager:
    def __init__(self, base_dir: str = "data/profiles"):
        self.base_dir = Path(base_dir)
        self.ready_dir = self.base_dir / "ready"
        self.used_dir = self.base_dir / "archive"
        self.tmp_dir = self.base_dir / "tmp"

        # Tworzenie struktury katalogów
        for d in [self.ready_dir, self.used_dir, self.tmp_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def save_profile(self, cookies: dict, metadata: dict | None = None) -> None:
        """
        Zapisuje wygrzany profil. Używa katalogu tmp, aby zapis był atomowy.
        """
        profile_id = str(uuid.uuid4())
        filename = f"{profile_id}.json"
        tmp_path = self.tmp_dir / filename
        final_path = self.ready_dir / filename

        data = {
            "id": profile_id,
            "created_at": time.time(),
            "cookies": cookies,  # To jest storage_state z Playwrighta
            "metadata": metadata or {}
        }

        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # Atomowe przesunięcie do ready (bezpieczne wątkowo)
            os.rename(tmp_path, final_path)
            logger.info(f"💾 [MANAGER] Dodano nowy profil do puli: {profile_id}")
        except OSError as e:
            logger.error(f"❌ Błąd zapisu profilu: {e}")
            if tmp_path.exists():
                os.remove(tmp_path)

    def get_fresh_profile(self) -> dict | None:
        """
        Pobiera najstarszy dostępny profil i przenosi go do archiwum.
        Zwraca dane profilu lub None, jeśli kolejka jest pusta.
        """
        # Listujemy pliki i sortujemy po czasie (FIFO)
        files = sorted(list(self.ready_dir.glob("*.json")), key=lambda f: f.stat().st_mtime)

        if not files:
            return None

        for file_path in files:
            # Próba "zaklepania" pliku poprzez zmianę nazwy (lock)
            # Dodajemy prefix .lock, żeby inny proces go nie wziął
            locked_path = file_path.with_suffix(".json.lock")
            try:
                os.rename(file_path, locked_path)
            except OSError:
                # Ktoś inny właśnie wziął ten plik, próbujemy następny
                continue

            # Teraz mamy plik na wyłączność. Czytamy i przenosimy do archive.
            try:
                with open(locked_path, encoding="utf-8") as f:
                    data = json.load(f)

                archive_path = self.used_dir / file_path.name
                os.rename(locked_path, archive_path)

                logger.info(f"📤 [MANAGER] Pobrano profil: {data['id']}")
                return data
        # W przypadku błędu odczytu/Parsowania JSON
            except (OSError, json.JSONDecodeError) as e:
                logger.error(f"❌ Błąd odczytu profilu {file_path}: {e}")
                # W razie awarii próbujemy przywrócić lub usunąć uszkodzony
                if locked_path.exists():
                    os.remove(locked_path)  # Usuwamy uszkodzony
                return None

        return None

    def count_ready(self) -> int:
        return len(list(self.ready_dir.glob("*.json")))
