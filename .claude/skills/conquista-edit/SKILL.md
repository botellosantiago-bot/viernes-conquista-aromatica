---
name: conquista-edit
description: Edita los videos de Arturo, dueño del canal de perfumes de YouTube "Conquista Aromática" — reseñas de perfumes, videos largos 16:9, lives editados, Shorts, Reels y TikTok 9:16. Corta las pausas conservando el timing de comedia, transcribe y corrige subtítulos, aplica su firma sonora (aplausos en "Conquista Aromática", riser que se corta en seco y PUM en "¡SIEMPRE está en el plan!", megáfono en "a lo que desean proyectar", Rafaguiza), pantallas divididas, franja de ingredientes, veredicto, música con ducking y arma el primer corte y el final con QA medido. Úsala SIEMPRE que Arturo pida editar, cortar, montar, subtitular o arreglar un video, Short, Reel, TikTok, live, reseña o perfume ("edítame este video", "hazme un short de esto", "quítale las pausas", "ponle subtítulos"), o cuando mencione Conquista Aromática, su manual de edición, la rafaguiza o el cierre del canal, aunque no diga la palabra "skill".
---

# Edición de videos de Conquista Aromática

Arturo no es técnico. Te va a decir cosas como "edítame este video". Tú corres todo, le hablas en palabras normales y solo
le preguntas lo que de verdad falta. **No publicas nada**: dejas el video listo y Arturo decide y sube.

> **El manual de Arturo manda sobre todo lo demás:** `references/manual.md`. Léelo completo al empezar cada video (son 5 minutos
> y es la fuente de verdad). Regla de oro: *primero se entiende el perfume y la historia; después entran los efectos.*
> El humor y el timing de Arturo no se tocan para meter más edición.

## Reglas que no se rompen

1. **No inventes** notas aromáticas, precios, marcas ni datos de un perfume. Solo lo que se oye en el audio o lo que Arturo te dio.
   El kit lo hace cumplir: una nota en la franja de ingredientes solo sale si Arturo la dice.
2. **No completes palabras que no estén grabadas** (el megáfono cubre lo que está en el audio, aunque falte alguna palabra).
3. **No deformes etiquetas ni el frasco**, no le cambies la cara a Arturo y no presentes escenas de IA como hechos: toda
   ilustración de IA lleva su etiqueta "Ilustración" (`"ia": true` en el plan).
4. **Nada sin derechos claros.** La música la pone Arturo con licencia (ver `estudio/remotion/public/musica/LEEME.md`). Los
   efectos incluidos están en `estudio/remotion/public/sfx/CREDITOS.md`. Si no sabes la licencia de algo, dilo.
5. **Los originales de Arturo no se borran ni se modifican** (`videos/<slug>/crudo/` solo se lee). Cópialos, no los muevas.
6. **Di la verdad de lo que hiciste.** Lo que no mediste o no miraste, no lo declares hecho: usa lo que dice `qa.py` (OK, FALLA,
   AVISO y MANUAL) tal cual.

## Qué pedirle a Arturo si falta

Pregunta solo lo que no tengas, todo junto en un mensaje corto:

- **El video** (o los clips). Si es uno solo, basta. Si no está en `videos/`, pídele que lo arrastre o dime dónde está.
- **Para qué es:** ¿YouTube horizontal / live (16:9), o Short / Reel / TikTok (9:16), o los dos? Si dice "el video" sin más, haz 16:9 y ofrécele el vertical.
- **El nombre exacto del perfume y la casa** (como se escriben), y las **notas que sí quiere mostrar**. Nunca las deduzcas.
- **Fotos o close-ups del frasco**, atomizador, textura, ingredientes (si quiere esas tomas de apoyo).
- **Música con licencia** (lounge, lo-fi, cuerdas para el cierre). Sin música se edita igual y se le avisa qué quedó sin ella.
- **Si hay rafaguiza:** en qué segundos se aplica el perfume (se puede ver en el video; si no se oye el PSSHT, se lo preguntas).
- Si algo del audio no se entiende (un nombre de perfume, una marca), pídele cómo se escribe.

