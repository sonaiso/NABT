/-
  Jisr/SakkJumla.lean — صكُّ الجملة: قوّتُها، والسببُ الذي يذكره لفظُها، ومرجعُ ضميرها وإشارتها؛ ثمّ الواقعُ بعد القوّة.

**قولُ المالك** في الجلسة (2026-10-26): «راجع كتاب الشخصية الجزء الثالث والجزء الاول وراجع كتاب التفكير واربط مع قطر الندى والالفية ومغني اللبيب وسيبويه من خلال lean انت مجموعة وكلاء خبراء اوجد حلا»
- **مصدرُ النقل:** لفظُه من ملخّص الجلسة بعد ضغطها، ووقتُه منه فلم يُكتب.
- **السياق:** جاء بعد مقترحٍ ألصقه يحقن رُخَصًا في حالات مرجع NABT الخمس والعشرين. ووصفُ المقترح من الملخّص أيضًا.
- **التصميم:** قرارُ البنّاء.

**السؤال.** ثلاثُ مسائلَ تُقرأ من صورة التركيب وحدها، ثمّ رابعةٌ عليها:
1. **القوّة** (`awwal`، `thani`): أيُّ جملةٍ في التركيب خبرٌ يُخبر به المتكلّم، وأيُّها معلَّقةٌ أو محكيّةٌ أو مظنونة، أو إنشاء.
   الخبرُ ما يحتمل التصديقَ والتكذيب، والإنشاءُ لا يحتملهما (ج3: `khabar`، `insha`).
2. **السببُ المذكور** (`sabab`): هل في التركيب دالٌّ يذكر علّةَ الفعل، أو يربط حدثين ربطَ سببيّة.
   - و«سببيّة» هنا ربطٌ يذكره اللفظ، لا السببُ الحتميّ الذي حدّه ج1 (`sababHatman`). وهي أوسعُ منه: فاءُ السببيّة و«حتى» المرفوعةُ منها.
   - وهي غيرُ الدافع في نفس الفاعل. وحملُ ذلك على نصّ ج3 في البيان (`filBiwasita`: فعلُ الرسول لا يدلّ بنفسه على أنّه بيانٌ بل
     بالواسطة) قراءتي، والنصُّ في بيان المجمل لا في الفعل النحويّ.
3. **المرجع** (`marji`): لأنا وأنت وهو وهذا وذاك، معيَّنٌ أو محتمَلٌ أو لا حكم.
4. **الواقع بعد القوّة** (`waqiJumla`): لا يُسأل عن واقع جملةٍ إلّا إذا كانت خبرًا. وحكمُها حينئذٍ ما يُمرَّر إليه، والمقصودُ `Waqi.hukm`
   (`la_waqi_bila_mushahada`).

**المدخلُ تحليلٌ يُعطى، لا مُخرَجُ قارئٍ من النصّ** (P4 لم يُبنَ). وحقولُه حقولُ مواصفة الضابط المجمَّد
`tahaqquq/dawabit/sakk/wasf.md` بأعيانها.

**الأسانيد.** `asanid` (§٦) قطعٌ حرفيّة من المودَعات المختومة: الكتاب، والمغني، والقطر، والألفية، والشخصيّة ج1 (`a1.txt`) وج3
(`a2.txt`)، و«التفكير» (`a3.txt`). يفحصها `tahaqquq/test_sakk.py` على المودَع موصولةَ الأسطر بأدنى مدًى. وأرقامُ الأسطر أدناه أسطرُ
تلك الملفّات.
- و«التفكير» لا يقوم عليه حكمٌ هنا: قطعتُه الوحيدة (`sifaLaAthar`) في توثيق `dafiNabt`، قراءةً.

**الربطُ بقطع Lean القائمة** (§٧):
- **ربطُ حكم:** «إن» يُجازى بها في باب الجزاء المبنيّ (`Jisr/BabJaza.lean`)، والتعليقُ في `awwal` لا يكون إلّا بأداةٍ كذلك (`taliq_iff_jaza`).
- **مطابقةُ لفظٍ ورقمِ سطر، لا مبرهنتا توافق:**
  - «لم» لفظُ الأداة، و«لم يفعل» نفيُ الماضي المنقطع في `Aql/Awwaliyyat.lean` (`lam_nafy_madi`). ولا شيء فيها يصل `.nafy` في `awwal` بمخرج
    `Aql.Awwaliyyat`.
  - والمفعولُ له أسلوبٌ في جرد القطر بسطره (`Jisr/Ikhbar.lean`)، وسندُه هنا السطرُ نفسُه (`mafulLahu_qatr`).
- **وما سوى ذلك لم يُربط:** `Jisr/NafyFil.lean` وفيه سندُ «لم» نفسُه (`nafyFaala`، الكتاب س9783)، وصورُ نفي الأزمنة الأخرى، وأحكامُ الجواب في باب
  الجزاء، والضمائرُ في `Jisr/QiraaSimat.lean`.

**ما هو تعيينُ البنّاء** (لا نصُّ المصادر):
- **ترتيبُ `awwal`:** «إن» أوّلًا، ثمّ الاستفهامُ بـ«تقول»، ثمّ «لم» (`nafyLam`، `lamJazm`)، وإلّا خبرٌ مثبت. وجملةُ القول نفسُها خبر.
- **بعد «إن» بلا فعل قول:** الجملتان معلَّقتان (`taliqIn`؛ والجزاءُ «يحتمل الوقوع وعدمه»: `taliqIhtimal`). وقولُ الخليل في جواب سؤال
  سيبويه (`ghayrWajib`) في الكلام الأوّل وحده، وموضعُه «أتي الأمير لا يقطع اللص» لا «إن».
- **بعد «إن» مع فعل القول:** الثانيةُ لا حكم. لم يُبنَ.
- **بعد «قال»:**
  - «إنّ» ومرفوعٌ وجملةٌ فعليّة: حكاية (`qultHikaya`، `qalaInna`).
  - منصوبٌ أو «أنّ»: ظنٌّ عند بني سليم (`sulaym`، `sulaymAlfiyya`)، ولا حكمَ في لغة العامّة (`qultLaZann`). **وبلا لغةٍ معلنة ظنٌّ**:
    الصورةُ نفسُها تدلّ على تلك اللغة.
  - بلا صورةٍ معلنة: حكايةٌ وحدها، إلّا عند بني سليم فالوجهان.
- **بعد «تقول» مستفهمًا** (`taqulZann`، و`taqulAlfiyya` بشرطيه: الاستفهامُ والاتّصال):
  - منصوبٌ أو «أنّ»: ظنّ (`yunus`).
  - مرفوعٌ: حكاية (`taqulRaf`). و«إنّ»: حكاية (`yunusHikaya`). والجملةُ الفعليّةُ حكايةٌ تعيينًا.
  - بلا صورةٍ معلنة: الوجهان (`ihtimalQawl`).
