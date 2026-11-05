// Render de un video de Conquista Aromática.
//
//   node scripts/render.mjs <composición> <slug> <salida.mp4|.wav> [--stem voz|fx|musica|cuerdas] [--borrador] [--bloque 1800]
//
//   composición  Conquista16x9 (YouTube largo y lives) o Conquista9x16 (Shorts, Reels, TikTok)
//   --stem       en vez del video, saca SOLO una parte del audio en WAV (voz / fx / musica / cuerdas). Sirve para medir en QA.
//   --stems-dir  carpeta: saca los cuatro stems de una vez (un solo bundle).
//   --borrador   media resolución y calidad menor: para revisar ritmo y chistes rápido.
//   --por-bloques  fuerza el render por trozos aunque el video sea corto (para probarlo)
//   --bloque N   cuadros por bloque en videos largos (por defecto 1800 = 60 s). Más de 3 minutos se renderiza SIEMPRE por trozos
//                (Chrome nuevo en cada bloque: la memoria no se acumula) y se une sin costuras de audio.
//
// Adaptado del render por bloques del estudio. Rutas relativas a esta carpeta: ../../bin/ffmpeg (el que instala instalar.sh).
import { bundle } from "@remotion/bundler";
import { combineChunks, renderMedia, selectComposition } from "@remotion/renderer";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const raiz = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const FF = fs.existsSync(path.resolve(raiz, "..", "bin", "ffmpeg")) ? path.resolve(raiz, "..", "bin", "ffmpeg") : "ffmpeg";

const args = process.argv.slice(2);
const pos = [];
const opt = { stem: null, stemsDir: null, borrador: false, bloque: 1800, porBloques: false };
for (let i = 0; i < args.length; i++) {
  if (args[i] === "--stem") opt.stem = args[++i];
  else if (args[i] === "--stems-dir") opt.stemsDir = args[++i];
  else if (args[i] === "--borrador") opt.borrador = true;
  else if (args[i] === "--por-bloques") opt.porBloques = true;
  else if (args[i] === "--bloque") opt.bloque = Number(args[++i]);
  else pos.push(args[i]);
}
const [id, slug, salidaArg] = pos;
if (!id || !slug || (!salidaArg && !opt.stemsDir)) {
  console.error("Uso: node scripts/render.mjs <Conquista16x9|Conquista9x16> <slug> <salida> [--stem voz|fx|musica] [--borrador]");
  process.exit(2);
}
const salida = salidaArg ? path.resolve(salidaArg) : null;
if (salida) fs.mkdirSync(path.dirname(salida), { recursive: true });
const trabajo = path.join(raiz, "out", `bloques_${slug}_${id}${opt.borrador ? "_borrador" : ""}`);
const T0 = Date.now();
const seg = () => `${((Date.now() - T0) / 1000).toFixed(0)} s`;
const chromiumOptions = { gl: "angle" };

const serveUrl = await bundle({ entryPoint: path.join(raiz, "src/index.ts") });
// bundle() copia public/ a una carpeta temporal y no la borra: se limpia al salir.
process.on("exit", () => fs.rmSync(serveUrl, { recursive: true, force: true }));
const inputProps = { slug, stem: opt.stem ?? "todo" };
const composition = await selectComposition({ serveUrl, id, inputProps, chromiumOptions });
const total = composition.durationInFrames;
console.log(`${id} ${composition.width}x${composition.height} ${composition.fps} fps, ${total} cuadros (${(total / composition.fps).toFixed(1)} s)`);

if (opt.stemsDir) {
  // Todos los stems con UN solo bundle: voz, fx, musica y cuerdas (WAV 48 kHz) para medir en QA.
  fs.mkdirSync(opt.stemsDir, { recursive: true });
  for (const stem of ["voz", "fx", "musica", "cuerdas"]) {
    const props = { slug, stem };
    const comp = await selectComposition({ serveUrl, id, inputProps: props, chromiumOptions });
    await renderMedia({ composition: comp, serveUrl, codec: "wav", inputProps: props, chromiumOptions, outputLocation: path.join(opt.stemsDir, `${stem}.wav`) });
    console.log(`audio (${stem}) listo (${seg()})`);
  }
  process.exit(0);
}