Si es un video vertical y pide 16:9 (o al revés), explícale sencillo por qué se ve recortado o con poca calidad. No estires imágenes.

## El flujo, paso por paso

Todos los comandos se corren desde la raíz de la repo, con el Python del estudio:
`estudio/.venv/bin/python scripts/<script>.py ...` (abajo escrito como `py`). Si `estudio/.venv` no existe, falta instalar:
corre `bash instalar.sh` (o avísale a Arturo que abra el instalador). El detalle de cada archivo está en `references/pipeline.md`.

**0. Prepara.** Elige un `slug` corto en minúsculas (`resena-sauvage`). `py scripts/nuevo.py <slug>` y copia los clips a
`videos/<slug>/crudo/`. Lee `references/manual.md`.

**1. Analiza.** `py scripts/analyze.py <slug>` (tarda unos minutos: transcribe). Lee `videos/<slug>/analisis.md` y MIRA la hoja
de cuadros `work/contacto_*.jpg` con la herramienta Read (las guías verdes marcan zona segura; el recuadro naranja, lo que
sobrevive al recorte 9:16). Anota dónde está la cara y el frasco (`foco`). Revisa los avisos.

**2. Transcribe y entiende.** La transcripción ya viene en `analisis.md` (por frases, con el vocabulario del canal para que
Whisper escriba "Conquista Aromática" y "rafaguiza"). Lee el video completo como lo leería Arturo: ¿de qué perfume habla, cuál es
la historia, dónde están los chistes y los remates? Eso decide TODO lo demás. Nota qué frases de firma salieron
(aplausos, "oler bien", cierre, rafaguiza) y cuáles no.

**3. Corta las pausas conservando el timing de comedia.** Las pausas largas aparecen en `analisis.md` con la palabra de antes y
de después. Decide mirando y oyendo el contexto: una pausa antes de un remate NO se quita. Escribe `videos/<slug>/edl.json`
(formato en `references/pipeline.md`): `max_pausa` (por defecto 0.9 s: solo se acortan las más largas), `conservar` para los
silencios que son el chiste, `quitar` para retomas. Corre `py scripts/cut.py <slug>`. Lee `work/informe_cortes.md` y mira los
cuadros alrededor de cada corte. Nunca recortes expresiones ni miradas. La pausa entre "el canal donde oler bien" y "SIEMPRE" se respeta sola.

**3b. Subtítulos revisados a mano.** `py scripts/words.py ver <slug>` y corrige con `videos/<slug>/fixes.json` +
`py scripts/words.py corregir <slug>` (marcas, perfumes y notas bien escritos, acentos, mayúsculas). Si dudas de un nombre,
pregúntale a Arturo. Cuando estén bien, escribe `videos/<slug>/subtitulos-revisados.txt` con una línea (quién confirmó y cuándo).

**4. Plan por beats con palabras reales.** Escribe `videos/<slug>/plan.json` (formato en `references/pipeline.md` y recursos
en `references/kit.md`). Cada beat se ancla a una frase que SÍ se oye (`"en": "huele como un postre"`); si la frase no está,
`plan.py` se detiene y te lo dice. Qué va en cada momento (todo sale del manual):
- Gancho: entrar directo al tema; rótulo con el nombre del perfume en los primeros segundos.
- "Tiene manzana, lavanda y canela" → `ingredientes` (franja con nombres grandes, sin llenar la pantalla).
- "El perfume sale disparado" / una escena narrada → `split` (Arturo abajo, apoyo arriba) con foto o ilustración rotulada.
- Close-ups del frasco, atomizador, textura → `apoyo` (y regreso a su cara antes del remate).
- Cambio real de idea o lugar → `transicion` (el whoosh sale solo, variado). Cortes limpios por defecto.
- Remate cómico → `remate` con `pop`, `scratch` o `silencio` (elige según el chiste; el silencio también es un efecto).
- Dato importante → `revelacion` (shimmer o impacto suave, sin sonar a tráiler).
- Veredicto → `veredicto` (1 a 4 puntos, de lado, sin tapar cara ni frasco).
- Una idea por pantalla. No abuses: más de ~14 recursos por minuto es sobreedición.
La firma (aplausos, riser/PUM, cierre, megáfono, rafaguiza) se detecta sola en las palabras. En la rafaguiza di los segundos
de los sprays: `{"tipo": "rafaguiza", "sprays": [17.45, 17.85, 18.2]}` (si no se oyen, pregúntale a Arturo). Corre `py scripts/plan.py <slug>`;
corrige errores hasta que no queden y lee los avisos.

