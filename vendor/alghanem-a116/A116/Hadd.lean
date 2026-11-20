import A116.Ternary
import A116.Ladder
import A116.Pause

/-!
# التقاءُ الساكنين على حدّه: قافيةُ المدّ (CVVC) لا تُرخَّص وصلًا إلّا والمُغلِقُ أوّلُ مثلين

## الدَّينُ الذي تسدّه هذه الوحدة

`Ternary.ContinueLicensed` يقرأ الأصنافَ `cv | v | c` وحدَها، فـ«حَاجَّ» (`حَ اْ جْ جَ`) و«قَالْتُ»
(`قَ اْ لْ تُ`) عنده سلسلةٌ واحدة `cv v c cv`، فيقبلهما معًا؛ والثنائيُّ (`Admissible`) يرفضهما معًا.
والقيدُ الذي يفرّق بينهما يقرأ **هويّةَ الحامل**: المُغلِقُ بعد المدّ يساوي حاملُه حاملَ الخانة التي
بعده (تضعيف)، أي «التقاءُ الساكنين على حدّه». وكان هذا دَينًا مسمًّى في `tests/test_ilal.py` و
`tests/test_residue.py`.

## ما يُعرَّف هنا

* `kindOf`: إسقاطُ الخانات على أصنافها (`cv` متحرّك؛ `v` حرفُ مدٍّ ساكنٌ بعد حركته المجانسة: ا بعد
  فتحة، و بعد ضمّة، ي بعد كسرة؛ وإلّا `c`). كان في `gate.licence.kind_of` «معلنًا لا مبرهنًا»؛ وهو
  هنا تعريفٌ في Lean يطابقه البايثون بجدولٍ مولَّد (`lake exe a116-table hadd`).
  **تنبيه:** «ساكن» في الخانة معناه موضعيٌّ — «موضعٌ لا تتبعه حركةٌ قصيرة» — لا «عدمُ الحركة نطقًا»؛
  فحرفُ المدّ خانةٌ ساكنةٌ موضعًا وجزءٌ ثانٍ من حركةٍ طويلةٍ نطقًا، ودورُه `v` هو ما يفرّقه.
* `geminateB`: كلُّ `v` يليه `c` فالـ`c` يليه خانةٌ بحامله نفسه.
* `isFarq`: **مدُّ الفرق** (آلْآنَ): همزةٌ مفتوحةٌ ثمّ ألفُ مدٍّ ثمّ لامٌ ساكنة في أوّل الكلمة — الاستثناءُ
  الوحيد المشهود في المدوّنة المختومة؛ معلنٌ من اصطلاح القرّاء، وموضعُ نصّه في مصدرٍ مسمًّى لم يُتحقَّق
  في هذه الوحدة (`MADD_AL_FARQ_SOURCE_LOCUS_UNVERIFIED`).
* `strictB`: `continueB (kindOf w) && haddB w`.

## المبرهنات

* `strictB_continue`: كلُّ مرخَّصٍ بالقيد مرخَّصٌ ثلاثيًّا (القيدُ تضييقٌ لا توسيع).
* `geminateB_vc_carrier`: **لكلّ** موضعٍ في **أيّ** سلسلةٍ مقبولة: إن تلا `v` صنفُ `c` فحاملُ الـ`c`
  هو حاملُ ما بعده.
* `strict_cvvc_is_geminate`: الشيءُ نفسُه على الخانات: كلُّ كلمةٍ مرخَّصةٍ بالقيد (غيرِ مدّ الفرق)
  كلُّ قافيةِ مدٍّ فيها مدغمة.
* `geminateB_vc_final`: `v` ثمّ `c` في الآخر لا يُقبل وصلًا.
* `hadd_debt_closed`: «قَالْتُ» مرخَّصةٌ ثلاثيًّا ومرفوضةٌ بالقيد — الدَّينُ المسمّى مسدود.
* `hajja_strict`، `dallina_strict`، `qultu_strict`، `alaana_strict`: الشواهدُ الموجبة.
* `farq_needs_its_hamza`: الطفرةُ المرفوضة — الصورةُ نفسُها بغير همزة الاستفهام في أوّلها مرفوضة؛
  فالاستثناءُ لا يتّسع لكلّ مدٍّ قبل لام.
* `kindOf_hajja`: إسقاطُ خانات «حَاجَّ» هو `Ternary.hajja` بعينه.
* **الحدّ بين كلمتين** (`strictJoinB`): الاستثناءُ داخلَ الكلمة الواحدة وحدَها. `straddle_rejected` (مدٌّ آخرَ
  الأولى ومُغلِقٌ أوّلَ الثانية مرفوضٌ لكلّ طول)، `strictJoinB_strict`، `strictJoinB_nil`، والعيبُ المسدود
  `ya_shafiina_straddles` (يَا + الشَّافِعِينَ: يقبله `strictB` موصولًا ويرفضه `strictJoinB`)، وشاهدا القبول
  `quli_dallina_join` و`quli_lhamdu_join`.
* **الوقف** (`strictPauseB`، `haddPauseB`، `strictJoinPauseB`): المدُّ العارض للسكون — `v c` في الطرف وحدَه
  يُقبل وقفًا؛ `strictB_pause` (الوصلُ يستلزم الوقف)، `geminatePauseB_vc_carrier` (كلُّ `v c` داخليٍّ مدغمٌ
  وقفًا أيضًا)، `strictPauseB_pause` (وقفُ المرخَّص وصلًا مرخَّصٌ وقفًا إذا صار آخرُه مُغلِقًا)، والشواهدُ
  `rahim_pause_debt_closed`، `asr_tamm_pause`، `rahmani_rahim_join_pause`، والطفرةُ `qaaltu_pause_still_refused`.

ولا يُبرهَن هنا أنّ هذا القيدَ هو قانونُ العربيّة: Lean يُبرهن خواصَّ التعريف على الخانات؛ ومطابقتُه
للمرويّ مقيسةٌ على المدوّنة المختومة (`tests/test_hadd.py`).
-/

namespace A116.Hadd

open A116 A116.Stages A116.Ladder

