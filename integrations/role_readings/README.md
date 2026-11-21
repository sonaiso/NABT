# إعادة تحقق الأدوار ومصادرها

من جذر NABT، مع Python 3.12 وLean/Lake بإصدار formal/lean-toolchain، نفذ الأوامر التالية. يضم event.jsonl شواهد التين والهدية والموت، ويضم retained.jsonl طلبات المراحل السابقة وتوقعاتها الأصلية. تُحفظ الملفات الصادرة في مجلد خارج الشجرة.

```sh
sh integrations/usul_ledger/check.sh
sh integrations/awamil_profile/check.sh
PYTHONPATH=src:. python -m unittest tests.test_event_roles tests.test_masdar_frames tests.test_lineage_roles tests.test_named_matrix tests.test_usul_ledger tests.test_genus_chains
PYTHONPATH=src:. python integrations/role_readings/replay.py --suite event --output /tmp/nabt-role-review
PYTHONPATH=src:. python integrations/role_readings/audit_emission.py --suite event --output /tmp/nabt-role-review
PYTHONPATH=src:. python integrations/role_readings/replay.py --suite retained --native-only --output /tmp/nabt-role-review
PYTHONPATH=src:. python integrations/role_readings/audit_patterns.py --output /tmp/nabt-role-review
```

لإعادة فحص الإيصالات الخارجية للمشاهد السابقة، احذف خيار --native-only. تستعمل البوابة الطلب المستقل وتعيد فحص كل مخرج. في الوضع الداخلي يُفحص حساب القضايا بالفاحص الأرضي الأصلي وتُقارَن أحكامه بالتوقعات. يفحص audit_emission.py قوالب المترجم وحالات صدورها في إيصالات المجموعة المختارة، ويفحص audit_patterns.py توليد أوزان المرجع واستردادها. تقرأ المسوغات والحدود في [تعليل الإسناد](../../docs/FOUNDATIONS_OF_EVENT_ROLES_AR.md).
