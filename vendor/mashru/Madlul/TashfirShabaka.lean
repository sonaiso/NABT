/-
  Madlul/TashfirShabaka.lean — جسرُ المعلومة المعمَّم (الثامن): طيُّ وفكُّ بنى Madlul.Shabaka (alaqat):
  Luzum، Uslub، Fil، Qawl (أحدَ عشرَ منشِئًا)، وShabaka نفسُها (ستّةُ حقولٍ List(String×String)).

  السند: نفسُ تفويض المالك 2026-10-17 22:55 («alaqat/hawass/awwaليyyat/makan/isnad … ابني واكتشف كيف
  نقرا/تبني من الرياضيات»). الخمسةُ الباقيةُ من الاسم الثمانيّ قبل هذه القطعة: hawass وmakan وawwaliyyat
  بُنيت، وalaqat (هذه القطعة) وisnad تبقيان. قُرئ Madlul/Shabaka.lean كاملًا (474 سطرًا) فرشةً هذه الجلسةُ
  قبل التصميم، معَ Madlul/TashfirKhawass.lean وMadlul/TashfirSullam.lean (لاستبعادهما: الأولى تكفي
  `listEnc`/`listDec` ذاتَيهما؛ الثانية تعمّم Tayy على درجة سلّم SLGE لا على «قائمة نصوص» — مشكلةٌ مختلفة).

  **المشكلة الجديدة.** TashfirHawass أغلق حقلين/ثلاثةَ حقولٍ نصّيّةٍ **بعددٍ ثابتٍ معلومٍ** (Tasmiya اثنان،
  Khibra ثلاثة) بتسلسل `splitAtSep` مرّتين أو ثلاثًا يدويًّا. هنا العددُ **غيرُ ثابت**: كلُّ حقلٍ من حقول
  Shabaka السّتّة `List (String × String)` طولُه غيرُ محدود، وQawl أحدَ عشرَ منشِئًا كلٌّ يحمل اثنتين أو
  ثلاثَ نصوصٍ — فلا تسلسلَ ثابتَ العدد من `splitAtSep` يغلق «عددًا غيرَ محدودٍ من نصوصٍ غيرِ محدودة الطول»
  دفعةً واحدة.

  **الحلّ: تعميمُ `splitAtSep` نفسِه من جزءٍ واحدٍ إلى كلّ الأجزاء.** `splitAllSep` تفصل القائمةَ عند **كلّ**
  وقوعٍ للرمز المحجوز لا عند أوّله فقط (بتكرار `splitAtSep` على الذَّيل حتّى تنتهي القائمة، بلازمة إنهاءٍ
  جديدةٍ `splitAtSep_snd_lt`: طولُ الذَّيل يقلّ دائمًا)، و`joinTrailing` تجمعها بفاصلٍ **لاحقٍ** لكلّ جزءٍ
  (لا بينها) — فعددُ الفواصل يساوي عددَ الأجزاء، لا ناقص واحد، وهذا بعينه ما يجعل `splitAllSep_joinTrailing`
  عكسَها التامّ بشرطٍ واحدٍ («الفاصلُ ليس بين عناصر أيّ جزءٍ») لا بشرطٍ على عدد الأجزاء. هذه أداةٌ عامّةٌ
  جديدةٌ أعمّ من `splitAtSep` نفسِها، لا حالةً خاصّةً منها.

  **طبقتان من `stringsEnc`/`stringsListEnc` فوقها، بفاصلٍ لاحقٍ مختلفٍ لكلّ طبقة.** `stringsEnc : List
  String → Nat` تدمج رموزَ حروف كلّ نصٍّ (`stringCodes`، من TashfirNas) بفاصلٍ لاحقٍ هو `charBound` نفسُه
  (أكبرُ من أيّ رمز حرفٍ حتمًا بـ`charEnc_lt`، لا بحدٍّ مختار — نفسُ حيلة TashfirHawass)، ثمّ `listEnc` على
  القاعدة `charBound+1`. فوقها `stringsListEnc : List (List String) → Nat` تدمج كلَّ قائمةٍ داخليّةٍ خامّةً
  (`innerFlat`، بلا طبقة `listEnc` خاصّةٍ بها) بفاصلٍ لاحقٍ **آخر** هو `charBound+1` (أكبرُ من `charBound`
  نفسِه فأكبرُ من كلّ رمز حرفٍ ومن الفاصل الداخليّ معًا — مبرهنٌ بـ`stringsListEnc_lt`/`_notMem`، لا مفترَضٌ)،
  ثمّ `listEnc` على القاعدة `charBound+2`. فكلُّ طبقةٍ تحجز رمزًا واحدًا فوق سقف الطبقة التي تحتها مباشرةً —
  تعميمٌ حسابيٌّ لحيلة الفصل الواحدة نفسِها، لا قناةٌ موازية لكلّ طبقة.

  **النتيجة: Qawl وShabaka كلاهما غيرُ مشروطين بتاتًا — لا استثناء.** تاجُ Qawl محدودٌ (`tagOf`، دون 11)
  في موضع `mixEnc` المقيَّد، ونصوصُ منشِئه (`toStrings`، اثنانِ أو ثلاثةٌ) بـ`stringsEnc` غيرِ المشروطة —
  فلا حدَّ على طول أيّ نصّ. Shabaka تسطّح كلَّ حقلٍ من حقولها الستّة أزواجًا (`pairsToStrings`) إلى
  `List String` ثمّ `stringsListEnc` على القائمة السداسيّة — فلا حدَّ على طول أيّ نصٍّ ولا على عدد أصول أيّ
  حقل. خلافًا لـTashfirHawass (استثناءٌ خفيفٌ وحيدٌ: `ShahidWaqi.mawdi`، حقلُ Nat خامٌ لا بنيةُ حروف) هذه
  القطعةُ **أشملُ**: لا Sahih، لا Subtype، لا `Classical.propDecidable` في أيّ بنيةٍ طُويت هنا.

  **المؤجَّل عمدًا: `Ikhbar A`.** معمَّمةٌ على نوعٍ حرٍّ `A` بـ`Tayy A Nat` عشوائيّ؛ حيلةُ حجز الفاصل تعتمد
  ضمانًا **نوعيًّا** (`charEnc_lt`: كلُّ رمز حرفٍ دون `charBound` بتعريف Char نفسِه) لا يُعمَّم على ترميزٍ
  عشوائيٍّ لـ`A` — لا سقفَ موحَّدًا على مَدى ترميزٍ لا يُعرَف شكلُه. لا شاهدَ ملموسًا لـ`Ikhbar A` في
  Madlul/Shabaka.lean نفسِه يُلزم حلَّ هذا (مذكورةٌ بالاسم في تعليقَي `Fil`/`fil_shahid` أدناه)، فتأجيلٌ
  معلَنٌ مسبَّبٌ لا ثغرةٌ صامتة.

  البنى المطويّة: Luzum (تعدادانِ بلا حمولة: lazim/mutaaddi) وUslub (ستّةٌ: mujarrad/majhul/mutawaa/
  tadiya/musharaka/talab) ترميزًا مباشرًا كـZaman5؛ Fil (ism:String + luzum:Luzum، `mixEnc` واحدٌ يكفي
  كـTashfirAzmina، لا فصلَ هنا — حقلٌ نصّيٌّ واحدٌ وحيد)؛ Qawl وShabaka بالفصل كما أعلاه.

  **ملاحظةٌ منهجيّةٌ على بناء هذه القطعة بعينها (لا تخمينًا، بل مرصودةٌ من مخرج `lake build` الفعليّ
  أثناء الكتابة):** أربعةُ أخطاءٍ صغيرةٍ أُصلحت تباعًا — (أ) `eq_or_ne` غيرُ معرَّفٍ في هذه البيئة؛ استُبدل
  بـ`cases xs with | nil => … | cons y ys => …`؛ (ب) `omega` رأى `(y::ys).length` (في فرضيّةٍ لم تُبسَّط)
  و`ys.length+1` (في الهدف المبسَّط) ذرّتين منفصلتين فأخفق؛ أُصلح بـ`simp only […] at hrec ⊢` على الفرضيّة
  والهدف معًا قبل `omega`؛ (ج) `cases q <;> decide` على `tagOf_lt` رفض بـ«Expected type must not contain
  free variables» لأنّ متغيّرات حقول Qawl النصّيّة تبقى حرّةً بعد التفكيك رغم أنّ `tagOf` لا يعتمد قيمتها؛
  أُصلح بفكّ التعريف أوّلًا (`simp only [tagOf]`، تقبل متغيّراتٍ حرّةً بخلاف `decide`) ثمّ `omega` على الهدف
  المغلَق؛ (د) محاولةُ `Edit` أولى على `stringsList_dec_enc` فشلت لعدم تطابق النصّ حرفيًّا؛ أُعيدت القراءةُ
  بالأداة ثمّ أُعيد التعديل من النصّ المقروء بعينه. البناءُ النهائيّ خلا من هذه الأخطاء الأربعة، ولم يحتَجْ
  إلى عزلٍ بالقسمة الثنائية كما احتاجت TashfirMakan (لا OOM ولا تعليقٌ هنا).

  **التحقّق المحلّيّ (هذه الجلسةُ، بالأداة):** `lake build Madlul.TashfirShabaka` وحدَها — 20 عملًا نجاحٌ،
  تحذيرُ `if_neg` المعروف وحده (لا معيارًا جديدًا، كـTashfirHawass)؛ `lake build` كاملًا — 112 عملًا نجاحٌ؛
  `lean Audit.lean` مباشرةً — exit 0، صفرُ أسطر error، 974 سطرَ `#print axioms` بالضبط (944+30، رقمًا
  لرقم). توزيعُ مسلّمات الثلاثين: ستٌّ بلا مسلّماتٍ أصلًا (luzum_dec_enc/luzumEnc_lt/tayyLuzum_la_yudi/
  uslub_dec_enc/uslubEnc_lt/tayyUslub_la_yudi — تعدادانِ بلا حمولة، كـZaman5 بعينها)؛ أربعٌ
  [propext،Quot.sound] (splitAtSep_snd_lt/splitAllSep_unfold/splitAllSep_joinTrailing/tagOf_lt)؛ ثلاثٌ
  [propext] فقط (joinTrailing_mem/toStrings_ofStrings/stringsToPairs_pairsToStrings)؛ والباقيةُ سبعَ عشرةَ
  [propext،Classical.choice،Quot.sound] كاملةً (موروثةً عبر stringEnc/charCodes_dec_enc ولوازم نواة String،
  نفسُ النمط المفحوص في TashfirNas/TashfirHawass لا تكرارَ خطإٍ). فحصُ أنماطٍ محظورةٍ (`sorry`/
  `native_decide`/`axiom`) على هذا الملفّ بعينه: صفرُ نتائج. ثلاثُ طفراتٍ (`P152`–`P154` في
  `tafrat.json`): P152 حذفُ الفاصل اللاحق من `joinTrailing` (`c ++ (joinTrailing sep cs)` بدل
  `c ++ (sep :: joinTrailing sep cs)`) كشفه فشلُ `splitAtSep_join`/`splitAllSep_joinTrailing` بعدم تطابق
  الشكل المُعاد بناؤه؛ P153 تضييقُ قاعدة تاج Qawl من 11 إلى 10 في `qawlEnc` وحدها (فتنافرُ معَ `tagOf_lt`
  وشرطِ `SLGE.mixDec_enc` في `qawl_dec_enc`) كشفه فشلُ `rw` بعدم العثور على الشكل؛ P154 تبديلُ ترتيب الزوج
  في حالة `stringsToPairs` (`(b,a)` بدل `(a,b)`) كشفه فشلُ `stringsToPairs_pairsToStrings` بهدفٍ غيرِ
  محلول — جُرِّبت الثلاثُ يدويًّا بـ`lake build` المباشر وأفشلت البناء كلَّ مرّةٍ بخطإٍ حقيقيّ مختلفٍ، ثمّ
  أُعيد الملفُّ لأصله بعد كلٍّ منها (diff صفريّ مؤكَّد). خطّ الأساس 944←974.

  لا جدولَ خارجيًّا لهذه القطعة فلا مرآة بايثون — كـTashfirMadda/TashfirKhawass/TashfirMirsat/TashfirAzmina/
  TashfirMakan/TashfirAwwaliyyat/TashfirNas/TashfirHawass جميعًا.

  مؤجَّلٌ: Isnad (التكراريّةُ الحقيقيّةُ في Jumla — شجرةٌ لا قائمةٌ مسطَّحة، آخرُ الاسم الثمانيّ)، جسورُ
  العوامل/Itar3 (مصرَّحٌ بتنفيذهما)، وجدولُ اللزوم من مقاييس/لسان (الملفّان حاضران في `/home/claude/mudaa_dir`
  بهذا الطرف، لم يُستخرج منهما شيء)، وIkhbar A كما أعلاه.
