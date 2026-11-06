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

# En Windows "python3" puede ser el acceso falso de la Microsoft Store: se usa el primero que de verdad corra.
PY_VOZ=""
for candidato in python3 python py; do
  if "$candidato" -c 'pass' >/dev/null 2>&1; then PY_VOZ="$candidato"; break; fi
done
[ -n "$PY_VOZ" ] || PY_VOZ=python3

ARCHIVO="$("$PY_VOZ" - "$CARPETA" "$RECIENTES" <<'PY' 2>/dev/null
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
ARCHIVO="${ARCHIVO%$'\r'}"  # Python en Windows termina las líneas con \r\n
[ -n "$ARCHIVO" ] || ARCHIVO="$(ls "$CARPETA" | head -1)"
[ -n "$ARCHIVO" ] || exit 0

if command -v afplay >/dev/null 2>&1; then
  afplay "$CARPETA/$ARCHIVO" >/dev/null 2>&1
elif command -v powershell.exe >/dev/null 2>&1; then
  # Windows: el reproductor que ya trae el sistema, sin instalar nada. Espera a que termine la frase.
  VIERNES_MP3="$(cygpath -w "$CARPETA/$ARCHIVO")" powershell.exe -NoProfile -NonInteractive -Command '
    Add-Type -AssemblyName PresentationCore
    $p = New-Object System.Windows.Media.MediaPlayer
    $p.Open([Uri]$env:VIERNES_MP3)
    $t = 0
    while (-not $p.NaturalDuration.HasTimeSpan -and $t -lt 50) { Start-Sleep -Milliseconds 100; $t++ }
    $p.Play()
    if ($p.NaturalDuration.HasTimeSpan) { Start-Sleep -Milliseconds ([int]$p.NaturalDuration.TimeSpan.TotalMilliseconds + 250) }
    $p.Close()
  ' >/dev/null 2>&1
elif command -v ffplay >/dev/null 2>&1; then
  ffplay -nodisp -autoexit -loglevel quiet "$CARPETA/$ARCHIVO" >/dev/null 2>&1
elif command -v mpg123 >/dev/null 2>&1; then
  mpg123 -q "$CARPETA/$ARCHIVO" >/dev/null 2>&1
fi
exit 0
