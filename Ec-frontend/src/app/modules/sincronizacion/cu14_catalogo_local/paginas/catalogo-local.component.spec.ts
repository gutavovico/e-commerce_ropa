import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { signal } from '@angular/core';
import { provideRouter } from '@angular/router';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { CatalogoLocalComponent } from './catalogo-local.component';
import { AlmacenEnMemoria, AlmacenLocal } from '../../../../core/sin-conexion/almacen-local';
import { ConectividadService } from '../../../../core/sin-conexion/conectividad.service';
import { SinConexionService } from '../../../../core/sin-conexion/sin-conexion.service';
import { DispositivoLocal } from '../../../../core/sin-conexion/sin-conexion.models';

/** Paquete literal de `GET /sin-conexion/catalogo` (generado con `CatalogoLocalOut.model_dump_json`). */
const CATALOGO = JSON.parse(
  '{"generado_en":"2026-11-09T15:00:00Z","modo":"completo","moneda":"BOB","productos":[{"id_producto":5,"nombre":"Camisa formal blanca","descripcion":"Algodón","id_categoria":2,"precio_base":"350.00","imagen_url":"/ar/menshopping_camisa.png","variantes":[{"id_variante":41,"sku":"MSH-CAM-M","id_talla":2,"id_color":1,"precio":"350.00"}]}],"categorias":[{"id_categoria":2,"nombre":"Camisas formales","id_categoria_padre":null}],"tallas":[{"id_talla":2,"codigo":"M","orden":2}],"colores":[{"id_color":1,"nombre":"Blanco","codigo_hex":"#FFFFFF"}],"promociones":[],"sucursales":[{"id_sucursal":3,"nombre":"Menshopping Santa Cruz","direccion":"Dirección por confirmar","ciudad":"Santa Cruz de la Sierra","horario_apertura":"09:00","horario_cierre":"20:00"},{"id_sucursal":4,"nombre":"Menshopping Beni","direccion":"Dirección por confirmar","ciudad":"Trinidad","horario_apertura":"09:00","horario_cierre":"20:00"}],"existencias":[{"id_variante":41,"id_sucursal":3,"cantidad_disponible":5},{"id_variante":41,"id_sucursal":4,"cantidad_disponible":0}]}'
);

describe('CatalogoLocalComponent (P2-CU14 A4 / CU15 A1)', () => {
  let fixture: ComponentFixture<CatalogoLocalComponent>;
  let almacen: AlmacenEnMemoria;
  let servicio: SinConexionService;

  beforeEach(async () => {
    almacen = new AlmacenEnMemoria();
    TestBed.configureTestingModule({
      imports: [CatalogoLocalComponent],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: AlmacenLocal, useValue: almacen },
        { provide: ConectividadService, useValue: { enLinea: signal(false) } },
      ],
    });
    servicio = TestBed.inject(SinConexionService);
    const dispositivo: DispositivoLocal = {
      clave: 'menshopping:10', codigo: 'menshopping', idCliente: 10, identificador: 'uuid', codigoCorto: '3F9A', correlativo: 0,
      parametros: { operacion_offline_habilitada: true, dias_antiguedad_offline: 7, horas_vencimiento_reserva: 24, moneda: 'BOB' },
    };
    await almacen.guardarDispositivo(dispositivo);
    await almacen.guardarCatalogo({ codigo: 'menshopping', paquete: CATALOGO, guardadoEn: '2026-11-09T15:00:00.000Z' });
    await servicio.prepararTienda('menshopping', 10, null); // sin red: solo lo local

    fixture = TestBed.createComponent(CatalogoLocalComponent);
    fixture.detectChanges();
  });

  afterEach(() => TestBed.resetTestingModule());

  const raiz = () => fixture.nativeElement as HTMLElement;
  const botones = () => [...raiz().querySelectorAll('button')];

  it('muestra el catálogo guardado con su fecha y el aviso de desactualizado (RN42)', () => {
    expect(raiz().textContent).toContain('Puede estar desactualizado · Datos del 09/11/2026');
    expect(raiz().textContent).toContain('Camisa formal blanca');
    expect(raiz().textContent).toContain('350,00');
  });

  it('reserva sin conexión: sucursal sin existencias deshabilitada y código PROV guardado', async () => {
    botones().find((b) => b.textContent?.includes('Camisa formal blanca'))!.click();
    fixture.detectChanges();
    const beni = botones().find((b) => b.textContent?.includes('Menshopping Beni'))!;
    expect(beni.disabled).toBe(true);
    expect(beni.textContent).toContain('Sin existencias');

    botones().find((b) => b.textContent?.includes('Menshopping Santa Cruz'))!.click();
    fixture.detectChanges();
    const componente = fixture.componentInstance as unknown as { franja: { set(v: string): void }; franjas(): { iso: string }[] };
    // Con 24 h de vencimiento siempre queda al menos una hora dentro del horario de la tienda.
    const primera = componente.franjas()[0];
    expect(primera).toBeDefined();
    componente.franja.set(primera.iso);
    fixture.detectChanges();
    botones().find((b) => b.textContent?.trim() === 'Reservar')!.click();
    await new Promise((r) => setTimeout(r, 0));
    fixture.detectChanges();

    expect(raiz().textContent).toContain('Reserva guardada: PROV-3F9A-000001');
    const [op] = await almacen.operaciones('menshopping:10');
    expect(op.estado).toBe('registrada_localmente');
    expect(op.idSucursal).toBe(3);
    expect(op.datos.items).toEqual([{ id_variante: 41, cantidad: 1 }]);
  });
});
