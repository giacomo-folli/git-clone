import argparse, collections, hashlib, os
import struct, zlib

from . import utils, cli

# Data for one entry in the git index (.git/index)
IndexEntry = collections.namedtuple(
    "IndexEntry",
    [
        "ctime_s",
        "ctime_n",
        "mtime_s",
        "mtime_n",
        "dev",
        "ino",
        "mode",
        "uid",
        "gid",
        "size",
        "sha1",
        "flags",
        "path",
    ],
)


class Service:
    MAIN_DIR = ".sbam"
    OBJECTS_DIR = os.path.join(MAIN_DIR, "objects")
    REFS_DIR = os.path.join(MAIN_DIR, "refs")
    HEAD_FILE = os.path.join(MAIN_DIR, "HEAD")

    def mkdir_if_not_exists(self, path):
        if not os.path.exists(path):
            os.mkdir(path)

    def sbam_already_initialized(self) -> bool:
        return os.path.exists(self.MAIN_DIR)

    def init(self, args):
        if os.path.exists(self.MAIN_DIR):
            print(f"A {self.MAIN_DIR} directory already exists!")
            return

        self.mkdir_if_not_exists(self.MAIN_DIR)
        self.mkdir_if_not_exists(self.OBJECTS_DIR)
        self.mkdir_if_not_exists(self.REFS_DIR)

        with open(self.HEAD_FILE, "w") as temp_file:
            temp_file.write("ref: refs/heads/main\n")

        if args.crazy:
            print("What are you crazy! flag is set!")

        print("Initialized sbam directory")

    def cat_file(self, args):
        sha1 = args.hash
        target_file = os.path.join(self.OBJECTS_DIR, sha1[:2], sha1[2:])

        data = utils.read_file(target_file)
        decomp = zlib.decompress(data)

        start = decomp.find(b"\x00")
        parsed = decomp[start + 1 :].strip(b"\n").decode("utf-8")
        print(parsed)

    def hash_object(self, data, obj_type="blob", write=True):
        """
        Compute hash of object data of given type and write to object store
        if "write" is True. Return SHA-1 object hash as hex string.
        """

        header = "{} {}".format(obj_type, len(data)).encode()
        full_data = header + b"\x00" + data
        sha1 = hashlib.sha1(full_data).hexdigest()

        if write:
            path = os.path.join(self.MAIN_DIR, self.OBJECTS_DIR, sha1[:2], sha1[2:])

            if not os.path.exists(path):
                os.makedirs(os.path.dirname(path), exist_ok=True)
                utils.write_file(path, zlib.compress(full_data))

        return sha1

    def ls_tree(self, args):
        sha1 = args.hash
        target_file = os.path.join(self.OBJECTS_DIR, sha1[:2], sha1[2:])

        data = utils.read_file(target_file)
        decomp = zlib.decompress(data)

        start = decomp.find(b"\x00")
        parsed = decomp[start + 1 :]

        decoded = parsed.strip(b"\n\r").decode("UTF-8")
        print(decoded)

    def write_tree(self, args):
        print("To implement")

    def read_index(self):
        """Read git index file and return list of IndexEntry objects."""

        try:
            data = utils.read_file(os.path.join(self.MAIN_DIR, "index"))
        except FileNotFoundError:
            return []

        digest = hashlib.sha1(data[:-20]).digest()
        assert digest == data[-20:], "invalid index checksum"

        signature, version, num_entries = struct.unpack("!4sLL", data[:12])
        assert signature == b"DIRC", "invalid index signature {}".format(signature)
        assert version == 2, "unknown index version {}".format(version)

        entry_data = data[12:-20]
        entries = []

        i = 0
        while i + 62 < len(entry_data):
            fields_end = i + 62
            fields = struct.unpack("!LLLLLLLLLL20sH", entry_data[i:fields_end])

            path_end = entry_data.index(b"\x00", fields_end)
            path = entry_data[fields_end:path_end]

            entry = IndexEntry(*(fields + (path.decode(),)))
            entries.append(entry)
            entry_len = ((62 + len(path) + 8) // 8) * 8

            i += entry_len
        assert len(entries) == num_entries

        return entries

    def get_status(self):
        """
        Get status of working copy, return tuple of (changed_paths, new_paths, deleted_paths).
        """
        paths = set()

        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d != ".git"]
            for file in files:
                path = os.path.join(root, file)
                path = path.replace("\\", "/")
                if path.startswith("./"):
                    path = path[2:]
                paths.add(path)
        entries_by_path = {e.path: e for e in self.read_index()}
        entry_paths = set(entries_by_path)
        changed = {
            p
            for p in (paths & entry_paths)
            if self.hash_object(utils.read_file(p), "blob", write=False)
            != entries_by_path[p].sha1.hex()
        }
        new = paths - entry_paths
        deleted = entry_paths - paths
        return (sorted(changed), sorted(new), sorted(deleted))

    def status(self):
        """Show status of working copy."""
        changed, new, deleted = self.get_status()
        if changed:
            print("changed files:")
            for path in changed:
                print("   ", path)
        if new:
            print("new files:")
            for path in new:
                print("   ", path)
        if deleted:
            print("deleted files:")
            for path in deleted:
                print("   ", path)

    def run(self, args):
        match args.command:
            case "init":
                self.init(args)
            case "cat-file":
                self.cat_file(args)
            case "hash-object":
                data = utils.read_file(args.file)
                sha1 = self.hash_object(data, args.type, write=args.write)
                print(sha1)
            case "ls-tree":
                self.ls_tree(args)
            case "write-tree":
                self.write_tree(args)
            case "status":
                self.status()
            case _:
                print("LOL")


def main() -> None:
    clid = cli.Cli()
    args = clid.parser.parse_args()

    sbam = Service()
    sbam.run(args)
