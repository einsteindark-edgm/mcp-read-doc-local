"""Custom exceptions for the MCP PDF Extract application."""


class DocumentLoadError(Exception):
    """Raised when a document cannot be loaded or read."""
    pass


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass