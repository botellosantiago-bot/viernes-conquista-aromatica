"""Paso 1: analizar el material de un video ANTES de proponer nada.

  estudio/.venv/bin/python scripts/analyze.py <slug> [--modelo medium]

Lee los clips de videos/<slug>/crudo/ (en orden de nombre) y deja:
  videos/<slug>/analisis.md          resumen: tamaño y formato, transcripción por frases, pausas candidatas, repeticiones,
                                     frases de firma encontradas y lo que falta pedirle a Arturo
  videos/<slug>/work/analisis.json   lo mismo, para los otros scripts
  videos/<slug>/work/contacto_<clip>.jpg   hoja de cuadros con zonas seguras (para MIRAR cara, frasco y manos)
No corta nada. Que una pausa salga listada no significa que haya que quitarla: puede ser el timing de un chiste.
"""
import argparse
import glob
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from anclas import detectar_firma  # noqa: E402
from common import FF, PROMPT_CANAL, existe_video, envolvente, guardar, norm, probe, transcribir, vdir, VIDEOS  # noqa: E402

EXT = (".mov", ".mp4", ".m4v", ".mkv")
UMBRAL_VOZ = -48.0  # dBFS: por debajo no hay voz
STOP = {"la", "de", "el", "que", "y", "a", "en", "lo", "los", "las", "un", "una", "es", "no", "se", "me", "te", "tu", "mi"}


def clips_de(slug):
    cr = os.path.join(VIDEOS, slug, "crudo")
    return sorted(f for f in glob.glob(os.path.join(cr, "*")) if f.lower().endswith(EXT) and not os.path.basename(f).startswith("."))


def pausas(ruta, palabras, minimo=0.5):
    """Silencios >= minimo con la palabra anterior y la siguiente (para decidir si son timing de comedia)."""
    db = envolvente(ruta)
    voz = db > UMBRAL_VOZ
    salida, i = [], 0
    while i < len(voz):
        if not voz[i]:
            j = i
            while j < len(voz) and not voz[j]:
                j += 1
            if (j - i) / 100 >= minimo and i > 0 and j < len(voz):
                a, b = i / 100, j / 100
                antes = next((w["w"] for w in reversed(palabras) if w["e"] <= a + 0.15), "")
                despues = next((w["w"] for w in palabras if w["s"] >= b - 0.15), "")
                salida.append({"de": round(a, 2), "a": round(b, 2), "dura": round(b - a, 2), "antes": antes, "despues": despues})
            i = j
        else:
            i += 1
    return salida


def repeticiones(palabras):
    """Frases de 3 palabras que se repiten pronto: posibles retomas (el mismo tramo grabado dos veces)."""
    toks = [(norm(w["w"]), w["s"]) for w in palabras if norm(w["w"])]
    visto, rep = {}, []
    for k in range(len(toks) - 2):
        g = tuple(t for t, _ in toks[k : k + 3])
        if sum(t in STOP for t in g) >= 2:
            continue
        t0 = toks[k][1]
        if g in visto and 0 < t0 - visto[g] < 8:
            rep.append({"frase": " ".join(g), "primera": visto[g], "segunda": t0})
        visto[g] = t0
    return rep


