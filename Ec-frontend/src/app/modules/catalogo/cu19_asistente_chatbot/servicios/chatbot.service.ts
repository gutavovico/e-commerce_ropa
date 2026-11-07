import { Injectable, inject, signal } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { catchError, finalize, of, tap } from 'rxjs';
import {
  InteraccionHistorialDto,
  MensajeBurbuja,
  MensajeChatbotPeticion,
  RespuestaChatbotDto,
} from '../modelos/chatbot.dto';

@Injectable({
  providedIn: 'root',
})
export class ChatbotService {
  private readonly http = inject(HttpClient);
  private readonly chatEndpoint = '/api/v1/asistente/chat';
  private readonly historialEndpoint = '/api/v1/asistente/historial';
  private readonly TOKEN_KEY = 'fashionstore_token';
  private readonly CHAT_MENSAJES_KEY = 'fashionstore_chat_mensajes';
  private readonly CHAT_SUGERENCIAS_KEY = 'fashionstore_chat_sugerencias';

  // --- Estado Reactivo con Signals ---
  readonly abierto = signal<boolean>(false);
  readonly cargando = signal<boolean>(false);
  readonly error = signal<string | null>(null);
  readonly mensajesNoLeidos = signal<boolean>(false);

  readonly sugerenciasRapidas = signal<string[]>([
    '¿Tienen vestidos de noche en Madrid?',
    '¿Cuáles son los horarios de atención?',
    '¿Cómo funciona el probador virtual?',
  ]);

  readonly mensajes = signal<MensajeBurbuja[]>([
    {
      id: 'bienvenida',
      emisor: 'asistente',
      texto:
        'Bienvenido a Fashion Store. Soy su asistente de estilismo personal de alta costura. ¿En qué puedo asesorarle hoy?',
      hora: this.formatearHora(new Date()),
    },
  ]);

  constructor() {
    this.recuperarSesion();
  }

