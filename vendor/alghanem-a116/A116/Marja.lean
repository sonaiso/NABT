import A116.Fasl
import A116.MakharijIdgham

/-!
# مرجعُ المالك: القوانينُ الأربعة على البرج — الابتداءُ والوصلُ والفصلُ والوقف (ADR ١١٨)

**نصُّ المالك (2026-10-19 21:53 بتوقيت عمّان) كاملًا:** «جدول الكندي: لا يُبنى قبل أن ترفع صفحات الجدول من التحقيق،
وأن تقرّر نوع المودَع ومعنى «التجاور» الذي نقارن به. ابني جدولنا الخاص ابحث بعمق عن الكندي وما شابه ولكن ابني جدولنا
الخاص واجمع فيه قانون الابتداء وقانون الوصل وقانون الفصل وقانون الوقف  ليكون مرجع خاص بالمالك ومعتمده ونختمه كمرجع خاص
ويجب ان تراجع الليف في جذر المشروع للمخارج والصفات وحروف كل مخرج وترخيصها التدريجي اعمل بعمق» (بايتاتُه في
`docs/marja/khatm.json`).

**ما هو.** جدولٌ واحدٌ يجمع القوانينَ الأربعة على البرج «مخرجٌ ⊃ صفةٌ ⊃ حرفٌ ⊃ حالةٌ ⊃ موضع». أكثرُ أعمدته دوالُّ قائمةٌ
في الشجرة يركّبها هذا الملفُّ ويعدّها ويسمّيها، **وما كُتب هنا جديدًا تعيينُ البنّاء (م٢٢)**: `qablK` (أصنافُ السابق
بحالته، ومبرهنتُه `qablK_mada`)، وحكمُ الساكن بعد ساكنٍ وصلًا بشرط «للحامل متحرّكٌ مرخَّص» (`mutaharrikOf` يمثّله
بالفتحة)، والمُنشئ `yuskan`، وجمعُ الأحكام في `Hukm`. و«المرجعُ» هنا مرجعُ المالك الخاصّ، لا «مرجعٌ محجوب» بمعنى م١٢:
لا يُقاس عليه «مقيسًا».

* **الفصلُ** (`Fasl`، ADR ٧٤) بسببه ومانعه على **سُلَّم الباب**: المخرجُ ثمّ الجهرُ ثمّ الصنفُ (ما أسمّيه «الشدّةَ وما
  يقابلها»، بعبارتي لا بلفظ الكتاب) ثمّ الإطباق — وهذا ترتيبُ فقرات «هذا باب عدد الحروف العربية ومخارجها ومهموسها
  ومجهورها وأحوال مجهورها ومهموسها واختلافها» في الكتاب المختوم (JK006989: العنوانُ س21188–21189، المخارجُ س21209،
  المجهورةُ س21222، المهموسةُ س21224، الشديدةُ س21233، المطبقةُ س21252)؛ **وجعلُ ترتيب الفقرات ترتيبَ درجات الترخيص
  تعيينُ البنّاء** (م٢٢) لا نصّ. والمخارجُ الستّةَ عشر مخارجُ سيبويه (`placed16`) باختيار البنّاء، والدَّينُ
  `CANON_IS_JAZARI` (ADR ٧٣) قائم. لكلّ درجةٍ موانعُها، وكلُّ مانعٍ في درجةٍ مانعٌ فيما قبلها (`tadarruj`)، والدرجةُ
  الأخيرة تفصل (`fasl_akhir`)، وكلُّ صفةٍ من الثلاث لازمة (`mukhtamal_sibawayh`)؛ و**درجةُ ولادة الحرف** أوّلُ درجةٍ
  لا مانعَ له فيها (`wilada`).
* **الليف** (`Makharij.fiber`، ADR ٦٨): حروفُ كلّ مخرجٍ بترتيب الباب، والخياشيمُ ليفٌ فارغ؛ وولادةُ حروف الليف الواحد
  داخلَ درجات السُّلَّم (`lif_wilada`).
