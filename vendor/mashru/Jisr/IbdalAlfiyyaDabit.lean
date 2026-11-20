/-
  Jisr/IbdalAlfiyyaDabit.lean — مقارنةُ ضابط «الإبدال: الواوُ والياءُ في الكلمة» (`tahaqquq/dawabit/ibdal/wasf.md`) قبل الحالات: الحالةُ
  بنوعها، وحكمُ المحرّك عليها، والتصنيف. يُودَع مع الشفرة قبل أن يقرأ البنّاءُ الحالات، والحالاتُ تُولَّد بعده في
  `Jisr/IbdalAlfiyyaDawabit.lean`.

  **الحقلُ المسؤول** `hukm` في كلّ حالة. والمواصفةُ تسمّي القيمَ ولا تسمّي أسماءَ المقارنة؛ فالتصنيفُ من البنّاء على نسق الضوابط القائمة
  (`Jisr/NassItarDabit.lean`):
  * المتوقَّعُ واحد: صواب؛ أو نقصُ تغطية («لا حكم» من المحرّك حيث المتوقَّع حكم)؛ أو تجاوز (حكمٌ حيث المتوقَّع «لا حكم»)؛ أو قبولٌ خاطئ
    (`غير_ممنوع` حيث المتوقَّع `ممنوع`)؛ أو ردٌّ خاطئ (`ممنوع` حيث المتوقَّع `غير_ممنوع`).
  * المتوقَّعُ بديلان (`غموض`): «لا حكم» من المحرّك صواب (لم يختر)، وأحدُ البديلين «اختيارٌ بلا مرجّح»، وما سواهما خطأٌ باسمه (`khata`).
  * ما رفضه القارئ (`kalima = none`) إخفاقٌ باسمه (`rafdQari`).
  وسببُ المنع (`Sabab`) لا يُقارَن: المواصفةُ لا تسأل عنه.
-/
import Jisr.IbdalAlfiyya

namespace Jisr.IbdalAlfiyya.Dabit

open Jisr.IbdalAlfiyya

inductive Fia
  | mujib | hadd | kharij | umum | ghumud
  deriving DecidableEq, Repr

/-- القيمُ الثلاث في المواصفة: `ممنوع`، `غير_ممنوع`، `لا_حكم`. -/
inductive Qima
  | mamnu | ghayrMamnu | laHukm
  deriving DecidableEq, Repr

/-- حكمُ المحرّك بلا سببه. -/
def qimaOf : Hukm → Qima
  | .mamnu _ => .mamnu
  | .ghayrMamnu => .ghayrMamnu
  | .laHukm => .laHukm

/-- حالةُ الضابط بعد التوليد: الكلمةُ كما يقرؤها القارئ (`none`: رفضها)، والمتوقَّع (واحد، أو بديلان في الغموض). -/
structure Hala where
  ism : String
  fia : Fia
  kalima : Option Dal.Kalima
  hukm : List Qima
  zawj : Option String
  deriving DecidableEq, Repr

inductive Natija
  | sawab | naqsTaghtiya | tajawuz | qabulKhati | raddKhati | ikhtiyar | rafdQari | khata
  deriving DecidableEq, Repr

/-- حكمُ المحرّك على الحالة. -/
def hukmMuharrik (h : Hala) : Qima :=
  match h.kalima with
  | some w => qimaOf (hukmKalima w)
  | none => .laHukm

def qarin (m : List Qima) (b : Qima) : Natija :=
  match m with
  | [x] =>
    if x = b then .sawab
    else match x, b with
      | .laHukm, _ => .tajawuz
      | _, .laHukm => .naqsTaghtiya
      | .mamnu, _ => .qabulKhati
      | _, _ => .raddKhati
  | _ => if b = .laHukm then .sawab else if m.contains b then .ikhtiyar else .khata

