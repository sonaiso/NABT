/-
# نفيُ الفعل وحروفُ الفعل عند سيبويه (الكتاب، س9755–9787)

**المصدر.** `sibawayhi.txt` المختوم (`a160f940…`)، الأسطر 9755–9787، وفيها ثلاثةُ أبواب: «هذا باب الحروف التي لا يليها بعدها إلا
الفعل ولا تغير الفعل عن حاله …» (9755–9771)، و«هذا باب الحروف التي يجوز أن يليها بعدها الأسماء ويجوز أن يليها بعدها الأفعال»
(9772–9781)، و«هذا باب نفي الفعل» (9782–9787). ورقمُ السطر خاصٌّ بهذا الملفّ. والاقتباساتُ في `asanid` قطعٌ حرفيّة، يفحصها
`tahaqquq/test_nafy.py` على المودَع موصولةَ الأسطر.

**نوعا السؤال** (حقولُ مواصفة الضابط المجمَّد `tahaqquq/dawabit/nafy/wasf.md` بأعيانها):
1. `Sual`: صورةٌ للفعل، ووجهةٌ (نفيُها أو إثباتُها)، وحالُ الفعل، والسياق. والجوابُ `jawab`: قائمةُ الصور أو «لا حكم» (`none`).
2. `hukmWali`: حرفٌ وما يليه، والجوابُ درجتُه في الكلام وفي الشعر.

**المدخلُ تحليلٌ يُعطى، لا مُخرَجُ قارئٍ من النصّ** (P4 لم يُبنَ).

**الأزمنةُ الخمسة** من `Aql/Awwaliyyat.lean` بأعيانها (`Zaman5`، `ithbat`، `nafy`، `ithbatQasam`، `nafyQasam`)، وهي قراءةُ البنّاء لهذا
الباب (`Awwaliyyat.lean` §٦: «سيبويه لا يقول خمسة أزمنة لفظًا»): هذا الملفّ لا يكتب جدولَ النفي ثانيةً، بل يسأله. فالضابطُ على هذه القطعة
قياسٌ لتلك الشفرة القائمة ولِما زِيد عليها هنا — **أعمى في القراءة لا في السياق**: حُقن في سياق المؤلّف `CLAUDE.md` وفيه وصفُ ذلك الجدول نفسه
(`tahaqquq/dawabit/nafy/mulhaq_1.md`).

**ما هو تعيينُ البنّاء** (لا نصُّ الباب):
- **الحال.** «يفعل» صورةُ زمنين (`Awwaliyyat.ithbat_la_yukhallis`). فالحالُ `hal` تختار «ما يفعل» (س9785: «أي هو في حال فعل»)،
  و`ghayrWaqi` تختار «لا يفعل» (س9786: «ولم يكن الفعل واقعا»)، و`ghayrMuallan` تُخرج الاثنتين. **وتُصفّي الحالُ صورتي القسم كذلك**:
  «ليفعلن» مستقبلٌ، فلا تُجاب مع `hal` (`hal_tusaffi_qasam`). ولا أثرَ لها في غير هذه الصور.
- **القسم.** صورتا القسم («لقد فعل»، «ليفعلن») تُجابان بنفيهما (س9784–9785، س9786–9787) في السياق غير المعلَن وفي القسم. والصورةُ
  المطلقة في سياق القسم («والله فعل» ونحوه) «لا حكم»: لم يذكرها الباب.
- **جوابُ «هل».** «ما فعل جوابا لهل فعل إذا أخبرت أنه لم يقع» (س9758): نفيُ «فعل» في هذا السياق «ما فعل» وحده. ولا حكمَ لغيره
  في هذا السياق، ولا لإثبات شيءٍ فيه. **ولا يُعكس هذا الصفّ** في الإثبات بلا سياق: إثباتُ «ما فعل» بلا سياقٍ «لقد فعل» وحدها (من صفّ القسم)،
  وصفُّ القسم يُعكس («لا يفعل» ← «ليفعلن»).
