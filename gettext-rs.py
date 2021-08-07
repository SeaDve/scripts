#!/usr/bin/env python3

import os
import sys
import subprocess

if len(sys.argv) != 4:
    print("Usage: gettext-rs <app-name> <src-dir> <build-dir>")
    sys.exit()
    
app_name = sys.argv[1]
src_dir = os.path.abspath(sys.argv[2])
build_dir = os.path.abspath(sys.argv[3])

def print_with_border(text):
    print("---------------------------------------------")
    print(text)
    print("---------------------------------------------")

try:
    if input("Commit or stash unsaved changes before proceeding [y/N]") not in ("y", "Y"):
        sys.exit()
except KeyboardInterrupt:
    sys.exit()

print_with_border("Replacing 'gettext!' with 'gettext'...")
subprocess.run(f"find {src_dir} -type f -exec sed -i 's/gettext!/gettext/g' {{}} \;", shell=True, check=True)

print_with_border(f"Running ninja -C {build_dir} {app_name}-pot...")
try:
    subprocess.run(f"ninja -C {build_dir} {app_name}-pot", shell=True, check=True)
except subprocess.CalledProcessError:
    pass
finally:
    print_with_border("Restoring directory...")
    subprocess.run(f"git restore {src_dir}", shell=True, check=True)
