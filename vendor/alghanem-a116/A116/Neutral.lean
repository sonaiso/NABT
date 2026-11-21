import A116.Wazn
import A116.Recovery

/-!
# الألفُ عنصرًا محايدًا: المعتلُّ والمهموزُ والمضعَّفُ في الأوزان، بدالّة آرتين

قرارُ المالك (2026-10-12): «اربط [قواعد الإعلال] بالأوزان، اجعل آرتين يعامل الألف كعنصرٍ محايد».

## المحايد

الألفُ لا تكون إلّا ساكنة (`Alif`)، فلا حالةَ لها تحملها: خانتُها الوحيدةُ المرخَّصة `اْ` (`alif_neutral_unique`)،
والوقفُ لا يغيّرها (`pause_fixes_alif`). وحذفُها `erase` **تشاكلٌ** على الوصل يرسلها إلى المحايد (الكلمة الفارغة):
`erase_append`، `erase_alif`؛ و**كلُّ** تشاكلٍ يرسل الألفَ إلى المحايد يمرّ به (`factor_through_erase`) — وهو
خاصّيّةُ القسمة الكلّيّة، نظيرُ ‎k[x_f] → k[x_f]/M‎ في آرتين.

## التقييمُ بالمحايد (`realizeN`)

التقييمُ في `Wazn` يرسل الأصلَ إلى حامله. وهنا: **الأصلُ الذي لا يقوى على خانته يُقيَّم بالمحايد** — ألفٌ ساكنة
تمتصّ حالتَه — وذلك في موضعين لا ثالثَ لهما هنا:
* **المعتلّ**: عينٌ أو لامٌ واوٌ أو ياء — والعينُ وحدَها إن لم تكن اللامُ معتلّة (اللفيف: هَوَى، أَحْيَا) — تقع في الوزن
  مرّةً واحدة، حالتُه فتحة، بعد فتحة (قَوَلَ ← قَالَ، دَعَوَ ← دَعَا)،
  أو بعد ساكنٍ صحيحٍ فتُنقَل إليه الفتحة (أَقْوَمَ ← أَقَامَ: النقل، `Ilal` القاعدة ٣).
* **المهموز**: همزةٌ أصليّةٌ ساكنةٌ بعد همزةٍ مفتوحة (ءَءْمَنَ ← ءَامَنَ: `Ilal` القاعدة ٧).
والمحايدُ قبل ساكنٍ صحيحٍ غيرِ مدغمٍ يُحذف (`dropNeutral`، `Ilal` القاعدة ٢ الملزَمة)، فيصير الوحدةَ حرفيًّا، وتسقط
همزةُ الوصل إن تحرّك أوّلُ الكلمة بالنقل. و**المضعَّف** (`mergeT`): عينٌ ولامٌ مثلان صحيحان متجاوران في الوزن، يقع المثلُ مرّةً واحدة، والثاني متحرّك — فيُسكَّن الأوّل
ويُدغم، وتُنقَل حركتُه إلى ساكنٍ صحيحٍ قبله (مَدَدَ ← مَدَّ، أَمْدَدَ ← أَمَدَّ).

## ما يُبرهَن

* `neutral_forgets_weak`: قَالَ من (ق و ل) ومن (ق ي ل) خاناتٌ واحدة — المحايدُ يمتصّ الفرق، فالحرفُ المعتلّ
  يُستردّ من البقيّة لا من الخانات (كما يشهد `gate.recover`: قَالَ ← قول، قيل).
* `neutral_identifies_lit_and_radical`: آمَنَ من فاعَلَ (ألفٌ زائدة) ومن أفعَلَ (همزةٌ صارت محايدًا) خاناتٌ واحدة.
* `neutral_restore`: سجلُّ التعديل يردّ الأصلَ من المحايد (`Recovery.edit_roundtrip`).
* `weak_check`/`weak_licensed`: على جذورٍ مرجعيّةٍ لكلّ صنف وعلى الأوزان الإحدى والثلاثين، كلُّ صورةٍ يحسبها
  `realizeN` مرخَّصةٌ بقيد الحدّ ابتداءً وصلًا، وخاناتُها من المرخَّص.
* `neutral_follows_fatha`: كلُّ محايدٍ في الصور المرجعيّة بعد فتحة — «الألفُ لا بدّ لها من حرفٍ قبلها مفتوح».

