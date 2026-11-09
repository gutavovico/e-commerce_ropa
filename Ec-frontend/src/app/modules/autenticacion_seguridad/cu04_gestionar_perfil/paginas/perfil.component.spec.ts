import { entrarEnTienda } from '../../../../core/tenant/tenant.testing';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter, Router } from '@angular/router';
import { signal } from '@angular/core';
import { of } from 'rxjs';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { PerfilComponent } from './perfil.component';
import { PerfilService } from '../servicios/perfil.service';
import { LoginService } from '../../cu02_iniciar_sesion/servicios/login.service';
import { PedidoHistorico, PerfilCliente } from '../modelos/perfil.dto';
import { MisReservasService } from '../../../reservas/cu13_consultar_cancelar_reservas/servicios/mis-reservas.service';

describe('PerfilComponent (CU04 + CU17)', () => {
  const mockPerfil: PerfilCliente = {
    id_usuario: 8402,
    numero_socio: '#8402',
    email: 'ana.valenzuela@studio.es',
    rol: 'cliente',
    fecha_registro: '2021-10-15T12:00:00Z',
    miembro_desde: 'Octubre 2021',
    nombres: 'Ana',
    apellidos: 'Valenzuela',
    telefono: '+34 612 884 901',
    talla_preferida: '38',
    genero: 'femenino',
    acepta_marketing: true,
    resumen_atelier: {
      visitas_registradas: 32,
      boutiques_visitadas: 4,
      preferencia_textil: '100% Seda & Lana',
      estatus_membresia: 'Nivel Platino',
    },
  };

  const mockPedido: PedidoHistorico = {
    id_venta: 42,
    numero_comprobante: 'FS-2026-000042',
    fecha_venta: '2026-04-11T15:30:00Z',
    tipo_venta: 'digital_web',
    estado: 'pagada',
    tipo_entrega: 'domicilio',
    nombre_sucursal: 'Boutique Equipetrol',
    nombre_sucursal_retiro: null,
    direccion_envio: 'Av. San Martín #450',
    codigo_promocion: null,
    subtotal: '890.00',
    descuento: '0.00',
    total: '890.00',
    metodo_pago: 'tarjeta_credito',
    referencia_pasarela: 'pi_test_42',
    items: [
      {
        id_venta_detalle: 101,
        id_producto: 7,
        id_variante: 19,
        sku: 'FS-ABR-007-M-NEG',
        nombre_producto: 'Abrigo de Lana Merino',
        imagen_url: 'https://cdn.fashionstore.test/abrigo.jpg',
        talla: 'M',
        color: 'Negro',
        color_hex: '#111111',
        cantidad: 1,
        precio_unitario: '890.00',
        subtotal_linea: '890.00',
        nombre_sucursal: 'Boutique Equipetrol',
      },
    ],
  };

  let mockPerfilService: any;
  let mockLoginService: any;
  let mockMisReservasService: any;
  let router: Router;

  beforeEach(async () => {
    mockPerfilService = {
      perfil: signal<PerfilCliente | null>(mockPerfil),
      cargando: signal<boolean>(false),
      guardando: signal<boolean>(false),
      error: signal<string | null>(null),
      mensajeExito: signal<string | null>(null),
      modalEdicionAbierto: signal<boolean>(false),
      pedidos: signal<PedidoHistorico[]>([]),
      totalPedidos: signal<number>(0),
      pedidosCompletados: signal<number>(0),
      cargandoPedidos: signal<boolean>(false),
      cargarPerfil: vi.fn().mockReturnValue(of(mockPerfil)),
      cargarHistorialCompras: vi.fn().mockReturnValue(
        of({ total_pedidos: 0, pedidos_completados: 0, pedidos: [] })
      ),
      actualizarPerfil: vi.fn().mockReturnValue(of(mockPerfil)),
      abrirModalEdicion: vi.fn(),
      cerrarModalEdicion: vi.fn(),
      limpiarMensajes: vi.fn(),
    };

    mockLoginService = {
      cerrarSesion: vi.fn().mockReturnValue(of(void 0)),
    };

    mockMisReservasService = {
      resumen: signal({ activas: 0, proxima: null }),
      cargando: signal(false),
      cargarMisReservas: vi.fn().mockReturnValue(
        of({ resumen: { activas: 0, proxima: null }, proximas: [], historial: [] })
      ),
    };

    await TestBed.configureTestingModule({
      imports: [PerfilComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        { provide: PerfilService, useValue: mockPerfilService },
        { provide: LoginService, useValue: mockLoginService },
        { provide: MisReservasService, useValue: mockMisReservasService },
      ],
    }).compileComponents();
    entrarEnTienda(); // P2-CU02: dentro del portal de FASHION STORE

    router = TestBed.inject(Router);
    vi.spyOn(router, 'navigate').mockImplementation(() => Promise.resolve(true));
  });

  it('debe instanciar el componente correctamente', () => {
    const fixture = TestBed.createComponent(PerfilComponent);
    const comp = fixture.componentInstance;
    expect(comp).toBeTruthy();
  });

  it('debe cargar los datos del perfil y el historial de compras al inicializarse', () => {
    const fixture = TestBed.createComponent(PerfilComponent);
    fixture.detectChanges();
    expect(mockPerfilService.cargarPerfil).toHaveBeenCalled();
    expect(mockPerfilService.cargarHistorialCompras).toHaveBeenCalled();
  });

  it('debe abrir y cerrar el modal de edición de datos', () => {
    const fixture = TestBed.createComponent(PerfilComponent);
    const comp = fixture.componentInstance;
    comp.abrirModal();
    expect(mockPerfilService.abrirModalEdicion).toHaveBeenCalled();

    comp.cerrarModal();
    expect(mockPerfilService.cerrarModalEdicion).toHaveBeenCalled();
  });

  it('debe llamar a cerrarSesion y redirigir a /login', () => {
    const fixture = TestBed.createComponent(PerfilComponent);
    const comp = fixture.componentInstance;
    comp.cerrarSesion();
    expect(mockLoginService.cerrarSesion).toHaveBeenCalled();
    expect(router.navigate).toHaveBeenCalledWith(['/', 'fashionstore', 'login']);
  });

  it('carga el resumen de reservas al iniciar', () => {
    const fixture = TestBed.createComponent(PerfilComponent);
    fixture.detectChanges();
    expect(mockMisReservasService.cargarMisReservas).toHaveBeenCalled();
  });

  it('la tarjeta de reservas muestra el resumen real y enlaza a /reservas, sin literales de bolsa', () => {
    mockMisReservasService.resumen.set({
      activas: 2,
      proxima: { id_reserva: 5, fecha_hora_atencion: '2026-10-05T16:00:00Z', nombre_sucursal: 'Atelier Serrano - Madrid' },
    });

    const fixture = TestBed.createComponent(PerfilComponent);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Mis Reservas');
    expect(compiled.textContent).toContain('2 reservas activas');
    expect(compiled.textContent).toContain('Atelier Serrano - Madrid');
    expect(compiled.textContent).toContain('VER MIS RESERVAS');
    expect(compiled.textContent).not.toContain('Bolsa de Compra');
    expect(compiled.textContent).not.toContain('3 Artículos seleccionados');
    expect(compiled.textContent).not.toContain('IR AL CHECKOUT');

    const enlace = compiled.querySelector('a[href="/fashionstore/reservas"]');
    expect(enlace).not.toBeNull();
  });

  it('la tarjeta de reservas muestra su estado vacío cuando no hay citas agendadas', () => {
    const fixture = TestBed.createComponent(PerfilComponent);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Sin citas agendadas');
  });

  it('CU17: muestra el estado vacío del historial cuando el cliente no tiene compras', () => {
    const fixture = TestBed.createComponent(PerfilComponent);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('0 PEDIDOS COMPLETADOS');
    expect(compiled.textContent).toContain('Sin compras registradas');
    expect(compiled.textContent).not.toContain('PED-001');
  });

  it('CU17: renderiza pedidos reales y abre el modal de comprobante digital', () => {
    mockPerfilService.pedidos.set([mockPedido]);
    mockPerfilService.totalPedidos.set(1);
    mockPerfilService.pedidosCompletados.set(1);

    const fixture = TestBed.createComponent(PerfilComponent);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('1 PEDIDO COMPLETADO');
    expect(compiled.textContent).toContain('Abrigo de Lana Merino');
    expect(compiled.textContent).toContain('FS-2026-000042');
    expect(compiled.textContent).toContain('Bs 890,00');

    fixture.componentInstance.descargarFactura(mockPedido);
    fixture.detectChanges();

    expect(compiled.textContent).toContain('FASHION STORE · COMPROBANTE DIGITAL');
    expect(compiled.textContent).toContain('Tarjeta de crédito');
    expect(compiled.textContent).toContain('pi_test_42');
  });
});
