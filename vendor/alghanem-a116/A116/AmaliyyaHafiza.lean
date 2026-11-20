import A116.Numbering
import A116.JisrWazaif

/-!
# العمليّةُ المحفوظة: عقدُ الجسر الحافظ للعمليّة ومجالِها، وأوّلُ عمليّتين على عدد الخانات (ADR ١٢١)

الخطّةُ الثانية (`docs/protocol/khitta-2.md`، م١) تطلب أن يكون كلُّ انتقالٍ على النصّ عمليّةً على تمثيله العدديّ. ورفع المالك
(2026-10-21 20:27) تحليلًا يقترح «ترميزًا يحفظ العمليات» بقانونين: حفظُ العمليّة وحفظُ مجالها. وهنا يُكتبان عقدًا عامًّا على
`JisrWazaif.Murakhkhas`، ثمّ تُبرهن أوّلُ عمليّتين على `Numbering.atomNumber`.

## العقد (لكلّ جسرين ولكلّ عمليّةٍ جزئيّة)

`Yahfaz J K f g`: ‎g (J.enc a) = (f a).map K.enc‎ لكلّ ‎a‎. ومنه:
* `majal`: المجالُ محفوظٌ **على صور الترميز** — ‎f‎ معرَّفةٌ على ‎a‎ ⟺ ‎g‎ معرَّفةٌ على ‎J.enc a‎؛ والعقدُ لا يقيّد ‎g‎ خارجها.
* `natija`: النتيجةُ ترميزُ النتيجة.
* `tarkib`: العمليّتان المحفوظتان تتركّبان عمليّةً محفوظة.
* `marjii`: التنفيذُ المرجعيّ (فكٌّ ثمّ عمليّةٌ ثمّ ترميز) يستوفي العقد دائمًا؛ فالعملُ الهندسيُّ تنفيذٌ مباشرٌ يُبرهن أنّه يساويه.

## العمليّتان على عدد الخانات (لكلّ سلسلة)

* `atomNumber_append`: **‎F(u ++ v) = 116^|v|·F(u) + F(v)‎** — الوصلُ ضربٌ وجمع، و`F [] = 0` محايدُه (`atomNumber_nil`).
* `wasl_yahfaz`: الوصلُ على الزوج (العدد، الطول) عمليّةٌ محفوظة بالمعنى أعلاه، والزوجُ جسرٌ يُردّ (تباين لا تقابل).
* `badal`: تبديلُ خانةٍ في موضعها يغيّر العددَ بفرق رقمَي الخانتين مضروبًا في ‎116^(ما بعدها)‎.

الحدّ (معلن): هذا عددُ الخانات ‎F‎ لا عددُ الشهادة ‎P(F, rank)‎؛ والوصلُ هنا حسابٌ لا ترخيص — قبولُه لغةً بقيد الحدّ
(`Hadd.strictJoinB`) وحدودُ الكلمات بقيّةٌ محفوظة (`JisrWazaif.tarkib`)؛ والتبديلُ يحسب أثرَ تغيير الحركة ولا يرخّصه صرفًا.
-/

set_option autoImplicit false

namespace A116.AmaliyyaHafiza

open A116 A116.JisrWazaif A116.Numbering

/-! ## ١. العقد -/

variable {A B A' B' A'' B'' : Type}

/-- **العمليّةُ المحفوظة:** تنفيذُ ‎g‎ على الترميز يعطي ترميزَ نتيجة ‎f‎، ويرفض حيث ترفض. -/
def Yahfaz (J : Murakhkhas A B) (K : Murakhkhas A' B') (f : A → Option A') (g : B → Option B') : Prop :=
  ∀ a, g (J.enc a) = (f a).map K.enc

/-- **المجالُ محفوظ.** -/
theorem majal {J : Murakhkhas A B} {K : Murakhkhas A' B'} {f : A → Option A'} {g : B → Option B'}
    (h : Yahfaz J K f g) (a : A) : (f a).isSome = (g (J.enc a)).isSome := by
  rw [h a]; cases f a <;> rfl

/-- **النتيجةُ ترميزُ النتيجة.** -/
theorem natija {J : Murakhkhas A B} {K : Murakhkhas A' B'} {f : A → Option A'} {g : B → Option B'}
    (h : Yahfaz J K f g) {a : A} {a' : A'} (hf : f a = some a') : g (J.enc a) = some (K.enc a') := by
  rw [h a, hf]; rfl

