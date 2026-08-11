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
└── __init__.py

tests/
hardware/
docs/
```

## Quick Start (development)

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate          # Linux/macOS
# .venv\Scripts\activate           # Windows

pip install -r requirements.txt

# Run basic self-test
python -m tesla_bms.decoder
```

## Status

- [x] Core data model
- [x] 0x6F2 brick voltage + temperature decoder
- [ ] Mock / simulator (optional)
- [ ] SocketCAN live listener
- [ ] Display + button UI
- [ ] Report generation
- [ ] SoftAP web dashboard

## License

Private project – all rights reserved.
