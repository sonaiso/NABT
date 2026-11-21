/-
  Madlul/JadwalLuzumNaql.lean — النقلُ لصفوف جدول اللزوم: كلُّ صفٍّ قضيّةٌ منقولة (`Naql.Naql` من `Aql/Naql.lean`).

  قولُ المالك في الجلسة (2026-10-25، 23:07 بتوقيت عمّان من بيانات الرسالة):
  «موافق على إضافة المبرهنات الثلاث وفقlean واربط مع النقل وبعدها اكمل الربط وفق افضل الممارسات ليكون كل المشروع مترابط ومتناسق ومتكامل وفق افضل الممارسات»
  وصدرُ رسالته بالإنجليزيّة سؤالُ البنّاء ألصقه بتعديلٍ منه: حذف «Should I» من أوّله، وجعل «Or should I» «Then you should I»، وحذف علامة الاستفهام من آخره:
  "build the two gaps as a separate PR: adding the three theorems to Audit.lean, and linking Naql to the dependency-table rows? Then you should I carry on with the items on your list"
  والثلاثُ سمّاها جوابُ البنّاء في الجلسة قبل السؤال (ليس في المستودع). والفجوةُ معلنةٌ في رأس `Aql/Naql.lean`: أعمدةُ القائل والدرجة
  ونوع الحقيقة أُجِّلت.

  السند (ج3، المودَع a2.txt):
  * س729: «والمراد بالعرب العرب الأقحاح الذين كانوا يتكلمون اللغة العربية قبل فساد اللسان العربي، وقد ظل قسم منهم، حتى القرن الرابع الهجري، كانوا يسكنون البادية، ولم تفسد لغتهم؛ ولذلك يؤخذ عنهم.»
    ثمّ: «أما طريق الأخذ عنهم فهي طريق الرواية الصحيحة، فاللفظ حتى يعتبر لفظاً عربياً لا بد أن يروى عن العرب بالرواية الصحيحة؛»
    والآحادُ فيه: «كالألفاظ المروية المعنعنة عن الأدباء الباحثين عن اللغة، كالخليل، والأصمعي، ونحوهما.»
  * س868، في التعريب: «وسواء أكان ذلك قبل فساد اللغة، أي قبل القرن الرابع الهجري، أم بعد فساد اللغة،» — فالزمنُ هناك ليس قيدًا للتعريب،
    والسطرُ يعيّن فسادَ اللغة بالقرن الرابع.
  * س892: «إذا احتمل النقل من الحقيقة اللغوية إلى الشرعية أو العرفية، أو عدم النقل، فالأصل عدم النقل».

  التعيين (تعيينُ البنّاء، معلن):
  * القائلُ المعجمُ نفسُه باسمه في `mudaat/sijill.json`: نسبةٌ قائمة بالبروتوكول خ٣ كما في `Aql/Naql.lean` (ووثيقةُ البروتوكول ليست في
    المستودع). ولا يُقرأ من السطر قائلٌ أدنى، كقولِ اللسان في سطر صفٍّ قائم: «وقال اللحياني» (س24031) — ذلك حكمٌ على نصّ المصدر لم يُبنَ.
  * الدرجةُ للزوج المرتَّب (جذرُ المادّة، الجذرُ الآخر): `Naql.binaDaraja` على عدد المعجمين المختومين اللذين في الجدول صفٌّ لهما بهذا الزوج
    (البروتوكول خ٤ كما في `Aql/Naql.lean`)، أيًّا كانت قراءةُ الحدّ. والاتّفاقُ اتّفاقُ الزوج لا نوعِ القضيّة: في فهم ← علم اللسانُ ترادفٌ
    (س236711) والمقاييسُ أصلٌ (س32736). واستقلالُ المعجمين لم يُفحص، و`Aql/Naql.lean` يشترطه؛ وسطرُ المقاييس نفسُه: «كذا يقولون أهل اللغة».
    وبلا صفٍّ للزوج لا درجة (`none`).
  * الحدُّ الزمانيّ بقراءتين، والقرارُ للمالك (`QiraaHadd`):
    - لعصر القائل الذي في الحقل، وهو المعجم: سندُها تعليقُ البنّاء على `NawNaql.mustahdathBadAlHadd` في `Aql/Naql.lean` («قائله بعد الحدّ الزمانيّ»).
      ومقياسُ عصره سنةُ وفاة صاحبه في رأس المودَع (`011.AuthorDIED`: اللسان 711، المقاييس 395)، وهذا تعيين. ونهايةُ الحدّ معاملٌ يقرّره
      المالك أيضًا: ج3 بين س868 («قبل القرن الرابع») وس729 («حتى القرن الرابع»)، و`Aql/Naql.lean` يجعل التعارضَ قرارَه. والقرنُ الرابع
      301–400 بالعدّ المعتاد، فنهايةُ س868 سنة 300 (`hadd868`)، ونهايةُ س729 إن شملت «حتى» القرنَ سنة 400 (`hadd729Shamil`) وإلّا 300.
    - أو لعصر المنقول عنه: بقراءة البنّاء لس729 («لا بد أن يروى عن العرب»)، والمعجمُ ناقلٌ. ولا تاريخَ للمنقول عنه في الصفّ، فلا حكم.
  * نوعُ الحقيقة: `mustahdathBadAlHadd` حيث أثبت الحدُّ الخروج، وإلّا `wadLughawi`. وس892 لا ينفي إلّا الشرعيّة والعرفيّة؛ ونفيُ المجاز
    والمعرَّب والصياغة تعيينٌ بلا سند. وفي المشروع حكمٌ يخالفه في صفَّي درس ← كتب (اللسان س115080، س115082): تعليقُ §٣ في `Madlul/Tarjih.lean`
    يجعل معنى الدراسة في «درس» مأخوذًا بالمشابهة، و`dars_laysa_mushtarak` تنفي الاشتراك بفرض أنّ سببه غيرُ الوضع الأوّل، ووصفُها أنّه مجازٌ إن
    لم يشتهر ومنقولٌ إن اشتهر؛ وعدُّ الصفّين من معنى الدراسة قراءةُ البنّاء. و`nawOf` تعطيهما قاعدةَ الأصل حيث لم يثبت الحدُّ الخروج. ولا يغيّر هذا «يصلح»، لأنّ `Naql.yasluhuAslanLughawiyyan` لا يقرأ النوع. والمستخرِجُ لا يُخرج علامةَ النقل عمودًا؛ وأقربُ
    الموجود في `shabaka/jadwal_luzum.py`: لا يُقرأ أصلٌ لابن فارس من مادّةٍ تطابق أوّلَ جملتها `ASL_NAFY` (ومن نمطه «فارسي» و«معرب»)،
    ما لم يطابقها النمطُ `YADULL`؛ ونمطا `HAML` و`ALAQA` في `shabaka/tarjih.py`، وهي أداةُ استكشاف، يعلّمان المأخوذَ بعلاقة (مجازًا أو منقولًا).
  * والقطعةُ تُسند إلى كلّ صفٍّ حقولًا بقاعدةٍ ثابتة من معجمه وجذريه وعلى الجدول، لا من حقل `w` (اللفظ المفسَّر أو المسمّى) ولا نوعِ قضيّته ولا سطره (`la_yaqra_lafz`)؛
    فعددتُها قطعةَ بنيةٍ خارج الضابط المجمَّد
    (البند 2أ في CLAUDE.md). وهذه قراءةُ البنّاء تنتظر إمضاء المالك: المنهجُ يسمّي من قطع البنية «الفاحص، والمخزن، والأدوات» وحدها،
    ومخرجُ القطعة حكمٌ على كلّ صفٍّ أيصلح نقلُه.

  المبرهنات (تكميمًا لا تصنيفًا؛ وتصنيفُها بالمعيار الموحَّد في CLAUDE.md):
  * لكلّ جدول: `la_mutawatir`، و`yashhad_saff`، و`mutadhafir_iff` (متعاضدٌ إذا وفقط إذا شهد المعجمان)، و`la_daraja_bila_saff`،
    و`daraja_jisr` (لصفٍّ لزوجه صفٌّ في الجدول: درجةُ `naqlOf` درجةُ زوجه)، و`bila_saff` (ولصفٍّ لا صفَّ لزوجه: آحادٌ ولا شيء)، و`la_yaqra_lafz`، و`yasluh_iff` (يصلح أصلًا لغويًّا إذا وفقط إذا لم يثبت الحدُّ خروجَه)،
    و`naw_hadd`، و`naw_ithnan`، و`iltizam_saff` (كلُّ التزامٍ مرخَّصٍ بلفظيه وراءه صفُّ تعليلٍ بهما).
  * لهذا الجدول: `iltizam_jadwal` (كلُّ التزامٍ مرخَّصٍ فيه صفُّه المقاييسُ س26425، ونقلُه يصلح إذا وفقط إذا لم يُخرج الحدُّ المقاييس).
  * على الشاهد: `shahid_hadd`، `shahid_daraja`، `shahid_qiraat`، `shahid_luzum_maqayis`، `shahid_fahm_juz_lisan`.
  بلا sorry ولا axiom ولا native_decide.
