import { ChangeDetectionStrategy, Component, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { TenantService } from '../../../../core/tenant/tenant.service';
import { EmpresaPublica, NOMBRE_PLATAFORMA } from '../../../../core/tenant/tenant.models';
import { LoginService } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import { destinoEmpleado, esRolEmpleado } from '../../../../core/guards/tenant.guard';

const AVISOS: Record<string, string> = {
  'tienda-inexistente': 'La tienda que buscas no existe. Elige una de la lista.',
  'tienda-no-disponible': 'Esa tienda no está disponible en este momento.',
};

/**
 * P2-CU02 · Directorio de tiendas en la raíz `/` (decisión A4). Lista las empresas activas con
 * suscripción vigente; con sesión de cliente muestra primero «Mis tiendas».
 */
@Component({
  selector: 'app-directorio',
  standalone: true,
  imports: [RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="min-h-screen bg-white text-[#111111] font-sans">
      <header class="border-b border-[#ECEAE6]">
        <div class="max-w-[1100px] mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
          <span class="text-sm font-semibold tracking-[0.25em] uppercase truncate">{{ plataforma }}</span>
          <nav class="flex items-center gap-4 text-[11px] uppercase tracking-[0.2em] shrink-0">
            @if (usuario(); as u) {
              @if (esEmpleado()) {
                <a [routerLink]="panel()" class="font-semibold hover:opacity-70">Mi panel</a>
              }
              <button type="button" class="text-[#666666] hover:text-black" (click)="cerrarSesion()">Cerrar sesión</button>
            } @else {
              <a routerLink="/login" class="font-semibold hover:opacity-70">Iniciar sesión</a>
            }
          </nav>
        </div>
      </header>

      <main class="max-w-[1100px] mx-auto px-4 sm:px-6 py-10 space-y-12">
        @if (aviso()) {
          <p role="alert" class="border border-[#ECEAE6] bg-[#FAF9F7] px-4 py-3 text-sm">{{ aviso() }}</p>
        }

        @if (esCliente()) {
          <section aria-labelledby="mis-tiendas">
            <h2 id="mis-tiendas" class="text-xs font-semibold uppercase tracking-[0.25em] mb-4">Mis tiendas</h2>
            @if (misTiendas() === null) {
              <p class="text-sm text-[#666666]">Cargando tus tiendas…</p>
            } @else if (misTiendas()!.length === 0) {
              <p class="text-sm text-[#666666]">
                Tu cuenta aún no está registrada en ninguna tienda. Entra en una de la lista y elige «Registrarme en esta tienda».
              </p>
            } @else {
              <ul class="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
                @for (tienda of misTiendas()!; track tienda.codigo) {
                  <li>
                    <a [routerLink]="['/', tienda.codigo, 'inicio']"
                       class="block border border-[#111111] px-5 py-6 hover:bg-[#111111] hover:text-white transition-colors">
                      <span class="block text-sm font-semibold tracking-[0.2em] uppercase truncate">{{ tienda.nombre }}</span>
                      <span class="block mt-1 text-[11px] text-current opacity-60">/{{ tienda.codigo }}</span>
                    </a>
                  </li>
                }
              </ul>
            }
          </section>
        }

        <section aria-labelledby="tiendas">
          <h1 id="tiendas" class="text-xs font-semibold uppercase tracking-[0.25em] mb-4">Tiendas</h1>
          @if (cargando()) {
            <p class="text-sm text-[#666666]">Cargando tiendas…</p>
          } @else if (error()) {
            <p role="alert" class="text-sm text-[#8C2F2B]">{{ error() }}</p>
          } @else if (tiendas().length === 0) {
            <p class="text-sm text-[#666666]">No hay tiendas disponibles en este momento.</p>
          } @else {
            <ul class="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
              @for (tienda of tiendas(); track tienda.codigo) {
                <li>
                  <a [routerLink]="['/', tienda.codigo]"
                     class="block border border-[#ECEAE6] px-5 py-6 hover:border-[#111111] transition-colors">
                    <span class="block text-sm font-semibold tracking-[0.2em] uppercase truncate">{{ tienda.nombre }}</span>
                    <span class="block mt-1 text-[11px] text-[#666666]">/{{ tienda.codigo }}</span>
                  </a>
                </li>
              }
            </ul>
          }
        </section>
      </main>
    </div>
  `,
})
export class DirectorioComponent implements OnInit {
  private readonly tenant = inject(TenantService);
  private readonly login = inject(LoginService);
  private readonly route = inject(ActivatedRoute);

  readonly plataforma = NOMBRE_PLATAFORMA;
  readonly tiendas = signal<EmpresaPublica[]>([]);
  readonly cargando = signal(true);
  readonly error = signal<string | null>(null);
  readonly aviso = signal<string | null>(null);

  readonly usuario = this.login.usuarioActual;
  readonly esCliente = computed(() => this.usuario()?.rol === 'cliente');
  readonly esEmpleado = computed(() => esRolEmpleado(this.usuario()?.rol));
  readonly panel = computed(() => destinoEmpleado(this.usuario()?.rol ?? ''));
  readonly misTiendas = this.tenant.misEmpresas;

  ngOnInit(): void {
    const clave = this.route.snapshot.queryParamMap.get('aviso');
    this.aviso.set(clave ? (AVISOS[clave] ?? null) : null);

    this.tenant.directorio().subscribe({
      next: (lista) => {
        this.tiendas.set(lista);
        this.cargando.set(false);
      },
      error: () => {
        this.error.set('No se pudo cargar el directorio de tiendas. Inténtalo de nuevo más tarde.');
        this.cargando.set(false);
      },
    });

    if (this.esCliente()) {
      this.tenant.cargarMisEmpresas().subscribe({ error: () => this.tenant.misEmpresas.set([]) });
    }
  }

  cerrarSesion(): void {
    this.login.cerrarSesion().subscribe();
  }
}
