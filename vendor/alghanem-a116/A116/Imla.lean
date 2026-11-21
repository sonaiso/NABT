import A116.Unicode
import A116.Hamza
import A116.Field112

/-!
# الإملاءُ والرسمُ بجسر يونيكود (ADR ٨٤)

أمرُ المالك (2026-10-16): «جسرُ الترميز يونيكود … ونعمل Lean للإملاء مع جسر يونيكود للرسم … ضروريٌّ عملُ Lean».

## الطبقات الثلاث

١. **الصورةُ القانونيّة** (`render`): كلُّ خانةٍ نقطتا يونيكود — الحرفُ ثمّ علامتُه (فتحة ‎U+064E‎، ضمّة ‎U+064F‎،
   كسرة ‎U+0650‎، سكون ‎U+0652‎) — وهي ذرّاتُ الشهادة في البوّابة بعينها (`gate.enter(...).atoms`،
   يفحصها `tests/test_imla.py` على المصحف كلِّه).
٢. **البايتات** (`Unicode.encodeAll`): UTF-8، وكلُّ خانةٍ أربعةُ بايتات.
٣. **الإملاء** (`imla`): الهمزةُ تُكتب على كرسيٍّ من خمسة (أ إ ؤ ئ ء) بقاعدةٍ من السياق، والمثلان أوّلُهما ساكنٌ
   وثانيهما متحرّكٌ يُكتبان حرفًا وشدّةً وحركة.

## ما يُبرهَن (لكلّ كلمة، لا على شواهد)

* `letterCp_chars`: جدولُ نقاط الحروف هو نقاطُ حروف `Field112.carriers29` بأعيانها.
* `parse_render`: القراءةُ بعد الصورة القانونيّة هويّة.
* `bytes_radd`، `bytes_len`: البايتاتُ تُقرأ إلى الخانات بأعيانها، وطولُها أربعةُ أمثال الخانات.
* `imla_radd`: **لأيّ قاعدةِ كرسيّ** تُقرأ الكلمةُ المكتوبة إملاءً إلى خاناتها بأعيانها — فالكرسيُّ والشدّةُ لا
  يُضيعان شيئًا؛ و`kursi_la_yahmil`: قاعدتا كرسيٍّ مختلفتان تُقرآن إلى الخانات نفسِها، و`kursi_yaghayyir_rasm`:
  ويختلف بهما الرسم — فالكرسيُّ رسمٌ لا خانة.
* `kursiHamza` مثولٌ لقاعدة `Hamza.seatOf` على السياق.

ما لا يُبرهَن هنا: التنوينُ والتاءُ المربوطة والألفُ المقصورة والألفُ الخنجريّة وواوُ «أولئك» — هي قواعدُ
`gate/residue.py` و`A116.Residue` على مستوى الرموز (`IMLA_RESIDUE_RULES_AT_GLYPH_LEVEL`).
-/

namespace A116.Imla

open A116 A116.Unicode

/-! ## ١. الصورة القانونيّة -/

/-- نقاطُ الحوامل التسعة والعشرين بترتيب `carriers29`. -/
def letterCp : List Nat :=
  [0x627, 0x628, 0x62A, 0x62B, 0x62C, 0x62D, 0x62E, 0x62F, 0x630, 0x631, 0x632, 0x633, 0x634, 0x635,
   0x636, 0x637, 0x638, 0x639, 0x63A, 0x641, 0x642, 0x643, 0x644, 0x645, 0x646, 0x647, 0x648, 0x64A,
   0x621]

/-- **الجدولُ نقاطُ حروف الحوامل بأعيانها.** -/
theorem letterCp_chars : letterCp = Field112.carriers29.map Char.toNat := by decide

def cpL (k : Fin carrierCount) : Nat := letterCp.getD k.val 0

def cpM : Haraka → Nat
  | .fatha => 0x64E
  | .damma => 0x64F
  | .kasra => 0x650
  | .sukun => 0x652

def shadda : Nat := 0x651

def renderC (c : Cell) : List Nat := [cpL c.carrier, cpM c.haraka]

/-- الصورةُ القانونيّة: الحرفُ ثمّ علامتُه، خانةً خانة. -/
def render (w : List Cell) : List Nat := w.flatMap renderC

def fromL (n : Nat) : Option (Fin carrierCount) := (List.finRange carrierCount).find? (cpL · == n)

def fromM (n : Nat) : Option Haraka := Haraka.all.find? (cpM · == n)

theorem fromL_cpL : ∀ k, fromL (cpL k) = some k := by decide

theorem fromM_cpM : ∀ h, fromM (cpM h) = some h := by intro h; cases h <;> decide

theorem fromM_shadda : fromM shadda = none := by decide

theorem cpM_ne_shadda : ∀ h, cpM h ≠ shadda := by intro h; cases h <;> decide

