import A116.Recovery

/-!
# اليونيكود — SLGE لتحويلات الترميز

البايتاتُ التي تدخل البوّابةَ UTF-8. وهذه الوحدةُ تبرهن أنّ القراءةَ والكتابةَ بينهما **تقابلٌ ذاتيُّ
الحدّ**: كلُّ نقطةِ ترميز (‎c < 0x110000‎ — مجالُ يونيكود كلُّه — وهو ما يشمل كلَّ العربيّ: ‎U+0600–U+06FF‎ بايتان، وما فوقه
حتى ‎U+10FFFF‎) تُكتب بايتاتٍ (1–4) وتُقرأ من رأس أيّ تيارٍ بعينها ويبقى ما بعدها بعينه.

* `utf8Encode c`: الصورةُ القياسيّة (أقصرُ صورة؛ لا overlong).
* `utf8Decode bs`: قارئٌ صارم: يتحقّق من بايتات الاستمرار ‎10xxxxxx‎ ومن الحدّ الأدنى لكلّ طول،
  فلا يقبل صورةً أطولَ من اللازم.
* `decode_encode`: ‎utf8Decode (utf8Encode c ++ rest) = some (c, rest)‎ لكلّ ‎c < 0x110000‎.
* `encode_prefix_free`: ترميزُ نقطةٍ لا يبدأ به ترميزُ أخرى (التفكيكُ وحيد).
* `decodeAll_encodeAll`: تيارُ نقاطٍ يعود كلُّه بترتيبه.
* `arabic_is_two_bytes`: كلُّ ما في ‎U+0600–U+06FF‎ بايتان.

## ترتيبُ العلامات (بقيّةٌ لا تطبيع)

الحرفُ قد تلحقه شدّةٌ وحركةٌ بأيّ ترتيبٍ في الرسم؛ والتطبيعُ (NFC) يثبّت ترتيبًا واحدًا ويُسقط
الترتيبَ الأصليّ. وهنا لا تطبيعَ يُسقط شيئًا: الترتيبُ الأصليّ **بقيّةٌ** تُسجَّل وتُردّ
(`markOrder_restore`، مثولٌ لـ`edit_roundtrip`) — على نسق بقيّة الطبعة في `Residue.lean`.
-/

namespace A116.Unicode

open A116.Recovery

/-- بايتاتُ نقطةِ ترميز، أقصرَ صورة. -/
def utf8Encode (c : Nat) : List Nat :=
  if c < 0x80 then [c]
  else if c < 0x800 then [0xC0 + c / 64, 0x80 + c % 64]
  else if c < 0x10000 then [0xE0 + c / 4096, 0x80 + (c / 64) % 64, 0x80 + c % 64]
  else [0xF0 + c / 262144, 0x80 + (c / 4096) % 64, 0x80 + (c / 64) % 64, 0x80 + c % 64]

/-- أبايتُ استمرارٍ؟ -/
def cont (b : Nat) : Bool := 0x80 ≤ b && b < 0xC0

/-- قارئٌ صارم من رأس التيار. -/
def utf8Decode : List Nat → Option (Nat × List Nat)
  | b0 :: rest =>
    if b0 < 0x80 then some (b0, rest)
    else if b0 < 0xC2 then none
    else if b0 < 0xE0 then
      match rest with
      | b1 :: r => if cont b1 then some ((b0 - 0xC0) * 64 + (b1 - 0x80), r) else none
      | [] => none
    else if b0 < 0xF0 then
      match rest with
      | b1 :: b2 :: r =>
        if cont b1 && cont b2 then
          let c := (b0 - 0xE0) * 4096 + (b1 - 0x80) * 64 + (b2 - 0x80)
          if 0x800 ≤ c then some (c, r) else none
        else none
      | _ => none
    else if b0 < 0xF5 then
      match rest with
      | b1 :: b2 :: b3 :: r =>
        if cont b1 && cont b2 && cont b3 then
          let c := (b0 - 0xF0) * 262144 + (b1 - 0x80) * 4096 + (b2 - 0x80) * 64 + (b3 - 0x80)
          if 0x10000 ≤ c then some (c, r) else none
        else none
      | _ => none
    else none
  | [] => none

theorem cont_of_mod (x : Nat) : cont (0x80 + x % 64) = true := by
  simp only [cont, Bool.and_eq_true, decide_eq_true_eq]
  have := Nat.mod_lt x (by decide : 0 < 64)
  omega

