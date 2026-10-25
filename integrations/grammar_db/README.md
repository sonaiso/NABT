# فهرس NABT الهجين للمصادر والقواعد

إضافة اختيارية خارج نواة `nabt`: PostgreSQL وpgvector يرتبان **معرّفات مرشحة** من
الفهرس المحلي المتحقق منه. الاقتباس المعروض يُستعاد من بايتات المصدر المحلية،
وتطبيق القاعدة يحتاج مقدماته وشهادته المستقلة. لا يمنح التشابه الدلالي ترخيصًا
نحويًا، ولا يثبت اكتمال العربية أو تحويل الكتب كاملة إلى Lean.

## ما تغير عن مقترح الألفية

- الفهرس يربط طبعة المصدر ومقطعها بالقواعد والشواهد والتصريحات البرهانية بعلاقات
  متعدد إلى متعدد؛ يصلح لقطر الندى ومغني اللبيب وكتاب سيبويه وشروح الألفية،
  ولا يختزل الكتب النثرية إلى جدول أبيات.
- `LaBSE` ينتج 768 بعدًا، فلا يصح تحميله في عمود `vector(384)`. نسجل البعد
  الفعلي ومعرّف النموذج ومراجعة ثابتة وبصمة الفهرس ووصفة الإدخال، ونرفض الخلط.
- نتيجة `1 - cosine_distance` تشابه في المجال `[-1,1]` وليست احتمال صحة.
  نعطي النتائج درجات ترتيب فقط؛ لا يوجد حقل `confidence_score`.
- لا تصفية بباب يتنبأ به LLM ولا `LIMIT 1` ثابت. الترتيب يجمع بحث PostgreSQL
  النصي مع مسافة جيب التمام الاختيارية باستخدام RRF، ثم يطبق حد العرض.
- المسح الدلالي دقيق داخل تشغيل التضمين المثبت. لا ننشئ IVFFlat أو HNSW،
  ولا نستنتج استنفاد قواعد العربية من استنفاد متجهات الفهرس.
- لا نص اعتماديات سحابية في النواة، ولا كلمة مرور داخل الشفرة، ولا تنزيل
  تلقائي لنموذج. قاعدة البيانات ليست مرجع الثقة حتى إذا أعادت بصمة صحيحة.

## المخطط وحدود الثقة

`schema.sql` يحفظ لقطات غير قابلة للتحديث والحذف العادي، وطبعات المصادر،
والمقاطع بحدود بايتاتها ونصوصها الأصلية، والقواعد ذات الأسماء المقيدة بالسجل،
وروابط الاستشهاد وأسماء التصريحات، وعناصر التغطية المنفصلة، ووثائق البحث،
وتشغيلات التضمين. البيانات الوصفية تحفظ حدود المصدر والإسناد وحالة التنفيذ.

تمنع المفاتيح الأجنبية المقاطع والقواعد اليتيمة، وتربط كل متجه ببعد تشغيله
ولقطته. تُرفض المتجهات الصفرية وغير المحدودة وأخطاء الأبعاد. تُحول الاتجاهات
إلى وحدة `float32` لتجنب فيضان حساب مسافة جيب التمام. النموذج لا يغيّر نص المصدر.

هذه القيود تحمي الاتساق التشغيلي؛ مدير قاعدة البيانات يستطيع تغييرها، لذلك
يجب إعادة بناء الفهرس المحلي والتحقق منه قبل إعادة إظهار أي شاهد. الاستيراد
العام يستدعي `validate_catalog` ويستخدم نسخته المعاد بناؤها. محاولة إعادة
استيراد لقطة موجودة تفشل صراحة؛ لا نستبدل صفوفها ولا نفترض سلامتها.

الفهرس يضم شواهد محددة من المعاجم، مع بيان أن النصين الكاملين للسان العرب
ومقاييس اللغة غير مثبتين محليًا. حالة المصدر وقاعدة التطبيق ليستا شيئًا واحدًا.
اسم تصريح Lean في جدول الروابط لا يثبت وحده وفاء ترجمة النص التراثي إلى الصيغة.

## تشغيل محلي اختياري

من جذر المستودع:

```bash
python -m venv .venv-db
. .venv-db/bin/activate
python -m pip install -r integrations/grammar_db/requirements.txt
export PYTHONPATH=src:.

# اختر كلمة مرور محليًا، دون كتابتها في ملف داخل المستودع.
read -r -s -p 'Database password: ' NABT_DB_PASSWORD
export NABT_DB_PASSWORD
export PGPASSWORD="$NABT_DB_PASSWORD"
export NABT_DATABASE_URL='host=127.0.0.1 port=5432 dbname=nabt_catalog user=nabt'
docker compose -f integrations/grammar_db/compose.yaml up -d --wait
python -m integrations.grammar_db load
# انسخ snapshot_sha من نتيجة الاستيراد:
python -m integrations.grammar_db search --snapshot "$SNAPSHOT_SHA" \
  --query 'مبتدأ زيد وعاذر خبر' --limit 10
```

الصورة مثبتة باسم الإصدار وبصمة OCI التي تحققت في 2026-10-25:
`pgvector/pgvector:0.8.7-pg17-bookworm@sha256:ac08538c6f8b9904c33c8224c5e5706dbe760aca29db1d096972b4052c22a75d`.
تُنشئ Compose المخطط عند تهيئة مجلد قاعدة البيانات أول مرة. على خادم موجود
استخدم `python -m integrations.grammar_db init` مرة واحدة بدل خطوة التهيئة.
اعزل دور تهيئة الامتداد والمخطط عن دور التطبيق في النشر الدائم؛ يحتاج دور
القراءة `USAGE` على المخطط و`SELECT` على جداوله فقط. لا تمنح التطبيق دور superuser.

