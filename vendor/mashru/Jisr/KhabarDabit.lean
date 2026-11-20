/-
# مقارنةُ ضابط الخبر قبل الحالات

**ما في هذا الملفّ.** مقارنةُ الضابط (`tahaqquq/dawabit/khabar/wasf.md`، §القياس): الحالةُ بنوعها، وجوابُ `Jisr.Khabar.jawab` عليها، والتصنيف.
يُودَع مع الشفرة قبل أن يقرأ البنّاءُ الحالات، والحالاتُ تُولَّد بعده في `Jisr/KhabarDawabit.lean`.

**الحقلان المسؤولان** (بنصّ المواصفة): `hukm` في كلّ حالة، و`daraja` حين يكون المتوقَّعُ «مقبول».
- **الحكم:** صواب؛ أو نقصُ تغطية («لا حكم» حيث المتوقَّع حكم)؛ أو قبولٌ خاطئ («مقبول» حيث المتوقَّع «خطأ»)؛ أو ردٌّ خاطئ («خطأ» حيث المتوقَّع
  «مقبول»)؛ أو تجاوز (حكمٌ حيث المتوقَّع «لا حكم»). وفي `غموض` بحكمين: «لا حكم» من المحرّك صواب، وأحدُ البديلين «اختيارٌ بلا مرجّح».
- **الدرجة:** درجاتُ المحرّك (قائمة) والمتوقَّعة (درجةٌ أو بديلان) سواءٌ بلا ترتيب: صواب؛ ودرجةٌ واحدةٌ من المحرّك هي أحدُ البديلين: اختيارٌ
  بلا مرجّح؛ وفي `غموض` بدرجتين «لا حكم» من المحرّك صواب (`wasf.md` §القياس: «وفي غموض ببديلين: لا_حكم من المحرّك … صواب»، والبديلان فيها حكمان
  أو درجتان)؛ وما سوى ذلك خطأٌ في الدرجة (`khataDaraja`).
- **وكانت** (الشفرةُ المجمَّدة في `4374052`، والتشغيلان الأوّلان): «لا حكم» في الغموض بدرجتين نقصَ تغطية، تضييقًا لم يُعلَن؛ صُحّحت بعد مراجعة
  `murajii`، على مادّةٍ مكشوفة، ولا أثرَ له في أعداد التشغيلين (المحرّكُ لم يُخرج «لا حكم» في حالة غموضٍ بدرجتين).

**زيادةُ البنّاء** (ليست في المواصفة):
- في `غموض` بحكمين، حكمٌ ليس من البديلين ولا «لا حكم» خطأٌ باسمه (`Natija.khata`).
- إن لم يكن حكمُ المحرّك «مقبولًا» والمتوقَّعُ «مقبول»، فنتيجةُ الدرجة نتيجةُ الحكم نفسُها (نقصُ تغطيةٍ أو ردٌّ خاطئ)، لا خطأٌ في الدرجة؛ إلّا
  «لا حكم» في الغموض بدرجتين فصوابٌ بنصّ المواصفة.
- درجتان من المحرّك والمتوقَّعُ درجةٌ واحدة (منهما أو من غيرهما) خطأٌ في الدرجة: المحرّكُ لم يحكم بما حكم به النطاق.
- الدرجةُ لا تُعدّ حقلًا مسؤولًا إلّا والمتوقَّعُ «مقبول» وحده (`h.hukm == [.maqbul]`)؛ وفي `غموض` بحكمين أحدُهما «مقبول» لا تُعدّ، ولو كُتبت للبديل
  المقبول درجة. والمواصفةُ («حين يكون المتوقَّعُ مقبول») تحتمل الوجهين، واختيارُ هذا الوجه للبنّاء.
-/
import Jisr.Khabar

namespace Jisr
namespace Khabar
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

/-- قائمتا درجاتٍ سواءٌ بلا ترتيب. -/
def sawaa (a b : List Daraja) : Bool := a.all b.contains && b.all a.contains

/-- مقارنةُ الدرجة، والمتوقَّعُ «مقبول»: المتوقَّعة (`m`) وجوابُ المحرّك (`j`). -/
def qarinDaraja (m : List Daraja) (j : Jawab) : Natija :=
  match j.hukm with
  | .laHukm => if 2 ≤ m.length then .sawab else .naqsTaghtiya
  | .khata => .raddKhati
  | .maqbul =>
    if sawaa m j.daraja then .sawab
    else if 2 ≤ m.length && j.daraja.length == 1 && j.daraja.all m.contains then .ikhtiyar
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

/-- **الدرجة:** سواءٌ بلا ترتيب؛ وواحدةٌ من بديلين اختيار؛ ودرجتان لمتوقَّعٍ واحد خطأ؛ وحكمٌ غيرُ «مقبول» نتيجتُه، إلّا «لا حكم» في الغموض بدرجتين
    فصواب. -/
theorem qarin_daraja :
    qarinDaraja [.qalil] ⟨.maqbul, [.qalil]⟩ = .sawab ∧
    qarinDaraja [.bitawil, .bila] ⟨.maqbul, [.bila, .bitawil]⟩ = .sawab ∧
    qarinDaraja [.qalil, .bila] ⟨.maqbul, [.qalil]⟩ = .ikhtiyar ∧
    qarinDaraja [.qalil] ⟨.maqbul, [.qalil, .bila]⟩ = .khataDaraja ∧
    qarinDaraja [.bila] ⟨.maqbul, [.bitawil]⟩ = .khataDaraja ∧
    qarinDaraja [.qalil] ⟨.laHukm, [.bila]⟩ = .naqsTaghtiya ∧
    qarinDaraja [.bitawil, .bila] ⟨.laHukm, [.bila]⟩ = .sawab ∧
    qarinDaraja [.qalil] ⟨.khata, [.bila]⟩ = .raddKhati := by
  decide

end Dabit
end Khabar
end Jisr
