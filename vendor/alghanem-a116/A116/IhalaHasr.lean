import A116.Hudud
import A116.Certificate

/-!
# الإحالةُ بالحصر على خانات الحدود، وعددُ الشهادة بحدّها (ADR ٨٦، تكملةُ ADR ٨٣؛ أمرُ المالك «الضمائرُ يجب برهان
الإحالة رياضيًّا» و«HADD_N … يجب عمل Lean»)

## ١. صفاتُ الضمير من المختوم

الضميرُ «ما دلّ على غيبةٍ أو حضور» (شرحُ ابن عقيل س724–726): المتكلّمُ والمخاطبُ **حضور**، والغائبُ وحدَه يحيل على
مذكورٍ في النصّ. صفاتُ المنفصل المرفوع من س792–797 (أنا للمتكلّم وحده، نحن للمشارك، أنت للمخاطب، أنتما للمخاطبَين،
أنتم، هو للغائب، هي للغائبة، هما، هم، هن)، وصفاتُ العائد المتّصل من س1136–1138 (ضربتُه، ضربتُهما، ضربتُهم،
ضربتُها، ضربتُهنّ)، وصفاتُ الموصول من س1023 وس1135–1142: الذي مفردٌ مذكّر، التي مفردةٌ مؤنّثة، الذين جمعٌ مذكّر،
اللاتي/اللائي جمعٌ مؤنّث؛ و«من» و«ما» **لفظُهما مفردٌ مذكّر ومعناهما حرّ** فيجوز مراعاةُ اللفظ ومراعاةُ المعنى.
خاناتُ الصور ما تطبعه البوّابة (`tests/test_ihala_hasr.py`).

## ٢. قانونُ الإحالة

* **اللياقة** (س1135: «ضمير لائق بالموصول إن كان مفردًا فمفرد وإن كان مذكّرًا فمذكّر»): اتّفاقُ العدد والجنس
  (`laiq`)؛ والعائدُ يلزم الصلة (س1133–1135) فلا صلةَ بلا عائدٍ لائق (`silaB`).
* **المرشّحون**: لضميرِ غيبةٍ في موضع i من النصّ، مرشّحو مرجعه كلُّ اسمٍ **قبله** يليق به (`murashshahun`)؛
  الإحالةُ **حصرٌ**: كلُّ مرشّحٍ يسبق الضميرَ (`murashshah_precedes`) ويليق به (`murashshah_laiq`)،
  والحضورُ لا مرجعَ له في النصّ (`hudur_no_marji`)، والإحالةُ تتعيّن إذا كان المرشّحُ واحدًا (`mutaayyin_iff`)،
  ولا تُخمَّن حين تتعدّد أو تنعدم (`MARJI_NOT_GUESSED`): المخرجُ ثلاثيٌّ — متعيّن / متعدّد / لا مرجع.
* **الموصولُ والعائد**: الموصولُ المتبوعُ بصلةٍ فيها عائدٌ لائقٌ وليس بينهما اسمٌ لائق — الموصولُ مرجعُه المتعيّن
  (`aid_refers_to_mawsul`)؛ وعلى «من» و«ما» وجهان: اللفظُ أو المعنى (`man_two_wajh`).

**نسبتُه إلى ADR ٨٣ (`A116.Ihala`)**: هناك **قيدُ** الإحالة (`Ihala.jaiz`: لا يعود الضميرُ على متأخّرٍ لفظًا ورتبة،
بالرتبة مدخلًا)؛ وهنا **حصرُ** المرشّحين على الخانات بالتقدّم اللفظيّ وحدَه واللياقة — فما يجيزه ADR ٨٣ بالرتبة
مع التأخّر اللفظيّ ليس في هذا الحصر (`RUTBA_NOT_IN_HASR`).

ما ليس هنا — باسمه: `MARJI_NOT_GUESSED` (لا ترجيحَ بالقرب ولا بغيره عند التعدّد: ليس في المختوم قانونٌ له)؛
`SIFAT_ARE_INPUT` (عددُ الاسم وجنسُه في النصّ معاملان لا يُقرآن من الخانات هنا)؛ `MUSTATIR_NOT_WRITTEN`
(الضميرُ المستتر س766–787 لم يُكتب)؛ `IHALA_NOT_IN_GATE`.

