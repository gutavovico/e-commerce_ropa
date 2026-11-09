/**
 * Moneda de la tienda — fix de P2-CU11 (decisiones M1, M6 y M8).
 * Spec: `.specs/finalized/P2-CU11-fix-moneda-zona-bolivia/spec.md`.
 *
 * El backend envía los importes como cadena (Decimal) y nunca se recalculan aquí: solo se les da
 * formato boliviano, `Bs 1.234,50` o `US$ 1.234,50`.
 */
import { Injectable, Pipe, PipeTransform, computed, inject } from '@angular/core';
import { TenantService } from './tenant.service';
import { LoginService } from '../../modules/autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';

export type Moneda = 'BOB' | 'USD';
export const MONEDA_POR_DEFECTO: Moneda = 'BOB';
export const MONEDAS: readonly { valor: Moneda; nombre: string }[] = [
  { valor: 'BOB', nombre: 'Boliviano (Bs)' },
  { valor: 'USD', nombre: 'Dólar estadounidense (US$)' },
];
const SIMBOLOS: Record<string, string> = { BOB: 'Bs', USD: 'US$' };

/** IVA de Bolivia, incluido en el precio (M9). Solo para los textos del desglose. */
export const TASA_IVA_TEXTO = '13 %';

export function simboloMoneda(moneda: string | null | undefined = MONEDA_POR_DEFECTO): string {
  const codigo = moneda || MONEDA_POR_DEFECTO;
  return SIMBOLOS[codigo] ?? codigo;
}

/** `Bs 1.234,50` / `US$ 1.234,50`. Cadena vacía si el valor no es un número. */
export function formatearImporte(
  valor: string | number | null | undefined,
  moneda: string | null | undefined = MONEDA_POR_DEFECTO,
): string {
  if (valor === null || valor === undefined || valor === '') return '';
  const numero = Number(valor);
  if (!Number.isFinite(numero)) return '';
  const [entero, decimales] = Math.abs(numero).toFixed(2).split('.');
  const miles = entero.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return `${numero < 0 ? '-' : ''}${simboloMoneda(moneda)} ${miles},${decimales}`;
}

/**
 * Moneda de la tienda actual: la del portal (`/{codigo}`) o, en el panel, la de la empresa del
 * empleado (sesión del login).
 */
@Injectable({ providedIn: 'root' })
export class MonedaService {
  private readonly tenant = inject(TenantService);
  private readonly login = inject(LoginService);

  readonly actual = computed<string>(() => {
    const deLaTienda = this.tenant.tenantActual?.()?.moneda;
    // Tolerante con dobles de LoginService que no declaran `usuarioActual` (igual que <app-marca-tienda />)
    const usuario = typeof this.login?.usuarioActual === 'function' ? this.login.usuarioActual() : null;
    return deLaTienda ?? usuario?.tenant?.moneda ?? MONEDA_POR_DEFECTO;
  });
}

/** `{{ total | importe }}` o, con la moneda de la respuesta, `{{ total | importe: r.moneda }}`. */
@Pipe({ name: 'importe', standalone: true, pure: false })
export class ImportePipe implements PipeTransform {
  private readonly monedas = inject(MonedaService);

  transform(valor: string | number | null | undefined, moneda?: string | null): string {
    return formatearImporte(valor, moneda || this.monedas.actual());
  }
}

/** `{{ '' | simboloMoneda }}` → `Bs` (etiquetas como «Monto recibido (Bs)»). */
@Pipe({ name: 'simboloMoneda', standalone: true, pure: false })
export class SimboloMonedaPipe implements PipeTransform {
  private readonly monedas = inject(MonedaService);

  transform(_valor?: unknown, moneda?: string | null): string {
    return simboloMoneda(moneda || this.monedas.actual());
  }
}