- **السين.** «سوف يفعل لأنها بمنزلة السين التي في قولك سيفعل … وإنما هي إثبات لقوله لن يفعل» (س9760–9762): «سيفعل» تُنفى بما تُنفى به
  «سوف يفعل»، وإثباتُ «لن يفعل» الصورتان معًا. وعودُ «هي» على السين وسوف معًا قراءتي.
- **الإثبات** عكسُ الجدول: صورُ الإثبات التي نفيُها الصورةُ المعطاة، مطلقةً في السياق غير المعلَن، وقسميّةً في غير المعلَن والقسم.
  فإثباتُ «لا يفعل» بلا سياقٍ «يفعل» و«ليفعلن» معًا. والحالُ تُصفّي الإثبات كما تُصفّي النفي.
- **حروفُ الفعل** (`hukmWali`):
  - «لا يفصل بينها وبين الفعل» (`laYufsal`): قد (س9757)، ولمّا (س9759: «أشبهت قد لما في أنها لا يفصل»)، وسوف (س9760–9762)، ولن (س9762:
    «فأشبهتها في أن لا يفصل»؛ **وعودُ «ها» على «لن» قراءتي**، و«قد» مرشّحٌ آخر). والاسمُ بعدها خطأٌ في الكلام، ولا حكمَ له في الشعر.
  - «أخلصوهن للفعل» (`mukhlasa`): ربما وقلما (س9762–9765)، وهلا ولولا وألا (س9765–9766). والاسمُ قبل الفعل خطأٌ في الكلام ومقبولٌ في
    الشعر («وقد يجوز في الشعر تقديم الاسم»، س9766–9767). **وقصرُ إذن الشعر على هذه دون `laYufsal` قراءتي**: هو بعد «أخلصوهن للفعل»
    وشاهدُه «قلما».
  - «كما» (س9778: «صيرت للفعل كما صيرت للفعل ربما»): الفعلُ مقبول، والاسمُ خطأٌ في الكلام، ولا حكمَ له في الشعر (الإذنُ في الباب
    قبله).
  - حروفُ الاستفهام هل وكيف ومن (س9769–9770): الفعلُ «أولى» فهو مقبول، والاسمُ قبله `marjuh`. ولا حكمَ للاسم وحده: العبارةُ فيما اجتمع
    بعدها اسمٌ وفعل.
  - لكن وإنما وكأنما وإذ (س9774): «يجوز أن يليها بعدها الأسماء ويجوز أن يليها بعدها الأفعال» (س9772–9773)، فكلُّها مقبولة.
  - **والشعرُ عامّةً** (تعيين): ما قُبل في الكلام قُبل في الشعر (`maqbul_kalam_maqbul_shir`)، والمرجوحُ في الكلام مرجوحٌ في الشعر؛ ولا سطرَ في
    النطاق يتكلّم عن الشعر إلّا س9766–9767.
  - «رب» و«قل» بلا «ما» (`bilaMa`): الفعلُ بعدهما خطأ («لم يكن لهم سبيل إلى رب يقول ولا إلى قل يقول»، س9764)، ولا حكمَ لغيره.
    **أُضيف بعد قراءة الحالات** (N20)، فالتشغيلُ الثاني على مادّةٍ مكشوفة.
  - وغيرُها «لا حكم».

**المنهج.** شفرةُ هذا الملفّ كُتبت قبل أن يقرأ البنّاءُ حالاتِ الضابط، وجُمّدت الحالاتُ قبلها
(`tahaqquq/dawabit/nafy/tajmid.json`؛ `hawkama/منهج_الضوابط.md`)، ودُفعت في `e7ac675`، والتشغيلُ الأوّل عليها في `natija_1.json`
(32/33). **وبعد قراءة الحالات** أُضيف `bilaMa` وسندُه وشاهدُه، فالتشغيلُ الثاني (`natija_2.json`) على مادّةٍ مكشوفة. **وبعد مراجعة
`murajii`** صُحّح الرأسُ (أثرُ الحال في صورتي القسم، وأسطرٌ ستّة، وما هو قراءتي) وأُضيف شاهدا `hal_tusaffi_qasam` و`huruf_jadwal`، بلا
تغييرٍ في الأحكام (`natija_3.json`). ونتيجتُها على الضابط في `Jisr/NafyFilQiyas.lean`، لا هنا.
-/
import Aql.Awwaliyyat

