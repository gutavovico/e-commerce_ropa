import { ChangeDetectionStrategy, Component, OnInit, computed, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { RouterLink } from '@angular/router';

import { ImportePipe } from '../../../../core/tenant/moneda';
import { LoginService } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import {
  ConflictoDetalle,
  ConflictoResumen,
  ConflictosService,
  EstadoCierre,
} from '../servicios/conflictos.service';

export const TIPO_CONFLICTO: Partial<Record<string, string>> = {
  stock_insuficiente: 'Stock insuficiente',
  precio_modificado: 'Precio modificado',
  producto_inactivo: 'Producto inactivo',
  sucursal_inactiva: 'Sucursal inactiva',
  suscripcion_no_vigente: 'Suscripción no vigente',
  antiguedad_excedida: 'Antigüedad excedida',
};

export const ESTADO_CONFLICTO: Partial<Record<string, string>> = {
  pendiente: 'Pendiente',
  reembolso_pendiente: 'Reembolso pendiente',
  resuelto: 'Resuelto',
};

type Filtro = 'pendiente' | 'reembolso_pendiente' | 'resuelto' | 'todos';

/**
 * P2-CU20 · Resolver conflictos de sincronización (`/admin/conflictos`). Compras pagadas que el
 * servidor no pudo aceptar al sincronizar: se revisan, se acepta su reembolso y el administrador
 * procesa los reembolsos al cierre del mes (decisión D2). El encargado solo ve sus sucursales (A2).
 */
@Component({
  selector: 'app-conflictos-admin',
  standalone: true,
  imports: [DatePipe, RouterLink, ImportePipe],
  templateUrl: './conflictos-admin.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ConflictosAdminComponent implements OnInit {
  private readonly servicio = inject(ConflictosService);
  private readonly login = inject(LoginService);

  protected readonly esAdmin = this.login.esAdmin;
  protected readonly tipos = TIPO_CONFLICTO;
  protected readonly estados = ESTADO_CONFLICTO;

  protected readonly filtro = signal<Filtro>('pendiente');
  protected readonly conflictos = signal<ConflictoResumen[]>([]);
  protected readonly cargando = signal(false);
  protected readonly error = signal<string | null>(null);
  protected readonly mensaje = signal<string | null>(null);
  protected readonly detalle = signal<ConflictoDetalle | null>(null);
  protected readonly procesando = signal(false);
  protected readonly cierre = signal<EstadoCierre | null>(null);
  protected readonly confirmarAnticipado = signal(false);

  protected readonly porReembolsar = computed(() => this.cierre()?.reembolsos_pendientes ?? 0);

  ngOnInit(): void {
    this.cargar();
    if (this.esAdmin()) this.cargarCierre();
  }

  protected cambiarFiltro(filtro: Filtro): void {
    this.filtro.set(filtro);
    this.cargar();
  }

  protected cargar(): void {
    this.cargando.set(true);
    this.error.set(null);
    const filtro = this.filtro();
    this.servicio.listar(filtro === 'todos' ? undefined : filtro).subscribe({
      next: (lista) => {
        this.conflictos.set(lista);
        this.cargando.set(false);
      },
      error: (e: HttpErrorResponse) => {
        this.error.set(mensajeDeError(e));
        this.cargando.set(false);
      },
    });
  }

  protected abrir(id: number): void {
    this.mensaje.set(null);
    this.servicio.detalle(id).subscribe({
      next: (d) => this.detalle.set(d),
      error: (e: HttpErrorResponse) => this.error.set(mensajeDeError(e)),
    });
  }

  protected cerrarDetalle(): void {
    this.detalle.set(null);
  }

  protected aceptar(conflicto: ConflictoDetalle): void {
    this.procesando.set(true);
    this.servicio.aceptarReembolso(conflicto.id_conflicto).subscribe({
      next: (d) => {
        this.detalle.set(d);
        this.mensaje.set('Reembolso aceptado: el cliente fue avisado y se procesará al cierre del mes.');
        this.procesando.set(false);
        this.cargar();
        if (this.esAdmin()) this.cargarCierre();
      },
      error: (e: HttpErrorResponse) => {
        this.procesando.set(false);
        // A3: otro usuario lo resolvió antes; se informa y se actualiza la lista.
        this.mensaje.set(mensajeDeError(e));
        this.detalle.set(null);
        this.cargar();
      },
    });
  }

  protected procesarCierre(): void {
    const estado = this.cierre();
    if (!estado) return;
    if (!estado.es_ultimo_dia_del_mes && !this.confirmarAnticipado()) {
      this.confirmarAnticipado.set(true);
      return;
    }
    this.procesando.set(true);
    this.servicio.procesarCierre(!estado.es_ultimo_dia_del_mes).subscribe({
      next: (r) => {
        this.procesando.set(false);
        this.confirmarAnticipado.set(false);
        this.mensaje.set(
          `${r.forzado ? 'Cierre anticipado de prueba' : 'Cierre de mes'}: ${r.reembolsados} de ${r.procesados} reembolsos procesados` +
            (r.fallidos.length ? `; ${r.fallidos.length} fallaron y se reintentarán en el próximo cierre.` : '.')
        );
        this.cargar();
        this.cargarCierre();
      },
      error: (e: HttpErrorResponse) => {
        this.procesando.set(false);
        this.confirmarAnticipado.set(false);
        this.mensaje.set(mensajeDeError(e));
      },
    });
  }

  protected cancelarAnticipado(): void {
    this.confirmarAnticipado.set(false);
  }

  protected valor(dato: unknown): string {
    return dato === undefined || dato === null ? '—' : String(dato);
  }

  private cargarCierre(): void {
    this.servicio.estadoCierre().subscribe({
      next: (c) => this.cierre.set(c),
      error: () => this.cierre.set(null),
    });
  }
}

function mensajeDeError(e: HttpErrorResponse): string {
  if (e.status === 0) return 'Sin conexión con el servidor.';
  const detalle = e.error?.detail;
  if (typeof detalle === 'string') return detalle;
  if (e.status === 403) return 'No tienes permiso para esta acción.';
  if (e.status === 404) return 'El conflicto no existe o no pertenece a tus sucursales.';
  return 'No se pudo completar la operación. Inténtalo de nuevo.';
}