def cortes_existentes(ruta, umbral=0.18):
    log = subprocess.run([FF, "-hide_banner", "-i", ruta, "-vf", f"select='gt(scene,{umbral})',showinfo", "-f", "null", "-"], capture_output=True, text=True).stderr
    return [round(float(x), 2) for x in re.findall(r"pts_time:([0-9.]+)", log)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--modelo", default="medium", help="tiny/base/small/medium/large-v3-turbo (medium por defecto; small para pruebas)")
    a = ap.parse_args()
    existe_video(a.slug)
    clips = clips_de(a.slug)
    if not clips:
        sys.exit(f"No hay videos en videos/{a.slug}/crudo/. Pídele a Arturo el video y ponlo ahí.")
    work = vdir(a.slug, "work")
    md = [f"# Análisis de {a.slug}\n"]
    todo = {"clips": {}}
    avisos = []
    from cuadros import hoja

    for c in clips:
        nombre = os.path.basename(c)
        p = probe(c)
        print(f"[{nombre}] {p['ancho_visible']}x{p['alto_visible']} {p['fps']} fps {p['duracion']:.1f} s — transcribiendo…", flush=True)
        if not p["audio"]:
            avisos.append(f"{nombre}: NO tiene audio. Sin voz no hay reseña que editar; pídele el archivo original.")
        palabras, lineas = transcribir(c, a.modelo)
        paus = pausas(c, palabras)
        rep = repeticiones(palabras)
        cortes = cortes_existentes(c)
        paso = max(2.0, p["duracion"] / 24)
        ts = [round(i * paso + paso / 2, 2) for i in range(24) if i * paso + paso / 2 < p["duracion"]]
        fmt = "9:16" if p["vertical"] else "16:9"
        hoja(c, ts, os.path.join(work, f"contacto_{os.path.splitext(nombre)[0]}.jpg"), ancho=360, cols=6, fmt=fmt)
        firma, av = detectar_firma(palabras)
        todo["clips"][nombre] = {"info": p, "palabras": palabras, "lineas": lineas, "pausas": paus, "repeticiones": rep, "cortes_existentes": cortes, "firma": firma}
        avisos += [f"{nombre}: {x}" for x in av]
        if not p["vertical"] and p["alto_visible"] < 1440:
            avisos.append(f"{nombre}: es horizontal de {p['alto_visible']}p. Para Shorts/Reels el recorte 9:16 sale con poca resolución; si puede, que grabe vertical o en 4K.")
        if p["vertical"]:
            avisos.append(f"{nombre}: es vertical. Sirve para 9:16; para 16:9 quedaría con barras o muy recortado, y no se debe estirar.")

        md.append(f"## {nombre}\n")
        md.append(f"- {p['ancho_visible']}x{p['alto_visible']} ({'vertical' if p['vertical'] else 'horizontal'}), {p['fps']} fps, {p['duracion']:.1f} s, audio: {'sí' if p['audio'] else 'NO'}")
        md.append(f"- Hoja de cuadros: `work/contacto_{os.path.splitext(nombre)[0]}.jpg` (verde = zona segura; naranja = lo que queda a la vista en 9:16)")
        md.append(f"- Cortes que ya trae: {len(cortes)}")
        md.append(f"- Palabras: {len(palabras)}\n")
        md.append("| inicio | fin | frase |\n|---:|---:|---|")
        md += [f"| {l['s']:.2f} | {l['e']:.2f} | {l['texto']} |" for l in lineas]
        md.append("")
        if paus:
            md.append("Pausas de 0.5 s o más (¿silencio muerto o timing de comedia? Se decide mirando, no por el número):")
            md += [f"- {x['de']:.2f}–{x['a']:.2f} ({x['dura']:.1f} s) entre «{x['antes']}» y «{x['despues']}»" for x in paus]
            md.append("")
        if rep:
            md.append("Posibles retomas (frase que se repite pronto):")
            md += [f"- «{r['frase']}» a {r['primera']:.1f}s y a {r['segunda']:.1f}s" for r in rep]
            md.append("")
        md.append("Frases de firma encontradas:")
        ap_ = ", ".join("%.1fs" % x["t"] for x in firma["aplausos"]) or "no"
        md.append("- «Conquista Aromática» (aplausos): " + ap_)
        md.append("- «El canal donde oler bien… SIEMPRE»: " + (", ".join("%.1fs -> siempre %.1fs" % (x["inicio"], x["siempre"]) for x in firma["oler_bien"]) or "no"))
        cz = firma["cierre"]
        if cz:
            mg = cz.get("megafono")
            mg_t = ("%.2f-%.2fs «%s»" % (mg["s"], mg["e"], mg["texto"])) if mg else "no"
            md.append("- Cierre: empieza %.1fs; megáfono %s" % (cz["inicio"], mg_t))
        else:
            md.append("- Cierre: no")
        rz = firma["rafaguiza"]
        md.append("- Rafaguiza: " + (("«%s» a %.1fs" % (rz["texto"], rz["inicio"])) if rz else "no"))
        md.append("")

    md.append("## Avisos y lo que falta pedirle a Arturo\n")
    md += [f"- {x}" for x in avisos] or ["- Nada raro."]
    md.append("- Pregúntale siempre: nombre exacto del perfume y la casa, notas que SÍ quiere mencionar, si tiene fotos o close-ups del frasco, y si hay música con licencia.")
    todo["avisos"] = avisos
    todo["prompt"] = PROMPT_CANAL
    guardar(todo, os.path.join(work, "analisis.json"))
    with open(os.path.join(VIDEOS, a.slug, "analisis.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print(f"\nListo → videos/{a.slug}/analisis.md")
    for x in avisos:
        print(" •", x)


if __name__ == "__main__":
    main()
