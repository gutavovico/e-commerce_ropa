import 'package:flutter/material.dart';

/// Tokens de color institucionales de Fashion Store (Haute Couture).
/// Paleta normativa: Obsidian (primary-900), Slate y Camel (secondary-500).
abstract final class AppColors {
  // Primarios y fondos
  static const Color primary900 = Color(0xFF0F172A);
  static const Color primaryDark = Color(0xFF111111);
  static const Color surfaceContainerLowest = Color(0xFFFFFFFF);
  static const Color white = Color(0xFFFFFFFF);
  static const Color black = Color(0xFF000000);

  // Camel / Dorado Alta Costura (secondary-500)
  static const Color secondary500 = Color(0xFFAD8C63);
  static const Color secondaryDark = Color(0xFF8C6E48);
  static const Color secondaryLight = Color(0xFFFAF7F2);
  static const Color secondaryBorder = Color(0xFFECE4D8);

  // Escala Slate
  static const Color slate50 = Color(0xFFF8FAFC);
  static const Color slate100 = Color(0xFFF1F5F9);
  static const Color slate200 = Color(0xFFE2E8F0);
  static const Color slate300 = Color(0xFFCBD5E1);
  static const Color slate400 = Color(0xFF94A3B8);
  static const Color slate500 = Color(0xFF64748B);
  static const Color slate600 = Color(0xFF475569);
  static const Color slate700 = Color(0xFF334155);
  static const Color slate800 = Color(0xFF1E293B);
  static const Color slate900 = Color(0xFF0F172A);

  // Semanticos: Exito (Esmeralda)
  static const Color emerald50 = Color(0xFFECFDF5);
  static const Color emerald100 = Color(0xFFD1FAE5);
  static const Color emerald200 = Color(0xFFA7F3D0);
  static const Color emerald600 = Color(0xFF059669);
  static const Color emerald700 = Color(0xFF047857);

  // Semanticos: Error y Conflicto 409 (Rosa / Carmesi sobrio)
  static const Color rose50 = Color(0xFFFFF1F2);
  static const Color rose100 = Color(0xFFFFE4E6);
  static const Color rose200 = Color(0xFFFECDD3);
  static const Color rose600 = Color(0xFFE11D48);
  static const Color rose700 = Color(0xFFBE123C);
  static const Color rose800 = Color(0xFF9F1239);

  // Semanticos: Advertencia / Reservas (Ambar)
  static const Color amber50 = Color(0xFFFFFBEB);
  static const Color amber100 = Color(0xFFFEF3C7);
  static const Color amber600 = Color(0xFFD97706);
  static const Color amber700 = Color(0xFFB45309);
}

/// Sistema de espaciado matematico Base-2 de Fashion Store (space-1 a space-7).
abstract final class AppSpacing {
  static const double space1 = 2.0;
  static const double space2 = 4.0;
  static const double space3 = 8.0;
  static const double space4 = 16.0;
  static const double space5 = 24.0;
  static const double space6 = 32.0;
  static const double space7 = 64.0;

  // Insets preconstruidos para componentes
  static const EdgeInsets paddingZero = EdgeInsets.zero;
  static const EdgeInsets paddingSpace1 = EdgeInsets.all(space1);
  static const EdgeInsets paddingSpace2 = EdgeInsets.all(space2);
  static const EdgeInsets paddingSpace3 = EdgeInsets.all(space3);
  static const EdgeInsets paddingSpace4 = EdgeInsets.all(space4);
  static const EdgeInsets paddingSpace5 = EdgeInsets.all(space5);
  static const EdgeInsets paddingSpace6 = EdgeInsets.all(space6);

  static const EdgeInsets paddingHorizontalSpace3 =
      EdgeInsets.symmetric(horizontal: space3);
  static const EdgeInsets paddingHorizontalSpace4 =
      EdgeInsets.symmetric(horizontal: space4);
  static const EdgeInsets paddingHorizontalSpace5 =
      EdgeInsets.symmetric(horizontal: space5);

  static const EdgeInsets paddingVerticalSpace2 =
      EdgeInsets.symmetric(vertical: space2);
  static const EdgeInsets paddingVerticalSpace3 =
      EdgeInsets.symmetric(vertical: space3);
  static const EdgeInsets paddingVerticalSpace4 =
      EdgeInsets.symmetric(vertical: space4);

