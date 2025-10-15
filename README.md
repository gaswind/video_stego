# video-stego — Encoder une phrase dans une vidéo (qualitatif)

> **But** : un outil propre et documenté pour cacher un message texte dans une vidéo, avec CLI, tests, CI, et notes de sécu/stéganalyse.

## ✨ Points clés qualité
- **Architecture claire** : lib Python + CLI (`video-stego`) + tests.
- **Robustesse** : en-tête avec *magic*, longueur et `CRC32` pour valider l’extraction.
- **Formats sûrs** : encode d’abord dans une **séquence d’images PNG** (lossless), puis *optionnellement* repackage en vidéo (via `ffmpeg`).
- **Capacité** : 1 bit par pixel (canal bleu). Capacité ≈ `frames * width * height / 8` octets (hors en-tête).
- **CI** : workflow GitHub Actions qui lance les tests.
- **Doc** : ce README, docstring, commentaires.

> ⚠️ **Important** : l’encodeur écrit des **PNG** pour préserver les bits (LSB). La recompression vidéo peut détruire l’info si le codec est *lossy*. Utiliser un codec **sans perte** (ex. `-c:v ffv1`) lors du repackage.

---

## Installation

```bash
# 1) Environnement Python (3.10+)
python -m venv .venv && source .venv/bin/activate

# 2) Dépendances
pip install -r requirements.txt

# 3) (Optionnel) install du package en mode dev
pip install -e .
```

### Dépendances système
- `ffmpeg` recommandé pour recompiler les PNG en vidéo finale :
  ```bash
  sudo apt-get install -y ffmpeg
  ```

---

## Utilisation rapide

### 1) Encoder un message
```bash
video-stego encode --in sample.mp4 --out-frames out_frames --text "Salut EPITA 2025" --repack out_lossless.mkv
```
- `--in` : vidéo source (sera **lue**, pas modifiée)
- `--out-frames` : dossier de sortie des PNG encodés
- `--text` : message à cacher (UTF‑8)
- `--repack` (optionnel) : crée une vidéo à partir des PNG (nécessite `ffmpeg` installé)

> Sans `--repack`, vous obtenez juste une séquence d’images.

### 2) Décoder un message
Depuis une **vidéo** (⚠️ codecs *lossy* = risque d’échec) :
```bash
video-stego decode --in out_lossless.mkv
```
Ou directement depuis le **dossier de PNG** :
```bash
video-stego decode --in out_frames
```

---

## Comment ça marche (résumé)
- On convertit la vidéo en frames (OpenCV) puis on écrit des **PNG**.
- On réserve un **en-tête** : `MAGIC="VSTEGO1" + uint32(message_len) + uint32(crc32)`
- On écrit les bits (header + message) dans le **bit de poids faible (LSB)** du canal **bleu** de chaque pixel, frame par frame, ligne par ligne.
- À la lecture, on récupère d’abord l’entête, puis on lit `message_len` octets et on vérifie le `CRC32`.

### Capacité approximative
```
capacité_octets ≈ (nb_frames * largeur * hauteur) / 8 - overhead
overhead ≈ 7 (MAGIC) + 4 (len) + 4 (crc) = 15 octets
```
> Exemple : 600 frames en 1280×720 ⇒ 600 * 921,600 / 8 ≈ **69 Mo** bruts possibles (théorique).

---

## Sécurité & stéganalyse (honnête)
- **LSB** est simple mais **détectable** par des analyses statistiques (RS, χ²). Évitez les contenus publics sensibles.
- Les **codecs avec perte** détruisent souvent les LSB. Utiliser PNG ou vidéo **sans perte** (FFV1, HuffYUV).
- Ajouter (futur) :
  - *Bit spreading* ou *whitening* (PRNG) pour mieux « mixer » les bits.
  - ECC (Hamming/Reed–Solomon) pour corriger des flips légers.
  - Modulation DCT (JPEG-like) ou motion vectors (plus avancé).

---

## Qualité logicielle
- **Tests** `pytest` : round‑trip basique.
- **Type hints** : `mypy` (optionnel).
- **Lint/format** : `ruff`, `black` (optionnels).

Lancez les tests :
```bash
pytest -q
```

---

## Roadmap
- [ ] Mode PRNG (clé) pour diffuser les bits de manière pseudo-aléatoire.
- [ ] ECC (Hamming 7,4) pour tolérer un peu de perte/compression.
- [ ] Backend DCT (robuste mais plus complexe).
- [ ] Benchmarks capacité/robustesse/détection.

---

## Licence
MIT — faites-en bon usage, de façon légale et éthique.
