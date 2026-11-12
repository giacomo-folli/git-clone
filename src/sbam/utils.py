import os
from enum import Enum


class Paths(Enum):
    MAIN_DIR = ".sbam"
    OBJECTS_DIR = os.path.join(MAIN_DIR, "objects")
    REFS_DIR = os.path.join(MAIN_DIR, "refs")
    HEAD_FILE = os.path.join(MAIN_DIR, "HEAD")


def read_file(path):
    """Read contents of file at given path as bytes."""

    with open(path, "rb") as f:
        return f.read()


def write_file(path, data):
    """Write data bytes to file at given path."""
    with open(path, "wb") as f:
        f.write(data)
