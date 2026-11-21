import A116.Neutral
import A116.Hajah

/-!
# الماضي ← المضارعُ بزائدةٍ من «أنيت» ← الأمرُ بإزالة الزوائد: ترخيصٌ جبريٌّ متدرّج (ADR ٢٤)

قرارُ المالك (2026-10-12): «صيغُ الماضي المجرّد: فتح فتح فتح، وفتح ضمّ فتح، وفتح كسر فتح، وكلٌّ منها يصبح n، وترتبط
بالمضارع بترخيص زوائد من الـ116: ن ي ت ء، ويولَّد المضارعُ وفق قانون الابتداء وقانون الوصل وقانون الوقف، ويكون الأمرُ
بإزالة الزوائد: قُمْ من قام، اِذْهَبْ، خُذْ، آتِ، أَعْطِ، قِ (وقى)، … عِ بالكسرة».

## الدرجات

* **الماضي المجرّد** ثلاثةٌ (`Wazn.thulathi[0..2]`: فَعَلَ، فَعِلَ، فَعُلَ)، لكلٍّ عددُه n في جدول درجته (`Ledger`).
* **المضارع** (`mudari`): حرفُ مضارعةٍ من «أنيت» — كلٌّ منها من الـ116 (`anayt_are_carriers`) — متحرّكٌ (ضمٌّ لِما ماضيه
  أربعة أحرف: فعّل وفاعل وأفعل، وفتحٌ لغيرها)، ثمّ جسمُ الوزن، ثمّ اللامُ بحالة الإعراب: ضمٌّ رفعًا، وسكونٌ جزمًا. والحرفُ
  المتحرّكُ **أبٌ** يقضي حاجةَ الساكن بعده (قانونُ الحاجة، `Hajah`): فيبدأ الجسمُ بساكنٍ بلا همزة وصل (يَذْهَبُ، يَنْكَسِرُ).
* **الأمر** (`amr`): **إزالةُ الزوائد** من المجزوم — حرفُ المضارعة يُزال، وما أزاحه يعود (همزةُ أفعل: أَعْطِ) — ثمّ
  **قانونُ الابتداء**: إن بدأ الباقي بساكنٍ قامت همزةُ الوصل بحركة **الفعل** (ضمٌّ إن ضُمّ ما بعد الساكن، وإلّا كسر:
  `waslVerb`) — لا بقاعدة لام الأداة. فيُحلّ `WASL_LAM_ARTICLE_VS_ROOT` في الفعل: الأمرُ من الْتَقَى اِلْتَقِ بالكسر.

## القواعد المعلنة على الخانات (لا تخمين؛ كلٌّ بموضعه في `Ilal` أو `Neutral` أو اسمه هنا)

المثال (الواوُ بين المفتوح والمكسور تُحذف: يَعِدُ، Ilal ٦)، المضعَّف (يُدغم والآخرُ متحرّك: يَمُدُّ)، الأجوف (العينُ بعد ساكنٍ
تنقل حركتَها وتصير مدًّا من جنسها: يَقُولُ، يَبِيعُ، يَخَافُ — Ilal ٣؛ وبعد مفتوحٍ غيرِ حرف المضارعة ألفًا: يَنْقَادُ)، الناقص
(اللامُ رفعًا مدٌّ من جنس ما قبلها، وجزمًا تُحذف: يَدْعُو/يَدْعُ)، المدُّ قبل ساكنٍ صحيحٍ يُحذف (يَقُلْ — ملزَم بقيد الحدّ)،
الافتعال (طاءٌ بعد الإطباق، دالٌ بعد د ذ ز، الفاءُ المعتلّةُ تاء — Ilal ٨–١٠)، همزتا أفعل (Ilal ٧: آمِنْ). ومنقولٌ مسمًّى
بنصّ المالك وبالبوّابة: تخفيفُ همزة رأى (`takhfif`: يَرَى، رَ)، وحذفُ الفاء المهموزة في أخذ وأكل وأمر (`hadhfFa`: خُذْ).

