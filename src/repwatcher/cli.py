"""Console script for repwatcher."""
import logging
import os
import sys

from repwatcher import repwatcher
from repwatcher.config import DATA_DIR, open_config

import typer
from rich.console import Console



app = typer.Typer()
console = Console()

@app.command()
def watch() -> None:
    """Watch for new replays."""
    repwatcher.watch()

@app.command()
def config()-> None:
    """Create or open a configuration file."""
    open_config()

def main() -> int:
    os.makedirs(DATA_DIR, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        filename=DATA_DIR / "repwatcher.log",
        format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    app()
    return 0
