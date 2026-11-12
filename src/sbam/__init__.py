import argparse, collections, hashlib, os
import struct, zlib

from . import utils, cli

Paths = utils.Paths

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


class SbamService:
    """Service for repository operations such as init, object lookup,
    status checks, and tree/index inspection.

    This class provides the core Git-like behaviors used by the sbam CLI:
    creating the repository layout, hashing and storing objects, reading index
    metadata, and reporting working tree changes.
    """

    def init(self):
        """Initialize the sbam repository layout in the current directory.

        Creates the main repository directory, object store, refs directory,
        and the HEAD file pointing to the default main branch when the
        repository has not already been initialized.
        """

        if os.path.exists(Paths.MAIN_DIR.value):
            print(f"A {Paths.MAIN_DIR.value} directory already exists!")
            return

        utils.mkdir_if_not_exists(Paths.MAIN_DIR.value)
        utils.mkdir_if_not_exists(Paths.OBJECTS_DIR.value)
        utils.mkdir_if_not_exists(Paths.REFS_DIR.value)

        with open(Paths.HEAD_FILE.value, "w") as temp_file:
            temp_file.write("ref: refs/heads/main\n")

        print("Initialized sbam directory")

    def cat_file(self, sha1):
        """Read and decode an object from the object database.

        The provided SHA-1 identifies a stored Git object in the repository's
        object store. The object file is decompressed, the Git header is
        discarded, and the remaining payload is returned as UTF-8 text.
        """
        target_file = os.path.join(Paths.OBJECTS_DIR.value, sha1[:2], sha1[2:])

        data = utils.read_file(target_file)
        decomp = zlib.decompress(data)

        start = decomp.find(b"\x00")
        return decomp[start + 1 :].strip(b"\n").decode("utf-8")

    def hash_object(self, data, obj_type="blob", write=True):
        """
        Compute hash of object data of given type and write to object store
        if "write" is True. Return SHA-1 object hash as hex string.
        """

        header = "{} {}".format(obj_type, len(data)).encode()
        full_data = header + b"\x00" + data
        sha1 = hashlib.sha1(full_data).hexdigest()

        if write:
            path = os.path.join(
                Paths.MAIN_DIR.value,
                Paths.OBJECTS_DIR.value,
                sha1[:2],
                sha1[2:],
            )

            if not os.path.exists(path):
                os.makedirs(os.path.dirname(path), exist_ok=True)
                utils.write_file(path, zlib.compress(full_data))

        return sha1

    def ls_tree(self, sha1):
        """Return the raw contents of a tree object identified by sha1.

        The object is read from the object database, decompressed, and the
        Git object header is skipped to expose the tree payload. This is
        intended for inspecting tree entries stored in the repository.
        """

        target_file = os.path.join(Paths.OBJECTS_DIR.value, sha1[:2], sha1[2:])

        data = utils.read_file(target_file)
        decomp = zlib.decompress(data)

        start = decomp.find(b"\x00")
        parsed = decomp[start + 1 :]

        return parsed.strip(b"\n\r").decode("UTF-8")

    def read_index(self):
        """Read git index file and return list of IndexEntry objects."""

        try:
            data = utils.read_file(os.path.join(Paths.MAIN_DIR.value, "index"))
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
        """Get status of working copy, return tuple of (changed_paths, new_paths, deleted_paths)."""
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
        """Dispatch the parsed command to its corresponding service method."""
        match args.command:
            case "init":
                self.init()
            case "cat-file":
                file = self.cat_file(args)
                print(file)
            case "hash-object":
                data = utils.read_file(args.file)
                sha1 = self.hash_object(data, args.type, write=args.write)
                print(sha1)
            case "ls-tree":
                tree = self.ls_tree(args)
                print(tree)
            case "status":
                self.status()
            case _:
                print("LOL")


def main() -> None:
    clid = cli.Cli()
    args = clid.parser.parse_args()

    sbam = SbamService()
    sbam.run(args)
