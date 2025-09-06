# scr/framecapture/precapture.py
from __future__ import annotations
from typing import Tuple
import math
import time
import cv2


class PreCaptureGuide:
    """
    Usa o MESMO VideoCapture e a MESMA janela do pipeline para exibir:
    - círculo central de posicionamento
    - contagem regressiva (3..2..1)
    Retorna True se completar a contagem, False se o usuário cancelar (ESC) ou falhar captura.
    NÃO cria e NÃO destrói a janela; isso é responsabilidade do chamador (pipeline).
    """

    def __init__(
        self,
        countdown_seconds: float = 5.0,
        circle_color: Tuple[int, int, int] = (0, 255, 0),
        text_color: Tuple[int, int, int] = (255, 255, 255),
        circle_thickness: int = 3,
        radius_frac: float = 0.22,   # raio ≈ 22% do menor lado
        title: str = "Posicione a mao no circulo (ESC cancela)",
    ):
        self.countdown_seconds = float(countdown_seconds)
        self.circle_color = circle_color
        self.text_color = text_color
        self.circle_thickness = int(circle_thickness)
        self.radius_frac = float(radius_frac)
        self.title = title

    def run_on(self, cap: cv2.VideoCapture, window_name: str) -> bool:
        start = time.monotonic()
        end_t = start + self.countdown_seconds

        while True:
            now = time.monotonic()
            remaining = end_t - now

            ok, frame = cap.read()
            if not ok or frame is None:
                print("[WARN] Falha ao ler frame na pré-gravação.")
                return False

            h, w = frame.shape[:2]
            center = (w // 2, h // 2)
            radius = max(10, int(min(w, h) * self.radius_frac))

            # círculo central
            cv2.circle(frame, center, radius, self.circle_color, self.circle_thickness, lineType=cv2.LINE_AA)

            # título/instrução
            self._put_center_text(frame, self.title, (w // 2, int(0.10 * h)), scale=0.8, thickness=2)

            # contagem 3..2..1
            secs = max(0, int(math.ceil(remaining)))
            if secs <= 0:
                self._put_center_text(frame, "GO!", (w // 2, int(0.60 * h)), scale=2.2, thickness=4)
                cv2.imshow(window_name, frame)
                cv2.waitKey(250)  # feedback rápido
                return True
            else:
                self._put_center_text(frame, f"{secs}", (w // 2, int(0.60 * h)), scale=2.2, thickness=4)

            cv2.imshow(window_name, frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                return False

    # ---- util ----
    def _put_center_text(self, frame, text: str, center_xy: Tuple[int, int], scale: float = 1.0, thickness: int = 2):
        font = cv2.FONT_HERSHEY_SIMPLEX
        (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)
        x = int(center_xy[0] - tw / 2)
        y = int(center_xy[1] + th / 2)
        cv2.putText(frame, text, (x, y), font, scale, self.text_color, thickness, lineType=cv2.LINE_AA)
