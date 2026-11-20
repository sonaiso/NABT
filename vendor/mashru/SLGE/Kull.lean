import SLGE.Muwahhad

/-!
# الجملةُ الكلّيّة: نوعٌ واحدٌ يحتوي الأُطرَ كلَّها — والبرهانُ مغلق

**‎UD‎** (الإطارُ الموحَّد بمعطياته كلِّها، وفيه الاستثناءُ التامّ)، و**‎Jumla‎** نوعٌ واحدٌ صوَرُه:
بسيطة، وشرطٌ بجملتين، ونداء، واستفهامٌ بالأسماء، وضميرُ شأن، وموصولٌ بصلته. لكلّ صورةٍ قانونُها من طبقتها
(‎TarkibExt‎) مقرونًا بقانون مكوّناتها (‎uK‎) — فقوانينُ الطبقات كلُّها أجزاءٌ من قانونٍ واحد (‎jOK‎)، ورقمٌ واحد (‎jEnc‎)
يُفكّ منه كلُّ مكوّن (‎j_value‎).

**الاستثناءُ التامّ** (القطر L326–331، الألفيّة L423–425) — حكمٌ مدرَّج (‎2‎ واجب، ‎1‎ راجح، ‎0‎ مرجوح):
* في الموجب: النصبُ واجب؛
* بعد النفي: المتّصلُ يُتبَع بدلًا راجحًا، والنصبُ مرجوح؛ والمنقطعُ نصبٌ واجبٌ عند الحجازيّين، وراجحٌ عند تميم والبدلُ مرجوح؛
* المستثنى المقدَّم على المستثنى منه: في الموجب نصبٌ واجب، وفي النفي «ولكنْ نصبَه اختر»: النصبُ راجح وغيرُه مرجوح.

**السلسلة:** ‎إن لم يكن‎ — فعلُ الشرط ناسخٌ مجزومٌ بلم، والجزمُ في دالِّه من ‎لم‎ وفي محلّه من ‎إن‎؛ ولا يكون فعلُ الشرط
مقرونًا بلن (الألفيّة L911: «جوابًا لو جُعل شرطًا لإنْ … لم ينجعل»).
-/

set_option synthInstance.maxSize 8192
set_option synthInstance.maxHeartbeats 0
set_option maxRecDepth 100000

namespace SLGE
namespace Kull

open Tarkib Maqam Simat Muwahhad

inductive Ist
  | none
  | mufarragh (i : Nat)
  | tamm (minhu st : Nat) (muttasil muqaddam : Bool) (lugha : Nat)
  deriving DecidableEq, Repr

structure UD where
  pre : List Nat
  f : Frame
  ats : List Attr
  ex : List Ext
  outer : Nat := 0
  ist : Ist := .none
  poetry : Bool := false
  nunDel : Bool := false
  nextSakin : Bool := false
  pronAttached : Bool := false
  ws : List (List Nat) := []
  deriving DecidableEq, Repr

/-! ## ١. الاستثناءُ التامّ: حكمٌ مدرَّج -/

/-- (حالةُ المستثنى، درجتُه). ‎badal‎: حالةُ المستثنى منه بموضعه. -/
def verdict (nafy muttasil muqaddam : Bool) (lugha badal : Nat) : List (Nat × Nat) :=
  if !nafy then [(0, 2)]
  else if muqaddam then [(0, 1), (badal, 0)]
  else if muttasil then [(badal, 1), (0, 0)]
  else if lugha == 0 then [(0, 2)] else [(0, 1), (badal, 0)]

def tammOK (pre : List Nat) (f : Frame) (m st : Nat) (mt mq : Bool) (lg : Nat) : Bool :=
  m < f.2.2.length && isNom (f.2.2.getD m (0, 0, 0)).1 && lg ≤ 1 &&
  (verdict (pre.contains 1) mt mq lg ((reqState f.1 f.2.1 (f.2.2.getD m (0, 0, 0)).1).getD 0)).any (·.1 == st)

def grade (pre : List Nat) (f : Frame) (m st : Nat) (mt mq : Bool) (lg : Nat) : Option Nat :=
  ((verdict (pre.contains 1) mt mq lg ((reqState f.1 f.2.1 (f.2.2.getD m (0, 0, 0)).1).getD 0)).find? (·.1 == st)).map (·.2)

