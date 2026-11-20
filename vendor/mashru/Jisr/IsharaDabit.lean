/-
# مقارنةُ ضابط أسماء الإشارة قبل الحالات

**ما في هذا الملفّ.** مقارنةُ الضابط (`tahaqquq/dawabit/ishara/wasf.md`، §القياس): الحالةُ بنوعها، وحكمُ `Jisr.Ishara.hukm` عليها، والتصنيف.
يُودَع مع الشفرة قبل أن يقرأ البنّاءُ الحالات، والحالاتُ تُولَّد بعده في `Jisr/IsharaDawabit.lean`.

**الحقلُ المسؤول** `hukm` في كلّ حالة (بنصّ المواصفة):
- صواب.
- نقصُ تغطية: «لا حكم» حيث المتوقَّع حكم.
- قبولٌ خاطئ: «مقبول» حيث المتوقَّع «خطأ».
- ردٌّ خاطئ: «خطأ» حيث المتوقَّع «مقبول».
- تجاوز: حكمٌ حيث المتوقَّع «لا حكم».
- وفي `غموض` بحكمين: «لا حكم» من المحرّك صواب (لم يختر)، وأحدُ البديلين «اختيارٌ بلا مرجّح».

**زيادةُ البنّاء** (ليست في المواصفة): في `غموض` بحكمين، حكمٌ ليس من البديلين ولا «لا حكم» خطأٌ باسمه (`Natija.khata`). والمحرّكُ لا يُخرج إلّا
حكمًا واحدًا، فـ«البديلان معًا» في المواصفة لا يقع منه.
-/
import Jisr.Ishara

namespace Jisr
namespace Ishara
namespace Dabit

inductive Fia
  | mujib | hadd | kharij | umum | ghumud
  deriving DecidableEq, Repr

/-- حالةُ الضابط بعد التوليد: المدخل، والمتوقَّع (حكمٌ واحد، أو بديلان في الغموض)، والزوج. -/
structure Hala where
  ism : String
  fia : Fia
  dakhil : Dakhil
  hukm : List Hukm
  zawj : Option String
  deriving DecidableEq, Repr

inductive Natija
  | sawab | naqsTaghtiya | tajawuz | qabulKhati | raddKhati | ikhtiyar | khata
  deriving DecidableEq, Repr

/-- المقارنة: المتوقَّع (`m`) وحكمُ المحرّك (`b`). -/
def qarinHukm (m : List Hukm) (b : Hukm) : Natija :=
  match m with
  | [x] =>
    if x = b then .sawab
    else match x, b with
      | .laHukm, _ => .tajawuz
      | _, .laHukm => .naqsTaghtiya
      | .maqbul, _ => .raddKhati
      | _, _ => .qabulKhati
  | _ => if b = .laHukm then .sawab else if m.contains b then .ikhtiyar else .khata

/-- النتائجُ على قائمة حالات: (الحالة، الفئة، النتيجة). -/
def natayij (halat : List Hala) : List (String × Fia × Natija) :=
  halat.map fun h => (h.ism, h.fia, qarinHukm h.hukm (hukm h.dakhil))

structure Ihsa where
  sawab : Nat
  naqsTaghtiya : Nat
  tajawuz : Nat
  qabulKhati : Nat
  raddKhati : Nat
  ikhtiyar : Nat
  khata : Nat
  deriving DecidableEq, Repr

def ihsa (l : List (String × Fia × Natija)) : Ihsa :=
  let c (n : Natija) := (l.filter (fun x => x.2.2 == n)).length
  ⟨c .sawab, c .naqsTaghtiya, c .tajawuz, c .qabulKhati, c .raddKhati, c .ikhtiyar, c .khata⟩

/-- الإخفاقاتُ بأسمائها: (الحالة، النتيجة). -/
def akhta (l : List (String × Fia × Natija)) : List (String × Natija) :=
  (l.filter (fun x => x.2.2 != .sawab)).map (fun x => (x.1, x.2.2))

/-- **الأزواج** (مدخلان يختلفان في حقلٍ واحد): لكلّ حالةٍ لها زوجٌ اسمُه أكبرُ من اسمها بترتيب النصوص (فيُعدّ الزوجُ مرّةً):
    (هي، زوجُها، أيختلف حكمُ المحرّك فيهما؟). -/
def azwaj (halat : List Hala) : List (String × String × Bool) :=
  halat.filterMap fun h =>
    match h.zawj with
    | some z =>
      if h.ism < z then
        match halat.find? (·.ism == z) with
        | some g => some (h.ism, z, hukm h.dakhil != hukm g.dakhil)
        | none => none
      else none
    | none => none

/-! ## جدولُ المقارنة (على الشاهد) -/

/-- **الحكمُ الواحد** (تسعةُ أزواج) **والبديلان.** -/
theorem qarin_hukm :
    [Hukm.maqbul, .khata, .laHukm].flatMap (fun m => [Hukm.maqbul, .khata, .laHukm].map (qarinHukm [m])) =
      [.sawab, .raddKhati, .naqsTaghtiya, .qabulKhati, .sawab, .naqsTaghtiya, .tajawuz, .tajawuz, .sawab] ∧
    qarinHukm [.maqbul, .khata] .laHukm = .sawab ∧ qarinHukm [.maqbul, .khata] .maqbul = .ikhtiyar ∧
    qarinHukm [.maqbul, .laHukm] .khata = .khata := by
  decide

end Dabit
end Ishara
end Jisr
