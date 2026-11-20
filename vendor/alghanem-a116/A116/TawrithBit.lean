import A116.HukmMuwahhad

/-!
# نواةُ التوريث بتّاتٍ: البتُّ الثلاثيّ قناعين، والتعارضُ مسمًّى لا مكتوم (ADR ١١٩)

أمرُ المالك (2026-10-21 12:28): «حلل وانتقد واستنتج وطور مشروع Alghanem»، على مرفقين: نموذجٌ بايثونيّ منتهٍ
(`verify_inheritance_kernel.py`) يمثّل `battQ` من `Madlul/Wiratha.lean` في Mashru (الإيداع `70ca1c2`، قُرئ للقراءة وحدَها)
قناعين `(known, value)` بعرض خمس خانات، ونتيجتُه (`inheritance_kernel_results.json`).

القيمةُ الثلاثيّة هنا `Option Bool`: ‎`some true`‎ نعم، ‎`some false`‎ لا، ‎`none`‎ لا حكم — وهي قيمةُ القابليّة في
`HukmMuwahhad.maurutha` بعينها.

## ما يُبنى، لكلّ عرض n (لا للعرض الخامس وحدَه كما في المرفق)

١. **البتّ** `batt a f`: ما بتّه الأوّلُ يبقى، وما تركه «لا حكم» يبتّه الثاني — وهو `battQ` في Mashru إن كان الأوّلُ الجنسَ
   الأعلى، وهو خطوةُ `maurutha` في الغانم إن كان الأوّلُ الأخصّ (`maurutha_batt`): **العمليّةُ واحدة والأسبقيّةُ معكوسة**.
٢. **القناعان**: الخانةُ بتّتان (معلوم، صادق) والصادقُ داخلَ المعلوم؛ الطيُّ والفكُّ تقابلٌ على القناعات الصالحة
   (`dec_enc`، `enc_dec`)، والبتُّ على القناعين صيغةٌ بتّيّة واحدة لكلّ خانة (`fast_eq`).
٣. **التعارضُ** `tanaqud`: الطرفان معلومان مختلفان؛ وقناعُه ‎k₁ ∧ k₂ ∧ (v₁ ⊕ v₂)‎ (`conflict_eq`).
٤. **البتُّ تحسينٌ للأوّل دائمًا، وللثاني ⟺ لا تعارض** (`batt_yuhassin`، `batt_yuhassin_thani_iff`)؛ والأسبقيّتان تتّفقان
   ⟺ لا تعارض (`batt_comm_iff`) — فالخلافُ بين «الجنسُ يغلب» (Mashru) و«الأخصُّ يغلب» (الغانم، ADR ١٠٢) واقعٌ في
   مواضع التعارض وحدَها.
٥. **الجمعُ بلا أسبقيّة** `wahhid`: يُعطي البتَّ حيث لا تعارض، ويرفض التعارضَ باسمه (`none`) — الرفضُ لا التخمين.
٦. **الأعداد لكلّ n**: الأزواجُ ‎9ⁿ‎، والمتّسقةُ ‎7ⁿ‎ (`count_muttasiq`)، والمتعارضةُ ‎9ⁿ − 7ⁿ‎ (`count_mutaarid`) — والمرفقُ فحصها للخامسة وحدَها (16,807 من 59,049).

الحدّ (معلن): القناعان هنا قائمتا بتّات لا عددان طبيعيّان، فلا مبرهنةَ هنا على `Nat.lor` و`Nat.land`
(`BIT_LIST_NOT_NAT_MASK`)؛ ولا قياسَ سرعة؛ و`qab` (قائمةُ القابليّات في Mashru) خارجُ النموذج كما في المرفق.
-/

set_option autoImplicit false

namespace A116.TawrithBit

/-- القيمةُ الثلاثيّة: نعم، لا، لا حكم. -/
abbrev Q := Option Bool

/-- **البتّ**: ما بتّه الأوّلُ يبقى، وما تركه «لا حكم» يبتّه الثاني. -/
def batt : Q → Q → Q
  | some b, _ => some b
  | none, f => f

/-- التحسين: كلُّ ما بتّه الأوّلُ باقٍ في الثاني. -/
def yuhassin (a b : Q) : Prop := ∀ x, a = some x → b = some x

/-- التعارض: الطرفان معلومان مختلفان. -/
def tanaqud : Q → Q → Bool
  | some x, some y => x != y
  | _, _ => false

/-- **البتُّ تحسينٌ للأوّل دائمًا.** -/
theorem batt_yuhassin (a f : Q) : yuhassin a (batt a f) := by
  intro x h; subst h; rfl

