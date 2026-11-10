import 'package:flutter/material.dart';

import '../../modulos/sincronizacion/cu14_catalogo_local/presentacion/pantalla_catalogo_sin_conexion.dart';
import '../../modulos/sincronizacion/cu19_sincronizacion/presentacion/pantalla_sincronizacion.dart';
import '../theme/app_theme.dart';
import 'sin_conexion_servicio.dart';

/// P2-CU14 (A4, RN42, RNF15) · Franja del hub, encima de la barra de navegación: sin conexión, con
/// la fecha de los datos guardados y lo pendiente. Con red solo aparece si queda algo por enviar.
class BandaSinConexion extends StatelessWidget {
  final SinConexionServicio servicio;

  const BandaSinConexion({super.key, required this.servicio});

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: servicio,
      builder: (context, _) {
        final pendientes = servicio.pendientes.length;
        if (servicio.clave == null || (servicio.enLinea && pendientes == 0)) return const SizedBox.shrink();
        final guardado = servicio.guardadoEn?.toLocal();
        String d(int n) => n.toString().padLeft(2, '0');
        final partes = <String>[
          if (!servicio.enLinea) 'Sin conexión',
          if (!servicio.enLinea && guardado != null)
            'Datos del ${d(guardado.day)}/${d(guardado.month)} ${d(guardado.hour)}:${d(guardado.minute)}',
          if (pendientes > 0) '$pendientes por sincronizar',
        ];
        return Material(
          key: const Key('banda-sin-conexion'),
          color: servicio.enLinea ? AppColors.amber50 : AppColors.slate900,
          child: Padding(
            padding: AppSpacing.paddingHorizontalSpace4,
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    partes.join(' · '),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: AppTypography.caption.copyWith(
                      color: servicio.enLinea ? AppColors.amber700 : AppColors.white,
                    ),
                  ),
                ),
                if (!servicio.enLinea && servicio.catalogo != null)
                  TextButton(
                    onPressed: () => Navigator.of(context).push(
                        MaterialPageRoute(builder: (_) => PantallaCatalogoSinConexion(servicio: servicio))),
                    child: const Text('Catálogo'),
                  ),
                TextButton(
                  onPressed: () => Navigator.of(context)
                      .push(MaterialPageRoute(builder: (_) => PantallaSincronizacion(servicio: servicio))),
                  child: const Text('Ver'),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
