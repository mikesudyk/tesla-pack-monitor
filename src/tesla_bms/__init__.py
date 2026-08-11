"""
Tesla Classic Model S/X BMS tools.

Target: 2012 – early 2021 packs (16 modules, 96 bricks, 32 temperatures).
"""

from .models import Brick, Module, PackState
from .decoder import decode_0x6F2_frame, decode_0x102_frame, update_from_6F2_frames

__all__ = [
    "Brick",
    "Module",
    "PackState",
    "decode_0x6F2_frame",
    "decode_0x102_frame",
    "update_from_6F2_frames",
]

__version__ = "0.2.0"