* **الابتداءُ والوصلُ والوقف** على الخانة في موضعها: الموضعُ تسعة — الابتداء، والوصلُ بعد كلّ حالةٍ من الأربع، والوقفُ بعد
  كلّ حالة — و**الدورُ** (`cv | v | c`) هو `Hadd.kindOne` بعينه (الموضعُ مشتقٌّ من الخانة وحالةِ ما قبلها، ADR ٢٢)،
  و**الحكمُ** من أزواج الجوار الستّة `Nizam.waslK` وزوجِ الوقف `Nizam.waqfK` على أصناف السابق الممكنة بحالته، ومن قيد
  الألف (`Alif`) وقانون «لا يُبتدأ بساكن ولا يُوقف على متحرّك» (`Boundary`). وما بقي فيه شرطٌ بعد الجوار يُسمّى شرطُه
  (قيدُ الحدّ `Hadd.haddB`: أوّلُ مثلين أو مدُّ الفرق `Hadd.isFarq`) ولا يُحسم في الخانة وحدَها. والوصلُ هنا خانةٌ بعد
  خانة: لا يمثّل التقاءَ الساكنين على الحدّ (`Iltiqa`) ولا القافيةَ العابرة (`MARJA_SEAM_ILTIQA_NOT_IN_LAW`).
* **عددُ الولادة n**: ‎n = 9·k + m‎ (k رقمُ الخانة في البرج `Jadwal.khanat`، وm رقمُ الموضع) تقابلٌ إلى ‎[0, 1044)‎
  (`n_tamam`) — عددُ الولادة في المرجع، غيرُ عدد الشهادة n في القانون الواحد.
* **والشاهدُ المبنيّ على قانون الأزواج**: الحكمُ يطابق `Hadd.strictB`/`strictPauseB` على كلماتٍ مبنيّةٍ للفحص («بَ…»،
  «بَبْ…»، «بَاْ…»؛ لا من مدوّنة) لكلّ خانة (`shahid_*`).

## الوسوم

**تعريفيٌّ البناء:** `sabab_take` (‏`rfl` في كلّ حالة)، `tadarruj` (لازمةٌ من بناء المفاتيح بادئاتٍ بعضُها لبعض)،
`dawr_kindOne`، والفرعُ المرفوض في `shahid_wasl_sakin`. **مبرهنٌ على الشاهد** (`decide` على الحروف التسعة والعشرين
والخانات الـ116 المعدودة): ما سواها، ومنه `tayin_akhir` (على `fasl_akhir`) و`mawadi_idx` و`qablK_mada`.
و**حكمُ الخانة الثلاثيُّ في هذا المرجع يتعيّن بالصنف** (`qanun_tadarruj`): الإطباقُ لا يغيّره، لأنّ `hukm` لا يرى من
الحرف إلّا كونَه ا أو و أو ي (المدّ وقيدُ الألف)، فأيُّ صفةٍ تفصل هذه الثلاثة تعيّنه. وليس هذا قولًا في الإدغام: الإطباقُ
في الكتاب داخلٌ في ترخيص الإدغام («ويقوي هذا أن الطاء وهي مطبقة لا تجعل مع التاء تاء خالصة لأنها أفضل منها بالإطباق …»،
س21410–21411). والمطابقةُ لنصّ الكتاب قراءةُ البنّاء: الحروفُ في الصفوف منقولةٌ في `Makharij` ومراسيها تُفحص في
`tests/test_makharij.py`.
-/

namespace A116.Marja

open A116 A116.Stages A116.Ladder A116.Nizam A116.Makharij A116.Fasl

/-! ## ١. سُلَّمُ الفصل بترتيب الباب -/

def b2n (b : Bool) : Nat := if b then 1 else 0

