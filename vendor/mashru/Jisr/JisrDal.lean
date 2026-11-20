/-
  Jisr/JisrDal.lean — الجسرُ إلى الدالّ: الإعرابُ بالحروف والتقديرُ وجرُّ الممنوع من الصرف بالفتحة وصيغةُ المجهول، على خلايا الكلمة وأطر المالك
  (`SLGE/Bridge.lean`: الحالةُ تحمل الإعراب، والعلاماتُ الفرعيّة حواملُها من حروف الزيادة؛ `SLGE/Wad.lean`: الإعراباتُ الأربعة؛ `SLGE/Ladder.lean`:
  الخانةُ `cellEnc`/`cellDec`؛ `SLGE/Hamza.lean`: صورةُ الابتداء بهمزة الوصل؛ `Dal/Khaliya.lean`: مرآةُ البنّاء للخلية دون 116). وموافقتُه قارئَ
  الطبقة الثالثة `Utur.halaIrab` في `Jisr/JisrDalUtur.lean` (فوق هذا الملفّ، فلا دورَ في الاستيراد).
  قرارُ المالك (2026-10-17، 00:09): «يجب عمل lean الجسر للدال … عمل الجسر lean وslge وبعدها ننتقل للإنشاء».

  **المرجع** (قطر الندى، مودَع مختوم، بأسطره — «/» موضعُ انقطاع السطر في المودَع):
  L75–78 «فصل: أنواع الإعراب أربعة. / (1) رفع (2) ونصب في اسم وفعل نحو "زيد يقوم" و "إن زيدا لن يقوم"، (3) / وجر في اسم نحو "بزيد"، (4) وجزم نحو
  "لم يقم". فيرفع بضمة، وينصب بفتحة، / ويجر بكسرة، ويجزم بحذف حركة، إلا الأسماء الستة»؛ L78–79 «وهي أبوه وأخوه وحموها / وهنوه وفوه وذو مال،
  فترفع بالواو وتنصب بالألف وتجر بالياء»؛ L79–80 «والأفصح / استعمال هن كغد»؛ L82–83 «والمثنى كالزيدان فيرفع بالألف، وجمع المذكر السالم كالزيدون
  فيرفع / بالواو، ويجران وينصبان بالياء»؛ L83–85 الملحقاتُ (كلا وكلتا مع الضمير، اثنان واثنتان، أولو وعشرون وأخواته، عالمون، أهلون، وابلون، أرضون،
  سنون وبابه، بنون، عليون)؛ L86–88 «وأولات وما جمع بألف وتاء مزيدتين وما سمي به منهما فينصب بالكسرة، نحو / خلق السموات، واصطفى البنات وما لا
  ينصرف فيجر بالفتحة نحو "بأفضل منه"، / إلا مع أل نحو "بالأفضل" أو بالإضافة نحو "بأفضلكم"»؛ L88–90 «والأمثلة الخمسة، وهي / تفعلان وتفعلون بالياء
  والتاء فيهما، وتفعلين، فترفع بثبوت النون، وتجزم / وتنصب بحذفها، نحو "فإن لم تفعلوا ولن تفعلوا"»؛ L90–91 «والفعل المضارع المعتل / الآخر فيجزم
  بحذف آخره، نحو "لم يغز ولم يخش ولم يرم"»؛ L92–95 «فصل: تقدر جميع الحركات في نحو "غلامي والفتى" ويسمى مقصورا، والضمة / والكسرة في نحو "القاضي"
  ويسمى منقوصا، والضمة والفتحة في نحو "يخشى"، / والضمة في نحو "يدعو ويقضي". وتظهر الفتحة في نحو "إن القاضي لن يقضي ولن / يدعو"»؛ المجهول
  L242–244 «ويضم أول الفعل مطلقا، ويشاركه ثاني نحو / تعلم، وثالث نحو انطلق. ويفتح ما قبل الآخر في المضارع، ويكسر في الماضي، / ولك في نحو قال وباع
  الكسر مخلصا ومشما ضما والضم مخلصا»؛ موانعُ الصرف L420–421 (بالاسم عند المالك `Wad.mawani9`). وشواهدُ من أبوابٍ أخرى بأسطرها: L115 «ويجزم فعلين»،
  L130 «كنية ك"أبي عمرو"»، L226 «"قام الزيدون" و "قامت الهندات"»، L285 «"يالله للمسلمين"»، L320 «{ولا تعثوا في الأرض مفسدين}»، L358 «أو مجردا
  فبشرطين»، L385 «أخاك أخاك إن من لا أخا له».

  **الصورة.** الخليةُ `4·حرف + حالة` (فتحة 0، ضمّة 1، كسرة 2، سكون 3)؛ `kh`/`harf`/`hala` هي خانةُ المالك `SLGE.cellEnc`/`cellDec` بعينها
  (`khaliya_malik`) ومرآةُ البنّاء `Dal.fakk` (`harf_fakk`)، والحواملُ مواضعُها في جدول المخارج `Dal.hawamil` (ا 2، ي 11، ن 14، و 28:
  `hawamil_huruf`)، ولا حكمَ إن كانت الخليةُ الأخيرة 116 فما فوق (`hukm`؛ وما قبلها محصورٌ بحرفه). (١) **البابُ معلَن** `Bab`: المفردُ المنصرف، والفعلُ الصحيح، والمقصور، والمنقوص، والمضافُ
  إلى الياء، والأسماءُ الستّة، والمثنّى، وجمعُ المذكر السالم، وجمعُ المؤنث السالم، والممنوعُ من الصرف (مجرّدًا أو مع أل والإضافة)، والأمثلةُ الخمسة،
  والمضارعُ المعتلّ الآخر — فالدالُّ لا يقرّر بابَ الكلمة (أهي مثنًّى أم اسمٌ آخرُه ألفٌ ونون؟): البابُ من المعجم، والجسرُ يقرأ الإعرابَ من الخلايا
  **بعد** إعلان الباب (كما أنّ الدالَّ وحده لا يقرّر المدلول: `Bridge.dal_undetermines`)؛ والملحقاتُ بالمثنّى والجمع (L83–85) وأولات (L86) وهن
  (L79–80) تدخل بإعلان بابها من المعجم لا بشاهدٍ هنا. (٢) **الحكمُ من الدالّ** `HukmDal` ثلاثيّ: معيَّنٌ، أو محتمَلٌ بين أكثر من إعرابٍ (الدالُّ
  لا يفرّق: ياءُ المثنّى والجمع نصبًا وجرًّا، فتحةُ الممنوع نصبًا وجرًّا، تقديرُ المقصور)، أو لا حكم (خليةٌ لا يقبلها الباب: حرفُ العلّة الحاملُ غيرُ
  ساكنٍ في المثنّى والجمع والستّة والمقصور، ومضارعٌ معتلٌّ آخرُه واوٌ مضمومة …). `hukm` يقرأ الخليةَ الأخيرة (وقبلَها في المثنّى والجمع).
  ولـ«لا حكم» سببٌ واحدٌ مسمّى `SababDal` (`sababDal`): كلمةٌ بلا خلايا، أو خليتُها الأخيرة 116 فما فوق، أو خليةٌ لا يقبلها البابُ المعلَن
  (`laYaqbaluhuBab` هو `hukmKhaliya = .laHukm` بعينه: لا يفرّق خطأَ إعلان الباب من خطأ الحركة) — `hukm_laHukm_sabab`: «لا حكم» ⟺ سبب.
  وتسميةُ السبب هنا رأيُ البنّاء على مبدأ LC11 («فصل عدم التمثيل عن الامتناع اللغوي») لا من LC06. (٣)
  **الأصليةُ** تقابلُ المالك بعينه (`Bridge.irabState`: `asliyya_tuqabil`)؛ **والفرعيةُ**: صفوفُ جدول المالك `Bridge.farIya` العشرة بأبوابنا
  (`farIyaBab_malik`)، ولكلّ صفٍّ القاعدةُ على كلّ كلمة (`farIya_kull`) وشاهدٌ يحمله (`muwafiq_farIya`)، وحواملُها من حروف الزيادة (`sitta_hamil`؛
  وعند المالك `Bridge.fariya_augs`). (٤) **التقدير**: المقصورُ والمضافُ إلى الياء لا يعيّنان شيئًا (`maqsur_la_yuayyin`، `mudaf_la_yuayyin`)،
  والمنقوصُ تظهر فتحتُه وحدَها (`manqus_fatha_zahira`). (٥) **الممنوع**: فتحتُه نصبٌ أو جرٌّ ولا كسرةَ له، ومع أل أو الإضافة يُجرّ بالكسرة
  (`mamnu_fatha`، `mamnu_bi_al`). (٦) **الأمثلةُ الخمسة**: بالنون رفعٌ وبحذفها نصبٌ أو جزم (`amthila_nun`). (٧) **المجهول** `majhul`: ضمُّ الأوّل
  (ومعه الثاني في نحو تعلّم، والثالث في نحو انطلق — بالصيغة المعلَنة `Siga`، في الماضي وحده: مثالا القطر ماضيان، ومضارعُهما بضمّ الأوّل وحده)، وفتحُ
  ما قبل الآخر في المضارع وكسرُه في الماضي؛ يحفظ الحروفَ والطولَ والخلايا دون 116 (`majhul_huruf`، `majhul_tul`، `majhul_dun_116`)، ويُرفض باسمه
  ما له سببٌ في `sababMajhul` (`majhul_none_iff`: لا رفضَ إلّا بسببٍ مسمّى؛ والأسبابُ حدودٌ للأداة لا امتناعٌ في العربية — LC06 «حدود تحويل
  المجهول وتفسير رفض التحويل» من «سجل التزامات إغلاق الإخبار ثم الإنشاء»، مرفق المالك `CLOSURE_LEDGER_AR.md`، غيرُ مودَعٍ ولا في المستودع؛ وموضعُ القراءة فيه لهذا البند سطرُ المرفق 85: «`Jisr/JisrDal.lean` —
  `majhul / majhul_marfud`؛ الالتزام `ca5ed3cd250cc6fb3000d5bae161f407a895f0c1`»).
  **والترخيصُ بنمطٍ موجب لا بغياب مانع** (`majhul_namat`: لا مخرجَ إلّا على نمطٍ معلَن `namat`)، على قاعدة القطر L242 «ويضم أول الفعل مطلقا»
  ومثاليها (تعلم، انطلق؛ L242–243). والأنماطُ تعيينُ البنّاء: الماضي فَعَلَ/فَعِلَ/فَعُلَ، وفَعَّلَ/فَعْلَلَ/أَفْعَلَ، وتَفَعَّلَ/تَفَعْلَلَ، واِنْفَعَلَ/اِفْتَعَلَ،
  واِسْتَفْعَلَ/اِفْعَنْلَلَ/اِفَّعَّلَ، آخرُه مفتوحٌ غيرُ واو (الكتاب س20543 «هذه الواو لا تقع قبلها أبدا كسرة إلا قلبت ياء وذلك نحو غاز وغزي»)؛ والمضارعُ
  مضمومَ الآخر ظاهرًا غيرَ واوٍ ولا ياء (`akhirMudari`) بحرفٍ من «نأيت» (L65): يَفْعِلُ/يُفْعِلُ، ويَنْفَعِلُ/يَفْتَعِلُ، ويُفَعِّلُ/يُفَعْلِلُ، ويَتَفَعَّلُ/يَتَفَعْلَلُ، ويَسْتَفْعِلُ/يَفْعَنْلِلُ، ويَفَّعَّلُ.
  **عقدُ المُدخَل** (تعيينُ البنّاء): الفعلُ وحده بلا سابقةٍ ولا لاحقة —؛ وما لا تُميّزه الخلايا يمرّ على عهدته (`shahid_anmat`): اللاحقةُ
  المضمومة في المضارع والمفتوحة في الماضي على نمط (يَدْعُهُ ← يُدْعَهُ، غَرَّكَ ← غُرِّكَ)، والزمنُ المعلَن خطأً على نمطه (يَشْرَبَ ماضيًا ← يُشْرِبَ)، وصورةُ الأصل للأجوف لا تُميّزها الخلايا
  ممّا جاء على الأصل غيرَ معتلّ (الكتاب س19976–19979 «وقد جاءت حروف على الأصل غير معتلة … نحو قولهم أجودت وأطولت واستحوذ»؛ وأَعْوَزَ من «عوز»، اللسان س110455–110457) (قَوَلَ ← قُوِلَ، بَيَعَ ← بُيِعَ، أَقْوَمَ ← أُقْوِمَ، يَقْوُلُ ← يُقْوَلُ، وأَعْوَزَ ← أُعْوِزَ) —، الماضي مفتوحَ الآخر ظاهرًا والمضارعُ مضمومَه، بزمنه (`madi`) وصيغته (`Siga`) المعلَنَين —
  على عهدة من يعلنه كما يُعلَن الباب؛ وما خرج عن الأنماط يُرفض باسمه. الأسبابُ التشخيصيّة: ما قصُر عن موضع المشارِك بثلاث (`qasir`)؛ والمضارعُ
  دون أربع خلايا (`mudariDunArba`: أصولُه ثلاثةٌ فأكثر بعد حرف المضارعة — تعيينُ البنّاء —، فما دون الأربع سقط منه أصلٌ لا يُعرف من الخلايا:
  المثالُ الواويّ يَعِدُ ويَضَعُ، والكتاب س19844 «ولم تذهب الواو كما ذهبت في الفعل»؛ وردُّه، يَعِدُ ← يُوعَدُ، بابُه من المعجم)؛ والماضي غيرُ
  المفتوح الآخر ظاهرًا (`madiAkhirGhayrFatha`: ضَرَبَتْ، قُلْتُ، رَدَّتْ، رَمَى) والمضارعُ غيرُ المضموم الآخر ظاهرًا (`mudariAkhirGhayrDamma`:
  يَدْعُوَ، يَعِدْنَ، يَقُمْ، يَضْرِبَ، يَضْرِبْ، ويَدْعُو المرفوعُ تقديرًا)؛ والآخرُ المشدَّد (`mudaafAkhir`: الإدغامُ لم يُبنَ — مَدَّ، يَمُدُّ)؛
  وحرفُ العلّة الساكن (`illaSakin`: فيُرفض الأجوفُ والناقصُ اللذان فيهما قلبٌ، قال وباع: ثلاثةُ أوجهٍ L244 لم تُبنَ، ومعهما أَوْعَدَ وبَيَّنَ
  ويُقَاتِلُ — `majhul_marfud`)؛ وإلّا فـ«خارج الأنماط» (`kharijAnmat`). وكانت هذه كلُّها تمرّ على غير القاعدة على ca5ed3c (`#eval`): يُعَدُ،
  يُضَعُ، يُغَزُ، يُدْعَوَ، يُعِدَنَ، ضُرَبِتْ، قُلِتُ، رُدِّتْ، مُدِدَ، يُمُدَدُ (`shawahid_sabab`)؛ سُيَعَدُ، فُضَرِبَ، يُعِدَهُ، ضُرَبِنَ، ضُرَبِتَ، سُرِوَ،
  اُنْطَلِقَ بالبسيطة، ويُضْرِبَ ماضيًا، ويُغْزَوُ ويُرْمَيُ من يَغْزُوُ ويَرْمِيُ بضمّةٍ ظاهرة (`shahid_anmat`؛ والزمنُ المعلَن خطأً لا يُرفض إلّا إذا خالف الشكلُ نمطَه). **ورفضٌ لا خطأ** (كانت صحيحةً على ca5ed3c وصارت تُرفض): يَقُمْ ويَقُلْ ويَضْرِبَ ويَضْرِبْ ويَمْدُدْ
  (المنصوبُ والمجزومُ خارج العقد)، ويَدَّحْرَجُ ويَزَّلْزَلُ (تَفَعْلَلَ المدغَمُ في المضارع خارج الأنماط، وماضيه اِدَّحْرَجَ يمرّ). وداخلَ الأنماط لم يُوجد مخرجٌ على غير القاعدة في الشواهد ولا في مداخلَ فحصها المراجعُ المستقلّ بـ`#eval`
  في الجلسة (غيرُ مودَعة ولا معدودةٍ هنا) إلّا ما لا تُميّزه الخلايا مما أُعلن على عهدة المُدخِل (ومنه صورةُ الأصل للأجوف: وجدها المراجعُ في السادسة، وكانت تمرّ منذ ca5ed3c)، وإلّا آخرَ المضارع واوًا أو ياءً مضمومةً ظاهرًا
  (يَغْزُوُ ← يُغْزَوُ؛ فات المراجعاتِ الأربعَ الأولى، وصُحّح بـ`akhirMudari`) — رأيٌ، لا برهانٌ ولا تقدير؛ وكونُ المُدخَل فعلًا مجرّدًا على عهدة المُدخِل. وقولُ المالك 2026-10-20، 13:01 («انت خبير
  أوافق على قرارك ونفذ») كان جوابًا عن سؤال البنّاء من أين يبدأ؛ وتصميمُ الأسباب والأنماط والعقد بعده قرارُ البنّاء.
  وعلى صورة الابتداء عند المالك (`Law.ibtidaForm`): مجهولُ «انطلق» هو صورةُ ابتداء مجهوله، فضمُّ الثالث يضمّ همزةَ الوصل بقاعدته `waslHaraka`
  (`intilaq_wasl`)؛ وهو نظيرُ `Shabaka.jahhil` على الأدوار. (٨) **الشواهد** مبنيّةً خلايا (32، كلُّها بلفظ القطر بأسطرها، وللأبواب الاثني عشر كلِّها
  شاهد): زيد (رفعًا ونصبًا)، بزيد، يقوم (رفعًا ونصبًا)، يقم، ذو، أخا، أبي، الزيدان، فعلين، بشرطين، الزيدون، مفسدين، للمسلمين، الهندات، السموات، بأفضل،
  بالأفضل، تفعلان، تفعلوا (نصبًا وجزمًا)، يغز، يخش، يرم، يخشى، يدعو (رفعًا ونصبًا)، القاضي (رفعًا ونصبًا)، غلامي، الفتى؛ والمجهول: ضَرَبَ→ضُرِبَ،
  يَضْرِبُ→يُضْرَبُ، تَعَلَّمَ→تُعُلِّمَ، اِنْطَلَقَ→اُنْطُلِقَ.

  **المبرهنات (27: 18 «مبرهن» و9 «مبرهن على الشاهد» بوسمَي `Mawsua.Wasm.tartib`)، بالمعيار الموحَّد** (`Nizam/Asas.lean` س6؛ 2026-10-20):
  13 لكلّ — `khaliya_malik` (بـ omega)، و`majhul_huruf`/`majhul_tul`/`majhul_dun_116` (بمبرهنات الاستقراء `badilInda_*`/`musharik_*`)، والتسعُ
  بمبرهناتٍ من الملفّ (`hukm_append`، `kh_lt`، `hala_kh`…): `asliyya_tuqabil`، `maqsur_la_yuayyin`، `mudaf_la_yuayyin`، `yayn_la_yufarriq`،
  `manqus_fatha_zahira`، `mamnu_fatha`، `mamnu_bi_al`، `amthila_nun`، `farIya_kull`؛ و5 تعريفيّة: `harf_fakk`، `majhul_marfud`، `hukm_laHukm_sabab`،
  `majhul_none_iff`، `majhul_namat`؛ و9 على الشاهد (`decide`): `hawamil_huruf` (على `Dal.hawamil`)، `sitta_hamil` (على `Law.augs`)، `farIyaBab_malik`
  (على `Bridge.farIya`)، `muwafiq_farIya` (لكلّ صفٍّ من العشرة شاهدٌ يحمله)، `shawahid_hukm`، `shawahid_majhul`، `intilaq_wasl` (على
  `Law.ibtidaForm`)، `shawahid_sabab`، `shahid_anmat`. (27 في `Audit.lean`، ومعها 2 في `Jisr/JisrDalUtur.lean`؛ والقواعدُ المساعدة `badilInda_*`/`musharik_*` داخليّة.) الإعرابُ المخرَج `SLGE.Wad.Irab` (إعراباتُ المالك الأربعة) لا `Jisr.Awamil.Irab` (إعرابُ جدول العوامل؛ الجسرُ بينهما لم يُبنَ).

  تعييناتُ البنّاء (تُعرض على المالك): البابُ معلَنٌ من المعجم لا من الدالّ (ومن أعلن الصحيحَ معتلًّا فجزمُه المقروء على عهدته)؛ حرفُ العلّة
  الحاملُ ساكنٌ، وحركةُ النون في المثنّى والجمع والأمثلة لا تُقرأ، وحركةُ ياء المضاف إليها لا تُقرأ؛ الأسماءُ الستّة تُقرأ قبل المضاف إليه (ضميرًا
  أو اسمًا: أبوه، ذو مال) وقطعُه قرارُ القارئ؛ الخلايا بالرسم (همزةُ الوصل حاملًا 0 بحركتها، واللامُ الشمسية لامًا ساكنة بلا تضعيفٍ لما بعدها،
  والشدّةُ في غيرها خليتين) ولا يقرأ الجسرُ إلّا الخليةَ الأخيرة وقبلَها — فحركاتُ الخلايا غيرِ المقروءة والفرقُ بين الهمزة (0) والألف (2) في أوّل الكلمة
  قراءةُ البنّاء لا يفحصها Lean ولا الاختبار (الاختبارُ يفحص الحروفَ وحدَها، وهمزةُ الوصل والقطع والألف عنده صنفٌ واحد)؛ التنوينُ (زيدٌ) في القارئ لا في الجسر فشواهدُ المفرد بلا تنوين؛ موانعُ الصرف التسعة نفسُها من المعجم
  (`Wad.mawani9` بالاسم)؛ المضارعُ المعتلّ: الجزمُ بحذف حرف العلّة يُقرأ من غياب حرف العلّة آخرًا؛ صيغُ المجهول الثلاث (بسيط/تفعّل/انفعل) على
  مثالَي القطر في الماضي، وموضعُ المشارِك بثلاثٍ أقلَّ طولٍ، والمضارعُ أربعٌ أقلَّ طولٍ، ورفضُ ذي حرف العلّة الساكن والآخرِ المشدَّد، والأنماطُ على قاعدة L242–243 (`namat`) وعقدُ المُدخَل؛ والمجهولُ على صورة الابتداء (همزةُ الوصل خليةً). الجدولُ
  `jisr_dal.tsv` مسجَّلٌ «مرشّحًا» حتّى يأذن المالك بختمه؛ ومطابقتُه `tahaqquq/test_jisrdal.py`.
