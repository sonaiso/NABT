/-
  Madlul/Ishtirak.lean — اتّفاقُ اللفظين واختلافُ المعنيين: الشبكةُ على عُقَد المعنى لا على الجذر.

  السند: سيبويه، الكتاب المختوم س247–251: «اعلم أن من كلامهم اختلاف اللفظين لاختلاف المعنيين واختلاف اللفظين والمعنى واحد واتفاق
  اللفظين واختلاف المعنيين … فاختلاف اللفظين لاختلاف المعنيين هو نحو جلس وذهب | واختلاف اللفظين والمعنى واحد نحو ذهب وانطلق |
  واتفاق اللفظين والمعنى مختلف قولك وجدت عليه من الموجدة ووجدت إذا أردت وجدان الضالة». ومغني اللبيب س2247: «الباء المفردة حرف جر
  لأربعة عشر معنى» وسيبويه اقتصر على الإلصاق «معنى لا يفارقها»: أصلٌ جامعٌ ومعانٍ.

  * مبرهن لكلّ: `alaqa` قسمةُ سيبويه حاصرةٌ متناظرة (`alaqa_hasira`، `alaqa_tanazur`، `ishtirak_iff`)؛ وصلةُ العُقَد تُسقَط على
    الجذور (`isqat_yahfaz`)، والعكسُ لا يلزم.
  * على الشاهد (الجدول المولَّد `IshtirakData.lean` من اللسان بقواعد H1–H3 في `shabaka/hiss.py`): شواهدُ سيبويه الثلاثة
    (`shawahid_sibawayhi`)؛ والصلاتُ بين عُقَد المالك أربعٌ بعينها (`silat_malik_arba`)، وإسقاطُها على الجذور خمسُ صلات
    (`isqat_khams`): الزائدةُ درس–كتب جاءت من «المدارس» (س115082) لا من عقدة «درس» (`dars_la_yasil`)، و«مقلمة ← الكتيبة» (س237970) صلةٌ
    بين جذرَي قلم وكتب لا بين عقدتَي المالك (`katiba_laysat_kitaba`). الشواهدُ بسطر اللسان لا بممثّل العقدة. بلا sorry ولا axiom ولا native_decide.
-/
import Madlul.IshtirakData

namespace Ishtirak

/-- قسمةُ سيبويه (والهويّة): اللفظُ صيغتُه ومعناه. -/
inductive Alaqa | huwiyya | ishtirak | taraduf | tabayun
  deriving DecidableEq, Repr

structure Lafz where
  sigha : String
  mana : Nat
  deriving DecidableEq, Repr

def alaqa (a b : Lafz) : Alaqa :=
  if a.sigha = b.sigha then (if a.mana = b.mana then .huwiyya else .ishtirak)
  else (if a.mana = b.mana then .taraduf else .tabayun)

theorem ishtirak_iff (a b : Lafz) : alaqa a b = .ishtirak ↔ a.sigha = b.sigha ∧ a.mana ≠ b.mana := by
  unfold alaqa; split <;> split <;> simp_all

theorem taraduf_iff (a b : Lafz) : alaqa a b = .taraduf ↔ a.sigha ≠ b.sigha ∧ a.mana = b.mana := by
  unfold alaqa; split <;> split <;> simp_all

theorem alaqa_tanazur (a b : Lafz) : alaqa a b = alaqa b a := by
  unfold alaqa
  by_cases h1 : a.sigha = b.sigha <;> by_cases h2 : a.mana = b.mana <;> simp [h1, h2, eq_comm]

/-- القسمة حاصرة: كلُّ زوجٍ في قسمٍ واحدٍ من الأربعة. -/
theorem alaqa_hasira (a b : Lafz) :
    alaqa a b = .huwiyya ∨ alaqa a b = .ishtirak ∨ alaqa a b = .taraduf ∨ alaqa a b = .tabayun := by
  unfold alaqa; split <;> split <;> simp

/-- شواهدُ سيبويه بأرقام معانٍ معلنة: وجد/موجدة 1، وجد/وجدان 2، ذهب 3، انطلق 3، جلس 4. -/
theorem shawahid_sibawayhi :
    alaqa ⟨"وجد", 1⟩ ⟨"وجد", 2⟩ = .ishtirak ∧ alaqa ⟨"ذهب", 3⟩ ⟨"انطلق", 3⟩ = .taraduf ∧
    alaqa ⟨"جلس", 4⟩ ⟨"ذهب", 3⟩ = .tabayun := by decide

