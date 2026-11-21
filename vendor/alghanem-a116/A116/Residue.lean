import A116.Recovery

/-!
# بقيّةُ الرسم — SLGE لقواعد الإملاء

الكلمةُ المرسومةُ في الطبعة = **الصورةُ القانونيّة** (كلُّ حرفٍ بعلامته، تقبلها البوّابة) +
**بقيّة**: قائمةُ ما فعلته الطبعةُ بالصورة، تعديلًا تعديلًا، كلُّ تعديلٍ بقاعدته وموضعه وسجلِّه
(`A116.Recovery.EditRecord`). فيُطوى الرسمُ عددين: عددُ الخانات (`Numbering`/`Fold`) وعددُ
البقيّة، ويُفكّ إلى الرسم بعينه.

## القواعد المودَعة (من إحصاء 9,668 كلمةٍ موقوفةٍ في مفردات المصحف، 2026-10-06)

| القاعدة | ما تركته الطبعة | الإصلاح (رسم ← قانونيّ) | السجلّ (قانونيّ ← رسم) |
|---|---|---|---|
| `sukun` | حرفٌ بلا علامة (مدٌّ، ميمُ جمع، نونٌ مخفاة…) | إدخالُ سكونٍ بعده | حذفُ السكون |
| `fariqa` | ألفٌ فارقةٌ بعد واوٍ ساكنةٍ في الآخر | حذفُ الألف | إعادةُ الألف |
| `tanwinAlif` | تنوينُ الفتح مكتوبًا بعد الألف | تقديمُ التنوين على الألف | تأخيرُه |
| `idgham` | شدّةٌ أوّلَ الكلمة (إدغامٌ من الوصل) | حذفُ الشدّة | إعادتُها |
| `ulaWaw` | واوٌ بعد «أُ» في أُولَئِكَ/أُولُو/أُولِي/أُولَاتُ لا تُنطق | حذفُ الواو | إعادتُها |

## ما يُبرهَن

* كلُّ قاعدةٍ تعديلٌ له سجلٌّ يعيد الرسمَ بعينه (`sukun_restore`، `fariqa_restore`،
  `tanwinAlif_restore`، `idgham_restore`، `ulaWaw_restore`) — مثولاتٌ لـ`edit_roundtrip`.
* **سلسلةُ التعديلات تُردّ بالترتيب المعكوس** (`chain_restore`): مهما تعدّدت قواعدُ الطبعة في
  الكلمة الواحدة، الردُّ يعيد الرسم.
* **بلا بقيّةٍ لا رسم**: صورتان قانونيّتان واحدةٌ وبقيّتان مختلفتان رسمان مختلفان — والعكس:
  الرسمُ يحدّد (الصورة، البقيّة) معًا (`residue_separates`، من
  `restoration_forces_fiber_separation`).

ولا يُبرهَن هنا أنّ `gate/residue.py` يطبّق هذه القواعد بعينها على الرسم الحقيقيّ؛ ذلك ما
تفحصه المطابقة والقياسُ المطبوع (كم كلمةً انتقلت من DEFER إلى READY).
-/

namespace A116.Residue

open A116.Recovery

/-- رموزُ الرسم: حرفٌ، علامةٌ (فتحة ضمّة كسرة سكون)، شدّة، تنوين، ألفٌ خنجريّة (طبعةُ globalquran). -/
inductive Glyph where
  | letter : Fin 29 → Glyph
  | mark : Fin 4 → Glyph
  | shadda : Glyph
  | tanwin : Fin 3 → Glyph
  | dagger : Glyph
  deriving DecidableEq, Repr

/-- قواعدُ الطبعة الستّ المبرهَنةُ هنا (والباقي في `gate/residue.py` مثولاتٌ لـ`edit_roundtrip` نفسِه). -/
inductive Rule where
  | sukun | fariqa | tanwinAlif | idgham | daggerAlif | ulaWaw
  deriving DecidableEq, Repr

/-- تعديلٌ واحد: قاعدتُه وسجلُّه. -/
structure Edit where
  rule : Rule
  record : EditRecord Glyph

abbrev sukun : Glyph := .mark 3
abbrev alif : Glyph := .letter 1
abbrev waw : Glyph := .letter 26

/-! ## القواعد مثولاتٍ لـ`edit_roundtrip` -/

/-- `sukun`: الطبعةُ حذفت سكونًا بعد حرفٍ؛ الإصلاحُ يدخله؛ السجلُّ يحذفه. -/
theorem sukun_restore (l r : List Glyph) :
    restoreEdit (l ++ ([sukun] ++ r)) ⟨l.length, 1, []⟩ = l ++ r := by
  have := edit_roundtrip l [] [sukun] r
  simpa using this

/-- `fariqa`: الطبعةُ كتبت ألفًا بعد واوٍ ساكنةٍ في الآخر؛ الإصلاحُ يحذفها؛ السجلُّ يعيدها. -/
theorem fariqa_restore (l : List Glyph) :
    restoreEdit (l ++ [waw, sukun]) ⟨l.length + 2, 0, [alif]⟩ = l ++ [waw, sukun, alif] := by
  have := edit_roundtrip (l ++ [waw, sukun]) [alif] [] []
  simpa using this

