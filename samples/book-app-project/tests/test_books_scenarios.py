import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import stat
import threading

import pytest
import books
from books import BookCollection
from exceptions import StorageError, ValidationError


@pytest.fixture(autouse=True)
def use_temp_data_file(tmp_path, monkeypatch):
    """Use a temporary data file for each test so tests never touch real data.json."""
    temp_file = tmp_path / "data.json"
    temp_file.write_text("[]")
    monkeypatch.setattr(books, "DATA_FILE", str(temp_file))


@pytest.fixture
def collection():
    """Provide a fresh, empty BookCollection backed by the temp data file."""
    return BookCollection()


def _running_as_root() -> bool:
    return hasattr(os, "geteuid") and os.geteuid() == 0


class TestDuplicateBooks:
    """Scenario: adding duplicate books (same title and author)."""

    def test_duplicate_title_and_author_raises_validation_error(self, collection):
        collection.add_book("Dune", "Frank Herbert", 1965)

        with pytest.raises(ValidationError):
            collection.add_book("Dune", "Frank Herbert", 1965)
        assert len(collection.books) == 1

    def test_duplicate_check_is_case_and_whitespace_insensitive(self, collection):
        collection.add_book("Dune", "Frank Herbert", 1965)

        with pytest.raises(ValidationError):
            collection.add_book("  DUNE  ", "  frank herbert  ", 1965)
        assert len(collection.books) == 1

    def test_duplicate_check_ignores_year_differences(self, collection):
        # Duplicate detection is based on title + author only, so a
        # different year still counts as a duplicate.
        collection.add_book("Dune", "Frank Herbert", 1965)

        with pytest.raises(ValidationError):
            collection.add_book("Dune", "Frank Herbert", 2000)
        assert len(collection.books) == 1

    def test_duplicate_error_message_includes_title_and_author(self, collection):
        collection.add_book("Dune", "Frank Herbert", 1965)

        with pytest.raises(ValidationError, match="Dune.*Frank Herbert"):
            collection.add_book("Dune", "Frank Herbert", 1965)

    def test_same_title_different_author_is_not_a_duplicate(self, collection):
        collection.add_book("Legend", "David Gemmell", 1984)

        book = collection.add_book("Legend", "Marie Lu", 2011)

        assert len(collection.books) == 2
        assert book.author == "Marie Lu"

    def test_same_author_different_title_is_not_a_duplicate(self, collection):
        collection.add_book("Dune", "Frank Herbert", 1965)

        book = collection.add_book("Dune Messiah", "Frank Herbert", 1969)

        assert len(collection.books) == 2
        assert book.title == "Dune Messiah"


class TestRemoveBookPartialTitleMatch:
    """Scenario: removing a book using a partial/substring title.

    ``BookCollection.remove_book`` requires an *exact* (case- and
    whitespace-insensitive) title match via ``find_book_by_title``. A
    partial/substring title must NOT remove an unrelated book that merely
    contains it as a substring (unlike the intentionally-buggy sample in
    samples/book-app-buggy, which uses a naive ``in`` substring check).
    """

    def test_partial_title_does_not_remove_unrelated_book(self, collection):
        collection.add_book("Dune Messiah", "Frank Herbert", 1969)

        result = collection.remove_book("Dune")

        assert result is False
        assert collection.find_book_by_title("Dune Messiah") is not None
        assert len(collection.books) == 1

    def test_partial_title_only_removes_exact_match_when_both_exist(self, collection):
        collection.add_book("Dune", "Frank Herbert", 1965)
        collection.add_book("Dune Messiah", "Frank Herbert", 1969)

        result = collection.remove_book("Dune")

        assert result is True
        assert collection.find_book_by_title("Dune") is None
        assert collection.find_book_by_title("Dune Messiah") is not None
        assert len(collection.books) == 1

    def test_substring_in_middle_of_title_does_not_match(self, collection):
        collection.add_book("The Hobbit", "J.R.R. Tolkien", 1937)

        result = collection.remove_book("Hobbit")

        assert result is False
        assert len(collection.books) == 1

    def test_exact_title_with_case_and_whitespace_differences_still_matches(self, collection):
        collection.add_book("Dune", "Frank Herbert", 1965)

        result = collection.remove_book("  dune  ")

        assert result is True
        assert collection.books == []