/-- **السببُ في الدرجة d**: المخرجُ، ثمّ الجهرُ، ثمّ الصنفُ من ثمانية (`mannerOf`؛ «الشدّةُ وما يقابلها» بعبارتي)، ثمّ
الإطباق. -/
def sabab : Nat → Char → List Nat
  | 0, c => [makhrajOf c]
  | 1, c => [makhrajOf c, b2n (jahrOf c)]
  | 2, c => [makhrajOf c, b2n (jahrOf c), mannerOf c]
  | _, c => [makhrajOf c, b2n (jahrOf c), mannerOf c, b2n (itbaqOf c)]

/-- **الدرجةُ d**: سببُها على الحروف التسعة والعشرين بترتيب المخارج. -/
def daraja (d : Nat) : Fasl Char (List Nat) := ⟨sabab d, placed16⟩

/-- السببُ في درجةٍ بادئةُ السبب في التي تليها (تعريفيّ: `rfl`). -/
theorem sabab_take (d : Nat) (hd : d < 3) (c : Char) : (sabab (d + 1) c).take (d + 1) = sabab d c := by
  rcases d with _ | _ | _ | d
  · rfl
  · rfl
  · rfl
  · omega

/-- **التدرّج**: ما فصل في درجةٍ لا يعود مانعًا في التي تليها — كلُّ مانعٍ في الدرجة ‎d+1‎ مانعٌ في الدرجة d (تعريفيُّ
البناء: لازمٌ من أنّ المفاتيحَ بادئاتٌ بعضُها لبعض). -/
theorem tadarruj (d : Nat) (hd : d < 3) (p : Char × Char) (h : p ∈ mani (daraja (d + 1))) :
    p ∈ mani (daraja d) := by
  obtain ⟨a, b⟩ := p
  obtain ⟨ha, hb, hne, he⟩ := (mem_mani (daraja (d + 1)) a b).1 h
  refine (mem_mani (daraja d) a b).2 ⟨ha, hb, hne, ?_⟩
  show sabab d a = sabab d b
  rw [← sabab_take d hd a, ← sabab_take d hd b]
  exact congrArg (List.take (d + 1)) he

/-- **الموانعُ بالدرجات** أزواجًا مرتّبة: المخرجُ وحدَه 40 (كـ`Fasl.makhraj_mani_count`)، ثمّ بالجهر 16، ثمّ بالصنف
ستّةٌ هي الأزواجُ الثلاثة بالاتّجاهين، ثمّ بالإطباق لا شيء. -/
theorem mani_darajat :
    (List.range 4).map (fun d => (mani (daraja d)).length) = [40, 16, 6, 0] := by
  decide +kernel

/-- موانعُ الدرجة الثانية هي تصادماتُ `Makharij.collisionsNoItbaq` بالاتّجاهين. -/
theorem mani_qabla_itbaq_lawla :
    mani (daraja 2) = collisionsNoItbaq.flatMap (fun p => [p, (p.2, p.1)]) := by
  decide +kernel

/-- **وبالصنف يبقى ما سمّاه الباب بعينه**: «ولولا الإطباق لصارت الطاء دالا والصاد سينا والظاء ذالا …» (س21258–21259) —
نتيجةُ `Makharij.lawla_itbaq`. -/
theorem mani_qabla_itbaq :
    mani (daraja 2) = [('ط', 'د'), ('د', 'ط'), ('س', 'ص'), ('ص', 'س'), ('ظ', 'ذ'), ('ذ', 'ظ')] := by
  rw [mani_qabla_itbaq_lawla, lawla_itbaq]
  rfl

/-- **الدرجةُ الأخيرة تفصل**، والتعيينُ فيها تامّ. -/
theorem fasl_akhir : fasl (daraja 3) = true := by decide +kernel

/-- التعيينُ في الدرجة الأخيرة تامٌّ على الحروف التسعة والعشرين (على الشاهد: بـ`fasl_akhir`). -/
theorem tayin_akhir : ∀ c ∈ placed16, tayin (daraja 3) (sabab 3 c) = some c :=
  fun c hc => tayin_of_fasl (daraja 3) fasl_akhir c hc

