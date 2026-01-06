from typing import TypedDict

class UserIdentity(TypedDict):
    """
    Definicja struktury danych tożsamości.
    Gwarantuje, że w słowniku zawsze będą te konkretne klucze.
    """
    first_name: str
    last_name: str
    birth_day: str
    birth_month_name: str
    birth_year: str
    password: str
    login: str
    domain: str