import multiprocessing
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from multiprocessing import Process

# Importy lokalne
from test_run import run_worker

from src.config import LAUNCHER_CONFIG
from src.logger_config import get_logger

# Inicjalizacja loggera dla procesu głównego
logger = get_logger("Launcher")


def main() -> None:
    """
    Główna funkcja zarządcza (Orchestrator).
    Uruchamia wiele procesów bota zgodnie z konfiguracją.
    """
    # Pobieramy konfigurację i rzutujemy na int
    concurrent_count: int = int(LAUNCHER_CONFIG.get("CONCURRENT_BROWSERS", 1))

    logger.info("=" * 60)
    logger.info("🚀 URUCHAMIANIE ZARZĄDCY BOTÓW")
    logger.info(f"👉 Liczba instancji do utworzenia: {concurrent_count}")
    logger.info("=" * 60)

    # Manager zarządza współdzielonymi obiektami między procesami
    manager = multiprocessing.Manager()

    # Tworzymy blokadę (Lock) przez Managera.
    # UWAGA: Nie typujemy tego jawnie jako ': Lock', ponieważ manager.Lock()
    # zwraca obiekt typu Proxy (AcquirerProxy), co powoduje błędy w IDE.
    file_lock = manager.Lock()

    processes: list[Process] = []

    try:
        for i in range(concurrent_count):
            instance_id = i + 1

            # Tworzymy proces
            p = multiprocessing.Process(
                target=run_worker,
                args=(instance_id, file_lock),
                name=f"Worker-{instance_id}"
            )

            processes.append(p)
            p.start()

            logger.info(f"➡️ [PID: {p.pid}] Uruchomiono proces nr {instance_id}")

        logger.info("=" * 60)
        logger.info("⏳ Oczekiwanie na zakończenie pracy wszystkich robotników...")

        # Czekamy na zakończenie każdego procesu
        for p in processes:
            p.join()
            logger.info(f"✅ Proces {p.name} zakończył pracę.")

        logger.info("🏁 WSZYSTKIE PROCESY ZAKOŃCZONE. Koniec programu.")

    except KeyboardInterrupt:
        logger.warning("\n🛑 Wykryto zatrzymanie (Ctrl+C)! Zabijanie procesów...")
        for p in processes:
            if p.is_alive():
                p.terminate()
                logger.warning(f"💀 Zabito proces {p.name}")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"💥 Błąd krytyczny w Launcherze: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Wymagane dla Windowsa
    multiprocessing.freeze_support()
    main()
