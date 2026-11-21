/-
  Aql/TashfirMakan.lean — جسرُ المعلومة المعمَّم (الخامس): طيُّ وفكُّ Aql.Makan.Izaha3 وAql.Makan.Mawdi
  وAql.Makan.Marja.

  السند: تفويض المالك 2026-10-17 22:55 («alaqat/hawass/awwaليyyat/makan/isnad … ابني واكتشف كيف نقرا/تبني
  من الرياضيات»)؛ makan من الخمسة، وقُرئ Aql/Makan.lean كاملًا (429 سطرًا) هذه الجلسةُ قبل أيّ تصميم.

  **الاكتشافُ البنائيّ لأنواع المجموع، بعد إخفاقَين فعليَّين لا تخمينًا:**
  (أ) `Izaha3` (ثلاثةُ حقول Int طليقة — بنيةٌ مطابقةٌ تمامًا لحقل `huna` في Aql.Mirsat.Mirsat): حقلٌ واحد
  (`amudi`) في موضع `o` غيرِ المقيَّد وحقلان (`ufuqi`،`tuli`) في `k₁`،`k₂` المقيَّدين بـBOUND، فتحتاج
  Sahih/Subtype (كـMadda/Mirsat، لا كAzmina). أُفرِدت جسرًا قائمًا بذاته (`izaha3Enc`/`izaha3Dec`) لأنّها
  تُستعمَل مرّتين: وحدها، وحمولةً داخل Marja.
  (ب) `Mawdi` (حقلانِ اختياريّان: `jiha : Option Jiha` محدودٌ [6 قيم] و`miqdar : Option (Nat × WahdaMakan)`
  طليقٌ): خيارُ النوع المحدود تعدادٌ مُزاح، وخيارُ النوع الطليق يوضَع في موضع `mixEnc` غيرِ المقيَّد (كـIzaha
  في TashfirAzmina) — فلا شرط Sahih هنا أصلًا.
  (ج) `Marja` (نوعُ مجموع: `sarih Izaha3 | manwi Izaha3 | la`) — هنا إخفاقانِ فعليّانِ قبل الحلّ:
  **الإخفاقُ الأوّل:** استُعملت `SLGE.blockEnc`/`blockDec` (قسمةُ المدى إلى كتلٍ، كتلتا Izaha3 بحجم BOUND³
  صريحًا وكتلةُ `la` بحجم 1). تجميعُ الملفّ بـ`lake build` (لا `lake env lean` الذي يتحقّق فقط بلا توليد
  كودٍ تنفيذيّ — وهو ما مرَّره دون قيدٍ زمنيّ، لأنّه لا يبلغ مرحلة الفحص هذه) أُنهي بالقتل (OOM، رمز 137)
  مرّتين. تتبُّعٌ مباشرٌ لذاكرة العملية (`/proc/<pid>/status` كلَّ ثانية، لا `lake build` المُغلَّف) أظهر نموًّا
  خطّيًّا ثابتًا (~190م.بايت/ث) من 550م.بايت إلى 6ج.بايت في 35 ثانية حتّى القتل: تجسيدُ القيمة الصريحة
  BOUND³ في تعريفٍ حوسوبيّ (`marjaSizes : List Nat`) هو السبب. **الحلّ:** لا حاجةَ إلى `blockEnc` أصلًا —
  التاجُ (محدودٌ بعدد المُنشِئات = 3) في `k₁` المقيَّد، والحمولةُ (مهما بلغ حجمُها الحقيقيّ) في `o` الطليق،
  بذات حيلة Mawdi/Azmina؛ فلا حدَّ رقميًّا على الحمولة يُحمَل أصلًا، ولا تجسيدَ لأيّ BOUND³.
  **الإخفاقُ الثاني:** بعد إزالة `blockEnc`، كُتبت مبرهنةُ الفكّ بخطوةٍ واحدة (`simp only [marjaEnc,
  marjaDec, marjaTag, marjaPayload, SLGE.mixDec_enc ...]`) على نسق الملفّات الأربعة السابقة — فعلَّقت (لا
  OOM بل حلقةٌ/بطءٌ أسّيّ، رمز 124 عند القطع بمهلة) في مرحلة التحقّق ذاتها (`simp only`)، لا التوليد. عزلٌ
  بالقسمة الثنائية (قطعةٌ فقطعة، على نسخٍ في `Scratch/` لم تُدفَع) حصر السببَ في الجمعِ بين عدّة معادلاتِ
  تفكيكٍ (marjaDec، marjaTag، marjaPayload) ومثالٍ معيَّنٍ من mixDec_enc في نداء simp واحد؛ وتعليقٌ ثانٍ
  أصغر: `cases m <;> decide` على `marjaTag_lt` فشل برسالة «Expected type must not contain free variables»
  لأنّ تفكيك Marja (بخلاف كلّ تعداداتٍ بلا حمولة في هذا المشروع) يُبقي متغيّر Izaha3 المحمول في السياق — أوّلُ
  مرّةٍ يُفكَّك فيها نوعُ مجموعٍ بحمولة في هذه السلسلة. **الحلّ:** خطواتٌ صريحةٌ متتابعة (`show`/`unfold
  marjaDec`/`rw` بمثالٍ معيَّن لكلّ حالةٍ من حالات التاج على حدة، لا نداءٌ واحدٌ جامع)، و`simp only [marjaTag]
  <;> omega` بدل `decide` حيث يبقى متغيّرٌ محمولٌ غيرُ ذي صلةٍ في السياق. كلُّ هذا الملفّ (لا فقرةٌ منه) جُرِّب
  فعليًّا بـ`lean … -c out.c` (توليدُ الكودِ الكامل، لا `lake env lean` وحدَه) قبل حفظه، ونجح.
  **الدرسُ المنهجيّ العامّ (يُطبَّق على ما تبقّى، لا سيّما Isnad.Jumla التكراريّة):** التحقّقُ بـ`lake env
  lean` يكفي الصحّةَ المنطقية لكن لا يكفي البناء الفعليّ، ولا يكفي استبعادَ تعليق/بطء الإثبات نفسِه؛ القطعةُ
  الحقيقيّةُ تحتاج تجميعًا فعليًّا (ويُفضَّل بتتبُّع ذاكرةٍ مباشرٍ عند الشكّ) قبل اعتبارها جاهزة. **والنتيجةُ
  الرياضيّةُ العامّة:** أنواعُ المجموع لا تحتاج أداةً جديدةً فوق `mixEnc` ما دام ترميزُها يقع في موضعٍ له
  موضعٌ طليقٌ متاح (تاجٌ صغيرٌ في المقيَّد + حمولةٌ في الطليق، مناظرةً لحيلة الحقل الطليق الواحد في المنتجات)؛
  وإثباتُ الفكّ لنوعِ مجموعٍ بحمولةٍ يحتاج تفكيكًا صريحًا حالةً حالة، لا نداءَ simp جامعًا واحدًا.

  ما يُبرهن هنا: `izaha3_dec_enc` (بشرط Izaha3.Sahih)؛ `jiha_dec_enc`/`jihaEnc_lt`، `wahdaMakan_dec_enc`/
  `wahdaMakanEnc_lt` (تعدادانِ محدودان بلا حمولة)؛ `ojiha_dec_enc`/`ojihaEnc_lt` (Option المحدود، مُزاح)؛
  `miq_dec_enc` (زوجٌ طليقٌ/محدود بـmixEnc)؛ `omiq_dec_enc` (Option الطليق، مُزاح)؛ `mawdi_dec_enc` (بلا
  شرطٍ أصلًا)؛ `marjaTag_lt` (على الشاهد)؛ `marja_dec_enc` بشرط Marja.Sahih (حالاتُ التاج الثلاث صريحةً)؛
  وTayy على الثلاثة (Izaha3Unit/Subtype، Mawdi مباشرةً بلا Unit، MarjaUnit/Subtype). وعلى الشاهد: فكُّ وطيُّ
  **الاثنتي عشرة حالةَ Mawdi الحقيقيّة من شواهد الكتاب نفسِها** (`Aql.Makan.shawahid`، لا شاهدًا مبنيًّا)؛
  وثلاثةُ أمثلةٍ مبنيّةٍ لـMarja (لا شاهدَ مودَعًا مفردًا له، كـmirsatThani/mirsatThalith).

  لا Mathlib في هذا المشروع (مُتحقَّقٌ: lakefile لا يذكرها) — فلا `ring`/`nlinarith`، ولا حاجةَ إليهما بعد
  التخلّي عن المسلك الحسابيّ (BOUND³) الذي استلزمهما.

  مؤجَّلٌ: alaqat/hawass/awwaliyyat/isnad (تحتاج Hawass/Shabaka أداةَ ترميز نصوصٍ String↔Nat لم تُبنَ بعد؛
  وIsnad.Jumla تكراريّةٌ حقًّا)؛ وجسورُ العوامل/الإسناد/Itar3؛ وأداةُ `blockEnc` لحالةٍ تحتاج حدًّا رقميًّا
  صريحًا على ترميز مجموعٍ متداخلٍ داخل موضعٍ مقيَّدٍ من طبقةٍ أخرى (لم تلزم هنا).
