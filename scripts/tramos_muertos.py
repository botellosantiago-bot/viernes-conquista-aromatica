"""Ayuda de ritmo: encuentra tramos largos donde NO aparece nada nuevo en pantalla (ni gesto grande, ni texto, ni apoyo, ni corte).

  estudio/.venv/bin/python scripts/tramos_muertos.py <video.mp4> [--limite 8] [--subs 0.78-0.95] [--detalle] [--json]

Funciona con 16:9 y 9:16 (usa el tamaño real del cuadro). Por defecto avisa de más de 8 s sin novedad en 16:9 y de más de 4 s en 9:16.
Es un AVISO, no un veredicto: Arturo hablando a cámara con buena energía es contenido; el manual pide NO sobreeditar y conservar
el timing de comedia. Úsalo en videos largos para decidir dónde conviene un close-up del frasco o una ilustración, y MIRA los
cuadros del tramo antes de tocar nada.

Cómo mide: sigue puntos entre cuadros, ajusta un movimiento de cámara (zoom, paneo, giro, perspectiva) y compara lo que ese
movimiento NO explica. Lo que sobra es información nueva. --subs ignora la franja (en fracción del alto) donde viven los
subtítulos, que cambian solos y no cuentan como novedad.
"""
import argparse
import json
import os
import sys

os.environ.setdefault("OPENCV_LOG_LEVEL", "ERROR")
import cv2  # noqa: E402
import numpy as np  # noqa: E402

ALTO = 480
PASO = 1 / 6
DIF = 24  # diferencia de brillo (0-255) que ya no es ruido
UMBRAL_VIVO = 0.012  # fracción de la pantalla; una cara que habla mueve poco, por eso es más bajo que para pantallas gráficas


def alinear(previo, gris):
    pts = cv2.goodFeaturesToTrack(previo, 500, 0.01, 6)
    if pts is None or len(pts) < 12:
        return previo
    sig, ok, _ = cv2.calcOpticalFlowPyrLK(previo, gris, pts, None, winSize=(21, 21), maxLevel=3)
    ok = ok.ravel() == 1
    if ok.sum() < 12:
        return previo
    M, _ = cv2.findHomography(pts[ok], sig[ok], cv2.RANSAC, 2.0)
    if M is None:
        return previo
    return cv2.warpPerspective(previo, M, gris.shape[::-1], borderMode=cv2.BORDER_REPLICATE)


def medir(ruta, subs=None):
    cap = cv2.VideoCapture(ruta)
    if not cap.isOpened():
        sys.exit(f"no se pudo abrir {ruta}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    salto = max(1, round(PASO * fps))
    n, previo, filas = 0, None, []
    nucleo = np.ones((3, 3), np.uint8)
    formato = None
    while True:
        ok, cuadro = cap.read()
        if not ok:
            break
        if n % salto == 0:
            h0, w0 = cuadro.shape[:2]
            formato = (w0, h0)
            gris = cv2.cvtColor(cv2.resize(cuadro, (round(w0 * ALTO / h0), ALTO), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
            gris = cv2.GaussianBlur(gris, (5, 5), 0)
            if previo is not None:
                dif = cv2.absdiff(alinear(previo, gris), gris)
                mascara = cv2.morphologyEx((dif > DIF).astype(np.uint8), cv2.MORPH_OPEN, nucleo)
                if subs:
                    mascara[int(subs[0] * ALTO) : int(subs[1] * ALTO)] = 0
                filas.append((n / fps, float(mascara.mean())))
            previo = gris
        n += 1
    cap.release()
    return filas, n / fps, formato


def tramos(filas, duracion, limite):
    salida, ult = [], 0.0
    for t, vivo in filas + [(duracion, 1.0)]:
        if vivo >= UMBRAL_VIVO:
            if t - ult > limite:
                salida.append({"de": round(ult, 2), "a": round(t, 2), "dura": round(t - ult, 2)})
            ult = t
    return salida


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--limite", type=float, help="segundos sin novedad que ya merecen mirarse (8 en 16:9, 4 en 9:16)")
    ap.add_argument("--subs", default="0.78-0.95", help="franja de subtítulos a ignorar, en fracción del alto (ninguna: --subs 0-0)")
    ap.add_argument("--detalle", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    subs = tuple(float(x) for x in a.subs.split("-"))
    filas, dur, fmt = medir(a.video, subs if subs[1] > subs[0] else None)
    limite = a.limite or (8.0 if fmt and fmt[0] > fmt[1] else 4.0)
    muertos = tramos(filas, dur, limite)
    if a.json:
        print(json.dumps({"duracion": round(dur, 2), "limite": limite, "tramos": muertos}, ensure_ascii=False))
        sys.exit()
    if a.detalle:
        for t, v in filas:
            print(f"{t:6.2f}  {v * 100:5.1f}%  {'#' * min(60, int(v * 400))}")
    total = sum(m["dura"] for m in muertos)
    print(f"{dur:.1f} s de video ({fmt[0]}x{fmt[1]}) · {len(muertos)} tramos de más de {limite:g} s sin novedad · {total:.1f} s ({100 * total / max(dur, 0.1):.0f}%)")
    for m in muertos:
        print(f"  ! {m['de']:6.2f} - {m['a']:6.2f}  {m['dura']:.2f} s sin nada nuevo")