- **المصدرُ المنصوب:** علّةٌ إن استوفى الشروط (`mafulLahu`، `udhr`). وبغير ذلك لا حكم: بفقد شرطٍ، فهو «جر بحرف التعليل» (`faqdShart`) لا
  منصوب؛ وبشروطٍ غيرِ معلنة كذلك، تعيينًا.
- **اللامُ الجارّة:** علّةٌ أو غيرُها. التعليلُ معنًى من معانيها (`lamMaani`، `lamTalil`).
- **اللامُ الناصبة وكي و«أنّ» بلا لام:** علّة (`kay`، `kayLam`، `liAnna`، `anLamMuqaddara`).
  - وعدُّ اللام الناصبة علّةً وحدها تعيين.
  - و«كي» بمعنى «كيف» (المغني س4157) لا تدخل هذا الصنف.
- **«حتى» منصوبًا:** غايةٌ أو بمعنى «كي» (`hattaWajhan`، `hattaKay`). فإن قال المثالُ إنّ الأوّل لم يؤدِّ إلى الثاني فغايةٌ
  وحدها (`hattaLamYuaddih`).
- **«حتى» مرفوعًا:** يُرفع الفعلُ بعدها على وجهين (`hattaRafWajhan`): دخولٌ متّصلٌ بالسير كاتّصاله بالفاء (`hattaRaf`)، ودخولٌ «الآن»
  بعد سيرٍ كان (`hattaAlan`). والرفعُ إذا كان الأوّلُ سببَ الثاني (`hattaLarafata`، `hattaMinSabab`)، وشرطُه «أن يكون مسببا عما قبلها»
  (`hattaMusabbab`): فسببيّة. وإن قال المثالُ إنّ الأوّل لم يؤدِّ فلا حكم: الرفعُ حينئذٍ «لا يجوز» (`hattaMusabbab`؛ وعلّتُه
  `hattaLaYatasabbab`)، وفي العطف بعد «حتى» يقول الكتاب «لأن رفع الأول لا يكون إلا وسبب دخوله سيره» (`hattaRafIllaSabab`)؛ والامتناعُ لا
  يُمثَّل، فليس في `Sabab` «ممتنع».
- **الفاء** (`faSababiyya`):
  - وجهان: السببيّةُ «لو أتيتني لحدثتني»، والآخرُ «ما تأتيني أبدا إلا لم تحدثني» (`faWajhan`، `faLaw`، `faAbadan`).
  - والسببيّةُ «غالب في العاطفة»، وقد تجيء «لمجرد الترتيب» (`faGhalib`، `faTartib`).
  - فإن قال المثالُ إنّ الأوّل أدّى إلى الثاني فسببيّة، أو لم يؤدِّ فلا سببَ مذكور، وإلّا فالوجهان.
  - وحملُ المرفوعة على المنصوبة في ذلك تعيين.
  - والقطرُ يسمّي المنصوبةَ «فاء السببية» (`faSababiyya`)، والألفيةُ «فا جواب» (`faJawab`)؛ والوجهان بلا أداءٍ معلن من نصّ الكتاب (`faWajhan`).
- **S14 وS24 وS25 (السبب):** اختار المالكُ فيها «عدّلها بسندٍ من النطاق» (2026-10-26، من سؤالٍ متعدّد الخيارات ونصُّ الخيار من البنّاء).
  فعُدّلت (`natija_3.json`)، ثمّ رُدّت إلى الشفرة المجمَّدة (`natija_5.json`)، والردُّ قرارُ البنّاء على شرط الخيار، وينتظر قرارَ المالك:
  S14 تعميمُ احتمال العلّة وغيرِها على كلّ مصدرٍ منصوبٍ شروطُه غيرُ معلنة، ولم تُوزن عليه نصوصُ النطاق في المصدر المنصوب (منها
  المغني س12981–13006، والكتاب س3659–3692، والقطر س293–296)؛ وS24 إخراجُ «غير مذكور» لمُدخَلٍ يقول مصدرُه «فلا يجوز» (المغني س2836)؛ وS25 تركُ الوجه الثاني من وجهي
  الكتاب («فالنصب على وجهين من المعاني» س8945) على قراءة البنّاء إيّاه «غيرَ مذكور»، والقطرُ يضع مثالَ الحالة نفسَه بعد «فاء السببية» (س108–109).
- **«لمّا»: الوجهان.**
  - سببٌ عند سيبويه: «فالأول سبب ما وقع وما لم يقع» (`lammaSabab`؛ وقبله `lammaSibawayhi`).
  - وظرفٌ بمعنى حين عند ابن السراج ومن تبعه (`lammaZarf`).
  - وفي نطاق المواصفة منهما «وترتبه عليه» وحدها (`lammaTartib`)، والموضعان الآخران خارجه.
- **«بعد» و«قبل»:** ظرفان (`zarfSibawayhi`)، وفي الأصل صفتان للزمان (`zarfZaman`، جوابًا في مسألة «من» الداخلة عليهما)، فلا سببَ
  مذكور. وقولُ ج1 في الحالة إنّها «ظرف خاص بملابسات خاصة» لا السبب (`hala`) في سبب الموت، و«ظرف» فيه الملابسة لا ظرفُ الزمان: فالاستشهادُ
  به قياسي.
- **المرجع:**
  - معيَّنٌ إذا أعطى السياقُ واحدًا من جنس ما يدلّ عليه اللفظ: المتكلّمُ لـ«أنا»، والمخاطَبُ لـ«أنت»، والمشارُ إليه لـ«هذا» و«ذاك»
    (`damir`، `ishara`). ولـ«هو» المفسِّرُ في الكلام أو المعروفُ في الموقف: «قد عرف من تعنى» (`idmar`)، وعدُّ الموقف منه قراءتي.
  - ومحتمَلٌ إذا صلح اثنان لـ«هو» (`taraddud`: التردّد في عود الضمير). وقولُ ج3 «فلا يحمل على أحدهما ما لم توجد قرينة» (`qarina`) في
    الإضمار بمعنى التقدير مقابلَ المجاز، لا في مرجع الضمير: فالاستشهادُ به قياسي. وصلوحُ اثنين في الموقف لـ«هو» قياسٌ كذلك، من جنس القياس
    الذي لم يختره المالك في الإشارة؛ ولم يُعرض عليه في «هو» (ينتظر قراره).
  - **والإشارةُ إلى اثنين لا حكم** حتى يُودَع لها سند: اختيارُ المالك (2026-10-26) من سؤالٍ متعدّد الخيارات، ونصُّ الخيار من البنّاء
    («لا حكم» حتى يُودَع سند). وكانت في الشفرة المجمَّدة «محتمَلًا» قياسًا (`natija_1.json`: تجاوزان).
  - ولا حكمَ إذا لم يُعطِ السياقُ شيئًا من جنسه (`mufassir`)، ومنه «هذا» مع مفسِّرٍ في الكلام وحده.
- **الواقع:** الجملةُ الثانية لا يُخبر بها المتكلّم، فلا يُسأل عن واقعها.

