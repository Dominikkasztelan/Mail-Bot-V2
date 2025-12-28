#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stats_tracker.py - Moduł do śledzenia i analizy statystyk bota

Ten moduł zawiera klasy i funkcje do:
- Śledzenia statystyk w czasie rzeczywistym
- Zapisywania danych do plików
- Generowania raportów i analiz
- Monitorowania wydajności bota
"""

import json
import time
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


class StatsTracker:
    """
    Klasa do śledzenia statystyk procesu tworzenia kont

    Funkcjonalności:
    - Śledzenie prób tworzenia kont w czasie rzeczywistym
    - Monitorowanie sukcesu/niepowodzenia CAPTCHA
    - Zapisywanie szczegółowych logów każdej próby
    - Generowanie statystyk sesji
    - Eksport danych do różnych formatów
    """

    def __init__(self, stats_file: str = "bot_stats.json", session_name: str = None):
        """
        Inicjalizuje tracker statystyk

        Args:
            stats_file: Nazwa pliku do zapisywania statystyk
            session_name: Nazwa sesji (domyślnie timestamp)
        """
        self.stats_file = Path(stats_file)
        self.session_name = session_name or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Główne statystyki sesji
        self.session_stats = {
            "session_info": {
                "session_name": self.session_name,
                "session_start": datetime.now().isoformat(),
                "session_end": None,
                "total_duration": 0
            },
            "accounts": {
                "attempted": 0,
                "created": 0,
                "failed": 0,
                "failed_form": 0,
                "failed_captcha": 0,
                "failed_max_retries": 0,
                "uncertain": 0
            },
            "captcha": {
                "total_attempts": 0,
                "successful_attempts": 0,
                "failed_attempts": 0,
                "chatgpt_successes": 0,
                "manual_entries": 0,
                "refresh_count": 0
            },
            "performance": {
                "success_rate": 0.0,
                "captcha_success_rate": 0.0,
                "average_time_per_account": 0.0,
                "total_full_restarts": 0,
                "fastest_account_time": None,
                "slowest_account_time": None
            },
            "details": []
        }

        # Bieżące konto
        self.current_account = None

        # Ustawienia
        self.auto_save = True
        self.save_interval = 30  # sekund
        self.last_save_time = time.time()

    def start_account_attempt(self, account_number: int, target_username: str = None) -> None:
        """
        Rozpoczyna śledzenie próby utworzenia konta

        Args:
            account_number: Numer konta w sekwencji
            target_username: Docelowa nazwa użytkownika (jeśli znana)
        """
        self.current_account = {
            "account_number": account_number,
            "target_username": target_username,
            "start_time": time.time(),
            "end_time": None,
            "duration": 0,
            "status": "in_progress",
            "username": None,
            "password": None,
            "email": None,
            "attempts": [],
            "total_attempts": 0,
            "captcha_attempts": 0,
            "captcha_successes": 0,
            "full_restarts": 0,
            "errors": [],
            "final_error": None
        }

        self.session_stats["accounts"]["attempted"] += 1
        self._log_event("account_started", account_number)

    def start_attempt(self, attempt_number: int, attempt_type: str = "full") -> None:
        """
        Rozpoczyna śledzenie pojedynczej próby

        Args:
            attempt_number: Numer próby dla tego konta
            attempt_type: Typ próby ("full", "captcha", "form")
        """
        if not self.current_account:
            raise ValueError("Nie rozpoczęto śledzenia konta")

        attempt = {
            "attempt_number": attempt_number,
            "attempt_type": attempt_type,
            "start_time": time.time(),
            "end_time": None,
            "duration": 0,
            "status": "in_progress",
            "captcha_attempts": 0,
            "captcha_method": None,  # "chatgpt", "manual", "auto"
            "error": None,
            "substeps": []
        }

        self.current_account["attempts"].append(attempt)
        self.current_account["total_attempts"] = attempt_number

        if attempt_type == "full":
            self.current_account["full_restarts"] = attempt_number - 1

    def record_captcha_attempt(self, method: str, success: bool, code: str = None, error: str = None) -> None:
        """
        Rejestruje próbę rozwiązania CAPTCHA

        Args:
            method: Metoda rozwiązania ("chatgpt", "manual", "auto")
            success: Czy próba się powiodła
            code: Wprowadzony kod CAPTCHA
            error: Opis błędu (jeśli wystąpił)
        """
        if not self.current_account or not self.current_account["attempts"]:
            return

        current_attempt = self.current_account["attempts"][-1]
        current_attempt["captcha_attempts"] += 1
        current_attempt["captcha_method"] = method

        # Aktualizuj statystyki konta
        self.current_account["captcha_attempts"] += 1

        # Aktualizuj statystyki sesji
        self.session_stats["captcha"]["total_attempts"] += 1

        if success:
            self.current_account["captcha_successes"] += 1
            self.session_stats["captcha"]["successful_attempts"] += 1

            if method == "chatgpt":
                self.session_stats["captcha"]["chatgpt_successes"] += 1
            elif method == "manual":
                self.session_stats["captcha"]["manual_entries"] += 1
        else:
            self.session_stats["captcha"]["failed_attempts"] += 1

        # Zapisz szczegóły
        captcha_detail = {
            "timestamp": datetime.now().isoformat(),
            "method": method,
            "success": success,
            "code": code[:3] + "***" if code and len(code) > 3 else code,  # Bezpieczeństwo
            "error": error
        }

        current_attempt["substeps"].append(captcha_detail)
        self._log_event("captcha_attempt", method, success)

    def record_captcha_refresh(self) -> None:
        """Rejestruje odświeżenie CAPTCHA"""
        self.session_stats["captcha"]["refresh_count"] += 1
        self._log_event("captcha_refresh")

    def finish_attempt(self, status: str, error: str = None) -> None:
        """
        Kończy bieżącą próbę

        Args:
            status: Status zakończenia ("success", "failed", "error")
            error: Opis błędu (jeśli wystąpił)
        """
        if not self.current_account or not self.current_account["attempts"]:
            return

        current_attempt = self.current_account["attempts"][-1]
        current_attempt["end_time"] = time.time()
        current_attempt["duration"] = current_attempt["end_time"] - current_attempt["start_time"]
        current_attempt["status"] = status
        current_attempt["error"] = error

        if error:
            self.current_account["errors"].append({
                "timestamp": datetime.now().isoformat(),
                "attempt": current_attempt["attempt_number"],
                "error": error
            })

    def finish_account(self, status: str, username: str = None, password: str = None,
                       email: str = None, final_error: str = None) -> None:
        """
        Kończy śledzenie próby utworzenia konta

        Args:
            status: Końcowy status ("created", "failed_form", "failed_captcha", "failed_max_retries", "error", "uncertain")
            username: Utworzona nazwa użytkownika
            password: Hasło konta
            email: Adres email
            final_error: Końcowy błąd (jeśli wystąpił)
        """
        if not self.current_account:
            return

        # Zakończ aktualną próbę jeśli jest w toku
        if self.current_account["attempts"] and self.current_account["attempts"][-1]["status"] == "in_progress":
            self.finish_attempt(status, final_error)

        # Aktualizuj dane konta
        self.current_account["end_time"] = time.time()
        self.current_account["duration"] = self.current_account["end_time"] - self.current_account["start_time"]
        self.current_account["status"] = status
        self.current_account["username"] = username
        self.current_account["password"] = "***hidden***" if password else None  # Bezpieczeństwo
        self.current_account["email"] = email
        self.current_account["final_error"] = final_error

        # Aktualizuj statystyki sesji
        if status == "created":
            self.session_stats["accounts"]["created"] += 1
        elif status == "failed_form":
            self.session_stats["accounts"]["failed_form"] += 1
            self.session_stats["accounts"]["failed"] += 1
        elif status == "failed_captcha":
            self.session_stats["accounts"]["failed_captcha"] += 1
            self.session_stats["accounts"]["failed"] += 1
        elif status == "failed_max_retries":
            self.session_stats["accounts"]["failed_max_retries"] += 1
            self.session_stats["accounts"]["failed"] += 1
        elif status == "uncertain":
            self.session_stats["accounts"]["uncertain"] += 1
        else:  # error lub inne
            self.session_stats["accounts"]["failed"] += 1

        # Dodaj konto do szczegółów
        self.session_stats["details"].append(self.current_account.copy())

        # Aktualizuj statystyki wydajności
        self._update_performance_stats()

        # Wyloguj zakończenie
        self._log_event("account_finished", status, username)

        # Auto-save jeśli włączone
        if self.auto_save:
            self._try_auto_save()

        # Wyczyść bieżące konto
        self.current_account = None

    def _update_performance_stats(self) -> None:
        """Aktualizuje statystyki wydajności"""
        accounts = self.session_stats["accounts"]
        performance = self.session_stats["performance"]

        # Wskaźnik sukcesu kont
        if accounts["attempted"] > 0:
            performance["success_rate"] = (accounts["created"] / accounts["attempted"]) * 100

        # Wskaźnik sukcesu CAPTCHA
        captcha = self.session_stats["captcha"]
        if captcha["total_attempts"] > 0:
            performance["captcha_success_rate"] = (captcha["successful_attempts"] / captcha["total_attempts"]) * 100

        # Średni czas na konto
        completed_accounts = [acc for acc in self.session_stats["details"] if acc["duration"] > 0]
        if completed_accounts:
            total_time = sum(acc["duration"] for acc in completed_accounts)
            performance["average_time_per_account"] = total_time / len(completed_accounts)

            # Najszybsze i najwolniejsze konto
            durations = [acc["duration"] for acc in completed_accounts]
            performance["fastest_account_time"] = min(durations)
            performance["slowest_account_time"] = max(durations)

        # Łączna liczba pełnych restartów
        performance["total_full_restarts"] = sum(acc["full_restarts"] for acc in self.session_stats["details"])

    def get_current_stats(self) -> Dict[str, Any]:
        """
        Zwraca bieżące statystyki w czytelnej formie

        Returns:
            Słownik z bieżącymi statystykami
        """
        return {
            "Sesja": self.session_name,
            "Czas trwania": self._format_duration(time.time() - time.mktime(
                datetime.fromisoformat(self.session_stats["session_info"]["session_start"]).timetuple())),
            "Konta próbowane": self.session_stats["accounts"]["attempted"],
            "Konta utworzone": self.session_stats["accounts"]["created"],
            "Konta nieudane": self.session_stats["accounts"]["failed"],
            "Wskaźnik sukcesu": f"{self.session_stats['performance']['success_rate']:.1f}%",
            "Próby CAPTCHA": self.session_stats["captcha"]["total_attempts"],
            "Sukces CAPTCHA": f"{self.session_stats['performance']['captcha_success_rate']:.1f}%",
            "ChatGPT sukcesy": self.session_stats["captcha"]["chatgpt_successes"],
            "Ręczne wprowadzenia": self.session_stats["captcha"]["manual_entries"],
            "Pełne restarty": self.session_stats["performance"]["total_full_restarts"],
            "Średni czas/konto": f"{self.session_stats['performance']['average_time_per_account']:.1f}s"
            if self.session_stats['performance']['average_time_per_account'] > 0 else "N/A"
        }

    def print_summary(self, detailed: bool = False) -> None:
        """
        Wyświetla podsumowanie statystyk

        Args:
            detailed: Czy wyświetlić szczegółowe informacje
        """
        print("\n" + "=" * 60)
        print(f"           PODSUMOWANIE SESJI: {self.session_name}")
        print("=" * 60)

        stats = self.get_current_stats()
        for key, value in stats.items():
            print(f"{key:25}: {value}")

        if detailed and self.session_stats["details"]:
            print("\n" + "-" * 60)
            print("SZCZEGÓŁOWE INFORMACJE")
            print("-" * 60)

            # Najlepsze konta
            successful = [acc for acc in self.session_stats["details"] if acc["status"] == "created"]
            if successful:
                fastest = min(successful, key=lambda x: x["duration"])
                print(f"Najszybsze konto:     {fastest['username']} ({fastest['duration']:.1f}s)")

                if len(successful) > 1:
                    slowest = max(successful, key=lambda x: x["duration"])
                    print(f"Najwolniejsze konto:  {slowest['username']} ({slowest['duration']:.1f}s)")

            # Statystyki błędów
            failed = [acc for acc in self.session_stats["details"] if acc["status"] != "created"]
            if failed:
                most_attempts = max(failed, key=lambda x: x["total_attempts"])
                print(
                    f"Najwięcej prób:       Konto #{most_attempts['account_number']} ({most_attempts['total_attempts']} prób)")

                # Najczęstsze błędy
                error_counts = {}
                for acc in failed:
                    if acc["final_error"]:
                        error_counts[acc["final_error"]] = error_counts.get(acc["final_error"], 0) + 1

                if error_counts:
                    most_common_error = max(error_counts.items(), key=lambda x: x[1])
                    print(f"Najczęstszy błąd:     {most_common_error[0]} ({most_common_error[1]}x)")

        print("=" * 60)

    def save_stats(self, filename: str = None) -> Path:
        """
        Zapisuje statystyki do pliku JSON

        Args:
            filename: Nazwa pliku (domyślnie używa self.stats_file)

        Returns:
            Ścieżka do zapisanego pliku
        """
        if filename:
            filepath = Path(filename)
        else:
            filepath = self.stats_file

        # Zaktualizuj informacje o sesji
        self.session_stats["session_info"]["session_end"] = datetime.now().isoformat()
        self.session_stats["session_info"]["total_duration"] = time.time() - time.mktime(
            datetime.fromisoformat(self.session_stats["session_info"]["session_start"]).timetuple()
        )

        # Utwórz katalog jeśli nie istnieje
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Zapisz do pliku
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.session_stats, f, indent=2, ensure_ascii=False)

        return filepath

    def export_to_csv(self, filename: str = None) -> Path:
        """
        Eksportuje statystyki kont do pliku CSV

        Args:
            filename: Nazwa pliku CSV

        Returns:
            Ścieżka do zapisanego pliku
        """
        if filename:
            filepath = Path(filename)
        else:
            filepath = self.stats_file.with_suffix('.csv')

        # Utwórz katalog jeśli nie istnieje
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Przygotuj dane
        fieldnames = [
            'account_number', 'username', 'email', 'status', 'duration',
            'total_attempts', 'captcha_attempts', 'captcha_successes',
            'full_restarts', 'final_error'
        ]

        # Zapisz do CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for account in self.session_stats["details"]:
                row = {field: account.get(field, '') for field in fieldnames}
                writer.writerow(row)

        return filepath

    def _try_auto_save(self) -> None:
        """Próbuje zapisać automatycznie jeśli minął odpowiedni czas"""
        current_time = time.time()
        if current_time - self.last_save_time >= self.save_interval:
            try:
                self.save_stats()
                self.last_save_time = current_time
            except Exception as e:
                print(f"⚠️ Błąd auto-save: {e}")

    def _log_event(self, event_type: str, *args) -> None:
        """Loguje zdarzenie do wewnętrznego loga"""
        # Tutaj można dodać logowanie do pliku lub zewnętrznego systemu
        pass

    def _format_duration(self, seconds: float) -> str:
        """
        Formatuje czas trwania w czytelnej formie

        Args:
            seconds: Liczba sekund

        Returns:
            Sformatowany czas
        """
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            minutes = (seconds % 3600) / 60
            return f"{hours:.1f}h {minutes:.0f}m"


class SessionAnalyzer:
    """
    Klasa do analizy i porównywania statystyk z różnych sesji
    """

    def __init__(self, stats_dir: str = "."):
        """
        Inicjalizuje analizator sesji

        Args:
            stats_dir: Katalog ze statystykami
        """
        self.stats_dir = Path(stats_dir)

    def load_session(self, filename: str) -> Dict[str, Any]:
        """
        Wczytuje statystyki sesji z pliku

        Args:
            filename: Nazwa pliku ze statystykami

        Returns:
            Słownik ze statystykami sesji
        """
        filepath = self.stats_dir / filename
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def compare_sessions(self, session1: str, session2: str) -> Dict[str, Any]:
        """
        Porównuje dwie sesje

        Args:
            session1: Nazwa pliku pierwszej sesji
            session2: Nazwa pliku drugiej sesji

        Returns:
            Słownik z porównaniem
        """
        stats1 = self.load_session(session1)
        stats2 = self.load_session(session2)

        comparison = {
            "session1": {
                "name": stats1["session_info"]["session_name"],
                "success_rate": stats1["performance"]["success_rate"],
                "accounts_created": stats1["accounts"]["created"],
                "captcha_success_rate": stats1["performance"]["captcha_success_rate"]
            },
            "session2": {
                "name": stats2["session_info"]["session_name"],
                "success_rate": stats2["performance"]["success_rate"],
                "accounts_created": stats2["accounts"]["created"],
                "captcha_success_rate": stats2["performance"]["captcha_success_rate"]
            }
        }

        # Oblicz różnice
        comparison["differences"] = {
            "success_rate_diff": stats2["performance"]["success_rate"] - stats1["performance"]["success_rate"],
            "accounts_diff": stats2["accounts"]["created"] - stats1["accounts"]["created"],
            "captcha_diff": stats2["performance"]["captcha_success_rate"] - stats1["performance"][
                "captcha_success_rate"]
        }

        return comparison


# Przykład użycia
if __name__ == "__main__":
    # Test trackera statystyk
    print("Testowanie StatsTracker...")

    tracker = StatsTracker("test_stats.json", "test_session")

    # Symulacja sesji
    tracker.start_account_attempt(1, "testuser1")
    tracker.start_attempt(1, "full")
    tracker.record_captcha_attempt("chatgpt", True, "ABC123")
    tracker.finish_attempt("success")
    tracker.finish_account("created", "testuser1", "password123", "testuser1@interia.pl")

    # Druga próba - nieudana
    tracker.start_account_attempt(2, "testuser2")
    tracker.start_attempt(1, "full")
    tracker.record_captcha_attempt("chatgpt", False, error="Niepoprawny kod")
    tracker.record_captcha_refresh()
    tracker.record_captcha_attempt("manual", True, "XYZ789")
    tracker.finish_attempt("failed")
    tracker.start_attempt(2, "full")
    tracker.finish_attempt("success")
    tracker.finish_account("created", "testuser2", "password456", "testuser2@interia.pl")

    # Wyświetl statystyki
    tracker.print_summary(detailed=True)

    # Zapisz statystyki
    json_file = tracker.save_stats()
    csv_file = tracker.export_to_csv()

    print(f"\nStatystyki zapisane do:")
    print(f"JSON: {json_file}")
    print(f"CSV:  {csv_file}")

    print(f"\nBieżące statystyki:")
    for key, value in tracker.get_current_stats().items():
        print(f"{key}: {value}")