#!/bin/bash
# Doble clic para hablar con Viernes.
cd "$(dirname "${BASH_SOURCE[0]}")" || exit 1
if ! command -v claude >/dev/null 2>&1; then
  echo "Falta instalar Claude Code. Guía: https://docs.claude.com/en/docs/claude-code/quickstart"
  read -r -p "Presiona Enter para cerrar." _
  exit 1
fi
exec claude
