import os
import re
import sys
from typing import cast

import requests
from packaging.version import parse as parse_version
from rich.console import Console
from tomlkit import TOMLDocument, parse

from .dexi_types import PackageEntry

MODEL_RE = re.compile(r'("models"\s*:\s*\[)([^]]*)(\])')
SUPPORTED_APP_VERSION = "2.29.5"

console = Console()


def fetch_pyproject(package: str, branch: str) -> dict:
    """
    Returns the parsed contents of a pyproject file from GitHub.

    Parmaters
    ---------
    package: str
        The package you want to return from.
    branch: str
        The package's branch.
    """
    author, repository = package.split("/")
    name = package_name(package, branch)

    url = (
        f"https://raw.githubusercontent.com/{author}/{repository}/{branch}/pyproject.toml"
    )

    response = requests.get(url)

    if not response.ok:
        error(f"Failed to fetch [red]pyproject.toml[/red] from [red]{name}[/red]")

    data = parse(response.text)

    if "project" not in data:
        error(
            'Failed to find [red]"project"[/red] section in '
            f"[red]pyproject.toml[/red] from [red]{name}[/red]"
        )

    return data


def parse_pyproject(path: str | None = None) -> TOMLDocument:
    """
    Parses a pyproject file and returns it.

    Parameters
    ----------
    path: str | None
        The path that holds the pyproject file.
    """
    if path is None:
        path = os.getcwd()

    path = f"{path}/pyproject.toml"

    if not os.path.isfile(path):
        error("Failed to find [red]pyproject.toml[/red] in the current directory")

    with open(path) as file:
        return parse(file.read())


def app_operations_supported() -> bool:
    """
    Returns whether app operations are supported on this Ballsdex version.
    """
    return parse_version(fetch_ballsdex_version()) >= parse_version(SUPPORTED_APP_VERSION)


def fetch_ballsdex_version(path: str | None = None) -> str:
    """
    Returns the Ballsdex version.

    Parameters
    ----------
    path: str | None
        The path that will be checked.
    """
    if path is None:
        path = os.getcwd()

    path = f"{path}/ballsdex/__init__.py"

    if not os.path.isfile(path):
        error("Failed to find [red]ballsdex/__init__.py[/red] in the current directory")

    with open(path) as file:
        return file.read().replace('__version__ = "', "").rstrip()[:-1]


def package_name(package: str, branch: str) -> str:
    """
    Returns a formatted version of a package name.

    Parameters
    ----------
    package: str
        The package you want to format.
    branch: str
        The branch of the package used for formatting.
    """
    return f"{package}@{branch}"


def fetch_package(package: str, packages: list[PackageEntry]) -> PackageEntry | None:
    """
    Returns a package from a list of packages.

    Parameters
    ----------
    package: str
        The package you're searching for.
    packages: list[PackageEntry]
        A list of packages.
    """
    for item in packages:
        if "/" in package and item["git"] != package:
            continue

        if "/" not in package and item["git"].split("/")[1] != package:
            continue

        return cast(PackageEntry, item)

    return None


def fetch_all_packages() -> list[PackageEntry]:
    """
    Returns a list of all packages in the pyproject file.
    """
    project = parse_pyproject()

    if "tool" not in project or "dexi" not in project["tool"]:  # type: ignore
        return []

    packages = project["tool"]["dexi"].get("packages", [])  # type: ignore

    return cast(list[PackageEntry], packages)


def add_list_entry(section: str, entry: str, path: str | None = None):
    """
    Adds an item to a list in the config file.

    Parameters
    ----------
    section: str
        The list that will be modified.
    entry: str
        The item that will be appended to the config list.
    path: str | None
        The config file path.
    """
    if path is None:
        path = os.getcwd()

    with open(f"{path}/config.yml") as file:
        lines = file.readlines()

    item = f"  - {entry}\n"

    if f"{section}:\n" not in lines or item in lines:
        return

    for i, line in enumerate(lines):
        if line.rstrip().startswith(f"{section}:"):
            lines.insert(i + 1, item)
            break

    with open(f"{path}/config.yml", "w") as file:
        file.writelines(lines)


def remove_list_entry(section: str, entry: str, path: str | None = None):
    """
    Removes an item from a list in the config file.

    Parameters
    ----------
    section: str
        The list that will be modified.
    entry: str
        The item that will be removed from the config list.
    path: str | None
        The config file path.
    """
    if path is None:
        path = os.getcwd()

    with open(f"{path}/config.yml") as file:
        lines = file.readlines()

    item = f"  - {entry}\n"

    if f"{section}:\n" not in lines or item not in lines:
        return

    lines.remove(item)

    with open(f"{path}/config.yml", "w") as file:
        file.writelines(lines)


def error(message: str) -> None:
    """
    Outputs a formatted error and stops execution.

    Parameters
    ----------
    message: str
        The message you want to output
    """
    if "$BD_V" in message:
        message = message.replace("$BD_V", fetch_ballsdex_version())

    console.print(f"[bold red]ERROR[/bold red] — [white]{message}[/white]")
    sys.exit(1)
