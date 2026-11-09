import { ChangeDetectionStrategy, Component, DestroyRef, OnInit, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { DatePipe } from '@angular/common';
import { AbstractControl, NonNullableFormBuilder, ReactiveFormsModule, ValidationErrors, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { MarcaTiendaComponent } from '../../../../core/tenant/marca-tienda.component';
import { LoginService } from '../../cu02_iniciar_sesion/servicios/login.service';
import { PerfilEmpleadoService } from '../servicios/perfil-empleado.service';
import { NOMBRES_ROL, PerfilEmpleado } from '../modelos/perfil-empleado.dto';

function contrasenasIguales(grupo: AbstractControl): ValidationErrors | null {
  const nueva = grupo.get('contrasena_nueva')?.value;
  const repetida = grupo.get('repetir')?.value;
  return nueva && repetida && nueva !== repetida ? { noCoinciden: true } : null;
}

/**
 * «Mi perfil» del empleado (`/admin/perfil`): administrador, encargado y cajero.
 * Sustituye al perfil del cliente, que el panel reutilizaba y que el backend rechaza a los empleados.
 */
@Component({
  selector: 'app-perfil-empleado',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, DatePipe, MarcaTiendaComponent],
  templateUrl: './perfil-empleado.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PerfilEmpleadoComponent implements OnInit {
  readonly servicio = inject(PerfilEmpleadoService);
  private readonly loginService = inject(LoginService);
  private readonly fb = inject(NonNullableFormBuilder);
  private readonly destroyRef = inject(DestroyRef);

  readonly error = signal<string | null>(null);
  readonly exito = signal<string | null>(null);

  readonly esCajero = computed(() => {
    const rol = this.servicio.perfil()?.rol ?? this.loginService.usuarioActual?.()?.rol;
    return rol === 'cajero';
  });
  /** El cajero vuelve a su caja; el resto, al panel. */
  readonly volver = computed(() => (this.esCajero() ? '/admin/pos' : '/admin'));
  readonly nombreRol = (rol: string) => NOMBRES_ROL[rol] ?? rol;

  readonly formDatos = this.fb.group({
    nombres: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(100)]],
    apellidos: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(100)]],
    telefono: ['', [Validators.maxLength(30)]],
  });

  readonly formContrasena = this.fb.group(
    {
      contrasena_actual: ['', [Validators.required]],
      contrasena_nueva: ['', [Validators.required, Validators.minLength(8)]],
      repetir: ['', [Validators.required]],
    },
    { validators: [contrasenasIguales] },
  );

  ngOnInit(): void {
    this.servicio
      .cargar()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({ next: (p) => this.aplicar(p), error: (e: Error) => this.error.set(e.message) });
  }

  guardarDatos(): void {
    this.limpiar();
    if (this.formDatos.invalid) {
      this.formDatos.markAllAsTouched();
      return;
    }
    const v = this.formDatos.getRawValue();
    this.servicio
      .actualizar({ nombres: v.nombres, apellidos: v.apellidos, telefono: v.telefono.trim() || null })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (p) => {
          this.aplicar(p);
          this.exito.set('Datos guardados.');
        },
        error: (e: Error) => this.error.set(e.message),
      });
  }

  cambiarContrasena(): void {
    this.limpiar();
    if (this.formContrasena.invalid) {
      this.formContrasena.markAllAsTouched();
      return;
    }
    const v = this.formContrasena.getRawValue();
    this.servicio
      .cambiarContrasena({ contrasena_actual: v.contrasena_actual, contrasena_nueva: v.contrasena_nueva })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.formContrasena.reset();
          this.exito.set('Contraseña cambiada. Úsala la próxima vez que inicies sesión.');
        },
        error: (e: Error) => this.error.set(e.message),
      });
  }

  private aplicar(p: PerfilEmpleado): void {
    this.formDatos.reset({ nombres: p.nombres, apellidos: p.apellidos, telefono: p.telefono ?? '' });
  }

  private limpiar(): void {
    this.error.set(null);
    this.exito.set(null);
  }
}