/-- **والبتُّ تحسينٌ للثاني ⟺ لا تعارض.** -/
theorem batt_yuhassin_thani_iff (a f : Q) : yuhassin f (batt a f) ↔ tanaqud a f = false := by
  cases a with
  | none => simp [batt, tanaqud, yuhassin]
  | some x =>
    cases f with
    | none => simp [batt, tanaqud, yuhassin]
    | some y => cases x <;> cases y <;> simp [batt, tanaqud, yuhassin]

/-- **الأسبقيّتان تتّفقان ⟺ لا تعارض**: «الجنسُ يغلب» و«الأخصُّ يغلب» يفترقان في التعارض وحدَه. -/
theorem batt_comm_iff (a f : Q) : batt a f = batt f a ↔ tanaqud a f = false := by
  cases a with
  | none => cases f <;> simp [batt, tanaqud]
  | some x =>
    cases f with
    | none => simp [batt, tanaqud]
    | some y => cases x <;> cases y <;> simp [batt, tanaqud]

/-- **الجمعُ بلا أسبقيّة**: البتُّ حيث لا تعارض، والتعارضُ رفضٌ (`none`). -/
def wahhid (a f : Q) : Option Q := if tanaqud a f then none else some (batt a f)

theorem wahhid_batt (a f : Q) (h : tanaqud a f = false) : wahhid a f = some (batt a f) := by
  simp [wahhid, h]

theorem wahhid_rafd (a f : Q) (h : tanaqud a f = true) : wahhid a f = none := by
  simp [wahhid, h]

/-- والجمعُ لا يبالي بالترتيب. -/
theorem wahhid_comm (a f : Q) : wahhid a f = wahhid f a := by
  cases a with
  | none => cases f <;> rfl
  | some x => cases f with
    | none => rfl
    | some y => cases x <;> cases y <;> rfl

/-- **البتُّ تحت كلّ محسِّنٍ للطرفين**: إن حسّن c الطرفين فهو يحسّن البتّ. (و«أصغرُهما» يقتضي معه أنّ البتَّ
يحسّن الثاني، وذلك ⟺ لا تعارض: `batt_yuhassin_thani_iff`.) -/
theorem batt_taht_muhassin (a f c : Q) (ha : yuhassin a c) (hf : yuhassin f c) :
    yuhassin (batt a f) c := by
  cases a with
  | none => simpa [batt] using hf
  | some x => simpa [batt] using ha

/-! ## خطوةُ `maurutha` في الغانم بتٌّ والأخصُّ أوّلًا -/

/-- **`maurutha` طيٌّ بالبتّ على سلسلة الجنس، والأخصُّ أوّل**. -/
theorem maurutha_batt (abb : HukmMuwahhad.Shajara) (n : Nat) (q : String → Option Bool) (j : String) :
    HukmMuwahhad.maurutha abb n q j = (HukmMuwahhad.silsila abb n j).foldr (fun x acc => batt (q x) acc) none := by
  unfold HukmMuwahhad.maurutha
  generalize HukmMuwahhad.silsila abb n j = l
  induction l with
  | nil => rfl
  | cons x xs ih =>
    simp only [List.findSome?, List.foldr_cons]
    cases h : q x with
    | none => simp [batt, ih]
    | some b => simp [batt]

/-! ## القناعان: الخانةُ بتّتان -/

/-- الخانةُ بتّتان: (معلوم، صادق). -/
def encQ : Q → Bool × Bool
  | none => (false, false)
  | some b => (true, b)

def decQ : Bool × Bool → Q
  | (false, _) => none
  | (true, b) => some b

/-- الصالح: الصادقُ داخلَ المعلوم. -/
def salih (p : Bool × Bool) : Bool := !p.2 || p.1

theorem decQ_encQ (q : Q) : decQ (encQ q) = q := by cases q <;> rfl
theorem encQ_salih (q : Q) : salih (encQ q) = true := by cases q with
  | none => rfl
  | some b => cases b <;> rfl
theorem encQ_decQ (p : Bool × Bool) (h : salih p = true) : encQ (decQ p) = p := by
  obtain ⟨k, v⟩ := p; cases k <;> cases v <;> simp_all [salih, encQ, decQ]

/-- البتُّ على البتّتين: ‎(k₁ ∨ k₂, v₁ ∨ (¬k₁ ∧ v₂))‎ — صيغةُ المرفق `fast` لخانةٍ واحدة. -/
def fastQ (p f : Bool × Bool) : Bool × Bool := (p.1 || f.1, p.2 || (!p.1 && f.2))

/-- وقناعُ التعارض لخانةٍ واحدة: ‎k₁ ∧ k₂ ∧ (v₁ ⊕ v₂)‎. -/
def conflictQ (p f : Bool × Bool) : Bool := p.1 && f.1 && (p.2 != f.2)

theorem fastQ_eq (a f : Q) : decQ (fastQ (encQ a) (encQ f)) = batt a f := by
  cases a with
  | none => cases f with
    | none => rfl
    | some y => cases y <;> rfl
  | some x => cases x <;> cases f <;> rfl