**المبرهنات (25).**
- **لكلّ (4):** `thani_la_mafhum`، `la_waqi_bila_mushahada`، `la_dafi_bila_dall`، `taliq_iff_jaza`. تستدعي مبرهناتٍ مسمّاةً أو `decide`.
- **تعريفيّة (14):** `taliq_la_yukhbar`، `thani_la_ikhbar`، `awwal_khabar_iff`، `qala_amma_la_zann`، `illa_bi_dall`، `zarf_laysa_sabab`،
  `lamma_wajhan`، `hatta_wa_fa`، `muayyan_iff`، `ithnan_la_yataayyan`، `ishara_ithnan_la_hukm`، `la_marji_bila_siyaq`،
  `la_waqi_bila_ikhbar`، `waqiNabt_iff`. برهانُها فكُّ التعريفات وتفكيكُ الحالات، فهي تعيد قولَ التعيين أعلاه.
- **على الشاهد (7):** `nabt_quwwa`، `nabt_marji`، `nabt_marji_C05`، `marjiNabt_huwa_mufassiran`، `nabt_la_tarqiya`، `lam_nafy_madi`،
  `mafulLahu_qatr`. برهانُها `decide`.

**حدُّه:**
- مبرهناتُ «لكلّ» خواصُّ للتعيين على مجاله، لا مطابقتُه للمصادر. ومطابقتُه تُقاس بالضابط المجمَّد (`Jisr/SakkJumlaQiyas.lean`).
- §٥ تشخيصٌ على مادّةٍ مكشوفة، لا قياس. انظر رأسَه.
- غيرُ موصولٍ بالمحرّك ولا بالقارئ.
-/

import Aql.Waqi
import Aql.Awwaliyyat
import Jisr.BabJaza
import Jisr.Ikhbar

namespace Jisr.SakkJumla

/-! ## ١. القوّة -/

/-- الأداةُ الداخلةُ على الكلام. -/
inductive Adat | laShay | lam | in_
  deriving DecidableEq, Repr

/-- فعلُ القول في الجملة الأولى. -/
inductive Qawl | laQawl | qala | taqulMustafhim
  deriving DecidableEq, Repr

/-- صورةُ ما بعد فعل القول. -/
inductive MaBaad | laQawl | innaMaksura | annaMaftuha | marfu | mansub | jumlaFiliyya | ghayrMuallan
  deriving DecidableEq, Repr

inductive Lugha | amma | banuSulaym | ghayrMuallan
  deriving DecidableEq, Repr

structure DakhilQ where
  adat : Adat
  qawl : Qawl
  maBaad : MaBaad
  lugha : Lugha
  deriving DecidableEq, Repr

/-- قوّةُ الجملة. -/
inductive Quwwa | ithbat | nafy | taliq | insha | hikaya | zann | laThani | laHukm
  deriving DecidableEq, Repr

/-- قوّةُ الجملة الأولى: المعلَّقةُ بـ«إن»، ثمّ الاستفهامُ بـ«تقول»، ثمّ المنفيّةُ بـ«لم»، وإلّا خبرٌ مثبت. -/
def awwal (d : DakhilQ) : Quwwa :=
  match d.adat, d.qawl with
  | .in_, _ => .taliq
  | _, .taqulMustafhim => .insha
  | .lam, _ => .nafy
  | _, _ => .ithbat

/-- ما بعد «قال» (بغير الاستفهام). -/
def baadQala (m : MaBaad) (l : Lugha) : List Quwwa :=
  match m, l with
  | .innaMaksura, _ | .marfu, _ | .jumlaFiliyya, _ => [.hikaya]
  | .mansub, .banuSulaym | .annaMaftuha, .banuSulaym => [.zann]
  | .mansub, .ghayrMuallan | .annaMaftuha, .ghayrMuallan => [.zann]
  | .mansub, .amma | .annaMaftuha, .amma => [.laHukm]
  | .ghayrMuallan, .banuSulaym => [.hikaya, .zann]
  | .ghayrMuallan, _ => [.hikaya]
  | .laQawl, _ => [.laHukm]

/-- ما بعد «تقول» مستفهمًا بها. -/
def baadTaqul (m : MaBaad) : List Quwwa :=
  match m with
  | .mansub | .annaMaftuha => [.zann]
  | .marfu | .innaMaksura | .jumlaFiliyya => [.hikaya]
  | .ghayrMuallan => [.hikaya, .zann]
  | .laQawl => [.laHukm]

/-- قوّةُ الجملة الثانية (قائمةُ البدائل). -/
def thani (d : DakhilQ) : List Quwwa :=
  match d.adat, d.qawl with
  | .in_, .laQawl => [.taliq]
  | .in_, _ => [.laHukm]
  | _, .laQawl => [.laThani]
  | _, .qala => baadQala d.maBaad d.lugha
  | _, .taqulMustafhim => baadTaqul d.maBaad

/-- **المعلَّقُ لا يُخبر به:** بعد «إن» بلا فعل قول الجملتان معلَّقتان (`taliqIn`، `taliqIhtimal`). -/
theorem taliq_la_yukhbar (d : DakhilQ) (h : d.adat = .in_) (hq : d.qawl = .laQawl) :
    awwal d = .taliq ∧ thani d = [.taliq] := by
  obtain ⟨a, q, m, l⟩ := d
  simp only at h hq
  subst h; subst hq
  exact ⟨rfl, rfl⟩

/-- **والجملةُ الثانية ليست خبرًا مثبتًا ولا منفيًّا يُخبر به المتكلّم.** -/
theorem thani_la_ikhbar (d : DakhilQ) : Quwwa.ithbat ∉ thani d ∧ Quwwa.nafy ∉ thani d := by
  obtain ⟨a, q, m, l⟩ := d
  cases a <;> cases q <;> cases m <;> cases l <;> simp [thani, baadQala, baadTaqul]

/-- **والأولى خبرٌ إذا وفقط إذا لم تكن بعد «إن» ولا استفهامًا بـ«تقول».** -/
theorem awwal_khabar_iff (d : DakhilQ) :
    (awwal d = .ithbat ∨ awwal d = .nafy) ↔ (d.adat ≠ .in_ ∧ d.qawl ≠ .taqulMustafhim) := by
  obtain ⟨a, q, m, l⟩ := d
  cases a <;> cases q <;> simp [awwal]

/-- **«قال» لا يُجرى مجرى الظنّ في لغة العامّة** (`qultLaZann`): المنصوبُ و«أنّ» بعده لا حكم، أيًّا كانت الأداة. -/
theorem qala_amma_la_zann (a : Adat) (m : MaBaad) (hm : m = .mansub ∨ m = .annaMaftuha) :
    thani ⟨a, .qala, m, .amma⟩ = [.laHukm] := by
  rcases hm with rfl | rfl <;> cases a <;> simp [thani, baadQala]

/-! ## ٢. السبب المذكور -/

/-- الرابطُ بين الحدث الأوّل وما بعده. -/
inductive Dall
  | masdarMansub | lamJarra | lamNasiba | kay | hattaMansub | hattaMarfu | faMansub | faMarfu
  | anBilaLam | lamma | baad | qabl | ghayrDhalik
  deriving DecidableEq, Repr

