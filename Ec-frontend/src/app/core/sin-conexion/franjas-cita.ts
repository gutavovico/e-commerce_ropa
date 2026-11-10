/**
 * P2-CU15 (RN25) · Horas de visita que el cliente puede elegir para una reserva.
 *
 * La reserva vence a las horas que define la empresa, contadas desde que se crea; una cita posterior
 * no llegaría a atenderse y el servidor la rechaza (400 `CITA_FUERA_DE_PLAZO`). Por eso solo se
 * ofrecen horas en punto entre la próxima hora completa (con al menos 1 h de margen) y el
 * vencimiento, dentro del horario de la tienda.
 */
export interface FranjaCita {
  /** Instante en ISO (UTC) para `fecha_hora_atencion`. */
  iso: string;
  etiqueta: string;
}

const HORA_APERTURA = 9;
const HORA_CIERRE = 20;
/** Margen para que el instante de la reserva no supere el vencimiento al llegar al servidor. */
const MARGEN_MINUTOS = 10;

export function franjasDeCita(
  ahora: Date,
  horasVencimiento: number,
  maximo = 8,
  apertura = HORA_APERTURA,
  cierre = HORA_CIERRE
): FranjaCita[] {
  const limite = ahora.getTime() + horasVencimiento * 3_600_000 - MARGEN_MINUTOS * 60_000;
  const cursor = new Date(ahora);
  cursor.setMinutes(0, 0, 0);
  cursor.setHours(cursor.getHours() + 2); // al menos 1 h de margen para llegar a la tienda

  const franjas: FranjaCita[] = [];
  while (cursor.getTime() <= limite && franjas.length < maximo) {
    const hora = cursor.getHours();
    if (hora >= apertura && hora < cierre) {
      franjas.push({ iso: cursor.toISOString(), etiqueta: etiquetaDe(cursor, ahora) });
    }
    cursor.setHours(cursor.getHours() + 1);
  }
  return franjas;
}

function etiquetaDe(fecha: Date, ahora: Date): string {
  const dias = diasEntre(ahora, fecha);
  const dia = dias === 0 ? 'Hoy' : dias === 1 ? 'Mañana' : fecha.toLocaleDateString('es-BO', { weekday: 'long', day: 'numeric' });
  const hora = fecha.toLocaleTimeString('es-BO', { hour: '2-digit', minute: '2-digit', hour12: false });
  return `${dia} ${hora}`;
}

function diasEntre(desde: Date, hasta: Date): number {
  const a = new Date(desde.getFullYear(), desde.getMonth(), desde.getDate()).getTime();
  const b = new Date(hasta.getFullYear(), hasta.getMonth(), hasta.getDate()).getTime();
  return Math.round((b - a) / 86_400_000);
}
