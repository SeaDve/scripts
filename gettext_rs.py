#!/usr/bin/env python3

import os
import re
import subprocess
from pathlib import Path
from typing import Optional

import utils
from utils import info, c_input


class Project:

    def __init__(self, directory: Path, src_dir: Path, build_dir: Path):
        self.directory = directory
        self.src_dir = src_dir
        self.build_dir = build_dir

        self.project_name = self._get_project_name()

    def _get_project_name(self) -> Optional[str]:
        line = utils.find_in_file("project", self.directory / 'meson.build')

        if not line:
            return None

        match = re.search("'(.*)'", line)

        if not match:
            return None

        return match.group(1)

    def replace_gettext_macros(self) -> None:
        info("Replacing 'gettext!' with 'gettext'...")
        subprocess.run(
            ["find", self.src_dir, "-type", "f", "-exec",
             "sed", "-i", "s/gettext!/gettext/g", "{}", ";"],
            check=True
        )
        info("Successfully replaced 'gettext!' with 'gettext'")

    def generate_pot_files(self) -> None:
        info("Generating pot file...")
        subprocess.run(["ninja", "-C", self.build_dir, f"{self.project_name}-pot"], check=True)
        info("Pot file has been successfully generated")

    def restore_directory(self) -> None:
        info("Restoring src directory...")
        subprocess.run(["git", "restore", self.src_dir], check=True)
        info("The src directory has been restored to previous state")


def main(src_dir: Path, build_dir: Path) -> None:
    if c_input(
        "Commit or stash unsaved changes before proceeding. Proceed? [y/N]"
    ) not in ("y", "Y"):
        return

    project_dir = src_dir.parent
    project = Project(project_dir, src_dir, build_dir)

    try:
        project.replace_gettext_macros()
        project.generate_pot_files()
    except subprocess.CalledProcessError as error:
        info(f"An error has occured: {error}")
    finally:
        project.restore_directory()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--src-dir', type=Path, required=False,
                        default=Path(os.getcwd()) / 'src',
                        help="The source directory")
    parser.add_argument('-b', '--build-dir', type=Path, required=False,
                        default=Path(os.getcwd()) / '_build',
                        help="The building directory")
    args = parser.parse_args()

    main(args.src_dir, args.build_dir)