/-- **‎قامَ القومُ إلّا زيدًا‎ نصبٌ واجب؛ ‎ما قامَ القومُ إلّا زيدٌ‎ بدلٌ راجح و‎إلّا زيدًا‎ مرجوح؛ ‎ما قامَ القومُ إلّا حمارًا‎ (منقطع)
نصبٌ واجبٌ عند الحجازيّين والرفعُ ممتنع، وعند تميم النصبُ راجحٌ والبدلُ مرجوح؛ ‎ما قامَ إلّا زيدًا القومُ‎ (مقدَّم) النصبُ راجح.** -/
theorem istithna_tamm :
    let f : Frame := (1, 0, [(2, 0, 0), (3, 0, 0)])
    grade [] f 1 0 true false 0 = some 2 ∧ grade [] f 1 1 true false 0 = none ∧
    grade [1] f 1 1 true false 0 = some 1 ∧ grade [1] f 1 0 true false 0 = some 0 ∧
    grade [1] f 1 0 false false 0 = some 2 ∧ grade [1] f 1 1 false false 0 = none ∧
    grade [1] f 1 0 false false 1 = some 1 ∧ grade [1] f 1 1 false false 1 = some 0 ∧
    grade [1] f 1 0 true true 0 = some 1 ∧ grade [] f 1 0 true true 0 = some 2 ∧ grade [] f 1 1 true true 0 = none := by
  decide

/-! ## ٢. الإطارُ الموحَّد بمعطياته -/

def uK (u : UD) : Bool :=
  framesL.contains u.f &&
  match u.ist with
  | .none => uOK u.pre u.f u.ats u.ex u.outer none u.poetry u.nunDel u.nextSakin u.pronAttached
  | .mufarragh i => uOK u.pre u.f u.ats u.ex u.outer (some i) u.poetry u.nunDel u.nextSakin u.pronAttached
  | .tamm m st mt mq lg =>
    uOK u.pre u.f u.ats u.ex u.outer none u.poetry u.nunDel u.nextSakin u.pronAttached && tammOK u.pre u.f m st mt mq lg

/-- **احتواءُ الطبقة السابقة:** الإطارُ الموحَّد بلا غلافٍ ولا استثناءٍ ولا عاملٍ خارجيّ هو الإطارُ المسمّى بعينه. -/
theorem kull_conservative (f : Frame) (ats : List Attr) (ex : List Ext)
    (h : ex.all (fun e => e.1 != 1 && e.1 != 2) = true) :
    uK { pre := [], f := f, ats := ats, ex := ex } = annOK2 f ats ex := by
  unfold uK
  simp only
  rw [u_conservative f ats ex h]
  cases hc : annOK2 f ats ex
  · simp
  · have : framesL.contains f = true := by
      unfold annOK2 at hc; simp only [Bool.and_eq_true] at hc; exact hc.1.1.1.1.1
    rw [this]; rfl

/-! ## ٣. الجملةُ الكلّيّة -/

inductive Jumla
  | basit (u : UD)
  | shart (adat : Nat) (c1 : UD) (c2 : Option UD) (rabit : Nat)
  | nida (harf fill mtype : Nat) (u : UD)
  | ist (tool i : Nat) (u : UD)
  | shaan (amil pfill : Nat) (feat : Feat) (jamid : Bool) (fasl : Nat) (u : UD)
  | mawsul (mfeat : Feat) (aidKind : Nat) (aidFeat : Feat) (sila : UD)

/-- فعلُ الشرط ناسخٌ فعليّ (‎إن كان، إن لم يكن‎)؛ ولا لنْ في فعل الشرط. -/
def kanaShart (adat : Nat) (c1 : UD) (c2 : Option UD) (rabit : Nat) (prev : Bool) : Bool :=
  adat < 10 && c1.f.1 == 0 && (c1.f.2.1 == 1 || c1.f.2.1 == 3) && (c1.outer == 0 || c1.outer == 5) &&
  match c2 with
  | none => prev && rabit == 0
  | some g => framesL.contains g.f && TarkibExt.rabitOK adat g.f rabit

def noLan (c1 : UD) : Bool := c1.outer != 4 && c1.f.2.1 != 4

/-- **القانونُ الواحد:** قانونُ الصورة من طبقتها، وقانونُ مكوّناتها. -/
def jOK (j : Jumla) (prev : Bool) : Bool :=
  match j with
  | .basit u => uK u
  | .shart a c1 c2 r =>
    noLan c1 && (TarkibExt.shartOK a c1.f (c2.map (·.f)) r prev || kanaShart a c1 c2 r prev) &&
    uK c1 && (match c2 with | none => true | some g => uK g)
  | .nida h fl m u => TarkibExt.nidaOK h fl m && uK u
  | .ist t i u => TarkibExt.istOK t u.f i && uK u
  | .shaan am pf ft jm fs u => TarkibExt.shaanOK am pf ft u.f jm fs && uK u
  | .mawsul mf k af s => TarkibExt.mawsulOK mf s.f k af && uK s