/-- مفتاحُ سيبويه: المخرجُ وما اختير من صفاته الثلاث (0 الجهر، 1 الصنف، 2 الإطباق). -/
def keyS (ss : List Nat) (c : Char) : List Nat :=
  makhrajOf c :: ss.map fun i => match i with
    | 0 => b2n (jahrOf c)
    | 1 => mannerOf c
    | _ => b2n (itbaqOf c)

/-- **الحدُّ الأدنى المكتمل على صفات الباب**: الثلاثُ تفصل، ولا تُسقَط واحدةٌ منها. -/
theorem mukhtamal_sibawayh : mukhtamal keyS [0, 1, 2] placed16 = true := by decide +kernel

/-- **التسلسلُ تامٌّ مع كلّ ترتيب**: لا مانعَ في الدرجة الأخيرة بأيّ ترتيبٍ للصفات الثلاث (فالترتيبُ يغيّر الدرجاتِ لا
النتيجة). -/
theorem tartib_la_yughayyir_al_akhir :
    [[0, 1, 2], [0, 2, 1], [1, 0, 2], [1, 2, 0], [2, 0, 1], [2, 1, 0]].all
      (fun ss => fasl ⟨keyS ss, placed16⟩) = true := by
  decide +kernel

/-! ### درجةُ ولادة الحرف -/

/-- الحرفُ منفصلٌ في الدرجة d: لا مانعَ له فيها. -/
def munfasil (d : Nat) (c : Char) : Bool := (mani (daraja d)).all fun p => p.1 != c

/-- **درجةُ الولادة**: أوّلُ درجةٍ ينفصل فيها الحرف (4 إن لم ينفصل، ولا يقع: `wilada_le`). -/
def wilada (c : Char) : Nat := ((List.range 4).find? (munfasil · c)).getD 4

/-- قرناءُ الحرف في الدرجة d: من يمنعه. -/
def qurana (d : Nat) (c : Char) : List Char := ((mani (daraja d)).filter (·.1 == c)).map (·.2)

/-- **كلُّ حرفٍ يولد في درجةٍ من الأربع.** -/
theorem wilada_le : placed16.all (wilada · ≤ 3) = true := by decide +kernel

/-- **عددُ المولودين في كلّ درجة**: بالمخرج وحدَه سبعة (ق ك ض ل ن ر ف: مخارجُ لا شريكَ فيها)، وبالجهر تسعة، وبالصنف
سبعة، وبالإطباق ستّة؛ ومجموعُهم 29. -/
theorem wilada_adad :
    (List.range 4).map (fun d => (placed16.filter (wilada · == d)).length) = [7, 9, 7, 6] := by
  decide +kernel

/-- **المولودون بالإطباق** هم أطرافُ «ولولا الإطباق» الستّة بأعيانهم. -/
theorem wilada_itbaq :
    placed16.filter (wilada · == 3) = ['ط', 'د', 'س', 'ص', 'ظ', 'ذ'] := by
  decide +kernel

/-- **المنفصلُ لا يعود مانعًا**: من وُلد في درجةٍ منفصلٌ في كلّ ما بعدها. -/
theorem mani_tadarruj :
    placed16.all (fun c => (List.range 4).all (fun d => !(wilada c ≤ d) || munfasil d c)) = true := by
  decide +kernel

/-! ## ٢. الليف: حروفُ كلّ مخرجٍ وولادتُها -/

/-- حروفُ المخرج m بترتيب الباب. -/
def lif (m : Nat) : List Char := placed16.filter (makhrajOf · == m)

/-- **الليفُ بأحجامه** (كـ`Makharij.fibers`): ستّةَ عشر مخرجًا، والخياشيمُ فارغة. -/
theorem lif_ahjam : (List.range 16).map (fun m => (lif m).length) = [3, 2, 2, 1, 1, 3, 1, 1, 1, 1, 3, 3, 3, 1, 3, 0] := by
  decide +kernel

