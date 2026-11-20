import A116.Hadd

/-!
# التقاءُ الساكنين على الحدّ: ما يفعله الوصلُ بآخر الكلمة الأولى

على حدّ الكلمتين قد يلتقي ساكنٌ آخرَ الأولى بساكنٍ أوّلَ الثانية (فِي + الْأَرْضِ ← `فِ يْ | لْ ءَ`؛
لُوطٍ + الْمُرْسَلُونَ ← `طِ نْ | لْ مُ`)، والمدوّنةُ المختومة لا تكتب ما يحدث عندئذٍ لأنّه ليس من رسم
الكلمة الواحدة. فكان ذلك رفضًا مسمًّى (`JUNCTION_NOT_LICENSED`، `CVVC_NOT_GEMINATE`،
`CVVC_ACROSS_WORD_BOUNDARY`)، لا تقصيرَ ولا كسرةَ تخمينًا (دَين `JUNCTION_SHORTENING`).

هذه الوحدةُ تسمّي **ثلاثةَ أوجهٍ لا رابعَ لها** يعمل بها الوصلُ في آخر الكلمة الأولى وحدَها، بترتيبٍ لا
يُبدَّل، وتُبرهن خواصَّها — والكلمةُ الثانيةُ لا تُمسّ، وشهادتُها شهادةُ ذرّاتها كما هي:

1. **الألفُ الفارقة تسقط** (`farqAlifDropped`): (و،ضمّ) ثمّ (ا،سكون) في الآخر — ألفٌ ساكنةٌ ليست مدًّا
   (صنفُها `c`) فلا نطقَ لها (اشْتَرَوُا + الضَّلَالَةَ).
2. **حرفُ المدّ يُحذف** (`maddDropped`): آخرُ الأولى `v` (الكتاب: «تذهب … لالتقاء الساكنين» ج3 س14295،
   «تحذف الياء لالتقاء الساكنين» س14719، «لا يكون بعد الألف حرف ساكن ليس بمدغم» س14318 — JK006989
   المختوم في SLGE).
3. **الساكنُ يُكسَر** (`sakinKasra`): «هذا باب تحرك أواخر الكلم الساكنة إذا حذفت ألف الوصل لالتقاء
   الساكنين … فجملة هذا الباب في التحرك أن يكون الساكن الأول مكسورا … لأن التنوين ساكن وقع بعده حرف ساكن»
   (س17595–17602). والمدوّنةُ تكتب هذا التحريكَ على الكلمة (قُلِ، مِنَ) إلّا على التنوين، فلا يفيض الوجهُ
   على مكتوب.

ما يُبرهَن: لا تصرّفَ بلا التقاء (`repair_noop_of_right_vowel`، `repair_noop_of_left_vowel`)؛ بعد كلّ وجهٍ
آخرُ الأولى متحرّكٌ فلا التقاءَ باقٍ (`repaired_ends_vowel`) والوصلُ ثابتٌ على ما أصلحه (`repair_fixed`)؛
الأصنافُ تُحسب موضعًا موضعًا فما قبل الحدّ لا يتغيّر بما بعده (`kindGo_append`)، وبعد الإصلاح لا قافيةَ مدٍّ
يقطعها الحدّ (`straddles_repaired_false`)؛ والطولُ ينقص خانةً على الأكثر (`repair_length`). والشواهدُ
الأربعةُ من المدوّنة بأوجهها، والطفراتُ: لا إصلاحَ قبل متحرّك، ولا للحروف المقطّعة (الر + تِلْكَ).

ولا يُبرهَن هنا أنّ هذه الأوجهَ هي أوجهُ العربيّة: Lean يُبرهن خواصَّ التعريف، والمطابقةُ للمرويّ (الكتاب)
معلَنةٌ بمواضعها، وأثرُها على المدوّنة مقيسٌ (`gen_context_certificates.py`).
-/

namespace A116.Iltiqa

open A116 A116.Stages A116.Hadd A116.Ladder

/-- أوجهُ الوصل في آخر الأولى. -/
inductive Repair | farqAlifDropped | maddDropped | sakinKasra
  deriving DecidableEq, Repr

def startsSukun : List Cell → Bool
  | x :: _ => x.haraka == .sukun
  | [] => false

