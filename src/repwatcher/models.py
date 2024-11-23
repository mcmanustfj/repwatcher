from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal, TypedDict

type Race = Literal["Zerg"] | Literal["Terran"] | Literal["Protoss"] | Literal["Random"]


class PlayerData(TypedDict):
    name: str
    race: Race
    is_human: bool


@dataclass
class Game:
    start_time: datetime
    duration: timedelta
    map: str
    players: list[PlayerData]
    winner: str

    def all_human(self) -> bool:
        return all(player["is_human"] for player in self.players)