/-- الحركةُ المجانسة لحرف المدّ، إن كان حاملُه حرفَ مدّ. -/
def maddVowel (k : Fin carrierCount) : Option Haraka :=
  if k = carrierOf 'ا' then some .fatha
  else if k = carrierOf 'و' then some .damma
  else if k = carrierOf 'ي' then some .kasra
  else none

/-- صنفُ الخانة بحسب حالة ما قبلها. -/
def kindOne (prev : Option Haraka) (x : Cell) : K :=
  if x.haraka ≠ .sukun then .cv
  else
    match prev, maddVowel x.carrier with
    | some a, some b => if a = b then .v else .c
    | _, _ => .c

def kindGo : Option Haraka → List Cell → List K
  | _, [] => []
  | p, x :: t => kindOne p x :: kindGo (some x.haraka) t

/-- إسقاطُ الخانات على الأصناف الثلاثة (مرآتُه `gate.licence.kind_of`). -/
def kindOf (w : List Cell) : List K := kindGo none w

theorem kindGo_length : ∀ (p : Option Haraka) (w : List Cell), (kindGo p w).length = w.length
  | _, [] => rfl
  | p, x :: t => by simp [kindGo, kindGo_length _ t]

/-- شرطُ الموضع الواحد: إن كان `v` وتلاه `c` فالـ`c` يليه حاملُه نفسُه. -/
def stepOK : K × Cell → List (K × Cell) → Bool
  | (.v, _), (.c, x) :: (_, y) :: _ => x.carrier == y.carrier
  | (.v, _), [(.c, _)] => false
  | _, _ => true

/-- كلُّ `v` يليه `c`: المُغلِقُ أوّلُ مثلين (يليه حاملُه نفسُه). -/
def geminateB : List (K × Cell) → Bool
  | [] => true
  | a :: tl => stepOK a tl && geminateB tl

/-- مدُّ الفرق: ءَ اْ لْ في أوّل الكلمة. -/
def isFarq : List Cell → Bool
  | h :: a :: l :: _ => h == atom 'ء' .fatha && a == atom 'ا' .sukun && l.carrier == carrierOf 'ل'
  | _ => false

def haddB (w : List Cell) : Bool :=
  let p := (kindOf w).zip w
  if isFarq w then geminateB (p.drop 2) else geminateB p

/-- الترخيصُ الثلاثيّ وصلًا مع قيد الحدّ. -/
def strictB (w : List Cell) : Bool := Ternary.continueB (kindOf w) && haddB w

/-! ## المبرهنات العامّة -/

theorem strictB_continue {w : List Cell} (h : strictB w = true) :
    Ternary.ContinueLicensed (kindOf w) := by
  simp only [strictB, Bool.and_eq_true] at h
  exact (Ternary.continueB_iff _).1 h.1

theorem geminateB_cons_true {a : K × Cell} {tl : List (K × Cell)}
    (h : geminateB (a :: tl) = true) : geminateB tl = true := by
  simp only [geminateB, Bool.and_eq_true] at h
  exact h.2

/-- **الحدّ لكلّ موضع:** في كلّ سلسلةٍ مقبولة، `v` ثمّ `c` ثمّ خانة ⇒ حاملُ الـ`c` حاملُ ما بعده. -/
theorem geminateB_vc_carrier :
    ∀ (p q : List (K × Cell)) (a x y : Cell) (k : K),
      geminateB (p ++ (.v, a) :: (.c, x) :: (k, y) :: q) = true → x.carrier = y.carrier
  | [], q, a, x, y, k, h => by
    simp only [List.nil_append, geminateB, Bool.and_eq_true] at h
    simpa [stepOK] using h.1
  | b :: p, q, a, x, y, k, h =>
    geminateB_vc_carrier p q a x y k (geminateB_cons_true (by simpa using h))

/-- `v` ثمّ `c` في آخر السلسلة: لا مثلَ بعد المُغلِق، فلا قبول. -/
theorem geminateB_vc_final :
    ∀ (p : List (K × Cell)) (a x : Cell), geminateB (p ++ [(.v, a), (.c, x)]) = false
  | [], a, x => by simp [geminateB, stepOK]
  | b :: p, a, x => by
    have ih := geminateB_vc_final p a x
    cases h : geminateB (b :: p ++ [(.v, a), (.c, x)]) with
    | false => rfl
    | true => exact absurd (geminateB_cons_true (by simpa using h)) (by simp [ih])

/-- **على الخانات:** في كلّ كلمةٍ مرخَّصةٍ بالقيد ليست مدَّ فرق، كلُّ مدٍّ يليه مُغلِقٌ فالمُغلِقُ أوّلُ مثلين،
بأيّ طولٍ وفي أيّ موضع. -/
theorem strict_cvvc_is_geminate {w : List Cell} (h : strictB w = true) (hf : isFarq w = false)
    {p q : List (K × Cell)} {a x y : Cell} {k : K}
    (hz : (kindOf w).zip w = p ++ (.v, a) :: (.c, x) :: (k, y) :: q) : x.carrier = y.carrier := by
  simp only [strictB, haddB, hf, Bool.and_eq_true] at h
  rw [hz] at h
  exact geminateB_vc_carrier p q a x y k (by simpa using h.2)

/-! ## الشواهد (بالحساب على خاناتٍ مسمّاة) -/

theorem cited_letters_are_carriers :
    ['ح', 'ا', 'ج', 'ق', 'ل', 'ت', 'ض', 'ب', 'ء', 'ن', 'و', 'ي'].all
      (Field112.carriers29.contains ·) = true := by
  decide

open Haraka in
/-- حَاجَّ: `حَ اْ جْ جَ`. -/
def hajjaCells : List Cell := [atom 'ح' fatha, atom 'ا' sukun, atom 'ج' sukun, atom 'ج' fatha]
open Haraka in
/-- قَالْتُ (الأصلُ المعلّ): `قَ اْ لْ تُ`. -/
def qaaltu : List Cell := [atom 'ق' fatha, atom 'ا' sukun, atom 'ل' sukun, atom 'ت' damma]
open Haraka in
/-- قُلْتُ: `قُ لْ تُ`. -/
def qultu : List Cell := [atom 'ق' damma, atom 'ل' sukun, atom 'ت' damma]
open Haraka in
/-- ضَالِّينَ: `ضَ اْ لْ لِ يْ نَ` (مدٌّ قبل مضعَّف، ثمّ مدٌّ قبل متحرّك). -/
def dallina : List Cell :=
  [atom 'ض' fatha, atom 'ا' sukun, atom 'ل' sukun, atom 'ل' kasra, atom 'ي' sukun, atom 'ن' fatha]
