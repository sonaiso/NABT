/-!
# الليفُ والرتبة — استعادةُ ما يُسقطه الإسقاط، وحدُّها الأدنى

منقولٌ من `tools/rasm_recovery/PROOF_AR.md` (مبرهنتا الاستعادة والحدّ الأدنى):
هناك مكتوبتان نثرًا ومفحوصتان بالتشغيل على مجالٍ منتهٍ، وهنا تفحصهما النواة لكلّ
مجالٍ منتهٍ ولكلّ إسقاط.

## الإطار

مجالٌ منتهٍ `D` بلا تكرار (الرسوم)، وإسقاطٌ `A : α → β` (الرسمُ ← ذرّاتُه). والليفُ
`fiber D A a` عناصرُ `D` التي صورتُها `a`، بترتيبها في `D`. والرتبةُ موضعُ العنصر
في ليفه، والشهادةُ ‎(A x, rank x)‎.

## المبرهنات

* `decode_encode`: **الاستعادة.** ‎decode(encode x) = x‎ لكلّ ‎x ∈ D‎.
* `encode_injective`: **التباين.** شهادتان متساويتان لعنصرين من `D` ⇒ العنصران واحد.
* `rank_lt`: الرتبةُ أصغرُ من حجم الليف، فسجلٌّ بـ‎m‎ حالةً يكفي.
* `register_injective_on_fiber`، `fiber_length_le`: **الحدّ الأدنى.** كلُّ سجلٍّ `s`
  بقيمٍ في ‎Fin k‎ يسمح لقارئٍ `H` باستعادة كلّ عنصرٍ من ليفه ومن صورته
  يحقّق ‎m ≤ k‎. وبـ‎k = 2^b‎: سجلٌّ ثابتُ الطول بـ‎b‎ بتّاتٍ يحتاج ‎m ≤ 2^b‎.

## ما لا تقوله

لا شيءَ هنا عن صحّة الإسقاط العربيّ: الاستعادةُ نسبيّةٌ إلى `A`، فإسقاطٌ خاطئٌ
يُستعاد بدقّةٍ تامّة. ولا عن أصغر طولٍ متوسّط بترميزٍ متغيّر، ولا عن حجم القاموس.
-/

namespace A116.Fiber

variable {α β : Type} [DecidableEq β]

/-- الليف: عناصرُ `D` التي صورتُها `a`، بترتيبها. -/
def fiber (D : List α) (A : α → β) (a : β) : List α := D.filter fun x => A x = a

/-- الرتبة: موضعُ `x` في ليفه. -/
def rank [DecidableEq α] (D : List α) (A : α → β) (x : α) : Nat := (fiber D A (A x)).idxOf x

/-- الشهادة: الصورةُ والرتبة. -/
def encode [DecidableEq α] (D : List α) (A : α → β) (x : α) : β × Nat := (A x, rank D A x)

/-- الفكّ: العنصرُ ذو الرتبة في الليف، إن وُجد. -/
def decode (D : List α) (A : α → β) (c : β × Nat) : Option α := (fiber D A c.1)[c.2]?

theorem mem_fiber {D : List α} {A : α → β} {x : α} (hx : x ∈ D) : x ∈ fiber D A (A x) := by
  simp [fiber, hx]

theorem rank_lt [DecidableEq α] {D : List α} {A : α → β} {x : α} (hx : x ∈ D) :
    rank D A x < (fiber D A (A x)).length :=
  List.idxOf_lt_length_of_mem (mem_fiber hx)

/-- **الاستعادة.** -/
theorem decode_encode [DecidableEq α] {D : List α} {A : α → β} {x : α} (hx : x ∈ D) :
    decode D A (encode D A x) = some x := by
  simp only [decode, encode, rank]
  rw [List.getElem?_eq_getElem (List.idxOf_lt_length_of_mem (mem_fiber hx))]
  simp [List.getElem_idxOf]

/-- **التباين**: من الاستعادة. -/
theorem encode_injective [DecidableEq α] {D : List α} {A : α → β} {x y : α} (hx : x ∈ D) (hy : y ∈ D)
    (h : encode D A x = encode D A y) : x = y := by
  have := decode_encode (A := A) hx
  rw [h, decode_encode hy] at this
  exact (Option.some.inj this).symm

/-- الفكُّ لا يُخرج إلا عنصرًا من `D` صورتُه المطلوبة؛ ورتبةٌ خارج الليف تُرفض. -/
theorem decode_sound {D : List α} {A : α → β} {c : β × Nat} {x : α}
    (h : decode D A c = some x) : x ∈ D ∧ A x = c.1 := by
  simp only [decode] at h
  have hm : x ∈ fiber D A c.1 := List.mem_of_getElem? h
  simp only [fiber, List.mem_filter, decide_eq_true_eq] at hm
  exact hm

theorem decode_none_of_rank_ge {D : List α} {A : α → β} {a : β} {r : Nat}
    (h : (fiber D A a).length ≤ r) : decode D A (a, r) = none := by
  simp [decode, h]

