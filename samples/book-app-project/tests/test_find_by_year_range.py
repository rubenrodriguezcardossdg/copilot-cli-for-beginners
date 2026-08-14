"""Focused pytest suite for BookCollection.find_by_year_range.

Covers matching within range, boundary (inclusive) years, invalid inputs,
and no-match scenarios.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import books
from books import BookCollection
from exceptions import ValidationError


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
    """Provide a BookCollection pre-populated with books across various years."""
    collection.add_book("1984", "George Orwell", 1949)
    collection.add_book("Animal Farm", "George Orwell", 1945)
    collection.add_book("Dune", "Frank Herbert", 1965)
    collection.add_book("The Fellowship of the Ring", "J.R.R. Tolkien", 1954)
    return collection


class TestFindByYearRangeMatch:
    """Books whose year falls within the given range."""

    def test_range_returns_single_matching_book(self, populated_collection):
        result = populated_collection.find_by_year_range(1960, 1970)

        assert len(result) == 1
        assert result[0].title == "Dune"

    def test_range_returns_multiple_matching_books(self, populated_collection):
        result = populated_collection.find_by_year_range(1940, 1955)

        titles = {book.title for book in result}
        assert titles == {"1984", "Animal Farm", "The Fellowship of the Ring"}

    def test_range_covering_all_books_returns_all(self, populated_collection):
        result = populated_collection.find_by_year_range(1900, 2000)

        assert len(result) == 4


class TestFindByYearRangeBoundaries:
    """Range boundaries are inclusive."""

    def test_start_year_equal_to_book_year_is_included(self, populated_collection):
        result = populated_collection.find_by_year_range(1965, 1965)

        assert len(result) == 1
        assert result[0].title == "Dune"

    def test_end_year_equal_to_book_year_is_included(self, populated_collection):
        result = populated_collection.find_by_year_range(1949, 1949)

        assert len(result) == 1
        assert result[0].title == "1984"

    def test_start_year_equal_to_end_year_with_no_match(self, populated_collection):
        result = populated_collection.find_by_year_range(1999, 1999)

        assert result == []


class TestFindByYearRangeInvalidInput:
    """Invalid year inputs raise ValidationError."""

    def test_end_year_before_start_year_raises(self, populated_collection):
        with pytest.raises(ValidationError):
            populated_collection.find_by_year_range(1970, 1960)

    @pytest.mark.parametrize("start_year,end_year", [(-1, 2000), (1900, -1)])
    def test_negative_year_raises(self, populated_collection, start_year, end_year):
        with pytest.raises(ValidationError):
            populated_collection.find_by_year_range(start_year, end_year)

    @pytest.mark.parametrize("start_year,end_year", [(True, 2000), (1900, False)])
    def test_bool_year_raises(self, populated_collection, start_year, end_year):
        with pytest.raises(ValidationError):
            populated_collection.find_by_year_range(start_year, end_year)

    @pytest.mark.parametrize("start_year,end_year", [("1960", 2000), (1900, "2000")])
    def test_non_integer_year_raises(self, populated_collection, start_year, end_year):
        with pytest.raises(ValidationError):
            populated_collection.find_by_year_range(start_year, end_year)


class TestFindByYearRangeNotFound:
    """Ranges that match no books."""

    def test_range_with_no_matches_returns_empty_list(self, populated_collection):
        result = populated_collection.find_by_year_range(2000, 2020)

        assert result == []

    def test_range_on_empty_collection_returns_empty_list(self, collection):
        result = collection.find_by_year_range(1900, 2000)

        assert result == []
