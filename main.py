import os
import base64
import json
import secrets
import string
import pyperclip
from pathlib import Path
import shutil
import time
from tkinter import *
from tkinter import messagebox as mb, simpledialog
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
import keyring

# App data directory (per-user, not inside repo)
APP_DIR = Path.home() / ".password-generator-saver"
JSON_FILE = APP_DIR / "data.json"
ENC_FILE = APP_DIR / "data.enc"
SALT_FILE = APP_DIR / "data.salt"


def ensure_app_dir():
    try:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        try:
            APP_DIR.chmod(0o700)
        except Exception:
            # On some platforms/chroots chmod may fail; ignore
            pass
    except Exception as e:
        mb.showerror(
            "Error", f"Unable to create data directory {APP_DIR}: {e}")
        raise


def migrate_legacy_data():
    """Detect legacy data files in the current working directory and move them to APP_DIR.
    This will back up any existing files in APP_DIR before replacing.
    """
    legacy_names = ["data.json", "data.enc", "data.salt"]
    cwd = Path.cwd()
    found = [cwd / n for n in legacy_names if (cwd / n).exists()]
    if not found:
        return
    try:
        proceed = mb.askyesno(
            "Migrate data",
            f"Found legacy data files in {cwd}.\nMove them to {APP_DIR}?\n(They will be backed up if files already exist.)",
        )
    except Exception:
        # If GUI isn't available, skip
        return
    if not proceed:
        return

    ensure_app_dir()
    moved = []
    for src in found:
        dst = APP_DIR / src.name
        try:
            if dst.exists():
                bak = dst.with_suffix(dst.suffix + f".bak-{int(time.time())}")
                dst.replace(bak)
            src.replace(dst)
            moved.append(src.name)
        except Exception:
            try:
                shutil.copy2(src, dst)
                src.unlink()
                moved.append(src.name)
            except Exception as e:
                mb.showerror("Error", f"Failed to move {src} -> {dst}: {e}")
    if moved:
        mb.showinfo(
            "Migrated", f"Moved files: {', '.join(moved)} to {APP_DIR}")


def derive_fernet_from_password(password: str) -> Fernet:
    # Ensure salt exists or create it
    ensure_app_dir()
    if SALT_FILE.exists():
        salt = SALT_FILE.read_bytes()
    else:
        salt = os.urandom(16)
        SALT_FILE.write_bytes(salt)

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


# Keyring helper: store a fernet key (not the user's password)
KEYRING_SERVICE = "password-generator-saver"
KEYRING_KEY_NAME = "fernet_key"


def load_fernet_from_keyring() -> Fernet | None:
    try:
        encoded = keyring.get_password(KEYRING_SERVICE, KEYRING_KEY_NAME)
        if not encoded:
            return None
        # stored value should be the base64-encoded Fernet key (utf-8 str)
        key = encoded.encode()
        return Fernet(key)
    except Exception:
        return None


def save_fernet_key_to_keyring(key: bytes | str) -> bool:
    try:
        # key is expected to be the base64 urlsafe-encoded Fernet key (bytes or str)
        if isinstance(key, bytes):
            encoded = key.decode()
        else:
            encoded = str(key)
        keyring.set_password(KEYRING_SERVICE, KEYRING_KEY_NAME, encoded)
        return True
    except Exception:
        return False


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
        # Try loading an existing Fernet key from keyring
        existing = load_fernet_from_keyring()
        if existing:
            reuse = mb.askyesno(
                "Keyring", "A stored encryption key was found. Use it?")
            if reuse:
                FERNET = existing
                ENCRYPT = True
                mb.showinfo(
                    "OK", "Encryption enabled using keyring-stored key.")
                return

        # No stored key: ask if the user wants to generate and store a random key
        store_key = mb.askyesno(
            "Keyring", "No stored key found. Generate and store a random encryption key in system keyring? (recommended)")
        if store_key:
            try:
                key = Fernet.generate_key()  # bytes
                FERNET = Fernet(key)
                saved = save_fernet_key_to_keyring(key)
                ENCRYPT = True
                if saved:
                    mb.showinfo(
                        "OK", "Encryption enabled and key saved to keyring.")
                else:
                    mb.showinfo(
                        "OK", "Encryption enabled but failed to save key to keyring.")
                return
            except Exception as e:
                mb.showerror("Error", f"Failed to generate/store key: {e}")
                ENCRYPT = False
                return
        # otherwise fallthrough to asking for a master password (not stored)

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
    try:
        ensure_app_dir()
        data_json = json.dumps(data, indent=4).encode()
        token = FERNET.encrypt(data_json)
        ENC_FILE.write_bytes(token)
        try:
            ENC_FILE.chmod(0o600)
        except Exception:
            pass
    except Exception as e:
        mb.showerror("Error", f"Failed to save encrypted data: {e}")


def load_data_plain():
    try:
        ensure_app_dir()
        if not JSON_FILE.exists():
            return {}
        return json.loads(JSON_FILE.read_text())
    except FileNotFoundError:
        return {}
    except Exception as e:
        mb.showerror("Error", f"Failed to load data: {e}")
        return None


def save_data_plain(data: dict):
    try:
        ensure_app_dir()
        JSON_FILE.write_text(json.dumps(data, indent=4))
        try:
            JSON_FILE.chmod(0o600)
        except Exception:
            pass
    except Exception as e:
        mb.showerror("Error", f"Failed to save data: {e}")


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
    rnd = secrets.SystemRandom()
    rnd.shuffle(password_list)
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


def copy_and_notify(text: str, ttl_ms: int = 10000):
    try:
        pyperclip.copy(text)
    except Exception:
        try:
            root.clipboard_clear()
            root.clipboard_append(text)
        except Exception:
            mb.showerror(
                "Error", "Unable to copy to clipboard on this platform.")
            return
    mb.showinfo(
        "Copied", f"Copied to clipboard (will be cleared in {ttl_ms//1000}s)")
    try:
        root.after(ttl_ms, clear_clipboard)
    except Exception:
        pass


def show_credentials_dialog(website: str, email: str, password: str):
    dlg = Toplevel(root)
    dlg.title(website)
    dlg.transient(root)
    Label(dlg, text=f"Email: {email}", anchor='w').grid(
        row=0, column=0, padx=8, pady=4, sticky='w')
    Label(dlg, text=f"Password: {password}", anchor='w').grid(
        row=1, column=0, padx=8, pady=4, sticky='w')
    btn_frame = Frame(dlg)
    btn_frame.grid(row=2, column=0, pady=(4, 8))
    Button(btn_frame, text="Copy password", command=lambda: copy_and_notify(
        password)).grid(row=0, column=0, padx=4)
    Button(btn_frame, text="Copy email", command=lambda: copy_and_notify(
        email)).grid(row=0, column=1, padx=4)
    Button(btn_frame, text="Close", command=dlg.destroy).grid(
        row=0, column=2, padx=4)
    # Center the dialog roughly over root
    try:
        dlg.update_idletasks()
        x = root.winfo_rootx() + (root.winfo_width() - dlg.winfo_width()) // 2
        y = root.winfo_rooty() + (root.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f'+{x}+{y}')
    except Exception:
        pass


# ---------------------------- SAVE PASSWORD ------------------------------- #
def save():
    website = website_entry.get().strip().lower()
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
    website = website_entry.get().strip().lower()
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
        # Show dialog with copy buttons
        show_credentials_dialog(website, email, password)
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