/-- النتائجُ على قائمة حالات: (الحالة، الفئة، النتيجة). -/
def natayij (halat : List Hala) : List (String × Fia × Natija) :=
  halat.map fun h => if h.kalima.isNone then (h.ism, h.fia, .rafdQari) else (h.ism, h.fia, qarin h.hukm (hukmMuharrik h))

structure Ihsa where
  sawab : Nat
  naqsTaghtiya : Nat
  tajawuz : Nat
  qabulKhati : Nat
  raddKhati : Nat
  ikhtiyar : Nat
  rafdQari : Nat
  khata : Nat
  deriving DecidableEq, Repr

def ihsa (l : List (String × Fia × Natija)) : Ihsa :=
  let c (n : Natija) := (l.filter (fun x => x.2.2 == n)).length
  ⟨c .sawab, c .naqsTaghtiya, c .tajawuz, c .qabulKhati, c .raddKhati, c .ikhtiyar, c .rafdQari, c .khata⟩

/-- الإخفاقاتُ بأسمائها: (الحالة، النتيجة). -/
def akhta (l : List (String × Fia × Natija)) : List (String × Natija) :=
  (l.filter (fun x => x.2.2 != .sawab)).map (fun x => (x.1, x.2.2))

/-- ما رفضه القارئ. -/
def rafd (halat : List Hala) : List String := (halat.filter (·.kalima.isNone)).map (·.ism)

/-- **الأزواج** (حرفٌ أو حركةٌ واحدة): لكلّ حالةٍ لها زوجٌ اسمُه أكبرُ من اسمها بترتيب النصوص (فيُعدّ الزوجُ مرّةً):
    (هي، زوجُها، أيختلف حكمُ المحرّك فيهما؟). -/
def azwaj (halat : List Hala) : List (String × String × Bool) :=
  halat.filterMap fun h =>
    match h.zawj with
    | some z =>
      if h.ism < z then
        match halat.find? (·.ism == z) with
        | some g => some (h.ism, z, hukmMuharrik h != hukmMuharrik g)
        | none => none
      else none
    | none => none

/-! ## جدولُ المقارنة (على الشاهد) -/

/-- **الحكمُ الواحد** (تسعةُ أزواج) **والبديلان.** -/
theorem qarin_jadwal :
    [Qima.mamnu, .ghayrMamnu, .laHukm].flatMap (fun m => [Qima.mamnu, .ghayrMamnu, .laHukm].map (qarin [m])) =
      [.sawab, .qabulKhati, .naqsTaghtiya, .raddKhati, .sawab, .naqsTaghtiya, .tajawuz, .tajawuz, .sawab] ∧
    qarin [.mamnu, .ghayrMamnu] .laHukm = .sawab ∧ qarin [.mamnu, .ghayrMamnu] .mamnu = .ikhtiyar ∧
    qarin [.mamnu, .laHukm] .ghayrMamnu = .khata := by
  decide

/-- **رفضُ القارئ إخفاقٌ باسمه** ولو كان المتوقَّعُ بديلين أو «لا حكم». -/
theorem rafd_ikhfaq :
    natayij [⟨"x", .ghumud, none, [.mamnu, .ghayrMamnu], none⟩, ⟨"y", .umum, none, [.laHukm], none⟩] =
      [("x", .ghumud, .rafdQari), ("y", .umum, .rafdQari)] := by
  decide

/-- **حكمُ المحرّك على كلمة القارئ:** «مُيْقِنٌ» ممنوعة (1222)، و«الْمُوقِنُ» غيرُ ممنوعة على صورة الابتداء بهمزة «أل». -/
theorem muharrik_kalima :
    hukmMuharrik ⟨"a", .hadd, some ⟨[109, 47, 30, 57, 59], false, false⟩, [.mamnu], none⟩ = .mamnu ∧
    hukmMuharrik ⟨"b", .mujib, some ⟨[55, 109, 115, 30, 57], true, true⟩, [.ghayrMamnu], none⟩ = .ghayrMamnu := by
  decide +kernel

end Jisr.IbdalAlfiyya.Dabit
