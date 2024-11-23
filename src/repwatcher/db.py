from pathlib import Path
from peewee import *
from .config import DATA_DIR
from .replay import ParsedReplay
db = SqliteDatabase(DATA_DIR / 'repwatcher.db', pragmas={'journal_mode': 'wal', 'foreign_keys': 1})

class BaseModel(Model):
    class Meta:
        database = db

class BuildOrder(BaseModel):
    buildorder = TextField()
    race = TextField()
    vs = TextField()

class Game(BaseModel):
    start_time = DateTimeField()
    duration = FloatField()
    map = TextField()
    player1 = TextField()
    player2 = TextField()
    player1race = TextField()
    player2race = TextField()
    winner = TextField()
    buildorder1=TextField(null=True)
    buildorder2=TextField(null=True)
    notes=TextField(null=True)
    path=TextField(null=True)
    url=TextField(null=True)

    class Meta: # type: ignore
        primary_key=CompositeKey('start_time', 'player1', 'player2')


    @staticmethod
    def from_game(game: ParsedReplay, path: Path | str | None = None) -> "Game":
        if len(game.players) != 2:
            raise NotImplementedError("Only 1v1 games are supported")
        if path:
            path = str(path)

        return Game.get_or_create(
            start_time=game.start_time,
            player1=game.players[0]['name'],
            player2=game.players[1]['name'],
            defaults=dict(
                duration=game.duration.total_seconds(),
                map=game.map,
                player1race = game.players[0]['race'],
                player2race = game.players[0]['race'],
                winner = game.winner,
                path = path
            )
        )[0]

db.connect()
db.create_tables([Game], safe=True)
