import re

BOLD = "\033[1m"
BLUE = '\033[34m'
ENDC = '\033[0m'


def print_colored(header, text):
    print(f"{BOLD}{BLUE}{header}{ENDC}: {text}")


def log(text):
    print_colored("INFO", text)


def replace_in_file(pattern: str, replacement: str, file_directory: str):
    with open(file_directory, 'r+') as file:
        file_contents = file.read()
        new_content = re.sub(pattern, replacement, file_contents, count=1)
        file.seek(0)
        file.truncate(0)
        file.write(new_content)


def multiline_input() -> str:
    raise NotImplementedError
