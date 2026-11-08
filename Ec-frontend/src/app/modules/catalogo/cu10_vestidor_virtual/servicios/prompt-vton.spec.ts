import { describe, it, expect } from 'vitest';
import { construirPromptVton } from './prompt-vton';

describe('construirPromptVton (CU10 · Decart Lucy VTON)', () => {
  it.each([
    // Nombres reales del catálogo en Neon
    ['Vestido plisado en seda natural', 'Vestidos', 'Substitute the current outfit with the dress'],
    ['Falda midi plisada en lino', 'Faldas', 'Substitute the current bottom with the skirt'],
    ['Pantalón sastre de tiro alto', 'Pantalones', 'Substitute the current pants with the trousers'],
    ['Bermuda sastre en algodón egipcio peinado', 'Pantalones', 'Substitute the current pants with the shorts'],
    ['Trench coat fluido con cinturón atelier', 'Chaquetas', 'Add the jacket'],
    ['Abrigo envolvente en baby alpaca', 'Chaquetas', 'Add the jacket'],
    ['Suéter de cuello cisne en lana merino & cachemira', 'Coleccion Atelier', 'Substitute the current top with the sweater'],
    ['Blusa de satén fluido', 'Camisas', 'Substitute the current top with the blouse'],
    ['Top lencero en lino y seda Milano', 'Camisas', 'Substitute the current top with the blouse'],
    ['Camiseta ORIGINAL', 'Camisas', 'Substitute the current top with the t-shirt'],
  ])('«%s» (%s) usa el patrón correcto', (nombre, categoria, esperado) => {
    const prompt = construirPromptVton(nombre, categoria);
    expect(prompt.startsWith(esperado)).toBe(true);
    expect(prompt).toContain('reference image');
  });

  it('recurre a la categoría cuando el nombre no identifica la prenda', () => {
    expect(construirPromptVton('Pieza Atelier N.º 7', 'Faldas')).toContain('with the skirt');
  });

  it('usa un prompt genérico de parte superior si nada coincide', () => {
    expect(construirPromptVton('Pieza Atelier N.º 7', null)).toBe(
      'Substitute the current top with the garment shown in the reference image'
    );
  });

  it('exige inicio de palabra: «Estopa» no activa la regla de «top»', () => {
    expect(construirPromptVton('Estopa decorativa', null)).toBe(
      'Substitute the current top with the garment shown in the reference image'
    );
  });
});
