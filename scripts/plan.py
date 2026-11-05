"""Paso 4: del plan por beats (con palabras reales) al plan resuelto que lee Remotion.

  estudio/.venv/bin/python scripts/plan.py <slug>

Lee    videos/<slug>/plan.json        lo que Viernes decide (beats anclados a frases que SÍ se oyen)
       videos/<slug>/work/base.mp4 y work/palabras.json
Hace   1) resuelve cada frase a segundos reales; si una frase no está dice cuál y se detiene (no inventa tiempos)
       2) detecta las frases de firma del manual (aplausos, "oler bien" -> SIEMPRE, cierre, megáfono, rafaguiza)
       3) genera el riser a la medida, el megáfono (ffmpeg: banda 400-3500 Hz + saturación) y la lista de sonidos
       4) copia lo necesario a estudio/remotion/public/trabajo/<slug>/ y escribe work/plan.resuelto.json

plan.json (todo opcional salvo lo que se use):
{
  "titulo": "Reseña de ...",  "perfume": "Nombre exacto que dio Arturo",
  "foco": {"x": 0.5, "y": 0.4},                    dónde está su cara en el cuadro (para recortar a 9:16)
  "musica": {"base": "base-lounge.mp3", "cierre": "cierre-cuerdas.mp3", "volumen": 0.16},
  "firma": {"aplausos": true, "oler_bien": true, "cierre": true, "rafaguiza": true},
  "cola": 1.5,                                      segundos de cola musical después de la última palabra (solo con cierre)
  "beats": [
    {"tipo": "palabra", "en": "huele como un postre", "texto": "POSTRE", "efecto": "pop|shimmer", "lado": "arriba"},
    {"tipo": "ingredientes", "en": "manzana", "hasta": "canela", "items": ["Manzana", {"nombre": "Lavanda", "foto": "lavanda.jpg"}, "Canela"]},
    {"tipo": "split", "en": "sale disparado", "hasta": "disparado", "apoyo": "frasco-despega.jpg", "ia": true, "etiqueta": "..."},
    {"tipo": "apoyo", "en": "...", "hasta": "...", "archivo": "closeup-frasco.mp4"},
    {"tipo": "veredicto", "en": "mi veredicto", "dur": 6, "titulo": "Veredicto", "puntos": ["...", "..."], "lado": "der"},
    {"tipo": "transicion", "en": "pasamos a", "estilo": "barrido|zoom|flash|luz|iris|negro|persiana"},
    {"tipo": "remate", "en": "...", "sonido": "pop|scratch|silencio", "silencio": 0.7},
    {"tipo": "revelacion", "en": "...", "texto": "OPCIONAL", "sonido": "shimmer|impacto"},
    {"tipo": "rafaguiza", "sprays": [17.45, 17.85, 18.2]},
    {"tipo": "rotulo", "en": "...", "texto": "Nombre", "sub": "Casa"},
    {"tipo": "zoom", "en": "...", "hasta": "...", "escala": 1.1},
    {"tipo": "sfx", "en": "...", "sonido": "pop-1", "volumen": 0.5}
  ]
}
Anclas: "en" = frase tal como se oye (sin importar acentos ni mayúsculas); "n" = cuál aparición (0 = primera);
"desde" = buscar después de ese segundo; "antes"/"despues" = ajuste fino en segundos; "t" = segundo exacto (último recurso).
"""
import argparse
import math
import os
import shutil
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sintetizar_sfx as sint  # noqa: E402
from anclas import NoEncontrada, buscar, detectar_firma  # noqa: E402
from common import FF, FPS, PUBLIC, SR, audio_f32, cargar, envolvente, existe_video, ff, guardar, norm, probe, trabajo, valle, VIDEOS  # noqa: E402