-/
import SLGE.Core
import Madlul.TashfirMadda
import Aql.Makan

set_option autoImplicit false

namespace Aql.TashfirMakan

open Mawsua Madlul.TashfirMadda Aql.Makan

/-! ## ١. Izaha3 — ثلاثةُ حقول Int طليقة (كحقل `huna` في Mirsat)؛ Sahih/Subtype -/

def izaha3Enc (r : Izaha3) : Nat :=
  SLGE.mixEnc BOUND BOUND (zigzag r.amudi) (zigzag r.ufuqi) (zigzag r.tuli)

def izaha3Dec (n : Nat) : Izaha3 :=
  match SLGE.mixDec BOUND BOUND n with
  | (amudiC, ufuqiC, tuliC) => { amudi := unzigzag amudiC, ufuqi := unzigzag ufuqiC, tuli := unzigzag tuliC }

/-- شرطُ الصحّة: الحقولُ الثلاثةُ بعد الزِّكزاك دون BOUND. -/
def Izaha3.Sahih (r : Izaha3) : Prop :=
  zigzag r.amudi < BOUND ∧ zigzag r.ufuqi < BOUND ∧ zigzag r.tuli < BOUND

theorem izaha3_dec_enc (r : Izaha3) (h : Izaha3.Sahih r) : izaha3Dec (izaha3Enc r) = r := by
  obtain ⟨h1, h2, h3⟩ := h
  simp only [izaha3Dec, izaha3Enc,
    SLGE.mixDec_enc BOUND BOUND (zigzag r.amudi) (zigzag r.ufuqi) (zigzag r.tuli) h2 h3,
    zigzag_unzigzag]

