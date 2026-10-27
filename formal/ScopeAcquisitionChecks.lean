import Nabt.ScopeAcquisition

open Nabt.ScopeAcquisition

set_option maxRecDepth 100000
set_option maxHeartbeats 8000000

private def src (text : String) : Nabt.Foundation.Source := ⟨"check", "observed", text⟩

-- These are separate finite controls, not additional general language laws.
example : (acquire (src "قَالَ زَيْدٌ: «كَتَبَ»")).map Envelope.body = some "كَتَبَ" := by decide +kernel
example : (acquire (src "قَالَ عَمْرٌو: «كَتَبَ».")).map Envelope.speaker = some "عَمْرٌو" := by decide +kernel
example : (acquire (src "قَالَ زَيْدٌ: «كَتَبَ»")).map Envelope.startByte = some 27 := by decide +kernel
example : (acquire (src "لَيْسَ صَحِيحًا أَنِّي كَتَبْتُ")).map Envelope.kind = some .negated := by decide +kernel
example : (acquire (src "إِنْ قُلْتُ كَتَبَ فَلَا تَكْتُبْ")).map Envelope.kind = some .hypothetical := by decide +kernel
example : acquire (src "قَالَ زَيْدٌ: «»") = none := by decide +kernel
example : acquire (src "قَالَ زَيْدٌ: «كَتَبَ»..") = none := by decide +kernel
example : acquire (src "قَالِ زَيْدٌ: «كَتَبَ»") = none := by decide +kernel
example : acquire (src "قَالَ زَيْدٌ عَمْرٌو: «كَتَبَ»") = none := by decide +kernel
example : acquire (src "قَالَ زَيْدٌ: «قَالَ عَمْرٌو: «كَتَبَ»»") = none := by decide +kernel
example : acquire (src "إِنْ قُلْتُ كَتَبَ فَلَا تَكْتُبْ فَلَا تَكْتُبْ") = none := by decide +kernel
example : acquire (src "قَالَ زَيْدٌ: «كَِتَبَ»") = none := by decide +kernel
