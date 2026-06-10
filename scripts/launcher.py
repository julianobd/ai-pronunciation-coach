"""PyInstaller entry point (plain script, no relative imports)."""

import sys

from pronunciation_coach.app import main

sys.exit(main())
