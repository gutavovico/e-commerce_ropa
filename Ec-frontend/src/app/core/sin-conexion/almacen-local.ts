import { Injectable } from '@angular/core';
import { DBSchema, IDBPDatabase, openDB } from 'idb';
import { CatalogoGuardado, DispositivoLocal, OperacionLocal } from './sin-conexion.models';

/**
 * P2-CU14 / CU19 · Almacenamiento local (IndexedDB). Las claves llevan el código de la tienda: dos
 * tiendas abiertas en el mismo navegador no ven lo de la otra. Las operaciones no se borran al
 * enviarse ni al cerrar sesión (RN37, RNF03).
 *
 * Es una clase abstracta para que las pruebas usen `AlmacenEnMemoria` (jsdom no trae IndexedDB).
 */
@Injectable({ providedIn: 'root', useFactory: () => new AlmacenIndexedDb() })
export abstract class AlmacenLocal {
  abstract dispositivo(clave: string): Promise<DispositivoLocal | undefined>;
  abstract guardarDispositivo(dispositivo: DispositivoLocal): Promise<void>;
  abstract catalogo(codigo: string): Promise<CatalogoGuardado | undefined>;
  /** Reemplaza el catálogo solo cuando la descarga terminó (CU14 A2). */
  abstract guardarCatalogo(catalogo: CatalogoGuardado): Promise<void>;
  abstract borrarCatalogos(): Promise<void>;
  abstract operaciones(clave: string): Promise<OperacionLocal[]>;
  abstract guardarOperacion(operacion: OperacionLocal): Promise<void>;
  /** Siguiente correlativo del dispositivo, en la misma transacción que lo incrementa. */
  abstract siguienteCorrelativo(clave: string): Promise<number>;
}

interface EsquemaSinConexion extends DBSchema {
  dispositivos: { key: string; value: DispositivoLocal };
  catalogos: { key: string; value: CatalogoGuardado };
  operaciones: { key: string; value: OperacionLocal; indexes: { porClave: string } };
}

const NOMBRE_BD = 'fashionstore-sin-conexion';

export class AlmacenIndexedDb extends AlmacenLocal {
  private bd: Promise<IDBPDatabase<EsquemaSinConexion>> | null = null;

  private abrir(): Promise<IDBPDatabase<EsquemaSinConexion>> {
    this.bd ??= openDB<EsquemaSinConexion>(NOMBRE_BD, 1, {
      upgrade(bd) {
        bd.createObjectStore('dispositivos', { keyPath: 'clave' });
        bd.createObjectStore('catalogos', { keyPath: 'codigo' });
        bd.createObjectStore('operaciones', { keyPath: 'uuid' }).createIndex('porClave', 'clave');
      },
    });
    return this.bd;
  }

  async dispositivo(clave: string) {
    return (await this.abrir()).get('dispositivos', clave);
  }

  async guardarDispositivo(dispositivo: DispositivoLocal) {
    await (await this.abrir()).put('dispositivos', dispositivo);
  }

  async catalogo(codigo: string) {
    return (await this.abrir()).get('catalogos', codigo);
  }

  async guardarCatalogo(catalogo: CatalogoGuardado) {
    await (await this.abrir()).put('catalogos', catalogo);
  }

  async borrarCatalogos() {
    await (await this.abrir()).clear('catalogos');
  }

  async operaciones(clave: string) {
    return (await this.abrir()).getAllFromIndex('operaciones', 'porClave', clave);
  }

  async guardarOperacion(operacion: OperacionLocal) {
    await (await this.abrir()).put('operaciones', operacion);
  }

  async siguienteCorrelativo(clave: string) {
    const tx = (await this.abrir()).transaction('dispositivos', 'readwrite');
    const dispositivo = await tx.store.get(clave);
    if (!dispositivo) throw new Error('Dispositivo sin registrar');
    dispositivo.correlativo += 1;
    await tx.store.put(dispositivo);
    await tx.done;
    return dispositivo.correlativo;
  }
}

/** Para pruebas: mismo contrato, en memoria. */
export class AlmacenEnMemoria extends AlmacenLocal {
  readonly dispositivos = new Map<string, DispositivoLocal>();
  readonly catalogos = new Map<string, CatalogoGuardado>();
  readonly ops = new Map<string, OperacionLocal>();

  async dispositivo(clave: string) {
    const d = this.dispositivos.get(clave);
    return d ? structuredClone(d) : undefined;
  }
  async guardarDispositivo(d: DispositivoLocal) {
    this.dispositivos.set(d.clave, structuredClone(d));
  }
  async catalogo(codigo: string) {
    return this.catalogos.get(codigo);
  }
  async guardarCatalogo(c: CatalogoGuardado) {
    this.catalogos.set(c.codigo, c);
  }
  async borrarCatalogos() {
    this.catalogos.clear();
  }
  async operaciones(clave: string) {
    return [...this.ops.values()].filter((o) => o.clave === clave).map((o) => structuredClone(o));
  }
  async guardarOperacion(o: OperacionLocal) {
    this.ops.set(o.uuid, structuredClone(o));
  }
  async siguienteCorrelativo(clave: string) {
    const d = this.dispositivos.get(clave);
    if (!d) throw new Error('Dispositivo sin registrar');
    d.correlativo += 1;
    return d.correlativo;
  }
}
