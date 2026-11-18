import collections, hashlib, os, operator, pathlib
import struct, zlib
from os import path
import time

from .. import utils

# Data for one entry in the git index (.sbam/index)
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
    _MAIN_DIR = ".sbam"
    _OBJECTS_DIR = path.join(_MAIN_DIR, "objects")
    _REFS_DIR = path.join(_MAIN_DIR, "refs")
    _HEADS_DIR = path.join(_REFS_DIR, "heads")
    _HEAD_FILE = path.join(_MAIN_DIR, "HEAD")
    _IGNORE_FILE = ".sbamignore"

    """Service for repository operations such as init, object lookup,
    status checks, and tree/index inspection.

    This class provides the core Git-like behaviors used by the sbam CLI:
    creating the repository layout, hashing and storing objects, reading index
    metadata, and reporting working tree changes.
    """

    def get_local_master_hash(self):
        """Get current commit hash (SHA-1 string) of local master branch."""

        master_path = os.path.join(self._MAIN_DIR, "refs", "heads", "master")
        try:
            return utils.read_file(master_path).decode().strip()
        except FileNotFoundError:
            return None

    def get_ignored_paths(self) -> list[str]:
        assert os.path.exists(
            self._IGNORE_FILE
        ), "currently .sbamignore always required for sake of simplicity"

        data = utils.read_file(self._IGNORE_FILE).decode("utf-8")
        paths = data.split("\n")

        assert "." not in paths, "Cannot ignore the main directory"
        assert (
            ".." not in paths
        ), "Cannot ignore the parent directory (and also why should you?)"

        return [p for p in paths if p]

    def init(self):
        """Initialize the sbam repository layout in the current directory.

        Creates the main repository directory, object store, refs directory,
        and the HEAD file pointing to the default main branch when the
        repository has not already been initialized.
        """

        if os.path.exists(self._MAIN_DIR):
            print(f"A {self._MAIN_DIR} directory already exists!")
            return

        for dir in [self._MAIN_DIR, self._OBJECTS_DIR, self._REFS_DIR, self._HEADS_DIR]:
            os.mkdir(dir)

        # For now, to make implement the feature
        utils.write_file(self._IGNORE_FILE, ("").encode())

        with open(self._HEAD_FILE, "w") as f:
            f.write("ref: refs/heads/master\n")

        print("Initialized sbam directory")

    def cat_file(self, sha1):
        """Read and decode an object from the object database.

        The provided SHA-1 identifies a stored Git object in the repository's
        object store. The object file is decompressed, the Git header is
        discarded, and the remaining payload is returned as UTF-8 text.
        """
        target_file = os.path.join(self._OBJECTS_DIR, sha1[:2], sha1[2:])

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
                self._OBJECTS_DIR,
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

        target_file = os.path.join(self._OBJECTS_DIR, sha1[:2], sha1[2:])

        data = utils.read_file(target_file)
        decomp = zlib.decompress(data)

        start = decomp.find(b"\x00")
        parsed = decomp[start + 1 :]

        return parsed.strip(b"\n\r").decode("UTF-8")

    def write_tree(self):
        """Write tree objects from the current index entries, recursively
        creating sub-trees for subdirectories."""

        entries = self.read_index()
        return self._write_tree_level(entries)

    # GEMINI COOK
    def _write_tree_level(self, entries):
        """Build a tree object for one directory level.

        Entries whose paths contain '/' are grouped by their first path
        component (the subdirectory name) and a sub-tree is created
        recursively.  Entries without '/' are direct blob children of
        this tree.
        """
        tree_entries = []

        # Group entries by first path component
        # e.g. "src/lib/utils.py" → key="src", remaining="lib/utils.py"
        children = {}  # name → list of IndexEntry (with paths stripped)
        blobs = []  # entries that live directly at this level

        for entry in entries:
            if "/" in entry.path:
                dir_name, rest = entry.path.split("/", 1)
                # Create a new IndexEntry with the remaining sub-path
                sub_entry = entry._replace(path=rest)
                children.setdefault(dir_name, []).append(sub_entry)
            else:
                blobs.append(entry)

        # First, add blob entries (files at this level)
        for entry in sorted(blobs, key=lambda e: e.path):
            mode_path = "{:o} {}".format(entry.mode, entry.path).encode()
            tree_entry = mode_path + b"\x00" + entry.sha1
            tree_entries.append(tree_entry)

        # Then, add tree entries (subdirectories) — recurse
        for dir_name in sorted(children.keys()):
            sub_tree_sha1 = self._write_tree_level(children[dir_name])
            mode_path = "40000 {}".format(dir_name).encode()
            tree_entry = mode_path + b"\x00" + bytes.fromhex(sub_tree_sha1)
            tree_entries.append(tree_entry)

        return self.hash_object(b"".join(tree_entries), "tree")

    def read_index(self):
        """Read git index file and return list of IndexEntry objects."""

        try:
            data = utils.read_file(os.path.join(self._MAIN_DIR, "index"))
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

        ignored_paths = self.get_ignored_paths()

        for root, dirs, files in os.walk("."):
            dirs[:] = [
                d for d in dirs if d != self._MAIN_DIR and d not in ignored_paths
            ]
            files = [f for f in files if f not in ignored_paths]

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

    def commit(self, message, author):
        """Commit the current state of the index to master with given message.
        Return hash of commit object.
        """
        tree = self.write_tree()
        parent = self.get_local_master_hash()
        timestamp = int(time.mktime(time.localtime()))
        utc_offset = -time.timezone

        author_time = "{} {}{:02}{:02}".format(
            timestamp,
            "+" if utc_offset > 0 else "-",
            abs(utc_offset) // 3600,
            (abs(utc_offset) // 60) % 60,
        )

        lines = ["tree " + tree]
        if parent:
            lines.append("parent " + parent)
        lines.append("author {} {}".format(author, author_time))
        lines.append("committer {} {}".format(author, author_time))
        lines.append("")
        lines.append(message)
        lines.append("")

        data = "\n".join(lines).encode()
        sha1 = self.hash_object(data, "commit")

        master_path = os.path.join(self._MAIN_DIR, "refs", "heads", "master")
        utils.write_file(master_path, (sha1 + "\n").encode())

        print("committed to master: {:7}".format(sha1))
        return sha1

    def write_index(self, entries):
        """Write list of IndexEntry objects to git index file."""
        packed_entries = []
        for entry in entries:
            entry_head = struct.pack(
                "!LLLLLLLLLL20sH",
                entry.ctime_s,
                entry.ctime_n,
                entry.mtime_s,
                entry.mtime_n,
                entry.dev,
                entry.ino,
                entry.mode,
                entry.uid,
                entry.gid,
                entry.size,
                entry.sha1,
                entry.flags,
            )
            path = entry.path.encode()
            length = ((62 + len(path) + 8) // 8) * 8
            packed_entry = entry_head + path + b"\x00" * (length - 62 - len(path))
            packed_entries.append(packed_entry)
        header = struct.pack("!4sLL", b"DIRC", 2, len(entries))
        all_data = header + b"".join(packed_entries)
        digest = hashlib.sha1(all_data).digest()
        utils.write_file(os.path.join(self._MAIN_DIR, "index"), all_data + digest)

    def add(self, paths):
        """Add all file paths to git index."""
        expanded_paths = []
        for path in paths:
            expanded_paths.extend(utils.expand_paths(path))
        paths = list(map(utils.normalize_path, expanded_paths))

        ignored_paths = self.get_ignored_paths()
        normalized_ignored_paths = list(map(utils.normalize_path, ignored_paths))

        paths = [
            path
            for path in paths
            if not any(
                ignored in path.split("/") or ignored == path
                for ignored in normalized_ignored_paths
            )
        ]

        all_entries = self.read_index()

        entries = [e for e in all_entries if e.path not in paths]

        for path in paths:
            sha1 = self.hash_object(utils.read_file(path), "blob")
            st = os.stat(path)
            flags = len(path.encode())
            assert flags < (1 << 12)
            entry = IndexEntry(
                int(st.st_ctime),
                0,
                int(st.st_mtime),
                0,
                st.st_dev,
                st.st_ino,
                st.st_mode,
                st.st_uid,
                st.st_gid,
                st.st_size,
                bytes.fromhex(sha1),
                flags,
                path,
            )
            entries.append(entry)

        entries.sort(key=operator.attrgetter("path"))
        self.write_index(entries)

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
            case "add":
                self.add(args.paths)
            case "status":
                self.status()
            case "commit":
                self.commit(args.message, author=args.author)
            case "check-ignore-file":
                paths = ", ".join(self.get_ignored_paths())
                if not paths:
                    print("None")
                else:
                    print(paths)
            case "push":
                print("NOT IMPLEMENTED")
            case _:
                print("Unknown command")
