"""Paso 3: quitar pausas muertas CONSERVANDO el timing de comedia, y sacar las palabras en tiempo final.

  estudio/.venv/bin/python scripts/cut.py <slug> [--sin-cortes] [--modelo medium] [--max-lado 2560]

Deja en videos/<slug>/work/:
  base.mp4            el video ya cortado: 30 fps constantes, voz limpia y nivelada (aprox. -18 LUFS, el master final la sube)
  palabras.json       las palabras con tiempos en el video final (es lo que se oye, transcrito de base.mp4)
  palabras_raw.json   copia de la transcripción original (words.py fix parte de ella)
  cortes.json         de dónde salió cada pieza
  informe_cortes.md   qué pausas se acortaron, cuáles se respetaron y qué revisar

Si no existe videos/<slug>/edl.json se usa el clip entero y solo se acortan las pausas MUY largas. edl.json:
{
  "max_pausa": 0.9,         pausas más largas que esto se acortan (las más cortas no se tocan: es el ritmo de Arturo)
  "pausa_objetivo": 0.5,    a cuánto se dejan
  "antes": 0.10, "despues": 0.18,   aire que se deja alrededor de cada corte (s)
  "conservar": [[12.1, 13.4]],      tramos del ORIGINAL donde no se toca nada (el silencio antes de un remate, una mirada)
  "keep": [ {"clip": "IMG_0001.MOV", "in": 2.0, "out": 80.5, "nota": "toma buena"} ],   si falta: cada clip entero
  "quitar": [ {"clip": "IMG_0001.MOV", "de": 31.0, "a": 36.2, "nota": "retoma"} ]        tramos que se eliminan del todo
}
Siempre se respeta, sin tocar, la pausa entre «el canal donde oler bien» y «SIEMPRE» (es parte de la firma).
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze import clips_de  # noqa: E402
from common import FPS, cargar, envolvente, existe_video, ff, filtro_desde_archivo, guardar, probe, transcribir, vdir, VIDEOS  # noqa: E402

UMBRAL_VOZ = -48.0
AF_VOZ = (
    "highpass=f=80,afftdn=nr=8:nf=-35,equalizer=f=250:t=q:w=1:g=-1.2,equalizer=f=3500:t=q:w=1.2:g=1.8,"
    "acompressor=threshold=-21dB:ratio=3:attack=8:release=120:makeup=3,loudnorm=I=-18:TP=-3:LRA=11"
)


def pausas_en(db, a, b, minimo):
    """Silencios >= minimo dentro de [a, b]: lista de (inicio, fin)."""
    out, i, ia, ib = [], int(a * 100), int(a * 100), int(b * 100)
    ib = min(ib, len(db))
    while i < ib:
        if db[i] <= UMBRAL_VOZ:
            j = i
            while j < ib and db[j] <= UMBRAL_VOZ:
                j += 1
            if (j - i) / 100 >= minimo and i > ia + 5 and j < ib - 5:
                out.append((i / 100, j / 100))
            i = j
        else:
            i += 1
    return out


def solapa(a, b, ventanas):
    return any(a < w1 and b > w0 for w0, w1 in ventanas)


def piezas_de(clip, ruta, desde, hasta, edl, protegidas):
    db = envolvente(ruta)
    total = probe(ruta)["duracion"]
    hasta = min(hasta, total)
    quitar = [(q["de"], q["a"]) for q in edl.get("quitar", []) if q["clip"] == clip]
    conservar = [tuple(w) for w in edl.get("conservar", [])] + protegidas
    max_pausa = edl.get("max_pausa", 0.9)
    objetivo = edl.get("pausa_objetivo", 0.5)
    infor = {"acortadas": [], "respetadas": []}
    cortes = []  # (a, b) a eliminar del tramo
    for pa, pb in pausas_en(db, desde, hasta, max_pausa):
        if solapa(pa, pb, conservar):
            infor["respetadas"].append((pa, pb))
            continue
        sobra = (pb - pa) - objetivo
        mitad = objetivo / 2
        cortes.append((pa + mitad, pb - mitad))
        infor["acortadas"].append((pa, pb, sobra))
    cortes += quitar
    cortes.sort()
    # unir cortes que se tocan y fabricar las piezas que quedan
    fus = []
    for a, b in cortes:
        if fus and a <= fus[-1][1] + 0.01:
            fus[-1] = (fus[-1][0], max(fus[-1][1], b))
        else:
            fus.append((a, b))
    piezas, cur = [], desde
    for a, b in fus:
        if a - cur > 0.15:
            piezas.append((cur, a))
        cur = max(cur, b)
    if hasta - cur > 0.15:
        piezas.append((cur, hasta))
    return [(round(x, 3), round(y, 3)) for x, y in piezas], infor


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--sin-cortes", action="store_true", help="no acortar ninguna pausa (solo normalizar)")
    ap.add_argument("--modelo", default="medium")
    ap.add_argument("--max-lado", type=int, default=2560, help="lado largo máximo del video base")
    a = ap.parse_args()
    existe_video(a.slug)
    work = vdir(a.slug, "work")
    base = os.path.join(work, "base.mp4")
    clips = clips_de(a.slug)
    if not clips:
        sys.exit(f"No hay videos en videos/{a.slug}/crudo/")
    ruta_edl = os.path.join(VIDEOS, a.slug, "edl.json")
    edl = cargar(ruta_edl) if os.path.exists(ruta_edl) else {}
    if a.sin_cortes:
        edl = {**edl, "max_pausa": 1e9}
    por_nombre = {os.path.basename(c): c for c in clips}
    ana = cargar(os.path.join(work, "analisis.json")) if os.path.exists(os.path.join(work, "analisis.json")) else {"clips": {}}
    keeps = edl.get("keep") or [{"clip": n, "in": 0.0, "out": probe(r)["duracion"]} for n, r in por_nombre.items()]

    plan, informe = [], ["# Informe de cortes\n"]
    for k in keeps:
        nombre = k["clip"]
        if nombre not in por_nombre:
            sys.exit(f"edl.json menciona «{nombre}» y no está en crudo/")
        ruta = por_nombre[nombre]
        prot = []
        for x in ana["clips"].get(nombre, {}).get("firma", {}).get("oler_bien", []):
            prot.append((x["bien_fin"] - 0.05, x["siempre"] + 0.05))
        piezas, inf = piezas_de(nombre, ruta, k.get("in", 0.0), k.get("out", 1e9), edl, prot)
        for pa, pb in piezas:
            plan.append({"clip": nombre, "ruta": ruta, "in": pa, "out": pb, "nota": k.get("nota", "")})
        informe.append(f"## {nombre}\n")
        informe.append(f"- {len(piezas)} piezas. Pausas acortadas: {len(inf['acortadas'])}; respetadas (timing/firma): {len(inf['respetadas'])}")
        informe += [f"  - acortada {x:.2f}–{y:.2f} s (se quitaron {s:.2f} s)" for x, y, s in inf["acortadas"]]
        informe += [f"  - RESPETADA {x:.2f}–{y:.2f} s" for x, y in inf["respetadas"]]
        informe.append("")
    if not plan:
        sys.exit("No quedó nada que exportar. Revisa edl.json")

    # tamaño del video base: el del primer clip, sin pasar de --max-lado
    p0 = probe(plan[0]["ruta"])
    W, H = p0["ancho_visible"], p0["alto_visible"]
    esc = min(1.0, a.max_lado / max(W, H))
    W, H = int(W * esc) // 2 * 2, int(H * esc) // 2 * 2
    entradas, fc, etiquetas = [], [], []
    idx = {}
    for pz in plan:
        if pz["ruta"] not in idx:
            idx[pz["ruta"]] = len(idx)
            entradas += ["-i", pz["ruta"]]
    for n, pz in enumerate(plan):
        i = idx[pz["ruta"]]
        dur = pz["out"] - pz["in"]
        fc.append(
            f"[{i}:v]trim=start={pz['in']:.3f}:end={pz['out']:.3f},setpts=PTS-STARTPTS,fps={FPS},"
            f"scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,setsar=1,format=yuv420p[v{n}]"
        )
        fc.append(
            f"[{i}:a]atrim=start={pz['in']:.3f}:end={pz['out']:.3f},asetpts=PTS-STARTPTS,aresample=48000,"
            f"aformat=channel_layouts=stereo,afade=t=in:d=0.004,afade=t=out:st={max(0, dur - 0.004):.4f}:d=0.004[a{n}]"
        )
        etiquetas.append(f"[v{n}][a{n}]")
    fc.append("".join(etiquetas) + f"concat=n={len(plan)}:v=1:a=1[vc][ac]")
    fc.append(f"[ac]{AF_VOZ},aresample=48000[ao]")
    guion = base + ".filtros.txt"
    with open(guion, "w") as f:
        f.write(";\n".join(fc))
    print(f"Exportando {len(plan)} piezas a {W}x{H}…", flush=True)
    ff(*entradas, *filtro_desde_archivo(guion), "-map", "[vc]", "-map", "[ao]", "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
       "-g", "15", "-keyint_min", "15", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", base)
    os.remove(guion)
    d = probe(base)["duracion"]
    t = 0.0
    tl = []
    for pz in plan:
        tl.append({"clip": pz["clip"], "origen_de": pz["in"], "origen_a": pz["out"], "final_de": round(t, 3), "nota": pz["nota"]})
        t += pz["out"] - pz["in"]
    guardar(tl, os.path.join(work, "cortes.json"))

    print("Transcribiendo el video final…", flush=True)
    palabras, lineas = transcribir(base, a.modelo)
    guardar({"words": palabras, "lineas": lineas}, os.path.join(work, "palabras_raw.json"))
    guardar({"words": palabras, "lineas": lineas}, os.path.join(work, "palabras.json"))
    origen = sum(probe(r)["duracion"] for r in {pz["ruta"]: 0 for pz in plan})
    informe.append(f"\nDuración del video base: {d:.1f} s ({len(palabras)} palabras). Material de origen: {origen:.1f} s.")
    informe.append("Revisa mirando los cuadros alrededor de cada corte: Whisper no oye todo y una pausa corta a veces es el chiste.")
    with open(os.path.join(work, "informe_cortes.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(informe) + "\n")
    print(f"Listo: {base} ({d:.1f} s, {len(palabras)} palabras) — informe en work/informe_cortes.md")


if __name__ == "__main__":
    main()
