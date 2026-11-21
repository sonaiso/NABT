import SLGE.Category

/-!
# المدلولُ وحده — شرطُ أن يكون الدالُّ دالًّا

**الحالة: غير مدقَّق.** كُتب دون سلسلة أدوات Lean (لا وصول إلى GitHub في بيئة الكتابة).
لا يُوسم شيءٌ منه «مبرهَنًا» قبل `lake build` و`lake env lean AuditMadlul.lean`.

السند (ج3، «تقسيم اللفظ باعتبار المدلول وحده»): خمسةُ أقسام — المدلولُ معنى، أو لفظٌ مفردٌ مستعمل
(«الكلمة»)، أو مفردٌ مهمل («أسماء حروف الهجاء»)، أو مركّبٌ مستعمل («الخبر»)، أو مركّبٌ مهمل («الهذيان»).
و«المهمل» ما «لم يوضع لمعنى»؛ و«الوضع للشيء فرعٌ عن تصوّره».

**ما يُبرهَن هنا (إن دُقِّق):**
* الأقسامُ خمسةٌ لا سادس، متمايزة.
* «المستعمل» إحالةٌ إلى القسم الأوّل: إن خلا نوعُ المعاني فلا مستعمل (تعريفيٌّ، صورتُه المنطقية فقط).
* سلسلةُ الدالّ وحده لا تُصنَّف بلا شاهد وضع، ولا تبلغ القسمَ الأوّل أبدًا.
* المركّبُ المستعمل ليس مجموعَ استعمال أجزائه (الهذيان).
* نظيرُ ‎nec_second/two_complete‎ في المدلول: من تسعة أزواجٍ مرتّبةٍ من الأقسام الثلاثة يحمل الإسنادَ ثلاثة،
  ولا زوجَ فيه حرف.

**الوسائط المعلنة:** ‎Cat.rolesOf‎ (من Category.lean). وتنبيه: ‎tim‎ هناك يجب أن يُقرأ «بهيئته»
(ج3: «أو يدل عليه لكن لا بهيئته بل بذاته كالصبوح … وأمس»)، وإلّا صار «أمس» فعلًا.
-/

namespace SLGE
namespace Madlul

/-- قسمُ المدلول: معنى، أو لفظٌ (مركّب؟، مستعمل؟). -/
inductive Div
  | maana
  | lafz (murakkab mustamal : Bool)
  deriving DecidableEq, Repr

def divs : List Div :=
  [.maana, .lafz false true, .lafz false false, .lafz true true, .lafz true false]

/-- **لا سادس:** كلُّ قسمٍ في القائمة. -/
theorem divs_complete : ∀ d : Div, d ∈ divs := by
  intro d
  cases d with
  | maana => simp [divs]
  | lafz a b => cases a <;> cases b <;> simp [divs]

theorem divs_length : divs.length = 5 := rfl

def code : Div → Nat
  | .maana => 0
  | .lafz m u => 1 + 2 * (if m then 1 else 0) + (if u then 0 else 1)

theorem codes : divs.map code = [0, 1, 2, 3, 4] := rfl

/-- **متمايزة:** الترميزُ متباين، فالخمسةُ خمسة. -/
theorem code_inj : ∀ d e : Div, code d = code e → d = e := by
  intro d e h
  cases d with
  | maana =>
    cases e with
    | maana => rfl
    | lafz m u => cases m <;> cases u <;> simp [code] at h
  | lafz m u =>
    cases e with
    | maana => cases m <;> cases u <;> simp [code] at h
    | lafz m' u' =>
      cases m <;> cases u <;> cases m' <;> cases u' <;> first | rfl | simp [code] at h

/-- المستعمل: موضوعٌ لمعنًى في مودَع الوضع. -/
def Mustamal {L M : Type} (wad : L → M → Prop) (l : L) : Prop := ∃ m, wad l m

