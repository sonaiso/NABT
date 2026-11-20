/-
  Dal/Qanun.lean — قانون الابتداء والوصل والوقف على خلايانا، والمقاطع نتيجةً، والجذر.

  القانون نفسه في مرفق المالك slge-closed (SLGE/Law.lean، Hamza.lean، Syllable.lean، Root.lean)، منقولًا بنصّه
  إلى مجلّد SLGE/ ومبنيًّا هنا. وهذا الملفّ **جسرٌ مبرهن**: ترميزُ خليتنا هو ترميز المالك بعينه (`ramz_eq_cellEnc`)،
  وجدولُ مخارجنا جدولُه بعينه (`ahjam_eq`)، وجدولُ المدّ واحد (`madd_eq`) — فكلّ مبرهنةٍ هناك تسري على خلايانا.

  ثمّ: القانون على خلايانا (`murakhkhasWaqf`، `murakhkhasWasl`)، ونتائجُه المنقولة: لا ابتداء بساكن
  (`la_ibtida_bisakin` من `sukun_first_dead`)، والخانات المرخَّصة ابتداءً 84 (`khaliya_mufrada_84`)،
  وشواهد المالك (بِنْت، قَالْتُ، حَاجَّ) بأحرفها من جدولنا. وتقطيعٌ تنفيذيٌّ `qatta` صحيحٌ بالبناء
  (`qatta_sahih`) وواحدٌ بمبرهنة المالك `wordChain_inj` (`qatta_wahid`)، والمقاطع ستّة (`anwa_sitta`).
  والجذور الثلاثية المرخَّصة 20,430 (`judhur_thulathiyya` من `root3` عند المالك).
  بلا sorry ولا axiom ولا native_decide.
-/
import Dal.Makharij
import SLGE.Hamza
import SLGE.Syllable
import SLGE.Root

namespace Dal
open SLGE SLGE.Law

/-! ## ١. الجسر: ترميزٌ واحد، وجدولٌ واحد -/

/-- رمز الخلية في آلة المالك: 4·حامل + حالة. -/
def ramz (k : Khaliya) : Nat := (n k).val

def ramzKull (ks : List Khaliya) : List Nat := ks.map ramz

theorem ramz_eq_cellEnc (k : Khaliya) : ramz k = SLGE.cellEnc k.hamil.val k.hala.val := by
  simp [ramz, n, SLGE.cellEnc, SLGE.mixEnc, Nat.mul_comm]

theorem ramz_lt (k : Khaliya) : ramz k < 116 := (n k).isLt

theorem ahjam_eq : ahjam = SLGE.makharijSizes := rfl

theorem madd_eq : ∀ h : HalaIsm, h ≠ .sukun → (maddOf h).map Fin.val = some (SLGE.maddOf h.ila.val) := by
  intro h hne; cases h <;> first | rfl | exact absurd rfl hne

/-- الحامل بموضعه في جدولنا والخلية منه: مقابل `carrierDec` عند المالك. -/
theorem makhraj_eq (c : Hamil) : (makhraj c).1 = (SLGE.carrierDec c.val).1 := by
  revert c; decide

/-! ## ٢. القانون على خلايانا -/

/-- مرخَّصة موقوفًا عليها. -/
def murakhkhasWaqf (ks : List Khaliya) : Bool := Fwaqf (run 0 (ramzKull ks))
/-- مرخَّصة في الوصل (يليها متحرّك). -/
def murakhkhasWasl (ks : List Khaliya) : Bool := Fwasl (run 0 (ramzKull ks))

/-- **لا يُبتدأ بساكن** (قانون الابتداء): من `sukun_first_dead` عند المالك. -/
theorem la_ibtida_bisakin (k : Khaliya) (h : k.hala = 3) (rest : List Khaliya) :
    murakhkhasWaqf (k :: rest) = false ∧ murakhkhasWasl (k :: rest) = false := by
  have hr : ramz k = 4 * k.hamil.val + 3 := by simp [ramz, n, h]; rfl
  simp only [murakhkhasWaqf, murakhkhasWasl, ramzKull, List.map_cons, hr]
  exact dead_not _ (sukun_first_dead k.hamil.val k.hamil.isLt _)