open Haraka in
/-- آلْآنَ: `ءَ اْ لْ ءَ اْ نَ`. -/
def alaana : List Cell :=
  [atom 'ء' fatha, atom 'ا' sukun, atom 'ل' sukun, atom 'ء' fatha, atom 'ا' sukun, atom 'ن' fatha]
open Haraka in
/-- الطفرة: آلْآنَ بغير همزة الاستفهام (`بَ اْ لْ ءَ اْ نَ`). -/
def baalaana : List Cell :=
  [atom 'ب' fatha, atom 'ا' sukun, atom 'ل' sukun, atom 'ء' fatha, atom 'ا' sukun, atom 'ن' fatha]

theorem kindOf_hajja : kindOf hajjaCells = Ternary.hajja := by decide

/-- `continueB` على وصل مقاطع: `parse` معرَّفٌ بالاستقراء المؤسَّس فلا تحسبه النواةُ مباشرةً، فيُمرّ
بمبرهنة `Stages.parse_flat`. -/
theorem continueB_flat (ss : List Syl) :
    Ternary.continueB (flat .none ss) = ss.all fun s => !Ternary.pauseOnly s := by
  simp [Ternary.continueB, parse_flat]

/-- **الدَّينُ المسمّى مسدود:** قَالْتُ مقبولةٌ ثلاثيًّا (CVVC + CV) ومرفوضةٌ بقيد الحدّ. -/
theorem hadd_debt_closed :
    Ternary.continueB (kindOf qaaltu) = true ∧ strictB qaaltu = false := by
  have hk : kindOf qaaltu = flat .none [.CVVC, .CV] := by decide
  simp only [strictB, hk, continueB_flat]
  decide

theorem hajja_strict : strictB hajjaCells = true := by
  have hk : kindOf hajjaCells = flat .none [.CVVC, .CV] := by decide
  simp only [strictB, hk, continueB_flat]
  decide

theorem dallina_strict : strictB dallina = true := by
  have hk : kindOf dallina = flat .none [.CVVC, .CVV, .CV] := by decide
  simp only [strictB, hk, continueB_flat]
  decide

theorem qultu_strict : strictB qultu = true := by
  have hk : kindOf qultu = flat .none [.CVC, .CV] := by decide
  simp only [strictB, hk, continueB_flat]
  decide

theorem alaana_strict : strictB alaana = true := by
  have hk : kindOf alaana = flat .none [.CVVC, .CVV, .CV] := by decide
  simp only [strictB, hk, continueB_flat]
  decide

/-- الاستثناءُ لا يتّسع: بلا همزة الاستفهام في الأوّل تُرفض الصورةُ نفسُها. -/
theorem farq_needs_its_hamza :
    Ternary.continueB (kindOf baalaana) = true ∧ strictB baalaana = false := by
  have hk : kindOf baalaana = flat .none [.CVVC, .CVV, .CV] := by decide
  simp only [strictB, hk, continueB_flat]
  decide

/-! ## الحدُّ بين كلمتين: الاستثناءُ داخلَ الكلمة الواحدة وحدَها

شرطُ باب «دابّة» عند المؤلّف أن يكون المدُّ والمدغمُ «من كلمةٍ واحدة». فإن كان المدُّ آخرَ الأولى
والمدغمُ أوّلَ الثانية (يَا + الشَّافِعِينَ ← `يَ اْ | شْ شَ …`) فالمدُّ يُقصَّر نطقًا، والقافيةُ ليست
على حدّها. `strictB` على السلسلة الموصولة لا يرى الحدّ فيقبلها؛ و`strictJoinB` يرفض كلَّ `v` يليه
`c` إن وقع الحدُّ بين المدّ وما بعد المُغلِق. -/

/-- قافيةُ مدٍّ يقطعها الحدّ: `v | c` أو `v c | x`، حيث `b` طولُ الكلمة الأولى. -/
def straddles (l r : List Cell) : Bool :=
  let k := kindOf (l ++ r)
  let b := l.length
  (decide (1 ≤ b) && k[b - 1]? == some .v && k[b]? == some .c) ||
    (decide (2 ≤ b) && k[b - 2]? == some .v && k[b - 1]? == some .c)

/-- الوصلُ مرخَّصٌ بقيد الحدّ: مرخَّصٌ موصولًا، ولا قافيةَ مدٍّ يقطعها الحدّ. -/
def strictJoinB (l r : List Cell) : Bool := strictB (l ++ r) && !straddles l r

theorem strictJoinB_strict {l r : List Cell} (h : strictJoinB l r = true) : strictB (l ++ r) = true := by
  simp only [strictJoinB, Bool.and_eq_true] at h
  exact h.1

/-- بلا كلمةٍ أولى لا حدَّ: القيدُ هو `strictB` بعينه. -/
theorem strictJoinB_nil (r : List Cell) : strictJoinB [] r = strictB r := by
  simp [strictJoinB, straddles]

/-- **الحدُّ لكلّ طول:** مدٌّ آخرَ الأولى يليه مُغلِقٌ أوّلَ الثانية — مرفوضٌ مهما كان بعده. -/
theorem straddle_rejected (l r : List Cell) (hb : 1 ≤ l.length)
    (hv : (kindOf (l ++ r))[l.length - 1]? = some .v) (hc : (kindOf (l ++ r))[l.length]? = some .c) :
    strictJoinB l r = false := by
  simp [strictJoinB, straddles, hb, hv, hc]

theorem cited_join_letters_are_carriers :
    ['ش', 'ف', 'ع', 'ح', 'م', 'د'].all (Field112.carriers29.contains ·) = true := by
  decide

open Haraka in
/-- «يَا» كما تحملها الشهادة: `يَ اْ`. -/
def ya : List Cell := [atom 'ي' fatha, atom 'ا' sukun]
open Haraka in
/-- «الشَّافِعِينَ» موصولةً: سقطت همزةُ الوصل ولامُ الشمسيّة بقيّةٌ (`شْ شَ اْ فِ عِ يْ نَ`). -/
def shshafiina : List Cell :=
  [atom 'ش' sukun, atom 'ش' fatha, atom 'ا' sukun, atom 'ف' kasra, atom 'ع' kasra, atom 'ي' sukun,
    atom 'ن' fatha]
