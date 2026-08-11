# Tesla Pack Monitor

DIY standalone diagnostic tool for **Classic Tesla Model S / X** battery packs (2012 – early 2021).

Target vehicle: **2015 Model S 85D**

## Features (planned)

- Read all 96 brick voltages and 32 module temperatures via CAN (`0x6F2`)
- Calculate imbalance, identify weak modules/bricks
- Local 2.4" display + physical buttons (standalone operation)
- Optional SoftAP web dashboard
- Report generation similar to commercial TPM tools

## Hardware

- Radxa Zero 3W (4 GB + 32 GB eMMC)
- Waveshare 2-Channel Isolated CAN HAT
- 2.4" SPI TFT (ILI9341)
- External 12 mm metal buttons
- Tesla BMS harness `1041309-00-F`
- Clear IP67 enclosure

See `hardware/` for assembly notes and pinouts.

## Project Structure

```
src/tesla_bms/
├── models.py      # Brick, Module, PackState data model
├── decoder.py     # 0x6F2 and 0x102 CAN frame decoders
├── candump.py     # candump-style log parser
├── cli.py         # CLI (demo + --log)
└── __init__.py

tests/
hardware/
docs/
```

## Quick Start (development)

The package lives under `src/`, so you need either an editable install or `PYTHONPATH=src`.

```bash
cd ~/Developer/tesla-pack-monitor

# One-time setup (recommended)
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Demo summary (synthetic 0x6F2 frames)
python -m tesla_bms
# or after install:
tpm
tpm --demo

# Decode a candump-style capture
tpm --log capture.log
```

Without installing, you can still run:

```bash
PYTHONPATH=src python3 -m tesla_bms
PYTHONPATH=src python3 -m tesla_bms --log capture.log
```

### Candump log format

Lines like:

```text
(123.456) can0 6F2#0011223344556677
can0 6F2#0011223344556677
```

Only frames with ID `0x6F2` are used. Other IDs and blank/comment lines are ignored.

## Status

- [x] Core data model
- [x] 0x6F2 brick voltage + temperature decoder
- [x] CLI demo mode + candump `--log` support
- [ ] SocketCAN live listener
- [ ] Display + button UI
- [ ] Report generation
- [ ] SoftAP web dashboard

## License

Private project – all rights reserved.
