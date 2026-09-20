import {
  ChangeDetectionStrategy,
  Component,
  inject,
  OnDestroy,
  OnInit,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { RecuperarPasswordService } from '../servicios/recuperar-password.service';

@Component({
  selector: 'app-recuperar-password',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './recuperar-password.component.html',
  styleUrls: ['./recuperar-password.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RecuperarPasswordComponent implements OnInit, OnDestroy {
  private readonly fb = inject(FormBuilder);
  private readonly recuperarService = inject(RecuperarPasswordService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  // Estados Reactivos con Signals
  readonly pasoActual = signal<'solicitar' | 'restablecer'>('solicitar');
  readonly cargando = signal<boolean>(false);
  readonly mensajeError = signal<string | null>(null);
  readonly mensajeExito = signal<string | null>(null);
  readonly segundosReenvio = signal<number>(0);
  readonly nivelFortaleza = signal<number>(0); // 0 = vacía, 1 = débil, 2 = media, 3 = fuerte
  readonly verPassword = signal<boolean>(false);
  readonly verConfirmarPassword = signal<boolean>(false);

  private temporizadorInterval: any = null;

  // Formulario de Paso 1: Solicitar Código
  readonly formSolicitud: FormGroup = this.fb.group({
    email: ['', [Validators.required, Validators.email, Validators.maxLength(255)]],
  });

  // Formulario de Paso 2: Restablecer Contraseña (Fiel a la imagen)
  readonly formRestablecer: FormGroup = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    codigo: ['', [Validators.required, Validators.minLength(6), Validators.maxLength(8)]],
    nueva_password: ['', [Validators.required, Validators.minLength(8), Validators.maxLength(100)]],
    confirmar_password: ['', [Validators.required, Validators.minLength(8), Validators.maxLength(100)]],
  });

  ngOnInit(): void {
    // Si viene email por queryParams, precargar y avanzar a restablecer
    const emailParam = this.route.snapshot.queryParamMap.get('email');
    if (emailParam) {
      this.formSolicitud.patchValue({ email: emailParam });
      this.formRestablecer.patchValue({ email: emailParam });
      this.pasoActual.set('restablecer');
    }

    // Escuchar cambios en la nueva contraseña para calcular reactivamente la fortaleza
    this.formRestablecer.get('nueva_password')?.valueChanges.subscribe((val: string) => {
      this.calcularFortaleza(val || '');
    });
  }

  ngOnDestroy(): void {
    if (this.temporizadorInterval) {
      clearInterval(this.temporizadorInterval);
    }
  }

  toggleVerPassword(): void {
    this.verPassword.update((v) => !v);
  }

  toggleVerConfirmarPassword(): void {
    this.verConfirmarPassword.update((v) => !v);
  }

  /**
   * Evalúa la robustez de la contraseña (1 a 3 barras).
   */
  private calcularFortaleza(password: string): void {
    if (!password || password.length === 0) {
      this.nivelFortaleza.set(0);
      return;
    }
    let score = 0;
    if (password.length >= 8) score++;
    if (/[a-zA-Z]/.test(password) && /\d/.test(password)) score++;
    if (/[A-Z]/.test(password) && /[^a-zA-Z0-9]/.test(password)) score++;
    this.nivelFortaleza.set(Math.min(score, 3) || 1);
  }

  /**
   * Inicia cuenta regresiva para reenvío de código.
   */
  private iniciarTemporizador(segundos: number = 60): void {
    this.segundosReenvio.set(segundos);
    if (this.temporizadorInterval) {
      clearInterval(this.temporizadorInterval);
    }
    this.temporizadorInterval = setInterval(() => {
      const actual = this.segundosReenvio();
      if (actual <= 1) {
        clearInterval(this.temporizadorInterval);
        this.segundosReenvio.set(0);
      } else {
        this.segundosReenvio.set(actual - 1);
      }
    }, 1000);
  }

  /**
   * Paso 1: Despacha la solicitud de envío de código OTP.
   */
  onSolicitarCodigo(): void {
    if (this.formSolicitud.invalid || this.cargando()) {
      this.formSolicitud.markAllAsTouched();
      return;
    }

    const email = this.formSolicitud.value.email.trim();
    this.cargando.set(true);
    this.mensajeError.set(null);
    this.mensajeExito.set(null);

    this.recuperarService.solicitarCodigo(email).subscribe({
      next: (resp) => {
        this.cargando.set(false);
        this.formRestablecer.patchValue({ email });
        this.pasoActual.set('restablecer');
        this.mensajeExito.set(resp.mensaje);
        this.iniciarTemporizador(resp.tiempo_espera_segundos || 60);
      },
      error: (err) => {
        this.cargando.set(false);
        this.mensajeError.set(
          err.error?.detail || 'No fue posible enviar el código. Intenta nuevamente.',
        );
      },
    });
  }

  /**
   * Reenvío del código OTP desde el paso 2.
   */
  onReenviarCodigo(): void {
    if (this.segundosReenvio() > 0 || this.cargando()) return;

    const email = this.formRestablecer.value.email || this.formSolicitud.value.email;
    if (!email) {
      this.pasoActual.set('solicitar');
      return;
    }

    this.cargando.set(true);
    this.mensajeError.set(null);

    this.recuperarService.solicitarCodigo(email).subscribe({
      next: (resp) => {
        this.cargando.set(false);
        this.mensajeExito.set('Se ha reenviado un nuevo código a tu correo.');
        this.iniciarTemporizador(resp.tiempo_espera_segundos || 60);
      },
      error: (err) => {
        this.cargando.set(false);
        this.mensajeError.set(
          err.error?.detail || 'No se pudo reenviar el código. Intenta más tarde.',
        );
      },
    });
  }

  /**
   * Paso 2: Valida el código y actualiza la contraseña.
   */
  onRestablecerPassword(): void {
    if (this.formRestablecer.invalid || this.cargando()) {
      this.formRestablecer.markAllAsTouched();
      return;
    }

    const { email, codigo, nueva_password, confirmar_password } =
      this.formRestablecer.value;

    if (nueva_password !== confirmar_password) {
      this.mensajeError.set('Las contraseñas no coinciden.');
      return;
    }

    this.cargando.set(true);
    this.mensajeError.set(null);
    this.mensajeExito.set(null);

    this.recuperarService
      .restablecerPassword({
        email: email.trim(),
        codigo: codigo.replace(/\s+/g, '').trim(),
        nueva_password,
        confirmar_password,
      })
      .subscribe({
        next: (resp) => {
          this.cargando.set(false);
          this.mensajeExito.set(resp.mensaje);
          // Redirigir al login tras 2 segundos para dar feedback visual de éxito
          setTimeout(() => {
            this.router.navigate(['/login'], {
              queryParams: { restablecido: 'true' },
            });
          }, 1800);
        },
        error: (err) => {
          this.cargando.set(false);
          this.mensajeError.set(
            err.error?.detail ||
              'No fue posible restablecer la contraseña. Verifica el código e intenta de nuevo.',
          );
        },
      });
  }
}
