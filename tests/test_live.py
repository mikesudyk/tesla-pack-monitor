"""
Tests for live SocketCAN helpers and CLI --can error handling.

Run with:
    python -m pytest tests/test_live.py
or:
    python tests/test_live.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tesla_bms.cli import main
from tesla_bms.live import (
    FRAME_ID_6F2,
    CanInterfaceError,
    apply_message,
    collect_pack_state,
    open_bus,
)
from tesla_bms.models import PackState


def test_apply_message_filters_non_6f2():
    state = PackState()
    other = SimpleNamespace(
        arbitration_id=0x102,
        data=bytes(8),
        is_error_frame=False,
        is_remote_frame=False,
    )
    assert apply_message(other, state) is False

    good = SimpleNamespace(
        arbitration_id=FRAME_ID_6F2,
        data=bytes(8),
        is_error_frame=False,
        is_remote_frame=False,
    )
    assert apply_message(good, state) is True


def test_open_bus_wraps_failure():
    fake_can = MagicMock()
    fake_can.Bus.side_effect = OSError("No such device")

    with patch.dict(sys.modules, {"can": fake_can}):
        # Force re-import path: open_bus imports can inside the function
        try:
            open_bus("can0")
            assert False, "expected CanInterfaceError"
        except CanInterfaceError as exc:
            assert "can0" in str(exc)
            assert "No such device" in str(exc)


def test_collect_pack_state_with_mock_bus():
    payloads = [bytes([i]) + bytes(7) for i in range(32)]

    class FakeMsg:
        def __init__(self, data: bytes):
            self.arbitration_id = FRAME_ID_6F2
            self.data = data
            self.is_error_frame = False
            self.is_remote_frame = False

    bus = MagicMock()
    bus.recv.side_effect = [FakeMsg(p) for p in payloads]
    bus.set_filters = MagicMock()
    bus.shutdown = MagicMock()

    with patch("tesla_bms.live.open_bus", return_value=bus):
        state, count, indexes = collect_pack_state("can0", timeout=5.0)

    assert count == 32
    assert len(indexes) == 32
    assert bus.shutdown.called
    assert state is not None


def test_cli_can_missing_interface_returns_1():
    with patch(
        "tesla_bms.cli.collect_pack_state",
        side_effect=CanInterfaceError("Could not open CAN interface 'can0'"),
    ):
        code = main(["--can", "can0"])
    assert code == 1


def test_cli_rejects_can_and_log_together():
    try:
        main(["--can", "can0", "--log", "x.log"])
        assert False, "expected SystemExit from argparse"
    except SystemExit as exc:
        assert exc.code == 2


if __name__ == "__main__":
    test_apply_message_filters_non_6f2()
    test_open_bus_wraps_failure()
    test_collect_pack_state_with_mock_bus()
    test_cli_can_missing_interface_returns_1()
    test_cli_rejects_can_and_log_together()
    print("All live tests passed.")
