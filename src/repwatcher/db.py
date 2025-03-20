import datetime
from pathlib import Path
from sqlalchemy import (
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Mapped, mapped_column
from .config import DATA_DIR
from .replay import ParsedReplay

engine = create_engine(f"sqlite:///{DATA_DIR / 'repwatcher.db'}", echo=True)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()


class BuildOrder(Base):
    __tablename__ = "build_order"
    buildorder: Mapped[str] = mapped_column(primary_key=True)
    race: Mapped[str] = mapped_column(primary_key=True)
    vs: Mapped[str] = mapped_column(primary_key=True)

    @staticmethod
    def get_buildorders_from_matchup(Game) -> tuple[list[str], list[str]]:
        p1 = [
            x.buildorder
            for x in session.query(BuildOrder)
            .filter_by(race=Game.player1race, vs=Game.player2race)
            .all()
        ]
        p2 = [
            x.buildorder
            for x in session.query(BuildOrder)
            .filter_by(race=Game.player2race, vs=Game.player1race)
            .all()
        ]
        return p1, p2


class Game(Base):
    __tablename__ = "game"
    start_time: Mapped[datetime.datetime]
    duration: Mapped[float]
    map: Mapped[str]
    player1: Mapped[str] = mapped_column(primary_key=True)
    player2: Mapped[str] = mapped_column(primary_key=True)
    player1race: Mapped[str]
    player2race: Mapped[str]
    winner: Mapped[str]
    buildorder1: Mapped[str | None]
    buildorder2: Mapped[str | None]
    notes: Mapped[str | None]
    path: Mapped[str | None]
    url: Mapped[str | None]

    @staticmethod
    def from_parsed_replay(
        game: ParsedReplay, path: Path | str | None = None
    ) -> "Game":
        if len(game.players) != 2:
            raise NotImplementedError("Only 1v1 games are supported")
        if path:
            path = str(path)

        existing_game = (
            session.query(Game)
            .filter_by(
                start_time=game.start_time,
                player1=game.players[0]["name"],
                player2=game.players[1]["name"],
            )
            .first()
        )

        if existing_game:
            return existing_game

        new_game = Game(
            start_time=game.start_time,
            player1=game.players[0]["name"],
            player2=game.players[1]["name"],
            duration=game.duration.total_seconds(),
            map=game.map,
            player1race=game.players[0]["race"],
            player2race=game.players[1]["race"],
            winner=game.winner,
            path=path,
        )
        session.add(new_game)
        session.commit()
        return new_game


Base.metadata.create_all(engine)


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
        session.merge(bo)
    session.commit()