theorem conflictQ_eq (a f : Q) : conflictQ (encQ a) (encQ f) = tanaqud a f := by
  cases a with
  | none => cases f <;> rfl
  | some x => cases f with
    | none => cases x <;> rfl
    | some y => cases x <;> cases y <;> rfl

/-! ## على n خانة، لكلّ n -/

/-- الطيُّ: قناعا المعلوم والصادق خانةً خانة. -/
def enc (s : List Q) : List Bool × List Bool := ((s.map encQ).map Prod.fst, (s.map encQ).map Prod.snd)

def dec (m : List Bool × List Bool) : List Q := (m.1.zip m.2).map fun p => decQ p

/-- الصالح: القناعان بطولٍ واحد والصادقُ داخلَ المعلوم في كلّ خانة. -/
def salihM (m : List Bool × List Bool) : Bool := m.1.length == m.2.length && (m.1.zip m.2).all salih

/-- البتُّ على القناعين: صيغةٌ بتّيّةٌ خانةً خانة. -/
def fast (p f : List Bool × List Bool) : List Bool × List Bool :=
  ((p.1.zip f.1).map fun x => x.1 || x.2,
   (((p.1.zip p.2).zip f.2)).map fun x => x.1.2 || (!x.1.1 && x.2))

/-- قناعُ التعارض: ‎k₁ ∧ k₂ ∧ (v₁ ⊕ v₂)‎ خانةً خانة. -/
def conflict (p f : List Bool × List Bool) : List Bool :=
  ((p.1.zip f.1).zip (p.2.zip f.2)).map fun x => x.1.1 && x.1.2 && (x.2.1 != x.2.2)

theorem dec_enc : ∀ s : List Q, dec (enc s) = s
  | [] => rfl
  | q :: s => by
    have := dec_enc s
    simp only [dec, enc, List.map_cons, List.zip_cons_cons] at this ⊢
    rw [this]
    cases q with
    | none => rfl
    | some b => rfl

theorem enc_salih : ∀ s : List Q, salihM (enc s) = true
  | [] => rfl
  | q :: s => by
    have := enc_salih s
    simp only [salihM, enc, List.map_cons, List.length_cons, List.zip_cons_cons, List.all_cons,
      Bool.and_eq_true, beq_iff_eq] at this ⊢
    refine ⟨by omega, ?_, this.2⟩
    exact encQ_salih q

theorem enc_dec : ∀ (k v : List Bool), salihM (k, v) = true → enc (dec (k, v)) = (k, v)
  | [], [], _ => rfl
  | [], _ :: _, h => by simp [salihM] at h
  | _ :: _, [], h => by simp [salihM] at h
  | a :: k, b :: v, h => by
    simp only [salihM, List.length_cons, List.zip_cons_cons, List.all_cons, Bool.and_eq_true,
      beq_iff_eq] at h
    have ih := enc_dec k v (by simp only [salihM, Bool.and_eq_true, beq_iff_eq]; exact ⟨by omega, h.2.2⟩)
    simp only [enc, dec, List.map_cons, List.zip_cons_cons] at ih ⊢
    have e := encQ_decQ (a, b) h.2.1
    simp only [Prod.mk.injEq, List.map_map] at ih ⊢
    rw [e]
    refine ⟨?_, ?_⟩ <;> simp only [List.cons.injEq, true_and]
    · exact ih.1
    · exact ih.2

/-- **البتُّ على القناعين هو البتُّ خانةً خانة، لكلّ n.** -/
theorem fast_eq : ∀ (s t : List Q), s.length = t.length →
    dec (fast (enc s) (enc t)) = List.zipWith batt s t
  | [], [], _ => rfl
  | [], _ :: _, h => by simp at h
  | _ :: _, [], h => by simp at h
  | a :: s, f :: t, h => by
    have ih := fast_eq s t (by simpa using h)
    simp only [dec, fast, enc, List.map_cons, List.zip_cons_cons, List.zipWith_cons_cons] at ih ⊢
    rw [ih, ← fastQ_eq a f]
    rfl

/-- **قناعُ التعارض هو التعارضُ خانةً خانة، لكلّ n.** -/
theorem conflict_eq : ∀ (s t : List Q), s.length = t.length →
    conflict (enc s) (enc t) = List.zipWith tanaqud s t
  | [], [], _ => rfl
  | [], _ :: _, h => by simp at h
  | _ :: _, [], h => by simp at h
  | a :: s, f :: t, h => by
    have ih := conflict_eq s t (by simpa using h)
    simp only [conflict, enc, List.map_cons, List.zip_cons_cons, List.zipWith_cons_cons] at ih ⊢
    rw [ih, ← conflictQ_eq a f]
    rfl

