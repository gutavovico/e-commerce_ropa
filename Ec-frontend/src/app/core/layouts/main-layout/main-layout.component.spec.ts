import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { signal } from '@angular/core';

import { MainLayoutComponent } from './main-layout.component';
import { CatalogoService } from '../../../modules/catalogo/servicios/catalogo.service';

describe('MainLayoutComponent', () => {
  let component: MainLayoutComponent;
  let fixture: ComponentFixture<MainLayoutComponent>;

  let mockCatalogoService: any;

  beforeEach(async () => {
    mockCatalogoService = {
      cestaCount: signal<number>(3),
    };

    await TestBed.configureTestingModule({
      imports: [MainLayoutComponent],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        { provide: CatalogoService, useValue: mockCatalogoService },
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

  it('debe renderizar el contador de la bolsa de compras en el header', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('3');
  });

  it('debe contener un router-outlet para las vistas hijas', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const routerOutlet = compiled.querySelector('router-outlet');
    expect(routerOutlet).toBeTruthy();
  });
});
