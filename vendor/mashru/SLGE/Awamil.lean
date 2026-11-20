import SLGE.Tarkib
import SLGE.AwamilTable

/-!
# العواملُ معادلات: كلُّ عاملٍ قيدٌ على حالات مواضع معمولاته

**المعادلة:** ‎state(موضع الدور r) = h‎، و‎state(r₁) = state(r₂)‎ للتابع. والحالةُ حالةُ الخانة الأخيرة
(‎Bridge.irabState‎: رفع ‎1‎، نصب ‎0‎، جرّ ‎2‎، جزم ‎3‎). فالعاملُ ليس كلمةً تُعدّ بل دالّةٌ في ‎n‎:
يقيّد حالاتِ مواضع بعينها، ومواضعُه في الإطار (‎Tarkib.framesL‎) ولو كان مضمَرًا.

**الأدوار:** ‎0‎ الاسم/المفعول الأوّل، ‎1‎ الخبر/المفعول الثاني، ‎2‎ الفعل المضارع، ‎6‎ المجرور، ‎9‎ المعطوف عليه،
‎10‎ المعطوف، ‎11‎ فعل الشرط، ‎12‎ جوابه، ‎13‎ المنادى.

**الأصناف** (من عمود «الحكم الإعرابي» في المرفق، مولَّدة في ‎AwamilTable.lean‎):
‎1‎ كان (13)، ‎2‎ إنّ (6)، ‎3‎ ظنّ (10)، ‎4‎ ناصبُ المضارع (7)، ‎5‎ جازمُه (4)، ‎6‎ كاد (6)، ‎7‎ الجارّ (17)، ‎8‎ العاطف (8)،
‎9‎ لامُ التعليل (1، جارّةٌ أو ناصبةٌ بأنْ مضمرة)، ‎10‎ الشرطُ الجازم (10)، ‎11‎ الشرطُ غيرُ الجازم (4)، ‎12‎ الاستفهام (10)، ‎13‎ النداء (4).
-/

set_option synthInstance.maxSize 8192
set_option synthInstance.maxHeartbeats 0

namespace SLGE
namespace Awamil

/-- المعادلاتُ البديلة لكلّ صنف: كلُّ بديلٍ قائمةُ (دور، حالة). -/
def eqs : Nat → List (List (Nat × Nat))
  | 1 => [[(0, 1), (1, 0)]]
  | 2 => [[(0, 0), (1, 1)]]
  | 3 => [[(0, 0), (1, 0)]]
  | 4 => [[(2, 0)]]
  | 5 => [[(2, 3)]]
  | 6 => [[(0, 1), (2, 1)]]
  | 7 => [[(6, 2)]]
  | 9 => [[(6, 2)], [(2, 0)]]
  | 10 => [[(11, 3), (12, 3)]]
  | 13 => [[(13, 0)], [(13, 1)]]
  | _ => [[]]

/-- معادلاتُ التساوي (التابعُ يأخذ حالةَ متبوعه). -/
def links : Nat → List (Nat × Nat)
  | 8 => [(9, 10)]
  | _ => []

def isFilRole (r : Nat) : Bool := r == 2 || r == 11 || r == 12

/-- الحالاتُ الجائزة في الدور: الاسمُ ‎{1,0,2}‎ والفعلُ ‎{1,0,3}‎ (‎Wad.irabOf‎ عبر ‎irabState‎). -/
def allowed (r h : Nat) : Bool :=
  (if isFilRole r then Wad.irabOf .fil else Wad.irabOf .ism).any (fun x => Bridge.irabState x == h)

/-- **المرفقُ كما وُلِّد:** ‎100‎ عاملٍ، كلٌّ في صنف (لا صنفَ ‎0‎)، وأعدادُ الأصناف. -/
theorem table_classes :
    table.length = 100 ∧ table.all (fun r => r.2.1 != 0) = true ∧
    ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13].map fun c => (table.filter (·.2.1 == c)).length) =
      [13, 6, 10, 7, 4, 6, 17, 8, 1, 10, 4, 10, 4] ∧
    (table.filter (·.2.2)).map (·.1) = ["فاء السببية", "واو المعية"] := by decide

/-- **الانغلاق:** لا معادلةَ في أيّ صنفٍ تفرض على دورٍ حالةً لا يقبلها قسمُه (لا جرَّ على فعل ولا جزمَ على اسم). -/
theorem eqs_closed : (List.range 14).all (fun c => (eqs c).all fun alt => alt.all fun (r, h) => allowed r h) = true := by
  decide

