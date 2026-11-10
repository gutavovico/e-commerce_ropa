import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { computed, signal } from '@angular/core';
import { provideRouter } from '@angular/router';
import { afterEach, describe, expect, it } from 'vitest';

import { ConflictosAdminComponent } from './conflictos-admin.component';
import { LoginService } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';

/** Payloads literales generados con `cu20_conflictos/esquemas.py` (`model_dump_json`). */
const RESUMEN = JSON.parse(
  '{"id_conflicto":7,"tipo":"stock_insuficiente","estado":"pendiente","creado_en":"2026-11-09T15:00:00Z","id_sucursal":3,"nombre_sucursal":"Menshopping Santa Cruz","id_venta":501,"numero_comprobante":"MOV-2026-00501","total":"350.00","cliente":"Ana Rojas"}'
);
const DETALLE = JSON.parse(
  '{"id_conflicto":7,"tipo":"stock_insuficiente","estado":"pendiente","creado_en":"2026-11-09T15:00:00Z","id_sucursal":3,"nombre_sucursal":"Menshopping Santa Cruz","id_venta":501,"numero_comprobante":"MOV-2026-00501","total":"350.00","cliente":"Ana Rojas","detalle":{"motivo":"STOCK_INSUFICIENTE","mensaje":"Ya no quedan unidades suficientes en la sucursal.","id_variante":41,"id_sucursal":3,"esperado":1,"encontrado":0},"lineas":[{"id_variante":41,"nombre_producto":"Camisa formal blanca","sku":"MSH-CAM-M","cantidad":1,"precio_unitario":"350.00"}],"pago":{"id_pago":90,"metodo_pago":"tarjeta_credito","monto":"350.00","estado":"confirmado","confirmado_en":"2026-11-09T15:00:00Z"},"fecha_compra":"2026-11-09T15:00:00Z","aceptado_por":null,"aceptado_en":null,"resuelto_en":null,"referencia_reembolso":null,"intentos_reembolso":0,"ultimo_error":null}'
);
const CIERRE = JSON.parse('{"es_ultimo_dia_del_mes":false,"reembolsos_pendientes":1}');
const RESULTADO_CIERRE = JSON.parse('{"forzado":true,"procesados":1,"reembolsados":1,"fallidos":[]}');

describe('ConflictosAdminComponent (P2-CU20)', () => {
  let fixture: ComponentFixture<ConflictosAdminComponent>;
  let http: HttpTestingController;

  function crear(rol: 'administrador' | 'encargado_sucursal'): void {
    const usuario = signal({ id_usuario: 1, rol, email: 'x@y.com', nombres: 'A', apellidos: 'B', token: 't' });
    TestBed.configureTestingModule({
      imports: [ConflictosAdminComponent],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        {
          provide: LoginService,
          useValue: { usuarioActual: usuario, esAdmin: computed(() => usuario().rol === 'administrador') },
        },
      ],
    });
    fixture = TestBed.createComponent(ConflictosAdminComponent);
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    http.expectOne((r) => r.url === '/api/v1/conflictos-sync' && r.params.get('estado') === 'pendiente').flush([RESUMEN]);
    if (rol === 'administrador') http.expectOne('/api/v1/conflictos-sync/cierre').flush(CIERRE);
    fixture.detectChanges();
  }

  const texto = () => (fixture.nativeElement as HTMLElement).textContent ?? '';
  const boton = (contenido: string) =>
    [...(fixture.nativeElement as HTMLElement).querySelectorAll('button')].find((b) => b.textContent?.includes(contenido));

  afterEach(() => {
    http.verify();
    TestBed.resetTestingModule();
  });

  it('lista los pendientes con su tipo y el importe tal como llega', () => {
    crear('administrador');
    expect(texto()).toContain('MOV-2026-00501 · Stock insuficiente');
    expect(texto()).toContain('Ana Rojas');
    expect(texto()).toContain('350,00');
  });

  it('el detalle muestra la compra, el pago y el dato que no coincide', () => {
    crear('administrador');
    boton('MOV-2026-00501')!.click();
    http.expectOne('/api/v1/conflictos-sync/7').flush(DETALLE);
    fixture.detectChanges();
    expect(texto()).toContain('Esperado: 1');
    expect(texto()).toContain('Encontrado: 0');
    expect(texto()).toContain('1 × Camisa formal blanca (MSH-CAM-M)');
    expect(texto()).toContain('tarjeta_credito');
  });

  it('A3: si otro usuario ya lo resolvió, lo informa y actualiza la lista', () => {
    crear('encargado_sucursal');
    boton('MOV-2026-00501')!.click();
    http.expectOne('/api/v1/conflictos-sync/7').flush(DETALLE);
    fixture.detectChanges();
    boton('Aceptar reembolso')!.click();
    http.expectOne('/api/v1/conflictos-sync/7/aceptar-reembolso').flush(
      { detail: 'Otro usuario ya resolvió este conflicto. Actualiza la lista.', code: 'CONFLICTO_YA_RESUELTO' },
      { status: 409, statusText: 'Conflict' }
    );
    http.expectOne((r) => r.url === '/api/v1/conflictos-sync').flush([]);
    fixture.detectChanges();
    expect(texto()).toContain('Otro usuario ya resolvió este conflicto');
    expect(texto()).toContain('No hay conflictos en este estado.');
  });

  it('el encargado no ve el cierre de mes (D2: solo el administrador)', () => {
    crear('encargado_sucursal');
    expect(texto()).not.toContain('Procesar reembolsos del cierre');
  });

  it('fuera del último día el cierre exige confirmar «cierre anticipado de prueba»', () => {
    crear('administrador');
    boton('Procesar reembolsos del cierre')!.click();
    fixture.detectChanges();
    http.expectNone('/api/v1/conflictos-sync/procesar-cierre');
    expect(texto()).toContain('cierre anticipado de prueba');

    boton('Confirmar cierre anticipado')!.click();
    const peticion = http.expectOne('/api/v1/conflictos-sync/procesar-cierre');
    expect(peticion.request.body).toEqual({ forzar: true });
    peticion.flush(RESULTADO_CIERRE);
    http.expectOne((r) => r.url === '/api/v1/conflictos-sync').flush([]);
    http.expectOne('/api/v1/conflictos-sync/cierre').flush({ es_ultimo_dia_del_mes: false, reembolsos_pendientes: 0 });
    fixture.detectChanges();
    expect(texto()).toContain('Cierre anticipado de prueba: 1 de 1 reembolsos procesados.');
  });
});