open Haraka in
/-- «قُلِ»: `قُ لِ`. -/
def quli : List Cell := [atom 'ق' damma, atom 'ل' kasra]
open Haraka in
/-- «الْحَمْدُ» موصولةً: `لْ حَ مْ دُ`. -/
def lhamdu : List Cell := [atom 'ل' sukun, atom 'ح' fatha, atom 'م' sukun, atom 'د' damma]

/-- **العيبُ مسمًّى ومسدود:** `strictB` على الموصول يقبل «يَا + الشَّافِعِينَ»، و`strictJoinB` يرفضه. -/
theorem ya_shafiina_straddles :
    strictB (ya ++ shshafiina) = true ∧ strictJoinB ya shshafiina = false := by
  have hk : kindOf (ya ++ shshafiina) = flat .none [.CVVC, .CVV, .CV, .CVV, .CV] := by decide
  refine ⟨?_, ?_⟩
  · simp only [strictB, hk, continueB_flat]; decide
  · simp only [strictJoinB, strictB, hk, continueB_flat]; decide

/-- المدُّ والمدغمُ في الكلمة الثانية وحدَها (قُلِ + ضَالِّينَ): مقبول. -/
theorem quli_dallina_join : strictJoinB quli dallina = true := by
  have hk : kindOf (quli ++ dallina) = flat .none [.CV, .CV, .CVVC, .CVV, .CV] := by decide
  simp only [strictJoinB, strictB, hk, continueB_flat]; decide

/-- الوصلُ بعد متحرّك (قُلِ + الْحَمْدُ): مقبول. -/
theorem quli_lhamdu_join : strictJoinB quli lhamdu = true := by
  have hk : kindOf (quli ++ lhamdu) = flat .none [.CV, .CVC, .CVC, .CV] := by decide
  simp only [strictJoinB, strictB, hk, continueB_flat]; decide

/-! ## قيدُ الحدّ وقفًا: المدُّ العارض للسكون

في الوقف يُسكَّن الآخر (`Pause.pause`)، فتجتمع قافيةُ مدٍّ ومُغلِقٌ في الطرف (الرَّحِيمْ: `رَ حِ يْ مْ`) وليس
بعد المُغلِق مثلٌ — فيرفضها `haddB` (`geminateB_vc_final`) مع أنّ `Ternary.pauseB` يقبل CVVC في
الآخر. القيدُ وقفًا: كلُّ `v c` داخليٍّ مدغمٌ كما هو (`geminatePauseB_vc_carrier`)، والطرفيُّ وحده يُقبل
(`geminatePauseB_vc_final`). والوصلُ يستلزم الوقف (`strictB_pause`)، ووقفُ المرخَّص وصلًا مرخَّصٌ وقفًا
إذا صار آخرُه مُغلِقًا (`strictPauseB_pause`)؛ وما يبقى خارجَه باسمه: آخرٌ صار حرفَ مدٍّ بعد مدٍّ
(CVV + `v` ليس مقطعًا) — لا تُدَّعى له مبرهنة. -/

/-- شرطُ الموضع الواحد وقفًا: كـ`stepOK` إلّا `v` ثمّ `c` في الآخر. -/
def stepOKPause : K × Cell → List (K × Cell) → Bool
  | (.v, _), [(.c, _)] => true
  | a, tl => stepOK a tl

def geminatePauseB : List (K × Cell) → Bool
  | [] => true
  | a :: tl => stepOKPause a tl && geminatePauseB tl

def haddPauseB (w : List Cell) : Bool :=
  let p := (kindOf w).zip w
  if isFarq w then geminatePauseB (p.drop 2) else geminatePauseB p

/-- الترخيصُ الثلاثيّ وقفًا مع قيد الحدّ. -/
def strictPauseB (w : List Cell) : Bool := Ternary.pauseB (kindOf w) && haddPauseB w

/-- الوصلُ وقفًا على الثانية: مرخَّصٌ موصولًا وقفًا، ولا قافيةَ مدٍّ يقطعها الحدّ. -/
def strictJoinPauseB (l r : List Cell) : Bool := strictPauseB (l ++ r) && !straddles l r

theorem stepOK_pause {a : K × Cell} {tl : List (K × Cell)} (h : stepOK a tl = true) :
    stepOKPause a tl = true := by
  unfold stepOKPause; split
  · rfl
  · exact h

theorem geminateB_pause : ∀ {p : List (K × Cell)}, geminateB p = true → geminatePauseB p = true
  | [], _ => rfl
  | a :: tl, h => by
    simp only [geminateB, Bool.and_eq_true] at h
    simp only [geminatePauseB, Bool.and_eq_true]
    exact ⟨stepOK_pause h.1, geminateB_pause h.2⟩

theorem haddB_pause {w : List Cell} (h : haddB w = true) : haddPauseB w = true := by
  unfold haddB at h; unfold haddPauseB
  split <;> rename_i hf <;> simp only [hf] at h <;> exact geminateB_pause h

/-- الوصلُ يستلزم الوقف: القيدُ وقفًا لا يضيّق على مرخَّصٍ وصلًا. -/
theorem strictB_pause {w : List Cell} (h : strictB w = true) : strictPauseB w = true := by
  simp only [strictB, Bool.and_eq_true] at h
  simp only [strictPauseB, Bool.and_eq_true]
  exact ⟨(Ternary.pauseB_iff _).2 (Ternary.continue_is_pause ((Ternary.continueB_iff _).1 h.1)),
         haddB_pause h.2⟩

theorem geminatePauseB_cons_true {a : K × Cell} {tl : List (K × Cell)}
    (h : geminatePauseB (a :: tl) = true) : geminatePauseB tl = true := by
  simp only [geminatePauseB, Bool.and_eq_true] at h
  exact h.2