/-- شروطُ المفعول له. -/
inductive Shurut | mustawfat | faqdFail | faqdWaqt | ghayrMuallan | laYantabiq
  deriving DecidableEq, Repr

/-- هل أدّى الأوّلُ إلى الثاني (لحتى والفاء). -/
inductive Adaa | sabab | laysaSabab | ghayrMuallan | laYantabiq
  deriving DecidableEq, Repr

structure DakhilS where
  dall : Dall
  shurut : Shurut
  adaa : Adaa
  deriving DecidableEq, Repr

/-- السببُ المذكور. -/
inductive Sabab | illa | sababiyya | ghayrMadhkur | laHukm
  deriving DecidableEq, Repr

/-- الحكمُ في السبب (قائمةُ البدائل). -/
def sabab (d : DakhilS) : List Sabab :=
  match d.dall with
  | .masdarMansub => if d.shurut = .mustawfat then [.illa] else [.laHukm]
  | .lamJarra => [.illa, .ghayrMadhkur]
  | .lamNasiba | .kay | .anBilaLam => [.illa]
  | .hattaMansub => if d.adaa = .laysaSabab then [.ghayrMadhkur] else [.illa, .ghayrMadhkur]
  | .hattaMarfu => if d.adaa = .laysaSabab then [.laHukm] else [.sababiyya]
  | .faMansub | .faMarfu =>
      match d.adaa with
      | .sabab => [.sababiyya]
      | .laysaSabab => [.ghayrMadhkur]
      | _ => [.sababiyya, .ghayrMadhkur]
  | .lamma => [.sababiyya, .ghayrMadhkur]
  | .baad | .qabl => [.ghayrMadhkur]
  | .ghayrDhalik => [.laHukm]

/-- الروابطُ التي تذكر علّة. -/
def dawallIlla : List Dall := [.masdarMansub, .lamJarra, .lamNasiba, .kay, .hattaMansub, .anBilaLam]

/-- **لا علّةَ بلا دالٍّ عليها:** العلّةُ لا تخرج إلّا من رابطٍ في `dawallIlla`. -/
theorem illa_bi_dall (d : DakhilS) (h : Sabab.illa ∈ sabab d) : d.dall ∈ dawallIlla := by
  obtain ⟨dl, s, a⟩ := d
  cases dl <;> cases s <;> cases a <;> simp_all [sabab, dawallIlla]

/-- **والظرفُ ليس سببًا:** «بعد» و«قبل» لا تذكران سببًا، أيًّا كانت بقيّةُ الحقول (`zarfSibawayhi`، `zarfZaman`). -/
theorem zarf_laysa_sabab (d : DakhilS) (h : d.dall = .baad ∨ d.dall = .qabl) :
    sabab d = [.ghayrMadhkur] := by
  obtain ⟨dl, s, a⟩ := d
  simp only at h
  rcases h with rfl | rfl <;> rfl

/-- **«لمّا» على الوجهين** (`lammaSabab`، `lammaZarf`)، أيًّا كانت بقيّةُ الحقول. -/
theorem lamma_wajhan (s : Shurut) (a : Adaa) : sabab ⟨.lamma, s, a⟩ = [.sababiyya, .ghayrMadhkur] := rfl

/-- **«حتى» والفاء إذا قال المثالُ إنّ الأوّل لم يؤدِّ إلى الثاني:** لا سببيّة. المنصوبةُ بعد «حتى» غاية (`hattaLamYuaddih`)، والمرفوعةُ
    لا حكم، فرفعُها حينئذٍ «لا يجوز» (`hattaMusabbab`)؛ وبعد الفاء لا سببَ مذكور (`faAbadan`). -/
theorem hatta_wa_fa (s : Shurut) :
    sabab ⟨.hattaMansub, s, .laysaSabab⟩ = [.ghayrMadhkur] ∧ sabab ⟨.hattaMarfu, s, .laysaSabab⟩ = [.laHukm] ∧
    sabab ⟨.faMansub, s, .laysaSabab⟩ = [.ghayrMadhkur] ∧ sabab ⟨.faMarfu, s, .laysaSabab⟩ = [.ghayrMadhkur] :=
  ⟨rfl, rfl, rfl, rfl⟩

/-! ## ٣. المرجع -/

inductive Lafz | ana | anta | huwa | hadha | dhaka
  deriving DecidableEq, Repr

inductive Siyaq
  | mutakallimMuayyan | mukhatabMuayyan | mufassirWahid | mufassiran | musharWahid | musharIthnan | laShay
  deriving DecidableEq, Repr

structure DakhilM where
  lafz : Lafz
  siyaq : Siyaq
  deriving DecidableEq, Repr

inductive Marji | muayyan | muhtamal | laHukm
  deriving DecidableEq, Repr

/-- الحكمُ في المرجع. -/
def marji (d : DakhilM) : Marji :=
  match d.lafz, d.siyaq with
  | .ana, .mutakallimMuayyan => .muayyan
  | .anta, .mukhatabMuayyan => .muayyan
  | .huwa, .mufassirWahid | .huwa, .musharWahid => .muayyan
  | .huwa, .mufassiran | .huwa, .musharIthnan => .muhtamal
  | .hadha, .musharWahid | .dhaka, .musharWahid => .muayyan
  | _, _ => .laHukm

/-- **لا يتعيّن المرجعُ إلّا بما يعطيه الموقفُ أو الكلامُ واحدًا من جنس اللفظ.** -/
theorem muayyan_iff (d : DakhilM) :
    marji d = .muayyan ↔
      (d.lafz = .ana ∧ d.siyaq = .mutakallimMuayyan) ∨ (d.lafz = .anta ∧ d.siyaq = .mukhatabMuayyan) ∨
      (d.lafz = .huwa ∧ (d.siyaq = .mufassirWahid ∨ d.siyaq = .musharWahid)) ∨
      ((d.lafz = .hadha ∨ d.lafz = .dhaka) ∧ d.siyaq = .musharWahid) := by
  obtain ⟨l, s⟩ := d
  cases l <;> cases s <;> simp [marji]

/-- **وما صلح لاثنين لا يتعيّن** (`taraddud`). -/
theorem ithnan_la_yataayyan (d : DakhilM) (h : d.siyaq = .mufassiran ∨ d.siyaq = .musharIthnan) :
    marji d ≠ .muayyan := by
  obtain ⟨l, s⟩ := d
  simp only at h
  rcases h with rfl | rfl <;> cases l <;> simp [marji]

/-- **والإشارةُ إلى اثنين لا حكمَ فيها** حتى يُودَع لها سند (اختيارُ المالك 2026-10-26). -/
theorem ishara_ithnan_la_hukm (l : Lafz) (h : l = .hadha ∨ l = .dhaka) : marji ⟨l, .musharIthnan⟩ = .laHukm := by
  rcases h with rfl | rfl <;> rfl

/-- **ولا مرجعَ بلا موقفٍ ولا كلام** (`mufassir`). -/
theorem la_marji_bila_siyaq (l : Lafz) : marji ⟨l, .laShay⟩ = .laHukm := by
  cases l <;> rfl

