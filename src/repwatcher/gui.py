import logging
import os
import platform
import subprocess
import webbrowser

from ttkbootstrap.window import Window  # type: ignore
from tkinter import StringVar, Text
import ttkbootstrap as ttk  # type: ignore

from repwatcher.replay import sanitizemap
from .db import BuildOrder, Game


def post_game(game: Game) -> None:
    app = Window(title="Post Game", themename="flatly")
    app.place_window_center()
    mainframe = ttk.Frame(app, padding=10)
    mainframe.pack(side="top", fill="both", expand=True)
    ttk.Label(mainframe, text="Winner").grid(column=0, row=0, columnspan=2)

    winnervar = StringVar(value=game.winner)
    ttk.Combobox(
        mainframe,
        values=[game.player1, game.player2],
        textvariable=winnervar,
        state="readonly",
    ).grid(column=2, row=0, columnspan=2)

    ttk.Label(mainframe, text=game.player1).grid(column=0, row=1)
    ttk.Label(mainframe, text=game.player1race).grid(column=1, row=1)
    ttk.Label(mainframe, text=game.player2).grid(column=0, row=2)
    ttk.Label(mainframe, text=game.player2race).grid(column=1, row=2)
    ttk.Label(mainframe, text="Map").grid(column=0, row=4)
    ttk.Label(mainframe, text=sanitizemap(game.map)).grid(column=1, row=4)
    ttk.Label(mainframe, text="Duration").grid(column=2, row=4)
    ttk.Label(
        mainframe, text=f"{float(game.duration) // 60:.0f}:{game.duration % 60:02.0f}"
    ).grid(column=3, row=4)

    p1buildorders, p2buildorders = BuildOrder.get_buildorders_from_matchup(game)

    ttk.Label(mainframe, text="Build Order").grid(column=2, row=1)
    p1bo = StringVar(value=game.buildorder1)
    ttk.Combobox(mainframe, values=p1buildorders, textvariable=p1bo).grid(
        column=3, row=1
    )

    ttk.Label(mainframe, text="Build Order").grid(column=2, row=2)
    p2bo = StringVar(value=game.buildorder2)
    ttk.Combobox(mainframe, values=p2buildorders, textvariable=p2bo).grid(
        column=3, row=2
    )

    ttk.Label(mainframe, text="Notes").grid(column=0, row=5, columnspan=4)
    notes = Text(mainframe, height=10, width=50)
    notes.insert("1.0", game.notes or "")
    notes.grid(column=0, row=6, columnspan=4)

    def save_game():
        game.winner = winnervar.get()
        if newnotes := notes.get("1.0", "end"):
            game.notes = newnotes
        if bo := p1bo.get():
            if bo not in p1buildorders:
                BuildOrder.create(
                    buildorder=bo, race=game.player1race, vs=game.player2race
                )
            game.buildorder1 = bo
        if bo := p2bo.get():
            if bo not in p2buildorders:
                BuildOrder.create(
                    buildorder=bo, race=game.player2race, vs=game.player1race
                )
            game.buildorder2 = bo
        game.save()
        app.destroy()

    buttonframe = ttk.Frame(app, padding=10)
    buttonframe.pack(side="bottom", fill="x", expand=True)

    def open_replay_cmd():
        try:
            if platform.system() == "Darwin":  # macOS
                subprocess.call(("open", game.path))
            elif platform.system() == "Windows":  # Windows
                os.startfile(game.path)
            else:  # linux variants
                subprocess.call(("xdg-open", game.path))
        except:  # noqa
            logging.exception("Failed to open replay")

    open_url = ttk.Button(
        buttonframe, text="Open URL", command=lambda: webbrowser.open(game.url)
    )
    save = ttk.Button(buttonframe, text="Save", command=save_game)
    open_replay = ttk.Button(
        buttonframe, text="Open Replay (SB)", command=open_replay_cmd
    )

    # pack buttons to be equally spaced in a row
    open_url.pack(side="left", expand=True)
    save.pack(side="left", expand=True)
    open_replay.pack(side="left", expand=True)

    app.mainloop()
