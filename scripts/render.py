"""Renderizar un video de Arturo (plan -> Remotion -> master de audio).

  estudio/.venv/bin/python scripts/render.py <slug> --formato 16:9|9:16 [--entrega primer-corte|final|borrador] [--stems]

  --entrega    primer-corte (por defecto): para revisar ritmo y chistes. final: la versión limpia. borrador: media resolución, rápido.
  --stems      además saca el audio por partes (voz, fx, musica, cuerdas) en work/stems-<formato>/ para medirlo en QA
Siempre corre antes plan.py (es barato) para que lo que se renderiza sea lo último que decidió el plan.
Salida: videos/<slug>/out/<slug>-<16x9|9x16>-<entrega>.mp4
"""
import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FORMATOS, PY, REMOTION, VIDEOS, existe_video, formato, vdir  # noqa: E402


def node(*args):
    r = subprocess.run(["node", os.path.join("scripts", "render.mjs"), *args], cwd=REMOTION)
    if r.returncode != 0:
        sys.exit("El render falló (mira el mensaje de arriba).")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--formato", required=True)
    ap.add_argument("--entrega", default="primer-corte", choices=["primer-corte", "final", "borrador"])
    ap.add_argument("--stems", action="store_true")
    ap.add_argument("--sin-plan", action="store_true", help="no volver a correr plan.py")
    a = ap.parse_args()
    existe_video(a.slug)
    fmt = formato(a.formato)
    info = FORMATOS[fmt]
    if not a.sin_plan:
        r = subprocess.run([PY, os.path.join(os.path.dirname(os.path.abspath(__file__)), "plan.py"), a.slug])
        if r.returncode != 0:
            sys.exit("plan.py encontró errores: corrígelos antes de renderizar.")
    out = vdir(a.slug, "out")
    work = vdir(a.slug, "work")
    crudo = os.path.join(work, f"render-{info['etiqueta']}.mp4")
    final = os.path.join(out, f"{a.slug}-{info['etiqueta']}-{a.entrega}.mp4")
    args = [info["id"], a.slug, crudo] + (["--borrador"] if a.entrega == "borrador" else [])
    node(*args)
    r = subprocess.run([PY, os.path.join(os.path.dirname(os.path.abspath(__file__)), "masterizar.py"), crudo, final])
    if r.returncode != 0:
        sys.exit("El master de audio falló.")
    if a.stems:
        sd = os.path.join(work, f"stems-{info['etiqueta']}")
        os.makedirs(sd, exist_ok=True)
        node(info["id"], a.slug, "--stems-dir", sd)
    print(f"\nListo: {final}")


if __name__ == "__main__":
    main()
