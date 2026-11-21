import A116.Haqaiq

/-!
# المجازُ في المصدر والمشتقّ، والحقيقةُ شرطُ إمكان المجاز (ADR ٩٤، أمرُ المالك 2026-10-17)

نصُّ المالك: «حلّل الوزن في المجاز في كتاب الشخصيّة… المصدرُ والمشتقّاتُ مجاز، ولكنّ الحقيقةَ شرطُ إمكان المجاز».

## السند (الشخصيّة ج3 المختومة، الأسطرُ 1-based)

* س395: الحقيقةُ «اللفظ المستعمل فيما وُضع له أوّلًا في اللغة»، والمجازُ «في غير ما وُضع له أوّلًا… لما بينهما من
  التعلّق»، وهو في المفردات أو في التركيب أو فيهما (س398).
* س399: «ويُشترط في استعمال المجاز وجودُ العلاقة بين المعنى الحقيقيّ والمعنى المجازيّ… لا بدّ أن تكون من أنواع
  العلاقة التي استعملتها العرب، ولكن لا يُشترط أن يكون التعبيرُ قد استعمله العرب».
* س409: «تسمية الشيء باعتبار ما كان عليه… أم مشتقًّا كالضارب على من فرغ من الضرب».
* س410: «التعلّقُ الحاصل بين المصدر، واسم المفعول، واسم الفاعل — فإنّ كلًّا منها يُطلق على الآخر مجازًا، وهو ستّة
  أقسام»: دافقٌ = مدفوق، مستورًا = ساترًا، رجلٌ صوم = صائم، قم قائمًا = قيامًا، المفتون = الفتنة، خلقُ الله = مخلوقه.
* س411: «المجازُ بالذات إنّما يكون في اسم الجنس… كالأسد للشجاع، والقتل للضرب الشديد، ولا يدخل في غير ذلك».
* س412: الحرفُ لا مجازَ فيه بالذات، «فيسري التجوّزُ من المتعلَّقات إليها».
* س413: «الفعلُ بأقسامه، والمشتقُّ بأقسامه… تابعٌ لأصله وهو المصدر في كونه حقيقةً أو مجازًا. فإطلاقُ ضاربٍ… بعد
  انقضاء الضرب أو قبله إنّما كان مجازًا».
* س414: العلَمُ ليس بمجاز.
* س415: «الأصلُ في الكلام هو الحقيقة… لاحتياج المجاز إلى الوضع الأوّل للمعنى الحقيقيّ، وإلى المناسبة بينه وبين
  المعنى المجازيّ، وإلى النقل منه إليه، في حين أنّ الحقيقة لا تحتاج إلّا إلى الوضع الأوّل».

## ما يُبنى

* **الحقيقةُ شرطُ إمكان المجاز**: شروطُ الحقيقة جزءٌ من شروط المجاز، فلا مجازَ بلا وضعٍ أوّل (`la_majaz_bila_haqiqa`).
* **المجازُ بالذات في اسم الجنس وحدَه** (والمصدرُ اسمُ جنسٍ للحدث: «القتل للضرب الشديد»)، والفعلُ والمشتقُّ تابعان
  للمصدر، والحرفُ لمتعلَّقه، والعلَمُ لا مجازَ فيه.
* **الوزنُ دالٌّ والدورُ مدلول**: الحقيقةُ أن يوافق الدورُ الوزن، والمجازُ أن يخالفه بإحدى الستّ، والستُّ هي كلُّ
  الأزواج المرتّبة من الثلاثة؛ فالوزنُ وحدَه لا يعيّن الدور.
* **زمانُ الإطلاق من نسبة «الآن»** (`Malumat.nisba`): المشتقُّ حال الحدث حقيقة، وقبلَه أو بعدَه مجاز، وبين إطارين
  «لا حكم».

وما لا يُبرهَن: أنّ هذه علاقاتُ العرب. ذلك مرويُّ ج3 بأسطره.
-/

namespace A116.Majaz

open A116.Malumat

inductive Hukm | haqiqa | majaz | laHukm
  deriving DecidableEq, Repr

/-! ## ١. الحقيقةُ شرطُ إمكان المجاز (س399، س415) -/

