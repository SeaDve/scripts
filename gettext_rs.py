#!/usr/bin/env python3

import subprocess

from utils import log, c_input


def replace_gettext_macros(src_dir: str) -> None:
    log("Replacing 'gettext!' with 'gettext'...")
    subprocess.run(
        ["find", src_dir, "-type", "f", "-exec", "sed", "-i", "s/gettext!/gettext/g", "{}", ";"],
        check=True
    )
    log("Successfully replaced 'gettext!' with 'gettext'")


def generate_pot_files(build_dir: str, project_name: str) -> None:
    log("Generating pot file...")
    subprocess.run(["ninja", "-C", build_dir, f"{project_name}-pot"], check=True)
    log("Pot file has been successfully generated")


def restore_directory(src_dir: str) -> None:
    log("Restoring src directory...")
    subprocess.run(["git", "restore", src_dir], check=True)
    log("The src directory has been restored to previous state")


def main(project_name: str, src_dir: str, build_dir: str) -> None:
    if c_input("Commit or stash unsaved changes before proceeding. Proceed? [y/N]") not in ("y", "Y"):
        return

    try:
        replace_gettext_macros(src_dir)
        generate_pot_files(build_dir, project_name)
    except subprocess.CalledProcessError as error:
        log(f"An error has occured: {error}")
    finally:
        restore_directory(src_dir)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('project_name', help="The meson project name", type=str)
    parser.add_argument('src_dir', help="The source directory", type=str)
    parser.add_argument('build_dir', help="The building directory", type=str)
    args = parser.parse_args()

    main(args.project_name, args.src_dir, args.build_dir)
