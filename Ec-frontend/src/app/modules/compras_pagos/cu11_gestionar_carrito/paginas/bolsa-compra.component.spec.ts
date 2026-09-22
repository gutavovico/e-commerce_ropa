import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { Location } from '@angular/common';
import { computed, signal } from '@angular/core';
import { of, throwError } from 'rxjs';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { BolsaCompraComponent } from './bolsa-compra.component';
import { CarritoService } from '../servicios/carrito.service';
import { CarritoItem, CarritoResumen, TipoEntrega } from '../modelos/carrito.model';

function crearItem(sobrescribir: Partial<CarritoItem> = {}): CarritoItem {
  return {
    id_carrito_detalle: 44,
    id_variante: 3,
    id_producto: 1,
    nombre_producto: 'Vestido plisado en seda natural',
    linea_confeccion: null,
    sku: 'VES-PLI-40-ROJ',
    talla_codigo: '40',
    color_nombre: 'Rojo Carmín',
    color_hex: '#8C1C2B',
    imagen_url: 'https://cdn.fashionstore.test/vestido.jpg',
    precio_lista: '890.00',
    precio_unitario: '756.50',
    descuento_linea: '133.50',
    motivo_descuento: 'Membresia Prive',
    cantidad: 1,
    id_sucursal: 1,
    nombre_sucursal: 'Atelier Serrano - Madrid',
    stock_disponible: 15,
    cantidad_maxima: 15,
    subtotal_linea: '756.50',
    ...sobrescribir,
  };
}

const RESUMEN_CON_PRENDAS: CarritoResumen = {
  total_prendas: 1,
  total_lineas: 1,
  subtotal: '890.00',
  descuento: '133.50',
  total: '756.50',
  iva_incluido: '131.30',
  moneda: 'EUR',
};

const RESUMEN_VACIO: CarritoResumen = {
  total_prendas: 0,
  total_lineas: 0,
  subtotal: '0.00',
  descuento: '0.00',
  total: '0.00',
  iva_incluido: '0.00',
  moneda: 'EUR',
};