-/
import Aql.Mawsua
import Madlul.TashfirNas
import Madlul.TashfirKhawass
import Madlul.TashfirHawass
import Madlul.Shabaka

set_option autoImplicit false

namespace Madlul.TashfirShabaka

open Mawsua Madlul.TashfirNas Madlul.TashfirKhawass Madlul.TashfirHawass Madlul.Shabaka

/-! ## ٠. أداةٌ جديدةٌ: الفصلُ إلى كلّ الأجزاء (تعميمُ splitAtSep من جزءٍ واحدٍ إلى عددٍ غيرِ محدود) -/

/-- **طولُ الذَّيل يقلّ دائمًا** حين القائمةُ غيرُ خاليةٍ: لازمةُ إنهاء `splitAllSep`. -/
theorem splitAtSep_snd_lt (sep : Nat) : ∀ l : List Nat, l ≠ [] → (splitAtSep sep l).2.length < l.length := by
  intro l
  induction l with
  | nil => intro h; exact absurd rfl h
  | cons x xs ih =>
    intro _
    simp only [splitAtSep]
    by_cases hx : x = sep
    · simp [hx]
    · rw [if_neg hx]
      show (splitAtSep sep xs).2.length < (x :: xs).length
      cases xs with
      | nil => simp [splitAtSep]
      | cons y ys =>
        have hrec := ih (List.cons_ne_nil y ys)
        simp only [List.length_cons] at hrec ⊢
        omega

