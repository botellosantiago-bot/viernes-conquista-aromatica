#!/bin/bash
# Deja a Viernes lista en esta computadora (Windows, desde Git Bash, o Mac). Se puede correr las veces que haga falta: solo hace lo que falte.
# Uso: bash instalar.sh
# Todo lo suyo queda en esta carpeta. Fuera de ella solo crea el acceso "Abrir Viernes" en el Escritorio y usa las cachés
# normales de cada herramienta: el modelo de Whisper en la de Hugging Face, y lo que guarden npm y pip.
set -uo pipefail
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ESTUDIO="$RAIZ/estudio"
REGISTRO="$RAIZ/.viernes-estado/instalar.log"
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) WINDOWS=1; VENV_PY="$ESTUDIO/.venv/Scripts/python.exe" ;;
  *) WINDOWS=0; VENV_PY="$ESTUDIO/.venv/bin/python" ;;
esac
mkdir -p "$RAIZ/.viernes-estado"
: > "$REGISTRO"

# Corre un paso guardando su salida; si falla, enseña el final del error real para no adivinar la causa.
paso() {
  local mensaje="$1"; shift
  echo "--- $mensaje" >> "$REGISTRO"
  if ! "$@" >> "$REGISTRO" 2>&1; then
    tail -8 "$REGISTRO"
    alto "$mensaje (el detalle completo está en .viernes-estado/instalar.log)"
  fi
}

alto() {
  echo
  echo "✋ $1"
  echo "   Cuando esté, vuelve a correr: bash instalar.sh"
  echo "   Si te atoras, mándale este mensaje a Santiago."
  exit 1
}

# Solo para esta repo: que las actualizaciones y los commits locales de Viernes funcionen aunque Git no esté configurado.
if [ -d "$RAIZ/.git" ]; then
  git -C "$RAIZ" config pull.rebase false
  git -C "$RAIZ" config user.name >/dev/null 2>&1 || git -C "$RAIZ" config user.name "Viernes de Arturo"
  git -C "$RAIZ" config user.email >/dev/null 2>&1 || git -C "$RAIZ" config user.email "viernes@localhost"
fi

echo "Instalando a Viernes. La primera vez tarda unos minutos y necesita internet."
echo

# En Windows "python3" puede ser el acceso falso de la Microsoft Store: solo cuenta el que de verdad corre y es 3.12+.
PY_BASE=()
for candidato in "py -3.12" "py -3" "python3" "python"; do
  # shellcheck disable=SC2086
  if $candidato -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)' >/dev/null 2>&1; then
    read -r -a PY_BASE <<< "$candidato"
    break
  fi
done
[ "${#PY_BASE[@]}" -gt 0 ] || alto "Falta Python 3.12 o más nuevo. Instálalo desde https://www.python.org/downloads/"
command -v node >/dev/null 2>&1 || alto "Falta Node.js. Instala la versión LTS desde https://nodejs.org/"
NODE_MAYOR="$(node -p 'process.versions.node.split(".")[0]' | tr -d '\r')"
[ "$NODE_MAYOR" -ge 18 ] || alto "Node.js es muy viejo: hace falta 18 o más nuevo. Instala la LTS desde https://nodejs.org/"
command -v npm >/dev/null 2>&1 || alto "Falta npm. Viene con Node.js: reinstálalo desde https://nodejs.org/"

if [ ! -x "$VENV_PY" ]; then
  echo "→ Preparando Python"
  "${PY_BASE[@]}" -m venv "$ESTUDIO/.venv" || alto "No se pudo crear el entorno de Python."
fi
# En Windows el Python del entorno vive en Scripts\python.exe. Este atajo deja el mismo comando en todas partes:
# estudio/.venv/bin/python, en UTF-8 para que los acentos no truenen con la codificación de Windows.
if [ "$WINDOWS" -eq 1 ]; then
  mkdir -p "$ESTUDIO/.venv/bin"
  {
    echo '#!/bin/bash'
    echo 'export PYTHONUTF8=1 PYTHONIOENCODING=utf-8'
    echo 'exec "$(dirname "${BASH_SOURCE[0]}")/../Scripts/python.exe" "$@"'
  } > "$ESTUDIO/.venv/bin/python"
  chmod +x "$ESTUDIO/.venv/bin/python"
  export PYTHONUTF8=1 PYTHONIOENCODING=utf-8
fi
if ! "$VENV_PY" -c 'import faster_whisper, cv2, imageio_ffmpeg' >/dev/null 2>&1; then
  echo "→ Instalando herramientas de transcripción y video"
  paso "No se pudo actualizar pip." "$VENV_PY" -m pip install --upgrade pip
  paso "No se pudieron instalar las herramientas de Python." "$VENV_PY" -m pip install -r "$ESTUDIO/requirements.txt"
