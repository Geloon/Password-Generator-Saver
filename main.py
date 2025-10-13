from tkinter import *
from tkinter import messagebox as mb, simpledialog
from random import shuffle
import secrets
import string
import pyperclip
import json
import os
import base64

# Optional encryption
import pathlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
import keyring

# Files
JSON_FILE = "data.json"
ENC_FILE = "data.enc"
SALT_FILE = "data.salt"


def derive_fernet_from_password(password: str) -> Fernet:
    # Ensure salt exists or create it
    if os.path.exists(SALT_FILE):
        salt = open(SALT_FILE, "rb").read()
    else:
        salt = os.urandom(16)
        open(SALT_FILE, "wb").write(salt)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return Fernet(key)


ENCRYPT = False
FERNET = None


def ask_enable_encryption():
    global ENCRYPT, FERNET
    enable = mb.askyesno(
        "Encryption", "Enable local encryption for stored passwords? (recommended)")
    if not enable:
        ENCRYPT = False
        return

    # Offer to use system keyring
    use_keyring = mb.askyesno(
        "Keyring", "Store master password in system keyring? (recommended)")
    if use_keyring:
        stored = keyring.get_password("password-generator-saver", "master")
        if stored:
            # Ask to reuse stored or set a new one
            reuse = mb.askyesno(
                "Keyring", "A master password is stored. Use it?")
            if reuse:
                try:
                    FERNET = derive_fernet_from_password(stored)
                    ENCRYPT = True
                    mb.showinfo(
                        "OK", "Encryption enabled using keyring-stored master password.")
                    return
                except Exception as e:
                    mb.showerror(
                        "Error", f"Failed to initialize encryption: {e}")
        # No stored password or user wants to set new
        pw = simpledialog.askstring(
            "Master password", "Set master password:", show="*")
        if not pw:
            mb.showinfo("Info", "Encryption disabled (no password provided).")
            ENCRYPT = False
            return
        pw_confirm = simpledialog.askstring(
            "Confirm", "Confirm master password:", show="*")
        if pw != pw_confirm:
            mb.showerror(
                "Error", "Passwords do not match. Encryption disabled.")
            ENCRYPT = False
            return
        try:
            FERNET = derive_fernet_from_password(pw)
            ENCRYPT = True
            # store in keyring if user chose
            keyring.set_password("password-generator-saver", "master", pw)
            mb.showinfo(
                "OK", "Encryption enabled and master password saved to keyring.")
            return
        except Exception as e:
            mb.showerror("Error", f"Failed to enable encryption: {e}")
            ENCRYPT = False
            return

    # Fallback: not using keyring
    pw = simpledialog.askstring(
        "Master password", "Set master password:", show="*")
    if not pw:
        mb.showinfo("Info", "Encryption disabled (no password provided).")
        ENCRYPT = False
        return
    pw_confirm = simpledialog.askstring(
        "Confirm", "Confirm master password:", show="*")
    if pw != pw_confirm:
        mb.showerror("Error", "Passwords do not match. Encryption disabled.")
        ENCRYPT = False
        return
    try:
        FERNET = derive_fernet_from_password(pw)
        ENCRYPT = True
        mb.showinfo("OK", "Encryption enabled. Keep your master password safe.")
    except Exception as e:
        mb.showerror("Error", f"Failed to enable encryption: {e}")
        ENCRYPT = False


def load_data_encrypted():
    try:
        with open(ENC_FILE, "rb") as f:
            token = f.read()
        data_json = FERNET.decrypt(token).decode()
        return json.loads(data_json)
    except FileNotFoundError:
        return {}
    except Exception as e:
        mb.showerror("Error", f"Unable to decrypt data: {e}")
        return None


def save_data_encrypted(data: dict):
    data_json = json.dumps(data, indent=4).encode()
    token = FERNET.encrypt(data_json)
    with open(ENC_FILE, "wb") as f:
        f.write(token)


