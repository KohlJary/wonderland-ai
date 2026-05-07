"""Allow ``python -m wonderland.tui`` to launch the app."""

from wonderland.tui.app import main

if __name__ == "__main__":
    raise SystemExit(main())