/-- **ولادةُ حروف الليف**: درجةُ ولادة كلّ حرفٍ في ليف مخرجه بترتيب الباب. -/
theorem lif_wilada :
    (List.range 16).map (fun m => (lif m).map wilada) =
      [[2, 1, 2], [1, 1], [1, 1], [0], [0], [2, 1, 2], [0], [0], [0], [0], [3, 3, 1], [1, 3, 3], [3, 3, 1], [0],
       [2, 2, 2], []] := by
  decide +kernel

/-! ## ٣. الولادة: الخانةُ في موضعها — الابتداءُ والوصلُ والوقف -/

/-- **الموضع**: الابتداء، أو الوصلُ بعد حالة، أو الوقفُ بعد حالة. -/
inductive Mawdi where
  | ibtida
  | wasl (p : Haraka)
  | waqf (p : Haraka)
  deriving DecidableEq, Repr

def harakat : List Haraka := [.fatha, .damma, .kasra, .sukun]

def mawadi : List Mawdi := [.ibtida] ++ harakat.map .wasl ++ harakat.map .waqf

/-- رقمُ الموضع. -/
def mIdx : Mawdi → Nat
  | .ibtida => 0
  | .wasl p => 1 + p.index
  | .waqf p => 5 + p.index

/-- أرقامُ المواضع التسعة 0…8 بترتيبها (على الشاهد). -/
theorem mawadi_idx : mawadi.map mIdx = List.range 9 := by decide

/-- **الدورُ** في الموضع: `Hadd.kindOne` على حالة ما قبلها. -/
def dawr : Mawdi → Cell → K
  | .ibtida, x => Hadd.kindOne none x
  | .wasl p, x => Hadd.kindOne (some p) x
  | .waqf p, x => Hadd.kindOne (some p) x

/-- تعريفيّ: الدورُ هو `kindOne` بعينه على حالة ما قبله. -/
theorem dawr_kindOne (p : Haraka) (x : Cell) :
    dawr (.wasl p) x = Hadd.kindOne (some p) x ∧ dawr .ibtida x = Hadd.kindOne none x := ⟨rfl, rfl⟩

/-- أصنافُ السابق الممكنة بحالته: المتحرّكُ `cv`، والساكنُ مدٌّ `v` أو مُغلِقٌ `c` (تعيينُ البنّاء؛ مبرهنتُه
`qablK_mada`). -/
def qablK : Mawdi → List K
  | .ibtida => []
  | .wasl p | .waqf p => if p == .sukun then [.v, .c] else [.cv]

/-- **`qablK` هو مدى `kindOne`**: لكلّ حالةٍ p، أصنافُ السابق في `qablK` هي بعينها أدوارُ الخانات التي حالتُها p بعد أيّ
حالةٍ أو ابتداءً — لا أقلّ ولا أكثر (على الشاهد). -/
theorem qablK_mada :
    harakat.all (fun p =>
      let ks := (Jadwal.khanat.filter (·.haraka == p)).flatMap
        (fun y => (none :: harakat.map some).map (Hadd.kindOne · y))
      (qablK (.wasl p)).all (ks.contains ·) && ks.all ((qablK (.wasl p)).contains ·)) = true := by
  decide +kernel

/-- **الحكم** على الولادة — حكمُ ترخيص، لا طبقةُ الحكم على الواقع (م١٠). -/
inductive Hukm where
  /-- مرخَّصٌ مع كلّ سابقٍ ممكن. -/
  | murakhkhas
  /-- مرخَّصٌ في الجوار مع بعض السابق (`qabl`) وبشرطٍ مسمًّى يُحسم بما بعده. -/
  | mashrut (qabl : List K) (shart : String)
  /-- الوقفُ يسكِّن: الخانةُ تصير ساكنتَها. -/
  | yuskan
  /-- مرفوضٌ باسمه. -/
  | marfud (ism : String)
  deriving DecidableEq, Repr

