# Viernes para Conquista Aromática

Arturo: esta carpeta trae a Viernes, la IA que hizo tu sobrino Santiago, ya entrenada con tu manual de edición.

Le das tu video y te regresa un corte con tu firma: los aplausos, el riser y el PUM de "¡siempre está en el plan!", tu rafaguiza y tu cierre con violines y megáfono. Tú revisas y decides. Viernes no publica nada.

## Qué necesitas

- Una **Mac**.
- **[Claude Code](https://docs.claude.com/en/docs/claude-code/quickstart)** con tu propia cuenta de Claude.
- **[Python 3.10 o más nuevo](https://www.python.org/downloads/)** y **[Node.js LTS](https://nodejs.org/)**.
- Unos 3 GB libres para instalar, más lo que pesen tus videos.

## Instalar

Abre la app **Terminal** y pega estos comandos, uno por uno. Santiago te pasa el enlace de la repo.

```bash
git clone <ENLACE-DE-LA-REPO> ~/Viernes
```

```bash
bash ~/Viernes/instalar.sh
```

Al terminar, Viernes te saluda en voz alta. Te deja en el Escritorio un acceso llamado **Abrir Viernes**.

La primera vez que lo abras, macOS o Claude Code pueden pedirte confirmar que confías en la carpeta. Si macOS lo bloquea, haz clic derecho sobre el acceso y elige **Abrir**.

## Usarla

1. Abre **Abrir Viernes**.
2. Pon tu video en la carpeta `videos` y dile, con tus palabras: *"Edítame este video para YouTube"* o *"Sácame un Short de esta reseña"*.
3. Revisa el primer corte y pídele cambios como se los pedirías a un editor.

## Tu música

Viernes no trae música. Dale pistas que tengas derecho a usar: lounge, lo-fi y cuerdas para tu cierre.

## Para actualizarla

```bash
cd ~/Viernes && git pull && bash instalar.sh
```

## Si algo falla

Pregúntale a Viernes primero. Si no se arregla, mándale a Santiago el mensaje de error completo. Nunca pongas contraseñas ni llaves en el chat.

## Créditos

Hecha por Santiago Botello. La voz es sintética, generada con ElevenLabs. Las licencias de los sonidos están en `estudio/remotion/public/sfx/CREDITOS.md`. El editor usa [Remotion](https://www.remotion.dev/), que tiene su propia licencia: gratis para personas y empresas pequeñas, y las más grandes necesitan una de paga. Revisa sus condiciones si el canal crece a empresa.