/-- شروطُ الاستعمال كما عدّها س415. -/
inductive Shart | wadAwwal | munasaba | naql
  deriving DecidableEq, Repr

def shurutHaqiqa : List Shart := [.wadAwwal]
def shurutMajaz : List Shart := [.wadAwwal, .munasaba, .naql]

/-- **شروطُ الحقيقة جزءٌ من شروط المجاز، والمجازُ يحتاج أكثر** — فهو خلافُ الأصل. -/
theorem haqiqa_shart_majaz :
    (∀ s ∈ shurutHaqiqa, s ∈ shurutMajaz) ∧ shurutHaqiqa.length < shurutMajaz.length := by decide

/-- العلاقةُ من أنواع العرب (س400–410)، وأحدَ عشرَ نوعًا عُدّت هنا. -/
inductive Alaqa
  | sababiyya | musabbabiyya | mushabaha | mudadda | kulliyya | juziyya
  | istidad | mujawara | ziyada | maKana | tabadulSigha
  deriving DecidableEq, Repr

/-- الاستعمال: الوضعُ الأوّل (المعنى الحقيقيّ)، والعلاقةُ المنقولة نوعُها، والقرينة. -/
structure Istimal where
  wad : Option String
  alaqa : Option Alaqa
  qarina : Bool
  deriving DecidableEq, Repr

def imkanMajaz (i : Istimal) : Bool := i.wad.isSome && i.alaqa.isSome

/-- الحكم: بلا قرينةٍ حقيقةٌ إن كان وضع؛ وبالقرينة مجازٌ إن أمكن، وإلّا «لا حكم». -/
def hukm (i : Istimal) : Hukm :=
  if i.qarina then (if imkanMajaz i then .majaz else .laHukm)
  else if i.wad.isSome then .haqiqa else .laHukm

/-- **لا مجازَ بلا حقيقة**: ما لا وضعَ أوّلَ له لا يكون مجازًا ولو قامت القرينة. -/
theorem la_majaz_bila_haqiqa (i : Istimal) (h : i.wad = none) : hukm i ≠ .majaz := by
  cases hq : i.qarina <;> simp [hukm, imkanMajaz, h, hq]

/-- **ولا مجازَ بلا علاقةٍ عربيّة** (س399). -/
theorem la_majaz_bila_alaqa (i : Istimal) (h : i.alaqa = none) : hukm i ≠ .majaz := by
  cases hq : i.qarina <;> cases hw : i.wad <;> simp [hukm, imkanMajaz, h, hq, hw]

/-- والمجازُ بالحكم يستلزم الحقيقةَ الممكنةَ للّفظ نفسِه: لو رُفعت القرينةُ لكان حقيقة. -/
theorem majaz_yastalzim_haqiqa (i : Istimal) (h : hukm i = .majaz) :
    hukm { i with qarina := false } = .haqiqa := by
  unfold hukm imkanMajaz at h
  by_cases hq : i.qarina <;> by_cases hw : i.wad.isSome <;> by_cases ha : i.alaqa.isSome <;>
    simp_all [hukm]

/-- الأسدُ للشجاع (س395): وضعٌ أوّلٌ وعلاقةُ مشابهة وقرينة؛ ويوافق `Haqaiq` (ADR ٩٢). -/
def asad : Istimal := ⟨some "الحيوان المفترس", some .mushabaha, true⟩

theorem asad_majaz :
    hukm asad = .majaz ∧ hukm { asad with qarina := false } = .haqiqa ∧
    Haqaiq.haml Haqaiq.naql "الأسد" (some (.mania (some .majaz))) = .majaz := by decide

/-! ## ٢. أين يدخل المجاز: بالذات وبالتبع (س411–414) -/

inductive Qism | ismJins | masdar | mushtaq | fil | harf | alam
  deriving DecidableEq, Repr

/-- المجازُ بالذات في اسم الجنس وحدَه، والمصدرُ منه («القتل للضرب الشديد»). -/
def bilDhat : Qism → Bool
  | .ismJins | .masdar => true
  | _ => false

