import A116.Mizan
import A116.MizanData

/-!
# الجدولُ تحت النواة (ADR ٤٤)

`mizan.csv` يطبعه `lake exe a116-table mizan` — شيفرةُ Lean **المترجَمة** لا النواة (`MIZAN_TABLE_PRINTED_BY_COMPILED_LEAN`،
ADR ٤٢). وهنا يُسدّ الدَّين: الجدولُ نفسُه مولَّدٌ مصدرَ Lean (`A116.MizanData`، `lake exe a116-table mizan-lean`)، والنواةُ
تُعيد حسابَ كلِّ صفٍّ منه من تعريف الآلة (`decide +kernel`) فتساويه:

* `cellT_eq`: لكلّ خانةٍ من الـ116 حاملُها وحالتُها ورقمُ خانتها في الآلة؛
* `stateT_eq`: لكلّ حالٍ من الـ42 قبولُه وصلًا ووقفًا وصورتُه بعد الحدّ؛
* `waslT_eq`، `waqfT_eq`: الانتقالُ على المجال كلِّه (42 × 116) وصلًا ووقفًا.

فما يطبعه المترجِمُ خطأً تردّه النواة؛ ولا ثقةَ بالطابع بعد هذا. ويبقى بين `mizan.csv` و`MizanData` فحصٌ نصّيٌّ
(`tests/test_mizan.py`)، وبين الجدول والبوّابة المفسِّرُ (`MIZAN_INTERPRETER_UNPROVEN`).
-/

set_option autoImplicit false

namespace A116.MizanKernel

open A116 A116.Mizan A116.MizanData

theorem cellT_eq :
    cellT = A116.cells.map fun c => (Field112.carrierChar c.carrier, c.haraka, ki (HarfBridge.unproj c)) := by
  decide +kernel

theorem stateT_eq :
    stateT = Harf.Hal.all.map fun s => (Harf.qabilWasl s, Harf.qabilWaqf s, hi (Harf.hadd s)) := by
  decide +kernel

theorem waslT_eq :
    waslT = Harf.Hal.all.map fun s => Harf.Khana.all.map fun x => hi (Harf.wasl s x) := by
  decide +kernel

theorem waqfT_eq :
    waqfT = Harf.Hal.all.map fun s => Harf.Khana.all.map fun x => hi (Harf.waqf s x) := by
  decide +kernel

end A116.MizanKernel
