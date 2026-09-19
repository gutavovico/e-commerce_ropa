import {
  ChangeDetectionStrategy,
  Component,
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
import { RegistroService } from '../servicios/registro.service';
import { RegistroClientePeticion } from '../modelos/registro.dto';

@Component({
  selector: 'app-registro',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './registro.component.html',
  styleUrls: ['./registro.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RegistroComponent {
  private readonly fb = inject(FormBuilder);
  private readonly registroService = inject(RegistroService);
  private readonly router = inject(Router);

  // Estados reactivos con Signals
  readonly cargando = signal<boolean>(false);
  readonly mensajeError = signal<string | null>(null);
  readonly exito = signal<boolean>(false);
  readonly mostrarPassword = signal<boolean>(false);

  // Medidor dinámico de fortaleza de contraseña
  readonly fortalezaNivel = signal<number>(0);
  readonly fortalezaTexto = signal<string>('Mín. 8 caracteres');
  readonly nivelSeguridadTexto = signal<string>('SEGURIDAD ALTA');

  // Formulario reactivo fiel a la interfaz de diseño
  readonly formulario: FormGroup = this.fb.group({
    nombreCompleto: [
      '',
      [Validators.required, Validators.minLength(3), Validators.maxLength(150)],
    ],
    email: [
      '',
      [Validators.required, Validators.email, Validators.maxLength(255)],
    ],
    password: [
      '',
      [Validators.required, Validators.minLength(8), Validators.maxLength(128)],
    ],
    terminosAceptados: [false, [Validators.requiredTrue]],
    notificaciones: [true],
  });

  constructor() {
    // Evaluar fortaleza de contraseña en tiempo real
    this.formulario.get('password')?.valueChanges.subscribe((pass: string) => {
      this.evaluarFortaleza(pass || '');
    });
  }

  alternarVisibilidadPassword(): void {
    this.mostrarPassword.update((valor) => !valor);
  }

  evaluarFortaleza(password: string): void {
    if (!password) {
      this.fortalezaNivel.set(0);
      this.fortalezaTexto.set('Mín. 8 caracteres');
      this.nivelSeguridadTexto.set('SEGURIDAD ALTA');
      return;
    }

    let puntuacion = 0;

    if (password.length >= 8) puntuacion += 1;
    if (/[A-Z]/.test(password) && /[a-z]/.test(password)) puntuacion += 1;
    if (/[0-9]/.test(password)) puntuacion += 1;
    if (/[^A-Za-z0-9]/.test(password) || password.length >= 12) puntuacion += 1;

    // Normalizar a rango 1-4 si hay caracteres
    puntuacion = Math.max(1, Math.min(4, puntuacion));

    this.fortalezaNivel.set(puntuacion);

    switch (puntuacion) {
      case 1:
        this.fortalezaTexto.set('1/4 DÉBIL');
        this.nivelSeguridadTexto.set('SEGURIDAD BAJA');
        break;
      case 2:
        this.fortalezaTexto.set('2/4 MEDIA');
        this.nivelSeguridadTexto.set('SEGURIDAD MEDIA');
        break;
      case 3:
        this.fortalezaTexto.set('3/4 ROBUSTA');
        this.nivelSeguridadTexto.set('SEGURIDAD ALTA');
        break;
      case 4:
        this.fortalezaTexto.set('4/4 EXCELENTE');
        this.nivelSeguridadTexto.set('SEGURIDAD MÁXIMA');
        break;
      default:
        this.fortalezaTexto.set('Mín. 8 caracteres');
        this.nivelSeguridadTexto.set('SEGURIDAD ALTA');
    }
  }

  enviarRegistro(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      if (this.formulario.get('terminosAceptados')?.invalid) {
        this.mensajeError.set(
          'Debes aceptar los Términos de Servicio y la Política de Privacidad para continuar.'
        );
      } else {
        this.mensajeError.set(
          'Por favor completa todos los campos requeridos correctamente.'
        );
      }
      return;
    }

    this.cargando.set(true);
    this.mensajeError.set(null);

    const formValues = this.formulario.value;

    // Desglose limpio de Nombre Completo para cumplir el contrato API
    const nombreLimpio = (formValues.nombreCompleto || '').trim();
    const partes = nombreLimpio.split(/\s+/);
    const nombres = partes[0] || 'Cliente';
    const apellidos = partes.length > 1 ? partes.slice(1).join(' ') : 'FashionStore';

    const peticion: RegistroClientePeticion = {
      email: formValues.email.trim().toLowerCase(),
      password: formValues.password,
      nombres: nombres,
      apellidos: apellidos,
      telefono: null,
      talla_preferida: null,
      ciudad_preferida: null,
    };

    this.registroService.registrar(peticion).subscribe({
      next: (respuesta) => {
        this.cargando.set(false);
        this.exito.set(true);

        try {
          localStorage.setItem('fs_token_acceso', respuesta.token_acceso);
          localStorage.setItem(
            'fs_usuario',
            JSON.stringify({
              id_usuario: respuesta.id_usuario,
              email: respuesta.email,
              nombres: respuesta.nombres,
              apellidos: respuesta.apellidos,
              rol: respuesta.rol,
            })
          );
        } catch {
          // Fallback seguro
        }

        setTimeout(() => {
          this.router.navigate(['/']);
        }, 1500);
      },
      error: (err: Error) => {
        this.cargando.set(false);
        this.mensajeError.set(err.message);
      },
    });
  }
}
