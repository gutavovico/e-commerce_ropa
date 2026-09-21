import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { ColeccionesService } from '../../servicios/colecciones.service';
import { ColeccionResumen, ProductoColeccionItem } from '../../modelos/colecciones.modelos';

@Component({
  selector: 'app-colecciones',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './colecciones.component.html',
  styleUrls: ['./colecciones.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ColeccionesComponent implements OnInit {
  protected readonly coleccionesService = inject(ColeccionesService);
  private readonly router = inject(Router);

  // Signals reactivas del servicio
  protected readonly cargando = this.coleccionesService.cargando;
  protected readonly coleccionDestacada = this.coleccionesService.coleccionDestacada;
  protected readonly otrasColecciones = this.coleccionesService.otrasColecciones;
  protected readonly temporadaActivaNombre = this.coleccionesService.temporadaActivaNombre;
  protected readonly totalColecciones = this.coleccionesService.totalColecciones;
  protected readonly error = this.coleccionesService.error;

  ngOnInit(): void {
    this.coleccionesService.cargarColeccionesActivas().subscribe();
  }

  protected irAColeccion(col: ColeccionResumen): void {
    this.router.navigate(['/colecciones', col.id_coleccion]);
  }

  protected irACatalogo(producto: ProductoColeccionItem): void {
    this.router.navigate(['/buscar'], {
      queryParams: { q: producto.nombre },
    });
  }

  protected onImgError(event: Event): void {
    const img = event.target as HTMLImageElement;
    if (img) {
      img.src =
        'https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=800&auto=format&fit=crop&q=80';
    }
  }

  protected reintentar(): void {
    this.coleccionesService.cargarColeccionesActivas().subscribe();
  }
}