## ما يُبرهَن

* `waslVerb_ne_fatha`، `amr_lqy`: همزةُ الوصل في الفعل لا تُفتح أبدًا، والأمرُ من الْتَقَى (لقي، افتعل) اِلْتَقِ — وقاعدةُ
  `Boundary.waslVowel` تفتحها: فالفرقُ مبرهَن، والعلاجُ قانونُ الفعل.
* `amr_head_vowelled`: **قانونُ الابتداء** — الأمرُ لا يبدأ بساكنٍ أبدًا، لكلّ جذرٍ ووزنٍ وباب.
* `owner_examples`: أمثلةُ المالك كلُّها خاناتٍ بأعيانها: قُمْ، اِذْهَبْ، خُذْ، أَعْطِ، قِ، صِ، رَ، عِ، ومعها بِعْ، خَفْ، عِدْ، اُكْتُبْ.
* `reference_licensed`: على الجذور المرجعيّة والأوزان التسعة والأبواب، المضارعُ رفعًا والأمرُ مرخَّصان بقيد الحدّ وصلًا،
  وخاناتُهما من المرخَّص، وقانونُ الحاجة قائمٌ على المضارع بأبيه حرفِ المضارعة.
* `amr_restores_mudari`: ردُّ حرف المضارعة إلى الأمر (بعد نزع همزة الوصل وما أعاده) يعيد المجزومَ بعينه — الإزالةُ تُردّ.
-/

set_option autoImplicit false

namespace A116.Mudari

open A116 A116.Stages A116.Hadd A116.Wazn A116.Neutral A116.Ladder

/-! ## ١. الأوزانُ والزوائد -/

inductive Form where
  | I | II | III | IV | V | VI | VII | VIII | X
  deriving DecidableEq, Repr

def Form.all : List Form := [.I, .II, .III, .IV, .V, .VI, .VII, .VIII, .X]

/-- حروفُ المضارعة «أنيت»: كلُّها حواملُ من الـ116. -/
def anayt : List Char := ['ء', 'ن', 'ي', 'ت']

theorem anayt_are_carriers : anayt.all (Field112.carriers29.contains ·) = true := by decide

/-- الخانةُ موسومةً بأصلها إن كانت أصلًا. -/
abbrev TC := Cell × Option (Fin 3)

def isWeak (k : Fin carrierCount) : Bool := k == carrierOf 'و' || k == carrierOf 'ي'

def maddOf : Haraka → Fin carrierCount
  | .damma => carrierOf 'و'
  | .kasra => carrierOf 'ي'
  | _ => carrierOf 'ا'

/-- تاءُ الافتعال بحسب الفاء (Ilal ٨، ٩). -/
def taOf (k : Fin carrierCount) : Fin carrierCount :=
  if [carrierOf 'ص', carrierOf 'ض', carrierOf 'ط', carrierOf 'ظ'].contains k then carrierOf 'ط'
  else if [carrierOf 'د', carrierOf 'ذ', carrierOf 'ز'].contains k then carrierOf 'د'
  else carrierOf 'ت'

def lit (c : Char) (h : Haraka) : TC := (atom c h, none)
def rad (r : Root 3) (i : Fin 3) (h : Haraka) : TC := (⟨r i, h⟩, some i)