-/
import SLGE.Bridge
import SLGE.Hamza
import Dal.Makharij

set_option autoImplicit false

namespace Jisr
namespace JisrDal
open SLGE SLGE.Wad

/-! ## ١. الخلية والباب والحكم -/

/-- حرفُ الخلية (رقمُ حامله في جدول المخارج) وحالتُها (فتحة 0، ضمّة 1، كسرة 2، سكون 3). -/
def harf (c : Nat) : Nat := c / 4
def hala (c : Nat) : Nat := c % 4

/-- خليةٌ من حرفٍ وحالة. -/
def kh (h s : Nat) : Nat := 4 * h + s

theorem harf_kh (h s : Nat) (hs : s < 4) : harf (kh h s) = h := by unfold harf kh; omega
theorem hala_kh (h s : Nat) (hs : s < 4) : hala (kh h s) = s := by unfold hala kh; omega

/-- **الخليةُ خانةُ المالك بعينها**: `kh` هو `SLGE.cellEnc` و`(harf, hala)` هو `SLGE.cellDec` (الدرجة 1 في سلّمه، `SLGE/Ladder.lean`) — لكلّ حرفٍ
وحالةٍ ورقم. -/
theorem khaliya_malik : (∀ h s : Nat, kh h s = SLGE.cellEnc h s) ∧ (∀ n : Nat, SLGE.cellDec n = (harf n, hala n)) :=
  ⟨fun h s => by unfold kh SLGE.cellEnc SLGE.mixEnc; omega, fun n => by simp [SLGE.cellDec, SLGE.mixDec, harf, hala]⟩