def endsSukun (l : List Cell) : Bool :=
  match l.getLast? with
  | some a => a.haraka == .sukun
  | none => false

/-- الألفُ الفارقة: (و،ضمّ) ثمّ (ا،سكون) في الآخر. -/
def endsFarqAlif (l : List Cell) : Bool :=
  l.getLast? == some (atom 'ا' .sukun) && l.dropLast.getLast? == some (atom 'و' .damma)

def lastKind (l : List Cell) : Option K := (kindOf l).getLast?

/-- الإصلاحُ على آخر الأولى عند التقاء ساكنين على الحدّ، وإلّا لا شيء. -/
def repair (l r : List Cell) : List Cell × Option Repair :=
  if !(startsSukun r && endsSukun l) then (l, none)
  else if endsFarqAlif l then (l.dropLast, some .farqAlifDropped)
  else if lastKind l == some .v then (l.dropLast, some .maddDropped)
  else
    match l.getLast? with
    | some a => (l.dropLast ++ [⟨a.carrier, .kasra⟩], some .sakinKasra)
    | none => (l, none)

/-- الوصلُ بقيد الحدّ بعد الإصلاح. -/
def strictJoinRepairedB (l r : List Cell) : Bool := strictJoinB (repair l r).1 r
def strictJoinPauseRepairedB (l r : List Cell) : Bool := strictJoinPauseB (repair l r).1 r

/-! ## لا تصرّفَ بلا التقاء -/

theorem repair_noop_of_right_vowel (l r : List Cell) (h : startsSukun r = false) :
    repair l r = (l, none) := by
  simp [repair, h]

theorem repair_noop_of_left_vowel (l r : List Cell) (h : endsSukun l = false) :
    repair l r = (l, none) := by
  simp [repair, h]

/-! ## الأصنافُ تُحسب موضعًا موضعًا -/

theorem kindGo_append : ∀ (p : Option Haraka) (a b : List Cell),
    kindGo p (a ++ b) = kindGo p a ++ kindGo (lastH p a) b
  | _, [], _ => rfl
  | p, x :: t, b => by simp [kindGo, lastH, kindGo_append (some x.haraka) t b]

theorem lastH_snoc (p : Option Haraka) (l : List Cell) (a : Cell) :
    lastH p (l ++ [a]) = some a.haraka := by
  induction l generalizing p with
  | nil => rfl
  | cons x t ih => simp [lastH, ih]

theorem dropLast_append_of_getLast? : ∀ {l : List Cell} {a : Cell},
    l.getLast? = some a → l.dropLast ++ [a] = l
  | [], _, h => by simp at h
  | [x], a, h => by simp at h; simp [h]
  | x :: y :: t, a, h => by
    have ih := dropLast_append_of_getLast? (l := y :: t) (a := a) (by simpa using h)
    simpa [List.dropLast] using ih

theorem lastH_of_getLast? {l : List Cell} {a : Cell} (p : Option Haraka) (h : l.getLast? = some a) :
    lastH p l = some a.haraka := by
  rw [← dropLast_append_of_getLast? h, lastH_snoc]

theorem maddVowel_ne_sukun {k : Fin carrierCount} {b : Haraka} (h : maddVowel k = some b) :
    b ≠ .sukun := by
  unfold maddVowel at h
  split at h
  · simp only [Option.some.injEq] at h; subst h; decide
  · split at h
    · simp only [Option.some.injEq] at h; subst h; decide
    · split at h
      · simp only [Option.some.injEq] at h; subst h; decide
      · simp at h

/-- صنفُ `v` لا يقع إلّا بعد متحرّك: الخانةُ قبل حرف المدّ حركتُها حركتُه المجانسة. -/
theorem kindOne_v_prev {p : Option Haraka} {x : Cell} (h : kindOne p x = .v) :
    ∃ v, p = some v ∧ v ≠ .sukun := by
  unfold kindOne at h
  split at h
  · exact absurd h (by decide)
  · revert h
    cases p with
    | none => intro h; simp at h
    | some a =>
      cases hm : maddVowel x.carrier with
      | none => intro h; simp at h
      | some b =>
        intro h
        dsimp only at h
        split at h <;> rename_i hab
        · subst hab; exact ⟨a, rfl, maddVowel_ne_sukun hm⟩
        · simp at h