def sakinOf (x : Cell) : Cell := ⟨x.carrier, .sukun⟩
def mutaharrikOf (x : Cell) : Cell := ⟨x.carrier, .fatha⟩

/-- **الحكم**: الألفُ المتحرّكة لا تُرخَّص (`Alif`)؛ ولا يُبتدأ بساكن؛ ولا يُوقف على متحرّك (يسكَّن)؛ والجوارُ بأزواج
`waslK` (ووقفًا `waqfK` أيضًا) على أصناف السابق الممكنة؛ وما جاز مع المدّ وحدَه وصلًا فشرطُه قيدُ الحدّ: أوّلُ مثلين أو
مدُّ الفرق (`Hadd.isFarq`)، يُحسمان بما بعده لا هنا. **وتعيينُ البنّاء**: إن لم يكن للحامل متحرّكٌ مرخَّص
(`mutaharrikOf` يمثّله بالفتحة) فلا أوّلَ مثلين له، فيُرفض. -/
def hukm (m : Mawdi) (x : Cell) : Hukm :=
  if !Jadwal.licensableCell x then .marfud "BARE_ALIF_OWN_MARK_NOT_LICENSED"
  else match m with
  | .ibtida => if ternary.ibtida (dawr m x) then .murakhkhas else .marfud "INITIAL_SUKUN_WITHOUT_REPAIR"
  | .wasl _ =>
    let ok := (qablK m).filter (waslK · (dawr m x))
    if ok == qablK m then .murakhkhas
    else if ok.isEmpty then .marfud "JUNCTION_NOT_LICENSED"
    else if Jadwal.licensableCell (mutaharrikOf x) then .mashrut ok "CVVC_NOT_GEMINATE"
    else .marfud "CVVC_NOT_GEMINATE"
  | .waqf _ =>
    if x.haraka != .sukun then .yuskan
    else
      let ok := (qablK m).filter (fun k => waslK k (dawr m x) || waqfK k (dawr m x))
      if ok == qablK m then .murakhkhas
      else if ok.isEmpty then .marfud "NOT_PAUSE_LICENSED"
      else .mashrut ok "PAUSE"

/-- الولادة: (الخانة، الموضع). -/
def wiladat : List (Cell × Mawdi) := Jadwal.khanat.flatMap fun x => mawadi.map (x, ·)

/-- **عددُ الولادة n**: ‎9·k + m‎ — عددُها في المرجع، غيرُ عدد الشهادة n. -/
def nOf (b : Cell × Mawdi) : Nat := 9 * Jadwal.khanat.idxOf b.1 + mIdx b.2

/-- **تمامُ العدد**: أعدادُ الولادات الـ1044 هي ‎0…1043‎ بترتيبها، فهي تقابل. -/
theorem n_tamam : wiladat.map nOf = List.range 1044 := by decide +kernel

/-- اسمُ الحكم للعدّ. -/
def hukmIsm : Hukm → String
  | .murakhkhas => "murakhkhas"
  | .mashrut _ _ => "mashrut"
  | .yuskan => "yuskan"
  | .marfud _ => "marfud"

def hukmAll : List String := ["murakhkhas", "mashrut", "yuskan", "marfud"]

/-- العدُّ في موضعٍ: (مرخَّص، مشروط، يسكَّن، مرفوض). -/
def adad (m : Mawdi) : List Nat :=
  hukmAll.map fun h => (Jadwal.khanat.filter fun x => hukmIsm (hukm m x) == h).length

/-- **الابتداء**: 84 خانةً مرخَّصة (كـ`Jadwal.ibtida_wasl_waqf_counts`)، والساكنُ 29 مرفوضٌ باسمه، والألفُ المتحرّكةُ 3. -/
theorem adad_ibtida : adad .ibtida = [84, 0, 0, 32] := by decide +kernel

/-- **الوصلُ بعد متحرّك**: كلُّ الـ113 مرخَّصة. -/
theorem adad_wasl_mutaharrik :
    [Haraka.fatha, .damma, .kasra].map (fun p => adad (.wasl p)) = [[113, 0, 0, 3], [113, 0, 0, 3], [113, 0, 0, 3]] := by
  decide +kernel

