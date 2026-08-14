# `books.py` API Reference

`books.py` provides the `Book` data model and the `BookCollection` class, which manages an in-memory list of books that is automatically persisted to a JSON file (`data.json`) on every mutation.

## Usage Example

```python
from books import BookCollection
from exceptions import ValidationError, StorageError

collection = BookCollection()  # loads existing books from data.json

try:
    collection.add_book("Dune", "Frank Herbert", 1965)
except ValidationError as e:
    print(f"Could not add book: {e}")

collection.mark_as_read("Dune")
matches = collection.find_by_author("Herbert")
recent = collection.find_by_year_range(1960, 1970)
collection.remove_book("Dune")
```

---

## `Book`

A `@dataclass` representing a single book entry.

| Attribute | Type | Description |
|---|---|---|
| `title` | `str` | The book's title. |
| `author` | `str` | The book's author. |
| `year` | `int` | Publication year. Must be non-negative and not later than the current calendar year. |
| `read` | `bool` | Whether the book has been marked as read. Defaults to `False`. |

```python
>>> Book(title="Dune", author="Frank Herbert", year=1965)
Book(title='Dune', author='Frank Herbert', year=1965, read=False)
```

---

## `BookCollection`

An in-memory collection of `Book` objects backed by a JSON file. On construction, it loads existing data via `load_books()`. Mutating methods (`add_book`, `remove_book`, `mark_as_read`) persist changes to disk automatically.

### `__init__() -> None`
Initializes the collection and loads any existing books from `DATA_FILE`.

### `load_books() -> None`
Loads books from the JSON file if it exists, populating `self.books`.

- **Never raises.** Falls back to an empty collection (with a printed warning) if the file is missing, unreadable, corrupted, or contains malformed entries.
- If the file exists but is corrupted (invalid JSON) or has an unexpected shape (not a JSON list), a timestamped backup (`data.json.corrupted.<timestamp>.bak`) is saved before falling back to empty, so data isn't silently lost.
- **Gotcha**: malformed individual entries (e.g., missing required fields) are skipped with a warning rather than aborting the whole load.

### `save_books() -> None`
Serializes every `Book` in `self.books` to `DATA_FILE` as a JSON array, overwriting existing content.

- **Raises**: `StorageError` if the file cannot be written (permission denied, disk full, invalid path).

### `add_book(title: str, author: str, year: int) -> Book`
Adds a new book to the collection and persists it.

| Param | Description |
|---|---|
| `title` | Stripped of whitespace; must not be empty. |
| `author` | Stripped of whitespace; must not be empty. |
| `year` | Non-negative integer (`bool` rejected), and not later than the current calendar year. |

- **Returns**: the newly created `Book`.
- **Raises**: `ValidationError` if title/author are empty, `year` is invalid or in the future, or a book with the same title+author (case-insensitive) already exists. `StorageError` if the save fails.

```python
>>> collection.add_book("Dune", "Frank Herbert", 1965)
Book(title='Dune', author='Frank Herbert', year=1965, read=False)
```

### `list_books() -> List[Book]`
Returns all books in insertion order (empty list if none).

### `find_book_by_title(title: str) -> Optional[Book]`
Case-insensitive exact-title lookup. Returns `None` if `title` is blank or no match is found.

### `mark_as_read(title: str) -> bool`
Marks the first book matching `title` (case-insensitive) as read and persists the change.

- **Returns**: `True` if found and marked, `False` if no match.
- **Raises**: `ValidationError` if `title` is empty.

### `remove_book(title: str) -> bool`
Removes the first book matching `title` (case-insensitive) and persists the change.

- **Returns**: `True` if found and removed, `False` if no match.
- **Raises**: `ValidationError` if `title` is empty.

### `find_by_author(author: str) -> List[Book]`
Substring, case-insensitive author search with whitespace normalization (runs of internal whitespace collapse to a single space).

- **Gotcha**: this is a substring match, not an exact match — searching `"Tolkien"` matches `"J.R.R. Tolkien"`.
- Returns an empty list if `author` is blank or no books match.

### `find_by_year_range(start_year: int, end_year: int) -> List[Book]`
Returns all books whose `year` falls within `[start_year, end_year]` (inclusive).

| Param | Description |
|---|---|
| `start_year` | Non-negative integer (`bool` rejected). |
| `end_year` | Non-negative integer (`bool` rejected); must not be earlier than `start_year`. |

- **Raises**: `ValidationError` if either year is invalid or `end_year < start_year`.
- **Gotcha**: unlike `add_book`, this method does **not** reject years later than the current calendar year — it only checks non-negativity and range ordering.

```python
>>> collection.find_by_year_range(1960, 1970)
[Book(title='Dune', author='Frank Herbert', year=1965, read=False)]
```

---

## Internal Helpers

### `_data_file(mode: str) -> Iterator[TextIO]`
Context manager centralizing all `DATA_FILE` access; guarantees the file handle is closed even on error.

### `_backup_corrupted_file() -> Optional[str]`
Copies the current (corrupted) `DATA_FILE` to a timestamped backup (`<DATA_FILE>.corrupted.<timestamp>.bak`) so data isn't lost when `load_books()` falls back to an empty collection. Returns the backup path, or `None` if the backup itself failed.

---

## Exceptions

Both raised from `exceptions.py` and caught by type in `book_app.py`:

- **`ValidationError`** — invalid input (empty fields, bad year, duplicate book).
- **`StorageError`** — the JSON file could not be written.
