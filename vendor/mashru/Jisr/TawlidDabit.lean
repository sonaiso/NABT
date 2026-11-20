/-
  Jisr/TawlidDabit.lean — مقارنةُ ضابط «نواة التوليد» (`tahaqquq/dawabit/nawat_tawlid/wasf.md`، §القياس) قبل الحالات: الحالةُ بمدخلها
  (مفتاحُ الجذر، والعامل، والجنس)، ومخرجُ المولّد عليها (`Jisr.Tawlid.hukmMiftah`: الصيغةُ والموروثُ والقيدُ والحكم)، والتصنيف. يُودَع مع
  الشفرة قبل أن يقرأ البنّاءُ الحالات، والحالاتُ تُولَّد بعده في `Jisr/TawlidDawabit.lean`.

  **الحقلُ المسؤول** (بنصّ المواصفة): `hukm`، وتُقارن الصيغةُ والموروثُ والقيدُ بالتساوي: اختلافُ أحدها خطأ. ثمّ في الحكم: صوابٌ (تساوٍ)،
  أو نقصُ تغطية («لا حكم» حيث المتوقَّع حكم)، أو تجاوز (حكمٌ حيث المتوقَّع «لا حكم»)، أو قبولٌ خاطئ («مرخَّص» حيث المتوقَّع «ممتنع» أو
  «لا حكم»)، أو ردٌّ خاطئ («ممتنع»/«لا حكم» حيث المتوقَّع «مرخَّص»)، أو اختيارٌ بلا مرجّح (أحدُ بديلي الغموض)، أو خطأ (ما سوى ذلك).
-/
import Jisr.Tawlid

namespace Jisr
namespace Tawlid
namespace Dabit

open Madlul.Tayin Madlul.Nawat

inductive Fia
  | mujib | hadd | kharij | sura | ghumud
  deriving DecidableEq, Repr

/-- حالةُ الضابط: مدخلُها والمتوقَّع. `sigha = none` و`qayd = none` «لا_حكم» (لا عقدة)؛ و`qayd = some none` «لا». -/
structure Hala where
  ism : String
  fia : Fia
  jadhr : String
  amil : Amil
  jins : Option Qism
  sigha : Option String
  mawruth : List Shart
  qayd : Option (Option Qayd)
  hukm : List Hukm
  deriving DecidableEq, Repr

inductive Natija
  | sawab | naqsTaghtiya | tajawuz | qabulKhati | raddKhati | ikhtiyar | khata
  deriving DecidableEq, Repr

/-- مخرجُ المولّد على الحالة: (الصيغة، الموروث، القيد، الحكم). -/
def makhrajMuharrik (h : Hala) : Option String × List Shart × Option (Option Qayd) × Hukm :=
  let (u, k) := hukmMiftah h.jadhr h.amil h.jins
  (u.bind (·.sigha), (u.map (·.mawruth)).getD [], u.map (·.qayd), k)

def qarinHukm (m : List Hukm) (b : Hukm) : Natija :=
  match m with
  | [x] =>
    if x = b then .sawab
    else if b = .laHukm then .naqsTaghtiya
    else if x = .laHukm then .tajawuz
    else if b = .murakhkhas then .qabulKhati
    else if x = .murakhkhas then .raddKhati
    else .khata
  | _ => if m.contains b then .ikhtiyar else .khata

def qarin (h : Hala) : Natija :=
  let (s, w, q, k) := makhrajMuharrik h
  if s = h.sigha ∧ w = h.mawruth ∧ q = h.qayd then qarinHukm h.hukm k else .khata

def natayij (hs : List Hala) : List (String × Fia × Natija) :=
  hs.map fun h => (h.ism, h.fia, qarin h)

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

/-- **جدولُ المقارنة** (على الشاهد). -/
theorem qarin_jadwal :
    qarinHukm [.murakhkhas] .murakhkhas = .sawab ∧ qarinHukm [.murakhkhas] .laHukm = .naqsTaghtiya ∧
    qarinHukm [.laHukm] .murakhkhas = .tajawuz ∧ qarinHukm [.mumtani] .murakhkhas = .qabulKhati ∧
    qarinHukm [.murakhkhas] .mumtani = .raddKhati ∧ qarinHukm [.laJins] .laNawat = .khata ∧
    qarinHukm [.murakhkhas, .laHukm] .laHukm = .ikhtiyar ∧ qarinHukm [.murakhkhas, .laHukm] .mumtani = .khata := by
  decide

/-- اختلافُ الصيغة خطأٌ ولو اتّفق الحكم. -/
theorem sigha_mukhtalifa_khata :
    qarin ⟨"x", .sura, "ك-س-ر", .failiyya, some .insan, some "كسر", [.quwwaMuaththira, .haraka], some none, [.laHukm]⟩ = .khata := by
  decide +kernel

end Dabit
end Tawlid
end Jisr
