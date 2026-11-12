import 'package:flutter/material.dart';

/// BeeSky Cloud Light — the v0.39 redesign tokens (docs/redesign-mapping.md).
///
/// The SAME file as the main Flutter app's lib/theme.dart, so all
/// three faces of the product (Tk, main Flutter app, this agent app)
/// share one design system. "BeeSky Cloud Light × Linear × Modern
/// Windows 11 Fluent UI": warm white background, white surfaces,
/// thin #E0E5D9 borders, soft yellow highlights, dark text.
///
/// Contrast rule: pure brand yellow (#FFE000) is a FILL/BORDER
/// color only — never small text on white; accent-as-text call
/// sites use [BeeSkyColors.accentInk] instead.
class BeeSkyColors {
  // Prompt table, 1:1.
  static const brand = Color(0xFFFFE000); // Brand Primary
  static const brandHover = Color(0xFFF5D200); // Brand Hover
  static const text = Color(0xFF202A28); // Text Primary
  static const muted = Color(0xFF7B8877); // Text Secondary
  static const bg = Color(0xFFF7F8F4); // App Background
  static const sidebarBg = Color(0xFFFFFFFF); // Sidebar Background
  static const surface = Color(0xFFFFFFFF); // Surface
  static const border = Color(0xFFE0E5D9); // Border
  static const activeNav = Color(0xFFFFF1B7); // Active Navigation
  static const ok = Color(0xFF16A34A); // Success
  static const warn = Color(0xFFF59E0B); // Warning
  static const bad = Color(0xFFDC2626); // Error
  static const info = Color(0xFF2563EB); // Info

  // Legacy names, remapped to the light system (call sites keep
  // working unchanged).
  static const panel = surface;
  static const panel2 = bg;
  static const panelGlass = surface;
  static const glassBorder = border;
  static const rimLight = surface; // no rim light on light cards
  static const ghostFill = Color(0xFFEFF2EA);
  static const entryFill = surface;
  static const entryBorder = border;
  static const tableWell = surface;
  static const tableHeading = bg;
  static const tableZebra = Color(0xFFFAFBF8);
  static const accent = brand;
  static const accentText = Color(0xFF141414);
  static const accentHover = brandHover;

  /// Dark amber for small yellow-meaning text/icons on light
  /// backgrounds (sort indicators, running-state icons, "MỚI"
  /// pill, focused labels). #FFE000 text on white fails contrast.
  static const accentInk = Color(0xFF7A5A00);

  /// A hashboard at/over the temperature limit (models.tempLimitC),
  /// in the table's NHIỆT cell and the detail panel's board lines.
  static const hotTemp = bad;
  static const selectBg = activeNav;
}

/// 4px spacing scale; radii per the prompt: cards 10–12,
/// buttons 8–9, inputs 8.
const double radiusCard = 12;
const double radiusWidget = 8;
const double radiusPill = 999;

/// Numeric values: tabular figures so columns don't jitter.
/// IPs / technical identifiers: monospace fallback stack.
const _tabular = FontFeature.tabularFigures();

TextStyle numStyle({double fontSize = 13, FontWeight? weight, Color? color}) {
  return TextStyle(
    fontSize: fontSize,
    fontWeight: weight,
    color: color,
    fontFeatures: const [_tabular],
  );
}

TextStyle monoStyle({double fontSize = 13, FontWeight? weight, Color? color}) {
  return TextStyle(
    fontSize: fontSize,
    fontWeight: weight,
    color: color,
    fontFamilyFallback: const ['Consolas', 'Courier New', 'monospace'],
  );
}

ThemeData buildBeeSkyTheme() {
  final base = ThemeData.light(useMaterial3: true);
  const fontFallback = ['Inter', 'Segoe UI', 'Roboto'];
  return base.copyWith(
    scaffoldBackgroundColor: BeeSkyColors.bg,
    colorScheme: base.colorScheme.copyWith(
      primary: BeeSkyColors.accent,
      onPrimary: BeeSkyColors.accentText,
      surface: BeeSkyColors.surface,
      onSurface: BeeSkyColors.text,
      error: BeeSkyColors.bad,
    ),
    textTheme: base.textTheme.apply(
      bodyColor: BeeSkyColors.text,
      displayColor: BeeSkyColors.text,
      fontFamilyFallback: fontFallback,
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: BeeSkyColors.surface,
      foregroundColor: BeeSkyColors.text,
      elevation: 0,
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: BeeSkyColors.entryFill,
      isDense: true,
      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
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
        borderSide: const BorderSide(color: BeeSkyColors.accentInk, width: 1.5),
      ),
      labelStyle: const TextStyle(color: BeeSkyColors.muted),
      floatingLabelStyle: const TextStyle(color: BeeSkyColors.accentInk),
      hintStyle: const TextStyle(color: BeeSkyColors.muted),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: BeeSkyColors.accent,
        foregroundColor: BeeSkyColors.accentText,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(radiusWidget),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
        textStyle: const TextStyle(fontWeight: FontWeight.w700),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        backgroundColor: BeeSkyColors.surface,
        foregroundColor: BeeSkyColors.text,
        side: const BorderSide(color: BeeSkyColors.border),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(radiusWidget),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: BeeSkyColors.accentInk,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(radiusWidget),
        ),
      ),
    ),
    checkboxTheme: CheckboxThemeData(
      fillColor: WidgetStateProperty.resolveWith(
        (states) => states.contains(WidgetState.selected)
            ? BeeSkyColors.accent
            : BeeSkyColors.surface,
      ),
      checkColor: WidgetStateProperty.all(BeeSkyColors.accentText),
      side: const BorderSide(color: BeeSkyColors.border),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
    ),
    popupMenuTheme: const PopupMenuThemeData(
      color: BeeSkyColors.surface,
      surfaceTintColor: Colors.transparent,
    ),
    dialogTheme: const DialogThemeData(
      backgroundColor: BeeSkyColors.surface,
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.all(Radius.circular(radiusCard)),
      ),
    ),
    dividerTheme: const DividerThemeData(color: BeeSkyColors.border),
    snackBarTheme: const SnackBarThemeData(
      backgroundColor: BeeSkyColors.text,
      contentTextStyle: TextStyle(color: BeeSkyColors.surface),
    ),
    progressIndicatorTheme: const ProgressIndicatorThemeData(
      color: BeeSkyColors.accentInk,
    ),
    tooltipTheme: const TooltipThemeData(
      decoration: BoxDecoration(
        color: BeeSkyColors.text,
        borderRadius: BorderRadius.all(Radius.circular(6)),
      ),
      textStyle: TextStyle(color: BeeSkyColors.surface, fontSize: 12),
    ),
  );
}

/// A light card: white surface, 1px thin border, one soft shadow,
/// 12px corners. (v0.39: the dark "glass" card — translucent panel,
/// rim light, heavy shadow — is retired with the dark theme.)
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
            color: Color(0x0F202A28),
            blurRadius: 8,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Padding(padding: padding, child: child),
    );
  }
}
