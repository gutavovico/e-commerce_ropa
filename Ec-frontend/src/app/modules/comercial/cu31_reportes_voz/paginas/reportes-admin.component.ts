/**
 * Componente de Pagina Editorial para CU31: Generar reportes ejecutivos y consultas por voz.
 * Nomenclatura oficial estricta: "Generar reportes ejecutivos y consultas por voz"
 */

import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ReportesAdminService } from '../servicios/reportes-admin.service';
import { VozReconocimientoService } from '../servicios/voz-reconocimiento.service';
import { LoginService } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import {
  FormatoReporte,
  ModuloReporte,
  RangoTemporal,
  ReporteFiltros,
} from '../modelos/reportes-voz.dto';

@Component({
  selector: 'app-reportes-admin',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './reportes-admin.component.html',
  styleUrls: ['./reportes-admin.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ReportesAdminComponent implements OnInit {
  readonly reportesService = inject(ReportesAdminService);
  readonly vozService = inject(VozReconocimientoService);
  private readonly loginService = inject(LoginService);

  // Estado del usuario activo
  readonly usuario = computed(() => this.loginService.usuarioActual());
  readonly rolUsuario = computed(() =>
    String(this.usuario()?.rol || 'administrador').toLowerCase().trim()
  );
  readonly esAdmin = computed(
    () => this.rolUsuario() === 'administrador' || this.rolUsuario() === 'admin'
  );
  readonly esEncargado = computed(() => this.rolUsuario() === 'encargado_sucursal');

  // Senales reactivas de la vista
  readonly filtros = computed(() => this.reportesService.filtros());
  readonly previsualizacion = computed(() => this.reportesService.previsualizacion());
  readonly generando = computed(() => this.reportesService.generando());
  readonly previsualizando = computed(() => this.reportesService.previsualizando());
  readonly errorServicio = computed(() => this.reportesService.error());
  readonly comandoVozActivo = computed(() => this.reportesService.comandoVozActivo());
  readonly sucursales = computed(() => this.reportesService.sucursales());

  // Senales de voz
  readonly escuchandoVoz = computed(() => this.vozService.escuchando());
  readonly transcripcionVoz = computed(() => this.vozService.transcripcion());
  readonly errorVoz = computed(() => this.vozService.errorVoz());
  readonly soportaVoz = computed(() => this.vozService.soportaVoz());

  // Mensaje de exito o notificacion
  readonly mensajeExito = signal<string | null>(null);

  // Texto editable para comando manual o dictado
  textoComando = signal<string>('');

  ngOnInit(): void {
    // Si el usuario es encargado de sucursal, restringir sucursal fija si aplica
    if (this.esEncargado() && this.usuario()?.id_sucursal) {
      this.reportesService.actualizarFiltros({
        id_sucursal: this.usuario()!.id_sucursal,
      });
    }

    // Cargar catalogo de sucursales
    this.reportesService.cargarSucursales().subscribe({
      next: () => {},
      error: () => {},
    });

    // Cargar previsualizacion inicial
    this.solicitarPrevisualizacion();
  }

  // --- Operaciones de Voz ---

  toggleMicrofono(): void {
    if (this.escuchandoVoz()) {
      this.vozService.detenerEscucha();
      const transcrito = this.transcripcionVoz();
      if (transcrito) {
        this.textoComando.set(transcrito);
      }
    } else {
      this.mensajeExito.set(null);
      this.reportesService.limpiarError();
      this.vozService.iniciarEscucha();
    }
  }

  interpretarComando(texto?: string): void {
    const textoAProcesar = (texto || this.textoComando() || this.transcripcionVoz()).trim();
    if (!textoAProcesar) {
      return;
    }

    this.vozService.detenerEscucha();
    this.textoComando.set(textoAProcesar);

    this.reportesService.interpretarComandoVoz({ texto_dictado: textoAProcesar }).subscribe({
      next: (resultado) => {
        this.mensajeExito.set(
          `Comando interpretado: Modulo ${resultado.modulo.toUpperCase()}, Formato ${resultado.formato.toUpperCase()}, Periodo ${resultado.periodo.toUpperCase()}.`
        );
        this.solicitarPrevisualizacion();

        if (resultado.accion_recomendada === 'ejecutar_exportacion') {
          // Opcional: descarga automatica si la confianza es alta
        }
      },
      error: () => {},
    });
  }

  usarEjemploVoz(ejemplo: string): void {
    this.textoComando.set(ejemplo);
    this.interpretarComando(ejemplo);
  }

  // --- Operaciones de Filtros Manuales ---

  seleccionarModulo(modulo: ModuloReporte): void {
    if (modulo === 'bitacora' && !this.esAdmin()) {
      return;
    }
    this.reportesService.actualizarFiltros({ modulo });
    this.solicitarPrevisualizacion();
  }

  seleccionarFormato(formato: FormatoReporte): void {
    this.reportesService.actualizarFiltros({ formato });
    this.solicitarPrevisualizacion();
  }

  seleccionarPeriodo(periodo: RangoTemporal): void {
    this.reportesService.actualizarFiltros({ periodo });
    this.solicitarPrevisualizacion();
  }

  cambiarSucursal(idSucursalStr: string): void {
    const idSucursal = idSucursalStr ? parseInt(idSucursalStr, 10) : null;
    this.reportesService.actualizarFiltros({ id_sucursal: idSucursal });
    this.solicitarPrevisualizacion();
  }

  actualizarFechaInicio(fecha: string): void {
    this.reportesService.actualizarFiltros({ fecha_inicio: fecha || null });
    this.solicitarPrevisualizacion();
  }

  actualizarFechaFin(fecha: string): void {
    this.reportesService.actualizarFiltros({ fecha_fin: fecha || null });
    this.solicitarPrevisualizacion();
  }

  // --- Previsualizacion y Descarga ---

  solicitarPrevisualizacion(): void {
    this.reportesService.cargarPrevisualizacion().subscribe({
      next: () => {},
      error: () => {},
    });
  }

  descargarReporte(): void {
    this.mensajeExito.set(null);
    this.reportesService.exportarReporte().subscribe({
      next: () => {
        this.mensajeExito.set('El archivo del reporte ha sido generado y descargado exitosamente.');
      },
      error: () => {},
    });
  }

  cerrarAlerta(): void {
    this.mensajeExito.set(null);
    this.reportesService.limpiarError();
  }
}