theorem fiber_nodup {D : List α} (hD : D.Nodup) (A : α → β) (a : β) :
    (fiber D A a).Nodup :=
  hD.filter _

/-- سجلٌّ يُستعاد منه كلُّ عنصرٍ من ليفه مع الصورة متباينُ القيم على الليف. -/
theorem register_injective_on_fiber {γ : Type} {D : List α} {A : α → β} {a : β}
    (s : α → γ) (H : β → γ → α) (hH : ∀ x ∈ fiber D A a, H a (s x) = x)
    {x y : α} (hx : x ∈ fiber D A a) (hy : y ∈ fiber D A a) (h : s x = s y) : x = y := by
  rw [← hH x hx, ← hH y hy, h]

private theorem nodup_map_of_injOn {γ : Type} (s : α → γ) :
    ∀ (l : List α), l.Nodup → (∀ x ∈ l, ∀ y ∈ l, s x = s y → x = y) → (l.map s).Nodup
  | [], _, _ => List.nodup_nil
  | x :: xs, hl, hinj => by
    rw [List.nodup_cons] at hl
    rw [List.map_cons, List.nodup_cons]
    refine ⟨?_, nodup_map_of_injOn s xs hl.2 fun u hu v hv => hinj u (by simp [hu]) v
      (by simp [hv])⟩
    intro hm
    obtain ⟨y, hy, hxy⟩ := List.mem_map.1 hm
    have : y = x := hinj y (by simp [hy]) x (by simp) hxy
    exact hl.1 (this ▸ hy)

/-- قائمةُ أعدادٍ بلا تكرارٍ كلُّها أصغرُ من ‎n‎ طولُها لا يزيد على ‎n‎. -/
theorem nodup_nat_length_le : ∀ (n : Nat) (l : List Nat), l.Nodup → (∀ x ∈ l, x < n) →
    l.length ≤ n
  | 0, [], _, _ => Nat.le_refl 0
  | 0, x :: _, _, h => absurd (h x (by simp)) (Nat.not_lt_zero x)
  | n + 1, l, hl, h => by
    by_cases hn : n ∈ l
    · have hlen := List.length_erase_of_mem hn
      have ih := nodup_nat_length_le n (l.erase n) (hl.erase n) fun x hx => by
        have ⟨hne, hmem⟩ := (hl.mem_erase_iff).1 hx
        have := h x hmem
        omega
      have : 0 < l.length := List.length_pos_of_mem hn
      omega
    · have ih := nodup_nat_length_le n l hl fun x hx => by
        have := h x hx
        have : x ≠ n := fun e => hn (e ▸ hx)
        omega
      omega

/-- قائمةٌ بلا تكرارٍ من ‎Fin k‎ طولُها لا يزيد على ‎k‎ (مبدأ الحمام). -/
theorem nodup_fin_length_le {k : Nat} (l : List (Fin k)) (hl : l.Nodup) : l.length ≤ k := by
  have hn : (l.map Fin.val).Nodup :=
    nodup_map_of_injOn Fin.val l hl fun x _ y _ h => Fin.ext h
  have := nodup_nat_length_le k (l.map Fin.val) hn fun x hx => by
    obtain ⟨y, _, rfl⟩ := List.mem_map.1 hx
    exact y.isLt
  simpa using this

/-- **الحدّ الأدنى.** كلُّ سجلٍّ بقيمٍ في ‎Fin k‎ يُستعاد منه الليفُ كلُّه يحقّق ‎m ≤ k‎. -/
theorem fiber_length_le {D : List α} (hD : D.Nodup) {A : α → β} {a : β} {k : Nat}
    (s : α → Fin k) (H : β → Fin k → α) (hH : ∀ x ∈ fiber D A a, H a (s x) = x) :
    (fiber D A a).length ≤ k := by
  have hn := nodup_map_of_injOn s (fiber D A a) (fiber_nodup hD A a)
    fun x hx y hy h => register_injective_on_fiber s H hH hx hy h
  simpa using nodup_fin_length_le _ hn

/-- وسجلُّ الرتبة يبلغ هذا الحدّ: ‎m‎ حالةً بالضبط تكفي. -/
theorem rank_register_fits [DecidableEq α] {D : List α} {A : α → β} {x : α} (hx : x ∈ D) :
    ∃ r : Fin (fiber D A (A x)).length, (r : Nat) = rank D A x :=
  ⟨⟨rank D A x, rank_lt hx⟩, rfl⟩

/-- **البتّات.** سجلٌّ ثابتُ الطول بـ‎b‎ بتّاتٍ يستعيد الليفَ ⇒ ‎m ≤ 2^b‎. -/
theorem fiber_length_le_two_pow {D : List α} (hD : D.Nodup) {A : α → β} {a : β} {b : Nat}
    (s : α → Fin (2 ^ b)) (H : β → Fin (2 ^ b) → α)
    (hH : ∀ x ∈ fiber D A a, H a (s x) = x) : (fiber D A a).length ≤ 2 ^ b :=
  fiber_length_le hD s H hH

end A116.Fiber
