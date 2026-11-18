from os import PathLike, path, mkdir
from enum import Enum


def read_file(path: str | PathLike) -> bytes:
    """Read contents of file at given path as bytes."""

    with open(path, "rb") as f:
        return f.read()


def write_file(path: str | PathLike, data) -> None:
    """Write data bytes to file at given path."""
    with open(path, "wb") as f:
        f.write(data)


def mkdir_if_not_exists(dir_path: str | PathLike) -> None:
    """Create a directory if it does not already exist."""
    if not path.exists(dir_path):
        mkdir(dir_path)
