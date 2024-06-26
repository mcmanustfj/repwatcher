from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path
import platformdirs
import logging

import typer

DATA_DIR = Path(platformdirs.user_data_dir(appname="RepWatcher"))
config_file = DATA_DIR / "config.txt"


@dataclass
class Config:
    replay_directory: str
    authtoken: str


@lru_cache(maxsize=1)
def get_config() -> Config:
    logging.info(f"Reading config from {config_file}")
    with open(config_file, "r") as f:
        dict = json.load(f)
        return Config(**dict)


def ensure_config() -> None:
    if not config_file.exists():
        create_config()


def create_config() -> None:
    replay_directory = str(
        Path(platformdirs.user_documents_dir())
        / "StarCraft"
        / "Maps"
        / "Replays"
        / "Autosave"
    )
    logging.info(f"Creating config file at {config_file}")
    logging.info(f"Default replay directory: {replay_directory}")
    logging.info("Run repwatcher config to change the replay directory.")
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, "w") as f:
        config = {
            "replay_directory": replay_directory,
            "authtoken": "",
        }
        json.dump(config, f, indent=4)


def open_config() -> None:
    ensure_config()
    # if on windows
    typer.launch(str(config_file))
