"""Focused pytest suite for BookCollection.find_by_author.

Covers four required scenarios: full author name match, partial author
name match, case-insensitive matching, and author name not found.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import books
from books import BookCollection


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
    """Provide a BookCollection pre-populated with a few known books/authors."""
    collection.add_book("1984", "George Orwell", 1949)
    collection.add_book("Animal Farm", "George Orwell", 1945)
    collection.add_book("Dune", "Frank Herbert", 1965)
    collection.add_book("The Fellowship of the Ring", "J.R.R. Tolkien", 1954)
    return collection


class TestFindByAuthorFullMatch:
    """Full (exact, whole) author name match."""

    def test_full_author_name_returns_matching_book(self, populated_collection):
        result = populated_collection.find_by_author("Frank Herbert")

        assert len(result) == 1
        assert result[0].title == "Dune"
        assert result[0].author == "Frank Herbert"

    def test_full_author_name_returns_all_books_by_that_author(self, populated_collection):
        result = populated_collection.find_by_author("George Orwell")

        titles = {book.title for book in result}
        assert len(result) == 2
        assert titles == {"1984", "Animal Farm"}


class TestFindByAuthorPartialMatch:
    """Partial (substring) author name match."""

    @pytest.mark.parametrize("query", ["Herbert", "Frank", "rank Herb"])
    def test_partial_author_name_returns_matching_book(self, populated_collection, query):
        result = populated_collection.find_by_author(query)

        assert len(result) == 1
        assert result[0].title == "Dune"

    def test_partial_author_name_matches_last_name_only(self, populated_collection):
        result = populated_collection.find_by_author("Tolkien")

        assert len(result) == 1
        assert result[0].title == "The Fellowship of the Ring"

    def test_partial_author_name_matches_multiple_books(self, populated_collection):
        result = populated_collection.find_by_author("Orwell")

        assert len(result) == 2


class TestFindByAuthorCaseInsensitive:
    """Case-insensitive matching, for both full and partial names."""

    @pytest.mark.parametrize("query", ["george orwell", "GEORGE ORWELL", "George ORWELL"])
    def test_case_insensitive_full_name_match(self, populated_collection, query):
        result = populated_collection.find_by_author(query)

        assert len(result) == 2

    @pytest.mark.parametrize("query", ["herbert", "HERBERT", "HeRbErT"])
    def test_case_insensitive_partial_name_match(self, populated_collection, query):
        result = populated_collection.find_by_author(query)

        assert len(result) == 1
        assert result[0].title == "Dune"


class TestFindByAuthorNotFound:
    """Author name(s) that do not exist in the collection."""

    def test_unknown_author_returns_empty_list(self, populated_collection):
        result = populated_collection.find_by_author("Nobody Real")

        assert result == []

    def test_author_not_found_on_empty_collection(self, collection):
        result = collection.find_by_author("George Orwell")

        assert result == []

    @pytest.mark.parametrize("query", ["", "   "])
    def test_blank_or_empty_query_returns_empty_list(self, populated_collection, query):
        result = populated_collection.find_by_author(query)

        assert result == []
