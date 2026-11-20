import A116.TawrithBit

/-!
# الاكتسابُ بالأمثلة المضادّة: لغةُ البرامج وعقودُها (ADR ١٢٣)

المتعلّمُ (`tools/gen_iktisab.py`) يعدّد برامجَ هذه اللغة، والمعلّمُ يردّ عليه بأمثلةٍ مضادّة من مواصفةٍ
لا يراها. وهنا ما يجعل البرنامجَ المكتسَب قدرةً مبرهنة لا مطابقةَ أمثلة:

* `nuqati`: اللغةُ **نقطيّة** — البتُّ j من قيمة البرنامج على أعدادٍ طبيعيّة هو قيمتُه على البتّات j منها.
* `min_jadwal`: فإذا صدق البرنامجُ على **جدول بتٍّ واحد** (‎2ᵏ‎ صفًّا، تحت شرط صفٍّ معلَن) صدق على كلّ
  عرضٍ ولكلّ موضع. فالحكمُ على الجدول برهانٌ لكلّ الأعداد، لا عيّنة.
* `subst_eval`: نداءُ المكتبة تعويض، وقيمتُه قيمةُ الجسم على قيم الوسائط — فعقدُ الإجراء المركّب يُبنى من
  عقد المكتسَب السابق دون فتحه (`IktisabAqd.batt_qima_bil_min_naqis`).

المواصفاتُ هنا تعريفاتُ `TawrithBit` القائمة (`batt`، `encQ`، `decQ`، `conflictQ`، `salih`)، فالعقدُ يقيس
المكتسَبَ على ما بُرهن قبله لا على ما كتبه المتعلّم.
-/

set_option autoImplicit false

namespace A116.Iktisab

/-- لغةُ المتعلّم: متغيّرٌ برقمه، صفر، وثلاثُ عمليّات. -/
inductive Ibara where
  | var : Nat → Ibara
  | sifr : Ibara
  | wa : Ibara → Ibara → Ibara
  | aw : Ibara → Ibara → Ibara
  | xor : Ibara → Ibara → Ibara
  deriving DecidableEq, Repr

/-- القيمةُ على بتّات. -/
def evalB (env : List Bool) : Ibara → Bool
  | .var i => env.getD i false
  | .sifr => false
  | .wa a b => evalB env a && evalB env b
  | .aw a b => evalB env a || evalB env b
  | .xor a b => evalB env a ^^ evalB env b

/-- القيمةُ على أعدادٍ طبيعيّة (أقنعةٌ بأيّ عرض). -/
def evalN (env : List Nat) : Ibara → Nat
  | .var i => env.getD i 0
  | .sifr => 0
  | .wa a b => evalN env a &&& evalN env b
  | .aw a b => evalN env a ||| evalN env b
  | .xor a b => evalN env a ^^^ evalN env b

/-- البتّاتُ j من المدخلات. -/
def bitAt (env : List Nat) (j : Nat) : List Bool := env.map (·.testBit j)

theorem getD_bitAt (env : List Nat) (i j : Nat) :
    (bitAt env j).getD i false = (env.getD i 0).testBit j := by
  induction env generalizing i with
  | nil => simp [bitAt, Nat.zero_testBit]
  | cons x xs ih =>
    cases i with
    | zero => simp [bitAt]
    | succ i => simpa [bitAt] using ih i

/-- **اللغةُ نقطيّة.** -/
theorem nuqati (e : Ibara) (env : List Nat) (j : Nat) :
    (evalN env e).testBit j = evalB (bitAt env j) e := by
  induction e with
  | var i => simp only [evalN, evalB]; exact (getD_bitAt env i j).symm
  | sifr => simp [evalN, evalB, Nat.zero_testBit]
  | wa a b iha ihb => simp [evalN, evalB, Nat.testBit_and, iha, ihb]
  | aw a b iha ihb => simp [evalN, evalB, Nat.testBit_or, iha, ihb]
  | xor a b iha ihb => simp [evalN, evalB, Nat.testBit_xor, iha, ihb]

/-- كلُّ صفوف الجدول بطول k. -/
def bools : Nat → List (List Bool)
  | 0 => [[]]
  | n + 1 => (bools n).flatMap fun l => [false :: l, true :: l]

