import typer

from .commands.installer import install_packages
from .commands.manager import (
    add_package,
    remove_package,
    update_all_packages,
    update_package,
)
from .commands.viewer import list_packages
from .core.errors import Errors

app = typer.Typer()


@app.command()
def add(package: str, branch: str = "main"):
    """
    Adds a package.

    Parameters
    ----------
    package: str
        The package you want to add.
    branch: str
        The branch you want to add the package from.
    """
    Errors(["invalid_project", "invalid_version", "no_config_found"]).check()

    add_package(package.replace("https://github.com/", ""), branch)


@app.command()
def remove(package: str):
    """
    Removes and uninstalls a package.

    Parameters
    ----------
    package: str
        The package you want to remove.
    """
    Errors(["invalid_project", "invalid_version", "no_config_found"]).check()

    remove_package(package)


@app.command()
def update(package: str | None = None):
    """
    Updates all packages or a specified package.

    Parameters
    ----------
    package: str
        The package you want to update.
        Automatically updates all packages if not specified.
    """
    Errors(["invalid_project", "invalid_version", "no_config_found"]).check

    if package is None:
        update_all_packages()
        return

    update_package(package)


@app.command()
def install(all: bool = False):
    """
    Installs all packages.

    Parameters
    ----------
    all: bool
        Whether you want to install all packages,
        including ones that have already been installed.
    """
    Errors(["invalid_project", "invalid_version", "no_config_found"]).check()

    install_packages(all)


@app.command("list")
def dlist(hide_update: bool = False):
    """
    Lists all packages.

    Parameters
    ----------
    hide_update: bool
        Whether packages should hide if an update is available.
    """
    Errors(["invalid_project"]).check()

    list_packages(hide_update)
