import A116.Cells

/-!
# الحقلُ 112 في hamil هو جدولُ الـ112 في A116 بعينه، والفرقُ صفُّ الهمزة لا غير

## المصدران (مقروءان من الشيفرة، لا من نثر)

* hamil (`Saleh1967/hamil-hala-zaman-program`، الالتزام `6efd033`):
  `algebra_engine.LETTERS = list("ابتثجحخدذرزسشصضطظعغفقكلمنهوي") + ["ى","ة","آ","ء"]`،
  و`field112_laws.BASE28 = LETTERS[:28]`، والحركاتُ الأربع `STATES[:4]` =
  فتحة، ضمة، كسرة، سكون. والحقلُ `BASE28 × HARAKAT4`.
* Alghanem: `letter_fingerprint.LETTER_VOCABULARY = (*"ابتثجحخدذرزسشصضطظعغفقكلمنهوي", "ء")`،
  وهو ترتيبُ الحوامل الـ29 في `Cells`.

`letters28` أدناه هي السلسلةُ نفسُها حرفًا بحرف؛ ويفحص
`tests/tools/test_lean_field112_conformance.py` مطابقتَها لـ`LETTER_VOCABULARY` في CI.

## المبرهنات

* `field112_eq_cells112`: صورةُ `cells112` بأسماء الحروف **تساوي** جداءَ hamil
  `letters28 × Haraka.all` قائمةً بقائمة، بالترتيب نفسه.
* `hamzaRow_named`: صفُّ الهمزة هو `ء` بحالاته الأربع.
* `cells_eq_field112_append_hamza`: الـ116 = الحقلُ 112 ثمّ صفُّ الهمزة.

فالـ28 في الحقل 112 **حروفٌ** لا «مبنياتُ إحالة»، والفرقُ 116 − 112 هو حاملُ الهمزة
المفردة بحالاته الأربع.
-/

namespace A116.Field112

open A116

/-- الحروفُ الثمانيةُ والعشرون بترتيب المصدرين. -/
def letters28 : List Char := "ابتثجحخدذرزسشصضطظعغفقكلمنهوي".toList

theorem letters28_length : letters28.length = 28 := by decide

theorem letters28_nodup : letters28.Nodup := by decide

/-- الحواملُ التسعةُ والعشرون: الثمانيةُ والعشرون ثمّ الهمزة. -/
def carriers29 : List Char := letters28 ++ ['ء']

theorem carriers29_length : carriers29.length = carrierCount := by decide

/-- اسمُ الحامل حرفًا. -/
def carrierChar (l : Fin carrierCount) : Char :=
  carriers29.get ⟨l.val, by rw [carriers29_length]; exact l.isLt⟩

/-- الخانةُ حرفًا وحالة. -/
def named (c : Cell) : Char × Haraka := (carrierChar c.carrier, c.haraka)

/-- حقلُ hamil: `BASE28 × HARAKAT4` بالترتيب: الحرفُ أوّلًا ثمّ الحالة. -/
def hamilField112 : List (Char × Haraka) :=
  letters28.flatMap fun l => Haraka.all.map fun h => (l, h)

theorem hamilField112_length : hamilField112.length = 112 := by decide

theorem field112_eq_cells112 : cells112.map named = hamilField112 := by decide

theorem hamzaRow_named : hamzaRow.map named = Haraka.all.map fun h => ('ء', h) := by decide

theorem cells_eq_field112_append_hamza :
    cells.map named = hamilField112 ++ Haraka.all.map (fun h => ('ء', h)) := by decide

end A116.Field112