/-- فصلُ قائمةٍ إلى **كلّ** أجزائها المفصولة بـ`sep` (لا الجزء الأوّل وحده كـ`splitAtSep`): تكرارُ الفصل حتّى
تنتهي القائمة. -/
def splitAllSep (sep : Nat) (l : List Nat) : List (List Nat) :=
  match l with
  | [] => []
  | x :: xs =>
    let p := splitAtSep sep (x :: xs)
    p.1 :: splitAllSep sep p.2
termination_by l.length
decreasing_by exact splitAtSep_snd_lt sep (x :: xs) (by simp)

/-- جمعُ الأجزاء بفاصلٍ **لاحقٍ** لكلّ جزء (لا بينها): جزءٌ ثمّ `sep` ثمّ جزءٌ ثمّ `sep`، ... — تكرارٌ ثابتٌ يجعل
عددَ الفواصل يساوي عدد الأجزاء، لا عددَها ناقص واحد. -/
def joinTrailing (sep : Nat) : List (List Nat) → List Nat
  | [] => []
  | c :: cs => c ++ (sep :: joinTrailing sep cs)

/-- فكُّ `splitAllSep` بخطوةٍ واحدة لقائمةٍ غيرِ خالية: بتعريفه مباشرةً. -/
theorem splitAllSep_unfold (sep : Nat) (l : List Nat) (hl : l ≠ []) :
    splitAllSep sep l = (splitAtSep sep l).1 :: splitAllSep sep (splitAtSep sep l).2 := by
  cases l with
  | nil => exact absurd rfl hl
  | cons x xs => simp only [splitAllSep]