-/
import Madlul.JadwalLuzum
import Aql.Naql

namespace JadwalLuzum
open Qaida QawaninDalala

/-! ## ١. القائلُ والدرجة -/

/-- القائلُ: المعجمُ باسمه في سجلّ المودَعات. -/
def qailOf : Mujam → String
  | .lisan => "لسان العرب"
  | .maqayis => "مقاييس اللغة"

def kullMujam : List Mujam := [.lisan, .maqayis]

/-- يشهد المعجمُ للزوج (a ← b): في الجدول صفٌّ منه جذرُ مادّته a وجذرُه الآخر b. -/
def yashhad (T : List Saff) (a b : String) (m : Mujam) : Bool :=
  T.any fun r => r.mujam == m && r.a == a && r.b == b

def mujamat (T : List Saff) (a b : String) : List Mujam := kullMujam.filter (yashhad T a b)

/-- درجةُ نقل الزوج: لا درجةَ بلا شاهد، وإلّا `binaDaraja` على عدد المعجمين. -/
def darajaSila (T : List Saff) (a b : String) : Option Naql.Daraja :=
  match (mujamat T a b).length with
  | 0 => none
  | n => some (Naql.binaDaraja n)

/-! ## ٢. الحدُّ الزمانيّ بقراءتيه، ونوعُ الحقيقة -/

