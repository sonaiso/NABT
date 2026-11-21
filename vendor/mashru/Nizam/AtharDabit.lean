/-
  Nizam/AtharDabit.lean — مقارنةُ ضابط «أثر العُقَد» (`tahaqquq/dawabit/athar/wasf.md`، §القياس) قبل الحالات: الحالةُ بنوعها، ومخرجُ
  المحرّك فيها، والتصنيف. يُودَع مع الشفرة قبل أن يقرأ البنّاءُ الحالات، والحالاتُ تُولَّد بعده في `Nizam/AtharDawabit.lean`.

  **مخرجُ المحرّك في الحقلين** (تعيينُ البنّاء، بنصّ المواصفة §ما يُختبر):
  * `quwwa` في نوع `قوة`: `quwwaJumla` على نصّ الجملة (`Nizam/Athar.lean`)، بقيمه الخمس التي يُخرجها (إثبات، نفي، تعليق، إنشاء، لا حكم).
  * `qayd` في نوع `قيد`: «لا حكم» إن لم يكن للجملة إطارٌ مرخَّصٌ بعد المعجم (`adwarKalimat` فارغة)؛ وإلّا صنفُ قيد الجملة (`qaydJumla`) إن كان
    له صنفُ مخالفة (`sinfOf`)، وإلّا «لا قيد» (قيدٌ بلا صنف — الاسم —، أو لا قيد). وصنفٌ واحدٌ أبدًا: `qaydJumla` يختار قيدًا واحدًا.

  **التصنيف** (بنصّ المواصفة §القياس): القائمتان مجموعتين — التساوي صواب، و«لا حكم» حيث المتوقَّعُ حكمٌ نقصُ تغطية، وحكمٌ حيث المتوقَّعُ
  «لا حكم» تجاوز، وفي `غموض` بعضُ البديلين اختيارٌ بلا مرجّح، وما سوى ذلك خطأ؛ وما لا يقرأ القارئُ كلَّ كلماته (`kullMaqrua`) ردٌّ من القارئ
  (`rafdQari`) في حقله، لا «لا حكم».
-/
import Nizam.Athar

namespace Nizam.Athar
namespace Dabit

open Nizam.Silsila
open Jisr.SakkJumla (Quwwa)

inductive Fia
  | mujib | hadd | kharij | umum | ghumud
  deriving DecidableEq, Repr

inductive Naw
  | quwwa | qayd
  deriving DecidableEq, Repr

/-- قيمةُ حقل القيد: صنفُ مخالفة، أو «لا قيد»، أو «لا حكم». -/
inductive QaydQ
  | sinf (k : SLGE.Madlul.Mukhalafa)
  | laQayd
  | laHukm
  deriving DecidableEq, Repr

/-- حالةُ الضابط بعد التوليد: نصُّها، ومتوقَّعُ حقل نوعها (واحدٌ، أو بديلان فأكثر)، والحقلُ الآخر فارغ. -/
structure Hala where
  ism : String
  naw : Naw
  fia : Fia
  nass : String
  quwwa : List Quwwa
  qayd : List QaydQ
  zawj : Option String
  deriving DecidableEq, Repr

/-- مخرجُ المحرّك في حقل القيد. -/
def qaydMuharrik (t : List Char) : QaydQ :=
  if (adwarKalimat t).isEmpty then .laHukm
  else
    match qaydJumla t with
    | some p =>
      match Jisr.MantuqMafhum.sinfOf p.1 with
      | some k => .sinf k
      | none => .laQayd
    | none => .laQayd

inductive Natija
  | sawab | naqsTaghtiya | tajawuz | ikhtiyar | khata | rafdQari
  deriving DecidableEq, Repr

/-- القائمتان مجموعتين. -/
def sawa {α : Type} [DecidableEq α] (a b : List α) : Bool := a.all (b.contains ·) && b.all (a.contains ·)

/-- المتوقَّعُ `taw` والمخرجُ `makh`، و`la` قيمةُ «لا حكم» في الحقل. -/
def qarin {α : Type} [DecidableEq α] (la : α) (f : Fia) (taw makh : List α) : Natija :=
  if sawa taw makh then .sawab
  else if makh = [la] then .naqsTaghtiya
  else if taw = [la] then .tajawuz
  else if f = .ghumud && makh.all (taw.contains ·) then .ikhtiyar
  else .khata

/-- النتيجةُ في حالة: ردُّ القارئ أوّلًا، ثمّ مقارنةُ حقل النوع. -/
def natijaHala (h : Hala) : Natija :=
  let t := h.nass.toList
  if !kullMaqrua t then .rafdQari
  else
    match h.naw with
    | .quwwa => qarin Quwwa.laHukm h.fia h.quwwa [quwwaJumla t]
    | .qayd => qarin QaydQ.laHukm h.fia h.qayd [qaydMuharrik t]