/-- **الفصلُ إلى كلّ الأجزاء يعيد الأجزاءَ بعينها** حين جُمعت بفاصلٍ لاحقٍ وليس هو فيها (شرطٌ على كلّ جزءٍ، لا
على القائمة كلِّها دفعةً): عكسُ `joinTrailing`. -/
theorem splitAllSep_joinTrailing (sep : Nat) (chunks : List (List Nat)) (h : ∀ c ∈ chunks, sep ∉ c) :
    splitAllSep sep (joinTrailing sep chunks) = chunks := by
  induction chunks with
  | nil => simp [joinTrailing, splitAllSep]
  | cons c cs ih =>
    simp only [List.mem_cons, forall_eq_or_imp] at h
    have hjoin : splitAtSep sep (joinTrailing sep (c :: cs)) = (c, joinTrailing sep cs) := by
      simp only [joinTrailing]
      exact splitAtSep_join sep c (joinTrailing sep cs) h.1
    have hne : joinTrailing sep (c :: cs) ≠ [] := by
      simp only [joinTrailing]
      cases c <;> simp
    rw [splitAllSep_unfold sep _ hne, hjoin]
    simp only [List.cons.injEq, true_and]
    exact ih h.2

/-- **عضويّةُ `joinTrailing`**: ما في المجموع هو الفاصلُ نفسُه أو عضوٌ من جزءٍ من الأجزاء — لازمةٌ لنقل حدودٍ
على عناصر الأجزاء إلى حدٍّ على المجموع كلِّه. -/
theorem joinTrailing_mem (sep : Nat) (chunks : List (List Nat)) (x : Nat) (hx : x ∈ joinTrailing sep chunks) :
    x = sep ∨ ∃ c ∈ chunks, x ∈ c := by
  induction chunks with
  | nil => simp [joinTrailing] at hx
  | cons c cs ih =>
    simp only [joinTrailing, List.mem_append, List.mem_cons] at hx
    rcases hx with hx | hx | hx
    · exact Or.inr ⟨c, by simp, hx⟩
    · exact Or.inl hx
    · rcases ih hx with h | ⟨c', hc', hxc'⟩
      · exact Or.inl h
      · exact Or.inr ⟨c', by simp [hc'], hxc'⟩

/-! ## ١. طيُّ `List String` المعمَّم: فصلٌ بـ`charBound` كفاصلٍ لاحق، ثمّ `listEnc` -/

/-- رموزُ حروف نصٍّ (دون `charBound` كلُّها، بمبرهنة `charEnc_lt`). -/
def stringCodes (s : String) : List Nat := s.toList.map charEnc

/-- **طيُّ قائمة نصوصٍ**: رموزُ كلّ نصٍّ، مفصولةٌ بفاصلٍ لاحقٍ هو `charBound` نفسُه (لا بحدٍّ مختار — كـTashfirHawass)،
ثمّ `listEnc` على القاعدة `charBound+1`. -/
def stringsEnc (strs : List String) : Nat :=
  listEnc (charBound + 1) (joinTrailing charBound (strs.map stringCodes))

