import { ChangeDetectionStrategy, Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { CatalogoService } from '../../../modules/catalogo/servicios/catalogo.service';
import { CarritoService } from '../../../modules/compras_pagos/cu11_gestionar_carrito/servicios/carrito.service';
import { LoginService } from '../../../modules/autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';

@Component({
  selector: 'app-main-layout',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <div class="min-h-screen bg-[#FFFFFF] text-[#111111] flex flex-col font-sans selection:bg-black selection:text-white">
      <!-- 1. BARRA SUPERIOR DE NAVEGACIÓN INSTITUCIONAL PERSISTENTE (4 RUTAS RAÍZ HUB) -->
      <header class="w-full border-b border-[#ECEAE6] bg-white sticky top-0 z-30">
        <div class="max-w-[1440px] mx-auto px-6 h-16 flex items-center justify-between">
          <!-- Marca Principal -->
          <a
            routerLink="/inicio"
            class="text-sm font-semibold tracking-[0.25em] text-[#111111] uppercase hover:opacity-80 transition-opacity"
          >
            FASHION STORE
          </a>

          <!-- Navegación Desktop: Rutas Raíz y Consola Admin Condicional -->
          <nav class="hidden md:flex items-center space-x-10 text-[11px] font-medium tracking-[0.2em] uppercase">
            <a
              routerLink="/inicio"
              routerLinkActive="text-black font-semibold border-b-2 border-black pb-1"
              [routerLinkActiveOptions]="{ exact: true }"
              class="text-[#666666] hover:text-black transition-colors"
            >
              INICIO
            </a>
            <a
              routerLink="/buscar"
              routerLinkActive="text-black font-semibold border-b-2 border-black pb-1"
              class="text-[#666666] hover:text-black transition-colors"
            >
              BUSCAR
            </a>
            <a
              routerLink="/catalogo"
              routerLinkActive="text-black font-semibold border-b-2 border-black pb-1"
              class="text-[#666666] hover:text-black transition-colors"
            >
              CATÁLOGO
            </a>
            <a
              [routerLink]="esAdmin() ? '/admin/perfil' : '/perfil'"
              routerLinkActive="text-black font-semibold border-b-2 border-black pb-1"
              class="text-[#666666] hover:text-black transition-colors"
            >
              {{ esAdmin() ? 'MI CUENTA (ADMIN)' : 'PERFIL' }}
            </a>
            @if (esAdmin()) {
              <a
                routerLink="/admin"
                class="inline-flex items-center gap-1.5 px-3 py-1 bg-[#111111] text-[#AD8C63] text-[10px] font-bold tracking-widest uppercase rounded-full border border-[#AD8C63]/40 hover:bg-[#222222] transition-colors"
                title="Consola Administrativa"
              >
                <span class="w-1.5 h-1.5 rounded-full bg-[#AD8C63]"></span>
                CONSOLA ADMIN
              </a>
            }
          </nav>

          <!-- Utilidades: Notificaciones, Cesta, Avatar -->
          <div class="flex items-center space-x-6">
            <!-- Notificaciones -->
            <button
              type="button"
              class="relative text-[#333333] hover:text-black transition-colors"
              title="Notificaciones"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="1.5"
                  d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                />
              </svg>
              <span class="absolute -top-1 -right-1 w-2 h-2 bg-[#991B1B] rounded-full"></span>
            </button>

            <!-- Cesta con Contador -->
            <a
              routerLink="/bolsa"
              class="relative flex items-center text-[#333333] hover:text-black transition-colors"
              title="Bolsa de compra"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="1.5"
                  d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"
                />
              </svg>
              <span
                class="absolute -top-1.5 -right-2 bg-black text-white text-[9px] font-bold w-4 h-4 rounded-full flex items-center justify-center"
              >
                {{ cestaCount() }}
              </span>
            </a>

            <!-- Avatar Circular -->
            <a
              [routerLink]="esAdmin() ? '/admin/perfil' : '/perfil'"
              class="w-8 h-8 rounded-full overflow-hidden border border-[#D5D2CD] hover:border-black transition-colors block shrink-0"
              [title]="esAdmin() ? 'Mi Cuenta Corporativa' : 'Mi Cuenta'"
            >
              <img
                src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80"
                alt="Perfil de Usuario"
                class="w-full h-full object-cover"
              />
            </a>
          </div>
        </div>
      </header>

      <!-- 2. CONTENIDO PRINCIPAL ENRUTADO (VISTAS HIJAS) -->
      <main class="flex-1 w-full">
        <router-outlet></router-outlet>
      </main>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})

export class MainLayoutComponent implements OnInit {
  private readonly carritoService = inject(CarritoService);
  private readonly loginService = inject(LoginService);

  /**
   * Contador real de prendas en la bolsa.
   *
   * Antes leía un `signal` de `CatalogoService` inicializado en 2 y que sólo se incrementaba en
   * memoria, de modo que mostraba una cifra inventada y desalineada con la bolsa persistida.
   * Ahora deriva del estado de `CarritoService`, único origen de verdad del carrito.
   */
  protected readonly cestaCount = this.carritoService.totalPrendas;

  ngOnInit(): void {
    // La bolsa es de cada cliente: sin sesión no hay nada que pedir al backend y la petición
    // devolvería 401, disparando el redirect del interceptor sobre una pantalla pública.
    if (this.loginService.estaAutenticado()) {
      this.carritoService.cargarCarrito().subscribe({
        error: () => {
          /* El contador queda en cero; el error ya se publicó en la señal del servicio. */
        },
      });
    }
  }
}
