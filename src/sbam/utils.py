import os
from enum import Enum


def read_file(path: str | os.PathLike) -> bytes:
    """Read contents of file at given path as bytes."""

    with open(path, "rb") as f:
        return f.read()


def write_file(path: str | os.PathLike, data) -> None:
    """Write data bytes to file at given path."""
    with open(path, "wb") as f:
        f.write(data)


def mkdir_if_not_exists(dir_path: str | os.PathLike) -> None:
    """Create a directory if it does not already exist."""
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)


def expand_paths(path: str | os.PathLike) -> list[str]:
    """Expand a file or directory path into a list of file paths."""
    paths = []
    if os.path.isdir(path):
        for root, _, filenames in os.walk(path):
            paths.extend(
                os.path.join(root, filename).replace("\\", "/")
                for filename in filenames
            )
    else:
        paths.append(path)
    return paths


def normalize_path(path: str) -> str:
    return path.replace("\\", "/").rstrip("/")
