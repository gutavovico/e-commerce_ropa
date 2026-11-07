import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';

import { ChatbotService } from './chatbot.service';
import { RespuestaChatbotDto } from '../modelos/chatbot.dto';

describe('ChatbotService (CU19)', () => {
  let service: ChatbotService;
  let httpMock: HttpTestingController;

  const mockRespuesta: RespuestaChatbotDto = {
    id_interaccion: 99,
    respuesta: 'Disponemos de piezas exclusivas de alta costura.',
    productos_sugeridos: [
      {
        id_producto: 10,
        nombre: 'Vestido Seda Noir',
        precio: '1250.00',
        categoria: 'Vestidos',
        imagen_url: 'https://example.com/vestido.jpg',
        disponible: true,
        sucursal_nombre: 'Atelier Serrano',
      },
    ],
    sucursales_sugeridas: [
      {
        id_sucursal: 1,
        nombre: 'Atelier Serrano',
        direccion: 'Calle Serrano 48',
        horario: '09:00 - 20:00',
      },
    ],
    sugerencias_rapidas: ['¿Tienen probador virtual?', 'Ver otras tallas'],
  };

  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();

    TestBed.configureTestingModule({
      providers: [
        ChatbotService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });

    service = TestBed.inject(ChatbotService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    sessionStorage.clear();
  });

  it('debe inicializarse cerrado y con mensaje de bienvenida oficial', () => {
    expect(service.abierto()).toBe(false);
    expect(service.cargando()).toBe(false);
    expect(service.mensajes().length).toBe(1);
    expect(service.mensajes()[0].emisor).toBe('asistente');
  });

  it('debe alternar el estado abierto/cerrado con alternarChat', () => {
    service.alternarChat();
    expect(service.abierto()).toBe(true);

    service.cerrarChat();
    expect(service.abierto()).toBe(false);

    service.abrirChat();
    expect(service.abierto()).toBe(true);
  });

  it('debe enviar mensaje, agregar burbujas y actualizar sugerencias rápidas', () => {
    service.enviarMensaje('¿Tienen vestidos de gala?');

    expect(service.cargando()).toBe(true);
    expect(service.mensajes().length).toBe(2);
    expect(service.mensajes()[1].texto).toBe('¿Tienen vestidos de gala?');

    const req = httpMock.expectOne('/api/v1/asistente/chat');
    expect(req.request.method).toBe('POST');
    expect(req.request.body.mensaje).toBe('¿Tienen vestidos de gala?');
    expect(req.request.body.canal).toBe('web');

    req.flush(mockRespuesta);

    expect(service.cargando()).toBe(false);
    expect(service.mensajes().length).toBe(3);
    const botMsg = service.mensajes()[2];
    expect(botMsg.emisor).toBe('asistente');
    expect(botMsg.texto).toBe('Disponemos de piezas exclusivas de alta costura.');
    expect(botMsg.productos?.length).toBe(1);
    expect(botMsg.productos?.[0].id_producto).toBe(10);
    expect(service.sugerenciasRapidas()).toEqual(['¿Tienen probador virtual?', 'Ver otras tallas']);
  });

  it('debe manejar error HTTP con mensaje de cortesía sin romper el estado', () => {
    service.enviarMensaje('Consulta con fallo');

    const req = httpMock.expectOne('/api/v1/asistente/chat');
    req.flush('Error de servidor', { status: 500, statusText: 'Server Error' });

    expect(service.cargando()).toBe(false);
    expect(service.error()).toBeTruthy();
    expect(service.mensajes().length).toBe(3);
    expect(service.mensajes()[2].texto).toContain('Disculpe la molestia');
  });

  it('debe cargar historial de interacciones si el usuario está autenticado', () => {
    localStorage.setItem('fashionstore_token', 'mock_jwt_token');

    service.cargarHistorial();

    const req = httpMock.expectOne('/api/v1/asistente/historial?limite=10');
    expect(req.request.method).toBe('GET');
    expect(req.request.headers.get('Authorization')).toBe('Bearer mock_jwt_token');

    req.flush([
      {
        id_interaccion: 10,
        mensaje_usuario: '¿Horarios en Madrid?',
        respuesta_ia: 'De 09:00 a 20:00.',
        canal: 'web',
        creado_en: '2026-11-07T06:00:00Z',
      },
    ]);

    expect(service.mensajes().length).toBe(3);
    expect(service.mensajes()[1].texto).toBe('¿Horarios en Madrid?');
    expect(service.mensajes()[2].texto).toBe('De 09:00 a 20:00.');
  });

  it('debe reiniciar conversación con limpiarConversacion', () => {
    service.enviarMensaje('Hola');
    const req = httpMock.expectOne('/api/v1/asistente/chat');
    req.flush(mockRespuesta);

    service.limpiarConversacion();
    expect(service.mensajes().length).toBe(1);
    expect(service.mensajes()[0].id).toBe('bienvenida');
    expect(service.mensajesNoLeidos()).toBe(false);
  });

  it('no debe mostrar mensajes no leídos por defecto y debe activarse solo si llega respuesta estando cerrado', () => {
    expect(service.mensajesNoLeidos()).toBe(false);

    service.enviarMensaje('Consulta con chat cerrado');
    const req = httpMock.expectOne('/api/v1/asistente/chat');
    req.flush(mockRespuesta);

    expect(service.mensajesNoLeidos()).toBe(true);

    service.abrirChat();
    expect(service.mensajesNoLeidos()).toBe(false);
  });

  it('debe persistir mensajes en sessionStorage y limpiarlos al invocar limpiarConversacion', () => {
    service.enviarMensaje('Mensaje para persistir');
    const req = httpMock.expectOne('/api/v1/asistente/chat');
    req.flush(mockRespuesta);

    const guardado = sessionStorage.getItem('fashionstore_chat_mensajes');
    expect(guardado).toBeTruthy();
    expect(guardado).toContain('Mensaje para persistir');

    service.limpiarConversacion();
    expect(sessionStorage.getItem('fashionstore_chat_mensajes')).toBeNull();
    expect(service.mensajes().length).toBe(1);
  });
});