/-! ## بعد الإصلاح آخرُ الأولى متحرّك -/

/-- آخرُ السلسلة موجودٌ ومتحرّك. -/
def EndsVowel (l : List Cell) : Prop := ∃ p, l.getLast? = some p ∧ p.haraka ≠ .sukun

theorem endsSukun_false_of_endsVowel {l : List Cell} (h : EndsVowel l) : endsSukun l = false := by
  obtain ⟨p, hp, hs⟩ := h
  simp [endsSukun, hp, hs]

theorem ne_nil_of_endsVowel {l : List Cell} (h : EndsVowel l) : l ≠ [] := by
  obtain ⟨p, hp, _⟩ := h
  intro he; subst he; simp at hp

/-- حرفُ المدّ في الآخر مسبوقٌ بمتحرّك: ما قبله حركتُه ليست سكونًا. -/
theorem madd_last_prev_vowel {l : List Cell} {a : Cell} (ha : l.getLast? = some a)
    (hv : lastKind l = some .v) : EndsVowel l.dropLast := by
  have hl := dropLast_append_of_getLast? ha
  unfold lastKind kindOf at hv
  rw [← hl, kindGo_snoc] at hv
  simp only [List.getLast?_append, List.getLast?_singleton, Option.some_or, Option.some.injEq] at hv
  obtain ⟨v, hp, hvs⟩ := kindOne_v_prev hv
  rcases hd : l.dropLast.getLast? with _ | p
  · have : l.dropLast = [] := List.getLast?_eq_none_iff.1 hd
    rw [this] at hp; simp [lastH] at hp
  · refine ⟨p, hd, ?_⟩
    rw [lastH_of_getLast? none hd] at hp
    simp only [Option.some.injEq] at hp
    rw [hp]; exact hvs

/-- الإصلاحُ أحدُ أربعة لا خامسَ لها. -/
theorem repair_eq (l r : List Cell) :
    repair l r = (l, none) ∨
    (endsFarqAlif l = true ∧ repair l r = (l.dropLast, some .farqAlifDropped)) ∨
    (lastKind l = some .v ∧ repair l r = (l.dropLast, some .maddDropped)) ∨
    (∃ a, l.getLast? = some a ∧
      repair l r = (l.dropLast ++ [⟨a.carrier, .kasra⟩], some .sakinKasra)) := by
  unfold repair
  split
  · exact Or.inl rfl
  · split <;> rename_i hf
    · exact Or.inr (Or.inl ⟨hf, rfl⟩)
    · split <;> rename_i hv
      · exact Or.inr (Or.inr (Or.inl ⟨by simpa using hv, rfl⟩))
      · split <;> rename_i a ha
        · exact Or.inr (Or.inr (Or.inr ⟨a, ha, rfl⟩))
        · exact Or.inl rfl

theorem repaired_endsVowel (l r : List Cell) (t : Repair) (h : (repair l r).2 = some t) :
    EndsVowel (repair l r).1 := by
  rcases repair_eq l r with h0 | ⟨hf, he⟩ | ⟨hv, he⟩ | ⟨a, ha, he⟩
  · rw [h0] at h; simp at h
  · rw [he]
    simp only [endsFarqAlif, Bool.and_eq_true, beq_iff_eq] at hf
    exact ⟨atom 'و' .damma, hf.2, by show Haraka.damma ≠ .sukun; decide⟩
  · rw [he]
    cases hl : l.getLast? with
    | none =>
      have : l = [] := List.getLast?_eq_none_iff.1 hl
      subst this; simp [lastKind, kindOf, kindGo] at hv
    | some a => exact madd_last_prev_vowel hl hv
  · rw [he]
    exact ⟨⟨a.carrier, .kasra⟩, by simp, by show Haraka.kasra ≠ .sukun; decide⟩

theorem repaired_ends_vowel (l r : List Cell) (t : Repair) (h : (repair l r).2 = some t) :
    endsSukun (repair l r).1 = false :=
  endsSukun_false_of_endsVowel (repaired_endsVowel l r t h)

