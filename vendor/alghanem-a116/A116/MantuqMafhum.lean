import A116.Dalalat
import A116.Iqtiran
import A116.Naql

/-!
# الجسرُ من المنطوق إلى المفهوم الأصوليّ (ADR ١١٢، المهمّة ٢ من خطّة ADR ١١١، إذنُ المالك 2026-10-18)

السندُ الشخصيّة ج3 المختومة (`corpora/nabhani/shakhsiyya_j3.txt.gz`، بترقيم الغانم 1-based، 1,090 سطرًا):

* س516: «والمنطوق هو ما دل عليه اللفظ قطعاً في محل النطق»، «فتخرج دلالة الاقتضاء».
* س518: «المفهوم هو ما فهم من اللفظ في غير محل النطق»، و«الدلالة الالتزامية».
* س520: الاقتضاءُ لازمٌ «بأن يكون شرطاً للمعنى المدلول عليه بالمطابقة».
* س522: التنبيهُ والإيماء «إنما تقع فيما يدل على العلية».
* س524: الإشارةُ حكمٌ «لم يكن مقصوداً من الكلام».
* س526: الموافقةُ مدلولٌ «في محل السكوت موافقاً لمدلوله في محل النطق»؛ س528: «بأن لا يكون شرطاً للمعنى
  المطابقي بل تابعاً له»، و«فإن اشتراط الأولوية في مفهوم الموافقة لا معنى له»؛ س532: «على أنه لا توجد دلالة
  قياسية وإنما يوجد قياس».
* س534: المخالفةُ «مخالفاً لمدلوله في محل النطق»، «كمفهوم الصفة، ومفهوم الشرط، ومفهوم الغاية، ومفهوم العدد».
* س536: «وشرطه أن تكون تلك الصفة وصفاً مفهماً».
* س548: «إنما يكون معمولاً به إذا استكمل شرطين: أحدهما تقييد الحكم بالعدد، والثاني أن يدل سياق الكلام على نفي
  الحكم عن غير العدد»، وشاهدُه السالب «اعطني القرشين».
* س550: «فلا يعمل بمفهوم الاسم مطلقاً»؛ س551: «لا يعمل بمفهوم الوصف غير المفهم»؛ س552: مفهومُ «إنما»؛
  س553: «مخرج الأعم الأغلب لا مفهوم له»؛ س554: «إذا ورد نص من الكتاب أو السنة يعطله».
* س555: «فمفهوم المخالفة محصور في الأصناف الأربعة ليس غير».

## ما يُبنى

1. **الأنواعُ الخمسة** (`Naw`) والفصلُ بينها بأربع صفاتٍ للازم؛ ترتيبُ الفحص تعيينُ البنّاء (`NAW_ORDER_DECLARED`)،
   والصفاتُ مُدخَلة (`MAFHUM_FEATURES_ARE_INPUT`)، وصفةُ «من التركيب» (س528) ومصدرُ الاقتضاء عقلًا وشرعًا (س520)
   ساقطان من الترميز (`TARKIB_SOURCE_NOT_ENCODED`).
2. **المخالفةُ محصورةٌ في الأربعة**، والصفةُ بشرط `Dalalat.mufhim` بعينه، والعددُ بشرط السياق (س548)؛ وموانعُ س550–554
   أسبابُ رفضٍ مسمّاة؛ والأغلبُ والنصُّ المعطِّل مُدخَلان (`AGHLAB_IS_INPUT`، `MUATTIL_IS_INPUT`).
3. **المادّة ٢٤**: `MafhumUsul` نوعٌ للمستخرَج، والشاهدُ مودَعٌ **مقرونٌ بالمفهوم الذي يشهد له** (`Mudaa`)، فالرتبةُ
   تُحسب من المودَع بمساري الغانم القائمين (`Iqtiran.martaba`، `Naql.jisrWad`/`jisrWaqi`)، وشهادةُ غيره لا ترفعه.

والأوسامُ في كلّ مبرهنة: «لكلّ» لما يقول شيئًا عن كلّ مدخل، و«تعريفيّ أو نتيجةٌ مباشرة» لما يفكّ التعريف، و«على
الشاهد» لـ`decide`؛ وكلُّ ذلك على الترميز، والمطابقةُ للنصّ قراءةُ البنّاء (م٢٢).
-/

namespace A116.MantuqMafhum

/-! ## ١. المنطوقُ والمفهوم (س516، س518) -/

