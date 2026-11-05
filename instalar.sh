#!/bin/bash
# Deja a Viernes lista en esta Mac. Se puede correr las veces que haga falta: solo hace lo que falte.
# Uso: bash instalar.sh
# No toca nada fuera de esta carpeta, salvo crear el acceso "Abrir Viernes" en el Escritorio.
set -uo pipefail
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ESTUDIO="$RAIZ/estudio"

alto() {
  echo
  echo "✋ $1"
  echo "   Cuando esté, vuelve a correr: bash instalar.sh"
  echo "   Si te atoras, mándale este mensaje a Santiago."
  exit 1
}

echo "Instalando a Viernes. La primera vez tarda unos minutos y necesita internet."
echo

command -v python3 >/dev/null 2>&1 || alto "Falta Python 3. Instálalo desde https://www.python.org/downloads/"
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' || alto "Python es muy viejo: hace falta 3.10 o más nuevo. Instálalo desde https://www.python.org/downloads/"
command -v node >/dev/null 2>&1 || alto "Falta Node.js. Instala la versión LTS desde https://nodejs.org/"
NODE_MAYOR="$(node -p 'process.versions.node.split(".")[0]')"
[ "$NODE_MAYOR" -ge 18 ] || alto "Node.js es muy viejo: hace falta 18 o más nuevo. Instala la LTS desde https://nodejs.org/"
command -v npm >/dev/null 2>&1 || alto "Falta npm. Viene con Node.js: reinstálalo desde https://nodejs.org/"

if [ ! -x "$ESTUDIO/.venv/bin/python" ]; then
  echo "→ Preparando Python"
  python3 -m venv "$ESTUDIO/.venv" || alto "No se pudo crear el entorno de Python."
fi
if ! "$ESTUDIO/.venv/bin/python" -c 'import faster_whisper, cv2, imageio_ffmpeg' >/dev/null 2>&1; then
  echo "→ Instalando herramientas de transcripción y video"
  "$ESTUDIO/.venv/bin/python" -m pip install -q --upgrade pip || alto "No se pudo actualizar pip. Revisa tu internet."
  "$ESTUDIO/.venv/bin/python" -m pip install -q -r "$ESTUDIO/requirements.txt" || alto "No se pudieron instalar las herramientas de Python. Revisa tu internet."
fi
echo "✓ Python listo"

FFMPEG="$("$ESTUDIO/.venv/bin/python" -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')" || alto "No se encontró ffmpeg."
mkdir -p "$ESTUDIO/bin"
ln -sfn "$FFMPEG" "$ESTUDIO/bin/ffmpeg"
"$ESTUDIO/bin/ffmpeg" -version >/dev/null 2>&1 || alto "ffmpeg no arranca."
echo "✓ ffmpeg listo"

if [ ! -d "$ESTUDIO/remotion/node_modules" ]; then
  echo "→ Instalando el editor de video"
  (cd "$ESTUDIO/remotion" && npm ci --no-audit --no-fund --silent) || alto "No se pudo instalar el editor de video. Revisa tu internet."
fi
echo "→ Revisando el navegador del editor (la primera vez baja unos 170 MB)"
(cd "$ESTUDIO/remotion" && npx --no-install remotion browser ensure >/dev/null 2>&1) || alto "No se pudo bajar el navegador del editor. Revisa tu internet."
echo "✓ Editor de video listo"

echo "→ Revisando el modelo de transcripción (la primera vez baja cerca de 1.5 GB)"
"$ESTUDIO/.venv/bin/python" -c 'from faster_whisper import WhisperModel; WhisperModel("medium", device="cpu", compute_type="int8")' >/dev/null 2>&1 || alto "No se pudo bajar el modelo de transcripción. Revisa tu internet."
echo "✓ Transcripción lista"

mkdir -p "$RAIZ/videos"
chmod +x "$RAIZ/voz/di.sh" "$RAIZ/voz/al-iniciar.sh" "$RAIZ/Abrir Viernes.command" 2>/dev/null

# Acceso directo para abrirla con doble clic.
if [ -d "$HOME/Desktop" ]; then
  ACCESO="$HOME/Desktop/Abrir Viernes.command"
  if [ ! -e "$ACCESO" ]; then
    {
      echo '#!/bin/bash'
      printf 'exec %q\n' "$RAIZ/Abrir Viernes.command"
    } > "$ACCESO"
    chmod +x "$ACCESO"
    echo "✓ Acceso \"Abrir Viernes\" en tu Escritorio"
  fi
fi

if command -v claude >/dev/null 2>&1; then
  echo "✓ Claude Code listo"
  FALTA_CLAUDE=0
else
  FALTA_CLAUDE=1
fi

echo
echo "────────────────────────────────────────────"
echo "Hola, soy Viernes, la asistente de contenido de tu sobrino Santiago Botello."
echo "Él me mandó a resolverte tu vida."
echo "────────────────────────────────────────────"
bash "$RAIZ/voz/di.sh" saludo
echo
if [ "$FALTA_CLAUDE" -eq 1 ]; then
  echo "Falta un paso: instalar Claude Code. Guía: https://docs.claude.com/en/docs/claude-code/quickstart"
  echo "Después abre \"Abrir Viernes\" en tu Escritorio."
else
  echo "Para empezar, abre \"Abrir Viernes\" en tu Escritorio y dime: edítame este video."
fi
