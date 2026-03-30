class SmartDigestError(Exception):
    """Base application error."""


class ConfigurationError(SmartDigestError):
    """Raised when configuration is invalid."""


class ParserError(SmartDigestError):
    """Raised when Telegram channel parsing fails."""


class DigestError(SmartDigestError):
    """Raised when digest generation or delivery fails."""