/-- المنطوق: ما دلّ عليه اللفظ قطعًا ومباشرةً (س516). -/
def mantuqB (qati mubashir : Bool) : Bool := qati && mubashir

/-- **ما لم يُفهم قطعًا ليس منطوقًا** (س516، وبه أُخرج الاقتضاء: «لم تفهم قطعاً بل احتمالاً»). تعريفيّ. -/
theorem ghayr_qati_laysa_mantuq (mubashir : Bool) : mantuqB false mubashir = false := rfl

/-- أنواعُ المفهوم الخمسة (س518–534). -/
inductive Naw | iqtida | tanbih | ishara | muwafaqa | mukhalafa
  deriving DecidableEq, Repr

/-- صفاتُ اللازم في نصّه (مُدخَلة، `MAFHUM_FEATURES_ARE_INPUT`):
`shart` شرطٌ للمعنى المطابقيّ (س520)، `illiyya` يلزم منه التعليلُ وضعًا (س522)، `maqsud` مقصودٌ من الكلام (س524)،
`muwafiq` موافقٌ لمدلول المنطوق (س526، س534). -/
structure Sifat where
  shart : Bool
  illiyya : Bool
  maqsud : Bool
  muwafiq : Bool
  deriving DecidableEq, Repr

/-- التصنيف (ترتيبُ الفحص تعيينُ البنّاء، `NAW_ORDER_DECLARED`). -/
def naw (s : Sifat) : Naw :=
  if s.shart then .iqtida
  else if s.illiyya then .tanbih
  else if !s.maqsud then .ishara
  else if s.muwafiq then .muwafaqa
  else .mukhalafa

/-- **على الترميز، يفترق الاقتضاءُ والموافقةُ بصفة الشرط** (س520 مقابل س528): ما كان موافقةً بلا شرط يصير اقتضاءً
بالشرط، وهو مقصودٌ موافق. لكلّ صفات؛ والنصُّ يفرّقهما بالمصدر أيضًا (`TARKIB_SOURCE_NOT_ENCODED`). -/
theorem iqtida_muwafaqa_fasl (s : Sifat) (h : naw { s with shart := false } = .muwafaqa) :
    naw { s with shart := true } = .iqtida ∧ s.maqsud = true ∧ s.muwafiq = true := by
  refine ⟨by simp [naw], ?_, ?_⟩ <;>
  · cases hi : s.illiyya <;> cases hm : s.maqsud <;> cases hw : s.muwafiq <;> simp_all [naw]

/-- الموافقةُ والمخالفةُ تفترقان بالموافقة إذا لم يكن شرطٌ ولا تعليلٌ وكان مقصودًا. تعريفيّ. -/
theorem muwafaqa_mukhalafa_fasl (s : Sifat) (h1 : s.shart = false) (h2 : s.illiyya = false)
    (h3 : s.maqsud = true) : naw s = (if s.muwafiq then .muwafaqa else .mukhalafa) := by
  simp [naw, h1, h2, h3]

/-- **الأنواعُ الخمسة كلُّها تقع**. على الشاهد. -/
theorem kull_naw_yaqa : ∀ n : Naw, ∃ s : Sifat, naw s = n := by
  intro n; cases n
  · exact ⟨⟨true, false, true, true⟩, rfl⟩
  · exact ⟨⟨false, true, true, true⟩, rfl⟩
  · exact ⟨⟨false, false, false, true⟩, rfl⟩
  · exact ⟨⟨false, false, true, true⟩, rfl⟩
  · exact ⟨⟨false, false, true, false⟩, rfl⟩

/-- المفهومُ كلُّه التزام (س518، س528، س530). تعريف. -/
def dalalaOf : Naw → Dalalat.Dalala := fun _ => .iltizam

/-- مصدرُ الحكم في محلّ السكوت: لفظيٌّ لا قياسيّ (س529، س532). -/
inductive Masdar | lafzi | qiyasi
  deriving DecidableEq, Repr

def masdarOf : Naw → Masdar := fun _ => .lafzi

/-- لا دلالةَ قياسيّة (س532). تعريفيّ. -/
theorem la_dalala_qiyasiyya (n : Naw) : masdarOf n ≠ .qiyasi := by cases n <;> decide

/-- صورُ الموافقة (س527): الأدنى على الأعلى، والأعلى على الأدنى، والمساوي، وغيرُها. -/
inductive SuratMuwafaqa | adna | ala | musawi | ghayruha
  deriving DecidableEq, Repr

