# El kit de edición (Remotion)

Vive en `estudio/remotion/src/kit/`. Todo el kit mide el lienzo con `useVideoConfig` (nada de 1080x1920 fijo), así que el
mismo plan sale en **16:9 (1920x1080)** y en **9:16 (1080x1920)**. Las composiciones son `Conquista16x9` y `Conquista9x16`
(`src/Root.tsx`); las dos leen `public/trabajo/<slug>/plan.resuelto.json`, que escribe `scripts/plan.py`.
Casi nunca hay que tocar TypeScript: se decide en `plan.json` y se renderiza. Se edita el kit solo para cambiar cómo se ve algo.

## Identidad visual: PROPUESTA de Viernes

> Arturo **no ha definido marca** (logo, paleta ni tipografía). Lo de abajo es una propuesta mía para que el canal se vea
> elegante pero juvenil. Si Arturo trae su marca, se cambia en un solo archivo y todo el kit la sigue.

Todo color y toda fuente salen de **`src/kit/theme.ts`**, y de ningún otro lado:

| rol | valor | uso |
|---|---|---|
| negro cálido | `#14100C` | fondos, plecas, tarjetas |
| crema | `#FFF4E0` | texto principal |
| ámbar | `#F2A83B` | palabra activa del subtítulo, líneas, palabra clave |
| dorado | `#E8C77A` | detalles y texto secundario |
| acento vivo (coral-rosa) | `#FF4D6D` | golpes: "SIEMPRE", rafaguiza, megáfono, suscríbete |
| rayo | `#9FD8FF` | rayos eléctricos de la Rafaguiza |

Tipografías (Google Fonts, vía `@remotion/google-fonts`): **Fraunces** (serif con carácter: rótulos, veredicto) y **Outfit**
(muy legible en celular: subtítulos, palabras clave, franja). Necesitan internet la primera vez que se renderiza.

## Piezas

| pieza | archivo | qué hace | se activa con |
|---|---|---|---|
| Voz + ducking de música | `Mezcla.tsx` | La música baja ~12 dB mientras Arturo habla (baja en 0.12 s, sube en 0.55 s) y se corta un instante en un remate de silencio. Sin pista de música no hace nada y no falla. | `musica` en el plan, o pistas `base*` / `cierre*` en `public/musica` |
| Video de Arturo | `Fondo.tsx` | Recorte "cover" alrededor del `foco`; congela el último cuadro en la cola. Su audio es la voz (si hay megáfono, el video va mudo y la voz sale de `voz.flac`, ver abajo). | siempre |
| Subtítulos | `Subtitulos.tsx` | Frases cortas, palabra activa en ámbar, zona segura, se apagan cuando otro elemento muestra las mismas palabras. | siempre (palabras de `palabras.json`) |
| Palabra clave | `PalabraClave.tsx` | Una palabra enorme, con borde, `pop` o `shimmer`. `lado`: arriba / abajo / izq / der. | `{"tipo":"palabra"}` |
| Revelación | `PalabraClave.tsx` | Chispas suaves + sonido shimmer o impacto suave. | `{"tipo":"revelacion"}` |
| Franja de ingredientes | `Ingredientes.tsx` | Foto o inicial de cada nota con su nombre grande, entra en el instante en que Arturo la dice. | `{"tipo":"ingredientes"}` |
| Split / PiP | `Split.tsx` | Arturo abajo, apoyo arriba (`modo: "split"`); o apoyo a pantalla completa con Arturo en recuadro (`"pip"`). Foto, video o `FrascoIlustrado` (genérico, rotulado "Ilustración"). | `{"tipo":"split"}` |
| Apoyo / close-up | `Split.tsx` | Foto o video a pantalla completa con empuje lento. | `{"tipo":"apoyo"}` |
| Veredicto | `Veredicto.tsx` | Tarjeta con 1–4 puntos que entran uno a uno; `lado`: der / izq / abajo. | `{"tipo":"veredicto"}` |
| Rótulo | `Veredicto.tsx` | Nombre del perfume y la casa, esquina superior. | `{"tipo":"rotulo"}` |
| Firma "oler bien" | `Firma.tsx` + `Mezcla.tsx` | Riser a la medida que sube SOLO durante "el canal donde oler bien" y se corta en seco; brillo ámbar por los bordes mientras sube; PUM grave en "SIEMPRE" + texto "¡SIEMPRE ESTÁ EN EL PLAN!", anillo y temblor breve. | automático |
| Aplausos | `Firma.tsx` + `Mezcla.tsx` | Aplauso breve que arranca con "Conquista" y se apaga rápido; confeti dorado por los costados. | automático (primera mención) |
| Rafaguiza | `Rafaguiza.tsx` | Texto de entrada + en cada spray PSSHT → destello (1.º), rayo (2.º), aura de poder y partículas (3.º). Todo por los bordes: el centro nunca se tapa. | automático si dice "rafaguiza"; sprays en el beat `rafaguiza` |
| Cierre del canal | `Cierre.tsx` + `Mezcla.tsx` | Cuerdas que entran en "Hermosas y hermosos, denle like" (suben 2.5 s, por debajo de la voz, cola de 1.5 s); iconos discretos de like / campanita / suscríbete; señal de megáfono. | automático si dice "denle like" |
| Megáfono | `Conquista.tsx` + `scripts/plan.py` | `plan.py` procesa con ffmpeg SOLO "a lo que desean proyectar" (banda 400–3500 Hz, saturación ligera, mismo volumen) y guarda ese tramo en `fx/megafono.wav`. Luego arma `fx/voz.flac`: la voz original muestra por muestra con el tramo empalmado (8 ms por borde). El kit reproduce esa pista en lugar del audio del video, así que el efecto cae exactamente en esas palabras y el resto de la voz queda idéntica. | automático ("a lo que desean proyectar") |
| Transiciones | `Transiciones.tsx` | barrido, zoom, flash, luz (fuga ámbar), iris, negro, persiana, shutter; adaptadas del kit del estudio y medidas con el tamaño real. | `{"tipo":"transicion"}` |