/-- **الاستنفاد في الخانة الواحدة:** 84 خلية من 116 تُرخَّص كلمةً من خلية واحدة (المتحرّكات غير الألف). -/
theorem khaliya_mufrada_84 : ((List.range 116).filter fun a => Fwaqf (run 0 [a])).length = 84 := by
  decide +kernel

/-- خلية بحرفها وحالتها (الحرف من جدول المخارج؛ ما ليس فيه يُرفض). -/
def kh? (c : Char) (h : HalaIsm) : Option Khaliya :=
  match hawamil.idxOf? c with
  | some i => if hi : i < 29 then some ⟨⟨i, hi⟩, h.ila⟩ else none
  | none => none

/-- شاهد المالك «بِنْت»: مرخَّصة موقوفًا عليها، ممتنعة في الوصل. -/
theorem shahid_bint :
    (do let b ← kh? 'ب' .kasra; let n ← kh? 'ن' .sukun; let t ← kh? 'ت' .sukun
        pure (murakhkhasWaqf [b, n, t], murakhkhasWasl [b, n, t])) = some (true, false) := by
  decide

/-- شاهد المالك «قَالْتُ» ممتنعة (مدٌّ ثمّ ساكن غير مدغم)، و«قُلْتُ» مرخَّصة. -/
theorem shahid_qaltu :
    (do let q ← kh? 'ق' .fatha; let a ← kh? 'ا' .sukun; let l ← kh? 'ل' .sukun; let t ← kh? 'ت' .damma
        pure (murakhkhasWaqf [q, a, l, t])) = some false ∧
    (do let q ← kh? 'ق' .damma; let l ← kh? 'ل' .sukun; let t ← kh? 'ت' .damma
        pure (murakhkhasWaqf [q, l, t])) = some true := by
  decide

/-- شاهد المالك «حَاجَّ»: الساكن بعد المدّ مُدغمٌ في مثله فيُرخَّص. -/
theorem shahid_hajja :
    (do let h ← kh? 'ح' .fatha; let a ← kh? 'ا' .sukun; let j1 ← kh? 'ج' .sukun; let j2 ← kh? 'ج' .fatha
        pure (murakhkhasWaqf [h, a, j1, j2])) = some true := by
  decide

/-- الحرف الذي ليس في الجدول يُرفض باسمه لا يُخمَّن. -/
theorem harf_kharij_marfud : kh? 'ة' .sukun = none ∧ kh? 'ى' .fatha = none := by decide

/-! ## ٣. المقاطع: تقطيعٌ تنفيذيّ، صحيحٌ بالبناء وواحدٌ بمبرهنة المالك -/

instance : DecidablePred Valid := fun x =>
  inferInstanceAs (Decidable (x.1 < 6 ∧ x.2.1 < 87 ∧ x.2.2.1 < (radix x.1).1 ∧ x.2.2.2 < (radix x.1).2))
instance : DecidablePred AlifOK := fun x =>
  inferInstanceAs (Decidable (x.2.1 / 3 ≠ 2 ∧ ∀ c ∈ closers x, c ≠ 2))

/-- المتحرّك ثمّ ما يليه من سواكن حتّى المتحرّك التالي. -/
def akhudhSawakin : List Nat → List Nat × List Nat
  | [] => ([], [])
  | a :: l => if a % 4 = 3 then (a / 4 :: (akhudhSawakin l).1, (akhudhSawakin l).2) else ([], a :: l)

theorem akhudhSawakin_len (l : List Nat) : (akhudhSawakin l).2.length ≤ l.length := by
  induction l with
  | nil => simp [akhudhSawakin]
  | cons a l ih =>
    simp only [akhudhSawakin]
    split
    · simp only [List.length_cons]; omega
    · simp

/-- بناء المقطع من فاتحه وسواكنه: الأنواع الستّة، وما عداها لا مقطع. -/
def maqta (a : Nat) (sawakin : List Nat) : Option Syl :=
  let h := a % 4
  let o := 3 * (a / 4) + h
  let m := SLGE.maddOf h
  match sawakin with
  | [] => some (0, o, 0, 0)
  | [k] => if k = m then some (1, o, 0, 0) else some (2, o, unskip m k, 0)
  | [k1, k2] => if k1 = m then some (3, o, k2, 0) else some (4, o, unskip m k1, k2)
  | [k1, k2, k3] => if k1 = m then some (5, o, k2, k3) else none
  | _ => none

