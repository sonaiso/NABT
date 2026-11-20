/-
  Madlul/TashfirHawass.lean — جسرُ المعلومة المعمَّم (السابع): طيُّ وفكُّ بنى Madlul.Hawass (الحواسّ الخمس
  وتشارك الخبرة)، وHukm المحلّيّ، وMaratib.ShahidWaqi (حقل Khibra).

  السند: تفويض المالك 2026-10-17 22:55 («alaqat/hawass/awwaليyyat/makan/isnad … ابني واكتشف كيف نقرا/تبني
  من الرياضيات»)؛ makan وawwaliyyat وأداةُ النصّ العامّة (TashfirNas، القطع 5–7) بُنيت. قُرئ Madlul/Hawass.lean
  وAql/Maratib.lean كاملين فرشةً هذه الجلسةُ قبل التصميم.

  **المشكلة الجديدة.** هنا بنيتان تحملان حقلَي/ثلاثةَ حقول String معًا (Tasmiya: ism،bud؛ Khibra:
  jins،bud،ism، وداخلها ShahidWaqi.basma) — والأداتان المبنيّتان حتّى الآن (TashfirNas: حقلٌ واحد؛ mixEnc:
  حقلٌ حرٌّ وآخرُ محدودٌ *بنوعه*) لا تكفيان حقلين غيرَ محدودين معًا. المحاولةُ الأولى المرفوضة قبل أن تُكتب
  (توثيقًا لا بناءً): حدٌّ أعلى BOUND على قيمة تشفير أحد النصّين (نمط TashfirMadda/TashfirMirsat) — تنهار
  فعليًّا هنا: نصٌّ من حرفين عربيّين فقط يتجاوز 2^32 في ترميز listEnc (كلُّ حرفٍ حتّى charBound، فالقيمة
  تكبر بتصاعدٍ أُسّيّ مع الطول)؛ أيُّ BOUND معقولٍ هشٌّ أمام نصٍّ أطول بقليل من شواهد اليوم — وهذا عينُ ما
  تحذر منه المادّة الثالثة من الدستور (لا يُبنى حدٌّ يوافق شواهد اليوم وحدها).

  **الحلّ: الفصلُ بقيمةٍ محجوزة، لا بحدٍّ مختار.** أُدمج رموزَ الحروف (الطبقة الدنيا؛ كلُّها دائمًا دون
  charBound بتعريف Char نفسِه، لا بحدٍّ أختاره) لكلّ النصوص في قائمةٍ واحدةٍ متّصلة، مفصولةً برمزٍ محجوزٍ
  هو charBound نفسُه (أكبرُ من أيّ رمز حرفٍ حقيقيّ حتمًا بمبرهنة `charEnc_lt` — لا تخمين)، وأرمّز القائمةَ
  كلَّها بـ`listEnc` على القاعدة charBound+1. الفكُّ يفصل عند أوّل وقوعٍ للرمز المحجوز (`splitAtSep`،
  أداةٌ جديدةٌ عامّةٌ هنا)، وشرطُ مبرهنتها («الرمزُ المحجوزُ ليس بين رموز النصّ الأوّل») لازمٌ دائمًا من
  `charEnc_lt` نفسِها — **لا شرطًا أختاره أنا**. فالطيُّ على Bud وTasmiya وجزءِ Khibra **غيرُ مشروطٍ بتاتًا**
  (كـKhawass/TashfirNas/TashfirAwwaliyyat لا كـMadda/Mirsat/Izaha3): أفضل من كلّ تصميمٍ بديلٍ على mixEnc
  وحدها، ولا يحتاج Subtype ولا `Classical.propDecidable` في أيّ من هذه البنى.

  **الاستثناء الوحيد: `ShahidWaqi.mawdi`.** حقلٌ Nat خامٌ (فهرسُ شاهدٍ في قائمة أمثلة) لا بنيةُ حروفٍ، فلا
  يدخل الفصلَ بالضمان النوعيّ نفسِه (لا يحمل Char يُضمَن دون charBound بتعريف نوعه). أُدرجه رقمًا خامًا في
  ذَيل القائمة المتّصلة، فيحتاج شرطًا وحيدًا خفيفًا (`mawdi < charBound+1`) — صادقًا على كلّ شاهدٍ بُني في
  الملفّ (أقصى قيمةٍ فعليّة: 5)، لا على نوع Nat كلِّه. لم أُغلِّفه بـSahih/Subtype/Classical.propDecidable
  (نمط Madda/Mirsat): شرطٌ واحدٌ خفيفٌ صدقُه مضمونٌ عمليًّا (فهرسٌ صغير) أصدقُ معروضًا مبرهنةً شرطيّةً مباشرةً
  من تغليفٍ يحمل مسلّمةً زائدةً لصورةٍ شكليّة. **فرصةٌ محتملةٌ لم تُستثمر (ذكرًا لا بناءً):** تشفيرُ mawdi
  نفسِه رقائمَ (digits) على نمط النصّ يزيل هذا الشرطَ أيضًا — لم أبنِه توفيرًا للوقت أمام القطع الباقية
  (Shabaka، Isnad)، ويُترك فرصةً صريحةً لا نقصًا صامتًا.

  البنى المطويّة: أربعةُ تعداداتٍ بلا حمولة (Hassa 5، Hawass.Hukm 3، Shidda 3، Thubut 2) ترميزًا مباشرًا
  كـZaman5؛ Bud (ism:String + hawass:List Hassa)، Tasmiya (ism،bud:String)، Maratib.ShahidWaqi
  (basma:String + mawdi:Nat)، Khibra (shahid:ShahidWaqi + hassa:Hassa + jins،bud،ism:String) — كلُّها
  بالفصل؛ غيرُ مشروطةٍ إلّا بشرط mawdi الخفيف حيث يَرِد (ShahidWaqi وKhibra عبره).

  **ملاحظةٌ فنّيّة:** كلُّ تجميعاتِ `++`/`::` أدناه مُقوَّسةٌ تصريحًا (`l1 ++ (sep :: l2)`) لا اعتمادًا على
  أسبقيّة المحلّلِ، لإزالة أيّ التباسٍ في تجميع المحلّل وضمان مطابقة شكل `splitAtSep_join` حرفيًّا.

  مؤجَّلٌ: alaqat (Shabaka، لم تُقرأ بنيتُها التفصيليّةُ بعدُ هذه الجلسةَ)، Isnad (تكراريّةٌ حقًّا)، جسورُ
  العوامل/Itar3، وجدولُ اللزوم من مقاييس/لسان.
