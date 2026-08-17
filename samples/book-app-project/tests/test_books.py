import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime

import pytest
import books
from books import Book, BookCollection


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


@pytest.fixture
def populated_collection(collection):
    """Provide a BookCollection pre-populated with three books."""
    collection.add_book("1984", "George Orwell", 1949)
    collection.add_book("Animal Farm", "George Orwell", 1945)
    collection.add_book("Dune", "Frank Herbert", 1965)
    return collection


class TestAddBook:
    """Tests for BookCollection.add_book."""

    def test_add_book_happy_path(self, collection):
        book = collection.add_book("1984", "George Orwell", 1949)

        assert isinstance(book, Book)
        assert len(collection.books) == 1
        assert book.title == "1984"
        assert book.author == "George Orwell"
        assert book.year == 1949
        assert book.read is False

    def test_add_book_strips_whitespace_from_title_and_author(self, collection):
        book = collection.add_book("  1984  ", "  George Orwell  ", 1949)

        assert book.title == "1984"
        assert book.author == "George Orwell"

    def test_add_book_zero_year_is_allowed(self, collection):
        book = collection.add_book("Unknown Year Book", "Some Author", 0)

        assert book.year == 0

    def test_add_book_current_year_is_allowed(self, collection):
        current_year = datetime.now().year
        book = collection.add_book("Current Year Book", "Some Author", current_year)

        assert book.year == current_year

    def test_add_book_future_year_raises_validation_error(self, collection):
        future_year = datetime.now().year + 1

        with pytest.raises(ValueError):
            collection.add_book("Future Book", "Some Author", future_year)
        assert len(collection.books) == 0

    def test_add_book_returns_book_instance(self, collection):
        book = collection.add_book("1984", "George Orwell", 1949)

        assert isinstance(book, Book)

    @pytest.mark.parametrize(
        "title,author,year",
        [
            pytest.param("", "George Orwell", 1949, id="empty-title"),
            pytest.param("   ", "George Orwell", 1949, id="whitespace-title"),
            pytest.param("1984", "", 1949, id="empty-author"),
            pytest.param("1984", "   ", 1949, id="whitespace-author"),
            pytest.param("1984", "George Orwell", -1, id="negative-year"),
            pytest.param("1984", "George Orwell", "1949", id="non-int-year"),
            pytest.param("1984", "George Orwell", True, id="bool-year"),
        ],
    )
    def test_add_book_invalid_input_raises_validation_error(self, collection, title, author, year):
        with pytest.raises(ValueError):
            collection.add_book(title, author, year)
        assert len(collection.books) == 0

    def test_add_duplicate_book_raises_validation_error(self, collection):
        collection.add_book("1984", "George Orwell", 1949)

        with pytest.raises(ValueError):
            collection.add_book("1984", "George Orwell", 1949)
        assert len(collection.books) == 1

    def test_add_duplicate_book_case_insensitive_raises_validation_error(self, collection):
        collection.add_book("1984", "George Orwell", 1949)

        with pytest.raises(ValueError):
            collection.add_book("1984", "GEORGE ORWELL", 1949)
        assert len(collection.books) == 1

    def test_add_book_persists_to_disk(self, tmp_path, monkeypatch):
        data_file = tmp_path / "data.json"
        data_file.write_text("[]")
        monkeypatch.setattr(books, "DATA_FILE", str(data_file))
        collection = BookCollection()
        collection.add_book("1984", "George Orwell", 1949)

        reloaded = BookCollection()

        assert len(reloaded.books) == 1
        assert reloaded.books[0].title == "1984"