namespace Jisr
namespace NafyFil

open Aql.Awwaliyyat

/-! ## النوع الأوّل: نفيُ الصورة وإثباتُها -/

inductive Jiha
  | nafy | ithbat
  deriving DecidableEq, Repr

inductive Hal
  | hal | ghayrWaqi | ghayrMuallan
  deriving DecidableEq, Repr

inductive Siyaq
  | qasam | jawabHal | ghayrMuallan
  deriving DecidableEq, Repr

structure Sual where
  jiha : Jiha
  sura : String
  hal : Hal
  siyaq : Siyaq
  deriving DecidableEq, Repr

/-- الأزمنةُ الخمسة بترتيب `Awwaliyyat.nafy_asma`. -/
def azmina : List Zaman5 := [.madiMunqati, .madiMuttasil, .hal, .mustaqbal, .mustaqbalMunaffas]

/-- الحالُ توافق الزمن: الحالُ تنفي المستقبل، وغيرُ الواقع ينفي الحال، وغيرُ المعلَن يوافق الكلّ. -/
def halYuwafiq : Hal → Zaman5 → Bool
  | .hal, .mustaqbal => false
  | .ghayrWaqi, .hal => false
  | _, _ => true

/-- «سيفعل» بمنزلة «سوف يفعل» (س9760). -/
def sin (s : String) : String := if s = "سيفعل" then "سوف يفعل" else s

/-- النفي: من الجدول المطلق في غير القسم، ومن جدول القسم في غير جواب «هل». -/
def nafyOf (q : Sual) : List String :=
  let s := sin q.sura
  let mutlaq := (azmina.filter (fun z => ithbat z == s && halYuwafiq q.hal z)).filterMap (fun z =>
    match q.siyaq with
    | .ghayrMuallan => some (nafy z)
    | .jawabHal => if z = .madiMunqati then some "ما فعل" else none
    | .qasam => none)
  let qasam := azmina.filterMap (fun z =>
    if ithbatQasam z == some s && q.siyaq != .jawabHal && halYuwafiq q.hal z then nafyQasam z else none)
  (mutlaq ++ qasam).eraseDups

/-- الإثبات: عكسُ الجدولين، و«سيفعل» مع «سوف يفعل». -/
def ithbatOf (q : Sual) : List String :=
  let mutlaq := (azmina.filter (fun z => nafy z == q.sura && halYuwafiq q.hal z && q.siyaq == .ghayrMuallan)).map ithbat
  let qasam := azmina.filterMap (fun z =>
    if nafyQasam z == some q.sura && q.siyaq != .jawabHal && halYuwafiq q.hal z then ithbatQasam z else none)
  let r := (mutlaq ++ qasam).eraseDups
  if r.contains "سوف يفعل" then r ++ ["سيفعل"] else r

/-- **الجواب:** قائمةُ الصور، أو «لا حكم» (`none`) إن خلت. -/
def jawab (q : Sual) : Option (List String) :=
  let r := match q.jiha with
    | .nafy => nafyOf q
    | .ithbat => ithbatOf q
  if r.isEmpty then none else some r

/-! ## النوع الثاني: ما يلي الحرف -/

inductive Yali
  | fil | ismThummaFil | ism
  deriving DecidableEq, Repr

inductive Daraja
  | maqbul | marjuh | qabih | khata | laHukm
  deriving DecidableEq, Repr

structure Hukm where
  kalam : Daraja
  shir : Daraja
  deriving DecidableEq, Repr

def laYufsal : List String := ["قد", "لما", "سوف", "لن"]
def mukhlasa : List String := ["ربما", "قلما", "هلا", "لولا", "ألا"]
def istifham : List String := ["هل", "كيف", "من"]
def yajuz : List String := ["لكن", "إنما", "كأنما", "إذ"]
/-- «رب» و«قل» بلا «ما» (س9764؛ أُضيف بعد قراءة الحالات، `natija_2.json`). -/
def bilaMa : List String := ["رب", "قل"]

