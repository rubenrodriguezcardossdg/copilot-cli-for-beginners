from exceptions import ValidationError


def print_menu() -> None:
    print("\n📚 Book Collection App")
    print("1. Add a book")
    print("2. List books")
    print("3. Mark book as read")
    print("4. Remove a book")
    print("5. Exit")


def print_empty_choice_error() -> None:
    print("Input cannot be empty. Please enter a number between 1 and 5.")


def print_invalid_choice_error() -> None:
    print("Invalid choice. Please enter a number between 1 and 5.")


def is_valid_choice(choice: str) -> bool:
    """Check whether ``choice`` is a digit string between 1 and 5."""
    return choice.isdigit() and 1 <= int(choice) <= 5


def get_user_choice() -> str:
    while True:
        choice = input("Choose an option (1-5): ").strip()

        if not choice:
            print_empty_choice_error()
            continue

        if not is_valid_choice(choice):
            print_invalid_choice_error()
            continue

        return choice


def print_empty_title_error() -> None:
    print("Title cannot be empty. Please enter a book title.")


def print_invalid_year_warning() -> None:
    print("Invalid year. Defaulting to 0.")


def parse_year(year_input: str) -> int:
    """Convert ``year_input`` to an int.

    Raises:
        ValidationError: If ``year_input`` is not a valid integer.
    """
    try:
        return int(year_input)
    except ValueError as e:
        raise ValidationError(f"Invalid year: {year_input!r} is not a whole number.") from e


def get_book_details() -> tuple[str, str, int]:
    """Prompt the user for details of a new book via the terminal.

    Takes no parameters; all values are collected interactively from
    standard input:
        - Title: re-prompted until a non-empty value is entered.
        - Author: entered as-is, no emptiness validation is performed.
        - Publication year: converted to ``int``. If the input is not a
          valid integer, a warning is printed and the year defaults to 0.

    Returns:
        tuple[str, str, int]: A ``(title, author, year)`` tuple where
    ``title`` is guaranteed non-empty, ``author`` is the stripped raw
    input (may be empty), and ``year`` is the publication year (or 0
    if invalid input was given).
    """
    title = input("Enter book title: ").strip()
    while not title:
        print_empty_title_error()
        title = input("Enter book title: ").strip()

    author = input("Enter author: ").strip()

    year_input = input("Enter publication year: ").strip()
    try:
        year = parse_year(year_input)
    except ValidationError:
        print_invalid_year_warning()
        year = 0

    return title, author, year
