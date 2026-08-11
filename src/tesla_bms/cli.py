#!/usr/bin/env python3
"""
Command-line interface for Tesla Pack Monitor.

Usage:
    python -m tesla_bms                # run demo with sample data
    python -m tesla_bms --demo         # same as above
    python -m tesla_bms --log capture.log
    python -m tesla_bms --can can0
    python -m tesla_bms --help
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from .candump import load_6F2_frames_from_log
from .decoder import update_from_6F2_frames
from .live import CanInterfaceError, collect_pack_state
from .models import PackState


def _make_sample_frames() -> List[bytes]:
    """
    Generate a realistic-looking set of 0x6F2 frames for demonstration.

    Creates a pack with mild imbalance so the summary is interesting.
    These are synthetic — replace with real captured frames later.
    """
    frames: List[bytes] = []

    # Helper to pack four 14-bit values into the 7 data bytes
    def pack_values(v1: int, v2: int, v3: int, v4: int) -> bytes:
        # Reverse of _extract_four_14bit
        b1 = v1 & 0xFF
        b2 = ((v1 >> 8) & 0x3F) | ((v2 & 0x03) << 6)
        b3 = (v2 >> 2) & 0xFF
        b4 = ((v2 >> 10) & 0x0F) | ((v3 & 0x0F) << 4)
        b5 = (v3 >> 4) & 0xFF
        b6 = ((v3 >> 12) & 0x03) | ((v4 & 0x3F) << 2)
        b7 = (v4 >> 6) & 0xFF
        return bytes([b1, b2, b3, b4, b5, b6, b7])

    # Base voltage ~3.90 V → raw ≈ 3.90 / 0.000305 ≈ 12787
    base = 12787

    # Create 24 voltage frames (indexes 0-23) with slight variation
    for idx in range(24):
        # Introduce a few weaker bricks for demo purposes
        offsets = [0, 0, 0, 0]
        if idx == 3:          # bricks 12-15 a bit low
            offsets = [-180, -220, -150, -90]
        if idx == 11:         # bricks 44-47 low
            offsets = [-300, -280, -310, -250]
        if idx == 18:         # bricks 72-75 slightly high
            offsets = [80, 60, 90, 70]

        vals = [base + o for o in offsets]
        data = bytes([idx]) + pack_values(*vals)
        frames.append(data)

    # Create 8 temperature frames (indexes 24-31) ~ 25-32 °C
    # raw = temp / 0.0122
    for i, idx in enumerate(range(24, 32)):
        t_base = int(28.0 / 0.0122)          # ~28 °C
        temps = [
            t_base + (i * 3),
            t_base + 15 + (i * 2),
            t_base - 10,
            t_base + 8,
        ]
        data = bytes([idx]) + pack_values(*temps)
        frames.append(data)

    return frames


def print_summary(state: PackState) -> None:
    """Pretty-print a full pack summary to stdout."""
    print()
    print("╔══════════════════════════════════════════════════╗")
    print("║           TESLA PACK MONITOR – SUMMARY           ║")
    print("╚══════════════════════════════════════════════════╝")
    print()

    # Top-level metrics
    print(state.summary())
    print()

    # Weakest / strongest bricks
    weakest = state.weakest_bricks(5)
    strongest = state.strongest_bricks(3)

    if weakest:
        print("── Weakest bricks ──────────────────────────────")
        for b in weakest:
            print(f"  {b}")
        print()

    if strongest:
        print("── Strongest bricks ────────────────────────────")
        for b in strongest:
            print(f"  {b}")
        print()

    # Per-module overview
    print("── Module overview ─────────────────────────────")
    print(f"{'Mod':<4} {'Avg V':>8} {'Min V':>8} {'Max V':>8} {'Imb mV':>8}  Temps")
    print("-" * 58)

    for mod in state.modules():
        avg = mod.avg_voltage()
        mn = mod.min_voltage()
        mx = mod.max_voltage()
        imb = mod.imbalance_mV()

        avg_s = f"{avg:.4f}" if avg is not None else "  —"
        mn_s = f"{mn:.4f}" if mn is not None else "  —"
        mx_s = f"{mx:.4f}" if mx is not None else "  —"
        imb_s = f"{imb:6.1f}" if imb is not None else "   —"

        temps = []
        for t in mod.temperatures:
            if t is not None:
                temps.append(f"{t:.1f}°C")
            else:
                temps.append("—")
        temp_s = "  ".join(temps)

        print(f"{mod.index:<4} {avg_s:>8} {mn_s:>8} {mx_s:>8} {imb_s:>8}  {temp_s}")

    print()


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tesla-bms",
        description="Tesla Classic Model S/X Pack Monitor CLI",
        epilog=(
            "Examples:\n"
            "  tesla-bms --demo\n"
            "  tesla-bms --log capture.log\n"
            "  tesla-bms --can can0\n"
            "\n"
            "Log format (candump-style):\n"
            "  (123.456) can0 6F2#0011223344556677\n"
            "  can0 6F2#0011223344556677\n"
            "\n"
            "Live CAN uses SocketCAN at 500 kbit/s and listens for 0x6F2.\n"
            "Requires a Linux SocketCAN interface (not available on macOS\n"
            "without extra hardware / virtual CAN setup)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "--demo",
        action="store_true",
        help="Run with built-in sample data (default if no --log/--can)",
    )
    source.add_argument(
        "--log",
        metavar="FILE",
        help="Decode 0x6F2 frames from a candump-style log file",
    )
    source.add_argument(
        "--can",
        metavar="INTERFACE",
        help="Listen live on SocketCAN INTERFACE at 500 kbit/s for 0x6F2",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version and exit",
    )

    args = parser.parse_args(argv)

    if args.version:
        from . import __version__
        print(f"tesla-bms {__version__}")
        return 0

    if args.log:
        try:
            frames = load_6F2_frames_from_log(Path(args.log))
        except FileNotFoundError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        except OSError as exc:
            print(f"error: could not read log file: {exc}", file=sys.stderr)
            return 1

        print(f"Loaded {len(frames)} 0x6F2 frame(s) from {args.log}")
        state = update_from_6F2_frames(frames)
        print_summary(state)
        return 0

    if args.can:
        try:
            state, count, indexes = collect_pack_state(args.can)
        except CanInterfaceError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

        print(
            f"Collected {count} 0x6F2 frame(s) "
            f"covering {len(indexes)} index(es) from {args.can}"
        )
        print_summary(state)
        return 0

    # Default / --demo: synthetic sample frames
    print("Loading sample 0x6F2 frames (demo mode)...")
    frames = _make_sample_frames()
    state = update_from_6F2_frames(frames)
    print_summary(state)

    return 0


if __name__ == "__main__":
    sys.exit(main())