class TestRemoveBook:
    """Tests for BookCollection.remove_book."""

    def test_remove_existing_book(self, populated_collection):
        result = populated_collection.remove_book("Dune")

        assert result is True
        assert populated_collection.find_book_by_title("Dune") is None
        assert len(populated_collection.books) == 2

    @pytest.mark.parametrize(
        "title",
        ["dune", "DUNE", "DuNe", "  dune  "],
        ids=["lowercase", "uppercase", "mixed-case", "case-and-whitespace"],
    )
    def test_remove_book_case_insensitive_matching(self, populated_collection, title):
        result = populated_collection.remove_book(title)

        assert result is True
        assert populated_collection.find_book_by_title("Dune") is None
        assert len(populated_collection.books) == 2

    def test_remove_nonexistent_book_returns_false(self, populated_collection):
        result = populated_collection.remove_book("Nonexistent Book")

        assert result is False
        assert len(populated_collection.books) == 3

    @pytest.mark.parametrize("title", ["", "   "], ids=["empty", "whitespace"])
    def test_remove_book_empty_title_raises_validation_error(self, collection, title):
        with pytest.raises(ValueError):
            collection.remove_book(title)

    def test_remove_book_on_empty_collection_returns_false(self, collection):
        assert collection.remove_book("Anything") is False

    def test_remove_book_persists_change(self, tmp_path, monkeypatch):
        data_file = tmp_path / "data.json"
        data_file.write_text("[]")
        monkeypatch.setattr(books, "DATA_FILE", str(data_file))
        collection = BookCollection()
        collection.add_book("1984", "George Orwell", 1949)
        collection.remove_book("1984")

        reloaded = BookCollection()

        assert reloaded.books == []


class TestFindBookByTitle:
    """Tests for BookCollection.find_book_by_title."""

    def test_find_existing_book(self, populated_collection):
        book = populated_collection.find_book_by_title("1984")

        assert book is not None
        assert book.title == "1984"

    @pytest.mark.parametrize(
        "search_title",
        ["1984", "  1984  ", "1984".upper(), "1984".lower()],
        ids=["exact", "whitespace-padded", "uppercase", "lowercase"],
    )
    def test_find_book_by_title_ignores_case_and_whitespace(self, populated_collection, search_title):
        assert populated_collection.find_book_by_title(search_title) is not None

    @pytest.mark.parametrize("search_title", ["", "   "], ids=["empty", "whitespace"])
    def test_find_book_by_title_empty_or_blank_returns_none(self, populated_collection, search_title):
        assert populated_collection.find_book_by_title(search_title) is None

    def test_find_book_by_title_not_found_returns_none(self, populated_collection):
        assert populated_collection.find_book_by_title("Nonexistent") is None

    def test_find_book_by_title_on_empty_collection_returns_none(self, collection):
        assert collection.find_book_by_title("1984") is None


