#!/usr/bin/env python3

import os
import sys
import subprocess

BOLD = "\033[1m"
BLUE = '\033[34m'
ENDC = '\033[0m'

def print_colored(header, text):
    print(f"{BOLD}{BLUE}{header}{ENDC}: {text}")

def log(text):
    print_colored("INFO", text)

if len(sys.argv) != 4:
    print_colored("USAGE", "gettext-rs [meson-project-name] [src-dir] [build-dir]")
    sys.exit()
    
app_name = sys.argv[1]
src_dir = os.path.abspath(sys.argv[2])
build_dir = os.path.abspath(sys.argv[3])

try:
    if input("Commit or stash unsaved changes before proceeding [y/N]") not in ("y", "Y"):
        sys.exit()
except KeyboardInterrupt:
    sys.exit()

log("Replacing 'gettext!' with 'gettext'...")
subprocess.run(f"find {src_dir} -type f -exec sed -i 's/gettext!/gettext/g' {{}} \;", shell=True, check=True)

log(f"Running ninja -C {build_dir} {app_name}-pot...")
try:
    subprocess.run(f"ninja -C {build_dir} {app_name}-pot", shell=True, check=True)
except subprocess.CalledProcessError:
    pass
finally:
    log("Restoring directory...")
    subprocess.run(f"git restore {src_dir}", shell=True, check=True)