-/
import Aql.Mawsua
import Madlul.TashfirNas
import Madlul.TashfirKhawass
import Madlul.Hawass
import Aql.Maratib

set_option autoImplicit false

namespace Madlul.TashfirHawass

open Mawsua Madlul.TashfirNas Madlul.TashfirKhawass Madlul.Hawass

/-! ## ٠. أداةٌ جديدةٌ: الفصلُ عند أوّل وقوعٍ لقيمةٍ محجوزة -/

/-- فصلُ قائمةٍ عند أوّل وقوعٍ للقيمة `sep`: ما قبلَه (بلا الفاصل) وما بعدَه. كُلّيّة: لا فاصل ⇒ القائمةُ كلُّها
«قبل» والذَّيلُ خالٍ. -/
def splitAtSep (sep : Nat) : List Nat → List Nat × List Nat
  | [] => ([], [])
  | x :: xs =>
    if x = sep then ([], xs)
    else
      let p := splitAtSep sep xs
      (x :: p.1, p.2)

/-- **الفصلُ يعيد الطرفين**: شرطٌ على القائمة المبنيّة («الفاصلُ ليس في الأوّل») لا على نوعها — ويصدق دائمًا
حين `l1` رموزَ حروفٍ و`sep = charBound` (بمبرهنة `charEnc_lt` الآتية، لا بالتخمين). -/
theorem splitAtSep_join (sep : Nat) (l1 l2 : List Nat) (h : sep ∉ l1) :
    splitAtSep sep (l1 ++ (sep :: l2)) = (l1, l2) := by
  induction l1 with
  | nil => simp [splitAtSep]
  | cons x xs ih =>
    simp only [List.mem_cons, not_or] at h
    simp only [List.cons_append, splitAtSep]
    rw [if_neg (Ne.symm h.1), ih h.2]