class TestFindByAuthor:
    """Tests for BookCollection.find_by_author."""

    def test_find_by_author_single_match(self, populated_collection):
        result = populated_collection.find_by_author("Frank Herbert")

        assert len(result) == 1
        assert result[0].title == "Dune"

    def test_find_by_author_returns_multiple_matches(self, populated_collection):
        result = populated_collection.find_by_author("George Orwell")

        assert len(result) == 2
        assert {b.title for b in result} == {"1984", "Animal Farm"}

    def test_find_by_author_case_insensitive(self, populated_collection):
        result = populated_collection.find_by_author("GEORGE ORWELL")

        assert len(result) == 2

    @pytest.mark.parametrize("author", ["", "   "], ids=["empty", "whitespace"])
    def test_find_by_author_empty_or_blank_returns_empty_list(self, populated_collection, author):
        assert populated_collection.find_by_author(author) == []

    def test_find_by_author_no_match_returns_empty_list(self, populated_collection):
        assert populated_collection.find_by_author("Nobody") == []

    def test_find_by_author_partial_match(self, collection):
        collection.add_book(
            "The Fellowship of the Ring", "J.R.R. Tolkien", 1954
        )

        result = collection.find_by_author("Tolkien")

        assert len(result) == 1
        assert result[0].title == "The Fellowship of the Ring"

    def test_find_by_author_partial_match_is_case_insensitive(self, collection):
        collection.add_book(
            "The Fellowship of the Ring", "J.R.R. Tolkien", 1954
        )

        result = collection.find_by_author("tolkien")

        assert len(result) == 1

    def test_find_by_author_on_empty_collection_returns_empty_list(self, collection):
        assert collection.find_by_author("George Orwell") == []

    def test_find_by_author_ignores_extra_internal_whitespace_in_query(self, collection):
        collection.add_book("Dune", "Frank Herbert", 1965)

        result = collection.find_by_author("Frank  Herbert")

        assert len(result) == 1
        assert result[0].title == "Dune"

    def test_find_by_author_matches_when_stored_author_has_extra_whitespace(self, collection):
        collection.add_book("Dune", "Frank  Herbert", 1965)

        result = collection.find_by_author("Frank Herbert")

        assert len(result) == 1
        assert result[0].title == "Dune"

    def test_find_by_author_with_hyphenated_name(self, collection):
        collection.add_book("Nausea", "Jean-Paul Sartre", 1938)

        result = collection.find_by_author("Jean-Paul Sartre")

        assert len(result) == 1
        assert result[0].title == "Nausea"

    def test_find_by_author_hyphenated_name_is_case_insensitive(self, collection):
        collection.add_book("Nausea", "Jean-Paul Sartre", 1938)

        result = collection.find_by_author("jean-paul sartre")

        assert len(result) == 1

    def test_find_by_author_hyphenated_name_requires_exact_hyphenation(self, collection):
        collection.add_book("Nausea", "Jean-Paul Sartre", 1938)

        # A space instead of a hyphen is not a substring of the hyphenated
        # author string, so it still does not match.
        result = collection.find_by_author("Jean Paul Sartre")

        assert result == []

    def test_find_by_author_with_multiple_first_names(self, collection):
        collection.add_book(
            "One Hundred Years of Solitude", "Gabriel Jose Garcia Marquez", 1967
        )

        result = collection.find_by_author("Gabriel Jose Garcia Marquez")

        assert len(result) == 1
        assert result[0].title == "One Hundred Years of Solitude"

    def test_find_by_author_partial_of_multiple_first_names_does_not_match(self, collection):
        collection.add_book(
            "One Hundred Years of Solitude", "Gabriel Jose Garcia Marquez", 1967
        )

        # find_by_author matches on substrings, but "Gabriel Garcia Marquez"
        # is not a contiguous substring of "Gabriel Jose Garcia Marquez"
        # (the middle name "Jose" breaks the sequence), so it should not match.
        result = collection.find_by_author("Gabriel Garcia Marquez")

        assert result == []

    def test_find_by_author_empty_string_returns_empty_list(self, populated_collection):
        assert populated_collection.find_by_author("") == []

    def test_find_by_author_empty_string_on_empty_collection_returns_empty_list(self, collection):
        assert collection.find_by_author("") == []

    @pytest.mark.parametrize(
        "author_name",
        [
            pytest.param("Gabriel García Márquez", id="a-and-i-accents"),
            pytest.param("José Saramago", id="e-acute"),
            pytest.param("Stanisław Lem", id="l-with-stroke"),
            pytest.param("Naguib Mahfouz", id="unaccented-baseline"),
            pytest.param("Björk Guðmundsdóttir", id="o-umlaut-and-eth"),
        ],
    )
    def test_find_by_author_with_accented_characters(self, collection, author_name):
        collection.add_book("Some Title", author_name, 2000)

        result = collection.find_by_author(author_name)

        assert len(result) == 1
        assert result[0].author == author_name

    def test_find_by_author_accented_name_is_case_insensitive(self, collection):
        collection.add_book("Blindness", "José Saramago", 1995)

        result = collection.find_by_author("JOSÉ SARAMAGO")

        assert len(result) == 1

    def test_find_by_author_accented_and_unaccented_versions_do_not_match_each_other(self, collection):
        collection.add_book("Blindness", "José Saramago", 1995)

        # "Jose" (no accent) is a different string from "José"; matching
        # is exact on characters, not accent-insensitive/normalized, so a
        # substring search still won't find it.
        result = collection.find_by_author("Jose Saramago")

        assert result == []