/-- سنةُ وفاة صاحب المعجم في رأس المودَع المختوم (`011.AuthorDIED`)؛ يطابقها `test_luzum.py` على المودَع. -/
def wafat : Mujam → Nat
  | .lisan => 711
  | .maqayis => 395

/-- نهايتا الحدّ من نصّي ج3 (والقرنُ الرابع 301–400): س868 «قبل القرن الرابع»، وس729 «حتى القرن الرابع» إن شملته. -/
def hadd868 : Nat := 300
def hadd729Shamil : Nat := 400

/-- قراءتا حقل الحدّ: لعصر القائل الذي في الحقل بنهايةٍ للحدّ، أو لعصر المنقول عنه. والقرارُ للمالك. -/
inductive QiraaHadd | asrQail (nihaya : Nat) | asrManqul
  deriving DecidableEq, Repr

def haddOf : QiraaHadd → Mujam → Option Bool
  | .asrQail b, m => some (decide (wafat m ≤ b))
  | .asrManqul, _ => none

/-- نوعُ الحقيقة: مستحدَثٌ بعد الحدّ حيث أثبت الحدُّ الخروج، وإلّا قاعدةُ الأصل. -/
def nawOf (q : QiraaHadd) (m : Mujam) : Naql.NawNaql :=
  if haddOf q m = some false then .mustahdathBadAlHadd else .wadLughawi

/-- النقلُ لصفٍّ في قراءةٍ للحدّ: قائلُه معجمُه، ودرجتُه بعدد معجمَي زوجه، وحدُّه ونوعُه بالقراءة. -/
def naqlOf (q : QiraaHadd) (T : List Saff) (r : Saff) : Naql.Naql :=
  ⟨some (qailOf r.mujam), Naql.binaDaraja (mujamat T r.a r.b).length, haddOf q r.mujam, nawOf q r.mujam⟩

/-! ## ٣. المبرهن لكلّ جدول -/

/-- الدرجةُ لا تكون متواترًا لأيّ جدولٍ وزوج. -/
theorem la_mutawatir (T : List Saff) (a b : String) : darajaSila T a b ≠ some .mutawatir := by
  unfold darajaSila
  split
  · simp
  · intro h
    exact Naql.la_mutawatir_min_al_add _ (Option.some.inj h)