/-- **المعادلةُ تعيّن الناسخ:** زوجُ (حالة الاسم، حالة الخبر) يعيّن صنفَه — كان، إنّ، ظنّ — والابتداءُ ‎(1,1)‎ هو الرابع. -/
theorem nasikh_by_equation :
    ([1, 2, 3].map fun c => eqs c) = [[[(0, 1), (1, 0)]], [[(0, 0), (1, 1)]], [[(0, 0), (1, 0)]]] ∧
    ([1, 2, 3].map fun c => eqs c).Nodup := by decide

/-- **العاملُ في الفرع اللفظيّ والإطار متّفقان:** معادلاتُ كان وإنّ وظنّ والناصب والجازم هي ‎Tarkib.reqState‎ بعينها. -/
theorem eqs_match_tarkib :
    eqs 1 = [[(0, (Tarkib.reqState 0 1 0).getD 9), (1, (Tarkib.reqState 0 1 1).getD 9)]] ∧
    eqs 2 = [[(0, (Tarkib.reqState 0 2 0).getD 9), (1, (Tarkib.reqState 0 2 1).getD 9)]] ∧
    eqs 3 = [[(0, (Tarkib.reqState 0 3 0).getD 9), (1, (Tarkib.reqState 0 3 1).getD 9)]] ∧
    eqs 4 = [[(2, (Tarkib.reqState 1 4 2).getD 9)]] ∧ eqs 5 = [[(2, (Tarkib.reqState 1 5 2).getD 9)]] := by decide

/-- **الاستنفاد:** كلُّ (قسم، إعراب) تفرضه معادلةُ صنفٍ ما — مع الابتداء والتجرّد (‎Wad.manawiF‎) للرفع. -/
theorem eqs_exhaust :
    [(false, 0), (false, 2), (true, 0), (true, 3)].all (fun (isF, h) =>
      (List.range 14).any fun c => (eqs c).any fun alt => alt.any fun (r, h') => isFilRole r == isF && h' == h) = true ∧
    [(false, 1), (true, 1)].all (fun (isF, h) =>
      (List.range 14).any fun c => (eqs c).any fun alt => alt.any fun (r, h') => isFilRole r == isF && h' == h) = true := by
  decide

/-! ## التابع: معادلةُ التساوي تنتشر -/

/-- سلسلةُ معطوفات: كلُّ متجاورين حالتُهما واحدة. -/
def chainEq : List Nat → Bool
  | a :: b :: l => a == b && chainEq (b :: l)
  | _ => true

/-- **لكلّ سلسلةِ عطف:** إن تساوى كلُّ متجاورين فكلُّها حالةُ الأوّل — فالعاملُ في المتبوع عاملٌ في التوابع كلّها. -/
theorem atf_propagates : ∀ (l : List Nat) (a : Nat), chainEq (a :: l) = true → ∀ x ∈ l, x = a
  | [], _, _, x, hx => by simp at hx
  | b :: l, a, h, x, hx => by
    simp only [chainEq, Bool.and_eq_true, beq_iff_eq] at h
    obtain ⟨hab, hrest⟩ := h
    simp at hx
    rcases hx with hx | hx
    · rw [hx, hab]
    · rw [atf_propagates l b hrest x hx, hab]

/-! ## المضمَرُ عاملٌ له موضع: ‎أنْ‎ المضمرة بعد فاء السببية وواو المعية -/

/-- **العاملُ المضمَر لا يفقد قيمته في ‎n‎:** ‎(لا تُهمِلْ) فتندمَ‎ — إطارٌ فيه ناصبٌ مقدَّر قبل الفعل، غيرُ الإطار بلا ناصب؛
والكلمةُ الظاهرة واحدة (‎تندمَ‎) والرقمان مختلفان، والفعلُ فيهما بحالتين مختلفتين (نصب/رفع). -/
theorem hidden_amil_value :
    (1, 4, [(7, 1, 0), (2, 0, 0), (3, 1, Tarkib.deic)]) ∈ Tarkib.framesL ∧
    (1, 0, [(2, 0, 0), (3, 1, Tarkib.deic)]) ∈ Tarkib.framesL ∧
    Tarkib.reqState 1 4 2 = some 0 ∧ Tarkib.reqState 1 0 2 = some 1 ∧
    Tarkib.sEnc (1, 4, [(7, 1, 0), (2, 0, 0), (3, 1, Tarkib.deic)]) [[4 * 18 + 0, 4 * 14 + 3, 4 * 17 + 0, 4 * 27 + 0]] ≠
      Tarkib.sEnc (1, 0, [(2, 0, 0), (3, 1, Tarkib.deic)]) [[4 * 18 + 0, 4 * 14 + 3, 4 * 17 + 0, 4 * 27 + 0]] := by
  refine ⟨by decide +kernel, by decide +kernel, rfl, rfl, ?_⟩
  exact Tarkib.frame_value _ _ (by decide +kernel) (by decide +kernel) (by decide) _

end Awamil
end SLGE
