#!/usr/bin/env python3
from __future__ import annotations

import glob
import os
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from argparse import Namespace
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple
from xml.etree import ElementTree

BOLD_RED = "\033[1;31m"
BOLD_GREEN = "\033[1;32m"
BOLD_YELLOW = "\033[1;33m"
RED = "\033[31m"
GREEN = "\033[32m"
ENDC = "\033[0m"

OK = f"{GREEN}ok{ENDC}"
FAILED = f"{BOLD_RED}FAILED{ENDC}"
SKIPPED = f"{BOLD_YELLOW}SKIPPED{ENDC}"
RUNNING = f"   {BOLD_GREEN}RUNNING{ENDC}"
ERROR = f"{RED}error{ENDC}"


class CheckError(Exception, ABC):
    @abstractmethod
    def message(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def suggestion(self) -> str:
        raise NotImplementedError


class MissingDependencyError(CheckError):
    def __init__(self, whats_missing: str, install_command: Optional[str] = None):
        self._whats_missing = whats_missing
        self._install_command = install_command

    def message(self) -> str:
        return f"{ERROR}: Missing dependency `{self._whats_missing}`"

    def suggestion(self) -> str:
        message = f"Please install `{self._whats_missing}` first"

        if self._install_command is not None:
            message += f" by running `{self._install_command}`"

        return message


class FailedCheckError(CheckError):
    def __init__(
        self,
        error_message: str,
        suggestion_message: str,
    ):
        self._error_message = error_message
        self._suggestion_message = suggestion_message

    def message(self) -> str:
        return self._error_message

    def suggestion(self) -> str:
        return self._suggestion_message


class Check(ABC):
    @abstractmethod
    def id(self) -> CheckID:
        """Unique identifier for the check."""

        raise NotImplementedError

    @abstractmethod
    def version(self) -> Optional[str]:
        """The version of the check, if any."""

        raise NotImplementedError

    @abstractmethod
    def subject(self) -> str:
        """Displayed string while running the check."""

        raise NotImplementedError

    @abstractmethod
    def run(self) -> None:
        """If this method did not raise an error, the check is considered successful."""

        raise NotImplementedError


class CheckID(Enum):
    RUSTFMT = "rustfmt"
    TYPOS = "typos"
    POTFILES_ALPHABETICALLY = "potfiles_alphabetically"
    POTFILES_EXIST = "potfiles_exist"
    POTFILES_SANITY = "potfiles_sanity"
    UI_FILES = "ui_files"
    RESOURCES = "resources"
    FORBIDDEN_PATTERNS = "forbidden_patterns"


class Rustfmt(Check):
    """Run rustfmt to enforce code style."""

    def id(self) -> CheckID:
        return CheckID.RUSTFMT

    def version(self) -> Optional[str]:
        try:
            return get_output(["cargo", "fmt", "--version"])
        except FileNotFoundError:
            return None

    def subject(self) -> str:
        return "code style"

    def run(self) -> None:
        try:
            return_code, output = run_and_get_output(
                ["cargo", "fmt", "--all", "--", "--check"]
            )
        except FileNotFoundError:
            raise MissingDependencyError(
                "cargo fmt", install_command="rustup component add rustfmt"
            )

        if return_code != 0:
            raise FailedCheckError(
                error_message=output,
                suggestion_message="Try running `cargo fmt --all`",
            )


class Typos(Check):
    """Run typos to check for spelling mistakes."""

    def id(self) -> CheckID:
        return CheckID.TYPOS

    def version(self) -> Optional[str]:
        try:
            return_code, output = self._run_typos(["--version"])

            if return_code != 0:
                return None

            return output
        except FileNotFoundError:
            return None

    def subject(self) -> str:
        return "spelling mistakes"

    def run(self) -> None:
        try:
            return_code, output = self._run_typos(["--color", "always"])
        except FileNotFoundError:
            raise MissingDependencyError(
                "typos", install_command="cargo install typos-cli"
            )

        if return_code != 0:
            raise FailedCheckError(
                error_message=output,
                suggestion_message="Try running `typos -w`",
            )

    @staticmethod
    def _run_typos(args: List[str]) -> Tuple[int, str]:
        try:
            return run_and_get_output(["typos", *args])
        except FileNotFoundError:
            typos_full_path = os.path.expanduser("~/.cargo/bin/typos")
            return run_and_get_output([typos_full_path, *args])


class PotfilesAlphabetically(Check):
    """Check if files in POTFILES are sorted alphabetically.

    This assumes the following:
        - POTFILES is located at `po/POTFILES.in`
    """

    def id(self) -> CheckID:
        return CheckID.POTFILES_ALPHABETICALLY

    def version(self) -> None:
        return None

    def subject(self) -> str:
        return "po/POTFILES.in alphabetical order"

    def run(self) -> None:
        files = self._get_files()

        for file, sorted_file in zip(files, sorted(files)):
            if file != sorted_file:
                raise FailedCheckError(
                    error_message=f"{ERROR}: Found file `{file}` before `{sorted_file}` in POTFILES.in",
                    suggestion_message="Please sort the POTFILES files alphabetically",
                )

    @staticmethod
    def _get_files() -> List[str]:
        with open("po/POTFILES.in") as potfiles_file:
            return [line.strip() for line in potfiles_file.readlines()]


class PotfilesExist(Check):
    """Check if all files in POTFILES exist.

    This assumes the following:
        - POTFILES is located at 'po/POTFILES.in'
    """

    def id(self) -> CheckID:
        return CheckID.POTFILES_EXIST

    def version(self) -> None:
        return None

    def subject(self) -> str:
        return "po/POTFILES.in all files exist"

    def run(self) -> None:
        files = self._get_non_existent_files()
        n_files = len(files)

        if n_files > 0:
            message = [
                f"{ERROR}: Found {n_files} file{'s'[:n_files^1]} in POTFILES.in that does not exist:"
            ]

            for file in files:
                message.append(str(file))

            raise FailedCheckError(
                error_message="\n".join(message),
                suggestion_message="Make sure that all files in POTFILES exist",
            )

    @staticmethod
    def _get_non_existent_files() -> List[Path]:
        files: List[Path] = []

        with open("po/POTFILES.in") as potfiles_file:
            for line in potfiles_file.readlines():
                file = Path(line.strip())
                if not file.exists():
                    files.append(file)

        return files


class PotfilesSanity(Check):
    """Check if all files with translatable strings are present and only those.

    The limitations are the following:
        - Only detects UI (Glade) or Rust files

    This assumes the following:
        - POTFILES is located at `po/POTFILES.in`
        - UI (Glade) files are located in `data/resources/ui` and use `translatable="yes"`
        - Rust files are located in `src` and use `*gettext` methods or macros
    """

    def id(self) -> CheckID:
        return CheckID.POTFILES_SANITY

    def version(self) -> None:
        return None

    def subject(self) -> str:
        return "po/POTFILES.in sanity"

    def run(self) -> None:
        potfiles = self._get_rust_or_ui_potfiles()
        files_with_translatable = self._get_ui_files() + self._get_rust_files()

        potfiles_without_translatable = [
            potfile for potfile in potfiles if potfile not in files_with_translatable
        ]
        files_that_should_be_potfile = [
            file for file in files_with_translatable if file not in potfiles
        ]

        n_potfiles_without_translatable = len(potfiles_without_translatable)
        n_files_that_should_be_potfile = len(files_that_should_be_potfile)

        message: List[str] = []

        if n_potfiles_without_translatable > 0:
            message.append(
                f"{ERROR}: Found {n_potfiles_without_translatable} file{'s'[:n_potfiles_without_translatable^1]} in POTFILES.in without translatable strings:"
            )

            for potfile in sorted(potfiles_without_translatable):
                message.append(str(potfile))

        if n_potfiles_without_translatable > 0 and n_files_that_should_be_potfile > 0:
            message.append("")

        if n_files_that_should_be_potfile > 0:
            message.append(
                f"{ERROR}: Found {n_files_that_should_be_potfile} file{'s'[:n_files_that_should_be_potfile^1]} with translatable strings not present in POTFILES.in:"
            )

            for file in sorted(files_that_should_be_potfile):
                message.append(str(file))

        if n_potfiles_without_translatable > 0 or n_files_that_should_be_potfile > 0:
            raise FailedCheckError(
                error_message="\n".join(message),
                suggestion_message="Make sure that POTFILES lists all and only the necessary files",
            )

    @staticmethod
    def _get_rust_or_ui_potfiles() -> List[Path]:
        potfiles: List[Path] = []

        with open("po/POTFILES.in") as potfiles_file:
            for line in potfiles_file.readlines():
                file = Path(line.strip())

                if file.suffix in [".ui", ".rs"]:
                    potfiles.append(file)

        return potfiles

    @staticmethod
    def _get_ui_files() -> List[Path]:
        output = get_output(
            [
                "find",
                "data/resources/ui",
                "-type",
                "f",
                "-exec",
                "grep",
                "-lI",
                'translatable="yes"',
                "{}",
                ";",
            ]
        )
        return [Path(line) for line in output.splitlines()]

    @staticmethod
    def _get_rust_files() -> List[Path]:
        output = get_output(
            [
                "find",
                "src",
                "-type",
                "f",
                "-exec",
                "grep",
                "-lIE",
                r"gettext\(|gettext_f\(|gettext!\(",
                "{}",
                ";",
            ]
        )

        # Ignore src/i18n.rs as it contains test cases that are not meant to be translated
        return [Path(line) for line in output.splitlines() if not line == "src/i18n.rs"]


class UiFiles(Check):
    """Validate ui files using gtk4-builder-tool.

    This ignores errors starting with the following:
        - Failed to lookup template parent type
        - Invalid object type

    This assumes the following:
        - ui files are located in `data/resources/ui/*.ui`
        - only one gresource in the file
    """

    def id(self) -> CheckID:
        return CheckID.UI_FILES

    def version(self) -> None:
        return None

    def subject(self) -> str:
        return "data/resources/ui/*.ui validity"

    def run(self) -> None:
        errors: List[str] = []

        for ui_file in glob.glob("data/resources/ui/*.ui"):
            try:
                return_code, output = run_and_get_output(
                    ["gtk4-builder-tool", "validate", ui_file]
                )
            except FileNotFoundError:
                raise MissingDependencyError(
                    "gtk4-devel", install_command="sudo dnf install gtk4-devel"
                )

            if (
                return_code != 0
                and "Failed to lookup template parent type" not in output
                and "Invalid object type" not in output
            ):
                errors.append(f"> {ui_file} <\n{output}\n")

        if len(errors) != 0:
            raise FailedCheckError(
                error_message="\n".join(errors),
                suggestion_message="Please fix the given errors on the ui files",
            )


class Resources(Check):
    """Check if files in data/resources/resources.gresource.xml are sorted alphabetically.

    This assumes the following:
        - gresource file is located in `data/resources/resources.gresource.xml`
        - only one gresource in the file
    """

    def id(self) -> CheckID:
        return CheckID.RESOURCES

    def version(self) -> None:
        return None

    def subject(self) -> str:
        return "data/resources/resources.gresource.xml"

    def run(self) -> None:
        tree = ElementTree.parse("data/resources/resources.gresource.xml")
        gresource = tree.find("gresource")

        if gresource is None:
            return

        files = [element.text for element in gresource.findall("file") if element.text]
        sorted_files = sorted(files, key=lambda f: Path(f).with_suffix(""))

        for file, sorted_file in zip(files, sorted_files):
            if file != sorted_file:
                raise FailedCheckError(
                    error_message=f"{ERROR}: Found file `{file}` before `{sorted_file}` in resources.gresource.xml",
                    suggestion_message="Please sort the resources alphabetically",
                )


class ForbiddenPatterns(Check):
    """Checks for forbidden patterns in the src directory."""

    @dataclass
    class Match:
        path: Path
        line_number: int
        column_number: int
        pattern: str

    def id(self) -> CheckID:
        return CheckID.FORBIDDEN_PATTERNS

    def version(self) -> None:
        return None

    def subject(self) -> str:
        joined = ", ".join(self._get_patterns())
        return f"no {joined}"

    def run(self) -> None:
        matches = self._get_matches(self._get_patterns())
        n_matches = len(matches)

        if n_matches > 0:
            message = [
                f"{ERROR}: Found {n_matches} forbidden pattern{'s'[:n_matches^1]}:"
            ]

            for match in matches:
                message.append(
                    f"found `{match.pattern}` at {match.path}:{match.line_number}:{match.column_number}"
                )

            raise FailedCheckError(
                error_message="\n".join(message),
                suggestion_message="Please use `log::*` macros instead for logging or implement todo!",
            )

    @staticmethod
    def _get_patterns() -> List[str]:
        gettext_macro_patterns = [
            "dcgettext!",
            "dcngettext!",
            "dgettext!",
            "dngettext!",
            "gettext!",
            "ngettext!",
            "npgettext!",
            "pgettext!"
        ]

        return ["dbg!", "println!", "print!", "todo!", *gettext_macro_patterns]

    @staticmethod
    def _get_matches(patterns: List[str]) -> List[Match]:
        to_find = "|".join(patterns)

        output = get_output(
            [
                "find",
                "src",
                "-type",
                "f",
                "-exec",
                "awk",
                f"match($0, /{to_find}/, p) {{ print FILENAME, FNR, index($0, p[0]), p[0] }}",
                "{}",
                ";",
            ]
        )

        matches: List[ForbiddenPatterns.Match] = []

        for line in output.splitlines():
            path, line_number, column_number, pattern = line.split()
            matches.append(
                ForbiddenPatterns.Match(
                    Path(path), int(line_number), int(column_number), pattern
                )
            )

        return matches


class Runner:
    """Runs the checks."""

    @dataclass
    class CheckItem:
        check: Check
        prerequisites: List[Check]

    def __init__(
        self,
        to_skip: List[CheckID],
        verbose: bool = False,
    ):
        self._to_skip = to_skip
        self._verbose = verbose

        self._check_items: List[Runner.CheckItem] = []
        self._successful_checks: List[Check] = []
        self._failed_checks: List[Tuple[Check, CheckError]] = []

    def add(self, check: Check, prerequisites: List[Check] = []) -> None:
        check_item = Runner.CheckItem(check, prerequisites)
        self._check_items.append(check_item)

    def run_all(self) -> bool:
        """Returns true if there are no failed checks; skipped or successful checks will be allowed."""

        n_checks = len(self._check_items)

        print(f"{RUNNING} checks at {os.getcwd()}")
        print("")
        print(f"running {n_checks} checks")

        n_skipped = 0
        start_time = time.time()

        for item in self._check_items:
            if item.check.id() in self._to_skip:
                n_skipped += 1
                self._print_result(item.check, f"{SKIPPED} (via command flag)")
                continue

            if not self._has_complete_prerequisite(item):
                n_skipped += 1
                self._print_has_incomplete_prerequisite(item)
                continue

            try:
                item.check.run()
            except CheckError as e:
                self._failed_checks.append((item.check, e))
                self._print_result(item.check, FAILED)
            else:
                self._successful_checks.append(item.check)
                self._print_result(item.check, OK)

        check_duration = time.time() - start_time
        n_successful_checks = len(self._successful_checks)
        n_failed = len(self._failed_checks)

        if n_failed > 0:
            print("")
            self._print_failures()

        print("")
        self._print_final_result(
            n_checks, n_successful_checks, n_failed, n_skipped, check_duration
        )

        return n_failed == 0

    def _has_complete_prerequisite(self, item: CheckItem) -> bool:
        for prerequisite_check in item.prerequisites:
            if prerequisite_check not in self._successful_checks:
                return False
        return True

    def _print_has_incomplete_prerequisite(self, item: CheckItem) -> None:
        prerequisites_to_print = [
            prerequisite.subject()
            for prerequisite in item.prerequisites
            if prerequisite not in self._successful_checks
        ]

        requires_message = ", ".join(prerequisites_to_print)

        self._print_result(
            item.check,
            f"{SKIPPED} (requires: {requires_message})",
        )

    def _print_failures(self) -> None:
        print("failures:")
        print("")

        for (check, error) in self._failed_checks:
            message = error.message()
            suggestion = error.suggestion()

            if message is not None or suggestion is not None:
                print(f"---- {check.subject()} ----")

            if message is not None:
                print(message)
                print("")

            if suggestion is not None:
                print(suggestion)
                print("")

        print("")
        print("failures:")

        for (check, _) in self._failed_checks:
            print(f"    {check.subject()}")

    def _print_result(self, check: Check, remark: str) -> None:
        messages = ["check", check.subject()]

        version = check.version() if self._verbose else None
        if version is not None:
            messages.append(f"({version})")

        messages.append("...")
        messages.append(remark)

        print(" ".join(messages))

    @staticmethod
    def _print_final_result(
        total: int, n_successful: int, n_failed: int, n_skipped: int, duration: float
    ) -> None:
        result = OK if n_failed == 0 else FAILED

        print(
            f"check result: {result}. {n_successful} passed; {n_failed} failed; {n_skipped} skipped; finished in {duration:.2f}s"
        )


def run_and_get_output(args: List[str]) -> Tuple[int, str]:
    process = subprocess.run(args, capture_output=True)
    stdout = process.stdout.decode("utf-8").strip()
    stderr = process.stderr.decode("utf-8").strip()
    return (process.returncode, "\n".join([stdout, stderr]).strip())


def get_output(args: List[str]) -> str:
    process = subprocess.run(args, capture_output=True, check=True)
    return process.stdout.decode("utf-8").strip()


def main(args: Optional[Namespace]) -> int:
    runner = Runner(
        to_skip=args.skip if args else [], verbose=args.verbose if args else False
    )
    runner.add(Rustfmt())
    runner.add(Typos())

    potfiles_exist = PotfilesExist()
    potfiles_sanity = PotfilesSanity()
    runner.add(potfiles_exist)
    runner.add(potfiles_sanity, prerequisites=[potfiles_exist])
    runner.add(
        PotfilesAlphabetically(),
        prerequisites=[potfiles_exist, potfiles_sanity],
    )

    runner.add(UiFiles())
    runner.add(Resources())
    runner.add(ForbiddenPatterns())

    if runner.run_all():
        return os.EX_OK
    else:
        return 1


def parse_args() -> Namespace:
    from argparse import ArgumentParser

    parser = ArgumentParser(
        description="Run conformity checks on the current Rust project"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Use verbose output"
    )
    parser.add_argument(
        "-s",
        "--skip",
        nargs="+",
        default=[],
        type=CheckID,
        help=f"Checks to skip. It can be any of the following: {', '.join([check_id.value for check_id in CheckID])}",
    )

    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main(parse_args()))
