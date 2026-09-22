import 'package:flutter/material.dart';
import 'package:ec_mobile/src/core/theme/app_theme.dart';
import 'package:ec_mobile/src/features/gestion_operativa/cu21_sucursales_ciudades/dominio/entidades/ciudad.dart';

/// Selector horizontal de ciudades en chips de lujo (AC-17).
class SelectorCiudadesChips extends StatelessWidget {
  final List<Ciudad> ciudades;
  final int? ciudadSeleccionadaId;
  final ValueChanged<int?> alSeleccionarCiudad;

  const SelectorCiudadesChips({
    super.key,
    required this.ciudades,
    required this.ciudadSeleccionadaId,
    required this.alSeleccionarCiudad,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: AppSpacing.space6 + AppSpacing.space2,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        padding: AppSpacing.paddingHorizontalSpace4,
        itemCount: ciudades.length + 1,
        separatorBuilder: (context, index) => AppSpacing.gapHSpace3,
        itemBuilder: (context, index) {
          if (index == 0) {
            final esTodas = ciudadSeleccionadaId == null;
            return _construirChip(
              etiqueta: 'TODAS',
              seleccionado: esTodas,
              alPulsar: () => alSeleccionarCiudad(null),
            );
          }

          final ciudad = ciudades[index - 1];
          final esSeleccionada = ciudadSeleccionadaId == ciudad.idCiudad;
          return _construirChip(
            etiqueta: ciudad.nombre.toUpperCase(),
            contador: ciudad.totalSucursales,
            seleccionado: esSeleccionada,
            alPulsar: () => alSeleccionarCiudad(ciudad.idCiudad),
          );
        },
      ),
    );
  }

  Widget _construirChip({
    required String etiqueta,
    int? contador,
    required bool seleccionado,
    required VoidCallback alPulsar,
  }) {
    return InkWell(
      onTap: alPulsar,
      borderRadius: AppRadius.radiusLarge,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.space4,
          vertical: AppSpacing.space2,
        ),
        decoration: BoxDecoration(
          color:
              seleccionado ? AppColors.primary900 : AppColors.secondaryLight,
          borderRadius: AppRadius.radiusLarge,
          border: Border.all(
            color: seleccionado
                ? AppColors.primary900
                : AppColors.secondaryBorder,
            width: AppSpacing.space1 / 2,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              etiqueta,
              style: AppTypography.labelSmall.copyWith(
                color: seleccionado ? AppColors.white : AppColors.slate700,
                fontWeight:
                    seleccionado ? FontWeight.w700 : FontWeight.w500,
              ),
            ),
            if (contador != null) ...[
              AppSpacing.gapHSpace2,
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.space2,
                  vertical: AppSpacing.space1 / 2,
                ),
                decoration: BoxDecoration(
                  color: seleccionado
                      ? AppColors.secondary500
                      : AppColors.slate200,
                  borderRadius: AppRadius.radiusSmall,
                ),
                child: Text(
                  contador.toString(),
                  style: AppTypography.labelSmall.copyWith(
                    fontSize: 9,
                    color: seleccionado
                        ? AppColors.white
                        : AppColors.slate700,
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
