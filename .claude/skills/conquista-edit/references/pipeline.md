# Pipeline: archivos, scripts y formatos

Todo se corre desde la raíz de la repo con `estudio/.venv/bin/python scripts/<script>.py`. Las rutas son relativas a la repo:
venv en `estudio/.venv`, ffmpeg en `estudio/bin/ffmpeg`, Remotion en `estudio/remotion/`. Los videos de Arturo viven en
`videos/<slug>/` (fuera de git).

```
videos/<slug>/
  crudo/               originales (solo se leen)
  apoyo/               fotos, close-ups e ilustraciones que Arturo pase
  musica/              pistas de este video (si no están en estudio/remotion/public/musica)
  work/                todo lo intermedio: base.mp4, palabras.json, plan.resuelto.json, informes, stems, hojas de cuadros
  out/                 entregas: <slug>-16x9-primer-corte.mp4, <slug>-9x16-final.mp4, ...
  analisis.md          lo escribe analyze.py
  edl.json             decisiones de corte (a mano)
  fixes.json           correcciones de palabras (a mano)
  plan.json            el plan por beats (a mano)
  subtitulos-revisados.txt   marca de que los subtítulos se revisaron con Arturo
```

## Scripts

| script | qué hace | salida clave |
|---|---|---|
| `nuevo.py <slug>` | crea las carpetas | `videos/<slug>/` |
| `analyze.py <slug> [--modelo]` | tamaño y formato, transcripción (Whisper, vocabulario del canal), pausas con su contexto, retomas, frases de firma, hojas de cuadros con zona segura | `analisis.md`, `work/analisis.json`, `work/contacto_*.jpg` |
| `cut.py <slug> [--sin-cortes]` | acorta SOLO las pausas largas (respeta `conservar` y la pausa de la firma), une clips, normaliza a 30 fps y limpia/nivela la voz, vuelve a transcribir el resultado | `work/base.mp4`, `work/palabras.json`, `work/informe_cortes.md` |
| `words.py ver|corregir <slug>` | ver palabras numeradas / aplicar `fixes.json` (idempotente) | `work/palabras.json` |
| `plan.py <slug>` | resuelve `plan.json` a segundos reales, detecta la firma, genera el riser a medida y el megáfono (ffmpeg), prepara `estudio/remotion/public/trabajo/<slug>/` | `work/plan.resuelto.json` |
| `render.py <slug> --formato ... --entrega ... [--stems]` | corre `plan.py`, renderiza con Remotion y masteriza el audio | `out/<slug>-<fmt>-<entrega>.mp4`, `work/stems-<fmt>/` |
| `qa.py <slug> --formato ...` | el checklist del manual como mediciones | `work/qa-<fmt>.md`, `work/qa-<fmt>-cuadros.jpg` |
| `cuadros.py <video> <hoja.jpg> t1 t2 ...` | hoja de cuadros con zona segura y marca de tiempo, para MIRARLA | jpg |
| `tramos_muertos.py <video>` | aviso de tramos largos sin novedad (solo ayuda de ritmo) | texto |
| `masterizar.py` | volumen parejo (-16 LUFS) y picos bajo -1 dBTP | lo usa `render.py` |
| `sintetizar_sfx.py` | riser, PUM, rayo, shimmer y PSSHT de respaldo con numpy | `public/sfx/*-sint.wav` |

El render por trozos (videos de más de 3 minutos) lo hace `estudio/remotion/scripts/render.mjs` solo.

## `edl.json` (cortes)

```json
{
  "max_pausa": 0.9,
  "pausa_objetivo": 0.5,
  "conservar": [[17.0, 18.9]],
  "keep": [{"clip": "IMG_0001.MOV", "in": 2.0, "out": 80.5, "nota": "toma buena"}],
  "quitar": [{"clip": "IMG_0001.MOV", "de": 31.0, "a": 36.2, "nota": "retoma"}]
}
```
Todos los tiempos son segundos del ORIGINAL. Sin `keep`, cada clip entra entero. Una pausa más corta que `max_pausa` no se toca
(es el ritmo de Arturo). `conservar` protege un silencio que es el chiste, una mirada o los sprays de la rafaguiza.
La pausa entre "el canal donde oler bien" y "siempre" se protege sola.

## `plan.json` (lo que decide Viernes)

