import React from "react";

/** Iconos propios (trazos simples, dibujados aquí): nada de logos ni marcas ajenas. */
type P = { size: number; color: string };

export const IconoLike: React.FC<P> = ({ size, color }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={1.9} strokeLinecap="round" strokeLinejoin="round">
    <path d="M7 11v9H4a1 1 0 0 1-1-1v-7a1 1 0 0 1 1-1h3z" />
    <path d="M7 11l4-8c1.6 0 2.7 1.3 2.4 2.9L13 9h5.4a2 2 0 0 1 2 2.4l-1.3 6.6a2 2 0 0 1-2 1.6H7" />
  </svg>
);

export const IconoCampana: React.FC<P> = ({ size, color }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={1.9} strokeLinecap="round" strokeLinejoin="round">
    <path d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15z" />
    <path d="M10 20a2 2 0 0 0 4 0" />
    <path d="M12 3V2" />
  </svg>
);

export const IconoSuscribir: React.FC<P> = ({ size, color }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={1.9} strokeLinecap="round" strokeLinejoin="round">
    <rect x="2.5" y="5" width="19" height="14" rx="4" />
    <path d="M10 9.2v5.6l5-2.8z" fill={color} />
  </svg>
);

export const IconoMegafono: React.FC<P> = ({ size, color }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={1.9} strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 10v4a1 1 0 0 0 1 1h3l8 4V5L7 9H4a1 1 0 0 0-1 1z" />
    <path d="M18 9.5a4 4 0 0 1 0 5" />
    <path d="M20.5 7a8 8 0 0 1 0 10" />
  </svg>
);

export const Chispa: React.FC<{ size: number; color: string }> = ({ size, color }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill={color}>
    <path d="M12 0c.8 6.2 3 9.2 12 12-9 2.8-11.2 5.8-12 12-.8-6.2-3-9.2-12-12 9-2.8 11.2-5.8 12-12z" />
  </svg>
);
