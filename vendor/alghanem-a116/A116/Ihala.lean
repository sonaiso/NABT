import A116.Mufrad

/-!
# الضميرُ والإحالةُ والموصولُ والإشارة (ADR ٨٣)

أمرُ المالك (2026-10-16): «الضمائرُ والإحالةُ والموصولُ والإشارة، على أساس ADR ٨١: فالضميرُ اسمٌ جزئيٌّ يفتقر
إلى مفسِّر، والإحالةُ هي علاقتُه بذلك المفسِّر».

## السند (شرحُ ابن عقيل المختوم؛ المراسي في `marasi` يفحصها `tests/test_ihala.py`)

* س720: المعارفُ ستّة: «المضمر … واسمُ الإشارة … والعلم … والمحلّى بالألف واللام … والموصول … وما أُضيف».
* س724–725: «الضميرُ ما دلّ على غيبةٍ كهو أو حضور، وهو [الحضور] قسمان: ضميرُ المخاطب … وضميرُ المتكلّم».
* س1703–1706، س1719–1721: «لئلّا يعود الضميرُ على متأخّرٍ لفظًا ورتبة» — قيدُ الإحالة؛ وس1722: «وقد جرى
  الخلافُ في جواز ضرب غلامُه زيدًا».
* س345: الموصولاتُ «مفتقرةٌ في سائر أحوالها إلى الصلة فأشبهت الحرفَ في ملازمة الافتقار فبُنيت».
* س1133–1137: «الموصولاتُ كلُّها حرفيّةً كانت أو اسميّةً يلزم أن يقع بعدها صلة … ويُشترط في صلة الموصول
  الاسميّ أن تشتمل على ضميرٍ لائقٍ بالموصول: إن كان مفردًا فمفرد، وإن كان مذكّرًا فمذكّر».
* س1138–1141: «مَن وما … يجوز حينئذٍ مراعاةُ اللفظ ومراعاةُ المعنى».
* س1143: «صلةُ الموصول لا تكون إلّا جملةً أو شبهَ جملة».
* س1001–1010: «المشارُ إليه له رتبتان القربُ والبعد … أُتي بالكاف وحدها فتقول ذاك أو الكاف واللام نحو ذلك،
  وهذه الكافُ حرفُ خطابٍ فلا موضعَ لها من الإعراب … فإن تقدّم حرفُ التنبيه … أتيت بالكاف وحدها … ولا يجوز
  الإتيانُ بالكاف واللام فلا تقول هذالك».

## ما يُبرهَن

١. **الحضورُ ثلاثيّ** (`Hudur`)، و**المفسِّرُ في النصّ للغائب وحدَه** (`mufassir_fi_nass_iff`): المتكلّمُ
   والمخاطبُ يتعيّنان بالمقام لا بلفظٍ في النصّ — ومكانُ ذلك طبقةُ الحكم لا طبقةُ الدالّ (المادّة ١٧).
٢. **قيدُ الإحالة** (`jaiz`): يجوز إن تقدّم المفسِّرُ لفظًا أو رتبة، ويُمنع ⟺ تأخّر لفظًا ورتبةً معًا
   (`mamnu_iff`)؛ والشاهدان «في الدار صاحبُها» جائزٌ و«صاحبُها في الدار» ممنوع (`shawahid_ihala`)،
   و«ضرب غلامُه زيدًا» ممنوعٌ بهذا القيد وهو موضعُ خلافٍ مسمًّى (`ghulamuhu_mamnu`).
٣. **الموصول**: لا يتمّ إلّا بصلة؛ والاسميُّ صلتُه تشتمل على عائدٍ لائق، والحرفيُّ لا عائدَ له
   (`ismi_yahtaj_aid`، `harfi_bila_aid`) — فالضميرُ لا يعود إلّا على اسم؛ و«مَن» تجيز مراعاةَ اللفظ والمعنى
   (`man_lafz_wa_maana`).
٤. **الإشارة**: القربُ بلا كاف والبعدُ بالكاف، واللامُ لا تكون بلا كاف ولا مع «ها» (`ishara_shawahid`)؛ والكافُ
   في «ذلك» حرفُ خطاب وفي «أكرمك» ضمير — خاناتٌ واحدةٌ بقسمين (`kaf_qismayn`).
