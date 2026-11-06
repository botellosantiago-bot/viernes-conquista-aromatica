"""Utilidades compartidas: rutas de la repo, ffmpeg, audio, palabras y Whisper.

Todo se resuelve en relación con ESTA carpeta, así que la repo se puede mover o clonar donde sea.
"""
import json
import os
import re
import subprocess
import sys
import unicodedata

# Que los hijos de Python hablen UTF-8 también en Windows: acentos y símbolos no deben tronar en la consola.
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
for _flujo in (sys.stdout, sys.stderr):
    try:
        _flujo.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# cv2 y av traen cada uno su libavdevice y macOS avisa en la consola; es solo ruido.
os.environ.setdefault("OPENCV_LOG_LEVEL", "ERROR")

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(SCRIPTS)
ESTUDIO = os.path.join(RAIZ, "estudio")
REMOTION = os.path.join(ESTUDIO, "remotion")
PUBLIC = os.path.join(REMOTION, "public")
TRABAJO = os.path.join(PUBLIC, "trabajo")  # copias de trabajo para Remotion (fuera de git)
VIDEOS = os.path.join(RAIZ, "videos")
# En Windows el Python del entorno vive en Scripts\\python.exe; bin/python es solo un atajo para Git Bash.
PY = os.path.join(ESTUDIO, ".venv", "Scripts", "python.exe") if os.name == "nt" else os.path.join(ESTUDIO, ".venv", "bin", "python")
FPS = 30
SR = 48000


def _ffmpeg():
    local = os.path.join(ESTUDIO, "bin", "ffmpeg.exe" if os.name == "nt" else "ffmpeg")
    if os.path.exists(local):
        return local
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


FF = os.environ.get("CONQUISTA_FFMPEG") or _ffmpeg()


def vdir(slug, *partes):
    """videos/<slug>/... (crea las carpetas)."""
    d = os.path.join(VIDEOS, slug, *partes)
    os.makedirs(d if not os.path.splitext(d)[1] else os.path.dirname(d), exist_ok=True)
    return d


def existe_video(slug):
    if not os.path.isdir(os.path.join(VIDEOS, slug)):
        sys.exit(f"No existe videos/{slug}. Primero: python scripts/nuevo.py {slug}")


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def ff(*args, silencioso=True):
    cmd = [FF, "-hide_banner", "-loglevel", "error" if silencioso else "info", "-y", *args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"ffmpeg falló:\n{' '.join(cmd)}\n{r.stderr[-1500:]}")
    return r


def probe(ruta):
    """Duración, tamaño, rotación, fps y audio con PyAV."""
    import av

    with av.open(ruta) as c:
        v = next((s for s in c.streams if s.type == "video"), None)
        a = next((s for s in c.streams if s.type == "audio"), None)
        rot = 0
        if v is not None:
            try:
                rot = int(float(v.metadata.get("rotate", 0))) if v.metadata else 0
            except ValueError:
                rot = 0
            try:
                sd = getattr(v, "side_data", None) or {}
                m = sd.get("DISPLAYMATRIX") if hasattr(sd, "get") else None
                if m is not None:
                    rot = int(round(-float(m))) % 360
            except Exception:
                pass
        dur = float(c.duration / 1_000_000) if c.duration else 0.0
        info = {
            "duracion": round(dur, 3),
            "ancho": v.codec_context.width if v else 0,
            "alto": v.codec_context.height if v else 0,
            "rotacion": rot,
            "fps": round(float(v.average_rate), 3) if v and v.average_rate else 0,
            "audio": bool(a),
        }
    w, h = info["ancho"], info["alto"]
    if abs(info["rotacion"]) in (90, 270):
        w, h = h, w
    info["ancho_visible"], info["alto_visible"] = w, h
    info["vertical"] = h > w
    return info


