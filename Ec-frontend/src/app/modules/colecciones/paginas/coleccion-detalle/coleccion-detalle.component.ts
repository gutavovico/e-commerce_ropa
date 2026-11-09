import { TenantService } from '../../../../core/tenant/tenant.service';
import { MarcaTiendaComponent } from '../../../../core/tenant/marca-tienda.component';
import { RutaPortalPipe } from '../../../../core/tenant/ruta-portal.pipe';
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
import { ImportePipe } from '../../../../core/tenant/moneda';

@Component({
  selector: 'app-coleccion-detalle',
  standalone: true,
  imports: [ImportePipe, MarcaTiendaComponent, RutaPortalPipe, CommonModule, RouterLink],
  templateUrl: './coleccion-detalle.component.html',
  styleUrls: ['./coleccion-detalle.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ColeccionDetalleComponent implements OnInit {
  protected readonly coleccionesService = inject(ColeccionesService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly portal = inject(TenantService);

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
        this.router.navigate(this.portal.ruta(['/colecciones']));
      }
    });
  }

  protected irACatalogo(producto: ProductoColeccionItem): void {
    this.router.navigate(this.portal.ruta(['/productos', producto.id_producto]));
  }

  protected reintentar(): void {
    const idStr = this.route.snapshot.paramMap.get('id');
    const id = idStr ? Number(idStr) : null;
    if (id && !isNaN(id)) {
      this.coleccionesService.cargarDetalleColeccion(id).subscribe();
    }
  }
}
