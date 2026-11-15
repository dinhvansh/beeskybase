import 'package:flutter/material.dart';

/// Shared Mine desktop palette: cool neutral surfaces, semantic status colors,
/// compact controls and brand yellow reserved for primary actions.
class BeeSkyColors {
  // Keep both native applications aligned with the cloud shell.
  static const brand = Color(0xFFFACC15); // Brand Primary
  static const brandHover = Color(0xFFEAB308); // Brand Hover
  static const text = Color(0xFF18202E); // Text Primary
  static const muted = Color(0xFF64748B); // Text Secondary
  static const bg = Color(0xFFF6F7F9); // App Background
  static const sidebarBg = Color(0xFFFFFFFF); // Sidebar Background
  static const surface = Color(0xFFFFFFFF); // Surface
  static const border = Color(0xFFDCE1E8); // Border
  static const activeNav = Color(0xFFE8EBF0); // Active Navigation
  static const ok = Color(0xFF16A34A); // Success
  static const warn = Color(0xFFB77908); // Warning
  static const bad = Color(0xFFDC2626); // Error
  static const info = Color(0xFF2563EB); // Info

  // Legacy names, remapped to the light system (call sites keep
  // working unchanged).
  static const panel = surface;
  static const panel2 = bg;
  static const panelGlass = surface;
  static const glassBorder = border;
  static const rimLight = surface; // no rim light on light cards
  static const ghostFill = Color(0xFFF1F3F6);
  static const entryFill = surface;
  static const entryBorder = border;
  static const tableWell = surface;
  static const tableHeading = bg;
  static const tableZebra = Color(0xFFFAFBFC);
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
const double radiusCard = 8;
const double radiusWidget = 6;
const double radiusPill = 6;

/// Numeric values: tabular figures so columns don't jitter.
/// IPs / technical identifiers: monospace fallback stack.
const _tabular = FontFeature.tabularFigures();

TextStyle numStyle({double fontSize = 13, FontWeight? weight, Color? color}) {
  return TextStyle(
    fontFamily: 'BeeSkySans',
    fontSize: fontSize,
    fontWeight: weight,
    color: color,
    fontFeatures: const [_tabular],
  );
}

TextStyle monoStyle({double fontSize = 13, FontWeight? weight, Color? color}) {
  return TextStyle(
    fontFamily: 'BeeSkySans',
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
    visualDensity: VisualDensity.compact,
    splashFactory: InkRipple.splashFactory,
    materialTapTargetSize: MaterialTapTargetSize.padded,
    colorScheme: base.colorScheme.copyWith(
      primary: BeeSkyColors.accentInk,
      onPrimary: BeeSkyColors.accentText,
      surface: BeeSkyColors.surface,
      onSurface: BeeSkyColors.text,
      error: BeeSkyColors.bad,
    ),
    textTheme: base.textTheme.apply(
      bodyColor: BeeSkyColors.text,
      displayColor: BeeSkyColors.text,
      fontFamily: 'BeeSkySans',
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
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        textStyle: const TextStyle(
            fontFamily: 'BeeSkySans', fontWeight: FontWeight.w700),
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
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
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
    tabBarTheme: TabBarThemeData(
      // v0.39.1 fix: bare TabBars (Settings 5 tabs, Presets center)
      // inherited labelColor = colorScheme.primary = #FFE000, so the
      // selected tab — and any tab on hover — rendered yellow text on
      // white (≈1.6:1, unreadable). v0.39.2, owner feedback: labels
      // are plain black, and hover has NO yellow at all — just a
      // neutral pale-grey wash. Yellow survives only as the thin
      // underline indicator (a fill).
      labelColor: BeeSkyColors.text,
      unselectedLabelColor: BeeSkyColors.muted,
      indicatorColor: BeeSkyColors.accent,
      dividerColor: BeeSkyColors.border,
      overlayColor: WidgetStateProperty.resolveWith(
        (states) => states.contains(WidgetState.hovered)
            ? BeeSkyColors.ghostFill
            : Colors.transparent,
      ),
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

/// Shared flat surface retained under its legacy name for existing screens.
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
      ),
      child: Padding(padding: padding, child: child),
    );
  }
}
