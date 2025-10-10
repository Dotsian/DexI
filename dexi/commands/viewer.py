from packaging.version import parse as parse_version

from ..core.utils import console, fetch_all_packages, fetch_pyproject, package_name


def list_packages(hide_update: bool = False):
    """
    Displays a list of packages.

    Parameters
    ----------
    hide_update: bool
        Whether packages should hide if an update is available.
    """
    packages = fetch_all_packages()

    for package in packages:
        package_info = fetch_pyproject(package["git"], package["branch"])

        project_version = package_info["project"]["version"]
        notice = ""

        if (
            parse_version(project_version) > parse_version(package["version"])
            and not hide_update
        ):
            notice = f" → [yellow]v{project_version}[/yellow]"

        name = package_name(package["git"], package["branch"])

        console.print(
            f"  [cyan]—[/cyan] [bold green]{name}[/bold green] "
            f"[cyan]v{package['version']}[/cyan]{notice}"
        )
