"""Click-based CLI entry point.

The team extends this with new commands. The ``main`` group is the
attachment point; add subcommands with ``@main.command()``.
"""

from __future__ import annotations

import click


@click.group()
def main() -> None:
    """App CLI — extend with new commands."""


@main.command()
@click.option("--name", default="World", help="Who to greet.")
def greet(name: str) -> None:
    """Print a greeting to stdout."""
    click.echo(f"Hello, {name}!")


if __name__ == "__main__":
    main()