/-- النتائجُ على قائمة حالات: (الحالة، الفئة، النوع، النتيجة). -/
def natayij (halat : List Hala) : List (String × Fia × Naw × Natija) :=
  halat.map fun h => (h.ism, h.fia, h.naw, natijaHala h)

structure Ihsa where
  sawab : Nat
  naqsTaghtiya : Nat
  tajawuz : Nat
  ikhtiyar : Nat
  khata : Nat
  rafdQari : Nat
  deriving DecidableEq, Repr

def ihsa (l : List (String × Fia × Naw × Natija)) : Ihsa :=
  let c (n : Natija) := (l.filter (fun x => x.2.2.2 == n)).length
  ⟨c .sawab, c .naqsTaghtiya, c .tajawuz, c .ikhtiyar, c .khata, c .rafdQari⟩

/-- الإخفاقاتُ بأسمائها: (الحالة، النوع، النتيجة). -/
def akhta (l : List (String × Fia × Naw × Natija)) : List (String × Naw × Natija) :=
  (l.filter (fun x => x.2.2.2 != .sawab)).map (fun x => (x.1, x.2.2.1, x.2.2.2))

/-- أيختلف مخرجُ المحرّك في حقل نوع الحالة بين حالتين. -/
def farq (h g : Hala) : Bool :=
  match h.naw with
  | .quwwa => quwwaJumla h.nass.toList != quwwaJumla g.nass.toList
  | .qayd => qaydMuharrik h.nass.toList != qaydMuharrik g.nass.toList

/-- الأزواج: (الحالة، زوجُها، أيختلف مخرجُ المحرّك فيهما)، كلُّ زوجٍ مرّةً واحدة. -/
def azwaj (halat : List Hala) : List (String × String × Bool) :=
  halat.filterMap fun h =>
    match h.zawj with
    | some z =>
      if h.ism < z then
        match halat.find? (·.ism == z) with
        | some g => some (h.ism, z, farq h g)
        | none => none
      else none
    | none => none

/-- عددُ المتوقَّع في حقلٍ بقيمه: لكلّ قيمةٍ عددُ ما متوقَّعُه هي وحدها، ثمّ عددُ ما متوقَّعُه بديلان فأكثر. -/
def aadadQiyam {α : Type} [DecidableEq α] (qiyam : List α) (l : List (List α)) : List Nat :=
  qiyam.map (fun v => (l.filter (· = [v])).length) ++ [(l.filter (fun x => decide (2 ≤ x.length))).length]

/-- أعدادُ المجال بترتيبٍ ثابت (يحسبها اختبارُ القطعة من `cases.json` بالترتيب نفسه): الحالات، وحالاتُ النوعين؛ ثمّ متوقَّعُ `quwwa` بقيمه
    (إثبات، نفي، تعليق، إنشاء، لا حكم) ثمّ بديلان فأكثر؛ ثمّ متوقَّعُ `qayd` بقيمه (صفة، شرط، غاية، عدد، لا قيد، لا حكم) ثمّ قائمةٌ من اثنين فأكثر؛
    ثمّ ذواتُ الزوج؛ ثمّ الفئات: موجب، حدّ، خارج، عموم، غموض. -/
def majalAadad (halat : List Hala) : List Nat :=
  let hq := halat.filter (·.naw == .quwwa)
  let hd := halat.filter (·.naw == .qayd)
  [halat.length, hq.length, hd.length] ++
  aadadQiyam [Quwwa.ithbat, .nafy, .taliq, .insha, .laHukm] (hq.map (·.quwwa)) ++
  aadadQiyam [QaydQ.sinf .sifa, .sinf .shart, .sinf .ghaya, .sinf .adad, .laQayd, .laHukm] (hd.map (·.qayd)) ++
  [(halat.filter (·.zawj.isSome)).length] ++
  [Fia.mujib, .hadd, .kharij, .umum, .ghumud].map (fun f => (halat.filter (·.fia == f)).length)

/-- **المقارنة على الشاهد:** المجموعتان بلا ترتيب، وبعضُ البديلين في الغموض اختيارٌ وفي غيره خطأ، والامتناعُ نقصُ تغطية، والحكمُ حيث لا حكمَ
    تجاوز. -/
theorem qarin_shawahid :
    qarin Quwwa.laHukm .ghumud [.insha, .ithbat] [.ithbat, .insha] = .sawab ∧
    qarin Quwwa.laHukm .ghumud [.insha, .ithbat] [.ithbat] = .ikhtiyar ∧
    qarin Quwwa.laHukm .mujib [.insha, .ithbat] [.ithbat] = .khata ∧
    qarin Quwwa.laHukm .mujib [.nafy] [.laHukm] = .naqsTaghtiya ∧
    qarin QaydQ.laHukm .kharij [.laHukm] [.laQayd] = .tajawuz ∧
    qarin QaydQ.laHukm .mujib [.sinf .ghaya] [.laQayd] = .khata := by
  decide

end Dabit
end Nizam.Athar