def audio_f32(ruta, desde=0.0, hasta=None, sr=SR, canales=1):
    """Audio como arreglo float32 (muestras, canales) o (muestras,) si es mono."""
    import numpy as np

    cmd = [FF, "-v", "error", "-ss", f"{desde:.4f}", "-i", ruta]
    if hasta is not None:
        cmd += ["-t", f"{hasta - desde:.4f}"]
    cmd += ["-vn", "-ac", str(canales), "-ar", str(sr), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    return x if canales == 1 else x.reshape(-1, canales)


_env = {}


def envolvente(ruta):
    """Energía (dBFS) en ventanas de 10 ms, 16 kHz mono."""
    import numpy as np

    if ruta not in _env:
        x = audio_f32(ruta, sr=16000)
        n = len(x) // 160
        _env[ruta] = 20 * np.log10(np.sqrt(np.mean(x[: n * 160].reshape(n, 160) ** 2, axis=1)) + 1e-9)
    return _env[ruta]


def norm(w):
    w = unicodedata.normalize("NFD", w.lower())
    return re.sub(r"[^a-z0-9%]", "", "".join(c for c in w if unicodedata.category(c) != "Mn"))


# Vocabulario del canal: ayuda a Whisper a escribir bien las frases de firma (salen del manual, no se inventan).
PROMPT_CANAL = (
    "Reseña de perfumes. ¡Hermosas y hermosos, bienvenidos a Conquista Aromática! "
    "El canal donde oler bien, ¡siempre está en el plan! ¡Es hora de darnos una rafaguiza! "
    "Denle like, toca la campanita y suscríbete."
)
ALUCINACIONES = ("subtítulos realizados", "amara.org", "subtitulos por")

_modelos = {}


def whisper(modelo="medium"):
    if modelo not in _modelos:
        from faster_whisper import WhisperModel

        _modelos[modelo] = WhisperModel(modelo, device="cpu", compute_type="int8")
    return _modelos[modelo]


def transcribir(ruta, modelo="medium", prompt=None):
    """Palabras con tiempos. Modo literal (sin VAD) para no tragarse repeticiones ni titubeos."""
    m = whisper(modelo)
    segs, _ = m.transcribe(
        ruta,
        language="es",
        word_timestamps=True,
        vad_filter=False,
        condition_on_previous_text=False,
        initial_prompt=(prompt or PROMPT_CANAL),
        temperature=0,
    )
    palabras, lineas = [], []
    for s in segs:
        if any(h in s.text.lower() for h in ALUCINACIONES):
            continue
        lineas.append({"s": round(s.start, 2), "e": round(s.end, 2), "texto": s.text.strip()})
        for w in s.words or []:
            palabras.append({"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3), "p": round(w.probability, 2)})
    return palabras, lineas


def guardar(obj, ruta):
    os.makedirs(os.path.dirname(os.path.abspath(ruta)), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def cargar(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def valle(db, t, radio=0.08):
    """Instante (s) de menor energía en t±radio: para cortar o cambiar de proceso sin pisar una sílaba."""
    import numpy as np

    a = max(0, int((t - radio) * 100))
    b = min(len(db), int((t + radio) * 100) + 1)
    if b <= a:
        return t
    seg = db[a:b]
    mn = seg.min()
    idx = np.where(seg <= mn + 1.5)[0]
    cercano = idx[np.argmin(np.abs((a + idx) / 100 - t))]
    return (a + int(cercano)) / 100


# ---- Formatos ----
FORMATOS = {
    "16:9": {"id": "Conquista16x9", "w": 1920, "h": 1080, "etiqueta": "16x9"},
    "9:16": {"id": "Conquista9x16", "w": 1080, "h": 1920, "etiqueta": "9x16"},
}


def formato(valor):
    v = valor.replace("x", ":").replace("X", ":")
    if v not in FORMATOS:
        sys.exit(f"Formato desconocido «{valor}». Usa 16:9 o 9:16.")
    return v


def trabajo(slug):
    d = os.path.join(TRABAJO, slug)
    os.makedirs(d, exist_ok=True)
    return d


def filtro_desde_archivo(ruta):
    """Argumentos para que ffmpeg lea un filtergraph largo de un archivo (cambió de nombre en ffmpeg 7)."""
    r = subprocess.run([FF, "-version"], capture_output=True, text=True).stdout
    m = re.search(r"version\s+n?(\d+)", r)
    mayor = int(m.group(1)) if m else 7
    return ["-/filter_complex", ruta] if mayor >= 7 else ["-filter_complex_script", ruta]
