#!/usr/bin/env python3

import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, List

import utils
from utils import info, c_input


def show_diff_main_branch_from_last_tagged(metainfo_file: Path) -> None:
    homepage_uri = find_homepage(metainfo_file)

    if not homepage_uri:
        info("No homepage uri found")
        info("Skipping show diff of main branch from last tagged")
        return

    last_tagged_version = subprocess.run(
        ['git', 'describe', '--tags', '--abbrev=0'],
        check=True, capture_output=True, text=True
    ).stdout

    uri = os.path.join(homepage_uri, 'compare', f'{last_tagged_version}...main')

    info(f"Opening uri at '{uri}'")
    utils.launch_web_for_uri(uri)


def find_homepage(metainfo_file: Path) -> Optional[str]:
    line = utils.find_in_file("homepage", metainfo_file)

    if not line:
        return None

    match = re.search('>(.*)<', line)

    if not match:
        return None

    return match.group(1)


def create_new_release_template(header: str, body: List[str], version: str) -> str:
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

    def __init__(self, directory: Path):
        self.directory = directory
        self.files = os.listdir(self.directory)

        self.metainfo_file = self._get_metainfo_file()
        self.meson_build_file = self._get_meson_build_file()
        self.cargo_toml_file = self._get_cargo_toml_file()

    def _get_metainfo_file(self) -> Optional[Path]:
        data_files = os.listdir(self.directory / 'data')
        for file in data_files:
            if 'metainfo' in file or 'appdata' in file:
                return self.directory / 'data' / file
        return None

    def _get_meson_build_file(self) -> Optional[Path]:
        if 'meson.build' in self.files:
            return self.directory / 'meson.build'
        return None

    def _get_cargo_toml_file(self) -> Optional[Path]:
        if 'Cargo.toml' in self.files:
            return self.directory / 'Cargo.toml'
        return None

    def _update_meson_version(self) -> None:
        if self.meson_build_file is None:
            info("Meson build file not found")
            info("Skipping meson version update...")
            return

        info(f"Meson build file found at '{self.meson_build_file}'")
        info("Replacing meson build version with new_version...")

        utils.find_and_replace_in_file(
            r"version:\s*'(.*)'", f"version: '{self.new_version}'",
            self.meson_build_file
        )
        info("Successfully replaced meson build's version with new version")

    def _update_cargo_version(self) -> None:
        if self.cargo_toml_file is None:
            info("Cargo toml file not found")
            info("Skipping cargo version update...")
            return

        info(f"Cargo toml file found at '{self.cargo_toml_file}'")
        info("Replacing cargo toml version with new_version...")

        utils.find_and_replace_in_file(
            r'version\s*=\s*"(.*)"', f'version = "{self.new_version}"',
            self.cargo_toml_file
        )
        info("Successfully replaced cargo toml's version with new version")

    def _update_metainfo_release_notes(self) -> None:
        if self.metainfo_file is None:
            info("Metainfo file not found")
            info("Skipping metainfo release notes update...")
            return

        info("Showing changes from last tagged version to main branch...")
        show_diff_main_branch_from_last_tagged(self.metainfo_file)

        info("Launching Gedit...")
        info("Write the release notes in the window and save the file")

        output = utils.get_user_input_from_gedit()
        if output is None:
            info("Failed to get release notes")
            info("Skipping metainfo release notes update...")
            return

        header = output.pop(0)
        body = output

        info(f"Metainfo file found at '{self.metainfo_file}'")
        info("Updating the metainfo file with the provided release notes and version")

        with self.metainfo_file.open(mode='r+') as file:
            file_lines = file.readlines()
            for index, line in enumerate(file_lines):
                if '<releases>' in line:
                    release_template = create_new_release_template(header, body, self.new_version)
                    file_lines.insert(index + 1, release_template)
            file.truncate(0)
            file.seek(0)
            file.writelines(file_lines)

        info("Successfully updated metainfo with latest release")

        release_note_lines = [f"* {line}" for line in body]
        release_note_lines.insert(0, header)
        release_note = "\n".join(release_note_lines)

        try:
            utils.copy_to_clipboard(release_note)
            info(f"Copied release notes for version {self.new_version} to clipboard")
            info("You can now paste the release note to github and make a release")
        except FileNotFoundError:
            info("Failed to copy release_note to clipboard")
            info(f"Printing the release notes for version {self.new_version} instead...")
            print(release_note)
            info("Copy and paste this release note to github and make a release")

    def set_new_version(self, new_version: str) -> None:
        self.new_version = new_version
        self._update_cargo_version()
        self._update_meson_version()
        self._update_metainfo_release_notes()

    def commit_and_push_changes(self) -> None:
        if c_input("Do you want to commit the changes? [y/N]") not in ("y", "Y"):
            return

        if self.metainfo_file is not None:
            subprocess.run(['git', 'add', self.metainfo_file], check=True)
            info("Added meson build to staged files")

        if self.meson_build_file is not None:
            subprocess.run(['git', 'add', self.meson_build_file], check=True)
            info("Added cargo toml to staged files")

        if self.cargo_toml_file is not None:
            subprocess.run(['git', 'add', self.cargo_toml_file], check=True)
            info("Added metainfo to staged files")

        subprocess.run(['git', 'commit', '-m', f'chore: Bump to {self.new_version}'], check=True)
        info("Changes committed")

        if c_input("Do you want to push the changes? [y/N]") not in ("y", "Y"):
            return

        subprocess.run(['git', 'pull', 'origin', 'main'], check=True)
        info("Pulled changes from origin/main")

        subprocess.run(['git', 'push', 'origin', 'main'], check=True)
        info("Pushed local changes to origin/main")


def main(project_directory: Path, new_version: str) -> None:
    if c_input(
        "Commit or stash unsaved changes before proceeding. Proceed? [y/N]"
    ) not in ("y", "Y"):
        return

    info(f"Making release for version {new_version}...")

    project = Project(project_directory)
    project.set_new_version(new_version)
    project.commit_and_push_changes()

    info("Make sure to also update the pot files")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('project_dir', help="The root directory of the project", type=Path)
    parser.add_argument('version', help="The new version in format $N.$N.$N", type=str)
    args = parser.parse_args()

    main(args.project_dir, args.version)
