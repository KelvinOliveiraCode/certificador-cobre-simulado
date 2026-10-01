"""Permite executar como ``python -m certsim``.

Enables running as ``python -m certsim``.
"""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())