/-- ومرآةُ البنّاء `Dal.fakk` (الخلية `Dal.Khaliya` دون 116) تفكّ إلى الحرف والحالة نفسِهما. -/
theorem harf_fakk (m : Fin 116) : (Dal.fakk m).hamil.val = harf m.val ∧ (Dal.fakk m).hala.val = hala m.val := ⟨rfl, rfl⟩

/-- الحروفُ الحوامل في الإعراب بالحروف (بترتيب `Dal.hawamil`): ا 2، ي 11، ن 14، و 28. -/
def alif : Nat := 2
def ya : Nat := 11
def nun : Nat := 14
def waw : Nat := 28

/-- **الحواملُ الأربعة مواضعُها في جدول المخارج المعلَن** `Dal.hawamil` — على الشاهد. -/
theorem hawamil_huruf :
    Dal.hawamil[alif]? = some 'ا' ∧ Dal.hawamil[ya]? = some 'ي' ∧ Dal.hawamil[nun]? = some 'ن' ∧ Dal.hawamil[waw]? = some 'و' := by
  decide

/-- حرفُ علّةٍ ساكن: ألفٌ أو واوٌ أو ياءٌ بالسكون (أيًّا كان ما قبلها — فليس «حرفَ مدّ» بالضرورة). -/
def illaSakin (c : Nat) : Bool := (harf c == alif || harf c == waw || harf c == ya) && hala c == 3

/-- الصيغةُ الصرفيّة للمجهول (القطر L242–243): بسيطٌ (ضمُّ الأوّل)، وما شاركه ثانيه (تعلّم)، وما شاركه ثالثه (انطلق). -/
inductive Siga | basit | thani | thalith
deriving DecidableEq, Repr

/-- أبوابُ الإعراب على الدالّ — تُعلَن من المعجم لا من الدالّ. -/
inductive Bab
  | mufrad                 -- المفرد المنصرف: بالحركات (L76–78)؛ وجمع التكسير مثله (قراءة البنّاء: القطر لا يسمّيه هنا، «كسير» 0 في المودَع)
  | filSahih               -- الفعل المضارع الصحيح الآخر: ضمّة/فتحة/سكون (L76–78)
  | maqsur                 -- تُقدَّر جميع الحركات (L92)
  | manqus                 -- تُقدَّر الضمّة والكسرة وتظهر الفتحة (L93–94)
  | mudafLiYa              -- المضاف إلى ياء المتكلّم (L92)
  | sitta                  -- الأسماء الستّة: بالواو والألف والياء (L78–79)
  | muthanna               -- بالألف رفعًا وبالياء نصبًا وجرًّا (L82–83)
  | jamMudhakkar           -- بالواو رفعًا وبالياء نصبًا وجرًّا (L82–83)
  | jamMuannath            -- يُنصب بالكسرة (L86–87)
  | mamnu (alAwIdafa : Bool) -- ما لا ينصرف: يُجرّ بالفتحة إلّا مع أل أو الإضافة (L87–88)
  | amthila                -- الأمثلة الخمسة: بثبوت النون وحذفها (L88–90)
  | mudariMutall           -- المضارع المعتلّ الآخر: جزمه بالحذف وتقديره (L90–91، L93–95)
deriving DecidableEq, Repr

/-- الأبوابُ بإعلاناتها الثلاثةَ عشر (الممنوعُ مجرّدًا ومع أل أو الإضافة). -/
def abwab : List Bab :=
  [.mufrad, .filSahih, .maqsur, .manqus, .mudafLiYa, .sitta, .muthanna, .jamMudhakkar, .jamMuannath, .mamnu false, .mamnu true, .amthila,
   .mudariMutall]

/-- حكمُ الإعراب من الدالّ: معيَّن، أو محتمَلٌ بين أكثر من إعراب (الدالّ لا يفرّق)، أو لا حكم. -/
inductive HukmDal
  | muayyan (i : Irab)
  | muhtamal (l : List Irab)
  | laHukm
deriving DecidableEq, Repr

/-- الخليةُ الأخيرة وما قبلها. -/
def akhir (l : List Nat) : Option Nat := l.getLast?
def qablAkhir (l : List Nat) : Option Nat := l.dropLast.getLast?

theorem akhir_append (l : List Nat) (c : Nat) : akhir (l ++ [c]) = some c := by simp [akhir]
theorem akhir_append2 (l : List Nat) (d c : Nat) : akhir (l ++ [d, c]) = some c := by simp [akhir]
theorem qablAkhir_append (l : List Nat) (d c : Nat) : qablAkhir (l ++ [d, c]) = some d := by
  simp [qablAkhir, List.dropLast_append_of_ne_nil]

/-- حكمُ الباب على الكلمة `l` وخليتها الأخيرة `c` (دون 116): حرفُ العلّة الحاملُ ساكنٌ، وحركةُ النون لا تُقرأ. -/
def hukmKhaliya (b : Bab) (l : List Nat) (c : Nat) : HukmDal :=
  match b with
    | .mufrad => match hala c with
      | 0 => .muayyan .nasb | 1 => .muayyan .raf | 2 => .muayyan .jarr | _ => .laHukm
    | .filSahih => match hala c with
      | 0 => .muayyan .nasb | 1 => .muayyan .raf | 3 => .muayyan .jazm | _ => .laHukm
    | .maqsur => if harf c == alif && hala c == 3 then .muhtamal [.raf, .nasb, .jarr] else .laHukm
    | .mudafLiYa => if harf c == ya then .muhtamal [.raf, .nasb, .jarr] else .laHukm
    | .manqus => if harf c == ya then (match hala c with | 0 => .muayyan .nasb | 3 => .muhtamal [.raf, .jarr] | _ => .laHukm)
                 else .laHukm
    | .sitta => if hala c != 3 then .laHukm
                else if harf c == waw then .muayyan .raf else if harf c == alif then .muayyan .nasb
                else if harf c == ya then .muayyan .jarr else .laHukm
    | .muthanna => if harf c == nun then
          (match qablAkhir l with
           | some d => if hala d != 3 then .laHukm
                       else if harf d == alif then .muayyan .raf else if harf d == ya then .muhtamal [.nasb, .jarr] else .laHukm
           | none => .laHukm)
        else .laHukm
    | .jamMudhakkar => if harf c == nun then
          (match qablAkhir l with
           | some d => if hala d != 3 then .laHukm
                       else if harf d == waw then .muayyan .raf else if harf d == ya then .muhtamal [.nasb, .jarr] else .laHukm
           | none => .laHukm)
        else .laHukm
    | .jamMuannath => match hala c with
      | 1 => .muayyan .raf | 2 => .muhtamal [.nasb, .jarr] | _ => .laHukm
    | .mamnu false => match hala c with
      | 1 => .muayyan .raf | 0 => .muhtamal [.nasb, .jarr] | _ => .laHukm
    | .mamnu true => match hala c with
      | 0 => .muayyan .nasb | 1 => .muayyan .raf | 2 => .muayyan .jarr | _ => .laHukm
    | .amthila => if harf c == nun then .muayyan .raf else if illaSakin c then .muhtamal [.nasb, .jazm] else .laHukm
    | .mudariMutall => if harf c == alif then (if hala c == 3 then .muhtamal [.raf, .nasb] else .laHukm)
                       else if harf c == waw || harf c == ya then
                         (match hala c with | 0 => .muayyan .nasb | 3 => .muayyan .raf | _ => .laHukm)
                       else .muayyan .jazm

/-- **الجسر:** حكمُ الإعراب من الباب المعلَن وخلايا الكلمة: على الخلية الأخيرة، ولا حكمَ على خليةٍ 116 فما فوق (`Dal.Khaliya`). -/
def hukm (b : Bab) (l : List Nat) : HukmDal :=
  match akhir l with
  | none => .laHukm
  | some c => if c < 116 then hukmKhaliya b l c else .laHukm

/-- **أسبابُ «لا حكم» في الجسر:** كلمةٌ بلا خلايا، أو خليتُها الأخيرة 116 فما فوق، أو خليةٌ لا يقبلها البابُ المعلَن — سببٌ واحدٌ مسمّى. -/
inductive SababDal
  | farigh          -- لا خليةَ أخيرة
  | fawqHadd        -- الخليةُ الأخيرة 116 فما فوق (`Dal.Khaliya`: الخلايا دون 116)
  | laYaqbaluhuBab  -- الخليةُ لا يقبلها البابُ المعلَن (`hukmKhaliya`)
deriving DecidableEq, Repr

def sababDal (b : Bab) (l : List Nat) : Option SababDal :=
  match akhir l with
  | none => some .farigh
  | some c => if c < 116 then (if hukmKhaliya b l c = .laHukm then some .laYaqbaluhuBab else none) else some .fawqHadd

/-- **لا «لا حكم» في الجسر إلّا بسببٍ مسمّى**، ولكلّ سببٍ «لا حكم». -/
theorem hukm_laHukm_sabab (b : Bab) (l : List Nat) : hukm b l = .laHukm ↔ sababDal b l ≠ none := by
  unfold hukm sababDal
  split
  · simp
  · rename_i c _
    by_cases hc : c < 116 <;> by_cases hk : hukmKhaliya b l c = .laHukm <;> simp [hc, hk]