## ٣. عددُ الشهادة بحدّها

`Certificate.certNumber` يقرن رقمَ الذرّات بالرتبة؛ وبالحدّ: ‎N = P(n(الوحدة)، الرتبة)‎ حيث n من `Hudud` يحمل الجنس
— تباينٌ على المجال (`certHadd_injective`)، ويفصل الجنسَ على الذرّات نفسِها (`certHadd_jins`)، ويُردّ منه عددُ
الشهادة القديم (`certHadd_to_certNumber`: لا فقد). الواجهةُ `dal-v1` مجمَّدة فالعددُ هنا في Lean لا في البوّابة
(`HADD_N_NOT_IN_GATE` قائمٌ بشطره الثاني).
-/

namespace A116.IhalaHasr

open A116 A116.Ladder A116.Hudud

/-! ## ١. الصفات -/

inductive Shakhs | mutakallim | mukhatab | ghaib
  deriving DecidableEq, Repr, Inhabited

inductive Adad | mufrad | muthanna | jam
  deriving DecidableEq, Repr, Inhabited

inductive Naw | mudhakkar | muannath
  deriving DecidableEq, Repr, Inhabited

/-- صفةُ الضمير: الشخص، العدد، والنوعُ إن فرّقه اللفظ. -/
structure Sifa where
  shakhs : Shakhs
  adad : Adad
  naw : Option Naw
  deriving DecidableEq, Repr, Inhabited

/-- المنفصلُ المرفوع بصفاته (س792–797)، خاناتُه من `Hudud.damirRaf`. -/
def damirSifa : List (List Cell × Sifa) :=
  [(damirRaf[0]!, ⟨.mutakallim, .mufrad, none⟩),     -- أَنَا للمتكلّم وحده
   (damirRaf[1]!, ⟨.mutakallim, .jam, none⟩),        -- نَحْنُ للمتكلّم المشارك
   (damirRaf[2]!, ⟨.mukhatab, .mufrad, some .mudhakkar⟩), -- أَنتَ للمخاطب
   (damirRaf[3]!, ⟨.mukhatab, .muthanna, none⟩),     -- أَنتُمَا للمخاطبَين أو المخاطبتين
   (damirRaf[4]!, ⟨.mukhatab, .jam, some .mudhakkar⟩),   -- أَنتُمْ للمخاطبين
   (damirRaf[5]!, ⟨.ghaib, .mufrad, some .mudhakkar⟩),   -- هُوَ للغائب
   (damirRaf[6]!, ⟨.ghaib, .mufrad, some .muannath⟩),    -- هِيَ للغائبة
   (damirRaf[7]!, ⟨.ghaib, .muthanna, none⟩),        -- هُمَا للغائبَين أو الغائبتين
   (damirRaf[8]!, ⟨.ghaib, .jam, some .mudhakkar⟩),      -- هُمْ للغائبين
   (damirRaf[9]!, ⟨.ghaib, .jam, some .muannath⟩)]       -- هُنَّ للغائبات

/-- العائدُ المتّصل بصفاته (س1136–1138: ضربتُه، ضربتُهما، ضربتُهم، ضربتُها، ضربتُهنّ)؛ خاناتُ اللاحقة كما تطبعها
البوّابة (لَهُ، لَهُمَا، لَهُمْ، لَهَا، لَهُنَّ). -/
def aidSifa : List (List Cell × Sifa) :=
  [([atom 'ه' .damma], ⟨.ghaib, .mufrad, some .mudhakkar⟩),
   ([atom 'ه' .damma, atom 'م' .fatha, atom 'ا' .sukun], ⟨.ghaib, .muthanna, none⟩),
   ([atom 'ه' .damma, atom 'م' .sukun], ⟨.ghaib, .jam, some .mudhakkar⟩),
   ([atom 'ه' .fatha, atom 'ا' .sukun], ⟨.ghaib, .mufrad, some .muannath⟩),
   ([atom 'ه' .damma, atom 'ن' .sukun, atom 'ن' .fatha], ⟨.ghaib, .jam, some .muannath⟩)]

