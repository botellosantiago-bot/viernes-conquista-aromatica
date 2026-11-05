"""Masterizar el audio de un render: volumen parejo y picos bajo -1 dBTP.

  estudio/.venv/bin/python scripts/masterizar.py <entrada.mp4> <salida.mp4> [--lufs -16] [--tp -1.5]

Dos pasadas de loudnorm (la primera mide, la segunda aplica una ganancia LINEAL: no cambia la dinámica ni los tiempos) y un
limitador de seguridad. El video se copia sin recodificar. Esto es lo que garantiza "efectos sin saturación, picos bajo -1 dBTP".
"""
import argparse
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FF  # noqa: E402


def medir(ruta, lufs, tp):
    r = subprocess.run([FF, "-hide_banner", "-nostats", "-i", ruta, "-vn", "-af", f"loudnorm=I={lufs}:TP={tp}:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    if not m:
        sys.exit("No pude medir el volumen:\n" + r.stderr[-800:])
    return json.loads(m.group(0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada")
    ap.add_argument("salida")
    ap.add_argument("--lufs", type=float, default=-16.0)
    ap.add_argument("--tp", type=float, default=-1.5)
    a = ap.parse_args()
    m = medir(a.entrada, a.lufs, a.tp)
    print(f"Antes: {float(m['input_i']):.1f} LUFS, pico real {float(m['input_tp']):.1f} dBTP")
    limite = 10 ** ((a.tp - 0.3) / 20)  # limitador de seguridad un poco por debajo del objetivo
    filtro = (
        f"loudnorm=I={a.lufs}:TP={a.tp}:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
        f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true:print_format=summary,"
        f"alimiter=limit={limite:.4f}:attack=2:release=40:level=disabled"
    )
    tmp = a.salida + ".tmp.mp4"
    r = subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-i", a.entrada, "-map", "0:v", "-map", "0:a", "-c:v", "copy", "-af", filtro, "-ar", "48000", "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart", tmp], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("ffmpeg falló al masterizar:\n" + r.stderr[-1000:])
    os.replace(tmp, a.salida)
    print(f"Masterizado → {a.salida}")


if __name__ == "__main__":
    main()