/-! ## ١. التعدادات الأربعة بلا حمولة — ترميزٌ مباشر كـZaman5، بلا mixEnc -/

def hassaEnc : Hassa → Nat
  | .basar => 0 | .sam => 1 | .dhawq => 2 | .lams => 3 | .shamm => 4
def hassaDec : Nat → Hassa
  | 0 => .basar | 1 => .sam | 2 => .dhawq | 3 => .lams | _ => .shamm
theorem hassa_dec_enc (h : Hassa) : hassaDec (hassaEnc h) = h := by cases h <;> rfl
theorem hassaEnc_lt (h : Hassa) : hassaEnc h < 5 := by cases h <;> decide

def tayyHassa : Tayy Hassa Nat where
  tawi := hassaEnc
  fakk := fun n => some (hassaDec n)
  fakk_tawi := fun h => by rw [hassa_dec_enc]
theorem tayyHassa_la_yudi (h : Hassa) : tayyHassa.fakk (tayyHassa.tawi h) = some h :=
  tayyHassa.fakk_tawi h

def hukmEnc : Hukm → Nat
  | .mafhum => 0 | .maaluma => 1 | .laHukm => 2
def hukmDec : Nat → Hukm
  | 0 => .mafhum | 1 => .maaluma | _ => .laHukm
theorem hukm_dec_enc (h : Hukm) : hukmDec (hukmEnc h) = h := by cases h <;> rfl
theorem hukmEnc_lt (h : Hukm) : hukmEnc h < 3 := by cases h <;> decide

def tayyHukm : Tayy Hukm Nat where
  tawi := hukmEnc
  fakk := fun n => some (hukmDec n)
  fakk_tawi := fun h => by rw [hukm_dec_enc]
theorem tayyHukm_la_yudi (h : Hukm) : tayyHukm.fakk (tayyHukm.tawi h) = some h :=
  tayyHukm.fakk_tawi h

def shiddaEnc : Shidda → Nat
  | .khafi => 0 | .mutadil => 1 | .shadid => 2
def shiddaDec : Nat → Shidda
  | 0 => .khafi | 1 => .mutadil | _ => .shadid
theorem shidda_dec_enc (s : Shidda) : shiddaDec (shiddaEnc s) = s := by cases s <;> rfl
theorem shiddaEnc_lt (s : Shidda) : shiddaEnc s < 3 := by cases s <;> decide

def tayyShidda : Tayy Shidda Nat where
  tawi := shiddaEnc
  fakk := fun n => some (shiddaDec n)
  fakk_tawi := fun s => by rw [shidda_dec_enc]
theorem tayyShidda_la_yudi (s : Shidda) : tayyShidda.fakk (tayyShidda.tawi s) = some s :=
  tayyShidda.fakk_tawi s

def thubutEnc : Thubut → Nat
  | .sifaMushabbaha => 0 | .hal => 1
def thubutDec : Nat → Thubut
  | 0 => .sifaMushabbaha | _ => .hal
theorem thubut_dec_enc (t : Thubut) : thubutDec (thubutEnc t) = t := by cases t <;> rfl
theorem thubutEnc_lt (t : Thubut) : thubutEnc t < 2 := by cases t <;> decide

def tayyThubut : Tayy Thubut Nat where
  tawi := thubutEnc
  fakk := fun n => some (thubutDec n)
  fakk_tawi := fun t => by rw [thubut_dec_enc]
theorem tayyThubut_la_yudi (t : Thubut) : tayyThubut.fakk (tayyThubut.tawi t) = some t :=
  tayyThubut.fakk_tawi t

/-! ## ٢. مقدّماتٌ مشتركة: عضويّة رموز النصّ ضمن القاعدة، وغيابُ الفاصل عنها -/

/-- `charBound = 2^32 ≥ 5`: حقيقةٌ عدديّةٌ على القيمة المختارة نفسِها (لا على نوعها)، لازمةٌ ليعرف `omega` أنّ
رموزَ التعدادات الصغيرة (Hassa دون 5) تدخل تحت القاعدة charBound+1 — `omega` لا يحسب 2^32 من نفسه (قيمةٌ
مُعرَّفةٌ لا رقمٌ حرفيّ في الهدف)، فتُحسب هنا مرّةً بـ`decide` ثمّ تُستعمل حيثما لزم. -/
theorem charBound_ge5 : 5 ≤ charBound := by unfold charBound; decide

