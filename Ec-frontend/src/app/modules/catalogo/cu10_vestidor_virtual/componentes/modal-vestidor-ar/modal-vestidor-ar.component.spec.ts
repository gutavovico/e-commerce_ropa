import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ModalVestidorArComponent, describirErrorCamara } from './modal-vestidor-ar.component';
import { VestidorService } from '../../servicios/vestidor.service';
import { ProductoDetalle, VarianteDetalle } from '../../../cu07_detalle_producto/modelos/producto-detalle.model';

describe('ModalVestidorArComponent (CU10)', () => {
  let component: ModalVestidorArComponent;
  let fixture: ComponentFixture<ModalVestidorArComponent>;
  let vestidorServiceMock: {
    obtenerTokenDecart: ReturnType<typeof vi.fn>;
    registrarSesion: ReturnType<typeof vi.fn>;
    actualizarSesion: ReturnType<typeof vi.fn>;
  };

  const mockProducto: ProductoDetalle = {
    id_producto: 42,
    nombre: 'Vestido Escultural de Gala en Seda',
    descripcion: 'Vestido exclusivo de alta costura.',
    precio_base: '1200.00',
    precio_final: '1200.00',
    tiene_descuento: false,
    descuento_monto: '0.00',
    porcentaje_descuento: null,
    cuotas_info: 'o 3 cuotas sin interés',
    subtitulo_atelier: 'ALTA COSTURA · MILÁN / PARÍS',
    linea_confeccion: 'ATELIER PRIVÉ 2026',
    etiqueta_badge: 'EDICIÓN LIMITADA',
    sku_base: 'ATEL-VEST-42',
    rating_promedio: 5.0,
    total_resenas: 24,
    beneficio_membresia: 'Beneficio Privé',
    categoria_id: 1,
    categoria_nombre: 'Vestidos de Gala',
    coleccion_id: 1,
    coleccion_nombre: 'Atelier Privé 2026',
    imagen_principal: 'https://fashionstore.com/images/42.jpg',
    galeria: [],
    modelo_ar_url: 'https://fashionstore.com/ar/42_2d.png',
    modelo_info: 'MODELO: 1,78M',
    composicion: {
      cuerpo_principal: '100% Seda Natural',
      forro_interior: 'Seda Habotai',
      tecnica_textil: 'Drapeado Escultural',
      descripcion_confeccion: 'Confección artesanal en taller',
      instrucciones_cuidado: ['Limpieza en seco especializada'],
    },
    colores_disponibles: [
      { id_color: 1, nombre: 'Negro Obsidian', codigo_hex: '#1E1E1E', disponible: true },
    ],
    tallas_disponibles: [
      { id_talla: 1, codigo: '38', orden: 1, disponible: true, stock_total: 5 },
    ],
    variantes: [],
    piezas_look_complementario: [],
    total_guardados: 98,
  };

  const mockVariante: VarianteDetalle = {
    id_variante: 10,
    id_producto: 42,
    id_talla: 1,
    talla_codigo: '38',
    talla_orden: 1,
    id_color: 1,
    color_nombre: 'Negro Obsidian',
    color_hex: '#1E1E1E',
    sku: 'ATEL-VEST-38-NEG',
    precio_extra: '0.00',
    precio_final_variante: '1200.00',
    stock_total_disponible: 5,
    tiene_stock: true,
  };

  beforeEach(async () => {
    vestidorServiceMock = {
      obtenerTokenDecart: vi.fn().mockReturnValue(
        of({
          token: 'decart_client_token_test',
          expira_en_segundos: 60,
          servicio: 'decart_lucy_vton_720p',
        })
      ),
      registrarSesion: vi.fn().mockReturnValue(
        of({
          id_sesion_ar: 845,
          id_cliente: 10,
          id_producto: 42,
          dispositivo: 'web',
          motor: 'local',
          duracion_segundos: 45,
          fecha_hora: '2026-09-13T16:44:28Z',
          resultado_url: undefined,
          genero_interes: false,
        })
      ),
      actualizarSesion: vi.fn().mockReturnValue(
        of({
          id_sesion_ar: 845,
          id_cliente: 10,
          id_producto: 42,
          dispositivo: 'web',
          motor: 'local',
          duracion_segundos: 45,
          fecha_hora: '2026-09-13T16:44:28Z',
          resultado_url: 'https://fashionstore.com/captura.jpg',
          genero_interes: true,
        })
      ),
    };

    await TestBed.configureTestingModule({
      imports: [ModalVestidorArComponent],
      providers: [{ provide: VestidorService, useValue: vestidorServiceMock }],
    }).compileComponents();

    fixture = TestBed.createComponent(ModalVestidorArComponent);
    component = fixture.componentInstance;

    fixture.componentRef.setInput('producto', mockProducto);
    fixture.componentRef.setInput('variante', mockVariante);
    fixture.detectChanges();
  });

  it('debe crearse e iniciar por defecto en Motor 1 (Local)', () => {
    expect(component).toBeTruthy();
    expect(component.motorActivo()).toBe('local');
    expect(component.etiquetaMotor()).toContain('MOTOR 1 · LOCAL');
  });

  it('debe renderizar el nombre de la prenda y la talla correctamente', () => {
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('Vestido Escultural de Gala en Seda');
    expect(el.textContent).toContain('Talla 38');
  });

  it('debe conmutar a Motor 2 (IA Decart) al solicitar token exitosamente', () => {
    component.activarModoRealistaIA();

    expect(vestidorServiceMock.obtenerTokenDecart).toHaveBeenCalled();
    expect(component.motorActivo()).toBe('ia');
    expect(component.streamingIA()).toBe(true);
    expect(component.segundosRestantesIA()).toBe(60);
  });

  it('debe activar Fallback Automático a Motor 1 si el servicio Decart retorna error (503)', () => {
    vestidorServiceMock.obtenerTokenDecart.mockReturnValue(
      throwError(() => ({ status: 503, statusText: 'Service Unavailable' }))
    );

    component.activarModoRealistaIA();

    expect(component.motorActivo()).toBe('local');
    expect(component.streamingIA()).toBe(false);
    expect(component.errorFallback()).toContain('El servicio realista con IA de Decart no se encuentra disponible');
  });

  it('debe permitir conmutar manualmente de regreso a Motor 1 (Local)', () => {
    component.activarModoRealistaIA();
    expect(component.motorActivo()).toBe('ia');

    component.conmutarAMotorLocal();
    expect(component.motorActivo()).toBe('local');
    expect(component.streamingIA()).toBe(false);
  });

  it('debe emitir anadirAlCarrito y registrar sesión con genero_interes=true al pulsar "AÑADIR A LA BOLSA"', () => {
    const anadirSpy = vi.spyOn(component.anadirAlCarrito, 'emit');
    const cerrarSpy = vi.spyOn(component.cerrar, 'emit');

    component.onAnadirABolsaClick();

    expect(vestidorServiceMock.registrarSesion).toHaveBeenCalledWith(
      expect.objectContaining({
        id_producto: 42,
        genero_interes: true,
      })
    );
    expect(anadirSpy).toHaveBeenCalled();
    expect(cerrarSpy).toHaveBeenCalled();
  });

  it('debe emitir reservarBoutique y registrar sesión con genero_interes=true al pulsar "RESERVAR EN BOUTIQUE"', () => {
    const reservarSpy = vi.spyOn(component.reservarBoutique, 'emit');
    const cerrarSpy = vi.spyOn(component.cerrar, 'emit');

    component.onReservarBoutiqueClick();

    expect(vestidorServiceMock.registrarSesion).toHaveBeenCalledWith(
      expect.objectContaining({
        id_producto: 42,
        genero_interes: true,
      })
    );
    expect(reservarSpy).toHaveBeenCalled();
    expect(cerrarSpy).toHaveBeenCalled();
  });

  it('debe emitir cerrar al invocar onCerrarClick', () => {
    const cerrarSpy = vi.spyOn(component.cerrar, 'emit');
    component.onCerrarClick();
    expect(cerrarSpy).toHaveBeenCalled();
  });

  it('debe actualizar escala y offset vertical con los controles de calibración', () => {
    const fakeEventZoom = { target: { value: '115' } } as unknown as Event;
    component.actualizarEscala(fakeEventZoom);
    expect(component.escalaPrenda()).toBe(115);

    const fakeEventOffset = { target: { value: '25' } } as unknown as Event;
    component.actualizarOffsetVertical(fakeEventOffset);
    expect(component.offsetVertical()).toBe(25);
  });

  describe('diagnóstico de la cámara', () => {
    afterEach(() => {
      delete (navigator as unknown as { mediaDevices?: unknown }).mediaDevices;
    });

    it.each([
      ['NotAllowedError', 'bloqueó el acceso'],
      ['NotReadableError', 'en uso por otra aplicación'],
      ['NotFoundError', 'No se encontró una cámara'],
      ['RarezaDesconocida', '(RarezaDesconocida)'],
    ])('traduce %s a una causa accionable', (nombre, esperado) => {
      expect(describirErrorCamara(nombre)).toContain(esperado);
    });

    it('muestra la causa cuando getUserMedia falla y la limpia al reintentar con éxito', async () => {
      const getUserMedia = vi
        .fn()
        .mockRejectedValueOnce(Object.assign(new Error('ocupada'), { name: 'NotReadableError' }))
        .mockResolvedValueOnce({ getTracks: () => [], getVideoTracks: () => [] });
      Object.defineProperty(navigator, 'mediaDevices', { value: { getUserMedia }, configurable: true });
      vi.spyOn(console, 'error').mockImplementation(() => {});

      await component.iniciarCamaraLocal();
      expect(component.camaraActiva()).toBe(false);
      expect(component.mensajeCamara()).toContain('en uso por otra aplicación');

      await component.reintentarCamara();
      expect(component.camaraActiva()).toBe(true);
      expect(component.mensajeCamara()).toBeNull();
    });
  });

  describe('conexión con el SDK de Decart (navegador con cámara)', () => {
    type OpcionesCliente = { apiKeyProvider: () => Promise<string> };
    type OpcionesConnect = Record<string, unknown>;

    let opcionesCliente: OpcionesCliente;
    let opcionesConnect: OpcionesConnect | undefined;
    let resolverConnect: (rt: unknown) => void;
    let informeConectividad: { quality: string; metrics: { transport: string; rttMs: number | null }; reasons: string[] };
    const rtFake = { on: vi.fn(), disconnect: vi.fn() };
    const connectFake = vi.fn();
    const pistaVideo = { applyConstraints: vi.fn().mockResolvedValue(undefined) };
    const modeloFake = { name: 'lucy-vton-3.6', width: 1280, height: 720, fps: { ideal: 30, max: 30 } };

    beforeEach(() => {
      opcionesConnect = undefined;
      rtFake.on.mockClear();
      rtFake.disconnect.mockClear();
      pistaVideo.applyConstraints.mockClear();
      informeConectividad = { quality: 'good', metrics: { transport: 'udp', rttMs: 40 }, reasons: [] };
      connectFake.mockReset().mockImplementation((_stream: unknown, opts2: OpcionesConnect) => {
        opcionesConnect = opts2;
        return new Promise((resolve) => (resolverConnect = resolve));
      });
      Object.defineProperty(navigator, 'mediaDevices', { value: {}, configurable: true });

      const sdkFake = {
        createDecartClient: vi.fn((opts: OpcionesCliente) => {
          opcionesCliente = opts;
          return {
            realtime: {
              connect: connectFake,
              checkConnectivity: vi.fn(async () => informeConectividad),
            },
          };
        }),
        createConsoleLogger: vi.fn(() => ({})),
        models: { realtime: vi.fn(() => modeloFake) },
      };

      const interno = component as unknown as {
        mediaStream: unknown;
        cargarSdkDecart: () => Promise<unknown>;
        obtenerPrendaComoDataUrl: () => Promise<string>;
      };
      interno.mediaStream = { getTracks: () => [], getVideoTracks: () => [pistaVideo] };
      vi.spyOn(interno, 'cargarSdkDecart').mockResolvedValue(sdkFake);
      vi.spyOn(interno, 'obtenerPrendaComoDataUrl').mockResolvedValue('data:image/png;base64,AAAA');
    });

    afterEach(() => {
      vi.useRealTimers();
      delete (navigator as unknown as { mediaDevices?: unknown }).mediaDevices;
    });

    it('pide un token nuevo al backend en cada re-marcación en lugar de reutilizar el caducado', async () => {
      component.activarModoRealistaIA();
      await vi.waitFor(() => expect(opcionesConnect).toBeDefined());

      // Primera marcación: el token ya emitido, sin otra petición.
      expect(await opcionesCliente.apiKeyProvider()).toBe('decart_client_token_test');
      expect(vestidorServiceMock.obtenerTokenDecart).toHaveBeenCalledTimes(1);

      // Re-marcación del SDK: token fresco.
      await opcionesCliente.apiKeyProvider();
      expect(vestidorServiceMock.obtenerTokenDecart).toHaveBeenCalledTimes(2);
    });

    it('observa cola y capacidad durante connect() y limita los reintentos del SDK', async () => {
      component.activarModoRealistaIA();
      await vi.waitFor(() => expect(opcionesConnect).toBeDefined());

      expect(opcionesConnect).toEqual(
        expect.objectContaining({
          retries: 1,
          onConnectionChange: expect.any(Function),
          onQueuePosition: expect.any(Function),
          onCapacityWait: expect.any(Function),
        })
      );

      const onQueuePosition = opcionesConnect!['onQueuePosition'] as (q: { position: number; queueSize: number }) => void;
      onQueuePosition({ position: 2, queueSize: 5 });
      expect(component.mensajeAviso()).toContain('posición 2 de 5');
    });

    it('al vencer la espera conmuta a Local y cierra la sesión que llegue tarde', async () => {
      vi.useFakeTimers();
      component.activarModoRealistaIA();
      await vi.waitFor(() => expect(opcionesConnect).toBeDefined());

      vi.advanceTimersByTime(45_000);
      expect(component.motorActivo()).toBe('local');
      expect(component.conectandoIA()).toBe(false);
      expect(component.errorFallback()).toContain('Tiempo de espera excedido');

      // connect() resuelve después del timeout: la sesión huérfana se cierra y no se adopta.
      resolverConnect(rtFake);
      await vi.waitFor(() => expect(rtFake.disconnect).toHaveBeenCalled());
      expect(rtFake.on).not.toHaveBeenCalled();
      expect(component.streamingIA()).toBe(false);
    });

    it('no intenta conectar si el chequeo previo declara la red crítica', async () => {
      informeConectividad = {
        quality: 'critical',
        metrics: { transport: 'failed', rttMs: null },
        reasons: ['no ICE candidates'],
      };

      component.activarModoRealistaIA();
      await vi.waitFor(() => expect(component.conectandoIA()).toBe(false));

      expect(connectFake).not.toHaveBeenCalled();
      expect(component.motorActivo()).toBe('local');
      expect(component.errorFallback()).toContain('no permite el vídeo en tiempo real');
      expect(component.errorFallback()).toContain('failed');
    });

    it('ajusta la cámara a la resolución y tasa de cuadros del modelo antes de conectar', async () => {
      component.activarModoRealistaIA();
      await vi.waitFor(() => expect(opcionesConnect).toBeDefined());

      expect(pistaVideo.applyConstraints).toHaveBeenCalledWith({
        width: { ideal: 1280 },
        height: { ideal: 720 },
        frameRate: { ideal: 30, max: 30 },
      });
    });

    it('envía un prompt de sustitución según el tipo de prenda', async () => {
      component.activarModoRealistaIA();
      await vi.waitFor(() => expect(opcionesConnect).toBeDefined());

      const estado = opcionesConnect!['initialState'] as { prompt: { text: string }; image: string };
      expect(estado.prompt.text).toBe('Substitute the current outfit with the dress shown in the reference image');
      expect(estado.image).toBe('data:image/png;base64,AAAA');
    });
  });
});
