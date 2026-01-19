# src/utils.py
"""
Shared utility functions for the Mail Bot project.
"""


def clean_polish_chars(text: str) -> str:
    """
    Removes Polish diacritics and converts to lowercase.
    Useful for creating login names from Polish names.
    
    Args:
        text: Input string (e.g., "Żółć")
    
    Returns:
        Cleaned string (e.g., "zolc")
    """
    replacements = {
        'ł': 'l', 'Ł': 'l',
        'ś': 's', 'Ś': 's',
        'ą': 'a', 'Ą': 'a',
        'ż': 'z', 'Ż': 'z',
        'ź': 'z', 'Ź': 'z',
        'ć': 'c', 'Ć': 'c',
        'ń': 'n', 'Ń': 'n',
        'ó': 'o', 'Ó': 'o',
        'ę': 'e', 'Ę': 'e',
    }
    result = text.lower()
    for polish, ascii_char in replacements.items():
        result = result.replace(polish, ascii_char)
    return result
