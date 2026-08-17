import sys
from typing import List

from books import Book, BookCollection
from exceptions import StorageError, ValidationError


# Global collection instance
collection = BookCollection()


def show_books(books: List[Book]) -> None:
    """Display books in a user-friendly format."""
    if not books:
        print("No books found.")
        return

    print("\nYour Book Collection:\n")

    for index, book in enumerate(books, start=1):
        status = "✓" if book.read else " "
        print(f"{index}. [{status}] {book.title} by {book.author} ({book.year})")

    print()


def handle_list() -> None:
    books = collection.list_books()
    show_books(books)


def handle_add() -> None:
    print("\nAdd a New Book\n")

    title = input("Title: ").strip()
    author = input("Author: ").strip()
    year_str = input("Year: ").strip()

    if not year_str:
        print("\nError: Year cannot be empty.\n")
        return

    try:
        year = int(year_str)
    except ValueError:
        print("\nError: Year must be a whole number.\n")
        return

    try:
        collection.add_book(title, author, year)
        print("\nBook added successfully.\n")
    except ValidationError as e:
        print(f"\nError: {e}\n")
    except StorageError as e:
        print(f"\nError: Could not save the book: {e}\n")


def handle_remove() -> None:
    print("\nRemove a Book\n")

    title = input("Enter the title of the book to remove: ").strip()

    try:
        removed = collection.remove_book(title)
    except ValidationError as e:
        print(f"\nError: {e}\n")
        return
    except StorageError as e:
        print(f"\nError: Could not save changes: {e}\n")
        return

    if removed:
        print("\nBook removed successfully.\n")
    else:
        print("\nNo book found with that title.\n")


def handle_find() -> None:
    print("\nFind Books by Author\n")

    author = input("Author name: ").strip()
    books = collection.find_by_author(author)

    show_books(books)


def handle_search_year() -> None:
    print("\nFind Books by Year Range\n")

    start_str = input("Start year: ").strip()
    end_str = input("End year: ").strip()

    try:
        start_year = int(start_str)
        end_year = int(end_str)
    except ValueError:
        print("\nError: Start year and end year must be whole numbers.\n")
        return

    try:
        books = collection.find_by_year_range(start_year, end_year)
    except ValidationError as e:
        print(f"\nError: {e}\n")
        return

    show_books(books)


def show_help() -> None:
    print("""
Book Collection Helper

Commands:
  list      - Show all books
  add       - Add a new book
  remove    - Remove a book by title
  find      - Find books by author
  find-year - Find books by year range
  help      - Show this help message
""")


COMMANDS = {
    "list": handle_list,
    "add": handle_add,
    "remove": handle_remove,
    "find": handle_find,
    "find-year": handle_search_year,
    "help": show_help,
}


def main() -> None:
    if len(sys.argv) < 2:
        show_help()
        return

    command = sys.argv[1].lower()
    handler = COMMANDS.get(command)

    if handler is None:
        print("Unknown command.\n")
        show_help()
        sys.exit(1)

    handler()


if __name__ == "__main__":
    main()
