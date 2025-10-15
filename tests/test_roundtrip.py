import os, shutil, cv2, numpy as np
from video_stego.encode import encode
from video_stego.decode import decode

def _make_dummy_video(path: str, w=64, h=48, frames=30, fps=10):
    fourcc = cv2.VideoWriter_fourcc(*"FFV1")  # lossless if available
    out = cv2.VideoWriter(path, fourcc, fps, (w, h))
    if not out.isOpened():
        # fallback to MJPG (lossy) just to create something; we will only roundtrip via PNGs
        fourcc = cv2.VideoWriter_fourcc(*"MJPG")
        out = cv2.VideoWriter(path, fourcc, fps, (w, h))
    for i in range(frames):
        img = np.full((h, w, 3), 127, dtype=np.uint8)
        cv2.putText(img, str(i), (5, h//2), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1, cv2.LINE_AA)
        out.write(img)
    out.release()

def test_roundtrip(tmp_path):
    vid = str(tmp_path / "in.avi")
    out_dir = str(tmp_path / "frames")
    _make_dummy_video(vid)
    encode(vid, out_dir, "hello world")
    # decode directly from frames (robust path)
    msg = decode(out_dir)
    assert msg == "hello world"