/-- الموافقةُ من التركيب لا من الأولويّة (س528): كلُّ صورةٍ موافقة. -/
def muwafaqaMinTarkib : SuratMuwafaqa → Bool := fun _ => true

/-- الأولويّةُ ليست شرطًا (س528). تعريفيّ. -/
theorem awlawiyya_laysat_shart :
    muwafaqaMinTarkib .musawi = true ∧ muwafaqaMinTarkib .ghayruha = true := ⟨rfl, rfl⟩

/-! ## ٢. المخالفة: القيدُ والموانع (س534–555) -/

/-- القيدُ الذي عُلّق به الحكم: الأربعةُ (س534) — والعددُ بدلالة السياق على نفي الحكم عن غيره (س548) — والاسمُ
(س550)، و«إنما» (س552). القائمةُ مغلقةٌ بتعيين البنّاء (`QAYD_CLOSED_DECLARED`). -/
inductive Qayd
  | sifa (w : Dalalat.Wasf)
  | shart
  | ghaya
  | adad (siyaq : Bool)
  | ism
  | innama
  deriving DecidableEq, Repr

/-- سببُ أن لا يُعمل بالمخالفة، مسمًّى بسطره. -/
inductive Mani
  | adadBilaSiyaq  -- س548
  | ism            -- س550
  | wasfGhayrMufhim -- س551
  | innama         -- س552
  | aghlab         -- س553
  | muattil        -- س554
  deriving DecidableEq, Repr

/-- المفهومُ الأصوليّ المستخرَج: نوعُه، ومعناه في محلّ السكوت. -/
structure MafhumUsul where
  naw : Naw
  mana : String
  deriving DecidableEq, Repr

/-- حكمُ الجسر: يُعمل بالمفهوم، أو لا يُعمل به لمانعٍ مسمًّى. -/
inductive Hukm
  | yumal (m : MafhumUsul)
  | layumal (m : Mani)
  deriving DecidableEq, Repr

/-- مانعُ القيد بنوعه (س548، س550–552)، أو لا مانع. -/
def maniQayd : Qayd → Option Mani
  | .sifa w => if Dalalat.mufhim w then none else some .wasfGhayrMufhim
  | .shart | .ghaya => none
  | .adad siyaq => if siyaq then none else some .adadBilaSiyaq
  | .ism => some .ism
  | .innama => some .innama

/-- جسرُ المخالفة: مانعُ القيد، ثمّ الأغلب (س553)، ثمّ النصُّ المعطِّل (س554) — الترتيبُ تعيينُ البنّاء
(`MANI_ORDER_DECLARED`)، ويعيّن اسمَ المانع إذا اجتمع مانعان. -/
def mukhalafa (q : Qayd) (aghlab muattil : Bool) (mana : String) : Hukm :=
  match maniQayd q with
  | some m => .layumal m
  | none =>
    if aghlab then .layumal .aghlab
    else if muattil then .layumal .muattil
    else .yumal ⟨.mukhalafa, mana⟩

/-- القيودُ الأربعة (س555). -/
def arbaa : Qayd → Bool
  | .sifa _ | .shart | .ghaya | .adad _ => true
  | .ism | .innama => false

/-- **الحصر** (س555، وشرطا س536 وس548): ما يُعمل به قيدُه من الأربعة، والصفةُ مفهمة، والعددُ بسياقه، ولا أغلبَ ولا
معطِّل. لكلّ قيدٍ ومدخل (بالحالات). -/
theorem hasr_arbaa (q : Qayd) (a u : Bool) (s : String) (m : MafhumUsul)
    (h : mukhalafa q a u s = .yumal m) :
    arbaa q = true ∧ (∀ w, q = .sifa w → Dalalat.mufhim w = true) ∧
    (∀ c, q = .adad c → c = true) ∧ a = false ∧ u = false ∧ m = ⟨.mukhalafa, s⟩ := by
  cases q with
  | sifa w =>
    cases hw : Dalalat.mufhim w <;> cases a <;> cases u <;> simp_all [mukhalafa, maniQayd, arbaa]
  | adad c => cases c <;> cases a <;> cases u <;> simp_all [mukhalafa, maniQayd, arbaa]
  | ism => simp [mukhalafa, maniQayd] at h
  | innama => simp [mukhalafa, maniQayd] at h
  | shart | ghaya => cases a <;> cases u <;> simp_all [mukhalafa, maniQayd, arbaa]

