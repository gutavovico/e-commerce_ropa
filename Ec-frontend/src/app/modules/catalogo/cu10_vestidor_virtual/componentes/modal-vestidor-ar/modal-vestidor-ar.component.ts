import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  EventEmitter,
  OnDestroy,
  OnInit,
  Output,
  ViewChild,
  computed,
  inject,
  input,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { firstValueFrom } from 'rxjs';
import type { CapacityWait, ConnectionState, ModelDefinition, QueuePosition, RealTimeClient } from '@decartai/sdk';
import { ProductoDetalle, VarianteDetalle } from '../../../cu07_detalle_producto/modelos/producto-detalle.model';
import { TipoMotorVestidor, TokenVestidorDecartOut } from '../../modelos/vestidor.dto';
import { VestidorService } from '../../servicios/vestidor.service';
import { construirPromptVton } from '../../servicios/prompt-vton';
import { ImportePipe } from '../../../../../core/tenant/moneda';

/** Lado mínimo recomendado por Decart para la imagen de referencia de la prenda. */
const LADO_MINIMO_REFERENCIA_PX = 512;
/** Regla de negocio de control de costes: duración máxima de la sesión realista (no es la vida del token). */
const LIMITE_SESION_IA_SEGUNDOS = 60;
/**
 * Reintentos del SDK por conexión. Con 1 reintento son 2 marcaciones de ~15 s de WebRTC cada una:
 * la ventana completa del SDK cabe dentro de `TIMEOUT_CONEXION_IA_MS`, de modo que el SDK se rinde
 * por sí mismo antes de que la UI dé la conexión por perdida.
 */
const REINTENTOS_CONEXION_SDK = 1;
const PRESUPUESTO_ESPERA_CAPACIDAD_MS = 20_000;
const TIMEOUT_CONEXION_IA_MS = 45_000;

/** Traduce el `DOMException.name` de `getUserMedia` a una causa accionable para el cliente. */
export function describirErrorCamara(nombre: string): string {
  switch (nombre) {
    case 'NotAllowedError':
    case 'SecurityError':
      return 'El navegador bloqueó el acceso a la cámara. Permítalo desde el icono de cámara de la barra de direcciones y pulse «Reintentar cámara».';
    case 'NotReadableError':
    case 'AbortError':
      return 'La cámara está en uso por otra aplicación o pestaña (Zoom, Teams, la app Cámara u otra pestaña con el vestidor abierto). Ciérrela y pulse «Reintentar cámara».';
    case 'NotFoundError':
    case 'OverconstrainedError':
      return 'No se encontró una cámara compatible en este equipo.';
    default:
      return `No se pudo abrir la cámara (${nombre}).`;
  }
}