ولا يُبرهَن هنا أنّ هذا هو إعلالُ العربيّة كلُّه: ما سوى الموضعين (المبنيُّ للمجهول الأجوف، الأمرُ المحذوفُ عينُه أو
لامُه أو فاؤه، إبدالُ الافتعال، الياءُ بعد الكسرة) يبقى أصلُه حرفًا، ويقيسه `tests/test_neutral.py` على البوّابة فجواتٍ
مسمّاة.
-/

set_option autoImplicit false

namespace A116.Neutral

open A116 A116.Stages A116.Ternary A116.Ladder A116.Hadd A116.Boundary A116.Wazn A116.Recovery

/-! ## ١. الألفُ محايد -/

def alifS : Cell := atom 'ا' .sukun

def isAlif (c : Cell) : Bool := c.carrier == carrierOf 'ا'

/-- حذفُ الألف. -/
def erase (w : List Cell) : List Cell := w.filter fun c => !isAlif c

theorem erase_append (a b : List Cell) : erase (a ++ b) = erase a ++ erase b := by
  simp [erase, List.filter_append]

theorem erase_alif (h : Haraka) : erase [⟨carrierOf 'ا', h⟩] = [] := by
  simp [erase, isAlif]

theorem erase_idem (w : List Cell) : erase (erase w) = erase w := by
  simp [erase, List.filter_filter]

/-- **خاصّيّةُ القسمة الكلّيّة**: كلُّ تشاكلٍ على الوصل يرسل الألفَ إلى المحايد يمرّ بـ`erase`. -/
theorem factor_through_erase {β : Type} (g : List Cell → List β)
    (hg : ∀ a b, g (a ++ b) = g a ++ g b) (ha : ∀ h, g [⟨carrierOf 'ا', h⟩] = []) :
    ∀ w, g w = g (erase w) := by
  have g0 : g [] = [] := by
    have h := hg [] []
    rw [List.append_nil] at h
    have hl := congrArg List.length h
    rw [List.length_append] at hl
    exact List.eq_nil_of_length_eq_zero (by omega)
  intro w
  induction w with
  | nil => rfl
  | cons c t ih =>
    have e : c :: t = [c] ++ t := rfl
    rw [e, hg, erase_append, hg, ← ih]
    by_cases hc : isAlif c = true
    · have : c = ⟨carrierOf 'ا', c.haraka⟩ := by
        cases c; simp only [isAlif, beq_iff_eq] at hc; simp [hc]
      have he : erase [c] = [] := by rw [this]; exact erase_alif _
      rw [he, g0, this, ha]
    · have he : erase [c] = [c] := by simp [erase, hc]
      rw [he]

/-- المحايدُ وحيدٌ بين الخانات المرخَّصة، ولا حالةَ له غيرُ السكون. -/
theorem alif_neutral_unique : Alif.licensable.filter isAlif = [alifS] := by decide

/-- الوقفُ لا يغيّر المحايدَ آخرًا. -/
theorem pause_fixes_alif (v : List Cell) : Pause.pause (v ++ [alifS]) = v ++ [alifS] := by
  rw [Pause.pause_snoc]; rfl

/-! ## ٢. التقييمُ بالمحايد -/

def weakCarrier (k : Fin carrierCount) : Bool := k == carrierOf 'و' || k == carrierOf 'ي'

/-- كم مرّةً يقع الأصلُ i في الرموز. -/
def occ (S : List (CSym 3)) (i : Fin 3) : Nat :=
  (S.filter fun s => match s with | .slot j _ => j == i | _ => false).length

def isConsSukun (c : Cell) : Bool := c.haraka == .sukun && (maddVowel c.carrier).isNone

/-- التقييمُ بالمحايد على رمزٍ، والسابقُ في رأس `acc` (معكوسًا). -/
def stepN (r : Root 3) (S : List (CSym 3)) (acc : List Cell) : CSym 3 → List Cell
  | .lit c => c :: acc
  | .slot i h =>
    if r i == hamza && h == .sukun && acc.head? == some ⟨hamza, .fatha⟩ then alifS :: acc
    else if i != 0 && !(i == 1 && weakCarrier (r 2)) && weakCarrier (r i) && occ S i == 1 &&
        h == .fatha then
      match acc with
      | p :: rest =>
        if p.haraka == .fatha then alifS :: acc
        else if isConsSukun p then alifS :: ⟨p.carrier, .fatha⟩ :: rest
        else ⟨r i, h⟩ :: acc
      | [] => [⟨r i, h⟩]
    else ⟨r i, h⟩ :: acc

