#!/usr/bin/env python3

import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, List

import utils
from utils import info, c_input


def show_diff_main_branch_from_last_tagged(
    homepage_uri: str, last_tagged_version: str
) -> None:
    uri = os.path.join(homepage_uri, "compare", f"{last_tagged_version}...main")

    info(f"Opening uri at '{uri}'")
    utils.launch_web_for_uri(uri)


def create_new_release_template(header: str, body: List[str], version: str) -> str:
    date_now = datetime.now().strftime("%Y-%m-%d")
    new_release_xml = [
        '<release version="{}" date="{}">'.format(version, date_now),
        "  <description>",
        "    <p>{}</p>".format(header),
        "    <ul>",
    ]

    for line in body:
        new_release_xml.append(f"      <li>{line}</li>")

    new_release_xml += [
        "    </ul>",
        "  </description>",
        "</release>",
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
        data_files = os.listdir(self.directory / "data")
        for file in data_files:
            if "metainfo" in file or "appdata" in file:
                return self.directory / "data" / file
        return None

    def _get_meson_build_file(self) -> Optional[Path]:
        if "meson.build" in self.files:
            return self.directory / "meson.build"
        return None

    def _get_cargo_toml_file(self) -> Optional[Path]:
        if "Cargo.toml" in self.files:
            return self.directory / "Cargo.toml"
        return None

    def _update_meson_version(self) -> None:
        if self.meson_build_file is None:
            info("Meson build file not found")
            info("Skipping meson version update...")
            return

        info(f"Meson build file found at '{self.meson_build_file}'")
        info("Replacing meson build version with new_version...")

        utils.find_and_replace_in_file(
            r"version:\s*'(.*)'",
            f"version: '{self.new_version}'",
            self.meson_build_file,
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
            r'version\s*=\s*"(.*)"',
            f'version = "{self.new_version}"',
            self.cargo_toml_file,
        )
        info("Successfully replaced cargo toml's version with new version")

    def _update_metainfo_release_notes(self) -> None:
        if self.metainfo_file is None:
            info("Metainfo file not found")
            info("Skipping metainfo release notes update...")
            return

        homepage_uri = self.get_repo_homepage()
        if not homepage_uri:
            info("No homepage uri found")
            info("Skipping show diff of main branch from last tagged")
        else:
            info("Showing changes from last tagged version to main branch...")
            last_tagged_version = self.get_last_tagged_version()
            show_diff_main_branch_from_last_tagged(homepage_uri, last_tagged_version)

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

        with self.metainfo_file.open(mode="r+") as file:
            file_lines = file.readlines()
            for index, line in enumerate(file_lines):
                if "<releases>" in line:
                    release_template = create_new_release_template(
                        header, body, self.new_version
                    )
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
            info(
                f"Printing the release notes for version {self.new_version} instead..."
            )
            print(release_note)
            info("Copy and paste this release note to github and make a release")

    def get_repo_homepage(self) -> Optional[str]:
        if not self.metainfo_file:
            return None

        matches = utils.find_in_file('type="homepage">(.*)<', self.metainfo_file)

        if len(matches) < 1:
            return None

        return matches[0]

    def get_last_tagged_version(self) -> str:
        return subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.rstrip()

    def set_new_version(self, new_version: str) -> None:
        self.new_version = new_version
        self._update_cargo_version()
        self._update_meson_version()
        self._update_metainfo_release_notes()

    def fetch_origin(self) -> None:
        info("Running git fetch...")
        subprocess.run(["git", "fetch"], check=True)
        info("Sucessfully run git fetch")

    def commit_changes(self) -> None:
        if self.metainfo_file is not None:
            subprocess.run(["git", "add", self.metainfo_file], check=True)
            info("Added metainfo to staged files")

        if self.meson_build_file is not None:
            subprocess.run(["git", "add", self.meson_build_file], check=True)
            info("Added meson build to staged files")

        if self.cargo_toml_file is not None:
            subprocess.run(
                ["git", "add", self.cargo_toml_file, "Cargo.lock"], check=True
            )
            info("Added cargo toml to staged files")

        subprocess.run(
            ["git", "commit", "-m", f"chore: Bump to {self.new_version}"], check=True
        )
        info("Changes committed")

    def push_changes_to_remote_repo(self) -> None:
        subprocess.run(["git", "pull", "origin", "main"], check=True)
        info("Pulled changes from origin/main")

        subprocess.run(["git", "push", "origin", "main"], check=True)
        info("Pushed local changes to origin/main")


def main(project_directory: Path, new_version: str) -> None:
    if c_input(
        "Commit or stash unsaved changes before proceeding. Proceed? [y/N]"
    ) not in ("y", "Y"):
        return

    project = Project(project_directory)
    project.fetch_origin()

    if new_version is None:
        last_version = project.get_last_tagged_version().lstrip("v")
        new_version = c_input(
            f"Last version was '{last_version}'. What version do you want next?"
        )

    info(f"Making release for version {new_version}...")

    project.set_new_version(new_version)

    if c_input("Do you want to commit the changes? [y/N]") in ("y", "Y"):
        project.commit_changes()
        if c_input("Do you want to push the changes? [y/N]") in ("y", "Y"):
            project.push_changes_to_remote_repo()

    if c_input("Do you want to open a browser to create a new release? [y/N]") in (
        "y",
        "Y",
    ):
        project_homepage = project.get_repo_homepage()
        if project_homepage is not None:
            utils.launch_web_for_uri(os.path.join(project_homepage, "releases", "new"))
            info("Opened webpage to create a release")

    info(f"Successfuly made a new release for {new_version}...")
    info("Make sure to also update the pot files")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--project-dir",
        type=Path,
        required=False,
        default=os.getcwd(),
        help="The root directory of the project",
    )
    parser.add_argument(
        "-n",
        "--new-version",
        type=str,
        required=False,
        help="The new version in format $N.$N.$N",
    )
    args = parser.parse_args()

    main(args.project_dir, args.new_version)
