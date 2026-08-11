"""
CAN frame decoders for Classic Tesla Model S/X BMS.

Primary message: 0x6F2
  - Indexes 0-23  → 96 brick voltages
  - Indexes 24-31 → 32 temperatures

Also includes a simple 0x102 helper for pack voltage.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from .models import (
    NUM_BRICKS,
    NUM_TEMPS,
    PackState,
)


# Scaling factors (community / OVMS consensus)
VOLTAGE_SCALE = 0.000305          # volts per raw count
TEMP_SCALE = 0.0122               # °C per raw count
INVALID_RAW = 0x3FFF


def _extract_four_14bit(data: bytes) -> Tuple[int, int, int, int]:
    """
    Extract four 14-bit values from a 0x6F2 frame.

    data must be the full 8-byte payload:
      byte 0 = index
      bytes 1-7 = packed values
    """
    if len(data) < 8:
        raise ValueError("0x6F2 frame must be 8 bytes")

    d = data
    v1 = ((d[2] & 0x3F) << 8) | d[1]
    v2 = ((d[4] & 0x0F) << 10) | (d[3] << 2) | (d[2] >> 6)
    v3 = ((d[6] & 0x03) << 12) | (d[5] << 4) | (d[4] >> 4)
    v4 = (d[7] << 6) | (d[6] >> 2)
    return v1, v2, v3, v4


def _to_signed_14(raw: int) -> int:
    """Convert 14-bit two's-complement value to a Python signed int."""
    if raw & 0x2000:          # sign bit set
        return raw - 0x4000
    return raw


def decode_0x6F2_frame(data: bytes, state: PackState) -> None:
    """
    Decode one 0x6F2 frame and update PackState in-place.

    Parameters
    ----------
    data : bytes
        8-byte CAN payload (byte 0 = index, bytes 1-7 = data)
    state : PackState
        Pack state object to update
    """
    if len(data) != 8:
        return

    index = data[0]
    if index > 31:
        return

    v1, v2, v3, v4 = _extract_four_14bit(data)
    values = [v1, v2, v3, v4]

    if index < 24:
        # Brick voltages (indexes 0-23)
        base = index * 4
        for i, raw in enumerate(values):
            brick_idx = base + i
            if brick_idx >= NUM_BRICKS:
                continue
            if raw == 0 or raw == INVALID_RAW:
                state.bricks[brick_idx].voltage = None
            else:
                state.bricks[brick_idx].voltage = raw * VOLTAGE_SCALE
    else:
        # Temperatures (indexes 24-31)
        base = (index - 24) * 4
        for i, raw in enumerate(values):
            temp_idx = base + i
            if temp_idx >= NUM_TEMPS:
                continue
            if raw == 0 or raw == INVALID_RAW:
                state.temperatures[temp_idx] = None
            else:
                signed = _to_signed_14(raw)
                state.temperatures[temp_idx] = signed * TEMP_SCALE


def decode_0x102_frame(data: bytes, state: PackState) -> None:
    """
    Best-effort decode of the pack voltage/current message (0x102).

    This is based on public reverse-engineering and may need refinement
    once live data is available.
    """
    if len(data) < 2:
        return

    # Pack voltage – bytes 0-1, little-endian, scale 0.01 V
    raw_v = data[0] | (data[1] << 8)
    state.pack_voltage = raw_v / 100.0


def update_from_6F2_frames(
    frames: List[bytes],
    state: Optional[PackState] = None,
) -> PackState:
    """
    Convenience helper: feed a list of 0x6F2 payloads and return updated state.
    """
    if state is None:
        state = PackState()
    for frame in frames:
        decode_0x6F2_frame(frame, state)
    return state


# ---------------------------------------------------------------------------
# Simple self-test when run directly
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    pack = PackState()

    # Structural example only – replace with real frames later
    example = bytes([
        0x00,             # index 0
        0xA0, 0x0F,
        0x00, 0x00,
        0x00, 0x00, 0x00,
    ])
    decode_0x6F2_frame(example, pack)

    print(pack.summary())
    print("\nFirst module:")
    for b in pack.modules()[0].bricks:
        print(f"  {b}")