theorem charBound_notin_charCodes (s : String) : charBound ∉ s.toList.map charEnc := by
  intro hcon
  obtain ⟨c, -, hc⟩ := List.mem_map.1 hcon
  have := charEnc_lt c
  omega

theorem charCodes_lt (s : String) : ∀ x ∈ s.toList.map charEnc, x < charBound + 1 := by
  intro x hx
  obtain ⟨c, -, rfl⟩ := List.mem_map.1 hx
  exact Nat.lt_succ_of_lt (charEnc_lt c)

/-- فكّ قائمة رموز حروفٍ ثمّ لفّها نصًّا يعيد النصّ الأصل (تركيبُ `charList_dec_enc`/`String.ofList_toList`،
التركيبُ نفسُه في `string_dec_enc`، مفرَّقًا هنا ليُستعمل بعد الفصل). -/
theorem charCodes_dec_enc (s : String) :
    String.ofList ((s.toList.map charEnc).map charDec) = s := by
  rw [charList_dec_enc]; exact String.ofList_toList

/-! ## ٣. Bud (ism:String + hawass:List Hassa) — بالفصل، غيرُ مشروط -/

def budEnc (b : Bud) : Nat :=
  listEnc (charBound + 1) ((b.ism.toList.map charEnc) ++ (charBound :: (b.hawass.map hassaEnc)))

def budDec (n : Nat) : Bud :=
  let combined := listDec (charBound + 1) n
  let p := splitAtSep charBound combined
  { ism := String.ofList (p.1.map charDec), hawass := p.2.map hassaDec }

theorem bud_dec_enc (b : Bud) : budDec (budEnc b) = b := by
  have hmem : ∀ x ∈ (b.ism.toList.map charEnc) ++ (charBound :: (b.hawass.map hassaEnc)), x < charBound + 1 := by
    intro x hx
    rcases List.mem_append.1 hx with h | h
    · exact charCodes_lt b.ism x h
    · rcases List.mem_cons.1 h with h | h
      · omega
      · obtain ⟨hh, -, rfl⟩ := List.mem_map.1 h
        have := hassaEnc_lt hh
        have := charBound_ge5
        omega
  show budDec (listEnc (charBound + 1) ((b.ism.toList.map charEnc) ++ (charBound :: (b.hawass.map hassaEnc)))) = b
  unfold budDec
  simp only
  rw [list_dec_enc (charBound + 1) _ hmem, splitAtSep_join charBound _ _ (charBound_notin_charCodes b.ism)]
  have h1 : String.ofList ((b.ism.toList.map charEnc).map charDec) = b.ism := charCodes_dec_enc b.ism
  have h2 : (b.hawass.map hassaEnc).map hassaDec = b.hawass := by
    induction b.hawass with
    | nil => rfl
    | cons h hs ih => simp [hassa_dec_enc, ih]
  simp only [h1, h2]

/-! ## ٤. Tasmiya (ism،bud:String) — بالفصل، غيرُ مشروط -/

def tasmiyaEnc (t : Tasmiya) : Nat :=
  listEnc (charBound + 1) ((t.ism.toList.map charEnc) ++ (charBound :: (t.bud.toList.map charEnc)))

def tasmiyaDec (n : Nat) : Tasmiya :=
  let combined := listDec (charBound + 1) n
  let p := splitAtSep charBound combined
  { ism := String.ofList (p.1.map charDec), bud := String.ofList (p.2.map charDec) }

theorem tasmiya_dec_enc (t : Tasmiya) : tasmiyaDec (tasmiyaEnc t) = t := by
  have hmem : ∀ x ∈ (t.ism.toList.map charEnc) ++ (charBound :: (t.bud.toList.map charEnc)), x < charBound + 1 := by
    intro x hx
    rcases List.mem_append.1 hx with h | h
    · exact charCodes_lt t.ism x h
    · rcases List.mem_cons.1 h with h | h
      · omega
      · exact charCodes_lt t.bud x h
  show tasmiyaDec (listEnc (charBound + 1) ((t.ism.toList.map charEnc) ++ (charBound :: (t.bud.toList.map charEnc)))) = t
  unfold tasmiyaDec
  simp only
  rw [list_dec_enc (charBound + 1) _ hmem, splitAtSep_join charBound _ _ (charBound_notin_charCodes t.ism)]
  simp only [charCodes_dec_enc]