/-- **فكُّ قائمة النصوص**: `listDec` ثمّ فصلٌ إلى كلّ الأجزاء بـ`charBound` ثمّ فكُّ رموز كلّ جزء نصًّا. -/
def stringsDec (n : Nat) : List String :=
  (splitAllSep charBound (listDec (charBound + 1) n)).map (fun codes => String.ofList (codes.map charDec))

theorem stringsEnc_lt (strs : List String) : ∀ x ∈ joinTrailing charBound (strs.map stringCodes), x < charBound + 1 := by
  intro x hx
  rcases joinTrailing_mem charBound (strs.map stringCodes) x hx with h | ⟨c, hc, hxc⟩
  · omega
  · obtain ⟨s, -, rfl⟩ := List.mem_map.1 hc
    exact charCodes_lt s x hxc

theorem stringsEnc_notMem (strs : List String) : ∀ c ∈ strs.map stringCodes, charBound ∉ c := by
  intro c hc
  obtain ⟨s, -, rfl⟩ := List.mem_map.1 hc
  exact charBound_notin_charCodes s

/-- نواةُ الفكّ (بلا طبقة `listEnc`/`listDec`): تُستعمَل هنا مباشرةً، وتُستعمَل ثانيةً في طبقة `stringsListEnc`
أدناه حيث لا تلتفّ القائمةُ الداخليّةُ بـ`listEnc` خاصّةٍ بها. -/
theorem stringsRaw_dec_enc (strs : List String) :
    (splitAllSep charBound (joinTrailing charBound (strs.map stringCodes))).map
      (fun codes => String.ofList (codes.map charDec)) = strs := by
  rw [splitAllSep_joinTrailing charBound _ (stringsEnc_notMem strs)]
  induction strs with
  | nil => rfl
  | cons s ss ih => simp only [List.map_cons, stringCodes, charCodes_dec_enc, ih]

/-- **الفكُّ يعيد الأصل لكلّ قائمة نصوص — بلا شرط** (كـBud/Tasmiya في TashfirHawass، لا كـMadda/Mirsat): لا حدّ
على عدد النصوص ولا على طول أيٍّ منها. -/
theorem strings_dec_enc (strs : List String) : stringsDec (stringsEnc strs) = strs := by
  simp only [stringsDec, stringsEnc]
  rw [list_dec_enc (charBound + 1) _ (stringsEnc_lt strs)]
  exact stringsRaw_dec_enc strs

/-! ## ٢. طيُّ `List (List String)` المعمَّم: طبقةٌ فوق السابقة بفاصلٍ لاحقٍ آخر (`charBound+1`) -/

/-- القائمةُ الداخليّةُ خامّةً (بلا `listEnc` خاصّ بها): رموزُ نصوصها مفصولةٌ بـ`charBound`. -/
def innerFlat (strs : List String) : List Nat := joinTrailing charBound (strs.map stringCodes)

/-- **طيُّ قائمة قوائم النصوص**: كلّ قائمةٍ داخليّةٍ خامّةً (`innerFlat`)، مفصولةٌ بفاصلٍ لاحقٍ آخرَ هو
`charBound+1` (أكبرُ من `charBound` نفسِه فأكبرُ من كلّ رمز حرفٍ ومن الفاصل الداخليّ معًا)، ثمّ `listEnc` على
القاعدة `charBound+2`. -/
def stringsListEnc (ls : List (List String)) : Nat :=
  listEnc (charBound + 2) (joinTrailing (charBound + 1) (ls.map innerFlat))

def stringsListDec (n : Nat) : List (List String) :=
  (splitAllSep (charBound + 1) (listDec (charBound + 2) n)).map
    (fun flat => (splitAllSep charBound flat).map (fun codes => String.ofList (codes.map charDec)))

theorem stringsListEnc_lt (ls : List (List String)) :
    ∀ x ∈ joinTrailing (charBound + 1) (ls.map innerFlat), x < charBound + 2 := by
  intro x hx
  rcases joinTrailing_mem (charBound + 1) _ x hx with h | ⟨c, hc, hxc⟩
  · omega
  · obtain ⟨strs, -, rfl⟩ := List.mem_map.1 hc
    rcases joinTrailing_mem charBound (strs.map stringCodes) x hxc with h2 | ⟨c2, hc2, hxc2⟩
    · omega
    · obtain ⟨s, -, rfl⟩ := List.mem_map.1 hc2
      have := charCodes_lt s x hxc2
      omega

theorem stringsListEnc_notMem (ls : List (List String)) :
    ∀ c ∈ ls.map innerFlat, (charBound + 1) ∉ c := by
  intro c hc hcon
  obtain ⟨strs, -, rfl⟩ := List.mem_map.1 hc
  rcases joinTrailing_mem charBound (strs.map stringCodes) (charBound + 1) hcon with h | ⟨c2, hc2, hxc2⟩
  · omega
  · obtain ⟨s, -, rfl⟩ := List.mem_map.1 hc2
    have := charCodes_lt s (charBound + 1) hxc2
    omega