fi
if ! "$VENV_PY" -c 'import faster_whisper, cv2, av' >/dev/null 2>&1; then
  if [ "$WINDOWS" -eq 1 ]; then
    alto "Las herramientas de video no arrancan. Instala Microsoft Visual C++ Redistributable: winget install Microsoft.VCRedist.2015+.x64"
  fi
  alto "Las herramientas de video no arrancan."
fi
echo "✓ Python listo"

FFMPEG="$("$VENV_PY" -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())' | tr -d '\r')"
[ -n "$FFMPEG" ] || alto "No se encontró ffmpeg."
mkdir -p "$ESTUDIO/bin"
if [ "$WINDOWS" -eq 1 ]; then
  cp -f "$(cygpath -u "$FFMPEG")" "$ESTUDIO/bin/ffmpeg.exe" || alto "No se pudo copiar ffmpeg."
else
  ln -sfn "$FFMPEG" "$ESTUDIO/bin/ffmpeg"
fi
"$ESTUDIO/bin/ffmpeg" -version >/dev/null 2>&1 || alto "ffmpeg no arranca."
echo "✓ ffmpeg listo"

# La marca solo se escribe si todo terminó: una instalación a medias no cuenta como lista.
MARCA_NPM="$ESTUDIO/remotion/node_modules/.instalacion-completa"
if [ ! -f "$MARCA_NPM" ] || [ "$ESTUDIO/remotion/package-lock.json" -nt "$MARCA_NPM" ]; then
  echo "→ Instalando el editor de video"
  (cd "$ESTUDIO/remotion" && paso "No se pudo instalar el editor de video." npm ci --no-audit --no-fund --fetch-retries=5 --fetch-timeout=120000) || exit 1
  touch "$MARCA_NPM"
fi
echo "→ Revisando el navegador del editor (la primera vez baja unos 170 MB)"
(cd "$ESTUDIO/remotion" && paso "No se pudo bajar el navegador del editor." npx --no-install remotion browser ensure) || exit 1
echo "✓ Editor de video listo"

echo "→ Revisando el modelo de transcripción (la primera vez baja cerca de 1.5 GB)"
paso "No se pudo bajar el modelo de transcripción." "$VENV_PY" -c 'from faster_whisper import WhisperModel; WhisperModel("medium", device="cpu", compute_type="int8")'
echo "✓ Transcripción lista"

mkdir -p "$RAIZ/videos"
chmod +x "$RAIZ/voz/di.sh" "$RAIZ/voz/al-iniciar.sh" "$RAIZ/Abrir Viernes.command" 2>/dev/null

# Acceso directo para abrirla con doble clic.
if [ "$WINDOWS" -eq 1 ]; then
  # El Escritorio puede estar dentro de OneDrive: se le pregunta a Windows dónde está.
  ESCRITORIO="$(powershell.exe -NoProfile -NonInteractive -Command "[Environment]::GetFolderPath('Desktop')" 2>/dev/null | tr -d '\r')"
  if [ -n "$ESCRITORIO" ] && [ -d "$(cygpath -u "$ESCRITORIO")" ]; then
    ACCESO="$(cygpath -u "$ESCRITORIO")/Abrir Viernes.cmd"
    if [ ! -e "$ACCESO" ]; then
      printf '@echo off\r\ncall "%s\\Abrir Viernes.cmd"\r\n' "$(cygpath -w "$RAIZ")" > "$ACCESO"
      echo "✓ Acceso \"Abrir Viernes\" en tu Escritorio"
    fi
  fi
elif [ -d "$HOME/Desktop" ]; then
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

# El saludo se dice una sola vez en la vida: actualizar no vuelve a saludar.
echo
if [ ! -f "$RAIZ/.viernes-estado/ya-saludo" ]; then
  touch "$RAIZ/.viernes-estado/ya-saludo"
  echo "────────────────────────────────────────────"
  echo "Hola, soy Viernes, la asistente de contenido de tu sobrino Santiago Botello."
  echo "Él me mandó a resolverte tu vida."
  echo "────────────────────────────────────────────"
  bash "$RAIZ/voz/di.sh" saludo
else
  echo "✓ Viernes está al día."
fi
echo
if [ "$FALTA_CLAUDE" -eq 1 ]; then
  if [ "$WINDOWS" -eq 1 ]; then
    echo "Falta un paso: instalar Claude Code. Abre PowerShell y sigue la guía: https://code.claude.com/docs/en/setup"
  else
    echo "Falta un paso: instalar Claude Code. Guía: https://docs.claude.com/en/docs/claude-code/quickstart"
  fi
  echo "Después abre \"Abrir Viernes\" en tu Escritorio."
else
  echo "Para empezar, abre \"Abrir Viernes\" en tu Escritorio y dime: edítame este video."
fi
