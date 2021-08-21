import re
import subprocess

BOLD = '\033[1m'
BLUE = '\033[34m'
TURQUOISE = '\033[36m'
ENDC = '\033[0m'


def print_colored(header: str, text: str):
    print(f"{BOLD}{BLUE}{header}{ENDC}: {text}")


def log(text: str):
    print_colored("INFO", text)


def input_colored(header: str, text: str):
    return input(f"{BOLD}{TURQUOISE}{header}{ENDC}: {text}")


def c_input(text: str):
    return input_colored("CONSOLE", text)


def replace_in_file(pattern: str, replacement: str, file_directory: str):
    with open(file_directory, 'r+') as file:
        file_contents = file.read()
        new_content = re.sub(pattern, replacement, file_contents, count=1)
        file.seek(0)
        file.truncate(0)
        file.write(new_content)


def create_temp_file() -> str:
    import os
    import random
    import string
    import tempfile

    tmp_file_name = ''.join(random.choice(string.ascii_letters) for _ in range(10))
    tmp_file_location = tempfile.gettempdir()
    tmp_file_dir = os.path.join(tmp_file_location, tmp_file_name)
    subprocess.run(['touch', tmp_file_dir], check=True)
    return tmp_file_dir


def launch_gedit(file_dir: str):
    subprocess.run(['gedit', file_dir], check=True)


def get_user_input_from_gedit() -> list:
    tmp_file = create_temp_file()

    while True:
        launch_gedit(tmp_file)

        with open(tmp_file) as file:
            file_output = file.read().strip().splitlines()
            file_output = [line for line in file_output if line]

            for index, line in enumerate(file_output):
                if index == 0:
                    print(line)
                else:
                    print(f"* {line}")

        if c_input("Was that right? [y/N]") in ("y", "Y"):
            return file_output

        if c_input("Do you want to try again? [y/N]") not in ("y", "Y"):
            return None


def copy_to_clipboard(text: str):
    echo_text = subprocess.run(["echo", text], check=True, capture_output=True)
    subprocess.run(["xclip", "-selection", "clipboard"], input=echo_text.stdout)
