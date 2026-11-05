# QA: el checklist del manual convertido en mediciones

El manual de Arturo (secciones 2, 8, 9, 10 y 11) pide cosas que se pueden OÍR y MEDIR. `scripts/qa.py` las mide sobre el video
renderizado y sobre el audio por partes ("stems": voz, efectos, música y cuerdas por separado, que saca `render.py --stems`).
Así nada se declara "bien" por suposición.

```
py scripts/render.py <slug> --formato 16:9 --entrega primer-corte --stems
py scripts/qa.py <slug> --formato 16:9
```
Estados: **OK** | **FALLA** (se corrige, y se vuelve a renderizar y medir) | **AVISO** (lo dices en la entrega) |
**MANUAL** (lo confirma Viernes mirando o Arturo; nunca se marca como hecho sin que se haya hecho).
Sale con código 1 si hay alguna FALLA. El informe queda en `videos/<slug>/work/qa-<fmt>.md`.

## Del checklist del manual a la medición

| manual | qué se mide | tolerancia |
|---|---|---|
| Riser "solo en *el canal donde oler bien*" (§2, §6, §9) | En el stem de efectos: el riser se oye desde la frase (medido cuando está 35 dB bajo su pico) y no antes de 0.12 s antes de "el" | empieza entre -0.12 s y +0.5 s de "el" |
| Riser "quitado justo antes de *SIEMPRE*" (§2) | Último instante con riser antes del PUM; "siempre" empieza después | margen ≥ 30 ms |
| "No mantener el riser debajo del remate" (§2) | Agudos (>4 kHz) desde "siempre" hasta +0.8 s contra el pico del riser | ≥ 25 dB menos |
| PUM sincronizado con *SIEMPRE* (§2) | Arranque del golpe grave (<150 Hz) contra el inicio de la palabra | ± 50 ms |
| Aplausos en "Conquista Aromática" (§2, §9) | Arranque del aplauso contra la palabra; a los 2 s ya no suenan | ± 80 ms; < -45 dB a los 2 s |
| Aplausos "bajar rápidamente para no tapar la voz" (§2) | Efectos vs voz en ventanas de 200 ms | efectos ≤ -3 dB bajo la voz (se excluye el PUM de SIEMPRE y su cola) |
| Megáfono SOLO en "a lo que desean proyectar" (§10) | Se resta la voz del render menos la voz original, cuadro a cuadro de 10 ms: fuera de la ventana debe ser idéntica; dentro, distinta | 0 cuadros distintos fuera; ventana = palabras (± 60 ms al inicio, ± 80 ms al final) |
| Megáfono de "banda limitada" sin perder inteligibilidad (§10) | Energía de graves (<300 Hz) y agudos (>5 kHz) dentro de la ventana contra la original; los medios (0.5–3 kHz) se conservan | graves y agudos ≤ -12 dB; medios > -6 dB |
| Cuerdas entran al empezar "Hermosas y hermosos, denle like" (§10) | Stem de cuerdas: cuándo suena la primera nota; suben suave; quedan bajo la voz | ± 500 ms (una pista con intro lenta entra más tarde); +4 dB en 2 s; ≥ 10 dB bajo la voz |
| PSSHT sincronizado con cada spray (§11) | Salto brusco de agudos en cada spray | ± 70 ms |
| Rafaguiza "no cubrir el rostro ni el producto" (§11) | Se compara el centro del cuadro (donde van cara y perfume) del video final con el video limpio de Arturo en cada spray | diferencia media < 9 de 255 |
| "La voz siempre manda", "música por debajo" (§2, §8) | Voz vs música durante la voz | ≥ 10 dB |
| "Efectos sin saturación, evitar picos" (§2, §8) | True peak del video final con `ebur128` | ≤ -1.0 dBTP |
| "Volumen consistente" (§8) | LUFS integrados del video final | -16 ± 1.5 |
| "Whoosh variado, no repetir en cada corte" (§2, §4) | Whooshes: separados ≥ 2.4 s, no el mismo archivo seguido, cada uno junto a un cambio real (transición, split, apoyo) | todas |
| "Máximo una idea por pantalla" (§4) | Textos grandes que se encimen (plan) | ninguno |
| "No abusar de zooms, memes, sonidos o transiciones" (§8) | Recursos visuales por minuto | aviso si > 14/min |
| "No presentar escenas de IA como hechos" (§5) | Todo beat con `ia: true` lleva etiqueta "Ilustración" | todas |
| "No inventar notas aromáticas" (§5) | La franja solo acepta notas que se oyen en esas palabras (lo comprueba `plan.py`); en el veredicto, una palabra larga que no esté en el audio da aviso | error / aviso |
| Formato 16:9 o 9:16 (§8) | Tamaño y fps del video final; duración contra el plan | exactos |

## Lo que solo puede confirmar una persona (estado MANUAL)

- **Subtítulos revisados** (marcas, perfumes, notas): la lista de palabras dudosas y nombres propios sale en el informe. Se
  revisa con Arturo y se escribe `videos/<slug>/subtitulos-revisados.txt`.
- **¿Se entiende de qué perfume habla en los primeros segundos?** Se mira el primer corte.
- **El humor conserva su timing, no está sobreeditado:** se ve el primer corte; las pausas que se respetaron están en `work/informe_cortes.md`.
- **La cara de Arturo y los textos:** el kit coloca los textos en posiciones fijas y no detecta su cara. En cada cuadro de 9:16 revisa que nada le tape la cara; si pasa, cambia `foco` o `lado` en el plan.
- **Piel natural, frasco fiel, etiquetas sin deformar, sin tapar cara ni frasco, texto dentro de zona segura:** MIRAR cuadros.
  `qa.py` deja `work/qa-<fmt>-cuadros.jpg` con los momentos de firma y las guías de zona segura: ábrelo con Read y míralo de verdad.
- **Derechos** de música, efectos, fotos y material generado antes de publicar (§8). La música sin `LICENCIAS.md` queda en MANUAL.
- **Que la voz se entienda perfecto:** lo medido (voz ≥ 10 dB sobre la música) no sustituye oírla.

## Qué hacer con una FALLA

| falla | causa probable | arreglo |
|---|---|---|
| El riser pasa de "siempre" o no cae el PUM | `siempre` mal transcrito o tiempos de Whisper corridos | `words.py ver` / `fixes.json` con `tiempo`; volver a `plan.py` |
| Megáfono toca otras palabras / no cubre todas | tiempos de palabra imprecisos en el audio continuo | corregir los tiempos de "a" y "proyectar" en `fixes.json`; el borde se ajusta solo al valle de energía más cercano |
| PSSHT desfasado | `sprays` mal marcados | medir el spray real en el video y corregir los segundos |
| Rafaguiza tapa el centro | efecto demasiado grande para el encuadre | bajar `poder` (`"poder": false` en el beat `rafaguiza`) o dejar solo el destello |
| La voz no manda | música muy alta | bajar `musica.volumen` en el plan |
| Picos sobre -1 dBTP | no debería pasar con el master; si pasa, algo se cortó | volver a masterizar con `masterizar.py` y revisar |
| Whooshes juntos | demasiados cambios seguidos | quitar transiciones; el manual prefiere cortes limpios |

Cuando todo lo medible esté OK, la entrega cuenta honestamente: qué se midió, qué quedó en MANUAL y qué se avisó.
Una prueba con voz sintética no demuestra que Whisper entienda la voz de Arturo; con su voz real se revisan las palabras primero.