٥. **المعارفُ الستّ أسماء**، وحاجاتُ ما يحتاج منها (تفسير، صلة، مشارٌ إليه، مضافٌ إليه) ليست تعلّقَ الحرف
   (`marifa_ism`)؛ والموصولُ والإشارةُ والضميرُ مبنيّةٌ بالشبه لا بالحرفيّة.

ما لا يُبرهَن: أنّ ضميرًا في المصحف يعود على كلمةٍ بعينها — الإحالةُ مدخلٌ يُروى ولا مرجعَ لها مودَع
(`IHALA_GOLD_ABSENT`)؛ والرتبةُ (مبتدأ قبل خبر…) مدخلٌ (`RUTBA_IS_INPUT`).
-/

namespace A116.Ihala

open A116 A116.Tarkib A116.Mufrad

/-! ## ١. الضميرُ وحضورُه -/

/-- س724–725: الغيبةُ والحضور، والحضورُ متكلّمٌ ومخاطب. -/
inductive Hudur where
  | mutakallim | mukhatab | ghaib
  deriving DecidableEq, Repr

/-- مفسِّرُه لفظٌ في النصّ: الغائبُ وحدَه؛ والحاضرُ يتعيّن بالمقام (س906: «بقيد التكلّم أو الخطاب»). -/
def mufassirFiNass : Hudur → Bool
  | .ghaib => true
  | _ => false

theorem mufassir_fi_nass_iff (h : Hudur) : mufassirFiNass h = true ↔ h = .ghaib := by
  cases h <;> decide

/-! ## ٢. قيدُ الإحالة: لا يعود الضميرُ على متأخّرٍ لفظًا ورتبة -/

/-- إحالةٌ: موضعُ الضمير وموضعُ مفسِّره في السطر. -/
structure Ihala where
  damir : Nat
  mufassir : Nat
  deriving DecidableEq, Repr

/-- جائزةٌ إن تقدّم المفسِّرُ لفظًا أو رتبة؛ والرتبةُ مدخلٌ (مبتدأٌ قبل خبر، فاعلٌ قبل مفعول). -/
def jaiz (rutba : Nat → Nat) (e : Ihala) : Bool :=
  decide (e.mufassir < e.damir) || decide (rutba e.mufassir < rutba e.damir)

/-- **الممنوعُ هو المتأخّرُ لفظًا ورتبةً معًا** — لا أحدُهما. -/
theorem mamnu_iff (rutba : Nat → Nat) (e : Ihala) :
    jaiz rutba e = false ↔ e.damir ≤ e.mufassir ∧ rutba e.damir ≤ rutba e.mufassir := by
  simp [jaiz, Nat.not_lt]

theorem taqaddum_lafzi (rutba : Nat → Nat) (e : Ihala) (h : e.mufassir < e.damir) :
    jaiz rutba e = true := by simp [jaiz, h]

theorem taqaddum_rutbi (rutba : Nat → Nat) (e : Ihala) (h : rutba e.mufassir < rutba e.damir) :
    jaiz rutba e = true := by simp [jaiz, h]

/-- رتبُ الشاهدين: المبتدأ 0 والخبرُ 1، وكلُّ كلمةٍ برتبة ركنها. -/
def rutbaFiDar : Nat → Nat
  | 0 => 1 | 1 => 1 | _ => 0      -- «في الدار صاحبُها»: في(خبر) الدار(خبر) صاحبُها(مبتدأ)
def rutbaSahibuha : Nat → Nat
  | 0 => 0 | _ => 1               -- «صاحبُها في الدار»: صاحبُها(مبتدأ) في الدار(خبر)

/-- «في الدار صاحبُها» جائز (المفسِّرُ «الدار» متقدّمٌ لفظًا)، و«صاحبُها في الدار» ممنوع (س1703–1706). -/
theorem shawahid_ihala :
    jaiz rutbaFiDar ⟨2, 1⟩ = true ∧ jaiz rutbaSahibuha ⟨0, 2⟩ = false := by decide

/-- «ضرب غلامُه زيدًا»: الهاءُ في الفاعل (رتبةٌ 0) ومفسِّرُها المفعولُ (رتبةٌ 1) متأخّرٌ لفظًا ورتبة —
ممنوعٌ بالقيد، وهو موضعُ خلافٍ مسمًّى في الشرح (س1722). -/
def rutbaGhulamuhu : Nat → Nat
  | 2 => 1 | _ => 0

