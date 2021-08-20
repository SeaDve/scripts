#!/usr/bin/env python3

import re
import os
import glob
import fileinput
import subprocess
from xml.etree import ElementTree

from utils import log


def multiline_input()  -> str:
    raise NotImplemented


def get_metainfo_file(project_directory) -> str:
    data_files = os.listdir(os.path.join(project_directory, 'data'))
    for file in data_files:
        if 'metainfo' in file or 'appdata' in file:
            return os.path.join(project_directory, 'data', file)
    return None


def edit_metainfo_file(metainfo_file, release_notes, new version):
    raise NotImplemented


def get_main_build_file(project_directory) -> str:
    files = os.listdir(project_directory)
    if 'meson.build' in files:
        return os.path.join(project_directory, 'meson.build')
    return None


def get_cargo_file(project_directory) -> str:
    files = os.listdir(project_directory)
    if 'Cargo.toml' in files:
        return os.path.join(project_directory, 'Cargo.toml')
    return None


def replace_with_new_version_meson(meson_build_file, new_version):
    if meson_build_file is None:
        log("Meson build file not found")
        return

    log("Meson build file found")
    log(f"Replacing meson build version with new_version...")

    with open(meson_build_file, 'r+') as file:
        file_contents = file.read()
        new_content = re.sub(r"version:\s*'(.*)'", f"version: '{new_version}'", file_contents, count=1)
        file.seek(0)
        file.truncate(0)
        file.write(new_content)

        log("Successfully replaced meson build's version with new version")


def replace_with_new_version_cargo(cargo_toml_file, new_version):
    if cargo_toml_file is None:
        log("Cargo toml file not found")
        return

    log("Cargo toml file found")
    log(f"Replacing cargo toml version with new_version...")

    with open(cargo_toml_file, 'r+') as file:
        file_contents = file.read()
        new_content = re.sub(r'version\s*=\s*"(.*)"', f'version = "{new_version}"', file_contents, count=1)
        file.seek(0)
        file.truncate(0)
        file.write(new_content)

        log("Successfully replaced cargo toml's version with new version")


def make_release_on_dir(project_directory, new_version):
    metainfo_file = get_metainfo_file(project_directory)

    log(f"Making release for version {new_version}...")

    meson_build_file = get_main_build_file(project_directory)
    cargo_toml_file = get_cargo_file(project_directory)

    replace_with_new_version_meson(meson_build_file, new_version)
    replace_with_new_version_cargo(cargo_toml_file, new_version)

    return  # FIXME remove this

    if input("Do you want to commit the changes? [y/N]") not in ("y", "Y"):
        return

    if metainfo_file is not None:
        subprocess.call(['git', 'add', metainfo_file], check=True)
        log("Added meson build to staged files")

    if meson_build_file is not None:
        subprocess.call(['git', 'add', meson_build_file], check=True)
        log("Added cargo toml to staged files")

    if cargo_toml_file is not None:
        subprocess.call(['git', 'add', cargo_toml_file], check=True)
        log("Added metainfo to staged files")

    subprocess.call(['git', 'commit', '-m', f'chore: Bump to {new_version}'], check=True)
    log("Changes committed")

    if input("Do you want to push the changes? [y/N]") not in ("y", "Y"):
        return

    subprocess.call(['git', 'pull', 'origin', 'main'], check=True)
    log("Pulled changes from origin/main")

    subprocess.call(['git', 'push', 'origin', 'main'], check=True)
    log("Pushed local changes to origin/main")


# tree = ElementTree.parse(args.appstream_file)
# root = tree.getroot()

# releases = root.find('releases')
# latest_release = releases[0]

# latest_version = latest_release.get('version')
# latest_release_description = latest_release.find('description')

# header = latest_release_description.find('p')
# body = latest_release_description.find('ul')

# lines = [f"* {line.text}" for line in body]
# lines.insert(0, header.text)
# output = "\n".join(lines)

# try:
#     import gi
#     gi.require_version('Gtk', '3.0')
#     from gi.repository import Gtk, Gdk

    # FIXME Not working, so raise ImportError for now
#     raise ImportError

#     clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
#     clipboard.set_text(output, -1)
#     clipboard.store()

#     log(f"Copied release notes for version {latest_version} to clipboard")
# except ImportError:
#     log("Failed to import `Gtk` and `Gdk`")
#     log(f"Printing the release notes for version {latest_version} instead...")

#     print(output)

if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument('project_dir', help="The root directory of the project", type=str)
    parser.add_argument('version', help="The new version in format $N.$N.$N", type=str)
    args = parser.parse_args()

    # FIXME uncommit this

    # if input("Commit or stash unsaved changes before proceeding. Proceed? [y/N]") not in ("y", "Y"):
    #     sys.exit()

    make_release_on_dir(args.project_dir, args.version)
    log("Make sure to update the pot files to")
    log("Copy and paste this release note to github and make a release")

    # FIXME paste rleease notes here