theorem kh_lt (h s : Nat) (hh : h < 29) (hs : s < 4) : kh h s < 116 := by unfold kh; omega

theorem hukm_append (b : Bab) (l : List Nat) (c : Nat) (hc : c < 116) : hukm b (l ++ [c]) = hukmKhaliya b (l ++ [c]) c := by
  simp [hukm, akhir_append, hc]
theorem hukm_append2 (b : Bab) (l : List Nat) (d c : Nat) (hc : c < 116) : hukm b (l ++ [d, c]) = hukmKhaliya b (l ++ [d, c]) c := by
  simp [hukm, akhir_append2, hc]

/-- هل يحتمل الحكمُ هذا الإعراب؟ -/
def yahtamil : HukmDal → Irab → Bool
  | .muayyan i, j => i == j
  | .muhtamal l, j => l.contains j
  | .laHukm, _ => false

/-! ## ٢. الأصلية تقابلُ المالك، والفرعية توافق جدولَه -/

/-- **العلاماتُ الأصلية هي تقابلُ المالك بعينه**: المفردُ المنصرف آخرُه حالةُ الإعراب (`Bridge.irabState`) للرفع والنصب والجرّ، والفعلُ
الصحيح للرفع والنصب والجزم — لكلّ كلمةٍ وحرفٍ أخير (في هذا الاتّجاه: من حالة المالك إلى الحكم). -/
theorem asliyya_tuqabil (l : List Nat) (h : Nat) (hh : h < 29) :
    (∀ i : Irab, i ≠ .jazm → hukm .mufrad (l ++ [kh h (Bridge.irabState i)]) = .muayyan i) ∧
    (∀ i : Irab, i ≠ .jarr → hukm .filSahih (l ++ [kh h (Bridge.irabState i)]) = .muayyan i) := by
  refine ⟨fun i hi => ?_, fun i hi => ?_⟩ <;> cases i <;>
    simp [hukm_append, kh_lt, hh, hukmKhaliya, hala_kh, Bridge.irabState] at *

/-- **المقصورُ لا يعيّن شيئًا** — الحركاتُ كلُّها مقدَّرة (L92): لكلّ كلمةٍ وخليةٍ أخيرة. -/
theorem maqsur_la_yuayyin (l : List Nat) (c : Nat) : ∀ i, hukm .maqsur (l ++ [c]) ≠ .muayyan i := by
  intro i; simp only [hukm, akhir_append]; split
  · simp only [hukmKhaliya]; split <;> simp
  · simp

/-- **المضافُ إلى الياء لا يعيّن شيئًا** (L92). -/
theorem mudaf_la_yuayyin (l : List Nat) (c : Nat) : ∀ i, hukm .mudafLiYa (l ++ [c]) ≠ .muayyan i := by
  intro i; simp only [hukm, akhir_append]; split
  · simp only [hukmKhaliya]; split <;> simp
  · simp

/-- **ياءُ المثنّى والجمع لا تفرّق النصبَ من الجرّ** — لكلّ كلمةٍ آخرُها ياءٌ ساكنةٌ فنون: محتمَلٌ بينهما (L83). -/
theorem yayn_la_yufarriq (l : List Nat) (sn : Nat) (hsn : sn < 4) :
    hukm .muthanna (l ++ [kh ya 3, kh nun sn]) = .muhtamal [.nasb, .jarr] ∧
    hukm .jamMudhakkar (l ++ [kh ya 3, kh nun sn]) = .muhtamal [.nasb, .jarr] := by
  constructor <;> simp [hukm_append2, kh_lt, hukmKhaliya, qablAkhir_append, harf_kh, hala_kh, hsn, ya, nun, waw, alif]

/-- **المنقوصُ تظهر فتحتُه وحدَها** (L93–94): ياءٌ مفتوحةٌ نصبٌ، وساكنةٌ الرفعُ والجرُّ مقدَّران، وغيرُهما لا حكم — بفكّ التعريف. -/
theorem manqus_fatha_zahira (l : List Nat) (s : Nat) (hs : s < 4) :
    hukm .manqus (l ++ [kh ya s]) = (if s = 0 then .muayyan .nasb else if s = 3 then .muhtamal [.raf, .jarr] else .laHukm) := by
  have h4 : s = 0 ∨ s = 1 ∨ s = 2 ∨ s = 3 := by omega
  rcases h4 with rfl | rfl | rfl | rfl <;> simp [hukm_append, kh_lt, hukmKhaliya, harf_kh, hala_kh, ya]

/-- **الممنوعُ من الصرف**: فتحتُه نصبٌ أو جرّ (الدالّ لا يفرّق)، ولا كسرةَ له (L87–88) — بفكّ التعريف. -/
theorem mamnu_fatha (l : List Nat) (h : Nat) (hh : h < 29) :
    hukm (.mamnu false) (l ++ [kh h 0]) = .muhtamal [.nasb, .jarr] ∧ hukm (.mamnu false) (l ++ [kh h 2]) = .laHukm := by
  constructor <;> simp [hukm_append, kh_lt, hh, hukmKhaliya, hala_kh]

/-- **ومع أل أو الإضافة يُجرّ بالكسرة** كالمنصرف (L88) — بفكّ التعريف. -/
theorem mamnu_bi_al (l : List Nat) (h : Nat) (hh : h < 29) : hukm (.mamnu true) (l ++ [kh h 2]) = .muayyan .jarr := by
  simp [hukm_append, kh_lt, hh, hukmKhaliya, hala_kh]

/-- **الأمثلةُ الخمسة**: بثبوت النون رفعٌ، وبحذفها (فيبقى حرفُ العلّة ساكنًا) نصبٌ أو جزم (L89–90) — بفكّ التعريف. -/
theorem amthila_nun (l : List Nat) (sn h : Nat) (hsn : sn < 4) (hh : h = alif ∨ h = waw ∨ h = ya) :
    hukm .amthila (l ++ [kh nun sn]) = .muayyan .raf ∧ hukm .amthila (l ++ [kh h 3]) = .muhtamal [.nasb, .jazm] := by
  constructor
  · simp [hukm_append, kh_lt, hsn, nun, hukmKhaliya, harf_kh]
  · rcases hh with rfl | rfl | rfl <;> simp [hukm_append, kh_lt, hukmKhaliya, illaSakin, harf_kh, hala_kh, alif, waw, ya, nun]

/-- **حواملُ الأسماء الستّة** من حروف الزيادة — على الشاهد (جدولُ المالك `Law.augs`؛ وعنده `Bridge.fariya_augs`). -/
theorem sitta_hamil : [waw, alif, ya].all (fun c => Law.augs.contains c) = true := by decide

/-- صفوفُ جدول المالك `Bridge.farIya` بأبوابنا: (الباب، الإعراب، حاملُ العلامة). -/
def farIyaBab : List (Bab × Irab × Nat) :=
  [(.sitta, .raf, waw), (.sitta, .nasb, alif), (.sitta, .jarr, ya),
   (.muthanna, .raf, alif), (.muthanna, .nasb, ya), (.muthanna, .jarr, ya),
   (.jamMudhakkar, .raf, waw), (.jamMudhakkar, .nasb, ya), (.jamMudhakkar, .jarr, ya),
   (.amthila, .raf, nun)]

/-- اسمُ الباب عند المالك في `Bridge.farIya`. -/
def ismBab : Bab → String
  | .sitta => "الأسماء الستة" | .muthanna => "المثنى" | .jamMudhakkar => "جمع المذكر" | .amthila => "الأمثلة الخمسة" | _ => ""

/-- **صفوفُنا هي صفوفُ المالك صفًّا صفًّا** (`Bridge.farIya` بأسمائه) — على الشاهد. -/
theorem farIyaBab_malik : farIyaBab.map (fun x => (ismBab x.1, x.2)) = Bridge.farIya := by decide

/-- لاحقةُ العلامة الفرعية في بابها: حرفُ العلّة ساكنًا آخرًا (الستّة)، أو ساكنًا فالنونُ بحالتها (المثنّى والجمع)، أو النونُ بحالتها (الأمثلة). -/
def lahiqa : Bab → Nat → Nat → List Nat
  | .muthanna, h, sn => [kh h 3, kh nun sn]
  | .jamMudhakkar, h, sn => [kh h 3, kh nun sn]
  | .amthila, h, sn => [kh h sn]
  | _, h, _ => [kh h 3]

/-- **الفرعيةُ على كلّ كلمة**: لكلّ صفٍّ من صفوف جدول المالك العشرة، كلُّ كلمةٍ تنتهي بلاحقة ذلك الحامل في ذلك الباب يحتمل حكمُها ذلك الإعراب
(والمعيَّنُ منها ما لا تشترك فيه الياء) — بفكّ التعريف لكلّ كلمةٍ وحركةِ نون. -/
theorem farIya_kull (l : List Nat) (sn : Nat) (hsn : sn < 4) :
    farIyaBab.all (fun x => yahtamil (hukm x.1 (l ++ lahiqa x.1 x.2.2 sn)) x.2.1) = true := by
  simp [farIyaBab, lahiqa, hukm_append, hukm_append2, kh_lt, hsn, hukmKhaliya, yahtamil, qablAkhir_append, harf_kh, hala_kh, waw, alif,
        ya, nun]

/-! ## ٣. الشواهد: توافقُ جدول المالك `Bridge.farIya` -/

/-- شاهدٌ خلايا: لفظُه، وسطرُ القطر الذي فيه لفظُه، وبابُه المعلَن، وخلاياه، وإعرابُه المشهود. -/
structure Shahid where
  lafz : String
  satr : Nat
  bab : Bab
  khalaya : List Nat
  irab : Irab
deriving DecidableEq, Repr

