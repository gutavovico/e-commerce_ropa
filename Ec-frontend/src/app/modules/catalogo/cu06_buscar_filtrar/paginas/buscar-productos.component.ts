import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  OnDestroy,
  inject,
  signal,
  computed,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Subject, debounceTime, distinctUntilChanged, takeUntil } from 'rxjs';

import { CatalogoService } from '../../servicios/catalogo.service';
import {
  FiltrosBusquedaState,
  ProductoItem,
} from '../../modelos/catalogo.modelos';

@Component({
  selector: 'app-buscar-productos',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './buscar-productos.component.html',
  styleUrls: ['./buscar-productos.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BuscarProductosComponent implements OnInit, OnDestroy {
  protected readonly catalogoService = inject(CatalogoService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly destroy$ = new Subject<void>();

  // Signals derivadas del servicio
  protected readonly productos = this.catalogoService.productos;
  protected readonly paginacion = this.catalogoService.paginacion;
  protected readonly filtrosDisponibles = this.catalogoService.filtrosDisponibles;
  protected readonly cargando = this.catalogoService.cargando;
  protected readonly error = this.catalogoService.error;
  protected readonly totalSugerencias = this.catalogoService.totalSugerencias;
  protected readonly cestaCount = this.catalogoService.cestaCount;
  protected readonly busquedasRecientes = this.catalogoService.busquedasRecientes;

  // Estado local de la vista: Todos los filtros son OPCIONALES por defecto
  protected readonly vistaCuadruple = signal<boolean>(true);
  protected readonly ordenSeleccionado = signal<string>('recientes');
  protected readonly temporadaSeleccionada = signal<string>('Todas las temporadas');
  protected readonly coleccionSeleccionada = signal<string>('');
  protected readonly tallaSeleccionada = signal<string>('');
  protected readonly colorSeleccionado = signal<string>('');
  protected readonly precioMin = signal<number>(0);
  protected readonly precioMax = signal<number>(2500);
  protected readonly filtroPrecioActivo = signal<boolean>(false);
  protected readonly guiaAtelierAbierta = signal<boolean>(false);
  protected readonly mensajeAgregado = signal<string | null>(null);

  // Form control para el input de búsqueda (sin auto-ejecución hasta confirmar)
  protected readonly searchControl = new FormControl<string>('', { nonNullable: true });
  // Término de búsqueda confirmado y activo
  protected readonly terminoBusquedaActivo = signal<string>('');

  // Listas locales de apoyo y temporales
  protected readonly temporadasTabs = [
    { id: 'todas', nombre: 'Todas las temporadas' },
    { id: 'otono2024', nombre: 'Otoño / Invierno 2024' },
    { id: 'primavera2025', nombre: 'Primavera / Verano 2025' },
    { id: 'capsula', nombre: 'Cápsula Edición Limitada' },
  ];

  protected readonly opcionesColeccionFallback = [
    { id: 1, nombre: 'Sastrería Atelier', conteo: 3 },
    { id: 2, nombre: 'Esenciales Minimalistas', conteo: 1 },
    { id: 3, nombre: 'Alta Costura', conteo: 3 },
    { id: 4, nombre: 'Seda Natural Pura', conteo: 1 },
  ];

  protected readonly tallasAtelier = ['36', '38', '40', '42', '44', 'Única'];

  // Paleta extendida de colores de ropa (haute couture / confección textil)
  protected readonly coloresAtelierFallback = [
    { nombre: 'Marfil', hex: '#FCFBF8', border: '#E5E5E5' },
    { nombre: 'Blanco Puro', hex: '#FFFFFF', border: '#E5E5E5' },
    { nombre: 'Camel', hex: '#C2A688', border: '#B09477' },
    { nombre: 'Beige Arena', hex: '#D8C4B6', border: '#C5B1A3' },
    { nombre: 'Ébano', hex: '#1A1A1A', border: '#000000' },
    { nombre: 'Champagne', hex: '#E8DFCF', border: '#D6CDBC' },
    { nombre: 'Borgoña', hex: '#5E1924', border: '#4E141E' },
    { nombre: 'Terracota', hex: '#B85D3B', border: '#A65335' },
    { nombre: 'Azul Marino', hex: '#1C2A39', border: '#141E28' },
    { nombre: 'Verde Oliva', hex: '#4B5842', border: '#3F4A37' },
    { nombre: 'Esmeralda', hex: '#1B4D3E', border: '#153E32' },
    { nombre: 'Rosa Palo', hex: '#E8C5C8', border: '#D6B3B6' },
    { nombre: 'Malva', hex: '#A594A6', border: '#938294' },
    { nombre: 'Rojo Carmín', hex: '#991B1B', border: '#801616' },
    { nombre: 'Gris Perla', hex: '#C5C6C7', border: '#B2B3B4' },
    { nombre: 'Ocre', hex: '#C68B29', border: '#B27D25' },
  ];

  // Colecciones dinámicas derivadas del backend
  protected readonly listaColecciones = computed(() => {
    const backendCols = this.filtrosDisponibles()?.colecciones;
    if (backendCols && backendCols.length > 0) {
      return backendCols.map((col) => ({
        id: col.id,
        nombre: col.nombre,
        conteo: col.conteo ?? 0,
      }));
    }
    return this.opcionesColeccionFallback;
  });

  // Colores dinámicos derivados del backend enriquecidos con fallback
  protected readonly listaColores = computed(() => {
    const backendCols = this.filtrosDisponibles()?.colores;
    if (backendCols && backendCols.length > 0) {
      return backendCols.map((c) => ({
        nombre: c.nombre,
        hex: c.extra || '#1A1A1A',
        border:
          c.extra === '#FFFFFF' || c.extra === '#FCFBF8'
            ? '#E5E5E5'
            : c.extra || '#1A1A1A',
      }));
    }
    return this.coloresAtelierFallback;
  });

  // Cálculo de resumen de piezas mostradas
  protected readonly resumenPaginacionTexto = computed(() => {
    const meta = this.paginacion();
    const count = this.productos().length;
    const total = meta.total_registros || count;
    return `Mostrando ${count} de ${total} piezas de sastrería seleccionadas`;
  });

  ngOnInit(): void {
    // 1. Cargar metadatos globales del backend
    this.catalogoService.obtenerFiltrosDisponibles().subscribe();

    // 2. Escuchar cambios en los query params de la URL para sincronización transparente
    this.route.queryParams.pipe(takeUntil(this.destroy$)).subscribe((params) => {
      const q = params['q'] || '';
      this.terminoBusquedaActivo.set(q);
      // Mantener limpio el campo de entrada tras confirmar la búsqueda
      this.searchControl.setValue('', { emitEvent: false });

      this.temporadaSeleccionada.set(params['temporada'] || 'Todas las temporadas');
      this.coleccionSeleccionada.set(params['coleccion'] || '');
      this.tallaSeleccionada.set(params['talla'] || '');
      this.colorSeleccionado.set(params['color'] || '');
      this.ordenSeleccionado.set(params['orden'] || 'recientes');

      if (params['precioMin'] !== undefined || params['precioMax'] !== undefined) {
        this.filtroPrecioActivo.set(true);
        if (params['precioMin']) this.precioMin.set(Number(params['precioMin']));
        if (params['precioMax']) this.precioMax.set(Number(params['precioMax']));
      } else {
        this.filtroPrecioActivo.set(false);
      }

      this.ejecutarConsulta(params['pagina'] ? Number(params['pagina']) : 1);
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Ejecuta la consulta invocando al servicio con los filtros confirmados.
   */
  protected ejecutarConsulta(pagina: number = 1): void {
    const estado: Partial<FiltrosBusquedaState> = {
      q: this.terminoBusquedaActivo().trim() || undefined,
      talla: this.tallaSeleccionada() || undefined,
      color: this.colorSeleccionado() || undefined,
      ordenar_por: this.ordenSeleccionado() as any,
      pagina: pagina,
      limite: this.vistaCuadruple() ? 12 : 8,
      solo_en_stock: false,
    };

    if (this.filtroPrecioActivo()) {
      estado.precio_min = this.precioMin();
      estado.precio_max = this.precioMax();
    }

    const colNombre = this.coleccionSeleccionada();
    if (colNombre) {
      const col = this.filtrosDisponibles()?.colecciones.find(
        (c) => c.nombre.toLowerCase() === colNombre.toLowerCase()
      );
      if (col) {
        estado.coleccion_id = col.id;
      }
    }

    const tempNombre = this.temporadaSeleccionada();
    if (tempNombre && tempNombre !== 'Todas las temporadas') {
      const temp = this.filtrosDisponibles()?.temporadas.find(
        (t) => t.nombre.toLowerCase() === tempNombre.toLowerCase()
      );
      if (temp) {
        estado.temporada_id = temp.id;
      }
    }

    this.catalogoService.buscarProductos(estado).subscribe();
  }

  /**
   * Refleja los filtros activos en los Query Params de la URL.
   */
  private actualizarUrl(nuevosParams: Record<string, any>): void {
    const paramsActuales = { ...this.route.snapshot.queryParams, ...nuevosParams };

    // Limpiar claves con valor nulo, indefinido o vacío
    Object.keys(paramsActuales).forEach((k) => {
      if (
        paramsActuales[k] === null ||
        paramsActuales[k] === undefined ||
        paramsActuales[k] === ''
      ) {
        delete paramsActuales[k];
      }
    });

    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: paramsActuales,
      queryParamsHandling: 'merge',
    });
  }

  // --- Handlers de Interacción y Confirmación de Búsqueda ---

  protected seleccionarTemporada(nombre: string): void {
    const valor = nombre === 'Todas las temporadas' ? 'Todas las temporadas' : nombre;
    this.temporadaSeleccionada.set(valor);
  }

  protected alternarColeccion(nombre: string): void {
    const nueva = this.coleccionSeleccionada() === nombre ? '' : nombre;
    this.coleccionSeleccionada.set(nueva);
  }

  protected seleccionarTalla(talla: string): void {
    const nueva = this.tallaSeleccionada() === talla ? '' : talla;
    this.tallaSeleccionada.set(nueva);
  }

  protected seleccionarColor(color: string): void {
    const nuevo = this.colorSeleccionado() === color ? '' : color;
    this.colorSeleccionado.set(nuevo);
  }

  protected onCambioPrecioMin(event: Event): void {
    const val = Number((event.target as HTMLInputElement).value);
    if (val <= this.precioMax()) {
      this.precioMin.set(val);
      this.filtroPrecioActivo.set(true);
    }
  }

  protected onCambioPrecioMax(event: Event): void {
    const val = Number((event.target as HTMLInputElement).value);
    if (val >= this.precioMin()) {
      this.precioMax.set(val);
      this.filtroPrecioActivo.set(true);
    }
  }

  protected cambiarOrden(event: Event): void {
    const val = (event.target as HTMLSelectElement).value;
    this.ordenSeleccionado.set(val);
    this.confirmarBusqueda();
  }

  /**
   * Confirma la búsqueda: aplica el término del input si fue escrito,
   * limpia la barra de búsqueda y aplica los filtros seleccionados.
   * Se ejecuta al presionar Enter o al hacer clic en el botón BUSCAR.
   */
  protected confirmarBusqueda(): void {
    const inputVal = this.searchControl.value.trim();
    if (inputVal) {
      this.terminoBusquedaActivo.set(inputVal);
    }
    // Limpiar el texto de la barra de búsqueda
    this.searchControl.setValue('', { emitEvent: false });

    this.actualizarUrl({
      q: this.terminoBusquedaActivo() || null,
      temporada: this.temporadaSeleccionada() === 'Todas las temporadas' ? null : this.temporadaSeleccionada(),
      coleccion: this.coleccionSeleccionada() || null,
      talla: this.tallaSeleccionada() || null,
      color: this.colorSeleccionado() || null,
      precioMin: this.filtroPrecioActivo() ? this.precioMin() : null,
      precioMax: this.filtroPrecioActivo() ? this.precioMax() : null,
      orden: this.ordenSeleccionado(),
      pagina: 1,
    });
  }

  protected quitarTerminoBusqueda(): void {
    this.terminoBusquedaActivo.set('');
    this.actualizarUrl({ q: null, pagina: 1 });
  }

  protected restablecerFiltros(): void {
    this.searchControl.setValue('', { emitEvent: false });
    this.terminoBusquedaActivo.set('');
    this.temporadaSeleccionada.set('Todas las temporadas');
    this.coleccionSeleccionada.set('');
    this.tallaSeleccionada.set('');
    this.colorSeleccionado.set('');
    this.precioMin.set(0);
    this.precioMax.set(2500);
    this.filtroPrecioActivo.set(false);
    this.ordenSeleccionado.set('recientes');

    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: {},
    });
  }

  protected cambiarPagina(nuevaPagina: number): void {
    const meta = this.paginacion();
    if (nuevaPagina >= 1 && nuevaPagina <= meta.total_paginas) {
      this.actualizarUrl({ pagina: nuevaPagina });
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }

  protected aplicarBusquedaFrecuente(termino: string): void {
    this.terminoBusquedaActivo.set(termino);
    this.searchControl.setValue('', { emitEvent: false });
    this.confirmarBusqueda();
  }

  protected limpiarInput(): void {
    this.searchControl.setValue('');
  }

  protected toggleVista(cuadruple: boolean): void {
    this.vistaCuadruple.set(cuadruple);
  }

  protected toggleFavorito(item: ProductoItem): void {
    this.catalogoService.toggleFavorito(item.id_producto);
  }

  protected agregarACesta(item: ProductoItem): void {
    this.catalogoService.agregarACesta(item);
    this.mensajeAgregado.set(`«${item.nombre}» añadida a la cesta.`);
    setTimeout(() => this.mensajeAgregado.set(null), 3000);
  }

  protected toggleGuiaAtelier(): void {
    this.guiaAtelierAbierta.update((v) => !v);
  }
}