# Ganancia que nivela cada sonido a ~ -6 dBFS de pico (medido con volumedetect el 4-nov-2026).
GANANCIA = {
    "aplauso-1": 0.64, "aplauso-2": 3.0, "pop-1": 1.16, "pop-2": 1.0, "psst-1": 1.29, "psst-3": 1.2, "psst-sint": 0.62,
    "pum-sint": 0.52, "rayo-sint": 0.62, "riser-sint-3s": 0.62, "scratch-1": 0.5, "scratch-2": 0.58, "shimmer-1": 1.22,
    "shimmer-2": 0.72, "shimmer-sint": 0.72, "whoosh-1": 0.76, "whoosh-2": 1.7, "whoosh-3": 1.64,
}
EXT_SFX = {"psst-sint": "wav", "pum-sint": "wav", "rayo-sint": "wav", "riser-sint-3s": "wav", "shimmer-sint": "wav"}
ESTILOS = ("barrido", "zoom", "flash", "luz", "iris", "negro", "persiana", "shutter")


def sfx_ruta(nombre):
    return f"sfx/{nombre}.{EXT_SFX.get(nombre, 'mp3')}"


class Plan:
    def __init__(self, slug):
        self.slug = slug
        self.errores, self.avisos = [], []
        self.sfx = []  # {"t","archivo","vol","dur","tag"}
        self.ultimo_whoosh = -99.0
        self.var_whoosh = 0

    def err(self, m):
        self.errores.append(m)

    def aviso(self, m):
        self.avisos.append(m)

    def poner_sfx(self, t, nombre, vol, dur=None, tag=None, ruta=None):
        g = GANANCIA.get(nombre, 1.0)
        self.sfx.append({"t": round(max(0.0, t), 3), "archivo": ruta or sfx_ruta(nombre), "vol": round(min(1.0, vol * g), 3), "dur": dur, "tag": tag or nombre.split("-")[0]})

    def whoosh(self, t, vol=0.13):
        """Whoosh variado: nunca el mismo dos veces seguidas y nunca más de uno cada 2.5 s."""
        if t - self.ultimo_whoosh < 2.5:
            self.aviso(f"Se omitió un whoosh a {t:.1f}s: hubo otro hace menos de 2.5 s (el manual pide no repetirlos en cada corte).")
            return
        self.ultimo_whoosh = t
        self.var_whoosh = self.var_whoosh % 3 + 1
        self.poner_sfx(t - 0.12, f"whoosh-{self.var_whoosh}", vol, tag="whoosh")


def resolver(plan, palabras, b, clave="en", n_clave="n", obligatorio=True):
    """Ancla de un beat -> (inicio, fin, descripción de la frase)."""
    if "t" in b and clave not in b:
        return float(b["t"]), float(b["t"]) + float(b.get("dur", 1.0)), f"t={b['t']}"
    if clave not in b:
        if obligatorio:
            plan.err(f"Beat «{b.get('tipo')}» sin «en»: {b}")
        return None
    try:
        h = buscar(palabras, b[clave], b.get(n_clave, 0), b.get("desde", 0.0))
    except NoEncontrada as ex:
        plan.err(f"[{b.get('tipo')}] {ex}")
        return None
    s, e = h["s"] + b.get("antes", 0.0), h["e"] + b.get("despues", 0.0)
    return s, e, h["texto"]


def archivo_apoyo(plan, nombre):
    """Busca el archivo en videos/<slug>/apoyo/ y lo prepara en public/trabajo/<slug>/apoyo/."""
    origen = os.path.join(VIDEOS, plan.slug, "apoyo", nombre)
    if not os.path.exists(origen):
        plan.err(f"Falta el archivo «{nombre}» en videos/{plan.slug}/apoyo/. Pídele a Arturo la foto o el close-up (o genera la ilustración y márcala con \"ia\": true).")
        return None
    destino = os.path.join(trabajo(plan.slug), "apoyo", nombre)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    if not os.path.exists(destino) or os.path.getmtime(destino) < os.path.getmtime(origen):
        shutil.copy2(origen, destino)
    tipo = "video" if nombre.lower().endswith((".mp4", ".mov", ".m4v", ".webm")) else "imagen"
    return {"src": f"trabajo/{plan.slug}/apoyo/{nombre}", "tipo": tipo}