theorem ghulamuhu_mamnu : jaiz rutbaGhulamuhu ⟨1, 2⟩ = false := by decide

/-! ## ٣. الموصول والعائد -/

inductive Adad where
  | mufrad | muthanna | jam
  deriving DecidableEq, Repr

inductive Jins where
  | mudhakkar | muannath
  deriving DecidableEq, Repr

/-- السمةُ التي يُشترط فيها أن يكون العائدُ لائقًا (س1134–1137). -/
structure Simah where
  adad : Adad
  jins : Jins
  deriving DecidableEq, Repr

inductive Mawsul where
  /-- الاسميّ: بسماتٍ يجوز للعائد مراعاتُها (لفظًا، ومعنًى في مَن وما). -/
  | ismi (simat : List Simah)
  /-- الحرفيّ (أنْ المصدريّة وأخواتها، س1025–1027). -/
  | harfi
  deriving Repr

inductive SilaNaw where
  | jumla | shibhJumla
  deriving DecidableEq, Repr

/-- الصلة: نوعُها وسماتُ الضمائر العائدة فيها على الموصول. -/
structure Sila where
  naw : SilaNaw
  awaid : List Simah
  deriving Repr

/-- العائدُ لائقٌ: سمتُه من سمات الموصول. -/
def laiq (simat : List Simah) (s : Simah) : Bool := simat.contains s

/-- تمامُ الموصول بصلته (س1132–1137). -/
def tamm : Mawsul → Option Sila → Bool
  | _, none => false
  | .harfi, some _ => true
  | .ismi simat, some s => s.awaid.any (laiq simat)

/-- **لا موصولَ بلا صلة** — «الافتقار اللازم» (س345). -/
theorem la_tamam_bila_sila (m : Mawsul) : tamm m none = false := by cases m <;> rfl

/-- **الاسميُّ يحتاج عائدًا لائقًا**: صلةٌ بلا عائدٍ لائقٍ لا تُتمّه. -/
theorem ismi_yahtaj_aid (simat : List Simah) (s : Sila) :
    tamm (.ismi simat) (some s) = true ↔ ∃ a ∈ s.awaid, laiq simat a = true := by
  simp [tamm, List.any_eq_true]

/-- **الحرفيُّ لا عائدَ له**: صلتُه تُتمّه وإن خلت من ضمير — فالضميرُ لا يعود على حرف. -/
theorem harfi_bila_aid (n : SilaNaw) : tamm .harfi (some ⟨n, []⟩) = true := rfl

def ms : Simah := ⟨.mufrad, .mudhakkar⟩
def fs : Simah := ⟨.mufrad, .muannath⟩
def mp : Simah := ⟨.jam, .mudhakkar⟩

/-- «الذي» مفردٌ مذكّر؛ و«مَن» لفظُها مفردٌ مذكّر ويجوز معناها غيرَه (س1138–1141). -/
def alladhi : Mawsul := .ismi [ms]
def man : Mawsul := .ismi [ms, fs, ⟨.muthanna, .mudhakkar⟩, ⟨.muthanna, .muannath⟩, mp, ⟨.jam, .muannath⟩]

/-- «جاءني الذي ضربتُه» تامّ، و«الذي ضربتُها» لا يتمّ؛ و«مَن قامت» تامٌّ بمراعاة المعنى. -/
theorem man_lafz_wa_maana :
    tamm alladhi (some ⟨.jumla, [ms]⟩) = true ∧ tamm alladhi (some ⟨.jumla, [fs]⟩) = false ∧
    tamm man (some ⟨.jumla, [ms]⟩) = true ∧ tamm man (some ⟨.jumla, [fs]⟩) = true := by decide

/-! ## ٤. الإشارة -/

/-- صيغةُ اسم الإشارة: «ها» التنبيه قبله، والكاف، واللام (س1004–1010). -/
structure Sigha where
  ha : Bool
  kaf : Bool
  lam : Bool
  deriving DecidableEq, Repr