@Component({
  selector: 'app-modal-vestidor-ar',
  standalone: true,
  imports: [ImportePipe, CommonModule],
  templateUrl: './modal-vestidor-ar.component.html',
  styleUrls: ['./modal-vestidor-ar.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ModalVestidorArComponent implements OnInit, OnDestroy {
  private readonly vestidorService: VestidorService = inject(VestidorService);

  // --- Inputs ---
  readonly producto = input.required<ProductoDetalle>();
  readonly variante = input<VarianteDetalle | null>(null);

  // --- Outputs ---
  @Output() readonly cerrar = new EventEmitter<void>();
  @Output() readonly anadirAlCarrito = new EventEmitter<void>();
  @Output() readonly reservarBoutique = new EventEmitter<void>();

  @ViewChild('videoElement') readonly videoRef?: ElementRef<HTMLVideoElement>;
  @ViewChild('remoteVideoElement') readonly remoteVideoRef?: ElementRef<HTMLVideoElement>;
  @ViewChild('canvasSnapshot') readonly canvasRef?: ElementRef<HTMLCanvasElement>;

  // --- Signals de Estado ---
  readonly motorActivo = signal<TipoMotorVestidor>('local');
  readonly camaraActiva = signal<boolean>(false);
  readonly permisoCamaraDenegado = signal<boolean>(false);
  /** Causa concreta del fallo de la cámara, visible en el panel lateral (la prenda tapa el visor). */
  readonly mensajeCamara = signal<string | null>(null);
  readonly conectandoIA = signal<boolean>(false);
  readonly streamingIA = signal<boolean>(false);
  readonly mensajeAviso = signal<string | null>(null);
  readonly errorFallback = signal<string | null>(null);

  // Calibración manual en Motor 1
  readonly escalaPrenda = signal<number>(100);
  readonly offsetVertical = signal<number>(35);
  readonly opacidadPrenda = signal<number>(95);

  // Temporizador de duración de sesión y límite IA (60 s)
  readonly segundosTranscurridos = signal<number>(0);
  readonly segundosRestantesIA = signal<number>(60);
  readonly capturaGenerada = signal<string | null>(null);

  private mediaStream: MediaStream | null = null;
  private timerSesionId: any = null;
  private timerIAId: any = null;
  private timeoutStreamingId: any = null;
  private sesionRegistrada = false;
  private rtClient: RealTimeClient | null = null;
  /**
   * Identifica la conexión en curso. `client.realtime.connect()` no se puede abortar: si el usuario
   * cierra, conmuta o vence el temporizador mientras sigue en vuelo, se incrementa este contador y la
   * conexión que llegue tarde se reconoce como huérfana y se cierra al instante.
   */
  private intentoConexionIA = 0;

  // --- Computeds ---
  readonly recursoVisualPrenda = computed(() => {
    const prod = this.producto();
    return prod.modelo_ar_url || prod.imagen_principal;
  });

  readonly tieneModeloArUrl = computed(() => {
    const ar = this.producto().modelo_ar_url;
    return !!ar && ar.trim().length > 0;
  });

  readonly etiquetaMotor = computed(() => {
    return this.motorActivo() === 'local'
      ? 'MOTOR 1 · LOCAL EN DISPOSITIVO (EDGE)'
      : 'MOTOR 2 · REALISTA STREAMING IA (DECART)';
  });

  ngOnInit(): void {
    this.iniciarContadorSesion();
    this.iniciarCamaraLocal();
  }

  ngOnDestroy(): void {
    this.desconectarDecart();
    this.limpiarTemporizadores();
    this.detenerCamara();
    if (!this.sesionRegistrada) {
      this.registrarSesionSilenciosa(false);
    }
  }

  /**
   * Intenta acceder a la cámara web del cliente para alimentar el video de fondo.
   */
  async iniciarCamaraLocal(): Promise<void> {
    if (typeof navigator === 'undefined' || !('mediaDevices' in navigator)) {
      this.camaraActiva.set(false);
      return;
    }

    try {
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'user' },
        audio: false,
      });

      this.camaraActiva.set(true);
      this.permisoCamaraDenegado.set(false);
      this.mensajeCamara.set(null);

      setTimeout(() => {
        if (this.videoRef?.nativeElement && this.mediaStream) {
          this.videoRef.nativeElement.srcObject = this.mediaStream;
          this.videoRef.nativeElement.play().catch(() => {});
        }
      }, 100);
    } catch (error) {
      this.camaraActiva.set(false);
      this.permisoCamaraDenegado.set(true);
      // El nombre del DOMException distingue un permiso bloqueado de una cámara ocupada por otra
      // aplicación o pestaña; antes se descartaba y el visor quedaba en negro sin explicación.
      const nombre = (error as { name?: string } | null)?.name ?? 'Error';
      console.error('[VESTIDOR] No se pudo abrir la cámara:', nombre, error);
      this.mensajeCamara.set(describirErrorCamara(nombre));
    }
  }

  /** Vuelve a pedir la cámara tras resolver la causa (permiso concedido o app que la ocupaba cerrada). */
  async reintentarCamara(): Promise<void> {
    this.detenerCamara();
    this.mensajeCamara.set(null);
    this.permisoCamaraDenegado.set(false);
    await this.iniciarCamaraLocal();
  }

  detenerCamara(): void {
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => track.stop());
      this.mediaStream = null;
    }
    this.camaraActiva.set(false);
  }

  /**
   * Conmuta a Motor 1 (Local): Edge processing en navegador sin costo.
   */
  conmutarAMotorLocal(): void {
    this.desconectarDecart();
    this.detenerTimerIA();
    this.streamingIA.set(false);
    this.conectandoIA.set(false);
    this.motorActivo.set('local');
    this.errorFallback.set(null);
    this.mensajeAviso.set('Modo Local (Edge) activado. Procesamiento 100% privado en su equipo.');
    setTimeout(() => this.mensajeAviso.set(null), 3500);
  }

  /**
   * Solicita token efímero y conecta con Decart Lucy VTON usando @decartai/sdk oficial.
   * Si falla la red, la API o WebRTC, conmuta automáticamente a Motor 1 (Fallback).
   *
   * El primer token se pide antes de conectar para que un 401/503 del backend active el fallback
   * de inmediato; las marcaciones posteriores (reintentos del SDK) piden uno nuevo vía
   * `apiKeyProvider`, porque el token caduca a los 60 s.
   */
  async activarModoRealistaIA(): Promise<void> {
    if (this.streamingIA() || this.conectandoIA()) return;

    const intento = ++this.intentoConexionIA;
    this.conectandoIA.set(true);
    this.errorFallback.set(null);

    this.vestidorService.obtenerTokenDecart().subscribe({
      next: (tokenData: TokenVestidorDecartOut) => {
        void this.conectarDecart(intento, tokenData.token);
      },
      error: (err: any) => {
        if (!this.esIntentoVigente(intento)) return;
        // FALLBACK AUTOMÁTICO A MOTOR 1 LOCAL
        if (err?.status === 401) {
          this.ejecutarFallbackMotorLocal(
            'Inicie sesión con su cuenta para acceder al modo realista con IA (Decart Lucy VTON). Continuando en Motor Local.'
          );
        } else {
          this.ejecutarFallbackMotorLocal(
            'El servicio realista con IA de Decart no se encuentra disponible o agotó créditos de prueba. Conmutando automáticamente al Motor Local.'
          );
        }
      },
    });
  }

  /** Carga diferida del SDK de Decart; aislada en un método para poder sustituirla en las pruebas. */
  protected cargarSdkDecart(): Promise<typeof import('@decartai/sdk')> {
    return import('@decartai/sdk');
  }

  private async conectarDecart(intento: number, tokenInicial: string): Promise<void> {
    // Entorno sin soporte de MediaDevices (ej. pruebas unitarias en JSDOM)
    const tieneMedia = typeof navigator !== 'undefined' && 'mediaDevices' in navigator;
    if (!tieneMedia) {
      this.conectandoIA.set(false);
      this.streamingIA.set(true);
      this.motorActivo.set('ia');
      this.segundosRestantesIA.set(LIMITE_SESION_IA_SEGUNDOS);
      this.iniciarTimerIA();
      return;
    }

    try {
      // En navegador real: asegurar cámara local activa
      if (!this.mediaStream) {
        await this.iniciarCamaraLocal();
      }
      if (!this.esIntentoVigente(intento)) return;
      if (!this.mediaStream) {
        this.ejecutarFallbackMotorLocal('Se requiere cámara activa para el Motor 2. Continuando en Motor Local.');
        return;
      }

      const { createDecartClient, createConsoleLogger, models } = await this.cargarSdkDecart();

      // Token por marcación: el primero es el ya emitido; cada reintento pide uno nuevo al backend.
      // Con un token fijo, cualquier re-marcación pasados 60 s fallaba con TOKEN_EXPIRED.
      let tokenPendiente: string | null = tokenInicial;
      const client = createDecartClient({
        apiKeyProvider: async () => {
          if (tokenPendiente) {
            const token = tokenPendiente;
            tokenPendiente = null;
            return token;
          }
          const nuevo = await firstValueFrom(this.vestidorService.obtenerTokenDecart());
          return nuevo.token;
        },
        // Traza cada intento, reintento y su causa en la consola como `[DecartSDK] ...`.
        logger: createConsoleLogger('info'),
      });
      const model = models.realtime('lucy-vton-3.6');

      // Chequeo previo (≤ 5 s, sin coste): si la red no deja pasar WebRTC no tiene sentido hacer
      // esperar al cliente 45 s; la documentación de Decart recomienda ocultar el modo en ese caso.
      const informe = await client.realtime.checkConnectivity();
      console.info('[DECART] Chequeo de conectividad:', informe);
      if (!this.esIntentoVigente(intento)) return;
      if (informe.quality === 'critical') {
        const motivos = informe.reasons.length ? `: ${informe.reasons.join('; ')}` : '';
        this.ejecutarFallbackMotorLocal(
          `Su red no permite el vídeo en tiempo real con Decart (transporte ${informe.metrics.transport}${motivos}). ` +
            'Conmutando al Motor Local.'
        );
        return;
      }

      // La cámara debe entregar exactamente la resolución y la tasa de cuadros del modelo.
      await this.ajustarCamaraAlModelo(model);
      if (!this.esIntentoVigente(intento)) return;

      // Imagen de referencia: la prenda sola (modelo_ar_url) sobre fondo blanco.
      const prendaDataUrl = await this.obtenerPrendaComoDataUrl();
      if (!this.esIntentoVigente(intento)) return;

      this.iniciarTimeoutEsperaStreaming(intento);

      // Todo lo que deba observarse MIENTRAS connect() está en curso va como callback de opciones:
      // los eventos de `rt.on(...)` quedan retenidos por el SDK hasta que connect() resuelve.
      const rt = await client.realtime.connect(this.mediaStream, {
        model,
        mirror: 'auto',
        resolution: '720p',
        retries: REINTENTOS_CONEXION_SDK,
        capacityRetryBudgetMs: PRESUPUESTO_ESPERA_CAPACIDAD_MS,
        onRemoteStream: (remoteStream: MediaStream) => {
          if (!this.esIntentoVigente(intento)) return;
          this.mostrarStreamRemoto(remoteStream);
        },
        onConnectionChange: (state: ConnectionState) => {
          console.log('[DECART] Estado de conexión:', state);
          // Durante la conexión, `disconnected` solo llega al agotar los reintentos y connect()
          // rechaza a continuación: el catch muestra la causa. Aquí solo se atiende la caída
          // de una sesión que ya estaba emitiendo.
          if (state === 'disconnected' && this.streamingIA() && this.esIntentoVigente(intento)) {
            this.ejecutarFallbackMotorLocal(
              'Se perdió la conexión con Decart Lucy VTON. Conmutando al Motor Local.'
            );
          }
        },
        onQueuePosition: ({ position, queueSize }: QueuePosition) => {
          console.info('[DECART] En cola:', position, 'de', queueSize);
          if (this.esIntentoVigente(intento)) {
            this.mensajeAviso.set(`Decart está ocupado: posición ${position} de ${queueSize} en la cola.`);
          }
        },
        onCapacityWait: ({ retryAfterMs, attempt }: CapacityWait) => {
          console.warn('[DECART] Sin capacidad; reintento', attempt, 'en', retryAfterMs, 'ms');
          if (this.esIntentoVigente(intento)) {
            this.mensajeAviso.set('Decart no tiene capacidad disponible en este momento. Reintentando…');
          }
        },
        initialState: {
          prompt: {
            // Patrón de la guía de Decart («Substitute the current … with …»). Se deja enhance:
            // el prompt solo sitúa la prenda; el detalle lo aporta la imagen de referencia.
            text: construirPromptVton(this.producto().nombre, this.producto().categoria_nombre),
            enhance: true,
          },
          image: prendaDataUrl || undefined,
        },
      });

      // Si el usuario cerró, conmutó o venció el temporizador mientras connect() seguía en vuelo,
      // esta sesión ya no tiene dueño: se cierra al instante para no generar (ni facturar) sin vista.
      if (!this.esIntentoVigente(intento)) {
        rt.disconnect();
        return;
      }
      this.rtClient = rt;

      rt.on('error', (err) => {
        console.error('[DECART ERROR]', err);
        this.ejecutarFallbackMotorLocal(
          `Error en la transmisión de Decart Lucy VTON (${err.code}). Conmutando al Motor Local.`
        );
      });

      rt.on('sessionEnded', (ended) => {
        console.warn('[DECART SESSION ENDED]', ended);
        const motivo = ended?.reason === 'insufficient_credits'
          ? 'Créditos de Decart agotados.'
          : ended?.reason === 'moderation_violation'
          ? 'La imagen no superó la moderación de contenido.'
          : 'Sesión finalizada por el servicio Decart.';
        this.ejecutarFallbackMotorLocal(`${motivo} Conmutando al Motor Local.`);
      });

      rt.on('diagnostic', (diag) => {
        console.log('[DECART DIAGNOSTIC]', diag);
      });
    } catch (err) {
      if (!this.esIntentoVigente(intento)) return;
      console.warn('[DECART] Fallo al conectar streaming WebRTC:', err);
      const codigo = (err as { code?: string } | null)?.code;
      this.ejecutarFallbackMotorLocal(
        `No fue posible establecer la sesión de streaming WebRTC con Decart Lucy VTON${codigo ? ` (${codigo})` : ''}. ` +
          'Conmutando al Motor Local. Consulte la consola del navegador ([DecartSDK]) para ver la causa.'
      );
    }
  }

  private mostrarStreamRemoto(remoteStream: MediaStream): void {
    this.limpiarTimeoutEsperaStreaming();
    const video = this.remoteVideoRef?.nativeElement;
    if (video) {
      video.srcObject = remoteStream;
      video.muted = true;
      video.playsInline = true;

      const activarVistaVideo = () => {
        console.log('[DECART] Video de Lucy VTON activo:', video.videoWidth, 'x', video.videoHeight);
        this.conectandoIA.set(false);
        this.streamingIA.set(true);
        this.motorActivo.set('ia');
      };

      video.onloadeddata = activarVistaVideo;
      video.onplaying = activarVistaVideo;

      video.play().catch((e) => console.warn('[DECART] Error al reproducir video:', e));

      // Respaldo para asegurar visualización si onloadeddata se retrasa
      setTimeout(() => {
        if (this.conectandoIA()) {
          activarVistaVideo();
        }
      }, 3500);
    } else {
      this.conectandoIA.set(false);
      this.streamingIA.set(true);
      this.motorActivo.set('ia');
    }

    this.segundosRestantesIA.set(LIMITE_SESION_IA_SEGUNDOS);

    this.mensajeAviso.set(
      `Streaming Decart Lucy VTON establecido. Límite de control de costes: ${LIMITE_SESION_IA_SEGUNDOS} s.`
    );
    setTimeout(() => this.mensajeAviso.set(null), 4000);

    this.iniciarTimerIA();
  }

  private esIntentoVigente(intento: number): boolean {
    return intento === this.intentoConexionIA;
  }

  /**
   * Imagen de referencia para Lucy VTON: la prenda SOLA (`modelo_ar_url`). Nunca la foto de catálogo
   * (`imagen_principal`), en la que una modelo viste la prenda: la documentación de Decart lo señala
   * como error común. Se aplana sobre fondo blanco, porque la transparencia de un PNG no es el «fondo
   * liso» que pide el modelo, y se exporta como JPEG. Sin recurso de prenda se devuelve `undefined`
   * y Decart trabaja solo con el prompt, que también es un modo admitido.
   */
  private async obtenerPrendaComoDataUrl(): Promise<string | undefined> {
    const url = this.producto().modelo_ar_url?.trim();
    if (!url) {
      console.warn('[DECART] La prenda no tiene modelo_ar_url: se envía solo el prompt.');
      return undefined;
    }

    try {
      const imagen = await this.cargarImagen(url);
      const ancho = imagen.naturalWidth;
      const alto = imagen.naturalHeight;
      if (Math.min(ancho, alto) < LADO_MINIMO_REFERENCIA_PX) {
        console.warn(
          `[DECART] La imagen de la prenda mide ${ancho}x${alto}; Decart recomienda al menos ` +
            `${LADO_MINIMO_REFERENCIA_PX}x${LADO_MINIMO_REFERENCIA_PX} px.`
        );
      }

      const canvas = document.createElement('canvas');
      canvas.width = ancho;
      canvas.height = alto;
      const ctx = canvas.getContext('2d');
      if (!ctx) return undefined;
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, ancho, alto);
      ctx.drawImage(imagen, 0, 0);
      return canvas.toDataURL('image/jpeg', 0.92);
    } catch (error) {
      console.warn('[DECART] No se pudo preparar la imagen de la prenda; se envía solo el prompt.', error);
      return undefined;
    }
  }

  private cargarImagen(url: string): Promise<HTMLImageElement> {
    return new Promise((resolve, reject) => {
      const imagen = new Image();
      imagen.crossOrigin = 'anonymous';
      imagen.onload = () => resolve(imagen);
      imagen.onerror = () => reject(new Error(`No se pudo cargar la imagen de la prenda: ${url}`));
      imagen.src = url;
    });
  }

  /**
   * Ajusta la pista de vídeo ya abierta a la resolución y la tasa de cuadros del modelo. La cámara
   * se abre antes de cargar el SDK (Motor 1), así que no puede pedirlas en `getUserMedia`.
   */
  private async ajustarCamaraAlModelo(model: Pick<ModelDefinition, 'width' | 'height' | 'fps'>): Promise<void> {
    const pista = this.mediaStream?.getVideoTracks()[0];
    if (!pista) return;
    try {
      await pista.applyConstraints({
        width: { ideal: model.width },
        height: { ideal: model.height },
        frameRate: model.fps,
      });
    } catch (error) {
      console.warn('[DECART] La cámara no admite las restricciones del modelo; se usa su configuración actual.', error);
    }
  }

  private iniciarTimeoutEsperaStreaming(intento: number): void {
    this.limpiarTimeoutEsperaStreaming();
    this.timeoutStreamingId = setTimeout(() => {
      if (this.esIntentoVigente(intento) && !this.streamingIA()) {
        console.warn('[DECART] Timeout esperando señal WebRTC de Decart.');
        this.ejecutarFallbackMotorLocal(
          'Tiempo de espera excedido al conectar la señal de video de Decart Lucy VTON. Conmutando al Motor Local. ' +
            'Consulte la consola del navegador ([DecartSDK]) para ver la causa.'
        );
      }
    }, TIMEOUT_CONEXION_IA_MS);
  }

  private limpiarTimeoutEsperaStreaming(): void {
    if (this.timeoutStreamingId) {
      clearTimeout(this.timeoutStreamingId);
      this.timeoutStreamingId = null;
    }
  }

  private ejecutarFallbackMotorLocal(mensaje: string): void {
    this.desconectarDecart();
    this.detenerTimerIA();
    this.conectandoIA.set(false);
    this.streamingIA.set(false);
    this.motorActivo.set('local');
    this.errorFallback.set(mensaje);
  }

  /**
   * Cierra la sesión activa y anula cualquier conexión aún en vuelo: la que resuelva después
   * se detecta como huérfana en `conectarDecart` y se desconecta al instante.
   */
  private desconectarDecart(): void {
    this.intentoConexionIA++;
    this.limpiarTimeoutEsperaStreaming();
    if (this.rtClient) {
      try {
        this.rtClient.disconnect();
      } catch {
        // Ignorar excepciones al cerrar conexión WebRTC
      }
      this.rtClient = null;
    }
    if (this.remoteVideoRef?.nativeElement) {
      this.remoteVideoRef.nativeElement.srcObject = null;
    }
  }

  private iniciarTimerIA(): void {
    this.detenerTimerIA();
    this.timerIAId = setInterval(() => {
      const rest = this.segundosRestantesIA() - 1;
      this.segundosRestantesIA.set(rest);

      if (rest <= 0) {
        this.detenerTimerIA();
        this.desconectarDecart();
        this.streamingIA.set(false);
        this.motorActivo.set('local');
        this.mensajeAviso.set(
          'Límite de tiempo en modo realista alcanzado (60 s por control de costos). Conmutando a vestidor local.'
        );
      }
    }, 1000);
  }

  private detenerTimerIA(): void {
    if (this.timerIAId) {
      clearInterval(this.timerIAId);
      this.timerIAId = null;
    }
  }

  private iniciarContadorSesion(): void {
    this.timerSesionId = setInterval(() => {
      this.segundosTranscurridos.update((s) => s + 1);
    }, 1000);
  }

  private limpiarTemporizadores(): void {
    if (this.timerSesionId) {
      clearInterval(this.timerSesionId);
      this.timerSesionId = null;
    }
    this.detenerTimerIA();
  }

  /**
   * Genera captura fotográfica de la silueta/prenda superpuesta.
   */
  capturarFoto(): void {
    const canvas = this.canvasRef?.nativeElement;
    const video = this.videoRef?.nativeElement;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = 640;
    canvas.height = 800;

    // Fondo del video o color neutro de atelier
    if (this.camaraActiva() && video && video.videoWidth) {
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    } else {
      ctx.fillStyle = '#171717';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
    }

    const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
    this.capturaGenerada.set(dataUrl);
    this.mensajeAviso.set('Fotografía capturada. Se guardará con su interacción.');
    setTimeout(() => this.mensajeAviso.set(null), 3000);
  }

  // --- Calibradores Manuales ---
  actualizarEscala(e: Event): void {
    const val = Number((e.target as HTMLInputElement).value);
    this.escalaPrenda.set(val);
  }

  actualizarOffsetVertical(e: Event): void {
    const val = Number((e.target as HTMLInputElement).value);
    this.offsetVertical.set(val);
  }

  actualizarOpacidad(e: Event): void {
    const val = Number((e.target as HTMLInputElement).value);
    this.opacidadPrenda.set(val);
  }

  // --- Acciones Comerciales y Cierre ---
  onAnadirABolsaClick(): void {
    this.registrarSesionSilenciosa(true);
    this.anadirAlCarrito.emit();
    this.onCerrarClick();
  }

  onReservarBoutiqueClick(): void {
    this.registrarSesionSilenciosa(true);
    this.reservarBoutique.emit();
    this.onCerrarClick();
  }

  onCerrarClick(): void {
    this.desconectarDecart();
    this.detenerCamara();
    this.limpiarTemporizadores();
    if (!this.sesionRegistrada) {
      this.registrarSesionSilenciosa(false);
    }
    this.cerrar.emit();
  }

  private registrarSesionSilenciosa(generoInteres: boolean): void {
    this.sesionRegistrada = true;
    const duracion = Math.max(1, this.segundosTranscurridos());

    this.vestidorService
      .registrarSesion({
        id_producto: this.producto().id_producto,
        dispositivo: 'web',
        motor: this.motorActivo(),
        duracion_segundos: duracion,
        resultado_url: this.capturaGenerada() || undefined,
        genero_interes: generoInteres,
      })
      .subscribe({
        next: () => {},
        error: () => {},
      });
  }
}
