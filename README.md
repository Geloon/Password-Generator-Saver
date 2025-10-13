# Password-Generator-Saver

Easy and simple software for generating passwords and storing them in a json file!

After clicking in the 'Add' button it will create a new json file with all the information stored.
It allows us to search if an account does exist or not by clicking on the Search button.

I need testing & feedback with the executable file!

If you don't trust this executable but want to try it out anyway you can run the python file yourself:  

1) Install python, see how in:  [https://www.python.org/downloads/]

2) Open the folder with the cmd and type: **pip install pyperclip**

3) Run it

This is how it looks:

![This is an image](https://github.com/Geloon/Password-Generator-Saver/blob/master/sample.png?raw=true)

>[!NOTE]
>When using the search function you won't be able to copy the data from the window (in case you want to paste somewhere)

Security & running notes
-------------------------
- This version adds optional local encryption (Fernet) for stored credentials. You will be prompted at startup to enable encryption and to set a master password.
- You can choose to store the master password in the system keyring (Windows Credential Manager, macOS Keychain, or Linux Secret Service). This is recommended to avoid retyping it every time.
- The app no longer commits `data.json` or sensitive files; make sure not to commit your own exported `data.json`.

Development
-----------
Run tests with:

```
pip install -r requirements.txt
pytest
```

CI
--
This repo includes a GitHub Actions workflow that runs `pytest` on push and pull requests.