/-- الوصلُ ثابتٌ على ما أصلحه: إصلاحُ المُصلَح لا شيء. -/
theorem repair_fixed (l r : List Cell) (t : Repair) (h : (repair l r).2 = some t) :
    repair (repair l r).1 r = ((repair l r).1, none) :=
  repair_noop_of_left_vowel _ _ (repaired_ends_vowel l r t h)

/-! ## لا قافيةَ مدٍّ يقطعها الحدّ بعد الإصلاح -/

theorem kindOne_cv {p : Option Haraka} {x : Cell} (h : x.haraka ≠ .sukun) : kindOne p x = .cv := by
  simp [kindOne, h]

/-- إن كان آخرُ الأولى متحرّكًا فلا `v` قبل الحدّ ولا `c` عنده بعد `v`. -/
theorem straddles_false_of_endsVowel (l r : List Cell) (hl : EndsVowel l) : straddles l r = false := by
  obtain ⟨a, ha, has⟩ := hl
  obtain ⟨l0, rfl⟩ : ∃ l0, l = l0 ++ [a] := ⟨l.dropLast, (dropLast_append_of_getLast? ha).symm⟩
  have hk : kindOf (l0 ++ [a] ++ r) = kindOf l0 ++ [K.cv] ++ kindGo (some a.haraka) r := by
    rw [kindOf, kindGo_append, kindGo_append, lastH_snoc]
    simp [kindOf, kindGo, kindOne_cv (p := lastH none l0) has]
  have hlen : (kindOf l0).length = l0.length := kindGo_length none l0
  have h1 : (kindOf (l0 ++ [a] ++ r))[(l0 ++ [a]).length - 1]? = some K.cv := by
    rw [hk, List.length_append, List.length_singleton, Nat.add_sub_cancel, List.append_assoc,
      List.getElem?_append_right (by omega)]
    simp [hlen]
  simp only [straddles, h1]
  simp

theorem straddles_repaired_false (l r : List Cell) (t : Repair) (h : (repair l r).2 = some t) :
    straddles (repair l r).1 r = false :=
  straddles_false_of_endsVowel _ _ (repaired_endsVowel l r t h)

/-! ## الطول -/

theorem repair_length (l r : List Cell) :
    l.length - 1 ≤ (repair l r).1.length ∧ (repair l r).1.length ≤ l.length := by
  unfold repair
  split
  · simp
  · split
    · simp
    · split
      · simp
      · split
        · rename_i a ha
          have hne : l ≠ [] := by intro he; subst he; simp at ha
          have hpos : 0 < l.length := List.length_pos_iff.2 hne
          simp only [List.length_append, List.length_dropLast, List.length_singleton]; omega
        · simp

/-! ## الشواهد من المدوّنة (بالحساب على خاناتٍ مسمّاة) -/

theorem cited_letters_are_carriers :
    ['ف', 'ي', 'ل', 'ء', 'ر', 'ض', 'س', 'م', 'ا', 'ش', 'ت', 'و', 'ط', 'ن', 'ق', 'ح', 'د', 'ك',
     'ع'].all (Field112.carriers29.contains ·) = true := by
  decide

open Haraka in
/-- فِي: `فِ يْ`. -/
def fi : List Cell := [atom 'ف' kasra, atom 'ي' sukun]
open Haraka in
/-- الْأَرْضِ موصولةً: `لْ ءَ رْ ضِ`. -/
def lardi : List Cell := [atom 'ل' sukun, atom 'ء' fatha, atom 'ر' sukun, atom 'ض' kasra]
open Haraka in
/-- إِلَى: `ءِ لَ اْ`. -/
def ila : List Cell := [atom 'ء' kasra, atom 'ل' fatha, atom 'ا' sukun]
open Haraka in
/-- السَّمَاءِ موصولةً: `سْ سَ مَ اْ ءِ`. -/
def ssamai : List Cell :=
  [atom 'س' sukun, atom 'س' fatha, atom 'م' fatha, atom 'ا' sukun, atom 'ء' kasra]
open Haraka in
/-- اشْتَرَوُا ابتداءً: `ءِ شْ تَ رَ وُ اْ` (الألفُ الفارقة خانةٌ ساكنةٌ صنفُها `c`). -/
def ishtarawu : List Cell :=
  [atom 'ء' kasra, atom 'ش' sukun, atom 'ت' fatha, atom 'ر' fatha, atom 'و' damma, atom 'ا' sukun]