/-- **الاحتواء:** كلُّ صورةٍ مرخَّصة تحقّق قانونَ طبقتها بعينه، ومكوّناتُها إطاراتٌ موحَّدةٌ مرخَّصة. -/
theorem containment :
    (∀ u p, jOK (.basit u) p = uK u) ∧
    (∀ h fl m u p, jOK (.nida h fl m u) p = (TarkibExt.nidaOK h fl m && uK u)) ∧
    (∀ t i u p, jOK (.ist t i u) p = (TarkibExt.istOK t u.f i && uK u)) ∧
    (∀ am pf ft jm fs u p, jOK (.shaan am pf ft jm fs u) p = (TarkibExt.shaanOK am pf ft u.f jm fs && uK u)) ∧
    (∀ mf k af s p, jOK (.mawsul mf k af s) p = (TarkibExt.mawsulOK mf s.f k af && uK s)) ∧
    (∀ a c1 c2 r p, jOK (.shart a c1 c2 r) p = true → c1.f.1 == 1 → noLan c1 = true → c2.isSome →
      TarkibExt.shartOK a c1.f (c2.map (·.f)) r p = true ∨ kanaShart a c1 c2 r p = true) := by
  refine ⟨fun _ _ => rfl, fun _ _ _ _ _ => rfl, fun _ _ _ _ => rfl, fun _ _ _ _ _ _ _ => rfl, fun _ _ _ _ _ => rfl, ?_⟩
  intro a c1 c2 r p h _ _ _
  unfold jOK at h
  simp only [Bool.and_eq_true, Bool.or_eq_true] at h
  exact h.1.1.2

/-! ## ٤. السلسلة: ‎إن لم يكن‎ -/

def lamYakun : UD :=
  { pre := [], f := (0, 1, [(7, 0, 0), (0, 0, 0), (1, 0, 0)]),
    ats := [(1, 9, (0, 0, 0), false), noun 1 0 0, noun 0 0 0], ex := [e0, e0, e0], outer := 5, nunDel := true }

def jawab : UD :=
  { pre := [], f := (1, 0, [(2, 0, 0), (3, 1, hudur)]), ats := [(1, 9, (2, 0, 0), false), pron 2 0 0], ex := [e0, e0] }

def lanTafal : UD :=
  { pre := [], f := (1, 4, [(7, 0, 0), (2, 0, 0), (3, 1, hudur)]), ats := [harfA, (1, 9, (2, 0, 0), false), pron 2 0 0], ex := [e0, e0, e0] }

def lamTafal : UD :=
  { pre := [], f := (1, 5, [(7, 0, 0), (2, 0, 0), (3, 1, hudur)]), ats := [harfA, (1, 9, (2, 0, 0), false), pron 2 0 0], ex := [e0, e0, e0] }

/-- **‎إن لم تفعلْ … تفعلْ‎ مرخَّصة و‎إن لن تفعلَ‎ لا** — والإطاران مرخَّصان في أنفسهما، فالمانعُ قانونُ فعل الشرط وحده. -/
theorem lan_not_shart :
    uK lanTafal = true ∧ uK lamTafal = true ∧
    jOK (.shart 0 lamTafal (some jawab) 0) false = true ∧ jOK (.shart 0 lanTafal (some jawab) 0) false = false := by
  decide +kernel

/-- **‎إن لم يكنْ زيدٌ قائمًا … تَفعلْ‎ مرخَّصة؛ و‎إن لن يكونَ‎ لا (لن لا تكون في فعل الشرط)؛ والجزمُ في دال ‎يكنْ‎ من ‎لم‎
(‎reqState 1 5 2 = 3‎) وفي محلّ جملة الشرط من ‎إن‎ (‎shartState‎).** -/
theorem in_lam_yakun :
    jOK (.shart 0 lamYakun (some jawab) 0) false = true ∧
    jOK (.shart 0 { lamYakun with outer := 4, nunDel := false } (some jawab) 0) false = false ∧
    reqState 1 5 2 = some 3 ∧ TarkibExt.shartState 0 0 = (some 3, some 3) := by decide +kernel

def qawm (pre : List Nat) : UD :=
  { pre := pre, f := (1, 0, [(2, 0, 0), (3, 0, 0)]), ats := [past 0 0, noun 1 0 2], ex := [e0, (0, false, 4, 0)],
    ist := Ist.tamm 1 1 true false 0 }

