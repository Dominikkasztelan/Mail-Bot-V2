# tests/test_smoke_e2e.py
import pytest
from playwright.sync_api import Page, expect
from src.registration_page import RegistrationPage


# Oznaczamy test jako "slow", żeby nie odpalał się przy szybkich testach jednostkowych
# (Wymaga: pip install pytest-playwright)
@pytest.mark.slow
def test_interia_form_selectors_are_valid(page: Page):
    """
    SMOKE TEST: Wchodzi na prawdziwą stronę Interii i sprawdza,
    czy kluczowe pola formularza nadal istnieją.
    Nie zakłada konta! Tylko sprawdza obecność elementów.
    """
    bot = RegistrationPage(page)

    # 1. Załaduj stronę
    try:
        bot.load()  # To wywoła page.goto()
    except Exception:
        pytest.fail("Nie udało się wejść na stronę Interii (Timeout/Błąd sieci)")

    # 2. Sprawdź czy widzimy kluczowe pola (czy Interia nie zmieniła HTMLa)
    # Używamy asercji Playwrighta 'expect', która czeka (auto-wait)
    expect(bot.input_name).to_be_visible(timeout=5000)
    expect(bot.input_surname).to_be_visible(timeout=5000)
    expect(bot.input_login).to_be_visible(timeout=5000)
    expect(bot.input_password).to_be_visible(timeout=5000)

    # Jeśli ten test przejdzie, to znaczy, że Twój RegistrationPage jest kompatybilny
    # z aktualną wersją strony Interia.pl.