def load_data_plain():
    try:
        with open(JSON_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_data_plain(data: dict):
    with open(JSON_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ---------------------------- PASSWORD GENERATOR ------------------------------- #
def password_generator():
    password_entry.delete(0, 'end')
    # Use `secrets` for cryptographically secure randomness
    letters = string.ascii_letters
    numbers = string.digits
    symbols = '!#$%&()*+'

    password_letters = [secrets.choice(letters)
                        for _ in range(secrets.choice(range(8, 11)))]
    password_symbols = [secrets.choice(symbols)
                        for _ in range(secrets.choice(range(2, 5)))]
    password_numbers = [secrets.choice(numbers)
                        for _ in range(secrets.choice(range(2, 5)))]
    password_list = password_letters + password_symbols + password_numbers
    shuffle(password_list)
    password = "".join(password_list)
    password_entry.insert(0, password)

    # Ask whether to copy to clipboard
    copy_now = mb.askyesno(
        "Clipboard", "Copy password to clipboard? (will be cleared in 10s)")
    if copy_now:
        try:
            pyperclip.copy(password)
        except Exception:
            # fallback to Tk clipboard
            root.clipboard_clear()
            root.clipboard_append(password)

        # Clear clipboard after 10 seconds
        root.after(10000, clear_clipboard)


def clear_clipboard():
    try:
        # Try clearing both pyperclip and Tk clipboard
        pyperclip.copy("")
    except Exception:
        pass
    try:
        root.clipboard_clear()
    except Exception:
        pass


# ---------------------------- SAVE PASSWORD ------------------------------- #
def save():
    website = website_entry.get().strip()
    email = email_username_entry.get().strip()
    password = password_entry.get().strip()
    if len(website) == 0 or len(password) == 0:
        mb.showinfo(title="Oops", message="You left something empty")
        return

    new_data = {
        website: {
            "email": email,
            "password": password,
        }
    }

    if ENCRYPT:
        data = load_data_encrypted()
        if data is None:
            return
        data.update(new_data)
        save_data_encrypted(data)
    else:
        data = load_data_plain()
        data.update(new_data)
        save_data_plain(data)

    website_entry.delete(0, END)
    password_entry.delete(0, END)
    mb.showinfo("Saved", "Credentials saved successfully.")


# ---------------------------- FIND PASSWORD ------------------------- #
def find_password():
    website = website_entry.get().strip()
    if len(website) == 0:
        mb.showinfo(title="Error",
                    message="Please enter the website to search.")
        return

    if ENCRYPT:
        data = load_data_encrypted()
        if data is None:
            return
    else:
        data = load_data_plain()

    if website in data:
        email = data[website]["email"]
        password = data[website]["password"]
        mb.showinfo(title=website,
                    message=f"Email: {email}\nPassword: {password}")
    else:
        mb.showinfo(title="Error", message=f"No details for {website} exists.")


# ---------------------------- UI SETUP ------------------------------- #
root = Tk()
root.title("Password Generator/Saver by Geloon")
root.config(padx=50, pady=50)

# Prompt about encryption early
root.after(100, ask_enable_encryption)

# Website Label
website_label = Label(text="Website:")
website_label.grid(row=1, column=0)

# Website Entry
website_entry = Entry(width=25)
website_entry.grid(row=1, column=1, columnspan=2)
website_entry.focus()

# Email/Username Label
email_username_label = Label(text="Email/Username:")
email_username_label.grid(row=2, column=0)

# Email/Username Entry
email_username_entry = Entry(width=25)
email_username_entry.grid(row=2, column=1, columnspan=2)
email_username_entry.insert(0, "user@email.com")

# Password Label
password_label = Label(text="Password:")
password_label.grid(row=3, column=0)

# Password Entry
password_entry = Entry(width=25)
password_entry.grid(row=3, column=1, columnspan=2)

# Buttons
generate_password_button = Button(
    text="Generate Password", command=password_generator)
generate_password_button.grid(row=4, column=1, columnspan=2)

add_button = Button(text="Add", width=36, command=save)
add_button.grid(row=5, column=1, columnspan=2)

search_button = Button(text="Search", width=5, command=find_password)
search_button.grid(row=1, column=2)

root.mainloop()
