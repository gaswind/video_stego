from __future__ import annotations
import os
from typing import Iterator, Tuple
import cv2
import numpy as np
from .utils import payload_from_text, bytes_to_bits

def _iter_video_frames(path: str) -> Tuple[Iterator[np.ndarray], int, int, float, int]:
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError(f"Impossible d'ouvrir la vidéo: {path}")
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or -1

    def gen():
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                yield frame
        finally:
            cap.release()
    return gen(), w, h, fps, count

def capacity_bits(n_frames: int, width: int, height: int) -> int:
    # 1 bit par pixel (canal bleu uniquement)
    return n_frames * width * height

def embed_bits_into_frames(frames: Iterator[np.ndarray], bits: np.ndarray, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    bit_idx = 0
    frame_idx = 0
    total_bits = len(bits)

    for frame in frames:
        # OpenCV BGR
        b = frame[..., 0]  # canal bleu
        h, w = b.shape[:2]
        pixels = h * w

        # nombre de bits à écrire sur cette frame
        nb = min(total_bits - bit_idx, pixels)
        if nb > 0:
            # Aplatir pour écriture rapide puis reshape
            flat = b.reshape(-1).copy()
            # modifie LSB
            flat[:nb] = (flat[:nb] & 0xFE) | bits[bit_idx: bit_idx + nb]
            b2 = flat.reshape(h, w)
            frame[..., 0] = b2
            bit_idx += nb

        # Sauvegarde PNG lossless
        out_path = os.path.join(out_dir, f"frame_{frame_idx:06d}.png")
        ok = cv2.imwrite(out_path, frame)
        if not ok:
            raise RuntimeError(f"Echec écriture {out_path}")
        frame_idx += 1

        if bit_idx >= total_bits:
            # On continue tout de même à écrire les frames restantes inchangées
            # pour garder même durée/nb frames (utile si repack vidéo ensuite).
            pass

    if bit_idx < total_bits:
        raise ValueError("Capacité insuffisante: message trop long pour cette vidéo.")

def encode(in_video: str, out_frames: str, text: str) -> None:
    frames, w, h, fps, n = _iter_video_frames(in_video)
    if n <= 0:
        # Si inconnu, on va streamer jusqu'au bout dans embed (qui lèvera si manque)
        # mais on ne peut pas pré-checker la capacité.
        pass

    payload = payload_from_text(text)
    bits = bytes_to_bits(payload)

    # Pré-check si nombre de frames connu
    if n > 0:
        cap_bits = capacity_bits(n, w, h)
        if len(bits) > cap_bits:
            raise ValueError(f"Message trop long. Capacité ~{cap_bits//8} octets, besoin {len(bits)//8} octets.")

    embed_bits_into_frames(frames, bits, out_frames)
