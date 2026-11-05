# Viernes para Conquista Aromática

Arturo: esta carpeta trae a Viernes, la IA que hizo tu sobrino Santiago, ya entrenada con tu manual de edición.

Le das tu video y te regresa un corte con tu firma: los aplausos, el riser y el PUM de "¡siempre está en el plan!", tu rafaguiza y tu cierre con violines y megáfono. Tú revisas y decides. Viernes no publica nada.

## Qué necesitas

- Una **Mac con chip Apple (M1 o más nuevo)**. Es donde se probó. En una Mac modesta, transcribir y exportar puede tardar bastante; en una Intel no está probada.
- **[Claude Code](https://docs.claude.com/en/docs/claude-code/quickstart)** con tu propia cuenta de Claude. Editar consume tu plan.
- **Una cuenta de GitHub** con invitación a esta repo. Santiago te la manda.
- **[GitHub CLI](https://cli.github.com/)**, **[Python 3.12 o más nuevo](https://www.python.org/downloads/)** y **[Node.js LTS](https://nodejs.org/)**.
- **Git.** Si tu Mac no lo tiene, al usarlo te ofrece instalar las herramientas de Xcode: acepta y vuelve a correr el comando.
- Unos **3 GB libres** para instalar, más lo que pesen tus videos.

## Instalar

Abre la app **Terminal** y corre estos comandos, uno por uno.

Primero inicia sesión en GitHub. Elige GitHub.com, HTTPS, autenticar Git y entrar con el navegador. No necesitas pegar ninguna contraseña ni token:

```bash
gh auth login
```

Baja a Viernes. Santiago te pasa el nombre exacto de la repo:

```bash
gh repo clone <NOMBRE-DE-LA-REPO> ~/Viernes
```

Instálala:

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

## Qué sale de tu Mac

Tus videos no se suben a esta repo ni a GitHub. Pero para editarlos, Viernes le manda a Claude lo que lee: la transcripción, los textos y los cuadros que revisa. No le des nada que no quieras compartir con ese servicio.

## Para actualizarla

```bash
cd ~/Viernes && git pull --no-rebase --no-edit && bash instalar.sh
```

Si `git pull` falla, no borres nada: dile a Viernes *"se atoró la actualización"*. Suele pasar cuando se cambió algo del kit, como los colores. Por eso Viernes guarda esos cambios con un commit. Si no se arregla, mándale el error a Santiago.

## Para desinstalarla

1. Arrastra a la Papelera la carpeta `Viernes` de tu carpeta personal, con tus videos dentro si ya no los quieres. Saca antes los que quieras conservar.
2. Arrastra a la Papelera **Abrir Viernes** de tu Escritorio.
3. Para recuperar el espacio del modelo de transcripción, en Finder usa *Ir → Ir a la carpeta* con `~/.cache/huggingface/hub` y manda a la Papelera `models--Systran--faster-whisper-medium`.

## Si algo falla

Pregúntale a Viernes primero. Si no se arregla, mándale a Santiago el mensaje de error completo. Nunca pongas contraseñas ni llaves en el chat.

## Créditos

Hecha por Santiago Botello. La voz es sintética, generada con ElevenLabs. Las licencias de los sonidos están en `estudio/remotion/public/sfx/CREDITOS.md`. El editor usa [Remotion](https://www.remotion.dev/), que tiene su propia licencia: gratis para personas y empresas pequeñas, y las más grandes necesitan una de paga. Revisa sus condiciones si el canal crece a empresa.
