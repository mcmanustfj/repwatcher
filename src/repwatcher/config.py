from dataclasses import dataclass
import json
from pathlib import Path
import platformdirs
import logging

import typer

DATA_DIR = Path(platformdirs.user_data_dir(appname="RepWatcher"))
config_file: Path = DATA_DIR / "config.txt"

app = typer.Typer()


@dataclass
class Config:
    replay_directory: str
    authtoken: str
    bw_aliases: list[str]
    screp_path: str = "screp.exe"
    advanced: bool = False


def get_config() -> Config:
    with open(config_file, "r") as f:
        _config = json.load(f)
        try:
            _config["bw_aliases"] = [
                s.strip() for s in _config.get("bw_aliases", "").split(",")
            ]
            return Config(**_config)
        except TypeError:
            logging.error(f"Failed to read config from {config_file}")
            logging.error(f"Config: {_config}")
            print(
                "Failed to read config file. Run repwatcher config reset to reset it."
            )
            raise


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
    print(f"Creating config file at {config_file}")
    print(f"Default replay directory: {replay_directory}")
    print(
        "Run repwatcher config set replay_directory DIR to change the replay directory."
    )
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, "w") as f:
        config = {
            "replay_directory": replay_directory,
            "authtoken": "",
            "screp_path": "",
            "advanced": False,
            "bw_aliases": [],
        }
        json.dump(config, f, indent=4)


@app.command("open")
def open_config() -> None:
    ensure_config()
    # if on windows
    typer.launch(str(config_file))


@app.command()
def reset() -> None:
    if config_file.exists():
        logging.info(f"Deleting config file at {config_file}")
        config_file.unlink()
    create_config()
    print("Config reset to default values.")


@app.command("set")
def set_config(key: str, value: str) -> None:
    ensure_config()
    config = get_config()
    if hasattr(config, key):
        logging.info(f"Setting {key} to {value}")
        with open(config_file, "r") as f:
            _config = json.load(f)
        _config[key] = value
        with open(config_file, "w") as f:
            json.dump(_config, f, indent=4)
    else:
        print(f"Invalid key: {key}")


@app.command()
def show() -> None:
    ensure_config()
    config = get_config()
    for key, value in config.__dict__.items():
        print(f"{key}={value}")