describe('BolsaCompraComponent (CU11 + CU15)', () => {
  let fixture: ComponentFixture<BolsaCompraComponent>;
  let componente: BolsaCompraComponent;

  const items = signal<CarritoItem[]>([]);
  const resumen = signal<CarritoResumen>(RESUMEN_VACIO);
  const cargando = signal<boolean>(false);
  const procesando = signal<boolean>(false);
  const error = signal<string | null>(null);
  const expiraEn = signal<string | null>(null);

  let mockCarrito: any;

  async function montar(): Promise<void> {
    await TestBed.configureTestingModule({
      imports: [BolsaCompraComponent],
      providers: [
        provideRouter([]),
        { provide: CarritoService, useValue: mockCarrito },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(BolsaCompraComponent);
    componente = fixture.componentInstance;
    fixture.detectChanges();
  }

  beforeEach(() => {
    items.set([]);
    resumen.set(RESUMEN_VACIO);
    cargando.set(false);
    procesando.set(false);
    error.set(null);
    expiraEn.set(null);

    mockCarrito = {
      items: computed(() => items()),
      resumen: computed(() => resumen()),
      cargando,
      procesando,
      error,
      estaVacia: computed(() => items().length === 0),
      hayDescuento: computed(() => resumen().descuento !== '0.00'),
      haySucursalesMultiples: computed(() => false),
      expiraEn: computed(() => expiraEn()),
      tipoEntrega: signal<TipoEntrega>('domicilio'),
      direccionEnvio: signal<string>(''),
      sucursalRetiro: signal<number | null>(null),
      cuponAplicado: signal<string | null>(null),
      cargarCarrito: vi.fn().mockReturnValue(of({})),
      obtenerBoutiques: vi.fn().mockReturnValue(of([])),
      actualizarCantidad: vi.fn().mockReturnValue(of({})),
      eliminarItem: vi.fn().mockReturnValue(of({})),
      tramitarPedido: vi.fn().mockReturnValue(of({ numero_comprobante: 'FS-2026-000001' })),
    };
  });

  // -------------------------------------------------------------------
  // Jerarquía Hub-and-Spoke
  // -------------------------------------------------------------------

  it('no renderiza la barra de navegación institucional (pantalla secundaria)', async () => {
    await montar();
    const compiled = fixture.nativeElement as HTMLElement;

    // El layout principal expone 4 enlaces de navegación en un <nav> dentro del header.
    expect(compiled.querySelector('header nav')).toBeNull();
    expect(compiled.querySelector('router-outlet')).toBeNull();
  });

  it('ofrece el retorno contextual mediante Location.back()', async () => {
    await montar();
    const location = TestBed.inject(Location);
    const espia = vi.spyOn(location, 'back');

    componente['volver']();

    // `back()` preserva filtros y scroll del origen real, a diferencia de navegar a una ruta fija.
    expect(espia).toHaveBeenCalled();
  });

  // -------------------------------------------------------------------
  // Estados de la pantalla
  // -------------------------------------------------------------------

  it('muestra el estado vacío con enlace al catálogo', async () => {
    await montar();
    const compiled = fixture.nativeElement as HTMLElement;

    expect(compiled.textContent).toContain('Tu bolsa está vacía');
    const enlace = Array.from(compiled.querySelectorAll('a[href]')).find(
      (a) => a.getAttribute('href') === '/catalogo'
    );
    expect(enlace).toBeTruthy();
  });

  it('muestra el esqueleto de carga mientras llega la bolsa', async () => {
    cargando.set(true);
    await montar();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelectorAll('.animate-pulse').length).toBeGreaterThan(0);
    expect(compiled.textContent).not.toContain('Tu bolsa está vacía');
  });

  it('muestra los mensajes de negocio del backend ante un error', async () => {
    items.set([crearItem()]);
    resumen.set(RESUMEN_CON_PRENDAS);
    error.set('No hay existencias suficientes. Disponibles: 2, solicitadas: 3.');
    await montar();

    const compiled = fixture.nativeElement as HTMLElement;
    const alerta = compiled.querySelector('[role="alert"]');
    expect(alerta?.textContent).toContain('Disponibles: 2');
  });

  // -------------------------------------------------------------------
  // Reactividad del resumen
  // -------------------------------------------------------------------

  it('renderiza el desglose financiero con el IVA incluido', async () => {
    items.set([crearItem()]);
    resumen.set(RESUMEN_CON_PRENDAS);
    await montar();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('890.00');   // subtotal a precio de lista
    expect(compiled.textContent).toContain('133.50');   // descuento
    expect(compiled.textContent).toContain('756.50');   // total
    expect(compiled.textContent).toContain('131.30');   // IVA contenido
  });

  it('recalcula el total al instante cuando cambia la bolsa', async () => {
    items.set([crearItem()]);
    resumen.set(RESUMEN_CON_PRENDAS);
    await montar();

    expect((fixture.nativeElement as HTMLElement).textContent).toContain('756.50');

    // Simula la respuesta del backend tras subir la cantidad a 2.
    items.set([crearItem({ cantidad: 2, subtotal_linea: '1513.00' })]);
    resumen.set({
      ...RESUMEN_CON_PRENDAS,
      total_prendas: 2,
      subtotal: '1780.00',
      descuento: '267.00',
      total: '1513.00',
    });
    fixture.detectChanges();

    const texto = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(texto).toContain('1513.00');
    expect(texto).toContain('2 prendas');
  });

  // -------------------------------------------------------------------
  // Controles de cantidad
  // -------------------------------------------------------------------

  it('deshabilita «−» cuando sólo queda una unidad', async () => {
    items.set([crearItem({ cantidad: 1 })]);
    resumen.set(RESUMEN_CON_PRENDAS);
    await montar();

    const botones = fixture.nativeElement.querySelectorAll('button[aria-label^="Reducir"]');
    expect((botones[0] as HTMLButtonElement).disabled).toBe(true);
  });

  it('deshabilita «+» al alcanzar el tope de existencias de la boutique', async () => {
    items.set([crearItem({ cantidad: 2, cantidad_maxima: 2, stock_disponible: 2 })]);
    resumen.set(RESUMEN_CON_PRENDAS);
    await montar();

    const boton = fixture.nativeElement.querySelector(
      'button[aria-label^="Aumentar"]'
    ) as HTMLButtonElement;

    expect(boton.disabled).toBe(true);
    expect((fixture.nativeElement as HTMLElement).textContent).toContain(
      'Máximo disponible en esta boutique'
    );
  });

  it('envía la cantidad absoluta al incrementar', async () => {
    items.set([crearItem({ cantidad: 1, cantidad_maxima: 5 })]);
    resumen.set(RESUMEN_CON_PRENDAS);
    await montar();

    componente['incrementar'](items()[0]);

    expect(mockCarrito.actualizarCantidad).toHaveBeenCalledWith(44, 2);
  });

  it('no llama al backend si «+» ya está en el tope', async () => {
    items.set([crearItem({ cantidad: 3, cantidad_maxima: 3 })]);
    resumen.set(RESUMEN_CON_PRENDAS);
    await montar();

    componente['incrementar'](items()[0]);

    expect(mockCarrito.actualizarCantidad).not.toHaveBeenCalled();
  });

  it('elimina la línea solicitada', async () => {
    items.set([crearItem()]);
    resumen.set(RESUMEN_CON_PRENDAS);
    await montar();

    componente['eliminar'](items()[0]);

    expect(mockCarrito.eliminarItem).toHaveBeenCalledWith(44);
  });

  // -------------------------------------------------------------------
  // Entrega, cupón y tramitación
  // -------------------------------------------------------------------

  it('exige dirección para habilitar la tramitación a domicilio', async () => {
    items.set([crearItem()]);
    resumen.set(RESUMEN_CON_PRENDAS);
    await montar();

    expect(componente['puedeTramitar']()).toBe(false);

    mockCarrito.direccionEnvio.set('Calle de Claudio Coello 48, 28001 Madrid');
    expect(componente['puedeTramitar']()).toBe(true);
  });

  it('exige boutique para habilitar la recogida en tienda', async () => {
    items.set([crearItem()]);
    resumen.set(RESUMEN_CON_PRENDAS);
    await montar();

    componente['seleccionarEntrega']('recogida_boutique');
    expect(componente['puedeTramitar']()).toBe(false);

    componente['seleccionarBoutique'](1);
    expect(componente['puedeTramitar']()).toBe(true);
  });

  it('revela el campo de dirección sólo en entrega a domicilio', async () => {
    items.set([crearItem()]);
    resumen.set(RESUMEN_CON_PRENDAS);
    await montar();

    expect(fixture.nativeElement.querySelector('#direccionEnvio')).toBeTruthy();

    componente['seleccionarEntrega']('recogida_boutique');
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('#direccionEnvio')).toBeNull();
  });

  it('registra el cupón introducido y permite retirarlo', async () => {
    items.set([crearItem()]);
    resumen.set(RESUMEN_CON_PRENDAS);
    await montar();

    componente['codigoCupon'].set('  MAISON-2025  ');
    componente['aplicarCupon']();
    expect(mockCarrito.cuponAplicado()).toBe('MAISON-2025');

    componente['retirarCupon']();
    expect(mockCarrito.cuponAplicado()).toBeNull();
  });

  it('muestra la confirmación de la orden tras tramitar', async () => {
    items.set([crearItem()]);
    resumen.set(RESUMEN_CON_PRENDAS);
    mockCarrito.tramitarPedido.mockReturnValue(
      of({
        id_venta: 1,
        numero_comprobante: 'FS-2026-000001',
        total: '756.50',
        total_prendas: 1,
        tipo_entrega: 'domicilio',
        nombre_sucursal_retiro: null,
        mensaje_confirmacion: 'Tu orden ha sido registrada.',
      })
    );
    await montar();

    mockCarrito.direccionEnvio.set('Serrano 48');
    componente['tramitarPedido']();
    fixture.detectChanges();

    const texto = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(texto).toContain('FS-2026-000001');
    expect(texto).toContain('Tu orden ha sido registrada.');
  });

  it('retira el cupón si el backend lo rechaza, para permitir reintentar', async () => {
    items.set([crearItem()]);
    resumen.set(RESUMEN_CON_PRENDAS);
    mockCarrito.tramitarPedido.mockImplementation(() => {
      error.set("El código 'NO-EXISTE' no corresponde a ninguna invitación.");
      return throwError(() => ({ status: 400 }));
    });
    await montar();

    mockCarrito.direccionEnvio.set('Serrano 48');
    mockCarrito.cuponAplicado.set('NO-EXISTE');
    componente['tramitarPedido']();

    expect(mockCarrito.cuponAplicado()).toBeNull();
  });

  // -------------------------------------------------------------------
  // Temporizador
  // -------------------------------------------------------------------

  it('limpia el temporizador al destruir el componente', async () => {
    expiraEn.set(new Date(Date.now() + 10 * 60 * 1000).toISOString());
    items.set([crearItem()]);
    resumen.set(RESUMEN_CON_PRENDAS);
    await montar();

    const limpiar = vi.spyOn(globalThis, 'clearInterval');
    fixture.destroy();

    // Sin esta limpieza el intervalo sigue vivo tras navegar y dispara detección de cambios
    // sobre un componente ya destruido.
    expect(limpiar).toHaveBeenCalled();
  });

  it('formatea la cuenta atrás en minutos y segundos', async () => {
    expiraEn.set(new Date(Date.now() + 605 * 1000).toISOString());
    items.set([crearItem()]);
    resumen.set(RESUMEN_CON_PRENDAS);
    await montar();

    const tiempo = componente['tiempoRestante']();
    expect(tiempo).toMatch(/^\d+:\d{2}$/);
  });
});
