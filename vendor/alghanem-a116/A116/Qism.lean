/-!
# تقسيمُ الكلم: البناءُ والإعرابُ وأصنافُ المعرب، والفرزُ يزيد القراءة (ADR ٥٤)

كلُّ قاعدةٍ هنا بيتٌ من الألفيّة في شرح ابن عقيل المختوم (`corpora/ibn-aqil/sharh-alfiyya.txt.gz`، بأرقام
أسطره):

* **الاسم** (س305، س350): «والاسم منه معرب ومبني لشبه من الحروف مدني … ومعرب الأسماء ما قد سلما من شبه
  الحرف» — والمبنيُّ هو الصنفُ المغلق المقيس في SLGE (ADR ٥٣ هناك)؛ هنا المعرب.
* **الفعل** (س360–361): «وفعل أمر ومضي بنيا وأعربوا مضارعا إن عريا من نون توكيد مباشر ومن نون إناث» —
  `binaFil`، `murab_iff`، `mabni_iff`.
* **أصنافُ المعرب** وآخرُ كلٍّ في كلّ حالة (`ending`): الصحيحُ بالحركات، والفعلُ يُجزم بالتسكين
  (س406–407)؛ الأسماءُ الستّة بالواو والألف والياء (س415)؛ المثنّى بالألف والياء (س496–498)؛ جمعُ المذكّر
  السالم بالواو والياء (س530)؛ جمعُ المؤنّث يُكسر في الجرّ والنصب (س608)؛ ما لا ينصرف يُجرّ بالفتحة ما لم
  يُضف أو يكن بعد أل (س641)؛ الأفعالُ الخمسة بثبوت النون رفعًا وحذفِها نصبًا وجزمًا (س648–649)؛ المقصورُ
  يُقدَّر إعرابُه كلُّه، والمنقوصُ يظهر نصبُه ويُقدَّر رفعُه وجرُّه (س663–665)؛ والمعتلُّ من الأفعال: الألفُ
  يُقدَّر فيها غيرُ الجزم، والواوُ والياءُ يظهر نصبُهما، ويُحذف الثلاثُ جزمًا (س693–694).

**الآخرُ المرئيّ** (`Ending`): حركةُ الحرف الأخير، أو حرفُ مدٍّ ساكنٌ أخير، أو نونُ المثنّى والجمع بما قبلها.
فـ«يَدْعُ» مجزومًا آخرُه ضمّة، و«يَخْشَ» مجزومًا آخرُه فتحة، و«مُسْلِمَاتِ» منصوبًا آخرُه كسرة.

**الفرزُ يحسّن القراءة رياضيًّا.** القارئُ السليمُ الأتمّ لمنظورٍ `v` على الأصناف (`decide₁ v`) يحكم بحالةٍ
إن اتّفقت عليها كلُّ الأصناف التي يراها المنظورُ واحدًا وتُظهر ذلك الآخر، وإلّا امتنع. فهو **سليم**
(`read_sound`) و**أتمُّ كلّ قارئٍ سليمٍ** بذلك المنظور (`read_best`). وثلاثةُ منظورات: بلا فرز (`blindV`)،
وبفرز الاسم من الفعل (`qismV`)، وبالصنف كلّه (`classV`). المبرهَن: كلُّ ما يحكم به منظورٌ يحكم به ألطفُ
منه بالحالة نفسها (`blind_le_qism`، `qism_le_class`)، والأعدادُ على أزواج (صنف، حالة) الخمسة والأربعين
(`pairs_length`): **بلا فرز 5، وبفرز الاسم من الفعل 11، وبالصنف 24** (`coverage_counts`). والقارئُ الساذج (آخرُ حركةٍ ← حالة)
**غيرُ سليم**: يخطئ في 5 أزواج (`naive_wrong_count`؛ يَدْعُ مجزومًا يقرؤه رفعًا: `naive_yadu`). وما يبقى
ملتبسًا بعد الصنف (21 زوجًا) التباسٌ لا يرفعه إلّا العامل: دَينٌ مسمًّى `CASE_NEEDS_AMIL`.

وما لا يُبرهَن هنا: أنّ هذه هي العربية — هذا منقولٌ من الألفيّة، وLean يبرهن خواصَّ المنقول.
-/

namespace A116.Qism

/-! ## الفعل: البناءُ والإعراب -/

inductive Zaman | madi | mudari | amr
  deriving DecidableEq, Repr

/-- النونُ المتّصلة: لا نون، توكيدٌ مباشر، توكيدٌ مفصولٌ بألف اثنين أو واو جماعة أو ياء مخاطبة (الشرح
س375–379: «هل تضربانّ»)، نونُ الإناث. -/
inductive Nun | none | tawkidMubashir | tawkidMafsul | inath
  deriving DecidableEq, Repr

