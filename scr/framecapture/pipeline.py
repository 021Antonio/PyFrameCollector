# scr/framecapture/pipeline.py
import cv2
import threading
import time
from .config import CaptureConfig
from .storage import FrameStorage
from .video import VideoSource
from .precapture import PreCaptureGuide


PRE_COUNTDOWN_SECONDS = 5.0  # contagem antes de iniciar a gravação


class TimeSampler:
    """Decide salvar por intervalo de tempo (1 / fps)."""
    def __init__(self, fps: float):
        self.interval = 1.0 / fps if fps and fps > 0 else 0.0
        self._last_save_t: float | None = None

    def should_save(self) -> bool:
        now = time.monotonic()
        if self.interval <= 0.0:
            self._last_save_t = now
            return True
        if self._last_save_t is None or (now - self._last_save_t) >= self.interval:
            self._last_save_t = now
            return True
        return False


class CapturePipeline:
    def __init__(self, cfg: CaptureConfig):
        self.cfg = cfg
        self.out_dir = cfg.get_output_dir()
        self.storage = FrameStorage(self.out_dir, cfg.image_ext, cfg.filename_prefix)
        self.video: VideoSource | None = None
        self.sampler = TimeSampler(cfg.save_fps)
        self._running = False
        self._thread: threading.Thread | None = None

    def _loop(self):
        # 1) abre câmera
        try:
            self.video = VideoSource(self.cfg.camera_index)
        except Exception as e:
            print(f"[ERRO] {e}")
            self._running = False
            return

        # 2) cria janela (uma vez) e faz a PRÉ-GRAVAÇÃO na MESMA janela
        window_name = "Captura (ESC para parar)"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

        print(f"[INFO] Pasta: {self.out_dir}")
        print(f"[INFO] Taxa alvo: ~{self.cfg.save_fps:.1f} FPS | Duração máx: {self.cfg.max_duration_seconds:.1f}s")
        print(f"[INFO] Mostrando guia de posicionamento ({PRE_COUNTDOWN_SECONDS:.0f}s)...")

        guide = PreCaptureGuide(countdown_seconds=PRE_COUNTDOWN_SECONDS)
        ok = guide.run_on(self.video.cap, window_name)
        if not ok:
            self._running = False
            self._cleanup(window_name)
            print("[INFO] Pré-gravação cancelada.")
            return

        print("[INFO] Iniciando gravação...")
        start = time.monotonic()

        # 3) loop de gravação (mesma janela, mesma câmera)
        while self._running:
            # corta por tempo (ex.: 5s)
            if self.cfg.max_duration_seconds > 0 and (time.monotonic() - start) >= self.cfg.max_duration_seconds:
                print(f"[INFO] Tempo máximo atingido ({self.cfg.max_duration_seconds:.1f}s). Encerrando captura.")
                break

            ok, frame = self.video.read()
            if not ok or frame is None:
                print("[WARN] Falha ao ler frame da câmera.")
                break

            # preview opcional
            if self.cfg.preview:
                cv2.imshow(window_name, frame)
                if cv2.waitKey(1) & 0xFF == 27:  # ESC
                    self._running = False
                    break

            # salva por tempo (~fps)
            if self.sampler.should_save():
                path = self.storage.save(frame)
                print(f"[SAVE] {path}")

        self._running = False
        self._cleanup(window_name)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def _cleanup(self, window_name: str | None):
        if self.video:
            self.video.release()
        if window_name:
            try:
                cv2.destroyWindow(window_name)
            except cv2.error:
                pass
        print("[INFO] Captura finalizada.")
