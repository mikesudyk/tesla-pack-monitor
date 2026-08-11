"""
Tests for candump-style log parsing and CLI --log handling.

Run with:
    python -m pytest tests/
or:
    python tests/test_candump.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tesla_bms.candump import (
    iter_6F2_frames,
    load_6F2_frames_from_log,
    parse_candump_line,
)
from tesla_bms.cli import main


def test_parse_with_timestamp():
    result = parse_candump_line("(123.456) can0 6F2#0011223344556677")
    assert result is not None
    can_id, payload = result
    assert can_id == 0x6F2
    assert payload == bytes.fromhex("0011223344556677")


def test_parse_without_timestamp():
    result = parse_candump_line("can0 6F2#AABBCCDDEEFF0011")
    assert result is not None
    can_id, payload = result
    assert can_id == 0x6F2
    assert payload == bytes.fromhex("AABBCCDDEEFF0011")


def test_parse_ignores_other_ids_and_junk():
    assert parse_candump_line("") is None
    assert parse_candump_line("# comment") is None
    assert parse_candump_line("not a can line") is None

    other = parse_candump_line("can0 102#0102")
    assert other is not None
    assert other[0] == 0x102


def test_iter_filters_6F2_only():
    lines = [
        "(1.0) can0 6F2#0001020304050607",
        "can0 102#AABB",
        "can0 6F2#08090A0B0C0D0E0F",
        "",
        "# ignore me",
    ]
    frames = iter_6F2_frames(lines)
    assert len(frames) == 2
    assert frames[0] == bytes.fromhex("0001020304050607")
    assert frames[1] == bytes.fromhex("08090A0B0C0D0E0F")


def test_load_file_and_errors():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "capture.log"
        path.write_text(
            "(0.1) can0 102#0000\n"
            "(0.2) can0 6F2#0001020304050607\n",
            encoding="utf-8",
        )
        frames = load_6F2_frames_from_log(path)
        assert len(frames) == 1

        empty = Path(tmp) / "empty.log"
        empty.write_text("can0 102#0000\n", encoding="utf-8")
        try:
            load_6F2_frames_from_log(empty)
            assert False, "expected ValueError"
        except ValueError:
            pass

        try:
            load_6F2_frames_from_log(Path(tmp) / "missing.log")
            assert False, "expected FileNotFoundError"
        except FileNotFoundError:
            pass


def test_cli_log_missing_file_returns_1():
    code = main(["--log", "/tmp/definitely-does-not-exist-tpm.log"])
    assert code == 1


def test_cli_log_no_6f2_returns_1():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "other.log"
        path.write_text("can0 102#0102\n", encoding="utf-8")
        code = main(["--log", str(path)])
        assert code == 1


def test_cli_log_success():
    # One voltage frame (index 0) with packed zeros — enough to exercise the path
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "ok.log"
        path.write_text("can0 6F2#0000000000000000\n", encoding="utf-8")
        code = main(["--log", str(path)])
        assert code == 0


if __name__ == "__main__":
    test_parse_with_timestamp()
    test_parse_without_timestamp()
    test_parse_ignores_other_ids_and_junk()
    test_iter_filters_6F2_only()
    test_load_file_and_errors()
    test_cli_log_missing_file_returns_1()
    test_cli_log_no_6f2_returns_1()
    test_cli_log_success()
    print("All candump tests passed.")
