import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { Router, provideRouter } from '@angular/router';
import { describe, it, expect, beforeEach, vi } from 'vitest';

import { WidgetChatbotComponent } from './widget-chatbot.component';
import { ChatbotService } from '../servicios/chatbot.service';

describe('WidgetChatbotComponent (CU19)', () => {
  let component: WidgetChatbotComponent;
  let fixture: ComponentFixture<WidgetChatbotComponent>;
  let chatbotService: ChatbotService;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WidgetChatbotComponent],
      providers: [
        ChatbotService,
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(WidgetChatbotComponent);
    component = fixture.componentInstance;
    chatbotService = TestBed.inject(ChatbotService);
    fixture.detectChanges();
  });

  it('debe crearse el componente correctamente', () => {
    expect(component).toBeTruthy();
  });

  it('debe mostrar el botón flotante para abrir el asistente sin indicador de no leído por defecto', () => {
    const botonFlotante = fixture.nativeElement.querySelector('button[aria-label*="asistente"]');
    expect(botonFlotante).toBeTruthy();

    // No debe existir el círculo indicador por defecto
    const badgeNoLeido = botonFlotante.querySelector('span.rounded-full');
    expect(badgeNoLeido).toBeNull();

    // Debe mostrarse únicamente si hay mensajes no leídos
    chatbotService.mensajesNoLeidos.set(true);
    fixture.detectChanges();
    const badgeActivo = botonFlotante.querySelector('span.rounded-full');
    expect(badgeActivo).toBeTruthy();

    // Al abrir el chat desaparece
    chatbotService.abrirChat();
    fixture.detectChanges();
    expect(botonFlotante.querySelector('span.rounded-full')).toBeNull();
  });

  it('debe abrir y cerrar la ventana flotante de chat al alternar', () => {
    expect(fixture.nativeElement.querySelector('aside .w-\\[380px\\], aside header')).toBeFalsy();

    chatbotService.abrirChat();
    fixture.detectChanges();

    const cabecera = fixture.nativeElement.querySelector('header');
    expect(cabecera).toBeTruthy();
    expect(cabecera.textContent).toContain('Fashion Store');
    expect(cabecera.textContent).toContain('Asistente de Estilo');
  });

  it('debe enviar mensaje al invocar enviar() con texto no vacío', () => {
    const spy = vi.spyOn(chatbotService, 'enviarMensaje');
    chatbotService.abrirChat();
    fixture.detectChanges();

    component.nuevoMensaje.set('¿Tienen blazers negros?');
    component.enviar();

    expect(spy).toHaveBeenCalledWith('¿Tienen blazers negros?');
    expect(component.nuevoMensaje()).toBe('');
  });

  it('no debe enviar mensaje si el texto está en blanco', () => {
    const spy = vi.spyOn(chatbotService, 'enviarMensaje');
    component.nuevoMensaje.set('   ');
    component.enviar();

    expect(spy).not.toHaveBeenCalled();
  });

  it('debe seleccionar sugerencia rápida e invocar enviarMensaje', () => {
    const spy = vi.spyOn(chatbotService, 'enviarMensaje');
    component.seleccionarSugerencia('¿Cuáles son los horarios?');

    expect(spy).toHaveBeenCalledWith('¿Cuáles son los horarios?');
  });

  it('debe navegar a /productos/:id al seleccionar una prenda', () => {
    const router = TestBed.inject(Router);
    const spy = vi.spyOn(router, 'navigate');

    component.irAProducto(10);
    expect(spy).toHaveBeenCalledWith(['/productos', 10]);
  });
});