  static const EdgeInsets paddingCard = EdgeInsets.all(space4);
  static const EdgeInsets paddingDialog = EdgeInsets.all(space5);
  static const EdgeInsets paddingSheet = EdgeInsets.all(space5);

  // Espaciadores de caja (SizedBox)
  static const SizedBox gapHSpace1 = SizedBox(width: space1);
  static const SizedBox gapHSpace2 = SizedBox(width: space2);
  static const SizedBox gapHSpace3 = SizedBox(width: space3);
  static const SizedBox gapHSpace4 = SizedBox(width: space4);
  static const SizedBox gapHSpace5 = SizedBox(width: space5);

  static const SizedBox gapVSpace1 = SizedBox(height: space1);
  static const SizedBox gapVSpace2 = SizedBox(height: space2);
  static const SizedBox gapVSpace3 = SizedBox(height: space3);
  static const SizedBox gapVSpace4 = SizedBox(height: space4);
  static const SizedBox gapVSpace5 = SizedBox(height: space5);
  static const SizedBox gapVSpace6 = SizedBox(height: space6);
}

/// Radios de borde normalizados de Fashion Store.
abstract final class AppRadius {
  static const Radius circularSmall = Radius.circular(6.0);
  static const Radius circularMedium = Radius.circular(10.0);
  static const Radius circularLarge = Radius.circular(16.0);
  static const Radius circularSheet = Radius.circular(24.0);

  static const BorderRadius radiusSmall = BorderRadius.all(circularSmall);
  static const BorderRadius radiusMedium = BorderRadius.all(circularMedium);
  static const BorderRadius radiusLarge = BorderRadius.all(circularLarge);
  static const BorderRadius radiusSheet =
      BorderRadius.vertical(top: circularSheet);
}

/// Tipografia institucional Outfit de Fashion Store.
abstract final class AppTypography {
  static const String fontFamily = 'Outfit';

  static const TextStyle h1 = TextStyle(
    fontFamily: fontFamily,
    fontSize: 24,
    fontWeight: FontWeight.w700,
    letterSpacing: -0.5,
    color: AppColors.slate900,
  );

  static const TextStyle h2 = TextStyle(
    fontFamily: fontFamily,
    fontSize: 18,
    fontWeight: FontWeight.w700,
    letterSpacing: -0.3,
    color: AppColors.slate900,
  );

  static const TextStyle h3 = TextStyle(
    fontFamily: fontFamily,
    fontSize: 15,
    fontWeight: FontWeight.w600,
    color: AppColors.slate900,
  );

  static const TextStyle body = TextStyle(
    fontFamily: fontFamily,
    fontSize: 13,
    fontWeight: FontWeight.w400,
    color: AppColors.slate700,
  );

  static const TextStyle bodyMedium = TextStyle(
    fontFamily: fontFamily,
    fontSize: 13,
    fontWeight: FontWeight.w500,
    color: AppColors.slate900,
  );

  static const TextStyle caption = TextStyle(
    fontFamily: fontFamily,
    fontSize: 11,
    fontWeight: FontWeight.w400,
    color: AppColors.slate500,
  );

  static const TextStyle labelSmall = TextStyle(
    fontFamily: fontFamily,
    fontSize: 10,
    fontWeight: FontWeight.w600,
    letterSpacing: 1.0,
    color: AppColors.slate500,
  );

  static const TextStyle tag = TextStyle(
    fontFamily: fontFamily,
    fontSize: 11,
    fontWeight: FontWeight.w600,
    letterSpacing: 0.5,
    color: AppColors.secondary500,
  );

  static const TextStyle button = TextStyle(
    fontFamily: fontFamily,
    fontSize: 12,
    fontWeight: FontWeight.w700,
    letterSpacing: 0.8,
    color: AppColors.white,
  );
}

/// Tema global aglutinador.
abstract final class AppTheme {
  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      fontFamily: AppTypography.fontFamily,
      scaffoldBackgroundColor: AppColors.slate50,
      colorScheme: const ColorScheme.light(
        primary: AppColors.primary900,
        secondary: AppColors.secondary500,
        surface: AppColors.surfaceContainerLowest,
        error: AppColors.rose600,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: AppColors.white,
        foregroundColor: AppColors.slate900,
        elevation: 0,
      ),
    );
  }
}
