#!/bin/bash
# Se corre al abrir Claude Code en esta carpeta. Le dice a Viernes cómo presentarse y nunca debe bloquear ni fallar.
# Hay dos marcas: `ya-saludo` (ya se oyó el saludo, lo pone instalar.sh) y `ya-se-presento` (ya lo dijo en el chat).
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ESTADO="$RAIZ/.viernes-estado"
mkdir -p "$ESTADO" 2>/dev/null

if [ -f "$ESTADO/ya-se-presento" ]; then
  (bash "$RAIZ/voz/di.sh" sesion >/dev/null 2>&1 &)
  echo "Viernes: Arturo ya te conoce. No repitas el saludo completo; al primer mensaje preséntate con una frase corta, si hace falta."
else
  touch "$ESTADO/ya-se-presento" 2>/dev/null
  if [ ! -f "$ESTADO/ya-saludo" ]; then
    touch "$ESTADO/ya-saludo" 2>/dev/null
    (bash "$RAIZ/voz/di.sh" saludo >/dev/null 2>&1 &)
  fi
  echo "Viernes: es la primera conversación de Arturo contigo. Abre tu primer mensaje exactamente con: \"Hola, soy Viernes, la asistente de contenido de tu sobrino Santiago Botello. Él me mandó a resolverte tu vida.\" Luego pregúntale qué video editamos."
fi
exit 0