/-- متعاضدٌ إذا وفقط إذا شهد المعجمان كلاهما للزوج. -/
theorem mutadhafir_iff (T : List Saff) (a b : String) :
    darajaSila T a b = some .mutadhafir ↔ yashhad T a b .lisan = true ∧ yashhad T a b .maqayis = true := by
  cases h1 : yashhad T a b .lisan <;> cases h2 : yashhad T a b .maqayis <;>
    simp [darajaSila, mujamat, kullMujam, List.filter, h1, h2, Naql.binaDaraja]

/-- يشهد معجمُ كلِّ صفٍّ لزوجه. -/
theorem yashhad_saff (T : List Saff) (r : Saff) (hr : r ∈ T) : yashhad T r.a r.b r.mujam = true := by
  simp only [yashhad, List.any_eq_true, Bool.and_eq_true, beq_iff_eq]
  exact ⟨r, hr, ⟨rfl, rfl⟩, rfl⟩

/-- ولا درجةَ إلّا بصفٍّ للزوج في الجدول. -/
theorem la_daraja_bila_saff (T : List Saff) (a b : String) :
    darajaSila T a b = none ↔ ¬ ∃ r ∈ T, r.a = a ∧ r.b = b := by
  constructor
  · intro h ⟨r, hr, ha, hb⟩
    have hy := yashhad_saff T r hr
    rw [ha, hb] at hy
    cases hm : r.mujam <;> rw [hm] at hy <;>
      cases h2 : yashhad T a b .lisan <;> cases h3 : yashhad T a b .maqayis <;>
      simp_all [darajaSila, mujamat, kullMujam, List.filter]
  · intro h
    have h1 : yashhad T a b .lisan = false := by
      simp only [yashhad, List.any_eq_false]
      intro r hr hc
      simp only [Bool.and_eq_true, beq_iff_eq] at hc
      exact h ⟨r, hr, hc.1.2, hc.2⟩
    have h2 : yashhad T a b .maqayis = false := by
      simp only [yashhad, List.any_eq_false]
      intro r hr hc
      simp only [Bool.and_eq_true, beq_iff_eq] at hc
      exact h ⟨r, hr, hc.1.2, hc.2⟩
    simp [darajaSila, mujamat, kullMujam, List.filter, h1, h2]

