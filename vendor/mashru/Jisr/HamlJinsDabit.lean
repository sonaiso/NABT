/-
  Jisr/HamlJinsDabit.lean — مقارنةُ ضابط «الحمل من الجنس» (`tahaqquq/dawabit/haml_jins/wasf.md`، §القياس) قبل الحالات: الحالةُ بمدخلها
  المجرَّد (جنسُ المسند إليه، ومثالُ المسند، والنسبة)، وحكمُ المحرّك عليها (`Jisr.QabiliyyaJins.hukmMujarrad`)، والتصنيف. يُودَع مع الشفرة
  قبل أن يقرأ البنّاءُ الحالات، والحالاتُ تُولَّد بعده في `Jisr/HamlJinsDawabit.lean`.

  **الحقلُ المسؤول** (بنصّ المواصفة): `hukm` في كلّ حالة: صوابٌ (تساوٍ)، أو نقصُ تغطية («لا حكم» حيث المتوقَّع حكم)، أو تجاوز (حكمٌ حيث
  المتوقَّع «لا حكم»)، أو قبولٌ خاطئ («مرخَّص» حيث المتوقَّع «ممتنع» أو «لا حكم»)، أو ردٌّ خاطئ («ممتنع»/«لا حكم» حيث المتوقَّع «مرخَّص»)،
  أو اختيارٌ بلا مرجّح (أحدُ بديلي الغموض)، أو خطأ (ما سوى ذلك).
-/
import Jisr.QabiliyyaJins

namespace Jisr
namespace QabiliyyaJins
namespace Dabit

inductive Fia
  | mujib | hadd | kharij | umum | ghumud
  deriving DecidableEq, Repr

/-- حالةُ الضابط: مدخلُها المجرَّد والمتوقَّع (واحدٌ، أو بديلان في الغموض). -/
structure Hala where
  ism : String
  fia : Fia
  jins : Option Madlul.Tayin.Qism
  mithalQab : Option Madlul.Tayin.QabHaraka
  nisba : Nisab.Nisba
  hukm : List HukmMujarrad
  deriving DecidableEq, Repr

inductive Natija
  | sawab | naqsTaghtiya | tajawuz | qabulKhati | raddKhati | ikhtiyar | khata
  deriving DecidableEq, Repr

/-- حكمُ المحرّك على الحالة. -/
def hukmMuharrik (h : Hala) : HukmMujarrad := hukmMujarrad h.jins h.mithalQab h.nisba

def qarin (m : List HukmMujarrad) (b : HukmMujarrad) : Natija :=
  match m with
  | [x] =>
    if x = b then .sawab
    else if b = .laHukm then .naqsTaghtiya
    else if x = .laHukm then .tajawuz
    else if b = .murakhkhas then .qabulKhati
    else if x = .murakhkhas then .raddKhati
    else .khata
  | _ => if m.contains b then .ikhtiyar else .khata

def natayij (hs : List Hala) : List (String × Fia × Natija) :=
  hs.map fun h => (h.ism, h.fia, qarin h.hukm (hukmMuharrik h))

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

/-- الإخفاقاتُ بأسمائها. -/
def akhta (l : List (String × Fia × Natija)) : List (String × Natija) :=
  (l.filter (fun x => x.2.2 != .sawab)).map (fun x => (x.1, x.2.2))

/-- **جدولُ المقارنة** (على الشاهد): الصوابُ بالتساوي، والخلوُّ حيث حكمٌ نقصُ تغطية، والحكمُ حيث خلوٌّ تجاوز، والترخيصُ في غير موضعه قبولٌ
خاطئ، وردُّ المرخَّص ردٌّ خاطئ، وغيابُ الصفّ في غير موضعه خطأ. -/
theorem qarin_jadwal :
    qarin [.murakhkhas] .murakhkhas = .sawab ∧ qarin [.murakhkhas] .laHukm = .naqsTaghtiya ∧
    qarin [.laHukm] .murakhkhas = .tajawuz ∧ qarin [.mumtani] .murakhkhas = .qabulKhati ∧
    qarin [.murakhkhas] .mumtani = .raddKhati ∧ qarin [.laJins] .laMithal = .khata ∧
    qarin [.murakhkhas, .laHukm] .laHukm = .ikhtiyar ∧ qarin [.murakhkhas, .laHukm] .mumtani = .khata := by
  decide

end Dabit
end QabiliyyaJins
end Jisr
