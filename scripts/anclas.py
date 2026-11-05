"""Anclas: encontrar frases en las palabras REALES del video y detectar las frases de firma de Conquista Aromática.

Todo el plan de edición se amarra a palabras que se oyen en el audio. Si una frase no está, aquí se detiene con un error
que lista palabras parecidas: nunca se inventa un tiempo ni se completa una palabra que Arturo no grabó.
"""
import difflib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import norm  # noqa: E402


class NoEncontrada(Exception):
    pass


def _tokens(frase):
    return [t for t in (norm(p) if not p.endswith("*") else norm(p[:-1]) + "*" for p in frase.split()) if t.strip("*")]


def _coincide(palabra, token):
    n = norm(palabra)
    if token.endswith("*"):
        return n.startswith(token[:-1]) and len(n) >= len(token) - 1
    return n == token


def todas(palabras, frase, desde=0.0, hasta=None):
    """Todas las apariciones de una frase: lista de (i, j) con índices de la primera y la última palabra.
    Un token terminado en * acepta prefijos («suscrib*»); sin * debe ser la palabra completa («conquista» no es «conquistas»)."""
    tk = _tokens(frase)
    if not tk:
        return []
    salida = []
    i = 0
    while i < len(palabras):
        if palabras[i]["s"] + 1e-6 >= desde and (hasta is None or palabras[i]["s"] <= hasta):
            k, j = 0, i
            while k < len(tk) and j < len(palabras):
                if not norm(palabras[j]["w"]):  # signo suelto
                    j += 1
                    continue
                if not _coincide(palabras[j]["w"], tk[k]):
                    break
                k += 1
                j += 1
            if k == len(tk):
                salida.append((i, j - 1))
                i = j
                continue
        i += 1
    return salida


def buscar(palabras, frase, n=0, desde=0.0, hasta=None):
    """Aparición n de la frase (0 = primera). Devuelve {i, j, s, e, texto}."""
    hits = todas(palabras, frase, desde, hasta)
    if n >= len(hits):
        cerca = difflib.get_close_matches(norm(frase.split()[0].rstrip("*")), sorted({norm(w["w"]) for w in palabras if norm(w["w"])}), n=6, cutoff=0.5)
        raise NoEncontrada(
            f"No encuentro «{frase}» (aparición {n + 1}; hay {len(hits)}) en las palabras del video"
            + (f" desde {desde:.1f}s" if desde else "")
            + (f". Palabras parecidas: {', '.join(cerca)}" if cerca else "")
            + ". Revisa words.py print: si Whisper la escribió distinto, corrígela con fixes.json; si Arturo no la dijo, no se inventa."
        )
    i, j = hits[n]
    return {"i": i, "j": j, "s": palabras[i]["s"], "e": palabras[j]["e"], "texto": " ".join(w["w"] for w in palabras[i : j + 1])}


def detectar_firma(palabras):
    """Busca en las palabras reales los momentos de firma del manual. Devuelve (firma, avisos)."""
    avisos = []
    f = {"aplausos": [], "oler_bien": [], "cierre": None, "rafaguiza": None}

    # 1) «Conquista Aromática» (el nombre del canal, no «conquistas aromáticas»)
    for i, j in todas(palabras, "conquista aromatica"):
        f["aplausos"].append({"t": palabras[i]["s"], "fin": palabras[j]["e"], "texto": "Conquista Aromática"})

    # 2) «el canal donde oler bien» → «SIEMPRE está en el plan»
    for i, j in todas(palabras, "el canal donde oler bien"):
        sig = None
        for k in range(j + 1, min(len(palabras), j + 8)):
            if norm(palabras[k]["w"]) == "siempre" and palabras[k]["s"] - palabras[j]["e"] < 4.0:
                sig = k
                break
        if sig is None:
            avisos.append(f"«el canal donde oler bien» a {palabras[i]['s']:.1f}s no va seguido de «siempre»: no hay PUM que sincronizar.")
            continue
        fin_plan = sig
        for k in range(sig, min(len(palabras), sig + 6)):
            fin_plan = k
            if "plan" in norm(palabras[k]["w"]):
                break
        f["oler_bien"].append(
            {
                "inicio": palabras[i]["s"],
                "bien_fin": palabras[j]["e"],
                "siempre": palabras[sig]["s"],
                "frase_fin": palabras[fin_plan]["e"],
                "pausa": round(palabras[sig]["s"] - palabras[j]["e"], 3),
            }
        )
    if not f["oler_bien"] and not any("oler bien" in a for a in avisos):
        avisos.append("No aparece «el canal donde oler bien… siempre está en el plan». Si el video no lleva presentación, es normal.")

    # 3) Cierre del canal
    c = {}
    try:
        d = buscar(palabras, "denle like")
        h = None
        for k in range(max(0, d["i"] - 5), d["i"]):
            if norm(palabras[k]["w"]).startswith("hermos") and d["s"] - palabras[k]["s"] < 4.0:
                h = k
                break
        c["inicio"] = palabras[h]["s"] if h is not None else d["s"]
        c["denle_like"] = d["s"]
        c["like"] = palabras[d["j"]]["s"]
        for clave, frase in (("campanita", "campanit*"), ("suscribete", "suscrib*")):
            try:
                c[clave] = buscar(palabras, frase, desde=d["s"])["s"]
            except NoEncontrada:
                avisos.append(f"En el cierre no oigo «{frase.rstrip('*')}»: no se pone ese icono.")
        c["campanita_fin"] = None
        # megáfono: «a lo que desean proyectar» (si falta alguna palabra, solo las que sí están grabadas)
        intentos = ["a lo que desean proyectar", "lo que desean proyectar", "desean proyectar", "a lo que desean"]
        m = None
        for fr in intentos:
            try:
                m = buscar(palabras, fr, desde=d["s"])
                m["frase"] = fr
                break
            except NoEncontrada:
                continue
        if m:
            c["megafono"] = {"s": m["s"], "e": m["e"], "texto": m["texto"], "parcial": m["frase"] != intentos[0]}
            if m["frase"] != intentos[0]:
                avisos.append(f"Megáfono PARCIAL: solo «{m['texto']}» está grabado; no se completa la frase.")
        else:
            avisos.append("En el cierre no oigo «a lo que desean proyectar»: no hay megáfono.")
        f["cierre"] = c
    except NoEncontrada:
        avisos.append("No aparece «denle like»: este video no trae el cierre del canal (no se pone música de cuerdas ni megáfono).")

    # 4) Rafaguiza
    for i, p in enumerate(palabras):
        if norm(p["w"]).startswith(("rafag", "rafaguis", "rafaguiz")):
            ini = i
            for k in range(max(0, i - 6), i):
                if norm(palabras[k]["w"]) in ("es", "hora") and p["s"] - palabras[k]["s"] < 3.0:
                    ini = k
                    break
            f["rafaguiza"] = {"inicio": palabras[ini]["s"], "palabra_s": p["s"], "fin": p["e"], "texto": " ".join(w["w"] for w in palabras[ini : i + 1])}
            break
    return f, avisos