/-- **القراءةُ تعيد الكتابةَ وما بعدها بعينه** لكلّ نقطةٍ في مجال يونيكود. -/
theorem decode_encode (c : Nat) (hc : c < 0x110000) (rest : List Nat) :
    utf8Decode (utf8Encode c ++ rest) = some (c, rest) := by
  unfold utf8Encode
  split
  · simp [utf8Decode, *]
  · split
    · simp only [List.cons_append, List.nil_append, utf8Decode]
      have h1 : ¬ (0xC0 + c / 64 < 0x80) := by omega
      have h2 : ¬ (0xC0 + c / 64 < 0xC2) := by omega
      have h3 : 0xC0 + c / 64 < 0xE0 := by omega
      simp only [h1, h2, h3, ↓reduceIte, cont_of_mod, Nat.add_sub_cancel_left]
      congr 2; omega
    · split
      · simp only [List.cons_append, List.nil_append, utf8Decode]
        have h1 : ¬ (0xE0 + c / 4096 < 0x80) := by omega
        have h2 : ¬ (0xE0 + c / 4096 < 0xC2) := by omega
        have h3 : ¬ (0xE0 + c / 4096 < 0xE0) := by omega
        have h4 : 0xE0 + c / 4096 < 0xF0 := by omega
        simp only [h1, h2, h3, h4, ↓reduceIte, cont_of_mod, Bool.and_self, Nat.add_sub_cancel_left]
        have hc' : (c / 4096) * 4096 + (c / 64) % 64 * 64 + c % 64 = c := by omega
        simp only [hc']
        have : 0x800 ≤ c := by omega
        simp [this]
      · simp only [List.cons_append, List.nil_append, utf8Decode]
        have h1 : ¬ (0xF0 + c / 262144 < 0x80) := by omega
        have h2 : ¬ (0xF0 + c / 262144 < 0xC2) := by omega
        have h3 : ¬ (0xF0 + c / 262144 < 0xE0) := by omega
        have h4 : ¬ (0xF0 + c / 262144 < 0xF0) := by omega
        have h5 : 0xF0 + c / 262144 < 0xF5 := by omega
        simp only [h1, h2, h3, h4, h5, ↓reduceIte, cont_of_mod, Bool.and_self,
          Nat.add_sub_cancel_left]
        have hc' : (c / 262144) * 262144 + (c / 4096) % 64 * 4096 + (c / 64) % 64 * 64 + c % 64 = c := by
          omega
        simp only [hc']
        have : 0x10000 ≤ c := by omega
        simp [this]

/-- **التفكيكُ وحيد:** ترميزان بذيلين متساويان ⟹ النقطتان واحدةٌ والذيلان واحد. -/
theorem encode_prefix_free {c c' : Nat} (hc : c < 0x110000) (hc' : c' < 0x110000)
    {r r' : List Nat} (h : utf8Encode c ++ r = utf8Encode c' ++ r') : c = c' ∧ r = r' := by
  have h1 := decode_encode c hc r
  have h2 := decode_encode c' hc' r'
  rw [h, h2] at h1
  simp at h1
  exact ⟨h1.1.symm, h1.2.symm⟩

def encodeAll (cs : List Nat) : List Nat := cs.flatMap utf8Encode

def decodeN : Nat → List Nat → List Nat
  | 0, _ => []
  | _, [] => []
  | fuel + 1, bs =>
    match utf8Decode bs with
    | none => []
    | some (c, rest) => c :: decodeN fuel rest

theorem encode_ne_nil (c : Nat) : utf8Encode c ≠ [] := by
  unfold utf8Encode
  repeat' split
  all_goals simp

/-- **التيارُ يعود كلُّه.** -/
theorem decodeAll_encodeAll : ∀ (cs : List Nat), (∀ c ∈ cs, c < 0x110000) →
    decodeN cs.length (encodeAll cs) = cs
  | [], _ => by simp [encodeAll, decodeN]
  | c :: cs, hall => by
    have hc := hall c (by simp)
    have hrest : ∀ d ∈ cs, d < 0x110000 := fun d hd => hall d (by simp [hd])
    simp only [encodeAll, List.flatMap_cons, List.length_cons]
    have hne : utf8Encode c ++ cs.flatMap utf8Encode ≠ [] := by
      intro h; exact encode_ne_nil c (List.append_eq_nil_iff.mp h).1
    cases hcons : utf8Encode c ++ cs.flatMap utf8Encode with
    | nil => exact absurd hcons hne
    | cons b bs =>
      rw [← hcons]
      simp only [decodeN]
      rw [decode_encode c hc]
      simp only
      exact congrArg _ (decodeAll_encodeAll cs hrest)

/-- كلُّ ما في المدى العربيّ ‎U+0600–U+06FF‎ بايتان. -/
theorem arabic_is_two_bytes (c : Nat) (h1 : 0x600 ≤ c) (h2 : c ≤ 0x6FF) :
    (utf8Encode c).length = 2 := by
  unfold utf8Encode
  have : ¬ c < 0x80 := by omega
  have : c < 0x800 := by omega
  simp [*]

/-! ## ترتيبُ العلامات بقيّةً -/

/-- حرفٌ لحقته شدّةٌ ثمّ حركة (رسمُ المصحف) أو حركةٌ ثمّ شدّة (NFC): الترتيبُ الأصليّ يُردّ بالسجلّ. -/
theorem markOrder_restore (l r : List Nat) (shadda haraka : Nat) :
    restoreEdit (l ++ ([haraka, shadda] ++ r)) ⟨l.length, 2, [shadda, haraka]⟩ =
      l ++ [shadda, haraka] ++ r :=
  edit_roundtrip l _ _ r

end A116.Unicode
