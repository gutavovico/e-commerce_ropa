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

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LoginComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly loginService = inject(LoginService);
  private readonly router = inject(Router);

  ngOnInit(): void {
    const usuario = this.loginService.usuarioActual();
    if (usuario) {
      if (usuario.rol === 'administrador') {
        this.router.navigate(['/admin']);
      } else {
        this.router.navigate(['/perfil']);
      }
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
        setTimeout(() => {
          if (resp.rol === 'administrador') {
            this.router.navigate(['/admin']);
          } else {
            this.router.navigate(['/perfil']);
          }
        }, 600);
      },
      error: (err: Error) => {
        this.cargando.set(false);
        this.mensajeError.set(err.message);
      },
    });
  }
}