/-- **لا دالَّ بلا مدلول:** إن خلا نوعُ المعاني فلا لفظَ مستعمل. -/
theorem no_maana_no_dal {L M : Type} (wad : L → M → Prop) (h : M → False) (l : L) :
    ¬ Mustamal wad l := fun ⟨m, _⟩ => h m

/-- قسمُ سلسلةٍ من عالَم الدالّ: بشاهد الوضع (‎some‎) أو بلا شاهد (‎none‎). -/
def qismOf (murakkab : Bool) : Option Bool → Option Div
  | none => none
  | some u => some (.lafz murakkab u)

/-- **لا عالَمَ مغلقًا:** بلا شاهد وضعٍ لا قسم. -/
theorem qism_none (m : Bool) : qismOf m none = none := rfl

/-- **الدالُّ وحده لا يبلغ القسم الأوّل:** ما يصنّفه عالَمُ الدالّ لفظٌ أبدًا، لا معنى. -/
theorem qism_never_maana (m : Bool) (o : Option Bool) : qismOf m o ≠ some .maana := by
  cases o <;> simp [qismOf]

/-- المركّبُ المستعمل: أجزاؤه مستعملة وله إفادة. -/
def murakkabMustamal (parts : List Bool) (ifada : Bool) : Bool := parts.all id && ifada

/-- **الهذيان:** كلُّ جزءٍ مستعمل والمجموعُ مهمل. -/
theorem hadhayan : murakkabMustamal [true, true] false = false ∧
    murakkabMustamal [true, true] true = true := by decide

def kinds : List Cat.Kind := [.ism, .fil, .harf]

/-- زوجٌ مرتّبٌ يحمل إسنادًا: أحدُهما مسنَدٌ إليه والآخر مسنَد. -/
def isnad (a b : Cat.Kind) : Bool :=
  ((Cat.rolesOf a).1 && (Cat.rolesOf b).2) || ((Cat.rolesOf b).1 && (Cat.rolesOf a).2)

def pairs : List (Cat.Kind × Cat.Kind) := kinds.flatMap fun a => kinds.map fun b => (a, b)

/-- **الإسنادُ زوجٌ:** ‎9‎ أزواج، يحمل الإسنادَ منها ‎3‎. -/
theorem isnad_count : pairs.length = 9 ∧ (pairs.filter fun p => isnad p.1 p.2).length = 3 := by
  decide

/-- **لا إسنادَ في زوجٍ فيه حرف.** -/
theorem isnad_harf : ∀ k : Cat.Kind, isnad .harf k = false ∧ isnad k .harf = false := by
  intro k; cases k <;> decide

/-! ## الإفادةُ منطوقٌ ومفهومٌ لا ثالث لهما (ج3)

المقدّمةُ منقولة لا مستنتَجة: «دلالات اللفظ باعتبار الدال وحده محصورة في هذه الدلالات الثلاث».
والنتيجةُ صورتُها: دالّةٌ كلّيّةٌ من ثلاثةٍ على اثنين، فلا ثالثَ في الصورة. -/

inductive Dalala | mutabaqa | tadammun | iltizam
  deriving DecidableEq, Repr

inductive Tariq | mantuq | mafhum
  deriving DecidableEq, Repr

def tariq : Dalala → Tariq
  | .mutabaqa => .mantuq
  | .tadammun => .mantuq
  | .iltizam => .mafhum

/-- **لا ثالث.** -/
theorem no_third : ∀ d : Dalala, tariq d = .mantuq ∨ tariq d = .mafhum := by
  intro d; cases d <;> simp [tariq]

/-- **وكلاهما يقع.** -/
theorem both_occur : (∃ d, tariq d = .mantuq) ∧ (∃ d, tariq d = .mafhum) :=
  ⟨⟨.mutabaqa, rfl⟩, ⟨.iltizam, rfl⟩⟩

/-- **المفهومُ هو الالتزامُ وحده.** -/
theorem mafhum_iff_iltizam : ∀ d : Dalala, tariq d = .mafhum ↔ d = .iltizam := by
  intro d; cases d <;> simp [tariq]

