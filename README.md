# Tesla Pack Monitor

DIY diagnostic tool for **Classic Tesla Model S / X** battery packs (2012 – early 2021).

Target vehicle: **2015 Model S 85D**

**Project guide:** [https://tpm.5udyk.com/](https://tpm.5udyk.com/)

This repository is **private** for now.

## Current features

| Option | Description |
|--------|-------------|
| *(default)* / `--demo` | Synthetic `0x6F2` sample data |
| `--log FILE` | Decode a candump-style capture |
| `--can INTERFACE` | Live SocketCAN listener at 500 kbit/s (Linux) |
| `--json` | Print a JSON summary instead of the table |
| `--weak N` | How many weakest bricks to include (default: 5) |
| `--report FILENAME` | Save the human-readable summary to a file |

## Quick start

```bash
cd ~/Developer/tesla-pack-monitor

# One-time setup
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Run via the helper script (sets PYTHONPATH for you)
./tpm
./tpm --json
./tpm --weak 10
./tpm --report scan.txt
./tpm --log capture.log
./tpm --log capture.log --json --report scan.txt
./tpm --can can0          # Linux + SocketCAN hardware/vcan
```

## Project structure

```
tpm                 # executable CLI helper (./tpm …)
src/tesla_bms/
├── models.py       # Brick, Module, PackState
├── decoder.py      # 0x6F2 / 0x102 CAN decoders
├── candump.py      # candump-style log parser
├── live.py         # SocketCAN live capture
├── cli.py          # command-line interface
└── __init__.py
tests/
hardware/           # assembly notes / pinouts (planned)
docs/
```

## Candump log format

```text
(123.456) can0 6F2#0011223344556677
can0 6F2#0011223344556677
```

Only frames with ID `0x6F2` are used.

## Hardware (planned)

- Radxa Zero 3W (4 GB + 32 GB eMMC)
- Waveshare 2-Channel Isolated CAN HAT
- 2.4" SPI TFT (ILI9341)
- External 12 mm metal buttons
- Tesla BMS harness `1041309-00-F`
- Clear IP67 enclosure

## Roadmap

- [x] Core data model + `0x6F2` decoder
- [x] CLI: demo, `--log`, `--can`, `--json`, `--weak`, `--report`
- [ ] Display + button UI
- [ ] SoftAP web dashboard

## License

Private project – all rights reserved.