/-- اللامُ لا تكون إلّا مع الكاف، ولا تجتمع مع «ها» («فلا تقول هذالك»). -/
def sahiha (s : Sigha) : Bool := (!s.lam || s.kaf) && !(s.ha && s.lam)

inductive RutbaIshara where
  | qurb | bud
  deriving DecidableEq, Repr

/-- «المشارُ إليه له رتبتان القربُ والبعد» (س1001): البعدُ بالكاف. -/
def rutbaIshara (s : Sigha) : RutbaIshara := if s.kaf then .bud else .qurb

def dha : Sigha := ⟨false, false, false⟩
def hadha : Sigha := ⟨true, false, false⟩
def dhaka : Sigha := ⟨false, true, false⟩
def dhalika : Sigha := ⟨false, true, true⟩
def hadhaka : Sigha := ⟨true, true, false⟩
def hadhalika : Sigha := ⟨true, true, true⟩

theorem ishara_shawahid :
    rutbaIshara hadha = .qurb ∧ rutbaIshara dhaka = .bud ∧ rutbaIshara dhalika = .bud ∧
    rutbaIshara hadhaka = .bud ∧ sahiha hadhaka = true ∧ sahiha hadhalika = false ∧
    sahiha dhalika = true ∧ sahiha ⟨false, false, true⟩ = false := by decide

/-- **الكافُ قسمان والخاناتُ واحدة**: في «ذلك» حرفُ خطابٍ لا موضعَ له من الإعراب (س1005)، وفي «أكرمك»
ضميرٌ اسم (س727)؛ والترخيصُ لا يفرّقهما لأيّ خانات. -/
theorem kaf_qismayn (c : List Cell) :
    tarkibB [⟨c, .harf⟩] = tarkibB [⟨c, qismOf huwa⟩] ∧ qismOf huwa ≠ Qism.harf := by
  refine ⟨rfl, by decide⟩

/-! ## ٥. المعارفُ الستّ -/

/-- س720. -/
inductive Marifa where
  | mudmar | ishara | alam | muarraf | mawsul | mudaf
  deriving DecidableEq, Repr

/-- حاجاتُ المعرفة إلى غيرها — وليس فيها تعلّقُ الحرف. -/
inductive HajaM where
  | tafsir | musharIlayh | sila | mudafIlayh
  deriving DecidableEq, Repr

def hajaM : Marifa → Option HajaM
  | .mudmar => some .tafsir
  | .ishara => some .musharIlayh
  | .mawsul => some .sila
  | .mudaf => some .mudafIlayh
  | _ => none

def marifat : List Marifa := [.mudmar, .ishara, .alam, .muarraf, .mawsul, .mudaf]

/-- **المعارفُ الستّ أسماء**: أربعٌ منها تحتاج غيرَها، وحاجاتُها أربعٌ متباينة، والعلمُ والمعرّفُ لا يحتاجان. -/
theorem marifa_ism :
    marifat.length = 6 ∧ (marifat.filterMap hajaM).length = 4 ∧ (marifat.filterMap hajaM).Nodup ∧
    hajaM .alam = none ∧ hajaM .muarraf = none := by decide

/-! ## المراسي -/

def marasi : List (Nat × String) :=
  [ (720, "المضمر كهم واسم الإشارة كذي والعلم كهند"),
    (724, "يشير إلى أن الضمير ما دل على غيبة كهو أو حضور"),
    (1705, "لئلا يعود الضمير على متأخر لفظا"),
    (1722, "وقد جرى الخلاف في جواز ضرب غلامه زيدا"),
    (345, "فإنها مفتقرة في سائر أحوالها إلى الصلة"),
    (1133, "الموصولات كلها حرفية كانت أو اسمية يلزم أن يقع بعدها صلة"),
    (1134, "ويشترط في صلة الموصول الاسمي أن تشتمل على ضمير لائق بالموصول"),
    (1139, "فيجوز حينئذ مراعاة اللفظ"),
    (1143, "صلة الموصول لا تكون إلا جملة أو شبه جملة"),
    (1001, "البيت إلى أن المشار إليه له رتبتان القرب والبعد"),
    (1005, "وهذه الكاف حرف خطاب فلا موضع لها من الإعراب"),
    (1010, "ولا يجوز الإتيان بالكاف واللام فلا تقول هذالك") ]

end A116.Ihala
