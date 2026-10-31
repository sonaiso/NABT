# تشغيل عقد الشرح عبر المدخل الموجود

من جذر NABT، بعد بناء المحقق بالأداة المثبتة:

```bash
lake --dir formal build verifiedReading
python -m tools.entropy_framework reuse --run explainable-pilot -- answer examples/explanation_contracts/source.txt examples/explanation_contracts/query.txt --answer-version v2 --output artifacts/local/explanation-answer.json
python -m tools.entropy_framework reuse --run explainable-pilot -- verify examples/explanation_contracts/source.txt examples/explanation_contracts/query.txt artifacts/local/explanation-answer.json --answer-version v2
```

النتيجة المتوقعة `UNKNOWN` في نطاق الاستلزام من هذا المصدر. في
`explanation.operations` تحفظ القاعدة مقدمتين، وتظهر «سالم هو عادل»
في `missing_full_premises`. أما شاهد «سالم هو حكيم» فموجود. لا يستنتج
البرنامج أن الوصف الغائب كاذب، ولا يمنح وصفًا خارجيًا للشخص.

لعرض جواب مؤيد وسلسلة اعتماده، استعمل مصدر المثال السابق وسؤاله:

```bash
python -m tools.entropy_framework reuse --run explainable-pilot -- answer examples/verified_reading/source.txt examples/verified_reading/query.txt --output artifacts/local/explanation-supported.json
python -m tools.entropy_framework reuse --run explainable-pilot -- verify examples/verified_reading/source.txt examples/verified_reading/query.txt artifacts/local/explanation-supported.json --answer-version v2
```

يمكن تقديم مقترح خارجي بالشكل القائم عبر `answer --certificate FILE`؛
يجري عليه المحقق نفسه. لا توجد مكالمة نموذج لغوي في المثال. لا تعدل
ملف الجواب لحذف مقدمة أو مانع: يعيد `verify` بناء العرض كاملًا ويرفض
اختلافه. عند تغير المصدر يقدم النص الجديد ويعاد إصدار الجواب.

يبقى `--answer-version v1` متاحًا لإنتاج الصيغة السابقة. اشتراط v2
في إعادة الفحص يمنع قبول صيغة لا تحتوي عقد الشرح. لا تغير بصمة المحقق
في جواب تاريخي لكي يوافق بناءً جديدًا؛ أنشئ جوابًا جديدًا بالمحقق الجديد.