/-- المحايدُ لا يقف قبل ساكنٍ صحيح (قافيةُ مدٍّ غيرُ مدغمة، `Hadd.geminateB_vc_final`): يُحذف — فيصير المحايدُ
الوحدةَ حرفيًّا (`Ilal.hadhf_ayn_forced`: الأصلُ غيرُ مرخَّص فالحذفُ ملزَم). -/
def dropNeutral : List Cell → List Cell
  | a :: b :: rest =>
    if a == alifS && isConsSukun b && (rest.head?.map (·.carrier) != some b.carrier) then
      b :: dropNeutral rest
    else a :: dropNeutral (b :: rest)
  | l => l

def evalN (r : Root 3) (S : List (CSym 3)) : List Cell :=
  dropNeutral (S.foldl (stepN r S) []).reverse

/-- المضعَّف: إن انتهى الجسمُ بالعين مرّةً واحدة واللامُ مثلُها والثاني متحرّك: تُسكَّن العين، وتُنقَل حركتُها إلى
ساكنٍ صحيحٍ قبلها. -/
def mergeT (r : Root 3) (W : WaznC 3) (hEnd : Haraka) : List (CSym 3) :=
  let S := W.body ++ [.slot W.last hEnd]
  match W.body.reverse with
  | .slot j h' :: before =>
    if r j == r W.last && j != W.last && !weakCarrier (r j) && occ S j == 1 && hEnd != .sukun &&
        h' != .sukun then
      let before' := match before with
        | .slot k .sukun :: more => if weakCarrier (r k) then before else .slot k h' :: more
        | .lit c :: more => if isConsSukun c then .lit ⟨c.carrier, h'⟩ :: more else before
        | _ => before
      before'.reverse ++ [.slot j .sukun, .slot W.last hEnd]
    else S
  | _ => S

/-- الوزنُ في سياقه بالمحايد: الوصلُ ابتداءً من أوّل خانتين ناتجتين، والوقفُ يُسكّن الأخيرة (والمحايدُ ثابت). -/
def realizeN (W : WaznC 3) (r : Root 3) (entry : Entry) (exit : Exit) (h : Haraka) : List Cell :=
  let core := evalN r (mergeT r W h)
  let core := if exit == .pause then Pause.pause core else core
  let pre := match core with
    | c1 :: c2 :: _ =>
      if W.wasl && entry == .start && c1.haraka == .sukun then [⟨hamza, waslVowel c1 c2⟩] else []
    | _ => []
  pre ++ core

/-! ## ٣. الشواهد -/

def rootOf (a b c : Char) : Root 3
  | ⟨0, _⟩ => carrierOf a
  | ⟨1, _⟩ => carrierOf b
  | _ => carrierOf c

def wI : Option (WaznC 3) := thulathi[0]?

/-- **المحايدُ يمتصّ المعتلّ**: قَالَ من (ق و ل) ومن (ق ي ل) خاناتٌ واحدة: قَ اْ لَ. -/
theorem neutral_forgets_weak :
    (wI.map fun W => realizeN W (rootOf 'ق' 'و' 'ل') .start .continue .fatha) =
      some [atom 'ق' .fatha, alifS, atom 'ل' .fatha] ∧
    (wI.map fun W => realizeN W (rootOf 'ق' 'ي' 'ل') .start .continue .fatha) =
      some [atom 'ق' .fatha, alifS, atom 'ل' .fatha] := by
  decide +kernel

/-- **المحايدُ يوحّد الزائدَ والأصليّ**: آمَنَ من فاعَلَ (ألفٌ زائدة) ومن أفعَلَ (همزةٌ صارت محايدًا) خاناتٌ واحدة. -/
theorem neutral_identifies_lit_and_radical :
    ((thulathi[4]?).map fun W => realizeN W (rootOf 'ء' 'م' 'ن') .start .continue .fatha) =
      ((thulathi[5]?).map fun W => realizeN W (rootOf 'ء' 'م' 'ن') .start .continue .fatha) ∧
    ((thulathi[5]?).map fun W => realizeN W (rootOf 'ء' 'م' 'ن') .start .continue .fatha) =
      some [atom 'ء' .fatha, alifS, atom 'م' .fatha, atom 'ن' .fatha] := by
  decide +kernel

