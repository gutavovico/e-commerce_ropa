import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { ViewportScroller } from '@angular/common';
import { LandingPageComponent } from './landing.component';

describe('LandingPageComponent', () => {
  let component: LandingPageComponent;
  let fixture: ComponentFixture<LandingPageComponent>;

  const mockViewportScroller = {
    scrollToAnchor: vi.fn(),
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LandingPageComponent],
      providers: [
        provideRouter([]),
        { provide: ViewportScroller, useValue: mockViewportScroller },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(LandingPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe crearse correctamente', () => {
    expect(component).toBeTruthy();
  });

  it('debe renderizar el logotipo FASHION STORE en el header', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const logo = compiled.querySelector('header a');
    expect(logo?.textContent?.trim()).toContain('FASHION STORE');
  });

  it('debe renderizar los botones de autenticación para Iniciar Sesión y Registrar', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const loginLink = compiled.querySelector('a[href="/login"]');
    const registroLink = compiled.querySelector('a[href="/registro"]');

    expect(loginLink).toBeTruthy();
    expect(registroLink).toBeTruthy();
  });

  it('debe renderizar las 3 métricas de precisión en el Hero', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const hero = compiled.querySelector('#hero');
    expect(hero?.textContent).toContain('0.8mm');
    expect(hero?.textContent).toContain('50piezas');
    expect(hero?.textContent).toContain('100%');
  });

  it('debe actualizar la prenda seleccionada reactivamente con Signals', () => {
    expect(component['prendaSeleccionadaId']()).toBe('sastreria');
    expect(component['prendaActiva']().nombre).toBe('Blazer Lana Camel');

    component['seleccionarPrenda']('noche');
    fixture.detectChanges();

    expect(component['prendaSeleccionadaId']()).toBe('noche');
    expect(component['prendaActiva']().nombre).toBe('Vestido Plisado');
  });

  it('debe renderizar las 4 sucursales flagship', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const sucursales = compiled.querySelectorAll('#sucursales h3');
    expect(sucursales.length).toBe(4);
    expect(compiled.textContent).toContain('Madrid · Serrano');
    expect(compiled.textContent).toContain('París · Saint-Honoré');
    expect(compiled.textContent).toContain('Milán · Montenapoleone');
    expect(compiled.textContent).toContain('Barcelona · Gràcia');
  });

  it('debe ejecutar scrollToSection invocando scrollIntoView si está disponible', () => {
    const targetSection = fixture.nativeElement.querySelector('#vestidor-virtual');
    targetSection.scrollIntoView = vi.fn();

    component.scrollToSection('vestidor-virtual');
    expect(targetSection.scrollIntoView).toHaveBeenCalledWith({
      behavior: 'smooth',
      block: 'start',
    });
  });

  it('debe recurrir a scrollToAnchor si el elemento no existe o carece de scrollIntoView', () => {
    component.scrollToSection('seccion-inexistente');
    expect(mockViewportScroller.scrollToAnchor).toHaveBeenCalledWith(
      'seccion-inexistente'
    );
  });
});