class TestMarkAsRead:
    """Tests for BookCollection.mark_as_read."""

    def test_mark_existing_book_as_read(self, populated_collection):
        result = populated_collection.mark_as_read("Dune")

        assert result is True
        assert populated_collection.find_book_by_title("Dune").read is True

    def test_mark_as_read_only_affects_matching_book(self, populated_collection):
        populated_collection.mark_as_read("Dune")

        assert populated_collection.find_book_by_title("1984").read is False
        assert populated_collection.find_book_by_title("Animal Farm").read is False

    def test_mark_nonexistent_book_returns_false(self, populated_collection):
        result = populated_collection.mark_as_read("Nonexistent Book")

        assert result is False

    @pytest.mark.parametrize("title", ["", "   "], ids=["empty", "whitespace"])
    def test_mark_as_read_empty_title_raises_validation_error(self, collection, title):
        with pytest.raises(ValueError):
            collection.mark_as_read(title)

    def test_mark_as_read_on_empty_collection_returns_false(self, collection):
        assert collection.mark_as_read("Anything") is False

    def test_mark_as_read_persists_change(self, tmp_path, monkeypatch):
        data_file = tmp_path / "data.json"
        data_file.write_text("[]")
        monkeypatch.setattr(books, "DATA_FILE", str(data_file))
        collection = BookCollection()
        collection.add_book("1984", "George Orwell", 1949)
        collection.mark_as_read("1984")

        reloaded = BookCollection()

        assert reloaded.books[0].read is True


class TestListBooks:
    """Tests for BookCollection.list_books."""

    def test_list_books_empty_initially(self, collection):
        assert collection.list_books() == []

    def test_list_books_returns_all_added_books_in_order(self, populated_collection):
        result = populated_collection.list_books()

        assert [b.title for b in result] == ["1984", "Animal Farm", "Dune"]


class TestFindByYearRange:
    """Tests for BookCollection.find_by_year_range."""

    def test_find_by_year_range_single_match(self, populated_collection):
        result = populated_collection.find_by_year_range(1960, 1970)

        assert len(result) == 1
        assert result[0].title == "Dune"

    def test_find_by_year_range_multiple_matches(self, populated_collection):
        result = populated_collection.find_by_year_range(1940, 1955)

        assert {b.title for b in result} == {"1984", "Animal Farm"}

    def test_find_by_year_range_covering_all_books_returns_all(self, populated_collection):
        result = populated_collection.find_by_year_range(1900, 2000)

        assert len(result) == 3

    def test_find_by_year_range_start_equal_to_end_matches_exact_year(self, populated_collection):
        result = populated_collection.find_by_year_range(1965, 1965)

        assert len(result) == 1
        assert result[0].title == "Dune"

    def test_find_by_year_range_boundaries_are_inclusive(self, populated_collection):
        result = populated_collection.find_by_year_range(1949, 1965)

        assert {b.title for b in result} == {"1984", "Dune"}

    def test_find_by_year_range_no_matches_returns_empty_list(self, populated_collection):
        result = populated_collection.find_by_year_range(2000, 2020)

        assert result == []

    def test_find_by_year_range_on_empty_collection_returns_empty_list(self, collection):
        assert collection.find_by_year_range(1900, 2000) == []

    def test_find_by_year_range_reversed_range_raises_validation_error(self, populated_collection):
        with pytest.raises(ValueError):
            populated_collection.find_by_year_range(1970, 1960)

    @pytest.mark.parametrize(
        "start_year,end_year",
        [
            pytest.param(-1, 2000, id="negative-start-year"),
            pytest.param(1900, -1, id="negative-end-year"),
            pytest.param(True, 2000, id="bool-start-year"),
            pytest.param(1900, False, id="bool-end-year"),
            pytest.param("1960", 2000, id="non-int-start-year"),
            pytest.param(1900, "2000", id="non-int-end-year"),
        ],
    )
    def test_find_by_year_range_invalid_input_raises_validation_error(
        self, populated_collection, start_year, end_year
    ):
        with pytest.raises(ValueError):
            populated_collection.find_by_year_range(start_year, end_year)


