from exceptions import ValidationError


def print_menu() -> None:
    """Print the main menu of book collection actions to standard output.

    Example:
        >>> print_menu()  # doctest: +SKIP
        📚 Book Collection App
        1. Add a book
        2. List books
        3. Mark book as read
        4. Remove a book
        5. Exit
    """
    print("\n📚 Book Collection App")
    print("1. Add a book")
    print("2. List books")
    print("3. Mark book as read")
    print("4. Remove a book")
    print("5. Exit")


def print_empty_choice_error() -> None:
    """Print a warning that the menu choice input was left empty."""
    print("Input cannot be empty. Please enter a number between 1 and 5.")


def print_invalid_choice_error() -> None:
    """Print a warning that the menu choice was not a valid option."""
    print("Invalid choice. Please enter a number between 1 and 5.")


def is_valid_choice(choice: str) -> bool:
    """Check whether ``choice`` is a digit string between 1 and 5.

    Args:
        choice (str): The raw menu selection to validate.

    Returns:
        bool: ``True`` if ``choice`` consists only of digits and represents
            a whole number from 1 to 5 (inclusive); ``False`` otherwise
            (including empty strings and non-digit input).

    Example:
        >>> is_valid_choice("3")
        True
        >>> is_valid_choice("7")
        False
    """
    return choice.isdigit() and 1 <= int(choice) <= 5


def get_user_choice() -> str:
    """Prompt the user for a menu choice until a valid one is entered.

    Repeatedly prompts on standard input, printing an error message via
    :func:`print_empty_choice_error` or :func:`print_invalid_choice_error`
    and re-prompting when the input is empty or not a whole number from 1
    to 5 (see :func:`is_valid_choice`). This function never raises; it
    only returns once valid input has been given.

    Returns:
        str: The validated menu choice, as the original digit string
            (e.g. ``"1"``).

    Example:
        >>> get_user_choice()  # doctest: +SKIP
        Choose an option (1-5): 2
        '2'
    """
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
    """Print a warning that the book title input was left empty."""
    print("Title cannot be empty. Please enter a book title.")


def print_invalid_year_warning() -> None:
    """Print a warning that the year input was invalid and was defaulted to 0."""
    print("Invalid year. Defaulting to 0.")


def parse_year(year_input: str) -> int:
    """Convert ``year_input`` to an int.

    Args:
        year_input (str): The raw publication year text to parse (e.g. from
            user input). Leading/trailing whitespace is not stripped by
            this function; callers should strip beforehand if needed.

    Returns:
        int: The parsed year, which may be negative or otherwise out of
            range; this function only checks that the string is a valid
            whole number, not that it's a sensible publication year.

    Raises:
        ValidationError: If ``year_input`` is not a valid integer.

    Example:
        >>> parse_year("1965")
        1965
        >>> parse_year("not a year")
        Traceback (most recent call last):
            ...
        exceptions.ValidationError: Invalid year: 'not a year' is not a whole number.
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