/-- مفهومُ الصفة التزامٌ بالعلّيّة (س536، س538) — `Dalalat.mufhim` تعريفُه هذا الالتزام. نتيجةٌ مباشرة. -/
theorem sifa_iltizam (w : Dalalat.Wasf) (a u : Bool) (s : String) (m : MafhumUsul)
    (h : mukhalafa (.sifa w) a u s = .yumal m) :
    Dalalat.dalala true w.m ["العلية"] = some .iltizam := by
  have := (hasr_arbaa _ _ _ _ _ h).2.1 w rfl
  simpa [Dalalat.mufhim] using this

/-- الأغلبُ أو النصُّ المعطِّل لا يُعمل معه بمفهومٍ لأيّ قيد (س553، س554). نتيجةٌ مباشرة. -/
theorem mani_yusqit (q : Qayd) (a u : Bool) (s : String) (h : a = true ∨ u = true) :
    ∀ m, mukhalafa q a u s ≠ .yumal m := by
  intro m hm
  have := hasr_arbaa _ _ _ _ _ hm
  rcases h with h | h <;> simp_all

/-- «يُعمل به» ⟺ لا مانعَ من الثلاثة. لكلّ مدخل. (ومنه استنتاجٌ لا مبرهنة: أيُّ ترتيبٍ للموانع الثلاثة يعطي
العملَ نفسَه، لأنّ الشرط عطفُها.) -/
theorem yumal_iff (q : Qayd) (a u : Bool) (s : String) :
    (∃ m, mukhalafa q a u s = .yumal m) ↔ (maniQayd q = none ∧ a = false ∧ u = false) := by
  constructor
  · rintro ⟨m, hm⟩
    unfold mukhalafa at hm
    split at hm
    · cases hm
    · rename_i hq
      cases a <;> cases u <;> simp_all
  · rintro ⟨hq, rfl, rfl⟩
    exact ⟨⟨.mukhalafa, s⟩, by simp [mukhalafa, hq]⟩

/-- مفهومُ الاسم لا يُعمل به (س550). تعريفيّ. -/
theorem la_mafhum_ism (a u : Bool) (s : String) : mukhalafa .ism a u s = .layumal .ism := rfl

/-! ## ٣. الشواهد بأسطرها

الأوصافُ مُرمَّزةٌ بقراءة البنّاء (أجزاءُ المسمّى ولازمُه)، والمعاني بلفظ سطرها. -/

/-- السائمة (س536): ذاتٌ وسوم، والعلّيّةُ لازمٌ ذهنيّ (ترميزُ البنّاء). -/
def saima : Dalalat.Wasf := ⟨"السائمة", .mushtaq, ⟨["ذات", "السوم"], ["العلية"], []⟩, true⟩
/-- الربيبةُ في الحجر (س553: «إذ الغالب أن الربيبة إنما تكون في الحجر») — وصفٌ خرج مخرجَ الأغلب. -/
def fiHujur : Dalalat.Wasf := ⟨"في الحجر", .mushtaq, ⟨["ذات", "الحجر"], ["العلية"], []⟩, true⟩
/-- «أَضْعَافًا مُضَاعَفَةً» (س554) — وصفٌ عطّل مفهومَه نصٌّ آخر. -/
def adafan : Dalalat.Wasf := ⟨"أضعافاً مضاعفة", .mushtaq, ⟨["ذات", "التضعيف"], ["العلية"], []⟩, true⟩

