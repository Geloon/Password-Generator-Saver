import os
import tempfile
import json
from main import derive_fernet_from_password, save_data_encrypted, load_data_encrypted


def test_derive_and_encrypt_decrypt(tmp_path):
    # Setup temporary files for salt and enc
    cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        pw = "testmaster"
        f = derive_fernet_from_password(pw)
        data = {"example.com": {"email": "a@b.com", "password": "secret"}}
        # Save encrypted
        token = f.encrypt(json.dumps(data).encode())
        open("data.enc", "wb").write(token)
        # Load using helper
        global FERNET
        from main import FERNET as FERNET_global
        # monkeypatch FERNET in module
        import importlib
        m = importlib.import_module('main')
        m.FERNET = f
        loaded = m.load_data_encrypted()
        assert loaded == data
    finally:
        os.chdir(cwd)