/-- الاستثناءُ التامّ في الجملة الكلّيّة: ‎ما قامَ القومُ إلّا زيدٌ‎ (بدلٌ مرفوع) مرخَّصة، وبلا نفيٍ لا (الموجبُ نصبٌ واجب). -/
theorem tamm_in_jumla : jOK (.basit (qawm [1])) false = true ∧ jOK (.basit (qawm [])) false = false := by decide +kernel

/-! ## ٥. الرقمُ الواحد -/

def istCode : Ist → Nat
  | .none => 0
  | .mufarragh i => pair 1 i
  | .tamm m st mt mq lg => pair 2 (pair m (pair st (pair (bCode mt) (pair (bCode mq) lg))))

def illaOf : Ist → Option Nat
  | .mufarragh i => some i
  | _ => none

def udEnc (u : UD) : Nat :=
  pair (uEnc u.pre u.f u.ats u.ex u.outer (illaOf u.ist) u.poetry u.nunDel u.ws)
    (pair (istCode u.ist) (pair (bCode u.nextSakin) (bCode u.pronAttached)))

theorem bCode_inj (a b : Bool) (h : bCode a = bCode b) : a = b := by cases a <;> cases b <;> simp_all [bCode]

theorem pair_zero : pair 0 0 = 0 := by decide

theorem pair_ne0 (u r : Nat) (hu : 0 < u) : pair u r ≠ 0 := by
  intro h; have := (pair_injective (h.trans pair_zero.symm)).1; omega

theorem istCode_inj (a b : Ist) (h : istCode a = istCode b) : a = b := by
  cases a with
  | none => cases b with
    | none => rfl
    | mufarragh i => simp only [istCode] at h; exact absurd h.symm (pair_ne0 1 i (by decide))
    | tamm _ _ _ _ _ => simp only [istCode] at h; exact absurd h.symm (pair_ne0 2 _ (by decide))
  | mufarragh i => cases b with
    | none => simp only [istCode] at h; exact absurd h (pair_ne0 1 i (by decide))
    | mufarragh j => simp only [istCode] at h; rw [(pair_injective h).2]
    | tamm _ _ _ _ _ => simp only [istCode] at h; have := (pair_injective h).1; omega
  | tamm m st mt mq lg => cases b with
    | none => simp only [istCode] at h; exact absurd h (pair_ne0 2 _ (by decide))
    | mufarragh j => simp only [istCode] at h; have := (pair_injective h).1; omega
    | tamm m' st' mt' mq' lg' =>
      simp only [istCode] at h
      obtain ⟨_, h⟩ := pair_injective h
      obtain ⟨h1, h⟩ := pair_injective h
      obtain ⟨h2, h⟩ := pair_injective h
      obtain ⟨h3, h⟩ := pair_injective h
      obtain ⟨h4, h5⟩ := pair_injective h
      rw [h1, h2, bCode_inj _ _ h3, bCode_inj _ _ h4, h5]

theorem uK_mem (u : UD) (h : uK u = true) : u.f ∈ framesL := by
  unfold uK at h; simp only [Bool.and_eq_true] at h; exact List.contains_iff_mem.mp h.1

theorem ud_value (u v : UD) (hu : uK u = true) (hv : uK v = true) (h : udEnc u = udEnc v) : u = v := by
  unfold udEnc at h
  obtain ⟨h1, h⟩ := pair_injective h
  obtain ⟨h2, h⟩ := pair_injective h
  obtain ⟨h3, h4⟩ := pair_injective h
  obtain ⟨a1, a2, a3, a4, a5, a6, _, a8, a9⟩ := u_value _ _ _ _ (uK_mem u hu) (uK_mem v hv) _ _ _ _ _ _ _ _ _ _ _ _ _ _ h1
  cases u; cases v
  simp only at a1 a2 a3 a4 a5 a6 a8 a9 h2 h3 h4
  have e1 := istCode_inj _ _ h2; have e2 := bCode_inj _ _ h3; have e3 := bCode_inj _ _ h4
  subst a1 a2 a3 a4 a5 a6 a8 a9 e1 e2 e3; rfl

def fC (f : Feat) : Nat := pair f.1 (pair f.2.1 f.2.2)

theorem fC_inj (f g : Feat) (h : fC f = fC g) : f = g := by
  obtain ⟨a, b, c⟩ := f; obtain ⟨a', b', c'⟩ := g
  unfold fC at h
  obtain ⟨h1, h⟩ := pair_injective h
  obtain ⟨h2, h3⟩ := pair_injective h
  simp only at h1 h2 h3; rw [h1, h2, h3]