/-- **الفكُّ يعيد الأصل لكلّ قائمة قوائم نصوصٍ — بلا شرط**: طبقةٌ فوق `stringsRaw_dec_enc`، بفاصلٍ لاحقٍ آخر. -/
theorem stringsList_dec_enc (ls : List (List String)) : stringsListDec (stringsListEnc ls) = ls := by
  simp only [stringsListDec, stringsListEnc]
  rw [list_dec_enc (charBound + 2) _ (stringsListEnc_lt ls)]
  rw [splitAllSep_joinTrailing (charBound + 1) _ (stringsListEnc_notMem ls)]
  induction ls with
  | nil => rfl
  | cons strs ss ih =>
    simp only [List.map_cons, innerFlat]
    rw [stringsRaw_dec_enc strs, ih]

/-! ## ٣. طيُّ Luzum وUslub (تعدادانِ بلا حمولة، ترميزٌ مباشر) وFil (نصٌّ + تعدادٌ محدود، `mixEnc` واحد) -/

def luzumEnc : Luzum → Nat
  | .lazim => 0 | .mutaaddi => 1
def luzumDec : Nat → Luzum
  | 0 => .lazim | _ => .mutaaddi
theorem luzum_dec_enc (l : Luzum) : luzumDec (luzumEnc l) = l := by cases l <;> rfl
theorem luzumEnc_lt (l : Luzum) : luzumEnc l < 2 := by cases l <;> decide

def tayyLuzum : Tayy Luzum Nat where
  tawi := luzumEnc
  fakk := fun n => some (luzumDec n)
  fakk_tawi := fun l => by rw [luzum_dec_enc]
theorem tayyLuzum_la_yudi (l : Luzum) : tayyLuzum.fakk (tayyLuzum.tawi l) = some l := tayyLuzum.fakk_tawi l

def uslubEnc : Uslub → Nat
  | .mujarrad => 0 | .majhul => 1 | .mutawaa => 2 | .tadiya => 3 | .musharaka => 4 | .talab => 5
def uslubDec : Nat → Uslub
  | 0 => .mujarrad | 1 => .majhul | 2 => .mutawaa | 3 => .tadiya | 4 => .musharaka | _ => .talab
theorem uslub_dec_enc (u : Uslub) : uslubDec (uslubEnc u) = u := by cases u <;> rfl
theorem uslubEnc_lt (u : Uslub) : uslubEnc u < 6 := by cases u <;> decide

def tayyUslub : Tayy Uslub Nat where
  tawi := uslubEnc
  fakk := fun n => some (uslubDec n)
  fakk_tawi := fun u => by rw [uslub_dec_enc]
theorem tayyUslub_la_yudi (u : Uslub) : tayyUslub.fakk (tayyUslub.tawi u) = some u := tayyUslub.fakk_tawi u

/-- **طيُّ Fil**: حقلٌ طليقٌ واحدٌ (`ism`، بأداة TashfirNas `stringEnc` غيرِ المشروطة) وحقلٌ محدودٌ واحد
(`luzum`، تعدادٌ من اثنتين) — `mixEnc` واحدٌ يكفي، كـTashfirAzmina، لا حاجةَ إلى الفصل هنا. -/
def filEnc (f : Fil) : Nat := SLGE.mixEnc 2 1 (stringEnc f.ism) (luzumEnc f.luzum) 0
def filDec (n : Nat) : Fil :=
  match SLGE.mixDec 2 1 n with
  | (ismC, luzumC, _) => { ism := stringDec ismC, luzum := luzumDec luzumC }

/-- **الفكُّ يعيد الأصل لكلّ Fil — بلا شرط** (`luzum` محدودٌ بتعريف نوعه، و`ism` حقلٌ طليقٌ واحدٌ وحيد). -/
theorem fil_dec_enc (f : Fil) : filDec (filEnc f) = f := by
  have h := luzumEnc_lt f.luzum
  simp only [filDec, filEnc]
  rw [SLGE.mixDec_enc 2 1 _ _ 0 h Nat.zero_lt_one]
  simp only [string_dec_enc, luzum_dec_enc]

def tayyFil : Tayy Fil Nat where
  tawi := filEnc
  fakk := fun n => some (filDec n)
  fakk_tawi := fun f => by rw [fil_dec_enc]
theorem tayyFil_la_yudi (f : Fil) : tayyFil.fakk (tayyFil.tawi f) = some f := tayyFil.fakk_tawi f

/-! ## ٤. طيُّ Qawl (أحدَ عشرَ منشِئًا، كلٌّ حقلاه أو حقولُه الثلاثة نصوصٌ): تاجٌ محدودٌ + `stringsEnc` -/

