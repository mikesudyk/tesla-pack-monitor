"""
Basic tests for the 0x6F2 decoder.

Run with:
    python -m pytest tests/
or simply:
    python tests/test_decoder.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running the test file directly without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tesla_bms.models import PackState, NUM_BRICKS, NUM_TEMPS
from tesla_bms.decoder import decode_0x6F2_frame, _extract_four_14bit, _to_signed_14


def test_extract_four_14bit_basic():
    # Minimal smoke test – just ensure the function runs and returns four ints
    data = bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    v1, v2, v3, v4 = _extract_four_14bit(data)
    assert isinstance(v1, int)
    assert isinstance(v2, int)
    assert isinstance(v3, int)
    assert isinstance(v4, int)


def test_signed_14bit():
    assert _to_signed_14(0x0000) == 0
    assert _to_signed_14(0x0001) == 1
    assert _to_signed_14(0x1FFF) == 8191          # max positive
    assert _to_signed_14(0x2000) == -8192         # min negative
    assert _to_signed_14(0x3FFF) == -1


def test_decode_empty_frame_does_not_crash():
    state = PackState()
    decode_0x6F2_frame(b"", state)                # too short
    decode_0x6F2_frame(bytes([0x00] * 8), state)  # valid length
    assert len(state.bricks) == NUM_BRICKS
    assert len(state.temperatures) == NUM_TEMPS


def test_pack_state_helpers():
    state = PackState()
    # Manually set a couple of voltages
    state.bricks[0].voltage = 3.900
    state.bricks[1].voltage = 3.850
    state.bricks[2].voltage = 3.920

    assert abs(state.min_brick_voltage() - 3.850) < 1e-6
    assert abs(state.max_brick_voltage() - 3.920) < 1e-6
    assert abs(state.imbalance_mV() - 70.0) < 1e-3

    weakest = state.weakest_bricks(1)
    assert weakest[0].index == 1


if __name__ == "__main__":
    test_extract_four_14bit_basic()
    test_signed_14bit()
    test_decode_empty_frame_does_not_crash()
    test_pack_state_helpers()
    print("All basic tests passed.")