## واجهة الاستخدام والتحقق من المعرفات

```python
from pathlib import Path
import psycopg
from tools.grammar_catalog.catalog import build_catalog
from tools.grammar_catalog.retrieval import SearchIndex
from integrations.grammar_db.client import load_catalog, search

root = Path.cwd()
catalog = build_catalog(root)
local = SearchIndex(catalog, root=root)
with psycopg.connect() as connection:  # libpq environment / local service config
    snapshot = load_catalog(connection, catalog, root)
    proposals = search(connection, snapshot, 'بناء فعل الأمر', k=10)
    restored = local.rehydrate_database(proposals)
```

`search` يعيد المعرف والنوع والدرجات فقط؛ `rehydrate_database` يتحقق من اللقطة
والمعرفات ويستعيد النص محليًا. رفض معرف مجهول أو بصمة مختلفة ليس حكمًا لغويًا.
`NO_CANDIDATES` يعني عدم وجود مرشحين لهذا الاستعلام فقط. حد العرض ليس حدًا
لمتحقق القواعد؛ مسار التحقق الكامل المنفصل لا يعتمد على نجاح البحث.

الإسقاط النصي ومحتوى وثائق البحث مشتركان مع الفهرس المحلي، ويشمل وصف القاعدة
وشواهدها. ترتيب PostgreSQL `ts_rank_cd` ليس BM25 المحلي؛ لا تنقل أرقام benchmark
المحلي إلى هذه الخلفية. يلزم قياس مستقل لكل نموذج/تشغيل وخلفية ترتيب.

## توليد المتجهات اختياري

```bash
python -m pip install -r integrations/grammar_db/requirements-embeddings.txt
# عيّن MODEL_ID و MODEL_COMMIT إلى نموذج SentenceTransformer ومراجعة ثابتة.
python -m integrations.grammar_db.embed_catalog index \
  --model "$MODEL_ID" --revision "$MODEL_COMMIT" --allow-download
python -m integrations.grammar_db.embed_catalog query \
  --model "$MODEL_ID" --revision "$MODEL_COMMIT" --query 'بناء فعل الأمر'
```

لا توجد مراجعة افتراضية عائمة (`main`) ولا افتراض أن AraBERT الخام نموذج تضمين
جُملي معاير. الإدخال وثيقة الفهرس المشتركة بعد الإسقاط النصي، ثم تطبيع الاتجاه
إلى وحدة. الاستعلام يستخدم الإسقاط والنموذج والمراجعة نفسها. `trust_remote_code`
معطل. دون `--allow-download` يجب أن يكون النموذج مخزنًا محليًا. النموذج المثبت
قد يقطع المدخل الطويل إلى حد تسلسله؛ يصرح السكريبت بهذا الحد ولا يدعي استنفادًا.
اعتماديات DB المباشرة مثبتة؛ ملف ML الاختياري لا يمثل قفلًا كاملًا لكل اعتماديات
PyTorch المتعدية. لم ننزّل LaBSE أو نقس جودة تشابهه على العربية ضمن هذه الإضافة.

## الاختبارات والأدلة

```bash
PYTHONPATH=src:. python -m unittest discover -s integrations/grammar_db/tests -v
# خادم اختبار جديد مستقل؛ لا تستخدم قاعدة تشغيل فعلية:
NABT_TEST_DATABASE_URL='host=127.0.0.1 dbname=nabt_test user=nabt_test' \
  PYTHONPATH=src:. python -m unittest discover -s integrations/grammar_db/tests -v
```

المجموعة تشمل أربعة اختبارات تحقق خالصة و12 اختبار خادم: الاستيراد العام من
المصادر المحلية، اتساق العلاقات، استعادة البايتات، البحث الهجين واتجاهات مستقلة
معلومة، المعرفات والبيانات الخبيثة، الأبعاد والقيم غير المحدودة، منع تغيير
اللقطات، والتراجع الذري عن استيراد ناقص. اختبار التضمين يستخدم متجهات اصطناعية
معلومة هندسيًا؛ لا يمثل benchmark لنموذج لغوي.

في بيئة التطوير الحالية نجحت الاختبارات الخالصة؛ اختبارات الخادم تتخطى نفسها
بصراحة إذا غاب `NABT_TEST_DATABASE_URL`. لم يمكن بدء PostgreSQL محليًا بسبب قيود
تغيير هوية المستخدم وعدم توفر Docker. سير العمل
`.github/workflows/grammar-catalog-database.yml` يشغّل المجموعة على خدمة PostgreSQL
فعلية مثبتة. لا يُعلن نجاح فحص الخادم إلا بعد نتيجة ذلك التشغيل.

## مراجع أولية

- [توثيق pgvector: المسح الدقيق والتقريبي والتصفية وإصدارات Docker](https://github.com/pgvector/pgvector)
- [محول pgvector لـ Psycopg 3](https://github.com/pgvector/pgvector-python#psycopg-3)
- [قيود PostgreSQL والعلاقات بين الصفوف](https://www.postgresql.org/docs/current/ddl-constraints.html)
- [بطاقة LaBSE الأصلية: 768 بعدًا](https://huggingface.co/sentence-transformers/LaBSE)
