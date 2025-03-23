import logging
import os
import platform
import subprocess
from typing import Sequence
import webbrowser

from ttkbootstrap.window import Window  # type: ignore
from tkinter import StringVar, Text
import ttkbootstrap as ttk  # type: ignore

from .replay import sanitizemap
from .db import BuildOrder, Game, session


THEMENAME = "flatly"


class global_window:
    def __init__(self) -> None:
        self.window = Window(title="hidden", themename="flatly")
        self.window.withdraw()

        self.toplevel_count = 0

    def toplevel(self, *args, **kwargs) -> ttk.Toplevel:
        tl = ttk.Toplevel(*args, **kwargs)
        self.toplevel_count += 1

        def on_close():
            tl.destroy()
            self.toplevel_count -= 1
            if self.toplevel_count == 0:
                self.window.destroy()

        tl.protocol("WM_DELETE_WINDOW", on_close)
        return tl

    def close_child(self, child: ttk.Toplevel) -> None:
        child.destroy()
        self.toplevel_count -= 1
        if self.toplevel_count == 0:
            self.window.destroy()


ROOT = global_window()


def edit_game(game: Game) -> None:
    app = ROOT.toplevel(title="Edit Game")
    mainframe = ttk.Frame(app, padding=10)
    mainframe.pack(side="top", fill="both", expand=True)
    ttk.Label(mainframe, text="Winner").grid(column=0, row=0, columnspan=2)
    winner_var = StringVar(value=game.winner)
    ttk.Combobox(
        mainframe,
        values=[game.player1, game.player2],
        textvariable=winner_var,
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
        game.winner = winner_var.get()
        if new_notes := notes.get("1.0", "end"):
            game.notes = new_notes
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
        session.add(game)
        session.commit()

        ROOT.close_child(app)
        ttk.Style.instance = None

    button_frame = ttk.Frame(app, padding=10)
    button_frame.pack(side="bottom", fill="x", expand=True)

    open_url = ttk.Button(
        button_frame,
        text="Open URL",
        command=lambda: webbrowser.open(game.url),  # type: ignore
        state="enabled" if game.url else "disabled",
    )
    save = ttk.Button(button_frame, text="Save", command=save_game)
    open_replay = ttk.Button(
        button_frame,
        text="Open Replay (SB)",
        command=lambda: open_replay_cmd(game),
        state="enabled" if game.path else "disabled",
    )

    # pack buttons to be equally spaced in a row
    open_url.pack(side="left", expand=True)
    save.pack(side="left", expand=True)
    open_replay.pack(side="left", expand=True)

    # app.lift()
    app.place_window_center()
    app.attributes("-topmost", True)
    # app.attributes("-topmost", False)

    app.mainloop()


def list_games(games: Sequence[Game]) -> None:
    app = ROOT.toplevel(title="Replay list")
    # style = ttk.Style()
    # style.configure(".", font=("", 14))
    # style.configure("Treeview", rowheight=28)

    app.place_window_center()
    tree = ttk.Treeview(
        app,
        columns=("start", "duration", "map", "p1", "p2", "result"),
        show="headings",
    )
    tree.heading("start", text="Start")
    tree.heading("duration", text="Duration")
    tree.heading("map", text="Map")
    tree.heading("p1", text="Player 1")
    tree.heading("p2", text="Player 2")
    tree.heading("result", text="Result")
    tree.pack()

    for game in games:
        dur = f"{game.duration // 60:.0f}:{game.duration % 60:02.0f}"
        tree.insert(
            parent="",
            index="end",
            values=(
                game.start_time.strftime("%m/%d %H:%M"),
                dur,
                sanitizemap(game.map),
                f"{game.player1} ({game.player1race[:1]})",
                f"{game.player2} ({game.player2race[:1]})",
                "Win" if game.winner == game.player1 else "Loss",
            ),
        )

    def click_game(event):
        focusstr = tree.focus()
        focusidx = int(focusstr[1:]) - 1
        game = games[focusidx]
        edit_game(game)

    tree.bind("<Double-Button-1>", click_game)

    app.mainloop()


def open_replay_cmd(game: Game):
    if not game.path:
        return
    try:
        if platform.system() == "Darwin":  # macOS
            subprocess.call(("open", game.path))
        elif platform.system() == "Windows":  # Windows
            os.startfile(game.path)
        else:  # linux variants
            subprocess.call(("xdg-open", game.path))
    except:  # noqa
        logging.exception("Failed to open replay")
