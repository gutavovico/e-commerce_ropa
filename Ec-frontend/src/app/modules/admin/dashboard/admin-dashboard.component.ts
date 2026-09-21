import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';
import { LoginService } from '../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';

@Component({
  selector: 'app-admin-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive],
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
  readonly esAdmin = computed(() => this.rolUsuario() === 'administrador');
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
        return 'Administrador';
      case 'encargado_sucursal':
        return 'Encargado de Sucursal';
      case 'cajero':
        return 'Cajero';
      default:
        return 'Cliente';
    }
  });

  readonly totalModulosActivos = computed(() =>
    this.esAdmin() ? '4 Activos' : '2 Activos'
  );

  readonly nivelAccesoLabel = computed(() =>
    this.esAdmin() ? 'Superusuario' : 'Encargado de Sede'
  );

  navegar(ruta: string): void {
    this.router.navigate([ruta]);
  }
}