def hacer_megafono(base, s, e, db, slug):
    """Genera con ffmpeg el tramo con efecto megáfono y arma la pista de voz final.

    1) Procesa SOLO [s, e] (los bordes se ajustan al valle de energía más cercano): banda 400-3500 Hz + saturación ligera,
       con el mismo volumen que la voz original. Eso queda en fx/megafono.wav (el tramo procesado, para poder oírlo solo).
    2) Arma fx/voz.flac: la voz ORIGINAL de base.mp4, muestra por muestra, con ese tramo empalmado (8 ms de empalme por borde).
       Fuera del tramo es idéntica a la original. El kit reproduce esta pista en lugar del audio del video; así el cambio ocurre
       sin huecos ni dobles (Remotion silencia el audio por cuadros, y eso dejaba un hueco de ~25 ms antes del tramo).
    """
    s2, e2 = valle(db, s, 0.05), valle(db, e, 0.05)
    if e2 - s2 < 0.2:
        s2, e2 = s, e
    orig = audio_f32(base, 0.0, None, SR, 2)  # TODO el audio, leído desde el inicio (sin saltos de búsqueda: alineación exacta)
    i0, i1 = int(round(s2 * SR)), int(round(e2 * SR))
    seg = orig[i0:i1]
    tmp = os.path.join(trabajo(slug), "fx", "_mega_in.wav")
    os.makedirs(os.path.dirname(tmp), exist_ok=True)
    out_tmp = os.path.join(trabajo(slug), "fx", "_mega_out.wav")
    _escribir_wav(tmp, seg)
    cadena = (
        "highpass=f=400:poles=2,lowpass=f=3500:poles=2,equalizer=f=1800:t=q:w=1.1:g=3,volume=3.0,"
        "asoftclip=type=tanh,acompressor=threshold=-22dB:ratio=5:attack=2:release=30,highpass=f=380,lowpass=f=3600"
    )
    ff("-i", tmp, "-af", cadena, "-ar", str(SR), "-ac", "2", out_tmp)
    proc = _leer_wav(out_tmp)[: len(seg)]
    if len(proc) < len(seg):
        proc = np.pad(proc, ((0, len(seg) - len(proc)), (0, 0)))
    # iguala el volumen percibido (RMS) al de la voz original y deja margen de pico
    rms_o, rms_p = float(np.sqrt(np.mean(seg**2)) + 1e-9), float(np.sqrt(np.mean(proc**2)) + 1e-9)
    proc = proc * (rms_o / rms_p)
    pico = float(np.max(np.abs(proc)))
    if pico > 0.85:
        proc *= 0.85 / pico
    n = len(proc)
    mix = orig.copy()
    mix[i0 : i0 + n] = proc
    xf = int(0.008 * SR)
    r = np.linspace(0, 1, xf)[:, None]
    mix[i0 : i0 + xf] = orig[i0 : i0 + xf] * (1 - r) + proc[:xf] * r
    mix[i0 + n - xf : i0 + n] = proc[n - xf :] * (1 - r) + orig[i0 + n - xf : i0 + n] * r
    d = os.path.join(trabajo(slug), "fx")
    _escribir_wav(os.path.join(d, "megafono.wav"), proc)
    flac = os.path.join(d, "voz.flac")
    pr = subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-c:a", "flac", flac], input=mix.astype("<f4").tobytes(), capture_output=True)
    if pr.returncode != 0:
        raise SystemExit("No pude escribir la pista de voz: " + pr.stderr.decode()[-500:])
    for f in (tmp, out_tmp):
        os.remove(f)
    return {"s": round(s2, 3), "e": round(e2, 3), "archivo": f"trabajo/{slug}/fx/megafono.wav", "voz": f"trabajo/{slug}/fx/voz.flac"}


