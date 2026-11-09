import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { signal } from '@angular/core';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { of } from 'rxjs';
import { PuntoVentaComponent } from './punto-venta.component';
import { LoginService } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import { UsuarioSesion } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/modelos/login.dto';

/**
 * Payloads literales con la forma exacta que serializa el backend (`esquemas.py`): los importes
 * `Decimal` llegan como cadena y la página los muestra tal cual, sin recalcularlos.
 */
const VARIANTE = {
  id_variante: 501,
  sku: 'FS-CAM-AMA-M',
  id_producto: 77,
  nombre_producto: 'Camiseta básica amarilla',
  categoria_nombre: 'Camisas',
  talla_codigo: 'M',
  color_nombre: 'Amarillo',
  imagen_url: '/static/productos/camiseta-amarilla.png',
  precio_lista: '25.00',
  precio_final: '25.00',
  disponible_en_sucursal: 3,
};

const LINEA = {
  id_variante: 501,
  sku: 'FS-CAM-AMA-M',
  nombre_producto: 'Camiseta básica amarilla',
  talla_codigo: 'M',
  color_nombre: 'Amarillo',
  imagen_url: '/static/productos/camiseta-amarilla.png',
  cantidad: 1,
  precio_lista: '25.00',
  precio_unitario: '25.00',
  subtotal_linea: '25.00',
  motivo_descuento: null,
  origen: 'caja',
};

const PREVISUALIZACION = {
  subtotal: '25.00',
  descuento: '0.00',
  total: '25.00',
  iva_incluido: '2.88',
  cupon_aplicado: null,
  lineas: [LINEA],
  lineas_reserva_excluidas: [],
};

const VENTA_PENDIENTE = {
  subtotal: '25.00',
  descuento: '0.00',
  total: '25.00',
  iva_incluido: '2.88',
  cupon_aplicado: null,
  id_venta: 900,
  numero_comprobante: 'POS-2026-000900',
  estado: 'pendiente',
  fecha_venta: '2026-11-08T15:30:00Z',
  id_sucursal: 2,
  nombre_sucursal: 'Boutique Calacoto',
  direccion_sucursal: 'Av. Ballivián 1234',
  cajero_nombre: 'Carlos Perez',
  cliente: null,
  reserva_codigo: null,
  lineas: [LINEA],
  lineas_reserva_excluidas: [],
  pagos: [],
};

const PAGO_EFECTIVO = {
  id_pago: 1200,
  metodo_pago: 'efectivo',
  monto: '25.00',
  estado: 'confirmado',
  referencia: null,
  monto_recibido: '50.00',
  cambio: '25.00',
  creado_en: '2026-11-08T15:31:00Z',
  confirmado_en: '2026-11-08T15:31:00Z',
};

const CLIENTE_ANA = { id_cliente: 3, nombres: 'Ana', apellidos: 'Valenzuela', email: 'ana@correo.com' };

const RESERVA_ANA = {
  id_reserva: 7,
  codigo: 'RES-2026-0007',
  estado: 'confirmada',
  fecha_hora_atencion: '2026-11-08T16:00:00Z',
  cliente: CLIENTE_ANA,
  lineas: [
    { id_variante: 501, sku: 'FS-CAM-AMA-M', nombre_producto: 'Camiseta básica amarilla', talla_codigo: 'M', color_nombre: 'Amarillo', cantidad: 1 },
    { id_variante: 502, sku: 'FS-CAM-AMA-L', nombre_producto: 'Camiseta básica amarilla', talla_codigo: 'L', color_nombre: 'Amarillo', cantidad: 1 },
  ],
};

const CUPONES = [
  {
    codigo: 'MAISON-2025',
    nombre: 'Bono Atelier de Bienvenida',
    descripcion: null,
    tipo_descuento: 'porcentaje',
    valor_descuento: '10.00',
    alcance: 'global',
    fecha_fin: '2026-12-31T23:59:59Z',
    usos_restantes: 500,
  },
];

