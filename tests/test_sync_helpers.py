"""Tests for sync/compare helpers (pure functions in rustdesk_mcp.server)."""

from pathlib import Path

from rustdesk_mcp.server import (
    _diff_file_maps,
    _match_excluded,
    _parse_fork_list_line,
    _parse_remote_files,
    _sha256_file,
    _walk_local_files,
)


class TestMatchExcluded:
    def test_extension_pattern(self):
        assert _match_excluded("app.pyc", ["*.pyc"])
        assert not _match_excluded("app.py", ["*.pyc"])

    def test_dirname_pattern(self):
        assert _match_excluded("sub/__pycache__/x.pyc", ["__pycache__"])
        assert _match_excluded(".git", [".git"])

    def test_no_patterns(self):
        assert not _match_excluded("anything.txt", [])


class TestParseForkLine:
    def test_file(self):
        assert _parse_fork_list_line("[FILE] report.csv 1234b") == ("report.csv", 1234, "file")

    def test_dir(self):
        assert _parse_fork_list_line("[DIR] subdir 0b") == ("subdir", 0, "dir")

    def test_garbage(self):
        assert _parse_fork_list_line("not a listing line") is None
        assert _parse_fork_list_line("") is None


class TestParseRemoteFiles:
    def test_api_dicts(self):
        items = [{"name": "a.txt", "size": 10, "mtime": 5}]
        out = _parse_remote_files(items, [])
        assert out == {"a.txt": {"size": 10, "mtime": 5}}

    def test_fork_strings_skip_dirs(self):
        items = ["[FILE] a.txt 10b", "[DIR] sub 0b", "garbage"]
        out = _parse_remote_files(items, [])
        assert out == {"a.txt": {"size": 10, "mtime": 0}}

    def test_excludes_apply(self):
        items = [{"name": "a.pyc", "size": 1}, "[FILE] b.pyc 2b"]
        assert _parse_remote_files(items, ["*.pyc"]) == {}


class TestWalkLocal:
    def test_flat_and_recursive(self, tmp_path: Path):
        (tmp_path / "top.txt").write_text("top")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "nested.txt").write_text("nested")
        (sub / "skip.pyc").write_text("x")

        flat = _walk_local_files(tmp_path, False, [])
        assert set(flat) == {"top.txt"}

        rec = _walk_local_files(tmp_path, True, ["*.pyc"])
        assert set(rec) == {"top.txt", "sub/nested.txt"}


class TestDiffMaps:
    def test_categories(self):
        local = {
            "only.txt": {"size": 1, "mtime": 1},
            "newer.txt": {"size": 2, "mtime": 10},
            "older.txt": {"size": 3, "mtime": 1},
            "diff.txt": {"size": 4, "mtime": 1},
            "same.txt": {"size": 5, "mtime": 1},
        }
        remote = {
            "newer.txt": {"size": 2, "mtime": 2},
            "older.txt": {"size": 3, "mtime": 9},
            "diff.txt": {"size": 99, "mtime": 1},
            "same.txt": {"size": 5, "mtime": 1},
            "remote_only.txt": {"size": 6, "mtime": 1},
        }
        d = _diff_file_maps(local, remote)
        assert d["only_local"] == ["only.txt"]
        assert d["only_remote"] == ["remote_only.txt"]
        assert d["newer_local"] == ["newer.txt"]
        assert d["newer_remote"] == ["older.txt"]
        assert [e["file"] for e in d["size_mismatch"]] == ["diff.txt"]
        assert d["identical"] == ["same.txt"]


class TestSha256:
    def test_known_digest(self, tmp_path: Path):
        f = tmp_path / "hello.txt"
        f.write_bytes(b"hello")
        assert _sha256_file(f) == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
