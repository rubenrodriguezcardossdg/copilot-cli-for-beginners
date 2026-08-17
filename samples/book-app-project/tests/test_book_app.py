import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

import book_app
import books
from books import Book, BookCollection
from exceptions import StorageError, ValidationError


@pytest.fixture(autouse=True)
def use_temp_data_file(tmp_path, monkeypatch):
    """Back every test with a temporary data file and a fresh collection.

    ``book_app.collection`` is created once at import time from the real
    ``books.DATA_FILE``. Replacing it with a collection backed by a
    per-test temp file keeps tests isolated from each other and from any
    real ``data.json`` on disk.
    """
    temp_file = tmp_path / "data.json"
    temp_file.write_text("[]")
    monkeypatch.setattr(books, "DATA_FILE", str(temp_file))
    monkeypatch.setattr(book_app, "collection", BookCollection())


@pytest.fixture
def mock_inputs(monkeypatch):
    """Factory fixture that queues canned responses for sequential input() calls."""

    def _mock(responses):
        responses_iter = iter(responses)

        def fake_input(prompt=""):
            try:
                return next(responses_iter)
            except StopIteration:
                raise AssertionError(
                    f"input() was called more times than the {len(responses)} "
                    f"canned response(s) provided (prompt={prompt!r})"
                )

        monkeypatch.setattr("builtins.input", fake_input)

    return _mock


class TestShowBooks:
    """Tests for show_books."""

    def test_empty_list_prints_no_books_found(self, capsys):
        book_app.show_books([])

        assert "No books found." in capsys.readouterr().out

    def test_unread_book_shows_blank_status(self, capsys):
        book_app.show_books([Book(title="Dune", author="Frank Herbert", year=1965)])

        out = capsys.readouterr().out
        assert "1. [ ] Dune by Frank Herbert (1965)" in out

    def test_read_book_shows_checkmark_status(self, capsys):
        book_app.show_books(
            [Book(title="Dune", author="Frank Herbert", year=1965, read=True)]
        )

        out = capsys.readouterr().out
        assert "1. [✓] Dune by Frank Herbert (1965)" in out

    def test_multiple_books_are_numbered_in_order(self, capsys):
        book_app.show_books(
            [
                Book(title="1984", author="George Orwell", year=1949),
                Book(title="Dune", author="Frank Herbert", year=1965),
            ]
        )

        out = capsys.readouterr().out
        assert "1. [ ] 1984 by George Orwell (1949)" in out
        assert "2. [ ] Dune by Frank Herbert (1965)" in out


class TestHandleList:
    """Tests for handle_list."""

    def test_empty_collection_prints_no_books_found(self, capsys):
        book_app.handle_list()

        assert "No books found." in capsys.readouterr().out

    def test_populated_collection_lists_all_books(self, capsys):
        book_app.collection.add_book("Dune", "Frank Herbert", 1965)
        book_app.collection.add_book("1984", "George Orwell", 1949)

        book_app.handle_list()

        out = capsys.readouterr().out
        assert "Dune by Frank Herbert (1965)" in out
        assert "1984 by George Orwell (1949)" in out


class TestHandleAdd:
    """Tests for handle_add."""

    def test_happy_path_adds_book_and_prints_success(self, mock_inputs, capsys):
        mock_inputs(["Dune", "Frank Herbert", "1965"])

        book_app.handle_add()

        assert len(book_app.collection.list_books()) == 1
        assert "Book added successfully." in capsys.readouterr().out

    def test_empty_year_prints_error_and_does_not_add(self, mock_inputs, capsys):
        mock_inputs(["Dune", "Frank Herbert", ""])

        book_app.handle_add()

        assert book_app.collection.list_books() == []
        assert "Error: Year cannot be empty." in capsys.readouterr().out

    @pytest.mark.parametrize(
        "year_input",
        [
            pytest.param("abc", id="alphabetic"),
            pytest.param("19.65", id="decimal"),
            pytest.param("twenty", id="spelled-out"),
        ],
    )
    def test_non_numeric_year_prints_error_and_does_not_add(
        self, mock_inputs, capsys, year_input
    ):
        mock_inputs(["Dune", "Frank Herbert", year_input])

        book_app.handle_add()

        assert book_app.collection.list_books() == []
        assert "Error: Year must be a whole number." in capsys.readouterr().out

    def test_empty_title_prints_validation_error_and_does_not_add(
        self, mock_inputs, capsys
    ):
        mock_inputs(["", "Frank Herbert", "1965"])

        book_app.handle_add()

        assert book_app.collection.list_books() == []
        assert "Error: Title cannot be empty." in capsys.readouterr().out

    def test_duplicate_book_prints_validation_error(self, mock_inputs, capsys):
        book_app.collection.add_book("Dune", "Frank Herbert", 1965)
        mock_inputs(["Dune", "Frank Herbert", "1965"])

        book_app.handle_add()

        assert len(book_app.collection.list_books()) == 1
        assert "already in the collection" in capsys.readouterr().out

    def test_storage_error_on_save_is_reported(self, mock_inputs, capsys, monkeypatch):
        mock_inputs(["Dune", "Frank Herbert", "1965"])

        def raise_storage_error(*args, **kwargs):
            raise StorageError("disk full")

        monkeypatch.setattr(book_app.collection, "add_book", raise_storage_error)

        book_app.handle_add()

        assert "Error: Could not save the book: disk full" in capsys.readouterr().out


