import os
import sqlite3
import tabulate


def input_non_empty_string(prompt):
    """Requests input and ensures it is not empty"""
    while True:
        s = input(prompt)
        if len(s) > 0:
            return s
        print("Expected a value, please try again.")


def input_integer(prompt):
    """Requests an integer input from the user, repeating the prompt if there is an error."""
    while True:
        try:
            value = int(input(prompt))
            return value
        except ValueError as error:
            print("Expected an integer as input, please try again.")
            continue


def input_integer_or_none(prompt):
    """Requests an integer input from the user, allowing an empty string to mean no input given"""
    while True:
        try:
            value = input(prompt)
            if len(value) == 0:
                return None
            return int(value)
        except ValueError as error:
            print("Expected an integer as input, please try again.")
            continue


class Book(object):
    """Represents the data held about a book."""

    def __init__(self, id, title, author, quantity):
        self.id = id
        self.title = title
        self.author = author
        self.quantity = quantity


db = None


def initialise_database():
    """Checks whether the database file exists and sets it up for the program."""

    database_filename = "ebookstore.db"
    database_exists = os.path.exists(database_filename)

    db = sqlite3.connect(database_filename)

    # Create the file if it does not already exist.
    if not database_exists:

        # Create the books table.
        cursor = db.cursor()
        cursor.execute("""CREATE TABLE books (
id INTEGER NOT NULL,
Title TEXT,
Author TEXT,
Qty INTEGER DEFAULT 0,
PRIMARY KEY(id AUTOINCREMENT))""")
        db.commit()

        # Add initial data to the books table.
        initial_data = [
            (3001, "A Tale of Two Cities", "Charles Dickens", 30),
            (3002, "Harry Potter and the Philosopher's Stone", "J. K. Rowling", 40),
            (3003, "The Lion, the Witch, and the Warderobe", "C. S. Lewis", 25),
            (3004, "The Lord of the Rings", "J. R. R. Tolkien", 37),
            (3005, "Alice in Wonderland", "Lewis Carroll", 12)
        ]

        cursor.executemany("INSERT INTO books VALUES (?, ?, ?, ?)", initial_data)

        db.commit()

    return db

def find_matching_books(query):
    """Search for books matching the given query and return a list of matches."""

    cursor = db.cursor()
    cursor.execute("""SELECT * FROM books
WHERE Title LIKE ?
OR Author LIKE ?""", (query, query))

    books = []
    # Get all the matching records from the database
    rows = cursor.fetchall()

    for row in rows:
        book = Book(row[0], row[1], row[2], row[3])
        books.append(book)

    cursor.close()

    return books


def add_books():
    """Allows the user to add new books to the database."""
    print("-- Add new books --")
    print()

    # Ask for the details about the new books.
    while True:
        print("Please enter the book details:")
        title = input_non_empty_string("Title: ")
        author = input_non_empty_string("Author: ")
        quantity = input_integer("Number in stock: ")

        # Insert the new record into the database.
        cursor = db.cursor()
        cursor.execute("""INSERT INTO books (Title, Author, Qty)
VALUES (?, ?, ?)""", (title, author, quantity))
        db.commit()

        print("Saved.")
        print()

        choice = input("Add another? Y/N ").lower()
        if choice != "y":
            return


def query_for_books():
    """
    Asks the user to enter a query and then finds matching books in the database.
    If there are no matches, they are prompted to try again.
    """
    while True:
        query = input("Query (title or author): ")

        # Add wildcards so that the user does not have to enter exact
        # queries.
        query = f"%{query}%"

        # Get all the matching records from the database
        matches = find_matching_books(query)

        if len(matches) > 0:
            return matches

        # If there are no matches, offer to search again
        choice = input("No matches, try again? Y/N ").lower()
        if choice != "y":
            # Return an empty list if they don't want to search again.
            return []


def select_book_from_list(books):
    """
    Display a list of books to the user and ask them to select one.
    Checks if their selection is in range, and prompts to try again if it is not.
    """

    # Display the books to the user
    table_rows = [["#", "Title", "Author", "Stock Level"]]
    for index, book in enumerate(books):
        table_rows.append([index + 1, book.title, book.author, book.quantity])

    print(tabulate.tabulate(table_rows, headers="firstrow"))
    print()

    while True:
        index = input_integer("Enter the number of the book to update: ")
        index -= 1
        if index < 0 or index >= len(books):
            print(f"'{index + 1}' is not a valid choice, out of range.")
        else:
            return books[index]


def update_book():
    """Allows the user to search for and update book information."""
    print("-- Update --")
    print("Search for the book to be updated")

    matches = query_for_books()
    book = select_book_from_list(matches)

    # Ask for the updated details.
    new_title = input("Enter the new title, or blank to skip: ")
    new_author = input("Enter the new author, or blank to skip: ")
    new_quantity = input_integer_or_none("Enter the new stock level, or blank to skip: ")

    # Create a new book with either the new details, or existing details if no
    # new ones were provided.
    new_book = Book(book.id,
        new_title if len(new_title) > 0 else book.title,
        new_author if len(new_author) > 0 else book.author,
        new_quantity if new_quantity is not None else book.quantity)
    
    # Update the book in the database
    cursor = db.cursor()
    cursor.execute("""UPDATE books
SET Title = ?, Author = ?, Qty = ?
WHERE id = ?""", (new_book.title, new_book.author, new_book.quantity, new_book.id))
    db.commit()

    print("Updated.")
    print()


def delete_book():
    """Allows the user to search for and delete book information."""
    print("-- Delete --")
    print("Search for the book to be deleted")

    matches = query_for_books()
    book = select_book_from_list(matches)
    
    # Update the book in the database
    cursor = db.cursor()
    cursor.execute("""DELETE FROM books
WHERE id = ?""", (book.id, ))
    db.commit()

    print("Deleted.")
    print()


def search_books():
    """Allows the user to search for book information."""
    print("-- Search --")
    query = input("Query (title or author): ")
    print()

    # Add wildcards so that the user does not have to enter exact
    # queries.
    query = f"%{query}%"

    # Get all the matching records from the database
    matches = find_matching_books(query)

    print(f"{len(matches)} result(s)")
    print()
    # If there are any matches, display them to the user
    if len(matches) > 0:
        # Generate a readable table to display the books.
        table_rows = [["Title", "Author", "Stock Level"]]
        for book in matches:
            table_rows.append([book.title, book.author, book.quantity])

        print(tabulate.tabulate(table_rows, headers="firstrow"))
        print()


def main_menu():
    """Displays the main menu to the user."""
    while True:
        print("Please choose an option:")
        print("1. Enter book")
        print("2. Update book")
        print("3. Delete book")
        print("4. Search books")
        print("0. Exit")

        choice = input("> ").lower()

        if choice == "1":
            add_books()
        elif choice == "2":
            update_book()
        elif choice == "3":
            delete_book()
        elif choice == "4":
            search_books()
        elif choice == "0":
            return
        else:
            print("Invalid choice, please try again.")


db = initialise_database()
main_menu()
