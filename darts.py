import importlib.util
from pathlib import Path
import tkinter as tk
from tkinter import ttk


BASE_DIR = Path(__file__).resolve().parent
MENU_BG = "#161311"
MENU_PANEL = "#241d19"
MENU_PANEL_ALT = "#2b221d"
MENU_TEXT = "#f4ede3"
MENU_MUTED = "#b8a99a"
ACCENT_BLUE = "#4d86ff"
ACCENT_ORANGE = "#f08a2b"
BUTTON_TEXT = "#1b1512"


def load_module(module_name, filename):
    module_path = BASE_DIR / filename
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


five01_module = load_module("darts_501_app", "501.py")
cricket_module = load_module("darts_cricket_app", "cricket.py")


class DartsLauncher:
    def __init__(self, root):
        self.root = root
        self.root.attributes("-fullscreen", True)
        self.root.title("Darts")
        self.current_app = None
        self.show_menu()

    def clear_root(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_menu(self):
        self.clear_root()
        self.current_app = None
        self.root.title("Darts")
        self.x01_score_var = tk.StringVar(value="501")
        self.x01_in_var = tk.StringVar(value="Any")
        self.x01_out_var = tk.StringVar(value="Double")
        self.x01_mode_var = tk.StringVar(value="2v2 Teams")
        self.cricket_mode_var = tk.StringVar(value="2v2 Teams")
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()

        bg = tk.Canvas(self.root, bg=MENU_BG, highlightthickness=0)
        bg.place(x=0, y=0, relwidth=1, relheight=1)
        self.draw_menu_background(bg, screen_w, screen_h)

        hero = tk.Frame(self.root, bg=MENU_BG)
        hero.place(relx=0.5, rely=0.18, anchor="center")
        tk.Label(
            hero,
            text="OpenDart",
            font=("Avenir Next", 54, "bold"),
            fg=MENU_TEXT,
            bg=MENU_BG,
        ).pack()
        tk.Label(
            hero,
            text="Choose a board, step to the line, and let the match begin.",
            font=("Avenir Next", 18),
            fg=MENU_MUTED,
            bg=MENU_BG,
        ).pack(pady=(10, 0))

        card_row = tk.Frame(self.root, bg=MENU_BG)
        card_row.place(relx=0.5, rely=0.55, anchor="center")

        self.build_menu_card(
            parent=card_row,
            title="Cricket",
            subtitle="Race to close. Punish the misses.",
            description="Team play, solo mode, live stats, shot maps, and late-game pressure all in one board.",
            accent=ACCENT_BLUE,
            cta="Play Cricket",
            command=lambda: self.launch_game("cricket"),
            side="left",
            options_builder=self.build_cricket_options,
            card_height=430,
        )
        self.build_menu_card(
            parent=card_row,
            title="X01",
            subtitle="Chase the finish. Pick your rules.",
            description="Classic score-down play with a configurable starting score and in/out rules, individual or team formats, full match tracking.",
            accent=ACCENT_ORANGE,
            cta="Play X01",
            command=lambda: self.launch_game("x01"),
            side="right",
            options_builder=self.build_x01_options,
        )

        footer = tk.Frame(self.root, bg=MENU_BG)
        footer.place(relx=0.5, rely=0.88, anchor="center")
        tk.Label(
            footer,
            text="Game modes can be changed from inside each board.",
            font=("Avenir Next", 15),
            fg=MENU_MUTED,
            bg=MENU_BG,
        ).pack()
        tk.Button(
            footer,
            text="Quit",
            font=("Avenir Next", 18, "bold"),
            padx=26,
            pady=10,
            bg=MENU_TEXT,
            fg=BUTTON_TEXT,
            activebackground=MENU_MUTED,
            activeforeground=BUTTON_TEXT,
            bd=0,
            highlightthickness=0,
            command=self.root.destroy,
            cursor="hand2",
        ).pack(pady=(18, 0))

    def draw_menu_background(self, canvas, width, height):
        canvas.create_rectangle(0, 0, width, height, fill=MENU_BG, outline="")
        canvas.create_oval(-180, -120, 420, 420, fill="#241c18", outline="")
        canvas.create_oval(width - 430, -90, width + 110, 450, fill="#201915", outline="")
        canvas.create_oval(width - 520, height - 360, width + 40, height + 120, fill="#2d241e", outline="")
        canvas.create_oval(-140, height - 300, 360, height + 120, fill="#1f1815", outline="")
        canvas.create_arc(
            width * 0.18,
            height * 0.19,
            width * 0.82,
            height * 0.93,
            start=205,
            extent=110,
            style=tk.ARC,
            outline="#5c4735",
            width=3,
        )
        canvas.create_arc(
            width * 0.22,
            height * 0.22,
            width * 0.78,
            height * 0.89,
            start=22,
            extent=95,
            style=tk.ARC,
            outline="#745b45",
            width=2,
        )

    def build_menu_card(self, parent, title, subtitle, description, accent, cta, command, side, options_builder=None, card_height=None):
        height = card_height if card_height else (480 if options_builder else 350)
        card = tk.Frame(parent, bg=MENU_PANEL if side == "left" else MENU_PANEL_ALT, width=390, height=height)
        card.pack_propagate(False)
        card.pack(side=tk.LEFT, padx=20)

        accent_bar = tk.Frame(card, bg=accent, height=10)
        accent_bar.pack(fill=tk.X)

        body = tk.Frame(card, bg=card.cget("bg"), padx=28, pady=24)
        body.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            body,
            text=title,
            font=("Avenir Next", 34, "bold"),
            fg=MENU_TEXT,
            bg=body.cget("bg"),
            anchor="center",
        ).pack(anchor="center")
        tk.Label(
            body,
            text=subtitle,
            font=("Avenir Next", 16, "bold"),
            fg=accent,
            bg=body.cget("bg"),
            anchor="center",
        ).pack(anchor="center", pady=(6, 16))
        tk.Label(
            body,
            text=description,
            font=("Avenir Next", 15),
            fg=MENU_MUTED,
            bg=body.cget("bg"),
            justify=tk.CENTER,
            wraplength=320,
            anchor="center",
        ).pack(anchor="center")

        if options_builder:
            options_builder(body)

        stat_row = tk.Frame(body, bg=body.cget("bg"))
        stat_row.pack(anchor="center", pady=(28, 22))
        for text in ("Live Stats", "Profiles", "History"):
            pill = tk.Label(
                stat_row,
                text=text,
                font=("Avenir Next", 11, "bold"),
                fg=MENU_TEXT,
                bg="#352b25",
                padx=10,
                pady=6,
            )
            pill.pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            body,
            text=cta,
            font=("Avenir Next", 19, "bold"),
            bg=accent,
            fg=BUTTON_TEXT,
            activebackground=MENU_TEXT,
            activeforeground=BUTTON_TEXT,
            bd=0,
            highlightthickness=0,
            padx=22,
            pady=12,
            command=command,
            cursor="hand2",
        ).pack(anchor="center")

    X01_MODE_DISPLAY_TO_KEY = {
        "2v2 Teams": "2v2",
        "1v1": "2p",
        "3 Player": "3p",
        "4 Player": "4p",
    }

    CRICKET_MODE_DISPLAY_TO_KEY = {
        "2v2 Teams": "2v2",
        "1v1": "1v1",
        "Cutthroat (3p)": "cutthroat",
    }

    def build_cricket_options(self, parent):
        mode_row = tk.Frame(parent, bg=parent.cget("bg"))
        mode_row.pack(anchor="center", pady=(0, 18))
        column = tk.Frame(mode_row, bg=parent.cget("bg"))
        column.pack(side=tk.LEFT, padx=8)
        tk.Label(
            column,
            text="Mode",
            font=("Avenir Next", 11, "bold"),
            fg=MENU_MUTED,
            bg=parent.cget("bg"),
        ).pack()
        ttk.Combobox(
            column,
            textvariable=self.cricket_mode_var,
            values=list(self.CRICKET_MODE_DISPLAY_TO_KEY.keys()),
            font=("Avenir Next", 13),
            state="readonly",
            width=13,
        ).pack()

    def build_x01_options(self, parent):
        players_row = tk.Frame(parent, bg=parent.cget("bg"))
        players_row.pack(anchor="center", pady=(0, 10))
        column = tk.Frame(players_row, bg=parent.cget("bg"))
        column.pack(side=tk.LEFT, padx=8)
        tk.Label(
            column,
            text="Players",
            font=("Avenir Next", 11, "bold"),
            fg=MENU_MUTED,
            bg=parent.cget("bg"),
        ).pack()
        ttk.Combobox(
            column,
            textvariable=self.x01_mode_var,
            values=list(self.X01_MODE_DISPLAY_TO_KEY.keys()),
            font=("Avenir Next", 13),
            state="readonly",
            width=10,
        ).pack()

        options_row = tk.Frame(parent, bg=parent.cget("bg"))
        options_row.pack(anchor="center", pady=(0, 18))

        for label, var, values in (
            ("Score", self.x01_score_var, ["101", "301", "501", "701", "901"]),
            ("In", self.x01_in_var, ["Any", "Single", "Double", "Triple"]),
            ("Out", self.x01_out_var, ["Any", "Single", "Double", "Triple"]),
        ):
            column = tk.Frame(options_row, bg=parent.cget("bg"))
            column.pack(side=tk.LEFT, padx=8)
            tk.Label(
                column,
                text=label,
                font=("Avenir Next", 11, "bold"),
                fg=MENU_MUTED,
                bg=parent.cget("bg"),
            ).pack()
            ttk.Combobox(
                column,
                textvariable=var,
                values=values,
                font=("Avenir Next", 13),
                state="readonly",
                width=7,
            ).pack()

    def launch_game(self, game_key):
        self.clear_root()
        if game_key == "x01":
            self.current_app = five01_module.DartsApp(
                self.root,
                on_back=self.show_menu,
                initial_mode=self.X01_MODE_DISPLAY_TO_KEY[self.x01_mode_var.get()],
                starting_score=int(self.x01_score_var.get()),
                in_rule=self.x01_in_var.get().lower(),
                out_rule=self.x01_out_var.get().lower(),
            )
        elif game_key == "cricket":
            self.current_app = cricket_module.DartsApp(
                self.root,
                on_back=self.show_menu,
                initial_mode=self.CRICKET_MODE_DISPLAY_TO_KEY[self.cricket_mode_var.get()],
            )
        else:
            raise ValueError(f"Unknown game: {game_key}")


if __name__ == "__main__":
    root = tk.Tk()
    launcher = DartsLauncher(root)
    root.mainloop()