def hukmWali (harf : String) (y : Yali) : Hukm :=
  if harf ∈ laYufsal then
    match y with
    | .fil => ⟨.maqbul, .maqbul⟩
    | _ => ⟨.khata, .laHukm⟩
  else if harf ∈ mukhlasa then
    match y with
    | .fil => ⟨.maqbul, .maqbul⟩
    | .ismThummaFil => ⟨.khata, .maqbul⟩
    | .ism => ⟨.khata, .laHukm⟩
  else if harf = "كما" then
    match y with
    | .fil => ⟨.maqbul, .maqbul⟩
    | _ => ⟨.khata, .laHukm⟩
  else if harf ∈ istifham then
    match y with
    | .fil => ⟨.maqbul, .maqbul⟩
    | .ismThummaFil => ⟨.marjuh, .marjuh⟩
    | .ism => ⟨.laHukm, .laHukm⟩
  else if harf ∈ yajuz then ⟨.maqbul, .maqbul⟩
  else if harf ∈ bilaMa then
    match y with
    | .fil => ⟨.khata, .laHukm⟩
    | _ => ⟨.laHukm, .laHukm⟩
  else ⟨.laHukm, .laHukm⟩

/-! ## الأسانيد (قطعٌ حرفيّة؛ يفحصها `tahaqquq/test_nafy.py` موصولةَ الأسطر) -/

def asanid : List (String × Nat × Nat × String) := [
  ("nafyFaala", 9783, 9783, "إذا قال فعل فإن نفيه لم يفعل"),
  ("nafyQadFaala", 9783, 9783, "وإذا قال قد فعل فإن نفيه لما يفعل"),
  ("nafyLaqad", 9783, 9785, "وإذا قال لقد فعل فإن نفيه ما فعل لأنه كأنه قال والله لقد فعل فقال والله ما فعل"),
  ("nafyHal", 9785, 9785, "وإذا قال هو يفعل أي هو في حال فعل فإن نفيه ما يفعل"),
  ("nafyGhayrWaqi", 9785, 9786, "وإذا قال هو يفعل ولم يكن الفعل واقعا فنفيه لا يفعل"),
  ("nafyLayafalanna", 9786, 9787, "وإذا قال ليفعلن فنفيه لا يفعل كأنه قال والله ليفعلن فقلت والله لا يفعل"),
  ("nafySawfa", 9787, 9787, "وإذا قال سوف يفعل فإن نفيه لن يفعل"),
  ("jawabHal", 9758, 9758, "كما كانت ما فعل جوابا لهل فعل إذا أخبرت أنه لم يقع"),
  ("qad", 9757, 9757, "فمن تلك الحروف قد لا يفصل بينها وبين الفعل بغيره"),
  ("lamma", 9758, 9760, "ولما يفعل وقد فعل إنما هما لقوم ينتظرون شيئا فمن ثم أشبهت قد لما في أنها لا يفصل بينها وبين الفعل"),
  ("sawfaSin", 9760, 9761, "ومن تلك الحروف أيضا سوف يفعل لأنها بمنزلة السين التي في قولك سيفعل"),
  ("sawfaLan", 9761, 9762, "وإنما هي إثبات لقوله لن يفعل فأشبهتها في أن لا يفصل بينها وبين الفعل"),
  ("rubbama", 9762, 9763, "ومن تلك الحروف ربما وقلما وأشباههما جعلوا رب مع ما بمنزلة كلمة واحدة وهيئوها ليذكر بعدها الفعل"),
  ("rubbaYaqul", 9764, 9764, "لأنهم لم يكن لهم سبيل إلى رب يقول ولا إلى قل يقول"),
  ("akhlasuhuma", 9764, 9765, "فألحقوهما ما وأخلصوهما للفعل"),
  ("halla", 9765, 9766, "ومثل ذلك هلا ولولا وألا ألزموهن لا وجعلوا كل واحدة مع لا بمنزلة حرف واحد وأخلصوهن للفعل"),
  ("shir", 9766, 9767, "وقد يجوز في الشعر تقديم الاسم"),
  ("istifham", 9769, 9770, "إذا اجتمع بعد حروف الاستفهام نحو هل وكيف ومن اسم وفعل كان الفعل بأن يلي حرف الاستفهام أولى"),
  ("yajuz", 9772, 9773, "الحروف التي يجوز أن يليها بعدها الأسماء ويجوز أن يليها بعدها الأفعال"),
  ("yajuzHuruf", 9774, 9774, "وهي لكن وإنما وكأنما وإذ ونحو ذلك"),
  ("kama", 9777, 9778, "فزعم أن ما والكاف جعلتا بمنزلة حرف واحد وصيرت للفعل كما صيرت للفعل ربما")]

