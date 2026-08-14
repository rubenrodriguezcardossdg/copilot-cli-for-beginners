import json
import re
import shutil
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Iterator, List, Optional, TextIO

from exceptions import StorageError, ValidationError

DATA_FILE = "data.json"


@contextmanager
def _data_file(mode: str) -> Iterator[TextIO]:
    """Context manager that opens ``DATA_FILE`` and guarantees it is closed.

    Centralizes all file access for :class:`BookCollection` behind a single
    code path, instead of each method calling ``open()`` directly. The file
    is always closed on exit, even if an exception occurs while it is open.

    Args:
        mode (str): The file mode to open ``DATA_FILE`` with (e.g. ``"r"``
            for reading, ``"w"`` for writing).

    Yields:
        TextIO: The open file handle.

    Raises:
        OSError: If the file cannot be opened or closed (e.g. missing file,
            permission denied, disk full). Callers are responsible for
            catching and translating specific ``OSError`` subclasses as
            needed.

    Example:
        >>> with _data_file("r") as f:
        ...     data = f.read()
    """
    f = open(DATA_FILE, mode)
    try:
        yield f
    finally:
        f.close()


def _backup_corrupted_file() -> Optional[str]:
    """Copy the current (corrupted) ``DATA_FILE`` to a timestamped backup.

    Used so that data isn't silently lost when :meth:`BookCollection.load_books`
    detects a corrupted or malformed ``DATA_FILE`` and falls back to an
    empty collection. The original file is left untouched.

    Returns:
        Optional[str]: The path of the backup file that was created, or
            ``None`` if the backup could not be created (e.g. the original
            file no longer exists or cannot be read).

    Example:
        >>> _backup_corrupted_file()
        'data.json.corrupted.20240101120000.bak'
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = f"{DATA_FILE}.corrupted.{timestamp}.bak"
    try:
        shutil.copy2(DATA_FILE, backup_path)
    except OSError:
        return None
    return backup_path


@dataclass
class Book:
    """A single book entry in the collection.

    Attributes:
        title (str): The book's title.
        author (str): The book's author.
        year (int): The publication year.
        read (bool): Whether the book has been marked as read.
            Defaults to ``False``.

    Example:
        >>> Book(title="Dune", author="Frank Herbert", year=1965)
        Book(title='Dune', author='Frank Herbert', year=1965, read=False)
    """

    title: str
    author: str
    year: int
    read: bool = False


class BookCollection:
    """An in-memory collection of :class:`Book` objects backed by a JSON file.

    On construction, the collection is loaded from ``DATA_FILE`` (see
    :meth:`load_books`). Mutating methods (:meth:`add_book`,
    :meth:`remove_book`, :meth:`mark_as_read`) persist changes back to disk
    automatically.

    Example:
        >>> collection = BookCollection()
        >>> collection.add_book("Dune", "Frank Herbert", 1965)
        Book(title='Dune', author='Frank Herbert', year=1965, read=False)
    """

    def __init__(self) -> None:
        """Initialize the collection, loading any existing books from disk."""
        self.books: List[Book] = []
        self.load_books()

    def load_books(self) -> None:
        """Load books from the JSON file if it exists.

        Reads ``DATA_FILE`` and populates ``self.books`` with the parsed
        entries. Falls back to an empty collection (with a printed warning)
        if the file is missing, unreadable, corrupted, or contains
        malformed entries; this method never raises. When the file exists
        but is corrupted (invalid JSON) or has an unexpected shape (not a
        JSON list), a timestamped backup copy is saved (see
        :func:`_backup_corrupted_file`) before falling back to an empty
        collection, so the original data isn't silently lost.

        Returns:
            None: Updates ``self.books`` in place.

        Example:
            >>> collection = BookCollection()
            >>> collection.load_books()
            >>> collection.books
            []
        """
        try:
            with _data_file("r") as f:
                data = json.load(f)
        except FileNotFoundError:
            self.books = []
            return
        except json.JSONDecodeError:
            backup_path = _backup_corrupted_file()
            if backup_path:
                print(
                    f"Warning: {DATA_FILE} is corrupted. A copy has been saved to "
                    f"{backup_path}. Starting with empty collection."
                )
            else:
                print(f"Warning: {DATA_FILE} is corrupted. Starting with empty collection.")
            self.books = []
            return
        except PermissionError:
            print(f"Warning: permission denied reading {DATA_FILE}. Starting with empty collection.")
            self.books = []
            return

        if not isinstance(data, list):
            backup_path = _backup_corrupted_file()
            if backup_path:
                print(
                    f"Warning: {DATA_FILE} has an unexpected format. A copy has been saved "
                    f"to {backup_path}. Starting with empty collection."
                )
            else:
                print(f"Warning: {DATA_FILE} has an unexpected format. Starting with empty collection.")
            self.books = []
            return

        books: List[Book] = []
        for entry in data:
            try:
                books.append(Book(**entry))
            except TypeError as e:
                print(f"Warning: skipping malformed book entry {entry!r}: {e}")
        self.books = books

    def save_books(self) -> None:
        """Save the current book collection to JSON.

        Serializes every :class:`Book` in ``self.books`` and writes them to
        ``DATA_FILE`` as a JSON array, overwriting any existing content.

        Returns:
            None

        Raises:
            StorageError: If the data file cannot be written (e.g. permission
                denied, disk full, or an invalid path).

        Example:
            >>> collection = BookCollection()
            >>> collection.add_book("Dune", "Frank Herbert", 1965)  # calls save_books internally
            Book(title='Dune', author='Frank Herbert', year=1965, read=False)
        """
        try:
            with _data_file("w") as f:
                json.dump([asdict(b) for b in self.books], f, indent=2)
        except OSError as e:
            raise StorageError(f"Could not save books to {DATA_FILE}: {e}") from e

    def add_book(self, title: str, author: str, year: int) -> Book:
        """Add a new book to the collection and persist it.

        Args:
            title (str): The book's title. Leading/trailing whitespace is
                stripped; must not be empty after stripping.
            author (str): The book's author. Leading/trailing whitespace is
                stripped; must not be empty after stripping.
            year (int): The publication year. Must be a non-negative
                integer (``bool`` values are rejected).

        Returns:
            Book: The newly created and persisted book.

        Raises:
            ValidationError: If title/author are empty, year is not a
                non-negative integer, or the book (same title and author)
                already exists in the collection.
            StorageError: If the collection cannot be saved to disk.

        Example:
            >>> collection = BookCollection()
            >>> collection.add_book("Dune", "Frank Herbert", 1965)
            Book(title='Dune', author='Frank Herbert', year=1965, read=False)
        """
        title = title.strip()
        author = author.strip()

        if not title:
            raise ValidationError("Title cannot be empty.")
        if not author:
            raise ValidationError("Author cannot be empty.")
        if not isinstance(year, int) or isinstance(year, bool) or year < 0:
            raise ValidationError("Year must be a non-negative whole number.")
        if any(
            b.title.lower() == title.lower() and b.author.lower() == author.lower()
            for b in self.books
        ):
            raise ValidationError(f'"{title}" by {author} is already in the collection.')

        book = Book(title=title, author=author, year=year)
        self.books.append(book)
        self.save_books()
        return book

    def list_books(self) -> List[Book]:
        """Return all books currently in the collection.

        Returns:
            List[Book]: All books in the collection, in insertion order.
                Returns an empty list if the collection has no books.

        Example:
            >>> collection = BookCollection()
            >>> collection.add_book("Dune", "Frank Herbert", 1965)
            Book(title='Dune', author='Frank Herbert', year=1965, read=False)
            >>> collection.list_books()
            [Book(title='Dune', author='Frank Herbert', year=1965, read=False)]
        """
        return self.books

    def find_book_by_title(self, title: str) -> Optional[Book]:
        """Find a single book by its exact (case-insensitive) title.

        Args:
            title (str): The title to search for. Matching is
                case-insensitive and ignores leading/trailing whitespace.

        Returns:
            Optional[Book]: The matching book, or ``None`` if ``title`` is
                empty/blank or no book with that title exists.

        Example:
            >>> collection = BookCollection()
            >>> collection.add_book("Dune", "Frank Herbert", 1965)
            Book(title='Dune', author='Frank Herbert', year=1965, read=False)
            >>> collection.find_book_by_title("dune")
            Book(title='Dune', author='Frank Herbert', year=1965, read=False)
        """
        if not title or not title.strip():
            return None
        for book in self.books:
            if book.title.lower() == title.strip().lower():
                return book
        return None

    def mark_as_read(self, title: str) -> bool:
        """Mark a book as read by title.

        Args:
            title (str): The title of the book to mark as read (case
                insensitive, whitespace is ignored). Must not be empty.

        Returns:
            bool: ``True`` if a matching book was found and marked as read
                (and the change was persisted); ``False`` if no book with
                that title exists.

        Raises:
            ValidationError: If title is empty.
            StorageError: If the collection cannot be saved to disk.

        Example:
            >>> collection = BookCollection()
            >>> collection.add_book("Dune", "Frank Herbert", 1965)
            Book(title='Dune', author='Frank Herbert', year=1965, read=False)
            >>> collection.mark_as_read("Dune")
            True
        """
        if not title or not title.strip():
            raise ValidationError("Title cannot be empty.")
        book = self.find_book_by_title(title)
        if book:
            book.read = True
            self.save_books()
            return True
        return False

    def remove_book(self, title: str) -> bool:
        """Remove a book by title.

        Args:
            title (str): The title of the book to remove (case
                insensitive, whitespace is ignored). Must not be empty.

        Returns:
            bool: ``True`` if a matching book was found, removed, and the
                change was persisted; ``False`` if no book with that title
                exists.

        Raises:
            ValidationError: If title is empty.
            StorageError: If the collection cannot be saved to disk.

        Example:
            >>> collection = BookCollection()
            >>> collection.add_book("Dune", "Frank Herbert", 1965)
            Book(title='Dune', author='Frank Herbert', year=1965, read=False)
            >>> collection.remove_book("dune")
            True
        """
        if not title or not title.strip():
            raise ValidationError("Title cannot be empty.")
        book = self.find_book_by_title(title)
        if book:
            self.books.remove(book)
            self.save_books()
            return True
        return False

    def find_by_author(self, author: str) -> List[Book]:
        """Find all books whose author partially matches a given name.

        Args:
            author (str): The author name (or partial name) to search for
                (case insensitive; leading/trailing whitespace is ignored
                and any run of internal whitespace is treated as a single
                space). Any book whose author contains ``author`` as a
                substring under that normalization is considered a match,
                so searching for "Tolkien" finds "J.R.R. Tolkien" and
                "Frank  Herbert" (extra spaces) still finds "Frank Herbert".

        Returns:
            List[Book]: All books matching ``author``, in insertion order.
                Returns an empty list if ``author`` is empty/blank or no
                books match.

        Example:
            >>> collection = BookCollection()
            >>> collection.add_book("Dune", "Frank Herbert", 1965)
            Book(title='Dune', author='Frank Herbert', year=1965, read=False)
            >>> collection.find_by_author("herbert")
            [Book(title='Dune', author='Frank Herbert', year=1965, read=False)]
        """
        if not author or not author.strip():
            return []
        normalized_author = re.sub(r"\s+", " ", author.strip())
        pattern = re.compile(re.escape(normalized_author), re.IGNORECASE)
        return [b for b in self.books if pattern.search(re.sub(r"\s+", " ", b.author))]
