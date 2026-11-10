import 'package:flutter/material.dart';

/// BeeSky palette — ported 1:1 from the Python design system
/// (beesky/ui_theme.py) so the Flutter app and the Tk fallback look like
/// one product. Radii mirror ui_theme too: 16 cards / 12 widgets / pills.
class BeeSkyColors {
  static const bg = Color(0xFF0B0B0D);
  static const panel = Color(0xFF15151A);
  static const panel2 = Color(0xFF1C1C22);
  static const border = Color(0xFF26262E);
  static const panelGlass = Color(0xFF191920);
  static const glassBorder = Color(0xFF34343E);
  static const rimLight = Color(0xFF3D3D4A);
  static const ghostFill = Color(0xFF22222B);
  static const entryFill = Color(0xFF1E1E26);
  static const entryBorder = Color(0xFF30303C);
  static const tableWell = Color(0xFF121216);
  static const tableHeading = Color(0xFF1D1D24);
  static const tableZebra = Color(0xFF17171D);
  static const accent = Color(0xFFF5D800);
  static const accentText = Color(0xFF141414);
  static const text = Color(0xFFF2F2F3);
  static const muted = Color(0xFF9CA3AF);
  static const ok = Color(0xFF34D399);
  static const warn = Color(0xFFFBBF24);
  static const bad = Color(0xFFF87171);
  static const selectBg = Color(0xFF3A3410);
}

const double radiusCard = 16;
const double radiusWidget = 12;
const double radiusPill = 999;

ThemeData buildBeeSkyTheme() {
  final base = ThemeData.dark(useMaterial3: true);
  return base.copyWith(
    scaffoldBackgroundColor: BeeSkyColors.bg,
    colorScheme: base.colorScheme.copyWith(
      primary: BeeSkyColors.accent,
      onPrimary: BeeSkyColors.accentText,
      surface: BeeSkyColors.panel,
      onSurface: BeeSkyColors.text,
      error: BeeSkyColors.bad,
    ),
    textTheme: base.textTheme.apply(
      bodyColor: BeeSkyColors.text,
      displayColor: BeeSkyColors.text,
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: BeeSkyColors.entryFill,
      isDense: true,
      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(radiusWidget),
        borderSide: const BorderSide(color: BeeSkyColors.entryBorder),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(radiusWidget),
        borderSide: const BorderSide(color: BeeSkyColors.entryBorder),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(radiusWidget),
        borderSide: const BorderSide(color: BeeSkyColors.accent),
      ),
      labelStyle: const TextStyle(color: BeeSkyColors.muted),
      floatingLabelStyle: const TextStyle(color: BeeSkyColors.accent),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: BeeSkyColors.accent,
        foregroundColor: BeeSkyColors.accentText,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(radiusWidget),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
        textStyle: const TextStyle(fontWeight: FontWeight.w700),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        backgroundColor: BeeSkyColors.ghostFill,
        foregroundColor: BeeSkyColors.text,
        side: const BorderSide(color: BeeSkyColors.glassBorder),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(radiusWidget),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      ),
    ),
    dividerTheme: const DividerThemeData(color: BeeSkyColors.border),
    snackBarTheme: const SnackBarThemeData(
      backgroundColor: BeeSkyColors.panel2,
      contentTextStyle: TextStyle(color: BeeSkyColors.text),
    ),
    progressIndicatorTheme: const ProgressIndicatorThemeData(
      color: BeeSkyColors.accent,
    ),
  );
}

/// A "glass" card in the desktop sense used by the Tk app since v0.18:
/// translucent panel tone, 1px glass border, a rim-light top edge and
/// 16px rounded corners. (Real backdrop blur is what the WEB dashboards
/// do with CSS; on desktop this stays a simulated glass like the Tk app.)
class GlassCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  const GlassCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(18),
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: BeeSkyColors.panelGlass,
        borderRadius: BorderRadius.circular(radiusCard),
        border: Border.all(color: BeeSkyColors.glassBorder),
        boxShadow: const [
          BoxShadow(
            color: Color(0x66000000),
            blurRadius: 18,
            offset: Offset(0, 8),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(radiusCard),
        child: Stack(
          children: [
            // Rim light: a hairline highlight along the top edge.
            const Positioned(
              top: 0,
              left: 14,
              right: 14,
              child: Divider(
                height: 1,
                thickness: 1,
                color: BeeSkyColors.rimLight,
              ),
            ),
            Padding(padding: padding, child: child),
          ],
        ),
      ),
    );
  }
}
