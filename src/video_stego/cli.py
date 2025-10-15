from __future__ import annotations
import os
import shutil
import subprocess
import click
from .encode import encode as _encode
from .decode import decode as _decode

def _have_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None

@click.group()
def main():
    
@main.command("encode")
@click.option("--in", "in_video", required=True, type=click.Path(exists=True, dir_okay=False), help="Vidéo source")
@click.option("--out-frames", required=True, type=click.Path(file_okay=False), help="Dossier de PNG encodés")
@click.option("--text", required=True, type=str, help="Message texte à cacher (UTF-8)")
@click.option("--repack", "repack_video", required=False, type=click.Path(dir_okay=False), help="Sortie vidéo (optionnel, nécessite ffmpeg)")
@click.option("--fps", required=False, type=float, help="Forcer FPS lors du repack (sinon déduit de la vidéo)")
def encode_cmd(in_video, out_frames, text, repack_video, fps):
    \"\"\"Encode un message dans la vidéo (via frames PNG).\"\"\"
    _encode(in_video, out_frames, text)
    click.echo(f\"Frames encodées -> {out_frames}\")
    if repack_video:
        if not _have_ffmpeg():
            raise click.ClickException(\"ffmpeg introuvable. Installez-le ou omettez --repack.\")
        # Déduire FPS via ffprobe si présent, sinon utiliser --fps ou fallback 25
        use_fps = fps or 25
        # Repack lossless (FFV1) pour préserver les LSB
        cmd = [
            "ffmpeg",
            "-y",
            "-framerate", str(use_fps),
            "-i", os.path.join(out_frames, "frame_%06d.png"),
            "-c:v", "ffv1",
            repack_video,
        ]
        click.echo(\"Repack vidéo (lossless FFV1)…\")
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            raise click.ClickException(f\"ffmpeg a échoué: {e.stderr.decode('utf-8', 'ignore')}\")
        click.echo(f\"Vidéo écrite -> {repack_video}\")

@main.command("decode")
@click.option("--in", "in_path", required=True, type=click.Path(exists=True), help="Vidéo ou dossier de frames PNG")
def decode_cmd(in_path):
    \"\"\"Décode et affiche le message encodé.\"\"\"
    try:
        msg = _decode(in_path)
    except Exception as e:
        raise click.ClickException(str(e))
    click.echo(msg)
