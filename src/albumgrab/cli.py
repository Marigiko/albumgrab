"""Typer entry point for the albumgrab CLI.

Slice 1 stub: only the command surface exists so `albumgrab --help` works.
The discover -> select -> download -> tag pipeline is wired in Slice 3.
"""

from pathlib import Path
from typing import Annotated

import typer

from albumgrab.config import DEFAULT_OUTPUT_ROOT

app = typer.Typer(
    help="Download YouTube Music albums as tagged MP3 files.",
    no_args_is_help=True,
)


@app.command()
def main(
    artist: Annotated[
        str | None, typer.Argument(help="Artist name to search on YouTube Music")
    ] = None,
    output: Annotated[
        Path | None, typer.Option(help="Output directory root for the music library")
    ] = None,
) -> None:
    """Grab every track of the selected albums as tagged MP3s."""
    dest = output or Path(DEFAULT_OUTPUT_ROOT)
    typer.echo(f"albumgrab: '{artist}' -> {dest} (pipeline arrives in Slice 3)")


if __name__ == "__main__":
    app()
