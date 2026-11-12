import argparse


class Cli:
    def __init__(self):
        """Configure the command-line interface for sbam."""

        self.parser = argparse.ArgumentParser(
            description="sbam: a simple git-like version control system"
        )
        subparsers = self.parser.add_subparsers(
            dest="command", required=True, metavar="command"
        )

        # CAT-FILE----------------------------------------------------------------
        cat_file_parser = subparsers.add_parser(
            "cat-file", help="Print the contents of a specified file"
        )
        cat_file_parser.add_argument("hash", help="The hash of the file to print")

        # INIT--------------------------------------------------------------------
        sub_parser = subparsers.add_parser(
            "init", help="Initialize a new sbam repository"
        )
        sub_parser.add_argument("repo", help="directory name for new repo")

        # HASH-OBJECT-------------------------------------------------------------
        hash_object_parser = subparsers.add_parser(
            "hash-object",
            help="hash contents of given path (and optionally write to "
            "object store)",
        )

        hash_object_parser.add_argument("file", help="The file to hash")
        hash_object_parser.add_argument("path", help="path of file to hash")
        hash_object_parser.add_argument(
            "-t",
            choices=["commit", "tree", "blob"],
            default="blob",
            dest="type",
            help="type of object (default %(default)r)",
        )
        hash_object_parser.add_argument(
            "-w",
            action="store_true",
            dest="write",
            help="write object to object store (as well as printing hash)",
        )

        # LS-TREE------------------------------------------------------------------
        ls_tree_parser = subparsers.add_parser(
            "ls-tree", help="List the contents of a tree object"
        )
        ls_tree_parser.add_argument(
            "--name-only",
            action="store_true",
            help="Print only the names of the tree contents",
        )
        ls_tree_parser.add_argument("hash", help="The hash in the git objects")

        # WRITE-TREE---------------------------------------------------------------
        write_tree_parser = subparsers.add_parser(
            "write-tree",
            help="Creates a tree object from the current state of the staging area",
        )

        subparsers.add_parser("status", help="Show status of working copy")
