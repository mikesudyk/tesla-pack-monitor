"""
Data model for Classic Tesla Model S/X battery packs.

Architecture:
  - 16 modules
  - 6 bricks per module → 96 bricks total
  - 2 temperature sensors per module → 32 temperatures total
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


NUM_MODULES = 16
BRICKS_PER_MODULE = 6
NUM_BRICKS = NUM_MODULES * BRICKS_PER_MODULE          # 96
TEMPS_PER_MODULE = 2
NUM_TEMPS = NUM_MODULES * TEMPS_PER_MODULE            # 32


@dataclass
class Brick:
    """Single brick (parallel group of cells)."""
    index: int                          # 0 … 95
    voltage: Optional[float] = None     # volts

    @property
    def module(self) -> int:
        return self.index // BRICKS_PER_MODULE

    @property
    def position_in_module(self) -> int:
        return self.index % BRICKS_PER_MODULE

    def __str__(self) -> str:
        v = f"{self.voltage:.4f} V" if self.voltage is not None else "—"
        return f"Brick {self.index:02d} (M{self.module}) {v}"


@dataclass
class Module:
    """One of the 16 modules in the pack."""
    index: int
    bricks: List[Brick] = field(default_factory=list)
    temperatures: List[Optional[float]] = field(default_factory=list)  # °C

    def avg_voltage(self) -> Optional[float]:
        vals = [b.voltage for b in self.bricks if b.voltage is not None]
        return sum(vals) / len(vals) if vals else None

    def min_voltage(self) -> Optional[float]:
        vals = [b.voltage for b in self.bricks if b.voltage is not None]
        return min(vals) if vals else None

    def max_voltage(self) -> Optional[float]:
        vals = [b.voltage for b in self.bricks if b.voltage is not None]
        return max(vals) if vals else None

    def imbalance_mV(self) -> Optional[float]:
        mn, mx = self.min_voltage(), self.max_voltage()
        if mn is None or mx is None:
            return None
        return (mx - mn) * 1000.0

    def __str__(self) -> str:
        avg = self.avg_voltage()
        imb = self.imbalance_mV()
        avg_s = f"{avg:.4f} V" if avg is not None else "—"
        imb_s = f"{imb:.1f} mV" if imb is not None else "—"
        return f"Module {self.index:02d}  avg={avg_s}  imbalance={imb_s}"


@dataclass
class PackState:
    """Complete snapshot of a Classic Model S/X pack."""

    bricks: List[Brick] = field(default_factory=list)
    temperatures: List[Optional[float]] = field(default_factory=list)  # 32 values
    pack_voltage: Optional[float] = None      # from 0x102 if available
    pack_current: Optional[float] = None
    timestamp: Optional[float] = None

    def __post_init__(self) -> None:
        if not self.bricks:
            self.bricks = [Brick(i) for i in range(NUM_BRICKS)]
        if not self.temperatures:
            self.temperatures = [None] * NUM_TEMPS

    # ------------------------------------------------------------------
    # Derived metrics
    # ------------------------------------------------------------------

    def valid_voltages(self) -> List[float]:
        return [b.voltage for b in self.bricks if b.voltage is not None]

    def min_brick_voltage(self) -> Optional[float]:
        vals = self.valid_voltages()
        return min(vals) if vals else None

    def max_brick_voltage(self) -> Optional[float]:
        vals = self.valid_voltages()
        return max(vals) if vals else None

    def avg_brick_voltage(self) -> Optional[float]:
        vals = self.valid_voltages()
        return sum(vals) / len(vals) if vals else None

    def imbalance_mV(self) -> Optional[float]:
        mn = self.min_brick_voltage()
        mx = self.max_brick_voltage()
        if mn is None or mx is None:
            return None
        return (mx - mn) * 1000.0

    def weakest_bricks(self, n: int = 5) -> List[Brick]:
        valid = [b for b in self.bricks if b.voltage is not None]
        return sorted(valid, key=lambda b: b.voltage)[:n]

    def strongest_bricks(self, n: int = 5) -> List[Brick]:
        valid = [b for b in self.bricks if b.voltage is not None]
        return sorted(valid, key=lambda b: b.voltage, reverse=True)[:n]

    def modules(self) -> List[Module]:
        result = []
        for m in range(NUM_MODULES):
            start = m * BRICKS_PER_MODULE
            bricks = self.bricks[start : start + BRICKS_PER_MODULE]
            temps = self.temperatures[m * TEMPS_PER_MODULE : (m + 1) * TEMPS_PER_MODULE]
            result.append(Module(index=m, bricks=bricks, temperatures=temps))
        return result

    def summary(self) -> str:
        lines = ["=== Pack Summary ==="]
        if self.pack_voltage is not None:
            lines.append(f"Pack voltage : {self.pack_voltage:.2f} V")
        avg = self.avg_brick_voltage()
        mn = self.min_brick_voltage()
        mx = self.max_brick_voltage()
        imb = self.imbalance_mV()
        if avg is not None:
            lines.append(f"Avg brick    : {avg:.4f} V")
        if mn is not None and mx is not None:
            lines.append(f"Min / Max    : {mn:.4f} V  /  {mx:.4f} V")
        if imb is not None:
            lines.append(f"Imbalance    : {imb:.1f} mV")
        lines.append(f"Valid bricks : {len(self.valid_voltages())} / {NUM_BRICKS}")
        return "\n".join(lines)
