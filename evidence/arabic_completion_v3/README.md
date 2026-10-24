# أدلة المرحلة بعد PR 17 — NABT 0.17.0a1

هذه المرحلة تبدأ من إيداع الدمج
`d791fd7730cde2256dfac8a27687010b392876b3`. يشرح
[التقرير العربي](../../docs/ARABIC_COMPLETION_V3.md) موضوع كل دعوى،
وكاشف خطئها، ومصدر الكاشف، وحدود الحكم. تبقى شهادة فهم كل العربية
`NOT_ESTABLISHED`.

## النتائج وحدود مقاماتها

| المقياس | النتيجة | الدلالة |
| --- | ---: | --- |
| التركيبات الأصلية | 82/86 | أربع حالات و30 فحصًا ما زالت مخفقة |
| الخطاب الأصلي | 68/86 | 18 حالة و38 فحصًا ما زالت مخفقة |
| المجموعة الجديدة ذات الحكم الثابت | 14/22 | ثماني حالات مخفقة؛ حالتا تتبع إضافيتان خارج هذا المقام |
| حالات الأجوبة في المجموعة الجديدة | 19/29 | شهادات الأجوبة الـ29 مفحوصة؛ لا تتحول شهادة الامتناع إلى فهم موجب |
| تزوير الشهادات في المجموعة الجديدة | 13 ممارسة و5 غير ممارسة | الخمس ليست نجاحات؛ لم تتوافر مقدمات ممارستها |
| اختبارات Python الرئيسية | 1465 | اجتازت دون تخطٍّ، إضافة إلى مجموعات إعادة الفحص داخل البوابة |
| تدقيق Lean | 1011 تصريحًا | منها 21 لمقطع إنّ؛ ليس هذا عدد قواعد العربية |
| نقل مقطع إنّ التنفيذي | 32/32 | قانون إسناد الحالة الإعرابية داخل المجال المعلن والمعجم المقدم |
| تحقق الحزمة المعزولة | 49/49 | مطابقة ملفات الحزمة وتثبيتها والواجهة؛ ليس تقييم اكتمال لغة |

يبقى `strict_pass=false` في مجموعتي الـ86 والمجموعة الجديدة. اجتياز
بوابة الانحدار يثبت حفظ نتائجها وحدودها المعلنة. لا يثبت استيعاب
العربية أو مصادقة تحصيل المصادر أو صدق الوقائع الخارجية.

## مسار الأدلة

- [الأساس](baseline.json)، و[تجميد التنفيذ](code_freeze_v1.json)،
  و[أرشيف التنفيذ](code_freeze_v1.tar.gz).
- [القياس الصارم النهائي](strict_review_v2/comparison.json)،
  و[سياسة الانحدار](regression_policy_v1.json)،
  و[تحليل كل إخفاق متبقٍ](residual_review_v1/review.md).
- [المحاولة الصارمة الأولى](strict_attempt_v1/attempt.json)،
  و[مراجعة تصويب مدقق الشاهد](source_review/independent_validator_review_v1/postreview.json).
  حُفظت الدرجات الأولى، ولم يتغير التنفيذ أو المرجع الذهبي عند تصحيح المدقق.
- [مادة المجموعة الجديدة قبل التنفيذ](independent_oracle/freeze.json)،
  و[الملاحظة الأولى](independent_oracle/first_run_v1/preservation.json)،
  و[المراجعة المصححة](independent_oracle/postreview_run_v2/review.json)،
  و[مراجعتها المستقلة](independent_oracle/postreview_independent_review_v1/review.md).
- [إعادة التشغيل الفعلية داخل البوابة](oracle_regression_v2.json)،
  و[ربطها بأرشيف الجولة](oracle_regression_preservation_v1.json).
  ثبت تطابق سجل النداءات والمشاهدات الخام كاملًا؛ ليست إعادة التشغيل اختبارًا أعمى جديدًا.
- [نطاق برهان إنّ](formal_scope_review/SCOPE_REVIEW.md)،
  و[مادة واجهته المجمدة](inna_fragment_material_v1/freeze.json)،
  و[نتيجة واجهته](inna_fragment_transport_v2/report.json).
- [التحقق المحلي الكامل](full_validation_v1.json)،
  و[أرشيفه](full_validation_reports_v1.zip): 99 ملفًا، وثمانية تدفقات
  gzip/JSONL مفحوصة كاملة. درجات المجموعة الجديدة محفوظة منفصلة في
  ملفاتها داخل الأرشيف، ولا تضاف إلى درجات الـ86.
- [التحقق المعزول من الحزمة](package_validation_v1.json)،
  و[أرشيفه](package_validation_v1.zip)،
  و[إيصال حفظه](package_validation_receipt_v1.json).
- [متابعة إعداد CI بعد إقفال الجولة](ci_fragment_build_followup_v1/review.json).
  أضيف مسار `--lake` إلى أمر بناء مقطع إنّ وفحصه؛ بقيت المدخلات
  الـ525 الأخرى مطابقة. أُثبت غياب البرنامج التنفيذي قبل الأمر،
  ثم أُعيد بناؤه واجتاز 32/32. يبقى التقرير المحلي القديم دون تعديل،
  وتظل فحوص رأس الفرع وإيداع الدمج على GitHub أدلة مستقلة مطلوبة.
- [سجل تجربة التطوير المبكرة غير الناجحة](development_attempts/observation.json).
  لم تكن تلك تجربة إصدار على مدخلات ثابتة، ولم تستخدم درجتها اعتمادًا نهائيًا.

## إعادة الفحص

من جذر المستودع، مع أداة Lean المثبتة في `formal/lean-toolchain`:

```sh
python evidence/arabic_completion_v3/run_full_validation_v1.py \
  --lake /absolute/path/to/lean-4.34.1-linux/bin/lake \
  --output-dir artifacts/local/arabic-completion-reproduction
```

يجب أن يكون مجلد المخرجات جديدًا. المخرجات السابقة لا تستبدل.
ينفذ البرنامج `make formal check` ويحفظ الجرد قبل التنفيذ وبعده.
يبقى التقرير التاريخي منسوبًا إلى ملفاته وبصماته الأصلية؛ أي تصحيح
لاحق لإعداد CI يوثق بإيصال منفصل، ثم يربط بفحوص الإيداع البعيد.

يشغّل هذا الأمر المجموعة الجديدة وحدها، مع إعادة تنفيذ المنتج فعلًا:

```sh
python evidence/arabic_completion_v3/independent_oracle/run_regression_v2.py \
  --output-dir artifacts/local/arabic-completion-oracle-reproduction
```

تتحقق أداة الحزمة خارج مجلد المصدر بهذه الصورة:

```sh
python tools/verify_construction_package.py \
  --code-freeze evidence/arabic_completion_v3/code_freeze_v1.json \
  --output-dir artifacts/local/arabic-completion-package-reproduction
```

النسخ المصدرية والشواهد مثبتة في `source_review/` وفي سياسة المصادر
المعبأة. سلامة بايتات نسخة رقمية لا تعادل مصادقة عامة على طبعة الكتاب
أو على كل تفسير لغوي مستخلص منها.
