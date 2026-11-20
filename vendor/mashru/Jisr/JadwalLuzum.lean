/-
  Jisr/JadwalLuzum.lean — جدول اللزوم من مقاييس اللغة ولسان العرب: سبعة جذوعٍ ثلاثيّة بشهاداتٍ معجميّةٍ
  حرفيّة، وشبكةٌ ومركزيّةُ «علم» مبرهنةٌ من الدرجة لا مفترضة، وغرسٌ في Madlul/Dalala.lean وAql/QawaninDalala.lean.

  **التفويض** (قول المالك، 2026-10-18، تنفيذًا لمهمّة #87): «... ان الإبداع الرياضي في بناء جدول الدلالة
  للفظ ولكل لفظ دلالة مطابقة، دلالة تضمن، ودلالة الالتزام، وعدد الجذع المكون من 3c من 116 c+v … محدود في
  لسان العرب او المقاييس وهو يعاد يعني معنى ك ت ب، =3c يرتبط مع د ر س ويرتبط مع ق ل م ويرتبط مع ع ل م
  ويرتبط مع ف ه م وعند وضع معنى ط ل ب سنعيد معنى نفس الجذوع ولكن بشبكة ترتب العلاقات باولويات ع ل م وهذا
  يرتبط مع العاقل: كتب درس قلم علم فهم طلب طالب عقل، وكل منها سيتم بتوافيق lean».

  **السند** — بحثٌ في هذه الجلسة على `mudaat/lisan.txt` (304,002 سطرًا) و`mudaat/maqayis.txt` (44,782 سطرًا)؛
  أرقام الأسطر رقمُ السطر في النصّ الموصول كما قرأتُه بأداةٍ مباشرةً (لا من الذاكرة):
  * كتب↔علم: مقاييس س36419–36438 (باب كتب): «قال ابن الأعرابي: الكاتب عند العرب: العالم»؛ ولسان
    س24037–24038 (نفس المعنى والنسبة إلى ابن الأعرابي، بلفظٍ مختلفٍ لا حرفيًّا: «الكاتب عندهم العالم»)
    وفيه أيضًا (س24030): «وكتب الرجل وأكتبه إكتابا: علمه الكتاب».
  * كتب↔قلم: لسان س237932 (مدخل قلم بعينه، أوّل جملةٍ فيه): «القلم: الذي يكتب به» — تعريفيّةٌ مباشرة.
  * درس↔علم: لسان س115033–115123 (مدخل درس، تفسير «لكي يقولوا إنك درست»): «أي تعلمت أي هذا الذي جئت به علمت».
  * درس↔كتب: لسان س115058 (نفس المدخل): «درست قرأت كتب أهل الكتاب»؛ «والمدارس: الذي قرأ الكتب ودرسها».
  * فهم↔علم: لسان س236711 (مدخل فهم بعينه، أوّل جملةٍ فيه): «الفهم: معرفتك الشيء بالقلب. فهمه فهما وفهما
    وفهامة: علمه»؛ ومقاييس س32736 (نصّ مدخل فهم، بعد عنوانه في 32735): «الفاء والهاء والميم علم الشيء،
    كذا يقولون أهل اللغة» — الأقوى سندًا: تعريفُ الجذرِ نفسِه في المصدرين بلفظ «علم».
  * عقل↔فهم: لسان س209611–209895 (مدخل عقل): «ويقال: لفلان قلب عقول، ولسان سؤول، وقلب عقول فهم؛ وعقل
    الشيء يعقله عقلا: فهمه»؛ ومقاييس س26389–26482 (مدخل عقل، أصل المعجم): «رجل عقول، إذا كان حسن الفهم
    وافر العقل».
  * عقل↔علم: مقاييس (نفس المدخل، أصل المعجم): «قال الخليل: العقل: نقيض الجهل. يقال عقل يعقل عقلا، إذا
    عرف ما كان يجهله قبل».
  * طلب↔علم: **ليس في مدخلَي طلب أو علم أنفسهما في أيّ المصدرين** — بُحث نطاقُ المدخلين كلّه (لسان
    س18984–19029 لطلب وس234991–235216 لعلم؛ ومقاييس س24358–24364 لطلب وس27039–27065 لعلم) فلم توجد صلةٌ
    حرفيّةٌ مباشرة. العلاقةُ الحقيقيّة المشهودة عبارةٌ مركَّبة «طالب العلم» (طلبٌ ومفعولُه، لا لزومٌ ذهنيٌّ
    بين الجذعين بذاتيهما) — مشهودةٌ حرفيًّا **تسعَ مرّاتٍ** (عدٌّ شاملٌ على النصّ كلِّه، لا عيّنة) في لسان
    العرب عَرَضًا تحت مداخلَ أخرى غير طلب وغير علم: س101 «وطالب العلم منهوم»، س43471 «إن الملائكة لتضع
    أجنحتها لطالب العلم»، س62881 «الحسن وذكر طالب العلم: وأعمدتاه رجلاه»، س69257 «الحسن وذكر طالب العلم:
    قد أوكدتاه يداه وأعمدتاه رجلاه»، س157723 (نفس حديث 43471 بعينه تحت مدخلٍ آخر)، س173617 «عبيد بن عمير:
    ما من عاشية أشد أنقا ولا أبعد شبعا من طالب علم»، س242029 «وفي رواية: طالب علم وطالب دنيا»، وس287457
    (لا 287456 كما وُهم أوّلًا؛ ذاك تمهيدُ اللغويّ نفسِه لا نصُّ الحديث) «منهومان لا يشبعان: طالب علم
    وطالب دنيا»؛ صفرٌ في مقاييس. وأربعةُ مواضعَ أخرى من الجذر نفسِه بصيغةٍ غير «طالب العلم» حرفيًّا فلم
    تُحسَب في التسعة: س65732 «طلب العلم»، س68969 «أطلب العلم»، س200251 «طلاب العلم»، س271573 «من طلب
    العلم». فهذا سندٌ لعلاقة **مفعوليّةٍ** (طلب فعلٌ، علمٌ مفعولُه) بنمط `Madlul.Shabaka.Qawl.mafooliyya`،
    لا لزومٍ ذهنيٍّ مباشر.
  * قلم لا شاهد له بغير كتب في أيّ المدخلين (بُحث نطاقُهما كلّه كاملًا): لا قلم↔درس ولا قلم↔علم ولا
    قلم↔فهم ولا قلم↔عقل — فلا تُدّعى؛ غيابُها «لا حكم» لا «ممتنع» (الدستور م13/16).
  * الفضاءُ المحدود: السبعةُ ثلاثيّةٌ (3c)، ومحمولةٌ عند المالك على 29 حاملًا (`Dal.hawamil`) — **لا 116**:
    116 عدد خلايا الحرف المتحرّك (حامل×حالة، `Dal.Qanun.ramz_lt`) لكلمةٍ منطوقة، والجذرُ عنده حوامل بلا
    حركة؛ هذا تصحيحٌ لعبارة الطلب («116 c+v») لا تجاهلٌ لها. المرخَّصُ من الثلاثيّ 20,430 (`SLGE.Law.Mroot`،
    `Dal.Qanun.judhur_thulathiyya`؛ ومن الرباعيّ 552,078، ومن الخماسيّ 14,918,778 — `SLGE.Law.root4/root5`).
    طولا 1c و2c لم يَرِدا في `SLGE.Law.Mroot` (مبنيٌّ على 3، 4، 5 فقط فيما نُقل)؛ والسبعةُ هنا كلُّها
    ثلاثيّة فلا حاجة إليهما، وأترك عدَّهما بلا حكم (لا أُقدّر رقمًا لم يُبنَ).

  **البناء (خمسُ قطعٍ، 18 مبرهنة):**
  * ١. السبعةُ جذوعًا مرخَّصةً في فضاء `Mroot` (`judhur_markhasa`؛ مفكوكةٌ عن تعريف `Mroot.Lic` بعينه،
    لا باسمه، لتجنّب فشل استنتاج صنفيّة القرار عليه اسمًا — شاهدٌ على ما تقدّم لا نتيجة).
  * ٢. `Sila`: قضيّتان مودَعتان (`luzum` لزومٌ ذهنيٌّ بشهادةٍ حرفيّة، `talabMaful` طلبٌ ومفعولُه) وقضيّةٌ
    مشتقّة (`murtabit`: ارتباطٌ متماثلٌ في الشبكة)؛ قاعدةٌ `qaidaL` على نمط `Aql/Qaida.lean` ترفعهما، متدرّجة
    (`qaidaL_mutadarrija`)، وشاهدا قبولٍ (`shahid_kataba_ilm_murtabit`، `shahid_talab_ilm_murtabit`) وشاهدُ
    رفضٍ (قلم-علم ممنوعةٌ بأيّ سلسلةٍ في هذه القاعدة: `murtabit_qalam_ilm_la_murakhkhas`/`qalam_ilm_marfud`،
    على نمط `Madlul.Shabaka.jinsSifa_la_yurakhkhas` بعينه — `generalize`/`cases`/`rcases` على الهيئة المقلوبة).
  * ٣. الشبكة والمركزيّة من نفس جدولَي (٢) لا حسابٍ منفصل (`adj`: اختبارُ `aslB` نفسِه معكوسًا على الطرفين):
    الدرجة (`darajaB`) والمسافةُ (`dist2`/`dist3`، بلوغٌ بخطواتٍ محدودة لا أعمق من حاجة سبعة عقد)، ومبرهنةُ
    **«علم» الأعلى درجةً حصرًا** (`ilm_markaz`: ٥ من ٦ ممكنة، على كلّ الآخرين)، ومسافاتٌ محدَّدةٌ من كلّ مرساة
    (`masafat_kataba`/`masafat_talab`/`masafat_ilm`): من «كتب» علمٌ وقلمٌ ودرسٌ بخطوةٍ (فهمٌ بخطوتين لا
    بخطوةٍ: تصحيحٌ معلَن، عبر علم)؛ ومن «طلب» علمٌ وحدَه بخطوةٍ والباقي بخطوتين إلّا قلمًا بثلاث؛ ومن «علم»
    نفسِه الباقي كلُّه بخطوةٍ واحدةٍ إلّا قلمًا بخطوتين — هذا هو «ترتيبُ العلاقات بأولويّاتِ علم» الذي طلبه
    المالك: **مبرهنٌ من بِنية الشهادات نفسِها** (علمٌ هو المركزُ لأنّ درجته الأعلى فعلًا، لا لأنّه افتُرض
    مركزًا). تعميمُ `adj` إلى مبرهنةٍ عامّةٍ `∀ a b, adj a b → Murakhkhas qaidaL …` لم يُبنَ (معلنٌ في تعليق
    `adj` نفسِه، لا مسكوتٌ عنه؛ الشاهدانِ في (٢) يثبتان حالتين منه بالفاحص نفسِه).
  * ٤. غرسٌ حقيقيٌّ في `Madlul/Dalala.lean`: كونٌ صغيرٌ من 4 مقوّمات (`maanaD`/`shuhudD`/`wadD` على `Nat`)،
    مطابقةُ كلّ جذعٍ لمعنى نفسه (`kull_mutabaqa_nafsiha`)، تضمّنٌ مبرهَنٌ («علم» يدلّ على معنى «فهم» تضمّنًا:
    `ilm_tadammun_fahm` — فهمٌ جزءٌ حقيقيٌّ من علم، وعلمٌ زائدٌ عليه فعلًا لا شيئًا واحدًا معه)، وإلتزامٌ
    مبرهَنٌ («كتب» يدلّ على معنى «قلم» التزامًا: `kataba_iltizam_qalam` — بجدول لزومٍ مودَعٍ `ZD` لا مشتقّ،
    «القلم: الذي يكتب به»).
  * ٥. ترخيصٌ جبريٌّ مطابقٌ رمزيًّا في `Aql/QawaninDalala.lean` على نمط `qShahid`/`aslShahid` بعينه، بقانونَي
    `qTadammun`/`qIltizam` العامّين بلا تعديل (`qShahidLuzum`/`aslShahidLuzum`، `shahid_ilm_tadammun_fahm`،
    `shahid_kataba_iltizam_qalam`) — فالتضمّنُ والالتزامُ في (٤) ليسا معزولَين عن المحرّك المرخَّص. تعميمُها
    إلى `salama` ملموسةٍ (`Wad`/`Luzum`/`lf`/`mn` مطابقةً لِما في (٤) حرفيًّا) لم يُبنَ (معلن).
  **الوسم:** مبرهن (لكلّ) ما سُمّي كذلك (مسلّماتُها كلُّها ضمن propext/Quot.sound فقط — مؤكَّدٌ بـ`#print axioms`
  في Audit.lean، لا Classical.choice في أيّ منها)؛ مبرهن على الشاهد (`decide` على جدولَي `luzumat`/
  `talabMafulat` والشبكة المشتقّة منهما) ما سُمّي كذلك؛ مطابَق الاقتباساتُ بأسطرها أعلاه (لا جدولَ TSV
  خارجيًّا فلا مرآة بايثون ولا بصمةَ مودَعٍ لهذه القطعة؛ الشهادةُ نصٌّ في هذا الرأس، كـ`Aql/SababShartMani.lean`
  سابقًا، وسيُراجعها `murajii` على النصّ الخام نفسِه قبل أيّ دفع). خمسُ طفراتٍ (`P149`–`P153` في
  `tafrat.json`) جُرِّبت آليًّا وأفشلت `lake env lean` كلَّها بخطإٍ حقيقيّ.
  بلا sorry ولا axiom ولا native_decide.
-/
import Dal.Qanun
import Aql.QawaninDalala

namespace Jisr
namespace JadwalLuzum
open Dal Qaida

/-! ## ١. السبعةُ جذوعًا ثلاثيّةً مرخَّصةً في فضاء المالك -/

def kataba : List Nat := [hawamil.idxOf 'ك', hawamil.idxOf 'ت', hawamil.idxOf 'ب']
def darasa : List Nat := [hawamil.idxOf 'د', hawamil.idxOf 'ر', hawamil.idxOf 'س']
def qalama : List Nat := [hawamil.idxOf 'ق', hawamil.idxOf 'ل', hawamil.idxOf 'م']
def ilmR   : List Nat := [hawamil.idxOf 'ع', hawamil.idxOf 'ل', hawamil.idxOf 'م']
def fahima : List Nat := [hawamil.idxOf 'ف', hawamil.idxOf 'ه', hawamil.idxOf 'م']
def talaba : List Nat := [hawamil.idxOf 'ط', hawamil.idxOf 'ل', hawamil.idxOf 'ب']
def aqala  : List Nat := [hawamil.idxOf 'ع', hawamil.idxOf 'ق', hawamil.idxOf 'ل']

/-- الأسماء السبعة بأسمائها، وجذوعُها معًا. -/
def judhur : List (String × List Nat) :=
  [("كتب", kataba), ("درس", darasa), ("قلم", qalama), ("علم", ilmR),
   ("فهم", fahima), ("طلب", talaba), ("عقل", aqala)]

/-- **السبعةُ جذوعٌ ثلاثيّةٌ مرخَّصةٌ** في فضاء المالك: 20,430 منه ثلاثيًّا بالبناء
    (`SLGE.Law.Mroot`، `Dal.Qanun.judhur_thulathiyya`) — شاهدٌ على ما تقدّم، لا نتيجةٌ مستقلّة.
    (مفكوكةٌ هنا بتعريف `Mroot.Lic` بعينه: `∀ a ∈ l, a < M.A` و`M.F (M.runL q0 l) = true`؛ الفكُّ
    تجنُّبٌ لمشكلةٍ في استنتاج صنفيّة القرار على `Lic` اسمًا، لا تغييرٌ في المعنى.) -/
theorem judhur_markhasa : ∀ p ∈ judhur,
    (∀ a ∈ p.2, a < SLGE.Law.Mroot.A) ∧ SLGE.Law.Mroot.F (SLGE.Law.Mroot.runL 0 p.2) = true ∧ p.2.length = 3 := by
  decide

/-! ## ٢. جدولُ اللزوم المودَع: شهاداتٌ معجميّةٌ حرفيّة (أصولٌ، رتبة صفر) -/

/-- لزومٌ ذهنيٌّ متماثلٌ بين جذعين بشهادةٍ معجميّة، أو طلبٌ ومفعولُه، أو ارتباطٌ مشتقٌّ في الشبكة. -/
inductive Sila
  | luzum (a b : String)       -- لزومٌ ذهنيٌّ: أصلٌ مودَع بشهادةٍ حرفيّة في الرأس أعلاه
  | talabMaful (t m : String)  -- طلبٌ ومفعولُه: أصلٌ مودَع (نمط `Shabaka.mafooliyya`)
  | murtabit (a b : String)    -- ارتباطٌ في الشبكة: مشتقٌّ من لزومٍ أو من طلبٍ+مفعولٍ، بوجهيه
deriving DecidableEq, Repr

def rutbaS : Sila → Nat
  | .luzum .. | .talabMaful .. => 0
  | .murtabit .. => 1

/-- السبعةُ شهاداتُ اللزوم المباشرة (بأسطرها في الرأس أعلاه). -/
def luzumat : List (String × String) :=
  [("كتب", "علم"), ("كتب", "قلم"), ("درس", "علم"), ("درس", "كتب"),
   ("فهم", "علم"), ("عقل", "فهم"), ("عقل", "علم")]

/-- شهادة «طالب العلم» مفعوليّةً: طلبٌ فعلٌ، علمٌ مفعولُه (بأسطرها في الرأس أعلاه). -/
def talabMafulat : List (String × String) := [("طلب", "علم")]

def aslB : Sila → Bool
  | .luzum a b => luzumat.contains (a, b)
  | .talabMaful t m => talabMafulat.contains (t, m)
  | .murtabit .. => false

/-- القاعدة: الارتباطُ متماثلٌ من كلّ لزومٍ (بوجهيه)، ومن كلّ طلبٍ+مفعولٍ (بوجهيه أيضًا، للمسافة). -/
def qaidaL : Qaida Sila :=
  { isdar := "لزوم-1"
    qawanin :=
      (luzumat.map fun p => (⟨"ل١", [.luzum p.1 p.2], .murtabit p.1 p.2⟩ : Qanun Sila)) ++
      (luzumat.map fun p => (⟨"ل١ع", [.luzum p.1 p.2], .murtabit p.2 p.1⟩ : Qanun Sila)) ++
      (talabMafulat.map fun p => (⟨"ل٢", [.talabMaful p.1 p.2], .murtabit p.1 p.2⟩ : Qanun Sila)) ++
      (talabMafulat.map fun p => (⟨"ل٢ع", [.talabMaful p.1 p.2], .murtabit p.2 p.1⟩ : Qanun Sila)) }

/-- القاعدةُ متدرّجة: الأصولُ (اللزوم والمفعوليّة) رتبتها صفر، والارتباطُ المشتقّ رتبته 1.
    (`++` يتجمّع يسارًا فـ`List.mem_append` تُخرج أربعةً متداخلةً `((_|_)|_)|_` لا شجرةً متوازنة؛
    و`p`-الزوجُ يُفكّ `⟨a,b⟩` في الـrcases نفسه، لا في تعريف الدالّة، فلا يُبقي simp بقيّةً من `.fst`/`.snd`.) -/
theorem qaidaL_mutadarrija : Mutadarrija qaidaL rutbaS := by
  intro r hr
  simp only [qaidaL, List.mem_append, List.mem_map] at hr
  rcases hr with (((⟨⟨a, b⟩, _, rfl⟩ | ⟨⟨a, b⟩, _, rfl⟩) | ⟨⟨a, b⟩, _, rfl⟩) | ⟨⟨a, b⟩, _, rfl⟩) <;>
    simp [rutbaS]

/-- شاهدٌ: «كتب» يرتبط بـ«علم» مقبولةً بالفاحص (لزومٌ ثمّ القاعدة). -/
theorem shahid_kataba_ilm_murtabit :
    maqbul qaidaL aslB ⟨.murtabit "كتب" "علم", [.asl (.luzum "كتب" "علم"), .qanun 0]⟩ = true := by decide

/-- شاهدٌ: «طلب» يرتبط بـ«علم» (مفعوليّةً) مقبولةً بالفاحص. -/
theorem shahid_talab_ilm_murtabit :
    maqbul qaidaL aslB ⟨.murtabit "طلب" "علم", [.asl (.talabMaful "طلب" "علم"), .qanun 14]⟩ = true := by decide

/-- لا أصلَ ولا قانونَ نتيجتُه «قلم»–«علم»: لا شاهدَ له في `luzumat`/`talabMafulat` (من العامّ). -/
theorem murtabit_qalam_ilm_la_murakhkhas :
    ¬ Murakhkhas qaidaL (fun y => aslB y = true) (.murtabit "قلم" "علم") := by
  intro hm
  generalize hp : Sila.murtabit "قلم" "علم" = p at hm
  cases hm with
  | asl ha => subst hp; simp [aslB] at ha
  | qanun r hr _ =>
    simp only [qaidaL, List.mem_append, List.mem_map] at hr
    rcases hr with (((⟨⟨a, b⟩, hab, rfl⟩ | ⟨⟨a, b⟩, hab, rfl⟩) | ⟨⟨a, b⟩, hab, rfl⟩) | ⟨⟨a, b⟩, hab, rfl⟩) <;>
      simp only [Sila.murtabit.injEq] at hp <;> obtain ⟨rfl, rfl⟩ := hp <;>
      revert hab <;> decide

/-- ولا ارتباطَ بلا أصلٍ مودَع: «قلم»–«علم» مرفوضةٌ بأيّ سلسلةٍ في هذه القاعدة. -/
theorem qalam_ilm_marfud (c : Iddia Sila) (hc : c.qawl = .murtabit "قلم" "علم") :
    maqbul qaidaL aslB c = false := by
  cases hm : maqbul qaidaL aslB c
  · rfl
  · exact absurd (hc ▸ maqbul_murakhkhas qaidaL aslB c hm) murtabit_qalam_ilm_la_murakhkhas

/-! ## ٣. الشبكة والمركزيّة: الدرجة والمسافة، من نفس جدولَي اللزوم والمفعوليّة -/

/-- الارتباطُ المتماثل: من نفس ما يقرأه `aslB` (لزومٌ بوجهيه، أو طلبٌ ومفعولُه بوجهيه)؛ ليس حسابًا
    منفصلًا عن جدول الترخيص، بل الاختبارُ نفسُه معكوسًا على الطرفين. (تعميمُ هذا إلى مبرهنةٍ عامّة
    `∀ a b, adj a b → Murakhkhas qaidaL …` لكلّ a b لم يُبنَ هنا — الشاهدان `shahid_kataba_ilm_murtabit`
    و`shahid_talab_ilm_murtabit` أعلاه يثبتان حالتين منه بالفاحص نفسِه بعينه؛ وما بقي فعلى هذا الحساب
    المباشر على جدولَي `luzumat`/`talabMafulat` وحدهما، فلا دعوى ترخيصٍ عامّ غير مبنيّة.) -/
def adj (a b : String) : Bool :=
  aslB (.luzum a b) || aslB (.luzum b a) || aslB (.talabMaful a b) || aslB (.talabMaful b a)

/-- أسماءُ السبعة، لحساب الدرجة والمسافة عليها. -/
def asma : List String := judhur.map Prod.fst

/-- الوصولُ بخطوتين على الأكثر (مباشرةً أو بوسيط واحد من السبعة). -/
def dist2 (a b : String) : Bool := adj a b || asma.any (fun z => adj a z && adj z b)

/-- الوصولُ بثلاث خطواتٍ على الأكثر. -/
def dist3 (a b : String) : Bool := dist2 a b || asma.any (fun z => adj a z && dist2 z b)

/-- درجةُ الجذع: عددُ الآخرين الستّة المرتبطين به مباشرةً. -/
def darajaB (r : String) : Nat := (asma.filter (fun s => s != r && adj r s)).length

/-- **«علم» الأعلى درجةً حصرًا**: درجتُه 5 (من ٦ ممكنة: كلُّ الآخرين إلّا قلمًا)، وكلُّ غيره أدنى منها
    فعلًا — مبرهنٌ من بِنية الشهادات المودَعة في (٢) نفسِها، لا مفترَضًا ولا مرسومًا سلفًا. -/
theorem ilm_markaz : darajaB "علم" = 5 ∧ ∀ r ∈ asma, r ≠ "علم" → darajaB r < 5 := by decide

/-- درجاتُ الستّة الباقية، للمقارنة: كتب 3، درس وفهم وعقل 2، قلم وطلب 1 (كلُّها دون علم). -/
theorem darajat_baqiya :
    darajaB "كتب" = 3 ∧ darajaB "درس" = 2 ∧ darajaB "قلم" = 1 ∧
    darajaB "فهم" = 2 ∧ darajaB "طلب" = 1 ∧ darajaB "عقل" = 2 := by decide

/-- مسافاتُ «كتب»: علمٌ وقلمٌ ودرسٌ بخطوةٍ، وفهمٌ وعقلٌ وطلبٌ بخطوتين لا بخطوةٍ — تصحيحٌ معلَنٌ لِما
    تحتمله عبارة المالك («كتب يرتبط مع … فهم»): فهمٌ لا يلزم كتبًا مباشرةً في أيّ من المصدرين، بل عبر علم. -/
theorem masafat_kataba :
    adj "كتب" "علم" ∧ adj "كتب" "قلم" ∧ adj "كتب" "درس" ∧
    (¬ adj "كتب" "فهم" ∧ dist2 "كتب" "فهم") ∧
    (¬ adj "كتب" "عقل" ∧ dist2 "كتب" "عقل") ∧
    (¬ adj "كتب" "طلب" ∧ dist2 "كتب" "طلب") := by decide

/-- مسافاتُ «طلب»: علمٌ بخطوةٍ وحدَه، والباقي بخطوتين إلّا قلمًا بثلاث. هذا بعينه «ترتيبُ العلاقات
    بأولويّاتِ علم» الذي طلبه المالك: نفسُ السبعة تُعاد من مرساةٍ غير «كتب»، لكنّ أقربها الآن «علم»
    وحده (لا كتب، فلا سبيل لطلبٍ إلى كتبٍ إلّا عبر علم)، وأبعدها «قلم» الذي لا يرتبط بغير «كتب». -/
theorem masafat_talab :
    adj "طلب" "علم" ∧
    (¬ adj "طلب" "كتب" ∧ dist2 "طلب" "كتب") ∧
    (¬ adj "طلب" "درس" ∧ dist2 "طلب" "درس") ∧
    (¬ adj "طلب" "فهم" ∧ dist2 "طلب" "فهم") ∧
    (¬ adj "طلب" "عقل" ∧ dist2 "طلب" "عقل") ∧
    (¬ dist2 "طلب" "قلم" ∧ dist3 "طلب" "قلم") := by decide

/-- مسافاتُ «علم» نفسِه: الباقي كلُّه بخطوةٍ واحدةٍ إلّا قلمًا بخطوتين — «علم» مركزُ الشبكة فعلًا، لا
    بافتراض: كلُّ الآخرين الستّة على خطوةٍ منه أو خطوتين لا أكثر، وخمسةٌ منهم على خطوةٍ واحدة. -/
theorem masafat_ilm :
    adj "علم" "كتب" ∧ adj "علم" "درس" ∧ adj "علم" "فهم" ∧ adj "علم" "عقل" ∧ adj "علم" "طلب" ∧
    (¬ adj "علم" "قلم" ∧ dist2 "علم" "قلم") := by decide

/-! ## ٤. غرسٌ في Madlul/Dalala.lean: مطابقةٌ وتضمّنٌ وإلتزامٌ حقيقيّةٌ على كونٍ صغيرٍ من المقوّمات -/

/-- فضاءُ المقوّمات (كونٌ صغيرٌ للشاهد، لا دعوى استقصاء): 1 معرفةُ الشيء بالقلب (لسان س236711: تعريفُ
    «فهم» بعينه)، 2 زيادةُ العلم على الفهم (ما في «علم» فوق مجرّد الإدراك القلبيّ — فرقٌ يُثبته التضمّنُ
    التالي لا يُفترض)، 3 تقييدُ الحروف خطًّا (مدخل «كتب»)، 4 الأداةُ التي يُكتب بها (لسان س237932: أوّلُ
    تعريف «قلم» بعينه، ولذلك خارجةٌ عن معنى الكتابة ولازمةٌ لها ذهنًا). -/
def maanaD : String → Dalala.Maana Nat
  | "فهم" => fun x => x = 1
  | "علم" => fun x => x = 1 ∨ x = 2
  | "كتب" => fun x => x = 3
  | "قلم" => fun x => x = 4
  | _ => fun _ => False

def shuhudD : String → List String
  | "فهم" => ["لسان:236711"]
  | "علم" => ["لسان:236711", "مقاييس:32736"]
  | "كتب" => ["لسان:23989"]
  | "قلم" => ["لسان:237932"]
  | _ => []

def wadD : Dalala.Wad String Nat := ⟨maanaD, shuhudD⟩

/-- جدولُ اللزوم المودَع بين معنيي «كتب» و«قلم» وحدَهما — معلوماتٌ سابقة لا تُشتقّ من الوضع، على نسق
    `Dalala.Luzum` بعينه (اللزوم جدولٌ منفصل، الدستور والسند في رأس Madlul/Dalala.lean). -/
def ZD : Dalala.Luzum Nat := fun p q => p = maanaD "كتب" ∧ q = maanaD "قلم"

/-- **المطابقة**: كلّ واحدٍ من الأربعة يدلّ على معنى نفسه مطابقةً — تمامُ ما وُضع له لا جزءٌ منه. -/
theorem kull_mutabaqa_nafsiha :
    Dalala.Mutabaqa wadD "علم" (maanaD "علم") ∧ Dalala.Mutabaqa wadD "فهم" (maanaD "فهم") ∧
    Dalala.Mutabaqa wadD "كتب" (maanaD "كتب") ∧ Dalala.Mutabaqa wadD "قلم" (maanaD "قلم") :=
  ⟨⟨by decide, fun _ => Iff.rfl⟩, ⟨by decide, fun _ => Iff.rfl⟩,
   ⟨by decide, fun _ => Iff.rfl⟩, ⟨by decide, fun _ => Iff.rfl⟩⟩

/-- **التضمّن المبرهَن**: «علم» يدلّ على معنى «فهم» تضمّنًا — فهمٌ جزءٌ حقيقيٌّ غيرُ فارغٍ من علم (المقوّم
    1 فيهما معًا)، وعلمٌ زائدٌ عليه فعلًا (المقوّم 2 فيه لا في فهم) فليسا شيئًا واحدًا. -/
theorem ilm_tadammun_fahm : Dalala.Tadammun wadD "علم" (maanaD "فهم") :=
  ⟨by decide, ⟨1, rfl⟩, fun _ hx => Or.inl hx, 2, Or.inr rfl, by simp only [maanaD]; decide⟩

/-- **الالتزام المبرهَن**: «كتب» يدلّ على معنى «قلم» التزامًا — خارجٌ عن معنى الكتابة (المقوّم 4 ليس من
    المقوّم 3) ولازمٌ له في الذهن بشهادة جدول اللزوم المودَع `ZD` («القلم: الذي يكتب به»). -/
theorem kataba_iltizam_qalam : Dalala.Iltizam wadD ZD "كتب" (maanaD "قلم") :=
  ⟨by decide, ⟨4, rfl, by simp only [wadD, maanaD]; decide⟩, rfl, rfl⟩

/-! ## ٥. غرسٌ في Aql/QawaninDalala.lean: الثلاثُ مرخَّصةٌ جبريًّا بالقاعدة العامّة نفسِها (`qMutabaqa`،
    `qTadammun`، `qIltizam`)، على نسق `qShahid`/`aslShahid` بعينه — رمزيًّا، لا دعوى سلامةٍ (`salama`)
    ملموسةٍ هنا: تعميمُها إلى هذا الشاهد يحتاج `Wad`/`Luzum`/`lf`/`mn` مطابقةً لِما في (٤) حرفيًّا،
    ولم يُبنَ (معلنٌ لا مسكوتٌ عنه). معرّفات: كتب=1، علم=2؛ معنى الكتابة=10، معنى العلم=20، معنى الفهم=21
    (جزءٌ من 20)، معنى القلم=30 (خارجٌ عن 10 ولازمٌ له). -/

