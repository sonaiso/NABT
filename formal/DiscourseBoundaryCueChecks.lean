import Nabt.DiscourseBoundaryCueBridge

open Nabt.DiscourseBoundaryCueBridge
set_option maxRecDepth 100000
set_option maxHeartbeats 8000000

private def src (text : String) : Nabt.Foundation.Source := ⟨"check", "observed", text⟩

-- Independent finite surface controls. They do not certify body syntax/intent.
example : (acquire (src "لم أكتب؛ وأقصد كلاماً آخر")).map Envelope.cueText =
    some "أقصد كلاماً آخر" := by decide +kernel
example : (acquire (src "لَمْ أَكْتُبْ؛ وَأَقْصِدُ كَلَامًا آخَرَ.")).isSome = true := by decide +kernel
example : (acquire (src "لم أكتب؛ وَأَقْصِدُ كَلَامًا آخَرَ.")).isSome = true := by decide +kernel
example : (acquire (src "لَمْ أَكْتُبْ؛ وأقصد كلاماً آخر")).isSome = true := by decide +kernel
example : (readings (src "لم أكتب؛ وأقصد كلاماً آخر.")).length = 1 := by decide +kernel
example : (acquire (src "لم أكتب؛ وأقصد كلاماً آخر")).map Envelope.deniedText =
    some "أكتب" := by decide +kernel
example : acquire (src "لم أكتب؛ وأقصد ") = none := by decide +kernel
example : acquire (src "لم ؛ وأقصد كلاماً آخر") = none := by decide +kernel
example : acquire (src "لم أكتب؛ وَأقصد كلاماً آخر") = none := by decide +kernel
example : acquire (src "لم أكتب وأقصد كلاماً آخر") = none := by decide +kernel
example : acquire (src "لم أكتب؛ قال زيد وأقصد كلاماً آخر") = none := by decide +kernel
example : acquire (src "لم أكتب؛ وأقصد «كلاماً آخر»") = none := by decide +kernel
example : acquire (src "لم أكتب؛ وأقصد كلاماً آخر؛ وأقصد ثالثاً") = none := by decide +kernel
example : acquire (src "لم أكتب؛ وأقصد كَِلاماً آخر") = none := by decide +kernel
example : acquire (src "لم أكتب؛ وأقصد كلاماً آخر..") = none := by decide +kernel
example : acquire (src "لم أكتب؛  وأقصد كلاماً آخر") = none := by decide +kernel
