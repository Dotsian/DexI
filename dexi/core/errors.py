from dataclasses import dataclass, field
from pathlib import Path

from packaging.version import parse as parse_version

from .utils import error, fetch_ballsdex_version

SUPPORTED_VERSION = "2.22.0"


@dataclass
class Errors:
    """
    Handles all app errors.
    """

    errors: list[str] = field(default_factory=list[str])

    @staticmethod
    def invalid_project() -> None:
        if Path("ballsdex").is_dir() and Path("pyproject.toml").is_file():
            return

        error("Attempted to use [red]DexI[/red] command on an [red]invalid project[/red]")

    @staticmethod
    def no_config_found() -> None:
        if Path("config.yml").is_file():
            return

        error("No [red]'config.yml'[/red] file detected")

    @staticmethod
    def invalid_version() -> None:
        if parse_version(fetch_ballsdex_version()) >= parse_version(SUPPORTED_VERSION):
            return

        error(
            "DexI does not support [red]Ballsdex v$BD_V[/red], please update to "
            f"v{SUPPORTED_VERSION}+"
        )

    def check(self):
        for project_error in self.errors:
            getattr(self, project_error)()
