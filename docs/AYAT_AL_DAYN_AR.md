# آية الدَّين في NABT

نص الآية في `tools/grammar_catalog/data/ayat_al_dayn/source.txt`. يحتفظ هذا المصدر حرفيًا بالصيغة المقدَّمة ويفصل «يا» عن «أيها»، فينتج ١٢٩ موضعًا. يحصل كل موضع على رقم يبدأ من واحد ومدى نصف مفتوح ببايتات UTF-8. ترجع القراءة إلى نسخة الآية وبصمتها، وتؤجل تحليل نسخة مختلفة إلى أن تتوافر لها محاذاة. تتوافر في المرجع النحوي للمصحف مواضع تبدأ بـ«ياأيها» كلمةً واحدة، لذلك أُثبت إحداثي كل إحالة مراجعة صراحة.

### تشغيل القارئ

من جذر المستودع على فرع التجربة وبعد بناء أدوات بوابة NABT كما في docs/IO_GATEWAY_V1_AR.md:

```sh
export PYTHONPATH=src:.
python -m tools.ayat_demo --port 8282
```

افتح http://127.0.0.1:8282/ . يمر كل طلب في بوابة NABT ويُعاد تشغيله للتحقق من الإيصال. يمكن اختيار موضع من ١ إلى ١٢٩ للسحب ثم إعادة الطلب الأصلي. في جدول الألفاظ تظهر قرارات هوكم وملاحظات المراجعة في حقول مستقلة. يمكن أيضًا إخراج صفحة HTML لقراءة واحدة.

```sh
python -m tools.ayat_demo --export /tmp/ayat.html
python -m tools.grammar_catalog gateway run --request examples/io_gateway/ayat_al_dayn.json --output /tmp/ayat.json
python -m tools.grammar_catalog gateway verify --request examples/io_gateway/ayat_al_dayn.json --receipt /tmp/ayat.json
python -m unittest -v tests.post_segmentation_routing.test_ayat_al_dayn_routing
```

### هوية التشغيل

مستودع المقارنة هو https://github.com/hhiyassat/taaqol-hokom-final-septemper عند `086973036b3bc28f0acb90dd867baa20bbfae5cb` ومراجعة vendor/Taaqol-GPT عند `bc9d1ea5ef45970f5f3ec132441e30fd54b3da52`. شُغِّل `scripts.demo_ayat_al_dayn.run_all(False)` على هذه النسخة. هذه الشجرة غير شجرة التقرير المنقول `45e634d0d12b1df51b3db4a7684baeb7dd52ac6b`. في النسخة المعاد تشغيلها عُدّ ١٢٨ تنفيذًا للبوابة و٣٧ جذرًا معروفًا و٤٠ مؤجلًا و٥١ مجهولًا وموضع واحد مبهم. بلغ عداد H11–H15 في المصدر المعاد تشغيله ٣٣. لا تضاف مواضع التشغيل A0-S البالغ عددها ٣٣٧ إلى مقام عيّنة الآية. تبقى قراءات AWN وAFN وHFN خارج حساب الأحكام في هذه الشريحة.

لاستعادة ملف المشاهدات على حاسوب مستقل، نفّذ مما يلي في نسخة هوكم المثبّتة بعد `git submodule update --init --recursive`، ثم نفّذ أمر الإسقاط من جذر NABT. تُستخدم نسخة Python التي تلائم المشروعين.

```sh
PYTHONPATH=.:src:vendor/Taaqol-GPT/src python -c 'import json; from scripts.demo_ayat_al_dayn import run_all; print(json.dumps(run_all(False), ensure_ascii=False))' > /tmp/hokom-rows.json
python -m pytest -q tests/post_segmentation_routing/test_ayat_al_dayn_routing.py
# From NABT
PYTHONPATH=src:. python -m tools.grammar_catalog.ayat_import /tmp/hokom-rows.json /tmp/ayat-projection.json
cmp /tmp/ayat-projection.json tools/grammar_catalog/data/ayat_al_dayn/hokom.json
```

### بنية التفسير

تُراجع هوية النص ونسخة المشاهدات قبل ربط المواضع. يقرأ موجه الجذر المضيف من شجرة التجزئة، ويتوقف عند مسار مغلق أو غياب مضيف معجمي. فعند «بكم» يُحفظ تركيب الباء والضمير. تُحفظ حالة الجذر ومرشّح الوزن المعروض مستقلين عن حكم الطبقة. في «تداينتم» يمكن مراجعة شاهدي الفعل والمصدر النصّي دون رفع الجذر المؤجل إلى درجة الترخيص في هوكم.

تحدّد ستة عشر قاعدة موضعية أجزاء الآية، وأدواتها، وأدوار ألفاظها، ونطاق كل نسبة. يحوّل الكود العبارات الملتقطة في الأصل إلى بطاقات عربية، ويربط كل بطاقة بعقدة ودليل. هذه قراءة مراجعة مسبقًا لهذه الآية، وتُعدّ بطاقتها الكاملة مدعومة عند حضور جميع شواهد المقطع. لهذا يوقف سحب أي كلمة في المقطع بطاقته الكاملة؛ لا تزعم التجربة أن كل كلمة شرط لغوي أدنى مستقل.

يحصل نموذج التدخلات العصبي المدرَّب سابقًا على الرسم قبل السحب. يرتب الشواهد ويقدّر احتمال فقدان القراءة. يقتبس الجواب أعلى شاهد عصبي اجتاز فحص الانتماء إلى المقطع. تعذّر النموذج يُبقي النص المنضبط للقالب ويُسقط الاقتباس العصبي. الانتماء الفعلي إلى مسار الدليل هو الذي يحدد أثر السحب. تعرض البطاقة الأخيرة ثلاث نسب مستقلة في التقوى والتعليم والعلم. تبقى جهة المضارّة عند «ولا يضارّ» مؤجلة. لا يشتق هذا المسار حكمًا فقهيًا تطبيقيًا.

المرجع المستقل للمراجعات الموضعية هو [Quranic Arabic Corpus، البقرة ٢٨٢](https://corpus.quran.com/wordbyword.jsp?chapter=2&verse=282). يحمل كل موضع مراجع إحداثيه ورابطه. يمكن فحص تصنيف «رَبَّهُ» و«دُعُوا» و«أَلَّا» مع بقاء نتيجة المنتج الأصلي قابلة للقراءة والمقارنة.
