#!/usr/bin/env python3

import argparse
import subprocess
import sys

BOLD = "\033[1m"
BLUE = '\033[34m'
ENDC = '\033[0m'


def print_colored(header, text):
    print(f"{BOLD}{BLUE}{header}{ENDC}: {text}")


def log(text):
    print_colored("INFO", text)


parser = argparse.ArgumentParser()
parser.add_argument('project_name', help="The meson project name", type=str)
parser.add_argument('src_dir', help="The source directory", type=str)
parser.add_argument('build_dir', help="The building directory", type=str)
args = parser.parse_args()

if input("Commit or stash unsaved changes before proceeding. Proceed? [y/N]") not in ("y", "Y"):
    sys.exit()

log("Replacing 'gettext!' with 'gettext'...")
subprocess.run(f"find {args.src_dir} -type f -exec sed -i 's/gettext!/gettext/g' {{}} \;", shell=True, check=True)

log(f"Running ninja -C {args.build_dir} {args.project_name}-pot...")
try:
    subprocess.run(f"ninja -C {args.build_dir} {args.project_name}-pot", shell=True, check=True)
except subprocess.CalledProcessError:
    pass
finally:
    log("Restoring directory...")
    subprocess.run(f"git restore {args.src_dir}", shell=True, check=True)
