from pathlib import Path
from typing import Optional
import tkinter as tk
from tkinter import ttk, messagebox

# Pillow para abrir JPG/PNG/etc.
from PIL import Image, ImageTk


class TutorialViewer:
    """
    Mostra uma imagem de tutorial baseada na letra escolhida (A..Z).
    Procura arquivos {LETRA}.jpg|jpeg|png|gif em assets/tutorials (por padrão).
    """
    def __init__(self, master: tk.Tk, base_dir: Optional[Path] = None, max_size=(900, 700)):
        self.master = master
        self.base_dir = base_dir or Path(__file__).resolve().parent / "assets" / "tutorials"
        self.base_dir.mkdir(parents=True, exist_ok=True)  # garante a pasta
        self.max_size = max_size

        self._win: Optional[tk.Toplevel] = None
        self._img_tk: Optional[ImageTk.PhotoImage] = None
        self._current_letter: Optional[str] = None

    def _find_image_path(self, letter: str) -> Optional[Path]:
        letter = (letter or "").strip().upper()
        for ext in ("jpg", "jpeg", "png", "gif"):
            candidate = self.base_dir / f"{letter}.{ext}"
            if candidate.exists():
                return candidate
        return None

    def show(self, letter: str):
        path = self._find_image_path(letter)
        if path is None:
            messagebox.showerror(
                "Tutorial não encontrado",
                f"Não encontrei imagem para a letra '{letter}'.\n"
                f"Coloque um arquivo {letter}.jpg|png|gif na pasta:\n{self.base_dir}"
            )
            return

        # Se já existe uma janela aberta, fecha para recarregar
        if self._win is not None and tk.Toplevel.winfo_exists(self._win):
            self._win.destroy()
            self._win = None

        self._win = tk.Toplevel(self.master)
        self._win.title(f"Tutorial — {letter}")
        self._win.attributes("-topmost", True)
        self._win.resizable(True, True)

        # Carrega e ajusta para caber na janela (mantendo proporção)
        im = Image.open(path)
        im.thumbnail(self.max_size, Image.LANCZOS)
        self._img_tk = ImageTk.PhotoImage(im)

        lbl = ttk.Label(self._win, image=self._img_tk)
        lbl.pack(padx=10, pady=10)

        ttk.Button(self._win, text="Fechar", command=self._win.destroy).pack(pady=(0, 10))
        self._win.bind("<Escape>", lambda e: self._win.destroy())

        self._current_letter = letter

    def close(self):
        if self._win is not None and tk.Toplevel.winfo_exists(self._win):
            self._win.destroy()
            self._win = None
