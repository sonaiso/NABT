# تدقيق الغانم: المعرفة والعدد والجنس والاعتلال

**المصدر المثبت:** `Saleh1967/Alghanem@9d8fa03a51f894416e0abaf3b6821c5ae6441dcd`. بتاريخ 2026-10-23 يطابق هذا الختم رأس الفرع العام الذي تحققت منه المهمة الأم. الجرد شمل **165 ملف Lean متتبعا**، ثم القراءة المركزة لـ **19 ملفا و184 تصريحا**. يحمل [السجل الآلي](source_audit_alghanem.json) بصمات جميع ملفات Lean، ونطاقات السطر/البايت وبصمات التصريحات المختارة. لم أعد بناء المنبع؛ وصف «مبرهنة» أدناه وصف لعبارة البرهان الموجودة في المصدر المثبت، وليس شهادة kernel جديدة.

المحصلة القابلة للنقل هي **قوانين مشروطة بصفات معطاة، وتعدادات، وتحويلات من جذر معلوم، وشواهد جزئية**. لا يثبت هذا الجرد أن الغانم يكتسب جميع الصفات المطلوبة من كلمة جديدة. تفاصيل النثر الأصلي محفوظة في [29 نافذة مثبتة](primary_grammar_passages.json)، وخريطة كل طلب في [التغطية](requested_category_coverage.json).

## العقود والحدود

### AN01 — المعارف الستة تعداد لا محلل نص