/-- الشواهدُ (32، كلُّها بلفظ القطر في سطره): الأسماءُ الستّة قبل المضاف إليه (الحاملُ آخرُها)، والمفردُ بلا تنوين («زيدا» L76 بألف التنوين:
خلاياه خلايا «زيد» بالفتحة)، والخلايا بالرسم. ء 0، ه 1، ع 3،
غ 5، خ 6، ق 7، ج 9، ش 10، ض 12، ل 13، ر 15، ط 16، د 17، ت 18، ز 19، س 20، ذ 23، ف 25، ب 26، م 27. -/
def shawahid : List Shahid :=
  [⟨"زيد", 76, .mufrad, [kh 19 0, kh ya 3, kh 17 1], .raf⟩,
   ⟨"زيد", 76, .mufrad, [kh 19 0, kh ya 3, kh 17 0], .nasb⟩,
   ⟨"بزيد", 77, .mufrad, [kh 26 2, kh 19 0, kh ya 3, kh 17 2], .jarr⟩,
   ⟨"يقوم", 76, .filSahih, [kh ya 0, kh 7 1, kh waw 3, kh 27 1], .raf⟩,
   ⟨"يقوم", 76, .filSahih, [kh ya 0, kh 7 1, kh waw 3, kh 27 0], .nasb⟩,
   ⟨"يقم", 77, .filSahih, [kh ya 0, kh 7 1, kh 27 3], .jazm⟩,
   ⟨"ذو", 79, .sitta, [kh 23 1, kh waw 3], .raf⟩,
   ⟨"أخا", 385, .sitta, [kh 0 0, kh 6 0, kh alif 3], .nasb⟩,
   ⟨"أبي", 130, .sitta, [kh 0 0, kh 26 2, kh ya 3], .jarr⟩,
   ⟨"الزيدان", 82, .muthanna, [kh 0 0, kh 13 3, kh 19 0, kh ya 3, kh 17 0, kh alif 3, kh nun 2], .raf⟩,
   ⟨"فعلين", 115, .muthanna, [kh 25 2, kh 3 3, kh 13 0, kh ya 3, kh nun 2], .nasb⟩,
   ⟨"بشرطين", 358, .muthanna, [kh 26 2, kh 10 0, kh 15 3, kh 16 0, kh ya 3, kh nun 2], .jarr⟩,
   ⟨"الزيدون", 82, .jamMudhakkar, [kh 0 0, kh 13 3, kh 19 0, kh ya 3, kh 17 1, kh waw 3, kh nun 0], .raf⟩,
   ⟨"مفسدين", 320, .jamMudhakkar, [kh 27 1, kh 25 3, kh 20 2, kh 17 2, kh ya 3, kh nun 0], .nasb⟩,
   ⟨"للمسلمين", 285, .jamMudhakkar, [kh 13 2, kh 13 3, kh 27 1, kh 20 3, kh 13 2, kh 27 2, kh ya 3, kh nun 0], .jarr⟩,
   ⟨"الهندات", 226, .jamMuannath, [kh 0 0, kh 13 3, kh 1 2, kh nun 3, kh 17 0, kh alif 3, kh 18 1], .raf⟩,
   ⟨"السموات", 87, .jamMuannath, [kh 0 0, kh 13 3, kh 20 0, kh 27 0, kh waw 0, kh alif 3, kh 18 2], .nasb⟩,
   ⟨"بأفضل", 87, .mamnu false, [kh 26 2, kh 0 0, kh 25 3, kh 12 0, kh 13 0], .jarr⟩,
   ⟨"بالأفضل", 88, .mamnu true, [kh 26 2, kh 0 0, kh 13 3, kh 0 0, kh 25 3, kh 12 0, kh 13 2], .jarr⟩,
   ⟨"تفعلان", 89, .amthila, [kh 18 0, kh 25 3, kh 3 0, kh 13 0, kh alif 3, kh nun 2], .raf⟩,
   ⟨"تفعلوا", 90, .amthila, [kh 18 0, kh 25 3, kh 3 0, kh 13 1, kh waw 3, kh alif 3], .nasb⟩,
   ⟨"تفعلوا", 90, .amthila, [kh 18 0, kh 25 3, kh 3 0, kh 13 1, kh waw 3, kh alif 3], .jazm⟩,
   ⟨"يغز", 91, .mudariMutall, [kh ya 0, kh 5 3, kh 19 1], .jazm⟩,
   ⟨"يخش", 91, .mudariMutall, [kh ya 0, kh 6 3, kh 10 0], .jazm⟩,
   ⟨"يرم", 91, .mudariMutall, [kh ya 0, kh 15 3, kh 27 2], .jazm⟩,
   ⟨"يخشى", 93, .mudariMutall, [kh ya 0, kh 6 3, kh 10 0, kh alif 3], .raf⟩,
   ⟨"يدعو", 94, .mudariMutall, [kh ya 0, kh 17 3, kh 3 1, kh waw 3], .raf⟩,
   ⟨"يدعو", 95, .mudariMutall, [kh ya 0, kh 17 3, kh 3 1, kh waw 0], .nasb⟩,
   ⟨"القاضي", 93, .manqus, [kh 0 0, kh 13 3, kh 7 0, kh alif 3, kh 12 2, kh ya 3], .raf⟩,
   ⟨"القاضي", 94, .manqus, [kh 0 0, kh 13 3, kh 7 0, kh alif 3, kh 12 2, kh ya 0], .nasb⟩,
   ⟨"غلامي", 92, .mudafLiYa, [kh 5 1, kh 13 0, kh alif 3, kh 27 2, kh ya 3], .raf⟩,
   ⟨"الفتى", 92, .maqsur, [kh 0 0, kh 13 3, kh 25 0, kh 18 0, kh alif 3], .raf⟩]

/-- **الشواهدُ الاثنان والثلاثون**: كلُّ شاهدٍ يحتمل إعرابَه المشهود، والمعيَّنُ منها عشرون والباقي محتمَل (الدالّ لا يفرّق)؛ وكلُّها بلفظ القطر
في سطره (يفحصه الاختبارُ على المودَع)؛ وللأبواب الثلاثةَ عشر (الممنوعُ بوجهيه) كلِّها شاهد. -/
theorem shawahid_hukm :
    shawahid.length = 32 ∧ shawahid.all (fun s => yahtamil (hukm s.bab s.khalaya) s.irab) = true ∧
    (shawahid.filter fun s => match hukm s.bab s.khalaya with | .muayyan _ => true | _ => false).length = 20 ∧
    shawahid.all (fun s => s.satr != 0) = true ∧ abwab.all (fun b => shawahid.any fun s => s.bab == b) = true := by decide

/-- **لكلّ صفٍّ من صفوف جدول المالك شاهدٌ يحمله**: بذلك الباب، حاملُ علامته ذلك الحرفُ بعينه، وحكمُه من الدالّ يحتمل ذلك الإعراب — على الشاهد
(وجوديّةٌ على الصفوف العشرة؛ والقاعدةُ على كلّ كلمة في `farIya_kull`). -/
theorem muwafiq_farIya :
    farIyaBab.all (fun x => shawahid.any fun s =>
      s.bab == x.1 && s.irab == x.2.1 && yahtamil (hukm s.bab s.khalaya) x.2.1 &&
      (match s.bab with
       | .muthanna | .jamMudhakkar => qablAkhir s.khalaya |>.map harf
       | _ => akhir s.khalaya |>.map harf) == some x.2.2) = true := by decide

/-! ## ٤. صيغةُ المجهول على الخلايا -/

/-- تبديلُ حالة الخلية (الحالةُ بالباقي على 4 فلا تخرج الخليةُ عن حرفها). -/
def badilHala (c s : Nat) : Nat := 4 * harf c + s % 4

/-- تبديلُ حالة الخلية رقم `i` (من الصفر). -/
def badilInda : List Nat → Nat → Nat → List Nat
  | [], _, _ => []
  | c :: cs, 0, s => badilHala c s :: cs
  | c :: cs, i + 1, s => c :: badilInda cs i s

theorem badilHala_harf (c s : Nat) : harf (badilHala c s) = harf c := by
  unfold badilHala harf; omega

theorem badilHala_lt (c s : Nat) (hc : c < 116) : badilHala c s < 116 := by
  unfold badilHala harf; omega

theorem badilInda_harf (l : List Nat) (i s : Nat) : (badilInda l i s).map harf = l.map harf := by
  induction l generalizing i with
  | nil => rfl
  | cons c cs ih =>
    cases i with
    | zero => simp [badilInda, badilHala_harf]
    | succ i => simp [badilInda, ih]

theorem badilInda_tul (l : List Nat) (i s : Nat) : (badilInda l i s).length = l.length := by
  induction l generalizing i with
  | nil => rfl
  | cons c cs ih =>
    cases i with
    | zero => simp [badilInda]
    | succ i => simp [badilInda, ih]

theorem badilInda_lt (l : List Nat) (i s : Nat) (hl : ∀ c ∈ l, c < 116) : ∀ c ∈ badilInda l i s, c < 116 := by
  induction l generalizing i with
  | nil => intro c hc; simp [badilInda] at hc
  | cons a as ih =>
    intro c hc
    cases i with
    | zero =>
      simp only [badilInda, List.mem_cons] at hc
      rcases hc with rfl | hc
      · exact badilHala_lt a s (hl a (List.mem_cons_self))
      · exact hl c (List.mem_cons_of_mem a hc)
    | succ i =>
      simp only [badilInda, List.mem_cons] at hc
      rcases hc with rfl | hc
      · exact hl c (List.mem_cons_self)
      · exact ih i (fun d hd => hl d (List.mem_cons_of_mem a hd)) c hc

/-- موضعُ المشارِك في الضمّ (من الصفر): الأوّلُ وحده، أو الثاني، أو الثالث. -/
def mawdiMusharik : Siga → Nat
  | .basit => 0 | .thani => 1 | .thalith => 2

/-- مشاركةُ الثاني (تعلّم) أو الثالث (انطلق) في الضمّ. -/
def musharik : Siga → List Nat → List Nat
  | .basit, l => l
  | .thani, l => badilInda l 1 1
  | .thalith, l => badilInda l 2 1

theorem musharik_harf (g : Siga) (l : List Nat) : (musharik g l).map harf = l.map harf := by
  cases g <;> simp [musharik, badilInda_harf]

theorem musharik_tul (g : Siga) (l : List Nat) : (musharik g l).length = l.length := by
  cases g <;> simp [musharik, badilInda_tul]

theorem musharik_lt (g : Siga) (l : List Nat) (hl : ∀ c ∈ l, c < 116) : ∀ c ∈ musharik g l, c < 116 := by
  cases g with
  | basit => exact hl
  | thani => exact badilInda_lt l 1 1 hl
  | thalith => exact badilInda_lt l 2 1 hl

/-- الصيغةُ الفعليّة: المشاركةُ في الماضي وحده (مثالا القطر ماضيان)، والمضارعُ بسيطٌ أبدًا (ضمُّ الأوّل وحده: يُتَعَلَّمُ، يُنْطَلَقُ). -/
def sigaFiliyya (madi : Bool) (g : Siga) : Siga := if madi then g else .basit

/-- **أسبابُ رفض المجهول** (LC06): حدودٌ للأداة لا امتناعٌ في العربية. الأداةُ تبدّل حركاتِ الخلايا وحدها على قاعدة القطر L242–243،
فلا تُخرج صورةً إلّا لمُدخَلٍ على **نمطٍ معلَن** (`namat`) — ترخيصٌ بشاهدٍ موجب لا بغياب مانعٍ معروف؛ وما سواه يُرفض باسمه: سببٌ
تشخيصيٌّ إن عُرف، وإلّا «خارج الأنماط». -/
inductive SababMajhul
  | qasir                 -- أقصرُ من موضع المشارِك بثلاث خلايا
  | mudariDunArba         -- مضارعٌ دون أربع خلايا: سقط منه أصلٌ لا يُعرف من الخلايا (يَعِدُ، يَضَعُ، يَقُمْ) — ردُّه من المعجم
  | madiAkhirGhayrFatha   -- ماضٍ آخرُ خلاياه غيرُ مفتوحٍ ظاهرًا: لاحقةٌ (ضَرَبَتْ، ضَرَبْتُ) أو مقصورٌ (رَمَى) — لا يُبنى
  | mudariAkhirGhayrDamma -- مضارعٌ آخرُ خلاياه غيرُ مضمومٍ ظاهرًا: منصوبٌ أو مجزوم أو بلاحقة أو مقدَّرٌ (يَضْرِبَ، يَرْمِ، يَعِدْنَ، يَدْعُو)
  | mudaafAkhir           -- آخرُه مشدَّد (قبل الأخيرة ساكنةٌ من حرفها): الإدغامُ لم يُبنَ (مَدَّ، يَمُدُّ)
  | illaSakin             -- حرفُ علّةٍ ساكن: القلبُ (قال وباع، L244) وتبديلُ الحركات وحده (أَوْعَدَ، بَيَّنَ) لم يُبنيا
  | kharijAnmat           -- لا سببَ تشخيصيًّا ولا نمطَ معلَنًا: سابقةٌ، أو لاحقةٌ تُخرجه عن الأنماط، أو بابٌ لم يُبنَ (سَيَعِدُ، ضَرَبْنَ، سَرُوَ)