def tayyTasmiya : Tayy Tasmiya Nat where
  tawi := tasmiyaEnc
  fakk := fun n => some (tasmiyaDec n)
  fakk_tawi := fun t => by rw [tasmiya_dec_enc]
theorem tayyTasmiya_la_yudi (t : Tasmiya) : tayyTasmiya.fakk (tayyTasmiya.tawi t) = some t :=
  tayyTasmiya.fakk_tawi t

/-! ## ٥. Maratib.ShahidWaqi (basma:String + mawdi:Nat) — بالفصل + شرطٌ خفيفٌ وحيد على mawdi -/

/-- الشرطُ الوحيدُ في هذه القطعة كلِّها: فهرسُ الشاهد دون charBound+1 (صادقٌ على كلّ شاهدٍ حقيقيّ: فهرسٌ صغير
في قائمة أمثلة، لا على Nat كلِّه). -/
def shahidSahih (s : Maratib.ShahidWaqi) : Prop := s.mawdi < charBound + 1

def shahidEnc (s : Maratib.ShahidWaqi) : Nat :=
  listEnc (charBound + 1) ((s.basma.toList.map charEnc) ++ (charBound :: [s.mawdi]))

def shahidDec (n : Nat) : Maratib.ShahidWaqi :=
  let combined := listDec (charBound + 1) n
  let p := splitAtSep charBound combined
  { basma := String.ofList (p.1.map charDec), mawdi := p.2.headD 0 }