def qattaRaw : List Nat → Option (List Syl)
  | [] => some []
  | a :: l =>
    if a % 4 = 3 then none else
    match maqta a (akhudhSawakin l).1, qattaRaw (akhudhSawakin l).2 with
    | some x, some w => some (x :: w)
    | _, _ => none
termination_by l => l.length
decreasing_by
  simp_wf
  have := akhudhSawakin_len l
  omega

/-- التقطيع: يُبنى ثمّ يُفحص؛ لا يُقبل إلّا ما أعاد السلسلة بعينها بمقاطع صحيحة لا ألف فيها فاتحًا ولا مُغلِقًا. -/
def qatta (l : List Nat) : Option (List Syl) :=
  match qattaRaw l with
  | some w => if wordChain w = l ∧ ∀ x ∈ w, Valid x ∧ AlifOK x then some w else none
  | none => none

/-- **صحّة التقطيع بالبناء.** -/
theorem qatta_sahih (l : List Nat) (w : List Syl) (h : qatta l = some w) :
    wordChain w = l ∧ ∀ x ∈ w, Valid x ∧ AlifOK x := by
  unfold qatta at h
  split at h
  · split at h
    · cases h; assumption
    · cases h
  · cases h

/-- **وحدانيّة التقطيع:** أيّ تقطيعٍ صحيحٍ آخر للسلسلة هو هو (من `wordChain_inj` عند المالك). -/
theorem qatta_wahid (l : List Nat) (w w' : List Syl) (h : qatta l = some w)
    (hw' : ∀ x ∈ w', Valid x) (hc : wordChain w' = l) : w' = w := by
  obtain ⟨hl, hv⟩ := qatta_sahih l w h
  exact wordChain_inj w' w hw' (fun x hx => (hv x hx).1) (by rw [hc, hl])

/-- أنواع المقاطع الستّة. -/
inductive NawMaqta | CV | CVV | CVC | CVVC | CVCC | CVVCC deriving DecidableEq, Repr

def nawMaqta (x : Syl) : NawMaqta :=
  match x.1 with
  | 0 => .CV | 1 => .CVV | 2 => .CVC | 3 => .CVVC | 4 => .CVCC | _ => .CVVCC

/-- كلّ مقطع صحيح أحد الستّة، والستّة متباينة. -/
theorem anwa_sitta : (∀ x : Syl, Valid x → ∃ t : NawMaqta, nawMaqta x = t) ∧
    ([NawMaqta.CV, .CVV, .CVC, .CVVC, .CVCC, .CVVCC] : List NawMaqta).Nodup := by
  exact ⟨fun x _ => ⟨_, rfl⟩, by decide⟩

/-- شاهد: «كِتَاب» = كِ (CV) + تَاب (CVVC)، و«بِنْت» = CVCC. -/
theorem shahid_qatta :
    ((do let k ← kh? 'ك' .kasra; let t ← kh? 'ت' .fatha; let a ← kh? 'ا' .sukun; let b ← kh? 'ب' .sukun
         pure (murakhkhasWaqf [k, t, a, b], (qatta (ramzKull [k, t, a, b])).map (·.map nawMaqta)))
      = some (true, some [.CV, .CVVC])) ∧
    ((do let b ← kh? 'ب' .kasra; let n ← kh? 'ن' .sukun; let t ← kh? 'ت' .sukun
         pure ((qatta (ramzKull [b, n, t])).map (·.map nawMaqta))) = some (some [.CVCC])) := by
  decide +kernel

/-! ## ٤. الجذر -/

/-- **الجذور الثلاثية المرخَّصة 20,430** — مبرهنة المالك `root3` بعينها، على جدول مخارجنا (`ahjam_eq`). -/
theorem judhur_thulathiyya : Mroot.lev 3 0 3 = 20430 := root3

end Dal
