import React from "react";
import { Audio, Sequence, interpolate, staticFile, useVideoConfig } from "remotion";
import { clamp } from "./core";
import type { PlanResuelto, SfxEvento, Stem } from "./tipos";

/*
 * MEZCLA. La voz siempre manda: la música baja mientras Arturo habla y vuelve a subir en los silencios.
 * Los efectos (whoosh, aplausos, riser, PUM, pop...) los coloca plan.py con sus tiempos y volúmenes; aquí solo se reproducen.
 * Sin música (no hay pista con licencia) este archivo no falla: simplemente no pone nada.
 */
const ATAQUE = 0.12; // s que tarda la música en bajar antes de que entre la voz
const LIBERA = 0.55; // s que tarda en volver a subir
const PISO = 0.26; // cuánto queda de la música bajo la voz (-11.7 dB)

/** Ganancia de ducking (0..1) en el segundo t, a partir de los intervalos de voz y de los silencios cómicos. */
export const gananciaMusica = (t: number, voz: [number, number][], silencios: [number, number][], piso = PISO) => {
  let g = 1;
  for (const [a, b] of voz) {
    if (t < a - ATAQUE || t > b + LIBERA) continue;
    const gi = t < a ? 1 - (1 - piso) * ((t - (a - ATAQUE)) / ATAQUE) : t <= b ? piso : piso + (1 - piso) * ((t - b) / LIBERA);
    g = Math.min(g, gi);
  }
  for (const [a, b] of silencios) {
    // El silencio también es un efecto: la música se corta un instante para que funcione el remate.
    if (t >= a - 0.08 && t <= b + 0.3) g = Math.min(g, t < a ? 1 - (t - (a - 0.08)) / 0.08 : t <= b ? 0 : (t - b) / 0.3);
  }
  return Math.max(0, Math.min(1, g));
};

/** El riser y los aplausos se agachan bajo la voz (como la música); el resto de los efectos ya van a un volumen que no la tapa. */
const BAJAN_BAJO_VOZ = new Set(["riser", "aplauso"]);

const Sfx: React.FC<{ e: SfxEvento; voz: [number, number][] }> = ({ e, voz }) => {
  const { fps } = useVideoConfig();
  const desde = Math.floor(e.t * fps + 1e-6);
  const n = e.dur ? Math.max(1, Math.round(e.dur * fps)) : undefined;
  return (
    <Sequence from={desde} durationInFrames={n} layout="none" name={`sfx ${e.tag ?? ""}`}>
      <Audio
        src={staticFile(e.archivo)}
        volume={(f: number) => {
          const agacha = BAJAN_BAJO_VOZ.has(e.tag ?? "") ? gananciaMusica(desde / fps + f / fps, voz, [], 0.22) : 1;
          if (!e.dur || e.exacto) return e.vol * agacha; // el riser va exacto: su propio fundido de 4 ms ya lo corta en seco
          const x = Math.min(1, f / (e.dur * fps));
          return e.vol * agacha * (1 - x) ** 1.5; // aplausos e impactos: se apagan rápido para no tapar la voz
        }}
      />
    </Sequence>
  );
};

export const Efectos: React.FC<{ plan: PlanResuelto; stem: Stem }> = ({ plan, stem }) => {
  if (stem !== "todo" && stem !== "fx") return null;
  return (
    <>
      {plan.sfx.map((e, i) => (
        <Sfx key={i} e={e} voz={plan.voz} />
      ))}
    </>
  );
};

export const Musica: React.FC<{ plan: PlanResuelto; stem: Stem; total: number }> = ({ plan, stem, total }) => {
  const { fps } = useVideoConfig();
  if (stem !== "todo" && stem !== "musica" && stem !== "cuerdas") return null;
  const { base: baseTodo, cierre } = plan.musica;
  const base = stem === "cuerdas" ? null : baseTodo; // stem "cuerdas": solo la pista del cierre (para medir cuándo entra)
  const vol = plan.musica.volumen;
  const ini = plan.firma.cierre?.inicio ?? null;
  const tTotal = total / fps;
  const finBase = cierre && ini !== null ? ini + 1.2 : tTotal;
  const duck = (t: number) => gananciaMusica(t, plan.voz, plan.silencios);
  return (
    <>
      {base ? (
        <Sequence from={0} durationInFrames={Math.max(1, Math.round(finBase * fps))} layout="none" name="música base">
          <Audio
            src={staticFile(base)}
            loop
            volume={(f: number) => {
              const t = f / fps;
              const entra = interpolate(t, [0, 1.5], [0, 1], clamp);
              const sale = ini !== null && cierre ? interpolate(t, [ini - 0.2, ini + 1.2], [1, 0], clamp) : interpolate(t, [tTotal - 2, tTotal], [1, 0], clamp);
              return vol * entra * sale * duck(t);
            }}
          />
        </Sequence>
      ) : null}
      {cierre && ini !== null ? (
        <Sequence from={Math.round(ini * fps)} layout="none" name="cuerdas del cierre">
          <Audio
            src={staticFile(cierre)}
            volume={(f: number) => {
              const t = ini + f / fps;
              const entra = interpolate(t, [ini, ini + 2.5], [0, 1], clamp); // sube suavemente al inicio
              const sale = interpolate(t, [tTotal - 2.2, tTotal], [1, 0], clamp); // cola suave
              return vol * 1.15 * entra * sale * Math.max(duck(t), 0.3);
            }}
          />
        </Sequence>
      ) : null}
    </>
  );
};
