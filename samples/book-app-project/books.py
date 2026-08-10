import json
from dataclasses import dataclass, asdict
from typing import List, Optional

DATA_FILE = "data.json"


@dataclass
class Book:
    title: str
    author: str
    year: int
    read: bool = False


class BookCollection:
    def __init__(self) -> None:
        self.books: List[Book] = []
        self.load_books()

    def load_books(self) -> None:
        """Load books from the JSON file if it exists.

        Falls back to an empty collection (with a warning) if the file is
        missing, unreadable, corrupted, or contains malformed entries.
        """
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            self.books = []
            return
        except json.JSONDecodeError:
            print("Warning: data.json is corrupted. Starting with empty collection.")
            self.books = []
            return
        except PermissionError:
            print(f"Warning: permission denied reading {DATA_FILE}. Starting with empty collection.")
            self.books = []
            return

        if not isinstance(data, list):
            print("Warning: data.json has an unexpected format. Starting with empty collection.")
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

        Raises:
            OSError: If the data file cannot be written (e.g. permission
                denied, disk full, or an invalid path).
        """
        try:
            with open(DATA_FILE, "w") as f:
                json.dump([asdict(b) for b in self.books], f, indent=2)
        except OSError as e:
            raise OSError(f"Could not save books to {DATA_FILE}: {e}") from e

    def add_book(self, title: str, author: str, year: int) -> Book:
        """Add a new book to the collection and persist it.

        Raises:
            ValueError: If title/author are empty, year is not a
                non-negative integer, or the book (same title and author)
                already exists in the collection.
            OSError: If the collection cannot be saved to disk.
        """
        title = title.strip()
        author = author.strip()

        if not title:
            raise ValueError("Title cannot be empty.")
        if not author:
            raise ValueError("Author cannot be empty.")
        if not isinstance(year, int) or isinstance(year, bool) or year < 0:
            raise ValueError("Year must be a non-negative whole number.")
        if any(
            b.title.lower() == title.lower() and b.author.lower() == author.lower()
            for b in self.books
        ):
            raise ValueError(f'"{title}" by {author} is already in the collection.')

        book = Book(title=title, author=author, year=year)
        self.books.append(book)
        self.save_books()
        return book

    def list_books(self) -> List[Book]:
        return self.books

    def find_book_by_title(self, title: str) -> Optional[Book]:
        if not title or not title.strip():
            return None
        for book in self.books:
            if book.title.lower() == title.strip().lower():
                return book
        return None

    def mark_as_read(self, title: str) -> bool:
        """Mark a book as read by title.

        Raises:
            ValueError: If title is empty.
            OSError: If the collection cannot be saved to disk.
        """
        if not title or not title.strip():
            raise ValueError("Title cannot be empty.")
        book = self.find_book_by_title(title)
        if book:
            book.read = True
            self.save_books()
            return True
        return False

    def remove_book(self, title: str) -> bool:
        """Remove a book by title.

        Raises:
            ValueError: If title is empty.
            OSError: If the collection cannot be saved to disk.
        """
        if not title or not title.strip():
            raise ValueError("Title cannot be empty.")
        book = self.find_book_by_title(title)
        if book:
            self.books.remove(book)
            self.save_books()
            return True
        return False

    def find_by_author(self, author: str) -> List[Book]:
        """Find all books by a given author."""
        if not author or not author.strip():
            return []
        return [b for b in self.books if b.author.lower() == author.strip().lower()]