/-! ## مبرهنات (خواصُّ التعيين على مجاله؛ والضابطُ يشهد أنّه غيرُ فارغ: `Jisr/NafyFilQiyas.lean`) -/

/-- **الجوابُ لا يكون قائمةً فارغة** (تعريفيّة): «لا حكم» يُقال `none`، لا `some []`. -/
theorem jawab_ghayr_farigh (q : Sual) (l : List String) (h : jawab q = some l) : l ≠ [] := by
  unfold jawab at h
  intro hl
  subst hl
  simp at h

/-- **النفيُ على الأزمنة الخمسة** (على الشاهد): كلُّ صورة إثباتٍ مطلقةٍ بحالها المعيِّنة نفيُها صورةُ `Awwaliyyat.nafy` وحدها. -/
theorem nafy_khamsa :
    [(Zaman5.madiMunqati, Hal.ghayrMuallan), (.madiMuttasil, .ghayrMuallan), (.hal, .hal), (.mustaqbal, .ghayrWaqi),
     (.mustaqbalMunaffas, .ghayrMuallan)].map (fun p => jawab ⟨.nafy, ithbat p.1, p.2, .ghayrMuallan⟩) =
    azmina.map (fun z => some [nafy z]) := by
  decide

/-- **«يفعل» بلا حال صورتان** (على الشاهد): الحالُ لا تُعرف من الصورة، فالجوابُ البديلان. -/
theorem yafal_bila_hal :
    jawab ⟨.nafy, "يفعل", .ghayrMuallan, .ghayrMuallan⟩ = some ["ما يفعل", "لا يفعل"] := by
  decide

/-- **صورتا القسم** (على الشاهد): «لقد فعل» ← «ما فعل»، و«ليفعلن» ← «لا يفعل»؛ وإثباتُ «لا يفعل» في القسم «ليفعلن» وحدها، وبلا سياقٍ
    «يفعل» و«ليفعلن». -/
theorem qasam_shawahid :
    jawab ⟨.nafy, "لقد فعل", .ghayrMuallan, .ghayrMuallan⟩ = some ["ما فعل"] ∧
    jawab ⟨.nafy, "ليفعلن", .ghayrMuallan, .ghayrMuallan⟩ = some ["لا يفعل"] ∧
    jawab ⟨.ithbat, "لا يفعل", .ghayrMuallan, .qasam⟩ = some ["ليفعلن"] ∧
    jawab ⟨.ithbat, "لا يفعل", .ghayrMuallan, .ghayrMuallan⟩ = some ["يفعل", "ليفعلن"] := by
  decide

/-- **السين وجوابُ «هل»** (على الشاهد). -/
theorem sin_wa_hal :
    jawab ⟨.nafy, "سيفعل", .ghayrMuallan, .ghayrMuallan⟩ = some ["لن يفعل"] ∧
    jawab ⟨.ithbat, "لن يفعل", .ghayrMuallan, .ghayrMuallan⟩ = some ["سوف يفعل", "سيفعل"] ∧
    jawab ⟨.nafy, "فعل", .ghayrMuallan, .jawabHal⟩ = some ["ما فعل"] ∧
    jawab ⟨.nafy, "قد فعل", .ghayrMuallan, .jawabHal⟩ = none := by
  decide

