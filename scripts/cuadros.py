"""Hojas de cuadros para MIRAR el video (con zonas seguras) y medir dónde está la cara y el frasco.

  python scripts/cuadros.py <video> <salida.jpg> t1 t2 t3 ...        # cuadros en esos segundos
  python scripts/cuadros.py <video> <salida.jpg> --cada 5            # un cuadro cada 5 s
  opciones:  --formato 16:9|9:16   (qué zonas seguras dibujar; por defecto el del propio video)
             --cols 4   --ancho 480   --sin-guias

Guías: verde = zona segura de texto del formato; naranja = lo que queda a la vista si un video 16:9 se recorta a 9:16
(centrado en el "foco" del plan; aquí 0.5). Cada cuadro lleva su segundo.
"""
import argparse
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FF, probe  # noqa: E402

# Zona segura de texto (en px del lienzo): izquierda, arriba, derecha, abajo
SEGURA = {"16:9": (96, 54, 1824, 1026), "9:16": (80, 250, 900, 1500)}
LIENZO = {"16:9": (1920, 1080), "9:16": (1080, 1920)}


def cuadro(video, t, ancho, fmt, guias=True, foco=0.5):
    from PIL import Image, ImageDraw

    with tempfile.TemporaryDirectory() as tmp:
        f = os.path.join(tmp, "f.jpg")
        subprocess.run([FF, "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1", "-vf", f"scale={ancho}:-2", f], check=True)
        im = Image.open(f).convert("RGB")
    w, h = im.size
    d = ImageDraw.Draw(im)
    if guias:
        lw, lh = LIENZO[fmt]
        k = w / lw
        l, t0, r, b = (v * k for v in SEGURA[fmt])
        d.rectangle([l, t0, r, b], outline=(60, 240, 180), width=2)
        if fmt == "16:9":  # lo que sobrevive al recorte 9:16
            cw = h * 9 / 16
            x0 = max(0, min(w - cw, foco * w - cw / 2))
            d.rectangle([x0, 1, x0 + cw, h - 2], outline=(255, 160, 40), width=2)
    d.rectangle([0, h - 16, 54, h], fill=(20, 12, 8))
    d.text((3, h - 14), f"{t:.1f}s", fill=(255, 210, 120))
    return im


def hoja(video, tiempos, salida, ancho=480, cols=4, fmt=None, guias=True):
    from PIL import Image

    if fmt is None:
        p = probe(video)
        fmt = "9:16" if p["vertical"] else "16:9"
    tiles = [cuadro(video, t, ancho, fmt, guias) for t in tiempos]
    w, h = tiles[0].size
    filas = (len(tiles) + cols - 1) // cols
    hoja_ = Image.new("RGB", (cols * w, filas * h), (20, 12, 8))
    for i, im in enumerate(tiles):
        hoja_.paste(im, ((i % cols) * w, (i // cols) * h))
    os.makedirs(os.path.dirname(os.path.abspath(salida)), exist_ok=True)
    hoja_.save(salida, quality=85)
    return salida


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("salida")
    ap.add_argument("tiempos", nargs="*", type=float)
    ap.add_argument("--cada", type=float)
    ap.add_argument("--formato")
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--ancho", type=int, default=480)
    ap.add_argument("--sin-guias", action="store_true")
    a = ap.parse_args()
    ts = a.tiempos
    if a.cada:
        dur = probe(a.video)["duracion"]
        ts = [round(i * a.cada + 0.2, 2) for i in range(int(dur // a.cada) + 1) if i * a.cada + 0.2 < dur]
    if not ts:
        sys.exit(__doc__)
    print(hoja(a.video, ts, a.salida, a.ancho, a.cols, a.formato, not a.sin_guias))


if __name__ == "__main__":
    main()
