"""
Parse simple candump-style CAN log lines.

Supported formats:
    (123.456) can0 6F2#0011223344556677
    can0 6F2#0011223344556677
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

# Optional absolute timestamp, interface, then ID#hexdata
_CANDUMP_RE = re.compile(
    r"^(?:\([\d.]+\)\s+)?"          # optional (timestamp)
    r"(?P<iface>\S+)\s+"            # can0, vcan0, …
    r"(?P<can_id>[0-9A-Fa-f]+)"     # arbitration ID (hex)
    r"#(?P<data>[0-9A-Fa-f]+)"      # payload as contiguous hex
    r"\s*$"
)

FRAME_ID_6F2 = 0x6F2


def parse_candump_line(line: str) -> Optional[Tuple[int, bytes]]:
    """
    Parse one candump-style line.

    Returns
    -------
    (can_id, payload) or None if the line is blank, a comment, or not matched.
    """
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None

    match = _CANDUMP_RE.match(stripped)
    if not match:
        return None

    can_id = int(match.group("can_id"), 16)
    hex_data = match.group("data")
    if len(hex_data) % 2 != 0:
        return None

    try:
        payload = bytes.fromhex(hex_data)
    except ValueError:
        return None

    return can_id, payload


def iter_6F2_frames(lines: Iterable[str]) -> List[bytes]:
    """Return 0x6F2 payloads (8-byte frames preferred; others still returned)."""
    frames: List[bytes] = []
    for line in lines:
        parsed = parse_candump_line(line)
        if parsed is None:
            continue
        can_id, payload = parsed
        if can_id == FRAME_ID_6F2:
            frames.append(payload)
    return frames


def load_6F2_frames_from_log(path: Path | str) -> List[bytes]:
    """
    Read a candump log file and return all 0x6F2 payloads.

    Raises
    ------
    FileNotFoundError
        If the path does not exist.
    ValueError
        If the file contains no 0x6F2 frames.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Log file not found: {path}")

    with path.open("r", encoding="utf-8", errors="replace") as fh:
        frames = iter_6F2_frames(fh)

    if not frames:
        raise ValueError(f"No 0x6F2 frames found in {path}")

    return frames
