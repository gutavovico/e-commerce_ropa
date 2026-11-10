import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, inject, input, signal } from '@angular/core';

import { EmpresaResumen } from '../../../superadmin/modelos/superadmin.model';
import { RespaldosService, nombreDeArchivo } from '../../servicios/respaldos.service';

/**
 * RNF18 · Pestaña «Respaldos» del panel del super administrador.
 *
 * Descarga un respaldo de datos de toda la plataforma o de una sola empresa (decisiones H2 y H3). El
 * automático diario y la restauración se hacen fuera de la web (GitHub Actions y
 * `scripts/restaurar_respaldo.py`), nunca sobre producción.
 */
@Component({
  selector: 'app-respaldos',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="bg-white border border-black/15 p-6 space-y-5">
      <div>
        <h2 class="text-sm uppercase tracking-[0.18em] font-semibold">Respaldo manual</h2>
        <p class="text-sm text-black/70 mt-1">
          Archivo SQL con los datos. Se restaura en una rama nueva de Neon con
          <code>scripts/restaurar_respaldo.py</code>, nunca sobre producción.
        </p>
      </div>

      <fieldset class="space-y-3">
        <legend class="text-[11px] uppercase tracking-widest text-black/70 mb-1">Alcance</legend>
        <label class="flex items-center gap-2 text-sm">
          <input type="radio" name="alcance-respaldo" id="alcance-plataforma" [checked]="idTenant() === null"
                 (change)="idTenant.set(null)" />
          Toda la plataforma
        </label>
        <label class="flex flex-wrap items-center gap-2 text-sm">
          <input type="radio" name="alcance-respaldo" id="alcance-empresa" [checked]="idTenant() !== null"
                 [disabled]="empresas().length === 0" (change)="idTenant.set(empresas()[0]?.id_tenant ?? null)" />
          Una empresa
          <select id="empresa-respaldo" class="border border-black/20 px-2 py-1 text-sm min-w-0 max-w-full"
                  [disabled]="idTenant() === null" (change)="idTenant.set(+$any($event.target).value)">
            @for (e of empresas(); track e.id_tenant) {
              <option [value]="e.id_tenant" [selected]="idTenant() === e.id_tenant">{{ e.nombre }} ({{ e.codigo }})</option>
            }
          </select>
        </label>
        <p class="text-xs text-black/60">
          El de una empresa lleva solo sus filas, sus empleados y sus clientes registrados, y los catálogos globales.
        </p>
      </fieldset>

      <button type="button" id="btn-descargar-respaldo" (click)="descargar()" [disabled]="descargando()"
              class="bg-black text-white text-xs uppercase tracking-[0.18em] px-5 py-3 disabled:opacity-40">
        {{ descargando() ? 'Generando…' : 'Descargar respaldo' }}
      </button>

      @if (resultado(); as r) {
        <p id="resultado-respaldo" class="text-sm bg-emerald-50 text-emerald-900 border border-emerald-200 px-3 py-2">
          Descargado {{ r.archivo }} · {{ r.tablas }} tablas · {{ r.filas }} filas.
        </p>
      }
      @if (error(); as e) {
        <p role="alert" id="error-respaldo" class="text-sm bg-rose-50 text-rose-800 border border-rose-200 px-3 py-2">{{ e }}</p>
      }
    </section>

    <section class="bg-white border border-black/15 p-6 space-y-2 text-sm text-black/80">
      <h2 class="text-sm uppercase tracking-[0.18em] font-semibold text-black">Respaldo automático</h2>
      <p>Cada día a las 03:00 (hora de Bolivia), toda la base, cifrada, en Cloudflare R2 durante 30 días.</p>
      <p>Se lanza o se restaura desde GitHub → Actions → «Respaldo de la base (RNF18)».</p>
    </section>
  `,
})
export class RespaldosComponent {
  private readonly servicio = inject(RespaldosService);

  readonly empresas = input<EmpresaResumen[]>([]);

  readonly idTenant = signal<number | null>(null);
  readonly descargando = signal(false);
  readonly resultado = signal<{ archivo: string; tablas: string; filas: string } | null>(null);
  readonly error = signal<string | null>(null);

  descargar(): void {
    this.descargando.set(true);
    this.resultado.set(null);
    this.error.set(null);
    this.servicio.descargar(this.idTenant()).subscribe({
      next: (respuesta) => {
        const archivo = nombreDeArchivo(respuesta.headers.get('Content-Disposition'));
        this.guardar(respuesta.body, archivo);
        this.resultado.set({
          archivo,
          tablas: respuesta.headers.get('X-Respaldo-Tablas') ?? '—',
          filas: respuesta.headers.get('X-Respaldo-Filas') ?? '—',
        });
        this.descargando.set(false);
      },
      error: (e: HttpErrorResponse) => void this.mostrarError(e),
    });
  }

  private guardar(contenido: Blob | null, archivo: string): void {
    if (!contenido) return;
    const url = URL.createObjectURL(contenido);
    const enlace = document.createElement('a');
    enlace.href = url;
    enlace.download = archivo;
    enlace.click();
    URL.revokeObjectURL(url);
  }

  /** Con `responseType: 'blob'` el error del servidor también llega como Blob. */
  private async mostrarError(e: HttpErrorResponse): Promise<void> {
    let mensaje = 'No se pudo generar el respaldo.';
    try {
      const texto = e.error instanceof Blob ? await e.error.text() : JSON.stringify(e.error);
      const detalle = (JSON.parse(texto) as { detail?: unknown }).detail;
      if (typeof detalle === 'string') mensaje = detalle;
    } catch {
      // se queda el mensaje genérico
    }
    this.error.set(mensaje);
    this.descargando.set(false);
  }
}
