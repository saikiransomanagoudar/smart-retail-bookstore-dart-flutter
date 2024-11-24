import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

// Import your pages
import 'components/navbar.dart';
import 'pages/signup.dart';
import 'pages/login.dart';
import 'pages/home.dart';

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    // Configure routes
    final router = GoRouter(
      initialLocation: '/',
      routes: [
        GoRoute(
          path: '/',
          builder: (context, state) => Scaffold(
            appBar: AppBar(
              title: const Text('Smart Retail Books'),
              centerTitle: true,
            ),
            body: HomePage(),
          ),
        ),
        GoRoute(
          path: '/login',
          builder: (context, state) => LoginPage(),
        ),
        GoRoute(
          path: '/signup',
          builder: (context, state) => SignupPage(),
        ),
      ],
      errorBuilder: (context, state) {
        return Scaffold(
          appBar: AppBar(title: const Text('Page Not Found')),
          body: const Center(
            child: Text(
              '404 - Page Not Found',
              style: TextStyle(fontSize: 24),
            ),
          ),
        );
      },
    );

    return MaterialApp.router(
      title: 'Smart Retail Books',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        fontFamily: 'NotoSans',
      ),
      routerDelegate: router.routerDelegate,
      routeInformationParser: router.routeInformationParser,
    );
  }
}