if (opt.stem) {
  await renderMedia({ composition, serveUrl, codec: "wav", inputProps, chromiumOptions, outputLocation: salida });
  console.log(`audio (${opt.stem}) listo: ${salida} (${seg()})`);
  process.exit(0);
}

let ultimoProgreso = -1;
const escala = opt.borrador ? 0.5 : 1;
const comunes = {
  composition,
  serveUrl,
  inputProps,
  chromiumOptions,
  crf: opt.borrador ? 24 : 16,
  x264Preset: opt.borrador ? "veryfast" : "medium",
  jpegQuality: opt.borrador ? 80 : 95,
  scale: escala,
  offthreadVideoCacheSizeInBytes: 1_000_000_000,
};

if (total <= 5400 && !opt.porBloques) {
  await renderMedia({ ...comunes, codec: "h264", audioCodec: "aac", audioBitrate: "320k", outputLocation: salida, onProgress: ({ progress }) => { const p = Math.floor(progress * 10); if (p > ultimoProgreso) { ultimoProgreso = p; process.stdout.write(`${p * 10}% `); } } });
  console.log(`\nlisto: ${salida} (${seg()})`);
  process.exit(0);
}

// Videos largos: por bloques con h264-ts + AAC sin costuras (combineChunks).
fs.mkdirSync(trabajo, { recursive: true });
const videos = [];
const audios = [];
for (let a = 0; a < total; a += opt.bloque) {
  const b = Math.min(total - 1, a + opt.bloque - 1);
  const v = path.join(trabajo, `v_${String(a).padStart(7, "0")}.ts`);
  const au = path.join(trabajo, `a_${String(a).padStart(7, "0")}.aac`);
  videos.push(v);
  audios.push(au);
  if (fs.existsSync(v) && fs.statSync(v).size > 0 && fs.existsSync(au)) {
    console.log(`bloque ${a}-${b} ya existe`);
    continue;
  }
  const t = Date.now();
  for (const concurrency of [4, 2, 1]) {
    try {
      await renderMedia({ ...comunes, codec: "h264-ts", frameRange: [a, b], concurrency, outputLocation: v + ".tmp.ts", separateAudioTo: au + ".tmp.aac", audioCodec: "aac", forSeamlessAacConcatenation: true, audioBitrate: "320k" });
      break;
    } catch (err) {
      console.log(`bloque ${a}-${b} falló con concurrencia ${concurrency}: ${String(err.message ?? err).slice(0, 140)}`);
      if (concurrency === 1) throw err;
    }
  }
  fs.renameSync(v + ".tmp.ts", v);
  fs.renameSync(au + ".tmp.aac", au);
  console.log(`bloque ${a}-${b} listo (${((Date.now() - t) / 1000).toFixed(0)} s)`);
}
const unido = path.join(trabajo, "unido.mp4");
await combineChunks({
  outputLocation: unido,
  videoFiles: videos,
  audioFiles: audios,
  codec: "h264",
  fps: composition.fps,
  framesPerChunk: opt.bloque,
  compositionDurationInFrames: total,
  preferLossless: false,
  audioBitrate: "320k",
  audioCodec: "aac",
});
// El AAC trae un poco de relleno al final: se recorta al largo del video (copia, sin re-codificar).
execFileSync(FF, ["-hide_banner", "-loglevel", "error", "-y", "-i", unido, "-map", "0", "-c", "copy", "-shortest", "-movflags", "+faststart", salida]);
fs.rmSync(trabajo, { recursive: true, force: true });
console.log(`listo: ${salida} (${seg()})`);
