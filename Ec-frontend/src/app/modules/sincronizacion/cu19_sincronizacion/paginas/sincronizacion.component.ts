import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { DatePipe, Location } from '@angular/common';
import { RouterLink } from '@angular/router';

import { RutaPortalPipe } from '../../../../core/tenant/ruta-portal.pipe';
import { SinConexionService } from '../../../../core/sin-conexion/sin-conexion.service';
import { AvisoDto, EstadoOperacion, OperacionLocal } from '../../../../core/sin-conexion/sin-conexion.models';

export const ETIQUETA_ESTADO: Record<EstadoOperacion, string> = {
  registrada_localmente: 'Registrada en el dispositivo',
  enviada: 'Enviada',
  confirmada: 'Confirmada',
  rechazada: 'Rechazada',
  en_conflicto: 'En revisión',
};

const ESTILO_ESTADO: Record<EstadoOperacion, string> = {
  registrada_localmente: 'bg-neutral-100 text-neutral-700',
  enviada: 'bg-sky-50 text-sky-800',
  confirmada: 'bg-emerald-50 text-emerald-800',
  rechazada: 'bg-red-50 text-red-800',
  en_conflicto: 'bg-amber-50 text-amber-900',
};

const NO_REGISTRADO =
  'Todavía no estás registrado en esta tienda. Regístrate con «Registrarme en esta tienda» para usarla sin conexión.';

const ETIQUETA_CONFLICTO: Record<string, string> = {
  pendiente: 'Pendiente de revisión por la tienda',
  reembolso_pendiente: 'Reembolso aceptado: se procesa al cierre del mes',
  resuelto: 'Reembolso procesado',
};

/**
 * P2-CU19 · Hoja «Sincronización» (`/{codigo}/sincronizacion`): estado de cada operación hecha sin
 * conexión, sincronización manual, descarga del catálogo y bandeja de avisos (decisión D1).
 */
@Component({
  selector: 'app-sincronizacion',
  standalone: true,
  imports: [DatePipe, RouterLink, RutaPortalPipe],
  templateUrl: './sincronizacion.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SincronizacionComponent implements OnInit {
  private readonly location = inject(Location);
  protected readonly servicio = inject(SinConexionService);

  protected readonly avisos = signal<AvisoDto[]>([]);
  protected readonly cargandoAvisos = signal(false);
  protected readonly mensaje = signal<string | null>(null);

  ngOnInit(): void {
    void this.cargarAvisos();
    if (this.servicio.enLinea()) void this.servicio.refrescarEstados().catch(() => undefined);
  }

  protected etiqueta(op: OperacionLocal): string {
    return ETIQUETA_ESTADO[op.estado];
  }

  protected estilo(op: OperacionLocal): string {
    return ESTILO_ESTADO[op.estado];
  }

  protected conflicto(op: OperacionLocal): string | null {
    return op.estadoConflicto ? (ETIQUETA_CONFLICTO[op.estadoConflicto] ?? op.estadoConflicto) : null;
  }

  protected async sincronizar(): Promise<void> {
    this.mensaje.set(null);
    if (!this.servicio.enLinea()) {
      this.mensaje.set('Sin conexión: se enviará al recuperarla.');
      return;
    }
    if (this.servicio.registradoEnTienda() === false) {
      this.mensaje.set(NO_REGISTRADO);
      return;
    }
    if (!this.servicio.preparado()) {
      this.mensaje.set('Este dispositivo aún no está preparado. Vuelve a entrar en la tienda con conexión.');
      return;
    }
    const ok = await this.servicio.sincronizar();
    this.mensaje.set(
      ok
        ? 'Sincronización completada.'
        : this.servicio.sesionExpirada()
          ? 'Tu sesión expiró. Inicia sesión de nuevo: tus reservas siguen guardadas.'
          : 'No se pudo sincronizar. Lo intentaremos de nuevo en unos minutos.'
    );
    await this.cargarAvisos();
  }

  protected async descargar(): Promise<void> {
    this.mensaje.set(null);
    if (this.servicio.registradoEnTienda() === false) {
      this.mensaje.set(NO_REGISTRADO);
      return;
    }
    try {
      await this.servicio.descargarCatalogo();
      this.mensaje.set(this.servicio.aviso() ?? 'Catálogo actualizado.');
    } catch {
      this.mensaje.set('No se pudo descargar el catálogo. Se conserva el anterior.');
    }
  }

  protected async marcarLeido(aviso: AvisoDto): Promise<void> {
    if (aviso.leido) return;
    try {
      await this.servicio.marcarAvisoLeido(aviso.id_aviso);
      this.avisos.update((lista) => lista.map((a) => (a.id_aviso === aviso.id_aviso ? { ...a, leido: true } : a)));
    } catch {
      // Sin red: se marcará la próxima vez.
    }
  }

  protected volver(): void {
    this.location.back();
  }

  private async cargarAvisos(): Promise<void> {
    // La bandeja es del cliente en esta tienda: sin registro el servidor respondería 403.
    if (!this.servicio.enLinea() || !this.servicio.clave() || this.servicio.registradoEnTienda() !== true) return;
    this.cargandoAvisos.set(true);
    try {
      this.avisos.set((await this.servicio.cargarAvisos()).avisos);
    } catch {
      // La bandeja necesita conexión; la lista de operaciones no.
    } finally {
      this.cargandoAvisos.set(false);
    }
  }
}
