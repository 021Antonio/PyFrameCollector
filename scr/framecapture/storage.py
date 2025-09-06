from datetime import datetime
from pathlib import Path
import cv2

class FrameStorage:
    def __init__(self, base_dir: Path, image_ext: str = "jpg", filename_prefix: str = "frame"):
        self.base_dir = base_dir
        self.image_ext = image_ext.strip(".").lower()
        self.prefix = filename_prefix or "frame"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.counter = 0

    def save(self, frame) -> Path:
        self.counter += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{self.prefix}_{timestamp}_{self.counter:06d}.{self.image_ext}"
        path = self.base_dir / filename
        ok = cv2.imwrite(str(path), frame)
        if not ok:
            raise RuntimeError(f"Falha ao salvar imagem: {path}")
        return path
