/-
  Jisr/NassItarDabit.lean — مقارنةُ ضابط «من النصّ إلى الإطار» (`tahaqquq/dawabit/nass/wasf.md`، §القياس) قبل الحالات: الحالةُ بنوعها،
  وحكمُ المحرّك عليها، والتصنيف. يُودَع مع الشفرة قبل أن يقرأ البنّاءُ الحالات، والحالاتُ تُولَّد بعده في `Jisr/NassItarDawabit.lean`.

  **الحقلان المسؤولان** (بنصّ المواصفة، §القياس؛ وما زاده البنّاء موسوم):
  * `hukm` في كلّ حالة: صواب، أو نقصُ تغطية («لا حكم» حيث المتوقَّع حكم)، أو قبولٌ خاطئ، أو ردٌّ خاطئ، أو تجاوز (حكمٌ حيث المتوقَّع «لا
    حكم»). وفي `غموض` بحكمين: «لا حكم» من المحرّك صواب (لم يختر)، وأحدُ البديلين «اختيارٌ بلا مرجّح».
  * `itar` حيث المتوقَّعُ «مقبول» وحكمُ المحرّك «مقبول»: الإطاراتُ المقبولة عند المحرّك (`maqbula`) هي المتوقَّعُ بعينه، وإلّا خطأُ إطار. وفي
    `غموض` بإطارين: الإطاران معًا صواب، وأحدُهما «اختيارٌ بلا مرجّح».
  * **زيادةُ البنّاء** (ليست في المواصفة): ما رفضه القارئ (`kalimat = none`) إخفاقٌ باسمه (`rafdQari`) في حقل الحكم، لا «لا حكم» يُعدّ صوابًا
    في `خارج` أو `غموض`؛ ولا حقلَ إطارٍ له. وفي `غموض` بحكمين حكمٌ ليس من البديلين ولا «لا حكم» خطأٌ باسمه (`Natija.khata`).
-/
import Jisr.NassItar

namespace Jisr
namespace NassItar
namespace Dabit

open Jisr.Utur Dal

inductive Fia
  | mujib | hadd | kharij | umum | ghumud
  deriving DecidableEq, Repr

/-- حالةُ الضابط بعد التوليد: كلماتُها خلايا كما يقرؤها القارئ (`none`: رفضها)، والمتوقَّع. -/
structure Hala where
  ism : String
  fia : Fia
  kalimat : Option (List Kalima)
  /-- الحكمُ المتوقَّع: واحد، أو بديلان في الغموض. -/
  hukm : List Hukm
  /-- الإطارُ المتوقَّع: واحد، أو إطاران في الغموض. -/
  itar : List (List Dawr)
  zawj : Option String
  deriving DecidableEq, Repr

inductive Natija
  | sawab | naqsTaghtiya | tajawuz | qabulKhati | raddKhati | ikhtiyar | khataItar | rafdQari | khata
  deriving DecidableEq, Repr

inductive Haql
  | hukm | itar
  deriving DecidableEq, Repr

/-- حكمُ المحرّك على الحالة. -/
def hukmMuharrik (h : Hala) : Hukm :=
  match h.kalimat with
  | some ws => hukmNass ws
  | none => .laHukm

/-- الإطاراتُ المقبولة عند المحرّك. -/
def itarMuharrik (h : Hala) : List (List Dawr) :=
  match h.kalimat with
  | some ws => maqbula ws
  | none => []

def qarinHukm (m : List Hukm) (b : Hukm) : Natija :=
  match m with
  | [x] =>
    if x = b then .sawab
    else match x, b with
      | .laHukm, _ => .tajawuz
      | _, .laHukm => .naqsTaghtiya
      | .murakhkhas, _ => .raddKhati
      | _, _ => .qabulKhati
  | _ => if b = .laHukm then .sawab else if m.contains b then .ikhtiyar else .khata

/-- الإطارُ مسؤولٌ حيث المتوقَّعُ «مقبول» وحده وحكمُ المحرّك «مقبول». -/
def masulItar (h : Hala) : Bool := h.hukm == [.murakhkhas] && hukmMuharrik h == .murakhkhas

def sawaMajmua (a b : List (List Dawr)) : Bool := a.all (b.contains ·) && b.all (a.contains ·)

def qarinItar (m b : List (List Dawr)) : Natija :=
  if sawaMajmua m b then .sawab
  else if 2 ≤ m.length && !b.isEmpty && b.all (m.contains ·) then .ikhtiyar
  else .khataItar

