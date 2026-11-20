/-!
# الخاناتُ المئةُ والستَّ عشرة — تعريفٌ وتعداد

النظيرُ البايثونيُّ: `src/alghanem/arabic/a116_bridge_licence.py`
(`THE_CARRIERS`، `THE_HARAKAT`، `a116_cells`) و`letter_fingerprint.LETTER_VOCABULARY`.

## المسلّمات المُعلَنة في هذا الملف

* **م١ (الحوامل):** تسعةٌ وعشرون حاملًا، مُرقَّمةً `0 … 28` بترتيب
  `LETTER_VOCABULARY` نفسِه: الثمانيةُ والعشرون من «ا» إلى «ي»، ثمّ «ء» في
  الموضع `28`. والرقمُ هنا اسمٌ لا قيمة؛ والمطابقةُ بين الرقم والحرف يفحصها
  `tools/lean_a116_conformance.py` في CI، لا هذا الملفّ.
* **م٢ (الحالات):** أربعٌ بترتيب `THE_DECLARED_HARAKAT`: فتحة، ضمّة، كسرة، سكون.

## ما يُبرهَن هنا

1. `cells` تعدادٌ **تامٌّ** (`mem_cells`) و**بلا تكرار** (`cells_nodup`)،
   فطولُه هو عددُ الخانات، وهو `116` (`cells_length`). فالعددُ نتيجةٌ لا مُدخَل.
2. صفُّ الهمزة وحدَه هو الفرقُ بين الـ116 والـ112: `cells112` (ما سوى الهمزة)
   طولُه `112`، و`hamzaRow` أربعُ خاناتٍ لا غير.

ولا يُستعمَل القرارُ بالمترجِم في أيِّ موضع: كلُّ قرارٍ تفحصه نواةُ Lean نفسُها.
-/

namespace A116

/-- الحالاتُ الأربع (م٢). -/
inductive Haraka where
  | fatha
  | damma
  | kasra
  | sukun
  deriving DecidableEq, Repr

namespace Haraka

/-- الحالاتُ بترتيبها المُعلَن. -/
def all : List Haraka := [fatha, damma, kasra, sukun]

/-- أهي سكون؟ وهي الخاصّيّةُ الوحيدةُ التي يقرؤها النموذجُ المقطعيّ. -/
def isSukun : Haraka → Bool
  | sukun => true
  | _ => false

/-- رقمُ الحالة بترتيب `THE_DECLARED_HARAKAT`؛ يُستعمَل في جدول المطابقة وحدَه. -/
def index : Haraka → Nat
  | fatha => 0
  | damma => 1
  | kasra => 2
  | sukun => 3

theorem mem_all (h : Haraka) : h ∈ all := by
  cases h <;> simp [all]

end Haraka

/-- عددُ الحوامل (م١). -/
def carrierCount : Nat := 29

/-- الخانةُ: حاملٌ وحالته. -/
structure Cell where
  carrier : Fin carrierCount
  haraka : Haraka
  deriving DecidableEq, Repr

/-- أهي خانةُ سكون؟ -/
def Cell.isSukun (c : Cell) : Bool := c.haraka.isSukun

/-- الخاناتُ مُعدَّدةً بترتيب `a116_cells`: الحاملُ أوّلًا ثمّ الحالة. -/
def cells : List Cell :=
  (List.finRange carrierCount).flatMap fun l => Haraka.all.map fun h => ⟨l, h⟩

/-- **التمام:** كلُّ خانةٍ ممكنةٍ واقعةٌ في التعداد. -/
theorem mem_cells (c : Cell) : c ∈ cells := by
  cases c with
  | mk l h =>
    simp only [cells, List.mem_flatMap, List.mem_map]
    exact ⟨l, List.mem_finRange l, h, Haraka.mem_all h, rfl⟩

/-- **المنع:** لا خانةَ تُعَدّ مرّتين. -/
theorem cells_nodup : cells.Nodup := by decide

/-- **العدد:** طولُ تعدادٍ تامٍّ بلا تكرار هو `116 = 29 × 4`. -/
theorem cells_length : cells.length = 116 := by decide

theorem cells_length_eq_product : cells.length = carrierCount * Haraka.all.length := by
  decide

/-- الهمزةُ المفردة: الحاملُ الأخيرُ في `LETTER_VOCABULARY`. -/
def hamza : Fin carrierCount := ⟨28, by decide⟩

/-- جدولُ الـ112: كلُّ خانةٍ حاملُها غيرُ الهمزة. -/
def cells112 : List Cell := cells.filter fun c => c.carrier != hamza

/-- صفُّ الهمزة: الفرقُ بين الجدولين. -/
def hamzaRow : List Cell := cells.filter fun c => c.carrier == hamza

theorem cells112_length : cells112.length = 112 := by decide

theorem hamzaRow_length : hamzaRow.length = 4 := by decide

/-- الفرقُ صفُّ الهمزة وحدَه: `116 = 112 + 4`، مُشتقًّا لا مكتوبًا. -/
theorem cells_split : cells.length = cells112.length + hamzaRow.length := by decide

end A116