def _escribir_wav(ruta, x):
    import wave

    x = np.clip(x, -1, 1)
    with wave.open(ruta, "wb") as w:
        w.setnchannels(x.shape[1] if x.ndim == 2 else 1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())


def _leer_wav(ruta):
    return audio_f32(ruta, 0.0, None, SR, 2)


def detectar_sprays(base, palabras, desde, hasta):
    """Ráfagas agudas tipo PSSHT fuera de las palabras. Es una pista: se confirma mirando/oyendo."""
    x = audio_f32(base, desde, hasta, SR, 1)
    if len(x) < SR * 0.2:
        return []
    paso, vent = int(0.01 * SR), int(0.02 * SR)
    ventana = np.hanning(vent)
    energia, tiempos = [], []
    for i in range(0, len(x) - vent, paso):
        sp = np.abs(np.fft.rfft(x[i : i + vent] * ventana))
        fr = np.fft.rfftfreq(vent, 1 / SR)
        energia.append(20 * np.log10(sp[(fr > 5000) & (fr < 12000)].mean() + 1e-9))
        tiempos.append(desde + i / SR)
    energia, tiempos = np.array(energia), np.array(tiempos)
    piso = np.median(energia)
    hits, ultimo = [], -9
    for k in range(1, len(energia)):
        t = tiempos[k]
        if energia[k] > piso + 14 and energia[k - 1] <= piso + 14 and t - ultimo > 0.3:
            if any(w["s"] - 0.05 <= t <= w["e"] + 0.05 for w in palabras):
                continue
            hits.append(round(float(t), 3))
            ultimo = t
    return hits


def intervalos_voz(palabras, hueco=0.4, relleno=0.05):
    iv = []
    for w in palabras:
        a, b = w["s"] - relleno, w["e"] + relleno
        if iv and a - iv[-1][1] < hueco:
            iv[-1][1] = max(iv[-1][1], b)
        else:
            iv.append([max(0.0, a), b])
    return [[round(a, 3), round(b, 3)] for a, b in iv]


def buscar_musica(plan, nombre):
    """Pista de música: estudio/remotion/public/musica/ primero, luego videos/<slug>/musica/. None si no está (el kit se degrada)."""
    if not nombre:
        return None
    for base, rel in ((os.path.join(PUBLIC, "musica"), "musica"), (os.path.join(VIDEOS, plan.slug, "musica"), None)):
        p = os.path.join(base, nombre)
        if os.path.exists(p):
            if rel:
                return f"{rel}/{nombre}"
            d = os.path.join(trabajo(plan.slug), "musica", nombre)
            os.makedirs(os.path.dirname(d), exist_ok=True)
            if not os.path.exists(d) or os.path.getmtime(d) < os.path.getmtime(p):
                shutil.copy2(p, d)
            return f"trabajo/{plan.slug}/musica/{nombre}"
    plan.aviso(f"La pista «{nombre}» no está en estudio/remotion/public/musica/ ni en videos/{plan.slug}/musica/. Se edita sin ella.")
    return None


