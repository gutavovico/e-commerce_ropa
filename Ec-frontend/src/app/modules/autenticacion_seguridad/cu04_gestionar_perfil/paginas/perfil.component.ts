import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnInit,
  computed,
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
import { Router, RouterLink, RouterLinkActive } from '@angular/router';
import { PerfilService } from '../servicios/perfil.service';
import { LoginService } from '../../cu02_iniciar_sesion/servicios/login.service';
import { PedidoHistorico, PerfilClienteActualizar } from '../modelos/perfil.dto';

@Component({
  selector: 'app-perfil',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, RouterLinkActive],
  templateUrl: './perfil.component.html',
  styleUrls: ['./perfil.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PerfilComponent implements OnInit {
  protected readonly perfilService = inject(PerfilService);
  private readonly loginService = inject(LoginService);
  private readonly router = inject(Router);
  private readonly fb = inject(FormBuilder);
  private readonly cdr = inject(ChangeDetectorRef);

  // Exponer Signals reactivas
  protected readonly perfil = this.perfilService.perfil;
  protected readonly cargando = this.perfilService.cargando;
  protected readonly guardando = this.perfilService.guardando;
  protected readonly error = this.perfilService.error;
  protected readonly mensajeExito = this.perfilService.mensajeExito;
  protected readonly modalAbierto = this.perfilService.modalEdicionAbierto;
  protected readonly pedidos = this.perfilService.pedidos;
  protected readonly cerrandoSesion = signal<boolean>(false);
  protected readonly esAdmin = computed(() => {
    const rolPerfil = this.perfil()?.rol;
    if (rolPerfil === 'administrador') return true;
    if (typeof this.loginService?.usuarioActual === 'function') {
      return this.loginService.usuarioActual()?.rol === 'administrador';
    }
    return false;
  });

  // Formulario reactivo para la actualización de perfil
  protected readonly formularioPerfil: FormGroup = this.fb.group({
    nombres: ['', [Validators.required, Validators.maxLength(100)]],
    apellidos: ['', [Validators.required, Validators.maxLength(100)]],
    telefono: ['', [Validators.maxLength(30)]],
    talla_preferida: [''],
    acepta_marketing: [true],
  });

  // Lista normalizada de tallas de alta costura
  protected readonly tallasDisponibles: string[] = [
    'XS',
    'S',
    'M',
    'L',
    'XL',
    'XXL',
    '36',
    '38',
    '40',
    '42',
    '44',
  ];

  ngOnInit(): void {
    this.cargarDatos();
  }

  /**
   * Carga los datos iniciales del perfil del cliente desde la API.
   */
  cargarDatos(): void {
    this.perfilService.cargarPerfil().subscribe({
      next: (p) => {
        this.sincronizarFormulario(p);
        this.cdr.markForCheck();
      },
      error: () => {
        this.cdr.markForCheck();
      },
    });
  }

  /**
   * Sincroniza los controles del formulario con los datos reactivos del cliente.
   */
  private sincronizarFormulario(p: any): void {
    if (!p) return;
    this.formularioPerfil.patchValue({
      nombres: p.nombres || '',
      apellidos: p.apellidos || '',
      telefono: p.telefono || '',
      talla_preferida: p.talla_preferida || '38',
      acepta_marketing: p.acepta_marketing ?? true,
    });
  }

  /**
   * Despliega el modal de edición de datos de alta costura.
   */
  abrirModal(): void {
    this.sincronizarFormulario(this.perfil());
    this.perfilService.abrirModalEdicion();
    this.cdr.markForCheck();
  }

  /**
   * Cierra el modal de edición.
   */
  cerrarModal(): void {
    this.perfilService.cerrarModalEdicion();
    this.cdr.markForCheck();
  }

  /**
   * Procesa la actualización atómica del perfil en el backend.
   */
  guardarCambios(): void {
    if (this.formularioPerfil.invalid) {
      this.formularioPerfil.markAllAsTouched();
      this.cdr.markForCheck();
      return;
    }

    const val = this.formularioPerfil.getRawValue();
    const payload: PerfilClienteActualizar = {
      nombres: val.nombres?.trim() || undefined,
      apellidos: val.apellidos?.trim() || undefined,
      telefono: val.telefono?.trim() || null,
      talla_preferida: val.talla_preferida ? val.talla_preferida : null,
      acepta_marketing: !!val.acepta_marketing,
    };

    this.perfilService.actualizarPerfil(payload).subscribe({
      next: () => {
        this.cdr.markForCheck();
        setTimeout(() => {
          this.perfilService.limpiarMensajes();
          this.cdr.markForCheck();
        }, 4000);
      },
      error: () => {
        this.cdr.markForCheck();
      },
    });
  }

  /**
   * Cierra la sesión activa del usuario, revoca el token en el backend y redirige al login.
   */
  cerrarSesion(): void {
    if (this.cerrandoSesion()) return;
    this.cerrandoSesion.set(true);
    this.cdr.markForCheck();

    this.loginService.cerrarSesion().subscribe({
      next: () => {
        this.router.navigate(['/login']);
      },
      error: () => {
        this.router.navigate(['/login']);
      },
      complete: () => {
        this.cerrandoSesion.set(false);
        this.cdr.markForCheck();
      },
    });
  }

  /**
   * Acción para simular descarga o visualización de ticket digital.
   */
  descargarFactura(pedido: PedidoHistorico): void {
    alert(`Generando comprobante digital y factura para el pedido ${pedido.id} (${pedido.referencia}).`);
  }

  /**
   * Acción de agendamiento de cita en atelier privado.
   */
  agendarCita(): void {
    alert('Nuestro Concierge de Haute Couture se pondrá en contacto para coordinar su cita privada.');
  }
}