/-- حركةُ حرف المضارعة وجسمُ الوزن (بين الحرف واللام). -/
def body (r : Root 3) (b : Haraka) : Form → Haraka × List TC
  | .I => (.fatha, [rad r 0 .sukun, rad r 1 b])
  | .II => (.damma, [rad r 0 .fatha, rad r 1 .sukun, rad r 1 .kasra])
  | .III => (.damma, [rad r 0 .fatha, lit 'ا' .sukun, rad r 1 .kasra])
  | .IV => (.damma, [lit 'ء' .fatha, rad r 0 .sukun, rad r 1 .kasra])
  | .V => (.fatha, [lit 'ت' .fatha, rad r 0 .fatha, rad r 1 .sukun, rad r 1 .fatha])
  | .VI => (.fatha, [lit 'ت' .fatha, rad r 0 .fatha, lit 'ا' .sukun, rad r 1 .fatha])
  | .VII => (.fatha, [lit 'ن' .sukun, rad r 0 .fatha, rad r 1 .kasra])
  | .VIII => (.fatha,
      [((⟨if isWeak (r 0) then carrierOf 'ت' else r 0, .sukun⟩ : Cell), some 0),
       ((⟨taOf (r 0), .fatha⟩ : Cell), none), rad r 1 .kasra])
  | .X => (.fatha, [lit 'س' .sukun, lit 'ت' .fatha, rad r 0 .sukun, rad r 1 .kasra])

/-! ## ٢. القواعد على الخانات -/

def isConsSukun (c : Cell) : Bool := c.haraka == .sukun && (maddVowel c.carrier).isNone

def occ (xs : List TC) (i : Fin 3) : Nat := (xs.filter fun x => x.2 == some i).length

/-- المثال: الفاءُ الواويّةُ الساكنةُ بين حرف المضارعة وعينٍ مكسورة تُحذف (Ilal ٦). -/
def mithal (r : Root 3) (b : Haraka) (f : Form) (xs : List TC) : List TC :=
  if f == .I && r 0 == carrierOf 'و' && b == .kasra then xs.filter (·.2 != some 0) else xs

/-- المضعَّف: العينُ قبل اللام مثلُها، مرّةً واحدة، والآخرُ متحرّك: تُنقل حركتُها إلى الساكن الصحيح قبلها وتُسكَّن. -/
def doubled (r : Root 3) (xs : List TC) : List TC :=
  match xs.reverse with
  | l :: a :: p :: rest =>
    if r 1 == r 2 && !isWeak (r 1) && a.2 == some 1 && occ xs 1 == 1 && l.1.haraka != .sukun &&
        a.1.haraka != .sukun && isConsSukun p.1 then
      rest.reverse ++ [(⟨p.1.carrier, a.1.haraka⟩, p.2), (⟨a.1.carrier, .sukun⟩, a.2), l]
    else xs
  | _ => xs

/-- الأجوف: عينٌ معتلّةٌ متحرّكة (مرّةً، واللامُ صحيحة) بعد ساكنٍ صحيح: نقلٌ ومدٌّ من جنس الحركة؛ وبعد مفتوحٍ غيرِ
حرف المضارعة: ألف. والفاءُ الساكنةُ ساكنٌ صحيحٌ وإن كانت واوًا أو ياءً (لينٌ لا مدّ: يَيَاحُ). `first` أهو حرفُ المضارعة. -/
def hollowGo (r : Root 3) (cnt : Nat) : Bool → List TC → List TC
  | first, p :: a :: rest =>
    if a.2 == some 1 && isWeak (r 1) && !isWeak (r 2) && cnt == 1 && a.1.haraka != .sukun then
      if isConsSukun p.1 || (p.2 == some 0 && p.1.haraka == .sukun) then
        (⟨p.1.carrier, a.1.haraka⟩, p.2) :: (⟨maddOf a.1.haraka, .sukun⟩, a.2) :: rest
      else if p.1.haraka == .fatha && !first then p :: (alifS, a.2) :: rest
      else p :: hollowGo r cnt false (a :: rest)
    else p :: hollowGo r cnt false (a :: rest)
  | _, xs => xs

def hollow (r : Root 3) (xs : List TC) : List TC := hollowGo r (occ xs 1) true xs

/-- الناقص: اللامُ رفعًا مدٌّ من جنس ما قبلها، وجزمًا تُحذف. -/
def defective (r : Root 3) (xs : List TC) : List TC :=
  if !isWeak (r 2) then xs else
  match xs.reverse with
  | l :: p :: rest =>
    if l.1.haraka == .sukun then (p :: rest).reverse
    else if p.1.haraka != .sukun then (p :: rest).reverse ++ [(⟨maddOf p.1.haraka, .sukun⟩, l.2)]
    else xs
  | _ => xs

