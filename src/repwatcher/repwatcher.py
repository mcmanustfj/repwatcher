import os
import sys
from pathlib import Path
import requests
import atexit

from time import sleep

from watchdog.observers import Observer
from watchdog.observers.api import BaseObserver
from watchdog.events import FileSystemEventHandler, FileSystemEvent

import logging

from repwatcher.config import get_config


def is_uploaded(filename: str) -> bool:
    return filename.endswith(".uploaded.rep")


def uploadReplay(filename: Path) -> None:
    url = "https://repmastered.app/upload"
    success = False
    authtoken = get_config().authtoken
    cookies = {}
    if authtoken:
        cookies = {"authtoken": authtoken}
    try:
        sleep(0.5)
        with open(filename, "rb") as f:
            files = {"file": f}
            response = requests.post(url, files=files, cookies=cookies)
            if response.status_code == 200:
                logging.info(f"Uploaded {filename.name} successfully")
                success = True
            else:
                logging.error(
                    f"Failed to upload {filename.name} with status code {response.status_code}"
                )
    except OSError as e:
        logging.error(f"Failed to open file {filename.name}: {e}")

    if success:
        os.rename(filename, filename.with_suffix(".uploaded.rep"))


class ReplayHandler(FileSystemEventHandler):
    def on_created(self, event: FileSystemEvent):
        if (
            not event.is_directory
            and event.src_path.endswith(".rep")
            and not is_uploaded(event.src_path)
        ):
            try:
                uploadReplay(Path(event.src_path))
            except Exception:
                logging.exception("Unexpected error while uploading replay.")


def watch() -> None:
    logging.info("Starting RepMastered Watcher")
    config = get_config()

    if not Path(config.replay_directory).exists():
        logging.error(
            f"Replay directory {config.replay_directory} does not exist. Please update the config file."
        )
        sys.exit(1)

    logging.info(f"Watching {config.replay_directory} for new replays")

    observer = Observer()
    observer.schedule(ReplayHandler(), path=config.replay_directory, recursive=True)
    observer.start()

    atexit.register(cleanup, observer)

    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        sys.exit(0)


def cleanup(observer: BaseObserver) -> None:
    logging.info("Shutting down")
    observer.stop()
    observer.join()
