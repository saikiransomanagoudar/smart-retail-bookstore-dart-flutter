// lib/app.dart
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'pages/home.dart';
import 'pages/login.dart';
import 'pages/signup.dart';
import 'pages/auth_callback_page.dart';
import 'pages/user_preferences.dart';

class MyApp extends StatelessWidget {
  MyApp({super.key});

  // In your app.dart router configuration

  final _router = GoRouter(
    initialLocation: '/',
    debugLogDiagnostics: true,
    routes: [
      GoRoute(
        path: '/',
        builder: (context, state) => HomePage(),
      ),
      GoRoute(
        path: '/login',
        builder: (context, state) => LoginPage(),
      ),
      GoRoute(
        path: '/signup',
        builder: (context, state) => SignupPage(),
      ),
      GoRoute(
        path: '/user-preferences',
        builder: (context, state) => UserPreferencesPage(),
      ),
      GoRoute(
        path: '/sign-in/sso-callback',
        builder: (context, state) {
          print('Sign-in callback received');
          return AuthCallbackPage(
            onComplete: () => context.go('/dashboard'),
          );
        },
      ),
      GoRoute(
        path: '/sign-up/sso-callback',
        builder: (context, state) {
          print('Sign-up callback received');
          return AuthCallbackPage(
            onComplete: () => context.go('/dashboard'),
          );
        },
      ),
    ],
  );

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Smart Retail Books',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        fontFamily: 'NotoSans',
      ),
      routerConfig: _router,
      debugShowCheckedModeBanner: false,
    );
  }
}

// Simple Dashboard Page (you can replace this with your actual dashboard)
class DashboardPage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Dashboard'),
      ),
      body: Center(
        child: Text('Welcome to Dashboard'),
      ),
    );
  }
}