class BotError(Exception):
    """Bazowa klasa dla wszystkich błędów naszego bota."""
    pass

class ElementNotFoundError(BotError):
    """Rzucany, gdy bot nie może znaleźć elementu na stronie (np. zmiana HTML)."""
    pass

class CaptchaSolveError(BotError):
    """Rzucany, gdy solver Captchy zawiedzie mimo prób."""
    pass

class RegistrationFailedError(BotError):
    """Rzucany, gdy formularz został wysłany, ale nie nastąpiło przekierowanie (błąd 10001 itp)."""
    pass

class ConfigurationError(BotError):
    """Błąd w pliku config.py lub brak kluczy API."""
    pass