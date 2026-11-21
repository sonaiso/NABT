/-
# مقارنةُ ضابط الضمير قبل الحالات

**ما في هذا الملفّ.** مقارنةُ الضابط (`tahaqquq/dawabit/damir/wasf.md`، §القياس): الحالةُ بنوعها، وجوابُ `Jisr.Damir.jawab` عليها، والتصنيف.
يُودَع مع الشفرة قبل أن يقرأ البنّاءُ الحالات، والحالاتُ تُولَّد بعده في `Jisr/DamirDawabit.lean`.

**الحقلان المسؤولان** (بنصّ المواصفة): `hukm` في كلّ حالة، و`daraja` حين يكون المتوقَّعُ «مقبول» وحكمُ المحرّك «مقبول».
- **الحكم:** صواب؛ أو نقصُ تغطية («لا حكم» حيث المتوقَّع حكم)؛ أو قبولٌ خاطئ («مقبول» حيث المتوقَّع «خطأ»)؛ أو ردٌّ خاطئ («خطأ» حيث المتوقَّع
  «مقبول»)؛ أو تجاوز (حكمٌ حيث المتوقَّع «لا حكم»). وفي `غموض` بحكمين: «لا حكم» من المحرّك صواب، وأحدُ البديلين «اختيارٌ بلا مرجّح».
- **الدرجة** (§القياس، البند الثاني): درجاتُ المحرّك (قائمة) والمتوقَّعة (درجةٌ أو بديلان) سواءٌ بلا ترتيب: صواب؛ وفي `غموض` بدرجتين: `بلا_درجة`
  من المحرّك صواب، ودرجةٌ واحدةٌ هي أحدُ البديلين اختيارٌ بلا مرجّح؛ و`بلا_درجة` من المحرّك حيث المتوقَّع درجةٌ نقصُ تغطية؛ ودرجةٌ حيث المتوقَّع
  `بلا_درجة` تجاوز؛ وما سوى ذلك خطأٌ في الدرجة (`khataDaraja`).
- **وكانت** (الشفرةُ المجمَّدة في `af3356c`، والتشغيلان الأوّلان): الثلاثُ الأخيرة كلُّها خطأً في الدرجة، خلافَ المواصفة؛ صُحّحت بعد مراجعة `murajii`،
  على مادّةٍ مكشوفة، وعدُّ التشغيل الأوّل بالمواصفة في `tahaqquq/dawabit/damir/mulhaq_1.md` §١.

**زيادةُ البنّاء** (ليست في المواصفة):
- في `غموض` بحكمين، حكمٌ ليس من البديلين ولا «لا حكم» خطأٌ باسمه (`Natija.khata`).
- إن لم يكن حكمُ المحرّك «مقبولًا» والمتوقَّعُ «مقبول»، فحقلُ الدرجة يُعدّ ونتيجتُه نتيجةُ الحكم نفسُها (نقصُ تغطيةٍ أو ردٌّ خاطئ)؛ والمواصفةُ لا
  تجعله مسؤولًا حينئذٍ، فعددُ الحقول المسؤولة هنا ثابتٌ بالحالات لا بجواب المحرّك.
- درجتان من المحرّك والمتوقَّعُ `بلا_درجة` تجاوز: يقرأ البنّاءُ «ودرجةٌ حيث المتوقَّع `بلا_درجة` تجاوز» (§القياس) على الدرجتين أيضًا. أمّا
  درجتان والمتوقَّعُ درجةٌ واحدةٌ غيرُ `بلا_درجة` (منهما أو من غيرهما) فخطأٌ في الدرجة، وهو «وغيرُ ذلك خطأُ درجة» في المواصفة، لا زيادة.
-/
import Jisr.Damir

namespace Jisr
namespace Damir
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
  | .laHukm => .naqsTaghtiya
  | .khata => .raddKhati
  | .maqbul =>
    if sawaa m j.daraja then .sawab
    else if 2 ≤ m.length && j.daraja == [.bila] then .sawab
    else if 2 ≤ m.length && j.daraja.length == 1 && j.daraja.all m.contains then .ikhtiyar
    else if j.daraja == [.bila] then .naqsTaghtiya
    else if m == [.bila] then .tajawuz
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

/-- **الدرجة:** سواءٌ بلا ترتيب؛ وفي البديلين «بلا درجة» صواب وواحدةٌ منهما اختيار؛ و«بلا درجة» لمتوقَّعٍ بدرجة نقصُ تغطية، ودرجةٌ أو درجتان
    لمتوقَّعٍ بلا درجة تجاوز؛ ودرجتان لمتوقَّعٍ واحدٍ غيرِ «بلا درجة»، أو درجةٌ غيرُ المتوقَّعة، خطأ؛ وحكمٌ غيرُ «مقبول» نتيجتُه. -/
theorem qarin_daraja :
    qarinDaraja [.rajih] ⟨.maqbul, [.rajih]⟩ = .sawab ∧
    qarinDaraja [.rajih, .sawa] ⟨.maqbul, [.sawa, .rajih]⟩ = .sawab ∧
    qarinDaraja [.rajih, .sawa] ⟨.maqbul, [.bila]⟩ = .sawab ∧
    qarinDaraja [.rajih, .marjuh] ⟨.maqbul, [.rajih]⟩ = .ikhtiyar ∧
    qarinDaraja [.rajih] ⟨.maqbul, [.bila]⟩ = .naqsTaghtiya ∧
    qarinDaraja [.bila] ⟨.maqbul, [.marjuh]⟩ = .tajawuz ∧
    qarinDaraja [.bila] ⟨.maqbul, [.rajih, .marjuh]⟩ = .tajawuz ∧
    qarinDaraja [.rajih] ⟨.maqbul, [.rajih, .marjuh]⟩ = .khataDaraja ∧
    qarinDaraja [.rajih] ⟨.maqbul, [.marjuh]⟩ = .khataDaraja ∧
    qarinDaraja [.rajih] ⟨.laHukm, [.bila]⟩ = .naqsTaghtiya ∧
    qarinDaraja [.rajih] ⟨.khata, [.bila]⟩ = .raddKhati := by
  decide

end Dabit
end Damir
end Jisr