const CAJERO: UsuarioSesion = {
  id_usuario: 14,
  email: 'cajero@fashionstore.com',
  nombres: 'Carlos',
  apellidos: 'Perez',
  rol: 'cajero',
  token: 'jwt-cajero',
};

describe('PuntoVentaComponent (CU31-CU32)', () => {
  let fixture: ComponentFixture<PuntoVentaComponent>;
  let component: PuntoVentaComponent;
  let http: HttpTestingController;
  const usuarioActual = signal<UsuarioSesion | null>(CAJERO);

  /** Payload literal de GET /api/v1/mis-sucursales (P2-CU03 B5): un cajero con una sola sucursal. */
  const UNA_SUCURSAL = [{ id_sucursal: 2, nombre: 'Boutique Calacoto', ciudad: 'La Paz', es_principal: true }];

  async function crear(usuario: UsuarioSesion, misSucursales: unknown[] = UNA_SUCURSAL): Promise<void> {
    usuarioActual.set(usuario);
    await TestBed.configureTestingModule({
      imports: [PuntoVentaComponent],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: LoginService, useValue: { usuarioActual, cerrarSesion: () => of(void 0) } },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(PuntoVentaComponent);
    component = fixture.componentInstance;
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    if (usuario.rol !== 'administrador') {
      http.expectOne('/api/v1/mis-sucursales').flush(misSucursales);
      fixture.detectChanges();
    }
  }

  function texto(): string {
    return (fixture.nativeElement as HTMLElement).textContent ?? '';
  }

  /** Espera el debounce real de las búsquedas incrementales. */
  const esperarDebounce = () => new Promise((resolver) => setTimeout(resolver, 320));

  function anadir(): void {
    component.agregarVariante({ ...VARIANTE });
  }

  afterEach(() => {
    http.verify();
    TestBed.resetTestingModule();
  });

  describe('como cajero', () => {
    beforeEach(async () => crear(CAJERO));

    it('opera en su sucursal sin selector y muestra el estado vacío', () => {
      expect(component.sucursalLista()).toBe(true);
      expect((fixture.nativeElement as HTMLElement).querySelector('#select-sucursal-pos')).toBeNull();
      expect((fixture.nativeElement as HTMLElement).querySelector('#pos-vacio')).toBeTruthy();
    });

    it('tiene su propio espacio: sin enlace al panel corporativo y con cierre de sesión', () => {
      const raiz = fixture.nativeElement as HTMLElement;
      expect(raiz.querySelector('#btn-volver-dashboard-pos')).toBeNull();
      expect(raiz.querySelector('a[href="/admin"]')).toBeNull();
      expect(raiz.querySelector('#pos-sesion-cajero')?.textContent).toContain('Carlos Perez');
      expect(raiz.querySelector('#btn-cerrar-sesion-pos')).toBeTruthy();
    });

    it('ya no menciona escanear: el buscador es por nombre, categoría o SKU', () => {
      const raiz = fixture.nativeElement as HTMLElement;
      expect(raiz.textContent?.toLowerCase()).not.toContain('escan');
      expect(raiz.querySelector('#campo-prenda')?.getAttribute('placeholder')).toContain('Nombre, categoría o SKU');
    });

    it('busca prendas por nombre y lista todas las coincidencias con su stock', async () => {
      component.alEscribirPrenda('camiseta');
      await esperarDebounce();
      const busqueda = http.expectOne((r) => r.url === '/api/v1/pos/variantes');
      expect(busqueda.request.params.get('q')).toBe('camiseta');
      busqueda.flush([
        VARIANTE,
        { ...VARIANTE, id_variante: 502, sku: 'FS-CAM-AMA-L', talla_codigo: 'L', disponible_en_sucursal: 0 },
      ]);
      fixture.detectChanges();

      const lista = fixture.nativeElement.querySelector('#pos-resultados-prendas') as HTMLElement;
      expect(lista.querySelectorAll('li')).toHaveLength(2);
      expect(lista.textContent).toContain('Camisas');
      expect(lista.textContent).toContain('Agotada');
      expect((fixture.nativeElement.querySelector('#btn-anadir-502') as HTMLButtonElement).disabled).toBe(true);

      (fixture.nativeElement.querySelector('#btn-anadir-501') as HTMLButtonElement).click();
      http.expectOne('/api/v1/pos/ventas/previsualizar').flush(PREVISUALIZACION);
    });

    it('con menos de 2 letras no busca, y sin coincidencias lo indica', async () => {
      component.alEscribirPrenda('c');
      await esperarDebounce();
      http.expectNone((r) => r.url === '/api/v1/pos/variantes');

      component.alEscribirPrenda('zzz');
      await esperarDebounce();
      http.expectOne((r) => r.url === '/api/v1/pos/variantes').flush([]);
      fixture.detectChanges();
      expect(fixture.nativeElement.querySelector('#pos-prendas-sin-resultados').textContent).toContain('zzz');
    });

    it('añadir una prenda pinta los totales devueltos por previsualizar, sin calcularlos', () => {
      anadir();

      const prev = http.expectOne('/api/v1/pos/ventas/previsualizar');
      expect(prev.request.method).toBe('POST');
      expect(prev.request.body).toEqual({
        id_sucursal: null,
        id_cliente: null,
        reserva: null,
        codigo_cupon: null,
        lineas: [{ id_variante: 501, cantidad: 1 }],
        lineas_reserva_excluidas: [],
      });
      prev.flush({ ...PREVISUALIZACION, total: '23.75', descuento: '1.25' });
      fixture.detectChanges();

      expect(fixture.nativeElement.querySelector('#pos-total').textContent).toContain('Bs 23,75');
      expect(texto()).toContain('Camiseta básica amarilla');
    });

    it('añadir otra vez la misma prenda suma la cantidad en la misma línea', () => {
      anadir();
      http.expectOne('/api/v1/pos/ventas/previsualizar').flush(PREVISUALIZACION);
      anadir();
      const prev = http.expectOne('/api/v1/pos/ventas/previsualizar');
      expect(prev.request.body.lineas).toEqual([{ id_variante: 501, cantidad: 2 }]);
      prev.flush(PREVISUALIZACION);
    });

    it('no añade una prenda sin stock en la boutique y avisa', () => {
      component.agregarVariante({ ...VARIANTE, disponible_en_sucursal: 0 });
      fixture.detectChanges();

      http.expectNone('/api/v1/pos/ventas/previsualizar');
      expect(component.lineas()).toHaveLength(0);
      expect(fixture.nativeElement.querySelector('#pos-error').textContent).toContain('Sin stock');
    });

    it('busca clientes por nombre o correo y, al elegir uno, muestra sus reservas activas', async () => {
      component.alEscribirCliente('ana');
      await esperarDebounce();
      const busqueda = http.expectOne((r) => r.url === '/api/v1/pos/clientes');
      expect(busqueda.request.params.get('q')).toBe('ana');
      busqueda.flush([CLIENTE_ANA, { ...CLIENTE_ANA, id_cliente: 4, nombres: 'Mariana', email: 'mariana@correo.com' }]);
      fixture.detectChanges();
      expect(fixture.nativeElement.querySelectorAll('#pos-resultados-clientes li')).toHaveLength(2);

      (fixture.nativeElement.querySelector('#btn-cliente-3') as HTMLButtonElement).click();
      http.expectOne('/api/v1/pos/clientes/3/reservas').flush([RESERVA_ANA]);
      fixture.detectChanges();

      expect(fixture.nativeElement.querySelector('#pos-cliente').textContent).toContain('ana@correo.com');
      expect(fixture.nativeElement.querySelector('#pos-cliente-con-reservas').textContent).toContain('1 reserva');

      (fixture.nativeElement.querySelector('#btn-cargar-reserva-7') as HTMLButtonElement).click();
      http.expectOne('/api/v1/pos/reservas/RES-2026-0007').flush(RESERVA_ANA);
      const prev = http.expectOne('/api/v1/pos/ventas/previsualizar');
      expect(prev.request.body).toMatchObject({ reserva: 'RES-2026-0007', id_cliente: 3 });
      prev.flush({ ...PREVISUALIZACION, lineas: [{ ...LINEA, origen: 'reserva' }] });
    });

    it('un cliente sin reservas activas lo indica', () => {
      component.seleccionarCliente(CLIENTE_ANA);
      http.expectOne('/api/v1/pos/clientes/3/reservas').flush([]);
      fixture.detectChanges();
      expect(fixture.nativeElement.querySelector('#pos-cliente-sin-reservas')).toBeTruthy();
    });

    it('sin cuenta que coincida, la venta sigue como presencial sin cuenta', async () => {
      expect(fixture.nativeElement.querySelector('#pos-venta-sin-cuenta')).toBeTruthy();
      component.alEscribirCliente('Rosa Pérez');
      await esperarDebounce();
      http.expectOne((r) => r.url === '/api/v1/pos/clientes').flush([]);
      fixture.detectChanges();
      expect(fixture.nativeElement.querySelector('#pos-clientes-sin-resultados').textContent).toContain('presencial sin cuenta');

      anadir();
      const prev = http.expectOne('/api/v1/pos/ventas/previsualizar');
      expect(prev.request.body.id_cliente).toBeNull();
      prev.flush(PREVISUALIZACION);
    });

    it('con el campo de cupón vacío lista todos los cupones, filtra al escribir y aplica el elegido', async () => {
      anadir();
      http.expectOne('/api/v1/pos/ventas/previsualizar').flush(PREVISUALIZACION);
      fixture.detectChanges();

      component.abrirCupones();
      await esperarDebounce();
      const todos = http.expectOne((r) => r.url === '/api/v1/pos/cupones');
      expect(todos.request.params.has('q')).toBe(false);
      todos.flush(CUPONES);
      fixture.detectChanges();
      expect(fixture.nativeElement.querySelector('#pos-lista-cupones').textContent).toContain('MAISON-2025');
      expect(fixture.nativeElement.querySelector('#pos-lista-cupones').textContent).toContain('-10.00 %');

      component.alEscribirCupon('bono');
      await esperarDebounce();
      const filtrados = http.expectOne((r) => r.url === '/api/v1/pos/cupones');
      expect(filtrados.request.params.get('q')).toBe('bono');
      filtrados.flush(CUPONES);
      fixture.detectChanges();

      (fixture.nativeElement.querySelector('#btn-cupon-MAISON-2025') as HTMLButtonElement).click();
      const prev = http.expectOne('/api/v1/pos/ventas/previsualizar');
      expect(prev.request.body.codigo_cupon).toBe('MAISON-2025');
      prev.flush({ ...PREVISUALIZACION, cupon_aplicado: 'MAISON-2025' });
      fixture.detectChanges();
      expect(fixture.nativeElement.querySelector('#pos-cupon-aplicado').textContent).toContain('MAISON-2025');
    });

    it('registra la venta, cobra en efectivo y muestra el cambio que devuelve el servidor', () => {
      anadir();
      http.expectOne('/api/v1/pos/ventas/previsualizar').flush(PREVISUALIZACION);

      component.registrarVenta();
      http.expectOne((r) => r.url === '/api/v1/pos/ventas' && r.method === 'POST').flush(VENTA_PENDIENTE);
      fixture.detectChanges();
      expect(fixture.nativeElement.querySelector('#panel-cobro')).toBeTruthy();
      expect(component.lineas()).toHaveLength(0);

      component.montoRecibido.set('50,00');
      component.cobrar();
      const cobro = http.expectOne('/api/v1/pos/ventas/900/cobrar');
      expect(cobro.request.body).toEqual({
        metodo_pago: 'efectivo',
        monto_recibido: '50.00',
        referencia: null,
        aprobado: true,
      });
      cobro.flush({ ...VENTA_PENDIENTE, estado: 'pagada', pagos: [PAGO_EFECTIVO] });
      fixture.detectChanges();

      expect(fixture.nativeElement.querySelector('#panel-cobro')).toBeNull();
      const ticket = fixture.nativeElement.querySelector('#ticket-comprobante').textContent;
      expect(ticket).toContain('POS-2026-000900');
      expect(ticket).toContain('Cambio');
      expect(ticket).toContain('Bs 25,00');
    });

    it('registra el rechazo del datáfono: envía aprobado=false y la venta sigue pendiente', () => {
      component.abrirCobro(VENTA_PENDIENTE as never);
      component.metodoPago.set('tarjeta_credito');
      component.referenciaPago.set('AUT-999');
      fixture.detectChanges();
      expect(fixture.nativeElement.querySelector('#btn-cobro-rechazado')).toBeTruthy();

      component.cobrar(false);
      const cobro = http.expectOne('/api/v1/pos/ventas/900/cobrar');
      expect(cobro.request.body).toEqual({
        metodo_pago: 'tarjeta_credito',
        monto_recibido: null,
        referencia: 'AUT-999',
        aprobado: false,
      });
      cobro.flush({
        ...VENTA_PENDIENTE,
        pagos: [{ ...PAGO_EFECTIVO, metodo_pago: 'tarjeta_credito', estado: 'rechazado', monto_recibido: null, cambio: null }],
      });
      fixture.detectChanges();

      expect(component.ventaEnCobro()?.estado).toBe('pendiente');
      expect(component.ventaTicket()).toBeNull();
      expect(texto()).toContain('Cobro rechazado');
    });

    it('carga una reserva por código, fija a su cliente y excluye líneas al previsualizar', () => {
      component.referenciaReserva.set('RES-2026-0007');
      component.cargarReserva();
      http.expectOne('/api/v1/pos/reservas/RES-2026-0007').flush(RESERVA_ANA);
      const prev1 = http.expectOne('/api/v1/pos/ventas/previsualizar');
      expect(prev1.request.body.reserva).toBe('RES-2026-0007');
      expect(prev1.request.body.id_cliente).toBe(3);
      prev1.flush({ ...PREVISUALIZACION, lineas: [{ ...LINEA, origen: 'reserva' }] });

      component.alternarExclusion(502);
      const prev2 = http.expectOne('/api/v1/pos/ventas/previsualizar');
      expect(prev2.request.body.lineas_reserva_excluidas).toEqual([502]);
      prev2.flush(PREVISUALIZACION);
    });

    it('descarga el comprobante como PDF (Blob)', () => {
      component.verTicket({ ...VENTA_PENDIENTE, estado: 'pagada', pagos: [PAGO_EFECTIVO] } as never);
      URL.createObjectURL = () => 'blob:pdf';
      URL.revokeObjectURL = () => undefined;
      component.descargarPdf();
      const pdf = http.expectOne('/api/v1/pos/ventas/900/comprobante.pdf');
      expect(pdf.request.responseType).toBe('blob');
      pdf.flush(new Blob(['%PDF'], { type: 'application/pdf' }));
      expect(component.descargandoPdf()).toBe(false);
    });

    it('la pestaña de pendientes carga pendientes y ventas del día, y anula con motivo', () => {
      component.cambiarPestana('pendientes');
      http
        .expectOne((r) => r.url === '/api/v1/pos/ventas' && r.params.get('estado') === 'pendiente')
        .flush([VENTA_PENDIENTE]);
      http
        .expectOne((r) => r.url === '/api/v1/pos/ventas' && r.params.get('solo_hoy') === 'true')
        .flush([]);
      fixture.detectChanges();
      expect(texto()).toContain('POS-2026-000900');

      component.pedirAnulacion(VENTA_PENDIENTE as never);
      component.motivoAnulacion.set('Cliente desiste');
      component.confirmarAnulacion();
      const anular = http.expectOne('/api/v1/pos/ventas/900/anular');
      expect(anular.request.body).toEqual({ motivo: 'Cliente desiste' });
      anular.flush({ ...VENTA_PENDIENTE, estado: 'anulada' });

      http.expectOne((r) => r.url === '/api/v1/pos/ventas' && r.params.get('estado') === 'pendiente').flush([]);
      http.expectOne((r) => r.url === '/api/v1/pos/ventas' && r.params.get('solo_hoy') === 'true').flush([]);
      fixture.detectChanges();
      expect(fixture.nativeElement.querySelector('#pos-sin-pendientes')).toBeTruthy();
    });

    it('cobra un pedido web en efectivo con el endpoint de CU16', () => {
      component.cambiarPestana('web');
      http.expectOne('/api/v1/pos/pedidos-web-efectivo').flush([
        { id_pago: 55, id_venta: 40, numero_comprobante: 'WEB-2026-000040', cliente_nombre: 'Ana Valenzuela', total: '80.00', creado_en: '2026-11-07T10:00:00Z' },
      ]);
      fixture.detectChanges();
      expect(texto()).toContain('WEB-2026-000040');

      component.confirmarPedidoWeb(component.pedidosWeb()[0]);
      http.expectOne('/api/v1/admin/pagos/55/confirmar-efectivo').flush({});
      http.expectOne('/api/v1/pos/pedidos-web-efectivo').flush([]);
      fixture.detectChanges();
      expect(fixture.nativeElement.querySelector('#pos-sin-pedidos-web')).toBeTruthy();
    });
  });

  describe('como cajero con dos sucursales autorizadas (P2-CU03, RN07)', () => {
    beforeEach(async () =>
      crear(CAJERO, [
        { id_sucursal: 5, nombre: 'Boutique Sopocachi', ciudad: 'La Paz', es_principal: true },
        { id_sucursal: 2, nombre: 'Boutique Calacoto', ciudad: 'La Paz', es_principal: false },
      ]),
    );

    it('empieza en su sucursal principal, puede cambiar a la otra y la envía en las peticiones', () => {
      const selector = (fixture.nativeElement as HTMLElement).querySelector('#select-sucursal-pos');
      expect(selector).toBeTruthy();
      expect(component.idSucursal()).toBe(5);
      expect(component.sucursales().map((s) => s.nombre)).toEqual(['Boutique Sopocachi', 'Boutique Calacoto']);

      component.seleccionarSucursal(2);
      anadir();
      const prev = http.expectOne('/api/v1/pos/ventas/previsualizar');
      expect(prev.request.body.id_sucursal).toBe(2);
      prev.flush(PREVISUALIZACION);
    });
  });

  describe('como administrador', () => {
    beforeEach(async () => crear({ ...CAJERO, id_usuario: 1, rol: 'administrador' }));

    it('exige elegir boutique y la envía en las peticiones', async () => {
      http.expectOne('/api/v1/sucursales/activas').flush([
        { id_sucursal: 2, nombre: 'Boutique Calacoto', ciudad: 'La Paz', direccion: 'Av. Ballivián 1234' },
      ]);
      fixture.detectChanges();
      expect(fixture.nativeElement.querySelector('#pos-sin-sucursal')).toBeTruthy();
      expect(fixture.nativeElement.querySelector('#btn-volver-dashboard-pos')).toBeTruthy();
      expect(fixture.nativeElement.querySelector('#btn-cerrar-sesion-pos')).toBeNull();

      component.seleccionarSucursal(2);
      fixture.detectChanges();
      expect(fixture.nativeElement.querySelector('#campo-prenda')).toBeTruthy();

      component.alEscribirPrenda('camiseta');
      await esperarDebounce();
      const variante = http.expectOne((r) => r.url === '/api/v1/pos/variantes');
      expect(variante.request.params.get('id_sucursal')).toBe('2');
      variante.flush([VARIANTE]);
      component.agregarVariante(VARIANTE);
      const prev = http.expectOne('/api/v1/pos/ventas/previsualizar');
      expect(prev.request.body.id_sucursal).toBe(2);
      prev.flush(PREVISUALIZACION);
    });
  });
});
