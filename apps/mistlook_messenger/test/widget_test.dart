import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:mistlook_messenger/main.dart';

void main() {
  testWidgets('Mistlook splash renders', (WidgetTester tester) async {
    await tester.pumpWidget(const ProviderScope(child: MistlookApp()));
    expect(find.text('mistlook'), findsOneWidget);
    expect(find.text('Messages that feel like home.'), findsOneWidget);
    await tester.pump(const Duration(seconds: 1));
    await tester.pump(const Duration(milliseconds: 400));
  });
}
