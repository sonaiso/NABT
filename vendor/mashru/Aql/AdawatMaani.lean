/-
  Aql/AdawatMaani.lean — أدواتُ المعاني بوّاباتِ المنطق: الواو (AND)، أو بشِقّيها الإباحةُ (OR) والتخييرُ
  (XOR)، الواوُ مع «لا» (NOR)، والشرطُ النحويّ إن/لو (IF…THEN) — على طريقة Aql/SababShartMani.lean
  (PR #25: السببُ والشرطُ والمانعُ)، وفوق ركنِ الواقع في Aql/Aqliyya.lean.

  المناسبة: طلبُ المالك في الجلسة 2026-10-17: «أدواتُ المعاني بوّاباتُ المنطق، وتخضعُ لسببٍ وشرطٍ ومانعٍ:
  AND، OR، NOR، XOR، IF…THEN، مع PR 25». هذا الملفّ يصوغ خمسَ بوّاباتٍ من أدواتِ العطفِ والشرط عند
  النحويّين Prop-structures على عالَمِ شواهدَ، على نسق Shart/Mani في SababShartMani.lean تمامًا، ويصل
  بوّابةَ IF…THEN تحديدًا بذلك الملفّ نفسِه (شرطٌ جديدٌ، `ShartNahwi`، يُبرهَن استقلالُه عن `Shart` الأصوليّ).

  **السند** (كلاهما مختومٌ في mudaat/sijill.json؛ نسختان نصّيّتان OpenITI قُرئتا بأداةٍ في هذه الجلسة
  وبصمتاهما مطابقتان للمسجَّل: مغني اللبيب لابن هشام (ت761هـ)، والجنى الداني للمرادي (ت749هـ)؛ أرقامُ
  الأسطر من النسخة المحوَّلة نصًّا في هذه الجلسة، كسابقتها في SababShartMani.lean):

  * الواو العاطفة، الجمعُ المطلق — مغني س8201–8204: «الواو المفردة انتهى مجموع ما ذكر من أقسامها إلى
    خمسة عشر... الأول العاطفة ومعناها مطلق الجمع».
  * أو، الثالثُ (التخيير) والرابعُ (الإباحة) — مغني س1331–1344: «والثالث التخيير وهي الواقعة بعد الطلب
    وقبل ما يمتنع فيه الجمع... والرابع الإباحة وهي الواقعة بعد الطلب وقبل ما يجوز فيه الجمع»؛ الجنى
    س2421–2423 (أدقّ عبارة): «الثالث: التخيير... الرابع: الإباحة... والفرق بينهما جواز الجمع في الإباحة،
    ومنع الجمع في التخيير».
  * الواو مقترنةً بـ«لا» بعد نفيٍ — مغني س8219–8221 (وتتمّة الموضوع حتّى س8224): «والثالث اقترانها ب لا إن
    سبقت بنفي ولم تقصد المعية... ولتفيد أن الفعل منفي عنهما في حالتي الاجتماع والافتراق» — ضُبط مدى
    الاستشهاد (كان «8219–8224» شاملًا ثلاثة أسطر غير مقتبَسة حرفيًّا) بمراجعة `murajii` المستقلّة 2026-10-17.
  * إنْ الشرطيّة — مغني س357–359: «أحدها أن تكون شرطية نحو {إن ينتهوا يغفر لهم}».
  * لو، التفريقُ بين المساوي والأعمّ — مغني س5952–5957: «إن كان [الجواب] مساويا للشرط في العموم... لزم
    انتفاؤه لأنه يلزم من انتفاء السبب المساوي انتفاء مسببه وإن كان أعم... فلا يلزم انتفاؤه» (شاهداه
    في النصّ نفسِه: الشمسُ/النهارُ مساويان، والشمسُ/الضوءُ أعمّ؛ ومغني نفسُه، س5952–5953، يقرّر المعنى
    بعبارته الخاصّة: «ولا دلالة لها على امتناع الجواب ولا على ثبوته»)؛ والجنى س2969–2973، تعريفُ ابن
    مالك الثلاثةُ لـ«لو» — أدقّها: «لو حرف شرط يقتضي نفي ما يلزم لثبوته ثبوت غيره» (التسهيل)، مع تقريره
    صريحًا في الجنى (س2963): «ولا تدل على امتناع الجواب، في نفس الأمر، ولا ثبوته».

  **تنبيهٌ دستوريّ (رأي البنّاء لا نقلًا، كتحذير CLAIM_ABOVE_ITS_SUPPORT في CLAUDE.md)**: «الشرط» في
  اصطلاح الأصوليّين (`SababShartMani.Shart`؛ لازمٌ من العدم غيرُ كافٍ من الوجود، ج3 س243) غيرُ «الشرط» في
  اصطلاح النحويّين على إنْ/لو (كافٍ لجوابه، ولا يلزم من عدمه عدمُ الجواب بالضرورة) — اتّفاقُ اللفظِ لا
  اتّفاقُ المعنى. هذا الملفّ يسمّي الثاني `ShartNahwi` ولا يَدمجه بـ`Shart`، ويبرهن استقلالَهما (§٥) بدل
  افتراضِه.

  الوسم (صُحّح 2026-10-17 بمراجعة `murajii` المستقلّة؛ الترويسةُ الأولى كانت تسوّي الصنفين التاليين تحت
  «مبرهن» واحدة): تسعٌ من السبعَ عشرةَ مبرهنةٌ عامّةٌ («مبرهن» بحكم الدستور، مُكمَّمةٌ كُلِّيًّا لا على شاهدٍ
  ثابت) — `jam_yushhid_ibaha`، `jam_yunafi_takhyir`، `ibaha_tunaqid_takhyir`،
  `takhyir_maa_asl_alaw_yuaddi_ila_xor`، `xor_yastalzim_al_asl`، `nafy_aljihatayn_yusawi_nafy_alaw`،
  `nor_yastalzim_nand`، `nand_la_yastalzim_nor`، `musawi_yulzim_nafy_altarafayn` (الأخيرةُ منها حالةٌ
  حدّيّةٌ: قضيّةٌ مغلقةٌ عن True/False بعينهما لا عن متغيّرين عامّين، لكنّها لا تستعمل `decide` فتبقى هنا
  بحرف تعريف «مبرهن على الشاهد»). والثماني الباقيةُ `decide`/`cases ... <;> decide` على نوعٍ صغيرٍ
  مبنيٍّ («مبرهنٌ على الشاهد» لا «مبرهن»، بحكم الدستور نفسِه؛ `Mawsua.Wasm.tartib`): `takhyirIkhtiyar`،
  `ibahaMujalasa`، `wudu_shart_usuli_la_nahwi`، `shartNahwiDaw`، `daw_la_yakfi_lilshams`،
  `shams_intifa_la_yulzim_daw_intifa`، `shartNahwiNahar`، `shartNahwiNaharAksan`. بلا اعتمادٍ على سند
  الكتابين في البرهان نفسِه (السندُ تسميةٌ وسياقٌ لا مقدّمة، كسابقَيها Aql/Badiha.lean
  وAql/SababShartMani.lean). الكتابان مختومان، ومع ذلك لا نتيجةَ هنا توسَم «مطابَق»: المطابقةُ بين تصنيف
  النحويّين الخماسيّ وبوّاباتِ المنطق الحديثةِ الخماسيّةِ رأيُ البنّاء في القراءة، لا استخراجَ جدولٍ آليّ من
  مودَع. بلا sorry ولا axiom ولا native_decide.
-/
import Aql.SababShartMani

namespace AdawatMaani
open Aql
open SababShartMani

/-! ## ٠. أداةٌ: التناقض الثنائيّ (خارج Prop الأساسيّ؛ لا Mathlib في هذا المشروع) -/

/-- **التناقضُ الثنائيّ**: صدقُ أحدِهما وكذبُ الآخر، لا هما معًا ولا نقيضاهما معًا. -/
def XorP (p q : Prop) : Prop := (p ∧ ¬ q) ∨ (¬ p ∧ q)

/-! ## ١. الإباحةُ والتخييرُ: بنيتاهما أوّلًا (أو، مغني س1331–1344، الجنى س2421–2423) -/

/-- **الإباحةُ**: جوازُ الجمع بين الطرفين — شاهدٌ واحدٌ على الأقلّ يصدق فيه كِلاهما («جالس الحسن أو
ابن سيرين»، الجنى س2422؛ «جواز الجمع في الإباحة»، س2423). -/
structure Ibaha (ω : Type) (a b : ω → Prop) : Prop where
  yajuzu_aljam : ∃ w, a w ∧ b w

/-- **التخييرُ**: منعُ الجمع بين الطرفين على كلّ شاهد («خذ دينارا أو ثوبا»، الجنى س2421؛ «ومنع الجمع في التخيير»،
س2423). -/
structure Takhyir (ω : Type) (a b : ω → Prop) : Prop where
  yamnau_aljam : ∀ w, ¬ (a w ∧ b w)

/-! ## ٢. الواوُ: الجمعُ المطلق (AND) — مغني س8201–8204

لا بنيةَ جديدة هنا: صدقُ المجموع هو `∧` نفسُه بلا زيادة («معناها مطلق الجمع»، س8204). المبرهنتان
التاليتان تصلانه بالإباحة والتخيير أعلاه، لا تُعرِّفانه من جديد. -/

/-- **الجمعُ الفعليّ شاهدٌ على الإباحة**: إن صدق الطرفان معًا على شاهدٍ، فجوازُ جمعِهما واقعٌ، لا مجرَّدَ
دعوى. -/
theorem jam_yushhid_ibaha {ω : Type} {a b : ω → Prop} (w : ω) (h : a w ∧ b w) :
    Ibaha ω a b :=
  ⟨w, h⟩

/-- **الجمعُ الفعليّ ينافي كونَ الأداة للتخيير**: إذ لو كان التخييرُ (منعُ الجمع) جاريًا بين الطرفين، لم
يصحّ صدقُهما معًا على أيّ شاهد — وهذا الشاهدُ يصدقان فيه معًا. -/
theorem jam_yunafi_takhyir {ω : Type} {a b : ω → Prop} (w : ω) (h : a w ∧ b w) :
    ¬ Takhyir ω a b :=
  fun ht => ht.yamnau_aljam w h

/-! ## ٣. أو: التفريعُ على الإباحة والتخيير (OR/XOR) — تكملة §١ -/

/-- **الإباحةُ والتخييرُ متناقضان على الطرفين نفسِهما**: هذا نصُّ الفرق بينهما في الجنى الداني (س2423)
مبرهنًا، لا مجرَّدَ عبارة. -/
theorem ibaha_tunaqid_takhyir {ω : Type} {a b : ω → Prop} (hi : Ibaha ω a b) (ht : Takhyir ω a b) :
    False :=
  let ⟨w, haw, hbw⟩ := hi.yajuzu_aljam
  ht.yamnau_aljam w ⟨haw, hbw⟩

/-- **التخييرُ، مع صدقِ أصلِ «أو» على شاهدٍ، يُنتج التناقضَ الثنائيّ**: «منع الجمع» زائدًا كونَ أحدِهما
واقعًا يُساوي بوّابةَ XOR بعينها — هذا ما تزيده «التخيير» على معنى «أو» الأصليّ (الشكّ/الإبهام، مغني
س1326–1330). -/
theorem takhyir_maa_asl_alaw_yuaddi_ila_xor {ω : Type} {a b : ω → Prop} (ht : Takhyir ω a b)
    (w : ω) (hor : a w ∨ b w) : XorP (a w) (b w) :=
  hor.elim
    (fun ha => Or.inl ⟨ha, fun hb => ht.yamnau_aljam w ⟨ha, hb⟩⟩)
    (fun hb => Or.inr ⟨fun ha => ht.yamnau_aljam w ⟨ha, hb⟩, hb⟩)

/-- **XOR يستلزم أصلَ «أو»**: التخصيصُ لا يُسقط الأصل — من صدق أحدهما حصرًا يصدق أحدهما. -/
theorem xor_yastalzim_al_asl {p q : Prop} (h : XorP p q) : p ∨ q :=
  h.elim (fun hp => Or.inl hp.1) (fun hq => Or.inr hq.2)

/-- شاهدٌ مبنيّ للتخيير على مثال يومين لا يُجمعان: الجمعة والسبت. -/
inductive HalIkhtiyar | laYawm | yawmAljumah | yawmAlsabt
deriving DecidableEq

def HalIkhtiyar.jumah : HalIkhtiyar → Bool
  | .laYawm => false
  | .yawmAljumah => true
  | .yawmAlsabt => false

def HalIkhtiyar.sabt : HalIkhtiyar → Bool
  | .laYawm => false
  | .yawmAljumah => false
  | .yawmAlsabt => true

/-- التخييرُ شاهدًا: لا شاهدَ فيه اليومان معًا، بالبناء. -/
theorem takhyirIkhtiyar : Takhyir HalIkhtiyar (fun h => h.jumah = true) (fun h => h.sabt = true) where
  yamnau_aljam := by intro w; cases w <;> decide

/-- شاهدٌ مبنيّ للإباحة: «جالس الحسن أو ابن سيرين» — يُجمعان. -/
inductive HalMujalasa | laAhad | alHasanFaqat | ibnSirinFaqat | kilahuma
deriving DecidableEq

def HalMujalasa.hasan : HalMujalasa → Bool
  | .laAhad => false
  | .alHasanFaqat => true
  | .ibnSirinFaqat => false
  | .kilahuma => true

def HalMujalasa.sirin : HalMujalasa → Bool
  | .laAhad => false
  | .alHasanFaqat => false
  | .ibnSirinFaqat => true
  | .kilahuma => true

/-- الإباحةُ شاهدًا: شاهدٌ واحدٌ فيه الاثنان معًا (`kilahuma`)، بالبناء. -/
theorem ibahaMujalasa : Ibaha HalMujalasa (fun h => h.hasan = true) (fun h => h.sirin = true) where
  yajuzu_aljam := ⟨.kilahuma, by decide, by decide⟩

/-! ## ٤. الواوُ مع «لا»: NOR — مغني س8219–8221 -/

/-- **نفيُ الواو**: نفيُ المجموع في «حالتي الاجتماع والافتراق» معًا يُساوي نفيَ «أو» — هذا نصُّ مغني
«منفي عنهما في حالتي الاجتماع والافتراق» (س8221) مبرهَنًا. -/
theorem nafy_aljihatayn_yusawi_nafy_alaw {p q : Prop} : (¬ p ∧ ¬ q) ↔ ¬ (p ∨ q) :=
  ⟨fun h hor => hor.elim h.1 h.2,
   fun h => ⟨fun hp => h (Or.inl hp), fun hq => h (Or.inr hq)⟩⟩

/-- **نفيُ الواو أقوى من نفي الاجتماع وحدَه**: NOR يستلزم NAND. -/
theorem nor_yastalzim_nand {p q : Prop} (h : ¬ p ∧ ¬ q) : ¬ (p ∧ q) :=
  fun hpq => h.1 hpq.1

/-- **والعكسُ لا يلزم**: شاهدٌ بسيطٌ (True, False) يصدق فيه نفيُ الاجتماع (NAND) ويكذب فيه نفيُ الواو
(NOR) — هذا سببُ احتياج النحويّين إلى التنصيص على «حالتي الاجتماع والافتراق» معًا، لا الاجتماعِ فقط. -/
theorem nand_la_yastalzim_nor : ¬ (True ∧ False) ∧ ¬ (¬ True ∧ ¬ False) :=
  ⟨fun h => h.2, fun h => h.1 trivial⟩

/-! ## ٥. الشرطُ النحويّ: إنْ/لو (IF…THEN) — مغني س357–359، 5899–5967؛ الجنى س2939–2978 -/

/-- **الشرطُ النحويّ**: كفايةُ الشرط لجوابه على كلّ شاهد — عكسُ اتّجاه `SababShartMani.Shart` الأصوليّ
(الذي لزومُه من العدم، لا من الوجود، ج3 س243). سندُ هذا الاتّجاه: تعريفُ ابن مالك لـ«لو» في الجنى
(س2970–2971): «حرف شرط يقتضي نفي ما يلزم لثبوته ثبوت غيره» — شرطٌ يُثبَت لثبوته ثبوتُ جوابه. -/
structure ShartNahwi (ω : Type) (shart jawab : ω → Prop) : Prop where
  kafi_lijawabihi : ∀ w, shart w → jawab w

/-- **الشرطُ الأصوليّ (وضوءٌ/صلاةٌ، مبرهنٌ في PR #25، `shartWudu`) لا يُنتج الشرطَ النحويّ على الاتّجاه
نفسِه**: الوضوءُ لا يكفي للصلاة — نفسُ شاهد `wuduBilaSalaa` الذي أثبت `la_yalzam_min_wujud` هناك مقروءًا
هنا بلغة الكفاية. -/
theorem wudu_shart_usuli_la_nahwi :
    ¬ ShartNahwi HalWudu (fun h => h.wudu = true) (fun h => h.salaa = true) :=
  fun h => absurd (h.kafi_lijawabihi .wuduBilaSalaa (by decide)) (by decide)

/-- شاهدٌ جديدٌ: الشمسُ والضوءُ — «لو كانت الشمس طالعة كان الضوء موجودا» (مغني س5955–5956) حالةٌ «أعم»:
شاهدٌ ثالثٌ فيه ضوءٌ بلا شمسٍ (سراجٌ). -/
inductive HalDaw | laShamsWalaDaw | shamsWaDaw | laShamsWaDawSiraj
deriving DecidableEq

def HalDaw.shams : HalDaw → Bool
  | .laShamsWalaDaw => false
  | .shamsWaDaw => true
  | .laShamsWaDawSiraj => false

def HalDaw.daw : HalDaw → Bool
  | .laShamsWalaDaw => false
  | .shamsWaDaw => true
  | .laShamsWaDawSiraj => true

/-- الشمسُ تكفي للضوء، بالبناء: لا شاهدَ فيه شمسٌ بلا ضوء. -/
theorem shartNahwiDaw : ShartNahwi HalDaw (fun h => h.shams = true) (fun h => h.daw = true) where
  kafi_lijawabihi := by intro w; cases w <;> decide

/-- **ولا تنعكس الكفايةُ**: الضوءُ لا يكفي شرطًا للشمس — سراجٌ بلا شمس. -/
theorem daw_la_yakfi_lilshams :
    ¬ ShartNahwi HalDaw (fun h => h.daw = true) (fun h => h.shams = true) :=
  fun h => absurd (h.kafi_lijawabihi .laShamsWaDawSiraj (by decide)) (by decide)

/-- **ولا يلزم من انتفاء الشمس انتفاءُ الضوء**: هذا عينُ «أعم» في النصّ (س5956: «فلا يلزم انتفاؤه»)، وهو
أيضًا ما يُسقط `SababShartMani.Shart` الأصوليّ بين الشمس والضوء على اتّجاهه (`lazim_min_adam`). -/
theorem shams_intifa_la_yulzim_daw_intifa :
    ¬ (∀ w : HalDaw, w.shams = false → w.daw = false) :=
  fun h => absurd (h .laShamsWaDawSiraj (by decide)) (by decide)

/-- **الحالةُ «المساوي»**: إذا كفى كلٌّ من الوصفين للآخر (شرطٌ نحويٌّ في الاتّجاهين)، فانتفاءُ أحدهما
يلزمه انتفاءُ الآخر — مغني س5953–5954: «إن كان مساويا للشرط في العموم... لزم انتفاؤه». -/
theorem musawi_yulzim_nafy_altarafayn {ω : Type} {shart jawab : ω → Prop}
    (_h1 : ShartNahwi ω shart jawab) (h2 : ShartNahwi ω jawab shart) (w : ω) (hns : ¬ shart w) :
    ¬ jawab w :=
  fun hj => hns (h2.kafi_lijawabihi w hj)

/-- شاهدٌ: الشمسُ والنهارُ — حالةٌ «مساوٍ» (مغني س5962–5964: «ما يوجب فيه الشرع أو العقل انحصار
مسببية الثاني في سببية الأول... يلزم فيه من امتناع الأول امتناع الثاني قطعا»). عالمٌ بلا حالةٍ
ثالثة (بخلاف الضوء): لا نهارَ بلا شمسٍ، ولا شمسَ بلا نهار. -/
inductive HalNahar | laShamsWalaNahar | shamsWaNahar
deriving DecidableEq

def HalNahar.shams : HalNahar → Bool
  | .laShamsWalaNahar => false
  | .shamsWaNahar => true

def HalNahar.nahar : HalNahar → Bool
  | .laShamsWalaNahar => false
  | .shamsWaNahar => true

theorem shartNahwiNahar : ShartNahwi HalNahar (fun h => h.shams = true) (fun h => h.nahar = true) where
  kafi_lijawabihi := by intro w; cases w <;> decide

theorem shartNahwiNaharAksan :
    ShartNahwi HalNahar (fun h => h.nahar = true) (fun h => h.shams = true) where
  kafi_lijawabihi := by intro w; cases w <;> decide

end AdawatMaani