deriving DecidableEq, Repr

/-- آخرُ الكلمة مشدَّد: الخليةُ قبل الأخيرة ساكنةٌ من حرف الأخيرة (الشدّةُ خليتان). -/
def mudaafAkhir (l : List Nat) : Bool :=
  match l.reverse with
  | c :: d :: _ => harf d == harf c && hala d == 3
  | _ => false

/-- حرفٌ متحرّكٌ غيرُ الألف (دون 116). -/
def mutaharrik (c : Nat) : Bool := c < 116 && harf c != alif && hala c != 3
/-- حرفٌ صحيحٌ ساكن: ليس ألفًا ولا واوًا ولا ياءً. -/
def sahihSakin (c : Nat) : Bool := c < 116 && harf c != alif && harf c != waw && harf c != ya && hala c == 3
/-- حرفُ المضارعة: من «نأيت» (القطر L65 «وافتتاحه بحرف من نأيت»: ن 14، ء 0، ي 11، ت 18) مفتوحًا أو مضمومًا. -/
def harfMudara (c : Nat) : Bool :=
  c < 116 && (harf c == nun || harf c == 0 || harf c == ya || harf c == 18) && (hala c == 0 || hala c == 1)

/-- متحرّكٌ بحركةٍ معيّنة. -/
def mutaharrikBi (c h : Nat) : Bool := mutaharrik c && hala c == h
/-- آخرُ الماضي في النمط: مفتوحٌ غيرُ واو — الكتاب س20543 «هذه الواو لا تقع قبلها أبدا كسرة إلا قلبت ياء وذلك نحو غاز وغزي» (وفيه س20488
«سرو يسرو»). -/
def akhirMadi (c : Nat) : Bool := mutaharrikBi c 0 && harf c != waw
/-- آخرُ المضارع في النمط: مضمومٌ ظاهرًا غيرُ واوٍ ولا ياء — فالضمّةُ عليهما مقدَّرة: القطر L92–94 «تقدر جميع الحركات … والضمة في نحو
"يدعو ويقضي"»؛ والمخرجُ بفتحٍ قبلهما (يُغْزَوُ) على غير القاعدة: الكتاب س20502–20506 «وإذا كانت الياء والواو قبلها فتحة اعتلت وقلبت ألفا …
وذلك قولك رمى ويرمى وغزا ويغزى». -/
def akhirMudari (c : Nat) : Bool := mutaharrikBi c 1 && harf c != waw && harf c != ya

/-- **أنماطُ المُدخَل المعلَنة** (تعيينُ البنّاء على قاعدة القطر L242–243 «ويضم أول الفعل مطلقا، ويشاركه ثاني نحو / تعلم، وثالث نحو انطلق»
ومثاليها، وL243 «ويفتح ما قبل الآخر في المضارع، ويكسر في الماضي»): كلُّ خليةٍ متحرّكةٌ أو صحيحةٌ ساكنة في موضعها، وآخرُ الماضي مفتوحٌ
غيرُ واو (`akhirMadi`)، والمضارعُ بحرفٍ من «نأيت» (L65) مضمومَ الآخر ظاهرًا غيرَ واوٍ ولا ياء (`akhirMudari`):
- الماضي البسيط: فَعَلَ/فَعِلَ/فَعُلَ (ثلاثُ خلايا)؛ وفَعَّلَ/فَعْلَلَ/أَفْعَلَ (أربعٌ، الثانيةُ ساكنة).
- بمشاركة الثاني (`thani`): تَفَعَّلَ/تَفَعْلَلَ (تاءٌ مفتوحة، والثالثةُ ساكنة).
- بمشاركة الثالث (`thalith`): اِنْفَعَلَ/اِفْتَعَلَ (همزةُ وصلٍ مكسورة، والثانيةُ ساكنة)؛ واِسْتَفْعَلَ/اِفْعَنْلَلَ/اِفَّعَّلَ (ستٌّ، الثانيةُ والرابعةُ ساكنتان).
- المضارع: يَفْعِلُ/يُفْعِلُ (أربعٌ، الثانيةُ ساكنة)؛ ويَنْفَعِلُ/يَفْتَعِلُ (مفتوحُ الأوّل، الثانيةُ ساكنة) ويُفَعِّلُ/يُفَعْلِلُ (مضمومُ الأوّل، الثالثةُ ساكنة)؛
  ويَتَفَعَّلُ/يَتَفَعْلَلُ ويَسْتَفْعِلُ/يَفْعَنْلِلُ ويَفَّعَّلُ (يَذَّكَّرُ: الثانيةُ ساكنةٌ من حرف الثالثة والرابعةُ من حرف الخامسة) (ستّ).
ولا تُقرأ في النمط سابقة. **وما لا تُميّزه الخلايا يمرّ على عهدة المُدخِل** (`shahid_anmat`): اللاحقةُ المضمومة في المضارع والمفتوحة في
الماضي إذا وافق الشكلُ نمطًا (يَدْعُهُ في صورة يَكْرَهُ ← يُدْعَهُ؛ غَرَّكَ في صورة فَعَّلَ ← غُرِّكَ)، والزمنُ المعلَن خطأً إذا وافق الشكلُ نمطَ
الزمن المعلَن (يَشْرَبَ ماضيًا ← يُشْرِبَ)، وصورةُ الأصل للأجوف (قَوَلَ ← قُوِلَ)؛ واللاحقةُ غيرُ المضمومة في المضارع وغيرُ المفتوحة في الماضي تُرفض بسببها، وما سوى ذلك خارجَ الأنماط. -/
def namat (madi : Bool) (g : Siga) (l : List Nat) : Bool :=
  match madi, g, l with
  | true, .basit, [a, b, c] => mutaharrikBi a 0 && mutaharrik b && akhirMadi c
  | true, .basit, [a, x, b, c] => mutaharrikBi a 0 && sahihSakin x && mutaharrikBi b 0 && akhirMadi c
  | true, .thani, [t, a, x, b, c] => t == kh 18 0 && mutaharrikBi a 0 && sahihSakin x && mutaharrikBi b 0 && akhirMadi c
  | true, .thalith, [h, x, a, b, c] => h == kh 0 2 && sahihSakin x && mutaharrikBi a 0 && mutaharrikBi b 0 && akhirMadi c
  | true, .thalith, [h, x, t, y, b, c] =>
      h == kh 0 2 && sahihSakin x && mutaharrikBi t 0 && sahihSakin y && mutaharrikBi b 0 && akhirMadi c
  | false, _, [p, x, b, c] => harfMudara p && sahihSakin x && mutaharrik b && akhirMudari c
  | false, _, [p, a, b, c, d] =>
      harfMudara p && akhirMudari d && mutaharrikBi c 2 &&
      ((hala p == 0 && sahihSakin a && mutaharrikBi b 0) || (hala p == 1 && mutaharrikBi a 0 && sahihSakin b))
  | false, _, [p, a, b, c, d, e] =>
      harfMudara p && hala p == 0 && akhirMudari e &&
      ((a == kh 18 0 && mutaharrikBi b 0 && sahihSakin c && mutaharrikBi d 0) ||
       (sahihSakin a && mutaharrikBi b 0 && sahihSakin c && mutaharrikBi d 2) ||
       (sahihSakin a && mutaharrikBi b 0 && harf a == harf b && sahihSakin c && mutaharrikBi d 0 && harf c == harf d))
  | _, _, _ => false

/-- الأسبابُ التشخيصيّة بترتيبها: الطولُ (القصيرُ، ثمّ المضارعُ دون أربع — تعيينُ البنّاء)، ثمّ حالةُ الآخر ظاهرًا، ثمّ الآخرُ
المشدَّد، ثمّ حرفُ العلّة الساكن. -/
def sababTashkhis (madi : Bool) (g : Siga) (l : List Nat) : List SababMajhul :=
  (if l.length < mawdiMusharik (sigaFiliyya madi g) + 3 then [.qasir]
   else if !madi && l.length < 4 then [.mudariDunArba] else []) ++
  (if madi then (if (akhir l).map hala != some 0 then [.madiAkhirGhayrFatha] else [])
   else (if (akhir l).map hala != some 1 then [.mudariAkhirGhayrDamma] else [])) ++
  (if mudaafAkhir l then [.mudaafAkhir] else []) ++
  (if l.any illaSakin then [.illaSakin] else [])

/-- أسبابُ الرفض: التشخيصيّةُ إن وُجدت، وإلّا «خارج الأنماط» إن لم يكن المُدخَل على نمطٍ معلَن. -/
def sababMajhul (madi : Bool) (g : Siga) (l : List Nat) : List SababMajhul :=
  sababTashkhis madi g l ++ (if (sababTashkhis madi g l).isEmpty && !namat madi g l then [.kharijAnmat] else [])

/-- **المجهول** (L242–244): ضمُّ الأوّل — ومعه الثاني في نحو تعلّم، والثالث في نحو انطلق، في الماضي — وكسرُ ما قبل الآخر في الماضي وفتحُه في
المضارع، على صورة الابتداء (همزةُ الوصل خليةً). يُرفض باسمه ما له سببٌ في `sababMajhul` — رفضٌ لا خطأ، وحدٌّ للأداة لا امتناعٌ لغويّ. -/
def majhul (madi : Bool) (g : Siga) (l : List Nat) : Option (List Nat) :=
  if sababMajhul madi g l ≠ [] then none
  else some (badilInda (musharik (sigaFiliyya madi g) (badilInda l 0 1)) (l.length - 2) (if madi then 2 else 0))

/-- **المجهولُ يحفظ الحروف**: الحروفُ بعينها وإنّما تتبدّل الحركات — لكلّ كلمة. -/
theorem majhul_huruf (madi : Bool) (g : Siga) (l l' : List Nat) (h : majhul madi g l = some l') : l'.map harf = l.map harf := by
  unfold majhul at h
  split at h
  · exact absurd h (by simp)
  · simp only [Option.some.injEq] at h
    rw [← h, badilInda_harf, musharik_harf, badilInda_harf]

/-- **المجهولُ يحفظ الطول**. -/
theorem majhul_tul (madi : Bool) (g : Siga) (l l' : List Nat) (h : majhul madi g l = some l') : l'.length = l.length := by
  unfold majhul at h
  split at h
  · exact absurd h (by simp)
  · simp only [Option.some.injEq] at h
    rw [← h, badilInda_tul, musharik_tul, badilInda_tul]

