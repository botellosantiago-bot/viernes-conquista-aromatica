"""Crea la carpeta de un video nuevo de Arturo.

  python scripts/nuevo.py <slug>

Deja videos/<slug>/ con:
  crudo/     aquí van los clips originales (nunca se modifican ni se borran)
  work/      análisis, palabras, video base y todo lo intermedio
  out/       las entregas (primer corte y final)
  apoyo/     fotos, ilustraciones y close-ups que Arturo pase (opcional)
  musica/    pistas con licencia de este video, si no están en estudio/remotion/public/musica (opcional)
El slug va en minúsculas y sin espacios: por ejemplo  resena-sauvage  o  live-2026-11-08.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import VIDEOS  # noqa: E402


def main():
    if len(sys.argv) != 2 or not re.fullmatch(r"[a-z0-9][a-z0-9\-]*", sys.argv[1]):
        sys.exit(__doc__)
    slug = sys.argv[1]
    for d in ("crudo", "work", "out", "apoyo", "musica"):
        os.makedirs(os.path.join(VIDEOS, slug, d), exist_ok=True)
    print(f"Listo: videos/{slug}/  (pon los originales en videos/{slug}/crudo/)")


if __name__ == "__main__":
    main()
