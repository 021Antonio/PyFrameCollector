import cv2
import signal
import threading
from .config import CaptureConfig
from .storage import FrameStorage
from .video import VideoSource

class FrameSampler:
    def __init__(self, stride: int = 10):
        if stride < 1:
            raise ValueError("frame_stride deve ser >= 1")
        self.stride = stride
        self.index = 0

    def should_save(self) -> bool:
        self.index += 1
        return self.index % self.stride == 0

class CapturePipeline:
    def __init__(self, cfg: CaptureConfig):
        self.cfg = cfg
        self.out_dir = cfg.get_output_dir()
        self.storage = FrameStorage(self.out_dir, cfg.image_ext, cfg.filename_prefix)
        self.video = None
        self.sampler = FrameSampler(cfg.frame_stride)
        self._running = False
        self._thread: threading.Thread | None = None

    def _loop(self):
        try:
            self.video = VideoSource(self.cfg.camera_index)
        except Exception as e:
            print(f"[ERRO] {e}")
            self._running = False
            return

        window_name = "Preview (press ESC to close)" if self.cfg.preview else None
        if self.cfg.preview:
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

        print(f"[INFO] Salvando a cada {self.cfg.frame_stride} frame(s) em: {self.out_dir}")

        while self._running:
            ok, frame = self.video.read()
            if not ok or frame is None:
                print("[WARN] Falha ao ler frame da câmera.")
                break

            if self.cfg.preview:
                cv2.imshow(window_name, frame)
                # Fecha preview ao apertar ESC
                if cv2.waitKey(1) & 0xFF == 27:
                    self.stop()
                    break

            if self.sampler.should_save():
                path = self.storage.save(frame)
                print(f"[SAVE] {path}")

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
