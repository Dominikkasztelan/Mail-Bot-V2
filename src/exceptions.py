# src/exceptions.py

class BotError(Exception):
    """Bazowa klasa dla wszystkich błędów naszego bota."""
    pass

class ElementNotFoundError(BotError):
    pass

class CaptchaSolveError(BotError):
    pass

class CaptchaBlockadeError(BotError):  # <--- DODAJ TO
    """Rzucany, gdy strona żąda weryfikacji, ale bot nie może znaleźć ramki Captcha."""
    pass

class RegistrationFailedError(BotError):
    pass

class ConfigurationError(BotError):
    pass