class TestHandleRemove:
    """Tests for handle_remove."""

    def test_existing_title_is_removed_and_reports_success(self, mock_inputs, capsys):
        book_app.collection.add_book("Dune", "Frank Herbert", 1965)
        mock_inputs(["Dune"])

        book_app.handle_remove()

        assert book_app.collection.list_books() == []
        assert "Book removed successfully." in capsys.readouterr().out

    def test_missing_title_reports_not_found(self, mock_inputs, capsys):
        mock_inputs(["Nonexistent Book"])

        book_app.handle_remove()

        assert "No book found with that title." in capsys.readouterr().out

    def test_empty_title_prints_validation_error(self, mock_inputs, capsys):
        mock_inputs([""])

        book_app.handle_remove()

        assert "Error: Title cannot be empty." in capsys.readouterr().out

    def test_storage_error_on_save_is_reported(self, mock_inputs, capsys, monkeypatch):
        book_app.collection.add_book("Dune", "Frank Herbert", 1965)
        mock_inputs(["Dune"])

        def raise_storage_error(*args, **kwargs):
            raise StorageError("disk full")

        monkeypatch.setattr(book_app.collection, "remove_book", raise_storage_error)

        book_app.handle_remove()

        assert "Error: Could not save changes: disk full" in capsys.readouterr().out


class TestHandleFind:
    """Tests for handle_find."""

    def test_matching_author_lists_books(self, mock_inputs, capsys):
        book_app.collection.add_book("Dune", "Frank Herbert", 1965)
        mock_inputs(["Herbert"])

        book_app.handle_find()

        assert "Dune by Frank Herbert (1965)" in capsys.readouterr().out

    def test_no_matches_prints_no_books_found(self, mock_inputs, capsys):
        mock_inputs(["Nobody"])

        book_app.handle_find()

        assert "No books found." in capsys.readouterr().out


class TestHandleSearchYear:
    """Tests for handle_search_year."""

    def test_matching_range_lists_books(self, mock_inputs, capsys):
        book_app.collection.add_book("Dune", "Frank Herbert", 1965)
        mock_inputs(["1960", "1970"])

        book_app.handle_search_year()

        assert "Dune by Frank Herbert (1965)" in capsys.readouterr().out

    def test_non_numeric_years_print_error(self, mock_inputs, capsys):
        mock_inputs(["abc", "2020"])

        book_app.handle_search_year()

        out = capsys.readouterr().out
        assert "Error: Start year and end year must be whole numbers." in out

    def test_end_before_start_prints_validation_error(self, mock_inputs, capsys):
        mock_inputs(["2020", "2010"])

        book_app.handle_search_year()

        assert "end_year cannot be earlier than start_year" in capsys.readouterr().out


class TestShowHelp:
    """Tests for show_help."""

    def test_prints_all_commands(self, capsys):
        book_app.show_help()

        out = capsys.readouterr().out
        for command in ["list", "add", "remove", "find", "find-year", "help"]:
            assert command in out


class TestMain:
    """Tests for main() and command dispatch."""

    def test_no_arguments_shows_help(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["book_app.py"])

        book_app.main()

        assert "Commands:" in capsys.readouterr().out

    def test_unknown_command_exits_with_status_1(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["book_app.py", "bogus"])

        with pytest.raises(SystemExit) as exc_info:
            book_app.main()

        assert exc_info.value.code == 1
        out = capsys.readouterr().out
        assert "Unknown command." in out
        assert "Commands:" in out

    def test_command_is_case_insensitive(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["book_app.py", "LIST"])

        book_app.main()

        assert "No books found." in capsys.readouterr().out

    @pytest.mark.parametrize("command", ["list", "add", "remove", "find", "find-year", "help"])
    def test_known_command_dispatches_to_registered_handler(
        self, monkeypatch, command
    ):
        called = []
        monkeypatch.setitem(book_app.COMMANDS, command, lambda: called.append(True))
        monkeypatch.setattr(sys, "argv", ["book_app.py", command])

        book_app.main()

        assert called == [True]
