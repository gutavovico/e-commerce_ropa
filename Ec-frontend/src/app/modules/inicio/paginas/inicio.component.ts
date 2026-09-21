import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  computed,
  inject,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';

import { InicioService } from '../servicios/inicio.service';
import { ProductoRecomendadoItem } from '../modelos/inicio.modelos';
import { PerfilService } from '../../autenticacion_seguridad/cu04_gestionar_perfil/servicios/perfil.service';

@Component({
  selector: 'app-inicio',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './inicio.component.html',
  styleUrls: ['./inicio.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class InicioComponent implements OnInit {
  protected readonly inicioService = inject(InicioService);
  protected readonly perfilService = inject(PerfilService);
  private readonly router = inject(Router);

  // --- Signals derivadas para la vista ---
  protected readonly cargando = this.inicioService.cargando;
  protected readonly tieneHistorial = this.inicioService.tieneHistorial;
  protected readonly recomendaciones = this.inicioService.recomendaciones;
  protected readonly motivoGeneral = this.inicioService.motivoGeneral;
  protected readonly boutiqueReferencia = this.inicioService.boutiqueReferencia;
  protected readonly mensajeEmptyState = this.inicioService.mensajeEmptyState;
  protected readonly totalRecomendados = this.inicioService.totalRecomendados;
  protected readonly error = this.inicioService.error;
  protected readonly cestaCount = this.inicioService.cestaCount;
  protected readonly favoritos = this.inicioService.favoritos;
  protected readonly prendaAgregadaMensaje = this.inicioService.prendaAgregadaMensaje;

  // Saludo dinámico según autenticación y perfil del cliente
  protected readonly estaAutenticado = computed(() => !!this.inicioService.obtenerToken());

  protected readonly nombreUsuario = computed(() => {
    const perfil = this.perfilService.perfil();
    if (perfil && perfil.nombres) {
      return `${perfil.nombres} ${perfil.apellidos}`.trim();
    }
    return 'Ana Valenzuela';
  });

  ngOnInit(): void {
    this.inicioService.cargarRecomendaciones().subscribe();

    if (this.estaAutenticado() && !this.perfilService.perfil()) {
      this.perfilService.cargarPerfil().subscribe({
        error: () => {
          // Si falla la carga del perfil, no interrumpir la navegación en inicio
        },
      });
    }
  }

  protected esFavorito(idProducto: number): boolean {
    return this.favoritos().has(idProducto);
  }

  protected onToggleFavorito(idProducto: number, event: Event): void {
    event.stopPropagation();
    this.inicioService.toggleFavorito(idProducto);
  }

  protected onAgregarACesta(producto: ProductoRecomendadoItem, event: Event): void {
    event.stopPropagation();
    this.inicioService.agregarACesta(producto);
  }

  protected onVerPieza(idProducto: number): void {
    this.router.navigate(['/catalogo'], { queryParams: { producto: idProducto } });
  }

  protected onReintentar(): void {
    this.inicioService.cargarRecomendaciones().subscribe();
  }
}