open Haraka in
/-- الضَّلَالَةَ موصولةً: `ضْ ضَ لَ اْ لَ تَ`. -/
def ddalalata : List Cell :=
  [atom 'ض' sukun, atom 'ض' fatha, atom 'ل' fatha, atom 'ا' sukun, atom 'ل' fatha, atom 'ت' fatha]
open Haraka in
/-- لُوطٍ: `لُ وْ طِ نْ` (التنوينُ نونٌ ساكنة). -/
def lutin : List Cell := [atom 'ل' damma, atom 'و' sukun, atom 'ط' kasra, atom 'ن' sukun]
open Haraka in
/-- الْمُرْسَلُونَ موصولةً موقوفًا عليها: `لْ مُ رْ سَ لُ وْ نْ`. -/
def lmursalun : List Cell :=
  [atom 'ل' sukun, atom 'م' damma, atom 'ر' sukun, atom 'س' fatha, atom 'ل' damma, atom 'و' sukun,
    atom 'ن' sukun]
open Haraka in
/-- قُلِ: `قُ لِ`. -/
def quli : List Cell := [atom 'ق' damma, atom 'ل' kasra]
open Haraka in
/-- الْحَمْدُ موصولةً: `لْ حَ مْ دُ`. -/
def lhamdu : List Cell := [atom 'ل' sukun, atom 'ح' fatha, atom 'م' sukun, atom 'د' damma]
open Haraka in
/-- يَوْمِ: `يَ وْ مِ` (يبدأ بمتحرّك). -/
def yawmi : List Cell := [atom 'ي' fatha, atom 'و' sukun, atom 'م' kasra]
open Haraka in
/-- الر (بعد إصلاح الرسم): `ءَ لْ رْ` — حروفٌ مقطّعة؛ ليست من هذا الباب. -/
def alr : List Cell := [atom 'ء' fatha, atom 'ل' sukun, atom 'ر' sukun]
open Haraka in
/-- تِلْكَ: `تِ لْ كَ`. -/
def tilka : List Cell := [atom 'ت' kasra, atom 'ل' sukun, atom 'ك' fatha]

/-- **الدَّينُ المسمّى مسدود (المدّ):** فِي + الْأَرْضِ مرفوضٌ بلا إصلاح (قافيةُ مدٍّ غيرُ مدغمة) ومقبولٌ
بحذف الياء، والإصلاحُ مسمًّى. -/
theorem fi_lardi :
    strictJoinB fi lardi = false ∧ (repair fi lardi).2 = some .maddDropped ∧
    (repair fi lardi).1 = [atom 'ف' .kasra] ∧ strictJoinRepairedB fi lardi = true := by
  refine ⟨?_, by decide, by decide, ?_⟩
  · have hk : kindOf (fi ++ lardi) = flat .none [.CVVC, .CVC, .CV] := by decide
    simp only [strictJoinB, strictB, hk, continueB_flat]; decide
  · have hk : kindOf ((repair fi lardi).1 ++ lardi) = flat .none [.CVC, .CVC, .CV] := by decide
    simp only [strictJoinRepairedB, strictJoinB, strictB, hk, continueB_flat]; decide

/-- إِلَى + السَّمَاءِ: المدُّ في الأولى والمدغمُ في الثانية (كان `CVVC_ACROSS_WORD_BOUNDARY`) — بحذف الألف
مقبول. -/
theorem ila_ssamai :
    strictJoinB ila ssamai = false ∧ (repair ila ssamai).2 = some .maddDropped ∧
    strictJoinRepairedB ila ssamai = true := by
  refine ⟨?_, by decide, ?_⟩
  · have hk : kindOf (ila ++ ssamai) = flat .none [.CV, .CVVC, .CV, .CVV, .CV] := by decide
    simp only [strictJoinB, strictB, hk, continueB_flat]; decide
  · have hk : kindOf ((repair ila ssamai).1 ++ ssamai) = flat .none [.CV, .CVC, .CV, .CVV, .CV] := by
      decide
    simp only [strictJoinRepairedB, strictJoinB, strictB, hk, continueB_flat]; decide