class TestEmptyAndCorruptedDataEdgeCases:
    """Edge cases around empty, missing, and corrupted data files."""

    def test_new_collection_starts_empty(self, collection):
        assert collection.books == []
        assert collection.list_books() == []

    def test_load_books_empty_array_starts_empty(self, tmp_path, monkeypatch):
        data_file = tmp_path / "data.json"
        data_file.write_text("[]")
        monkeypatch.setattr(books, "DATA_FILE", str(data_file))

        collection = BookCollection()

        assert collection.books == []

    def test_load_books_missing_file_starts_empty(self, tmp_path, monkeypatch):
        missing_file = tmp_path / "does_not_exist.json"
        monkeypatch.setattr(books, "DATA_FILE", str(missing_file))

        collection = BookCollection()

        assert collection.books == []

    def test_load_books_corrupted_json_starts_empty(self, tmp_path, monkeypatch, capsys):
        corrupted_file = tmp_path / "data.json"
        corrupted_file.write_text("{not valid json")
        monkeypatch.setattr(books, "DATA_FILE", str(corrupted_file))

        collection = BookCollection()

        assert collection.books == []
        assert "corrupted" in capsys.readouterr().out

    def test_load_books_corrupted_json_creates_backup(self, tmp_path, monkeypatch, capsys):
        corrupted_file = tmp_path / "data.json"
        corrupted_content = "{not valid json"
        corrupted_file.write_text(corrupted_content)
        monkeypatch.setattr(books, "DATA_FILE", str(corrupted_file))

        BookCollection()
        output = capsys.readouterr().out

        assert "A copy has been saved to" in output
        backups = list(tmp_path.glob("data.json.corrupted.*.bak"))
        assert len(backups) == 1
        assert backups[0].read_text() == corrupted_content
        # Original (corrupted) file is left untouched.
        assert corrupted_file.read_text() == corrupted_content

    def test_load_books_non_list_json_starts_empty(self, tmp_path, monkeypatch, capsys):
        bad_format_file = tmp_path / "data.json"
        bad_format_file.write_text('{"title": "not a list"}')
        monkeypatch.setattr(books, "DATA_FILE", str(bad_format_file))

        collection = BookCollection()

        assert collection.books == []
        assert "unexpected format" in capsys.readouterr().out

    def test_load_books_non_list_json_creates_backup(self, tmp_path, monkeypatch, capsys):
        bad_format_file = tmp_path / "data.json"
        bad_format_content = '{"title": "not a list"}'
        bad_format_file.write_text(bad_format_content)
        monkeypatch.setattr(books, "DATA_FILE", str(bad_format_file))

        BookCollection()
        output = capsys.readouterr().out

        assert "A copy has been saved to" in output
        backups = list(tmp_path.glob("data.json.corrupted.*.bak"))
        assert len(backups) == 1
        assert backups[0].read_text() == bad_format_content

    def test_load_books_skips_malformed_entries(self, tmp_path, monkeypatch, capsys):
        data_file = tmp_path / "data.json"
        data_file.write_text(
            '[{"title": "1984", "author": "George Orwell", "year": 1949}, '
            '{"title": "Missing Fields Only"}]'
        )
        monkeypatch.setattr(books, "DATA_FILE", str(data_file))

        collection = BookCollection()

        assert len(collection.books) == 1
        assert collection.books[0].title == "1984"
        assert "malformed" in capsys.readouterr().out

    def test_find_operations_on_empty_collection_dont_raise(self, collection):
        assert collection.find_book_by_title("Anything") is None
        assert collection.find_by_author("Anyone") == []
        assert collection.list_books() == []
