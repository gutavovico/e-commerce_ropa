import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { TenantService } from './tenant.service';
import { LoginService } from '../../modules/autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';

/**
 * P2-CU02 · «Registrarme en esta tienda» (decisión A8, solo web).
 *
 * Aparece en el portal cuando un cliente con sesión no está registrado en la tienda, y también cuando
 * una operación (bolsa, reserva, compra) responde 403 CLIENTE_NO_REGISTRADO. No crea otra cuenta:
 * registra la cuenta actual en la tienda (`POST /api/v1/mis-empresas` con `X-Tenant`).
 */
@Component({
  selector: 'app-registro-en-tienda',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (visible()) {
      <div role="status" class="w-full bg-[#111111] text-white">
        <div class="max-w-[1440px] mx-auto px-4 sm:px-6 py-3 flex flex-col sm:flex-row sm:items-center gap-3 sm:justify-between text-xs tracking-wide">
          <p class="min-w-0">
            @if (hecho()) {
              Tu cuenta ya está registrada en {{ tienda()?.nombre }}. Puedes continuar con tu compra o reserva.
            } @else {
              Tu cuenta aún no está registrada en <strong>{{ tienda()?.nombre }}</strong>. Regístrate en esta
              tienda para comprar y reservar, sin crear otra cuenta.
            }
          </p>
          @if (error()) {
            <p class="text-[#F2B8B5]">{{ error() }}</p>
          }
          <div class="flex items-center gap-3 shrink-0">
            @if (!hecho()) {
              <button
                type="button"
                class="px-4 py-2 bg-white text-[#111111] font-semibold uppercase tracking-[0.15em] text-[10px] hover:bg-[#ECEAE6] disabled:opacity-60"
                [disabled]="enviando()"
                (click)="registrarme()"
              >
                {{ enviando() ? 'Registrando…' : 'Registrarme en esta tienda' }}
              </button>
            }
            <button type="button" class="underline text-[10px] uppercase tracking-[0.15em]" (click)="cerrar()">
              {{ hecho() ? 'Cerrar' : 'Ahora no' }}
            </button>
          </div>
        </div>
      </div>
    }
  `,
})
export class RegistroEnTiendaComponent {
  private readonly tenant = inject(TenantService);
  private readonly login = inject(LoginService);

  readonly tienda = this.tenant.tenantActual;
  readonly enviando = signal(false);
  readonly hecho = signal(false);
  readonly error = signal<string | null>(null);
  private readonly descartado = signal(false);

  readonly visible = computed(() => {
    const usuarioActual = this.login.usuarioActual;
    const rol = typeof usuarioActual === 'function' ? usuarioActual()?.rol : undefined;
    if (rol !== 'cliente' || !this.tienda()) return false;
    if (this.hecho()) return true;
    if (this.tenant.registroSolicitado()) return true;
    return !this.descartado() && this.tenant.estaRegistradoEnTienda() === false;
  });

  registrarme(): void {
    this.enviando.set(true);
    this.error.set(null);
    this.tenant.registrarmeEnTienda().subscribe({
      next: () => {
        this.enviando.set(false);
        this.hecho.set(true);
      },
      error: (err: HttpErrorResponse) => {
        this.enviando.set(false);
        this.error.set(err.error?.detail ?? 'No se pudo completar el registro en la tienda.');
      },
    });
  }

  cerrar(): void {
    this.descartado.set(true);
    this.hecho.set(false);
    this.tenant.registroSolicitado.set(false);
  }
}
