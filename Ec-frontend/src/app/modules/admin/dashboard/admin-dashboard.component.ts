import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink, RouterLinkActive, RouterModule } from '@angular/router';
import { LoginService } from '../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';

@Component({
  selector: 'app-admin-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, RouterLink, RouterLinkActive],
  templateUrl: './admin-dashboard.component.html',
  styleUrls: ['./admin-dashboard.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AdminDashboardComponent {
  private readonly loginService = inject(LoginService);
  private readonly router = inject(Router);

  readonly usuario = computed(() => this.loginService.usuarioActual());
  readonly rolUsuario = computed(() =>
    String(this.usuario()?.rol || 'administrador').toLowerCase().trim()
  );
  readonly esAdmin = computed(
    () => this.rolUsuario() === 'administrador' || this.rolUsuario() === 'admin'
  );
  readonly esEncargado = computed(() => this.rolUsuario() === 'encargado_sucursal');

  readonly usuarioEmail = computed(
    () => this.usuario()?.email || 'administrador@fashionstore.com'
  );
  readonly usuarioNombre = computed(() => {
    const u = this.usuario();
    if (!u) {
      return 'Administrador Corporativo';
    }
    const nombreCompleto = `${u.nombres || ''} ${u.apellidos || ''}`.trim();
    return nombreCompleto || 'Administrador Corporativo';
  });

  readonly rolLabel = computed(() => {
    switch (this.rolUsuario()) {
      case 'administrador':
      case 'admin':
        return 'Administrador';
      case 'encargado_sucursal':
        return 'Encargado de Sucursal';
      case 'cajero':
        return 'Cajero';
      default:
        return 'Cliente';
    }
  });

  readonly totalModulosActivos = computed(() => {
    if (this.esAdmin()) return '13 Activos';
    if (this.esEncargado()) return '10 Activos';
    return '0 Activos';
  });

  readonly nivelAccesoLabel = computed(() =>
    this.esAdmin() ? 'Superusuario' : 'Encargado de Sede'
  );

  navegar(ruta: string, event?: Event): void {
    if (event) {
      event.preventDefault();
    }
    this.router.navigateByUrl(ruta).then((exito) => {
      if (!exito) {
        console.error('[ROUTER] Navegacion rechazada o fallida hacia:', ruta);
        // Intento forzado de navegacion por comandos relativos/absolutos
        this.router.navigate([ruta]);
      }
    }).catch((err) => {
      console.error('[ROUTER] Error al cargar modulo o resolver ruta:', err);
    });
  }
}
