import { loadFont as cargarFraunces } from "@remotion/google-fonts/Fraunces";
import { loadFont as cargarOutfit } from "@remotion/google-fonts/Outfit";

/*
 * IDENTIDAD VISUAL DE CONQUISTA AROMÁTICA. Todo color y toda fuente salen de AQUÍ y de ningún otro lado.
 *
 * Es una PROPUESTA de Viernes: Arturo no ha definido marca (logo, paleta ni tipografía). Elegante pero juvenil:
 * negro cálido, ámbar/dorado y un acento vivo (coral-rosa). Si Arturo trae su marca, se cambia aquí y todo el kit la sigue.
 */
export const COLOR = {
  negro: "#14100C", // negro cálido: fondos y plecas
  negroSuave: "#1F1812", // tarjetas
  crema: "#FFF4E0", // texto principal sobre oscuro
  ambar: "#F2A83B", // acento principal (palabra activa, líneas, brillos)
  dorado: "#E8C77A", // acento suave (detalles, subtítulos secundarios)
  acento: "#FF4D6D", // acento vivo: coral-rosa para golpes (SIEMPRE, rafaguiza, megáfono)
  destello: "#FFE9B0", // flashes
  rayo: "#9FD8FF", // rayos eléctricos de la Rafaguiza
  sombra: "rgba(10,6,3,0.78)",
} as const;

/** Fraunces (serif suave, con carácter) para títulos y acentos; Outfit (geométrica, muy legible en celular) para palabras clave y subtítulos. */
const fr = cargarFraunces("normal", { weights: ["700", "900"], subsets: ["latin"] });
const frI = cargarFraunces("italic", { weights: ["700"], subsets: ["latin"] });
const ou = cargarOutfit("normal", { weights: ["600", "800", "900"], subsets: ["latin"] });

export const FUENTE = {
  titulo: `${fr.fontFamily}, Georgia, serif`,
  sans: `${ou.fontFamily}, "Helvetica Neue", Arial, sans-serif`,
};
export const FUENTES_LISTAS = Promise.all([fr.waitUntilDone(), frI.waitUntilDone(), ou.waitUntilDone()]);
