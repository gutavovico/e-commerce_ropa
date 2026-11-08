/**
 * Construcción del prompt para Decart Lucy VTON (CU10, Motor 2).
 *
 * La guía de prompting de Decart usa dos patrones en inglés: «Substitute the current <prenda>
 * with …» (sustituir lo que la persona lleva) y «Add … » (añadir una pieza encima). Un prompt
 * genérico del tipo «Virtually try on this garment» no indica qué prenda reemplazar, y el modelo
 * puede no aplicar la referencia. La prenda concreta la aporta la imagen de referencia; el prompt
 * solo dice dónde va.
 */

interface ReglaPrenda {
  /** Palabras clave en español, sin tildes y en minúsculas. */
  claves: readonly string[];
  prompt: string;
}

const SUFIJO = 'shown in the reference image';

/** El orden importa: la primera regla que coincide gana (p. ej. «vestido» antes que «top»). */
const REGLAS: readonly ReglaPrenda[] = [
  { claves: ['vestido'], prompt: `Substitute the current outfit with the dress ${SUFIJO}` },
  { claves: ['falda'], prompt: `Substitute the current bottom with the skirt ${SUFIJO}` },
  { claves: ['bermuda', 'short'], prompt: `Substitute the current pants with the shorts ${SUFIJO}` },
  {
    claves: ['pantalon', 'jean', 'palazzo'],
    prompt: `Substitute the current pants with the trousers ${SUFIJO}`,
  },
  {
    claves: ['abrigo', 'trench', 'gabardina', 'capa', 'chaqueta', 'blazer', 'saco', 'cardigan', 'chaleco'],
    prompt: `Add the jacket ${SUFIJO} over the person's current clothes`,
  },
  {
    claves: ['camiseta', 'polera', 'remera', 't-shirt'],
    prompt: `Substitute the current top with the t-shirt ${SUFIJO}`,
  },
  {
    claves: ['sueter', 'jersey', 'buzo', 'sudadera'],
    prompt: `Substitute the current top with the sweater ${SUFIJO}`,
  },
  {
    claves: ['blusa', 'camisa', 'top'],
    prompt: `Substitute the current top with the blouse ${SUFIJO}`,
  },
];

const PROMPT_POR_DEFECTO = `Substitute the current top with the garment ${SUFIJO}`;

function normalizar(texto: string | null | undefined): string {
  return (texto ?? '')
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase();
}

function buscarRegla(texto: string): ReglaPrenda | undefined {
  return REGLAS.find((regla) => regla.claves.some((clave) => new RegExp(`\\b${clave}`).test(texto)));
}

/**
 * Devuelve el prompt VTON para una prenda. Busca primero en el nombre (más específico: «Top
 * lencero» dentro de la categoría Camisas) y después en la categoría.
 */
export function construirPromptVton(nombre: string, categoria?: string | null): string {
  const regla = buscarRegla(normalizar(nombre)) ?? buscarRegla(normalizar(categoria));
  return regla?.prompt ?? PROMPT_POR_DEFECTO;
}