/-- النتائجُ على قائمة حالات: (الحالة، الفئة، الحقل، النتيجة). -/
def natayij (halat : List Hala) : List (String × Fia × Haql × Natija) :=
  halat.flatMap fun h =>
    if h.kalimat.isNone then [(h.ism, h.fia, Haql.hukm, Natija.rafdQari)]
    else (h.ism, h.fia, Haql.hukm, qarinHukm h.hukm (hukmMuharrik h)) ::
      (if masulItar h then [(h.ism, h.fia, Haql.itar, qarinItar h.itar (itarMuharrik h))] else [])

structure Ihsa where
  sawab : Nat
  naqsTaghtiya : Nat
  tajawuz : Nat
  qabulKhati : Nat
  raddKhati : Nat
  ikhtiyar : Nat
  khataItar : Nat
  rafdQari : Nat
  khata : Nat
  deriving DecidableEq, Repr

def ihsa (l : List (String × Fia × Haql × Natija)) : Ihsa :=
  let c (n : Natija) := (l.filter (fun x => x.2.2.2 == n)).length
  ⟨c .sawab, c .naqsTaghtiya, c .tajawuz, c .qabulKhati, c .raddKhati, c .ikhtiyar, c .khataItar, c .rafdQari, c .khata⟩

/-- الإخفاقاتُ بأسمائها: (الحالة، الحقل، النتيجة). -/
def akhta (l : List (String × Fia × Haql × Natija)) : List (String × Haql × Natija) :=
  (l.filter (fun x => x.2.2.2 != .sawab)).map (fun x => (x.1, x.2.2.1, x.2.2.2))

/-- ما رفضه القارئ. -/
def rafd (halat : List Hala) : List String := (halat.filter (·.kalimat.isNone)).map (·.ism)

/-- **الأزواج** (تبديلُ علامة إعرابٍ واحدة): لكلّ حالةٍ لها زوجٌ اسمُه أكبرُ من اسمها بترتيب النصوص (فيُعدّ الزوجُ مرّةً):
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
theorem qarin_hukm :
    [Hukm.murakhkhas, .mumtani, .laHukm].flatMap (fun m => [Hukm.murakhkhas, .mumtani, .laHukm].map (qarinHukm [m])) =
      [.sawab, .raddKhati, .naqsTaghtiya, .qabulKhati, .sawab, .naqsTaghtiya, .tajawuz, .tajawuz, .sawab] ∧
    qarinHukm [.murakhkhas, .mumtani] .laHukm = .sawab ∧ qarinHukm [.murakhkhas, .mumtani] .murakhkhas = .ikhtiyar ∧
    qarinHukm [.murakhkhas, .laHukm] .mumtani = .khata := by
  decide

/-- **الإطار:** المجموعةُ بلا ترتيب، والبعضُ في الغموض اختيار، والزائدُ خطأُ إطار. -/
theorem qarin_itar :
    qarinItar [[.fil, .fail]] [[.fil, .fail]] = .sawab ∧
    qarinItar [[.fil, .fail, .mudafIlayh], [.fil, .fail, .maful]] [[.fil, .fail, .maful], [.fil, .fail, .mudafIlayh]] = .sawab ∧
    qarinItar [[.fil, .fail, .mudafIlayh], [.fil, .fail, .maful]] [[.fil, .fail, .maful]] = .ikhtiyar ∧
    qarinItar [[.fil, .fail, .mudafIlayh]] [[.fil, .fail, .mudafIlayh], [.fil, .fail, .maful]] = .khataItar ∧
    qarinItar [[.fil, .fail]] [] = .khataItar := by
  decide

/-- **رفضُ القارئ إخفاقٌ باسمه** ولو كان المتوقَّعُ بديلين أو «لا حكم». -/
theorem rafd_ikhfaq :
    natayij [⟨"x", .ghumud, none, [.murakhkhas, .mumtani], [], none⟩, ⟨"y", .kharij, none, [.laHukm], [], none⟩] =
      [("x", .ghumud, .hukm, .rafdQari), ("y", .kharij, .hukm, .rafdQari)] := by
  decide

/-- **حقلُ الإطار تابعٌ لحكم المحرّك:** حالةٌ متوقَّعُها «مقبول» وحكمُ المحرّك فيها خطأ («ذَهَبَ الْوَلَدَ») لها حقلُ الحكم وحده. -/
theorem itar_tabi_hukm :
    natayij [⟨"z", .mujib, some [dhahaba, alWaladaK], [.murakhkhas], [[.fil, .fail]], none⟩] =
      [("z", .mujib, .hukm, .raddKhati)] := by
  decide +kernel

end Dabit
end NassItar
end Jisr
