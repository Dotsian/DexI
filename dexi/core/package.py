from dataclasses import dataclass, field
from typing import Self

from .utils import error, fetch_pyproject, package_name


@dataclass
class PackageConfig:
    """
    DexI package configuration.
    """

    source: str
    target: str
    exclude: list[str] = field(default_factory=list[str])


@dataclass
class AppConfig:
    """
    DexI app supported package configuration.
    """

    source: str
    target: str
    models: str = "models.py"


@dataclass
class Package:
    """
    DexI package.
    """

    version: str
    package: PackageConfig

    ballsdex_version: str | None = None
    include_license: bool = True

    app: AppConfig | None = None

    @classmethod
    def from_git(cls, package: str, branch: str) -> Self:
        if package.count("/") != 1:
            error(
                "Invalid GitHub repository identifier entered; Expected <name/repository>"
            )

        data = fetch_pyproject(package, branch)

        if not data or "tool" not in data or "dexi" not in data["tool"]:
            error(f"Could not locate {package_name(package, branch)}")

        dexi_tool = data["tool"]["dexi"]
        dexi_package = dexi_tool["package"]

        if not dexi_tool.get("public", False):
            error(f"Could not locate {package_name(package, branch)}")

        package_config = PackageConfig(
            dexi_package["source"], dexi_package["target"], dexi_package.get("exclude", [])
        )

        fields = {
            "version": data["project"]["version"],
            "ballsdex_version": dexi_tool.get("ballsdex-version"),
            "include_license": dexi_tool.get("include-license", True),
            "package": package_config,
        }

        if "app" in dexi_tool:
            dexi_app = dexi_tool["app"]
            models = dexi_app.get("models", "models")

            if models.endswith(".py"):
                models = models[:-3]

            fields["app"] = AppConfig(dexi_app["source"], dexi_app["target"], models)

        return cls(**fields)
