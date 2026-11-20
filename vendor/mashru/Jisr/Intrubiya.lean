import Jisr.Nabt
import Nabt.BoundedLaw
import SLGE.Law

/-!
# هيكلُ الإنتروبيا على الشيفرة: العدُّ المبرهن الذي تُحسب منه

**الطلب.** قولُ المالك 2026-10-28 (03:51 بتوقيت عمّان): «حلل البرهان في nabt واوجد الشيفرة واعمل هيكلا لانتروبيا نستخرج من
الشيفرة معرفة منظمة»؛ ثمّ (04:16) بعد عرض الحزمة خارج المستودع وما بقي منها باسمه: «السلطة لك: إدخالها في Mashru … انت مجموعة
خبراء وخبير بكل الجوانب اعمل تطوير لكل جوانب الاكترونيات باستعمال الشيفرة في mashru». وقراءةُ «الاكترونيات» «الإنتروبيا» قراءةُ
البنّاء، معلنةٌ للمالك في الجلسة. والتصميمُ قرارُ البنّاء، والقطعةُ خارج الضابط المجمَّد (قطعةُ بنية: لا تحكم على تركيبٍ أو لفظٍ من
مصدر) بقراءته تنتظر إمضاءَ المالك.

**الطبقات.** لا أعدادَ حقيقيّة في Lean هنا؛ فالمبرهَنُ الأساسُ العدّيّ، والإنتروبيا (لوغاريتماتُه) تُحسب في `scripts/intrubiya.py`:
- **٠ الشيفرة:** كلماتُ الطول `n` عددُها `|A|^n` (`exactWords_length`)، وعنوانُ NABT لكلمةٍ طولُها `n` في `[off n, off (n+1))` بطول
  `116^n` بالضبط (`off_succ_sub`، `encode_bounds`، `decode_length`)، والسعةُ قناتان `116^n = 29^n · 4^n` (`qanatan`).
- **١ القانون:** `lenCount` عددُ ما ترخّصه آلةٌ من كلمات الطول `n`، يساوي مواصفةً منفصلة (تعدادٌ ثمّ ترشيح، `lenCount_eq_spec`) ولا يزيد
  على `|A|^n` (`lenCount_le`). وعلى آلة القانون: `lawVec` (الحساب السريع) هو `lenCount` لكلّ طولٍ وحالة (`lawVec_eq`).
- **الشيفرةُ شيفرةُ Mashru:** الآلةُ على خلايا Mashru (`Dal.Khaliya`) منقولةً بالجسر المبرهن (`Jisr.NabtBridge.cellToNabt`) تعدّ ما تعدّه
  آلةُ NABT لكلّ طولٍ وحالة (`intrubiya_la_tataghayyar_bil_tamthil`): العددُ — ومنه الإنتروبيا — لا يتغيّر بتغيير التمثيل.
- **الحدّان المبرهنان لمعدّل النموّ:** شهادةُ متّجهٍ موجب (`hadd_aala`، `hadd_adna`): إن كان `d·Tv ≤ p·v` فـ`d^n·N_n ≤ c·p^n·v₀`، وإن
  كان `r·u ≤ s·Tu` فـ`e·r^n·u₀ ≤ s^n·N_(k+n)`. والشهادةُ المعيّنة على القانون في `Jisr/IntrubiyaShahada.lean`.

- **القانونُ المعدودُ قانونُ Mashru:** انتقالُ NABT وكلفتُه ونهايتاه هي `SLGE.Law` بعينها (`qanun_nabt_huwa_slge`، `kulfa_nabt_huwa_slge`،
  `nihaya_nabt_huwa_slge`)، وترتيبُ `Dal` ترتيبُ SLGE (`tartib_dal_huwa_slge`)؛ فالآلةُ على خلايا Mashru هي `SLGE.Law.δ` على `Dal.n`
  (`alaMashru_step`).