/-- **الوصلُ بعد ساكن**: المتحرّكُ مرخَّص (84)، والساكنُ مشروطٌ بالمدّ قبله وأوّلِ مثلين بعده (28) إلّا الألف (لا متحرّكَ
لها مرخَّصًا). -/
theorem adad_wasl_sakin : adad (.wasl .sukun) = [84, 28, 0, 4] := by decide +kernel

/-- **الوقف**: المتحرّكُ يسكَّن (84 وثلاثُ ألفاتٍ مرفوضة)، والساكنُ مرخَّصٌ بعد كلّ حالة (29). -/
theorem adad_waqf :
    harakat.map (fun p => adad (.waqf p)) = [[29, 0, 84, 3], [29, 0, 84, 3], [29, 0, 84, 3], [29, 0, 84, 3]] := by
  decide +kernel

/-! ### القانونُ على السُّلَّم: في أيّ درجةٍ يتعيّن حكمُ الولادة؟ -/

/-- **متّجهُ القانون للحرف**: الدورُ والحكمُ في كلّ (حالة، موضع) — ستّةٌ وثلاثون. -/
def qanunVec (c : Char) : List (K × Hukm) :=
  harakat.flatMap fun h => mawadi.map fun m => (dawr m (atom c h), hukm m (atom c h))

/-- **موانعُ القانون في الدرجة d**: حرفان سببُهما في الدرجة واحدٌ ومتّجها قانونهما مختلفان. -/
def qanunMani (d : Nat) : List (Char × Char) :=
  (mani (daraja d)).filter fun p => qanunVec p.1 != qanunVec p.2

/-- **حكمُ الخانة الثلاثيُّ في هذا المرجع يتعيّن بالصنف**: بالمخرج وحدَه لا يتعيّن في ثلاثة مخارج — الألفُ مع الهمزة
والهاء، والياءُ مع الجيم والشين، والواوُ مع الباء والميم — وبالجهر يخرج الهاءُ والشين، وبالصنف يتعيّن، فما بقي من موانع
الحروف بعده (الأزواجُ الثلاثة) حكمُها واحد. والسببُ أنّ `hukm` لا يرى من الحرف إلّا كونَه ا أو و أو ي؛ فلا يُقال منه إنّ
الإطباقَ خارجُ الترخيص كلِّه: هو في الكتاب داخلٌ في ترخيص الإدغام (س21410–21411). -/
theorem qanun_tadarruj :
    (List.range 4).map qanunMani =
      [[('ء', 'ا'), ('ه', 'ا'), ('ا', 'ء'), ('ا', 'ه'), ('ج', 'ي'), ('ش', 'ي'), ('ي', 'ج'), ('ي', 'ش'), ('ب', 'و'),
        ('م', 'و'), ('و', 'ب'), ('و', 'م')],
       [('ء', 'ا'), ('ا', 'ء'), ('ج', 'ي'), ('ي', 'ج'), ('ب', 'و'), ('م', 'و'), ('و', 'ب'), ('و', 'م')], [], []] := by
  decide +kernel

/-! ## ٤. الشاهدُ المبنيّ على قانون الأزواج: الحكمُ يطابق `strictB`/`strictPauseB` على كلماتٍ مبنيّةٍ للفحص لكلّ خانة -/

def ba (p : Haraka) : Cell := atom 'ب' p

/-- **الابتداء**: المرخَّصُ ابتداءً هو ما تُرخَّص كلمتُه وحدَه وصلًا. -/
theorem shahid_ibtida :
    Jadwal.khanat.all (fun x =>
      (hukm .ibtida x == .murakhkhas) == (Jadwal.licensableCell x && Hadd.strictB [x])) = true := by
  decide +kernel