class TestFindOnEmptyCollection:
    """Scenario: finding books when the collection has zero books."""

    @pytest.mark.parametrize(
        "title",
        ["Dune", "", "   ", "Nonexistent Book"],
        ids=["normal-title", "empty", "whitespace", "nonexistent"],
    )
    def test_find_book_by_title_returns_none(self, collection, title):
        assert collection.find_book_by_title(title) is None

    @pytest.mark.parametrize(
        "author",
        ["Frank Herbert", "", "   ", "Nobody"],
        ids=["normal-author", "empty", "whitespace", "nonexistent"],
    )
    def test_find_by_author_returns_empty_list(self, collection, author):
        assert collection.find_by_author(author) == []

    def test_list_books_returns_empty_list(self, collection):
        assert collection.list_books() == []

    def test_remove_book_on_empty_collection_returns_false(self, collection):
        assert collection.remove_book("Anything") is False

    def test_mark_as_read_on_empty_collection_returns_false(self, collection):
        assert collection.mark_as_read("Anything") is False


class TestSavePermissionErrors:
    """Scenario: file permission errors while saving the collection."""

    def test_save_wraps_permission_error_in_storage_error(self, collection, monkeypatch):
        def fake_open(*args, **kwargs):
            raise PermissionError("Permission denied (simulated)")

        monkeypatch.setattr(books, "open", fake_open, raising=False)

        with pytest.raises(StorageError):
            collection.add_book("Dune", "Frank Herbert", 1965)

    def test_save_permission_error_does_not_discard_in_memory_book(self, collection, monkeypatch):
        def fake_open(*args, **kwargs):
            raise PermissionError("Permission denied (simulated)")

        monkeypatch.setattr(books, "open", fake_open, raising=False)

        with pytest.raises(StorageError):
            collection.add_book("Dune", "Frank Herbert", 1965)

        # The book is appended to the in-memory list before save_books is
        # called, so it remains present even though persistence failed.
        assert len(collection.books) == 1
        assert collection.books[0].title == "Dune"

    def test_storage_error_message_mentions_data_file(self, collection, monkeypatch):
        def fake_open(*args, **kwargs):
            raise PermissionError("Permission denied (simulated)")

        monkeypatch.setattr(books, "open", fake_open, raising=False)

        with pytest.raises(StorageError, match="Could not save books"):
            collection.add_book("Dune", "Frank Herbert", 1965)

    @pytest.mark.skipif(
        os.name == "nt" or _running_as_root(),
        reason="POSIX file permission enforcement is unavailable on Windows or when running as root",
    )
    def test_save_to_a_real_read_only_file_raises_storage_error(self, tmp_path, monkeypatch):
        data_file = tmp_path / "data.json"
        data_file.write_text("[]")
        monkeypatch.setattr(books, "DATA_FILE", str(data_file))
        collection = BookCollection()
        os.chmod(data_file, stat.S_IREAD)

        try:
            with pytest.raises(StorageError):
                collection.add_book("Dune", "Frank Herbert", 1965)
        finally:
            os.chmod(data_file, stat.S_IREAD | stat.S_IWRITE)


class TestConcurrentAccess:
    """Scenario: concurrent access to the same book collection / data file.

    ``BookCollection`` has no built-in locking or transactional guarantees,
    so these tests document its actual current behavior under concurrent
    access rather than asserting an "ideal" thread-safe outcome.
    """

    def test_two_instances_sharing_a_file_can_lose_updates(self, tmp_path, monkeypatch):
        data_file = tmp_path / "data.json"
        data_file.write_text("[]")
        monkeypatch.setattr(books, "DATA_FILE", str(data_file))

        collection_a = BookCollection()
        collection_b = BookCollection()

        collection_a.add_book("1984", "George Orwell", 1949)
        # collection_b was loaded before collection_a's save, so its
        # in-memory state doesn't know about "1984". Its own save overwrites
        # the file, silently losing collection_a's change - a classic
        # "lost update" race condition with no locking in place.
        collection_b.add_book("Dune", "Frank Herbert", 1965)

        reloaded = BookCollection()
        titles = {b.title for b in reloaded.books}
        assert titles == {"Dune"}
        assert "1984" not in titles

    def test_concurrent_add_book_calls_from_multiple_threads(self, collection):
        errors = []

        def add_book(i):
            try:
                collection.add_book(f"Book {i}", f"Author {i}", 2000 + i)
            except Exception as e:  # pragma: no cover - defensive, should not trigger
                errors.append(e)

        threads = [threading.Thread(target=add_book, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        # In-memory list.append() is atomic under the GIL, so no thread's
        # addition is lost from self.books even without explicit locking.
        assert len(collection.books) == 10
        titles = {b.title for b in collection.books}
        assert titles == {f"Book {i}" for i in range(10)}

    def test_concurrent_saves_leave_data_file_as_valid_json(self, collection, tmp_path):
        def add_book(i):
            collection.add_book(f"Book {i}", f"Author {i}", 2000 + i)

        threads = [threading.Thread(target=add_book, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Regardless of which thread's save_books() call "won" the race to
        # write last, the resulting file must still be valid, parseable JSON
        # (no partial/corrupted writes), even though it may not reflect
        # every addition made in memory.
        reloaded = BookCollection()
        assert isinstance(reloaded.books, list)
