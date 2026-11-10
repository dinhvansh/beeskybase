import 'dart:async';

import 'package:flutter/material.dart';

import 'home_page.dart';
import 'sidecar.dart';
import 'theme.dart';

void main() {
  runApp(BeeSkyApp(bridge: createBridge()));
}

class BeeSkyApp extends StatelessWidget {
  final BeeSkyBridge bridge;
  const BeeSkyApp({super.key, required this.bridge});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'BeeSky',
      debugShowCheckedModeBanner: false,
      theme: buildBeeSkyTheme(),
      home: SplashGate(bridge: bridge),
    );
  }
}

/// Branded splash — the polish detail the owner pointed at in the
/// HashCore Toolkit: logo, name, tagline and a slim progress line, then
/// a hand-over to the main window (~0.9 s, no fake work behind it: the
/// sysinfo pre-fill happens inside HomePage in parallel).
class SplashGate extends StatefulWidget {
  final BeeSkyBridge bridge;
  const SplashGate({super.key, required this.bridge});

  @override
  State<SplashGate> createState() => _SplashGateState();
}

class _SplashGateState extends State<SplashGate> {
  bool _ready = false;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _timer = Timer(const Duration(milliseconds: 900), () {
      if (mounted) setState(() => _ready = true);
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_ready) return HomePage(bridge: widget.bridge);
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Image.asset('assets/beesky-logo.png', width: 96, height: 96),
            const SizedBox(height: 18),
            const Text(
              'BeeSky',
              style: TextStyle(fontSize: 34, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 6),
            const Text(
              'Giám sát & chẩn đoán máy đào ASIC',
              style: TextStyle(color: BeeSkyColors.muted, fontSize: 14),
            ),
            const SizedBox(height: 28),
            const SizedBox(
              width: 180,
              child: LinearProgressIndicator(minHeight: 3),
            ),
          ],
        ),
      ),
    );
  }
}
