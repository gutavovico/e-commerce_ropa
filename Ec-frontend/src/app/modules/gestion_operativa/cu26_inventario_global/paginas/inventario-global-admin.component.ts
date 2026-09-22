import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  OnDestroy,
  inject,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { Subscription, debounceTime, distinctUntilChanged } from 'rxjs';

import { InventarioGlobalAdminService } from '../servicios/inventario-global-admin.service';
import { SucursalesAdminService } from '../../cu21_sucursales_ciudades/servicios/sucursales-admin.service';
import { AtributosAdminService } from '../../cu23_categorias_tallas_colores/servicios/atributos-admin.service';
import {
  CriterioOrdenacionInventario,
  EstadoStockGlobal,
  InventarioGlobalItem,
} from '../modelos/inventario-global.dto';

@Component({
  selector: 'app-inventario-global-admin',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './inventario-global-admin.component.html',
  styleUrls: ['./inventario-global-admin.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class InventarioGlobalAdminComponent implements OnInit, OnDestroy {
  protected readonly inventarioService = inject(InventarioGlobalAdminService);
  protected readonly sucursalesService = inject(SucursalesAdminService);
  protected readonly atributosService = inject(AtributosAdminService);

  // --- Controles Reactivos de Filtros ---
  readonly busquedaControl = new FormControl<string>('', { nonNullable: true });
  readonly categoriaControl = new FormControl<number | null>(null);
  readonly sucursalControl = new FormControl<number | null>(null);
  readonly estadoControl = new FormControl<EstadoStockGlobal | 'todos'>('todos', {
    nonNullable: true,
  });
  readonly ordenControl = new FormControl<CriterioOrdenacionInventario>('nombre_asc', {
    nonNullable: true,
  });

  private readonly subs = new Subscription();

  ngOnInit(): void {
    // 1. Carga inicial de datos analiticos y maestros
    this.inventarioService.cargarInventario().subscribe({ error: () => {} });
    this.sucursalesService.cargarSucursales().subscribe({ error: () => {} });
    this.atributosService.cargarCategorias().subscribe({ error: () => {} });

    // 2. Suscripcion reactiva al buscador con debounce de 300 ms
    this.subs.add(
      this.busquedaControl.valueChanges
        .pipe(debounceTime(300), distinctUntilChanged())
        .subscribe((valor) => {
          this.inventarioService.actualizarFiltros({ q: valor });
        })
    );

    // 3. Suscripciones a selectores
    this.subs.add(
      this.categoriaControl.valueChanges.subscribe((catId) => {
        this.inventarioService.actualizarFiltros({ id_categoria: catId });
      })
    );

    this.subs.add(
      this.sucursalControl.valueChanges.subscribe((sucId) => {
        this.inventarioService.actualizarFiltros({ id_sucursal: sucId });
      })
    );

    this.subs.add(
      this.estadoControl.valueChanges.subscribe((estado) => {
        this.inventarioService.actualizarFiltros({ estado_stock: estado });
      })
    );

    this.subs.add(
      this.ordenControl.valueChanges.subscribe((orden) => {
        this.inventarioService.actualizarFiltros({ ordenar_por: orden });
      })
    );
  }

  ngOnDestroy(): void {
    this.subs.unsubscribe();
  }

  limpiarFiltros(): void {
    this.busquedaControl.setValue('', { emitEvent: false });
    this.categoriaControl.setValue(null, { emitEvent: false });
    this.sucursalControl.setValue(null, { emitEvent: false });
    this.estadoControl.setValue('todos', { emitEvent: false });
    this.ordenControl.setValue('nombre_asc', { emitEvent: false });
    this.inventarioService.limpiarFiltros();
  }

  cambiarPagina(pagina: number): void {
    this.inventarioService.cambiarPagina(pagina);
  }

  abrirModalDetalle(item: InventarioGlobalItem): void {
    this.inventarioService.abrirDetalle(item);
  }

  cerrarModalDetalle(): void {
    this.inventarioService.cerrarDetalle();
  }

  reintentar(): void {
    this.inventarioService.cargarInventario().subscribe({ error: () => {} });
  }

  trackByVariante(_index: number, item: InventarioGlobalItem): number {
    return item.id_variante;
  }
}