def parse : List Nat → Option (List Cell)
  | a :: b :: rest =>
    match fromL a, fromM b, parse rest with
    | some l, some h, some t => some (⟨l, h⟩ :: t)
    | _, _, _ => none
  | [] => some []
  | [_] => none

/-- **القراءةُ بعد الصورة هويّة.** -/
theorem parse_render : ∀ w, parse (render w) = some w
  | [] => rfl
  | c :: w => by
    have ih := parse_render w
    show parse (cpL c.carrier :: cpM c.haraka :: render w) = some (c :: w)
    simp only [parse, fromL_cpL, fromM_cpM, ih]

/-! ## ٢. البايتات -/

theorem renderC_lt_all : cells.all (fun c => (renderC c).all (· < 0x110000)) = true := by decide

theorem renderC_lt (c : Cell) : ∀ x ∈ renderC c, x < 0x110000 := by
  have h := List.all_eq_true.1 renderC_lt_all c (mem_cells c)
  intro x hx
  exact of_decide_eq_true (List.all_eq_true.1 h x hx)

theorem render_lt (w : List Cell) : ∀ x ∈ render w, x < 0x110000 := by
  intro x hx
  simp only [render, List.mem_flatMap] at hx
  obtain ⟨c, _, hc⟩ := hx
  exact renderC_lt c x hc

/-- **البايتاتُ تُقرأ إلى الخانات بأعيانها.** -/
theorem bytes_radd (w : List Cell) :
    parse (decodeN (render w).length (encodeAll (render w))) = some w := by
  rw [decodeAll_encodeAll _ (render_lt w)]
  exact parse_render w

theorem renderC_bytes_all : cells.all (fun c => (encodeAll (renderC c)).length == 4) = true := by decide

theorem renderC_bytes (c : Cell) : (encodeAll (renderC c)).length = 4 := by
  have h := List.all_eq_true.1 renderC_bytes_all c (mem_cells c)
  simpa using h

/-- **كلُّ خانةٍ أربعةُ بايتات.** -/
theorem bytes_len : ∀ w : List Cell, (encodeAll (render w)).length = 4 * w.length
  | [] => rfl
  | c :: w => by
    have ih := bytes_len w
    simp only [render, List.flatMap_cons, encodeAll, List.flatMap_append] at ih ⊢
    simp only [List.length_append, ih, List.length_cons]
    have := renderC_bytes c
    simp only [encodeAll] at this
    omega

/-! ## ٣. الإملاء: الكرسيّ والشدّة -/

def seatCp : Hamza.Seat → Nat
  | .alif => 0x623
  | .alifBelow => 0x625
  | .waw => 0x624
  | .ya => 0x626
  | .line => 0x621

/-- قاعدةُ كرسيٍّ: أيُّ دالّةٍ من (ما قبل، الخانة، ما بعد) إلى كرسيّ. -/
abbrev Kursi := Option Cell → Cell → Option Cell → Hamza.Seat

/-- حرفُ الخانة إملاءً: الهمزةُ على كرسيّها، وما سواها حرفُه. -/
def letterOf (σ : Kursi) (p : Option Cell) (c : Cell) (n : Option Cell) : Nat :=
  if c.carrier = hamza then seatCp (σ p c n) else cpL c.carrier

/-- الإملاء: والمثلان (الأوّلُ ساكنٌ والثاني متحرّك) حرفٌ وشدّةٌ وحركة. -/
def imlaGo (σ : Kursi) : Option Cell → List Cell → List Nat
  | _, [] => []
  | p, [c] => [letterOf σ p c none, cpM c.haraka]
  | p, c :: d :: t =>
    if c.haraka = .sukun ∧ d.carrier = c.carrier ∧ d.haraka ≠ .sukun then
      letterOf σ p c (some d) :: shadda :: cpM d.haraka :: imlaGo σ (some d) t
    else
      letterOf σ p c (some d) :: cpM c.haraka :: imlaGo σ (some c) (d :: t)

def imla (σ : Kursi) (w : List Cell) : List Nat := imlaGo σ none w

/-- قراءةُ الحرف إملاءً: كلُّ كرسيٍّ همزة. -/
def fromL' (n : Nat) : Option (Fin carrierCount) :=
  if [0x623, 0x625, 0x624, 0x626, 0x621].contains n then some hamza else fromL n

def read : List Nat → Option (List Cell)
  | [] => some []
  | [a, b] =>
    match fromL' a, fromM b with
    | some l, some h => some [⟨l, h⟩]
    | _, _ => none
  | a :: b :: m :: rest =>
    if b = shadda then
      match fromL' a, fromM m, read rest with
      | some l, some h, some t => if h = .sukun then none else some (⟨l, .sukun⟩ :: ⟨l, h⟩ :: t)
      | _, _, _ => none
    else
      match fromL' a, fromM b, read (m :: rest) with
      | some l, some h, some t => some (⟨l, h⟩ :: t)
      | _, _, _ => none
  | [_] => none

