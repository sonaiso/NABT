/-
  Madlul/Tashfir.lean — تشفيرُ معجم الأجناس (Madlul/Tayin.lean) على آلة الطيّ والفكّ المعمَّمة نفسِها التي
  شُفِّر بها الدالّ وحدُه (Aql/Mawsua.lean: Tayy)، بتركيبها لا بموازاتها.

  السند: Aql/Mawsua.lean يصرّح بعموم Tayy («الطيّ المعتبر ... يتركّب ... ويمتدّ إلى السلاسل. ومنه طيّ الخلية
  [الدال وحده] ...» — «ومنه» أي مثالٌ واحدٌ من آلةٍ عامّة لا الآلةُ كلّها). وMadlul/Tayin.lean (`ramzQism`،
  س341) يرمز الجنسَ رقمًا أحاديّ الاتّجاه (ترميزٌ معلَن، يطابق عمود `haqiqa` في المودَع) بلا فكٍّ ولا مبرهنة
  استرجاع. طلب المالك 2026-10-17 توظيف الآلة الثنائيّة المعمَّمة نفسِها على حدود الجسر (المعجم، العوامل،
  الإسناد) بدل حلولٍ منفصلة لكلٍّ منها. هذا أوّل تطبيقٍ فعليٍّ، على حدّ المعجم (الجنس) وحده — مهمّةٌ واحدةٌ
  صغيرة؛ العوامل والإسناد وItar3 نفسُه مؤجَّلةٌ لمهامٍّ تالية.

  ما يُبرهن هنا:
  ١. `ramzQism` يُغلَق بفكٍّ (`tayyQism`) محمولًا على Fin 116 — نفس مجال خليّة الدالّ وحده — بمبرهنة استرجاعٍ
     على الجنس كلِّه (أربعة مُنشِئات، لا شاهدٌ واحد): «مبرهن» لا «مبرهن على الشاهد» (الدستور يفرّق بالمجال لا
     بالأداة: decide/cases على نوعٍ مبنًى للمثال وحده يُنزَّل، وهذا على Qism نفسِه — نوعُ المشروع الحقيقيّ،
     لا نوعًا بُني لهذا البرهان وحده).
  ٢. يُركَّب (Tayy.tarkib، مبرهنٌ هناك مرّةً) إلى قناة الدالّ وحده الثنائيّة نفسِها (Mawsua.tayyBits) — بلا
     مبرهنةٍ جديدة؛ ويمتدّ (Tayy.qaima) إلى معجمٍ (قائمة أجناس) لا جنسٍ واحد.
-/
import Madlul.Tayin
import Aql.Mawsua

namespace Madlul.Tashfir

open Mawsua
open Madlul.Tayin

/-- طيّ الجنس إلى خليّةٍ دون ١١٦: رمزُه رمزُ `ramzQism` بعينه، محمولًا على `Fin 116` ليُركَّب مباشرةً إلى
قناة الدالّ وحده الثنائيّة. مبرهنةُ الاسترجاع (`fakk_tawi`) على الجنس الأربعة كلِّه. -/
def tayyQism : Tayy Qism (Fin 116) where
  tawi q := ⟨ramzQism q, by cases q <;> decide⟩
  fakk m := match m.val with
    | 1 => some .jamad
    | 2 => some .nabat
    | 3 => some .hayawan
    | 4 => some .insan
    | _ => none
  fakk_tawi q := by cases q <;> decide

/-- **التركيب**: الجنسُ يُطوى ثنائيًّا على قناة `Mawsua.tayyBits` نفسِها — بلا قناةٍ موازية؛ الاسترجاع موروثٌ
من `Tayy.tarkib` (مبرهنٌ هناك). -/
def tayyQismBinary : Tayy Qism (List Bool) := tayyQism.tarkib tayyBits

/-- فهمُ الجنس مشفَّرٌ: كلّ جنسٍ يُطوى ثنائيًّا ويُفكّ إلى نفسه بعينه — غير مشروطٍ، لكلّ جنسٍ. -/
theorem qism_la_yudi (q : Qism) : tayyQismBinary.fakk (tayyQismBinary.tawi q) = some q :=
  tayyQismBinary.fakk_tawi q

/-- ويمتدّ إلى معجمٍ (قائمة أجناس) لا جنسٍ واحد، بالرفع المعمَّم `Tayy.qaima` — نظيرُ `Mawsua.tayySifrWahid`
بعينه، على طبقة المدلول وحده لا الدالّ وحده. -/
def tayyQismSifrWahid : Tayy (List Qism) (List (List Bool)) := tayyQismBinary.qaima

theorem qismSifrWahid_la_yudi (qs : List Qism) :
    tayyQismSifrWahid.fakk (tayyQismSifrWahid.tawi qs) = some qs :=
  tayyQismSifrWahid.fakk_tawi qs

end Madlul.Tashfir
