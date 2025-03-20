"""Console script for repwatcher."""

import logging
import os
import sys
from pathlib import Path

from sqlalchemy import select
from . import config, watcher
from .config import DATA_DIR, get_config
from .replay import discover_replays, process_replay
from .db import Game, create_default_build_orders, session
from .webclient import upload_replays_repmastered
from .gui import edit_game

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
    edit_game(game)


@app.command()
def last() -> None:
    game: Game = session.scalars(select(Game).order_by(Game.start_time.desc())).first()
    edit_game(game)


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
    paths = {
        Path(x.path)
        for x in Game.select().where(Game.path is not None and Game.url is not None)
    }
    for replay_path in discover_replays():
        if replay_path in paths:
            continue
        if ".cpu.rep" in replay_path.name:
            continue
        try:
            game, path = process_replay(
                replay_path, bias_players=get_config().bw_aliases
            )
        except NotImplementedError:
            continue
        if not path:
            continue
        path_to_game[path] = Game.from_parsed_replay(game, path)
        name_to_path[path.name] = path
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


@app.command(help="Swaps players in old games with an alias in player2")
def backfill_alias() -> None:
    logging.info("Backfilling replays with aliases")
    for game in session.execute(
        select(Game).where(Game.player2.in_(get_config().bw_aliases))
    ):
        game.player1, game.player2 = game.player2, game.player1
        game.player1race, game.player2race = game.player2race, game.player1race
        game.winner = game.player1 if game.winner == game.player2 else game.player2
        game.save()


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