[formal/a116/A116/Ihala.lean:208–232](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/Ihala.lean#L208-L232).

**التصريحات:** `A116.Ihala.Marifa`, `A116.Ihala.HajaM`, `A116.Ihala.hajaM`, `A116.Ihala.marifat`, `A116.Ihala.marifa_ism`.

**Input:** A supplied Marifa enum: pronoun, demonstrative, proper name, article-bearing, relative, annexed.

**Result / proof scope:** A list of six kinds and four distinct external needs. marifa_ism proves list length6, four filterMap needs, Nodup, and no need for alam/muarraf; its statement does not contain an IsNoun predicate.

**Boundary:** No raw-text definiteness extraction; mudaf must be scoped to the relevant definite complement, not arbitrary idafa.

### AN02 — الجنس والعدد في الموصول صفات معطاة

[formal/a116/A116/Ihala.lean:104–170](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/Ihala.lean#L104-L170).

**التصريحات:** `A116.Ihala.Adad`, `A116.Ihala.Jins`, `A116.Ihala.Simah`, `A116.Ihala.Mawsul`, `A116.Ihala.Sila`, `A116.Ihala.laiq`, `A116.Ihala.tamm`, `A116.Ihala.ismi_yahtaj_aid`, `A116.Ihala.man_lafz_wa_maana`.

**Input:** Supplied singular/dual/plural and masculine/feminine features plus a list of permitted relative-pronoun readings.

**Result / proof scope:** Checks membership of an anaphoric feature bundle in allowed bundles and clause completeness. General conditional checks and finite witnesses, including multiple readings for man.

**Boundary:** Agreement compatibility is not acquisition of lexical gender/number, and not a universal nonrational-plural agreement rule.

### AN03 — حصر مرجع الضمير يحفظ تعدد المرشحين

[formal/a116/A116/IhalaHasr.lean:53–235](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/IhalaHasr.lean#L53-L235).

**التصريحات:** `A116.IhalaHasr.Adad`, `A116.IhalaHasr.Naw`, `A116.IhalaHasr.Sifa`, `A116.IhalaHasr.damirSifa`, `A116.IhalaHasr.aidSifa`, `A116.IhalaHasr.mawsulSifa`, `A116.IhalaHasr.sifat_counts`, `A116.IhalaHasr.laiq`, `A116.IhalaHasr.aidOf`, `A116.IhalaHasr.Unsur`, `A116.IhalaHasr.yaliq`, `A116.IhalaHasr.murashshahun`, `A116.IhalaHasr.ihala`, `A116.IhalaHasr.murashshah_precedes`, `A116.IhalaHasr.murashshah_laiq`, `A116.IhalaHasr.mutaayyin_iff`, `A116.IhalaHasr.no_guess`, `A116.IhalaHasr.two_marji_no_guess`.

**Input:** Typed input sequence; noun number and gender are inputs (SIFAT_ARE_INPUT). Closed tables contain10 pronouns,5 suffixes,7 relatives.

**Result / proof scope:** Preceding compatible antecedent candidates; unique/multiple/none result. Candidate precedence and compatibility; singleton iff selected; no selection from a nonsingleton candidate list.

**Boundary:** aidOf matches a cell suffix; it does not prove morphological segmentation. The source does not infer noun features from cells or validate natural-language antecedent truth.

### AN04 — النكرة والعموم يحتاجان قرينة مصنفة

[formal/a116/A116/Umum.lean:118–185](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/Umum.lean#L118-L185).

**التصريحات:** `A116.Umum.Qarina`, `A116.Umum.Tanawul`, `A116.Umum.tanawul`, `A116.Umum.umum`, `A116.Umum.nakira_nafy`, `A116.Umum.nafi_la_yughayyir`, `A116.Umum.takhsis_baqi`, `A116.Umum.siyaq_yufarriq`, `A116.Umum.al_idafa`, `A116.Umum.baqi`, `A116.Umum.baqi_iff`.

**Input:** Supplied Qarina (alJins,alJam,idafaJins,idafaJam,nakiraNafy,filManfi,nakiraIthbat) and takhsis Bool.

**Result / proof scope:** General scope, remainder scope, or no judgment; explicit remainder filtering. Conditional laws of the declared enum and filter membership; all grammatical/contextual features are already supplied.

**Boundary:** Do not turn the enum into a parser: article presence alone does not establish genericity; absence does not establish indefiniteness; no automatic universal quantification.

### AN05 — المثنى والجمع والمنقوص أبواب إعراب معلومة مسبقا

[formal/a116/A116/Qism.lean:68–195](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/Qism.lean#L68-L195).

**التصريحات:** `A116.Qism.Cls`, `A116.Qism.Ending`, `A116.Qism.ending`, `A116.Qism.pairs`, `A116.Qism.pairs_length`, `A116.Qism.cands`, `A116.Qism.read₁`, `A116.Qism.read_sound`, `A116.Qism.read_best`, `A116.Qism.coverage_counts`, `A116.Qism.naive_wrong_count`, `A116.Qism.naive_yadu`, `A116.Qism.blind_abstains`.

**Input:** Supplied noun/verb class (including dual, sound masculine/feminine plural, maqsur, manqus), case and/or abstract visible ending.

**Result / proof scope:** Abstract ending table and consensus case reader over45 legal class/case pairs. read_sound is candidate soundness; read_best needs nonempty unanimous candidates. Coverage5/11/24 is finite model coverage, not text accuracy.

**Boundary:** No extraction of class from suffix. iManqus abstracts raf/jarr as ya and does not implement every indefinite deletion or pause variant. The table lacks plural lexical admission.

### AN06 — نيابة علامة الجمع لا تثبت صنفه

[formal/a116/A116/Amil.lean:63–197](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/Amil.lean#L63-L197).

**التصريحات:** `A116.Amil.naib`, `A116.Amil.naib_classes`, `A116.Amil.naib_by_haraka`, `A116.Amil.mamul`, `A116.Amil.ism_no_jazm`, `A116.Amil.fil_no_jarr`, `A116.Amil.idafa_jarr`.

**Input:** Already typed Qism class plus governor or relation.

**Result / proof scope:** Alternative ending and case licensing, including sound feminine accusative kasra. Finite class checks and general statements about declared governor/relation functions.

**Boundary:** No new singular/dual/plural or gender inference; idafa_jarr concerns case of complement, not definiteness of the head.

### AN07 — ألف التأنيث ليست جنس المدلول

[formal/a116/A116/Tanith.lean:25–122](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/Tanith.lean#L25-L122).

**التصريحات:** `A116.Tanith.Kind`, `A116.Tanith.radMatch`, `A116.Tanith.inOrder`, `A116.Tanith.finalAlif`, `A116.Tanith.tanith`, `A116.Tanith.tanith_needs_final`, `A116.Tanith.tanith_needs_root`, `A116.Tanith.tanith_partition`, `A116.Tanith.witnesses`, `A116.Tanith.ilhaq_named`, `A116.Tanith.shape_blind`, `A116.Tanith.no_shape_function`.

**Input:** A supplied skeleton and root; subsequence matching permits declared weak/hamza variants.

**Result / proof scope:** Optional final-alif suffix kind maqsura/mamduda. Theorems prove classifier conditions and partition; examples include فقهاء/أصدقاء/أولياء. ilhaq_named exposes علباء classified as mamduda despite an ilhaq exception.

**Boundary:** No proof of root truth or nonempty root, no lexical-gender theorem; shape cannot decide the source function. Do not infer feminine referents from a suffix-name.

### AN08 — ساجدين شاهد مخصوص لا قانون جنس عام

[formal/a116/A116/Khawass.lean:84–272](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/Khawass.lean#L84-L272).

**التصريحات:** `A116.Khawass.sufuf`, `A116.Khawass.saffOf`, `A116.Khawass.aqilOf`, `A116.Khawass.Jam`, `A116.Khawass.haqqJam`, `A116.Khawass.hukmJam`, `A116.Khawass.sajidin`, `A116.Khawass.qarinatan_tattafiqan`.

**Input:** Finite deposited referent-kind rationality table and observed wawNun/alifTa choice.

**Result / proof scope:** haqiqa/majaz/no judgment according to source-specific analogy for rational description. sajidin is a closed witness; qarinatan_tattafiqan quantifies over deposited rows. haqqJam itself contains only aqil Bool and no grammatical-gender field.

**Boundary:** Cannot transfer aqil→wawNun and nonaqil→alifTa as a universal plural law. Rational feminine nouns and nonrational masculine nouns require separate axes.

### AN09 — وصف اعتلال الجذر وحراسة الترخيص الصوتي

[formal/a116/A116/Tasrif.lean:63–726](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/Tasrif.lean#L63-L726).

**التصريحات:** `A116.Tasrif.Cls`, `A116.Tasrif.cls`, `A116.Tasrif.Cls.weak`, `A116.Tasrif.Sifa`, `A116.Tasrif.sifa`, `A116.Tasrif.allSifa`, `A116.Tasrif.allSifa_length`, `A116.Tasrif.lift`, `A116.Tasrif.madi_exhausted`, `A116.Tasrif.mudari_exhausted`, `A116.Tasrif.amr_exhausted`, `A116.Tasrif.ajwafSifas`, `A116.Tasrif.madd_drop_forced`, `A116.Tasrif.waqa_waa`.

**Input:** A supplied3-radical root with NoAlif, prescribed form/vowels/prefix/mood; weak is only waw/ya, hamz is distinct.

**Result / proof scope:** Canonical feature abstraction and transformed templates; phonotactic licensing. 250 abstract feature combinations lift to NoAlif roots. madi covers three vowels; mudari/amr babs are the declared bare/FormIV pair. madd_drop_forced is a phonotactic rejection theorem under ajwafSifas.

**Boundary:** General quantified licensing is not lexical attestation or proof that every possible vowel combination is an Arabic conjugation. No inverse recovery of the root or its lexical bab.

### AN10 — تحويلات المعتل مرتبطة بالجذر والباب

[formal/a116/A116/Mudari.lean:48–314](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/Mudari.lean#L48-L314).

**التصريحات:** `A116.Mudari.Form`, `A116.Mudari.isWeak`, `A116.Mudari.body`, `A116.Mudari.mithal`, `A116.Mudari.hollowGo`, `A116.Mudari.hollow`, `A116.Mudari.defective`, `A116.Mudari.dropMadd`, `A116.Mudari.mudariT`, `A116.Mudari.refRoots`, `A116.Mudari.babs`, `A116.Mudari.reference_licensed`.

**Input:** Supplied root, one of nine forms I,II,III,IV,V,VI,VII,VIII,X, vowel, prefix and ending.

**Result / proof scope:** Conditional mithal/hollow/defective transformations and generated cell strings. reference_licensed holds over the listed reference roots and allowed parameter lists; other theorems have their own structural scopes.

**Boundary:** defective is weak-final verbal transformation, not nominal manqus. FormIX is absent; no full lexical/semantic completeness claim.

### AN11 — السطح لا يستعيد واو الجذر أو ياءه وحده

[formal/a116/A116/Neutral.lean:152–241](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/Neutral.lean#L152-L241).

**التصريحات:** `A116.Neutral.realizeN`, `A116.Neutral.rootOf`, `A116.Neutral.neutral_forgets_weak`, `A116.Neutral.lafif_witnesses`, `A116.Neutral.weak_licensed`.

**Input:** Supplied root, template, entry/exit and ending.

**Result / proof scope:** Weak-root realization and reference examples. neutral_forgets_weak maps both قول and قيل input roots to the same قال cell sequence; lafif_witnesses explicitly realizes هوى and أحيا.

**Boundary:** The theorem exhibits a noninjective forward map, not an algorithm that acquires the actual lexical root. Preserve alternatives and origin evidence.

### AN12 — إعادة المحذوف ليست ترخيص الحذف لغويا

[formal/a116/A116/Ilal.lean:53–174](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/Ilal.lean#L53-L174).

**التصريحات:** `A116.Ilal.admissible_replace_carrier`, `A116.Ilal.vowelled_to_sukun_between_vowelled`, `A116.Ilal.hadhf_ayn_forced`, `A116.Ilal.qalb_ayn_restore`, `A116.Ilal.hadhf_ayn_restore`, `A116.Ilal.qalb_lam_restore`, `A116.Ilal.hadhf_lam_restore`, `A116.Ilal.ibdal_restore`.

**Input:** Explicit cell strings, edit locations/residuals and structural phonotactic hypotheses.

**Result / proof scope:** Preservation of model admissibility or exact restoration of recorded edits. Conditional transformation and reconstruction proofs.

**Boundary:** An inverse edit record preserves information; it does not establish which linguistic edit or lexical reading the input actually has.

### AN13 — جمع التكسير لا تحدده صيغة مفرد واحدة

[suspended/samai/lean/BrokenPlural.lean:10–214](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/suspended/samai/lean/BrokenPlural.lean#L10-L214).

**التصريحات:** `Ghanem.Plural.table`, `Ghanem.Plural.F`, `Ghanem.Plural.F₀`, `Ghanem.Plural.F0_domain`, `Ghanem.Plural.F0_hits`, `Ghanem.Plural.F_domain`, `Ghanem.Plural.F_hits`, `Ghanem.Plural.F_only_miss`, `Ghanem.Plural.khalifa_two_plurals`, `Ghanem.Plural.no_plural_starts_with_sukun`, `Ghanem.Plural.hamza_plural_before_sukun`, `Ghanem.Plural.triliteral_not_function`.

**Input:** A generated130-row root/singular-pattern/plural-pattern table; reported sound-root, pause-form QAC scope.

**Result / proof scope:** Pattern-to-pattern candidate functions F/F0 and finite match statistics. F0:18/22; after excluding masculine faail F:18/19; خليفة has two plural patterns. triliteral_not_function disproves a universal function of singular pattern alone over this table.

**Boundary:** Suspended research module. It does not parse new words or prove all broken-plural correspondences. The hamza theorem checks !isVowel on a character, not an explicit sukun annotation. Gender is not recovered.

### AN14 — المصدر القاموسي اختبار محدود لا قانون شامل

[suspended/samai/lean/LexSamai.lean:27–1616](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/suspended/samai/lean/LexSamai.lean#L27-L1616).

**التصريحات:** `Ghanem.LexSamai.RootType`, `Ghanem.LexSamai.W`, `Ghanem.LexSamai.taf_total`, `Ghanem.LexSamai.naqis_all_tafila`, `Ghanem.LexSamai.mahmuz_split`, `Ghanem.LexSamai.salim_split`, `Ghanem.LexSamai.W_hits`, `Ghanem.LexSamai.F`, `Ghanem.LexSamai.F_domain`, `Ghanem.LexSamai.F_hits`, `Ghanem.LexSamai.F_af3al_sifa`, `Ghanem.LexSamai.F_without_sifa`, `Ghanem.LexSamai.G`, `Ghanem.LexSamai.G_domain`, `Ghanem.LexSamai.G_hits`.

**Input:** Deposited lexical rows with supplied root classes and singular/plural patterns.

**Result / proof scope:** Table counts and pattern predictions. W602/609; observed naqis29/29 tafila. F531/749, post-measurement exclusion gives531/595; G136/160.

**Boundary:** Suspended finite evidence with explicitly post-hoc exclusion; no universal plural generation, gender classifier or equivalence of verbal naqis and nominal manqus.

### AN15 — الأجوف وفعول: اتجاه إحصائي في صفوف معطاة

[suspended/samai/lean/AjwafFuul.lean:8–524](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/suspended/samai/lean/AjwafFuul.lean#L8-L524).

**التصريحات:** `Ghanem.AjwafFuul.RT`, `Ghanem.AjwafFuul.qamus`, `Ghanem.AjwafFuul.n`, `Ghanem.AjwafFuul.fu`, `Ghanem.AjwafFuul.counts`, `Ghanem.AjwafFuul.min_sample`, `Ghanem.AjwafFuul.direction`.

**Input:** 504 deposited dictionary rows already tagged by RT.

**Result / proof scope:** Counts156 hollow rows/17 fuul versus202 sound/56 fuul; a strict ratio comparison. Finite arithmetic and minimum sample size, not a grammatical impossibility theorem.

**Boundary:** No root classifier; the result neither excludes fuul from hollow roots nor establishes a productive law.

### AN16 — رفع العلمية في نموذج المنع ليس اكتساب النكرة

[formal/a116/A116/Mamnu.lean:36–90](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/Mamnu.lean#L36-L90).

**التصريحات:** `A116.Mamnu.Sifat`, `A116.Mamnu.strong`, `A116.Mamnu.wasfPair`, `A116.Mamnu.alamPair`, `A116.Mamnu.mamnu`, `A116.Mamnu.nakira_munsarif`, `A116.Mamnu.tanwin_munsarif`, `A116.Mamnu.al_munsarif`.

**Input:** Supplied semantic/shape flags, including alam, wasf, tanwin and al.

**Result / proof scope:** Boolean model of prohibition under the declared flags. nakira_munsarif explicitly clears alam while assuming no strong cause and no descriptive pair.

**Boundary:** This theorem does not infer nakira from a token, does not prove all definiteness absent, and does not make tanwin imply indefinite.

### AN17 — عد السلاسل ليس العدد والمعدود في النحو

[formal/a116/A116/Count.lean:42–186](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/Count.lean#L42-L186).

**التصريحات:** `A116.code`, `A116.decode`, `A116.decode_code`, `A116.code_decode`, `A116.U`, `A116.cellFold`, `A116.cellFold_injective`, `A116.cellFold_surjective`, `A116.U_succ_succ`.

**Input:** Lists of the116 declared cells with a specific admissibility automaton.

**Result / proof scope:** A bijection/rank and counts U(n+2)=87U(n+1)+87*29U(n). General model counting and inversion for every length.

**Boundary:** Not cardinal numeral spelling, noun agreement, grammatical number or counting external objects.

### AN18 — الترقيم العام والمفهوم العددي مجالان آخران

[formal/a116/A116/Numbering.lean:137–219](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/Numbering.lean#L137-L219).

**التصريحات:** `A116.Numbering.atomNumber`, `A116.Numbering.atomNumber_injective`, `A116.Numbering.atomNumber_surjective`, `A116.Numbering.pair`, `A116.Numbering.pair_injective`, `A116.Numbering.pair_surjective`.

**Input:** Cell strings or pairs of natural numbers.

**Result / proof scope:** Injective/surjective numbering and Cantor pairing. Arithmetic coding proofs.

**Boundary:** No bridge from code value to counted entities or nominal singular/dual/plural.

### AN19 — مفهوم العدد يستقبل سياقه ولا يحلل صياغته

[formal/a116/A116/MantuqMafhum.lean:120–253](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/MantuqMafhum.lean#L120-L253).

**التصريحات:** `A116.MantuqMafhum.Qayd`, `A116.MantuqMafhum.mukhalafa`, `A116.MantuqMafhum.hasr_arbaa`, `A116.MantuqMafhum.yumal_iff`, `A116.MantuqMafhum.shawahid`.

**Input:** Supplied Qayd.adad context Bool, blockers and a supplied meaning string.

**Result / proof scope:** Whether a semantic contrary implication is usable under that encoded context. General conditional gating and finite quoted witnesses.

**Boundary:** Not cardinal gender agreement, parsing number expressions or independently discovering the supplied meaning.

## قرارات لازمة قبل التنفيذ

1. **لا جنس من صيغة الجمع.** `Khawass.haqqJam` لا يحتوي أصلا حقلا للجنس، و`Tanith.tanith` يتحدث عن صورة لاحقة مع جذر معطى. تقابل ون/ات في ساجدين لا يغطي العاقلات ولا كل جموع غير العاقل. شواهد السيرافي23510–23560 تفرق المحاور وتذكر أكثر من وجه للاتفاق.
2. **لا عدد نحوي من لاحقة وحدها.** مصدر الألفية يستبعد أبيات وقضاة من جمع الألف والتاء الزائدتين؛ والعقود ملحقة بجمع المذكر. ين قد تكون للمثنى أو الجمع أو جزءا أصليا. لا يثبت `Qism.ending` أهلية الكلمة للباب الذي يتلقاه.
3. **لا نكرة من التنوين.** المصدر يذكر زيدا مع تنوين التمكين؛ العلم معرفة. كذلك غياب أل ليس دليلا كافيا على غياب التعريف، والإضافة لا تعرف رأسها إلا في مجالها وشروطها.
4. **لا أصل جذري من سطح قال.** `neutral_forgets_weak` يبقي القول والقيْل في الليف نفسه في هذا النموذج. تصنيف و/ي الموضعي ممكن على جذر مستقل، أما اختيار الأصل الحقيقي فيحتاج شاهده. الهمزة منفصلة عن العلة في `Tasrif.Cls`.
5. **المنقوص الاسمي باب مستقل.** اسم معرب وياء لازمة مكسور ما قبلها؛ يرمي والذي وظبي أمثلة مستبعدة صريحة. والنصوص الأقدم قد تسمي المقصور منقوصا؛ لذلك يثبت اصطلاح كل موضع بدل دمج جميع النتائج تحت اسم واحد.
6. **العدد1/2 قانون توافق لا ترخيص جملة.** مطابقة الجنس في تركيب معلوم لا تجعل «1 رجل» أو «واحد رجل» تركيبا عربيا صحيحا، ولا تثبت رتبة الكلمات أو الإعراب. وفي3–10 جنس آحاد المعدود هو المدخل، لا شكل جمعه. وفي11–19 يجب تمثيل الوحدة والعشرة منفصلتين.

## مواضع البحث السلبية

بحث أسماء الأبواب في ملفات Lean المتتبعة أعطى الأبواب المذكورة أعلاه، وإشارات غير نحوية مثل عد السلاسل ومفهوم العدد ومصطلح التمييز المنطقي. لم أعثر في هذا النطاق على دالة Lean عامة تجمع اكتساب الجنس والتعريف والعدد المعجمي من نص جديد، ولا على قانون كامل لصياغة العدد والمعدود. هذا حد نتيجة البحث في هذه اللقطة؛ ليس ادعاء غياب شيفرة أخرى أو نثر أو فروع تاريخية.

ملفات `suspended/samai/lean` أدلة بحثية منفصلة. نسب المطابقة المعروضة فيها عد لصفوف مودعة، وبعض الاستبعادات معلن بعد القياس. إبقاء هذا القيد ضروري حتى لا يتحول «18/19» أو «531/595» إلى قياس مستقل على ألفاظ جديدة.
