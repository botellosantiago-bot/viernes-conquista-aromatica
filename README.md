# Viernes para Conquista Aromática

Arturo: esta carpeta trae a Viernes, la IA que hizo tu sobrino Santiago, ya entrenada con tu manual de edición.

Le das tu video y te regresa un corte con tu firma: los aplausos, el riser y el PUM de "¡siempre está en el plan!", tu rafaguiza y tu cierre con violines y megáfono. Tú revisas y decides. Viernes no publica nada.

## Qué necesitas

- Una computadora con **Windows 10 u 11 de 64 bits**. Transcribir y exportar usa el procesador: en una computadora modesta puede tardar bastante.
- **[Claude Code](https://code.claude.com/docs/en/setup)** con tu propia cuenta de Claude. Editar consume tu plan.
- **Una cuenta de GitHub** con invitación a esta repo. Santiago te la manda: acéptala en tu correo o en github.com.
- Unos **3 GB libres** para instalar, más lo que pesen tus videos.

## Instalar

**1. Instala las herramientas.** Abre **PowerShell** desde el menú Inicio y corre estos comandos, uno por uno. Si Windows te pregunta si permites el cambio, di que sí:

```powershell
winget install --id Git.Git -e
winget install --id GitHub.cli -e
winget install --id Python.Python.3.12 -e
winget install --id OpenJS.NodeJS.LTS -e
winget install --id Microsoft.VCRedist.2015+.x64 -e
```

Para Claude Code, sigue el comando de PowerShell de [su guía oficial](https://code.claude.com/docs/en/setup).

**2. Cierra PowerShell** y abre **Git Bash**, también desde el menú Inicio. Todo lo que sigue va ahí.

**3. Inicia sesión en GitHub.** Elige GitHub.com, HTTPS, autenticar Git y entrar con el navegador. No necesitas pegar ninguna contraseña ni token:

```bash
gh auth login
```

**4. Baja a Viernes:**

```bash
gh repo clone botellosantiago-bot/viernes-conquista-aromatica ~/Viernes
```

**5. Instálala:**

```bash
bash ~/Viernes/instalar.sh
```

Al terminar, Viernes te saluda en voz alta y te deja en el Escritorio un acceso llamado **Abrir Viernes**.

La primera vez que lo abras, Windows o Claude Code pueden pedirte confirmar que confías en él.

También funciona en Mac: mismos pasos, con las herramientas de sus páginas oficiales y la app Terminal en lugar de Git Bash.

## Usarla

1. Abre **Abrir Viernes**.
2. Pon tu video en la carpeta `videos` y dile, con tus palabras: *"Edítame este video para YouTube"* o *"Sácame un Short de esta reseña"*.
3. Revisa el primer corte y pídele cambios como se los pedirías a un editor.

## Tu música

Viernes no trae música. Dale pistas que tengas derecho a usar: lounge, lo-fi y cuerdas para tu cierre.

## Qué sale de tu computadora

Tus videos no se suben a esta repo ni a GitHub. Pero para editarlos, Viernes le manda a Claude lo que lee: la transcripción, los textos y los cuadros que revisa. No le des nada que no quieras compartir con ese servicio.

## Para actualizarla

En Git Bash:

```bash
cd ~/Viernes && git pull --no-rebase --no-edit && bash instalar.sh
```

Si `git pull` falla, no borres nada: dile a Viernes *"se atoró la actualización"*. Suele pasar cuando se cambió algo del kit, como los colores. Por eso Viernes guarda esos cambios con un commit. Si no se arregla, mándale el error a Santiago.

## Para desinstalarla

1. Saca los videos que quieras conservar y manda a la Papelera la carpeta `Viernes` de tu carpeta personal (`C:\Users\tu-usuario\Viernes`).
2. Borra **Abrir Viernes** de tu Escritorio.
3. Para recuperar el espacio del modelo de transcripción, en el Explorador de archivos ve a `%USERPROFILE%\.cache\huggingface\hub` y borra `models--Systran--faster-whisper-medium`.

## Si algo falla

Pregúntale a Viernes primero. Si no se arregla, mándale a Santiago el mensaje de error completo. Nunca pongas contraseñas ni llaves en el chat.

## Créditos

Hecha por Santiago Botello. La voz es sintética, generada con ElevenLabs. Las licencias de los sonidos están en `estudio/remotion/public/sfx/CREDITOS.md`. El editor usa [Remotion](https://www.remotion.dev/), que tiene su propia licencia: gratis para personas y empresas pequeñas, y las más grandes necesitan una de paga. Revisa sus condiciones si el canal crece a empresa.