/-- الموصولُ بصفة لفظه (س1023، 1135–1142)؛ «من» و«ما» لفظُهما مفردٌ مذكّر ومعناهما حرّ (`hurr`). -/
structure MawsulSifa where
  cells : List Cell
  lafz : Adad × Naw
  hurr : Bool
  deriving DecidableEq, Repr, Inhabited

def mawsulSifa : List MawsulSifa :=
  [⟨mawsul[0]!, (.mufrad, .mudhakkar), false⟩,   -- الَّذِي
   ⟨mawsul[1]!, (.mufrad, .muannath), false⟩,    -- الَّتِي
   ⟨mawsul[2]!, (.jam, .mudhakkar), false⟩,      -- الَّذِينَ
   ⟨mawsul[3]!, (.jam, .muannath), false⟩,       -- اللَّاتِي
   ⟨mawsul[4]!, (.jam, .muannath), false⟩,       -- اللَّائِي
   ⟨mawsul[5]!, (.mufrad, .mudhakkar), true⟩,    -- مَنْ
   ⟨mawsul[6]!, (.mufrad, .mudhakkar), true⟩]    -- مَا

theorem sifat_counts : damirSifa.length = 10 ∧ aidSifa.length = 5 ∧ mawsulSifa.length = 7 := by decide

/-- الحضورُ والغيبة (س724–726): المتكلّمُ والمخاطبُ حضور. -/
def hudur (s : Sifa) : Bool := s.shakhs != .ghaib

theorem damir_hudur_ghaib :
    (damirSifa.filter fun p => hudur p.2).length = 5 ∧ (damirSifa.filter fun p => !hudur p.2).length = 5 := by
  decide

/-! ## ٢. اللياقة والصلة -/

/-- اللياقة (س1135): العددُ واحدٌ، والنوعُ واحدٌ حيث يفرّقه اللفظان. -/
def laiq (a : Adad × Naw) (s : Sifa) : Bool :=
  a.1 == s.adad && (s.naw.map (· == a.2)).getD true

/-- الصلةُ على الموصول: جملةٌ (كلماتٌ بخاناتها) تشتمل على عائدٍ لائق — كلمةٌ تنتهي بلاحقةٍ من `aidSifa` تليق
بلفظ الموصول. -/
def aidOf (w : List Cell) : Option Sifa :=
  (aidSifa.find? fun p => w.length > p.1.length && w.drop (w.length - p.1.length) == p.1).map (·.2)

def silaB (m : MawsulSifa) (sila : List (List Cell)) : Bool :=
  sila.any fun w => (aidOf w).map (laiq m.lafz) == some true

/-- شواهدُ الشرح (س1136–1138) على اللاحقة: الذي ← ه، الذين ← هم، التي ← ها، اللاتي ← هنّ؛ والمخالفةُ مرفوضة. -/
theorem shawahid_laiq :
    laiq (.mufrad, .mudhakkar) (aidSifa[0]!).2 = true ∧ laiq (.jam, .mudhakkar) (aidSifa[2]!).2 = true ∧
    laiq (.mufrad, .muannath) (aidSifa[3]!).2 = true ∧ laiq (.jam, .muannath) (aidSifa[4]!).2 = true ∧
    laiq (.mufrad, .mudhakkar) (aidSifa[2]!).2 = false ∧ laiq (.jam, .mudhakkar) (aidSifa[4]!).2 = false := by
  decide

/-- لا صلةَ بلا عائد (س1133): صلةٌ بلا لاحقةِ ضميرٍ مرفوضة. -/
theorem sila_needs_aid (m : MawsulSifa) : silaB m [] = false ∧ silaB m [[atom 'ك' .fatha]] = false := by
  cases m; simp [silaB, aidOf, aidSifa]

/-- «ضَرَبْتُهُ» بعد «الَّذِي» صلةٌ مقبولة؛ وبعد «الَّتِي» مرفوضة (العائدُ مذكّر). -/
def darabtuhu : List Cell :=
  [atom 'ض' .fatha, atom 'ر' .fatha, atom 'ب' .sukun, atom 'ت' .damma, atom 'ه' .damma]

