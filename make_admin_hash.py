
from werkzeug.security import generate_password_hash
from getpass import getpass

password = getpass("Enter a new admin password: ")
confirm = getpass("Confirm admin password: ")

if not password or password != confirm:
    print("Passwords are empty or do not match.")
else:
    print("\nYour password hash is:\n")
    print(generate_password_hash(password))
