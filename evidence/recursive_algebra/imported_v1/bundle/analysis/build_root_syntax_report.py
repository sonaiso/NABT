#!/usr/bin/env python3
"""Build the standalone Arabic report; reads verified inputs and writes one HTML file."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import html
import json
import re
from html.parser import HTMLParser

BASE = Path(__file__).resolve().parents[1]
OUTPUT = BASE / 'deliverables/Root_to_Sentence_Licensed_Algebra_2026-10-24.html'
PROOF = BASE / 'proof/RecursiveLicensedAlgebra.lean'
CHECK = json.loads((BASE / 'analysis/recursive_algebra_proof.json').read_text())
assert CHECK['exit_code'] == 0
assert hashlib.sha256(PROOF.read_bytes()).hexdigest() == CHECK['sha256']
assert len(CHECK['theorems']) == CHECK['theorem_count']
CHECKED_AMMAN = datetime.fromisoformat(CHECK['checked_at_utc']).astimezone(ZoneInfo('Asia/Amman')).strftime('%Y-%m-%d %H:%M:%S')

A = 'https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/'
M = 'https://github.com/Saleh1967/Mashru/blob/e4c801ffe9171dadedcc3aae23051ea0953ae361/'
N = 'https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/'
SOURCES = [
 ('Alghanem · RootGrade: مجال الجذر وتعداده وترقيمه', A+'RootGrade.lean#L51-L153'),
 ('Mashru · Root: ترقيم زوج الجذر والوزن', M+'SLGE/Root.lean#L188-L247'),
 ('Alghanem · Hudud: الجنس والخانات والرقم المتباين', A+'Hudud.lean#L51-L180'),
 ('Alghanem · JisrWazaif: جسور الترخيص والاسترجاع والبقية', A+'JisrWazaif.lean#L41-L265'),
 ('Alghanem · Tasrif: النقل العام وترخيص الصيغ المولدة', A+'Tasrif.lean#L544-L595'),
 ('Alghanem · Zawaid: حروف الزيادة والقوالب وتقشير الأصل', A+'Zawaid.lean#L39-L81'),
 ('NABT · Derivation: استرداد الأصل وسلامة قراءات القوالب', N+'formal/Nabt/Derivation.lean#L90-L213'),
 ('NABT · AffixFunctions: وظائف الزيادات وشروطها المعلنة', N+'formal/Nabt/AffixFunctions.lean#L68-L143'),
 ('Alghanem · QismDaraja: من مرشح القسم إلى وحدة مرقمة', A+'QismDaraja.lean#L124-L173'),
 ('NABT · Words: الصفات المعطاة وتصنيف الكلمة والمرشحون', N+'formal/Nabt/Words.lean#L39-L148'),
 ('Mashru · Tarkib: مولد الأطر وترقيم الإطار والكلمات', M+'SLGE/Tarkib.lean#L43-L184'),
 ('Alghanem · FractalTarkib: توريث الإسناد وقانون حد الوصل', A+'FractalTarkib.lean#L65-L147'),
 ('Alghanem · Bawwabat: AND وOR وNOR وXOR والقيمة المجهولة', A+'Bawwabat.lean#L44-L102'),
 ('Alghanem · Bawwabat: شروط السياق والخبر والاستلزام والتكافؤ', A+'Bawwabat.lean#L129-L228'),
 ('Mashru · AdawatMaani: الإباحة والتخيير وشرط XOR', M+'Aql/AdawatMaani.lean#L61-L113'),
 ('Mashru · AdawatMaani: NOR والشرط وعدم انعكاس الاستلزام', M+'Aql/AdawatMaani.lean#L153-L220'),
 ('Mashru · Phi: الشجرة المتكررة وقانون حفظ الواجهة', M+'Nizam/Phi.lean#L455-L515'),
 ('NABT · LicensedDerivation: الشجرة والأصل والخرج والبناة', N+'formal/Nabt/LicensedDerivation.lean#L35-L142'),
 ('NABT · LicensedDerivation: الشواهد وترخيص كل عقدة', N+'formal/Nabt/LicensedDerivation.lean#L159-L259'),
 ('NABT · LicensedDerivation: استعادة المصدر وحفظ المقدمات', N+'formal/Nabt/LicensedDerivation.lean#L446-L520'),
 ('NABT · BinaryUnitDomain: اكتمال المجال الثنائي وضرورة المرشح داخله', N+'formal/Nabt/BinaryUnitDomain.lean#L177-L337'),
 ('NABT · ConstructionEvidence: الحالة الخارجية وبقاء التعيين الداخلي', N+'formal/Nabt/ConstructionEvidence.lean#L125-L132'),
 ('NABT · ConstructionEvidence: هوية الأطراف وشروط علاقة التركيب', N+'formal/Nabt/ConstructionEvidence.lean#L238-L365'),
 ('NABT · Derivation: اصطدام قالبين وحفظ البدائل', N+'formal/Nabt/Derivation.lean#L728-L750'),
]

def ref(*nums):
    return '<span class="refs">' + ' '.join(f'<a href="#s{i}" aria-label="المصدر {i}">[{i}]</a>' for i in nums) + '</span>'

def code(s):
    return '<code dir="ltr">'+html.escape(s)+'</code>'

THEOREM_NOTES = {
 'licensed_induction': 'مبدأ الاستقراء على الشجرة المرخصة، مع فرضيات كل مُنشئ.',
 'certified_realization_sound': 'نقل عقود العلاقة بين الواجهة والصورة إلى كل الشجرة.',
 'certified_iff_all_node_conditions': 'الترخيص يكافئ اجتماع شروط جميع العقد.',
 'unary_rejected_on_interface_mismatch': 'اختلاف واجهة المدخل يمنع ترخيص الخطوة الأحادية.',
 'binary_rejected_on_gate_failure': 'فشل بوابة العقدة الثنائية يمنع ترخيصها.',
 'unary_origins_preserved': 'العملية الأحادية تحفظ قائمة الأصول الداخلية.',
 'binary_origins_preserved': 'العملية الثنائية تحفظ الأصول بترتيب اليسار ثم اليمين.',
 'unary_rank_increases': 'ارتفاع الشجرة يزيد عند البناء الأحادي.',
 'binary_rank_increases': 'ارتفاع الأب أكبر من ارتفاع كل واحد من الولدين.',
 'unary_retains_child': 'يمكن استرجاع الابن الكامل من العقدة الأحادية.',
 'binary_retains_children': 'يمكن استرجاع الولدين المرتبين من العقدة الثنائية.',
 'new_carrier_is_one_outer_unit': 'وضع الوحدة المركبة في قائمة مفردة يجعلها عنصرًا خارجيًا واحدًا.',
 'triangle_mono': 'رتابة الدالة المثلثية المستعملة في الترميز.',
 'pair_injective': 'ترميز الزوج الطبيعي متباين ويسترد المكونين.',
 'seed_number_injective': 'ترقيم البذرة يميز نوعها ومدخلاتها.',
 'tree_number_injective': 'تساوي رقمي الشجرتين يقتضي تساوي بنيتيهما الكاملتين.',
 'unit_number_injective': 'تباين الرقم للوحدات المرخصة ضمن السجل نفسه.',
 'roots_of_different_lengths_have_different_ids': 'وسما الثلاثي والرباعي يمنعان التباس رقميهما.',
 'unary_result_has_new_id': 'نتيجة البناء الأحادي تختلف رقمًا عن ابنها.',
 'binary_rule_tags_are_recovered': 'الرقم يسترد رقم القاعدة والولدين بالترتيب.',
 'and_gate': 'دليلا الشرطين ينتجان دليل اجتماعهما.',
 'or_gate_left': 'دليل فرع يكفي لإثبات وجود بديل مقبول.',
 'nor_gate_iff': 'نفي البديلين يكافئ نفي اتحادهما.',
 'xor_requires_exclusion': 'البوابة الحصرية تستبعد اجتماع الشرطين.',
 'implication_requires_antecedent': 'المقدمة المثبتة مع قاعدة الاستلزام تعطي النتيجة.',
 'implication_alone_insufficient': 'الاستلزام وحده لا يثبت نتيجته على العموم.',
 'ordered_children_are_not_exchangeable': 'تبديل ولدين مختلفين يغير رقم العقدة المرتبة.',
 'candidates_iff': 'التعداد يطابق المخزون المحدد وحد الارتفاع تمامًا.',
 'candidates_monotone': 'زيادة حد الارتفاع تحفظ جميع المرشحين السابقين.',
 'licensed_candidates_iff': 'التصفية تعطي بالضبط المرشحين المرخصين ضمن الحد.',
 'every_finite_licensed_tree_eventually_generated': 'كل شجرة منتهية مرخصة ومدعومة تظهر في مرحلة كافية.',
 'demo_candidate_counts': 'فحص عددي توضيحي: 3 ثم 27 ثم 1515 مرشحًا.',
}
assert set(THEOREM_NOTES) == set(CHECK['theorems'])
IMPORTANT = {'licensed_induction', 'certified_realization_sound', 'tree_number_injective',
             'ordered_children_are_not_exchangeable', 'licensed_candidates_iff',
             'every_finite_licensed_tree_eventually_generated'}

body = f'''
<header>
  <p class="eyebrow">تقرير بنائي وبرهاني · 24 أكتوبر 2026</p>
  <h1>من الجذر إلى الجملة:<br>جبر الوحدات المرخّصة المتكرر</h1>
  <p class="subtitle">جذر ثلاثي أو رباعي، ثم اشتقاق، ثم اسم أو فعل أو حرف، ثم مركب يحمل هويته ويعود مدخلًا لبناء أعلى.</p>
  <div class="status"><span>نواة Lean مستقلة: {CHECK['theorem_count']} مبرهنة مفحوصة</span><span>ثلاثة مستودعات مثبّتة</span><span>24 مرجعًا مباشرًا</span></div>
</header>
<main>
<section class="lead">
<h2>النتيجة التي يثبتها هذا العمل</h2>
<p>المقصود من <b>n</b> هنا هو هوية وحدة بنيت بقاعدة مرخصة: قد تكون جذرًا، أو كلمة مشتقة، أو مركبًا اسميًا، أو جملة تدخل في جملة أخرى. تنجح الفكرة عندما يبقى داخل الوحدة سجل تكوينها، وتظهر خارجها واجهة تحدد ما يمكن أن يتركب معها. بذلك يصير الناتج عنصرًا واحدًا بالنسبة إلى الدرجة التالية، مع بقاء أبنائه وأصله قابلين للاسترجاع.</p>
<p>التصحيح الأساسي لقراءة المصادر هو أن <b>الترقيم والبوابات موجودان فعلًا</b>. في Alghanem ترقيم للوحدات وجسور ترخيص وتصريف عام؛ وفي Mashru ترقيم للجذر والوزن وأطر للتركيب وبوابات منطق؛ وفي NABT، بعد PR14، شجرة اشتقاق مرخصة تحفظ المصدر والمقدمات. المطلوب الآن وصل هذه الإنجازات في سلسلة اشتقاق وتركيب واحدة ذات عقود واضحة. {ref(2,3,4,15,18,19)}</p>
<p>أُنشئت لهذا الغرض نواة مستقلة، <b>RecursiveLicensedAlgebra.lean</b>، واكتمل فحصها بنجاح. تعطي النواة البناء المتكرر وهوية الشجرة والاستقراء والاستنفاد المحدود؛ وتترك قواعد العربية وشواهدها معلمات يجب تقديمها وإثبات عقودها. <b>لم يُدمج هذا الملف المستقل في أي من المستودعات.</b></p>
</section>

<section>
<h2>1. ما الذي تحمله الوحدة عند كل درجة؟</h2>
<p>الحامل في المستوى الأعلى هو الشجرة كلها. أما «الحالة» و«الموضع» و«البقية» فهي واجهة تشرح إمكان استعمال ذلك الحامل. ولا يلزم أن تعني الحالة الأعلى حركةً صوتية؛ قد تمثل حالة إعرابية أو وضعًا اشتقاقيًا، بحسب تعريف القاعدة. وكذلك الموضع التركيبي يختلف عن إحداثيات وقوع الكلمة في نص بعينه.</p>
<table><thead><tr><th>المكوّن</th><th>المعنى العملي</th><th>مثال</th></tr></thead><tbody>
<tr><td>الحامل</td><td>البناء الكامل مع جذره وقاعدته وأبنائه المرتبين.</td><td>كلمة «كاتب» مع اشتقاقها؛ أو «في الدار» مع طرفيها.</td></tr>
<tr><td>الحالة</td><td>وسم مطلوب عند واجهة القاعدة، يثبت أثره بعقد.</td><td>اسم مجرور؛ فعل مجزوم؛ مركب مكتمل أو مفتوح.</td></tr>
<tr><td>الموضع</td><td>دور الوحدة أو منفذها في العلاقة التالية.</td><td>فاعل، خبر، مضاف إليه، طرف جواب الشرط.</td></tr>
<tr><td>البقية</td><td>المعلومات والطلبات التي يجب إبقاؤها عند الرفع.</td><td>متعلَّق الجار، فاعل مطلوب، أو صفة تحفظ أصلًا محذوفًا.</td></tr>
</tbody></table>
<p>يفيد عقد <code dir="ltr">JisrWazaif</code> هنا مباشرة: له ترميز وفك ترميز وقانون رجوع ونقل للترخيص. ويثبت استرداد أصل الماضي من خاناته مع صفة الأصل؛ كما يثبت أن إسقاط هذه الصفة قد يجعل الاسترجاع العام مستحيلًا. وفي Mashru يحفظ شرط الواجهة المتغيرات التي يحتاجها التركيب التالي. البقية إذن جزء من صحة البناء، وليست تعليقًا اختياريًا. {ref(4,17)}</p>
<p>في النواة الجديدة حقول <code dir="ltr">Face</code> معطاة صراحة. إدخال وسم «مجرور» لا يكتسب الجر من النص، وإدخال بقية لا يثبت أنها استوفيت. تتولى القاعدة وشهادتها هذا الربط، بينما يضمن الجبر حفظ ما عُرّف وثبت.</p>
</section>

<section>
<h2>2. هوية n ودرجة الجذر ونسخة القواعد</h2>
<p>ينبغي فصل رقم الهوية عن قياس الحجم. عدد أصول الجذر ثلاثة أو أربعة، وعدد خلايا الناتج قد يزيد، وارتفاع شجرة اشتقاقه مقياس ثالث. أما <b>n</b> فاسم بنيوي قابل للتمييز، لا عدد الحروف ولا حكمًا على معنى الكلمة.</p>
<p>يحصي RootGrade جميع قوائم الأصول على المجال المحدد، ويبرهن اكتمال التعداد بالنسبة إلى الطول. ترقيم Mashru للجذر والوزن يعمل داخل درجة معلومة؛ لذلك يجب حفظ الدرجة مع الرقم عند جمع الدرجات. وفي Hudud، الرقم متباين على سجل «الجنس والخانات»، وهو إنجاز مناسب لهوية ذلك السجل. {ref(1,2,3)}</p>
<div class="formula">n(tree₁) = n(tree₂) ⟹ tree₁ = tree₂</div>
<p>النواة المستقلة ترفع الهوية إلى <b>شجرة الاشتقاق</b>: يدخل في الترميز وسم البذرة الثلاثية أو الرباعية أو المعجمية، ثم أرقام القواعد والأبناء بالترتيب. التكوين نفسه يعطى الرقم نفسه؛ وتكراره في موضعين من نص يحتاج هوية وقوع إضافية.</p>
<p>هذا الترميز بالنسبة إلى سجل قواعد ثابت. وعند تبادل الأرقام بين نسخ المشروع، يكون الغلاف المقترح «معرف السجل، نسخته، الرقم البنيوي». النسخة ليست مضمّنة حاليًا في <code dir="ltr">Tree.n</code>. وسم الثلاثي/الرباعي موجود في البذرة، والدرجة الأعلى تستعاد من الشجرة المحفوظة؛ فلا يسقط اختلاف النوع أو الدرجة بمجرد تشابه رقم محلي.</p>
<p>تفرد الرقم لا يساوي تفرد تحليل الصورة. يثبت NABT أن صورة واحدة قد توافق قالبين بجذرين مختلفين، ويحفظ البديلين. إذا أريد تحليل وحيد وجب استنفاد البدائل المرخصة وتبيين ما يستبعدها، مع بقاء رقم كل تحليل متباينًا. {ref(24)}</p>
</section>

<section>
<h2>3. من الجذر إلى الكلمة: الزيادة عملية منظمة</h2>
<p>يبدأ المسار بجذر مرتب ومعلوم الدرجة، وشهادة دخوله في المجال. ثم تطبق قاعدة لها مواضع أصلية ومواضع زيادة وحالات وشروط. ترخيص الجذر مستقل عن ترخيص العملية عليه؛ وكذلك وجود الحرف في «سألتمونيها» لا يجعله زائدًا في كل وقوع، ولا يرخص وضعه في كل موضع. {ref(1,6)}</p>
<table><thead><tr><th>العملية</th><th>مثال توضيحي</th><th>ما تحفظه العقدة</th></tr></thead><tbody>
<tr><td>تعيين الحالات</td><td>كَتَبَ / كُتِبَ</td><td>الجذر وترتيبه وقاعدة توزيع الحالات.</td></tr>
<tr><td>زيادة داخل القالب</td><td>ك ت ب ← كاتب</td><td>الألف المضافة ومحاذاة أصول الجذر داخل الناتج.</td></tr>
<tr><td>نسخ أصل</td><td>ك ت ب ← كتّب</td><td>أن التكرار من الأصل الثاني، لا أصل رابع مستنتج من الطول.</td></tr>
<tr><td>سابقة أو لاحقة</td><td>أكرم / كتبتُ</td><td>موضع الإضافة وقاعدة اتصالها والتعديل اللازم في الجذع.</td></tr>
<tr><td>حذف أو إبدال</td><td>تحول مرخص في أصل معتل</td><td>الأصل السابق وأثر التعديل والبقية اللازمة لاستعادته.</td></tr>
</tbody></table>
<p>لذلك لا تكفي عملية لصق عامة. «كتبتُ» تحتاج ضبط باء الجذع بالسكون في هذا التصريف، وإضافة الألف في «كاتب» تقع داخل القالب. الدالة التي تحقق الصورة يجب أن تحفظ محاذاة العملية أو يبقى أصلها في الشجرة؛ حفظ الشجرة يسمح بالتعديل دون افتراض أن حروف الجذر مقطع متصل داخل الناتج.</p>
<p>في Alghanem، مبرهنات التصريف تنقل الفحص من تواقيع ممثلة إلى جميع الجذور ضمن فرضية <code dir="ltr">NoAlif</code> ومعلمات المولد؛ فهي براهين عامة لترخيص الصيغ المحددة. وفي NABT، الاسترداد يعيد تنفيذ القالب على كامل الكلمة، ويتحقق من المواضع والحروف الثابتة والطول. قوائم وظائف الزيادات تحدد شروط كل وظيفة؛ تطبيقها على وقوع معين يحتاج تحقيق هذه الشروط. {ref(5,7,8)}</p>
<p>للأدوات والمفردات التي لا نثبت لها هذا الاشتقاق مدخل معجمي مستقل. تدخل «في» مثلًا بوحدة موثقة وقاعدة عمل، دون فرض جذر ثلاثي مصطنع عليها. يحمل ناتج الاشتقاق قسمًا مثبتًا أو مرشحين ينتظرون دليلًا. وقد وصل QismDaraja فعلًا بين تصفية القسم ووحدة مرقمة؛ ويحفظ NABT الأقسام الثلاثة عند غياب العلامة المرخصة. {ref(8,9,10)}</p>
</section>

<section>
<h2>4. ثلاثة أقسام للكلمة، وأنواع متعددة للمركب</h2>
<p>الاسم والفعل والحرف أقسام للمفردة في هذا النموذج. أما «مركب اسمي» و«مركب فعلي» و«جار ومجرور» و«جملة اسمية» و«جملة فعلية» فهي أنواع وحدات أعلى. لا تكفي تسمية رأس المركب لإلغاء داخله أو البقية المطلوبة منه. لذلك تصرح النواة بهذه الفئات منفصلة، وتقبل الواجهة المكتملة أو المعلقة بحسب القاعدة.</p>
<p>الأزواج التسعة الآتية تستنفد حاصل ضرب الأقسام الثلاثة في نفسها، لكنها لا تستنفد العلاقات النحوية. الأمثلة توضيحية لشروط القواعد المقترحة؛ ليست مخرجات محلل عربي منفذ في النواة المستقلة. أطر Mashru تميز الإسناد والجر والتعلق وتحفظ الإطار مع الكلمات؛ ويتطلب NABT هوية الأطراف ودليل الارتباط واكتمال الإطار. {ref(11,23)}</p>
<table><thead><tr><th>الزوج</th><th>مثال</th><th>النتيجة التي تحتاجها القاعدة</th></tr></thead><tbody>
<tr><td>اسم + اسم</td><td>كتابُ الطالبِ / الطالبُ كاتبٌ</td><td>إضافة في الأول، وإسناد في الثاني؛ الصنفان وحدهما لا يفصلان العلاقة.</td></tr>
<tr><td>اسم + فعل</td><td>الطالبُ يكتبُ</td><td>إطار اسمي بخبر فعلي، مع علاقة الفاعل داخل الخبر.</td></tr>
<tr><td>اسم + حرف</td><td>الطالبُ في…</td><td>جزء مفتوح ينتظر مجرورًا ثم علاقة الخبر أو التعلق.</td></tr>
<tr><td>فعل + اسم</td><td>كتبَ الطالبُ</td><td>علاقة الفاعل والحالة؛ وقد تختلف الوظيفة في سياق آخر.</td></tr>
<tr><td>فعل + فعل</td><td>كادَ يكتبُ</td><td>قاعدة مخصوصة للفعل والخبر ومرجع الفاعل، لا وصل فعلين اعتباطًا.</td></tr>
<tr><td>فعل + حرف</td><td>ذهبَ إلى…</td><td>منفذ ينتظر مكمل الحرف وصلته بالفعل.</td></tr>
<tr><td>حرف + اسم</td><td>في الدارِ / إنَّ الطالبَ…</td><td>الأول جار ومجرور، والثاني افتتاح إطار ناسخ ينتظر خبره.</td></tr>
<tr><td>حرف + فعل</td><td>لم يكتبْ</td><td>قاعدة الجزم وشروط الفعل والفاعل.</td></tr>
<tr><td>حرف + حرف</td><td>وإنَّ…</td><td>ترتيب أداتين مع مجال عمل كل منهما، وبقية لم تستوف بعد.</td></tr>
</tbody></table>
<p>يوجد أيضًا في Alghanem مورّث مثبت للإسناد: يحتفظ بآخر قسم وبوجود إسناد سابق، ويحسب أثر الوصل من داخل الجزأين والزوج الحدّي. يصلح هذا ملخصًا بنيويًا داخل وحدة مرفوعة. ولتحليل أدوار كامل تضاف هوية العلاقة ومواقع طرفيها وشروطها. {ref(12)}</p>
</section>

<section>
<h2>5. مثال واحد يبيّن إعادة استعمال الناتج</h2>
<p>لنأخذ قراءة مقترحة لـ«الطالبُ كاتبٌ في الدارِ». نبنيها بالقواعد التالية على سبيل تصميم الواجهة، مع التصريح بأن اختيار هذه القراءة وتعلق شبه الجملة يحتاجان أدلتهما:</p>
<ol>
<li>الجذر «ك ت ب» بذرة مرخصة. تطبيق قالب «فاعل» مع شروطه ينتج «كاتب» ويحفظ أصل كل موضع، ثم تثبت قراءة الاسم وتمنح الوحدة رقمًا.</li>
<li>تدخل «في» و«الدار» و«الطالب» عبر قراءات معجمية أو اشتقاقية موثقة. ترفع الوحدات الاسمية إلى الواجهات التي تطلبها القواعد التالية.</li>
<li>قاعدة الجر تجمع «في» و«الدار» في وحدة شبه جملة. تحتفظ بمتطلب التعلق، بينما تظل حالة الاسم داخلها محفوظة.</li>
<li>قاعدة تعلق مناسبة تصل شبه الجملة بـ«كاتب». الناتج خبر مركب له رقم جديد وأبناء محفوظون؛ هذه الخطوة هي التي تستوفي التعلق.</li>
<li>قاعدة الإسناد تجمع «الطالب» والخبر المركب في جملة اسمية. تصبح الجملة وحدة يمكن عطف جملة أخرى عليها أو إدخالها في إطار أعلى مرخص.</li>
</ol>
<p>كل خطوة تتطلب ترخيص أبنائها وشرطها الخاص؛ نجاح الخطوة السابقة لا يمنح كل العمليات التالية ترخيصًا تلقائيًا. وإذا استعملت الجملة داخل إطار أعلى، تبقى تعييناتها الداخلية منفصلة عن موقعها الخارجي. لدى NABT تمثيل صريح لهذا الفصل في تعيين حالة الجملة مع حفظ تعيين الفعل داخلها. {ref(19,22)}</p>
</section>

<section>
<h2>6. البوابات الخمس: أدلة البناء، وترتيب اللفظ، وصدق الخبر</h2>
<p>توجد هذه البوابات بالفعل في Alghanem وMashru. يفصل استعمالها الصحيح ثلاثة أشياء: شروط السماح بعملية، وترتيب وحدات المنطوق، وتفسير قضية خبرية. قد تستعمل AND لجمع أدلة الترخيص، لكن ذلك لا يجعل وصل الكلمات تبادليًا. وقد تحمل أداة عطف معنى خبريًا، لكن رقمها وحده لا يعطي صدق طرفيها. {ref(13,14,15,16)}</p>
<table><thead><tr><th>البوابة</th><th>في ترخيص البناء</th><th>ما يلزم إبقاؤه</th></tr></thead><tbody>
<tr><td dir="ltr">AND</td><td>شهادة النوع وشهادة الموضع وشهادة الاتصال مطلوبة معًا.</td><td>اجتماع الأدلة لا يبدل ترتيب الأبناء.</td></tr>
<tr><td dir="ltr">OR</td><td>يوجد فرع قاعدة صالح؛ يحتفظ البناء بالفرع المختار.</td><td>قبول فرع لا يثبت بطلان بقية الفروع.</td></tr>
<tr><td dir="ltr">NOR</td><td>ثبت نفي المانعين أو البديلين المحددين.</td><td>غياب الشاهد ليس دليل نفي.</td></tr>
<tr><td dir="ltr">XOR</td><td>ثبت أحد البديلين وثبت استبعاد الآخر.</td><td>الانفراد يحتاج استبعادًا، لا مجرد العثور على مرشح.</td></tr>
<tr><td dir="ltr">IF–THEN</td><td>عند تفعيل قاعدة استدلال ذات مقدمة، يقدم دليل المقدمة للوصول إلى النتيجة.</td><td>بناء عبارة شرطية لا يشترط وقوع شرطها في العالم.</td></tr>
</tbody></table>
<p><b>ترخيص الجملة الشرطية يختلف عن تفعيل الاستدلال بمضمونها.</b> يمكن بناء «إنْ حضرَ الطالبُ بدأَ الدرسُ» إذا تحققت شروط تركيب طرفيها وربطهما، سواء وقع الحضور فعلًا أم لم يقع أو بقي مجهولًا. أما إذا أردنا استنتاج بدء الدرس من مضمون هذه العبارة، فنحتاج قاعدة الاستلزام ودليل تحقق مقدمتها. لذلك لا يجوز جعل صدق شرط المنطوق بوابة لازمة لمجرد إنشاء بنيته؛ حارس التركيب يفحص البنية، ودليل المقدمة يخدم خطوة الاستنتاج.</p>
<p>في تفسير الخطاب، «أو» الإباحة تختلف عن «أو» التخيير، والشرط المستلزم يختلف عن التكافؤ. يعالج Bawwabat أيضًا قيمة «لا حكم»، فلا يحول المجهول إلى كذب. هذه براهين مفيدة عندما تقدم قضايا الطرفين وسياق الأداة؛ أما استخراج تلك القضايا من الألفاظ فله عقد آخر. {ref(13,14,15)}</p>
<p>في النواة الجديدة، البوابات قضايا عن الأدلة. وبناء العقدة الثنائية مرتب: إذا اختلف الولدان، فإن تبديلهما يغير الرقم. تحفظ هذه النتيجة الفرق بين «كتاب الطالب» و«الطالب كتاب»، حتى لو كان جمع شرطي ترخيصهما يستعمل العملية المنطقية نفسها.</p>
</section>

<section>
<h2>7. ماذا أثبتت النواة المستقلة؟</h2>
<p>تستخدم النواة <code dir="ltr">Std</code> فقط. البذور ثلاثة أنواع: جذر ثلاثي، جذر رباعي، ومدخل معجمي. والبناة ورقة وعملية أحادية وعملية ثنائية؛ تحمل كل عملية رقم قاعدة. يجعل <code dir="ltr">Certified</code> ترخيص كل عقدة مشروطًا بترخيص الأبناء وتوافق الواجهات ونجاح البوابة. الناتج الموثق قابل مباشرة للاستعمال في قاعدة أخرى.</p>
<p>العقد <code dir="ltr">RealizationContracts</code> يربط الواجهة بالصورة بواسطة خاصية تختارها الدراسة، مثل صحة شكل صوتي أو أثر إعرابي. يجب إثباتها للبذور وإثبات حفظها عند كل قاعدة. بعدها يثبت الاستقراء أن جميع الأشجار المرخصة تحققها. هذه صلة صريحة بين صحة الصورة وصحة البناء؛ لا تُفترض فيها نسخة عربية لم تُقدَّم.</p>
<div class="formula">Local contracts for P + Certified(t) ⟹ P(face(t), surface(t))</div>
<p>أهم ست نتائج هي: الاستقراء المرخص؛ حفظ عقد التحقيق؛ تباين ترقيم الشجرة؛ حفظ ترتيب الولدين؛ اكتمال التعداد المرخص داخل الحد؛ ووصول كل شجرة منتهية مرخصة إلى مرحلة كافية. تظهر هذه النتائج بعلامة <b>★</b> في الجرد التالي. باقي المبرهنات يثبت واجبات الرفض والحفظ والترميز والبوابات التي تسندها.</p>
<table class="theorems"><thead><tr><th>م</th><th>اسم المبرهنة</th><th>المضمون المثبت</th></tr></thead><tbody>
'''

for i, name in enumerate(CHECK['theorems'],1):
    star = '<span class="star" aria-label="نتيجة رئيسية">★</span> ' if name in IMPORTANT else ''
    body += f'<tr><td>{i}</td><td>{star}{code(name)}</td><td>{THEOREM_NOTES[name]}</td></tr>\n'

body += f'''
</tbody></table>
<aside class="verification">
<h3>نتيجة الفحص الفعلي</h3>
<p>نجح التجميع بواسطة <b>Lean 4.34.1</b>، برمز خروج <b>0</b>، وفُحصت <b>{CHECK['theorem_count']} مبرهنة</b> في الملف المستقل. سجل الفحص لا يتضمن أوامر إثبات محظورة أو مواضع إثبات متروكة. هذا فحص للنواة الجديدة؛ أما براهين المستودعات فراجعتها الدراسة في مصادرها المثبتة، دون إعادة بناء شاملة لاعتماداتها.</p>
<p class="small">وقت التحقق بتوقيت عمّان: <bdi>{CHECKED_AMMAN}</bdi><br>بصمة الملف SHA-256: <code dir="ltr" class="hash">{CHECK['sha256']}</code></p>
</aside>
</section>

<section>
<h2>8. كيف يستكمل الجبر تدريجيًا؟</h2>
<p>يحدد المخزون قائمة بذور منتهية وقائمتي قواعد أحادية وثنائية. تبدأ المرحلة صفر بالبذور. وتضيف المرحلة التالية كل تطبيق أحادي على مرشح سابق، وكل تطبيق ثنائي على زوج مرتب من المرشحين السابقين، مع إبقاء البذور. يثبت <code dir="ltr">candidates_iff</code> أن الناتج هو تمامًا الأشجار المدعومة التي لا يتجاوز ارتفاعها الحد.</p>
<p>تثبت رتابة التعداد أن رفع الحد لا يفقد المرشحين السابقين. وتثبت نتيجة الوصول أن كل شجرة منتهية مرخصة في المخزون تظهر عند ارتفاع كافٍ. لا يلزم إنهاء المجال غير المحدود كي تستنفد كل درجة منتهية. وفي المثال العددي الصغير ذي ثلاث بذور وقاعدتين من كل نوع، تكون الأعداد 3 ثم 27 ثم 1515؛ إنها أعداد مرشحين بنيويين قبل اعتماد قواعد عربية بعينها.</p>
<p>تحتاج التصفية الحاسوبية إلى قابلية قرار الترخيص. كما أن حد طول الصورة وحده قد يسمح بسلسلة غير محدودة من الرفعات التي لا تغير اللفظ؛ اختيار ارتفاع الشجرة يمنع هذا الالتباس. وفي NABT استنفاد مثبت آخر لمجال أضيق: أشجار وصل ثنائي لمقطع أصلي محدد ووسم ثابت، مع ترتيب الأوراق. يفيد برهانه داخل هذا المجال، وتوسيع القواعد يستلزم توسيع مولد المجال وإثبات اكتماله. {ref(21)}</p>
<p>هنا معنى الاستقراء <b>ON</b> محدد: البرهان على الشجرة المنشأة. ومعنى البناء <b>FOR</b> في خطة العمل: توليد المرشحين وتكوين قواعد أو وحدات مقترحة ثم طلب شهاداتها. ليس كل مرشح مستنفد قانونًا مكتسبًا؛ قوة التعميم اللغوي تتوقف على الشواهد والعقود التي اجتازت الاختبار.</p>
</section>

<section>
<h2>9. الربط بالمستودعات والخطوة التالية</h2>
<p>يبدأ الربط بمحوّل يحفظ الجذر والقالب والمحاذاة من قارئ NABT، أو يحمل ناتج التصريف المثبت في Alghanem. ثم يصل شهادة القسم بوحدة Hudud، ويحدد واجهات الإسناد والجر والإضافة والعطف من أطر Mashru. وأخيرًا يترجم كل عقدة إلى سجل اشتقاق يحتفظ بالأبناء والشواهد؛ يوفر PR14 في NABT بناة الوصل والتغليف والإبدال والرفع، وبرهان استعادة المصدر وحفظ المقدمات. {ref(7,9,11,18,19,20)}</p>
<p>هذا يجعل العمل التالي مجموعة واجبات محددة: عقد لكل قاعدة صرفية، وعقد لكل علاقة تركيبية، ومحوّل مثبت بين تمثيلات الوحدات. لا يكفي توافق الأسماء أو الأرقام بين مشروعين؛ يجب أن يحفظ المحوّل ترتيب الحوامل، ومجال الحالات، وحدود المصدر، وتفسير الأدوار.</p>
<div class="scope">
<h3>نطاق النتيجة</h3>
<ul>
<li>وسوم الواجهة والقواعد والمدخلات المعجمية معطاة؛ النواة لا تكتسب الأقسام أو الحالات تلقائيًا.</li>
<li>تباين الرقم يخص الشجرة ضمن نسخة قواعد ثابتة؛ لا يثبت تفرد تحليل كل صورة أو صدق معناها.</li>
<li>الاستنفاد كامل ضمن المخزون والحد المعلنين؛ لا يتضمن ادعاء استنفاد كل العربية.</li>
<li>الأمثلة التركيبية توضح واجبات الربط؛ لم تُقدَّم بوصفها تطبيقًا عربيًا مكتملًا للنواة.</li>
<li>فُحص الملف المستقل وحده بناءً جديدًا، ولم يُدمج في المستودع ولم يُعد بناء المستودعات الأصلية.</li>
</ul>
</div>
</section>

<section class="sources">
<h2>10. المصادر المثبتة</h2>
<p>تصل الروابط إلى ملفات وأسطر في التزامات محددة، فتظل قابلة للمراجعة مع تغير الفروع. اللقطات: Alghanem عند <code dir="ltr">9d8fa03a51f894416e0abaf3b6821c5ae6441dcd</code>، وMashru عند <code dir="ltr">e4c801ffe9171dadedcc3aae23051ea0953ae361</code>، وNABT عند <code dir="ltr">171cfa32a4bad0b5f9e8ff856cd98e23028122c7</code>، وهو رأس PR14 الذي استند إليه هذا التقرير. مصادر المستودعات الثلاثة قرئت قراءةً فقط وطوبقت ملفات المراجعة مع لقطاتها.</p>
<ol>
'''
for i, (label,url) in enumerate(SOURCES,1):
    body += f'<li id="s{i}"><a href="{html.escape(url, quote=True)}">{html.escape(label)}</a></li>\n'
body += '''</ol></section>
</main>
<footer>تقرير مستقل مكتمل بذاته · الأمثلة التعليمية موسومة بوصفها أمثلة · الروابط الخارجية للتوثيق والتحقق من المصدر.</footer>
'''

CSS = '''
:root{color-scheme:light;--ink:#152832;--muted:#51636b;--teal:#0b6d70;--line:#d8e3e5;--paper:#fff;--tint:#eff7f6}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#f2f5f5;color:var(--ink);font-family:"Noto Naskh Arabic","Geeza Pro",Tahoma,Arial,sans-serif;font-size:18px;line-height:1.95}
header,main,footer{max-width:1080px;margin:auto}header{padding:66px 58px 44px;background:#143e48;color:#fff;border-bottom:8px solid #b9ded5}main{background:var(--paper);padding:12px 58px 56px}footer{padding:24px 58px;font-size:14px;color:var(--muted)}
h1,h2,h3,p{margin-top:0}h1{font-size:43px;line-height:1.5;letter-spacing:-.3px;margin-bottom:20px}h2{font-size:28px;line-height:1.6;margin-bottom:20px;color:#174f5b}h3{font-size:21px;line-height:1.7;margin-bottom:12px}.eyebrow{font-size:15px;color:#c4e4e0;margin-bottom:15px}.subtitle{max-width:880px;font-size:21px;color:#e5f2f2;margin-bottom:24px}.status{display:flex;flex-wrap:wrap;gap:9px;font-size:13px}.status span{padding:4px 12px;border:1px solid #729599;border-radius:20px}section{padding-top:42px;margin-top:8px;border-top:1px solid var(--line)}section.lead{border:0;margin:0;padding-top:36px}p{margin-bottom:18px}b,strong{font-weight:700}a{color:var(--teal);text-decoration:underline;text-underline-offset:3px}.refs{white-space:nowrap;font-size:13px;font-family:Arial,sans-serif;direction:ltr;unicode-bidi:isolate}.refs a{padding-inline:2px}code,bdi{unicode-bidi:isolate}code{font-family:ui-monospace,"SFMono-Regular",Consolas,monospace;font-size:.79em;overflow-wrap:anywhere;line-height:1.55;background:#f1f5f6;border-radius:3px;padding:2px 4px}
table{width:100%;border-collapse:collapse;margin:20px 0 24px;font-size:16px;line-height:1.8}thead th{background:#e9f2f1;font-weight:700;color:#17434d}th,td{text-align:right;vertical-align:top;padding:11px 12px;border:1px solid var(--line)}tbody tr:nth-child(even){background:#fafcfc}th:first-child{min-width:85px}.formula{direction:ltr;text-align:center;unicode-bidi:isolate;font:600 17px/1.7 ui-monospace,Consolas,monospace;padding:17px;background:var(--tint);border-right:4px solid var(--teal);margin:20px 0;overflow-wrap:anywhere}.theorems{font-size:15px}.theorems td:first-child{width:45px;text-align:center}.theorems td:nth-child(2){width:44%}.theorems code{font-size:12px}.star{color:#986616}.verification,.scope{padding:22px 25px;background:#f0f7f5;border-right:4px solid #6b9f90;margin:24px 0}.verification p:last-child,.scope ul:last-child{margin-bottom:0}.small{font-size:13px;color:var(--muted)}.hash{display:inline-block;font-size:12px;background:transparent}ol,ul{padding-inline-start:28px;margin:14px 0 22px}li{padding-inline-start:5px;margin:7px 0}.sources{font-size:15px}.sources ol{columns:2;column-gap:34px}.sources li{break-inside:avoid;line-height:1.7;margin-bottom:14px}.sources p code{font-size:11px;background:transparent}
@media(max-width:760px){body{font-size:17px}header,main,footer{padding-left:22px;padding-right:22px}header{padding-top:40px}h1{font-size:31px}h2{font-size:24px}.subtitle{font-size:19px}table{font-size:14px}th,td{padding:8px 7px}.theorems code{font-size:10px}.theorems td:nth-child(2){width:42%}.sources ol{columns:1}.formula{font-size:13px}}
@media print{@page{size:A4;margin:16mm 13mm}body{background:white;font-size:11pt;line-height:1.7}header,main,footer{max-width:none;padding:0}header{background:white;color:var(--ink);border-bottom:2px solid var(--teal);padding-bottom:15pt}header .eyebrow,header .subtitle{color:var(--muted)}h1{font-size:27pt}h2{font-size:18pt;break-after:avoid}h3{font-size:13pt;break-after:avoid}.subtitle{font-size:13pt}.status{font-size:9pt}.status span{border-color:#aaa}section{padding-top:20pt}table{font-size:9pt}tr,aside{break-inside:avoid}thead{display:table-header-group}.theorems{font-size:8.4pt}.theorems code{font-size:7.4pt}.sources{font-size:9pt}.sources ol{columns:1}footer{margin-top:20pt;font-size:8pt}.formula{font-size:10pt}a{color:#174f5b}}
'''

document = '<!doctype html>\n<html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="تقرير موثق عن جبر الجذور والاشتقاق والتركيب المتكرر، وبوابات الترخيص، ونواة Lean مستقلة مثبتة."><title>من الجذر إلى الجملة — جبر الوحدات المرخصة</title><style>'+CSS+'</style></head><body>'+body+'</body></html>\n'
OUTPUT.parent.mkdir(parents=True,exist_ok=True)
OUTPUT.write_text(document, encoding='utf-8')

class TextCollector(HTMLParser):
    def __init__(self):
        super().__init__(); self.text=[]; self.skip=0; self.links=[]
    def handle_starttag(self, tag, attrs):
        if tag in {'style','script'}: self.skip += 1
        if tag=='a': self.links.append(dict(attrs).get('href',''))
    def handle_endtag(self, tag):
        if tag in {'style','script'}: self.skip -= 1
    def handle_data(self, data):
        if not self.skip: self.text.append(data)

parsed=TextCollector(); parsed.feed(document)
visible=' '.join(parsed.text)
word_count=len(visible.split())
arabic_words=len(re.findall(r'[\u0600-\u06ff]+', visible))
external=[x for x in parsed.links if x.startswith('https://')]
assert len(external)==24 and len(set(external))==24
assert all('/blob/' in x for x in external)
assert all(x.startswith('#') or x.startswith('https://') for x in parsed.links)
assert 'dir="rtl"' in document and 'lang="ar"' in document
assert len(IMPORTANT)==6
assert 2500<=word_count<=3500, word_count
print(json.dumps({'output':str(OUTPUT),'bytes':OUTPUT.stat().st_size,'visible_words':word_count,'arabic_word_segments':arabic_words,'theorems':CHECK['theorem_count'],'highlighted_theorems':len(IMPORTANT),'immutable_source_links':len(external),'proof_sha256':CHECK['sha256']},ensure_ascii=False,indent=2))