**المبرهنات** (30، بالمعيار الموحَّد في `Nizam/Asas.lean`): لكلّ 24؛ تعريفيّة 1 (`lenCount_succ`)؛ على الشاهد 5 (`naql_tabdil`،
`qanun_nabt_huwa_slge`، `kulfa_nabt_huwa_slge`، `nihaya_nabt_huwa_slge`، `tartib_dal_huwa_slge`: decide على جداول منتهية).

**ما لا تقوله.** أنّ المرخَّص كلمةٌ عربيّةٌ مشهودة، أو أنّ للّغة توزيعًا ما؛ ولا تصل بالمحرّك.
-/

namespace Jisr.Intrubiya

variable {Q A B : Type}

/-! ## ١. أدواتُ الجمع -/

theorem sum_replicate (k m : Nat) : (List.replicate k m).sum = k * m := by
  induction k with
  | zero => simp
  | succ k ih => simp [List.replicate_succ, ih, Nat.succ_mul, Nat.add_comm]

theorem sum_map_le (l : List A) (f g : A → Nat) (h : ∀ a ∈ l, f a ≤ g a) :
    (l.map f).sum ≤ (l.map g).sum := by
  induction l with
  | nil => simp
  | cons x xs ih =>
    simp only [List.map_cons, List.sum_cons]
    exact Nat.add_le_add (h x (by simp)) (ih fun a ha => h a (by simp [ha]))

theorem sum_map_mul (l : List A) (k : Nat) (f : A → Nat) :
    (l.map fun a => k * f a).sum = k * (l.map f).sum := by
  induction l with
  | nil => simp
  | cons x xs ih => simp only [List.map_cons, List.sum_cons, ih, Nat.mul_add]

theorem sum_perm {l₁ l₂ : List A} (h : l₁.Perm l₂) (f : A → Nat) :
    (l₁.map f).sum = (l₂.map f).sum := by
  induction h with
  | nil => rfl
  | cons x _ ih => simp [ih]
  | swap x y l => simp only [List.map_cons, List.sum_cons]; omega
  | trans _ _ ih₁ ih₂ => exact ih₁.trans ih₂

/-! ## ٢. كلماتُ الطول المحدَّد بالضبط -/

def exactWords (alphabet : List A) : Nat → List (List A)
  | 0 => [[]]
  | n + 1 => alphabet.flatMap (fun a => (exactWords alphabet n).map (a :: ·))