  private formatearHora(fecha: Date): string {
    return fecha.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  private obtenerToken(): string | null {
    if (typeof window === 'undefined') {
      return null;
    }
    return (
      localStorage.getItem(this.TOKEN_KEY) ||
      sessionStorage.getItem(this.TOKEN_KEY)
    );
  }

  private getAuthHeaders(): HttpHeaders {
    const token = this.obtenerToken();
    let headers = new HttpHeaders({ 'Content-Type': 'application/json' });
    if (token) {
      headers = headers.set('Authorization', `Bearer ${token}`);
    }
    return headers;
  }

  private recuperarSesion(): void {
    if (typeof window === 'undefined') {
      return;
    }
    try {
      const guardados = sessionStorage.getItem(this.CHAT_MENSAJES_KEY);
      if (guardados) {
        const parsed = JSON.parse(guardados);
        if (Array.isArray(parsed) && parsed.length > 0) {
          this.mensajes.set(parsed);
        }
      }
      const sugerencias = sessionStorage.getItem(this.CHAT_SUGERENCIAS_KEY);
      if (sugerencias) {
        const parsedSug = JSON.parse(sugerencias);
        if (Array.isArray(parsedSug) && parsedSug.length > 0) {
          this.sugerenciasRapidas.set(parsedSug);
        }
      }
    } catch {
      // Ignorar errores de parseo
    }
  }

  private persistirSesion(): void {
    if (typeof window === 'undefined') {
      return;
    }
    try {
      sessionStorage.setItem(
        this.CHAT_MENSAJES_KEY,
        JSON.stringify(this.mensajes())
      );
      sessionStorage.setItem(
        this.CHAT_SUGERENCIAS_KEY,
        JSON.stringify(this.sugerenciasRapidas())
      );
    } catch {
      // Ignorar cuotas de storage
    }
  }

  alternarChat(): void {
    const nuevoEstado = !this.abierto();
    this.abierto.set(nuevoEstado);
    if (nuevoEstado) {
      this.mensajesNoLeidos.set(false);
    }
  }

  abrirChat(): void {
    this.abierto.set(true);
    this.mensajesNoLeidos.set(false);
  }

  cerrarChat(): void {
    this.abierto.set(false);
  }

  enviarMensaje(texto: string, idSucursalPreferida?: number | null): void {
    const trimmed = texto.trim();
    if (!trimmed || this.cargando()) {
      return;
    }

    const idUsuarioMsg = `usr-${Date.now()}`;
    const horaMsg = this.formatearHora(new Date());

    // 1. Agregar mensaje del usuario a la lista y persistir en la sesión activa
    this.mensajes.update((prev) => [
      ...prev,
      {
        id: idUsuarioMsg,
        emisor: 'usuario',
        texto: trimmed,
        hora: horaMsg,
      },
    ]);
    this.persistirSesion();

    this.cargando.set(true);
    this.error.set(null);

    const payload: MensajeChatbotPeticion = {
      mensaje: trimmed,
      canal: 'web',
      id_sucursal_preferida: idSucursalPreferida,
    };

    this.http
      .post<RespuestaChatbotDto>(this.chatEndpoint, payload, {
        headers: this.getAuthHeaders(),
      })
      .pipe(
        tap((res) => {
          this.mensajes.update((prev) => [
            ...prev,
            {
              id: `bot-${res.id_interaccion}`,
              emisor: 'asistente',
              texto: res.respuesta,
              hora: this.formatearHora(new Date()),
              productos: res.productos_sugeridos,
              sucursales: res.sucursales_sugeridas,
            },
          ]);

          if (res.sugerencias_rapidas && res.sugerencias_rapidas.length > 0) {
            this.sugerenciasRapidas.set(res.sugerencias_rapidas);
          }

          this.persistirSesion();

          if (!this.abierto()) {
            this.mensajesNoLeidos.set(true);
          }
        }),
        catchError(() => {
          this.error.set('No fue posible conectar con el asistente.');
          this.mensajes.update((prev) => [
            ...prev,
            {
              id: `err-${Date.now()}`,
              emisor: 'asistente',
              texto:
                'Disculpe la molestia, en este momento el servicio de asesoría remota experimenta una pausa. Por favor, explore nuestro catálogo de alta costura o visite una de nuestras boutiques en Madrid o Santa Cruz.',
              hora: this.formatearHora(new Date()),
            },
          ]);
          this.persistirSesion();

          if (!this.abierto()) {
            this.mensajesNoLeidos.set(true);
          }
          return of(null);
        }),
        finalize(() => {
          this.cargando.set(false);
        })
      )
      .subscribe();
  }

  cargarHistorial(): void {
    const token = this.obtenerToken();
    if (!token) {
      return;
    }

    this.http
      .get<InteraccionHistorialDto[]>(`${this.historialEndpoint}?limite=10`, {
        headers: this.getAuthHeaders(),
      })
      .pipe(
        tap((historial) => {
          if (!historial || historial.length === 0) {
            return;
          }

          const burbujas: MensajeBurbuja[] = [
            {
              id: 'bienvenida',
              emisor: 'asistente',
              texto:
                'Bienvenido de nuevo a Fashion Store. Aquí tiene el registro de sus consultas recientes.',
              hora: this.formatearHora(new Date()),
            },
          ];

          for (const item of historial) {
            const fecha = new Date(item.creado_en);
            const hora = this.formatearHora(isNaN(fecha.getTime()) ? new Date() : fecha);

            burbujas.push({
              id: `hist-usr-${item.id_interaccion}`,
              emisor: 'usuario',
              texto: item.mensaje_usuario,
              hora: hora,
            });

            if (item.respuesta_ia) {
              burbujas.push({
                id: `hist-bot-${item.id_interaccion}`,
                emisor: 'asistente',
                texto: item.respuesta_ia,
                hora: hora,
              });
            }
          }

          this.mensajes.set(burbujas);
          this.persistirSesion();
        }),
        catchError(() => of(null))
      )
      .subscribe();
  }

  /// Reinicia la conversación exclusivamente al pulsar el botón de recarga (refresh) o al cerrar sesión
  limpiarConversacion(): void {
    if (typeof window !== 'undefined') {
      try {
        sessionStorage.removeItem(this.CHAT_MENSAJES_KEY);
        sessionStorage.removeItem(this.CHAT_SUGERENCIAS_KEY);
      } catch {
        // Ignorar
      }
    }

    this.mensajes.set([
      {
        id: 'bienvenida',
        emisor: 'asistente',
        texto:
          'Bienvenido a Fashion Store. Soy su asistente de estilismo personal de alta costura. ¿En qué puedo asesorarle hoy?',
        hora: this.formatearHora(new Date()),
      },
    ]);
    this.sugerenciasRapidas.set([
      '¿Tienen vestidos de noche en Madrid?',
      '¿Cuáles son los horarios de atención?',
      '¿Cómo funciona el probador virtual?',
    ]);
    this.mensajesNoLeidos.set(false);
    this.error.set(null);
  }
}
