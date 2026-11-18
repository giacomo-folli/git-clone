# sbam

A Python-based Git-inspired project built as a hands-on learning exercise in Python and version control internals.

## Overview

sbam is a minimal implementation of a Git-like version control system created to deepen understanding of how Git works internally. The project was developed as part of a learning journey focused on Python and the core mechanics behind Git, following the principles and exercises from the CodeCrafters course.

The goal was not to reproduce Git in full, but to build a simplified system from first principles in order to understand repository structure, hashing, object storage, and the command-line workflows that underpin modern version control.

## Key capabilities

- `init`: initialize a repository
- `hash-object`: hash file contents and optionally persist the object
- `cat-file`: read and print a stored object
- `ls-tree`: list the contents of a tree object
- `write-tree`: write tree objects from the staging area
- `add`: add one or more files to the staging area
- `status`: show changed, new, and deleted files
- `commit`: commit the staged state to the `master` branch
- `check-ignore-file`: list paths excluded by `.sbamignore`

## Example usage

```bash
sbam init
sbam add <path>
sbam status
sbam commit -m "<commit message>"
sbam hash-object -w <file to hash>
sbam cat-file <object-hash>
sbam ls-tree --name-only <tree-hash>
sbam write-tree
sbam check-ignore-file
```

## Architecture

The implementation follows the same foundational model used by Git:

- files are stored as immutable objects
- each object is referenced by a hash of its content
- metadata is encoded in a Git-like format
- repository state is stored in a simple directory structure instead of a database or advanced index system

This approach reflects the learning objective of the project: understanding the mechanics behind version control systems through direct implementation.

## Current status

The repository contains a functional starting point for a Git-like system, with the object model and command-line interface already in place. The project remains intentionally simple and instructional, emphasizing clarity and learning over breadth or production polish.

## Tools and technologies

- Python 3.13
- `argparse` for command-line parsing
- `hashlib` for content hashing
- `zlib` for compression