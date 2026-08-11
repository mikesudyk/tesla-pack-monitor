"""
Tests for JSON summary and --weak CLI options.
"""

from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tesla_bms.cli import main, summary_dict
from tesla_bms.decoder import update_from_6F2_frames
from tesla_bms.cli import _make_sample_frames


def test_summary_dict_shape():
    state = update_from_6F2_frames(_make_sample_frames())
    data = summary_dict(state, weak=3)

    assert "avg_voltage" in data
    assert "min_voltage" in data
    assert "max_voltage" in data
    assert "imbalance_mV" in data
    assert len(data["weakest_bricks"]) == 3
    assert set(data["weakest_bricks"][0]) == {"index", "module", "voltage"}
    assert len(data["modules"]) == 16
    assert "temperatures" in data["modules"][0]
    assert data["valid_bricks"] == 96


def test_cli_json_stdout_is_pure_json():
    buf = StringIO()
    with patch("sys.stdout", buf):
        code = main(["--json", "--weak", "2"])
    assert code == 0
    data = json.loads(buf.getvalue())
    assert len(data["weakest_bricks"]) == 2
    assert data["imbalance_mV"] is not None


def test_cli_weak_in_human_mode():
    buf = StringIO()
    with patch("sys.stdout", buf):
        code = main(["--weak", "10"])
    assert code == 0
    text = buf.getvalue()
    assert "Weakest bricks" in text
    # Demo has more than 5 weakish bricks listed when --weak 10
    assert "Brick" in text


def test_cli_weak_negative_rejected():
    code = main(["--weak", "-1"])
    assert code == 2


def test_cli_report_writes_file():
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scan.txt"
        buf = StringIO()
        with patch("sys.stdout", buf):
            code = main(["--report", str(path), "--weak", "3"])
        assert code == 0
        assert path.is_file()
        text = path.read_text(encoding="utf-8")
        assert "TESLA PACK MONITOR" in text
        assert "Weakest bricks" in text
        assert "Report saved to" in buf.getvalue()


def test_cli_report_with_json_keeps_stdout_json():
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scan.txt"
        buf = StringIO()
        with patch("sys.stdout", buf):
            code = main(["--json", "--report", str(path)])
        assert code == 0
        data = json.loads(buf.getvalue())
        assert "imbalance_mV" in data
        assert "TESLA PACK MONITOR" in path.read_text(encoding="utf-8")


def test_cli_report_bad_path_returns_1():
    # Directory that does not exist → OSError when writing
    code = main(["--report", "/no/such/dir/scan.txt"])
    assert code == 1


if __name__ == "__main__":
    test_summary_dict_shape()
    test_cli_json_stdout_is_pure_json()
    test_cli_weak_in_human_mode()
    test_cli_weak_negative_rejected()
    test_cli_report_writes_file()
    test_cli_report_with_json_keeps_stdout_json()
    test_cli_report_bad_path_returns_1()
    print("All JSON/weak/report tests passed.")