/-- المدُّ قبل ساكنٍ صحيحٍ غيرِ مدغمٍ يُحذف (قيدُ الحدّ؛ Ilal ٢). -/
def dropMadd : List TC → List TC
  | p :: m :: c :: rest =>
    if m.1.haraka == .sukun && maddVowel m.1.carrier == some p.1.haraka && isConsSukun c.1 &&
        (rest.head?.map (·.1.carrier) != some c.1.carrier) then
      p :: dropMadd (c :: rest)
    else p :: dropMadd (m :: c :: rest)
  | xs => xs

/-- تخفيفُ همزة العين بعد ساكنٍ صحيح: تُنقل حركتُها وتُحذف — منقولٌ في «رأى» المجرّد بابَ فَعَلَ يَفْعَلُ (يَرَى؛
نصُّ المالك: «والأمرُ من رأى رَ»). -/
def takhfifRoots : List (Root 3) := [rootOf 'ر' 'ء' 'ي']

def takhfifGo : List TC → List TC
  | p :: a :: rest =>
    if a.2 == some 1 && a.1.carrier == hamza && isConsSukun p.1 then (⟨p.1.carrier, a.1.haraka⟩, p.2) :: rest
    else p :: takhfifGo (a :: rest)
  | xs => xs

def takhfif (r : Root 3) (f : Form) (b : Haraka) (xs : List TC) : List TC :=
  if f == .I && b == .fatha && takhfifRoots.any (fun t => decide (t 0 = r 0 ∧ t 1 = r 1 ∧ t 2 = r 2)) then
    takhfifGo xs else xs

/-- حذفُ الفاء المهموزة في الأمر — منقولٌ في أخذ وأكل وأمر، بابَ يَفْعُلُ (خُذْ، كُلْ، مُرْ). -/
def hadhfFaRoots : List (Root 3) := [rootOf 'ء' 'خ' 'ذ', rootOf 'ء' 'ك' 'ل', rootOf 'ء' 'م' 'ر']

def sameRoot (r t : Root 3) : Bool := decide (t 0 = r 0 ∧ t 1 = r 1 ∧ t 2 = r 2)

/-! ## ٣. المضارعُ والأمر -/

/-- المضارعُ بحرفه `pre` وحالةِ لامه `e` (ضمٌّ رفعًا، سكونٌ جزمًا)؛ همزةُ أفعل تُزاح بعد الحرف. -/
def mudariT (r : Root 3) (f : Form) (b : Haraka) (pre : Char) (e : Haraka) : List TC :=
  let (pv, bd) := body r b f
  let bd := if f == .IV then bd.drop 1 else bd
  let xs := (atom pre pv, none) :: bd ++ [rad r 2 e]
  dropMadd (defective r (hollow r (takhfif r f b (doubled r (mithal r b f xs)))))

def mudari (r : Root 3) (f : Form) (b : Haraka) (pre : Char) (e : Haraka) : List Cell :=
  (mudariT r f b pre e).map (·.1)

/-- حركةُ همزة الوصل في الفعل: ضمٌّ إن ضُمّ ما بعد الساكن، وإلّا كسر — لا فتحَ. -/
def waslVerb (next : Cell) : Haraka := if next.haraka == .damma then .damma else .kasra

theorem waslVerb_ne_fatha (c : Cell) : waslVerb c ≠ .fatha := by
  unfold waslVerb; split <;> decide

theorem waslVerb_ne_sukun (c : Cell) : waslVerb c ≠ .sukun := by
  unfold waslVerb; split <;> decide

