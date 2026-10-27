# أدلة شبكة الدلالة v1

هذه اللقطة تخص إغلاق الرسم المثبت تحت فروض تفسير معلنة، ولا تثبت
استيعاب العربية أو صدق العالم. [التصميم والعقود](../../docs/LEXICAL_GRAPH_AR.md)
و[مراجعة المصادر](../../docs/LEXICAL_GRAPH_SOURCE_REVIEW_AR.md) يحددان نطاقها.

- `graph.json`: الرسم المعاد توليده؛ 91 عقدة و90 قاعدة مشروطة و6 إحالات.
- `source_review.json` و`reference_edges.json`: مواضع المصدر ومحاذاة إحالات التضاد المؤلفة.
- `license_audit.json`: تراخيص القواعد بفاحص `lexicalCompletion` الأصلي.
- `example_request.json` و`example_receipt.json`: تشغيل Lean فعلي؛ إسقاط مكون الخروج دون استنتاج الدخول من إحالة التضاد.
- `benchmark.json`: ثمانية ضوابط مثبتة و4096 حالة Horn اصطناعية مقابل أوراكل مستقل؛ المقامان منفصلان.
- `axioms.json` و`axioms.log`: تدقيق 1456 تصريحًا مع جميع تصريحات مساحة Nabt، بلا مسلمات مشروع.
- `proof_catalog.json`: 1456 تصريحًا في1453 بنية عبارة متميزة؛ الثلاثة أسماء الزائدة تاريخية، لا تكرار جديد.
- ملفات `*_proof_links.json` و`grammar_link_summary.json`: روابط الطبقات إلى الفهرس المترجم الجديد.
- `validation.json` والسجلات المضغوطة: أوامر الفحص، نتائجها، وحدود إعادة التشغيل.

نجح الاكتشاف العام في2261 اختبارًا، مع28 متخطى من2289. أضيفت بعد بدء
ذلك التشغيل ثلاثة اختبارات نقل/طوبولوجيا، ثم اجتاز الملف المركّز النهائي
29/29، بما فيه استنفاد512 رسمًا مستقلًا لفحص المكونات الدورية. لا نضيف
الاختبارات الثلاثة بأثر رجعي إلى عدد تشغيل الاكتشاف العام. اختبارات
PostgreSQL منفصلة؛ انظر حالة تنفيذها في وثيقة امتداد التخزين.

```bash
make formal
make test
make conformance
python tools/check_axioms.py --output artifacts/local/graph/axioms.json
python tools/build_lexical_graph.py --check
python tools/benchmark_lexical_graph.py --output artifacts/local/graph/benchmark.json
make -f Makefile -f integrations/grammar_catalog.mk proof-catalog
make -f Makefile -f integrations/lexical_graph.mk lexical-graph
```

يجب تثبيت الأداة المشار إليها في `formal/lean-toolchain` وتوفير مصدر
لسان العرب المثبت قبل تشغيل المسار العام. يمكن تحديد `LAKE=/path/to/lake`.
تختلف بصمة الملف التنفيذي بحسب بيئة البناء؛ لذلك تسجل كل إعادة فحص
بصمتها، وتثبت المصدر والمواصفة ولا تقارن الملفات التنفيذية بين أنظمة
مختلفة. لم يُشغّل `make check` الشامل في هذه المرحلة ولم يحدث نشر للموقع.
