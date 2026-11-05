"""Sonidos hechos con numpy, sin muestras de terceros: riser, PUM, rayo, shimmer y un PSSHT de respaldo.

Se usan dos veces:
  1) para dejar el juego base en estudio/remotion/public/sfx/ (se corre una sola vez, ya está hecho):
        python scripts/sintetizar_sfx.py --base
  2) para hacer el riser y el PUM A LA MEDIDA de cada video (plan.py los pide con la duración exacta de la frase
     "el canal donde oler bien"), así el riser termina justo antes de "SIEMPRE" y no sobra ni falta.

Todo se escribe en WAV 48 kHz mono 16 bit. Los sonidos son generados aquí: no hay nada de terceros ni licencias que revisar.
"""
import argparse
import os
import sys
import wave

import numpy as np

SR = 48000
RNG = np.random.default_rng(20261104)  # semilla fija: el mismo sonido cada vez


def _t(dur):
    return np.arange(int(dur * SR)) / SR


def escribir(ruta, x, pico=0.9):
    x = np.asarray(x, dtype=np.float64)
    m = float(np.max(np.abs(x))) or 1.0
    x = np.clip(x / m * pico, -1, 1)
    os.makedirs(os.path.dirname(os.path.abspath(ruta)), exist_ok=True)
    with wave.open(ruta, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())
    return ruta


def _pasabajas_variable(x, fc):
    """Filtro de un polo con frecuencia de corte que cambia en el tiempo (fc es un arreglo por muestra)."""
    a = 1 - np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    s = 0.0
    for i in range(len(x)):
        s += a[i] * (x[i] - s)
        y[i] = s
    return y


def riser(dur=3.0):
    """Subida de tensión: barrido de tonos que sube y ruido que se abre. Termina en seco (fundido de 4 ms)."""
    t = _t(dur)
    k = t / dur
    f = 180 * (3200 / 180) ** (k**1.4)  # barrido exponencial 180 Hz -> 3.2 kHz
    fase = 2 * np.pi * np.cumsum(f) / SR
    tono = sum(np.sin(fase * m + p) * g for m, p, g in ((1, 0, 1.0), (1.005, 1.3, 0.6), (2.01, 0.7, 0.35)))
    ruido = RNG.standard_normal(len(t))
    ruido = _pasabajas_variable(ruido, 400 + 7000 * k**1.6)
    sube = 0.06 + 0.94 * k**1.7
    x = (0.55 * tono / 2.0 + 0.7 * ruido / (np.std(ruido) + 1e-9) * 0.35) * sube
    ataque = np.minimum(1, t / 0.12)
    x *= ataque
    corte = int(0.004 * SR)
    x[-corte:] *= np.linspace(1, 0, corte)
    return x


def pum(dur=1.1):
    """Golpe grave, corto y contundente: sub que cae de 70 a 38 Hz, cuerpo y un clic de ataque."""
    t = _t(dur)
    f = 38 + 36 * np.exp(-t / 0.07)
    fase = 2 * np.pi * np.cumsum(f) / SR
    cuerpo = np.sin(fase) * np.exp(-t / 0.32)
    armonico = np.sin(2 * fase) * np.exp(-t / 0.10) * 0.35
    clic = RNG.standard_normal(len(t)) * np.exp(-t / 0.006)
    clic = _pasabajas_variable(clic, np.full(len(t), 1800.0)) * 0.5
    x = cuerpo + armonico + clic
    x = np.tanh(1.8 * x) / np.tanh(1.8)
    x[: int(0.0015 * SR)] *= np.linspace(0, 1, int(0.0015 * SR))
    x *= np.minimum(1, (dur - t) / 0.15)
    return x


def rayo(dur=0.9):
    """Chisporroteo eléctrico: ráfagas de ruido agudo con compuertas aleatorias y un zumbido de red."""
    t = _t(dur)
    ruido = np.diff(RNG.standard_normal(len(t) + 1))  # pasa-altas simple
    compuerta = np.zeros(len(t))
    pos = 0
    while pos < len(t):
        largo = int(RNG.uniform(0.004, 0.03) * SR)
        compuerta[pos : pos + largo] = RNG.uniform(0.3, 1.0)
        pos += largo + int(RNG.uniform(0.002, 0.04) * SR)
    zumbido = np.sin(2 * np.pi * 120 * t) * 0.25 + np.sin(2 * np.pi * 360 * t) * 0.12
    env = np.exp(-t / 0.35) * np.minimum(1, t / 0.004)
    x = (ruido * compuerta * 0.6 + zumbido * compuerta) * env
    x = np.tanh(2.2 * x)
    x *= np.minimum(1, (dur - t) / 0.08)
    return x


def shimmer(dur=1.8):
    """Destello suave: parciales agudos que aparecen escalonados y se apagan (nada de tráiler de acción)."""
    t = _t(dur)
    base = np.array([1318.5, 1568.0, 1975.5, 2349.3, 2637.0, 3136.0, 3951.1])  # mi sol si re mi sol si
    x = np.zeros(len(t))
    for i, f in enumerate(base):
        inicio = 0.03 * i
        tt = np.clip(t - inicio, 0, None)
        env = (tt > 0) * np.minimum(1, tt / 0.01) * np.exp(-tt / (0.45 - 0.03 * i))
        x += np.sin(2 * np.pi * f * t + i) * env * (0.5 + 0.5 * RNG.random())
    brillo = np.diff(RNG.standard_normal(len(t) + 1)) * np.exp(-t / 0.12) * 0.08
    x += brillo
    x *= np.minimum(1, (dur - t) / 0.2)
    return x


def psst(dur=0.32):
    """PSSHT de respaldo (aire a presión). El kit usa los PSSHT grabados CC0; este solo cubre si faltaran."""
    t = _t(dur)
    r = np.diff(RNG.standard_normal(len(t) + 1))
    r = _pasabajas_variable(r, np.full(len(t), 9000.0))
    env = np.minimum(1, t / 0.012) * np.exp(-t / 0.13)
    return r * env


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", action="store_true", help="deja los sonidos base en estudio/remotion/public/sfx/")
    ap.add_argument("--riser", type=float, help="riser con esta duración (s)")
    ap.add_argument("--pum", action="store_true")
    ap.add_argument("--salida", help="ruta del WAV para --riser / --pum")
    a = ap.parse_args()
    if a.base:
        d = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "estudio", "remotion", "public", "sfx")
        escribir(os.path.join(d, "riser-sint-3s.wav"), riser(3.0), 0.8)
        escribir(os.path.join(d, "pum-sint.wav"), pum(), 0.95)
        escribir(os.path.join(d, "rayo-sint.wav"), rayo(), 0.8)
        escribir(os.path.join(d, "shimmer-sint.wav"), shimmer(), 0.7)
        escribir(os.path.join(d, "psst-sint.wav"), psst(), 0.8)
        print("listo:", d)
    elif a.riser and a.salida:
        escribir(a.salida, riser(a.riser), 0.8)
    elif a.pum and a.salida:
        escribir(a.salida, pum(), 0.95)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