/-- `tanwinAlif`: الطبعةُ كتبت الألفَ قبل التنوين؛ الإصلاحُ يقدّم التنوين؛ السجلُّ يعيد الترتيب. -/
theorem tanwinAlif_restore (l r : List Glyph) (t : Fin 3) :
    restoreEdit (l ++ ([.tanwin t, alif] ++ r)) ⟨l.length, 2, [alif, .tanwin t]⟩ =
      l ++ [alif, .tanwin t] ++ r :=
  edit_roundtrip l _ _ r

/-- `idgham`: الطبعةُ وضعت شدّةً أوّلَ الكلمة؛ الإصلاحُ يحذفها؛ السجلُّ يعيدها. -/
theorem idgham_restore (c : Fin 29) (r : List Glyph) :
    restoreEdit ([.letter c] ++ r) ⟨1, 0, [.shadda]⟩ = [.letter c] ++ [.shadda] ++ r := by
  have := edit_roundtrip [.letter c] [.shadda] [] r
  simpa using this

/-- `daggerAlif`: الطبعةُ (globalquran، ومنها مدوّنةُ hamil) كتبت ألفًا خنجريّةً فوق الحرف (الرَّحْمَٰنِ)؛ الإصلاحُ
يحذفها فتصير الصورةُ صورةَ المدوّنة المختومة بعينها (الرَّحْمَنِ)؛ السجلُّ يعيدها في موضعها. -/
theorem daggerAlif_restore (l r : List Glyph) :
    restoreEdit (l ++ r) ⟨l.length, 0, [.dagger]⟩ = l ++ [.dagger] ++ r := by
  have := edit_roundtrip l [.dagger] [] r
  simpa using this

/-- `ulaWaw`: الطبعةُ كتبت واوًا بعد «أُ» في أُولَئِكَ وأُولُو وأُولِي وأُولَاتُ ولا تُنطق؛ الإصلاحُ يحذفها فلا يُشهَد
بمدٍّ غيرِ منطوق؛ السجلُّ يعيدها في موضعها (ADR ٥٢؛ ومواضعُها في `gate/residue.py` بـ`ULA_TAILS`). -/
theorem ulaWaw_restore (l r : List Glyph) :
    restoreEdit (l ++ r) ⟨l.length, 0, [waw]⟩ = l ++ [waw] ++ r := by
  have := edit_roundtrip l [waw] [] r
  simpa using this

/-! ## السلسلة -/

/-- ردُّ قائمةِ سجلّاتٍ بالترتيب المعطى (الأخيرُ تطبيقًا أوّلُ ردًّا). -/
def restoreAll (out : List Glyph) : List (EditRecord Glyph) → List Glyph
  | [] => out
  | e :: es => restoreAll (restoreEdit out e) es

/-- تطبيقٌ مجرَّد: خطوةٌ تأخذ رسمًا وتعطي رسمًا وسجلًّا يردّه. -/
structure Step where
  apply : List Glyph → List Glyph
  record : List Glyph → EditRecord Glyph
  sound : ∀ s, restoreEdit (apply s) (record s) = s

/-- تطبيقُ خطواتٍ متتالية مع جمع السجلّات (الأحدثُ في الرأس). -/
def runSteps : List Step → List Glyph → List Glyph × List (EditRecord Glyph)
  | [], s => (s, [])
  | st :: sts, s =>
    let (s', recs) := runSteps sts (st.apply s)
    (s', recs ++ [st.record s])

/-- **سلسلةُ التعديلات تُردّ**: مهما كان عددُ القواعد المطبَّقة على الكلمة، `restoreAll` يعيد الرسم. -/
theorem chain_restore : ∀ (sts : List Step) (s : List Glyph),
    restoreAll (runSteps sts s).1 (runSteps sts s).2 = s
  | [], s => rfl
  | st :: sts, s => by
    simp only [runSteps]
    have ih := chain_restore sts (st.apply s)
    rw [restoreAll_append, ih]
    simp [restoreAll, st.sound]
where
  restoreAll_append (out : List Glyph) (a b : List (EditRecord Glyph)) :
      restoreAll out (a ++ b) = restoreAll (restoreAll out a) b := by
    induction a generalizing out with
    | nil => rfl
    | cons e es ih => simp [restoreAll, ih]

/-- **الرسمُ يحدّد الصورةَ والبقيّةَ معًا**: صورتان وبقيّتان تردّان إلى رسمٍ واحد هما واحدةٌ وواحدة. -/
theorem residue_separates (f : List Glyph → List Glyph) (res : List Glyph → List (EditRecord Glyph))
    (h : ∀ s, restoreAll (f s) (res s) = s) {s s' : List Glyph}
    (hf : f s = f s') (hr : res s = res s') : s = s' :=
  restoration_forces_fiber_separation f res (fun p => restoreAll p.1 p.2) h hf hr

end A116.Residue
