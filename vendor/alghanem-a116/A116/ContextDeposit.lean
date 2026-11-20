import A116.NizamLine
import A116.Iltiqa
import A116.PauseCount
import A116.ContinueCount

/-!
# مودَعُ السياق والسطر (ADR ٣٤)

مودَعُ السياق (`gate/api.py` بسياق `joined`، `tools/gen_context_certificates.py`) يقرن كلَّ كلمةٍ **خامٍ** بصورة ابتداء
ما قبلها **مصلَحةً** عليها (`Iltiqa.strictJoinRepairedB`)، وآخرُ السطر وقف. هذا `depAQ`. والسطرُ: الكلماتُ مصلَحةً
كلٌّ على تاليتها (`repairsL`)، أوّلُها صورةُ الابتداء.

أنّ المودَعَ **هو** السطرُ (`strictLinePauseB ∘ repairsL`) وصورةُ ابتداء الأولى (`strictB`) وكلُّ كلمةٍ خامٍ بعدها
مرخَّصةٌ بعد «بَ» (`rawAQ`) — بشروطٍ مسمّاة: غيرُ فارغة، وإن ختمها ساكنٌ فطولُها اثنتان فأكثر، وأوّلُها متحرّكٌ أو
ساكنٌ ليس حرفَ مدّ، وصورةُ ابتدائها هي أو متحرّكٌ قبلها — مبرهَنٌ في Algebra على هذه التعريفات بأعيانها
(`HarfBridge.deposit_eq_line_pause`، `HarfBridge.deposit_eq_line`، ADR ٦ هناك، `943fe7f`)؛ ولا يُعاد هنا.

وهنا الشاهدان على أنّ الشرطين لازمان:
* `deposit_needs_raw`: «بِ قَالْ الْحَمْدُ» — السطرُ («بِ قَالِ لْحَمْدُ») مرخَّصٌ وصلًا ووقفًا والمودَعُ يرفض؛ فالمودَعُ
  ليس السطرَ وحدَه.
* `deposit_needs_free`: «ءَ» ثمّ «اْلْ» (أوّلُها حرفُ مدٍّ ساكن) — المودَعُ وصلًا (`depA`) غيرُ الصيغة؛ ووقفًا يتساويان
  (`free_witness_pause_agrees`). والقيدُ اللازمُ بعد التعميم (ADR ٣٦): حرفُ المدّ الساكن أوّلًا يليه متحرّك
  (`deposit_needs_vowel_after_madd`، وصلًا ووقفًا).
-/

set_option autoImplicit false

namespace A116.ContextDeposit

open A116 A116.Hadd A116.NizamLine A116.Iltiqa A116.Ladder Haraka

def depTailAQ : List Cell → List (List Cell × List Cell) → Bool
  | _, [] => true
  | Sp, [(W, _)] => strictJoinPauseRepairedB Sp W
  | Sp, (W, S) :: q :: rest => strictJoinRepairedB Sp W && depTailAQ S (q :: rest)

/-- المودَع: أزواجُ (الكلمةُ خامًا، صورةُ ابتدائها)؛ آخرُ السطر وقف، والكلمةُ الواحدةُ ابتداءٌ ووقف. -/
def depAQ : List (List Cell × List Cell) → Bool
  | [] => true
  | [(_, S)] => strictPauseB S
  | (_, S) :: q :: rest => strictB S && depTailAQ S (q :: rest)

/-- كلُّ كلمةٍ مصلَحةٌ على تاليتها، والأخيرةُ كما هي. -/
def repairsL : List (List Cell) → List (List Cell)
  | [] => []
  | [w] => [w]
  | w :: v :: rest => (repair w v).1 :: repairsL (v :: rest)

def baA : List Cell := [atom 'ب' fatha]

/-- كلُّ كلمةٍ خامٍ بعد الأولى مرخَّصةٌ بعد «بَ»، والأخيرةُ وقفًا. -/
def rawAQ : List (List Cell × List Cell) → Bool
  | [] => true
  | [(W, _)] => strictJoinPauseB baA W
  | (W, _) :: q :: rest => strictJoinB baA W && rawAQ (q :: rest)

def biA : List Cell := [atom 'ب' kasra]
def qaalA : List Cell := [atom 'ق' fatha, atom 'ا' sukun, atom 'ل' sukun]

/-- «بِ قَالْ الْحَمْدُ»: الأولى صورتُها هي، و«الْحَمْدُ» صورتُها همزةٌ مفتوحةٌ قبلها. -/
def biQaalHamd : List (List Cell × List Cell) :=
  [(biA, biA), (qaalA, qaalA), (Iltiqa.lhamdu, atom 'ء' fatha :: Iltiqa.lhamdu)]

/-- **الخامُ لازم**: السطرُ المصلَح مرخَّص، والمودَعُ يرفض، والفرقُ «قَالْ» خامًا بعد «بَ». -/
theorem deposit_needs_raw :
    depAQ biQaalHamd = false ∧
    strictLinePauseB (repairsL [biA, qaalA, Iltiqa.lhamdu]) = true ∧
    strictLineB (repairsL [biA, qaalA, Iltiqa.lhamdu]) = true ∧ strictB biA = true ∧
    rawAQ biQaalHamd.tail = false ∧
    repairsL [qaalA, Iltiqa.lhamdu] = [[atom 'ق' fatha, atom 'ا' sukun, atom 'ل' kasra], Iltiqa.lhamdu] := by
  decide +kernel

