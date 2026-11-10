import { DestroyRef, Injectable, inject, signal } from '@angular/core';
import { DOCUMENT } from '@angular/common';

/**
 * Estado de la conexión del navegador (RNF15). `navigator.onLine` solo dice si hay una red: la
 * sincronización trata además cualquier fallo de red como «sin conexión» y reintenta (CU19 A1).
 */
@Injectable({ providedIn: 'root' })
export class ConectividadService {
  private readonly ventana = inject(DOCUMENT).defaultView;

  readonly enLinea = signal<boolean>(this.ventana?.navigator?.onLine ?? true);

  constructor() {
    const ventana = this.ventana;
    if (!ventana) return;
    const alConectar = () => this.enLinea.set(true);
    const alDesconectar = () => this.enLinea.set(false);
    ventana.addEventListener('online', alConectar);
    ventana.addEventListener('offline', alDesconectar);
    inject(DestroyRef).onDestroy(() => {
      ventana.removeEventListener('online', alConectar);
      ventana.removeEventListener('offline', alDesconectar);
    });
  }
}
