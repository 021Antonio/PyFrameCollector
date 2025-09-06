from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class CaptureConfig:
    output_parent: Path
    output_dir_name: str               # uma letra A..Z
    filename_prefix: str = "frame"
    frame_stride: int = 20             # <= FIXO: 20 frames
    camera_index: int = 0
    image_ext: str = "jpg"
    preview: bool = True

    def get_output_dir(self) -> Path:
        # força letra A..Z
        letter = (self.output_dir_name or "A").strip().upper()
        if len(letter) != 1 or not letter.isalpha():
            letter = "A"
        base = self.output_parent / letter
        base.mkdir(parents=True, exist_ok=True)
        return base
