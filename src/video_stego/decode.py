from __future__ import annotations
import os, glob
from typing import Iterator, Tuple, Optional
import cv2
import numpy as np
from .utils import MAGIC, HEADER_LEN, bits_to_bytes, parse_payload

def _iter_video_frames(path: str) -> Tuple[Iterator[np.ndarray], float]:
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError(f"Impossible d'ouvrir la vidéo: {path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    def gen():
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                yield frame
        finally:
            cap.release()
    return gen(), fps

def _iter_png_frames(dir_path: str) -> Iterator[np.ndarray]:
    files = sorted(glob.glob(os.path.join(dir_path, "frame_*.png")))
    if not files:
        raise RuntimeError(f"Aucune frame PNG trouvée dans {dir_path}")
    for f in files:
        img = cv2.imread(f, cv2.IMREAD_COLOR)
        if img is None:
            raise RuntimeError(f"Lecture échouée: {f}")
        yield img

def _extract_bits(frames: Iterator[np.ndarray], need_bytes: Optional[int]) -> bytes:
    # On lit progressivement : d'abord de quoi récupérer l'en-tête, puis la suite.
    collected_bits = []
    header_needed_bits = (len(MAGIC) + 4 + 4) * 8
    total_needed_bits = None  # devient connu après header
    got_header = False

    def take_bits_from_frame(frame: np.ndarray) -> None:
        nonlocal got_header, total_needed_bits
        b = frame[..., 0].reshape(-1)
        # On consomme tout
        collected_bits.extend((b & 1).tolist())

    for frame in frames:
        take_bits_from_frame(frame)
        if not got_header and len(collected_bits) >= header_needed_bits:
            # essayer de parser l'entête
            header_bytes = bits_to_bytes(np.array(collected_bits[:header_needed_bits], dtype=np.uint8))
            # Confirm MAGIC + len pour connaître la suite
            if header_bytes[: len(MAGIC)] != MAGIC:
                # Si pas trouvé, on échoue
                raise ValueError("Magic introuvable (la source n'est probablement pas encodée ou a été recompressée).")
            msg_len = int.from_bytes(header_bytes[len(MAGIC): len(MAGIC)+4], "big")
            # total bytes = header + msg_len
            total_needed_bits = (len(MAGIC)+4+4 + msg_len) * 8
            got_header = True

        if got_header and total_needed_bits is not None and len(collected_bits) >= total_needed_bits:
            break

    if not got_header:
        raise ValueError("Impossible d'extraire l'en-tête (source trop courte ?)")

    if total_needed_bits is None:
        raise ValueError("Longueur totale inconnue")

    bits_array = np.array(collected_bits[:total_needed_bits], dtype=np.uint8)
    return bits_to_bytes(bits_array)

def decode(in_path: str) -> str:
    # in_path peut être un dossier PNG ou une vidéo
    if os.path.isdir(in_path):
        frames = _iter_png_frames(in_path)
        raw = _extract_bits(frames, need_bytes=None)
    else:
        frames, _fps = _iter_video_frames(in_path)
        raw = _extract_bits(frames, need_bytes=None)
    return parse_payload(raw)