/-! ## ٤. الواقع بعد القوّة -/

/-- حكمُ الواقع على جملةٍ بقوّتها: ما لا يُخبر به لا يُسأل عن واقعه؛ وما يُخبر به حكمُه `w`، والمقصودُ `Waqi.hukm`. -/
def waqiJumla (q : Quwwa) (w : Waqi.Hukm) : Waqi.Hukm :=
  match q with
  | .ithbat | .nafy => w
  | _ => .laHukm

/-- **لا واقعَ لما لا يُخبر به** (`insha`). -/
theorem la_waqi_bila_ikhbar (q : Quwwa) (w : Waqi.Hukm) (h : q ≠ .ithbat ∧ q ≠ .nafy) : waqiJumla q w = .laHukm := by
  cases q <;> simp_all [waqiJumla]

/-- **والجملةُ الثانية لا يُسأل عن واقعها أبدًا.** -/
theorem thani_la_mafhum (d : DakhilQ) (w : Waqi.Hukm) : ∀ q ∈ thani d, waqiJumla q w = .laHukm := by
  intro q hq
  apply la_waqi_bila_ikhbar
  obtain ⟨h1, h2⟩ := thani_la_ikhbar d
  exact ⟨fun e => h1 (e ▸ hq), fun e => h2 (e ▸ hq)⟩

/-- **ولا واقعَ بلا مشاهدة**، على أيّ سجلّ: إذا لم يطابق القضيّةَ صفٌّ من المشاهدات فحكمُ الجملة «لا حكم» بأيّ قوّة
    (`Waqi.la_hukm_bila_mushahada`). -/
theorem la_waqi_bila_mushahada (sijill : List (String × Idaa.Naw)) (basmaOf : Nat → String) (T : List Waqi.Mushahada)
    (m s v : String) (h : Waqi.mutabiq T m s v = []) (q : Quwwa) :
    waqiJumla q (Waqi.hukm sijill basmaOf T m s v) = .laHukm := by
  cases q <;> simp [waqiJumla, Waqi.la_hukm_bila_mushahada sijill basmaOf T m s v h]

/-! ## ٥. على مرجع NABT ذي الخمس والعشرين حالة (تشخيصٌ على مادّةٍ مكشوفة)

**الذهب** منقولٌ من `evidence/semantic_axes_v1/revision_2/reference.json` في sonaiso/nabt (الإيداع `b64401f`؛ بصمةُ الملفّ `9787e449…`)،
بالحقول التي يحكم فيها هذا الملفّ، ويطابقه `tahaqquq/test_sakk.py` بتوقّعاتٍ منقولةٍ يدويًّا. وهو مؤقّت: حالاتُه كلُّها
`provisional_authored`، ومراجعتُها البشريّة الخارجيّة `pending`، و`blind_external_test` فيه `false`. والإيداعُ ليس في main ذلك المستودع.

**المدخل** تحليلٌ كتبه البنّاء لكلّ حالة.

**الموافقةُ ثلاثُ مبرهناتٍ، لا واحدة:**
- **القوّة** على الخمس والعشرين (`nabt_quwwa`).
- **حالةُ المرجع** على C01–C05 وحدها، فالمرجعُ عند NABT «Only C01–C05; not_applicable is excluded». وهي حالتُه لا هويّتُه: مدخلُ C01
  وC02 هنا واحد، وذهبُهما في `target_ids` مختلف. توافقه في C01–C04 (`nabt_marji`)، وتخالفه في C05 (`nabt_marji_C05`): الإشارةُ إلى اثنين
  «لا حكم» هنا باختيار المالك، وذهبُه «ambiguous».
- **الدافعُ والواقع** (`nabt_la_tarqiya`): «لا ترقية»، أي سلامةٌ لا نجاحُ تفسير، بنصّ NABT «absence of an unsafe promotion may be
  separately reported as safety, never full interpretation success». والدافعُ في عشرين حالةً مدخلُه `none` فهو غيرُ متعيّنٍ بالتعريف،
  وفي الخمس الباقية «بعد» أو «قبل»: ففرعُ `madhkur` لا يُختبر هنا. والواقعُ ممرَّرٌ ثابتًا `.laHukm`، ولم تُبنَ قضيّةٌ (m s v) لجمل NABT.

**الموافقةُ والمخالفةُ والضابط:**
- مدخلُ `khabar` هو مدخلُ S01 بعينه، ومتوقَّعُه هناك الخبرُ والإنشاءُ معًا (`Jisr/SakkJumlaQiyas.lean`: اختيارٌ بلا مرجّح). وعليه تقوم موافقةُ
  القوّة الأولى في عشرين حالة (N وV وT وC).
- ومدخلُ C05 (`hadha` مع `musharIthnan`) هو مدخلُ S38 بعينه، ومتوقَّعُه هناك «لا حكم». وكانت الشفرةُ المجمَّدة تُخرج فيه «محتمَلًا» فتوافق
  NABT وتتجاوز في الضابط؛ وبعد اختيار المالك «لا حكم» صار العكس (`nabt_marji_C05`). -/

inductive QuwwaNabt | assertPos | assertNeg | hypothetical | quoted | ghayr
  deriving DecidableEq, Repr

def ilaNabt : Quwwa → QuwwaNabt
  | .ithbat => .assertPos
  | .nafy => .assertNeg
  | .taliq => .hypothetical
  | .hikaya => .quoted
  | _ => .ghayr

/-- `madhkur` ليست من قيم NABT (قيمُ الدافع في مرجعه كلُّها `underdetermined`): اسمُها وحملُ العلّة والسببيّة عليها قراءتي. -/
inductive DafiNabt | underdetermined | madhkur
  deriving DecidableEq, Repr

/-- الدافعُ بلغة NABT: «مذكور» إذا كان الحكمُ علّةً أو سببيّةً بلا بديل، وإلّا غيرُ متعيّن (قراءتي). وما لا رابطَ له غيرُ متعيّن:
    فصفةُ الشيء لا تعني أنّها أثرُه (`sifaLaAthar`؛ وحملُه على منع NABT الدافعَ من قسم الكلمة `instinct_from_pos` قراءتي). -/
def dafiNabt : Option DakhilS → DafiNabt
  | none => .underdetermined
  | some d => if sabab d = [.illa] ∨ sabab d = [.sababiyya] then .madhkur else .underdetermined

/-- **لا دافعَ من الظرف ولا من «لمّا» ولا من «غير ذلك» ولا بلا رابط.** و«بعد» و«قبل» وحدهما ما يمنعه NABT باسم `causality_from_temporal_order`.
    وخروجُ «لمّا» من تعيين الوجهين ومن اشتراط قيمةٍ واحدة في `dafiNabt`، لا من نصّ. -/
