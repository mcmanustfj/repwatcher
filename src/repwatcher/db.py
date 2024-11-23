from datetime import datetime
from pathlib import Path
from peewee import (
    Model,
    SqliteDatabase,
    CompositeKey,
    TextField,
    DateTimeField,
    FloatField,
)
from .config import DATA_DIR
from .replay import ParsedReplay, Race

db = SqliteDatabase(
    DATA_DIR / "repwatcher.db", pragmas={"journal_mode": "wal", "foreign_keys": 1}
)


class BaseModel(Model):
    class Meta:
        database = db


class BuildOrder(BaseModel):
    buildorder: str = TextField()  # type: ignore
    race: Race = TextField()  # type: ignore
    vs: Race = TextField()  # type: ignore

    class Meta:  # type: ignore
        primary_key = CompositeKey("buildorder", "race", "vs")

    @staticmethod
    def get_buildorders_from_matchup(Game) -> tuple[list[str], list[str]]:
        p1 = [
            x.buildorder
            for x in BuildOrder.select().where(
                BuildOrder.race == Game.player1race, BuildOrder.vs == Game.player2race
            )
        ]  # type: ignore
        p2 = [
            x.buildorder
            for x in BuildOrder.select().where(
                BuildOrder.race == Game.player2race, BuildOrder.vs == Game.player1race
            )
        ]  # type: ignore
        return p1, p2


class Game(BaseModel):
    start_time: datetime = DateTimeField()  # type: ignore
    duration: float = FloatField()  # type: ignore
    map: str = TextField()  # type: ignore
    player1: str = TextField()  # type: ignore
    player2: str = TextField()  # type: ignore
    player1race: str = TextField()  # type: ignore
    player2race: str = TextField()  # type: ignore
    winner: str = TextField()  # type: ignore
    buildorder1: str = TextField(null=True)  # type: ignore
    buildorder2: str = TextField(null=True)  # type: ignore
    notes: str = TextField(null=True)  # type: ignore
    path: str = TextField(null=True)  # type: ignore
    url: str = TextField(null=True)  # type: ignore

    class Meta:  # type: ignore
        primary_key = CompositeKey("start_time", "player1", "player2")

    @staticmethod
    def from_game(game: ParsedReplay, path: Path | str | None = None) -> "Game":
        if len(game.players) != 2:
            raise NotImplementedError("Only 1v1 games are supported")
        if path:
            path = str(path)

        return Game.get_or_create(
            start_time=game.start_time,
            player1=game.players[0]["name"],
            player2=game.players[1]["name"],
            defaults=dict(
                duration=game.duration.total_seconds(),
                map=game.map,
                player1race=game.players[0]["race"],
                player2race=game.players[1]["race"],
                winner=game.winner,
                path=path,
            ),
        )[0]


db.connect()
db.create_tables([Game, BuildOrder], safe=True)


def create_default_build_orders():
    default_build_orders = [
        # ZvP
        BuildOrder(buildorder="3hs5hh", race="Zerg", vs="Protoss"),
        BuildOrder(buildorder="3hs5hh mutas", race="Zerg", vs="Protoss"),
        BuildOrder(buildorder="973", race="Zerg", vs="Protoss"),
        BuildOrder(buildorder="Ling allin", race="Zerg", vs="Protoss"),
        # PvZ
        BuildOrder(buildorder="9-9 gate", race="Protoss", vs="Zerg"),
        BuildOrder(buildorder="10-12 gate", race="Protoss", vs="Zerg"),
        BuildOrder(buildorder="FFE standard", race="Protoss", vs="Zerg"),
        BuildOrder(buildorder="FFE sairless", race="Protoss", vs="Zerg"),
        BuildOrder(buildorder="GFE standard", race="Protoss", vs="Zerg"),
        BuildOrder(buildorder="GFE sairless", race="Protoss", vs="Zerg"),
        BuildOrder(buildorder="Sair DT", race="Protoss", vs="Zerg"),
        BuildOrder(buildorder="1 base tech", race="Protoss", vs="Zerg"),
        # ZvT
        BuildOrder(buildorder="2hm", race="Zerg", vs="Terran"),
        BuildOrder(buildorder="3hm", race="Zerg", vs="Terran"),
        BuildOrder(buildorder="2 hatch lurker", race="Zerg", vs="Terran"),
        BuildOrder(buildorder="3 hatch lurker", race="Zerg", vs="Terran"),
        # TvZ
        BuildOrder(buildorder="8 rax", race="Terran", vs="Zerg"),
        BuildOrder(buildorder="2 rax acad", race="Terran", vs="Zerg"),
        BuildOrder(buildorder="4 rax +1", race="Terran", vs="Zerg"),
        BuildOrder(buildorder="1 base T", race="Terran", vs="Zerg"),
        BuildOrder(buildorder="Factory expand", race="Terran", vs="Zerg"),
        BuildOrder(buildorder="2 port wraith", race="Terran", vs="Zerg"),
        # ZvZ
        BuildOrder(buildorder="9 pool speed", race="Zerg", vs="Zerg"),
        BuildOrder(buildorder="12 hatch", race="Zerg", vs="Zerg"),
        BuildOrder(buildorder="12 pool", race="Zerg", vs="Zerg"),
        BuildOrder(buildorder="9 pool lair", race="Zerg", vs="Zerg"),
        BuildOrder(buildorder="Overpool speed", race="Zerg", vs="Zerg"),
        BuildOrder(buildorder="Overpool lair", race="Zerg", vs="Zerg"),
        BuildOrder(buildorder="9 hatch", race="Zerg", vs="Zerg"),
    ]
    for bo in default_build_orders:
        BuildOrder.insert(
            [bo.buildorder, bo.race, bo.vs]
        ).on_conflict_ignore().execute()
