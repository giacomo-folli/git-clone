# sbam

A Python-based Git-inspired project built as a hands-on learning exercise in Python and version control internals.

## Overview

sbam is a minimal implementation of a Git-like version control system created to deepen understanding of how Git works internally. The project was developed as part of a learning journey focused on Python and the core mechanics behind Git, following the principles and exercises from the CodeCrafters course.

The goal was not to reproduce Git in full, but to build a simplified system from first principles in order to understand repository structure, hashing, object storage, and the command-line workflows that underpin modern version control.

## Why this project exists

This project was created to learn by doing:

- understand Python in a practical, systems-oriented context
- explore Git internals instead of treating Git as a black box
- implement a real software tool with a clear, testable design
- practice command-line programming, file handling, cryptographic hashing, and serialization

The structure and implementation are intentionally educational and compact, reflecting a focused effort to learn core engineering concepts rather than to deliver a production-grade product.

## What the project demonstrates

- Repository initialization in a hidden `.sbam` directory
- Content-addressable storage using SHA-1 hashes
- Compression of stored objects with `zlib`
- Git-like object layout for blobs and tree metadata
- A command-line interface built with Python's `argparse`
- Practical experience with Python file I/O, hashing, and object modeling

## Key capabilities

- `init`: initialize a repository
- `hash-object`: hash a file and persist it as a repository object
- `cat-file`: read a stored object from the object database
- `ls-tree`: inspect a tree object
- `write-tree`: prepare the code path for writing tree objects from the current repository state

## Example usage

```bash
git-clone init
git-clone hash-object README.md
git-clone cat-file <object-hash>
git-clone ls-tree <tree-hash>
```

## Architecture

The implementation follows the same foundational model used by Git:

- files are stored as immutable objects
- each object is referenced by a hash of its content
- metadata is encoded in a Git-like format
- repository state is stored in a simple directory structure instead of a database or advanced index system

This approach reflects the learning objective of the project: understanding the mechanics behind version control systems through direct implementation.

## Learning focus

This project is centered on a few core skills:

- Python fundamentals and practical scripting
- CLI tool design
- file-system interaction
- hashing and integrity verification
- understanding data structures used in software systems

It is a strong example of building a small but meaningful software project to deepen technical understanding and improve engineering judgment.

## Current status

The repository contains a functional starting point for a Git-like system, with the object model and command-line interface already in place. The project remains intentionally simple and instructional, emphasizing clarity and learning over breadth or production polish.

## Tools and technologies

- Python 3.13
- `argparse` for command-line parsing
- `hashlib` for content hashing
- `zlib` for compression

## Project identity

Repository: `giacomo-folli/git-clone`

This project reflects a focused learning effort in Python and Git internals, informed by the CodeCrafters course and aimed at understanding the core principles behind version control systems from the inside out.
