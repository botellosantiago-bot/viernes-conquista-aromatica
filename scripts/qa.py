"""QA: el checklist del manual de Arturo convertido en MEDICIONES reales sobre el video renderizado.

  estudio/.venv/bin/python scripts/qa.py <slug> --formato 16:9|9:16 [--entrega primer-corte]

Necesita haber corrido antes:  render.py <slug> --formato ... --stems   (deja el video y el audio por partes: voz, fx, música).
Mide sobre los stems (así cada cosa se oye sola, sin que la tape la voz):
  riser     empieza con «el canal donde oler bien» y TERMINA antes de «SIEMPRE»; no queda nada de riser debajo del remate
  PUM       su golpe grave cae en el arranque de «SIEMPRE»
  aplausos  arrancan con «Conquista Aromática» y son breves
  megáfono  la voz procesada difiere de la original SOLO en «a lo que desean proyectar» (resta voz - original, cuadro a cuadro)
            y ahí queda en banda limitada (sin graves ni agudos)
  PSSHT     uno en cada spray de la Rafaguiza; y los efectos visuales no tocan el centro del cuadro (cara y perfume)
  mezcla    la música y los efectos quedan por debajo de la voz; las cuerdas del cierre entran donde deben
  picos     el video final no pasa de -1 dBTP (true peak) y el volumen es parejo
Además revisa el plan (una idea por pantalla, whooshes variados, sobreedición) y lista lo que SOLO puede confirmar una persona.
Estados:  OK  |  FALLA (hay que corregir)  |  AVISO  |  MANUAL (lo confirma Viernes mirando o Arturo)
Escribe videos/<slug>/work/qa-<formato>.md y sale con código 1 si algo FALLA.
"""
import argparse
import math
import os
import re
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FF, FORMATOS, FPS, PUBLIC, SR, VIDEOS, audio_f32, cargar, existe_video, formato, norm, probe  # noqa: E402

R = []  # (estado, nombre, detalle)


def anota(estado, nombre, detalle):
    R.append((estado, nombre, detalle))
    print(f"[{estado:6}] {nombre}: {detalle}")


def banda(ruta, hp=None, lp=None, canales=1):
    """Audio float32 mono (o estéreo) con un filtro de banda aplicado por ffmpeg."""
    fl = []
    if hp:
        fl.append(f"highpass=f={hp}:poles=2")
    if lp:
        fl.append(f"lowpass=f={lp}:poles=2")
    cmd = [FF, "-v", "error", "-i", ruta, "-vn"]
    if fl:
        cmd += ["-af", ",".join(fl)]
    cmd += ["-ac", str(canales), "-ar", str(SR), "-f", "f32le", "-"]
    x = np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, dtype=np.float32)
    return x


def env(x, hop=0.005):
    n = int(hop * SR)
    m = len(x) // n
    r = np.sqrt(np.mean(x[: m * n].reshape(m, n) ** 2, axis=1))
    return 20 * np.log10(r + 1e-9), hop


def db(v):
    return 20 * math.log10(v + 1e-9)


def primero(e, hop, t0, t1, umbral):
    a, b = max(0, int(t0 / hop)), min(len(e), int(t1 / hop))
    idx = np.where(e[a:b] > umbral)[0]
    return (a + idx[0]) * hop if len(idx) else None


def ultimo(e, hop, t0, t1, umbral):
    a, b = max(0, int(t0 / hop)), min(len(e), int(t1 / hop))
    idx = np.where(e[a:b] > umbral)[0]
    return (a + idx[-1] + 1) * hop if len(idx) else None