/-- **الشواهد** (على الشاهد؛ المعاني بلفظ أسطرها): السائمة (س536) والشرط (س541) والغاية (س546) والعدد بسياقه (س548)
يُعمل بها بمعانيها بلفظ أسطرها؛ و«القرشين» بلا سياق (س548)، و«زيد قائم» (س550)، والسائل والمحتجر (س551،
`Dalalat.sail`، `Dalalat.muhtajir`)، و«إنما» (س552)، و«في الحجر» (س553)، و«أضعافاً مضاعفة» (س554) لا يُعمل بها، كلٌّ
بمانعه، ولا معنى لها في محلّ السكوت (`""`). -/
theorem shawahid :
    mukhalafa (.sifa saima) false false "عدم الوجوب في المعلوفة" =
      .yumal ⟨.mukhalafa, "عدم الوجوب في المعلوفة"⟩ ∧
    mukhalafa .shart false false "عدم وجوب الإنفاق بعدم الحمل" =
      .yumal ⟨.mukhalafa, "عدم وجوب الإنفاق بعدم الحمل"⟩ ∧
    mukhalafa .ghaya false false "بعد دخول الليل لا صيام" =
      .yumal ⟨.mukhalafa, "بعد دخول الليل لا صيام"⟩ ∧
    mukhalafa (.adad true) false false "تحـريم ما زاد على المائة" =
      .yumal ⟨.mukhalafa, "تحـريم ما زاد على المائة"⟩ ∧
    mukhalafa (.adad false) false false "" = .layumal .adadBilaSiyaq ∧
    mukhalafa .ism false false "" = .layumal .ism ∧
    mukhalafa (.sifa Dalalat.sail) false false "" = .layumal .wasfGhayrMufhim ∧
    mukhalafa (.sifa Dalalat.muhtajir) false false "" = .layumal .wasfGhayrMufhim ∧
    mukhalafa .innama false false "" = .layumal .innama ∧
    mukhalafa (.sifa fiHujur) true false "" = .layumal .aghlab ∧
    mukhalafa (.sifa adafan) false true "" = .layumal .muattil := by decide

/-! ## ٤. المادّة ٢٤: `MafhumUsul` ليس رتبةً، والشاهدُ شاهدٌ له بعينه -/

/-- مودَعُ الشواهد: كلُّ شهادةٍ مقرونةٌ بالمفهوم الذي تشهد له. -/
abbrev Mudaa := List (MafhumUsul × Naql.Shahada)

/-- شهاداتُ مفهومٍ بعينه في المودَع. -/
def shuhudFor (d : Mudaa) (m : MafhumUsul) : List Naql.Shahada :=
  (d.filter (fun p => p.1 == m)).map (·.2)

theorem mem_shuhudFor {d : Mudaa} {m : MafhumUsul} {s : Naql.Shahada} :
    s ∈ shuhudFor d m ↔ (m, s) ∈ d := by
  simp only [shuhudFor, List.mem_map, List.mem_filter, beq_iff_eq]
  constructor
  · rintro ⟨⟨m', s'⟩, ⟨hd, hm⟩, rfl⟩; simp at hm; subst hm; exact hd
  · intro h; exact ⟨(m, s), ⟨h, rfl⟩, rfl⟩

/-- شاهدُ واقعٍ له: شهادةٌ له بعينه، بالحسّ، من الواقع المختوم. -/
def waqiFor (d : Mudaa) (m : MafhumUsul) : Bool :=
  (shuhudFor d m).any (fun s => s.tariq == .hiss && s.mawda == .waqiMakhtum)

/-- المستخرَجُ منطوقًا ثلاثيًّا: المعمولُ به معيَّن، وما لا يُعمل به «لا حكم». -/
def toMantuq : Hukm → Iqtiran.Mantuq MafhumUsul
  | .yumal m => .muayyan m
  | .layumal _ => .laHukm

/-- رتبتُه بمسار الواقع: `Iqtiran.martaba` بشاهدٍ من المودَع. -/
def martabaWaqi (d : Mudaa) (h : Hukm) : Iqtiran.Martaba :=
  Iqtiran.martaba (waqiFor d) (toMantuq h)

/-- **لا رتبةَ «مفهوم» بلا شاهد واقعٍ له بعينه** (المادّة ٢٤). لكلّ مودَعٍ وحكم. -/
theorem la_martaba_bila_shahid (d : Mudaa) (h : Hukm) (hm : martabaWaqi d h = .mafhum) :
    ∃ m s, h = .yumal m ∧ (m, s) ∈ d ∧ s.tariq = .hiss ∧ s.mawda = .waqiMakhtum := by
  unfold martabaWaqi at hm
  obtain ⟨x, hx, hs⟩ := Iqtiran.la_mafhum_bila_waqi _ _ hm
  cases h with
  | layumal _ => cases hx
  | yumal m =>
    simp only [toMantuq, Iqtiran.Mantuq.muayyan.injEq] at hx
    subst hx
    obtain ⟨s, hsm, hp⟩ := List.any_eq_true.mp hs
    simp only [Bool.and_eq_true, beq_iff_eq] at hp
    exact ⟨_, s, rfl, mem_shuhudFor.mp hsm, hp.1, hp.2⟩

