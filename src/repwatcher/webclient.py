from pathlib import Path
import logging
from bs4 import BeautifulSoup, NavigableString
import requests

from .config import get_config

REPMASTERED_URL = "https://repmastered.icza.net"


def upload_replay_repmastered(filename: Path) -> str:
    return upload_replays_repmastered([filename])[filename.name]


def upload_replays_repmastered(filenames: list[Path]) -> dict[str, str]:
    url = f"{REPMASTERED_URL}/upload"
    authtoken = get_config().authtoken
    cookies = {}
    if authtoken:
        cookies = {"authtoken": authtoken}
    file_handles = [open(filename, "rb") for filename in filenames]
    try:
        files = [("fileInput", fh) for fh in file_handles]
        response = requests.post(url, files=files, cookies=cookies)
        if response.status_code != 200:
            logging.error(
                f"Failed to upload {filenames} with status code {response.status_code}"
            )
            raise RuntimeError(f"Failed to upload {filenames}")
    except OSError:
        logging.exception("Failed to open file")
        raise
    finally:
        for fh in file_handles:
            fh.close()

    soup = BeautifulSoup(response.text, "html.parser")
    # Find the 'Direct links to the uploaded games' <p> and extract the <a> tag inside the <ol>
    info_div = soup.find("div", class_="info")
    if (
        not info_div
        or isinstance(info_div, NavigableString)
        or "Received files: 0" in info_div.text
    ):
        logging.error(f"Something went wrong when uploading {files}")
        raise RuntimeError(f"Failed to upload {files}")
    replay_links = info_div.find_all("li")
    game_to_replay_link = {}
    for replay_link in replay_links:
        if not replay_link.find("a"):
            continue
        game_name = replay_link.text.split(" ")[0]
        game_to_replay_link[game_name] = REPMASTERED_URL + replay_link.find("a")["href"]
    return game_to_replay_link