/-- تاجُ المنشِئ (0–10، بترتيب تعريف Qawl في Madlul/Shabaka.lean). -/
def tagOf : Qawl → Nat
  | .qabiliyya .. => 0 | .mafooliyya .. => 1 | .sababiyya .. => 2 | .hala .. => 3
  | .tasmiya .. => 4 | .qanunMujam .. => 5 | .nisba .. => 6 | .sifa .. => 7
  | .yufal .. => 8 | .natija .. => 9 | .jinsSifa .. => 10

theorem tagOf_lt (q : Qawl) : tagOf q < 11 := by cases q <;> simp only [tagOf] <;> omega

/-- نصوصُ المنشِئ: حقلاه النصّيّان (العشرةُ ذاتُ الحقلين)، أو حقولُه الثلاثة (`nisba` وحدها). -/
def toStrings : Qawl → List String
  | .qabiliyya a b => [a, b] | .mafooliyya a b => [a, b] | .sababiyya a b => [a, b]
  | .hala a b => [a, b] | .tasmiya a b => [a, b] | .qanunMujam a b => [a, b]
  | .nisba a b c => [a, b, c]
  | .sifa a b => [a, b] | .yufal a b => [a, b] | .natija a b => [a, b] | .jinsSifa a b => [a, b]

/-- عكسُ `toStrings`/`tagOf`: من التاج وقائمة النصوص إلى المنشِئ. كُلّيّةٌ بالاحتياط الأخير (لا يُصادَف حقيقةً:
الطيُّ يحفظ التاجَ وعددَ النصوص معًا، فـ`toStrings_ofStrings` تكفي كلَّ شاهد). -/
def ofStrings : Nat → List String → Qawl
  | 0, [a, b] => .qabiliyya a b
  | 1, [a, b] => .mafooliyya a b
  | 2, [a, b] => .sababiyya a b
  | 3, [a, b] => .hala a b
  | 4, [a, b] => .tasmiya a b
  | 5, [a, b] => .qanunMujam a b
  | 6, [a, b, c] => .nisba a b c
  | 7, [a, b] => .sifa a b
  | 8, [a, b] => .yufal a b
  | 9, [a, b] => .natija a b
  | 10, [a, b] => .jinsSifa a b
  | _, _ => .qabiliyya "" ""

theorem toStrings_ofStrings (q : Qawl) : ofStrings (tagOf q) (toStrings q) = q := by
  cases q <;> rfl

/-- **طيُّ Qawl**: تاجٌ محدودٌ (دون 11) + نصوصُ المنشِئ (عددُها 2 أو 3، بأداة `stringsEnc` غيرِ المشروطة). -/
def qawlEnc (q : Qawl) : Nat := SLGE.mixEnc 11 1 (stringsEnc (toStrings q)) (tagOf q) 0
def qawlDec (n : Nat) : Qawl :=
  match SLGE.mixDec 11 1 n with
  | (strCode, tag, _) => ofStrings tag (stringsDec strCode)

/-- **الفكُّ يعيد الأصل لكلّ Qawl — بلا شرط**: لا حدَّ على طول أيٍّ من نصوصه. -/
theorem qawl_dec_enc (q : Qawl) : qawlDec (qawlEnc q) = q := by
  have h := tagOf_lt q
  simp only [qawlDec, qawlEnc]
  rw [SLGE.mixDec_enc 11 1 _ _ 0 h Nat.zero_lt_one]
  simp only [strings_dec_enc]
  exact toStrings_ofStrings q

def tayyQawl : Tayy Qawl Nat where
  tawi := qawlEnc
  fakk := fun n => some (qawlDec n)
  fakk_tawi := fun q => by rw [qawl_dec_enc]
theorem tayyQawl_la_yudi (q : Qawl) : tayyQawl.fakk (tayyQawl.tawi q) = some q := tayyQawl.fakk_tawi q

/-! ## ٥. طيُّ Shabaka (ستّةُ حقولٍ List(String×String)): تسطيحٌ زوجًا زوجًا، ثمّ `stringsListEnc` -/

/-- تسطيحُ قائمة أزواج النصوص: كلُّ زوجٍ نصّين متتابعين. -/
def pairsToStrings : List (String × String) → List String
  | [] => []
  | (a, b) :: rest => a :: b :: pairsToStrings rest

/-- عكسُ `pairsToStrings`: تجميعُ النصوص زوجًا زوجًا. الحالةُ المفردةُ (طرفٌ فاضل) لا تصدف حقيقةً — قائمةُ
`pairsToStrings` دائمًا زوجيّةُ الطول. -/
def stringsToPairs : List String → List (String × String)
  | [] => []
  | [_] => []
  | a :: b :: rest => (a, b) :: stringsToPairs rest

theorem stringsToPairs_pairsToStrings (l : List (String × String)) :
    stringsToPairs (pairsToStrings l) = l := by
  induction l with
  | nil => rfl
  | cons p ps ih =>
    obtain ⟨a, b⟩ := p
    simp only [pairsToStrings, stringsToPairs, ih]

