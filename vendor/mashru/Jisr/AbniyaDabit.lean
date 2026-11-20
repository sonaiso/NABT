/-
# مقارنةُ ضابط أبنية اسمَي الفاعل والمفعول قبل الحالات

**ما في هذا الملفّ.** مقارنةُ الضابط (`tahaqquq/dawabit/abniya/wasf.md`، §القياس): الحالةُ بنوعها، وجوابُ `Jisr.Abniya.jawab` عليها، والتصنيف.
يُودَع مع الشفرة قبل أن يقرأ البنّاءُ الحالات، والحالاتُ تُولَّد بعده في `Jisr/AbniyaDawabit.lean`.

**الحقلان المسؤولان** (بنصّ المواصفة): `hukm` في كلّ حالة، و`daraja` حين يكون المتوقَّعُ «مقبول».
- **الحكم:** صواب؛ أو نقصُ تغطية («لا حكم» حيث المتوقَّع حكم)؛ أو قبولٌ خاطئ («مقبول» حيث المتوقَّع «خطأ»)؛ أو ردٌّ خاطئ («خطأ» حيث المتوقَّع
  «مقبول»)؛ أو تجاوز (حكمٌ حيث المتوقَّع «لا حكم»). وفي `غموض` بحكمين: «لا حكم» من المحرّك صواب، وأحدُ البديلين «اختيارٌ بلا مرجّح».
- **الدرجة:** درجةُ المحرّك (واحدة) والمتوقَّعة (درجةٌ أو بديلان): الواحدةُ هي هي صواب؛ ودرجةُ المحرّك أحدُ البديلين: اختيارٌ بلا مرجّح؛ وما
  سوى ذلك خطأٌ في الدرجة (`khataDaraja`).

**زيادةُ البنّاء** (ليست في المواصفة):
- في `غموض` بحكمين، حكمٌ ليس من البديلين ولا «لا حكم» خطأٌ باسمه (`Natija.khata`).
- إن لم يكن حكمُ المحرّك «مقبولًا» والمتوقَّعُ «مقبول»، فنتيجةُ الدرجة نتيجةُ الحكم نفسُها (نقصُ تغطيةٍ أو ردٌّ خاطئ)، لا خطأٌ في الدرجة.
- الدرجةُ لا تُعدّ حقلًا مسؤولًا إلّا والمتوقَّعُ «مقبول» وحده (`h.hukm == [.maqbul]`)؛ وفي `غموض` بحكمين أحدُهما «مقبول» لا تُعدّ، ولو كُتبت للبديل
  المقبول درجة (B49، B50). والمواصفةُ («حين يكون المتوقَّعُ مقبول») تحتمل الوجهين، واختيارُ هذا الوجه للبنّاء.
-/
import Jisr.Abniya

namespace Jisr
namespace Abniya
namespace Dabit

inductive Fia
  | mujib | hadd | kharij | umum | ghumud
  deriving DecidableEq, Repr

/-- حالةُ الضابط بعد التوليد: المدخل، والمتوقَّع (حكمٌ أو بديلان، ودرجةٌ أو بديلان)، والزوج. -/
structure Hala where
  ism : String
  fia : Fia
  dakhil : Dakhil
  hukm : List Hukm
  daraja : List Daraja
  zawj : Option String
  deriving DecidableEq, Repr

inductive Natija
  | sawab | naqsTaghtiya | tajawuz | qabulKhati | raddKhati | ikhtiyar | khata | khataDaraja
  deriving DecidableEq, Repr

/-- مقارنةُ الحكم: المتوقَّع (`m`) وحكمُ المحرّك (`b`). -/
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

/-- مقارنةُ الدرجة، والمتوقَّعُ «مقبول»: المتوقَّعة (`m`) وجوابُ المحرّك (`j`). -/
def qarinDaraja (m : List Daraja) (j : Jawab) : Natija :=
  match j.hukm with
  | .laHukm => .naqsTaghtiya
  | .khata => .raddKhati
  | .maqbul =>
    if m == [j.daraja] then .sawab
    else if 2 ≤ m.length && m.contains j.daraja then .ikhtiyar
    else .khataDaraja

/-- النتائجُ على قائمة حالات، حقلًا حقلًا: (الحالة، الفئة، النتيجة)؛ الحكمُ لكلّ حالة، والدرجةُ لما متوقَّعُه «مقبول». -/
def natayij (halat : List Hala) : List (String × Fia × Natija) :=
  halat.flatMap fun h =>
    let j := jawab h.dakhil
    [(h.ism, h.fia, qarinHukm h.hukm j.hukm)] ++
      (if h.hukm == [.maqbul] then [(h.ism ++ "/daraja", h.fia, qarinDaraja h.daraja j)] else [])

structure Ihsa where
  sawab : Nat
  naqsTaghtiya : Nat
  tajawuz : Nat
  qabulKhati : Nat
  raddKhati : Nat
  ikhtiyar : Nat
  khata : Nat
  khataDaraja : Nat
  deriving DecidableEq, Repr

def ihsa (l : List (String × Fia × Natija)) : Ihsa :=
  let c (n : Natija) := (l.filter (fun x => x.2.2 == n)).length
  ⟨c .sawab, c .naqsTaghtiya, c .tajawuz, c .qabulKhati, c .raddKhati, c .ikhtiyar, c .khata, c .khataDaraja⟩

/-- الإخفاقاتُ بأسمائها: (الحقل، النتيجة). -/
def akhta (l : List (String × Fia × Natija)) : List (String × Natija) :=
  (l.filter (fun x => x.2.2 != .sawab)).map (fun x => (x.1, x.2.2))

/-- **الأزواج** (مدخلان يختلفان في حقلٍ واحد): لكلّ حالةٍ لها زوجٌ اسمُه أكبرُ من اسمها بترتيب النصوص (فيُعدّ الزوجُ مرّةً):
    (هي، زوجُها، أيختلف جوابُ المحرّك فيهما؟). -/
def azwaj (halat : List Hala) : List (String × String × Bool) :=
  halat.filterMap fun h =>
    match h.zawj with
    | some z =>
      if h.ism < z then
        match halat.find? (·.ism == z) with
        | some g => some (h.ism, z, jawab h.dakhil != jawab g.dakhil)
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

/-- **الدرجة:** الواحدةُ هي هي صواب؛ وأحدُ البديلين اختيار؛ وغيرُها خطأ؛ وحكمٌ غيرُ «مقبول» نتيجتُه. -/
theorem qarin_daraja :
    qarinDaraja [.qalil] ⟨.maqbul, .qalil⟩ = .sawab ∧
    qarinDaraja [.qiyas, .qalil] ⟨.maqbul, .qalil⟩ = .ikhtiyar ∧
    qarinDaraja [.qiyas] ⟨.maqbul, .qalil⟩ = .khataDaraja ∧
    qarinDaraja [.qiyas, .awla] ⟨.maqbul, .naql⟩ = .khataDaraja ∧
    qarinDaraja [.qalil] ⟨.laHukm, .bila⟩ = .naqsTaghtiya ∧
    qarinDaraja [.qalil] ⟨.khata, .bila⟩ = .raddKhati := by
  decide

end Dabit
end Abniya
end Jisr