/-- لصفٍّ لزوجه صفٌّ في الجدول (ومنه كلُّ صفٍّ في الجدول): درجةُ `naqlOf` هي درجةُ زوجه. -/
theorem daraja_jisr (q : QiraaHadd) (T : List Saff) (r : Saff) (h : ∃ r' ∈ T, r'.a = r.a ∧ r'.b = r.b) :
    darajaSila T r.a r.b = some (naqlOf q T r).daraja := by
  obtain ⟨r', hr', ha, hb⟩ := h
  have hy := yashhad_saff T r' hr'
  rw [ha, hb] at hy
  cases hm : r'.mujam <;> rw [hm] at hy <;>
    cases h2 : yashhad T r.a r.b .lisan <;> cases h3 : yashhad T r.a r.b .maqayis <;>
    simp_all [darajaSila, naqlOf, mujamat, kullMujam, List.filter]

/-- ولصفٍّ لا صفَّ لزوجه في الجدول: تُعطي `naqlOf` آحادًا و`darajaSila` لا شيء — فالحسابان يفترقان هناك وحده. -/
theorem bila_saff (q : QiraaHadd) (T : List Saff) (r : Saff) (h : ¬ ∃ r' ∈ T, r'.a = r.a ∧ r'.b = r.b) :
    (naqlOf q T r).daraja = .ahad ∧ darajaSila T r.a r.b = none := by
  have hn := (la_daraja_bila_saff T r.a r.b).2 h
  refine ⟨?_, hn⟩
  have h0 : (mujamat T r.a r.b).length = 0 := by
    unfold darajaSila at hn
    split at hn
    · assumption
    · simp at hn
  simp [naqlOf, h0, Naql.binaDaraja]

/-- النقلُ لا يقرأ حقلَ `w` من الصفّ ولا نوعَ قضيّته ولا سطرَه: صفّان بمعجمٍ وجذرين واحدةٍ نقلُهما واحد. -/
theorem la_yaqra_lafz (q : QiraaHadd) (T : List Saff) (r r' : Saff)
    (hm : r.mujam = r'.mujam) (ha : r.a = r'.a) (hb : r.b = r'.b) : naqlOf q T r = naqlOf q T r' := by
  simp [naqlOf, hm, ha, hb]

/-- يصلح نقلُ الصفّ أصلًا لغويًّا (`Naql.yasluhuAslanLughawiyyan`) إذا وفقط إذا لم يثبت الحدُّ خروجَ معجمه. -/
theorem yasluh_iff (q : QiraaHadd) (T : List Saff) (r : Saff) :
    Naql.yasluhuAslanLughawiyyan (naqlOf q T r) = true ↔ haddOf q r.mujam ≠ some false := by
  simp [Naql.yasluhuAslanLughawiyyan, naqlOf]

/-- والنوعُ مستحدَثٌ بعد الحدّ إذا وفقط إذا أثبت الحدُّ الخروج. -/
theorem naw_hadd (q : QiraaHadd) (T : List Saff) (r : Saff) :
    (naqlOf q T r).naw = .mustahdathBadAlHadd ↔ (naqlOf q T r).fiAlHadd = some false := by
  simp only [naqlOf, nawOf]
  split <;> simp_all

/-- ولا نوعَ غيرُ اثنين: قاعدةُ الأصل أو المستحدَث. -/
theorem naw_ithnan (q : QiraaHadd) (T : List Saff) (r : Saff) :
    (naqlOf q T r).naw = .wadLughawi ∨ (naqlOf q T r).naw = .mustahdathBadAlHadd := by
  simp only [naqlOf, nawOf]
  split <;> simp

/-- كلُّ التزامٍ مرخَّصٍ في قاعدة الجدول وراءه صفُّ تعليلٍ لفظُه ولازمُه لفظا الالتزام. -/
theorem iltizam_saff (T : List Saff) {l k : Nat}
    (h : Murakhkhas (qaidaOf T) (fun p => aslB T p = true) (.iltizam l k)) :
    ∃ r ∈ T, r.naw = .luzum ∧ ism T (lafz r) = l ∧ ism T r.b = k := by
  generalize hp : Qadiyya.iltizam l k = p at h
  cases h with
  | asl ha =>
    subst hp
    obtain ⟨r, _, hr⟩ := (aslB_iff T _).mp ha
    have := asl_rutba_sifr T r _ hr
    simp [rutba] at this
  | qanun q hq _ =>
    simp only [qaidaOf, List.mem_flatMap] at hq
    obtain ⟨r, hrT, hqr⟩ := hq
    refine ⟨r, hrT, ?_⟩
    cases hn : r.naw with
    | juz | asl =>
      simp only [qawaninOf, hn, List.mem_cons, List.not_mem_nil, or_false] at hqr
      rcases hqr with rfl | rfl <;> simp [qMutabaqa, qTadammun] at hp
    | taraduf | kharij =>
      simp only [qawaninOf, hn, List.mem_cons, List.not_mem_nil, or_false] at hqr
      subst hqr; simp [qMutabaqa] at hp
    | luzum =>
      simp only [qawaninOf, hn, List.mem_cons, List.not_mem_nil, or_false] at hqr
      rcases hqr with rfl | rfl
      · simp [qMutabaqa] at hp
      · simp only [qIltizam, Qadiyya.iltizam.injEq] at hp
        exact ⟨rfl, hp.1.symm, hp.2.symm⟩

/-! ## ٤. لهذا الجدول، وعلى الشاهد -/

/-- صفوفُ التعليل في الجدول: صفٌّ واحد، من المقاييس س26425. -/
theorem shahid_luzum_maqayis :
    (jadwal.filter fun r => r.naw == .luzum).map (fun r => (r.mujam, r.satr)) = [(.maqayis, 26425)] := by decide

/-- كلُّ التزامٍ مرخَّصٍ في قاعدة هذا الجدول صفُّه المقاييسُ س26425؛ ونقلُه يصلح إذا وفقط إذا لم يُخرج الحدُّ المقاييس. -/
theorem iltizam_jadwal {l k : Nat}
    (h : Murakhkhas (qaidaOf jadwal) (fun p => aslB jadwal p = true) (.iltizam l k)) :
    ∃ r ∈ jadwal, r.naw = .luzum ∧ ism jadwal (lafz r) = l ∧ ism jadwal r.b = k ∧
      r.mujam = .maqayis ∧ r.satr = 26425 ∧
      ∀ q, (Naql.yasluhuAslanLughawiyyan (naqlOf q jadwal r) = true ↔ haddOf q .maqayis ≠ some false) := by
  obtain ⟨r, hr, hn, hl, hk⟩ := iltizam_saff jadwal h
  have hall : ∀ r ∈ jadwal, r.naw = .luzum → r.mujam = .maqayis ∧ r.satr = 26425 := by decide
  obtain ⟨hm, hs⟩ := hall r hr hn
  refine ⟨r, hr, hn, hl, hk, hm, hs, fun q => ?_⟩
  rw [yasluh_iff, hm]

/-- الحدُّ في القراءات: بنهاية س868 يخرج المعجمان، وبنهاية س729 الشاملة يدخل المقاييسُ ويخرج اللسان، وفي عصر المنقول عنه لا حكم. -/
theorem shahid_hadd :
    haddOf (.asrQail hadd868) .lisan = some false ∧ haddOf (.asrQail hadd868) .maqayis = some false ∧
    haddOf (.asrQail hadd729Shamil) .lisan = some false ∧ haddOf (.asrQail hadd729Shamil) .maqayis = some true ∧
    kullMujam.all (fun m => haddOf .asrManqul m == none) = true := by decide

/-- درجاتُ الأزواج المرتَّبة بين جذور الشبكة في الجدول، وهي سبعةٌ لا غير: فهم ← علم متعاضدة (اللسان س236711 والمقاييس س32736)،
    والستّةُ الباقية آحاد؛ والعكسُ علم ← فهم بلا درجة. -/
theorem shahid_daraja :
    let sh := ["كتب", "درس", "قلم", "علم", "فهم", "طلب", "عقل"]
    ((jadwal.filter fun r => sh.contains r.a && sh.contains r.b).map fun r => (r.a, r.b)).eraseDups =
      [("كتب", "علم"), ("درس", "كتب"), ("عقل", "فهم"), ("فهم", "علم"), ("فهم", "عقل"), ("قلم", "كتب"), ("عقل", "طلب")] ∧
    darajaSila jadwal "فهم" "علم" = some .mutadhafir ∧
    [("كتب", "علم"), ("درس", "كتب"), ("عقل", "فهم"), ("فهم", "عقل"), ("قلم", "كتب"), ("عقل", "طلب")].all
      (fun p => darajaSila jadwal p.1 p.2 == some .ahad) = true ∧
    darajaSila jadwal "علم" "فهم" = none := by decide

/-- الصفوفُ التي يصلح نقلُها في القراءتين، والأولى بنهايتيها: بنهاية س868 لا صفّ، وبنهاية س729 الشاملة صفوفُ المقاييس الثلاثةَ عشرَ وحدها،
    وفي عصر المنقول عنه الثلاثون. -/
theorem shahid_qiraat :
    (jadwal.filter fun r => Naql.yasluhuAslanLughawiyyan (naqlOf (.asrQail hadd868) jadwal r)).length = 0 ∧
    (jadwal.filter fun r => Naql.yasluhuAslanLughawiyyan (naqlOf (.asrQail hadd729Shamil) jadwal r)).length = 13 ∧
    (jadwal.filter fun r => Naql.yasluhuAslanLughawiyyan (naqlOf (.asrQail hadd729Shamil) jadwal r)).all
      (·.mujam == .maqayis) = true ∧
    (jadwal.filter fun r => Naql.yasluhuAslanLughawiyyan (naqlOf .asrManqul jadwal r)).length = 30 := by decide

/-- وأجزاءُ «الفهم» في الجدول (عرف، قلب) من اللسان وحده (س236711)؛ فلا يصلح نقلُها في عصر القائل بأيّ النهايتين. -/
theorem shahid_fahm_juz_lisan :
    (jadwal.filter fun r => r.a == "فهم" && r.naw == .juz).map (fun r => (r.mujam, r.b, r.satr)) =
      [(.lisan, "عرف", 236711), (.lisan, "قلب", 236711)] ∧
    [hadd868, hadd729Shamil].all (fun b => (jadwal.filter fun r => r.a == "فهم" && r.naw == .juz).all
      (fun r => !Naql.yasluhuAslanLughawiyyan (naqlOf (.asrQail b) jadwal r))) = true := by decide

end JadwalLuzum