/-- **الأمان:** الرخصةُ طرفيّةٌ وحدَها — كلُّ `v` ثمّ `c` ثمّ خانةٍ مدغمٌ وقفًا كما وصلًا. -/
theorem geminatePauseB_vc_carrier :
    ∀ (p q : List (K × Cell)) (a x y : Cell) (k : K),
      geminatePauseB (p ++ (.v, a) :: (.c, x) :: (k, y) :: q) = true → x.carrier = y.carrier
  | [], q, a, x, y, k, h => by
    simp only [List.nil_append, geminatePauseB, Bool.and_eq_true] at h
    simpa [stepOKPause, stepOK] using h.1
  | b :: p, q, a, x, y, k, h =>
    geminatePauseB_vc_carrier p q a x y k (geminatePauseB_cons_true (by simpa using h))

/-- الطرفُ يُقبل: `v` ثمّ `c` في الآخر لا يُسقط القبول. -/
theorem geminatePauseB_vc_final (p : List (K × Cell)) (a x : Cell) :
    geminatePauseB (p ++ [(.v, a), (.c, x)]) = geminatePauseB (p ++ [(.v, a)]) := by
  induction p with
  | nil => simp [geminatePauseB, stepOKPause, stepOK]
  | cons b p ih =>
    simp only [List.cons_append, geminatePauseB, ih]
    congr 1
    cases p with
    | nil => cases b with | mk k c => cases k <;> simp [stepOKPause, stepOK]
    | cons d q =>
      cases b with | mk k c => cases k <;> cases d with | mk k' c' => cases k' <;>
        cases q <;> simp [stepOKPause, stepOK]

/-- **على الخانات:** في كلّ كلمةٍ مرخَّصةٍ بالقيد وقفًا ليست مدَّ فرق، كلُّ مدٍّ يليه مُغلِقٌ ثمّ خانةٌ
فالمُغلِقُ أوّلُ مثلين. -/
theorem strict_pause_interior_geminate {w : List Cell} (h : strictPauseB w = true)
    (hf : isFarq w = false) {p q : List (K × Cell)} {a x y : Cell} {k : K}
    (hz : (kindOf w).zip w = p ++ (.v, a) :: (.c, x) :: (k, y) :: q) : x.carrier = y.carrier := by
  simp only [strictPauseB, haddPauseB, hf, Bool.and_eq_true] at h
  rw [hz] at h
  exact geminatePauseB_vc_carrier p q a x y k (by simpa using h.2)

/-! ### وقفُ المرخَّص وصلًا مرخَّصٌ وقفًا (إذا صار آخرُه مُغلِقًا) -/

open Stages in
/-- إغلاقُ المقطع بساكنٍ زائد؛ لا إغلاقَ لما كان موقوفًا عليه أصلًا. -/
def Syl.close : Syl → Option Syl
  | .CV => some .CVC
  | .CVV => some .CVVC
  | .CVC => some .CVCC
  | .CVVC => some .CVVCC
  | _ => none

open Stages in
theorem close_atoms {s t : Syl} (h : Syl.close s = some t) : t.atoms = s.atoms ++ [.c] := by
  cases s <;> simp [Syl.close] at h <;> subst h <;> rfl

open Stages in
theorem close_of_not_pauseOnly {s : Syl} (h : Ternary.pauseOnly s = false) : ∃ t, Syl.close s = some t := by
  cases s <;> simp [Ternary.pauseOnly] at h <;> exact ⟨_, rfl⟩

open Stages in
theorem flatMap_ends_cv (ss : List Syl) (ks : List K)
    (h : ss.flatMap Syl.atoms = ks ++ [.cv]) : ∃ ss0, ss = ss0 ++ [.CV] ∧ ss0.flatMap Syl.atoms = ks := by
  rcases List.eq_nil_or_concat ss with rfl | ⟨ss0, s, rfl⟩
  · simp at h
  · simp only [List.concat_eq_append] at h ⊢
    rw [List.flatMap_append, List.flatMap_singleton] at h
    have hl := congrArg List.getLast? h
    rw [List.getLast?_append, List.getLast?_append] at hl
    simp only [List.getLast?_singleton] at hl
    cases s <;> simp [Syl.atoms, Syl.coda] at hl
    refine ⟨ss0, rfl, ?_⟩
    have := List.append_inj_left' h (by rfl)
    simpa [Syl.atoms, Syl.coda] using this

