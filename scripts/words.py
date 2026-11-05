"""Ver y corregir las palabras del video final (subtítulos revisados a mano: marcas, perfumes y notas bien escritos).

  estudio/.venv/bin/python scripts/words.py ver <slug>        # palabras numeradas con tiempos, por renglones
  estudio/.venv/bin/python scripts/words.py corregir <slug>   # aplica videos/<slug>/fixes.json sobre la transcripción original

fixes.json (ortografía fiel: acentos, ñ, ¿¡, mayúsculas, nombres propios):
{
  "reemplazar": {"sovash": "Sauvage", "dior": "Dior"},     por palabra normalizada (sin acentos ni signos)
  "poner": {"5": "Hermosas"},                              por número (ver `ver`)
  "unir": [[12, 13, "Eau de Parfum"]],                     une palabras partidas (del número al número)
  "quitar": [40],                                          muletillas fantasma o alucinaciones
  "insertar": [[153, "último,", 43.16, 43.38]],            una palabra que Whisper se comió: va ANTES del número dado
  "tiempo": {"16": [3.90, 4.40]},                          corrige tiempos absurdos
}
Los números son los de `ver` ANTES de corregir. Es idempotente: siempre parte de palabras_raw.json.
Después de corregir hay que volver a correr plan.py.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cargar, existe_video, guardar, norm, VIDEOS  # noqa: E402


def rutas(slug):
    w = os.path.join(VIDEOS, slug, "work")
    return os.path.join(w, "palabras.json"), os.path.join(w, "palabras_raw.json")


def ver(slug):
    ws = cargar(rutas(slug)[0])["words"]
    linea, ini = [], 0
    for i, w in enumerate(ws):
        linea.append(f"{i}:{w['w']}")
        hueco = ws[i + 1]["s"] - w["e"] if i + 1 < len(ws) else 9
        if len(linea) >= 10 or hueco > 0.35:
            print(f"[{ws[ini]['s']:6.2f}-{w['e']:6.2f}] " + " ".join(linea))
            linea, ini = [], i + 1


def corregir(slug):
    actual, raw = rutas(slug)
    if not os.path.exists(raw):
        guardar(cargar(actual), raw)
    datos = cargar(raw)
    ws = datos["words"]
    fx = cargar(os.path.join(VIDEOS, slug, "fixes.json"))
    rep = {norm(k): v for k, v in fx.get("reemplazar", {}).items()}
    for w in ws:
        k = norm(w["w"])
        if k in rep:
            m = re.match(r"^([¿¡\"'(]*)(.*?)([.,;:?!…\"')]*)$", w["w"])
            pre, _, post = m.groups() if m else ("", "", "")
            w["w"] = pre + rep[k] + post
    for i, v in fx.get("poner", {}).items():
        ws[int(i)]["w"] = v
    for i, (a, b) in fx.get("tiempo", {}).items():
        ws[int(i)]["s"], ws[int(i)]["e"] = a, b
    ops = [(i, 2, ("unir", j, v)) for i, j, v in fx.get("unir", [])]
    ops += [(i, 1, ("quitar",)) for i in fx.get("quitar", [])]
    ops += [(i, 0, ("insertar", w, a, b)) for i, w, a, b in fx.get("insertar", [])]
    for i, _, op in sorted(ops, key=lambda o: (o[0], o[1]), reverse=True):
        if op[0] == "unir":
            ws[i] = {"w": op[2], "s": ws[i]["s"], "e": ws[op[1]]["e"]}
            del ws[i + 1 : op[1] + 1]
        elif op[0] == "quitar":
            del ws[i]
        else:
            ws.insert(i, {"w": op[1], "s": op[2], "e": op[3]})
    for a, b in zip(ws, ws[1:]):
        if b["s"] < a["s"]:
            raise SystemExit(f"Orden de tiempos roto entre «{a['w']}» y «{b['w']}»: revisa fixes.json")
    datos["words"] = ws
    guardar(datos, actual)
    print(f"{len(ws)} palabras corregidas → {actual}")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("ver", "corregir"):
        sys.exit(__doc__)
    existe_video(sys.argv[2])
    {"ver": ver, "corregir": corregir}[sys.argv[1]](sys.argv[2])
