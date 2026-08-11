"""Allow running as: python -m tesla_bms"""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())