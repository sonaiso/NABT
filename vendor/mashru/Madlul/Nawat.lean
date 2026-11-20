/-
# النواة (core knowledge): صفوفُ أقوال المالك المرقَّمة التي يتوسّع منها التوليد

**الطلب.** المالك 2026-11-17 (07:16): «هذه المنهجية تحول مبرهنات تبني على core knowledge هي أساس توسع الادراك والتعلم الذاتي»، ثمّ (07:20):
«نفذ على أقوالي المرقَّمة مصدرًا للنواة». فالنواةُ ليست ملفَّ تدريب (المالك: «كلُّ حكمٍ مبرهنٌ أو مفحوص، لا مُتعلَّم») بل **صفوفٌ من
`tahaqquq/dawabit/nawat_tawlid/masdar.md`** بأرقام أسطرها: الأجناسُ الأربعة بخواصّها (س3–س6، وهي `Madlul.Tayin.fusul`)، والجذران
اللذان مثّل بهما المالك بشروط فاعلهما ومفعولهما وقيدهما الفيزيائيّ وموانعهما (س22، س23). ولا صفَّ من المعنى: صفٌّ جديدٌ يُزاد
بسطرٍ مرقَّمٍ من المالك (أو مرشَّحٍ ينتظر إمضاءَه، `Jisr.Tawlid.satrMurashshah`).

**المفاتيح** (تعييناتُ البنّاء س30، س31، تنتظر الإمضاء): لفظُ الشرط يُربط بخاصّةٍ من خواصّ الجنس (`Madlul.Tayin.Khawass`) أو لا يُربط فلا
يُحكم به؛ ولفظُ المانع يُربط بجنسٍ أو بخاصّةٍ «لا» أو لا يُربط فلا يمنع (م13، س9).
-/
import Madlul.Wiratha

namespace Madlul
namespace Nawat

open Tayin

/-- ألفاظُ الشروط بلفظ المالك (س21–س23). -/
inductive Shart
  | hayat            -- «الحياة»
  | aql              -- «العقل»
  | idrak            -- «الإدراك»
  | haraka           -- «حركة»
  | quwwaMuaththira  -- «قوة_مؤثرة»
  | maddiyya         -- «المادية»
  | tamasukJuzi      -- «التماسك_الجزئي»
  | qabiliyyaTasawwur -- «القابلية_للتصور»
  | salabaNisbiyya   -- «الصلابة_النسبية»
  | tahayyuz         -- «التحيز_المكاني_أو_الزماني»
  deriving DecidableEq, Repr

/-- ألفاظُ الموانع بلفظ المالك (س22، س23). -/
inductive Mani
  | suyula | ghaziyya | tajarrudManawi | jumudMutlaq | inadamAql
  deriving DecidableEq, Repr

/-- القيدُ الفيزيائيّ (س21–س22): «صلب». -/
inductive Qayd | sulb
  deriving DecidableEq, Repr

/-- صفُّ جذرٍ في النواة: حروفُه الثلاثة (س12)، وشروطُ فاعله ومفعوله، وقيدُه، وموانعُه، ورقمُ سطره في المصدر. -/
structure SaffJadhr where
  c1 : Char
  c2 : Char
  c3 : Char
  shurutFail : List Shart
  shurutMafool : List Shart
  qayd : Option Qayd
  mawani : List Mani
  satr : Nat
  deriving DecidableEq, Repr

/-- مفتاحُ الجذر «ك-س-ر». -/
def SaffJadhr.miftah (s : SaffJadhr) : String := String.ofList [s.c1, '-', s.c2, '-', s.c3]

/-- س22: (ك - س - ر). -/
def kasara : SaffJadhr :=
  { c1 := 'ك', c2 := 'س', c3 := 'ر', shurutFail := [.quwwaMuaththira, .haraka], shurutMafool := [.maddiyya, .tamasukJuzi],
    qayd := some .sulb, mawani := [.suyula, .ghaziyya, .tajarrudManawi], satr := 22 }

/-- س23: (ع - ل - م). -/
def alima : SaffJadhr :=
  { c1 := 'ع', c2 := 'ل', c3 := 'م', shurutFail := [.hayat, .aql, .idrak], shurutMafool := [.qabiliyyaTasawwur],
    qayd := none, mawani := [.jumudMutlaq, .inadamAql], satr := 23 }

/-- **النواة:** الجذران بسطريهما؛ والأجناسُ `Tayin.fusul` بأسطرها (`satrQism`). -/
def nawat : List SaffJadhr := [kasara, alima]

/-- سطرُ كلّ جنسٍ في المصدر (س3–س6). -/
def satrQism : Qism → Nat | .jamad => 3 | .nabat => 4 | .hayawan => 5 | .insan => 6

/-- البحثُ في النواة بالمفتاح. -/
def saff (k : String) : Option SaffJadhr := nawat.find? (·.miftah == k)