def Izaha3Unit : Type := {r : Izaha3 // Izaha3.Sahih r}

noncomputable def izaha3FakkOf (code : Nat) : Option Izaha3Unit :=
  @dite (Option Izaha3Unit) (Izaha3.Sahih (izaha3Dec code)) (Classical.propDecidable _)
    (fun h => some ⟨izaha3Dec code, h⟩) (fun _ => none)

theorem izaha3FakkOf_tawiOf (u : Izaha3Unit) : izaha3FakkOf (izaha3Enc u.1) = some u := by
  obtain ⟨r, hr⟩ := u
  show izaha3FakkOf (izaha3Enc r) = some ⟨r, hr⟩
  have heq : izaha3Dec (izaha3Enc r) = r := izaha3_dec_enc r hr
  unfold izaha3FakkOf
  rw [heq, dite_eq_left hr]

noncomputable def tayyIzaha3 : Tayy Izaha3Unit Nat where
  tawi := fun u => izaha3Enc u.1
  fakk := izaha3FakkOf
  fakk_tawi := izaha3FakkOf_tawiOf

theorem tayyIzaha3_la_yudi (u : Izaha3Unit) : tayyIzaha3.fakk (tayyIzaha3.tawi u) = some u :=
  tayyIzaha3.fakk_tawi u

/-! ## ٢. الجهاتُ الستّ ووحداتُ المسافة الثلاث — تعدادانِ محدودان -/

def jihaEnc : Jiha → Nat
  | .fawq => 0 | .taht => 1 | .yamin => 2 | .shimal => 3 | .amam => 4 | .khalf => 5

def jihaDec : Nat → Jiha
  | 0 => .fawq | 1 => .taht | 2 => .yamin | 3 => .shimal | 4 => .amam | _ => .khalf

theorem jiha_dec_enc (j : Jiha) : jihaDec (jihaEnc j) = j := by cases j <;> rfl
theorem jihaEnc_lt (j : Jiha) : jihaEnc j < 6 := by cases j <;> decide

def wahdaMakanEnc : WahdaMakan → Nat
  | .dhira => 0 | .mil => 1 | .farsakh => 2

def wahdaMakanDec : Nat → WahdaMakan
  | 0 => .dhira | 1 => .mil | _ => .farsakh

theorem wahdaMakan_dec_enc (w : WahdaMakan) : wahdaMakanDec (wahdaMakanEnc w) = w := by cases w <;> rfl
theorem wahdaMakanEnc_lt (w : WahdaMakan) : wahdaMakanEnc w < 3 := by cases w <;> decide

/-! ## ٣. Mawdi — خيارانِ اختياريّان (محدودٌ ومُزاح، وطليقٌ موضوعٌ في `o`)؛ بلا شرطٍ أصلًا -/

/-- Option Jiha ↔ Nat: تعدادٌ مُزاح، محدودٌ بـ7 — بلا شرط (كـ`optNatEnc`). -/
def ojihaEnc : Option Jiha → Nat
  | none => 0
  | some j => jihaEnc j + 1

def ojihaDec : Nat → Option Jiha
  | 0 => none
  | n + 1 => some (jihaDec n)

theorem ojiha_dec_enc (o : Option Jiha) : ojihaDec (ojihaEnc o) = o := by
  cases o with
  | none => rfl
  | some j => simp [ojihaEnc, ojihaDec, jiha_dec_enc]

theorem ojihaEnc_lt (o : Option Jiha) : ojihaEnc o < 7 := by
  cases o with
  | none => decide
  | some j => have := jihaEnc_lt j; simp only [ojihaEnc]; omega

/-- Nat × WahdaMakan ↔ Nat: العددُ طليقٌ في موضع `o`، والوحدةُ في `k₁` المقيَّد بـ3 — بلا شرط. -/
def miqEnc : Nat × WahdaMakan → Nat
  | (n, w) => SLGE.mixEnc 3 1 n (wahdaMakanEnc w) 0

def miqDec (n : Nat) : Nat × WahdaMakan :=
  match SLGE.mixDec 3 1 n with
  | (nC, wC, _) => (nC, wahdaMakanDec wC)

theorem miq_dec_enc (p : Nat × WahdaMakan) : miqDec (miqEnc p) = p := by
  obtain ⟨n, w⟩ := p
  simp only [miqEnc, miqDec, SLGE.mixDec_enc 3 1 n (wahdaMakanEnc w) 0 (wahdaMakanEnc_lt w) Nat.zero_lt_one,
    wahdaMakan_dec_enc]

/-- Option (Nat × WahdaMakan) ↔ Nat: مُزاحٌ — بلا شرط. -/
def omiqEnc : Option (Nat × WahdaMakan) → Nat
  | none => 0
  | some p => miqEnc p + 1

def omiqDec : Nat → Option (Nat × WahdaMakan)
  | 0 => none
  | n + 1 => some (miqDec n)

theorem omiq_dec_enc (o : Option (Nat × WahdaMakan)) : omiqDec (omiqEnc o) = o := by
  cases o with
  | none => rfl
  | some p => simp [omiqEnc, omiqDec, miq_dec_enc]

/-- **الطيّ**: miqdar (طليقٌ، يحمل Nat بلا حدّ) في موضع `o` غيرِ المقيَّد، وjiha (محدودٌ بـ7) في `k₁`. -/
def mawdiEnc (m : Mawdi) : Nat := SLGE.mixEnc 7 1 (omiqEnc m.miqdar) (ojihaEnc m.jiha) 0

def mawdiDec (n : Nat) : Mawdi :=
  match SLGE.mixDec 7 1 n with
  | (miqC, jihaC, _) => { jiha := ojihaDec jihaC, miqdar := omiqDec miqC }

/-- **الفكُّ يعيد الأصل بلا شرطٍ أصلًا** — كـIzaha في TashfirAzmina: حقلٌ طليقٌ واحدٌ (بعد الإزاحة) يكفيه
موضعُ `o`. -/
theorem mawdi_dec_enc (m : Mawdi) : mawdiDec (mawdiEnc m) = m := by
  simp only [mawdiDec, mawdiEnc,
    SLGE.mixDec_enc 7 1 (omiqEnc m.miqdar) (ojihaEnc m.jiha) 0 (ojihaEnc_lt m.jiha) Nat.zero_lt_one,
    omiq_dec_enc, ojiha_dec_enc]

def tayyMawdi : Tayy Mawdi Nat where
  tawi := mawdiEnc
  fakk := fun n => some (mawdiDec n)
  fakk_tawi := fun m => by rw [mawdi_dec_enc]

theorem tayyMawdi_la_yudi (m : Mawdi) : tayyMawdi.fakk (tayyMawdi.tawi m) = some m :=
  tayyMawdi.fakk_tawi m

/-! ## ٤. Marja — نوعُ مجموع: التاجُ (محدودٌ بـ3) في `k₁`، والحمولةُ في `o` الطليق (لا blockEnc؛ انظر الترويسة) -/

/-- التاج: 0=sarih، 1=manwi، 2=la. -/
def marjaTag : Marja → Nat
  | .sarih _ => 0 | .manwi _ => 1 | .la => 2

/-- الحمولة: طيُّ Izaha3 لـsarih/manwi، و0 لـla (لا يُقرأ عند الفكّ). -/
def marjaPayload : Marja → Nat
  | .sarih r => izaha3Enc r
  | .manwi r => izaha3Enc r
  | .la => 0

/-- **الطيّ**: الحمولةُ (قد تبلغ BOUND³، لا حدَّ معلومًا يُحمَل هنا) في `o`، والتاجُ في `k₁` المقيَّد بـ3. -/
def marjaEnc (m : Marja) : Nat := SLGE.mixEnc 3 1 (marjaPayload m) (marjaTag m) 0

def marjaDec (n : Nat) : Marja :=
  match SLGE.mixDec 3 1 n with
  | (payloadC, tagC, _) =>
    match tagC with
    | 0 => .sarih (izaha3Dec payloadC)
    | 1 => .manwi (izaha3Dec payloadC)
    | _ => .la

/-- شرطُ الصحّة: الحمولةُ (إن وُجدت) صحيحةٌ بشرط Izaha3. -/
def Marja.Sahih : Marja → Prop
  | .sarih r => Izaha3.Sahih r
  | .manwi r => Izaha3.Sahih r
  | .la => True

/-- **الفكُّ يعيد الأصل بشرط Marja.Sahih** — حالاتُ التاج الثلاث صريحةً (`show`/`unfold`/`rw`، لا نداءَ simp
جامعًا واحدًا — انظر الترويسة: نداءٌ جامعٌ هنا يُعلِّق). -/
theorem marja_dec_enc (m : Marja) (h : Marja.Sahih m) : marjaDec (marjaEnc m) = m := by
  cases m with
  | sarih r =>
    show marjaDec (SLGE.mixEnc 3 1 (izaha3Enc r) 0 0) = .sarih r
    unfold marjaDec
    rw [SLGE.mixDec_enc 3 1 (izaha3Enc r) 0 0 (by decide) Nat.zero_lt_one]
    show Marja.sarih (izaha3Dec (izaha3Enc r)) = Marja.sarih r
    rw [izaha3_dec_enc r h]
  | manwi r =>
    show marjaDec (SLGE.mixEnc 3 1 (izaha3Enc r) 1 0) = .manwi r
    unfold marjaDec
    rw [SLGE.mixDec_enc 3 1 (izaha3Enc r) 1 0 (by decide) Nat.zero_lt_one]
    show Marja.manwi (izaha3Dec (izaha3Enc r)) = Marja.manwi r
    rw [izaha3_dec_enc r h]
  | la =>
    show marjaDec (SLGE.mixEnc 3 1 0 2 0) = .la
    unfold marjaDec
    rw [SLGE.mixDec_enc 3 1 0 2 0 (by decide) Nat.zero_lt_one]
    rfl

/-- على الشاهد (التاجُ محدودٌ بـ3) — `simp+omega` لا `decide`: تفكيكُ Marja يُبقي متغيّر Izaha3 المحمولَ في
السياق (أوّلُ نوعِ مجموعٍ بحمولةٍ في هذه السلسلة)، وdecide يرفض مع متغيّرٍ حرٍّ في السياق. -/
theorem marjaTag_lt (m : Marja) : marjaTag m < 3 := by cases m <;> simp only [marjaTag] <;> omega

def MarjaUnit : Type := {m : Marja // Marja.Sahih m}

noncomputable def marjaFakkOf (code : Nat) : Option MarjaUnit :=
  @dite (Option MarjaUnit) (Marja.Sahih (marjaDec code)) (Classical.propDecidable _)
    (fun h => some ⟨marjaDec code, h⟩) (fun _ => none)

theorem marjaFakkOf_tawiOf (u : MarjaUnit) : marjaFakkOf (marjaEnc u.1) = some u := by
  obtain ⟨m, hm⟩ := u
  show marjaFakkOf (marjaEnc m) = some ⟨m, hm⟩
  have heq : marjaDec (marjaEnc m) = m := marja_dec_enc m hm
  unfold marjaFakkOf
  rw [heq, dite_eq_left hm]

noncomputable def tayyMarja : Tayy MarjaUnit Nat where
  tawi := fun u => marjaEnc u.1
  fakk := marjaFakkOf
  fakk_tawi := marjaFakkOf_tawiOf

theorem tayyMarja_la_yudi (u : MarjaUnit) : tayyMarja.fakk (tayyMarja.tawi u) = some u :=
  tayyMarja.fakk_tawi u

/-! ## ٥. على الشاهد -/

/-- طيُّ وفكُّ الاثنتي عشرة حالةَ Mawdi الحقيقيّة من شواهد الكتاب (`Aql.Makan.shawahid`) — لا شاهدًا مبنيًّا. -/
theorem mawdi_shawahid_tudi : shawahid.map (fun p => mawdiDec (mawdiEnc p.2)) = shawahid.map (fun p => p.2) := by
  simp [mawdi_dec_enc]

/-- أمثلةٌ مبنيّة لـMarja (لا شاهدَ مودَعًا مفردًا لها، كـmirsatThani/mirsatThalith). -/
def marjaAsl : Marja := .sarih sifr
def marjaThani : Marja := .manwi ⟨3, -7, 12⟩
def marjaThalith : Marja := .la

theorem marja_shawahid_sahih : Marja.Sahih marjaAsl ∧ Marja.Sahih marjaThani ∧ Marja.Sahih marjaThalith := by
  unfold Marja.Sahih marjaAsl marjaThani marjaThalith Izaha3.Sahih sifr zigzag BOUND
  decide

theorem marja_shawahid_tudi :
    marjaDec (marjaEnc marjaAsl) = marjaAsl ∧ marjaDec (marjaEnc marjaThani) = marjaThani ∧
    marjaDec (marjaEnc marjaThalith) = marjaThalith := by
  obtain ⟨s1, s2, s3⟩ := marja_shawahid_sahih
  exact ⟨marja_dec_enc _ s1, marja_dec_enc _ s2, marja_dec_enc _ s3⟩

end Aql.TashfirMakan