/-- قانونُ الابتداء: إن بدأ الباقي بساكنٍ قامت همزةُ الوصل بحركة الفعل. -/
def ibtida : List Cell → List Cell
  | x :: y :: rest => if x.haraka == .sukun then ⟨hamza, waslVerb y⟩ :: x :: y :: rest else x :: y :: rest
  | [x] => if x.haraka == .sukun then [⟨hamza, .kasra⟩, x] else [x]
  | [] => []

/-- إزالةُ الزوائد: المجزومُ بالتاء يُزال حرفُه، ويعود ما أزاحه (همزةُ أفعل)، وتُحذف الفاءُ المهموزةُ في المنقول. -/
def amrRest (r : Root 3) (f : Form) (b : Haraka) : List Cell :=
  let rest := (mudari r f b 'ت' .sukun).drop 1
  let rest := if f == .IV then
      match rest with
      | x :: more => if x.carrier == hamza && x.haraka == .sukun then atom 'ء' .fatha :: alifS :: more
                     else atom 'ء' .fatha :: x :: more
      | [] => [atom 'ء' .fatha]
    else rest
  if f == .I && b == .damma && hadhfFaRoots.any (sameRoot r) then
      match rest with
      | x :: more => if x.carrier == hamza && x.haraka == .sukun then more else x :: more
      | [] => []
    else rest

/-- **الأمر**: إزالةُ الزوائد ثمّ قانونُ الابتداء. -/
def amr (r : Root 3) (f : Form) (b : Haraka) : List Cell := ibtida (amrRest r f b)

/-- همزةُ الوصل في الأمر: أقامها قانونُ الابتداء — الخاناتُ وحدَها لا تفرّقها من همزةٍ أصليّة (ءِلْ من وأل)، فيُحملُ
الفرقُ معها. -/
def amrWasl (r : Root 3) (f : Form) (b : Haraka) : Bool :=
  ((amrRest r f b).head?.map (·.haraka)) == some .sukun

/-! ## ٤. المبرهنات -/

theorem ibtida_head (xs : List Cell) : ∀ c, (ibtida xs).head? = some c → c.haraka ≠ .sukun := by
  intro c h
  match xs, h with
  | x :: y :: rest, h =>
    simp only [ibtida] at h
    split at h
    · simp only [List.head?_cons, Option.some.injEq] at h; subst h; exact waslVerb_ne_sukun y
    · rename_i hx; simp only [List.head?_cons, Option.some.injEq] at h; subst h
      simpa using hx
  | [x], h =>
    simp only [ibtida] at h
    split at h
    · simp only [List.head?_cons, Option.some.injEq] at h; subst h; decide
    · rename_i hx; simp only [List.head?_cons, Option.some.injEq] at h; subst h
      simpa using hx

/-- **قانونُ الابتداء في الأمر**: لا يبدأ الأمرُ بساكنٍ أبدًا، لكلّ جذرٍ ووزنٍ وباب. -/
theorem amr_head_vowelled (r : Root 3) (f : Form) (b : Haraka) (c : Cell)
    (h : (amr r f b).head? = some c) : c.haraka ≠ .sukun :=
  ibtida_head _ c h

def ktbR : Root 3 := rootOf 'ك' 'ت' 'ب'
def lqy : Root 3 := rootOf 'ل' 'ق' 'ي'

/-- **همزةُ وصل الفعل بقانونه**: الأمرُ من الْتَقَى اِلْتَقِ بالكسر، وقاعدةُ لام الأداة كانت تفتحها. -/
theorem amr_lqy :
    amr lqy .VIII .kasra = [⟨hamza, .kasra⟩, atom 'ل' .sukun, atom 'ت' .fatha, atom 'ق' .kasra] ∧
    Boundary.waslVowel (atom 'ل' .sukun) (atom 'ت' .fatha) = .fatha := by
  decide +kernel

