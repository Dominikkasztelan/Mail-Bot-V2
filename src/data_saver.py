import csv
import pandas as pd
from pathlib import Path
from datetime import datetime

# Importuj logger z odpowiedniego modułu
from src.logger_config import get_logger

logger = get_logger(__name__)


class AccountDataSaver:
    """
    Klasa odpowiedzialna za zapisywanie danych kont do plików CSV i XLSX.
    Umożliwia również odczytywanie zapisanych danych.
    """

    def __init__(self, output_dir="saved_accounts"):
        """
        Inicjalizuje zapisywacz danych kont.

        Args:
            output_dir: Katalog, w którym będą zapisywane pliki
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Przygotowanie nazw plików z datą
        self.date_str = datetime.now().strftime("%Y%m%d")
        self.csv_file = self.output_dir / f"accounts_{self.date_str}.csv"
        self.xlsx_file = self.output_dir / f"accounts_{self.date_str}.xlsx"

        # Sprawdź czy pliki już istnieją i ewentualnie utwórz nagłówki
        self._init_files_if_needed()

    def _init_files_if_needed(self):
        """Inicjalizuje pliki z nagłówkami, jeśli nie istnieją"""
        # Definicja kolumn
        self.columns = [
            "first_name", "last_name", "username", "password",
            "day", "month", "year", "email", "creation_date", "status"
        ]

        # Inicjalizacja pliku CSV jeśli nie istnieje
        if not self.csv_file.exists():
            try:
                with open(self.csv_file, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(self.columns)
                logger.info(f"✅ Utworzono nowy plik CSV: {self.csv_file}")
            except Exception as e:
                logger.error(f"❌ Błąd podczas tworzenia pliku CSV: {e}")

        # Inicjalizacja pliku XLSX jeśli nie istnieje
        if not self.xlsx_file.exists():
            try:
                df = pd.DataFrame(columns=self.columns)
                df.to_excel(self.xlsx_file, index=False)
                logger.info(f"✅ Utworzono nowy plik XLSX: {self.xlsx_file}")
            except Exception as e:
                logger.error(f"❌ Błąd podczas tworzenia pliku XLSX: {e}")

    def save_account_data(self, account_data, status="created", save_format="both"):
        """
        Zapisuje dane konta do pliku.

        Args:
            account_data: Słownik z danymi konta
            status: Status rejestracji konta (created, failed, etc.)
            save_format: Format zapisu (csv, xlsx, both)

        Returns:
            bool: True jeśli zapisano pomyślnie, False w przeciwnym razie
        """
        # Dodaj dodatkowe pola
        full_data = account_data.copy()
        full_data["email"] = f"{account_data['username']}@interia.pl"
        full_data["creation_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_data["status"] = status

        # Mapuj kolumny, aby upewnić się, że zapisujemy w odpowiedniej kolejności
        row_data = [full_data.get(col, "") for col in self.columns]

        success = True

        # Zapisz do CSV
        if save_format.lower() in ["csv", "both"]:
            try:
                with open(self.csv_file, 'a', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(row_data)
                logger.info(f"✅ Zapisano dane konta {full_data['username']} do CSV")
            except Exception as e:
                logger.error(f"❌ Błąd podczas zapisywania do CSV: {e}")
                success = False

        # Zapisz do XLSX
        if save_format.lower() in ["xlsx", "both"]:
            try:
                # Wczytaj istniejący plik
                if self.xlsx_file.exists():
                    df = pd.read_excel(self.xlsx_file)
                else:
                    df = pd.DataFrame(columns=self.columns)

                # Dodaj nowy wiersz
                new_row = pd.DataFrame([row_data], columns=self.columns)
                df = pd.concat([df, new_row], ignore_index=True)

                # Zapisz plik
                df.to_excel(self.xlsx_file, index=False)
                logger.info(f"✅ Zapisano dane konta {full_data['username']} do XLSX")
            except Exception as e:
                logger.error(f"❌ Błąd podczas zapisywania do XLSX: {e}")
                success = False

        return success

    def load_accounts(self, file_format="csv"):
        """
        Wczytuje zapisane konta z pliku.

        Args:
            file_format: Format pliku (csv lub xlsx)

        Returns:
            list: Lista słowników z danymi kont
        """
        accounts = []

        if file_format.lower() == "csv":
            file_path = self.csv_file
            if not file_path.exists():
                logger.warning(f"⚠️ Plik CSV {file_path} nie istnieje")
                return accounts

            try:
                with open(file_path, 'r', newline='', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        accounts.append(dict(row))
                logger.info(f"✅ Wczytano {len(accounts)} kont z pliku CSV")
            except Exception as e:
                logger.error(f"❌ Błąd podczas wczytywania z CSV: {e}")

        elif file_format.lower() == "xlsx":
            file_path = self.xlsx_file
            if not file_path.exists():
                logger.warning(f"⚠️ Plik XLSX {file_path} nie istnieje")
                return accounts

            try:
                df = pd.read_excel(file_path)
                accounts = df.to_dict('records')
                logger.info(f"✅ Wczytano {len(accounts)} kont z pliku XLSX")
            except Exception as e:
                logger.error(f"❌ Błąd podczas wczytywania z XLSX: {e}")

        return accounts

    def get_account_by_username(self, username, file_format="csv"):
        """
        Wyszukuje konto po nazwie użytkownika.

        Args:
            username: Nazwa użytkownika do wyszukania
            file_format: Format pliku (csv lub xlsx)

        Returns:
            dict: Słownik z danymi konta lub None jeśli nie znaleziono
        """
        accounts = self.load_accounts(file_format)
        for account in accounts:
            if account.get("username") == username:
                return account

        logger.warning(f"⚠️ Nie znaleziono konta o nazwie użytkownika: {username}")
        return None


# Funkcja pomocnicza do łatwego użycia
def save_account(account_data, status="created", save_format="both", output_dir="saved_accounts"):
    """
    Funkcja pomocnicza do szybkiego zapisania danych konta.

    Args:
        account_data: Słownik z danymi konta
        status: Status rejestracji konta (created, failed, etc.)
        save_format: Format zapisu (csv, xlsx, both)
        output_dir: Katalog wyjściowy

    Returns:
        bool: True jeśli zapisano pomyślnie, False w przeciwnym razie
    """
    saver = AccountDataSaver(output_dir)
    return saver.save_account_data(account_data, status, save_format)
