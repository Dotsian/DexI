import io
import os
import random
import shutil
import zipfile
from typing import cast

import requests

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
        error(f"Could not find '{package}' package")
        return

    data = Package.from_git(found_package["git"], found_package["branch"])

    if data.app is not None and not app_operations_supported():
        return

    desination = f"{os.getcwd()}/ballsdex/packages/{data.package.target}"

    if not os.path.isdir(desination):
        return

    if data.app is not None:
        remove_list_entry(
            "extra-tortoise-models",
            f"ballsdex.packages.{data.package.target}.{data.app.models}",
        )

        remove_list_entry("extra-django-apps", data.app.target)

    remove_list_entry("packages", f"ballsdex.packages.{data.package.target}")

    shutil.rmtree(desination)


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

    zip_url = f"https://github.com/{author}/{repository}/archive/refs/heads/{branch}.zip"
    desination = f"{os.getcwd()}/ballsdex/packages/{data.package.target}"

    name = package_name(repository, branch)

    if os.path.isdir(desination):
        if cancel_if_exists:
            return False

        replaced = True
        shutil.rmtree(desination)

    if data.app is not None:
        if not app_operations_supported():
            error(
                f"DexI packages with Django apps are not supported "
                f"on Ballsdex v$BD_V, please update to v{SUPPORTED_APP_VERSION}+"
            )

        app_desination = f"{os.getcwd()}/admin_panel/{data.app.target}"

        if os.path.isdir(app_desination):
            replaced = True
            shutil.rmtree(app_desination)

        os.makedirs(app_desination, exist_ok=True)

    os.makedirs(desination, exist_ok=True)

    response = requests.get(zip_url)

    if not response.ok:
        error(f"Failed to fetch {name}")

    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        base_folder = f"{repository}-{branch}/"

        for member in z.namelist():
            if member[-7:] in ["LICENSE", "LICENCE"]:
                with (
                    z.open(member) as src,
                    open(f"{desination}/{member[-7:]}", "wb") as dst,
                ):
                    shutil.copyfileobj(src, dst)

                continue

            if not member.startswith(f"{base_folder}{data.package.source}/"):
                continue

            relative_path = member[len(base_folder + data.package.source) + 1 :]

            if not relative_path or relative_path in data.package.exclude:
                continue

            target_path = os.path.join(desination, relative_path)

            if member.endswith("/"):
                os.makedirs(target_path, exist_ok=True)
                continue

            os.makedirs(os.path.dirname(target_path), exist_ok=True)

            with z.open(member) as src, open(target_path, "wb") as dst:
                shutil.copyfileobj(src, dst)

        if data.app is not None:  # I'll refactor this later
            app_desination = cast(str, app_desination)  # type: ignore

            for member in z.namelist():
                if not member.startswith(f"{base_folder}{data.app.source}/"):
                    continue

                relative_path = member[len(base_folder + data.app.source) + 1 :]

                if not relative_path:
                    continue

                target_path = os.path.join(app_desination, relative_path)

                if member.endswith("/"):
                    os.makedirs(target_path, exist_ok=True)
                    continue

                os.makedirs(os.path.dirname(target_path), exist_ok=True)

                with z.open(member) as src, open(target_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)

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