open Stages in
/-- على الأصناف: ما رُخِّص وصلًا وآخرُه متحرّكٌ، إذا صار آخرُه مُغلِقًا رُخِّص وقفًا (بشرط ألّا يكون كلمةً
من خانةٍ واحدة). -/
theorem pauseB_of_continueB_close (ks : List K) (hne : ks ≠ [])
    (h : Ternary.continueB (ks ++ [.cv]) = true) : Ternary.pauseB (ks ++ [.c]) = true := by
  unfold Ternary.continueB at h
  split at h
  · rename_i ss hp
    have hf := flat_parse hp
    simp only [flat, Lead.atoms, List.nil_append] at hf
    obtain ⟨ss0, rfl, hss0⟩ := flatMap_ends_cv ss ks hf
    rw [List.all_append] at h
    simp only [Bool.and_eq_true, List.all_eq_true] at h
    obtain ⟨hall, _⟩ := h
    rcases List.eq_nil_or_concat ss0 with rfl | ⟨ss1, t, rfl⟩
    · simp at hss0; exact absurd hss0 hne
    · simp only [List.concat_eq_append] at hss0 hall
      have ht : Ternary.pauseOnly t = false := by
        have := hall t (by simp)
        simpa using this
      obtain ⟨t', ht'⟩ := close_of_not_pauseOnly ht
      have hk : ks ++ [K.c] = flat .none (ss1 ++ [t']) := by
        simp only [flat, Lead.atoms, List.nil_append, List.flatMap_append, List.flatMap_singleton,
          close_atoms ht']
        rw [← hss0, List.flatMap_append, List.flatMap_singleton, List.append_assoc]
      unfold Ternary.pauseB
      rw [hk, parse_flat]
      simp only [List.dropLast_concat, List.all_eq_true]
      intro s hs
      have := hall s (by simp [hs])
      simpa using this
  · simp at h

/-- الحركةُ الأخيرة في سلسلةٍ (أو السابقة إن كانت فارغة). -/
def lastH (p : Option Haraka) : List Cell → Option Haraka
  | [] => p
  | x :: t => lastH (some x.haraka) t

theorem kindGo_snoc : ∀ (p : Option Haraka) (v : List Cell) (x : Cell),
    kindGo p (v ++ [x]) = kindGo p v ++ [kindOne (lastH p v) x]
  | _, [], _ => rfl
  | p, y :: t, x => by simp [kindGo, lastH, kindGo_snoc (some y.haraka) t x]

theorem isFarq_snoc (v : List Cell) (c : Cell) (h : Haraka) :
    isFarq (v ++ [⟨c.carrier, h⟩]) = isFarq (v ++ [c]) := by
  match v with
  | [] => rfl
  | [_] => rfl
  | [_, _] => simp [isFarq]
  | _ :: _ :: _ :: _ => simp [isFarq]

theorem zip_snoc_of_length {α β} (a : List α) (b : List β) (x : α) (y : β) (h : a.length = b.length) :
    (a ++ [x]).zip (b ++ [y]) = a.zip b ++ [(x, y)] := by
  rw [List.zip_append h]; rfl

theorem stepOKPause_close (a : K × Cell) (p : List (K × Cell)) (k : K) (x y : Cell)
    (hc : x.carrier = y.carrier) (h : stepOK a (p ++ [(k, x)]) = true) :
    stepOKPause a (p ++ [(.c, y)]) = true := by
  obtain ⟨ka, b⟩ := a
  cases ka with
  | cv => simp [stepOKPause, stepOK]
  | c => simp [stepOKPause, stepOK]
  | v =>
    match p with
    | [] => rfl
    | [(kc, z)] =>
      cases kc <;> simp [stepOKPause, stepOK] at h ⊢
      rw [← hc]; exact h
    | (kd, _) :: (ke, _) :: q =>
      cases kd <;> cases ke
      all_goals try simp [stepOKPause, stepOK]
      all_goals simpa [stepOKPause, stepOK] using h

/-- `geminateB` على سلسلةٍ آخرُها متحرّك يعطي `geminatePauseB` على السلسلة نفسها بآخرٍ مُغلِقٍ من حامله. -/
theorem geminatePauseB_close : ∀ (p : List (K × Cell)) (k : K) (x y : Cell), x.carrier = y.carrier →
    geminateB (p ++ [(k, x)]) = true → geminatePauseB (p ++ [(.c, y)]) = true
  | [], _, _, _, _, _ => rfl
  | a :: p, k, x, y, hc, h => by
    simp only [List.cons_append, geminateB, Bool.and_eq_true] at h
    simp only [List.cons_append, geminatePauseB, Bool.and_eq_true]
    exact ⟨stepOKPause_close a p k x y hc h.1, geminatePauseB_close p k x y hc h.2⟩

/-- **وقفُ المرخَّص وصلًا مرخَّصٌ وقفًا** إذا صار آخرُه مُغلِقًا: لكلّ كلمةٍ من خانتين فأكثر آخرُها متحرّك. -/
theorem strictPauseB_pause (v : List Cell) (c : Cell) (hv : v ≠ []) (hcv : c.haraka ≠ .sukun)
    (hk : kindOne (lastH none v) ⟨c.carrier, .sukun⟩ = .c) (h : strictB (v ++ [c]) = true) :
    strictPauseB (Pause.pause (v ++ [c])) = true := by
  rw [Pause.pause_snoc]
  simp only [strictB, Bool.and_eq_true] at h
  obtain ⟨hcont, hhadd⟩ := h
  have hcv' : kindOne (lastH none v) c = .cv := by simp [kindOne, hcv]
  have hk1 : kindOf (v ++ [c]) = kindOf v ++ [.cv] := by rw [kindOf, kindGo_snoc, hcv']; rfl
  have hk2 : kindOf (v ++ [⟨c.carrier, .sukun⟩]) = kindOf v ++ [.c] := by
    rw [kindOf, kindGo_snoc, hk]; rfl
  have hlen : (kindOf v).length = v.length := kindGo_length none v
  simp only [strictPauseB, Bool.and_eq_true]
  constructor
  · rw [hk2]
    exact pauseB_of_continueB_close (kindOf v) (by cases v <;> simp_all [kindOf, kindGo]) (hk1 ▸ hcont)
  · unfold haddB at hhadd
    unfold haddPauseB
    rw [isFarq_snoc, hk2, zip_snoc_of_length _ _ _ _ hlen]
    rw [hk1, zip_snoc_of_length _ _ _ _ hlen] at hhadd
    split at hhadd <;> rename_i hf <;> simp only [hf, ↓reduceIte]
    · match v, hv with
      | [], hv => exact absurd rfl hv
      | [a], _ => simp [isFarq] at hf
      | a :: b :: t, _ =>
        simp only [List.cons_append, kindOf, kindGo, List.zip_cons_cons, List.drop_succ_cons,
          List.drop_zero] at hhadd ⊢
        exact geminatePauseB_close _ _ c ⟨c.carrier, .sukun⟩ rfl hhadd
    · exact geminatePauseB_close _ _ c ⟨c.carrier, .sukun⟩ rfl hhadd

/-! ### الشواهد وقفًا -/

theorem cited_pause_letters_are_carriers :
    ['ر', 'ح', 'م', 'ع', 'ص', 'ت'].all (Field112.carriers29.contains ·) = true := by
  decide

open Haraka in
/-- الرَّحِيمِ موصولةً موقوفًا عليها: `رْ رَ حِ يْ مْ`. -/
def rrahimPause : List Cell :=
  [atom 'ر' sukun, atom 'ر' fatha, atom 'ح' kasra, atom 'ي' sukun, atom 'م' sukun]
open Haraka in
/-- رَحِيمٌ وصلًا: `رَ حِ يْ مُ`. -/
def rahimu : List Cell := [atom 'ر' fatha, atom 'ح' kasra, atom 'ي' sukun, atom 'م' damma]
open Haraka in
/-- الْعَصْرِ موقوفًا عليها: `عَ صْ رْ` (CVCC). -/
def asrPause : List Cell := [atom 'ع' fatha, atom 'ص' sukun, atom 'ر' sukun]
open Haraka in
/-- تَامّْ: `تَ اْ مْ مْ` (CVVCC). -/
def tammPause : List Cell := [atom 'ت' fatha, atom 'ا' sukun, atom 'م' sukun, atom 'م' sukun]
open Haraka in
/-- الرَّحْمَنِ ابتداءً (الكلمةُ اليساريّة بصورتها): `ءَ رْ رَ حْ مَ نِ`. -/
def rrahmani : List Cell :=
  [atom 'ء' fatha, atom 'ر' sukun, atom 'ر' fatha, atom 'ح' sukun, atom 'م' fatha, atom 'ن' kasra]

/-- **الدَّينُ المسمّى مسدود:** الرَّحِيمْ مرفوضةٌ وصلًا (`CVVC_NOT_GEMINATE`) ومقبولةٌ وقفًا. -/
theorem rahim_pause_debt_closed :
    strictB (Pause.pause rahimu) = false ∧ strictPauseB (Pause.pause rahimu) = true ∧
    strictPauseB rahimu = true := by
  refine ⟨?_, ?_, strictB_pause ?_⟩
  · have hk : kindOf (Pause.pause rahimu) = flat .none [.CV, .CVVC] := by decide
    simp only [strictB, hk, continueB_flat]; decide
  · have hk : kindOf (Pause.pause rahimu) = flat .none [.CV, .CVVC] := by decide
    simp only [strictPauseB, Ternary.pauseB, hk, parse_flat]; decide
  · have hk : kindOf rahimu = flat .none [.CV, .CVV, .CV] := by decide
    simp only [strictB, hk, continueB_flat]; decide

/-- `strictPauseB_pause` على شاهده: رَحِيمٌ ← رَحِيمْ. -/
theorem rahimu_pause_by_theorem : strictPauseB (Pause.pause rahimu) = true :=
  strictPauseB_pause [atom 'ر' .fatha, atom 'ح' .kasra, atom 'ي' .sukun] (atom 'م' .damma)
    (by simp) (by decide) (by decide) (by
      show strictB rahimu = true
      have hk : kindOf rahimu = flat .none [.CV, .CVV, .CV] := by decide
      simp only [strictB, hk, continueB_flat]; decide)

/-- CVCC وCVVCC وقفًا: مرفوضان وصلًا (`continueB`) مقبولان وقفًا. -/
theorem asr_tamm_pause :
    strictB asrPause = false ∧ strictPauseB asrPause = true ∧
    strictB tammPause = false ∧ strictPauseB tammPause = true := by
  have h1 : kindOf asrPause = flat .none [.CVCC] := by decide
  have h2 : kindOf tammPause = flat .none [.CVVCC] := by decide
  refine ⟨?_, ?_, ?_, ?_⟩
  · simp only [strictB, h1, continueB_flat]; decide
  · simp only [strictPauseB, Ternary.pauseB, h1, parse_flat]; decide
  · simp only [strictB, h2, continueB_flat]; decide
  · simp only [strictPauseB, Ternary.pauseB, h2, parse_flat]; decide

/-- **الطفرةُ المرفوضة:** الرخصةُ طرفيّةٌ — قَالْتُ تبقى مرفوضةً وقفًا، فالمدُّ قبل مُغلِقٍ داخليّ لا يُقبل. -/
theorem qaaltu_pause_still_refused : strictPauseB qaaltu = false := by
  have hk : kindOf qaaltu = flat .none [.CVVC, .CV] := by decide
  simp only [strictPauseB, Ternary.pauseB, hk, parse_flat]; decide

/-- الوصلُ وقفًا: الرَّحْمَنِ + الرَّحِيمْ مقبولٌ وقفًا ومرفوضٌ وصلًا. -/
theorem rahmani_rahim_join_pause :
    strictJoinB rrahmani rrahimPause = false ∧ strictJoinPauseB rrahmani rrahimPause = true := by
  have hk : kindOf (rrahmani ++ rrahimPause) = flat .none [.CVC, .CVC, .CV, .CVC, .CV, .CVVC] := by
    decide
  refine ⟨?_, ?_⟩
  · simp only [strictJoinB, strictB, hk, continueB_flat]; decide
  · simp only [strictJoinPauseB, strictPauseB, Ternary.pauseB, hk, parse_flat]; decide

theorem strictJoinPauseB_nil (r : List Cell) : strictJoinPauseB [] r = strictPauseB r := by
  simp [strictJoinPauseB, straddles]

theorem strictJoinB_pause {l r : List Cell} (h : strictJoinB l r = true) :
    strictJoinPauseB l r = true := by
  simp only [strictJoinB, Bool.and_eq_true] at h
  simp only [strictJoinPauseB, Bool.and_eq_true]
  exact ⟨strictB_pause h.1, h.2⟩

/-! ## الإلحاقُ ليس إدغامًا (الكتاب س21122: «أدغموا في أعددت كما لم يدغموا في جلببت»)

لامُ الإلحاق (جَلْبَبَ، شَمْلَلَ — س19135: «ألحقوا الزيادة من موضع اللام وأجروها مجرى دحرجت») مثلان
**أوّلُهما متحرّك**؛ والإدغامُ (أَعَدَّ، اطْمَأَنَّ) مثلان **أوّلُهما ساكن**. الفرقُ تعريفٌ على الخانات بلا
بُعدٍ جديد: أوّلُ زوج الإلحاق صنفُه `cv` في أيّ موضع (`ilhaq_not_geminate`) فلا يكون المُغلِقَ `c` الذي
يطلب `stepOK` مثلَه؛ وأوّلُ زوج الإدغام `c` (`idgham_closer`). والشاهدان على الشبكة بأعيانهما
(`jalbaba_vs_aadda`): جَلْبَبَ `cv c cv cv` وأَعَدَّ `cv cv c cv`، كلاهما مرخَّص، وجَلْبَبْ وقفًا وتَجَلْبَبَ
مرخَّصتان، ولا تُردّ إحدى الصورتين إلى الأخرى (`jalbaba_ne_jalabba`). -/

/-- زوجُ الإلحاق: مثلان أوّلُهما متحرّك. -/
def ilhaqPair (x y : Cell) : Bool := x.carrier == y.carrier && x.haraka != .sukun

/-- زوجُ الإدغام: مثلان أوّلُهما ساكن. -/
def idghamPair (x y : Cell) : Bool := x.carrier == y.carrier && x.haraka == .sukun

theorem ilhaq_idgham_disjoint (x y : Cell) (h : ilhaqPair x y = true) : idghamPair x y = false := by
  simp only [ilhaqPair, Bool.and_eq_true, bne_iff_ne, ne_eq] at h
  simp [idghamPair, h.2]

theorem kindOne_vowelled {p : Option Haraka} {x : Cell} (h : x.haraka ≠ .sukun) :
    kindOne p x = .cv := by
  simp [kindOne, h]

/-- **لامُ الإلحاق ليست مُغلِقًا**: في أيّ موضعٍ من أيّ كلمة، أوّلُ زوج الإلحاق صنفُه `cv` — فلا يكون
الـ`c` الذي يطلب `stepOK` مثلَه؛ الإلحاقُ خارج قيد الإدغام بالتعريف لا بالاستثناء. -/
theorem ilhaq_not_geminate :
    ∀ (p : Option Haraka) (w : List Cell) (x y : Cell) (q : List Cell), ilhaqPair x y = true →
      kindGo p (w ++ x :: y :: q) = kindGo p w ++ .cv :: kindGo (some x.haraka) (y :: q)
  | p, [], x, y, q, h => by
    simp only [ilhaqPair, Bool.and_eq_true, bne_iff_ne, ne_eq] at h
    simp [kindGo, kindOne_vowelled h.2]
  | p, a :: t, x, y, q, h => by
    simp [kindGo, ilhaq_not_geminate (some a.haraka) t x y q h]

/-- أوّلُ زوج الإدغام مُغلِقٌ `c` ما لم يكن حاملُه حرفَ مدٍّ بعد حركته (فذلك مدٌّ لا إدغام). -/
theorem idgham_closer {p : Option Haraka} {x y : Cell} (h : idghamPair x y = true)
    (hm : maddVowel x.carrier = none) : kindOne p x = .c := by
  simp only [idghamPair, Bool.and_eq_true, beq_iff_eq] at h
  simp [kindOne, h.2, hm]

open Haraka in
/-- جَلْبَبَ: `جَ لْ بَ بَ` — لامُ الإلحاق مثلان متحرّكان. -/
def jalbaba : List Cell := [atom 'ج' fatha, atom 'ل' sukun, atom 'ب' fatha, atom 'ب' fatha]
open Haraka in
/-- جَلْبَبْ وقفًا. -/
def jalbabPause : List Cell := [atom 'ج' fatha, atom 'ل' sukun, atom 'ب' fatha, atom 'ب' sukun]
open Haraka in
/-- تَجَلْبَبَ (س21110: «تجلبب ويتجلبب أجريته مجرى تدحرج»). -/
def tajalbaba : List Cell := atom 'ت' fatha :: jalbaba
open Haraka in
/-- أَعَدَّ: `ءَ عَ دْ دَ` — الإدغامُ مثلان أوّلُهما ساكن. -/
def aadda : List Cell := [atom 'ء' fatha, atom 'ع' fatha, atom 'د' sukun, atom 'د' fatha]
open Haraka in
/-- الطفرة: جَلَبَّ — لو أُدغمت لامُ الإلحاق لصارت صورةً أخرى بأصنافٍ أخرى. -/
def jalabba : List Cell := [atom 'ج' fatha, atom 'ل' fatha, atom 'ب' sukun, atom 'ب' fatha]

/-- الشاهدان بأعيانهما: كلاهما مرخَّص، وصنفاهما مختلفان عند المثلين. -/
theorem jalbaba_vs_aadda :
    strictB jalbaba = true ∧ strictPauseB jalbabPause = true ∧ strictB tajalbaba = true ∧
    strictB aadda = true ∧
    kindOf jalbaba = [.cv, .c, .cv, .cv] ∧ kindOf aadda = [.cv, .cv, .c, .cv] ∧
    ilhaqPair (atom 'ب' .fatha) (atom 'ب' .fatha) = true ∧
    idghamPair (atom 'د' .sukun) (atom 'د' .fatha) = true := by
  have h1 : kindOf jalbaba = flat .none [.CVC, .CV, .CV] := by decide
  have h2 : kindOf jalbabPause = flat .none [.CVC, .CVC] := by decide
  have h3 : kindOf tajalbaba = flat .none [.CV, .CVC, .CV, .CV] := by decide
  have h4 : kindOf aadda = flat .none [.CV, .CVC, .CV] := by decide
  refine ⟨?_, ?_, ?_, ?_, by decide, by decide, by decide, by decide⟩
  · simp only [strictB, h1, continueB_flat]; decide
  · simp only [strictPauseB, Ternary.pauseB, h2, parse_flat]; decide
  · simp only [strictB, h3, continueB_flat]; decide
  · simp only [strictB, h4, continueB_flat]; decide

/-- الطفرةُ المرفوضة: جَلَبَّ صورةٌ أخرى لا جَلْبَبَ — الخاناتُ تفرّق ولا تُردّ إحداهما إلى الأخرى. -/
theorem jalbaba_ne_jalabba : jalbaba ≠ jalabba ∧ kindOf jalabba = [.cv, .cv, .c, .cv] := by decide

/-! ## اسمُ الرفض `NOT_CONTINUE_LICENSED_AFTER_REPAIR` (سجلُّ الرفض، ADR ٦)

بعد إصلاح الرسم، إن لم يقبل الترخيصُ الثلاثيُّ وصلًا أصنافَ الكلمة رفضتها البوّابةُ بهذا الاسم؛ وهو
`Ternary.continueB` على `kindOf` بعينه، لا حكمٌ آخر. -/

/-- ما يُرفض باسم `NOT_CONTINUE_LICENSED_AFTER_REPAIR`: الأصنافُ لا يقبلها الترخيصُ الثلاثيّ وصلًا. -/
def notContinueLicensed (w : List Cell) : Bool := !Ternary.continueB (kindOf w)

theorem notContinueLicensed_iff (w : List Cell) :
    notContinueLicensed w = true ↔ Ternary.continueB (kindOf w) = false := by
  simp [notContinueLicensed]

/-- المرخَّصُ بالقيد لا يُرفض بهذا الاسم. -/
theorem strictB_not_refused {w : List Cell} (h : strictB w = true) : notContinueLicensed w = false := by
  simp only [strictB, Bool.and_eq_true] at h
  simp [notContinueLicensed, h.1]

end A116.Hadd
