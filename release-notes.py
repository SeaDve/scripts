#!/usr/bin/env python3

import os
import subprocess
from xml.etree import ElementTree

import utils
from utils import log, multiline_input


class Project:

    def __init__(self, directory: str):
        self.directory = directory
        self.files = os.listdir(self.directory)

        self.metainfo_file = self._get_metainfo_file()
        self.meson_build_file = self._get_meson_build_file()
        self.cargo_toml_file = self._get_cargo_toml_file()

    def _get_metainfo_file(self) -> str:
        data_files = os.listdir(os.path.join(self.directory, 'data'))
        for file in data_files:
            if 'metainfo' in file or 'appdata' in file:
                return os.path.join(self.directory, 'data', file)

    def _get_meson_build_file(self) -> str:
        if 'meson.build' in self.files:
            return os.path.join(self.directory, 'meson.build')
        return None

    def _get_cargo_toml_file(self) -> str:
        if 'Cargo.toml' in self.files:
            return os.path.join(self.directory, 'Cargo.toml')
        return None

    def _update_meson_version(self):
        if self.meson_build_file is not None:
            log("Meson build file found")
            log(f"Replacing meson build version with new_version...")

            utils.replace_in_file(r"version:\s*'(.*)'", f"version: '{self.new_version}'", self.meson_build_file)
            log("Successfully replaced meson build's version with new version")
        else:
            log("Meson build file not found")
            log("Skipping meson version update...")

    def _update_cargo_version(self):
        if self.cargo_toml_file is not None:
            log("Cargo toml file found")
            log(f"Replacing cargo toml version with new_version...")

            utils.replace_in_file(r'version\s*=\s*"(.*)"', f'version = "{self.new_version}"', self.cargo_toml_file)
            log("Successfully replaced cargo toml's version with new version")
        else:
            log("Cargo toml file not found")
            log("Skipping cargo version update...")

    def _update_metainfo_release_notes(self, release_notes: str):
        raise NotImplementedError

    def set_new_version(self, new_version: str):
        self.new_version = new_version
        self._update_cargo_version()
        self._update_meson_version()

    def commit_and_push_changes(self):
        if input("Do you want to commit the changes? [y/N]") not in ("y", "Y"):
            return

        if self.metainfo_file is not None:
            subprocess.run(['git', 'add', self.metainfo_file], check=True)
            log("Added meson build to staged files")

        if self.meson_build_file is not None:
            subprocess.run(['git', 'add', self.meson_build_file], check=True)
            log("Added cargo toml to staged files")

        if self.cargo_toml_file is not None:
            subprocess.run(['git', 'add', self.cargo_toml_file], check=True)
            log("Added metainfo to staged files")

        subprocess.run(['git', 'commit', '-m', f'chore: Bump to {self.new_version}'], check=True)
        log("Changes committed")

        if input("Do you want to push the changes? [y/N]") not in ("y", "Y"):
            return

        subprocess.run(['git', 'pull', 'origin', 'main'], check=True)
        log("Pulled changes from origin/main")

        subprocess.run(['git', 'push', 'origin', 'main'], check=True)
        log("Pushed local changes to origin/main")


def make_release_on_dir(project_directory: str, new_version: str):
    log(f"Making release for version {new_version}...")

    project = Project(project_directory)
    project.set_new_version(new_version)
    project.commit_and_push_changes()

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

    # FIXME uncomment this

    # if input("Commit or stash unsaved changes before proceeding. Proceed? [y/N]") not in ("y", "Y"):
    #     sys.exit()

    make_release_on_dir(args.project_dir, args.version)
    log("Make sure to also update the pot files")
    log("Copy and paste this release note to github and make a release")

    # FIXME paste release notes here
