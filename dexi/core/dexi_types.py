from typing import TypedDict


class SpecialMessage(TypedDict):
    emoji: str
    messages: list[str]


class PackageEntry(TypedDict):
    git: str
    version: str
    branch: str