def true_peak(ruta):
    r = subprocess.run([FF, "-hide_banner", "-nostats", "-i", ruta, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    resumen = r[r.rfind("Summary:") :]
    pk = re.search(r"True peak:\s*\n\s*Peak:\s*(-?[\d.]+|-inf) dBFS", resumen)
    li = re.search(r"I:\s*(-?[\d.]+) LUFS", resumen)
    lra = re.search(r"LRA:\s*([\d.]+) LU", resumen)
    return (float(pk.group(1)) if pk else None, float(li.group(1)) if li else None, float(lra.group(1)) if lra else None)


def cuadro_centro_ok(final, base, plan, fmt, t, W, H):
    """Diferencia media (0-255) en el centro del cuadro entre el video final y el video limpio de Arturo en el instante t."""
    fw, fh = plan["fuente"]["w"], plan["fuente"]["h"]
    k = max(W / fw, H / fh)
    sw, sh = fw * k, fh * k
    fx, fy = plan["foco"]["x"], plan["foco"]["y"]
    left = max(0, min(sw - W, fx * sw - W / 2))
    top = max(0, min(sh - H, fy * sh - H / 2))
    cx0, cx1 = (0.30, 0.70) if W > H else (0.25, 0.75)
    cy0, cy1 = (0.20, 0.62) if W > H else (0.22, 0.52)
    par = lambda v: int(v) // 2 * 2  # medidas pares: con impares el recorte 4:2:0 cambia de tamaño y las matrices no se alinean
    box = (par(W * cx0), par(H * cy0), par(W * (cx1 - cx0)), par(H * (cy1 - cy0)))

    def trozo(ruta, filtro):
        r = subprocess.run([FF, "-v", "error", "-ss", f"{t:.4f}", "-i", ruta, "-frames:v", "1", "-vf", filtro, "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True)
        return np.frombuffer(r.stdout, dtype=np.uint8).astype(np.float32)

    a = trozo(final, f"crop={box[2]}:{box[3]}:{box[0]}:{box[1]}")
    b = trozo(base, f"scale={int(round(sw))}:{int(round(sh))},crop={W}:{H}:{int(round(left))}:{int(round(top))},crop={box[2]}:{box[3]}:{box[0]}:{box[1]}")
    n = min(len(a), len(b))
    return float(np.mean(np.abs(a[:n] - b[:n]))) if n else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--formato", required=True)
    ap.add_argument("--entrega", default="primer-corte")
    a = ap.parse_args()
    existe_video(a.slug)
    fmt = formato(a.formato)
    info = FORMATOS[fmt]
    W, H = info["w"], info["h"]
    work = os.path.join(VIDEOS, a.slug, "work")
    plan = cargar(os.path.join(work, "plan.resuelto.json"))
    base = os.path.join(work, "base.mp4")
    final = os.path.join(VIDEOS, a.slug, "out", f"{a.slug}-{info['etiqueta']}-{a.entrega}.mp4")
    sd = os.path.join(work, f"stems-{info['etiqueta']}")
    palabras = plan["palabras"]
    total = plan["duracion_base"] + plan["cola"]

    # ---------- Archivo final ----------
    if not os.path.exists(final):
        sys.exit(f"Falta {final}: corre render.py primero.")
    p = probe(final)
    ok = (p["ancho_visible"], p["alto_visible"]) == (W, H)
    anota("OK" if ok else "FALLA", "Formato", f"{p['ancho_visible']}x{p['alto_visible']} a {p['fps']} fps (se esperaba {W}x{H} a 30)")
    anota("OK" if abs(p["duracion"] - total) < 0.15 else "FALLA", "Duración", f"{p['duracion']:.2f} s (plan: {total:.2f} s)")
    pk, lufs, lra = true_peak(final)
    anota("OK" if pk is not None and pk <= -1.0 else "FALLA", "Picos (true peak)", f"{pk} dBTP (límite -1.0)")
    anota("OK" if lufs is not None and -17.5 <= lufs <= -14.5 else "AVISO", "Volumen", f"{lufs} LUFS integrados, LRA {lra} (objetivo -16 ± 1.5)")

    tiene_stems = all(os.path.exists(os.path.join(sd, f"{s}.wav")) for s in ("voz", "fx", "musica", "cuerdas"))
    if not tiene_stems:
        anota("FALLA", "Stems", f"faltan voz/fx/musica/cuerdas en {sd}: corre render.py con --stems")
    else:
        voz = banda(os.path.join(sd, "voz.wav"))
        fx = banda(os.path.join(sd, "fx.wav"))
        fx_hi = banda(os.path.join(sd, "fx.wav"), hp=4000)
        fx_lo = banda(os.path.join(sd, "fx.wav"), lp=150)
        mus = banda(os.path.join(sd, "musica.wav"))
        e_fx, hop = env(fx)
        e_hi, _ = env(fx_hi)
        e_lo, _ = env(fx_lo)

        # ---------- Aplausos ----------
        otros = sorted(x["t"] for x in plan["sfx"] if x.get("tag") != "aplauso")
        for ap_ in plan["firma"]["aplausos"][:1]:
            t0 = ap_["t"]
            on = primero(e_fx, hop, t0 - 0.3, t0 + 0.6, -45)
            if on is None:
                anota("FALLA", "Aplausos en «Conquista Aromática»", f"no se oyen aplausos cerca de {t0:.2f}s")
            else:
                anota("OK" if abs(on - t0) <= 0.08 else "FALLA", "Aplausos arrancan con «Conquista»", f"arrancan a {on:.2f}s; la palabra empieza a {t0:.2f}s (diferencia {on - t0:+.3f}s)")
                # breves: a los 2.0 s ya no suenan (se mide hasta donde empiece otro efecto)
                sig = next((x for x in otros if x > t0 + 0.5), t0 + 3.0)
                a_, b_ = t0 + 2.0, min(t0 + 3.0, sig - 0.03)
                if b_ - a_ < 0.05:
                    anota("OK", "Aplausos breves", f"otro efecto entra a {sig:.2f}s, antes de que pudieran pasar de 2 s")
                else:
                    resto = float(np.max(e_fx[int(a_ / hop) : int(b_ / hop)]))
                    anota("OK" if resto < -45 else "FALLA", "Aplausos breves", f"entre {a_:.2f}s y {b_:.2f}s (2 s después de empezar) quedan {resto:.0f} dB (deben estar por debajo de -45 dB)")
        if not plan["firma"]["aplausos"]:
            anota("AVISO", "Aplausos", "no hay «Conquista Aromática» en el audio: no se puso aplauso")

        # ---------- Riser y PUM ----------
        for k, o in enumerate(plan["firma"]["oler_bien"]):
            s_ini, s_sie = o["inicio"], o["siempre"]
            a_r, b_r = int((s_ini - 0.4) / hop), int((s_sie - 0.03) / hop)
            tramo_r = e_fx[a_r:b_r]
            if len(tramo_r) == 0 or float(tramo_r.max()) < -40:
                anota("FALLA", f"Riser #{k + 1}", "no se oye riser")
            else:
                umbral = float(tramo_r.max()) - 35  # el riser arranca bajito: se mide cuando está 35 dB bajo su pico
                r_on = primero(e_fx, hop, s_ini - 0.4, s_sie - 0.03, umbral)
                r_off = ultimo(e_fx, hop, s_ini - 0.4, s_sie - 0.03, -50)
                anota("OK" if s_ini - 0.12 <= r_on <= s_ini + 0.5 else "FALLA", f"Riser #{k + 1} sube con «el canal donde oler bien»", f"se oye desde {r_on:.2f}s; la frase empieza a {s_ini:.2f}s y «bien» termina a {o['bien_fin']:.2f}s")
                # fin del riser: último instante con energía antes del PUM; el PUM arranca ~10 ms antes de «siempre» (cuadro de 33 ms)
                antes = s_sie - r_off
                anota("OK" if antes >= 0.03 else "FALLA", f"Riser #{k + 1} TERMINA antes de «SIEMPRE»", f"último sonido de riser a {r_off:.3f}s; «siempre» empieza a {s_sie:.3f}s (margen {antes * 1000:.0f} ms)")
                cubre = r_off >= o["bien_fin"] - 0.5
                anota("OK" if cubre else "FALLA", f"Riser #{k + 1} cubre la frase", f"termina a {r_off:.2f}s; «bien» termina a {o['bien_fin']:.2f}s")
                # "no mantener el riser debajo del remate": después del PUM los agudos DECAEN (un riser seguiría subiendo)
                pre = float(np.mean(e_hi[int((s_sie + 0.02) / hop) : int((s_sie + 0.12) / hop)]))
                post = float(np.mean(e_hi[int((s_sie + 0.5) / hop) : int((s_sie + 0.8) / hop)]))
                anota("OK" if post <= pre - 3 or post < -70 else "FALLA", f"Riser #{k + 1} no queda debajo del remate", f"agudos (>4 kHz) justo después de «siempre»: {pre:.0f} dB; medio segundo después: {post:.0f} dB (deben decaer ≥ 3 dB, un riser seguiría subiendo)")
            ventana = e_lo[int((s_sie - 0.2) / hop) : int((s_sie + 0.5) / hop)]
            pico = float(ventana.max())
            if pico < -40:
                anota("FALLA", f"PUM #{k + 1}", "no se oye el golpe grave")
            else:
                idx = int(np.argmax(ventana >= pico - 10))
                onset = (s_sie - 0.2) + idx * hop
                anota("OK" if abs(onset - s_sie) <= 0.05 else "FALLA", f"PUM #{k + 1} sincronizado con «SIEMPRE»", f"el golpe grave arranca a {onset:.3f}s; «siempre» a {s_sie:.3f}s ({(onset - s_sie) * 1000:+.0f} ms)")
        if not plan["firma"]["oler_bien"]:
            anota("AVISO", "Riser/PUM", "el video no trae «el canal donde oler bien… siempre»: no aplica")

        # ---------- Megáfono ----------
        cz = plan["firma"].get("cierre")
        mg = cz.get("megafono") if cz else None
        if mg:
            orig = audio_f32(base, 0.0, None, SR, 1)
            n = min(len(orig), len(voz))
            o, v = orig[:n], voz[:n]
            # alineación (por si el render movió el audio unas muestras)
            seg = slice(int(0.5 * SR), int(4.5 * SR))
            lags = range(-300, 301, 3)
            mejor = min(lags, key=lambda L: float(np.mean((np.roll(v[seg], -L) - o[seg]) ** 2)))
            if mejor:
                v = np.roll(v, -mejor)
            h10 = int(0.01 * SR)
            m = n // h10
            ro = np.sqrt(np.mean(o[: m * h10].reshape(m, h10) ** 2, axis=1))
            rd = np.sqrt(np.mean((v[: m * h10] - o[: m * h10]).reshape(m, h10) ** 2, axis=1))
            rel = rd / (ro + 1e-6)
            activo = ro > 10 ** (-50 / 20)
            dif = (rel > 0.25) & activo
            t = np.arange(m) * 0.01
            fuera = dif & ((t < mg["s"] - 0.03) | (t > mg["e"] + 0.03))
            dentro_t = t[dif & (t >= mg["s"] - 0.03) & (t <= mg["e"] + 0.03)]
            anota("OK" if mejor == 0 or abs(mejor) <= 6 else "AVISO", "Alineación voz (render vs original)", f"desfase {mejor / SR * 1000:+.2f} ms")
            anota("OK" if not fuera.any() else "FALLA", "Megáfono NO toca el resto de la voz", "fuera de la ventana la voz es idéntica a la original" if not fuera.any() else f"{int(fuera.sum())} cuadros de 10 ms difieren fuera de la ventana (p. ej. a {t[fuera][0]:.2f}s)")
            if len(dentro_t):
                a0, a1 = float(dentro_t[0]), float(dentro_t[-1] + 0.01)
                ws = [w for w in palabras if w["e"] > mg["s"] - 0.01 and w["s"] < mg["e"] + 0.01]
                txt = " ".join(w["w"] for w in ws)
                anota("OK" if abs(a0 - mg["s"]) <= 0.06 and abs(a1 - mg["e"]) <= 0.08 else "FALLA", "Megáfono cubre «a lo que desean proyectar»", f"efecto de {a0:.2f}s a {a1:.2f}s; palabras: «{txt}» ({mg['s']:.2f}-{mg['e']:.2f}s)")
            else:
                anota("FALLA", "Megáfono", "no se detecta ningún cambio en la voz dentro de la ventana")
            # banda limitada: graves y agudos caen dentro de la ventana
            i0, i1 = int(mg["s"] * SR), int(mg["e"] * SR)

            def energia(x, lo, hi):
                sp = np.abs(np.fft.rfft(x[i0:i1] * np.hanning(i1 - i0))) ** 2
                fr = np.fft.rfftfreq(i1 - i0, 1 / SR)
                return 10 * math.log10(float(sp[(fr >= lo) & (fr < hi)].sum()) + 1e-12)

            for nombre, lo, hi in (("graves (<300 Hz)", 60, 300), ("agudos (>5 kHz)", 5000, 12000), ("medios (500-3000 Hz)", 500, 3000)):
                d = energia(v, lo, hi) - energia(o, lo, hi)
                if "medios" in nombre:
                    anota("OK" if d > -6 else "AVISO", f"Megáfono conserva inteligibilidad ({nombre})", f"{d:+.1f} dB respecto a la voz original")
                else:
                    anota("OK" if d <= -12 else "FALLA", f"Megáfono en banda limitada: {nombre}", f"{d:+.1f} dB respecto a la voz original (se pide ≤ -12 dB)")
        elif cz:
            anota("AVISO", "Megáfono", "el cierre no trae «a lo que desean proyectar»: no hay megáfono")

        # ---------- Rafaguiza ----------
        rf = plan["firma"].get("rafaguiza")
        if rf and rf["sprays"]:
            for k, s in enumerate(rf["sprays"]):
                a_, b_ = int((s - 0.1) / hop), int((s + 0.2) / hop)
                lv = e_hi[a_:b_]
                subida = lv[6:] - lv[:-6]  # cuánto sube en 30 ms: el arranque del PSSHT es el salto más brusco
                on = None
                if len(subida) and float(subida.max()) >= 8 and float(lv.max()) > -45:
                    on = (a_ + int(np.argmax(subida)) + 3) * hop
                anota("OK" if on is not None and abs(on - s) <= 0.07 else "FALLA", f"PSSHT del spray {k + 1}", "no se oye" if on is None else f"el PSSHT arranca a {on:.3f}s (spray a {s:.3f}s, {(on - s) * 1000:+.0f} ms)")
            peor = 0.0
            for s in rf["sprays"]:
                for dt in (0.07, 0.14):
                    d = cuadro_centro_ok(final, base, plan, fmt, s + dt, W, H)
                    if d is not None:
                        peor = max(peor, d)
            anota("OK" if peor <= 9 else "FALLA", "Rafaguiza no tapa cara ni perfume (centro del cuadro)", f"diferencia máx. en el centro respecto al video limpio: {peor:.1f}/255 (límite 9)")
        elif rf:
            anota("AVISO", "Rafaguiza", "se dijo la frase pero no hay sprays marcados: solo lleva el texto de entrada")

        # ---------- Mezcla: la voz manda ----------
        e_v, _ = env(voz)
        e_m, _ = env(mus)
        activa = np.zeros(len(e_v), bool)
        for a0, b0 in plan["voz"]:
            activa[int(a0 / hop) : int(b0 / hop)] = True
        hay_mus = float(np.max(e_m)) > -60
        if hay_mus and activa.any():
            dv = db(float(np.mean(10 ** (e_v[activa] / 10)) ** 0.5))
            dm = db(float(np.mean(10 ** (e_m[: len(activa)][activa[: len(e_m)]] / 10)) ** 0.5))
            anota("OK" if dv - dm >= 10 else "FALLA", "La voz manda sobre la música", f"bajo la voz: voz {dv:.1f} dB, música {dm:.1f} dB (diferencia {dv - dm:.1f} dB, se pide ≥ 10)")
        else:
            anota("AVISO", "Música", "no hay música en el render (no hay pista con licencia): se editó sin ella")
        # efectos vs voz: energía en ventanas de 200 ms dentro de la voz (el PUM de «SIEMPRE» se excluye: es el golpe de la firma)
        h2 = int(0.2 / hop)
        nfx = min(len(e_fx), len(e_v)) // h2
        pf = np.array([10 * math.log10(np.mean(10 ** (e_fx[i * h2 : (i + 1) * h2] / 10)) + 1e-12) for i in range(nfx)])
        pv = np.array([10 * math.log10(np.mean(10 ** (e_v[i * h2 : (i + 1) * h2] / 10)) + 1e-12) for i in range(nfx)])
        ok_v = np.array([bool(activa[i * h2 : (i + 1) * h2].mean() > 0.8) and pv[i] > -40 for i in range(nfx)])
        for o in plan["firma"]["oler_bien"]:
            ok_v[int((o["siempre"] - 0.05) / 0.2) : int((o["siempre"] + 1.1) / 0.2) + 1] = False
        if ok_v.any():
            dif_ = pf - pv
            i_peor = int(np.argmax(np.where(ok_v, dif_, -999)))
            peor = float(dif_[i_peor])
            anota("OK" if peor <= -3 else "FALLA", "Los efectos quedan por debajo de la voz", f"peor momento: efectos {peor:+.1f} dB respecto a la voz, a {i_peor * 0.2:.1f}s (se pide ≤ -3 dB)")

        # ---------- Cierre: cuerdas ----------
        if cz:
            ini = cz["inicio"]
            if plan["musica"].get("cierre"):
                cu = banda(os.path.join(sd, "cuerdas.wav"))
                e_c, _ = env(cu)
                on = primero(e_c, hop, 0.0, ini + 6.0, -75)
                nivel_ini = max(-100.0, float(np.mean(e_c[int((ini + 0.1) / hop) : int((ini + 0.4) / hop)])))
                nivel_2s = float(np.mean(e_c[int((ini + 2.2) / hop) : int((ini + 2.8) / hop)]))
                anota("OK" if on is not None and abs(on - ini) <= 0.5 else "FALLA", "Cuerdas del cierre entran al empezar «Hermosas y hermosos, denle like»", "no se oyen" if on is None else f"entran a {on:.2f}s; el cierre empieza a {ini:.2f}s ({(on - ini) * 1000:+.0f} ms)")
                anota("OK" if nivel_2s >= nivel_ini + 4 else "AVISO", "Las cuerdas suben suavemente", f"{nivel_ini:.0f} dB al empezar -> {nivel_2s:.0f} dB a los 2 s")
                voz_c = activa[: len(e_c)] & (np.arange(len(e_c)) * hop >= ini)
                if voz_c.any():
                    dvc = db(float(np.mean(10 ** (e_v[: len(e_c)][voz_c] / 10)) ** 0.5))
                    dcc = db(float(np.mean(10 ** (e_c[voz_c] / 10)) ** 0.5))
                    anota("OK" if dvc - dcc >= 10 else "FALLA", "Las cuerdas quedan por debajo de la voz", f"voz {dvc:.1f} dB, cuerdas {dcc:.1f} dB (diferencia {dvc - dcc:.1f} dB, se pide ≥ 10)")
            else:
                anota("AVISO", "Cierre sin cuerdas", "no hay pista de cuerdas con licencia: el cierre queda sin violines (ver public/musica/LEEME.md)")

    # ---------- Plan: whooshes, una idea por pantalla, sobreedición ----------
    wh = [s for s in plan["sfx"] if s.get("tag") == "whoosh"]
    wh.sort(key=lambda s: s["t"])
    sep = all(b["t"] - a_["t"] >= 2.4 for a_, b in zip(wh, wh[1:]))
    var = all(a_["archivo"] != b["archivo"] for a_, b in zip(wh, wh[1:]))
    cambios = [b["inicio"] for b in plan["beats"] if b["tipo"] in ("transicion", "split", "apoyo")]
    huerfanos = [w for w in wh if not any(-0.05 <= c - (w["t"] + 0.12) <= 0.25 for c in cambios)]
    anota("OK" if sep and var and not huerfanos else "FALLA", "Whooshes en cambios reales, variados y espaciados", f"{len(wh)} whooshes; separados ≥2.4 s: {sep}; no repiten el mismo seguido: {var}; sin cambio que los justifique: {len(huerfanos)}")
    dup = [x for x in plan["avisos"] if x.startswith("UNA IDEA")]
    anota("OK" if not dup else "FALLA", "Una idea por pantalla", "sin textos encimados" if not dup else " | ".join(dup))
    vis = sum(1 for b in plan["beats"] if b["tipo"] in ("palabra", "split", "apoyo", "transicion", "zoom", "revelacion", "veredicto", "ingredientes"))
    por_min = vis / max(total / 60, 0.5)
    anota("OK" if por_min <= 14 else "AVISO", "No sobreeditado", f"{vis} recursos visuales en {total:.0f} s ({por_min:.1f}/min; se vigila por encima de 14/min)")
    ia = [b for b in plan["beats"] if b.get("ia")]
    anota("OK" if all(b.get("etiqueta") for b in ia) else "FALLA", "Escenas de IA rotuladas como ilustración", f"{len(ia)} ilustraciones de IA, todas con etiqueta" if ia else "no hay escenas de IA")
    anota("OK", "Notas y datos solo si se dicen", "plan.py no deja pasar una nota de la franja que no se oiga entre sus palabras (revisado al resolver el plan)")
    for x in plan["avisos"]:
        if "no aparece en el audio" in x:
            anota("AVISO", "Dato del veredicto no está en el audio", x)

    # ---------- Subtítulos y lo manual ----------
    rev = os.path.join(VIDEOS, a.slug, "subtitulos-revisados.txt")
    pw = cargar(os.path.join(work, "palabras.json"))["words"]
    dudosas = [f"«{w['w']}» {w['s']:.1f}s" for w in pw if w.get("p", 1) < 0.5][:25]
    nombres = sorted({w["w"].strip(".,;:!?¡¿") for i, w in enumerate(pw) if i and w["w"][:1].isupper() and not re.search(r"[.!?]$", pw[i - 1]["w"])})
    anota("OK" if os.path.exists(rev) else "MANUAL", "Subtítulos revisados a mano (marcas, perfumes, notas)", "confirmado en subtitulos-revisados.txt" if os.path.exists(rev) else f"falta revisar con Arturo. Palabras dudosas: {', '.join(dudosas) or 'ninguna'}. Nombres propios: {', '.join(nombres) or 'ninguno'}. Cuando estén bien: escribir videos/{a.slug}/subtitulos-revisados.txt")
    perf = [b for b in plan["beats"] if b["tipo"] in ("rotulo", "palabra") and b["inicio"] <= 10]
    anota("OK" if perf else "MANUAL", "Se entiende de qué perfume habla en los primeros segundos", "hay rótulo o palabra clave en los primeros 10 s (confirmar mirando)" if perf else "no hay rótulo ni palabra clave antes de 10 s: confirmarlo mirando el video")
    anota("MANUAL", "El humor conserva su timing", "se confirma viendo el primer corte; las pausas respetadas están en work/informe_cortes.md")
    anota("MANUAL", "Colores de piel y frasco fieles / etiquetas sin deformar", "se confirma mirando los cuadros de work/qa-" + info["etiqueta"] + "-cuadros.jpg")
    usa_publica = any(plan["musica"].get(k, "") and plan["musica"][k].startswith("musica/") for k in ("base", "cierre"))
    lic = os.path.join(PUBLIC, "musica", "LICENCIAS.md")
    if plan["musica"].get("base") or plan["musica"].get("cierre"):
        anota("OK" if (usa_publica and os.path.exists(lic)) else "MANUAL", "Derechos de la música", "hay LICENCIAS.md junto a las pistas" if (usa_publica and os.path.exists(lic)) else "no hay LICENCIAS.md que pruebe la licencia: verificar antes de publicar")

    # ---------- Hoja de cuadros para MIRAR ----------
    from cuadros import hoja

    ts = [1.0]
    for ap_ in plan["firma"]["aplausos"][:1]:
        ts.append(ap_["t"] + 0.3)
    for o in plan["firma"]["oler_bien"]:
        ts += [(o["riser_ini"] + o["riser_fin"]) / 2, o["siempre"] + 0.15]
    for b in plan["beats"]:
        if b["tipo"] in ("ingredientes", "split", "apoyo", "veredicto", "palabra"):
            ts.append(min(b["fin"] - 0.2, b["inicio"] + 0.9))
    rf = plan["firma"].get("rafaguiza")
    if rf:
        ts += [rf["inicio"] + 0.4] + [s + 0.1 for s in rf["sprays"]]
    if cz:
        ts += [v + 0.35 for v in cz["iconos"].values()]
        if mg:
            ts.append((mg["s"] + mg["e"]) / 2)
    ts.append(total - 0.3)
    ts = sorted({round(min(max(0.1, x), p["duracion"] - 0.1), 2) for x in ts})
    hoja_ = os.path.join(work, f"qa-{info['etiqueta']}-cuadros.jpg")
    hoja(final, ts, hoja_, ancho=360 if fmt == "9:16" else 520, cols=5 if fmt == "9:16" else 3, fmt=fmt)
    anota("MANUAL", "Revisar cuadros mirándolos", f"abre {hoja_} (guías verdes = zona segura): texto dentro de la zona, sin tapar cara ni frasco")

    # ---------- Informe ----------
    falla = [x for x in R if x[0] == "FALLA"]
    lineas = [f"# QA de {a.slug} ({fmt}, {a.entrega})\n", f"Resultado: **{'FALLA' if falla else 'PASA'}** — {sum(1 for x in R if x[0] == 'OK')} OK, {len(falla)} fallas, {sum(1 for x in R if x[0] == 'AVISO')} avisos, {sum(1 for x in R if x[0] == 'MANUAL')} por confirmar a mano.\n", "| estado | comprobación | medición |", "|---|---|---|"]
    lineas += [f"| {e} | {n} | {d} |" for e, n, d in R]
    with open(os.path.join(work, f"qa-{info['etiqueta']}.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")
    print(f"\n{'FALLA' if falla else 'PASA'} → work/qa-{info['etiqueta']}.md")
    sys.exit(1 if falla else 0)


if __name__ == "__main__":
    main()