theorem shahid_dec_enc (s : Maratib.ShahidWaqi) (h : shahidSahih s) : shahidDec (shahidEnc s) = s := by
  have hmem : ∀ x ∈ (s.basma.toList.map charEnc) ++ (charBound :: [s.mawdi]), x < charBound + 1 := by
    intro x hx
    rcases List.mem_append.1 hx with h' | h'
    · exact charCodes_lt s.basma x h'
    · rcases List.mem_cons.1 h' with h' | h'
      · omega
      · simp only [List.mem_singleton] at h'
        rw [h']
        exact h
  show shahidDec (listEnc (charBound + 1) ((s.basma.toList.map charEnc) ++ (charBound :: [s.mawdi]))) = s
  unfold shahidDec
  simp only
  rw [list_dec_enc (charBound + 1) _ hmem, splitAtSep_join charBound _ _ (charBound_notin_charCodes s.basma)]
  simp only [charCodes_dec_enc]
  rfl

/-! ## ٦. Khibra (shahid:ShahidWaqi + hassa:Hassa + jins،bud،ism:String) — بالفصل (أربعُ فتراتٍ) +
     نفسُ شرط mawdi -/

def khibraSahih (k : Khibra) : Prop := shahidSahih k.shahid

def khibraEnc (k : Khibra) : Nat :=
  listEnc (charBound + 1)
    ((k.shahid.basma.toList.map charEnc) ++ (charBound ::
      ((k.jins.toList.map charEnc) ++ (charBound ::
        ((k.bud.toList.map charEnc) ++ (charBound ::
          ((k.ism.toList.map charEnc) ++ (charBound :: [hassaEnc k.hassa, k.shahid.mawdi]))))))))

def khibraDec (n : Nat) : Khibra :=
  let combined := listDec (charBound + 1) n
  let p1 := splitAtSep charBound combined
  let p2 := splitAtSep charBound p1.2
  let p3 := splitAtSep charBound p2.2
  let p4 := splitAtSep charBound p3.2
  { shahid := { basma := String.ofList (p1.1.map charDec), mawdi := p4.2.getD 1 0 }
    hassa := hassaDec (p4.2.getD 0 0)
    jins := String.ofList (p2.1.map charDec)
    bud := String.ofList (p3.1.map charDec)
    ism := String.ofList (p4.1.map charDec) }

theorem khibra_dec_enc (k : Khibra) (h : khibraSahih k) : khibraDec (khibraEnc k) = k := by
  have hm : k.shahid.mawdi < charBound + 1 := h
  have hh := hassaEnc_lt k.hassa
  have hcb5 := charBound_ge5
  have hmem : ∀ x ∈ (k.shahid.basma.toList.map charEnc) ++ (charBound ::
      ((k.jins.toList.map charEnc) ++ (charBound ::
        ((k.bud.toList.map charEnc) ++ (charBound ::
          ((k.ism.toList.map charEnc) ++ (charBound :: [hassaEnc k.hassa, k.shahid.mawdi]))))))),
      x < charBound + 1 := by
    intro x hx
    rcases List.mem_append.1 hx with h1 | h1
    · exact charCodes_lt k.shahid.basma x h1
    rcases List.mem_cons.1 h1 with h1 | h1
    · omega
    rcases List.mem_append.1 h1 with h1 | h1
    · exact charCodes_lt k.jins x h1
    rcases List.mem_cons.1 h1 with h1 | h1
    · omega
    rcases List.mem_append.1 h1 with h1 | h1
    · exact charCodes_lt k.bud x h1
    rcases List.mem_cons.1 h1 with h1 | h1
    · omega
    rcases List.mem_append.1 h1 with h1 | h1
    · exact charCodes_lt k.ism x h1
    rcases List.mem_cons.1 h1 with h1 | h1
    · omega
    rcases List.mem_cons.1 h1 with h1 | h1
    · omega
    · rw [List.mem_singleton] at h1; omega
  show khibraDec
      (listEnc (charBound + 1) ((k.shahid.basma.toList.map charEnc) ++ (charBound ::
        ((k.jins.toList.map charEnc) ++ (charBound ::
          ((k.bud.toList.map charEnc) ++ (charBound ::
            ((k.ism.toList.map charEnc) ++ (charBound :: [hassaEnc k.hassa, k.shahid.mawdi])))))))))
      = k
  unfold khibraDec
  simp only
  rw [list_dec_enc (charBound + 1) _ hmem]
  rw [splitAtSep_join charBound (k.shahid.basma.toList.map charEnc) _ (charBound_notin_charCodes k.shahid.basma)]
  simp only
  rw [splitAtSep_join charBound (k.jins.toList.map charEnc) _ (charBound_notin_charCodes k.jins)]
  simp only
  rw [splitAtSep_join charBound (k.bud.toList.map charEnc) _ (charBound_notin_charCodes k.bud)]
  simp only
  rw [splitAtSep_join charBound (k.ism.toList.map charEnc) _ (charBound_notin_charCodes k.ism)]
  simp only [charCodes_dec_enc]
  have e1 : ([hassaEnc k.hassa, k.shahid.mawdi] : List Nat).getD 1 0 = k.shahid.mawdi := rfl
  have e2 : ([hassaEnc k.hassa, k.shahid.mawdi] : List Nat).getD 0 0 = hassaEnc k.hassa := rfl
  rw [e1, e2, hassa_dec_enc]

/- **لا Tayy/Subtype هنا عمدًا** (خلافًا لـTashfirMadda/TashfirMirsat): الشرطُ الوحيدُ (`khibraSahih`، أي
`shahidSahih k.shahid`) خفيفٌ وصدقُه مضمونٌ عمليًّا (فهرسُ شاهدٍ صغير)، فمبرهنةٌ شرطيّةٌ مباشرةٌ (`khibra_dec_enc`
أعلاه) أصدقُ من تغليفٍ بـSubtype/Classical.propDecidable لصورةٍ شكليّة لا تضيف شيئًا. -/

/-! ## ٧. على الشاهد: جداول Madlul.Hawass المبنيّة نفسُها (لا شاهدٌ جديدٌ) -/

/-- أبعادُ `abad` الخمسةُ (المبنيّة في Hawass.lean بحواسّها) تطوى وتُفكّ بعينها. -/
theorem abad_tudi : abad.map (fun b => budDec (budEnc b)) = abad := by
  simp [bud_dec_enc]

/-- أسماءُ `mujam` الثمانيةُ (الوضعُ على أبعاده) تطوى وتُفكّ بعينها. -/
theorem mujam_tudi : mujam.map (fun t => tasmiyaDec (tasmiyaEnc t)) = mujam := by
  simp [tasmiya_dec_enc]

/-- شاهدُ قول المالك بفهارسه الخمسة (`qawlMalik 1`‥`qawlMalik 5`) صادقٌ شرطَ `shahidSahih` ويطوى ويُفكّ. -/
theorem qawlMalik_tudi (i : Nat) (hi : i < charBound + 1) : shahidDec (shahidEnc (qawlMalik i)) = qawlMalik i :=
  shahid_dec_enc (qawlMalik i) hi

theorem qawlMalik_shawahid :
    shahidDec (shahidEnc (qawlMalik 1)) = qawlMalik 1 ∧ shahidDec (shahidEnc (qawlMalik 2)) = qawlMalik 2 ∧
    shahidDec (shahidEnc (qawlMalik 3)) = qawlMalik 3 ∧ shahidDec (shahidEnc (qawlMalik 4)) = qawlMalik 4 ∧
    shahidDec (shahidEnc (qawlMalik 5)) = qawlMalik 5 :=
  ⟨qawlMalik_tudi 1 (by decide), qawlMalik_tudi 2 (by decide), qawlMalik_tudi 3 (by decide),
   qawlMalik_tudi 4 (by decide), qawlMalik_tudi 5 (by decide)⟩

/-- خبراتُ `khibrat` الخمسُ بعينها (مثالُ المالك؛ شاهدُ كلٍّ منها `qawlMalik i` صادقُ شرط `khibraSahih`) تُطوى
وتُفكّ. -/
theorem khibrat_tudi :
    khibraDec (khibraEnc ⟨qawlMalik 1, .lams, "ثلج", "حرارة", "بارد"⟩) =
        (⟨qawlMalik 1, .lams, "ثلج", "حرارة", "بارد"⟩ : Khibra) ∧
    khibraDec (khibraEnc ⟨qawlMalik 2, .lams, "حجر", "صلابة", "صلب"⟩) =
        (⟨qawlMalik 2, .lams, "حجر", "صلابة", "صلب"⟩ : Khibra) ∧
    khibraDec (khibraEnc ⟨qawlMalik 3, .lams, "ماء", "قوام", "مائع"⟩) =
        (⟨qawlMalik 3, .lams, "ماء", "قوام", "مائع"⟩ : Khibra) ∧
    khibraDec (khibraEnc ⟨qawlMalik 4, .lams, "الحارّ", "حرارة", "ساخن"⟩) =
        (⟨qawlMalik 4, .lams, "الحارّ", "حرارة", "ساخن"⟩ : Khibra) ∧
    khibraDec (khibraEnc ⟨qawlMalik 5, .sam, "صوت عالٍ", "شدّة الصوت", "صراخ"⟩) =
        (⟨qawlMalik 5, .sam, "صوت عالٍ", "شدّة الصوت", "صراخ"⟩ : Khibra) :=
  ⟨khibra_dec_enc _ (by unfold khibraSahih shahidSahih; decide),
   khibra_dec_enc _ (by unfold khibraSahih shahidSahih; decide),
   khibra_dec_enc _ (by unfold khibraSahih shahidSahih; decide),
   khibra_dec_enc _ (by unfold khibraSahih shahidSahih; decide),
   khibra_dec_enc _ (by unfold khibraSahih shahidSahih; decide)⟩

/-- وهذه الخمسُ بعينها هي `khibrat` بترتيبها (تثبيتٌ أنّها ليست أمثلةً منفصلة). -/
theorem khibrat_eq :
    khibrat = [⟨qawlMalik 1, .lams, "ثلج", "حرارة", "بارد"⟩, ⟨qawlMalik 2, .lams, "حجر", "صلابة", "صلب"⟩,
      ⟨qawlMalik 3, .lams, "ماء", "قوام", "مائع"⟩, ⟨qawlMalik 4, .lams, "الحارّ", "حرارة", "ساخن"⟩,
      ⟨qawlMalik 5, .sam, "صوت عالٍ", "شدّة الصوت", "صراخ"⟩] := rfl

end Madlul.TashfirHawass
