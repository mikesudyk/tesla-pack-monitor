"""
Live SocketCAN capture for Classic Tesla 0x6F2 frames.

One-shot helper for the CLI today; open_bus / apply_message are kept
separate so a future continuous/live UI can reuse the same pieces.
"""

from __future__ import annotations

import time
from typing import Optional, Set

from .decoder import decode_0x6F2_frame
from .models import PackState

FRAME_ID_6F2 = 0x6F2
DEFAULT_BITRATE = 500_000
DEFAULT_TIMEOUT_S = 10.0
# Indexes 0-23 voltages + 24-31 temperatures → full pack refresh
EXPECTED_INDEXES = 32


class CanInterfaceError(RuntimeError):
    """Raised when the CAN interface cannot be opened or used."""


def open_bus(
    channel: str,
    *,
    bitrate: int = DEFAULT_BITRATE,
    interface: str = "socketcan",
):
    """
    Open a python-can bus.

    Raises
    ------
    CanInterfaceError
        If python-can is missing or the interface cannot be opened
        (common on macOS / machines without SocketCAN hardware).
    """
    try:
        import can
    except ImportError as exc:
        raise CanInterfaceError(
            "python-can is required for --can; install with: pip install python-can"
        ) from exc

    try:
        bus = can.Bus(
            channel=channel,
            interface=interface,
            bitrate=bitrate,
        )
    except Exception as exc:  # OSError, CanError, etc. vary by platform
        raise CanInterfaceError(
            f"Could not open CAN interface {channel!r} "
            f"({interface}, {bitrate} bit/s): {exc}"
        ) from exc

    try:
        bus.set_filters(
            [{"can_id": FRAME_ID_6F2, "can_mask": 0x7FF, "extended": False}]
        )
    except Exception:
        # Filtering is optional; we still filter in software below.
        pass

    return bus


def apply_message(msg, state: PackState) -> bool:
    """
    Apply one python-can Message to state if it is 0x6F2.

    Returns True if the message was consumed.
    """
    if msg is None:
        return False
    if getattr(msg, "is_error_frame", False) or getattr(msg, "is_remote_frame", False):
        return False
    if int(msg.arbitration_id) != FRAME_ID_6F2:
        return False

    data = bytes(msg.data)
    decode_0x6F2_frame(data, state)
    return True


def collect_pack_state(
    channel: str,
    *,
    bitrate: int = DEFAULT_BITRATE,
    timeout: float = DEFAULT_TIMEOUT_S,
    expected_indexes: int = EXPECTED_INDEXES,
    state: Optional[PackState] = None,
) -> tuple[PackState, int, Set[int]]:
    """
    Listen until enough distinct 0x6F2 indexes arrive, timeout, or Ctrl+C.

    Returns
    -------
    (state, frame_count, seen_indexes)

    Raises
    ------
    CanInterfaceError
        If the bus cannot be opened.
    KeyboardInterrupt
        Propagated only if no frames were collected; otherwise swallowed
        after a partial capture (caller prints summary).
    """
    if state is None:
        state = PackState()

    bus = open_bus(channel, bitrate=bitrate)
    frame_count = 0
    seen_indexes: Set[int] = set()
    deadline = time.monotonic() + timeout
    interrupted = False

    try:
        print(
            f"Listening on {channel} for 0x6F2 "
            f"(timeout {timeout:.0f}s, Ctrl+C to stop early)..."
        )
        while time.monotonic() < deadline:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                msg = bus.recv(timeout=min(0.25, remaining))
            except KeyboardInterrupt:
                interrupted = True
                break

            if not apply_message(msg, state):
                continue

            frame_count += 1
            data = bytes(msg.data)
            if len(data) == 8:
                seen_indexes.add(data[0])

            if len(seen_indexes) >= expected_indexes:
                break
    except KeyboardInterrupt:
        interrupted = True
    finally:
        try:
            bus.shutdown()
        except Exception:
            pass

    if interrupted:
        print("Interrupted — using frames collected so far.")

    if frame_count == 0:
        raise CanInterfaceError(
            f"No 0x6F2 frames received on {channel!r} "
            f"within {timeout:.0f}s"
        )

    return state, frame_count, seen_indexes