theorem fromL'_seat : ∀ s, fromL' (seatCp s) = some hamza := by intro s; cases s <;> decide

theorem fromL'_cpL : ∀ k : Fin carrierCount, k ≠ hamza → fromL' (cpL k) = some k := by decide

theorem fromL'_letter (σ : Kursi) (p : Option Cell) (c : Cell) (n : Option Cell) :
    fromL' (letterOf σ p c n) = some c.carrier := by
  unfold letterOf
  split
  · rename_i h; rw [fromL'_seat, h]
  · rename_i h; exact fromL'_cpL _ h

theorem read_cons2 (a b : Nat) (r : List Nat) (hb : b ≠ shadda) :
    read (a :: b :: r) =
      match fromL' a, fromM b, read r with
      | some l, some h, some t => some (⟨l, h⟩ :: t)
      | _, _, _ => none := by
  cases r with
  | nil =>
    simp only [read]
    cases fromL' a <;> cases fromM b <;> rfl
  | cons m rest => simp only [read, hb, ite_false]

/-- **الإملاءُ يُقرأ إلى الخانات بأعيانها لأيّ قاعدةِ كرسيّ.** -/
theorem imla_radd (σ : Kursi) : ∀ (p : Option Cell) (w : List Cell), read (imlaGo σ p w) = some w
  | _, [] => rfl
  | p, [c] => by
    simp only [imlaGo, read, fromL'_letter, fromM_cpM]
  | p, c :: d :: t => by
    unfold imlaGo
    split
    · rename_i h
      obtain ⟨hs, hc, hd⟩ := h
      have ih := imla_radd σ (some d) t
      simp only [read, ite_true, fromL'_letter, fromM_cpM, ih, hd, ite_false]
      cases c; cases d
      simp_all
    · have ih := imla_radd σ (some c) (d :: t)
      rw [read_cons2 _ _ _ (cpM_ne_shadda _), fromL'_letter, fromM_cpM, ih]

/-- **الكرسيُّ لا يحمل شيئًا**: قاعدتا كرسيٍّ تُقرآن إلى الخانات نفسِها. -/
theorem kursi_la_yahmil (σ τ : Kursi) (w : List Cell) : read (imla σ w) = read (imla τ w) := by
  simp only [imla, imla_radd]

/-- **والرسمُ يختلف بهما**: «ءَ» على الألف وعلى السطر. -/
theorem kursi_yaghayyir_rasm :
    imla (fun _ _ _ => .alif) [⟨hamza, .fatha⟩] ≠ imla (fun _ _ _ => .line) [⟨hamza, .fatha⟩] := by
  decide

/-- **الصورةُ القانونيّة إملاءٌ بكرسيّ السطر بلا مثلين**: كلماتٌ بلا شدّةٍ تُكتب كما تُقرأ. -/
theorem render_is_imla_line :
    render [⟨hamza, .fatha⟩, ⟨⟨21, by decide⟩, .fatha⟩] =
      imla (fun _ _ _ => .line) [⟨hamza, .fatha⟩, ⟨⟨21, by decide⟩, .fatha⟩] := by decide

/-! ## ٤. قاعدةُ `Hamza.seatOf` مثولًا -/

def isMaddLetter (c : Cell) : Bool :=
  c.haraka = .sukun && (c.carrier = ⟨0, by decide⟩ || c.carrier = ⟨26, by decide⟩ ||
    c.carrier = ⟨27, by decide⟩)

/-- سياقُ الهمزة من جاريها؛ و«ما قبلها حرفُ مدّ» تقريبٌ معلَن: ساكنٌ من حروف المدّ (`KURSI_PREVLONG_APPROX`). -/
def ctxOf (p : Option Cell) (c : Cell) (n : Option Cell) : Hamza.Ctx where
  pos := match p, n with
    | none, _ => .initial
    | _, none => .final
    | _, _ => .medial
  own := c.haraka
  prev := (p.map (·.haraka)).getD .sukun
  prevLong := (p.map isMaddLetter).getD false
  prevYa := (p.map fun q => isMaddLetter q && q.carrier == ⟨27, by decide⟩).getD false
  nextWaw := (n.map fun q => q.carrier == ⟨26, by decide⟩).getD false

def kursiHamza : Kursi := fun p c n => Hamza.seatOf (ctxOf p c n)

/-- «سَأَلَ» بالقاعدة: الهمزةُ المفتوحةُ بعد فتحةٍ على الألف، وتُقرأ إلى خاناتها. -/
def saala : List Cell := [⟨⟨11, by decide⟩, .fatha⟩, ⟨hamza, .fatha⟩, ⟨⟨22, by decide⟩, .fatha⟩]

theorem saala_imla :
    imla kursiHamza saala = [0x633, 0x64E, 0x623, 0x64E, 0x644, 0x64E] ∧ read (imla kursiHamza saala) = some saala := by
  decide

end A116.Imla