/-- بلا مودَعٍ: المعمولُ به «معلومة»، وما لا يُعمل به «من حيث هي». تعريفيّ. -/
theorem bila_mudaa (h : Hukm) :
    martabaWaqi [] h = (match h with | .yumal _ => .maluma | .layumal _ => .minHaythuHiya) := by
  cases h <;> rfl

/-- **شاهدُ غيره لا يرفعه**: إن لم تكن في المودَع شهادةٌ له بعينه فرتبتُه «معلومة». لكلّ مودَع. -/
theorem shahid_ghayrih_la_yarfa (d : Mudaa) (m : MafhumUsul) (h : ∀ s, (m, s) ∉ d) :
    martabaWaqi d (.yumal m) = .maluma := by
  have : waqiFor d m = false := by
    unfold waqiFor
    cases hc : (shuhudFor d m).any (fun s => s.tariq == .hiss && s.mawda == .waqiMakhtum) with
    | false => rfl
    | true =>
      obtain ⟨s, hsm, _⟩ := List.any_eq_true.mp hc
      exact absurd (mem_shuhudFor.mp hsm) (h s)
  simp [martabaWaqi, toMantuq, Iqtiran.martaba, this]

/-- رتبتُه بمسار الشهادة: ما لا يُعمل به «من حيث هي»، وما يُعمل به يُحكم بجسرٍ من `Naql` على شهاداته هو. -/
def hukmNaql (jisr : List Naql.Shahada → Naql.Hukm) (d : Mudaa) : Hukm → Naql.Hukm
  | .yumal m => jisr (shuhudFor d m)
  | .layumal _ => .minHaythuHiya

/-- **لا «مفهوم» بجسر الوضع بلا شهادةٍ له بعينه كافية** (المادّة ٢٤ وتعديل ADR ١٠٤). لكلّ مودَعٍ وحكم. -/
theorem la_mafhum_wad_bila_shahid (t : List Naql.Shahada → Bool) (d : Mudaa) (h : Hukm)
    (r : Naql.Rutba) (s : Naql.Shahada) (ss : List Naql.Shahada)
    (hm : hukmNaql (Naql.jisrWad t) d h = .mafhum r s ss) :
    ∃ m, h = .yumal m ∧ (m, s) ∈ d ∧ Naql.kafiNaql (s :: ss) = true := by
  cases h with
  | layumal _ => cases hm
  | yumal m =>
    simp only [hukmNaql, Naql.jisrWad] at hm
    obtain ⟨hs, _, hk⟩ := Naql.mafhum_bishahid _ _ _ _ r s ss hm
    exact ⟨m, rfl, mem_shuhudFor.mp hs, hk⟩

/-- وبجسر الواقع (`Naql.jisrWaqi`): لكلّ مودَعٍ وحكم. -/
theorem la_mafhum_waqi_bila_shahid (d : Mudaa) (h : Hukm)
    (r : Naql.Rutba) (s : Naql.Shahada) (ss : List Naql.Shahada)
    (hm : hukmNaql Naql.jisrWaqi d h = .mafhum r s ss) :
    ∃ m, h = .yumal m ∧ (m, s) ∈ d := by
  cases h with
  | layumal _ => cases hm
  | yumal m =>
    simp only [hukmNaql, Naql.jisrWaqi] at hm
    obtain ⟨hs, _, _⟩ := Naql.mafhum_bishahid _ _ _ _ r s ss hm
    exact ⟨m, rfl, mem_shuhudFor.mp hs⟩

/-- **شاهدٌ لمفهومٍ آخر لا يرفع هذا**: على الشاهد — شهادةُ حسٍّ من الواقع المختوم لـ«عدم الوجوب في المعلوفة»
لا تجعل «بعد دخول الليل لا صيام» مفهومًا، وتجعل صاحبَها مفهومًا. -/
-- شهادةٌ مصنوعةٌ للبرهان، لا من واقعٍ مختوم.
def shahidMithal : Naql.Shahada := ⟨"مثال", "مثال", .hiss, .waqiMakhtum, 0⟩

theorem shahid_li_ghayrih :
    martabaWaqi [(⟨.mukhalafa, "عدم الوجوب في المعلوفة"⟩, shahidMithal)]
        (.yumal ⟨.mukhalafa, "بعد دخول الليل لا صيام"⟩) = .maluma ∧
    martabaWaqi [(⟨.mukhalafa, "عدم الوجوب في المعلوفة"⟩, shahidMithal)]
        (.yumal ⟨.mukhalafa, "عدم الوجوب في المعلوفة"⟩) = .mafhum := by decide