/-- أصنافُ مفهوم المخالفة: «محصور في الأصناف الأربعة ليس غير». -/
inductive Mukhalafa | sifa | shart | ghaya | adad
  deriving DecidableEq, Repr

def mukhalafaAll : List Mukhalafa := [.sifa, .shart, .ghaya, .adad]

theorem mukhalafa_closed : ∀ m : Mukhalafa, m ∈ mukhalafaAll := by
  intro m; cases m <;> simp [mukhalafaAll]

/-! ## العامّ والخاصّ، والمطلق والمقيّد (ج3)

العامّ ما يصلح له لفظُه (قائمةُ أفرادٍ بالوضع)، والتخصيصُ «إخراج بعض ما يتناوله اللفظ». -/

def takhsis (amm : List Nat) (kharij : Nat → Bool) : List Nat := amm.filter (fun x => !kharij x)

/-- **التخصيصُ لا يُدخل جديدًا:** كلُّ ما بقي بعد التخصيص كان في العامّ. -/
theorem takhsis_sub (amm : List Nat) (k : Nat → Bool) : ∀ x ∈ takhsis amm k, x ∈ amm := by
  intro x hx
  exact (List.mem_filter.mp hx).1

def muqayyad (mutlaq : List Nat) (sifa : Nat → Bool) : List Nat := mutlaq.filter sifa

/-- **«من عمل بالمقيّد وفى بالعمل بدلالة المطلق»:** المقيّدُ داخلٌ في المطلق. -/
theorem amal_bil_muqayyad (mutlaq : List Nat) (q : Nat → Bool) : ∀ x ∈ muqayyad mutlaq q, x ∈ mutlaq := by
  intro x hx
  exact (List.mem_filter.mp hx).1

/-- **«ومن عمل بالمطلق لم يفِ بالعمل بدلالة المقيّد»:** على الشاهد (رقبة مؤمنة = 0، كافرة = 1). -/
theorem amal_bil_mutlaq_la_yafi : (1 ∈ [0, 1]) ∧ (1 ∉ muqayyad [0, 1] (fun x => x == 0)) := by decide

def haml (sameHukm sameSabab : Bool) : Bool := sameHukm && sameSabab

/-- **الحمل إذا وفقط إذا اتّحد الحكمُ والسبب.** -/
theorem haml_iff (h s : Bool) : haml h s = true ↔ h = true ∧ s = true := by
  cases h <;> cases s <;> decide

/-! ## خطابُ الوضع: السبب والشرط والمانع (ج3)

صورةٌ بطرفٍ واحدٍ لكلّ ركن (والقوائمُ في المرآة البايثونيّة ‎wad.py‎):
‎wujud dalil sabab shart mani = dalil ∧ sabab ∧ shart ∧ ¬mani‎. -/

def wujud (dalil sabab shart mani : Bool) : Bool := dalil && sabab && shart && !mani

/-- **«ما يلزم من عدمه العدم»:** -/
theorem shart_adam (d s m : Bool) : wujud d s false m = false := by
  cases d <;> cases s <;> cases m <;> rfl

/-- **«ولا يلزم من وجوده وجود»:** شاهدٌ يوجد فيه الشرط ولا يوجد الحكم. -/
theorem shart_la_yujib : ∃ d s m, wujud d s true m = false := ⟨true, false, false, rfl⟩

/-- **«فالسبب ليس موجباً للحكم»:** بلا دليلٍ لا حكم وإن وُجد السبب. -/
theorem sabab_la_yujib (sh m : Bool) : wujud false true sh m = false := by
  cases sh <;> cases m <;> rfl

/-- **المانعُ «يستلزم وجوده عكس ما يقتضيه الحكم».** -/
theorem mani_yamna (d s sh : Bool) : wujud d s sh true = false := by
  cases d <;> cases s <;> cases sh <;> rfl

/-- **ويقع الحكمُ إذا تمّت أركانه ولا مانع.** -/
theorem wujud_tamm : wujud true true true false = true := rfl

end Madlul
end SLGE