/-- **الوصلُ بعد متحرّك**: المرخَّصُ هو ما يُرخَّص بعد «بـ» بتلك الحالة. -/
theorem shahid_wasl_mutaharrik :
    [Haraka.fatha, .damma, .kasra].all (fun p => Jadwal.khanat.all (fun x =>
      (hukm (.wasl p) x == .murakhkhas) == (Jadwal.licensableCell x && Hadd.strictB [ba .fatha, ba p, x]))) = true := by
  decide +kernel

/-- **الوصلُ بعد ساكن**: المتحرّكُ يُرخَّص بعد «بَبْ» وبعد «بَاْ»؛ والساكنُ لا يُرخَّص بعد مُغلِق («بَبْ») ولا بعد مدٍّ بلا
مثله («بَاْ»)، ويُرخَّص بعد مدٍّ يليه مثلُه متحرّكًا — وهذا شرطُه المسمّى. **والفرعُ المرفوض تعريفيّ**: يعيد شرطَ `hukm`
ولا يسأل `strictB`. -/
theorem shahid_wasl_sakin :
    Jadwal.khanat.all (fun x => match hukm (.wasl .sukun) x with
      | .murakhkhas => Hadd.strictB [ba .fatha, ba .sukun, x] && Hadd.strictB [ba .fatha, atom 'ا' .sukun, x]
      | .mashrut _ _ => !Hadd.strictB [ba .fatha, ba .sukun, x] && !Hadd.strictB [ba .fatha, atom 'ا' .sukun, x] &&
          Hadd.strictB [ba .fatha, atom 'ا' .sukun, x, mutaharrikOf x]
      | .marfud _ => !Jadwal.licensableCell x || !Jadwal.licensableCell (mutaharrikOf x)
      | .yuskan => false) = true := by
  decide +kernel

/-- **الوقف**: لكلّ حالةٍ p ولكلّ خانةٍ ساكنة، `hukm (.waqf p)` مرخَّصٌ ⟺ الخانةُ مرخَّصةٌ ويُرخَّص وقفًا ما يُبنى لها
بعد «بَ» بالحالة p (وإن كانت p سكونًا فبعد «بَبْ» وبعد «بَاْ» معًا). -/
theorem shahid_waqf :
    harakat.all (fun p => Jadwal.khanat.all (fun x => x.haraka != .sukun ||
      ((hukm (.waqf p) x == .murakhkhas) ==
        (Jadwal.licensableCell x && Hadd.strictPauseB [ba .fatha, ba p, x] &&
          (p != .sukun || Hadd.strictPauseB [ba .fatha, atom 'ا' .sukun, x]))))) = true := by
  decide +kernel

/-- **ولا يُوقف على متحرّك**: المتحرّكُ طرفًا لا يُرخَّص وقفًا إلّا ساكنًا (`yuskan`). -/
theorem shahid_yuskan :
    Jadwal.khanat.all (fun x => hukm (.waqf .fatha) x != .yuskan ||
      (Hadd.strictPauseB [ba .fatha, sakinOf x])) = true := by
  decide +kernel

/-! ## ٥. الوصلُ بين الحرفين: قانونُ الإدغام لكلّ حرف (`MakharijIdgham.qism`) -/

/-- أقسامُ الحرف أوّلًا مع كلّ ثانٍ: (مثل، مثلٌ ممتنع، شاهدُ إدغام، شاهدُ امتناع، مسكوت، ممتنع، إظهار). -/
def idghamAdad (a : Char) : List Nat :=
  MakharijIdgham.qismAll.map fun q => (huruf.filter fun b => MakharijIdgham.qism a b == q).length

/-- **مجموعُ الأقسام على الحروف** هو استيفاءُ الـ841 (`MakharijIdgham.istinfad`). -/
theorem idgham_jumla :
    (List.range 7).map (fun i => (placed16.map fun a => (idghamAdad a).getD i 0).foldl (· + ·) 0) =
      [27, 2, 93, 44, 22, 37, 616] := by
  decide +kernel

end A116.Marja
