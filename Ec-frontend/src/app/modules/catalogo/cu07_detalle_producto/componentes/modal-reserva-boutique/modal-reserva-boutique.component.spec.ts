import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { ModalReservaBoutiqueComponent } from './modal-reserva-boutique.component';
import { ReservaService } from '../../servicios/reserva.service';
import { LoginService } from '../../../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import {
  DisponibilidadSucursalItem,
  ProductoDetalle,
  ReservaConfirmacion,
  VarianteDetalle,
} from '../../modelos/producto-detalle.model';

describe('ModalReservaBoutiqueComponent (CU12)', () => {
  const mockProducto: ProductoDetalle = {
    id_producto: 10,
    nombre: 'Vestido Plisado en Seda Marfil Natural',
    descripcion: 'Vestido largo de fiesta plisado.',
    precio_base: '890.00',
    precio_final: '890.00',
    tiene_descuento: false,
    descuento_monto: '0.00',
    porcentaje_descuento: null,
    cuotas_info: 'o 3 pagos de 296,66 € sin intereses',
    subtitulo_atelier: 'ALTA COSTURA · MILÁN / LYON',
    linea_confeccion: 'ALTA COSTURA LYON',
    etiqueta_badge: 'EDICIÓN LIMITADA',
    sku_base: 'ATEL-2025-VD9',
    rating_promedio: 4.9,
    total_resenas: 38,
    beneficio_membresia: 'Beneficio Privé',
    categoria_id: 3,
    categoria_nombre: 'Vestidos',
    coleccion_id: 4,
    coleccion_nombre: 'Seda & Plisados',
    imagen_principal: 'https://images.unsplash.com/photo-1566174053879-31528523f8ae',
    galeria: [],
    modelo_ar_url: null,
    modelo_info: 'MODELO: 1,77M',
    composicion: {
      cuerpo_principal: '100% Seda',
      forro_interior: 'Seda pura',
      tecnica_textil: 'Plisado',
      descripcion_confeccion: 'Artesanal',
      instrucciones_cuidado: ['Limpieza en seco'],
    },
    colores_disponibles: [],
    tallas_disponibles: [],
    variantes: [],
    piezas_look_complementario: [],
    total_guardados: 142,
  };

  const mockVariante: VarianteDetalle = {
    id_variante: 100,
    id_producto: 10,
    id_talla: 8,
    talla_codigo: '38',
    talla_orden: 11,
    id_color: 7,
    color_nombre: 'Ébano',
    color_hex: '#1A1A1A',
    sku: 'SKU-FEM-10',
    precio_extra: '0.00',
    precio_final_variante: '890.00',
    stock_total_disponible: 10,
    tiene_stock: true,
  };

  const mockSucursales: DisponibilidadSucursalItem[] = [
    {
      id_sucursal: 1,
      nombre: 'Flagship Madrid Serrano',
      ciudad: 'Madrid',
      direccion: 'Calle Serrano 48',
      telefono: '91 555 1234',
      horario_apertura: '09:00',
      horario_cierre: '20:00',
      cantidad_disponible: 2,
      cantidad_reservada: 0,
      estado_stock: 'disponible',
      badge_stock: '2 UDS EN STOCK',
      citas_disponibles_texto: 'Citas disponibles hoy y mañana',
      permite_reserva_directa: true,
    },
  ];

  // Copia literal de una respuesta real de POST /api/v1/reservas (`ReservaCreadaOut`).
  // Antes este mock reproducía la interfaz del propio frontend, así que la suite validaba
  // un contrato que el servidor nunca envía y ocultaba que el modal pintaba campos vacíos.
  const mockConfirmacion: ReservaConfirmacion = {
    id_reserva: 1,
    codigo_reserva: 'RES-2026-0001',
    id_sucursal: 1,
    nombre_sucursal: 'Flagship Madrid Serrano',
    direccion_sucursal: 'Calle de Serrano 44, Salamanca',
    fecha_hora_atencion: '2026-09-22T11:30:00Z',
    estado: 'pendiente',
    canal_origen: 'web',
    items: [
      {
        id_reserva_detalle: 1,
        id_variante: 100,
        sku: 'ATEL-2025-VD9-38-MAR',
        nombre_producto: 'Vestido Plisado en Seda Marfil Natural',
        talla_codigo: '38',
        color_nombre: 'Seda Marfil',
        cantidad: 1,
        precio_unitario: '890.00',
      },
    ],
    mensaje_confirmacion:
      'Cita de prueba presencial confirmada con nuestro equipo de sastrería.',
    cortesias_incluidas: [
      'Champán de cortesía o infusión artesanal de bienvenida',
      'Asesoramiento privado de estilista sénior de atelier',
    ],
    creado_en: '2026-09-21T10:00:00Z',
  };

  let mockReservaService: {
    obtenerSucursalesActivas: ReturnType<typeof vi.fn>;
    crearReservaBoutique: ReturnType<typeof vi.fn>;
  };

  let mockLoginService: {
    estaAutenticado: ReturnType<typeof vi.fn>;
  };

  beforeEach(async () => {
    mockReservaService = {
      obtenerSucursalesActivas: vi.fn().mockReturnValue(of(mockSucursales)),
      crearReservaBoutique: vi.fn().mockReturnValue(of(mockConfirmacion)),
    };

    mockLoginService = {
      estaAutenticado: vi.fn().mockReturnValue(true),
    };

    await TestBed.configureTestingModule({
      imports: [ModalReservaBoutiqueComponent],
      providers: [
        provideRouter([]),
        { provide: ReservaService, useValue: mockReservaService },
        { provide: LoginService, useValue: mockLoginService },
      ],
    }).compileComponents();
  });

  it('debe crearse y renderizar la información de la prenda seleccionada', () => {
    const fixture = TestBed.createComponent(ModalReservaBoutiqueComponent);
    fixture.componentRef.setInput('producto', mockProducto);
    fixture.componentRef.setInput('varianteSeleccionada', mockVariante);
    fixture.componentRef.setInput('sucursales', mockSucursales);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('RESERVAR CITA DE PRUEBA EN BOUTIQUE');
    expect(compiled.textContent).toContain('Vestido Plisado en Seda Marfil Natural');
    expect(compiled.textContent).toContain('Talla: 38 ES');
  });

  it('debe permitir seleccionar una boutique y una franja horaria', () => {
    const fixture = TestBed.createComponent(ModalReservaBoutiqueComponent);
    fixture.componentRef.setInput('producto', mockProducto);
    fixture.componentRef.setInput('varianteSeleccionada', mockVariante);
    fixture.componentRef.setInput('sucursales', mockSucursales);
    fixture.detectChanges();

    const comp = fixture.componentInstance;
    comp['seleccionarHorario']('MAÑANA 16:30H');
    expect(comp['horarioSeleccionado']()).toBe('MAÑANA 16:30H');
  });

  it('debe enviar la reserva al servicio y emitir reservaConfirmada si está autenticado', () => {
    const fixture = TestBed.createComponent(ModalReservaBoutiqueComponent);
    fixture.componentRef.setInput('producto', mockProducto);
    fixture.componentRef.setInput('varianteSeleccionada', mockVariante);
    fixture.componentRef.setInput('sucursales', mockSucursales);
    fixture.detectChanges();

    const comp = fixture.componentInstance;
    const emitSpy = vi.spyOn(comp.reservaConfirmada, 'emit');

    comp['confirmarReserva']();

    expect(mockReservaService.crearReservaBoutique).toHaveBeenCalledWith(
      expect.objectContaining({
        id_sucursal: 1,
        canal_origen: 'web',
        items: [{ id_variante: 100, cantidad: 1 }],
      })
    );
    expect(emitSpy).toHaveBeenCalledWith(mockConfirmacion);
    expect(comp['exito']()).toEqual(mockConfirmacion);
  });

  it('debe renderizar el código, la boutique y las cortesías que devuelve el backend', () => {
    const fixture = TestBed.createComponent(ModalReservaBoutiqueComponent);
    fixture.componentRef.setInput('producto', mockProducto);
    fixture.componentRef.setInput('varianteSeleccionada', mockVariante);
    fixture.componentRef.setInput('sucursales', mockSucursales);
    fixture.detectChanges();

    const comp = fixture.componentInstance;
    comp['confirmarReserva']();
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    // Con los nombres de campo desalineados, el modal imprimía «CÓDIGO: » sin nada detrás.
    expect(compiled.textContent).toContain('RES-2026-0001');
    expect(compiled.textContent).toContain('Calle de Serrano 44, Salamanca');
    expect(compiled.textContent).toContain(
      'Champán de cortesía o infusión artesanal de bienvenida'
    );
    // El total se deriva de las líneas, el backend no envía `total_prendas`.
    expect(comp['totalPrendas']()).toBe(1);
  });

  it('debe emitir evento cerrar al hacer clic en cancelar', () => {
    const fixture = TestBed.createComponent(ModalReservaBoutiqueComponent);
    fixture.componentRef.setInput('producto', mockProducto);
    fixture.componentRef.setInput('varianteSeleccionada', mockVariante);
    fixture.componentRef.setInput('sucursales', mockSucursales);
    fixture.detectChanges();

    const comp = fixture.componentInstance;
    const cerrarSpy = vi.spyOn(comp.cerrar, 'emit');

    comp['cerrarModal']();
    expect(cerrarSpy).toHaveBeenCalled();
  });
});
