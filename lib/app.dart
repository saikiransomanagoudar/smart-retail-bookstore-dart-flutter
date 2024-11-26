import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'auth_provider.dart';

import 'pages/home.dart';
import 'pages/login.dart';
import 'pages/signup.dart';
import 'pages/auth_callback_page.dart';
import 'pages/user_preferences.dart';
import 'components/navbar.dart';
import 'pages/dashboard.dart';

class MyApp extends StatelessWidget {
  MyApp({super.key});

  final _router = GoRouter(
    initialLocation: '/',
    debugLogDiagnostics: true,
    routes: [
      GoRoute(
        path: '/',
        builder: (context, state) {
          final authProvider = Provider.of<AuthProvider>(context, listen: false);
          return authProvider.isSignedIn ? DashboardPage() : HomePage();
        },
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
        path: '/dashboard',
        builder: (context, state) => AppShell(child: DashboardPage()),
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
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
      ],
      child: MaterialApp.router(
        title: 'Smart Retail Books',
        theme: ThemeData(
          primarySwatch: Colors.blue,
          fontFamily: 'NotoSans',
        ),
        routerConfig: _router,
        debugShowCheckedModeBanner: false,
      ),
    );
  }
}

// AppShell ensures Navbar is displayed on all pages
class AppShell extends StatelessWidget {
  final Widget child;

  const AppShell({Key? key, required this.child}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: PreferredSize(
        preferredSize: const Size.fromHeight(60),
        child: Navbar(), // Navbar widget here
      ),
      body: child,
    );
  }
}

// // Simple Dashboard Page (you can replace this with your actual dashboard)
// class DashboardPage extends StatelessWidget {
//   @override
//   Widget build(BuildContext context) {
//     return Scaffold(
//       body: Center(
//         child: Text(
//           'Welcome to Dashboard',
//           style: TextStyle(fontSize: 24),
//         ),
//       ),
//     );
//   }
// }
