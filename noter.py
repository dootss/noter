import os
import sys
import hashlib
import base64
from getpass import getpass

# i was having some really strange issue with this when
# testing in different environments. for whatever
# reason i had to import crypto in only a few
# instances, but on some others, it worked fine
# regardless, this should fix it
try: 
    from Cryptodome.Cipher       import AES
    from Cryptodome.Util.Padding import pad, unpad
except ImportError:
    try:
        from Crypto.Cipher       import AES
        from Crypto.Util.Padding import pad, unpad
    except ImportError:
        raise ImportError("crypto module not found! ensure you intall pycryptodome/pycrypto")


NOTES_DIR = 'cryptnotes'
KEY_STORAGE_FILE = '.key_storage'
KEY = None
BLOCK_SIZE = 16


def clear_screen():
    if sys.platform == 'linux' or sys.platform == 'linux2':
        os.system('clear')
    elif sys.platform == 'win32':
        os.system('cls')


class AnsiColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def display_header():
    print(f"{AnsiColors.HEADER}       N O T E R{AnsiColors.ENDC}")
    print(f"{'='*25}{AnsiColors.ENDC}")

# for if name already exists
def append_number_to_title(title):
    original_title = title
    i = 1
    while os.path.exists(os.path.join(NOTES_DIR, title)):
        title = f"{original_title} ({i})"
        i += 1
    return title


def main_menu():
    while True:
        clear_screen()
        display_header()
        notes_exist = list_notes()
        print('----')
        print(f"{AnsiColors.OKCYAN}[n] New Note")
        if notes_exist:
            print(f"[d] Delete Note")
        print(f"[x] Exit{AnsiColors.ENDC}")
        choice = input("Enter choice: ").lower()
        if choice == "n":
            create_note()
        elif choice == "d" and notes_exist:
            clear_screen()
            delete_note()
        elif choice.isdecimal() and notes_exist:
            load_note(int(choice))
        elif choice == "x":
            clear_screen()
            break
        else:
            pass


def list_notes():
    if not os.path.exists(NOTES_DIR):
        os.makedirs(NOTES_DIR)
    files = sorted([f for f in os.listdir(NOTES_DIR) if os.path.isfile(os.path.join(NOTES_DIR, f))])
    print(f"{AnsiColors.OKGREEN}Your notes:{AnsiColors.ENDC}")
    if not files:
        print(f"{AnsiColors.WARNING}No notes available.{AnsiColors.ENDC}")
        return False
    for i, file in enumerate(files):
        print(f"[{i+1}] {file}")
    return True


def get_note_input():
    note_content = ""
    while True:
        line = input()
        if line.upper() == "EXIT":
            break
        note_content += line + "\n"
    return note_content.strip()


def encrypt(message):
    global KEY
    cipher = AES.new(KEY, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(message.encode('utf-8'), BLOCK_SIZE))
    iv = base64.b64encode(cipher.iv).decode('utf-8')
    ct = base64.b64encode(ct_bytes).decode('utf-8')
    return (iv + ct).encode('utf-8')


def decrypt(encrypted_data):
    global KEY
    iv = base64.b64decode(encrypted_data[:24])
    ct = base64.b64decode(encrypted_data[24:])
    cipher = AES.new(KEY, AES.MODE_CBC, iv)
    pt = unpad(cipher.decrypt(ct), BLOCK_SIZE)
    return pt.decode('utf-8')

def sanitize_title(title):
    # prevent user from creating directories with the title
    return title.replace("/", "-").replace("\\", "-")

def create_note():
    clear_screen()
    display_header()
    title = input(f"{AnsiColors.OKBLUE}Enter the title of your note:{AnsiColors.ENDC} ").strip()

    if title == "":
        # go away because no title was entered
        return
    
    title = sanitize_title(title)
    title = append_number_to_title(title)

    clear_screen()
    display_header()
    print(f"{AnsiColors.HEADER}Editing note: {title}{AnsiColors.ENDC}\n")
    print(f"{AnsiColors.OKBLUE}Type your note, type 'EXIT' to save and return to the main menu:{AnsiColors.ENDC}")
    note_content = get_note_input()
    if note_content:
        save_note(title, note_content)
        print(f"{AnsiColors.OKGREEN}Note saved as '{title}'!{AnsiColors.ENDC}")
    else:
        # tempted to just remove this and let people make empty notes admittedly
        print(f"{AnsiColors.WARNING}Empty note discarded.{AnsiColors.ENDC}")


