"""Console script for repwatcher."""

import logging
import os
import sys
from pathlib import Path

from . import config, watcher
from .config import DATA_DIR, get_config
from .replay import discover_replays, process_replay
from .db import Game, create_default_build_orders
from .webclient import upload_replays_repmastered
from .gui import post_game

import typer
from rich.console import Console


app = typer.Typer()
app.add_typer(config.app, name="config")
console = Console()


@app.command()
def watch() -> None:
    """Watch for new replays."""
    if not Path(get_config().screp_path).exists():
        console.print(
            "screp not found. Please update the config file, or download screp from https://github.com/icza/screp/releases"
        )
        return
    watcher.watch()


@app.command()
def test() -> None:
    game: Game = Game.select().first()
    post_game(game)


@app.command()
def create_defaults() -> None:
    """Create default build orders."""
    create_default_build_orders()


@app.command()
def backfill() -> None:
    """Backfill replays."""
    logging.info("Backfilling replays")
    path_to_game: dict[Path, Game] = {}
    name_to_path: dict[str, Path] = {}
    for replay in discover_replays():
        try:
            game, path = process_replay(replay, bias_players=get_config().bw_aliases)
        except NotImplementedError:
            continue
        if not path:
            continue
        path_to_game[path] = Game.from_game(game, path)
        name_to_path[replay.name] = path

    to_upload = []
    for path, dbgame in path_to_game.items():
        if dbgame.url:
            continue
        to_upload.append(path)

    if not to_upload:
        return

    logging.info(f"Uploading {len(to_upload)} backfilled replays")
    name_to_url = upload_replays_repmastered(filenames=to_upload)
    for name, url in name_to_url.items():
        dbgame = path_to_game[name_to_path[name]]
        dbgame.url = url  # type: ignore
        dbgame.save()


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
