def print_menu():
    print("\n📚 Book Collection App")
    print("1. Add a book")
    print("2. List books")
    print("3. Mark book as read")
    print("4. Remove a book")
    print("5. Exit")


def get_user_choice() -> str:
    while True:
        choice = input("Choose an option (1-5): ").strip()

        if not choice:
            print("Input cannot be empty. Please enter a number between 1 and 5.")
            continue

        if not choice.isdigit() or not (1 <= int(choice) <= 5):
            print("Invalid choice. Please enter a number between 1 and 5.")
            continue

        return choice


def get_book_details():
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
        print("Title cannot be empty. Please enter a book title.")
        title = input("Enter book title: ").strip()

    author = input("Enter author: ").strip()

    year_input = input("Enter publication year: ").strip()
    try:
        year = int(year_input)
    except ValueError:
        print("Invalid year. Defaulting to 0.")
        year = 0

    return title, author, year


def print_books(books):
    if not books:
        print("No books in your collection.")
        return

    print("\nYour Books:")
    for index, book in enumerate(books, start=1):
        status = "✅ Read" if book.read else "📖 Unread"
        print(f"{index}. {book.title} by {book.author} ({book.year}) - {status}")
