from __future__ import annotations

import random
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, cast

from git import Repo

from ..core.dexi_types import PackageEntry
from ..core.fun import get_special
from ..core.package import Package
from ..core.utils import (
    SUPPORTED_APP_VERSION,
    add_list_entry,
    app_operations_supported,
    console,
    error,
    fetch_package,
    package_name,
    parse_pyproject,
    remove_list_entry,
)

if TYPE_CHECKING:
    from os import PathLike

    StrPath = str | PathLike


def uninstall_package(package: str):
    """
    Uninstalls a package.

    Parameters
    ----------
    package: str
        The package you want to uninstall.
    """
    project = parse_pyproject()

    if "tool" not in project or "dexi" not in project["tool"]:  # type: ignore
        return

    dexi_tool = project["tool"].get("dexi", {})  # type: ignore

    found_package = fetch_package(package, dexi_tool["packages"])

    if found_package is None:
        error(f"Could not find [red]'{package}'[/red] package")

    data = Package.from_git(found_package["git"], found_package["branch"])

    if data.app is not None and not app_operations_supported():
        return

    destination = Path.cwd() / "ballsdex" / "packages" / data.package.target

    if not destination.is_dir():
        return

    if data.app is not None:
        remove_list_entry(
            "extra-tortoise-models",
            f"ballsdex.packages.{data.package.target}.{data.app.models}",
        )

        remove_list_entry("extra-django-apps", data.app.target)

    remove_list_entry("packages", f"ballsdex.packages.{data.package.target}")

    shutil.rmtree(destination)


def install_package(
    package: PackageEntry, cancel_if_exists: bool = False, output: bool = True
) -> bool:
    """
    Installs a package.

    Parameters
    ----------
    package: PackageEntry
        The package you want to install.
    cancel_if_exists: bool
        Returns if the package is found in the packages folder.
    output: bool
        Whether you want to output the process to the console.
    """
    replaced = False

    repository = package["git"]
    branch = package["branch"]

    data = Package.from_git(repository, branch)

    author, repository = repository.split("/")
    # this should be reworked so it doesn't only work for github
    # but for now this should suffice
    repository_url = f"https://github.com/{author}/{repository}.git"
    package_destination = Path.cwd() / "ballsdex" / "packages" / data.package.target

    name = package_name(repository, branch)

    # We want to make sure that all packages from the same repo and branch
    # use the same "cache", but also that if the package is in a diff branch
    # or a different repo it doesn't accidently get updated when something else
    # does.
    cache_dir = Path.cwd() / "dexi-cache" / f"{author}-{repository}-{branch}"

    if package_destination.exists():
        if cancel_if_exists:
            return False

        replaced = True
        shutil.rmtree(package_destination)

    if data.app is not None:
        if not app_operations_supported():
            error(
                f"[red]DexI packages[/red] with Django apps are not supported on "
                f"red]Ballsdex v$BD_V[/red], please update to v{SUPPORTED_APP_VERSION}+"
            )

        app_destination = Path.cwd() / "admin_panel" / data.app.target

        if app_destination.exists():
            replaced = True
            shutil.rmtree(app_destination)

    if (cache_dir / ".git").is_dir():
        # pkg already cloned prior, so we can just pull
        repo = Repo.init(cache_dir)

        if not getattr(repo.remotes, "origin", None):
            error(
                f"[red]Cache dir exists for package at {cache_dir}"
                ", but there is no origin remote"
            )

        if not repo.remotes.origin.url == repository_url:
            error(
                f"[red]Cache dir exists for package at {cache_dir}"
                ", but it does not have the same remote url![/red]"
            )

        repo.remotes.origin.pull()
    else:
        cache_dir.mkdir(parents=True)
        repo = Repo.clone_from(repository_url, cache_dir)

    if branch not in [b.name for b in repo.branches]:
        print([b.name for b in repo.branches])
        error(f"[red]Asked to install branch {branch} but it is not present in repo!")

    repo.git.checkout(branch)

    package_src = cache_dir / data.package.source
    app_src: Path | None = None

    if not package_src.is_dir():
        error(f"[red]Source dir {data.package.source} not found in package!")
    if data.app:
        app_src = cache_dir / data.app.source
        if not app_src.is_dir():
            error(f"[red]App source {data.app.source} not found in package!")

    def copy_ignore_func(dir: StrPath, files: list[str]) -> list[str]:
        dir = Path(dir)
        return [
            str(dir.relative_to(cache_dir) / file)
            for file in files
            if file in data.package.exclude
        ]

    shutil.copytree(
        package_src, package_destination, dirs_exist_ok=True, ignore=copy_ignore_func
    )

    if data.app:
        if not app_src:
            # not possible but it makes the type checker complain
            # if this isn't here
            return False

        shutil.copytree(app_src, app_destination, dirs_exist_ok=True)

        add_list_entry(
            "extra-tortoise-models",
            f"ballsdex.packages.{data.package.target}.{data.app.models}",
        )

        add_list_entry("extra-django-apps", data.app.target)

    add_list_entry("packages", f"ballsdex.packages.{data.package.target}")

    if not output:
        return True

    color = "yellow" if replaced else "cyan"
    addition = ""

    if data.app is not None:
        addition += f" [white]&[/white] [bold green]admin_panel/{data.app.target}"

    console.print(
        f"  [{color}]+[/{color}] [grey]{name}[/grey]: "
        f"[bold green]ballsdex/packages/{data.package.target}{addition}[/bold green]"
    )

    return True


def install_packages(all: bool = False):
    """
    Installs all packages found in the pyproject file.

    Parameters
    ----------
    all: bool
        Whether you want to install all packages,
        including ones that have already been installed.
    """
    project = parse_pyproject()

    if "tool" not in project or "dexi" not in project["tool"]:  # type: ignore
        print("No packages found to install")
        return

    packages = cast(list[PackageEntry], project["tool"]["dexi"].get("packages", []))  # type: ignore

    if not packages:
        print("No packages found to install")
        return

    packages_installed = 0

    with console.status("[cyan]Installing packages..."):
        while packages:
            success = install_package(packages.pop(0), not all)

            if not success:
                continue

            packages_installed += 1

        special = get_special()

        plural = "" if packages_installed == 1 else "s"
        emoji = "📦" if special is None else special["emoji"]
        phrase = "" if special is None else f" {random.choice(special['messages'])}"

        console.print(
            f"{emoji}{phrase} Installed "
            f"[bold]{packages_installed}[/bold] package{plural}!"
        )