/-! ## الشبكة على العُقَد -/

abbrev Uqda := String × String

def silaUqad : List (Uqda × Uqda) := silatHiss.map fun e => ((e.1, e.2.1), (e.2.2.1, e.2.2.2.1))

def mubashir (E : List (Uqda × Uqda)) (x y : Uqda) : Bool := E.any fun p => p == (x, y) || p == (y, x)

def isqat (E : List (Uqda × Uqda)) : List (String × String) := E.map fun p => (p.1.1, p.2.1)

def mubashirJ (E : List (String × String)) (x y : String) : Bool := E.any fun p => p == (x, y) || p == (y, x)

/-- صلةُ العُقَد تُسقَط على جذريهما (لكلّ جدول). -/
theorem isqat_yahfaz (E : List (Uqda × Uqda)) (x y : Uqda) (h : mubashir E x y = true) :
    mubashirJ (isqat E) x.1 y.1 = true := by
  unfold mubashir at h
  unfold mubashirJ isqat
  obtain ⟨p, hp, hxy⟩ := List.any_eq_true.mp h
  refine List.any_eq_true.mpr ⟨(p.1.1, p.2.1), List.mem_map.mpr ⟨p, hp, rfl⟩, ?_⟩
  rcases Bool.or_eq_true_iff.mp hxy with h1 | h1 <;> simp at h1 <;> subst h1 <;> simp

def malik (r : String) : Uqda := (r, ((uqadMalik.find? (·.1 == r)).map (·.2)).getD "")

def sabaa : List String := ["كتب", "درس", "قلم", "علم", "فهم", "طلب", "عقل"]

def azwaj : List (String × String) :=
  (sabaa.zip (List.range 7)).flatMap fun (a, i) => (sabaa.drop (i + 1)).map fun b => (a, b)

/-- الصلاتُ المباشرة بين عُقَد المالك أربعٌ بعينها: كتب–قلم، كتب–علم، علم–فهم، فهم–عقل. -/
theorem silat_malik_arba :
    azwaj.filter (fun p => mubashir silaUqad (malik p.1) (malik p.2)) =
      [("كتب", "قلم"), ("كتب", "علم"), ("علم", "فهم"), ("فهم", "عقل")] := by decide

/-- وإسقاطُها على الجذور خمسُ صلات: تزيد درس–كتب. -/
theorem isqat_khams :
    azwaj.filter (fun p => mubashirJ (isqat silaUqad) p.1 p.2) =
      [("كتب", "درس"), ("كتب", "قلم"), ("كتب", "علم"), ("علم", "فهم"), ("فهم", "عقل")] := by decide

/-- الصلةُ المشهودة في سطرٍ من اللسان: (عقدة، عقدة). -/
def silaFi (n : Nat) : Option (Uqda × Uqda) :=
  (silatHiss.find? (·.2.2.2.2 == n)).map fun e => ((e.1, e.2.1), (e.2.2.1, e.2.2.2.1))

/-- لا تصل بين عقدتَي المالك لجذريها. -/
def bayna_malik (o : Option (Uqda × Uqda)) : Bool :=
  match o with
  | some (x, y) => x == malik x.1 && y == malik y.1
  | none => false

/-- صلةُ درس–كتب (س115082 «والمدارس: الذي قرأ الكتب ودرسها») بين جذرَي درس وكتب، لا من عقدة «درس» نفسِها
    (وهي في اللسان معنى العفاء: «درس الرسم: عفا»)؛ ولا صلةَ بين عقدتَي المالك لهما. -/
theorem dars_la_yasil : mubashir silaUqad (malik "درس") (malik "كتب") = false ∧
    ((silaFi 115082).map fun p => (p.1.1, p.2.1)) = some ("درس", "كتب") ∧ bayna_malik (silaFi 115082) = false := by decide

/-- «وألف مقلمة: يعني الكتيبة» (س237970): صلةٌ بين جذرَي قلم وكتب، لا بين عقدتَي المالك. -/
theorem katiba_laysat_kitaba : ((silaFi 237970).map fun p => (p.1.1, p.2.1)) = some ("قلم", "كتب") ∧
    bayna_malik (silaFi 237970) = false := by decide

end Ishtirak