inductive Bina | mabni | murab
  deriving DecidableEq, Repr

def binaFil : Zaman → Nun → Bina
  | .madi, _ => .mabni
  | .amr, _ => .mabni
  | .mudari, .tawkidMubashir => .mabni
  | .mudari, .inath => .mabni
  | .mudari, _ => .murab

theorem murab_iff (z : Zaman) (n : Nun) :
    binaFil z n = .murab ↔ z = .mudari ∧ (n = .none ∨ n = .tawkidMafsul) := by
  cases z <;> cases n <;> simp [binaFil]

theorem mabni_iff (z : Zaman) (n : Nun) :
    binaFil z n = .mabni ↔ z = .madi ∨ z = .amr ∨ n = .tawkidMubashir ∨ n = .inath := by
  cases z <;> cases n <;> simp [binaFil]

/-! ## أصنافُ المعرب وآخرُها -/

inductive Irab | raf | nasb | jarr | jazm
  deriving DecidableEq, Repr

inductive Ending | damma | fatha | kasra | sukun | waw | alif | ya | ani | ayni | una | ina
  deriving DecidableEq, Repr

inductive Cls
  | iSahih | iSitta | iMuthanna | iJamM | iJamF | iMamnu | iMaqsur | iManqus
  | fSahih | fKhamsaA | fKhamsaW | fKhamsaY | fMutalAlif | fMutalW | fMutalY
  deriving DecidableEq, Repr

def isIsm : Cls → Bool
  | .iSahih | .iSitta | .iMuthanna | .iJamM | .iJamF | .iMamnu | .iMaqsur | .iManqus => true
  | _ => false

/-- آخرُ المعرب في كلّ حالة؛ والاسمُ لا يُجزم والفعلُ لا يُجرّ (س404–405). -/
def ending : Cls → Irab → Option Ending
  | .iSahih, .raf => some .damma | .iSahih, .nasb => some .fatha | .iSahih, .jarr => some .kasra
  | .iSitta, .raf => some .waw | .iSitta, .nasb => some .alif | .iSitta, .jarr => some .ya
  | .iMuthanna, .raf => some .ani | .iMuthanna, .nasb => some .ayni | .iMuthanna, .jarr => some .ayni
  | .iJamM, .raf => some .una | .iJamM, .nasb => some .ina | .iJamM, .jarr => some .ina
  | .iJamF, .raf => some .damma | .iJamF, .nasb => some .kasra | .iJamF, .jarr => some .kasra
  | .iMamnu, .raf => some .damma | .iMamnu, .nasb => some .fatha | .iMamnu, .jarr => some .fatha
  | .iMaqsur, .raf => some .alif | .iMaqsur, .nasb => some .alif | .iMaqsur, .jarr => some .alif
  | .iManqus, .raf => some .ya | .iManqus, .nasb => some .fatha | .iManqus, .jarr => some .ya
  | .fSahih, .raf => some .damma | .fSahih, .nasb => some .fatha | .fSahih, .jazm => some .sukun
  | .fKhamsaA, .raf => some .ani | .fKhamsaA, .nasb => some .alif | .fKhamsaA, .jazm => some .alif
  | .fKhamsaW, .raf => some .una | .fKhamsaW, .nasb => some .waw | .fKhamsaW, .jazm => some .waw
  | .fKhamsaY, .raf => some .ina | .fKhamsaY, .nasb => some .ya | .fKhamsaY, .jazm => some .ya
  | .fMutalAlif, .raf => some .alif | .fMutalAlif, .nasb => some .alif | .fMutalAlif, .jazm => some .fatha
  | .fMutalW, .raf => some .waw | .fMutalW, .nasb => some .fatha | .fMutalW, .jazm => some .damma
  | .fMutalY, .raf => some .ya | .fMutalY, .nasb => some .fatha | .fMutalY, .jazm => some .kasra
  | _, _ => none

def classes : List Cls :=
  [.iSahih, .iSitta, .iMuthanna, .iJamM, .iJamF, .iMamnu, .iMaqsur, .iManqus,
   .fSahih, .fKhamsaA, .fKhamsaW, .fKhamsaY, .fMutalAlif, .fMutalW, .fMutalY]
def irabs : List Irab := [.raf, .nasb, .jarr, .jazm]
def endings : List Ending := [.damma, .fatha, .kasra, .sukun, .waw, .alif, .ya, .ani, .ayni, .una, .ina]

/-- أزواجُ (صنف، حالة) التي لها آخر. -/
def pairs : List (Cls × Irab) :=
  (classes.flatMap fun c => irabs.map fun i => (c, i)).filter fun p => (ending p.1 p.2).isSome

