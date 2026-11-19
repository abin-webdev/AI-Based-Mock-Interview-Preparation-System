import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mock_interview/login.dart';
import 'package:mock_interview/company_register.dart';
import 'package:mock_interview/notifications_page.dart';

void main() {
  testWidgets('Login page renders essential authentication UI widgets', (WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: MyLogin()));
    await tester.pumpAndSettle();

    expect(find.text('SIGN IN'), findsWidgets);
    expect(find.byType(ElevatedButton), findsWidgets);
    expect(find.text('New Candidate? '), findsOneWidget);
    expect(find.text('Register Company'), findsOneWidget);
  });

  testWidgets('Company registration screen renders required input fields', (WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: CompanyRegisterPage()));
    await tester.pumpAndSettle();

    // Verify company form header and fields (including offstage scrollable children)
    expect(find.text('Register as Company'), findsOneWidget);
    expect(find.text('Company Information'), findsOneWidget);
    expect(find.text('Company Name *'), findsOneWidget);
    expect(find.text('Corporate Email *', skipOffstage: false), findsOneWidget);
    expect(find.text('Contact Phone Number *', skipOffstage: false), findsOneWidget);
    expect(find.text('Register Company', skipOffstage: false), findsOneWidget);
  });

  testWidgets('Notifications page renders properly with actions', (WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: NotificationsPage()));

    expect(find.text('Notifications'), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
  });
}