/-- وبمسار الوضع كذلك (على الشاهد): شهادةُ وضعٍ لـ«عدم الوجوب في المعلوفة» لا تجعل غيرَه مفهومًا، وتجعله هو مفهومًا ظنّيًّا. -/
-- شهادةٌ مصنوعةٌ للبرهان، لا من مودَع وضعٍ مختوم.
def wadMithal : Naql.Shahada := ⟨"مثال", "مثال", .naql, .wad, 0⟩

theorem shahid_li_ghayrih_naql :
    hukmNaql (Naql.jisrWad (fun _ => false)) [(⟨.mukhalafa, "عدم الوجوب في المعلوفة"⟩, wadMithal)]
        (.yumal ⟨.mukhalafa, "بعد دخول الليل لا صيام"⟩) = .maluma [] ∧
    hukmNaql (Naql.jisrWad (fun _ => false)) [(⟨.mukhalafa, "عدم الوجوب في المعلوفة"⟩, wadMithal)]
        (.yumal ⟨.mukhalafa, "عدم الوجوب في المعلوفة"⟩) = .mafhum .zanni wadMithal [] := by decide

/-- المراسي: (الموضع، سطرُ ج3 بترقيم الغانم، العبارةُ بلفظها). يطابقها `tests/test_mantuq_mafhum.py`. -/
def marasi : List (String × Nat × String) :=
  [ ("mantuq", 516, "والمنطوق هو ما دل عليه اللفظ قطعاً في محل النطق"),
    ("mafhum", 518, "المفهوم هو ما فهم من اللفظ في غير محل النطق"),
    ("iqtida", 520, "بأن يكون شرطاً للمعنى المدلول عليه بالمطابقة"),
    ("tanbih", 522, "إنما تقع فيما يدل على العلية"),
    ("ishara", 524, "لم يكن مقصوداً من الكلام"),
    ("muwafaqa", 526, "في محل السكوت موافقاً لمدلوله في محل النطق"),
    ("tabi", 528, "بأن لا يكون شرطاً للمعنى المطابقي بل تابعاً له"),
    ("awlawiyya", 528, "فإن اشتراط الأولوية في مفهوم الموافقة لا معنى له"),
    ("qiyas", 532, "على أنه لا توجد دلالة قياسية وإنما يوجد قياس"),
    ("mukhalafa", 534, "كمفهوم الصفة، ومفهوم الشرط، ومفهوم الغاية، ومفهوم العدد"),
    ("sifa", 536, "وشرطه أن تكون تلك الصفة وصفاً مفهماً"),
    ("shart", 541, "فإنه يدل على نفي الحكم عند عدم تحقق الشرط"),
    ("ghaya", 546, "فإنه يدل على نفي الحكم فيما بعد الغاية"),
    ("adad", 548, "يدل على أن ما عدا ذلك العدد بخلافه"),
    ("adadSiyaq", 548, "والثاني أن يدل سياق الكلام على نفي الحكم عن غير العدد"),
    ("ism", 550, "فلا يعمل بمفهوم الاسم مطلقاً"),
    ("ghayrMufhim", 551, "وكذلك لا يعمل بمفهوم الوصف غير المفهم"),
    ("innama", 552, "وكذلك لا يعمل بمفهوم «إنما»"),
    ("aghlab", 553, "لخروجه مخرج الأعم الأغلب لا مفهوم له"),
    ("muattil", 554, "إذا ورد نص من الكتاب أو السنة يعطله"),
    ("hasr", 555, "فمفهوم المخالفة محصور في الأصناف الأربعة ليس غير") ]

/-- معاني الشواهد المعمول بها بسطرها، وألفاظُ الشواهد المرفوضة بسطرها: يطابقها الاختبار بلفظها في سطرها. -/
def maaniShawahid : List (Nat × String) :=
  [ (536, "عدم الوجوب في المعلوفة"), (541, "عدم وجوب الإنفاق بعدم الحمل"), (546, "بعد دخول الليل لا صيام"),
    (548, "تحـريم ما زاد على المائة") ]

def alfazMarfuda : List (Nat × String) :=
  [ (548, "القرشين"), (550, "زيد قائم"), (551, "للسائل"), (551, "لمحتجر"), (552, "إنما"), (553, "في الحجر"),
    (554, "أضعافاً مضاعفة") ]

end A116.MantuqMafhum
