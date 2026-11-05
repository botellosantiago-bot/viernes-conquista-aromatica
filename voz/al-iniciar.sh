#!/bin/bash
# Se corre al abrir Claude Code en esta carpeta. Saluda en voz alta y le dice a Viernes cómo presentarse.
# La primera vez usa el saludo completo; después, una frase corta. Nunca debe bloquear ni fallar.
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ESTADO="$RAIZ/.viernes-estado"
mkdir -p "$ESTADO" 2>/dev/null

if [ -f "$ESTADO/ya-saludo" ]; then
  (bash "$RAIZ/voz/di.sh" sesion >/dev/null 2>&1 &)
  echo "Viernes: Arturo ya te conoce. No repitas el saludo completo; al primer mensaje preséntate con una frase corta, si hace falta."
else
  touch "$ESTADO/ya-saludo" 2>/dev/null
  (bash "$RAIZ/voz/di.sh" saludo >/dev/null 2>&1 &)
  echo "Viernes: es la primera vez de Arturo contigo. Abre tu primer mensaje exactamente con: \"Hola, soy Viernes, la asistente de contenido de tu sobrino Santiago Botello. Él me mandó a resolverte tu vida.\" Luego pregúntale qué video editamos."
fi
exit 0