theorem darabtuhu_sila : silaB mawsulSifa[0]! [darabtuhu] = true ∧ silaB mawsulSifa[1]! [darabtuhu] = false := by
  decide

/-! ## ٣. المرشّحون للمرجع -/

/-- عنصرُ النصّ: اسمٌ بصفة عدده ونوعه (معاملان)، أو ضميرٌ بصفته، أو موصولٌ، أو غيرُ ذلك. -/
inductive Unsur where
  | ism (a : Adad × Naw)
  | damir (s : Sifa)
  | mawsul (m : MawsulSifa)
  | ghayr
  deriving DecidableEq, Repr

abbrev Nass := List Unsur

/-- هل العنصرُ مرجعٌ يليق بضميرٍ صفتُه s؟ الاسمُ بصفته، والموصولُ بلفظه (أو بأيّ عددٍ إن كان حرًّا). -/
def yaliq (u : Unsur) (s : Sifa) : Bool :=
  match u with
  | .ism a => laiq a s
  | .mawsul m => laiq m.lafz s || (m.hurr && s.shakhs == .ghaib)
  | _ => false

/-- مرشّحو مرجع الضمير في الموضع i: كلُّ عنصرٍ قبله يليق به — ولضمير الحضور لا مرشّح. -/
def murashshahun (t : Nass) (i : Nat) : List Nat :=
  match t[i]? with
  | some (.damir s) =>
      if hudur s then [] else (List.range i).filter fun j => (t[j]?.map (yaliq · s)).getD false
  | _ => []

/-- الحكمُ ثلاثيّ: متعيّن / متعدّد / لا مرجع. -/
inductive Hukm | mutaayyin (j : Nat) | mutaaddid (js : List Nat) | laMarji
  deriving DecidableEq, Repr

def ihala (t : Nass) (i : Nat) : Hukm :=
  match murashshahun t i with
  | [] => .laMarji
  | [j] => .mutaayyin j
  | js => .mutaaddid js

/-- كلُّ مرشّحٍ يسبق الضمير. -/
theorem murashshah_precedes (t : Nass) (i j : Nat) (h : j ∈ murashshahun t i) : j < i := by
  unfold murashshahun at h
  split at h
  · split at h
    · simp at h
    · exact List.mem_range.1 (List.mem_filter.1 h).1
  · simp at h

/-- كلُّ مرشّحٍ يليق بالضمير. -/
theorem murashshah_laiq (t : Nass) (i j : Nat) (s : Sifa) (hi : t[i]? = some (.damir s))
    (h : j ∈ murashshahun t i) : ∃ u, t[j]? = some u ∧ yaliq u s = true := by
  simp only [murashshahun, hi] at h
  by_cases hs : hudur s = true
  · simp [hs] at h
  · simp only [hs, Bool.false_eq_true, ↓reduceIte, List.mem_filter] at h
    cases hu : t[j]? with
    | none => simp [hu] at h
    | some u => exact ⟨u, rfl, by simpa [hu] using h.2⟩

/-- الحضورُ لا مرجعَ له في النصّ. -/
theorem hudur_no_marji (t : Nass) (i : Nat) (s : Sifa) (hi : t[i]? = some (.damir s)) (hs : hudur s = true) :
    ihala t i = .laMarji := by
  unfold ihala murashshahun; rw [hi]; simp [hs]

/-- التعيينُ حصرًا: متعيّنٌ على j ⟺ المرشّحون [j]. -/
theorem mutaayyin_iff (t : Nass) (i j : Nat) : ihala t i = .mutaayyin j ↔ murashshahun t i = [j] := by
  unfold ihala
  constructor
  · intro h; split at h <;> simp_all
  · intro h; rw [h]

/-- لا تخمين: المتعدّدُ ليس متعيّنًا، واللامرجعُ ليس متعيّنًا. -/
theorem no_guess (t : Nass) (i j : Nat) (h : ihala t i = .mutaayyin j) :
    murashshahun t i ≠ [] ∧ ∀ k, k ∈ murashshahun t i → k = j := by
  rw [mutaayyin_iff] at h; rw [h]; simp