theorem mem_bools : ∀ l : List Bool, l ∈ bools l.length
  | [] => by simp [bools]
  | b :: l => by
    simp only [List.length_cons, bools, List.mem_flatMap]
    exact ⟨l, mem_bools l, by cases b <;> simp⟩

/-- فحصُ الجدول: على كلّ صفٍّ صالح قيمةُ البرنامج هي المواصفة. -/
def jadwal (k : Nat) (valid spec : List Bool → Bool) (e : Ibara) : Bool :=
  (bools k).all fun bs => !valid bs || evalB bs e == spec bs

/-- **من الجدول إلى كلّ عرض:** ما صدق على جدول البتّ الواحد صدق على كلّ أعدادٍ وكلّ موضعٍ صالح. -/
theorem min_jadwal {k : Nat} {valid spec : List Bool → Bool} {e : Ibara}
    (h : jadwal k valid spec e = true) (env : List Nat) (hk : env.length = k) (j : Nat)
    (hv : valid (bitAt env j) = true) :
    (evalN env e).testBit j = spec (bitAt env j) := by
  rw [nuqati]
  have hm : bitAt env j ∈ bools k := by
    have := mem_bools (bitAt env j)
    simpa [bitAt, hk] using this
  have := List.all_eq_true.1 h _ hm
  simpa [hv] using this

/-- نداءُ المكتبة: تعويضُ المتغيّرات بوسائط. -/
def subst : Ibara → List Ibara → Ibara
  | .var i, σ => σ.getD i .sifr
  | .sifr, _ => .sifr
  | .wa a b, σ => .wa (subst a σ) (subst b σ)
  | .aw a b, σ => .aw (subst a σ) (subst b σ)
  | .xor a b, σ => .xor (subst a σ) (subst b σ)

theorem getD_map_evalB (σ : List Ibara) (env : List Bool) (i : Nat) :
    evalB env (σ.getD i .sifr) = (σ.map (evalB env)).getD i false := by
  induction σ generalizing i with
  | nil => simp [evalB]
  | cons x xs ih =>
    cases i with
    | zero => simp
    | succ i => simpa using ih i

/-- **قيمةُ النداء قيمةُ الجسم على قيم الوسائط.** -/
theorem subst_eval (e : Ibara) (σ : List Ibara) (env : List Bool) :
    evalB env (subst e σ) = evalB (σ.map (evalB env)) e := by
  induction e with
  | var i => simp only [subst]; exact getD_map_evalB σ env i
  | sifr => rfl
  | wa a b iha ihb => simp [subst, evalB, iha, ihb]
  | aw a b iha ihb => simp [subst, evalB, iha, ihb]
  | xor a b iha ihb => simp [subst, evalB, iha, ihb]

/-! ## المواصفاتُ من `TawrithBit` -/

open A116.TawrithBit

/-- الناقص موضعًا: مطلوبٌ وليس موجودًا. -/
def specNaqis (bs : List Bool) : Bool := bs.getD 0 false && !bs.getD 1 false

def pairOf (bs : List Bool) (i : Nat) : Bool × Bool := (bs.getD i false, bs.getD (i + 1) false)

/-- قيمةُ البتّ: `batt` على المفكوك ثمّ الترميز (`TawrithBit`). -/
def specBattQima (bs : List Bool) : Bool := (encQ (batt (decQ (pairOf bs 0)) (decQ (pairOf bs 2)))).2

/-- معلومُ البتّ. -/
def specBattMaalum (bs : List Bool) : Bool := (encQ (batt (decQ (pairOf bs 0)) (decQ (pairOf bs 2)))).1

/-- التعارض: قناعُ `conflictQ` بعينه. -/
def specTaarud (bs : List Bool) : Bool := conflictQ (pairOf bs 0) (pairOf bs 2)

/-- شرطُ الصفّ في مهامّ الأزواج: الزوجان صالحان (`salih`). -/
def salihPairs (bs : List Bool) : Bool := salih (pairOf bs 0) && salih (pairOf bs 2)

end A116.Iktisab