/-- **المحايدُ يُردّ بسجلّه**: الألفُ موضعَ الأصل تُستبدل بالأصل بعينه. -/
theorem neutral_restore (l r : List Cell) (radical : Cell) :
    restoreEdit (l ++ ([alifS] ++ r)) ⟨l.length, 1, [radical]⟩ = l ++ [radical] ++ r :=
  edit_roundtrip l _ _ r

/-! ## ٤. الترخيصُ على الأوزان كلِّها بجذورٍ مرجعيّةٍ لكلّ صنف -/

/-- الجذورُ المرجعيّة: أجوفُ واويٌّ ويائيّ، ناقصٌ واويٌّ ويائيّ، مثال، مهموزُ الفاء والعين واللام، مضعَّف، ولفيفان. -/
def refRoots : List (Root 3) :=
  [rootOf 'ق' 'و' 'ل', rootOf 'س' 'ي' 'ر', rootOf 'د' 'ع' 'و', rootOf 'ر' 'م' 'ي', rootOf 'و' 'ع' 'د',
   rootOf 'ء' 'م' 'ن', rootOf 'س' 'ء' 'ل', rootOf 'ق' 'ر' 'ء', rootOf 'م' 'د' 'د', rootOf 'ه' 'و' 'ي',
   rootOf 'ح' 'ي' 'ي']

def neutralFollowsFatha (w : List Cell) : Bool :=
  (w.zip w.tail).all fun (p, c) => !(c == alifS && p.haraka != .fatha)

theorem weak_check :
    refRoots.all (fun r => ((List.range thulathi.length).zip thulathi).all fun (i, W) =>
      let w := realizeN W r .start .continue (lastH i)
      contCheck w && w.all (Alif.licensable.contains ·) && neutralFollowsFatha w) = true := by
  decide +kernel

theorem weak_licensed :
    ∀ r ∈ refRoots, ∀ p ∈ (List.range thulathi.length).zip thulathi,
      strictB (realizeN p.2 r .start .continue (lastH p.1)) = true := by
  intro r hr p hp
  have h := weak_check
  rw [List.all_eq_true] at h
  have h2 := h r hr
  rw [List.all_eq_true] at h2
  have h3 := h2 p hp
  simp only [Bool.and_eq_true] at h3
  exact strictB_of_check h3.1.1

/-- كلُّ محايدٍ في الصور المرجعيّة بعد فتحة. -/
theorem neutral_follows_fatha :
    ∀ r ∈ refRoots, ∀ p ∈ (List.range thulathi.length).zip thulathi,
      neutralFollowsFatha (realizeN p.2 r .start .continue (lastH p.1)) = true := by
  intro r hr p hp
  have h := weak_check
  rw [List.all_eq_true] at h
  have h2 := h r hr
  rw [List.all_eq_true] at h2
  have h3 := h2 p hp
  simp only [Bool.and_eq_true] at h3
  exact h3.2

/-- **اللفيف**: هَوَى (العينُ تبقى واللامُ محايد) وأَحْيَا (المثلان المعتلّان لا يُدغمان، واللامُ محايد). -/
theorem lafif_witnesses :
    (wI.map fun W => realizeN W (rootOf 'ه' 'و' 'ي') .start .continue .fatha) =
      some [atom 'ه' .fatha, atom 'و' .fatha, alifS] ∧
    ((thulathi[5]?).map fun W => realizeN W (rootOf 'ح' 'ي' 'ي') .start .continue .fatha) =
      some [atom 'ء' .fatha, atom 'ح' .sukun, atom 'ي' .fatha, alifS] := by
  decide +kernel

/-- الصحيحُ لا يمسّه المحايد: على الجذر الصحيح `realizeN` هو `realize` بعينه (الأوزانُ كلُّها، الوصلُ والوقف). -/
theorem sound_unchanged :
    ((List.range thulathi.length).zip thulathi).all (fun (i, W) =>
      realizeN W ktb .start .continue (lastH i) == realize W ktb .start .continue (lastH i) &&
      realizeN W ktb .start .pause (lastH i) == realize W ktb .start .pause (lastH i)) = true := by
  decide +kernel

end A116.Neutral
