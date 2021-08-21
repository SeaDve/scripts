#!/usr/bin/env python3

import os
import subprocess
from datetime import datetime
from typing import Optional

import utils
from utils import log, c_input


def create_new_release_template(header: str, body: list, version: str) -> str:
    date_now = datetime.now().strftime("%Y-%m-%d")
    new_release_xml = [
        '<release version="{}" date="{}">'.format(version, date_now),
        '  <description>',
        '    <p>{}</p>'.format(header),
        '    <ul>',
    ]

    for line in body:
        new_release_xml.append(f'      <li>{line}</li>')

    new_release_xml += [
        '    </ul>',
        '  </description>',
        '</release>',
    ]

    new_release_xml = [f"    {line}\n" for line in new_release_xml]
    return "".join(new_release_xml)


class Project:

    def __init__(self, directory: str):
        self.directory = directory
        self.files = os.listdir(self.directory)

        self.metainfo_file = self._get_metainfo_file()
        self.meson_build_file = self._get_meson_build_file()
        self.cargo_toml_file = self._get_cargo_toml_file()

    def _get_metainfo_file(self) -> Optional[str]:
        data_files = os.listdir(os.path.join(self.directory, 'data'))
        for file in data_files:
            if 'metainfo' in file or 'appdata' in file:
                return os.path.join(self.directory, 'data', file)
        return None

    def _get_meson_build_file(self) -> Optional[str]:
        if 'meson.build' in self.files:
            return os.path.join(self.directory, 'meson.build')
        return None

    def _get_cargo_toml_file(self) -> Optional[str]:
        if 'Cargo.toml' in self.files:
            return os.path.join(self.directory, 'Cargo.toml')
        return None

    def _update_meson_version(self):
        if self.meson_build_file is None:
            log("Meson build file not found")
            log("Skipping meson version update...")
            return

        log("Meson build file found")
        log("Replacing meson build version with new_version...")

        utils.replace_in_file(
            r"version:\s*'(.*)'", f"version: '{self.new_version}'",
            self.meson_build_file
        )
        log("Successfully replaced meson build's version with new version")

    def _update_cargo_version(self):
        if self.cargo_toml_file is None:
            log("Cargo toml file not found")
            log("Skipping cargo version update...")
            return

        log("Cargo toml file found")
        log("Replacing cargo toml version with new_version...")

        utils.replace_in_file(
            r'version\s*=\s*"(.*)"', f'version = "{self.new_version}"',
            self.cargo_toml_file
        )
        log("Successfully replaced cargo toml's version with new version")

    def _update_metainfo_release_notes(self):
        log("Launching Gedit...")
        log("Write the release notes in the window and save the file")

        output = utils.get_user_input_from_gedit()
        if output is None:
            log("Failed to get release notes")
            log("Skipping metainfo release notes update...")
            return

        if self.metainfo_file is None:
            log("Metainfo file not found")
            log("Skipping metainfo release notes update...")
            return

        header = output.pop(0)
        body = output

        log("Metainfo file found")
        log("Updating the metainfo file with the provided release notes and version")

        with open(self.metainfo_file, 'r+') as file:
            file_lines = file.readlines()
            for index, line in enumerate(file_lines):
                if '<releases>' in line:
                    release_template = create_new_release_template(header, body, self.new_version)
                    file_lines.insert(index + 1, release_template)
            file.truncate(0)
            file.seek(0)
            file.writelines(file_lines)

        log("Successfully updated metainfo with latest release")

        release_note_lines = [f"* {line}" for line in body]
        release_note_lines.insert(0, header)
        release_note = "\n".join(release_note_lines)

        try:
            utils.copy_to_clipboard(release_note)
            log(f"Copied release notes for version {self.new_version} to clipboard")
            log("You can now paste the release note to github and make a release")
        except FileNotFoundError:
            log("Failed to copy release_note to clipboard")
            log(f"Printing the release notes for version {self.new_version} instead...")
            print(release_note)
            log("Copy and paste this release note to github and make a release")

    def set_new_version(self, new_version: str) -> None:
        self.new_version = new_version
        self._update_cargo_version()
        self._update_meson_version()
        self._update_metainfo_release_notes()

    def commit_and_push_changes(self):
        if c_input("Do you want to commit the changes? [y/N]") not in ("y", "Y"):
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

        if c_input("Do you want to push the changes? [y/N]") not in ("y", "Y"):
            return

        subprocess.run(['git', 'pull', 'origin', 'main'], check=True)
        log("Pulled changes from origin/main")

        subprocess.run(['git', 'push', 'origin', 'main'], check=True)
        log("Pushed local changes to origin/main")


def main(project_directory: str, new_version: str) -> None:
    if c_input(
        "Commit or stash unsaved changes before proceeding. Proceed? [y/N]"
    ) not in ("y", "Y"):
        return

    log(f"Making release for version {new_version}...")

    project = Project(project_directory)
    project.set_new_version(new_version)
    project.commit_and_push_changes()

    log("Make sure to also update the pot files")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('project_dir', help="The root directory of the project", type=str)
    parser.add_argument('version', help="The new version in format $N.$N.$N", type=str)
    args = parser.parse_args()

    main(args.project_dir, args.version)
