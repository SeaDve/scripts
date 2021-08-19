BOLD = "\033[1m"
BLUE = '\033[34m'
ENDC = '\033[0m'


def print_colored(header, text):
    print(f"{BOLD}{BLUE}{header}{ENDC}: {text}")


def log(text):
    print_colored("INFO", text)
