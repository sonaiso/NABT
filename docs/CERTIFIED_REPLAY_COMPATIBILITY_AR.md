# مراجعة توافق إعادة تشغيل قطر الندى

كشف فحص GitHub للالتزام `f4fb02868fb191b6d815538f29d62f63f738c9aa` اختلاف بصمة `formal/ProbeJson.lean` عن نسخته المثبتة في تجربة قطر الندى القديمة. التغيير مقصود: رفض مفاتيح JSON المتكررة بعد فك التهريب. لم يتغير قانون قطر الندى أو المعلم أو الأوزان. سجل الإخفاق محفوظ في حزمة هذه المراجعة، ورابطه [تشغيل GitHub الأول](https://github.com/sonaiso/NABT/actions/runs/40377013722).

أضيف ترحيل محدد بالبصمات إلى قبول إعادة التشغيل التاريخية، مع حفظ `run_01` ولقطات شفرته وجميع ملفاته الاثني عشر دون تعديل. يسمح السجل المثبت بتغييري القارئ ومقدمة إعادة التشغيل المعلنين فقط؛ ويرفض تغيير النموذج أو القوانين أو المقاييس أو الملفات التاريخية أو توسيع قائمة التنفيذ. يمر المسار التاريخي بهذه القيود حتى إذا أعيدت كتابة البيان ولقطاته كلها لتطابق التنفيذ الحالي؛ يغطي اختبار مستقل هذا التجاوز. لا تمنح مراجعة البصمات نجاحًا للنموذج؛ تظل مقارنة جميع نتائجه بالمصدر وLean واجبة.

لم يحدث تدريب جديد أو تغيير للإجابات المرجعية أو العتبات. السلوك الجديد يحافظ على بروتوكول التدريب ذي المفاتيح الفريدة، ويشدد رفض JSON غير المقبول؛ فلا ندعي تطابق السلوك لكل مدخل ممكن.

## نتائج الإعادة على ملفات الإصلاح المثبتة

| الفحص | النتيجة المرصودة |
|---|---|
| اختبارات قطر الندى، ومنها عشرة اختبارات للتوافق | 32 نجاحًا، صفر تخطٍ، صفر فشل مع المشغل الأصلي |
| إعادة تشغيل النموذج بالأوزان التاريخية | مطابقة 3417 تنبؤًا |
| التحقق الأصلي للنتائج المشروطة | 3307 قبولًا مشروطًا، 110 رفضًا مشروطًا |
| ربط التنبؤات بمواضع المصدر مستقلًا | 3417/3417 |
| إعادة تشغيل تجربتي المعجم المثبتتين | نجاح كليهما دون تعديل النتائج القديمة |
| فحص معمارية الأساس | 171 سطحًا، منها 161 مدخلًا محروسًا |

القبول اللغوي الكامل في هذه الإعادة **صفر**، وصدق الواقع غير مثبت. المقارنات المشروطة لا تغير النتيجة الأصلية للاستعمال الطبيعي **1/6**، ولا حسم المراد الموجب **0/5**، ولا تثبت اكتمال العربية أو التواتر.

الفحص العام المحلي السابق، **2768 نجاحًا و201 اختبار واجهة**، يخص الحزمة الأصلية عند `f4fb028`. بعد تعديل قبول إعادة التشغيل شُغّلت الفحوص المركزة المذكورة أعلاه على بصمات الملفات الواردة في [سجل التحقق](../evidence/qatr_lean_training/replay_compatibility_v1/verification.json)؛ لا يعاد إسناد الفحص العام القديم إلى شجرة جديدة. تبقى نتائج GitHub للرأس الجديد مستقلة عنه.

## إعادة التحقق

تُستخدم نسخة Python واعتماديات التدريب المثبتة في مسار CI، ونسختا MASAQ ولسان العرب المطابقتان لبصمات المصدر المنشورة. لا يلزم تدريب أو إنشاء بيانات بديلة.

```bash
cd formal
lake build qatrReading
cd ..
PYTHONPATH=src:. NABT_QATR_READING=formal/.lake/build/bin/qatrReading \
  python -m unittest discover -s tests -p 'test_qatr_*.py' -v
PYTHONPATH=src:. python tools/train_qatr_readings.py replay \
  --source artifacts/local/external/MASAQ.csv \
  --lean formal/.lake/build/bin/qatrReading \
  --output-dir evidence/qatr_lean_training/run_01
PYTHONPATH=src:. python tools/check_qatr_artifacts.py \
  --source artifacts/local/external/MASAQ.csv \
  --lean formal/.lake/build/bin/qatrReading \
  --model-dir evidence/qatr_lean_training/run_01
PYTHONPATH=src:. python tools/train_lexical_retrieval.py replay \
  --lisan artifacts/local/lisan.txt --output-dir evidence/lexical_denotation/run_01
PYTHONPATH=src:. python tools/train_lexical_weights.py replay \
  --lisan artifacts/local/lisan.txt --output-dir evidence/lexical_denotation/run_02
PYTHONPATH=src:. python tools/check_foundation_architecture.py \
  --output artifacts/local/certified-natural-use-ci/architecture.json
```

المراجعة التنفيذية في `review.json`، والفروق المحددة في `reviewed_changes.patch`، وسجلات التشغيل والإخفاق الأول في `verification_logs.zip`. هذه إضافة إلى [التقرير الأصلي](CERTIFIED_NATURAL_USE_AR.md)، وليست استبدالًا لأدلته أو رفعًا لرتبة الدعاوى.