theorem la_dafi_bila_dall (o : Option DakhilS)
    (h : o = none ∨ ∃ d : DakhilS, o = some d ∧ d.dall ∈ [Dall.baad, .qabl, .lamma, .ghayrDhalik]) :
    dafiNabt o = .underdetermined := by
  rcases h with rfl | ⟨⟨dl, s, a⟩, rfl, hd⟩
  · rfl
  · simp only [List.mem_cons, List.not_mem_nil, or_false] at hd
    rcases hd with rfl | rfl | rfl | rfl <;> simp [dafiNabt, sabab]

inductive MarjiNabt | resolved | ambiguous | unresolved | notApplicable
  deriving DecidableEq, Repr

def marjiNabt : Option DakhilM → MarjiNabt
  | none => .notApplicable
  | some d => match marji d with
    | .muayyan => .resolved
    | .muhtamal => .ambiguous
    | .laHukm => .unresolved

/-- **«هو» مع مفسِّرَين محتمَلٌ بلغة NABT** (على الشاهد؛ يحرس فرعَ `muhtamal` في `marjiNabt` بعد أن صارت C05 «لا حكم»). -/
theorem marjiNabt_huwa_mufassiran : marjiNabt (some ⟨.huwa, .mufassiran⟩) = .ambiguous := by
  decide

inductive WaqiNabt | notEstablished | established
  deriving DecidableEq, Repr

def waqiNabt (q : Quwwa) (w : Waqi.Hukm) : WaqiNabt :=
  if waqiJumla q w = .mafhum then .established else .notEstablished

/-- **لا يثبت واقعُ جملةٍ إلّا خبرًا حكمُه «مفهوم».** -/
theorem waqiNabt_iff (q : Quwwa) (w : Waqi.Hukm) :
    waqiNabt q w = .established ↔ (q = .ithbat ∨ q = .nafy) ∧ w = .mafhum := by
  cases q <;> cases w <;> simp [waqiNabt, waqiJumla]

structure HalaNabt where
  dq : DakhilQ
  ds : Option DakhilS
  dm : Option DakhilM
  deriving DecidableEq, Repr

structure MukhrajNabt where
  awwal : QuwwaNabt
  thani : List QuwwaNabt
  dafi : DafiNabt
  marji : MarjiNabt
  waqi : WaqiNabt
  deriving DecidableEq, Repr

/-- مخرجُ الصكّ بلغة NABT، وحكمُ الواقع `w` ممرَّرٌ إليه. -/
def sakkNabt (w : Waqi.Hukm) (h : HalaNabt) : MukhrajNabt :=
  ⟨ilaNabt (awwal h.dq), ((thani h.dq).filter (· != .laThani)).map ilaNabt, dafiNabt h.ds, marjiNabt h.dm,
   waqiNabt (awwal h.dq) w⟩

def khabar : DakhilQ := ⟨.laShay, .laQawl, .laQawl, .amma⟩
def zarf (d : Dall) : Option DakhilS := some ⟨d, .laYantabiq, .laYantabiq⟩

/-- تحليلُ البنّاء للحالات الخمس والعشرين بترتيبها. -/
def nabt25 : List (String × HalaNabt) := [
  ("N01", ⟨khabar, none, none⟩),
  ("N02", ⟨khabar, none, none⟩),
  ("N03", ⟨khabar, none, none⟩),
  ("N04", ⟨khabar, none, none⟩),
  ("N05", ⟨khabar, none, none⟩),
  ("V01", ⟨khabar, none, none⟩),
  ("V02", ⟨khabar, none, none⟩),
  ("V03", ⟨khabar, none, none⟩),
  ("V04", ⟨khabar, none, none⟩),
  ("V05", ⟨khabar, none, none⟩),
  ("T01", ⟨khabar, zarf .baad, none⟩),
  ("T02", ⟨khabar, zarf .qabl, none⟩),
  ("T03", ⟨khabar, zarf .baad, none⟩),
  ("T04", ⟨khabar, zarf .qabl, none⟩),
  ("T05", ⟨khabar, zarf .baad, none⟩),
  ("C01", ⟨khabar, none, some ⟨.ana, .mutakallimMuayyan⟩⟩),
  ("C02", ⟨khabar, none, some ⟨.ana, .mutakallimMuayyan⟩⟩),
  ("C03", ⟨khabar, none, some ⟨.hadha, .musharWahid⟩⟩),
  ("C04", ⟨khabar, none, some ⟨.hadha, .musharWahid⟩⟩),
  ("C05", ⟨khabar, none, some ⟨.hadha, .musharIthnan⟩⟩),
  ("Q01", ⟨⟨.lam, .laQawl, .laQawl, .amma⟩, none, none⟩),
  ("Q02", ⟨⟨.in_, .laQawl, .laQawl, .amma⟩, none, none⟩),
  ("Q03", ⟨⟨.laShay, .qala, .jumlaFiliyya, .amma⟩, none, none⟩),
  ("Q04", ⟨⟨.lam, .qala, .jumlaFiliyya, .amma⟩, none, none⟩),
  ("Q05", ⟨⟨.in_, .laQawl, .laQawl, .amma⟩, none, none⟩)]

/-- ذهبُ NABT في هذه الحقول، بترتيب الحالات: (القوّةُ الأولى، قوّةُ الثانية، الدافع، المرجع، الواقع). -/
def dhahab25 : List (String × MukhrajNabt) := [
  ("N01", ⟨.assertPos, [], .underdetermined, .notApplicable, .notEstablished⟩),
  ("N02", ⟨.assertPos, [], .underdetermined, .notApplicable, .notEstablished⟩),
  ("N03", ⟨.assertPos, [], .underdetermined, .notApplicable, .notEstablished⟩),
  ("N04", ⟨.assertPos, [], .underdetermined, .notApplicable, .notEstablished⟩),
  ("N05", ⟨.assertPos, [], .underdetermined, .notApplicable, .notEstablished⟩),
  ("V01", ⟨.assertPos, [], .underdetermined, .notApplicable, .notEstablished⟩),
  ("V02", ⟨.assertPos, [], .underdetermined, .notApplicable, .notEstablished⟩),
  ("V03", ⟨.assertPos, [], .underdetermined, .notApplicable, .notEstablished⟩),
  ("V04", ⟨.assertPos, [], .underdetermined, .notApplicable, .notEstablished⟩),
  ("V05", ⟨.assertPos, [], .underdetermined, .notApplicable, .notEstablished⟩),
  ("T01", ⟨.assertPos, [], .underdetermined, .notApplicable, .notEstablished⟩),
  ("T02", ⟨.assertPos, [], .underdetermined, .notApplicable, .notEstablished⟩),
  ("T03", ⟨.assertPos, [], .underdetermined, .notApplicable, .notEstablished⟩),
  ("T04", ⟨.assertPos, [], .underdetermined, .notApplicable, .notEstablished⟩),
  ("T05", ⟨.assertPos, [], .underdetermined, .notApplicable, .notEstablished⟩),
  ("C01", ⟨.assertPos, [], .underdetermined, .resolved, .notEstablished⟩),
  ("C02", ⟨.assertPos, [], .underdetermined, .resolved, .notEstablished⟩),
  ("C03", ⟨.assertPos, [], .underdetermined, .resolved, .notEstablished⟩),
  ("C04", ⟨.assertPos, [], .underdetermined, .resolved, .notEstablished⟩),
  ("C05", ⟨.assertPos, [], .underdetermined, .ambiguous, .notEstablished⟩),
  ("Q01", ⟨.assertNeg, [], .underdetermined, .notApplicable, .notEstablished⟩),
  ("Q02", ⟨.hypothetical, [.hypothetical], .underdetermined, .notApplicable, .notEstablished⟩),
  ("Q03", ⟨.assertPos, [.quoted], .underdetermined, .notApplicable, .notEstablished⟩),
  ("Q04", ⟨.assertNeg, [.quoted], .underdetermined, .notApplicable, .notEstablished⟩),
  ("Q05", ⟨.hypothetical, [.hypothetical], .underdetermined, .notApplicable, .notEstablished⟩)]