/-- حكمُ الكلمة: اسمُ الجنس والمصدرُ بحكمهما، والفعلُ والمشتقُّ بحكم المصدر، والحرفُ بحكم متعلَّقه، والعلَمُ حقيقة. -/
def hukmKalima (q : Qism) (dhati asl mutaallaq : Hukm) : Hukm :=
  match q with
  | .ismJins | .masdar => dhati
  | .mushtaq | .fil => asl
  | .harf => mutaallaq
  | .alam => .haqiqa

/-- **المشتقُّ والفعلُ تابعان للمصدر** (س413): حكمُهما حكمُه أيًّا كان ما يُنسب إليهما بالذات. -/
theorem tabi_lil_masdar (d a m : Hukm) :
    hukmKalima .mushtaq d a m = hukmKalima .masdar a d m ∧ hukmKalima .fil d a m = a := ⟨rfl, rfl⟩

/-- **الحرفُ بالتبع** (س412، «لِيَكُونَ لَهُمْ عَدُوًّا»): مجازُ لام العلّة مجازُ متعلَّقها. -/
theorem harf_bittaba (d a : Hukm) : hukmKalima .harf d a .majaz = .majaz := rfl

/-- **العلَمُ لا مجازَ فيه** (س414). -/
theorem alam_la_majaz (d a m : Hukm) : hukmKalima .alam d a m ≠ .majaz := by simp [hukmKalima]

theorem bilDhat_iff (q : Qism) : bilDhat q = true ↔ q = .ismJins ∨ q = .masdar := by
  cases q <;> simp [bilDhat]

/-! ## ٣. الوزنُ دالٌّ والدورُ مدلول: الستّ (س410) -/

inductive Sigha | masdar | faail | mafool
  deriving DecidableEq, Repr

/-- الأقسامُ الستّة بشواهدها: (الوزن، الدور، الشاهد). -/
def sitta : List (Sigha × Sigha × String) :=
  [(.faail, .mafool, "دافق"), (.mafool, .faail, "مستورا"), (.masdar, .faail, "صوم"),
   (.faail, .masdar, "قائما"), (.mafool, .masdar, "المفتون"), (.masdar, .mafool, "خلق")]

def sighat : List Sigha := [.masdar, .faail, .mafool]

/-- **«كلٌّ منها يُطلق على الآخر»**: الستُّ هي كلُّ الأزواج المرتّبة المتباينة من الثلاثة، بلا تكرار. -/
theorem sitta_kull_azwaj :
    (∀ a ∈ sighat, ∀ b ∈ sighat, a ≠ b → (a, b) ∈ sitta.map (fun r => (r.1, r.2.1))) ∧
    (sitta.map (fun r => (r.1, r.2.1))).Nodup ∧ sitta.length = 6 ∧
    (∀ r ∈ sitta, r.1 ≠ r.2.1) := by decide

/-- حكمُ الصيغة: الدورُ على وزنه حقيقة، ومخالفُه مجازٌ بعلاقة التبادل إن كان من الستّ. -/
def hukmSigha (wazn dawr : Sigha) : Hukm :=
  if wazn = dawr then .haqiqa
  else if (sitta.map (fun r => (r.1, r.2.1))).contains (wazn, dawr) then .majaz else .laHukm

/-- **كلُّ مخالفةٍ بين الوزن والدور مجازٌ ممكن، وكلُّ موافقةٍ حقيقة** — لا «لا حكم» في الستّ. -/
theorem wazn_dawr (w d : Sigha) :
    hukmSigha w d = (if w = d then .haqiqa else .majaz) := by
  cases w <;> cases d <;> decide

/-- **الوزنُ وحدَه لا يعيّن الدور**: «ضارب» حقيقةً فاعل، و«دافق» على وزنه نفسِه مفعول. -/
theorem wazn_la_yuayyin_dawr : ¬ ∃ f : Sigha → Sigha,
    f .faail = .faail ∧ ∀ r ∈ sitta, f r.1 = r.2.1 := by
  rintro ⟨f, h1, h2⟩
  have := h2 (.faail, .mafool, "دافق") (by decide)
  simp at this
  rw [h1] at this
  exact absurd this (by decide)

