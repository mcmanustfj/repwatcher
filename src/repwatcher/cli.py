"""Console script for repwatcher."""

import logging
import os
import sys


from . import config, watcher
from .config import DATA_DIR
from .replay import *
from .db import Game
from .webclient import upload_replay_repmastered, upload_replays_repmastered

import typer
from rich.console import Console


app = typer.Typer()
app.add_typer(config.app, name="config")
console = Console()


@app.command()
def watch() -> None:
    """Watch for new replays."""
    watcher.watch()


@app.command()
def test() -> None:
    import flet as ft # type: ignore
    def main(page: ft.Page):
        page.title = "Flet counter example"
        page.vertical_alignment = ft.MainAxisAlignment.CENTER

        txt_number = ft.TextField(value="0", text_align=ft.TextAlign.RIGHT, width=100)

        def minus_click(e):
            txt_number.value = str(int(txt_number.value or 0) - 1)
            page.update()

        def plus_click(e):
            txt_number.value = str(int(txt_number.value or 0) + 1)
            page.update()

        page.add(
            ft.Row(
                [
                    ft.IconButton(ft.icons.REMOVE, on_click=minus_click),
                    txt_number,
                    ft.IconButton(ft.icons.ADD, on_click=plus_click),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            )
        )

    ft.app(main)




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
