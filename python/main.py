import argparse
import hashlib
import os
import sys
import zlib


class Cli:
    __commands = ["init", "cat-file", "hash-object", "ls-tree"]

    def __init__(self, args):
        self.__args = args
        self.__commands_handler = {}

        self.__commands_handler["init"] = self.init
        self.__commands_handler["cat-file"] = self.cat_file
        self.__commands_handler["ls-tree"] = self.ls_tree
        self.__commands_handler["hash-object"] = self.hash_object

    def mkdir_if_not_exists(self, path):
        if not os.path.exists(path):
            os.mkdir(path)

    def git_already_initialized(self) -> bool:
        return os.path.exists(".git")

    def init(self):
        self.mkdir_if_not_exists(".git")
        self.mkdir_if_not_exists(".git/objects")
        self.mkdir_if_not_exists(".git/refs")

        with open(os.path.join(".git", "HEAD"), "w") as temp_file:
            temp_file.write("ref: refs/heads/main\n")

        print("Initialized git directory")

    def cat_file(self):
        hash = self.__args[2]
        dir = hash[:2]
        file = hash[2:]

        with open(os.path.join(".git", "objects", dir, file), "rb") as file:
            decomp = zlib.decompress(file.read())

        start = decomp.find(b"\x00")
        parsed = decomp[start + 1 :].strip(b"\n").decode("utf-8")
        print(parsed)

    def hash_object(self):
        fName = self.__args[2]

        with open(fName, "rb") as file:
            bytes = file.read()

        header = f"blob {len(bytes)}\x00"
        store = header.encode("ascii") + bytes
        hash = hashlib.sha1(store).hexdigest()

        if self.git_already_initialized():
            new_dir = os.path.join(os.getcwd(), ".git/objects", hash[:2])

            self.mkdir_if_not_exists(new_dir)
            with open(os.path.join(new_dir, hash[2:]), "wb") as file:
                file.write(zlib.compress(store))

        print(hash)

    def ls_tree(self):
        print("To implement")

    def instructions(self):
        print(
            """
    Wrong syntax in call. Expected syntax is: git [action]

    Supported actions are:
    - init: Initialize new git repository
    - cat-file: print to console contents of specified file
    - hash-objects: hash the specified file"""
        )

    def run(self):
        print("DEBUG: args ->", self.__args)

        parser = argparse.ArgumentParser()

        parser.add_argument(
            "command",
            choices=[cmd for cmd in self.__commands],
            help="Command to execute",
        )

        parser.add_argument(
            "-c",
            "--crazy",
            action="store_true",
            help="Additional flag for init command",
        )
        parser.add_argument("object", help="Object to hash")

        args = parser.parse_args()

        # TODO: Update to better handling of argparse

        command = args.command

        if command in self.__commands_handler.keys():
            handle_func = self.__commands_handler[command]
            handle_func()
        else:
            print("Unknown command: " + command)


if __name__ == "__main__":
    cli = Cli(sys.argv)
    cli.run()
