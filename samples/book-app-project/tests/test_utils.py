import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from utils import get_book_details


@pytest.fixture
def mock_inputs(monkeypatch):
    """Factory fixture that queues canned responses for sequential input() calls.

    Usage:
        mock_inputs(["Title", "Author", "2020"])
    """

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


class TestGetBookDetailsValidInput:
    """Happy-path behavior for get_book_details."""

    def test_valid_input_returns_expected_tuple(self, mock_inputs):
        mock_inputs(["Dune", "Frank Herbert", "1965"])

        title, author, year = get_book_details()

        assert title == "Dune"
        assert author == "Frank Herbert"
        assert year == 1965

    def test_valid_input_strips_surrounding_whitespace(self, mock_inputs):
        mock_inputs(["  Dune  ", "  Frank Herbert  ", "  1965  "])

        title, author, year = get_book_details()

        assert title == "Dune"
        assert author == "Frank Herbert"
        assert year == 1965

    @pytest.mark.parametrize(
        "year_input,expected_year",
        [
            pytest.param("0", 0, id="zero-year"),
            pytest.param("-500", -500, id="negative-year-not-validated-here"),
            pytest.param("2024", 2024, id="ordinary-year"),
        ],
    )
    def test_valid_numeric_year_is_parsed_as_int(self, mock_inputs, year_input, expected_year):
        mock_inputs(["Dune", "Frank Herbert", year_input])

        _, _, year = get_book_details()

        assert year == expected_year
        assert isinstance(year, int)


class TestGetBookDetailsEmptyStrings:
    """Behavior around empty/blank title and author input."""

    def test_empty_title_reprompts_until_non_empty(self, mock_inputs, capsys):
        mock_inputs(["", "   ", "Dune", "Frank Herbert", "1965"])

        title, author, year = get_book_details()

        assert title == "Dune"
        assert author == "Frank Herbert"
        assert year == 1965
        # Two blank attempts should each trigger the empty-title error message.
        assert capsys.readouterr().out.count("Title cannot be empty.") == 2

    def test_empty_author_is_allowed(self, mock_inputs):
        mock_inputs(["Dune", "", "1965"])

        title, author, year = get_book_details()

        assert title == "Dune"
        assert author == ""
        assert year == 1965

    def test_whitespace_only_author_becomes_empty_string(self, mock_inputs):
        mock_inputs(["Dune", "   ", "1965"])

        _, author, _ = get_book_details()

        assert author == ""

    def test_empty_year_input_defaults_to_zero_with_warning(self, mock_inputs, capsys):
        mock_inputs(["Dune", "Frank Herbert", ""])

        _, _, year = get_book_details()

        assert year == 0
        assert "Invalid year. Defaulting to 0." in capsys.readouterr().out


class TestGetBookDetailsInvalidYearFormats:
    """Behavior when the publication year isn't a valid whole number."""

    @pytest.mark.parametrize(
        "year_input",
        [
            pytest.param("abc", id="alphabetic"),
            pytest.param("twenty-twenty", id="spelled-out"),
            pytest.param("19.65", id="decimal"),
            pytest.param("1965a", id="trailing-letter"),
            pytest.param("19 65", id="embedded-space"),
            pytest.param("MCMLXV", id="roman-numeral"),
            pytest.param("1e10", id="scientific-notation"),
            pytest.param("NaN", id="nan-literal"),
        ],
    )
    def test_invalid_year_defaults_to_zero(self, mock_inputs, year_input):
        mock_inputs(["Dune", "Frank Herbert", year_input])

        _, _, year = get_book_details()

        assert year == 0

    def test_full_width_digit_year_is_actually_valid_and_parsed(self, mock_inputs):
        # int() accepts Unicode full-width digits, so this is NOT an
        # invalid-year case despite looking unusual; documented here to
        # avoid a future false assumption that it should default to 0.
        mock_inputs(["Dune", "Frank Herbert", "１９６５"])

        _, _, year = get_book_details()

        assert year == 1965

    def test_invalid_year_prints_warning(self, mock_inputs, capsys):
        mock_inputs(["Dune", "Frank Herbert", "not-a-year"])

        get_book_details()

        assert "Invalid year. Defaulting to 0." in capsys.readouterr().out

    def test_invalid_year_does_not_raise(self, mock_inputs):
        mock_inputs(["Dune", "Frank Herbert", "abc"])

        # get_book_details must swallow the ValidationError from parse_year
        # internally and never propagate it to the caller.
        title, author, year = get_book_details()

        assert (title, author, year) == ("Dune", "Frank Herbert", 0)


class TestGetBookDetailsVeryLongTitles:
    """Behavior with unusually long title input."""

    def test_very_long_title_is_preserved(self, mock_inputs):
        long_title = "A" * 10_000
        mock_inputs([long_title, "Author", "2020"])

        title, _, _ = get_book_details()

        assert title == long_title
        assert len(title) == 10_000

    def test_very_long_title_with_surrounding_whitespace_is_stripped(self, mock_inputs):
        long_title = "B" * 5_000
        mock_inputs([f"  {long_title}  ", "Author", "2020"])

        title, _, _ = get_book_details()

        assert title == long_title


class TestGetBookDetailsSpecialCharactersInAuthor:
    """Behavior with special / unicode characters in the author field."""

    @pytest.mark.parametrize(
        "author_input",
        [
            pytest.param("J.R.R. Tolkien", id="periods"),
            pytest.param("O'Brien", id="apostrophe"),
            pytest.param("Jean-Paul Sartre", id="hyphen"),
            pytest.param("Gabriel García Márquez", id="accented-characters"),
            pytest.param("村上春樹", id="cjk-characters"),
            pytest.param("Author <script>alert(1)</script>", id="html-injection-like"),
            pytest.param("Author; DROP TABLE books;--", id="sql-injection-like"),
            pytest.param("😀 Emoji Author 🎉", id="emoji"),
            pytest.param("Müller & Søn", id="mixed-diacritics-and-ampersand"),
        ],
    )
    def test_special_character_author_is_preserved_as_is(self, mock_inputs, author_input):
        mock_inputs(["Some Title", author_input, "2020"])

        _, author, _ = get_book_details()

        assert author == author_input
