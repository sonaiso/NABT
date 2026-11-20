/-
  Nizam/Talab.lean — قرار المالك ٢ (2026-10-18، 19:39): «الأمر والالتماس والسؤال "لا حكم" بلا مقام».

  السند وتعارضُه المعلن (ج3 س415، ترقيم `scripts/tahwil_docx.py`): القسمةُ عند النبهاني قسمةُ **دالٍّ بالوضع** — «المركب …
  وهو من أقسام الدال وحده»، «فإن أفاد طلباً بذاته، أي بالوضع، ينظر» — ومعيارُها الرتبة: «مع الاستعلاء على المطلوب منه فهو الأمر …
  مع التساوي فهو الالتماس … مع التسفل، أي التذلل، فهو السؤال»، ومثالُ الالتماس «أعطني الكتاب» بصيغة الأمر نفسها؛ وس600 يعرّف
  الأمر «طـلب الفعل على وجه الاستعلاء». فالرتبةُ هي المسنودة بالسطر. أمّا عدُّ الرتبة من المقام لا من اللفظ فقرارُ المالك ٢،
  وهو يخالف إطار س415 (قسمة الدال وحده)؛ والتوفيقُ بينهما — أنّ الوضعَ يفيد الطلب، والرتبةَ حالُ المتكلّم والمخاطَب لا يحملها
  لفظ «افعل» — قراءةُ البنّاء، معروضةٌ على المالك لا محسومة.
  ما تثبته المبرهنات (على هذا النموذج): `la_qisma_bila_maqam` و`qisma_bil_maqam` تعريفيّتان (`rfl`)؛ و`la_dalla_min_sigha`
  على النموذج: الصيغةُ نوعٌ بمنشئٍ واحد (`Sigha.ifal`) بتعيين البنّاء، فالمبرهنةُ تثبت أنّ `qismBiRutba` ليست ثابتة، لا أنّ
  الصيغة تقع في الثلاثة (ذاك مفروضٌ في النوع، وسنده مثالُ س415)؛ و`qismBiRutba_mutabayin` على النموذج بالحالات.
  ربطُ الصيغة بخلايا القارئ لم يُبنَ (م4 في البروتوكول).
  بلا sorry ولا axiom ولا native_decide.
-/
import Nizam.Asas

namespace Nizam.Talab

/-- رتبةُ المتكلّم من المخاطَب (ج3 س415): استعلاءٌ أو تساوٍ أو تسفّل؛ وعدُّها من المقام قرارُ المالك ٢ (س415 يجعل القسمة من الدال وحده). -/
inductive Rutba | istila | tasawi | tasafful
  deriving DecidableEq, Repr

/-- أقسامُ الطلب لتحصيل الماهية الثلاثة. -/
inductive Qism | amr | iltimas | sual
  deriving DecidableEq, Repr

/-- صيغةُ الطلب لتحصيل الماهية («افعل»)، مجرّدةً عن خلاياها. -/
inductive Sigha | ifal
  deriving DecidableEq, Repr

/-- ما يرخّصه اللفظ وحده: طلبُ تحصيل الماهية، لا أكثر. -/
inductive Madlul | talabTahsil
  deriving DecidableEq, Repr

def talabMinSigha : Jisr Sigha Madlul := fun _ => .murakhkhas .talabTahsil

/-- القسمُ بالرتبة (س415). -/
def qismBiRutba : Rutba → Qism
  | .istila => .amr
  | .tasawi => .iltimas
  | .tasafful => .sual

/-- القسمةُ الثلاثيّة: بمقامٍ مودَعٍ (رتبةٍ) تُرخَّص، وبلا مقامٍ لا حكم. -/
def qisma (maqam : Option Rutba) : Jisr Madlul Qism := fun _ =>
  match maqam with
  | some r => .murakhkhas (qismBiRutba r)
  | none => .laHukm

/-- بلا مقام: من الصيغة إلى القسم «لا حكم»، لا امتناع ولا ترخيص. -/
theorem la_qisma_bila_maqam (s : Sigha) : tarkib talabMinSigha (qisma none) s = .laHukm := rfl

/-- وبمقامٍ مودَعٍ يُرخَّص القسمُ الذي تعيّنه الرتبة. -/
theorem qisma_bil_maqam (s : Sigha) (r : Rutba) :
    tarkib talabMinSigha (qisma (some r)) s = .murakhkhas (qismBiRutba r) := rfl

/-- على النموذج (الصيغةُ بمنشئٍ واحد): لا دالّةَ من الصيغة وحدها تطابق القسمةَ في كلّ رتبة، أي `qismBiRutba` ليست ثابتة. -/
theorem la_dalla_min_sigha : ¬ ∃ f : Sigha → Qism, ∀ r, f .ifal = qismBiRutba r := by
  rintro ⟨f, hf⟩
  have h1 := hf .istila
  have h2 := hf .tasawi
  rw [h1] at h2
  cases h2

/-- والقسمةُ بالرتبة متباينة: كلُّ رتبةٍ قسمٌ مختلف (فالمقامُ وحده يفرّق). -/
theorem qismBiRutba_mutabayin (r₁ r₂ : Rutba) (h : qismBiRutba r₁ = qismBiRutba r₂) : r₁ = r₂ := by
  cases r₁ <;> cases r₂ <;> first | rfl | cases h

end Nizam.Talab