/-- أمثلةُ المالك خاناتٍ بأعيانها. -/
theorem owner_examples :
    amr (rootOf 'ق' 'و' 'م') .I .damma = [atom 'ق' .damma, atom 'م' .sukun] ∧
    amr (rootOf 'ذ' 'ه' 'ب') .I .fatha =
      [⟨hamza, .kasra⟩, atom 'ذ' .sukun, atom 'ه' .fatha, atom 'ب' .sukun] ∧
    amr (rootOf 'ء' 'خ' 'ذ') .I .damma = [atom 'خ' .damma, atom 'ذ' .sukun] ∧
    amr (rootOf 'ع' 'ط' 'و') .IV .kasra = [atom 'ء' .fatha, atom 'ع' .sukun, atom 'ط' .kasra] ∧
    amr (rootOf 'ء' 'ت' 'ي') .IV .kasra = [atom 'ء' .fatha, alifS, atom 'ت' .kasra] ∧
    amr (rootOf 'و' 'ق' 'ي') .I .kasra = [atom 'ق' .kasra] ∧
    amr (rootOf 'و' 'ص' 'ي') .I .kasra = [atom 'ص' .kasra] ∧
    amr (rootOf 'ر' 'ء' 'ي') .I .fatha = [atom 'ر' .fatha] ∧
    amr (rootOf 'و' 'ع' 'ي') .I .kasra = [atom 'ع' .kasra] ∧
    amr (rootOf 'ب' 'ي' 'ع') .I .kasra = [atom 'ب' .kasra, atom 'ع' .sukun] ∧
    amr (rootOf 'خ' 'و' 'ف') .I .fatha = [atom 'خ' .fatha, atom 'ف' .sukun] ∧
    amr (rootOf 'و' 'ع' 'د') .I .kasra = [atom 'ع' .kasra, atom 'د' .sukun] ∧
    amr ktbR .I .damma = [⟨hamza, .damma⟩, atom 'ك' .sukun, atom 'ت' .damma, atom 'ب' .sukun] := by
  decide +kernel

/-- المضارعُ: أمثلةٌ بأعيانها — يَقُولُ، يَبِيعُ، يَخَافُ، يَدْعُو، يَعِدُ، يَمُدُّ، يَرَى، يُعْطِي. -/
theorem mudari_examples :
    mudari (rootOf 'ق' 'و' 'ل') .I .damma 'ي' .damma =
      [atom 'ي' .fatha, atom 'ق' .damma, atom 'و' .sukun, atom 'ل' .damma] ∧
    mudari (rootOf 'د' 'ع' 'و') .I .damma 'ي' .damma =
      [atom 'ي' .fatha, atom 'د' .sukun, atom 'ع' .damma, atom 'و' .sukun] ∧
    mudari (rootOf 'و' 'ع' 'د') .I .kasra 'ي' .damma = [atom 'ي' .fatha, atom 'ع' .kasra, atom 'د' .damma] ∧
    mudari (rootOf 'م' 'د' 'د') .I .damma 'ي' .damma =
      [atom 'ي' .fatha, atom 'م' .damma, atom 'د' .sukun, atom 'د' .damma] ∧
    mudari (rootOf 'ر' 'ء' 'ي') .I .fatha 'ي' .damma = [atom 'ي' .fatha, atom 'ر' .fatha, alifS] ∧
    mudari (rootOf 'ع' 'ط' 'و') .IV .kasra 'ي' .damma =
      [atom 'ي' .damma, atom 'ع' .sukun, atom 'ط' .kasra, atom 'ي' .sukun] := by
  decide +kernel

/-! ## ٥. الترخيصُ على الجذور المرجعيّة -/

/-- الجذورُ المرجعيّة: صحيح، أجوفان، ناقصان، مثال، لفيفٌ مفروق، مهموزُ الفاء والعين، مضعَّف. -/
def refRoots : List (Root 3) :=
  [ktbR, rootOf 'ق' 'و' 'م', rootOf 'ب' 'ي' 'ع', rootOf 'د' 'ع' 'و', rootOf 'ر' 'م' 'ي', rootOf 'و' 'ع' 'د',
   rootOf 'و' 'ق' 'ي', rootOf 'ء' 'م' 'ن', rootOf 'ر' 'ء' 'ي', rootOf 'م' 'د' 'د', rootOf 'ص' 'ب' 'ر']

