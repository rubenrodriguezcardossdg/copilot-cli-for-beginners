"""Custom exception hierarchy for the book collection app.

Both ``books.py`` and ``utils.py`` previously signaled errors in different
ways (raising bare ``ValueError``/``OSError``, or silently returning a
default value with a printed warning). These classes give every module a
single, shared vocabulary for error handling.

Each exception also inherits from the built-in exception it replaces
(``ValueError`` or ``OSError``), so existing ``except ValueError`` /
``except OSError`` call sites and tests keep working unchanged.
"""


class BookAppError(Exception):
    """Base class for all book-app-project errors."""


class ValidationError(BookAppError, ValueError):
    """Raised when user-supplied book data fails validation."""


class StorageError(BookAppError, OSError):
    """Raised when the book collection cannot be read from or written to disk."""