def qShahidLuzum : Qaida.Qaida QawaninDalala.Qadiyya :=
  ⟨"لزوم-جذوع-0.1",
   [QawaninDalala.qMutabaqa 2 20, QawaninDalala.qTadammun 2 20 21,
    QawaninDalala.qMutabaqa 1 10, QawaninDalala.qIltizam 1 10 30]⟩

def aslShahidLuzum : QawaninDalala.Qadiyya → Bool
  | .wad 2 20 | .juz 21 20 | .wad 1 10 | .kharij 30 10 | .luzum 10 30 => true
  | _ => false

theorem shahidLuzum_shakl : qShahidLuzum.qawanin.all QawaninDalala.shakl = true := by decide
theorem shahidLuzum_mutadarrija : Mutadarrija qShahidLuzum QawaninDalala.rutba := by
  unfold Mutadarrija; decide

/-- «علم» يدلّ على معنى «الفهم» تضمّنًا في القاعدة العامّة: من الوضع ثمّ المطابقة ثمّ الجزء. -/
theorem shahid_ilm_tadammun_fahm :
    maqbul qShahidLuzum aslShahidLuzum
      ⟨.tadammun 2 21, [.asl (.wad 2 20), .qanun 0, .asl (.juz 21 20), .qanun 1]⟩ = true := by
  decide

/-- «كتب» يدلّ على معنى «القلم» التزامًا في القاعدة العامّة: بشرط اللزوم المودَع، لا بدونه. -/
theorem shahid_kataba_iltizam_qalam :
    maqbul qShahidLuzum aslShahidLuzum
      ⟨.iltizam 1 30, [.asl (.wad 1 10), .qanun 2, .asl (.kharij 30 10), .asl (.luzum 10 30), .qanun 3]⟩ = true := by
  decide

end JadwalLuzum
end Jisr