/-- الأبوابُ المرخَّصة للجذر في المجرّد (اللفيفُ المفروقُ بابُه الكسر: يَقِي، يَعِي؛ أجوفُ الياء لا ضمَّ في بابه). -/
def babs (r : Root 3) (f : Form) : List Haraka :=
  if f != .I then [.kasra]
  else if r 0 == carrierOf 'و' && isWeak (r 2) then [.kasra]
  else if r 1 == carrierOf 'ي' && !isWeak (r 2) then [.fatha, .kasra]
  else [.fatha, .damma, .kasra]

def licensable (w : List Cell) : Bool := w.all (Alif.licensable.contains ·)

theorem reference_check :
    refRoots.all (fun r => Form.all.all fun f => (babs r f).all fun b =>
      let m := mudari r f b 'ي' .damma
      let a := amr r f b
      contCheck m && contCheck a && licensable m && licensable a &&
        decide (Hajah.NeedLaw (kindOf m))) = true := by
  decide +kernel

/-- **المضارعُ والأمرُ مرخَّصان** على الجذور المرجعيّة والأوزان التسعة والأبواب، وقانونُ الحاجة على المضارع. -/
theorem reference_licensed :
    ∀ r ∈ refRoots, ∀ f ∈ Form.all, ∀ b ∈ babs r f,
      strictB (mudari r f b 'ي' .damma) = true ∧ strictB (amr r f b) = true ∧
      Hajah.NeedLaw (kindOf (mudari r f b 'ي' .damma)) := by
  intro r hr f hf b hb
  have h := reference_check
  simp only [List.all_eq_true] at h
  have h2 := h r hr f hf b hb
  simp only [Bool.and_eq_true, decide_eq_true_eq] at h2
  exact ⟨strictB_of_check h2.1.1.1.1, strictB_of_check h2.1.1.1.2, h2.2⟩

/-- نزعُ ما أعاده الأمرُ من همزة أفعل (وهمزةُ الوصل خارجَ `amrRest` أصلًا). -/
def unIV (f : Form) (xs : List Cell) : List Cell :=
  if f == .IV then
    match xs with
    | _ :: a :: more => if a == alifS then atom 'ء' .sukun :: more else a :: more
    | _ => xs
  else xs

/-- قانونُ الابتداء لا يضيف إلّا همزةً قبل ساكن، ولا يمسّ الباقي. -/
theorem ibtida_spec (xs : List Cell) :
    ibtida xs = xs ∨ ∃ w, w.carrier = hamza ∧ w.haraka ≠ .sukun ∧ ibtida xs = w :: xs := by
  match xs with
  | [] => exact Or.inl rfl
  | [x] =>
    simp only [ibtida]
    split
    · exact Or.inr ⟨⟨hamza, .kasra⟩, rfl, by decide, rfl⟩
    · exact Or.inl rfl
  | x :: y :: rest =>
    simp only [ibtida]
    split
    · exact Or.inr ⟨⟨hamza, waslVerb y⟩, rfl, waslVerb_ne_sukun y, rfl⟩
    · exact Or.inl rfl

/-- **الإزالةُ تُردّ**: حرفُ المضارعة مع ما بقي بعد الإزالة (ونزعِ ما أعاده) يعيد المجزومَ بعينه — على المرجعيّة إلّا المنقول. -/
theorem amr_restores_mudari :
    (refRoots.filter fun r => !(hadhfFaRoots.any (sameRoot r))).all (fun r => Form.all.all fun f =>
      (babs r f).all fun b =>
        let m := mudari r f b 'ت' .sukun
        (m.take 1 ++ unIV f (amrRest r f b)) == m) = true := by
  decide +kernel

end A116.Mudari
