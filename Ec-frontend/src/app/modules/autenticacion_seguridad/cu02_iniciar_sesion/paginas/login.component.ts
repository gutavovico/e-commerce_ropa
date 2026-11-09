import { TenantService } from '../../../../core/tenant/tenant.service';
import { MarcaTiendaComponent } from '../../../../core/tenant/marca-tienda.component';
import { RutaPortalPipe } from '../../../../core/tenant/ruta-portal.pipe';
import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { LoginService } from '../servicios/login.service';
import { LoginPeticion } from '../modelos/login.dto';
import { destinoEmpleado, esRolEmpleado } from '../../../../core/guards/tenant.guard';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [MarcaTiendaComponent, RutaPortalPipe, CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LoginComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly loginService = inject(LoginService);
  private readonly router = inject(Router);
  private readonly portal = inject(TenantService);

  ngOnInit(): void {
    const usuario = typeof this.loginService.usuarioActual === 'function' ? this.loginService.usuarioActual() : null;
    if (usuario) {
      this.irAlDestino(usuario.rol);
    }
  }

  /**
   * P2-CU02 §B.3 / P2-CU05: el super administrador va a `/admin/plataforma`; el empleado va a su panel;
   * el cliente, a la tienda del portal por el que entró o, desde el login general, al directorio.
   */
  private irAlDestino(rolCrudo: string): void {
    const rol = String(rolCrudo || '').toLowerCase().trim();
    if (rol === 'super_administrador') {
      this.router.navigate(['/admin/plataforma']);
    } else if (esRolEmpleado(rol)) {
      this.router.navigate([destinoEmpleado(rol)]);
    } else if (this.portal.tenantActual()) {
      this.router.navigate(this.portal.ruta(['/inicio']));
    } else {
      this.router.navigate(['/']);
    }
  }

  // Estados reactivos con Signals
  readonly cargando = signal<boolean>(false);
  readonly mensajeError = signal<string | null>(null);
  readonly exito = signal<boolean>(false);
  readonly mostrarPassword = signal<boolean>(false);

  // Formulario reactivo fuertemente tipado
  readonly formulario: FormGroup = this.fb.group({
    email: [
      '',
      [Validators.required, Validators.email, Validators.maxLength(255)],
    ],
    password: [
      '',
      [Validators.required, Validators.minLength(1), Validators.maxLength(128)],
    ],
    recordarDispositivo: [true],
  });

  /**
   * Alterna la visualización de la contraseña entre texto plano y oculto.
   */
  toggleMostrarPassword(): void {
    this.mostrarPassword.update((valor) => !valor);
  }

  /**
   * Procesa el envío del formulario de inicio de sesión.
   */
  onSubmit(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      this.mensajeError.set(
        'Por favor, ingresa tu correo electrónico y tu contraseña para continuar.'
      );
      return;
    }

    this.cargando.set(true);
    this.mensajeError.set(null);

    const valores = this.formulario.getRawValue();
    const peticion: LoginPeticion = {
      email: valores.email.trim(),
      password: valores.password,
      recordar_dispositivo: !!valores.recordarDispositivo,
    };

    this.loginService.iniciarSesion(peticion).subscribe({
      next: (resp) => {
        this.cargando.set(false);
        this.exito.set(true);
        // Redirigir segun el rol del usuario autenticado
        setTimeout(() => this.irAlDestino(resp.rol), 600);
      },
      error: (err: Error) => {
        this.cargando.set(false);
        this.mensajeError.set(err.message);
      },
    });
  }
}
