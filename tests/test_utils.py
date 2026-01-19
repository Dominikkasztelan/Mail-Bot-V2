# tests/test_utils.py
from src.utils import clean_polish_chars

def test_clean_polish_chars_basic():
    assert clean_polish_chars("Żółć") == "zolc"
    assert clean_polish_chars("Łukasz") == "lukasz"
    assert clean_polish_chars("Śnieżka") == "sniezka"

def test_clean_polish_chars_mixed():
    assert clean_polish_chars("Mąka i Woda") == "maka i woda"

def test_clean_polish_chars_no_change():
    assert clean_polish_chars("simple text") == "simple text"