/-- **طيُّ Shabaka**: الستّةُ حقولٌ مسطَّحةٌ أزواجًا إلى `List String`، ثمّ `stringsListEnc` على القائمة
السداسيّة — بلا شرط (لا حدَّ على طول أيّ حقلٍ ولا على عدد أصوله). -/
def shabakaEnc (sh : Shabaka) : Nat :=
  stringsListEnc [pairsToStrings sh.qabiliyyat, pairsToStrings sh.mafooliyyat, pairsToStrings sh.sababiyyat,
    pairsToStrings sh.halat, pairsToStrings sh.tasmiyat, pairsToStrings sh.qawaninMujam]

/-- الفكّ: فكُّ القائمة السداسيّة ثمّ تجميعُ كلّ حقلٍ أزواجًا. الاحتياطُ الأخير لا يصدف حقيقةً (الطيُّ يحفظ
العددَ سِتّةً دائمًا). -/
def shabakaDec (n : Nat) : Shabaka :=
  match stringsListDec n with
  | [f0, f1, f2, f3, f4, f5] =>
    { qabiliyyat := stringsToPairs f0, mafooliyyat := stringsToPairs f1, sababiyyat := stringsToPairs f2,
      halat := stringsToPairs f3, tasmiyat := stringsToPairs f4, qawaninMujam := stringsToPairs f5 }
  | _ => { qabiliyyat := [], mafooliyyat := [], sababiyyat := [], halat := [], tasmiyat := [], qawaninMujam := [] }

/-- **الفكُّ يعيد الأصل لكلّ Shabaka — بلا شرط**: الأشمل بين قطع هذا الملفّ — لا حدَّ على عدد أصول أيّ قائمةٍ
من الستّ ولا على طول أيّ نصٍّ فيها. -/
theorem shabaka_dec_enc (sh : Shabaka) : shabakaDec (shabakaEnc sh) = sh := by
  simp only [shabakaDec, shabakaEnc]
  rw [stringsList_dec_enc]
  simp only [stringsToPairs_pairsToStrings]

def tayyShabaka : Tayy Shabaka Nat where
  tawi := shabakaEnc
  fakk := fun n => some (shabakaDec n)
  fakk_tawi := fun sh => by rw [shabaka_dec_enc]
theorem tayyShabaka_la_yudi (sh : Shabaka) : tayyShabaka.fakk (tayyShabaka.tawi sh) = some sh :=
  tayyShabaka.fakk_tawi sh

/-! ## ٦. على الشاهد: شبكةُ المثال وأقوالُها -/

theorem shabaka_tudi : shabakaDec (shabakaEnc shabaka) = shabaka := shabaka_dec_enc shabaka
theorem shabakaP_tudi : shabakaDec (shabakaEnc shabaka') = shabaka' := shabaka_dec_enc shabaka'

/-- ستّةُ أقوالٍ من شواهد Madlul/Shabaka.lean نفسِه (`shawahid_maqbula`، `sail_sharab_marfud`/`bil_mujam`):
نسبةٌ، نتيجةٌ، حالةٌ، صفةٌ، موصوفٌ يُفعل، وذو حالةٍ موصوف — سِتّةٌ من أحدَ عشرَ منشِئًا. -/
theorem qawl_shawahid :
    qawlDec (qawlEnc (.nisba "الحيوان" "شرب" "الماء")) = .nisba "الحيوان" "شرب" "الماء" ∧
    qawlDec (qawlEnc (.natija "الحيوان" "الريّ")) = .natija "الحيوان" "الريّ" ∧
    qawlDec (qawlEnc (.hala "الماء" "سائل")) = .hala "الماء" "سائل" ∧
    qawlDec (qawlEnc (.sifa "الماء" "شراب")) = .sifa "الماء" "شراب" ∧
    qawlDec (qawlEnc (.yufal "شراب" "شرب")) = .yufal "شراب" "شرب" ∧
    qawlDec (qawlEnc (.jinsSifa "سائل" "شراب")) = .jinsSifa "سائل" "شراب" :=
  ⟨qawl_dec_enc _, qawl_dec_enc _, qawl_dec_enc _, qawl_dec_enc _, qawl_dec_enc _, qawl_dec_enc _⟩

/-- Fil وUslub/Luzum بنيةٌ تحتيّةٌ (`Ikhbar` معمَّمٌ على `A`، بلا شاهدٍ مبنيٍّ في Madlul/Shabaka.lean نفسِه —
انظر رأس الملفّ): شاهدٌ بُني هنا توضيحًا للطيّ لا نقلًا منه — فعلٌ متعدٍّ «شرب». -/
theorem fil_shahid : filDec (filEnc { ism := "شرب", luzum := .mutaaddi }) = { ism := "شرب", luzum := .mutaaddi } :=
  fil_dec_enc _

end Madlul.TashfirShabaka
