/**
 * Servicio de Reconocimiento de Voz mediante Web Speech API y Angular Signals.
 * Caso de Uso [CU31]: Generar reportes ejecutivos y consultas por voz.
 */

import { Injectable, signal, computed } from '@angular/core';

// Declaraciones de tipos para navegadores compatibles con Web Speech API
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

@Injectable({
  providedIn: 'root',
})
export class VozReconocimientoService {
  private recognition: any = null;
  private readonly _escuchando = signal<boolean>(false);
  private readonly _transcripcion = signal<string>('');
  private readonly _errorVoz = signal<string | null>(null);
  private readonly _soportaVoz = signal<boolean>(false);
  private readonly _idioma = signal<string>('es-BO');

  // Senales publicas de solo lectura
  readonly escuchando = computed(() => this._escuchando());
  readonly transcripcion = computed(() => this._transcripcion());
  readonly errorVoz = computed(() => this._errorVoz());
  readonly soportaVoz = computed(() => this._soportaVoz());
  readonly idioma = computed(() => this._idioma());

  constructor() {
    this.inicializarReconocimiento();
  }

  private inicializarReconocimiento(): void {
    if (typeof window === 'undefined') {
      this._soportaVoz.set(false);
      return;
    }

    const SpeechRecognitionClass =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (SpeechRecognitionClass) {
      this._soportaVoz.set(true);
      try {
        this.recognition = new SpeechRecognitionClass();
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.lang = this._idioma();

        this.recognition.onstart = () => {
          this._escuchando.set(true);
          this._errorVoz.set(null);
        };

        this.recognition.onresult = (event: any) => {
          let textoAcumulado = '';
          for (let i = event.resultIndex; i < event.results.length; i++) {
            const resultado = event.results[i];
            if (resultado && resultado[0]) {
              textoAcumulado += resultado[0].transcript;
            }
          }
          if (textoAcumulado) {
            this._transcripcion.set(textoAcumulado);
          }
        };

        this.recognition.onerror = (event: any) => {
          const mensaje = event?.error || 'Error desconocido en el reconocimiento de voz';
          this._errorVoz.set(mensaje);
          this._escuchando.set(false);
        };

        this.recognition.onend = () => {
          this._escuchando.set(false);
        };
      } catch (err: any) {
        this._soportaVoz.set(false);
        this._errorVoz.set('Fallo al inicializar el motor de reconocimiento por voz.');
      }
    } else {
      this._soportaVoz.set(false);
      this._errorVoz.set('El navegador no cuenta con soporte para Web Speech API.');
    }
  }

  cambiarIdioma(idioma: 'es-BO' | 'es-ES' | 'es-419'): void {
    this._idioma.set(idioma);
    if (this.recognition) {
      this.recognition.lang = idioma;
    }
  }

  iniciarEscucha(): void {
    if (!this._soportaVoz()) {
      this._errorVoz.set('Reconocimiento por voz no soportado en este navegador.');
      return;
    }

    if (this._escuchando()) {
      return;
    }

    this._errorVoz.set(null);
    this._transcripcion.set('');

    try {
      if (this.recognition) {
        this.recognition.lang = this._idioma();
        this.recognition.start();
      }
    } catch (err: any) {
      this._errorVoz.set('No se pudo iniciar el microfono o la escucha activa.');
      this._escuchando.set(false);
    }
  }

  detenerEscucha(): void {
    if (this.recognition && this._escuchando()) {
      try {
        this.recognition.stop();
      } catch (err) {
        // Ignorar si ya estaba detenido
      }
      this._escuchando.set(false);
    }
  }

  reiniciar(): void {
    this.detenerEscucha();
    this._transcripcion.set('');
    this._errorVoz.set(null);
  }

  asignarTextoManual(texto: string): void {
    this._transcripcion.set(texto);
    this._errorVoz.set(null);
  }
}