def depTailA : List Cell → List (List Cell × List Cell) → Bool
  | _, [] => true
  | Sp, (W, S) :: rest => strictJoinRepairedB Sp W && depTailA S rest

/-- المودَعُ والسطرُ كلُّه وصل (مواضعُ السطر الداخليّة). -/
def depA : List (List Cell × List Cell) → Bool
  | [] => true
  | (_, S) :: rest => strictB S && depTailA S rest

/-- **الأوّلُ الحرّ لازمٌ للصيغة**: «ءَ» ثمّ «اْلْ» (أوّلُها حرفُ مدٍّ ساكن) — المودَعُ غيرُ الصيغة. -/
theorem deposit_needs_free :
    depA [([atom 'ء' fatha], [atom 'ء' fatha]),
          ([atom 'ا' sukun, atom 'ل' sukun], [atom 'ء' fatha, atom 'ا' sukun, atom 'ل' sukun])] ≠
      (strictLineB (repairsL [[atom 'ء' fatha], [atom 'ا' sukun, atom 'ل' sukun]]) &&
        strictB [atom 'ء' fatha] && strictJoinB baA [atom 'ا' sukun, atom 'ل' sukun]) := by
  decide +kernel

/-! ## الوقفُ يُحسب بالآلة المبرهنة (ADR ٣٦)

`Stages.parse` لا تختزله النواةُ في `decide +kernel`، لكنّ `pauseB` و`continueB` مبرهَنٌ أنّهما قبولُ آلتين منتهيتين
بنيويّتَي التكرار (`Ternary.pauseB_eq_acc`، `Ternary.continueB_eq_accC`). فالحسابُ وقفًا يمرّ بهما. -/

/-- شاهدُ ADR ٣٤ («ءَ» ثمّ «اْلْ») **ليس شاهدًا وقفًا**: آخرُ السطر وقفٌ فالمدُّ العارض يُقبل، فيتساوى الطرفان. -/
theorem free_witness_pause_agrees :
    depAQ [([atom 'ء' fatha], [atom 'ء' fatha]),
           ([atom 'ا' sukun, atom 'ل' sukun], [atom 'ء' fatha, atom 'ا' sukun, atom 'ل' sukun])] =
      (strictLinePauseB (repairsL [[atom 'ء' fatha], [atom 'ا' sukun, atom 'ل' sukun]]) &&
        strictB [atom 'ء' fatha] &&
        rawAQ [([atom 'ا' sukun, atom 'ل' sukun], [atom 'ء' fatha, atom 'ا' sukun, atom 'ل' sukun])]) := by
  simp only [depAQ, depTailAQ, rawAQ, strictJoinPauseRepairedB, strictJoinPauseB, strictLinePauseB,
    strictPauseB, strictB, Ternary.pauseB_eq_acc, Ternary.continueB_eq_accC]
  decide +kernel

def abba : List Cell := [atom 'ا' sukun, atom 'ب' sukun, atom 'ب' fatha]

/-- **الشاهدُ وقفًا ووصلًا** (`HarfBridge.deposit_needs_vowel_after_madd` في Algebra، ADR ٧ هناك): «بَ اْبْبَ وَ»،
وصورةُ ابتداء الثانية «ءِاْبْبَ» — حرفُ مدٍّ ساكنٌ يليه ساكن: في السطر بعد فتحةٍ مدٌّ يُغلقه أوّلُ مثلين، وفي صورة
الابتداء بعد كسرةٍ ساكنٌ يليه ساكن؛ المودَعُ يرفض والصيغةُ تقبل. -/
theorem deposit_needs_vowel_after_madd :
    depAQ [([atom 'ب' fatha], [atom 'ب' fatha]), (abba, atom 'ء' kasra :: abba),
      ([atom 'و' fatha], [atom 'و' fatha])] = false ∧
    (strictLinePauseB (repairsL [[atom 'ب' fatha], abba, [atom 'و' fatha]]) && strictB [atom 'ب' fatha] &&
      rawAQ [(abba, atom 'ء' kasra :: abba), ([atom 'و' fatha], [atom 'و' fatha])]) = true ∧
    depA [([atom 'ب' fatha], [atom 'ب' fatha]), (abba, atom 'ء' kasra :: abba),
      ([atom 'و' fatha], [atom 'و' fatha])] = false ∧
    (strictLineB (repairsL [[atom 'ب' fatha], abba, [atom 'و' fatha]]) && strictB [atom 'ب' fatha] &&
      strictJoinB baA abba && strictJoinB baA [atom 'و' fatha]) = true := by
  simp only [depAQ, depTailAQ, depA, depTailA, rawAQ, strictJoinPauseRepairedB, strictJoinRepairedB,
    strictJoinPauseB, strictJoinB, strictLinePauseB, strictLineB, strictPauseB, strictB,
    Ternary.pauseB_eq_acc, Ternary.continueB_eq_accC]
  decide +kernel

end A116.ContextDeposit
