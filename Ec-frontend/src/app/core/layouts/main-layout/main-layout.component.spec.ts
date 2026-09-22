import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { computed, signal } from '@angular/core';
import { of } from 'rxjs';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { MainLayoutComponent } from './main-layout.component';
import { CarritoService } from '../../../modules/compras_pagos/cu11_gestionar_carrito/servicios/carrito.service';
import { LoginService } from '../../../modules/autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';

describe('MainLayoutComponent', () => {
  let component: MainLayoutComponent;
  let fixture: ComponentFixture<MainLayoutComponent>;

  let mockCarritoService: {
    totalPrendas: ReturnType<typeof computed<number>>;
    cargarCarrito: ReturnType<typeof vi.fn>;
  };
  let mockLoginService: {
    estaAutenticado: ReturnType<typeof vi.fn>;
    esAdmin: ReturnType<typeof signal<boolean>>;
  };

  const totalPrendas = signal<number>(3);

  beforeEach(async () => {
    totalPrendas.set(3);

    // El contador procede de CarritoService, único origen de verdad de la bolsa. Antes se
    // mockeaba un `cestaCount` de CatalogoService inicializado en 2 y sólo incrementado en
    // memoria, que mostraba una cifra inventada y ajena a la bolsa persistida.
    mockCarritoService = {
      totalPrendas: computed(() => totalPrendas()),
      cargarCarrito: vi.fn().mockReturnValue(of({})),
    };
    mockLoginService = {
      estaAutenticado: vi.fn().mockReturnValue(true),
      esAdmin: signal(false),
    };

    await TestBed.configureTestingModule({
      imports: [MainLayoutComponent],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        { provide: CarritoService, useValue: mockCarritoService },
        { provide: LoginService, useValue: mockLoginService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(MainLayoutComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe crearse correctamente el MainLayoutComponent', () => {
    expect(component).toBeTruthy();
  });

  it('debe renderizar la barra institucional persistente con las 4 rutas raíz (Hub)', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const logo = compiled.querySelector('header a');
    expect(logo?.textContent?.trim()).toContain('FASHION STORE');

    const navLinks = compiled.querySelectorAll('header nav a');
    expect(navLinks.length).toBe(4);
    expect(navLinks[0]?.textContent?.trim()).toBe('INICIO');
    expect(navLinks[1]?.textContent?.trim()).toBe('BUSCAR');
    expect(navLinks[2]?.textContent?.trim()).toBe('CATÁLOGO');
    expect(navLinks[3]?.textContent?.trim()).toBe('PERFIL');
  });

  it('debe renderizar el contador real de prendas de la bolsa', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('3');
  });

  it('debe reflejar los cambios de la bolsa sin recargar la vista', () => {
    totalPrendas.set(7);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('7');
  });

  it('debe cargar la bolsa al iniciar cuando hay sesión activa', () => {
    expect(mockCarritoService.cargarCarrito).toHaveBeenCalled();
  });

  it('debe enlazar el icono de la bolsa con la ruta /bolsa', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const enlaces = Array.from(compiled.querySelectorAll('a[href]'));
    const enlaceBolsa = enlaces.find((a) => a.getAttribute('href') === '/bolsa');

    expect(enlaceBolsa).toBeTruthy();
  });

  it('debe contener un router-outlet para las vistas hijas', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const routerOutlet = compiled.querySelector('router-outlet');
    expect(routerOutlet).toBeTruthy();
  });
});

describe('MainLayoutComponent sin sesión', () => {
  it('no debe pedir la bolsa al backend si el cliente no ha iniciado sesión', async () => {
    // Sin sesión la petición devolvería 401 y dispararía el redirect del interceptor sobre
    // una pantalla que puede ser pública.
    const cargarCarrito = vi.fn().mockReturnValue(of({}));

    await TestBed.configureTestingModule({
      imports: [MainLayoutComponent],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        {
          provide: CarritoService,
          useValue: { totalPrendas: computed(() => 0), cargarCarrito },
        },
        {
          provide: LoginService,
          useValue: { estaAutenticado: vi.fn().mockReturnValue(false), esAdmin: signal(false) },
        },
      ],
    }).compileComponents();

    const fixture = TestBed.createComponent(MainLayoutComponent);
    fixture.detectChanges();

    expect(cargarCarrito).not.toHaveBeenCalled();
  });
});
