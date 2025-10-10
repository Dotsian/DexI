# DexI - BallsDex Package Manager

![DexI Thumbnail](https://raw.githubusercontent.com/Dotsian/DexI/refs/heads/main/assets/thumbnail.png)

## What is DexI

[![CI](https://github.com/Dotsian/DexI/actions/workflows/CI.yml/badge.svg)](https://github.com/Dotsian/DexI/actions/workflows/CI.yml)
[![Issues](https://img.shields.io/github/issues/Dotsian/DexI)](https://github.com/Dotsian/DexI/issues)
[![Version](https://img.shields.io/badge/version-1.1.0-blue)](https://github.com/Dotsian/DexI/blob/master/CHANGELOG.md)

Dex Inventory "DexI" is a Ballsdex package manager developed by DotZZ that provides developers with package control and easily allows users to add, remove, install, and update third-party packages.

_**App support will only be available after Ballsdex v2.29.4**_

## DexI vs. the Traditional Method

Using DexI over the traditional method for package management is far better, as it automatically handles tasks and allows developers to have more control over their packages. Additionally, if a package was updated, DexI will detect the package update. Users can then easily update that package with a single command.

## Installation

You can install DexI using [uv](https://docs.astral.sh/uv/getting-started/installation/):

```bash
uv tool install git+https://github.com/Dotsian/DexI
```

Updating DexI with uv:

```bash
uv tool upgrade dexi
```

## Usage

> [!WARNING]
> Always ensure the package you're downloading can be **trusted**, otherwise malicious code can be executed on your application.

Type `dexi --help` to view a list of commands.
Type `dexi <COMMAND> --help` to view information about a command.

<details>

<summary>Example commands</summary>

**Adding template project:**

```bash
dexi add Dotsian/DexI-Package
```

**Removing template project:**

```bash
dexi remove DexI-Package
```

**Adding template project from branch:**

```bash
dexi add Dotsian/DexI-Package --branch app
```

**Installing all packages:**

```bash
dexi install
```

**Listing all packages:**

```bash
dexi list
```

**Updating all packages:**

```bash
dexi update
```

</details>

## DexI package compatibility

> [!NOTE]
> If you're updating a package, make sure to update the version in the `pyproject.toml` file, otherwise DexI won't notice if an update was made.

Package creators can easily add DexI support to their packages. An **[example package with DexI support](https://github.com/Dotsian/DexI-Package)** has been created to help creators add DexI support to their packages. Here is a step by step guide on how you can add DexI support:

### pyproject.toml

You must have a `pyproject.toml` file in your package's GitHub repository. Here is what the average repository should look like:

```text
package/
├── __init__.py
└── cog.py
pyproject.toml
```

Once you have your `pyproject.toml` file ready, you have to create a new project. Use the following template below:

```toml
[project]
name = "example package"
version = "1.0.0"
description = "This package adds a command called `/say`!"
requires-python = ">=3.12"
license = "MIT"
dependencies = [
    "discord.py>=2.5.0",
]
```

### Configuration

Add the following sections into your `pyproject.toml` file. If your package doesn't include a Django app, omit the `dexi.app` section.

#### dexi

```toml
[tool.dexi]
public = true
ballsdex-version = ">=2.22.0"
include-license = true
```

- `public` - Whether the package can be downloaded with DexI.
- `ballsdex-version` - The Ballsdex version that this package supports. Supports operators such as `>=`, `==`, etc.
- `include-license` - Whether the license will also be installed into the package.

#### dexi.package

```toml
[tool.dexi.package]
source = "Package"
target = "my_package"
exclude = []
```

- `source` - The folder DexI will install for the package. The path has to be identical to the path in the GitHub repository.
- `target` - The new name of the folder once DexI installs it to the application.
- `exclude` - Files that will be ignored during DexI installation. (e.g. `hide.py`)

#### dexi.app (APP)

```toml
[tool.dexi.app]
source = "App"
target = "my_app"
models = "models.py"
```

- `source` - The folder DexI will install for the app. The path has to be identical to the path in the GitHub repository.
- `target` - The new name of the folder once DexI installs as a Django app.
- `models` - The file containing all your models, located in the package folder. (defaults to `models.py`)