def autodetectar_musica(plan, prefijo):
    for base in (os.path.join(PUBLIC, "musica"), os.path.join(VIDEOS, plan.slug, "musica")):
        if os.path.isdir(base):
            for f in sorted(os.listdir(base)):
                if f.lower().startswith(prefijo) and f.lower().endswith((".mp3", ".wav", ".m4a", ".aac", ".ogg")):
                    return f
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    a = ap.parse_args()
    slug = a.slug
    existe_video(slug)
    work = os.path.join(VIDEOS, slug, "work")
    base = os.path.join(work, "base.mp4")
    if not os.path.exists(base):
        sys.exit("Falta work/base.mp4: primero cut.py")
    palabras = cargar(os.path.join(work, "palabras.json"))["words"]
    ruta_plan = os.path.join(VIDEOS, slug, "plan.json")
    cfg = cargar(ruta_plan) if os.path.exists(ruta_plan) else {}
    P = Plan(slug)
    pbase = probe(base)
    dur_base = pbase["duracion"]
    db = envolvente(base)
    tw = trabajo(slug)
    os.makedirs(os.path.join(tw, "fx"), exist_ok=True)
    # video base a public/trabajo (enlace duro si se puede: no duplica espacio)
    destino_video = os.path.join(tw, "base.mp4")
    if os.path.exists(destino_video):
        os.remove(destino_video)
    try:
        os.link(base, destino_video)
    except OSError:
        shutil.copy2(base, destino_video)

    firma_cfg = {"aplausos": True, "oler_bien": True, "cierre": True, "rafaguiza": True, **cfg.get("firma", {})}
    firma, av = detectar_firma(palabras)
    for x in av:
        P.aviso(x)

    # ---- Firma sonora ----
    res_firma = {"aplausos": [], "oler_bien": [], "cierre": None, "rafaguiza": None}
    if firma_cfg["aplausos"]:
        for k, x in enumerate(firma["aplausos"]):
            if k >= 1:
                P.aviso("Hay más de un «Conquista Aromática»: solo el primero lleva aplausos (breves, para no repetir).")
                break
            P.poner_sfx(x["t"] - 0.02, "aplauso-1", 0.55, dur=1.5, tag="aplauso")
            res_firma["aplausos"].append({"t": round(x["t"], 3), "fin": round(x["fin"], 3), "dur": 1.5})
    if firma_cfg["oler_bien"]:
        for k, x in enumerate(firma["oler_bien"]):
            ini_f = math.floor(x["inicio"] * FPS)
            fin_t = x["siempre"] - 0.06
            if x["pausa"] > 0.6:  # pausa dramática: el riser se corta poco después de "bien" y se deja el silencio antes del PUM
                fin_t = min(fin_t, x["bien_fin"] + 0.35)
            fin_f = math.floor(fin_t * FPS)
            dur_r = (fin_f - ini_f) / FPS
            if dur_r < 0.5:
                P.aviso(f"El riser #{k + 1} saldría de {dur_r:.2f} s: demasiado corto, se omite.")
                continue
            rr = os.path.join(tw, "fx", f"riser-{k}.wav")
            sint.escribir(rr, sint.riser(dur_r), 0.8)
            pum_f = math.floor(x["siempre"] * FPS)
            P.sfx.append({"t": ini_f / FPS, "archivo": f"trabajo/{slug}/fx/riser-{k}.wav", "vol": 0.34, "dur": round(dur_r, 4), "tag": "riser", "exacto": True})
            P.sfx.append({"t": pum_f / FPS, "archivo": sfx_ruta("pum-sint"), "vol": round(0.95 * GANANCIA["pum-sint"], 3), "dur": None, "tag": "pum", "exacto": True})
            res_firma["oler_bien"].append(
                {"inicio": x["inicio"], "riser_ini": ini_f / FPS, "riser_fin": fin_f / FPS, "bien_fin": x["bien_fin"], "siempre": x["siempre"], "pum": pum_f / FPS, "frase_fin": x["frase_fin"]}
            )
    cz = firma["cierre"]
    mus_cfg = cfg.get("musica", {}) or {}
    if firma_cfg["cierre"] and cz:
        cierre = {"inicio": cz["inicio"], "iconos": {}}
        for clave in ("like", "campanita", "suscribete"):
            if cz.get(clave) is not None:
                cierre["iconos"][clave] = round(cz[clave], 3)
        if cz.get("megafono"):
            m = cz["megafono"]
            mf = hacer_megafono(base, m["s"], m["e"], db, slug)
            mf["texto"] = m["texto"]
            mf["parcial"] = m["parcial"]
            cierre["megafono"] = mf
        res_firma["cierre"] = cierre
    rz = firma["rafaguiza"]
    if firma_cfg["rafaguiza"] and rz:
        res_firma["rafaguiza"] = {"inicio": rz["inicio"], "palabra_s": rz["palabra_s"], "fin": rz["fin"], "texto": rz["texto"], "sprays": []}

    # ---- Beats ----
    beats, texto_iv = [], []  # texto_iv: (inicio, fin, nombre) para "una idea por pantalla"
    for b in cfg.get("beats", []):
        tipo = b.get("tipo")
        r = resolver(P, palabras, b, obligatorio=tipo != "rafaguiza")
        if tipo == "rafaguiza":
            if not res_firma["rafaguiza"]:
                P.err("Beat rafaguiza, pero no oigo «rafaguiza» en el audio. Revisa palabras.py ver (¿Whisper la escribió distinto?).")
                continue
            sp = [float(t) for t in b.get("sprays", [])]
            if not sp:
                sp = detectar_sprays(base, palabras, res_firma["rafaguiza"]["fin"], min(dur_base, res_firma["rafaguiza"]["fin"] + 8))
                if sp:
                    P.aviso(f"Sprays detectados por el audio a {sp}: confírmalos mirando el video.")
                else:
                    P.aviso("No detecté el sonido de los sprays en el audio. Dime en qué segundos se aplica (beat rafaguiza con \"sprays\": [..]); sin ellos no se anima nada.")
            res_firma["rafaguiza"]["sprays"] = [round(t, 3) for t in sp]
            res_firma["rafaguiza"]["poder"] = b.get("poder", True)
            continue
        if r is None:
            continue
        s, e, frase = r
        item = {"tipo": tipo, "inicio": round(s, 3), "fin": round(e, 3), "frase": frase}
        if tipo == "palabra":
            texto = b.get("texto") or frase.upper()
            item.update({"texto": texto, "efecto": b.get("efecto", "pop"), "lado": b.get("lado"), "fin": round(max(e + 0.3, s + 1.0), 3)})
            texto_iv.append((item["inicio"], item["fin"], f"palabra «{texto}»"))
            if item["efecto"] == "shimmer":
                P.poner_sfx(s - 0.02, "shimmer-1", 0.07, tag="shimmer")
            else:
                P.poner_sfx(s - 0.02, "pop-1", 0.4, tag="pop")
        elif tipo == "ingredientes":
            fin_r = resolver(P, palabras, {**b, "en": b.get("hasta", b["en"])})
            if fin_r is None:
                continue
            items = []
            for it in b.get("items", []):
                nombre = it if isinstance(it, str) else it["nombre"]
                foto = None if isinstance(it, str) else it.get("foto")
                tt = None
                for w in palabras:  # el ingrediente tiene que haberse DICHO dentro del tramo
                    if s - 0.05 <= w["s"] <= fin_r[1] + 0.05 and norm(w["w"]).startswith(norm(nombre.split()[0])[:5]):
                        tt = w["s"]
                        break
                if tt is None:
                    P.err(f"[ingredientes] «{nombre}» no se dice entre {s:.1f}s y {fin_r[1]:.1f}s. No se muestran notas que Arturo no menciona.")
                    continue
                items.append({"nombre": nombre, "t": round(tt, 3), "foto": archivo_apoyo(P, foto) if foto else None})
            item.update({"fin": round(fin_r[1] + 1.0, 3), "items": items})
            texto_iv.append((item["inicio"], item["fin"], "franja de ingredientes"))
            for k, it in enumerate(items):
                P.poner_sfx(it["t"] - 0.03, f"pop-{1 + k % 2}", 0.3, tag="pop")
        elif tipo in ("split", "apoyo"):
            fin_r = resolver(P, palabras, {**b, "en": b.get("hasta", b["en"])}, obligatorio=False)
            if fin_r:
                item["fin"] = round(fin_r[1] + b.get("despues", 0.0), 3)
            nombre = b.get("apoyo") or b.get("archivo")
            if nombre:
                ar = archivo_apoyo(P, nombre)
                if ar is None:
                    continue
                item["archivo"] = ar
            else:
                item["ilustracion"] = "frasco"
            item.update({"etiqueta": b.get("etiqueta"), "ia": bool(b.get("ia")), "modo": b.get("modo", "split" if tipo == "split" else "completo"), "closeup": bool(b.get("closeup"))})
            if item["ia"] and not item.get("etiqueta"):
                item["etiqueta"] = "Ilustración"
            if b.get("sonido", True):
                P.whoosh(s)
        elif tipo == "veredicto":
            fin = s + float(b["dur"]) if "dur" in b else (resolver(P, palabras, {**b, "en": b["hasta"]})[1] if "hasta" in b else s + 6.0)
            pts = b.get("puntos", [])
            if not (1 <= len(pts) <= 4):
                P.err("[veredicto] lleva de 1 a 4 puntos (una idea por pantalla).")
            vocab = {norm(w["w"]) for w in palabras}
            for p_ in pts:
                for tok in p_.split():
                    t_ = norm(tok)
                    if len(t_) >= 6 and t_[:5] not in {v[:5] for v in vocab}:
                        P.aviso(f"[veredicto] «{tok}» (en «{p_}») no aparece en el audio: confírmalo con Arturo, no se inventan características.")
            item.update({"fin": round(fin, 3), "titulo": b.get("titulo", "Veredicto"), "puntos": pts, "lado": b.get("lado", "der")})
            texto_iv.append((item["inicio"], item["fin"], "veredicto"))
            P.poner_sfx(s, "shimmer-1", 0.07, tag="shimmer")
        elif tipo == "transicion":
            if b.get("estilo", "barrido") not in ESTILOS:
                P.err(f"[transicion] estilo «{b.get('estilo')}». Opciones: {', '.join(ESTILOS)}")
                continue
            item.update({"estilo": b.get("estilo", "barrido"), "inicio": round(s, 3)})
            P.whoosh(s)
        elif tipo == "remate":
            snd = b.get("sonido", "pop")
            fin_f = e
            item.update({"inicio": round(fin_f, 3), "fin": round(fin_f + float(b.get("silencio", 0.7)), 3), "sonido": snd})
            if snd == "pop":
                P.poner_sfx(fin_f + 0.04, "pop-2", 0.55, tag="pop")
            elif snd == "scratch":
                P.poner_sfx(fin_f + 0.02, "scratch-2", 0.5, tag="scratch")
            elif snd != "silencio":
                P.err(f"[remate] sonido «{snd}»: usa pop, scratch o silencio.")
                continue
        elif tipo == "revelacion":
            snd = b.get("sonido", "shimmer")
            item.update({"texto": b.get("texto"), "sonido": snd, "fin": round(max(e + 0.2, s + 1.2), 3)})
            if snd == "shimmer":
                P.poner_sfx(s, "shimmer-sint", 0.35, tag="shimmer")
            else:  # impacto suave: PUM bajito
                P.sfx.append({"t": round(s, 3), "archivo": sfx_ruta("pum-sint"), "vol": round(0.28 * GANANCIA["pum-sint"], 3), "dur": 0.6, "tag": "impacto"})
            if b.get("texto"):
                texto_iv.append((item["inicio"], item["fin"], "revelación"))
        elif tipo == "rotulo":
            item.update({"texto": b.get("texto"), "sub": b.get("sub"), "fin": round(s + float(b.get("dur", 3.5)), 3)})
            texto_iv.append((item["inicio"], item["fin"], "rótulo"))
        elif tipo == "zoom":
            fin_r = resolver(P, palabras, {**b, "en": b.get("hasta", b["en"])})
            item.update({"escala": float(b.get("escala", 1.1)), "fin": round(fin_r[1] if fin_r else s + 2, 3)})
        elif tipo == "sfx":
            nombre = b.get("sonido", "pop-1")
            if not os.path.exists(os.path.join(PUBLIC, sfx_ruta(nombre))):
                P.err(f"[sfx] «{nombre}» no existe en public/sfx/")
                continue
            P.poner_sfx(s, nombre, float(b.get("volumen", 0.5)))
            continue
        else:
            P.err(f"Tipo de beat desconocido: «{tipo}»")
            continue
        beats.append(item)

    # una idea por pantalla: dos textos grandes al mismo tiempo no valen
    texto_iv.sort()
    for i in range(len(texto_iv)):
        for j in range(i + 1, len(texto_iv)):
            if texto_iv[j][0] < texto_iv[i][1] - 0.2:
                P.aviso(f"UNA IDEA POR PANTALLA: {texto_iv[i][2]} ({texto_iv[i][0]:.1f}-{texto_iv[i][1]:.1f}s) se encima con {texto_iv[j][2]} ({texto_iv[j][0]:.1f}-{texto_iv[j][1]:.1f}s).")

    # ---- Efectos de la Rafaguiza ----
    rf = res_firma["rafaguiza"]
    if rf:
        P.poner_sfx(rf["inicio"] - 0.02, "shimmer-sint", 0.3, tag="shimmer")
        for k, t in enumerate(rf["sprays"]):
            P.poner_sfx(t - 0.01, f"psst-{1 if k % 2 == 0 else 3}", 0.45, tag="psst")
            if rf.get("poder", True) and k == 1:
                P.poner_sfx(t, "rayo-sint", 0.4, tag="rayo")
            if rf.get("poder", True) and k >= 2:
                P.poner_sfx(t, "shimmer-sint", 0.3, tag="shimmer")
            if rf.get("poder", True) and k == 0:
                P.poner_sfx(t + 0.05, "pop-1", 0.2, tag="pop")

    # ---- Cierre: cuerdas y megáfono ----
    base_mus = buscar_musica(P, mus_cfg.get("base") or autodetectar_musica(P, "base"))
    cierre_mus = buscar_musica(P, mus_cfg.get("cierre") or autodetectar_musica(P, "cierre"))
    cola = float(cfg.get("cola", 1.5 if (res_firma["cierre"] and cierre_mus) else 0.0))
    if res_firma["cierre"] and not cierre_mus:
        P.aviso("El cierre queda SIN violines/cuerdas: no hay pista con licencia en public/musica/. Pídele a Arturo una (ver public/musica/LEEME.md).")
    if not base_mus:
        P.aviso("Sin música de fondo: el video se edita sin ella. Pídele a Arturo una pista con licencia clara.")

    silencios = [[x["inicio"], x["fin"]] for x in beats if x["tipo"] == "remate"]
    resuelto = {
        "slug": slug,
        "titulo": cfg.get("titulo", slug),
        "perfume": cfg.get("perfume"),
        "fps": FPS,
        "duracion_base": round(dur_base, 3),
        "cola": cola,
        "video": f"trabajo/{slug}/base.mp4",
        "fuente": {"w": pbase["ancho_visible"], "h": pbase["alto_visible"]},
        "foco": cfg.get("foco", {"x": 0.5, "y": 0.4}),
        "palabras": [{"w": w["w"], "s": w["s"], "e": w["e"]} for w in palabras],
        "voz": intervalos_voz(palabras),
        "musica": {"base": base_mus, "cierre": cierre_mus, "volumen": float(mus_cfg.get("volumen", 0.16))},
        "firma": res_firma,
        "beats": beats,
        "silencios": silencios,
        "sfx": sorted(P.sfx, key=lambda x: x["t"]),
        "avisos": P.avisos,
    }
    guardar(resuelto, os.path.join(work, "plan.resuelto.json"))
    guardar(resuelto, os.path.join(tw, "plan.resuelto.json"))
    print(f"Plan resuelto: {len(beats)} beats, {len(P.sfx)} sonidos, duración {dur_base + cola:.1f} s")
    for x in P.avisos:
        print(" aviso:", x)
    if P.errores:
        print("\nERRORES (corrige plan.json o las palabras y vuelve a correr):")
        for x in P.errores:
            print(" x", x)
        sys.exit(1)


if __name__ == "__main__":
    main()