/-! ## ٤. الموصولُ والعائد -/

/-- الموصولُ ثمّ صلةٌ فيها عائدٌ غائبٌ لائق، ولا اسمَ بينهما يليق: مرجعُ العائد الموصولُ متعيّنًا، والشاهد
«جاءني الذي ضربتُه» (س1136) ثمّ عطف. -/
def shahid : Nass :=
  [.ghayr,                                                     -- جَاءَنِي
   .mawsul mawsulSifa[0]!,                                     -- الَّذِي
   .ghayr,                                                     -- ضَرَبْتُ
   .damir ⟨.ghaib, .mufrad, some .mudhakkar⟩]                  -- ـهُ

theorem aid_refers_to_mawsul : ihala shahid 3 = .mutaayyin 1 := by decide

/-- وبمرجعين لائقين لا تعيين: «زيدٌ جاءني الذي ضربتُه» — المتعدّدُ باسمه، لا بالقرب. -/
def shahid2 : Nass := .ism (.mufrad, .mudhakkar) :: shahid

theorem two_marji_no_guess : ihala shahid2 4 = .mutaaddid [0, 2] := by decide

/-- «من» بوجهين (س1139–1142): العائدُ المفردُ المذكّر على اللفظ، والجمعُ على المعنى، كلاهما يليق. -/
theorem man_two_wajh :
    yaliq (.mawsul mawsulSifa[5]!) ⟨.ghaib, .mufrad, some .mudhakkar⟩ = true ∧
    yaliq (.mawsul mawsulSifa[5]!) ⟨.ghaib, .jam, some .mudhakkar⟩ = true ∧
    yaliq (.mawsul mawsulSifa[0]!) ⟨.ghaib, .jam, some .mudhakkar⟩ = false := by decide

/-- وضميرُ الحضور بعد موصولٍ لا يحيل عليه: «الذي أنتَ» لا مرجعَ لأنت في النصّ. -/
theorem anta_after_mawsul : ihala [.mawsul mawsulSifa[0]!, .damir (damirSifa[2]!).2] 1 = .laMarji := by decide

end A116.IhalaHasr

/-! ## ٥. عددُ الشهادة بحدّها -/

namespace A116.Hudud

open A116.Fiber A116.Numbering

variable {α : Type} [DecidableEq α]

/-- عددُ الشهادة بحدّها: ‎P(n⟨الجنس، الذرّات⟩، الرتبة)‎. -/
def certHadd (D : List α) (A : α → List Cell) (j : Jins) (x : α) : Nat :=
  pair (n ⟨j, A x⟩) (rank D A x)

/-- التباين على المجال والجنس معًا. -/
theorem certHadd_injective {D : List α} {A : α → List Cell} {j k : Jins} {x y : α} (hx : x ∈ D) (hy : y ∈ D)
    (h : certHadd D A j x = certHadd D A k y) : j = k ∧ x = y := by
  obtain ⟨h1, h2⟩ := pair_injective h
  have hw := n_inj h1
  simp only [Wahda.mk.injEq] at hw
  refine ⟨hw.1, encode_injective (D := D) (A := A) hx hy ?_⟩
  simp only [encode, hw.2, h2]

/-- الجنسُ يفصل على الذرّات والرتبة نفسِها. -/
theorem certHadd_jins (D : List α) (A : α → List Cell) (x : α) {j k : Jins} (h : j ≠ k) :
    certHadd D A j x ≠ certHadd D A k x := by
  intro he; exact h (n_inj (pair_injective he).1 |> congrArg Wahda.jins)

/-- لا فقد: عددُ الحدّ اقترانٌ، وعددُ الشهادة القديم اقترانُ خارج قسمة أوّله على 11 بثانيه. -/
theorem certHadd_to_certNumber (D : List α) (A : α → List Cell) (j : Jins) (x : α) :
    ∃ u r, certHadd D A j x = pair u r ∧ Certificate.certNumber D A x = pair (u / 11) r :=
  ⟨n ⟨j, A x⟩, rank D A x, rfl, by unfold Certificate.certNumber; rw [n_div]⟩

end A116.Hudud