/-- **مفتاحُ الشرط** (س30): «الحياة» ⇐ الحياة؛ «العقل» و«الإدراك» ⇐ العقل؛ «حركة» ⇐ الانتقال (س7)؛ وما سواها بلا مفتاح. -/
def miftahShart : Shart → Option (Khawass → Qima)
  | .hayat => some hayat
  | .aql => some (·.aql)
  | .idrak => some (·.aql)
  | .haraka => some (·.intiqal)
  | _ => none

/-- فصلُ الشرط: الخواصُّ التي يطلبها الشرطُ «نعم» (لِتُورَّث بـ`Wiratha.warrith`). -/
def faslShart : Shart → Khawass
  | .hayat => { taghadhdhi := .naam, numuw := .naam, mawt := .naam }
  | .aql => { aql := .naam }
  | .idrak => { aql := .naam }
  | .haraka => { intiqal := .naam }
  | _ => {}

/-- **مفتاحُ المانع** (س31): «انعدام_العقل» ⇐ العقلُ «لا» في الجنس؛ «الجمود_المطلق» ⇐ الجنسُ الجماد؛ وما سواهما لا يمنع. -/
def maniMutahaqqiq (m : Mani) (q : Qism) : Bool :=
  match m with
  | .inadamAql => (fusul q).aql == .la
  | .jumudMutlaq => q == .jamad
  | _ => false

/-- الشرطُ متحقّقٌ في الجنس: له مفتاحٌ وخاصّتُه «نعم». -/
def shartMutahaqqiq (s : Shart) (q : Qism) : Bool :=
  match miftahShart s with
  | some f => f (fusul q) == .naam
  | none => false

/-- الشرطُ بلا مفتاحٍ لا يتحقّق في جنس (م13: لا يُحكم به). -/
theorem bila_miftah_la_yatahaqqaq (s : Shart) (q : Qism) (h : miftahShart s = none) : shartMutahaqqiq s q = false := by
  simp [shartMutahaqqiq, h]

/-- المانعُ بلا مفتاحٍ لا يمنع (س31): السيولة والغازيّة والتجرّد المعنويّ. -/
theorem mani_bila_miftah (q : Qism) :
    maniMutahaqqiq .suyula q = false ∧ maniMutahaqqiq .ghaziyya q = false ∧ maniMutahaqqiq .tajarrudManawi q = false := by
  simp [maniMutahaqqiq]

/-- «انعدام_العقل» يتحقّق في الحيوان وحدَه (س5، س8). -/
theorem inadamAql_hayawan : ∀ q : Qism, maniMutahaqqiq .inadamAql q = (q == .hayawan) := by intro q; cases q <;> decide

/-- «الجمود_المطلق» يتحقّق في الجماد وحدَه (س3). -/
theorem jumud_jamad : ∀ q : Qism, maniMutahaqqiq .jumudMutlaq q = (q == .jamad) := by intro q; cases q <;> decide

/-- الشرطُ المتحقّق لا يغيّر الجنسَ بالتوريث: خواصُّ الجنس بعد توريث فصلِ الشرط هي خواصُّه (`Wiratha.warrith`، فالشرطُ «نعم» فيه أصلًا). -/
theorem shart_mutahaqqiq_wiratha :
    ∀ s : Shart, ∀ q : Qism, shartMutahaqqiq s q = true → Wiratha.warrith (fusul q) (faslShart s) = fusul q := by
  intro s q; cases s <;> cases q <;> decide

/-- الحياةُ شرطٌ متحقّقٌ في النبات والحيوان والإنسان لا الجماد (س3–س6). -/
theorem hayat_fi_thalatha : ∀ q : Qism, shartMutahaqqiq .hayat q = (q != .jamad) := by intro q; cases q <;> decide

/-- العقلُ والإدراك شرطٌ متحقّقٌ في الإنسان وحدَه (س6، س8). -/
theorem aql_insan : ∀ q : Qism, shartMutahaqqiq .aql q = (q == .insan) ∧ shartMutahaqqiq .idrak q = (q == .insan) := by
  intro q; cases q <;> decide

/-- الحركةُ شرطٌ متحقّقٌ فيما ينتقل: الحيوان والإنسان (س5–س7). -/
theorem haraka_intiqal : ∀ q : Qism, shartMutahaqqiq .haraka q = ((fusul q).intiqal == .naam) := by intro q; cases q <;> decide

/-- النواةُ على المصدر: الجذران بسطريهما، ومفتاحاهما، ومن حروفٍ صحيحة (لا واو ولا ياء ولا همزة، وعينُه غيرُ لامه؛ س29). -/
theorem nawat_shahid :
    nawat.map (·.satr) = [22, 23] ∧ nawat.map (·.miftah) = ["ك-س-ر", "ع-ل-م"] ∧
    nawat.all (fun s => s.c2 != s.c3 && [s.c1, s.c2, s.c3].all (fun c => !['و', 'ي', 'ء', 'أ', 'إ', 'آ'].contains c)) = true := by
  decide +kernel

end Nawat
end Madlul