```json
{
  "titulo": "Reseña de ...", "perfume": "Nombre exacto que dio Arturo",
  "foco": {"x": 0.5, "y": 0.42},
  "musica": {"base": "base-lounge.mp3", "cierre": "cierre-cuerdas.mp3", "volumen": 0.16},
  "firma": {"aplausos": true, "oler_bien": true, "cierre": true, "rafaguiza": true},
  "cola": 1.5,
  "beats": [
    {"tipo": "rotulo", "en": "hermosas", "texto": "Perfume X", "sub": "Casa Y", "dur": 3},
    {"tipo": "ingredientes", "en": "manzana", "hasta": "canela", "items": ["Manzana", {"nombre": "Lavanda", "foto": "lavanda.jpg"}, "Canela"]},
    {"tipo": "split", "en": "sale disparado", "hasta": "disparado", "apoyo": "frasco.jpg", "ia": false, "etiqueta": "..."},
    {"tipo": "split", "en": "sale disparado", "hasta": "disparado", "ilustracion": "frasco", "ia": true},
    {"tipo": "apoyo", "en": "se ve así", "hasta": "de cerca", "archivo": "closeup.mp4", "closeup": true},
    {"tipo": "palabra", "en": "un postre", "texto": "POSTRE", "efecto": "pop", "lado": "arriba"},
    {"tipo": "revelacion", "en": "dura todo el día", "sonido": "shimmer"},
    {"tipo": "veredicto", "en": "mi veredicto", "dur": 6, "titulo": "Veredicto", "puntos": ["...", "..."], "lado": "der"},
    {"tipo": "transicion", "en": "pasamos a", "estilo": "barrido"},
    {"tipo": "remate", "en": "mi ex", "sonido": "scratch"},
    {"tipo": "zoom", "en": "mira esto", "hasta": "por favor", "escala": 1.08},
    {"tipo": "rafaguiza", "sprays": [17.45, 17.85, 18.2]},
    {"tipo": "sfx", "en": "...", "sonido": "pop-1", "volumen": 0.4}
  ]
}
```
- **Anclas:** `en` = frase tal como se oye (da igual acentos y mayúsculas); `hasta` = dónde termina; `n` = cuál aparición
  (0 es la primera); `desde` = buscar después de ese segundo; `antes`/`despues` = ajuste fino en segundos; `t` = segundo exacto (último recurso).
- `foco`: dónde está su cara en el cuadro original (0 a 1); decide el recorte a 9:16.
- Archivos de `apoyo`/`foto`/`archivo`: nombres dentro de `videos/<slug>/apoyo/`. Si falta uno, `plan.py` lo dice (hay que pedírselo a Arturo).
- `ia: true` obliga a rotular la imagen como "Ilustración". `ilustracion: "frasco"` es un frasco genérico, NO el de Arturo.
- Estilos de transición: `barrido`, `zoom`, `flash`, `luz`, `iris`, `negro`, `persiana`, `shutter`.
- Remates: `pop`, `scratch`, `silencio` (con `"silencio": 0.7` en segundos: la música se corta).
- Los whooshes salen solos con `transicion`, `split` y `apoyo`; separados 2.5 s como mínimo y nunca el mismo seguido.

## Errores comunes

| síntoma | qué pasa | qué hacer |
|---|---|---|
| `No encuentro «...»` en plan.py | la frase no está en las palabras | `words.py ver`; corregir con `fixes.json` o cambiar el ancla; si Arturo no la dijo, no se pone |
| `Falta el archivo ... en apoyo/` | beat con foto que no está | pedírsela a Arturo o usar `ilustracion` con `ia: true` |
| `UNA IDEA POR PANTALLA` | dos textos grandes a la vez | separar los beats |
| render falla bajando "Chrome Headless Shell" | primera vez, necesita internet (~170 MB) | reintentar con internet: `cd estudio/remotion && npx remotion browser ensure` |
| fuentes sin cargar / render lento al inicio | Google Fonts necesita internet | revisar conexión |
| `cannot open ... metadata_errors` al transcribir | versión de `av` incompatible con faster-whisper | `requirements.txt` ya la fija (`av>=14,<17`) |
| el riser no sale | la frase "el canal donde oler bien" no está, o pasó menos de 0.5 s | ver avisos de `plan.py` |
| mensajes `objc ... AVFFrameReceiver` | ruido inofensivo de macOS (cv2 y av juntos) | ignorar |
| en Windows, `No such file` con `estudio/.venv/bin/python` | hay que correrlo desde Git Bash; ese comando es un atajo que deja `instalar.sh` | usar Git Bash o volver a correr `bash instalar.sh` |