/-- **ما لا يذكره الباب «لا حكم»** (على الشاهد): الصورةُ المطلقة في سياق القسم، وصورةٌ لا في الجدول. -/
theorem la_hukm_shawahid :
    jawab ⟨.nafy, "فعل", .ghayrMuallan, .qasam⟩ = none ∧
    jawab ⟨.nafy, "افعل", .ghayrMuallan, .ghayrMuallan⟩ = none := by
  decide

/-- **«لا يفصل بينها وبين الفعل»** (تعريفيّة): الاسمُ بعد حروف `laYufsal` خطأٌ في الكلام. -/
theorem la_yufsal_khata (h : String) (y : Yali) (hh : h ∈ laYufsal) (hy : y ≠ .fil) :
    (hukmWali h y).kalam = .khata := by
  unfold hukmWali
  cases y <;> simp_all

/-- **«رب» و«قل» بلا «ما»** (على الشاهد؛ أُضيف بعد قراءة الحالات). -/
theorem rubba_bila_ma :
    hukmWali "رب" .fil = ⟨.khata, .laHukm⟩ ∧ hukmWali "قل" .fil = ⟨.khata, .laHukm⟩ ∧
    hukmWali "ربما" .fil = ⟨.maqbul, .maqbul⟩ := by
  decide

/-- **الحالُ تُصفّي صورتي القسم** (على الشاهد؛ بعد المراجعة): «ليفعلن» مستقبلٌ، فلا تُجاب مع الحال. -/
theorem hal_tusaffi_qasam :
    jawab ⟨.nafy, "ليفعلن", .hal, .ghayrMuallan⟩ = none ∧
    jawab ⟨.ithbat, "لا يفعل", .hal, .ghayrMuallan⟩ = none ∧
    jawab ⟨.ithbat, "ما فعل", .ghayrMuallan, .ghayrMuallan⟩ = some ["لقد فعل"] := by
  decide

/-- **جدولُ الحروف** (على الشاهد؛ بعد المراجعة): الاسمُ قبل الفعل بعد كلّ حرفٍ في القوائم، كلامًا وشعرًا. -/
theorem huruf_jadwal :
    ["قد", "لما", "سوف", "لن", "ربما", "قلما", "هلا", "لولا", "ألا", "كما", "هل", "كيف", "من", "لكن", "إنما", "كأنما", "إذ"].map
      (fun h => hukmWali h .ismThummaFil) =
    [⟨.khata, .laHukm⟩, ⟨.khata, .laHukm⟩, ⟨.khata, .laHukm⟩, ⟨.khata, .laHukm⟩,
     ⟨.khata, .maqbul⟩, ⟨.khata, .maqbul⟩, ⟨.khata, .maqbul⟩, ⟨.khata, .maqbul⟩, ⟨.khata, .maqbul⟩,
     ⟨.khata, .laHukm⟩, ⟨.marjuh, .marjuh⟩, ⟨.marjuh, .marjuh⟩, ⟨.marjuh, .marjuh⟩,
     ⟨.maqbul, .maqbul⟩, ⟨.maqbul, .maqbul⟩, ⟨.maqbul, .maqbul⟩, ⟨.maqbul, .maqbul⟩] := by
  decide

/-- **ما قُبل في الكلام قُبل في الشعر** (تعريفيّة). -/
theorem maqbul_kalam_maqbul_shir (h : String) (y : Yali) (hk : (hukmWali h y).kalam = .maqbul) :
    (hukmWali h y).shir = .maqbul := by
  unfold hukmWali at *
  by_cases h1 : h ∈ laYufsal <;> by_cases h2 : h ∈ mukhlasa <;> by_cases h3 : h = "كما" <;>
    by_cases h4 : h ∈ istifham <;> by_cases h5 : h ∈ yajuz <;> by_cases h6 : h ∈ bilaMa <;> cases y <;> simp_all
