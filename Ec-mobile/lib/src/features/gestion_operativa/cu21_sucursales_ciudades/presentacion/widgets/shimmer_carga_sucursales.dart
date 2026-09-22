import 'package:flutter/material.dart';
import 'package:ec_mobile/src/core/theme/app_theme.dart';

/// Widget de carga tipo shimmer para el estado visual de espera (AC-16).
class ShimmerCargaSucursales extends StatelessWidget {
  const ShimmerCargaSucursales({super.key});

  @override
  Widget build(BuildContext context) {
    return ListView.separated(
      padding: AppSpacing.paddingSpace4,
      itemCount: 4,
      separatorBuilder: (context, index) => AppSpacing.gapVSpace3,
      itemBuilder: (context, index) {
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
              Row(
                children: [
                  Container(
                    width: AppSpacing.space6 + AppSpacing.space3,
                    height: AppSpacing.space6 + AppSpacing.space3,
                    decoration: BoxDecoration(
                      color: AppColors.slate100,
                      borderRadius: AppRadius.radiusMedium,
                    ),
                  ),
                  AppSpacing.gapHSpace3,
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          width: 140,
                          height: 14,
                          decoration: BoxDecoration(
                            color: AppColors.slate200,
                            borderRadius: AppRadius.radiusSmall,
                          ),
                        ),
                        AppSpacing.gapVSpace2,
                        Container(
                          width: 80,
                          height: 10,
                          decoration: BoxDecoration(
                            color: AppColors.slate100,
                            borderRadius: AppRadius.radiusSmall,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              AppSpacing.gapVSpace4,
              Container(
                width: double.infinity,
                height: 12,
                decoration: BoxDecoration(
                  color: AppColors.slate100,
                  borderRadius: AppRadius.radiusSmall,
                ),
              ),
              AppSpacing.gapVSpace3,
              Container(
                width: double.infinity,
                height: 36,
                decoration: BoxDecoration(
                  color: AppColors.slate50,
                  borderRadius: AppRadius.radiusSmall,
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
