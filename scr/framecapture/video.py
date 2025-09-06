import sys
from typing import List, Dict, Optional
import cv2

# Tenta pegar nomes amigáveis no Windows via DirectShow
try:
    from pygrabber.dshow_graph import FilterGraph  # opcional: pip install pygrabber
    _HAS_PYGRABBER = True
except Exception:
    _HAS_PYGRABBER = False

def _probe_camera(index: int, width: Optional[int] = None, height: Optional[int] = None) -> Optional[Dict]:
    backend = cv2.CAP_DSHOW if sys.platform.startswith("win") else cv2.CAP_ANY
    cap = cv2.VideoCapture(index, backend)
    if not cap.isOpened():
        return None
    ok, frame = cap.read()
    if not ok or frame is None:
        cap.release()
        return None
    if width:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    if height:
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    info = {
        "index": index,
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "name": None,
    }
    cap.release()
    return info

def enumerate_cameras(max_devices: int = 10) -> List[Dict]:
    found = []
    for i in range(max_devices):
        info = _probe_camera(i)
        if info is not None:
            found.append(info)
    if _HAS_PYGRABBER and found:
        try:
            g = FilterGraph()
            device_names = g.get_input_devices()
            for dev in found:
                idx = dev["index"]
                if 0 <= idx < len(device_names):
                    dev["name"] = device_names[idx]
        except Exception:
            pass
    return found

class VideoSource:
    def __init__(self, camera_index: int = 0):
        backend = cv2.CAP_DSHOW if sys.platform.startswith("win") else cv2.CAP_ANY
        self.cap = cv2.VideoCapture(camera_index, backend)
        if not self.cap.isOpened():
            raise RuntimeError(f"Câmera {camera_index} indisponível")

    def read(self):
        return self.cap.read()

    def release(self):
        if self.cap:
            self.cap.release()