/-! ## ٤. زمانُ الإطلاق من «الآن» (س409، س413) -/

/-- حكمُ المصدر عند الإطلاق: الحدثُ مع الإطلاق حقيقة، وقبله أو بعده مجاز، وبين إطارين «لا حكم». -/
def hukmZaman (hadath itlaq : Mawqi) : Hukm :=
  match nisba hadath itlaq with
  | some .maa => .haqiqa
  | some _ => .majaz
  | none => .laHukm

/-- «ضاربٌ» بعد انقضاء الضرب أو قبله مجاز، وحالَه حقيقة، تبعًا للمصدر — لكلّ «آن». -/
theorem darib (n : Int) :
    hukmKalima .mushtaq .laHukm (hukmZaman ⟨.alAn, n⟩ ⟨.alAn, n⟩) .laHukm = .haqiqa ∧
    hukmKalima .mushtaq .laHukm (hukmZaman ⟨.alAn, n - 1⟩ ⟨.alAn, n⟩) .laHukm = .majaz ∧
    hukmKalima .mushtaq .laHukm (hukmZaman ⟨.alAn, n + 1⟩ ⟨.alAn, n⟩) .laHukm = .majaz := by
  have a1 : n - 1 < n := by omega
  have a2 : ¬ (n + 1 < n) := by omega
  have a3 : n + 1 ≠ n := by omega
  simp [hukmKalima, hukmZaman, nisba, cmpInt, a1, a2, a3]

/-- ونقلُ «الآن» لا يغيّر الحكم. -/
theorem zaman_shift (a b k : Int) (i : Itar) :
    hukmZaman ⟨i, a + k⟩ ⟨i, b + k⟩ = hukmZaman ⟨i, a⟩ ⟨i, b⟩ := by
  simp only [hukmZaman, nisba_shift]

/-- وبين إطارين لا حكم: حدثٌ بالهجريّ وإطلاقٌ بالميلاديّ. -/
theorem zaman_itarayn (a b : Int) :
    hukmZaman ⟨.istilah "الهجري", a⟩ ⟨.istilah "الميلادي", b⟩ = .laHukm := by
  simp [hukmZaman, hijri_miladi]

/-! ## المراسي -/

/-- (النصّ، السطر 1-based، النصّ بعينه). -/
def marasi : List (String × Nat × String) :=
  [("j3", 395, "الحقيقة هي اللفظ المستعمل فيما وضع له أولاً في اللغة"),
   ("j3", 395, "والمجاز هو اللفظ المستعمل في غير ما وضع له أولاً في اللغة لما بينهما من التعلق"),
   ("j3", 399, "ويشترط في استعمال المجاز وجود العلاقة بين المعنى الحقيقي والمعنى المجازي"),
   ("j3", 399, "ولكن لا يشترط أن يكون التعبير قد استعمله العرب"),
   ("j3", 409, "أم مشتقاً كالضارب على من فرغ من الضرب"),
   ("j3", 410, "فإن كلاً منها يطلق على الآخر مجازاً، وهو ستة أقسام"),
   ("j3", 410, "مِنْ مَاءٍ دَافِقٍ (6)  أي مدفوق"),
   ("j3", 410, "(رجل صوم وعدل)، أي صائم وعادل"),
   ("j3", 411, "والمجاز بالذات إنما يكون في اسم الجنس"),
   ("j3", 411, "والقتل للضرب الشديد"),
   ("j3", 412, "فيسري التجوز من المتعلقات إليها"),
   ("j3", 413, "تابع لأصله وهو المصدر في كونه حقيقة أو مجازاً"),
   ("j3", 413, "فإطلاق ضارب مثلاً بعد انقضاء الضرب أو قبله إنما كان مجازاً"),
   ("j3", 414, "فدل على أنه ليس بمجاز"),
   ("j3", 415, "والأصل في الكلام هو الحقيقة"),
   ("j3", 415, "لاحتياج المجاز إلى الوضع الأول للمعنى الحقيقي"),
   ("j3", 415, "في حين أن الحقيقة لا تحتاج إلا إلى الوضع الأول")]

end A116.Majaz
