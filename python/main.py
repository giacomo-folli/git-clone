import sys, os, zlib, hashlib, base64


def cli(args):
    print("DEBUG: args ->", args)

    # TODO: Add argparse for better args/flags handling
    if len(args) < 2:
        instructions()
        return

    command = args[1]

    match command:
        case "init":
            create_dir_if_not_exists(".git")
            create_dir_if_not_exists(".git/objects")
            create_dir_if_not_exists(".git/refs")

            with open(os.path.join(".git", "HEAD"), "w") as temp_file:
                temp_file.write("ref: refs/heads/main\n")

            print("Initialized git directory")

        case "cat-file":
            hash = args[2]
            dir = hash[:2]
            file = hash[2:]

            with open(os.path.join(".git", "objects", dir, file), "rb") as file:
                decomp = zlib.decompress(file.read())

            start = decomp.find(b"\x00")
            parsed = decomp[start + 1 :].strip(b"\n").decode("utf-8")
            print(parsed)

        case "hash-object":
            fName = args[2]

            with open(fName, "rb") as file:
                bytes = file.read()

            header = f"blob {len(bytes)}\x00"
            store = header.encode("ascii") + bytes
            hash = hashlib.sha1(store).hexdigest()

            new_dir = os.path.join(os.getcwd(), ".git/objects", hash[:2])

            create_dir_if_not_exists(new_dir)
            with open(os.path.join(new_dir, hash[2:]), "wb") as file:
                file.write(zlib.compress(store))

            print(hash)

        case "ls-tree":
            print("To implement")

        case _:
            print("Unknown command: " + command)


def create_dir_if_not_exists(path):
    if not os.path.exists(path):
        os.mkdir(path)
        print("new dir " + path + " created!")


def instructions():
    print(
        """
Wrong syntax in call. Expected syntax is: git [action]

Supported actions are:
- init: Initialize new git repository
- cat-file: print to console contents of specified file
- hash-objects: hash the specified file"""
    )


if __name__ == "__main__":
    cli(sys.argv)