/-- **الألفُ الفارقة:** اشْتَرَوُا + الضَّلَالَةَ مرفوضٌ بلا إصلاح (ساكنان ثمّ ثالث) ومقبولٌ بإسقاطها. -/
theorem ishtarawu_ddalalata :
    strictJoinB ishtarawu ddalalata = false ∧
    (repair ishtarawu ddalalata).2 = some .farqAlifDropped ∧
    strictJoinRepairedB ishtarawu ddalalata = true := by
  refine ⟨?_, by decide, ?_⟩
  · have hk : kindOf (ishtarawu ++ ddalalata) =
        flat .none [.CVC, .CV, .CV, .CVCC, .CV, .CVV, .CV, .CV] := by decide
    simp only [strictJoinB, strictB, hk, continueB_flat]; decide
  · have hk : kindOf ((repair ishtarawu ddalalata).1 ++ ddalalata) =
        flat .none [.CVC, .CV, .CV, .CVC, .CV, .CVV, .CV, .CV] := by decide
    simp only [strictJoinRepairedB, strictJoinB, strictB, hk, continueB_flat]; decide

/-- **التنوينُ يُكسَر:** لُوطٍ + الْمُرْسَلُونَ (وقفًا) مرفوضٌ بلا إصلاح (`NOT_PAUSE_LICENSED`: ساكنان
داخليّان) ومقبولٌ بكسر النون، وصلًا ووقفًا. -/
theorem lutin_lmursalun :
    strictJoinPauseB lutin lmursalun = false ∧ (repair lutin lmursalun).2 = some .sakinKasra ∧
    (repair lutin lmursalun).1.getLast? = some (atom 'ن' .kasra) ∧
    strictJoinPauseRepairedB lutin lmursalun = true ∧
    strictJoinRepairedB lutin (lmursalun.dropLast ++ [atom 'ن' .fatha]) = true := by
  refine ⟨?_, by decide, by decide, ?_, ?_⟩
  · have hk : kindOf (lutin ++ lmursalun) = flat .none [.CVV, .CVCC, .CVC, .CV, .CVVC] := by decide
    simp only [strictJoinPauseB, strictPauseB, Ternary.pauseB, hk, parse_flat]; decide
  · have hk : kindOf ((repair lutin lmursalun).1 ++ lmursalun) =
        flat .none [.CVV, .CV, .CVC, .CVC, .CV, .CVVC] := by decide
    simp only [strictJoinPauseRepairedB, strictJoinPauseB, strictPauseB, Ternary.pauseB, hk,
      parse_flat]; decide
  · have hk : kindOf ((repair lutin (lmursalun.dropLast ++ [atom 'ن' .fatha])).1 ++
        (lmursalun.dropLast ++ [atom 'ن' .fatha])) =
        flat .none [.CVV, .CV, .CVC, .CVC, .CV, .CVV, .CV] := by decide
    simp only [strictJoinRepairedB, strictJoinB, strictB, hk, continueB_flat]; decide

/-- **الطفراتُ المرفوضة:** لا إصلاحَ قبل متحرّك (فِي + يَوْمِ)، ولا بعد متحرّك (قُلِ + الْحَمْدُ)، ولا
للحروف المقطّعة (الر + تِلْكَ: الساكنان في الأولى نفسِها فيبقى الرفض). -/
theorem no_repair_without_clash :
    repair fi yawmi = (fi, none) ∧ repair quli lhamdu = (quli, none) ∧
    repair alr tilka = (alr, none) ∧ strictJoinRepairedB alr tilka = false ∧
    strictJoinRepairedB quli lhamdu = true := by
  refine ⟨by decide, by decide, by decide, ?_, ?_⟩
  · have hk : kindOf ((repair alr tilka).1 ++ tilka) = flat .none [.CVCC, .CVC, .CV] := by decide
    simp only [strictJoinRepairedB, strictJoinB, strictB, hk, continueB_flat]; decide
  · have hk : kindOf ((repair quli lhamdu).1 ++ lhamdu) = flat .none [.CV, .CVC, .CVC, .CV] := by
      decide
    simp only [strictJoinRepairedB, strictJoinB, strictB, hk, continueB_flat]; decide

end A116.Iltiqa
