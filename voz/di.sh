#!/bin/bash
# Viernes dice en voz alta una frase ya grabada. No usa internet ni llaves.
# Uso: bash voz/di.sh <grupo>     (saludo, sesion, listo, listo_humor, listo_con_pero, no_pude, entregado, espera_ok)
# No repite las últimas frases. Si no se puede reproducir audio, sale sin hacer ruido: hablar nunca debe romper el trabajo.
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GRUPO="${1:-listo}"
CARPETA="$RAIZ/voz/audio/$GRUPO"
[ -d "$CARPETA" ] || exit 0

ESTADO="$RAIZ/.viernes-estado"
mkdir -p "$ESTADO" 2>/dev/null
RECIENTES="$ESTADO/recientes-$GRUPO"

ARCHIVO="$(python3 - "$CARPETA" "$RECIENTES" <<'PY' 2>/dev/null
import os, random, sys
carpeta, recientes = sys.argv[1], sys.argv[2]
todas = sorted(f for f in os.listdir(carpeta) if f.endswith(".mp3"))
try:
    usadas = open(recientes).read().split()
except OSError:
    usadas = []
libres = [f for f in todas if f not in usadas] or todas
elegida = random.choice(libres)
usadas = (usadas + [elegida])[-max(1, len(todas) // 2):]
try:
    open(recientes, "w").write("\n".join(usadas))
except OSError:
    pass
print(elegida)
PY
)"
[ -n "$ARCHIVO" ] || ARCHIVO="$(ls "$CARPETA" | head -1)"
[ -n "$ARCHIVO" ] || exit 0

if command -v afplay >/dev/null 2>&1; then
  afplay "$CARPETA/$ARCHIVO" >/dev/null 2>&1
elif command -v ffplay >/dev/null 2>&1; then
  ffplay -nodisp -autoexit -loglevel quiet "$CARPETA/$ARCHIVO" >/dev/null 2>&1
elif command -v mpg123 >/dev/null 2>&1; then
  mpg123 -q "$CARPETA/$ARCHIVO" >/dev/null 2>&1
fi
exit 0
