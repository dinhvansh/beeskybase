import 'package:flutter/material.dart';

import 'agent_bridge.dart';
import 'agent_config.dart';
import 'config_page.dart';
import 'theme.dart';

void main() {
  final (bridge, store) = createAgentRuntime();
  runApp(BeeSkyAgentApp(bridge: bridge, store: store));
}

/// Standalone Agent setup and monitoring, backed by the shared Python engine.
class BeeSkyAgentApp extends StatelessWidget {
  final AgentBridge bridge;
  final AgentConfigStore store;
  const BeeSkyAgentApp({super.key, required this.bridge, required this.store});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'BeeSky Agent',
      debugShowCheckedModeBanner: false,
      theme: buildBeeSkyTheme(),
      home: AgentConfigPage(bridge: bridge, store: store),
    );
  }
}