def save_note(title, content):
    with open(os.path.join(NOTES_DIR, title), 'wb') as f:
        encrypted_data = encrypt(content)
        f.write(encrypted_data)


def pause():
    input(f"{AnsiColors.OKGREEN}Press enter to continue...{AnsiColors.ENDC}")

# Delete a note
def delete_note():
    display_header()
    notes_exist = list_notes()
    if not notes_exist:
        pause()
        return
    choice = input("Enter the number of the note to delete: ")
    try:
        choice = int(choice)
        files = sorted([f for f in os.listdir(NOTES_DIR) if os.path.isfile(os.path.join(NOTES_DIR, f))])
        file_name = files[choice-1]
        confirm = input("Are you sure you want to delete this note? [y/n]: ")
        if confirm.lower() == 'y':
            os.remove(os.path.join(NOTES_DIR, file_name))
        else:
            pass
    except (IndexError, ValueError):
        pass
        #print(f"{AnsiColors.FAIL}Invalid choice!{AnsiColors.ENDC}")

def load_note(note_id):
    files = sorted([f for f in os.listdir(NOTES_DIR) if os.path.isfile(os.path.join(NOTES_DIR, f))])
    try:
        note_title = files[note_id-1]
        with open(os.path.join(NOTES_DIR, note_title), 'rb') as f:
            encrypted_data = f.read()
        note_content = decrypt(encrypted_data)
        clear_screen()
        display_header()

        print(f"{AnsiColors.HEADER}Editing note: {note_title}{AnsiColors.ENDC}\n")

        print(f"{AnsiColors.OKBLUE}Type your note below; type 'EXIT' to save and return to the main menu:{AnsiColors.ENDC}")
        print(note_content)

        new_content = get_note_input()
        if new_content:
            updated_content = note_content + "\n" + new_content
            save_note(note_title, updated_content)
            print(f"{AnsiColors.OKGREEN}Note updated!{AnsiColors.ENDC}")
        else:
            print(f"{AnsiColors.WARNING}No changes made to the note.{AnsiColors.ENDC}")
    except IndexError:
        pass
    except ValueError: # where it was saved via a different key, or it's not encrypted at all.
        print(f"{AnsiColors.FAIL}Could not load note.{AnsiColors.ENDC}")
        pause()
        #print(f"{AnsiColors.FAIL}Invalid note number!{AnsiColors.ENDC}")



def manage_key(init=False):
    global KEY
    if init and not os.path.isfile(KEY_STORAGE_FILE):
        while True:
            key = getpass("Enter a secure key (will not be echoed): ")
            repeat_key = getpass("Repeat the key: ")
            if key == repeat_key:
                hashed_key = hashlib.sha256(key.encode()).hexdigest()
                with open(KEY_STORAGE_FILE, 'w') as f:
                    f.write(hashed_key)
                KEY = pad(key.encode(), BLOCK_SIZE)
                return
            else:
                print(f"{AnsiColors.FAIL}Keys do not match. Try again.{AnsiColors.ENDC}")
    elif os.path.isfile(KEY_STORAGE_FILE):
        while True:
            key = getpass("Enter your key to unlock the notes: ")
            hashed_key = hashlib.sha256(key.encode()).hexdigest()
            with open(KEY_STORAGE_FILE, 'r') as f:
                if f.read() == hashed_key:
                    KEY = pad(key.encode(), BLOCK_SIZE)
                    return
                else:
                    print(f"{AnsiColors.FAIL}Incorrect  key. Try again.{AnsiColors.ENDC}")


def main():
    manage_key(init=True)
    main_menu()

if __name__ == '__main__':
    main()
