import importlib.util
from pathlib import Path
import tkinter as tk


BASE_DIR = Path(__file__).resolve().parent


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

        frame = tk.Frame(self.root)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(frame, text="Choose Game", font=("Arial", 36, "bold")).pack(pady=20)
        tk.Button(frame, text="Cricket", font=("Arial", 28), width=16, command=lambda: self.launch_game("cricket")).pack(pady=10)
        tk.Button(frame, text="501", font=("Arial", 28), width=16, command=lambda: self.launch_game("501")).pack(pady=10)
        tk.Button(frame, text="Cricket 1v1", font=("Arial", 28), width=16, command=lambda: self.launch_game("cricket_solo")).pack(pady=10)
        tk.Button(frame, text="Quit", font=("Arial", 22), width=16, command=self.root.destroy).pack(pady=(24, 0))

    def launch_game(self, game_key):
        self.clear_root()
        if game_key == "501":
            self.current_app = five01_module.DartsApp(self.root, on_back=self.show_menu)
        elif game_key == "cricket":
            self.current_app = cricket_module.DartsApp(self.root, on_back=self.show_menu, initial_mode="teams")
        elif game_key == "cricket_solo":
            self.current_app = cricket_module.DartsApp(self.root, on_back=self.show_menu, initial_mode="solo")
        else:
            raise ValueError(f"Unknown game: {game_key}")


if __name__ == "__main__":
    root = tk.Tk()
    launcher = DartsLauncher(root)
    root.mainloop()