**5. Compón y revisa cuadros mirándolos.** Un borrador rápido: `py scripts/render.py <slug> --formato 16:9 --entrega borrador`.
Mira cuadros reales con Read: `py scripts/cuadros.py <video.mp4> work/hoja.jpg 2 5 8.1 ...` (o `--cada 5`). Busca: texto fuera de la zona
segura, gráficos tapando la cara o el frasco, texto ilegible en celular, dos ideas a la vez, recortes que cortan la cara. Corrige el plan.

**6. Primer corte.** `py scripts/render.py <slug> --formato 16:9 --entrega primer-corte --stems` (y lo mismo con `9:16` si lo pidió).
Luego `py scripts/qa.py <slug> --formato 16:9`. Videos largos (más de 3 minutos) se renderizan solos por trozos. Lee el
informe `work/qa-16x9.md`: cada FALLA se corrige (ver `references/qa.md`); cada MANUAL lo confirmas tú mirando o se lo preguntas a Arturo.

**7. Entrega del primer corte.** Mensaje corto para Arturo: dónde está el video (`videos/<slug>/out/`), qué decidiste
(1–2 líneas), **qué debe revisar: ritmo y chistes**, y qué quedó pendiente (música, subtítulos por confirmar, sprays). No lo
publiques. Si no hubo música o cuerdas, dilo.

**8. Correcciones.** Arturo dirá "quita ese zoom", "ese chiste no", "más rápido". Cambia `plan.json` o `edl.json` (y vuelve a
correr `cut.py` si cambian cortes; entonces revisa las palabras otra vez) y renderiza de nuevo. Una corrección a la vez; avísale qué cambió.

**9. Final.** `py scripts/render.py <slug> --formato ... --entrega final --stems` y `qa.py` otra vez (`--entrega final`). Entrega
con el resumen de lo medido (de verdad, copiado de `qa.py`), lo que sigue manual y el aviso de verificar derechos de música,
efectos, fotos y material generado antes de publicar. Si pide, deja el proyecto editable: `videos/<slug>/plan.json`, `edl.json`
y `estudio/remotion/` son el archivo de proyecto.

## Formatos y zonas seguras

- **16:9 (1920x1080):** YouTube largo y lives. **9:16 (1080x1920):** Shorts, Reels, TikTok. Mismo plan, dos composiciones.
- Zona segura de texto: 9:16 x 80–900, y 250–1400 (botones y descripción de las apps); 16:9 margen de 5%. El kit ya la respeta.
- Un video horizontal pasa a 9:16 recortando alrededor de su `foco` (la cara). Con 1080p queda blando: sugiere grabar vertical o 4K.
- Videos largos: render por trozos automático (`render.mjs`). Un live de una hora tarda en renderizar; avísale a Arturo.

## Cuando algo sale mal

- `plan.py` dice que no encuentra una frase: mira `words.py ver`; si Whisper la escribió distinto, corrígela con `fixes.json`; si Arturo no la dijo, no se inventa.
- El render se queja de una fuente o de Chrome: necesita internet la primera vez (fuentes de Google y el navegador interno de Remotion).
- Nada de contraseñas, llaves ni cuentas: no las pidas ni las guardes; ante cualquier cosa rara con eso, detente y avísale a Arturo.

## Referencias

- `references/manual.md` — el manual de Arturo, fiel y completo. **Manda.**
- `references/kit.md` — el kit Remotion: qué hace cada pieza, identidad visual (propuesta), sonidos, música.
- `references/pipeline.md` — archivos, scripts, formatos de `edl.json` y `plan.json`, errores comunes.
- `references/qa.md` — el checklist del manual convertido en mediciones, y qué hacer con cada falla.
