import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ColeccionesService } from '../../servicios/colecciones.service';
import { ProductoColeccionItem } from '../../modelos/colecciones.modelos';

@Component({
  selector: 'app-coleccion-detalle',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './coleccion-detalle.component.html',
  styleUrls: ['./coleccion-detalle.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ColeccionDetalleComponent implements OnInit {
  protected readonly coleccionesService = inject(ColeccionesService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  // Signals derivadas del servicio
  protected readonly cargando = this.coleccionesService.cargandoDetalle;
  protected readonly detalle = this.coleccionesService.coleccionDetalle;
  protected readonly error = this.coleccionesService.error;

  ngOnInit(): void {
    this.route.paramMap.subscribe((params) => {
      const idStr = params.get('id');
      const id = idStr ? Number(idStr) : null;
      if (id && !isNaN(id)) {
        this.coleccionesService.cargarDetalleColeccion(id).subscribe();
      } else {
        this.router.navigate(['/colecciones']);
      }
    });
  }

  protected irACatalogo(producto: ProductoColeccionItem): void {
    this.router.navigate(['/productos', producto.id_producto]);
  }

  protected reintentar(): void {
    const idStr = this.route.snapshot.paramMap.get('id');
    const id = idStr ? Number(idStr) : null;
    if (id && !isNaN(id)) {
      this.coleccionesService.cargarDetalleColeccion(id).subscribe();
    }
  }
}