def optCode : Option UD → Nat
  | none => 0
  | some g => udEnc g + 1

theorem opt_inj (a b : Option UD) (ha : (match a with | none => true | some g => uK g) = true)
    (hb : (match b with | none => true | some g => uK g) = true) (h : optCode a = optCode b) : a = b := by
  cases a with
  | none => cases b with
    | none => rfl
    | some _ => simp [optCode] at h
  | some g => cases b with
    | none => simp [optCode] at h
    | some g' => simp only [optCode] at h; exact congrArg some (ud_value g g' ha hb (by omega))

def jEnc : Jumla → Nat
  | .basit u => pair 0 (udEnc u)
  | .shart a c1 c2 r => pair 1 (pair a (pair (udEnc c1) (pair (optCode c2) r)))
  | .nida h fl m u => pair 2 (pair h (pair fl (pair m (udEnc u))))
  | .ist t i u => pair 3 (pair t (pair i (udEnc u)))
  | .shaan am pf ft jm fs u => pair 4 (pair am (pair pf (pair (fC ft) (pair (bCode jm) (pair fs (udEnc u))))))
  | .mawsul mf k af s => pair 5 (pair (fC mf) (pair k (pair (fC af) (udEnc s))))

/-- **الرقمُ الواحد يُفكّ:** جملتان كلّيّتان مرخَّصتان برقمٍ واحد صورتُهما واحدة ومكوّناتُهما كلُّها واحدة. -/
theorem j_value (j k : Jumla) (p q : Bool) (hj : jOK j p = true) (hk : jOK k q = true) (h : jEnc j = jEnc k) :
    (match j, k with
     | .basit u, .basit v => u = v
     | .shart a c1 c2 r, .shart a' c1' c2' r' => a = a' ∧ c1 = c1' ∧ c2 = c2' ∧ r = r'
     | .nida h1 f1 m1 u, .nida h2 f2 m2 v => h1 = h2 ∧ f1 = f2 ∧ m1 = m2 ∧ u = v
     | .ist t i u, .ist t' i' v => t = t' ∧ i = i' ∧ u = v
     | .shaan a pf ft jm fs u, .shaan a' pf' ft' jm' fs' v =>
         a = a' ∧ pf = pf' ∧ ft = ft' ∧ jm = jm' ∧ fs = fs' ∧ u = v
     | .mawsul mf k af s, .mawsul mf' k' af' s' => mf = mf' ∧ k = k' ∧ af = af' ∧ s = s'
     | _, _ => False) := by
  cases j <;> cases k <;> simp only [jEnc] at h <;>
    (try (have := (pair_injective h).1; simp at this)) <;> simp only [jOK, Bool.and_eq_true] at hj hk
  · exact ud_value _ _ hj hk (pair_injective h).2
  · obtain ⟨h1, h⟩ := pair_injective (pair_injective h).2
    obtain ⟨h2, h⟩ := pair_injective h
    obtain ⟨h3, h4⟩ := pair_injective h
    exact ⟨h1, ud_value _ _ hj.1.2 hk.1.2 h2, opt_inj _ _ hj.2 hk.2 h3, h4⟩
  · obtain ⟨h1, h⟩ := pair_injective (pair_injective h).2
    obtain ⟨h2, h⟩ := pair_injective h
    obtain ⟨h3, h4⟩ := pair_injective h
    exact ⟨h1, h2, h3, ud_value _ _ hj.2 hk.2 h4⟩
  · obtain ⟨h1, h⟩ := pair_injective (pair_injective h).2
    obtain ⟨h2, h3⟩ := pair_injective h
    exact ⟨h1, h2, ud_value _ _ hj.2 hk.2 h3⟩
  · obtain ⟨h1, h⟩ := pair_injective (pair_injective h).2
    obtain ⟨h2, h⟩ := pair_injective h
    obtain ⟨h3, h⟩ := pair_injective h
    obtain ⟨h4, h⟩ := pair_injective h
    obtain ⟨h5, h6⟩ := pair_injective h
    exact ⟨h1, h2, fC_inj _ _ h3, bCode_inj _ _ h4, h5, ud_value _ _ hj.2 hk.2 h6⟩
  · obtain ⟨h1, h⟩ := pair_injective (pair_injective h).2
    obtain ⟨h2, h⟩ := pair_injective h
    obtain ⟨h3, h4⟩ := pair_injective h
    exact ⟨fC_inj _ _ h1, h2, fC_inj _ _ h3, ud_value _ _ hj.2 hk.2 h4⟩

end Kull
end SLGE
