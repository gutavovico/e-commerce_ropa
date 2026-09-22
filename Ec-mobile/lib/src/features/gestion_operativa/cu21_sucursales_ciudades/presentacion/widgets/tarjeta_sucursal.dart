import 'package:flutter/material.dart';
import 'package:ec_mobile/src/core/theme/app_theme.dart';
import 'package:ec_mobile/src/features/gestion_operativa/cu21_sucursales_ciudades/dominio/entidades/sucursal.dart';

/// Tarjeta de boutique con diseno editorial de alta costura (AC-16, AC-17).
class TarjetaSucursal extends StatelessWidget {
  final Sucursal sucursal;
  final ValueChanged<bool> alAlternarEstado;
  final VoidCallback alEditar;
  final VoidCallback alEliminar;

  const TarjetaSucursal({
    super.key,
    required this.sucursal,
    required this.alAlternarEstado,
    required this.alEditar,
    required this.alEliminar,
  });

  void _confirmarCambioEstado(BuildContext context, bool nuevoEstado) {
    final accion = nuevoEstado ? 'activar' : 'desactivar';
    showDialog<bool>(
      context: context,
      builder: (dialogCtx) {
        return AlertDialog(
          backgroundColor: AppColors.white,
          shape: const RoundedRectangleBorder(
            borderRadius: AppRadius.radiusLarge,
          ),
          title: Text(
            'Confirmar $accion',
            style: AppTypography.h3,
          ),
          content: Text(
            'Desea $accion la boutique "${sucursal.nombre}"? '
            'Esta operacion sera validada contra reservas activas e inventario en custodia.',
            style: AppTypography.body,
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(dialogCtx).pop(false),
              child: Text(
                'CANCELAR',
                style: AppTypography.labelSmall.copyWith(
                  color: AppColors.slate500,
                ),
              ),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor:
                    nuevoEstado ? AppColors.emerald600 : AppColors.rose600,
                foregroundColor: AppColors.white,
                shape: const RoundedRectangleBorder(
                  borderRadius: AppRadius.radiusSmall,
                ),
              ),
              onPressed: () => Navigator.of(dialogCtx).pop(true),
              child: Text(
                'CONFIRMAR',
                style: AppTypography.labelSmall.copyWith(
                  color: AppColors.white,
                ),
              ),
            ),
          ],
        );
      },
    ).then((confirmado) {
      if (confirmado == true) {
        alAlternarEstado(nuevoEstado);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final monograma =
        sucursal.nombre.isNotEmpty ? sucursal.nombre[0].toUpperCase() : 'B';

    return Container(
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: AppRadius.radiusLarge,
        border: Border.all(
          color: AppColors.slate200,
          width: AppSpacing.space1 / 2,
        ),
      ),
      padding: AppSpacing.paddingCard,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 1. Cabecera: Monograma, Nombre, Ciudad y Badge de Estado
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Monograma Editorial
              Container(
                width: AppSpacing.space6 + AppSpacing.space3,
                height: AppSpacing.space6 + AppSpacing.space3,
                decoration: BoxDecoration(
                  color: AppColors.secondaryLight,
                  borderRadius: AppRadius.radiusMedium,
                  border: Border.all(
                    color: AppColors.secondaryBorder,
                    width: AppSpacing.space1 / 2,
                  ),
                ),
                alignment: Alignment.center,
                child: Text(
                  monograma,
                  style: AppTypography.h2.copyWith(
                    color: AppColors.secondary500,
                  ),
                ),
              ),
              AppSpacing.gapHSpace3,

              // Nombre y Ciudad
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Flexible(
                          child: Text(
                            sucursal.nombre,
                            style: AppTypography.h3,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                    AppSpacing.gapVSpace1,
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: AppSpacing.space2,
                        vertical: AppSpacing.space1 / 2,
                      ),
                      decoration: BoxDecoration(
                        color: AppColors.slate100,
                        borderRadius: AppRadius.radiusSmall,
                      ),
                      child: Text(
                        sucursal.ciudadNombre.toUpperCase(),
                        style: AppTypography.caption.copyWith(
                          fontSize: 9,
                          fontWeight: FontWeight.w600,
                          color: AppColors.slate700,
                        ),
                      ),
                    ),
                  ],
                ),
              ),

              // Insignia de Estado Operativo
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.space3,
                  vertical: AppSpacing.space1,
                ),
                decoration: BoxDecoration(
                  color: sucursal.activa
                      ? AppColors.emerald50
                      : AppColors.slate100,
                  borderRadius: AppRadius.radiusSmall,
                  border: Border.all(
                    color: sucursal.activa
                        ? AppColors.emerald200
                        : AppColors.slate300,
                    width: AppSpacing.space1 / 2,
                  ),
                ),
                child: Text(
                  sucursal.activa ? 'ACTIVA' : 'INACTIVA',
                  style: AppTypography.labelSmall.copyWith(
                    fontSize: 9,
                    color: sucursal.activa
                        ? AppColors.emerald700
                        : AppColors.slate500,
                  ),
                ),
              ),
            ],
          ),

          AppSpacing.gapVSpace3,

          // 2. Direccion y Horario
          Row(
            children: [
              const Icon(
                Icons.location_on_outlined,
                size: 14,
                color: AppColors.slate400,
              ),
              AppSpacing.gapHSpace1,
              Expanded(
                child: Text(
                  sucursal.direccion,
                  style: AppTypography.caption,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          AppSpacing.gapVSpace1,
          Row(
            children: [
              const Icon(
                Icons.access_time,
                size: 14,
                color: AppColors.slate400,
              ),
              AppSpacing.gapHSpace1,
              Text(
                '${sucursal.horarioApertura} - ${sucursal.horarioCierre}',
                style: AppTypography.caption.copyWith(
                  fontWeight: FontWeight.w500,
                  color: AppColors.slate700,
                ),
              ),
              if (sucursal.telefono != null) ...[
                const Spacer(),
                const Icon(
                  Icons.phone_outlined,
                  size: 14,
                  color: AppColors.slate400,
                ),
                AppSpacing.gapHSpace1,
                Text(
                  sucursal.telefono!,
                  style: AppTypography.caption,
                ),
              ],
            ],
          ),

          AppSpacing.gapVSpace3,

          // 3. Indicadores de Stock, Personal y Reservas
          Container(
            padding: AppSpacing.paddingSpace2,
            decoration: BoxDecoration(
              color: AppColors.slate50,
              borderRadius: AppRadius.radiusSmall,
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _construirIndicador(
                  etiqueta: 'PERSONAL',
                  valor: sucursal.totalEmpleados.toString(),
                ),
                _construirIndicador(
                  etiqueta: 'STOCK',
                  valor: sucursal.totalPrendasStock.toString(),
                ),
                _construirIndicador(
                  etiqueta: 'RESERVAS',
                  valor: sucursal.reservasActivasConteo.toString(),
                  esAlerta: sucursal.reservasActivasConteo > 0,
                ),
              ],
            ),
          ),

          AppSpacing.gapVSpace3,

          // 4. Barra Inferior: Switch de Activacion (AC-17) y Botones de Accion
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              // Switch de Activacion con dialogo confirmatorio
              Row(
                children: [
                  Switch.adaptive(
                    value: sucursal.activa,
                    activeTrackColor: AppColors.emerald600,
                    activeThumbColor: AppColors.white,
                    onChanged: (val) => _confirmarCambioEstado(context, val),
                  ),
                  Text(
                    sucursal.activa ? 'Operativa' : 'Cerrada',
                    style: AppTypography.caption.copyWith(
                      color: sucursal.activa
                          ? AppColors.emerald700
                          : AppColors.slate500,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),

              // Botones Editar / Eliminar
              Row(
                children: [
                  IconButton(
                    icon: const Icon(Icons.edit_outlined, size: 18),
                    color: AppColors.slate600,
                    onPressed: alEditar,
                    tooltip: 'Editar boutique',
                  ),
                  IconButton(
                    icon: const Icon(Icons.delete_outline, size: 18),
                    color: AppColors.rose600,
                    onPressed: alEliminar,
                    tooltip: 'Eliminar boutique',
                  ),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _construirIndicador({
    required String etiqueta,
    required String valor,
    bool esAlerta = false,
  }) {
    return Column(
      children: [
        Text(
          etiqueta,
          style: AppTypography.labelSmall.copyWith(
            fontSize: 8,
            color: esAlerta ? AppColors.amber700 : AppColors.slate400,
          ),
        ),
        AppSpacing.gapVSpace1,
        Text(
          valor,
          style: AppTypography.bodyMedium.copyWith(
            fontWeight: FontWeight.w700,
            color: esAlerta ? AppColors.amber700 : AppColors.slate900,
          ),
        ),
      ],
    );
  }
}
