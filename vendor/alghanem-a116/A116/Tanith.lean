/-!
# ألفُ التأنيث زيادةٌ بعد الأصول (ADR ٥٣)

**الكتاب** (المختوم في SLGE، `openiti-sibawayh-kitab.txt.gz`، بأرقام أسطره): «هذا باب ما لحقته ألف التأنيث
بعد ألف … وذلك نحو حمراء وصفراء وخضراء وصحراء … وفقهاء … أصدقاء وأصفياء … واعلم أن الألفين لا تزادان أبدا
إلا للتأنيث» (س10720–10731)؛ «فإن قلت فما بال علباء وحرباء فإن هذه الهمزة التي بعد الألف إنما هي بدل من ياء»
(س10732–10733)؛ وفي المقصورة: «وكان آخره ألف التأنيث … فإنك تحذف الزيادة التي هي للتأنيث … حبلى حبالى»
(س15357–15359). فألفُ التأنيث **زيادةٌ**: ما قبلها يحمل الأصولَ كلَّها.

**التعريف** على هيكل الكلمة (حروفُها بلا حركات) وجذرِها: آخرُها ألفٌ (ا/ى) فمقصورٌ مرشَّح، أو ألفٌ ثمّ
همزة فممدودٌ مرشَّح (`finalAlif`)؛ وهو ألفُ تأنيثٍ إن وقعت الأصولُ بترتيبها فيما قبله (`inOrder`) بمطابقةٍ
مسمّاة (`radMatch`): الحرفُ نفسُه، أو أصلٌ معتلٌّ (و/ي) بحرف علّة، أو أصلٌ مهموزٌ بكرسيّ همزةٍ أو بما
خُفّف إليه (ا، و، ي). فـ«أَوْلِيَاء» (ولي) و«أَصْدِقَاء» (صدق) ممدودةٌ للتأنيث، و«أَبْنَاء» (بني) و«أَسْمَاء»
(سمو) همزتُها من الأصل — وهذا ما لا يفرّقه شكلُ الآخر وحدَه (`shape_blind`): دَينُ SLGE المسمّى في
`Slge.Sarf.mamduda` («الهمزةُ الأصليّةُ في الممدود لا تفرّقها الخانة») يُسدّ بالجذر لا بالخانة.

**مانع**: لا ألفَ تأنيثٍ بلا آخرٍ ألفيٍّ (`tanith_needs_final`)، ولا ألفَ تأنيثٍ إلّا والأصولُ قبلها
(`tanith_needs_root`)، وكلُّ هيكلٍ آخرُه ألفيٌّ إمّا ألفُ تأنيثٍ وإمّا آخرُه من الأصل، لا ثالث
(`tanith_partition`). **والجامعُ** قياسٌ لا برهان (`tools/gen_qac_tanith.py`). والمستثنى بالاسم: إلحاقُ
علباء وحرباء (`ILHAQ_ALIF`) — تُعدّه هذه القاعدةُ تأنيثًا والكتابُ يردّه.
-/

namespace A116.Tanith

inductive Kind | maqsura | mamduda
  deriving DecidableEq, Repr

/-- كراسيُّ الهمزة وما تُخفَّف إليه. -/
def hamzaLike (c : Char) : Bool :=
  c == 'ء' || c == 'أ' || c == 'إ' || c == 'ؤ' || c == 'ئ' || c == 'آ' || c == 'ا' || c == 'و' || c == 'ي'

/-- حروفُ العلّة وما تُقلب إليه. -/
def weakLike (c : Char) : Bool := c == 'و' || c == 'ي' || c == 'ا' || c == 'ى'

/-- يقع الأصلُ `r` حرفًا `c` في الهيكل. -/
def radMatch (r c : Char) : Bool :=
  r == c || ((r == 'و' || r == 'ي') && weakLike c) || (r == 'ء' && hamzaLike c)

/-- الأصولُ بترتيبها في الهيكل، لا متجاورةً بالضرورة. -/
def inOrder : List Char → List Char → Bool
  | _, [] => true
  | [], _ :: _ => false
  | c :: cs, r :: rs => if radMatch r c then inOrder cs rs else inOrder cs (r :: rs)

