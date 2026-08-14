import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from utils import get_book_details


def test_get_book_details_returns_valid_tuple(monkeypatch):
    inputs = iter(["1984", "George Orwell", "1949"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    title, author, year = get_book_details()
    assert title == "1984"
    assert author == "George Orwell"
    assert year == 1949


def test_get_book_details_reprompts_empty_title(monkeypatch):
    inputs = iter(["", "  ", "Dune", "Frank Herbert", "1965"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    title, author, year = get_book_details()
    assert title == "Dune"


def test_get_book_details_reprompts_empty_author(monkeypatch):
    inputs = iter(["1984", "", "  ", "George Orwell", "1949"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    title, author, year = get_book_details()
    assert author == "George Orwell"


def test_get_book_details_invalid_year_defaults_to_zero(monkeypatch, capsys):
    inputs = iter(["1984", "George Orwell", "not-a-year"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    title, author, year = get_book_details()
    assert year == 0
    captured = capsys.readouterr()
    assert "Invalid year" in captured.out