/-- مخرجُ الصكّ على الحالات الخمس والعشرين، والواقعُ ممرَّرٌ ثابتًا `.laHukm`. -/
def mukhraj25 : List (String × MukhrajNabt) := nabt25.map (fun p => (p.1, sakkNabt .laHukm p.2))

/-- حالاتُ المرجع عند NABT. -/
def halatMarji : List String := ["C01", "C02", "C03", "C04", "C05"]

/-- **القوّةُ على الخمس والعشرين:** الأولى وقوى الثانية كذهب NABT. -/
theorem nabt_quwwa :
    mukhraj25.map (fun p => (p.1, p.2.awwal, p.2.thani)) = dhahab25.map (fun p => (p.1, p.2.awwal, p.2.thani)) := by
  decide

/-- **حالةُ المرجع على C01–C04** كذهب NABT (لا هويّتُه). -/
theorem nabt_marji :
    (mukhraj25.filter (fun p => (halatMarji.take 4).contains p.1)).map (fun p => (p.1, p.2.marji)) =
      (dhahab25.filter (fun p => (halatMarji.take 4).contains p.1)).map (fun p => (p.1, p.2.marji)) := by
  decide

/-- **وفي C05 يخالفه:** الإشارةُ إلى اثنين «لا حكم» هنا (`ishara_ithnan_la_hukm`)، وذهبُه «ambiguous». -/
theorem nabt_marji_C05 :
    (mukhraj25.filter (fun p => p.1 == "C05")).map (fun p => p.2.marji) = [.unresolved] ∧
    (dhahab25.filter (fun p => p.1 == "C05")).map (fun p => p.2.marji) = [.ambiguous] := by
  decide

/-- **لا ترقية في الدافع ولا في الواقع على الخمس والعشرين:** سلامةٌ لا نجاحُ تفسير. -/
theorem nabt_la_tarqiya :
    mukhraj25.map (fun p => (p.1, p.2.dafi, p.2.waqi)) = dhahab25.map (fun p => (p.1, p.2.dafi, p.2.waqi)) := by
  decide

/-! ## ٦. الأسانيد