theorem pairs_length : pairs.length = 45 := by decide

/-! ## القارئ بمنظور -/

/-- الحالاتُ المرشَّحة للآخر e فيما يراه المنظورُ v صنفًا واحدًا k. -/
def cands {κ : Type} [DecidableEq κ] (v : Cls → κ) (k : κ) (e : Ending) : List Irab :=
  (pairs.filter fun p => v p.1 == k && ending p.1 p.2 == some e).map (·.2)

/-- القارئُ السليمُ الأتمّ بالمنظور v. -/
def read₁ {κ : Type} [DecidableEq κ] (v : Cls → κ) (k : κ) (e : Ending) : Option Irab :=
  match cands v k e with
  | [] => none
  | i :: rest => if rest.all (· == i) then some i else none

theorem read_sound {κ : Type} [DecidableEq κ] (v : Cls → κ) (k : κ) (e : Ending) (i : Irab)
    (h : read₁ v k e = some i) : ∀ j ∈ cands v k e, j = i := by
  unfold read₁ at h
  split at h
  · cases h
  · rename_i i' rest heq
    split at h
    · rename_i hall
      cases h
      intro j hj
      rw [heq] at hj
      rcases List.mem_cons.1 hj with rfl | hj
      · rfl
      · exact (beq_iff_eq.1 (List.all_eq_true.1 hall j hj))
    · cases h

/-- كلُّ قارئٍ سليمٍ بالمنظور v يحكم حيث يحكم `read₁` بالحالة نفسها، أو يمتنع. -/
theorem read_best {κ : Type} [DecidableEq κ] (v : Cls → κ) (k : κ) (e : Ending) (i : Irab)
    (hsound : ∀ j ∈ cands v k e, j = i) (hne : cands v k e ≠ []) : read₁ v k e = some i := by
  unfold read₁
  split
  · rename_i h; exact absurd h hne
  · rename_i i' rest heq
    have hi' : i' = i := hsound i' (by rw [heq]; exact List.mem_cons_self ..)
    subst hi'
    have : rest.all (· == i') = true := by
      apply List.all_eq_true.2
      intro x hx
      exact beq_iff_eq.2 (hsound x (by rw [heq]; exact List.mem_cons_of_mem _ hx))
    simp [this]

def blindV : Cls → Unit := fun _ => ()
def qismV : Cls → Bool := isIsm
def classV : Cls → Cls := id

/-- عددُ الأزواج التي يقرؤها المنظورُ v صوابًا. -/
def covered {κ : Type} [DecidableEq κ] (v : Cls → κ) : Nat :=
  pairs.countP fun p => match ending p.1 p.2 with
    | some e => read₁ v (v p.1) e == some p.2
    | none => false

theorem coverage_counts : covered blindV = 5 ∧ covered qismV = 11 ∧ covered classV = 24 := by decide

/-- كلُّ ما يقرؤه المنظورُ الأخشن يقرؤه الألطفُ بالحالة نفسها. -/
theorem blind_le_qism : ∀ p ∈ pairs, ∀ e ∈ endings, ending p.1 p.2 = some e →
    read₁ blindV () e = some p.2 → read₁ qismV (isIsm p.1) e = some p.2 := by decide

theorem qism_le_class : ∀ p ∈ pairs, ∀ e ∈ endings, ending p.1 p.2 = some e →
    read₁ qismV (isIsm p.1) e = some p.2 → read₁ classV p.1 e = some p.2 := by decide

/-! ## الساذج -/

/-- آخرُ حركةٍ ← حالة. -/
def naive : Ending → Option Irab
  | .damma => some .raf | .fatha => some .nasb | .kasra => some .jarr | .sukun => some .jazm
  | _ => none

def naiveWrong : Nat :=
  pairs.countP fun p => match ending p.1 p.2 with
    | some e => (naive e).isSome && naive e != some p.2
    | none => false

theorem naive_wrong_count : naiveWrong = 5 := by decide

/-- «يَدْعُ» مجزومًا آخرُه ضمّة فيقرؤه الساذجُ رفعًا؛ والقارئُ بالصنف يقرؤه جزمًا. -/
theorem naive_yadu : ending .fMutalW .jazm = some .damma ∧ naive .damma = some .raf ∧
    read₁ classV .fMutalW .damma = some .jazm := by decide

/-- «مُسْلِمَاتِ» منصوبًا آخرُه كسرة؛ وبلا صنفٍ لا تُقرأ الكسرةُ ولا الفتحة. -/
theorem blind_abstains : read₁ blindV () .kasra = none ∧ read₁ blindV () .fatha = none ∧
    read₁ qismV true .fatha = none ∧ read₁ classV .iSahih .fatha = some .nasb := by decide

end A116.Qism