/-- الآخرُ الألفيّ وما قبله. -/
def finalAlif (sk : List Char) : Option (Kind × List Char) :=
  match sk.reverse with
  | 'ء' :: 'ا' :: rest => some (.mamduda, rest.reverse)
  | 'ا' :: rest => some (.maqsura, rest.reverse)
  | 'ى' :: rest => some (.maqsura, rest.reverse)
  | _ => none

/-- ألفُ التأنيث: آخرٌ ألفيٌّ والأصولُ كلُّها قبله. -/
def tanith (sk root : List Char) : Option Kind :=
  match finalAlif sk with
  | some (k, stem) => if inOrder stem root then some k else none
  | none => none

/-- شكلُ الآخر وحدَه (ما تقرؤه الخانة): آخرٌ ألفيّ. -/
def shape (sk : List Char) : Bool := (finalAlif sk).isSome

theorem tanith_needs_final (sk root : List Char) (k : Kind) (h : tanith sk root = some k) :
    ∃ stem, finalAlif sk = some (k, stem) := by
  unfold tanith at h
  split at h
  · rename_i k' stem heq
    split at h
    · cases h; exact ⟨stem, heq⟩
    · cases h
  · cases h

theorem tanith_needs_root (sk root stem : List Char) (k : Kind) (hf : finalAlif sk = some (k, stem))
    (h : tanith sk root = some k) : inOrder stem root = true := by
  unfold tanith at h
  rw [hf] at h
  simp only at h
  split at h
  · assumption
  · cases h

theorem tanith_partition (sk root stem : List Char) (k : Kind) (hf : finalAlif sk = some (k, stem)) :
    (tanith sk root = some k ∧ inOrder stem root = true) ∨
    (tanith sk root = none ∧ inOrder stem root = false) := by
  unfold tanith
  rw [hf]
  cases h : inOrder stem root <;> simp [h]

/-- شواهدُ الكتاب ومقابلاتُها: الممدودُ للتأنيث، والهمزةُ الأصليّة، والمقصور، ولامُ المعتلّ ألفًا. -/
theorem witnesses :
    tanith "صحراء".toList "صحر".toList = some .mamduda ∧
    tanith "حمراء".toList "حمر".toList = some .mamduda ∧
    tanith "فقهاء".toList "فقه".toList = some .mamduda ∧
    tanith "اصدقاء".toList "صدق".toList = some .mamduda ∧
    tanith "اولياء".toList "ولي".toList = some .mamduda ∧
    tanith "حبلى".toList "حبل".toList = some .maqsura ∧
    tanith "بشرى".toList "بشر".toList = some .maqsura ∧
    tanith "دنيا".toList "دنو".toList = some .maqsura ∧
    tanith "ابناء".toList "بني".toList = none ∧
    tanith "اسماء".toList "سمو".toList = none ∧
    tanith "سماء".toList "سمو".toList = none ∧
    tanith "انباء".toList "نبء".toList = none ∧
    tanith "هدى".toList "هدي".toList = none ∧
    tanith "فتى".toList "فتي".toList = none := by decide

/-- المستثنى المسمّى `ILHAQ_ALIF`: علباء تُعدّ هنا تأنيثًا، والكتابُ يجعل همزتها بدلًا من ياء الإلحاق. -/
theorem ilhaq_named : tanith "علباء".toList "علب".toList = some .mamduda := by decide

/-- الشكلُ أعمى: «ابناء» و«اصدقاء» آخرُهما واحد، والجذرُ وحدَه يفرّقهما؛ فلا دالّةَ في الشكل تساوي `tanith`. -/
theorem shape_blind :
    shape "ابناء".toList = shape "اصدقاء".toList ∧
    tanith "ابناء".toList "بني".toList ≠ tanith "اصدقاء".toList "صدق".toList := by decide

theorem no_shape_function (f : Bool → Option Kind)
    (h : ∀ sk root, tanith sk root = f (shape sk)) : False := by
  have h1 := h "ابناء".toList "بني".toList
  have h2 := h "اصدقاء".toList "صدق".toList
  have hs : shape "ابناء".toList = shape "اصدقاء".toList := by decide
  rw [hs] at h1
  have : tanith "ابناء".toList "بني".toList = tanith "اصدقاء".toList "صدق".toList := by rw [h1, h2]
  exact absurd this (by decide)

end A116.Tanith
