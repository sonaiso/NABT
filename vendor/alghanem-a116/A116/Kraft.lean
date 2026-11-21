/-!
# شفرةُ هوفمان في hamil §١٧: كرافت تامّ، والطولُ المتوسّط حسابًا

**الأعدادُ منقولة** — لا مقيسة هنا: الخلايا الثماني وتردداتُها (N = 330,728) وأطوالُ هوفمان من
`peeling_proof.md` §١٧ في `Saleh1967/hamil-hala-zaman-program` (الإيداع ‎232821b‎)، وهي قياسُ hamil على مجمَّده. وما يُبرهَن
هنا **حسابُها** لا قياسُها:

* `huffman_lengths`: خوارزميّةُ هوفمان (دمجُ الأصغرين، `huffman`) على الترددات الثمانية تُخرج الأطوالَ المنقولة بعينها.
* `kraft_complete`: ‎Σ 2^(5 − ℓ) = 2⁵‎ — متراجحةُ كرافت بالتساوي: شفرةٌ بادئةٌ تامّة، لا رمزَ فائض.
* `mean_length_bounds`: ‎2.4335 ≤ L < 2.4336‎ بت/موضع — L كما نقلته hamil، بقسمةٍ صحيحة.
* `flat_surplus_bounds`: فائضُ المسطَّح (3 بتّات) ‎0.5664 ≤ 3 − L < 0.5665‎ — hamil تكتب 0.5665 تقريبًا.
* `assignment_monotone`: الأكثرُ ترددًا لا يأخذ أطولَ من الأقلّ — شرطُ الترتيب (الرهن لا يُكسب بتبديل).

ولا يُبرهَن هنا حدُّ شانون ‎H ≤ L‎ ولا ‎H = 2.3098‎: يحتاجان اللوغاريتم على الحقيقيّات، والنواةُ هنا بلا Mathlib عمدًا. وهو
نفسُه ما ينقض «الضغطَ الفائق» تحت H: لا شفرةَ بلا فقدٍ طولُها دون الإنتروبيا.
-/

set_option autoImplicit false

namespace A116.Kraft

/-- الخلايا الثماني بتردداتها، كما في hamil §١٧ (منقول). -/
def freqs : List Nat := [123351, 78037, 45976, 37320, 37150, 3742, 2633, 2519]

/-- أطوالُ هوفمان المنقولة بالترتيب نفسه. -/
def lens : List Nat := [2, 2, 3, 3, 3, 4, 5, 5]

def total : Nat := freqs.foldl (· + ·) 0

/-- البتّاتُ على المجمَّد كلِّه: ‎Σ تردد × طول‎. -/
def bits : Nat := (freqs.zip lens).foldl (fun s p => s + p.1 * p.2) 0

/-! ## هوفمان: دمجُ الأصغرين -/

/-- عقدةٌ: وزنُها، ورموزُها. -/
abbrev Node := Nat × List Nat

def insertSorted (x : Node) : List Node → List Node
  | [] => [x]
  | y :: t => if x.1 ≤ y.1 then x :: y :: t else y :: insertSorted x t

def sortNodes (l : List Node) : List Node := l.foldr insertSorted []

/-- دمجُ الأصغرين وقودًا: كلُّ رمزٍ في العقدتين يزيد طولُه بتًّا. -/
def merge : Nat → List Node → List Nat → List Nat
  | 0, _, d => d
  | _ + 1, [], d => d
  | _ + 1, [_], d => d
  | f + 1, a :: b :: t, d =>
    let syms := a.2 ++ b.2
    let d' := (List.range d.length).map fun i => if syms.contains i then d.getD i 0 + 1 else d.getD i 0
    merge f (insertSorted (a.1 + b.1, syms) t) d'

def huffman (w : List Nat) : List Nat :=
  merge w.length (sortNodes ((List.range w.length).map fun i => (w.getD i 0, [i]))) (w.map fun _ => 0)

/-- **هوفمان يُخرج الأطوالَ المنقولة.** -/
theorem huffman_lengths : huffman freqs = lens := by decide

/-- **كرافت تامّ**: ‎Σ 2^(5 − ℓ) = 2⁵‎. -/
theorem kraft_complete : (lens.map fun l => 2 ^ (5 - l)).foldl (· + ·) 0 = 2 ^ 5 := by decide

/-- **L بين 2.4335 و2.4336** بت/موضع. -/
theorem mean_length_bounds : 24335 * total ≤ bits * 10000 ∧ bits * 10000 < 24336 * total := by decide

/-- **فائضُ المسطَّح** ‎3 − L‎ بين 0.5664 و0.5665. -/
theorem flat_surplus_bounds :
    5664 * total ≤ (3 * total - bits) * 10000 ∧ (3 * total - bits) * 10000 < 5665 * total := by decide

/-- **الترتيب**: كلّما زاد التردّدُ لم يزد الطول. -/
theorem assignment_monotone :
    ((freqs.zip lens).zip ((freqs.zip lens).drop 1)).all
      (fun (p, q) => decide (q.1 ≤ p.1) && decide (p.2 ≤ q.2)) = true := by decide

end A116.Kraft