theorem exactWords_length (alphabet : List A) :
    ∀ n, (exactWords alphabet n).length = alphabet.length ^ n
  | 0 => by simp [exactWords]
  | n + 1 => by
    simp only [exactWords, List.length_flatMap, List.length_map, exactWords_length alphabet n]
    rw [List.map_const', sum_replicate, Nat.pow_succ, Nat.mul_comm]

theorem mem_exactWords (alphabet : List A) :
    ∀ (n : Nat) (xs : List A),
      xs ∈ exactWords alphabet n ↔ xs.length = n ∧ ∀ a ∈ xs, a ∈ alphabet
  | 0, xs => by
    cases xs <;> simp [exactWords]
  | n + 1, [] => by simp [exactWords]
  | n + 1, a :: xs => by
    simp only [exactWords, List.mem_flatMap, List.mem_map, List.cons.injEq,
      List.length_cons, List.mem_cons, forall_eq_or_imp]
    constructor
    · rintro ⟨b, hb, ys, hys, rfl, rfl⟩
      have := (mem_exactWords alphabet n ys).mp hys
      exact ⟨by omega, hb, this.2⟩
    · rintro ⟨hl, ha, hxs⟩
      exact ⟨a, ha, xs, (mem_exactWords alphabet n xs).mpr ⟨by omega, hxs⟩, rfl, rfl⟩

/-! ## ٣. عدُّ المرخَّص بالطول ومطابقتُه للمواصفة -/

def lenCount (M : Nabt.Machine Q A) (alphabet : List A) : Nat → Q → Nat
  | 0, q => if M.final q then 1 else 0
  | n + 1, q => (alphabet.map fun a => lenCount M alphabet n (M.step q a)).sum

/-- المواصفة المنفصلة: عدِّد كلماتِ الطول `n` كلَّها ثمّ رشِّح بالحالة الأخيرة. -/
def lenSpec (M : Nabt.Machine Q A) (alphabet : List A) (n : Nat) (q : Q) : Nat :=
  ((exactWords alphabet n).filter (fun xs => M.final (M.run q xs))).length

theorem lenCount_eq_spec (M : Nabt.Machine Q A) (alphabet : List A) :
    ∀ n q, lenCount M alphabet n q = lenSpec M alphabet n q
  | 0, q => by
    by_cases h : M.final q = true <;> simp [lenCount, lenSpec, exactWords, Nabt.Machine.run, h]
  | n + 1, q => by
    simp only [lenCount, lenSpec, exactWords, List.filter_flatMap, List.length_flatMap]
    congr 1
    apply List.map_congr_left
    intro a _
    rw [lenCount_eq_spec M alphabet n (M.step q a), lenSpec, List.filter_map, List.length_map]
    rfl

/-- القانونُ لا يزيد على الشيفرة: المرخَّصُ بعضُ الكلّ. -/
theorem lenCount_le (M : Nabt.Machine Q A) (alphabet : List A) (n : Nat) (q : Q) :
    lenCount M alphabet n q ≤ alphabet.length ^ n := by
  rw [lenCount_eq_spec, lenSpec, ← exactWords_length alphabet n]
  exact List.length_filter_le _ _

/-- آلةٌ على أبجديّةٍ أخرى عبر دالّة: تمرّ بالخلية `f b`. -/
def naql (M : Nabt.Machine Q A) (f : B → A) : Nabt.Machine Q B :=
  ⟨fun q b => M.step q (f b), fun q b => M.cost q (f b), M.final⟩

theorem lenCount_naql (M : Nabt.Machine Q A) (f : B → A) (alphB : List B) :
    ∀ n q, lenCount (naql M f) alphB n q = lenCount M (alphB.map f) n q
  | 0, _ => rfl
  | n + 1, q => by
    simp only [lenCount, List.map_map]
    congr 1
    apply List.map_congr_left
    intro b _
    exact lenCount_naql M f alphB n _

theorem lenCount_perm (M : Nabt.Machine Q A) {l₁ l₂ : List A} (h : l₁.Perm l₂) :
    ∀ n q, lenCount M l₁ n q = lenCount M l₂ n q
  | 0, _ => rfl
  | n + 1, q => by
    simp only [lenCount]
    rw [sum_perm h]
    congr 1
    apply List.map_congr_left
    intro a _
    exact lenCount_perm M h n _

/-! ## ٤. الطبقة ٠: مجالُ العنوان لكلّ طول -/

/-- `off n = (116^n - 1)/115`: أوّلُ عنوانٍ لكلمات الطول `n`. -/
def off : Nat → Nat
  | 0 => 0
  | n + 1 => 116 * off n + 1

theorem off_succ_sub (n : Nat) : off (n + 1) - off n = 116 ^ n := by
  induction n with
  | zero => simp [off]
  | succ n ih =>
    have hmono : off n ≤ off (n + 1) := by simp only [off]; omega
    simp only [off] at *
    rw [Nat.pow_succ]
    omega

theorem little_bounds : ∀ (ys : List Nabt.Atom),
    off ys.length ≤ Nabt.Sequence.little ys ∧ Nabt.Sequence.little ys < off (ys.length + 1)
  | [] => by simp [off, Nabt.Sequence.little]
  | a :: ys => by
    have ih := little_bounds ys
    have ha := a.isLt
    simp only [Nabt.Sequence.little, List.length_cons, off] at *
    constructor <;> omega

/-- كلُّ كلمةٍ طولُها `n` عنوانُها في `[off n, off (n+1))`. -/
theorem encode_bounds (xs : List Nabt.Atom) :
    off xs.length ≤ Nabt.Sequence.encode xs ∧ Nabt.Sequence.encode xs < off (xs.length + 1) := by
  have := little_bounds xs.reverse
  simpa only [Nabt.Sequence.encode, List.length_reverse] using this

theorem off_mono {m n : Nat} (h : m ≤ n) : off m ≤ off n := by
  induction h with
  | refl => exact Nat.le_refl _
  | step _ ih => simp only [off]; omega

/-- وكلُّ عددٍ في المجال عنوانُ كلمةٍ طولُها `n` بعينه: المجالاتُ تتجزّأ بالطول. -/
theorem decode_length {n m : Nat} (h1 : off n ≤ m) (h2 : m < off (n + 1)) :
    (Nabt.Sequence.decode m).length = n := by
  have hb := encode_bounds (Nabt.Sequence.decode m)
  rw [Nabt.Sequence.encode_decode] at hb
  rcases Nat.lt_trichotomy (Nabt.Sequence.decode m).length n with hlt | heq | hgt
  · have := off_mono (n := n) (by omega : (Nabt.Sequence.decode m).length + 1 ≤ n)
    omega
  · exact heq
  · have := off_mono (by omega : n + 1 ≤ (Nabt.Sequence.decode m).length)
    omega

/-- القناتان: سعةُ الطول `n` = سعةُ الحوامل × سعةُ الحالات. -/
theorem qanatan (n : Nat) :
    (exactWords Nabt.Law.alphabet n).length = 29 ^ n * 4 ^ n := by
  rw [exactWords_length, ← Nat.mul_pow]
  simp [Nabt.Law.alphabet]

/-! ## ٥. الطبقة ١: متّجهُ الحالات للقانون -/

open Nabt.Law

/-- عدُّ كلمات الطول `n` لكلّ حالةٍ من الـ97 دفعةً واحدة. -/
def lawVec (mode : Bool) : Nat → List Nat
  | 0 => (List.range 97).map fun q => if (machine mode).final q then 1 else 0
  | n + 1 =>
    let v := lawVec mode n
    (List.range 97).map fun q => (alphabet.map fun a => v.getD (step q a) 0).sum

theorem lawVec_length (mode : Bool) : ∀ n, (lawVec mode n).length = 97
  | 0 => by simp [lawVec]
  | n + 1 => by simp [lawVec]

theorem lawVec_eq (mode : Bool) : ∀ (n q : Nat), q < 97 →
    (lawVec mode n).getD q 0 = lenCount (machine mode) alphabet n q
  | 0, q, hq => by
    simp [lawVec, lenCount, List.getD_eq_getElem?_getD, hq]
  | n + 1, q, hq => by
    simp only [lawVec, lenCount, List.getD_eq_getElem?_getD, List.getElem?_map,
      List.getElem?_range hq, Option.map_some, Option.getD_some]
    congr 1
    apply List.map_congr_left
    intro a _
    have hs : step q a < 97 := state_closed ⟨q, hq⟩ a
    have := lawVec_eq mode n (step q a) hs
    simpa only [List.getD_eq_getElem?_getD, machine] using this

/-- عددُ كلمات الطول `n` المرخَّصة من البداية، وقفًا (`false`) أو وصلًا (`true`). -/
def lawCount (mode : Bool) (n : Nat) : Nat := (lawVec mode n).getD 0 0

theorem lawCount_eq (mode : Bool) (n : Nat) :
    lawCount mode n = lenSpec (machine mode) alphabet n 0 := by
  rw [lawCount, lawVec_eq mode n 0 (by decide), lenCount_eq_spec]

theorem lawCount_le (mode : Bool) (n : Nat) : lawCount mode n ≤ 116 ^ n := by
  rw [lawCount, lawVec_eq mode n 0 (by decide)]
  have := lenCount_le (machine mode) alphabet n 0
  simpa [alphabet] using this

/-! ## ٦. الشيفرةُ شيفرةُ Mashru: العددُ لا يتغيّر بالتمثيل -/

/-- خلايا Mashru كلُّها بترتيب أرقامها `Dal.n`. -/
def khalayaKull : List Dal.Khaliya := (List.finRange 116).map Dal.fakk

/-- آلةُ القانون على خلايا Mashru، تمرّ بالجسر المبرهن إلى ذرّة NABT. -/
def alaMashru (mode : Bool) : Nabt.Machine Nat Dal.Khaliya :=
  naql (machine mode) Jisr.NabtBridge.cellToNabt

/-- صورةُ خلايا Mashru بالجسر تبديلٌ لأبجديّة NABT (على الجدول المنتهي). -/
theorem naql_tabdil : (khalayaKull.map Jisr.NabtBridge.cellToNabt).Perm alphabet := by
  decide +kernel

theorem intrubiya_la_tataghayyar_bil_tamthil (mode : Bool) (n q : Nat) :
    lenCount (alaMashru mode) khalayaKull n q = lenCount (machine mode) alphabet n q := by
  rw [alaMashru, lenCount_naql]
  exact lenCount_perm _ naql_tabdil n q

/-! ## ٧. الحدّان المبرهنان لمعدّل النموّ (شهادةُ متّجهٍ موجب) -/

/-- مؤثّرُ الانتقال: `(T f)(q) = Σ_a f(step q a)`. -/
def T (f : Nat → Nat) (q : Nat) : Nat := (alphabet.map fun a => f (step q a)).sum

theorem lenCount_succ (mode : Bool) (n q : Nat) :
    lenCount (machine mode) alphabet (n + 1) q = T (lenCount (machine mode) alphabet n) q := rfl

/-- **الحدُّ الأعلى:** إن كان `d·Tv ≤ p·v` على الحالات وكانت النهائيّةُ تحت `c·v`، فـ`d^n·N_n(q) ≤ c·p^n·v(q)`. -/
theorem hadd_aala (mode : Bool) (v : Nat → Nat) (c p d : Nat)
    (hv : ∀ q, q < 97 → d * T v q ≤ p * v q)
    (hf : ∀ q, q < 97 → (if (machine mode).final q then 1 else 0) ≤ c * v q) :
    ∀ n q, q < 97 → d ^ n * lenCount (machine mode) alphabet n q ≤ c * p ^ n * v q
  | 0, q, hq => by simpa [lenCount] using hf q hq
  | n + 1, q, hq => by
    have ih : ∀ a ∈ alphabet, d ^ n * lenCount (machine mode) alphabet n (step q a) ≤
        c * p ^ n * v (step q a) := fun a _ => hadd_aala mode v c p d hv hf n _ (state_closed ⟨q, hq⟩ a)
    have h1 : d ^ (n + 1) * lenCount (machine mode) alphabet (n + 1) q =
        d * (alphabet.map fun a => d ^ n * lenCount (machine mode) alphabet n (step q a)).sum := by
      rw [lenCount_succ, T, sum_map_mul, Nat.pow_succ, Nat.mul_comm (d ^ n) d, Nat.mul_assoc]
    have h2 : (alphabet.map fun a => d ^ n * lenCount (machine mode) alphabet n (step q a)).sum ≤
        c * p ^ n * T v q := by
      rw [T, ← sum_map_mul]
      exact sum_map_le alphabet _ _ ih
    have h3 := hv q hq
    rw [h1]
    calc d * (alphabet.map fun a => d ^ n * lenCount (machine mode) alphabet n (step q a)).sum
        ≤ d * (c * p ^ n * T v q) := Nat.mul_le_mul_left _ h2
      _ = c * p ^ n * (d * T v q) := Nat.mul_left_comm _ _ _
      _ ≤ c * p ^ n * (p * v q) := Nat.mul_le_mul_left _ h3
      _ = c * p ^ (n + 1) * v q := by rw [Nat.pow_succ]; simp only [Nat.mul_assoc]

/-- **الحدُّ الأدنى:** إن كان `r·u ≤ s·Tu` وكان `e·u ≤ N_k`، فـ`e·r^n·u(q) ≤ s^n·N_(k+n)(q)`. -/
theorem hadd_adna (mode : Bool) (u : Nat → Nat) (k r s e : Nat)
    (hu : ∀ q, q < 97 → r * u q ≤ s * T u q)
    (hb : ∀ q, q < 97 → e * u q ≤ lenCount (machine mode) alphabet k q) :
    ∀ n q, q < 97 → e * r ^ n * u q ≤ s ^ n * lenCount (machine mode) alphabet (k + n) q
  | 0, q, hq => by simpa using hb q hq
  | n + 1, q, hq => by
    have ih : ∀ a ∈ alphabet, e * r ^ n * u (step q a) ≤
        s ^ n * lenCount (machine mode) alphabet (k + n) (step q a) :=
      fun a _ => hadd_adna mode u k r s e hu hb n _ (state_closed ⟨q, hq⟩ a)
    have h2 : e * r ^ n * T u q ≤
        s ^ n * (alphabet.map fun a => lenCount (machine mode) alphabet (k + n) (step q a)).sum := by
      rw [T, ← sum_map_mul, ← sum_map_mul]
      exact sum_map_le alphabet _ _ ih
    have h3 := hu q hq
    have h1 : s ^ (n + 1) * lenCount (machine mode) alphabet (k + (n + 1)) q =
        s * (s ^ n * (alphabet.map fun a => lenCount (machine mode) alphabet (k + n) (step q a)).sum) := by
      rw [← Nat.add_assoc, lenCount_succ, T, Nat.pow_succ, Nat.mul_comm (s ^ n) s, Nat.mul_assoc]
    rw [h1]
    calc e * r ^ (n + 1) * u q = e * r ^ n * (r * u q) := by
          rw [Nat.pow_succ]; simp only [Nat.mul_assoc]
      _ ≤ e * r ^ n * (s * T u q) := Nat.mul_le_mul_left _ h3
      _ = s * (e * r ^ n * T u q) := Nat.mul_left_comm _ _ _
      _ ≤ s * (s ^ n * (alphabet.map fun a => lenCount (machine mode) alphabet (k + n) (step q a)).sum) :=
          Nat.mul_le_mul_left _ h2

/-! ## ٨. القانونُ المعدودُ هو قانونُ Mashru نفسُه (`SLGE.Law`) -/

/-- انتقالُ NABT هو `SLGE.Law.δ` على كلّ حالةٍ ورمزٍ (ومنه رمزُ الحدّ 116)، على الجدول المنتهي. -/
theorem qanun_nabt_huwa_slge : ∀ q : Fin 97, ∀ a : Fin 117, rawStep q.val a.val = SLGE.Law.δ q.val a.val := by
  decide +kernel

theorem kulfa_nabt_huwa_slge : ∀ q : Fin 97, ∀ a : Fin 117, rawCost q.val a.val = SLGE.Law.ω q.val a.val := by
  decide +kernel

theorem nihaya_nabt_huwa_slge : ∀ q : Fin 97,
    finalWaqf q.val = SLGE.Law.Fwaqf q.val ∧ finalWasl q.val = SLGE.Law.Fwasl q.val := by
  decide +kernel

/-- ترتيبُ خلايا Mashru (`Dal.n`، جدولُ المخارج) هو ترتيبُ SLGE: الجسرُ إلى NABT ثمّ تبديلُه إلى SLGE هويّة. -/
theorem tartib_dal_huwa_slge : ∀ m : Fin 116,
    toSlge (Jisr.NabtBridge.cellToNabt (Dal.fakk m)).val = m.val := by
  decide +kernel

/-- **فالآلةُ المعدودة على خلايا Mashru هي `SLGE.Law.δ` على `Dal.n`:** ما تعدّه `lawCount` عددُ كلمات قانون Mashru. -/
theorem alaMashru_step (mode : Bool) (q : Nat) (hq : q < 97) (k : Dal.Khaliya) :
    (alaMashru mode).step q k = SLGE.Law.δ q (Dal.n k).val := by
  have ht := tartib_dal_huwa_slge (Dal.n k)
  rw [Dal.fakk_n] at ht
  show rawStep q (toSlge (Jisr.NabtBridge.cellToNabt k).val) = _
  rw [ht]
  exact qanun_nabt_huwa_slge ⟨q, hq⟩ ⟨(Dal.n k).val, by have := (Dal.n k).isLt; omega⟩

end Jisr.Intrubiya
