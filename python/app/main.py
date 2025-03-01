import argparse
import hashlib
import os
import zlib


class Cli:
    main_dir = ".sbam"
    objects_dir = os.path.join(main_dir, "objects")
    refs_dir = os.path.join(main_dir, "refs")
    head_file = os.path.join(main_dir, "HEAD")

    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description="sbam: a simple git-like version control system"
        )
        subparsers = self.parser.add_subparsers(dest="command", required=True)

        # init command
        init_parser = subparsers.add_parser(
            "init", help="Initialize a new sbam repository"
        )
        init_parser.add_argument(
            "-c",
            "--crazy",
            action="store_true",
            help="Additional flag for init command",
        )
        init_parser.set_defaults(func=self.init)

        # cat-file command
        cat_file_parser = subparsers.add_parser(
            "cat-file", help="Print the contents of a specified file"
        )
        cat_file_parser.add_argument("hash", help="The hash of the file to print")
        cat_file_parser.set_defaults(func=self.cat_file)

        # hash-object command
        hash_object_parser = subparsers.add_parser(
            "hash-object", help="Hash the specified file"
        )
        hash_object_parser.add_argument("file", help="The file to hash")
        hash_object_parser.set_defaults(func=self.hash_object)

        # ls-tree command
        ls_tree_parser = subparsers.add_parser(
            "ls-tree", help="List the contents of a tree object"
        )
        ls_tree_parser.set_defaults(func=self.ls_tree)

    def mkdir_if_not_exists(self, path):
        if not os.path.exists(path):
            os.mkdir(path)

    def sbam_already_initialized(self) -> bool:
        return os.path.exists(self.main_dir)

    def init(self, args):
        self.mkdir_if_not_exists(self.main_dir)
        self.mkdir_if_not_exists(self.objects_dir)
        self.mkdir_if_not_exists(self.refs_dir)

        with open(self.head_file, "w") as temp_file:
            temp_file.write("ref: refs/heads/main\n")

        if args.crazy:
            print("What are you flag is set!")

        print("Initialized sbam directory")

    def cat_file(self, args):
        hash = args.hash
        dir = hash[:2]
        file = hash[2:]

        with open(os.path.join(self.objects_dir, dir, file), "rb") as file:
            decomp = zlib.decompress(file.read())

        start = decomp.find(b"\x00")
        parsed = decomp[start + 1 :].strip(b"\n").decode("utf-8")
        print(parsed)

    def hash_object(self, args):
        fName = args.file

        with open(fName, "rb") as file:
            bytes = file.read()

        header = f"blob {len(bytes)}\x00"
        store = header.encode("ascii") + bytes
        hash = hashlib.sha1(store).hexdigest()

        if self.sbam_already_initialized():
            new_dir = os.path.join(os.getcwd(), self.objects_dir, hash[:2])

            self.mkdir_if_not_exists(new_dir)
            with open(os.path.join(new_dir, hash[2:]), "wb") as file:
                file.write(zlib.compress(store))

        print(hash)

    def ls_tree(self, args):
        print("To implement")

    def run(self):
        args = self.parser.parse_args()
        args.func(args)


if __name__ == "__main__":
    cli = Cli()
    cli.run()
