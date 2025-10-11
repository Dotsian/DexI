import random
from typing import cast

from packaging.specifiers import SpecifierSet
from packaging.version import parse as parse_version
from tomlkit import array, dumps, inline_table, nl, table

from ..commands.installer import install_package, uninstall_package
from ..core.dexi_types import PackageEntry
from ..core.fun import get_special
from ..core.package import Package
from ..core.utils import (
    console,
    error,
    fetch_all_packages,
    fetch_ballsdex_version,
    fetch_package,
    fetch_pyproject,
    package_name,
    parse_pyproject,
)


def add_package(package: str, branch: str):
    """
    Adds a package into the pyproject file.

    Parameters
    ----------
    package: str
        The package you want to add.
    branch: str
        The package's branch you want to retrieve the package from.
    """
    data = Package.from_git(package, branch)

    if data.ballsdex_version:
        ballsdex = fetch_ballsdex_version()

        if not ballsdex:
            return

        installed_version = parse_version(ballsdex)

        specifier = SpecifierSet(data.ballsdex_version)

        if installed_version not in specifier:
            error(
                f"Ballsdex version requirement for [red]'{package}'[/red] is set to "
                f"[red]'{data.ballsdex_version}'[/red], while this instance is on "
                f"version [red]'{ballsdex}'[/red]"
            )

    project = parse_pyproject()

    tool = project.setdefault("tool", table(True))
    initialized = "dexi" not in tool
    dexi = tool.setdefault("dexi", table())

    if not initialized and fetch_package(package, fetch_all_packages()) is not None:
        error("This [red]package[/red] has already been added")

    package_array = dexi.setdefault("packages", array().multiline(True))

    if len(package_array) == 0:
        package_array = array().multiline(True)
        dexi["packages"] = package_array

    fields = {"git": package, "version": data.version, "branch": branch}

    package_item = inline_table()
    package_item.update(fields)

    package_array.append(package_item)

    if initialized:
        dexi.add(nl())

    with open("pyproject.toml", "w") as file:
        output = dumps(project)

        if initialized and "\n\n[tool.dexi]" in output:  # Cheap way of doing this
            output = output.replace("\n\n[tool.dexi]", "\n[tool.dexi]")

        file.write(output)

    name = package_name(package, branch)

    console.print(f"  [cyan]+[/cyan] [bold green]{name}[/bold green]=={data.version}")


def remove_package(package: str):
    """
    Removes a package from the pyproject file.

    Parameters
    ----------
    package: str
        The package you want to remove.
    """
    project = parse_pyproject()

    if project is None:
        print("Failed to fetch pyproject file")
        return

    if "tool" not in project or "dexi" not in project["tool"]:  # type: ignore
        print("Could not find 'dexi' in pyproject.toml")
        return

    dexi_tool = project["tool"].get("dexi", {})  # type: ignore

    package_entry = fetch_package(package, dexi_tool["packages"])

    if package_entry is None:
        error(f"Could not find [red]'{package}'[/red] package")
        return

    uninstall_package(package)

    dexi_tool["packages"].remove(package_entry)

    if len(dexi_tool["packages"]) == 0:
        dexi_tool["packages"] = array()

    with open("pyproject.toml", "w") as file:
        file.write(dumps(project))

    name = package_name(package, package_entry["branch"])

    console.print(
        f"  [red]-[/red] [white]{name}[/white]"
        f"[grey46]=={package_entry['version']}[/grey46]"
    )


def update_package(package: str | PackageEntry):
    """
    Update a specified package.

    Parameters
    ----------
    package: str | PackageEntry
        The package you want to update.
    """
    fetched_package = package

    if isinstance(package, str):
        package = cast(str, package)
        packages = fetch_all_packages()

        if not packages:
            return False

        package_entry = fetch_package(package, packages)

        if package_entry is None:
            print(f"Could not find {package}")
            return False

        fetched_package = package_entry

    fetched_package = cast(PackageEntry, fetched_package)

    project = fetch_pyproject(fetched_package["git"], fetched_package["branch"])

    name = package_name(fetched_package["git"], fetched_package["branch"])

    project_version = project["project"]["version"]

    if fetched_package["version"] == project_version:
        return False

    install_package(fetched_package, output=False)

    dexi_project = parse_pyproject()

    if "tool" not in dexi_project or "dexi" not in dexi_project["tool"]:  # type: ignore
        error("[red]pyproject.toml[/red] contains invalid [red]DexI data[/red]")

    dexi_tool = dexi_project["tool"]["dexi"]  # type: ignore

    if "packages" not in dexi_tool:  # type: ignore
        error("[[red]pyproject.toml[/red] contains invalid [red]DexI data[/red]")

    packages = dexi_tool["packages"]  # type: ignore

    new_package = fetched_package.copy()
    new_package["version"] = project_version

    dexi_tool["packages"][packages.index(fetched_package)] = new_package  # type: ignore

    with open("pyproject.toml", "w") as file:
        file.write(dumps(dexi_project))

    console.print(
        f"   [bold cyan]»[/bold cyan] [bold green]{name}[/bold green] "
        f"[cyan]{fetched_package['version']}[/cyan] → "
        f"[bold cyan]{project_version}[/bold cyan] [bold green][UPDATED][/bold green]"
    )

    return True


def update_all_packages():
    """
    Updates all packages.
    """
    packages = fetch_all_packages()

    if not packages:
        print("No packages found to update")
        return

    outdated_packages = packages
    packages_updated = 0

    with console.status("[cyan]Updating packages..."):
        while outdated_packages:
            success = update_package(outdated_packages.pop(0))

            if not success:
                continue

            packages_updated += 1

        special = get_special()

        plural = "" if packages_updated == 1 else "s"
        emoji = "📦" if special is None else special["emoji"]
        phrase = "" if special is None else f" {random.choice(special['messages'])}"

        console.print(
            f"{emoji}{phrase} Updated [bold]{packages_updated}[/bold] package{plural}!"
        )