/-- **المجهولُ لا يخرج عن خلايا الكلمة** (دون 116) — لكلّ كلمةٍ خلاياها دون 116. -/
theorem majhul_dun_116 (madi : Bool) (g : Siga) (l l' : List Nat) (hl : ∀ c ∈ l, c < 116) (h : majhul madi g l = some l') :
    ∀ c ∈ l', c < 116 := by
  unfold majhul at h
  split at h
  · exact absurd h (by simp)
  · simp only [Option.some.injEq] at h
    rw [← h]
    exact badilInda_lt _ _ _ (musharik_lt _ _ (badilInda_lt l 0 1 hl))

/-- **ما يُرفض باسمه**: القصيرُ عن موضع المشارِك بثلاث، وذو حرفِ العلّة الساكن — لكلّ صيغة، بفكّ التعريف. -/
theorem majhul_marfud (madi : Bool) (g : Siga) (l : List Nat)
    (hl : l.length < mawdiMusharik (sigaFiliyya madi g) + 3 ∨ l.any illaSakin = true) : majhul madi g l = none := by
  unfold majhul
  split
  · rfl
  · rename_i hn
    refine absurd ?_ hn
    unfold sababMajhul sababTashkhis
    rcases hl with h | h
    · simp [h]
    · simp [h]

/-- **لا مخرجَ إلّا على نمطٍ معلَن:** ترخيصُ المجهول بشاهدٍ موجب (`namat`) لا بغياب سببٍ تشخيصيّ. -/
theorem majhul_namat (madi : Bool) (g : Siga) (l l' : List Nat) (h : majhul madi g l = some l') : namat madi g l = true := by
  unfold majhul at h
  split at h
  · exact absurd h (by simp)
  · rename_i hn
    unfold sababMajhul at hn
    cases hd : (sababTashkhis madi g l).isEmpty <;> cases hm : namat madi g l <;> simp_all

/-- **لا رفضَ للمجهول إلّا بسببٍ مسمّى** (LC06): `none` ⟺ قائمةُ الأسباب غيرُ فارغة. -/
theorem majhul_none_iff (madi : Bool) (g : Siga) (l : List Nat) : majhul madi g l = none ↔ sababMajhul madi g l ≠ [] := by
  unfold majhul
  split <;> simp_all

/-- **على الشاهد (LC06):** ما كان يُخرج صورةً على غير قاعدةٍ تعرفها الأداة صار يُرفض باسمه (`#eval` على ca5ed3c للحال قبله):
- المضارعُ دون الأربع: يَعِدُ ويَضَعُ (كانا يُعَدُ ويُضَعُ؛ والواوُ ساقطةٌ من الفعل: الكتاب س19844–19845 «ولم تذهب الواو كما ذهبت في الفعل …
  ما في يعد»)، ويَغْزُ (كان يُغَزُ).
- المضارعُ غيرُ المضموم الآخر ظاهرًا: يَدْعُوَ (كان يُدْعَوَ)، ويَعِدْنَ بنون النسوة (كان يُعِدَنَ)، ويَدْعُو مرفوعًا تقديرًا (ومعه حرفُ العلّة
  الساكن)؛ و**رفضٌ لا خطأ**: يَقُمْ (كان يُقَمْ)، ويَضْرِبَ منصوبًا (كان يُضْرَبَ)، ويَضْرِبْ مجزومًا (كان يُضْرَبْ) — المنصوبُ والمجزومُ خارج العقد،
  والأداةُ لا تفرّق المجزومَ الأجوفَ من الناقص الذي كان يُخرج يُرَمِ من يَرْمِ.
- الماضي غيرُ المفتوح الآخر ظاهرًا: ضَرَبَتْ (كان ضُرَبِتْ)، وقُلْتُ (كان قُلِتُ)، ورَدَّتْ (كان رُدِّتْ)، ورَمَى (ومعه حرفُ العلّة الساكن).
- الآخرُ المشدَّد: مَدَّ ويَمُدُّ (كانا مُدِدَ ويُمُدَدُ).
- وما كان يُرفض بقي بأسبابه (قَالَ، والقصير)؛ ووَعَدَ ← وُعِدَ ويَضْرِبُ ← يُضْرَبُ وتَعَلَّمَ ← تُعُلِّمَ كما كانت.
وأسبابُ الجسر الثلاثة: كلمةٌ فارغة، وخليةٌ 116، وضَرْ بالسكون في المفرد؛ وضَرُ بالضمّة لا سبب.
ع 3، د 17، ض 12، م 27، ق 7، ل 13، ت 18، ر 15، غ 5، ز 19، ن 14، و 28. -/
theorem shawahid_sabab :
    sababMajhul false .basit [kh ya 0, kh 3 2, kh 17 1] = [.mudariDunArba] ∧
    sababMajhul false .basit [kh ya 0, kh 12 0, kh 3 1] = [.mudariDunArba] ∧
    sababMajhul false .basit [kh ya 0, kh 5 3, kh 19 1] = [.mudariDunArba] ∧
    sababMajhul false .basit [kh ya 0, kh 17 3, kh 3 1, kh waw 0] = [.mudariAkhirGhayrDamma] ∧
    sababMajhul false .basit [kh ya 0, kh 3 2, kh 17 3, kh nun 0] = [.mudariAkhirGhayrDamma] ∧
    sababMajhul false .basit [kh ya 0, kh 7 1, kh 27 3] = [.mudariDunArba, .mudariAkhirGhayrDamma] ∧
    sababMajhul false .basit [kh ya 0, kh 12 3, kh 15 2, kh 26 0] = [.mudariAkhirGhayrDamma] ∧
    sababMajhul false .basit [kh ya 0, kh 12 3, kh 15 2, kh 26 3] = [.mudariAkhirGhayrDamma] ∧
    sababMajhul false .basit [kh ya 0, kh 17 3, kh 3 1, kh waw 3] = [.mudariAkhirGhayrDamma, .illaSakin] ∧
    sababMajhul true .basit [kh 15 0, kh 27 0, kh alif 3] = [.madiAkhirGhayrFatha, .illaSakin] ∧
    sababMajhul true .basit [kh 12 0, kh 15 0, kh 26 0, kh 18 3] = [.madiAkhirGhayrFatha] ∧
    sababMajhul true .basit [kh 7 1, kh 13 3, kh 18 1] = [.madiAkhirGhayrFatha] ∧
    sababMajhul true .basit [kh 15 0, kh 17 3, kh 17 0, kh 18 3] = [.madiAkhirGhayrFatha] ∧
    sababMajhul true .basit [kh 27 0, kh 17 3, kh 17 0] = [.mudaafAkhir] ∧
    sababMajhul false .basit [kh ya 0, kh 27 1, kh 17 3, kh 17 1] = [.mudaafAkhir] ∧
    sababMajhul true .basit [kh 7 0, kh alif 3, kh 13 0] = [.illaSakin] ∧
    sababMajhul true .basit [kh 12 0, kh 15 0] = [.qasir] ∧
    majhul false .basit [kh ya 0, kh 3 2, kh 17 1] = none ∧
    majhul true .basit [kh waw 0, kh 3 0, kh 17 0] = some [kh waw 1, kh 3 2, kh 17 0] ∧
    majhul false .basit [kh ya 0, kh 12 3, kh 15 2, kh 26 1] = some [kh ya 1, kh 12 3, kh 15 0, kh 26 1] ∧
    majhul true .thani [kh 18 0, kh 3 0, kh 13 3, kh 13 0, kh 27 0] = some [kh 18 1, kh 3 1, kh 13 3, kh 13 2, kh 27 0] ∧
    sababDal .mufrad [] = some .farigh ∧ sababDal .mufrad [kh 12 0, 116] = some .fawqHadd ∧
    sababDal .mufrad [kh 12 0, kh 15 3] = some .laYaqbaluhuBab ∧ sababDal .mufrad [kh 12 0, kh 15 1] = none := by
  decide

set_option synthInstance.maxSize 8192 in
/-- **الأنماطُ على الشاهد (LC06):** ترخيصٌ بنمطٍ موجب —
- الماضي: رَضِيَ ← رُضِيَ، أَكَلَ ← أُكِلَ؛ عَلَّمَ ← عُلِّمَ، أَكْرَمَ ← أُكْرِمَ؛ تَزَلْزَلَ ← تُزُلْزِلَ؛ اِكْتَسَبَ ← اُكْتُسِبَ؛ اِسْتَغْفَرَ ← اُسْتُغْفِرَ.
- المضارع: يَقْرَأُ ← يُقْرَأُ، يُكْرِمُ ← يُكْرَمُ، تَضْرِبُ ← تُضْرَبُ؛ يَنْطَلِقُ ← يُنْطَلَقُ، يَكْتَسِبُ ← يُكْتَسَبُ، يُعَلِّمُ ← يُعَلَّمُ؛ يَتَزَلْزَلُ ← يُتَزَلْزَلُ،
  يَسْتَغْفِرُ ← يُسْتَغْفَرُ.
- يَفَّعَّلُ: يَذَّكَّرُ ← يُذَّكَّرُ.
- **وما لا تُميّزه الخلايا يمرّ على عهدة المُدخِل:** يَدْعُهُ ← يُدْعَهُ (في صورة يَكْرَهُ ← يُكْرَهُ)؛ غَرَّكَ ← غُرِّكَ (في صورة فَعَّلَ)؛ ويَشْرَبَ
  معلَنًا ماضيًا ← يُشْرِبَ (الزمنُ على عهدة المُدخِل)؛ وصورةُ الأصل للأجوف: قَوَلَ ← قُوِلَ، بَيَعَ ← بُيِعَ، أَقْوَمَ ← أُقْوِمَ، يَقْوُلُ ← يُقْوَلُ (لا تُميّزها الخلايا
  ممّا جاء على الأصل غيرَ معتلّ: أَعْوَزَ ← أُعْوِزَ — الكتاب س19976–19979؛ والأجوفُ بعد القلب بأوجهه الثلاثة L244 لم يُبنَ).
