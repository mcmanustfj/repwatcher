"""Python wrapper for screp.exe"""

from datetime import datetime, timedelta
from json import loads
import os
from pathlib import Path
import shutil

import requests
from .config import get_config
import subprocess
import logging

from .models import Game

def parse_replay(filename: str | Path) -> Game:
    filename = str(filename)
    logging.debug(f"Parsing replay {filename}")
    config = get_config()
    proc = subprocess.run([config.screp_path, filename], capture_output=True, text=True, encoding="utf-8")
    proc.check_returncode()
    results = loads(proc.stdout)
    players = results["Header"]["Players"]
    if len(players) != 2:
        raise NotImplementedError("Only 1v1 games are supported")

    return Game(
        start_time=datetime.strptime(
            results["Header"]["StartTime"], "%Y-%m-%dT%H:%M:%S%z"
        ),
        duration=timedelta(seconds=int(results["Header"]["Frames"]) / 24),
        map=results["Header"]["Map"],
        players=[
            {
                "name": players[i]["Name"],
                "race": players[i]["Race"]["Name"],
                "is_human": players[i]["Type"]["Name"] == "Human",
            }
            for i in range(len(players))
        ],
        winner=players[int(results["Computed"]["WinnerTeam"]) - 1]["Name"],
    )


def name_replay(game: Game, bias_players: list | None = None) -> str:
    winstr = ""
    if bias_players:
      game.players.sort(key=lambda x: x["name"] in bias_players, reverse=True)
      if game.players[0]["name"] in bias_players:
          if game.winner == game.players[0]["name"]:
              winstr = "-W"
          elif game.winner == game.players[1]["name"]:
              winstr = "-L"
    matchup = game.players[0]["race"][0] + "v" + game.players[1]["race"][0]
    mapstr = "".join(c for c in game.map if c.isalpha())
    name = f"{game.start_time:%Y%m%d%H%M}-{mapstr}-{matchup}-{game.players[0]["name"]}-{game.players[1]["name"]}{winstr}.rep"
    # Remove characters from name that can't be in filenames
    name = "".join(c for c in name if c not in r"\/:*?<>|?\"")
    return name


def process_replay(filename: str | Path, bias_players: list | None = None) -> tuple[Game, Path | None]:
    logging.debug(f"Processing replay {filename}")
    filename = Path(filename).resolve()
    game = parse_replay(filename)


    if game.duration.total_seconds() < 120:
        logging.info(f"Deleting {filename.name} due to short duration")
        os.remove(filename)
        return game, None


    if not game.all_human():
        logging.info(f"Skipping {filename.name} due to non-human players")
        return game, None

    name = name_replay(game, bias_players)
    if filename.name == name:
        logging.info(f"Skipping {filename.name} due to correct name")
        return game, filename
    parent = filename.parent
    new_filename = parent / name
    # shutil.copy(filename, new_filename)
    shutil.move(filename, new_filename)
    logging.info(f"Renamed {filename.name} to {name}")
    return game, new_filename

def discover_replays() -> list[Path]:
    config = get_config()
    return list(Path(config.replay_directory).rglob("*.rep"))