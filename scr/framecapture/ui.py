# scr/framecapture/ui.py
from pathlib import Path
from typing import Optional
import tkinter as tk
from tkinter import filedialog, ttk, messagebox

from .config import CaptureConfig
from .pipeline import CapturePipeline
from .video import enumerate_cameras
from .tutorial import TutorialViewer  # requer Pillow>=10

SAVE_FPS = 5.0                 # salva ~5 frames por segundo (tempo-baseado)
MAX_RECORD_SECONDS = 5.0       # cada sessão dura no máximo 5s
PRE_COUNTDOWN_SECONDS = 5.0    # contagem antes da gravação (na mesma janela)


class CaptureApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PyFrameCollector — Capture GUI")
        self.geometry("680x390")
        self.resizable(False, False)

        self.parent_dir: Optional[Path] = None
        self.cameras = enumerate_cameras(max_devices=10)
        self.pipeline: Optional[CapturePipeline] = None
        self.tutorial = TutorialViewer(self)

        # handler para cancelar o timer do auto-stop
        self._auto_stop_after_id: Optional[str] = None

        self._build_ui()

    # ---------- UI ----------
    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        # Destino
        frm_dir = ttk.LabelFrame(self, text="Destino")
        frm_dir.pack(fill="x", **pad)
        self.lbl_dir = ttk.Label(frm_dir, text="Nenhum diretório selecionado")
        self.lbl_dir.pack(side="left", padx=10, pady=8, expand=True, anchor="w")
        ttk.Button(frm_dir, text="Escolher pasta...", command=self._choose_dir).pack(side="right", padx=10, pady=8)

        # Arquivos (A..Z; prefixo/formatos fixos)
        frm_names = ttk.LabelFrame(self, text="Arquivos")
        frm_names.pack(fill="x", **pad)

        ttk.Label(frm_names, text="Pasta (A–Z):").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        letters = [chr(i) for i in range(ord('A'), ord('Z') + 1)]
        self.cmb_letter = ttk.Combobox(frm_names, values=letters, width=6, state="readonly")
        self.cmb_letter.current(0)
        self.cmb_letter.grid(row=0, column=1, padx=8, pady=6, sticky="w")

        # Informação fixa (não editável)
        ttk.Label(frm_names, text="Formato: JPG • Prefixo: frame_ (fixos)").grid(
            row=0, column=2, columnspan=3, sticky="w", padx=8, pady=6
        )

        # Captura (câmera + preview + info taxa)
        frm_cap = ttk.LabelFrame(self, text="Captura")
        frm_cap.pack(fill="x", **pad)

        ttk.Label(frm_cap, text="Câmera:").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        cam_options = []
        for d in self.cameras:
            name = d.get("name") or f"Camera #{d['index']}"
            res = f"{d['width']}x{d['height']}"
            cam_options.append(f"[{d['index']}] {name} — {res}")
        if not cam_options:
            cam_options = ["(Nenhuma câmera encontrada)"]

        self.cmb_camera = ttk.Combobox(frm_cap, values=cam_options, width=48, state="readonly")
        self.cmb_camera.current(0)
        self.cmb_camera.grid(row=0, column=1, padx=8, pady=6, sticky="w")

        self.var_preview = tk.BooleanVar(value=True)
        ttk.Checkbutton(frm_cap, text="Mostrar preview", variable=self.var_preview).grid(row=0, column=2, padx=8, pady=6)

        ttk.Label(frm_cap, text=f"Pré-contagem: {int(PRE_COUNTDOWN_SECONDS)}s • Gravação: {int(MAX_RECORD_SECONDS)}s • ~{SAVE_FPS:.0f} FPS").grid(
            row=0, column=3, sticky="w", padx=8, pady=6
        )

        # Controles
        frm_ctrl = ttk.Frame(self)
        frm_ctrl.pack(fill="x", **pad)

        # Botão de tutorial (seletor A..Z independente da pasta)
        ttk.Button(frm_ctrl, text="Abrir Tutorial", command=self._open_tutorial_picker).pack(side="left", padx=6)

        self.btn_start = ttk.Button(frm_ctrl, text="Iniciar Captura", command=self._start_capture)
        self.btn_start.pack(side="left", padx=6)

        self.btn_stop = ttk.Button(frm_ctrl, text="Parar", command=self._stop_capture, state="disabled")
        self.btn_stop.pack(side="left", padx=6)

        self.lbl_status = ttk.Label(frm_ctrl, text="Pronto.")
        self.lbl_status.pack(side="left", padx=12)

        # Desabilita Start se não houver câmera
        if not self.cameras or "(Nenhuma câmera encontrada)" in self.cmb_camera["values"]:
            self.btn_start.config(state="disabled")
            self.lbl_status.config(text="Nenhuma câmera detectada.")

    # ---------- Ações ----------
    def _choose_dir(self):
        sel = filedialog.askdirectory(title="Selecione o diretório onde a pasta A..Z será usada")
        if not sel:
            return
        self.parent_dir = Path(sel)
        self.lbl_dir.config(text=str(self.parent_dir))

    def _open_tutorial_picker(self):
        """Abre uma janela com botões A..Z; ao clicar, mostra a imagem do tutorial daquela letra."""
        win = tk.Toplevel(self)
        win.title("Escolha a letra do tutorial")
        win.resizable(False, False)
        win.attributes("-topmost", True)

        frame = ttk.Frame(win, padding=10)
        frame.pack()

        letters = [chr(i) for i in range(ord('A'), ord('Z') + 1)]
        cols = 7  # grade 7 colunas
        for idx, letter in enumerate(letters):
            r, c = divmod(idx, cols)
            btn = ttk.Button(frame, text=letter, width=4,
                             command=lambda L=letter: (self.tutorial.show(L), win.destroy()))
            btn.grid(row=r, column=c, padx=4, pady=4)

        # ESC fecha o seletor
        win.bind("<Escape>", lambda e: win.destroy())

    def _start_capture(self):
        if not self.parent_dir:
            messagebox.showerror("Erro", "Escolha o diretório de destino.")
            return

        subfolder_letter = self.cmb_letter.get().strip().upper()
        if not subfolder_letter:
            messagebox.showerror("Erro", "Selecione a pasta (A..Z).")
            return

        if not self.cameras:
            messagebox.showerror("Erro", "Nenhuma câmera disponível.")
            return
        cam_sel = self.cmb_camera.current()
        cam_index = self.cameras[cam_sel]["index"]

        cfg = CaptureConfig(
            output_parent=self.parent_dir,
            output_dir_name=subfolder_letter,   # A..Z
            save_fps=SAVE_FPS,                  # 5 FPS
            camera_index=cam_index,
            preview=self.var_preview.get(),
            max_duration_seconds=MAX_RECORD_SECONDS
        )
        self.pipeline = CapturePipeline(cfg)
        self.pipeline.start()

        # UI: travar/ativar botões e mensagem
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.lbl_status.config(
            text=f"Pré-contagem ({int(PRE_COUNTDOWN_SECONDS)}s) + gravando em {self.parent_dir / subfolder_letter} (~{SAVE_FPS:.0f} FPS, {int(MAX_RECORD_SECONDS)}s)..."
        )

        # Agenda parada automática (UI) para depois da pré-contagem + gravação
        total_ms = int((PRE_COUNTDOWN_SECONDS + MAX_RECORD_SECONDS) * 1000)
        self._auto_stop_after_id = self.after(total_ms, self._auto_stop_if_running)

    def _auto_stop_if_running(self):
        self._auto_stop_after_id = None
        if self.pipeline:
            self._stop_capture()

    def _stop_capture(self):
        # Cancela timer pendente (se houver)
        if self._auto_stop_after_id is not None:
            try:
                self.after_cancel(self._auto_stop_after_id)
            except Exception:
                pass
            self._auto_stop_after_id = None

        if self.pipeline:
            self.pipeline.stop()
            self.pipeline = None

        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.lbl_status.config(text="Parado.")