و**خارجَ الأنماط** يُرفض باسمه ما كان يمرّ على غير القاعدة (`#eval` على ca5ed3c): السابقةُ (سَيَعِدُ ← سُيَعَدُ، فَضَرَبَ ← فُضَرِبَ)، واللاحقةُ
التي تُخرجه عن الأنماط (يَعِدُهُ ← يُعِدَهُ، ضَرَبْنَ ← ضُرَبِنَ، ضَرَبْتَ ← ضُرَبِتَ)، وواوُ الماضي آخرًا (سَرُوَ ← سُرِوَ)، والصيغةُ والزمنُ المعلَنان
خطأً إذا خالف الشكلُ نمطَه (اِنْطَلَقَ بالبسيطة ← اُنْطَلِقَ؛ يَضْرِبَ ماضيًا ← يُضْرِبَ)؛ ومَكْتَبُ مُعلَنًا مضارعًا (الميمُ ليست من «نأيت»، L65)؛ وآخرُ المضارع واوًا أو ياءً
مضمومةً ظاهرًا (يَغْزُوُ ← يُغْزَوُ، يَرْمِيُ ← يُرْمَيُ).
وشواهدُ سالبةٌ لكلّ نمطٍ أطول (صورٌ مصنوعةٌ للحدّ، لا شواهدُ لغة): يَشْتَرِيُ ويَسْتَدْعِيُ (الياءُ مضمومةً في الخماسيّ والسداسيّ)، يَفْتَحُهُ، ومُعَلِّمُ مضارعًا، ويُسْتَخْرِجُ ومَسْتَخْرِجُ مضارعًا، ونَعَلَّمَ بالثانية،
وتَكْتَسَبَ بالثالثة، واِسْتَغْفِرَ ماضيًا.
س 20، ف 25، ه 1، ك 8، ط 16، ق 7، ء 0، م 27، ب 26، ع 3، ل 13، ز 19، ت 18، غ 5، ر 15، د 17، ض 12، ش 10، ذ 23، ح 4، خ 6، ج 9، و `waw`، ي `ya`. -/
theorem shahid_anmat :
    (majhul true .basit [kh 15 0, kh 12 2, kh ya 0] = some [kh 15 1, kh 12 2, kh ya 0] ∧
    majhul true .basit [kh 0 0, kh 8 0, kh 13 0] = some [kh 0 1, kh 8 2, kh 13 0] ∧
    majhul true .basit [kh 3 0, kh 13 3, kh 13 0, kh 27 0] = some [kh 3 1, kh 13 3, kh 13 2, kh 27 0] ∧
    majhul true .basit [kh 0 0, kh 8 3, kh 15 0, kh 27 0] = some [kh 0 1, kh 8 3, kh 15 2, kh 27 0] ∧
    majhul true .thani [kh 18 0, kh 19 0, kh 13 3, kh 19 0, kh 13 0] = some [kh 18 1, kh 19 1, kh 13 3, kh 19 2, kh 13 0] ∧
    majhul true .thalith [kh 0 2, kh 8 3, kh 18 0, kh 20 0, kh 26 0] = some [kh 0 1, kh 8 3, kh 18 1, kh 20 2, kh 26 0] ∧
    majhul true .thalith [kh 0 2, kh 20 3, kh 18 0, kh 5 3, kh 25 0, kh 15 0] =
      some [kh 0 1, kh 20 3, kh 18 1, kh 5 3, kh 25 2, kh 15 0] ∧
    majhul false .basit [kh ya 0, kh 7 3, kh 15 0, kh 0 1] = some [kh ya 1, kh 7 3, kh 15 0, kh 0 1] ∧
    majhul false .basit [kh ya 1, kh 8 3, kh 15 2, kh 27 1] = some [kh ya 1, kh 8 3, kh 15 0, kh 27 1] ∧
    majhul false .basit [kh 18 0, kh 12 3, kh 15 2, kh 26 1] = some [kh 18 1, kh 12 3, kh 15 0, kh 26 1] ∧
    majhul false .basit [kh ya 0, kh nun 3, kh 16 0, kh 13 2, kh 7 1] = some [kh ya 1, kh nun 3, kh 16 0, kh 13 0, kh 7 1] ∧
    majhul false .basit [kh ya 0, kh 8 3, kh 18 0, kh 20 2, kh 26 1] = some [kh ya 1, kh 8 3, kh 18 0, kh 20 0, kh 26 1] ∧
    majhul false .basit [kh ya 1, kh 3 0, kh 13 3, kh 13 2, kh 27 1] = some [kh ya 1, kh 3 0, kh 13 3, kh 13 0, kh 27 1] ∧
    majhul false .basit [kh ya 0, kh 18 0, kh 19 0, kh 13 3, kh 19 0, kh 13 1] =
      some [kh ya 1, kh 18 0, kh 19 0, kh 13 3, kh 19 0, kh 13 1] ∧
    majhul false .basit [kh ya 0, kh 20 3, kh 18 0, kh 5 3, kh 25 2, kh 15 1] =
      some [kh ya 1, kh 20 3, kh 18 0, kh 5 3, kh 25 0, kh 15 1] ∧
    majhul false .basit [kh ya 0, kh 17 3, kh 3 1, kh 1 1] = some [kh ya 1, kh 17 3, kh 3 0, kh 1 1] ∧
    majhul true .basit [kh 5 0, kh 15 3, kh 15 0, kh 8 0] = some [kh 5 1, kh 15 3, kh 15 2, kh 8 0] ∧
    majhul true .basit [kh ya 0, kh 10 3, kh 15 0, kh 26 0] = some [kh ya 1, kh 10 3, kh 15 2, kh 26 0] ∧
    majhul false .basit [kh ya 0, kh 23 3, kh 23 0, kh 8 3, kh 8 0, kh 15 1] = some [kh ya 1, kh 23 3, kh 23 0, kh 8 3, kh 8 0, kh 15 1] ∧
    majhul true .basit [kh 7 0, kh waw 0, kh 13 0] = some [kh 7 1, kh waw 2, kh 13 0] ∧
    majhul false .basit [kh ya 0, kh 7 3, kh waw 1, kh 13 1] = some [kh ya 1, kh 7 3, kh waw 0, kh 13 1] ∧
    majhul true .basit [kh 26 0, kh ya 0, kh 3 0] = some [kh 26 1, kh ya 2, kh 3 0] ∧
    majhul true .basit [kh 0 0, kh 7 3, kh waw 0, kh 27 0] = some [kh 0 1, kh 7 3, kh waw 2, kh 27 0] ∧
    majhul true .basit [kh 0 0, kh 3 3, kh waw 0, kh 19 0] = some [kh 0 1, kh 3 3, kh waw 2, kh 19 0]) ∧
    (sababMajhul false .basit [kh 20 0, kh ya 0, kh 3 2, kh 17 1] = [.kharijAnmat] ∧
    sababMajhul false .basit [kh ya 0, kh 5 3, kh 19 1, kh waw 1] = [.kharijAnmat] ∧
    sababMajhul false .basit [kh ya 0, kh 15 3, kh 27 2, kh ya 1] = [.kharijAnmat] ∧
    sababMajhul true .basit [kh 25 0, kh 12 0, kh 15 0, kh 26 0] = [.kharijAnmat] ∧
    sababMajhul false .basit [kh ya 0, kh 3 2, kh 17 1, kh 1 1] = [.kharijAnmat] ∧
    sababMajhul true .basit [kh 12 0, kh 15 0, kh 26 3, kh nun 0] = [.kharijAnmat] ∧
    sababMajhul true .basit [kh 12 0, kh 15 0, kh 26 3, kh 18 0] = [.kharijAnmat] ∧
    sababMajhul true .basit [kh 20 0, kh 15 1, kh waw 0] = [.kharijAnmat] ∧
    sababMajhul true .basit [kh 0 2, kh nun 3, kh 16 0, kh 13 0, kh 7 0] = [.kharijAnmat] ∧
    sababMajhul true .basit [kh ya 0, kh 12 3, kh 15 2, kh 26 0] = [.kharijAnmat] ∧
    sababMajhul false .basit [kh 27 0, kh 8 3, kh 18 0, kh 26 1] = [.kharijAnmat] ∧
    sababMajhul false .basit [kh ya 0, kh 25 3, kh 18 0, kh 4 1, kh 1 1] = [.kharijAnmat] ∧
    sababMajhul false .basit [kh 27 1, kh 3 0, kh 13 3, kh 13 2, kh 27 1] = [.kharijAnmat] ∧
    sababMajhul false .basit [kh ya 1, kh 20 3, kh 18 0, kh 6 3, kh 15 2, kh 9 1] = [.kharijAnmat] ∧
    sababMajhul false .basit [kh 27 0, kh 20 3, kh 18 0, kh 6 3, kh 15 2, kh 9 1] = [.kharijAnmat] ∧
    sababMajhul true .thani [kh nun 0, kh 3 0, kh 13 3, kh 13 0, kh 27 0] = [.kharijAnmat] ∧
    sababMajhul true .thalith [kh 18 0, kh 8 3, kh 18 0, kh 20 0, kh 26 0] = [.kharijAnmat] ∧
    sababMajhul true .thalith [kh 0 2, kh 20 3, kh 18 0, kh 5 3, kh 25 2, kh 15 0] = [.kharijAnmat] ∧
    sababMajhul false .basit [kh ya 0, kh 10 3, kh 18 0, kh 15 2, kh ya 1] = [.kharijAnmat] ∧
    sababMajhul false .basit [kh ya 0, kh 20 3, kh 18 0, kh 17 3, kh 3 2, kh ya 1] = [.kharijAnmat]) := by
  decide

/-- الشواهد: ضَرَبَ→ضُرِبَ، يَضْرِبُ→يُضْرَبُ، تَعَلَّمَ→تُعُلِّمَ (الشدّة خليتان: ساكنٌ فمتحرّك)، اِنْطَلَقَ→اُنْطُلِقَ (همزةُ الوصل حاملًا 0 مكسورةً في
الابتداء، ومضمومةً في المجهول)؛ ومضارعُ تعلّم بالصيغة الثانية يُتَعَلَّمُ (ضمُّ الأوّل وحده). ض 12، ر 15، ب 26، ط 16، ق 7. -/
theorem shawahid_majhul :
    majhul true .basit [kh 12 0, kh 15 0, kh 26 0] = some [kh 12 1, kh 15 2, kh 26 0] ∧
    majhul false .basit [kh ya 0, kh 12 3, kh 15 2, kh 26 1] = some [kh ya 1, kh 12 3, kh 15 0, kh 26 1] ∧
    majhul true .thani [kh 18 0, kh 3 0, kh 13 3, kh 13 0, kh 27 0] = some [kh 18 1, kh 3 1, kh 13 3, kh 13 2, kh 27 0] ∧
    majhul true .thalith [kh 0 2, kh nun 3, kh 16 0, kh 13 0, kh 7 0] = some [kh 0 1, kh nun 3, kh 16 1, kh 13 2, kh 7 0] ∧
    majhul false .thani [kh ya 0, kh 18 0, kh 3 0, kh 13 3, kh 13 0, kh 27 1] = some [kh ya 1, kh 18 0, kh 3 0, kh 13 3, kh 13 0, kh 27 1] := by
  decide

/-- **انطلق على صورة الابتداء عند المالك**: مجهولُ صورة الابتداء (`Law.ibtidaForm`: همزةُ الوصل حاملًا 0 بحركةٍ مشتقّةٍ من الثالث
`waslHaraka`: ضمّةٌ إن ضُمَّ الثالث وإلّا كسرة) هو صورةُ ابتداء المجهول — فضمُّ الثالث (L243) يضمّ همزةَ الوصل بقاعدة المالك — على الشاهد. -/
theorem intilaq_wasl :
    majhul true .thalith (Law.ibtidaForm false [kh nun 3, kh 16 0, kh 13 0, kh 7 0]) =
      some (Law.ibtidaForm false [kh nun 3, kh 16 1, kh 13 2, kh 7 0]) := by
  decide

end JisrDal
end Jisr