/-! ## الأعداد لكلّ n -/

def qiyam : List Q := [some true, some false, none]

/-- كلُّ الحالات بطول n. -/
def halat : Nat → List (List Q)
  | 0 => [[]]
  | n + 1 => qiyam.flatMap fun q => (halat n).map (q :: ·)

/-- كلُّ الأزواج بطول n، خانةً خانة. -/
def azwaj : Nat → List (List (Q × Q))
  | 0 => [[]]
  | n + 1 => (qiyam.flatMap fun a => qiyam.map fun f => (a, f)).flatMap fun p => (azwaj n).map (p :: ·)

/-- المتّسق: لا تعارضَ في خانة. -/
def muttasiq (w : List (Q × Q)) : Bool := w.all fun p => !tanaqud p.1 p.2

theorem length_flatMap_map {α β : Type} (l : List α) (m : List β) (g : α → β → β) :
    (l.flatMap fun a => m.map (g a)).length = l.length * m.length := by
  induction l with
  | nil => simp
  | cons a l ih => simp only [List.flatMap_cons, List.length_append, List.length_map, ih,
      List.length_cons, Nat.succ_mul, Nat.add_comm]

theorem azwaj_length (n : Nat) : (azwaj n).length = 9 ^ n := by
  induction n with
  | zero => rfl
  | succ n ih => rw [azwaj, length_flatMap_map, ih, Nat.pow_succ, Nat.mul_comm]; rfl

theorem count_aux (n : Nat) (ih : ((azwaj n).filter muttasiq).length = 7 ^ n) :
    ∀ B : List (Q × Q), ((B.flatMap fun p => (azwaj n).map (p :: ·)).filter muttasiq).length =
      (B.filter fun p => !tanaqud p.1 p.2).length * 7 ^ n
  | [] => by simp
  | p :: B => by
    rw [List.flatMap_cons, List.filter_append, List.length_append, count_aux n ih B, List.filter_map,
      List.length_map]
    by_cases h : tanaqud p.1 p.2 = true
    · have : (List.filter (muttasiq ∘ fun x => p :: x) (azwaj n)) = [] := by
        rw [List.filter_eq_nil_iff]
        intro w _
        simp [muttasiq, h]
      rw [this, List.filter_cons_of_neg (by simp [h])]; simp
    · have e : (List.filter (muttasiq ∘ fun x => p :: x) (azwaj n)) = (azwaj n).filter muttasiq := by
        apply List.filter_congr
        intro w _
        simp [muttasiq, Function.comp, h]
      rw [e, ih, List.filter_cons_of_pos (by simpa using h), List.length_cons, Nat.add_mul, Nat.one_mul,
        Nat.add_comm]

/-- **المتّسقُ من الأزواج بطول n عددُه ‎7ⁿ‎ لكلّ n** (والكلُّ ‎9ⁿ‎). -/
theorem count_muttasiq (n : Nat) : ((azwaj n).filter muttasiq).length = 7 ^ n := by
  induction n with
  | zero => rfl
  | succ n ih => rw [azwaj, count_aux n ih, Nat.pow_succ, Nat.mul_comm]; rfl

theorem length_filter_not {α : Type} (p : α → Bool) :
    ∀ l : List α, (l.filter p).length + (l.filter fun x => !p x).length = l.length := by
  intro l
  induction l with
  | nil => rfl
  | cons x l ih => cases h : p x <;> simp [h] <;> omega

/-- **المتعارضُ من الأزواج بطول n عددُه ‎9ⁿ − 7ⁿ‎ لكلّ n.** -/
theorem count_mutaarid (n : Nat) : ((azwaj n).filter fun w => !muttasiq w).length = 9 ^ n - 7 ^ n := by
  have := length_filter_not muttasiq (azwaj n)
  rw [count_muttasiq, azwaj_length] at this
  omega

/-- الشاهدُ على عرض المرفق: 59,049 زوجًا، منها 16,807 متّسقة، و42,242 فيها تعارض. -/
theorem shahid_khamsa :
    (azwaj 5).length = 59049 ∧ ((azwaj 5).filter muttasiq).length = 16807 ∧
      ((azwaj 5).filter fun w => !muttasiq w).length = 42242 := by
  rw [azwaj_length, count_muttasiq, count_mutaarid]; decide

/-- ومثالُ المرفق المضادّ: البتُّ يُبقي «نعم» على «لا» فلا يحسّن الثاني، والجمعُ يرفض. -/
theorem shahid_naam_la :
    batt (some true) (some false) = some true ∧ ¬ yuhassin (some false) (batt (some true) (some false)) ∧
      wahhid (some true) (some false) = none := by
  refine ⟨rfl, ?_, rfl⟩
  intro h; exact absurd (h false rfl) (by simp [batt])

end A116.TawrithBit