Reglas del kit que salen del manual: transiciones solo en cambios reales; textos grandes y una idea por pantalla (el plan
avisa si se encima); no se tapa la cara ni el frasco; "no abusar de zooms, memes, sonidos o transiciones".

## Cómo suena (todo el audio)

- La **voz** es el audio del video base (ya limpia y nivelada por `cut.py`). Manda siempre.
- La **música** se decide en el plan y baja bajo la voz. Hay una pista base hasta el cierre y las cuerdas desde el cierre.
- Los **efectos** los coloca `plan.py` con sus tiempos exactos y volúmenes, uno por evento (whoosh variado y nunca seguido,
  aplausos, riser, PUM, pop, scratch, shimmer, PSSHT, rayo). Los mantiene por debajo de la voz.
- Al final `masterizar.py` pone el volumen parejo (-16 LUFS) y deja los picos bajo -1 dBTP.

## Sonidos incluidos (`estudio/remotion/public/sfx/`, menos de 2 MB)

Créditos y licencias en `public/sfx/CREDITOS.md`. Resumen:

| tipo | archivos |
|---|---|
| whoosh | `whoosh-1` (corto), `whoosh-2` (largo), `whoosh-3` (seco) |
| aplauso | `aplauso-1` (breve), `aplauso-2` (público pequeño) |
| riser | `riser-sint-3s.wav` de muestra; el real lo genera `plan.py` con la duración exacta de la frase |
| PUM | `pum-sint.wav` (grave, corto) |
| pop | `pop-1`, `pop-2` (corcho) |
| scratch | `scratch-1` (largo), `scratch-2` (corto) |
| shimmer | `shimmer-1`, `shimmer-2`, `shimmer-sint.wav` |
| PSSHT | `psst-1` (largo), `psst-3` (corto), `psst-sint.wav` (respaldo) |
| rayo | `rayo-sint.wav` |

Los `*-sint` los genera `scripts/sintetizar_sfx.py` con numpy (sin muestras de terceros). El resto son grabaciones CC0 de Freesound.
Para añadir uno: copiarlo a `public/sfx/`, anotarlo en `CREDITOS.md` con su licencia comprobada y darle su ganancia en `GANANCIA` de `scripts/plan.py`.

## Música

No hay ninguna pista incluida. Arturo pone las suyas en `estudio/remotion/public/musica/` (ver `LEEME.md` ahí) y anota su licencia
en `LICENCIAS.md` junto a ellas. Nombres sugeridos: `base-lounge.mp3`, `base-lofi.mp3`, `cierre-cuerdas.mp3`. Sin pistas el video se
edita igual, sin música; el cierre queda sin cuerdas y `plan.py`/`qa.py` lo avisan. Nunca uses una pista de la que no se sepa la licencia.

## Probar el kit a mano

`cd estudio/remotion && npx remotion studio` abre el editor visual. La composición necesita un plan resuelto: primero corre
`plan.py` de algún video. Comprobación de tipos: `cd estudio/remotion && npx tsc --noEmit`.

## Por qué la voz del megáfono va en una pista aparte

Remotion silencia y mezcla el audio por cuadros (1/30 s) y, medido en la prueba, el corte de volumen cae unos 25 ms antes de
la frontera del cuadro. Silenciar la voz del video y mezclar encima el tramo procesado dejaba un hueco de ~25 ms antes de
"a lo que desean proyectar". Por eso `plan.py` empalma el tramo procesado en la voz original (muestra por muestra) y el kit
reproduce esa pista. `qa.py` lo comprueba restando esa voz de la original: fuera de las palabras del megáfono tiene que ser idéntica.