/-- **ما ترفضه العمليّةُ يرفضه تنفيذُها المرمَّز.** -/
theorem rafd {J : Murakhkhas A B} {K : Murakhkhas A' B'} {f : A → Option A'} {g : B → Option B'}
    (h : Yahfaz J K f g) {a : A} (hf : f a = none) : g (J.enc a) = none := by
  rw [h a, hf]; rfl

/-- **التركيب:** عمليّتان محفوظتان تتركّبان عمليّةً محفوظة. -/
theorem tarkib {J : Murakhkhas A B} {K : Murakhkhas A' B'} {L : Murakhkhas A'' B''}
    {f : A → Option A'} {g : B → Option B'} {f' : A' → Option A''} {g' : B' → Option B''}
    (h : Yahfaz J K f g) (h' : Yahfaz K L f' g') :
    Yahfaz J L (fun a => (f a).bind f') (fun b => (g b).bind g') := by
  intro a
  simp only [h a]
  cases f a with
  | none => rfl
  | some x => simp only [Option.map_some, Option.bind_some]; exact h' x

/-- **التنفيذُ المرجعيّ** (فكٌّ ثمّ عمليّةٌ ثمّ ترميز) يستوفي العقد لكلّ عمليّة. -/
theorem marjii (J : Murakhkhas A B) (K : Murakhkhas A' B') (f : A → Option A') :
    Yahfaz J K f (fun b => ((J.dec b).bind f).map K.enc) := by
  intro a
  simp only [J.radd a, Option.bind_some]

/-! ## ٢. الوصلُ على عدد الخانات -/

theorem foldl_shift' (f : Nat) : ∀ (w : List Nat) (acc : Nat),
    w.foldl (fun a d => f * a + d) acc = acc * f ^ w.length + w.foldl (fun a d => f * a + d) 0
  | [], acc => by simp
  | d :: ds, acc => by
    simp only [List.foldl_cons, List.length_cons, Nat.mul_zero, Nat.zero_add]
    rw [foldl_shift' f ds (f * acc + d), foldl_shift' f ds d, Nat.pow_succ]
    rw [Nat.add_mul, Nat.mul_comm (f ^ ds.length) f, ← Nat.mul_assoc, Nat.mul_comm acc f,
      Nat.add_assoc]

/-- قيمةُ الأرقام على الوصل. -/
theorem digits_append (f : Nat) (u v : List Nat) :
    digits f (u ++ v) = f ^ v.length * digits f u + digits f v := by
  unfold digits
  rw [List.foldl_append, foldl_shift', Nat.mul_comm]

/-- ‎O(n) = Σ_{j<n} 116ʲ‎ هو قيمةُ أرقامٍ كلُّها واحد. -/
theorem geo_eq_digits (f : Nat) : ∀ n, geo f n = digits f (List.replicate n 1)
  | 0 => rfl
  | n + 1 => by
    rw [List.replicate_succ, digits_cons, List.length_replicate, geo, geo_eq_digits f n, Nat.one_mul,
      Nat.add_comm]

theorem replicate_add' (x : Nat) : ∀ m n, List.replicate (m + n) x = List.replicate m x ++ List.replicate n x
  | 0, n => by simp
  | m + 1, n => by
    rw [Nat.add_right_comm, List.replicate_succ, List.replicate_succ, replicate_add' x m n,
      List.cons_append]

theorem geo_add (f m n : Nat) : geo f (m + n) = f ^ n * geo f m + geo f n := by
  rw [geo_eq_digits, geo_eq_digits, geo_eq_digits, replicate_add', digits_append,
    List.length_replicate]

theorem atomNumber_nil : atomNumber [] = 0 := rfl

/-- **الوصلُ عمليّةٌ عدديّة:** ‎F(u ++ v) = 116^|v|·F(u) + F(v)‎، لكلّ سلسلتين. -/
theorem atomNumber_append (u v : List Cell) :
    atomNumber (u ++ v) = 116 ^ v.length * atomNumber u + atomNumber v := by
  rw [atomNumber_closed, atomNumber_closed, atomNumber_closed, List.length_append, geo_add,
    List.map_append, digits_append, List.length_map, Nat.mul_add]
  ac_rfl

/-- ترميزُ السلسلة زوجًا (عددُها، طولُها): جسرٌ يُردّ (تباين، و`dec` يرفض زوجًا لا يوافق طولُه عددَه). والطولُ يُحمل لتيسير
 حساب الوصل (تعيينُ البنّاء)؛ وهو دالّةٌ في العدد بـ`atomNumber_injective`. -/
noncomputable def zawj : Murakhkhas (List Cell) (Nat × Nat) where
  enc w := (atomNumber w, w.length)
  dec p := if (Classical.choose (atomNumber_surjective p.1)).length = p.2
    then some (Classical.choose (atomNumber_surjective p.1)) else none
  radd w := by
    have hc := Classical.choose_spec (atomNumber_surjective (atomNumber w))
    have e := atomNumber_injective hc
    simp only [e, ite_true]
  licA _ := True
  licB _ := True
  naql _ _ := trivial

/-- الوصلُ على الأزواج: ‎(x, m) ⊙ (y, n) = (116ⁿ·x + y, m + n)‎. -/
def wasl (p q : Nat × Nat) : Nat × Nat := (116 ^ q.2 * p.1 + q.1, p.2 + q.2)

/-- **الوصلُ محفوظ:** ترميزُ الموصول وصلُ الترميزين. -/
theorem wasl_enc (u v : List Cell) : zawj.enc (u ++ v) = wasl (zawj.enc u) (zawj.enc v) := by
  simp only [zawj, wasl, atomNumber_append, List.length_append]

/-- وبصيغة العقد: العمليّةُ «صِلْ بـ‎v‎» وتنفيذُها على الأزواج. -/
theorem wasl_yahfaz (v : List Cell) :
    Yahfaz zawj zawj (fun u => some (u ++ v)) (fun p => some (wasl p (zawj.enc v))) := by
  intro u
  simp only [Option.map_some, wasl_enc]

theorem wasl_assoc (p q r : Nat × Nat) : wasl (wasl p q) r = wasl p (wasl q r) := by
  obtain ⟨x, m⟩ := p; obtain ⟨y, n⟩ := q; obtain ⟨z, k⟩ := r
  simp only [wasl, Prod.mk.injEq, Nat.pow_add, Nat.mul_add, Nat.add_assoc]
  constructor
  · rw [← Nat.mul_assoc, Nat.mul_comm (116 ^ k) (116 ^ n)]
  · trivial

theorem wasl_sifr (p : Nat × Nat) : wasl (0, 0) p = p ∧ wasl p (0, 0) = p := by
  obtain ⟨x, m⟩ := p
  simp [wasl]

/-! ## ٣. التبديلُ في الموضع -/

/-- **تبديلُ خانةٍ في موضعها:** الفرقُ فرقُ الرقمين مضروبًا في ‎116^|v|‎ (بصيغة الجمع في ℕ). -/
theorem badal (u v : List Cell) (c c' : Cell) :
    atomNumber (u ++ c' :: v) + bridgeIndex c * 116 ^ v.length =
      atomNumber (u ++ c :: v) + bridgeIndex c' * 116 ^ v.length := by
  have e : ∀ d : Cell, atomNumber (u ++ d :: v) =
      116 ^ (v.length + 1) * atomNumber u +
        (116 ^ v.length + bridgeIndex d * 116 ^ v.length + atomNumber v) := by
    intro d
    rw [atomNumber_append, List.length_cons, atomNumber_closed (d :: v), atomNumber_closed v,
      List.length_cons, geo, List.map_cons, digits_cons, List.length_map]
    omega
  rw [e c, e c']
  omega

/-! ## ٤. الشاهد -/

/-- «كَتَبَ» و«كُتِبَ» بترتيب الجسر: ‎[84, 8, 4]‎ و‎[85, 10, 4]‎. -/
def kataba : List Cell := [bridgeCell 84, bridgeCell 8, bridgeCell 4]
def kutiba : List Cell := [bridgeCell 85, bridgeCell 10, bridgeCell 4]

theorem shahid_raqm :
    kataba.map bridgeIndex = [84, 8, 4] ∧ kutiba.map bridgeIndex = [85, 10, 4] ∧
      atomNumber [bridgeCell 84] = 85 ∧ atomNumber [bridgeCell 8, bridgeCell 4] = 1049 ∧
      atomNumber kutiba = 1158497 ∧ atomNumber kataba = 1144809 := by
  decide

/-- والوصلُ على الشاهد: ‎116²·85 + 1049 = 1,144,809‎ من `atomNumber_append` لا من الحساب وحدَه. -/
theorem shahid_wasl : atomNumber kataba = 116 ^ 2 * atomNumber [bridgeCell 84] +
    atomNumber [bridgeCell 8, bridgeCell 4] :=
  atomNumber_append [bridgeCell 84] [bridgeCell 8, bridgeCell 4]

end A116.AmaliyyaHafiza
