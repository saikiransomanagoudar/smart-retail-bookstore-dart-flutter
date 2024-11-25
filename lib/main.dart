import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'auth_provider.dart';
import 'app.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final authProvider = AuthProvider();
  await authProvider.loadAuthState();

  runApp(
    ChangeNotifierProvider(
      create: (_) => authProvider,
      child: MyApp(),
    ),
  );
}