قطعٌ حرفيّة: (الاسم، الملفّ، أوّلُ سطر، آخرُ سطر، النصّ). يفحصها `tahaqquq/test_sakk.py` على المودَع موصولةَ الأسطر، بحذف البادئة
(«~~» أو «# » أو «### | ») وعلامات الصفحات والمخطوط وتوحيد البياض، وبأدنى مدًى. -/

def asanid : List (String × String × Nat × Nat × String) := [
  ("khabar", "a2.txt", 767, 767, "إن كان محتملاً التصديق والتكذيب فهو الخبر"),
  ("insha", "a2.txt", 896, 896, "أن الإنشاء لا يحتمل التصديق والتكذيب"),
  ("nafyLam", "sibawayhi.txt", 9783, 9783, "إذا قال فعل فإن نفيه لم يفعل"),
  ("lamJazm", "mughni.txt", 6404, 6404, "حرف جزم لنفي المضارع وقلبه ماضيا"),
  ("taliqIn", "mughni.txt", 6114, 6115, "وخاصية إن تعليق أمر بأمر مستقبل محتمل"),
  ("taliqIhtimal", "mughni.txt", 2228, 2229, "والمعلق يحتمل الوقوع وعدمه"),
  ("ghayrWajib", "sibawayhi.txt", 9622, 9623, "فقال الجزاء هاهنا خطأ لا يكون الجزاء أبدا حتى يكون الكلام الأول غير واجب"),
  ("qultHikaya", "sibawayhi.txt", 1272, 1273, "واعلم أن قلت إنما وقعت فى الكلام العرب على أن يحكى بها"),
  ("qalaInna", "sibawayhi.txt", 10023, 10023, "وذلك لأنك أردت أن تحكي قوله"),
  ("qultLaZann", "sibawayhi.txt", 1281, 1282, "ولم تجعل قلت كظننت لأنها إنما أصلها عندهم أن يكون ما بعدها محكي ا"),
  ("sulaym", "sibawayhi.txt", 1294, 1294, "وهم بنو سليم يجعلون باب قلت أجمع مثل ظننت"),
  ("sulaymAlfiyya", "alfiyya.txt", 301, 301, "وأجري القول كظن مطلقا ... عند سليم"),
  ("taqulZann", "sibawayhi.txt", 1277, 1277, "إلا تقول فى الاستفهام شبهوها بتظن"),
  ("taqulAlfiyya", "alfiyya.txt", 299, 299, "وكتظن اجعل تقول إن ولي ... مستفهما به ولم ينفصل"),
  ("taqulRaf", "sibawayhi.txt", 1292, 1293, "وإن شئت رفعت بما نصبت فجعلته حكاية"),
  ("yunus", "sibawayhi.txt", 10030, 10030, "إذا لم ترد الحكاية وجعلت تقول مثل تظن"),
  ("yunusHikaya", "sibawayhi.txt", 10031, 10031, "وإن أردت الحكاية قلت متى تقول إنك ذاهب"),
  ("ihtimalQawl", "mughni.txt", 9629, 9629, "قد يقع بعد القول ما يحتمل الحكاية وغيرها"),
  ("mafulLahu", "qatr.txt", 293, 293, "والمفعول له، وهو المصدر المعلل لحدث شاركه وقتا وفاعلا"),
  ("udhr", "sibawayhi.txt", 3659, 3659, "هذا باب ما ينتصب من المصادر لأنه عذر لوقوع الأمر"),
  ("faqdShart", "qatr.txt", 294, 294, "فإن فقد المعلل شرطا جر بحرف التعليل"),
  ("lamMaani", "alfiyya.txt", 491, 491, "واللام للملك وشبهه وفي"),
  ("lamTalil", "mughni.txt", 4802, 4802, "السادس التعليل"),
  ("kay", "sibawayhi.txt", 18402, 18403, "وأما كي فجواب لقوله كيمه كما يقول لمه فتقول ليفعل كذا وكذا"),
  ("kayLam", "mughni.txt", 4161, 4161, "أن تكون بمنزلة لام التعليل معنى وعملا"),
  ("hattaWajhan", "sibawayhi.txt", 8792, 8792, "اعلم أن حتى تنصب على وجهين"),
  ("hattaKay", "sibawayhi.txt", 8796, 8796, "وذلك إذا جاءت مثل كي التي فيها إضمار أن وفي معناها"),
  ("hattaRafWajhan", "sibawayhi.txt", 8797, 8797, "واعلم أن حتى يرفع الفعل بعدها على وجهين"),
  ("hattaRaf", "sibawayhi.txt", 8798, 8798, "تعني أنه كان دخول متصل بالسير كاتصاله به بالفاء"),
  ("hattaAlan", "sibawayhi.txt", 8804, 8805, "وأما الوجه الآخر فإنه يكون السير قد كان وما أشبهه ويكون الدخول وما أشبهه الآن"),
  ("hattaLamYuaddih", "sibawayhi.txt", 8889, 8890, "إذا كان دخول زيد لم يؤده سيرك ولم يكن سببه"),
  ("hattaLarafata", "sibawayhi.txt", 8892, 8892, "لرفعت لأنك جعلت دخول ثقلك يؤديه سيرك"),
  ("hattaMinSabab", "sibawayhi.txt", 8895, 8895, "إذا جعلت دخول زيد من سبب سيرك وهو الذي أداه"),
  ("hattaMusabbab", "mughni.txt", 2836, 2838, "والثاني أن يكون مسببا عما قبلها فلا يجوز سرت حتى تطلع الشمس"),
  ("hattaRafIllaSabab", "sibawayhi.txt", 8896, 8897, "لأن رفع الأول لا يكون إلا وسبب دخوله سيره"),
  ("hattaLaYatasabbab", "mughni.txt", 2838, 2839, "أما الأول فلأن طلوع الشمس لا يتسبب عن السير"),
  ("faSababiyya", "qatr.txt", 108, 108, "وبعد فاء السببية"),
  ("faJawab", "alfiyya.txt", 895, 895, "وبعد فا جواب نفي أو طلب"),
  ("faWajhan", "sibawayhi.txt", 8945, 8945, "فالنصب على وجهين من المعاني"),
  ("faLaw", "sibawayhi.txt", 8946, 8946, "أي لو أتيتني لحدثتني"),
  ("faAbadan", "sibawayhi.txt", 8946, 8947, "وأما الآخر فما تأتيني أبدا إلا لم تحدثني"),
  ("faGhalib", "mughni.txt", 3689, 3689, "والأمر الثالث السببية وذلك غالب في العاطفة"),
  ("faTartib", "mughni.txt", 3693, 3693, "وقد تجيء في ذلك لمجرد الترتيب"),
  ("liAnna", "sibawayhi.txt", 9863, 9863, "قلت لمه قلت لأن ذاك كذلك"),
  ("anLamMuqaddara", "mughni.txt", 711, 711, "وقبلها لام العلة مقدرة"),
  ("lammaTartib", "mughni.txt", 670, 671, "ولما تفيد وقوع الفعل الثاني عقب الأول وترتبه عليه"),
  ("lammaSibawayhi", "sibawayhi.txt", 18529, 18529, "فهي للأمر الذي قد وقع لوقوع غيره"),
  ("lammaSabab", "sibawayhi.txt", 18530, 18531, "فالأول سبب ما وقع وما لم يقع"),
  ("lammaZarf", "mughni.txt", 6490, 6491, "وزعم ابن السراج وتبعه الفارسي وتبعهما ابن جني وتبعهم جماعة أنها ظرف بمعنى حين"),
  ("zarfZaman", "mughni.txt", 7572, 7572, "وإنما هما في الأصل صفتان للزمان"),
  ("zarfSibawayhi", "sibawayhi.txt", 4200, 4200, "وقبل وبعد وإزاء وحذاء وما أشبه هذا من الأمكنة والأزمنة"),
  ("sababHatman", "a1.txt", 269, 269, "حتى يصح أن يكون سبباً لا بد أن ينتِج المسبَّب حتماً"),
  ("hala", "a1.txt", 269, 269, "وهذا بخلاف الحالة، فإنها ظرف خاص بملابسات خاصة يحصل فيها الشيء عادة"),
  ("filBiwasita", "a2.txt", 1431, 1431, "بخلاف فعل الرسول فإنه لا يدل بنفسه على كونه بياناً بل بالواسطة"),
  ("sifaLaAthar", "a3.txt", 137, 137, "فكون الشيء صفته كذا، لا تعني أن هذه الصفة أثره"),
  ("damir", "qatr.txt", 124, 124, "الضمير وهو ما دل على متكلم أو مخاطب أو غائب"),
  ("idmar", "sibawayhi.txt", 4457, 4458, "لأنك إنما تضمر اسما بعد ما تعلم أن من يحدث قد عرف من تعنى"),
  ("ishara", "sibawayhi.txt", 4471, 4472, "أراد أن يقرب [ ربه ] شيئا ويشير إليه لتعرفه بقلبك وبعينك"),
  ("mufassir", "a2.txt", 749, 749, "لأن المضمرات لا بد لها من شيء يفسرها"),
  ("qarina", "a2.txt", 918, 918, "فلا يحمل على أحدهما ما لم توجد قرينة"),
  ("taraddud", "a2.txt", 1419, 1419, "التردد في عود الضمير")]

/-! ## ٧. الربطُ بقطع Lean القائمة -/

/-- لفظُ الأداة. -/
def adatLafz : Adat → Option String
  | .laShay => none
  | .lam => some "لم"
  | .in_ => some "إن"

/-- **التعليقُ في الأولى بأداةٍ يُجازى بها في باب الجزاء المبنيّ، لا بغيرها** (`Jisr.BabJaza.sinfOf`). -/
theorem taliq_iff_jaza (d : DakhilQ) :
    awwal d = .taliq ↔ ∃ l, adatLafz d.adat = some l ∧ Jisr.BabJaza.sinfOf l = .jaza := by
  obtain ⟨a, q, m, l⟩ := d
  cases a <;> cases q <;> simp [awwal, adatLafz] <;> decide

/-- **«لم» صدرُ نفي الماضي المنقطع** في `Aql.Awwaliyyat` (الكتاب س9783: `nafyLam`): مطابقةُ لفظ، لا توافقُ حكم. -/
theorem lam_nafy_madi :
    adatLafz .lam = some "لم" ∧ Aql.Awwaliyyat.nafy .madiMunqati = "لم يفعل" ∧ Aql.Awwaliyyat.ithbat .madiMunqati = "فعل" := by
  decide

/-- **المفعولُ له أسلوبٌ في جرد القطر بسطره** (`Jisr.Ikhbar.satr`)، وسندُ `masdarMansub` هنا السطرُ نفسُه (`mafulLahu`): مطابقةُ رقم سطر. -/
theorem mafulLahu_qatr :
    Jisr.Ikhbar.satr .mafulLahu = 293 ∧
    asanid.any (fun x => x.1 == "mafulLahu" && x.2.1 == "qatr.txt" && x.2.2.1 == Jisr.Ikhbar.satr .mafulLahu) = true := by
  decide

end Jisr.SakkJumla
