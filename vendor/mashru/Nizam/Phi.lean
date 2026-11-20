/-
  Nizam/Phi.lean — Φ: التركيبُ الجامعُ المانع بالمنطق الثلاثيّ (المرحلة «ب» من قانون المواصفة).

  قولُ المالك (2026-10-20، 00:23 بتوقيت عمّان): «(ب) Φ العامّة في Lean مع المنطق الثلاثيّ، تُعمِّم kull_ma_kull. موافق».
  مصدرُ التصميم مرفقُ المالك «المبرهنة الجامعة المانعة للدالة الثنائية العودية Φ» (`Mashru_Fractal_Theorem_AR.md`، غيرُ مودَع): يقول
  في س4 إنّه «حجة رياضية كاملة بالاستقراء على شجرة منتهية، وليست شهادة نجاح Lean»؛ ومبرهنتُه (س43–47) على الحلول (حلٌّ أو لا)،
  وطبقتا الدليل P/N الثلاثيّتان في §8 (س78). وهنا تُبرهن في Lean بالحكم الثلاثيّ:

  ١. **الحكمُ الثلاثيّ وطبقتاه** (`K3`: مرخَّص P، ممتنع N، لا حكم U): الربطُ `wa` والفصلُ `aw`؛ وتمثيلُ القيمة الواحدة بطبقتي البتّات
     (قبول، ردّ) كما في المرفق س78: الربطُ (∧، ∨) والفصلُ (∨، ∧) (`tabaqat_wa`، `tabaqat_aw`)، والتمثيلُ حقنيّ ولا تجتمع الطبقتان فيه
     (`tabaqat_la_taarud` — صادقٌ بالبناء، إذ لا قيمةَ للتعارض في `K3`). و«لا حكم» غيابُ البتّين معًا، لا ردّ.
  ٢. **الإسقاطُ الوجوديّ** `yujad`: مرخَّصٌ ⟺ امتدادٌ مرخَّص، وممتنعٌ ⟺ كلُّ امتدادٍ ممتنع (`yujad_P`، `yujad_N`، `yujad_map_P`،
     `yujad_map_N`)؛ والنطاقُ الفارغ ممتنع — في المغلق. **و§٢أ (LC19 جزئيًّا، 2026-10-20؛ تصميمُه قرارُ البنّاء):** الإسقاطُ المفتوح
     `yujadMaftuh` لا يُخرج «ممتنع» أبدًا (`yujadMaftuh_ne_N`)، والنطاقُ `Nitaq` بشهادة استنفادٍ اختياريّة، و`yujadN` مغلقٌ بها ومفتوحٌ
     بدونها: لا امتناعَ كلّيًّا إلّا بالشهادة وامتناعِ كلّ قيمةٍ من النوع (`yujadN_N`، `la_N_bila_istinfad`)؛ والشهادةُ نسبيّةٌ إلى النوع
     (`shahada_nisbiyya`).
  ٣. **التركيبُ على منفذٍ مشترك** `tarkib` (`tarkib_P`، `tarkib_N`)، **والسلسلة** `zanjir`: مرخَّصةٌ ⟺ مسارٌ في النطاق كلُّ عوامله مرخِّصة
     (`zanjir_P`)، وممتنعةٌ ⟺ في كلّ مسارٍ عاملٌ يمنع (`zanjir_N`)، وما سواهما «لا حكم» (`zanjir_U`) — بالاستقراء على طول السلسلة.
  ٤. **Φ على الشجرة** (حالةُ المرفق العامّة، س38): عقدةٌ تربط ولدين ثمّ تُسقط متغيّراتٍ مسمّاة (`Shajara`، `phi`). بشرط الواجهة
     `Wajiha` (ما يُسقَط داخل ولدٍ لا يتعلّق به ربطُ عوامل الآخر، ويكفي له ألّا يتعلّق به عاملٌ منها `awraq_la_yataallaq` — قراءةُ البنّاء
     لقول المرفق س55) فـΦ بالعَوْد هي إسقاطٌ واحدٌ لربط العوامل
     كلّها على كلّ ما أُسقط (`phi_awd`)، فهي جامعةٌ مانعة: مرخِّصةٌ ⟺ يوجد مدٌّ للمُسقَطات من النطاق يُرخِّص فيه كلُّ عامل (`shajara_P`)،
     وممتنعةٌ ⟺ في كلّ مدٍّ عاملٌ يمنع (`shajara_N`)، وما سواهما «لا حكم» (`shajara_U`). وعمادُها أنّ الحكم الثلاثيّ شبكةٌ توزيعيّة
     (`wa_aw_tawzi`) فالإسقاطُ يتوزّع على ربطٍ بما لا يتعلّق بالمُسقَط (`yujadV_wa`).
  ٥. **ضرورةُ الواجهة** (المرفق س64–65، على الشاهد): a⊕b⊕c=0 حلولُه الأربعةُ بأعيانها وربطُ إسقاطاته الزوجيّة يقبل الثمانية
     (`wajiha_daruriyya`، على قوائم `Bool` لا على `phi`)؛ وعاملا key=0 وkey=1 على `phi` نفسِها: الشجرةُ الصحيحة ممتنعة، والتي تُسقط key
     في الولدين قبل الربط مرخِّصةٌ زورًا وتخالف `Wajiha`، والصحيحةُ تستوفيه (`mithal_miftah`).
  ٦. **العقدُ حالةٌ من Φ**: عواملُ العقد الأربعة — القانونُ (P/N)، والمانعُ (P/N)، والجذرُ (المرشَّحُ P وغيرُه U لا N)، والشاهدُ (المشهودُ P
     وغيرُه U) — مربوطةٌ بـ`tarkib` على منفذ الجذر، مرّةً على المواصفة (`phiAqd`، والشاهدُ `Mashhud`) ومرّةً على المنفّذ (`phiAqdB`،
     والشاهدُ بتُّ `mustawa`)، ومتساويتان بحقول العقد و`mustawa_iff` (`amil_sawa`، `phiAqdB_sawa`). والمنفّذُ `hukmB` يحسب Φ بعينها (`hukmB_phiB`:
     من تعريفه و`tarkib_P`/`tarkib_N`، بلا `kull_ma_kull`)، فـ`aqd_phi`؛ ومنه **مراتبُ `kull_ma_kull` الثلاث مشتقّةٌ من Φ لكلّ عقد**
     (`kull_ma_kull_min_phi`: من `tarkib_P`/`tarkib_N`، بلا `kull_ma_kull`). و`phiAqd` (المواصفة) هي `phi` على شجرة العقد ذاتِ الأوراق
     الأربع، وشجرتُه تستوفي `Wajiha` (`phiAqd_shajara`)؛ فبتركيبها مع `aqd_phi_mashru` يقع حكمُ المحرّك `hukmB` على `Mashru` تحت `phi` على
     الشجرة (`hukmB_shajara_mashru`). وعلى `Mashru` بنطاق الجذور 32768 (`jidhr_hadd`، `aqd_phi_mashru`)، وشاهدُه كَتَبَ ← «علم» ترادفًا P ولزومًا U
     (`kataba_phi` — يمرّ بـ`kull_ma_kull` عبر شاهدَي `Nizam/Aqd.lean`).

  71 مبرهنة بالمعيار الموحَّد (`Nizam/Asas.lean`): 40 لكلّ (منها سبعٌ في §٢أ: `yujadMaftuh_P`، `yujadMaftuh_ne_N`، `yujadMaftuh_U`،
  `yujadN_P`، `yujadN_N`، `la_N_bila_istinfad`، `shahada_nisbiyya`) (الاستقراءُ على القوائم والسلسلة والشجرة، وما يستدعي مبرهنةً من الملفّ
  أو من المكتبة أو من `Nizam/Aqd.lean`)، و27 تعريفيّة (`phiAqd_shajara`، `phiAqd_farigh`، `tabaqat_*` الثلاث، `wa_P`/`wa_N`/`aw_P`/`aw_N`،
  `wa_tabadul`، `wa_aw_tawzi`، `ghayruhuma_U`، `tahdith_*` الأربع، `rutba_*` الثلاث، وعواملُ العقد الثمانية `amil*_P`/`_N`/`_ghayr_N`)،
  و4 على الشاهد: `wajiha_daruriyya` بـ decide، و`mithal_miftah` (أشطرُه الأربعة: الأوّلُ simp بالتعريفات، والثاني والثالث decide، والرابعُ
  تطبيقُ الفرض على معطًى ثمّ decide) و`istinfad_shawahid` بـ decide (§٢أ)، و`kataba_phi` (نقلٌ عبر `aqd_phi_mashru` من مبرهنتين على الشاهد
  في `Nizam/Aqd.lean`) — و`mithal_miftah` و`kataba_phi` خارجَ حرف المعيار («برهانُها decide»)، معلَن.
  طفراتُها `P272`–`P282` و`P291`–`P299` و`P333`–`P334` و`P337`–`P338` في `tahaqquq/tafrat.json` تُفشل `lake build` مباشرة؛ لا جدولَ
  خارجيًّا فلا مرآة بايثون.

  ما لا يُدّعى:
  * **ما تُسقطه المرتبة**: `rutba` تُسقط القراءةَ واسمَ السبب؛ فشطرُ `kull_ma_kull` الرابع (`QiraaSahiha`) و`mumtani_asbab` لا يُشتقّان من Φ.
  * **التعارض**: المرفق س78 «تعارض P وN يُرفض كتعـارض دليل»؛ و`K3` لا قيمةَ فيه للتعارض، فلا يُمثَّل جمعُ أدلّةٍ مستقلّةٍ متعارضة.
  * **المستهلك**: لا يقع تحت `zanjir` ولا `phi` شيءٌ من المحرّك بعد غيرُ حكم العقد على `Mashru` (`hukmB_shajara_mashru`)، وشجرتُه تركيبٌ
    واحد على منفذ الجذر.
  * **النطاقات**: النطاقُ قائمةٌ واحدة تقيّد المُسقَطات وحدها؛ والمتغيّراتُ غيرُ المُسقَطة حرّةٌ في σ، فقد تُرخِّص Φ على قيمةٍ خارج النطاق.
    والمرفق يشترط مجالًا D_x لكلّ متغيّر (س9) وعواملَ مجال (س24)؛ لم تُبنَ.
  * **الواجهة**: `Wajiha` شرطٌ دلاليّ مكمَّمٌ على كلّ تكليفٍ وكلّ قيمةٍ في D (لا في النطاق وحده)، فلا يحسبه مستهلك؛ وواجهتا المرفق الصريحتان
    B_l = (B_t ∩ V_l) ∪ Sep وB_r (س29–30) لم تُبنيا، ولا برهانَ أنّ بناءهما يحقّق `Wajiha`.
  * **إعادةُ التجميع** (المرفق س61: تغييرُ تجميع الشجرة مع حفظ الواجهات لا يغيّر الحلول) لم تُبرهن؛ ولا حفظُ Φ للعلاقة الثلاثيّة في المثال
    الأوّل على `phi` (س64).
  * **المنفّذُ البتّيّ**: طبقتا البتّات مبرهنتان على القيمة الواحدة وحدها؛ ولا منفّذَ بالأقنعة والإزاحة لربط الشجرة (المرفق س40)، ولا ترميزَ
    حقنيًّا للتكاليف (§1).
  * **المرفق**: `src/bitjoin.py` المذكور في س4 غيرُ مرفوع، ولم يُقارَن به شيء؛ ولا تُعاد مقارنتُه «بمعدّد مباشر مستقل في 1000 نظام قيود منتهٍ» (س4).
  * **آلةُ δ** (المرفق §7، س67–73): المرحلة «ج».
  * **الاستنفاد** (§٢أ؛ LC19 جزئيًّا — الأداةُ `yujadN` وحدها؛ وLC وأسطرُه من سجلّ المالك `CLOSURE_LEDGER_AR.md`، غيرِ المودَع — §٢أ):
    اختبارُ LC19 المضادّ (السجلّ س238 «قائمة مرشحين فارغة بسبب غياب معجم لا تفسر
    حكما لغويا بالامتناع») يجتازه `yujadN` بلا شهادة (`nitaqFarigh` ← «لا حكم»)، ويسقط على `yujad` (`istinfad_shawahid`: `yujad [] = N`)
    وعلى `phiAqd` (`phiAqd_farigh`)، ولا مستهلكَ لـ`yujadN` في المحرّك. والشهادةُ نسبيّةٌ إلى النوع `D` (`shahada_nisbiyya`: على نوعٍ فرعيٍّ
    من القائمة تصدق على أيّ قائمة، وعلى `Empty` على الفارغة)، فلا تعني تمامَ البدائل إلّا مع «نطاق ثابت وجرد مستقل» (LC18، السجلّ س225). ولم
    يُبنَ: `phi` و`tarkib` و`zanjir` على `Nitaq` (فهي على `yujad` المغلق كما كانت)، ولا مجالٌ مستقلٌّ لكلّ متغيّر (LC12)، ولا مولِّدُ
    شهاداتٍ لتعداد الأطر النحويّة (LC18)، ولا «فشل البحث أو نفاد الميزانية تعليق» (LC19، السجلّ س237؛ لا بحثَ ولا ميزانيّةَ هنا)، ولا مانعٌ مسمًّى
    لكلّ بديل (بقراءة البنّاء لـ«موانع لكل بديل» س237: `yujadN_N` تشترط امتناعَ كلّ بديل، و`K3` لا يحمل السبب — LC15). والعقدُ على المغلق: نطاقُه قائمةٌ غيرُ فارغة تحوي كلَّ مرشّح
    بفرضَي `hd` و`hne` في مبرهناته؛ و`phiAqd` على القائمة الفارغة ممتنعٌ من الخلوّ (`phiAqd_farigh`) — تمنعه الفروضُ لا التعريف.
  * ولا تشهد المبرهنات بصحّة قيدٍ لغويّ: تضمن أنّ الحكم هو حكمُ العوامل المعطاة بعينه.
  بلا sorry ولا axiom ولا native_decide.
-/
import Nizam.Aqd

namespace Nizam
namespace Phi

open Nizam.Aqd

/-! ## ١. الحكمُ الثلاثيّ وطبقتاه -/

/-- مرخَّص، ممتنع، لا حكم. -/
inductive K3 | P | N | U
  deriving DecidableEq, Repr

namespace K3

/-- الربط: يكفي ممتنعٌ ليمتنع، ولا ترخيصَ إلّا بترخيص الطرفين. -/
def wa : K3 → K3 → K3
  | N, _ => N
  | _, N => N
  | P, P => P
  | _, _ => U

/-- الفصل: يكفي مرخِّصٌ ليُرخَّص، ولا امتناعَ إلّا بامتناع الطرفين. -/
def aw : K3 → K3 → K3
  | P, _ => P
  | _, P => P
  | N, N => N
  | _, _ => U

/-- طبقتا البتّات: (قبول، ردّ). -/
def tabaqat : K3 → Bool × Bool
  | P => (true, false)
  | N => (false, true)
  | U => (false, false)

end K3

open K3

theorem tabaqat_wa (x y : K3) :
    (wa x y).tabaqat = ((x.tabaqat.1 && y.tabaqat.1), (x.tabaqat.2 || y.tabaqat.2)) := by
  cases x <;> cases y <;> rfl

theorem tabaqat_aw (x y : K3) :
    (aw x y).tabaqat = ((x.tabaqat.1 || y.tabaqat.1), (x.tabaqat.2 && y.tabaqat.2)) := by
  cases x <;> cases y <;> rfl

/-- لا تعارضَ بين الطبقتين، والتمثيلُ حقنيّ. -/
theorem tabaqat_la_taarud (x : K3) : (x.tabaqat.1 && x.tabaqat.2) = false ∧
    ∀ y : K3, x.tabaqat = y.tabaqat → x = y := by
  cases x <;> refine ⟨rfl, fun y h => ?_⟩ <;> cases y <;> first | rfl | cases h

theorem wa_P (x y : K3) : wa x y = P ↔ x = P ∧ y = P := by cases x <;> cases y <;> simp [wa]
theorem wa_N (x y : K3) : wa x y = N ↔ x = N ∨ y = N := by cases x <;> cases y <;> simp [wa]
theorem aw_P (x y : K3) : aw x y = P ↔ x = P ∨ y = P := by cases x <;> cases y <;> simp [aw]
theorem aw_N (x y : K3) : aw x y = N ↔ x = N ∧ y = N := by cases x <;> cases y <;> simp [aw]

/-! ## ٢. الإسقاطُ الوجوديّ -/

/-- يُوجد امتدادٌ مرخَّص؟ وإلّا فهل كلُّ امتدادٍ ممتنع؟ (النطاقُ الفارغ: لا امتدادَ فممتنع.) -/
def yujad : List K3 → K3
  | [] => N
  | x :: xs => aw x (yujad xs)

theorem yujad_P : ∀ l : List K3, yujad l = P ↔ ∃ x ∈ l, x = P
  | [] => by simp [yujad]
  | x :: xs => by
    simp only [yujad, aw_P, yujad_P xs, List.mem_cons, exists_eq_or_imp]

theorem yujad_N : ∀ l : List K3, yujad l = N ↔ ∀ x ∈ l, x = N
  | [] => by simp [yujad]
  | x :: xs => by
    simp only [yujad, aw_N, yujad_N xs, List.mem_cons, forall_eq_or_imp]

/-- الإسقاطُ على صورةِ نطاق: مرخَّصٌ ⟺ قيمةٌ في النطاق صورتُها مرخَّصة. -/
theorem yujad_map_P {β : Type} (f : β → K3) : ∀ l : List β, yujad (l.map f) = P ↔ ∃ b ∈ l, f b = P
  | [] => by simp [yujad]
  | b :: l => by
    simp only [List.map, yujad, aw_P, yujad_map_P f l, List.mem_cons, exists_eq_or_imp]

/-- والإسقاطُ على صورةِ نطاق ممتنعٌ ⟺ كلُّ قيمةٍ في النطاق صورتُها ممتنعة. -/
theorem yujad_map_N {β : Type} (f : β → K3) : ∀ l : List β, yujad (l.map f) = N ↔ ∀ b ∈ l, f b = N
  | [] => by simp [yujad]
  | b :: l => by
    simp only [List.map, yujad, aw_N, yujad_map_N f l, List.mem_cons, forall_eq_or_imp]

/-! ## ٢أ. النطاقُ المستوعَب: لا امتناعَ كلّيًّا بلا شهادة استنفاد (LC19 جزئيًّا)

قولُ المالك في الجلسة (2026-10-20، 13:01 بتوقيت عمّان)، جوابًا عن سؤال البنّاء من أين يبدأ بعد تحليل «سجل التزامات إغلاق الإخبار ثم
الإنشاء» (س1؛ مرفق المالك `CLOSURE_LEDGER_AR.md` على ca5ed3c، غيرُ مودَع؛ وأرقامُ LC وأسطرُه منه):
«انت خبير أوافق على قرارك ونفذ». وقرارُ البنّاء المعروضُ البدءُ بما سمّاه «النواة ١» وعنونه «لا امتناعَ من غياب» — التسميةُ والعنوانُ
من البنّاء لا من السجلّ؛ وتصميمُ ما هنا (`yujadMaftuh`، `Nitaq`، `yujadN`) قرارُ البنّاء.

و`yujad` أعلاه مغلقٌ: يجعل القائمةَ نطاقًا مستوعَبًا، فالفارغُ ممتنعٌ وامتناعُ كلّ ما فيها امتناعٌ كلّيّ. وذلك صحيحٌ إذا شُهد أنّ القائمة
تستوعب كلَّ قيمةٍ ممكنة، وإلّا كان غيابُ المرشَّح (معجمٌ لم يُودَع، بحثٌ لم يكتمل) امتناعًا — خلافَ م13، وخلافَ عنوان `Aql/Mawsua.lean`
س333 «والغياب ليس امتناعًا» و`Madlul/Shabaka.lean` س40 «لا إغلاقَ للعالم». فهنا: الإسقاطُ المفتوح `yujadMaftuh` لا يُخرج «ممتنع» أبدًا،
والنطاقُ `Nitaq` يحمل شهادةَ استنفادٍ اختياريّة، و`yujadN` مغلقٌ بها ومفتوحٌ بدونها (`yujadN_N`: لا امتناعَ كلّيًّا إلّا بالشهادة وامتناعِ
كلّ قيمةٍ من النوع `D`، لا من القائمة وحدها).

حدودٌ معلَنة:
* LC19 جزئيًّا يعني الأداةَ `yujadN` وحدها: اختبارُه المضادّ (س238 «قائمة مرشحين فارغة بسبب غياب معجم لا تفسر حكما لغويا بالامتناع»)
  يجتازه `yujadN` بلا شهادة (`istinfad_shawahid`: `nitaqFarigh` ← «لا حكم»)، ويسقط على `yujad` (`yujad [] = N` في الشاهد نفسِه) وعلى
  `phiAqd` (`phiAqd_farigh`).
* الشهادةُ نسبيّةٌ إلى `D` (`shahada_nisbiyya`): على النوع الفرعيّ من القائمة نفسِها تصدق على أيّ قائمة فيرجع `yujadN` إلى `yujad`
  المغلق بعينه، وعلى `Empty` تصدق على الفارغة فيمتنع. فلا تعني تمامَ البدائل إلّا مع «نطاق ثابت وجرد مستقل» ومولِّدٍ تامّ (LC18 س225)؛
  ولم يُبنَ، ولا المجالُ المستقلُّ لكلّ متغيّر (LC12 س148).
* `phi` و`tarkib` و`zanjir` والعقدُ (§٦) على `yujad` المغلق كما كانت، ولا مستهلكَ لـ`yujadN` في المحرّك بعد. والعقدُ: نطاقُه قائمةٌ غيرُ
  فارغة تحوي كلَّ مرشّح بفرضَي `hd` و`hne` في مبرهناته، وبالثاني منهما فممتنعُه من القانون والمانع وحدهما (`phiAqd_N`)، إذ عاملا الجذر
  والشاهد لا يُخرجان N (`amilJidhr_ghayr_N`، `amilShahid_ghayr_N`)؛ و`phiAqd` على القائمة الفارغة ممتنعٌ من الخلوّ (`phiAqd_farigh`) —
  تمنعه الفروضُ لا التعريف.
* ولم يُبنَ من LC19 (س237) أنّ «فشل البحث أو نفاد الميزانية تعليق» (لا بحثَ ولا ميزانيّةَ هنا)، ولا مانعٌ مسمًّى لكلّ بديل (بقراءة البنّاء
  لـ«موانع لكل بديل»): `yujadN_N` تشترط امتناعَ كلّ بديل، لكنّ `K3` لا يحمل سببَ الامتناع (`rutba` تُسقطه — LC15). وتبعيّتاه في السجلّ (س239) LC11 «فصل عدم التمثيل عن
  الامتناع اللغوي» (س136؛ في إطار الطبقة الثالثة `Jisr/Utur.lean`) وLC18. -/

/-- **الإسقاطُ المفتوح:** امتدادٌ مرخَّص ← مرخَّص؛ وإلّا «لا حكم» — ولو خلت القائمة أو امتنع كلُّ ما فيها. -/
def yujadMaftuh (l : List K3) : K3 := aw (yujad l) U

theorem yujadMaftuh_P (l : List K3) : yujadMaftuh l = P ↔ ∃ x ∈ l, x = P := by
  unfold yujadMaftuh
  rw [aw_P, yujad_P]
  constructor
  · rintro (h | h)
    · exact h
    · cases h
  · exact Or.inl

/-- **لا امتناعَ من الإسقاط المفتوح.** -/
theorem yujadMaftuh_ne_N (l : List K3) : yujadMaftuh l ≠ N := by
  unfold yujadMaftuh
  intro h
  rw [aw_N] at h
  cases h.2

/-- وما سوى الترخيص «لا حكم». -/
theorem yujadMaftuh_U (l : List K3) : yujadMaftuh l = U ↔ ∀ x ∈ l, x ≠ P := by
  constructor
  · intro h x hx hp
    have := (yujadMaftuh_P l).2 ⟨x, hx, hp⟩
    rw [h] at this
    cases this
  · intro h
    cases hk : yujadMaftuh l
    · obtain ⟨x, hx, hxp⟩ := (yujadMaftuh_P l).1 hk
      exact absurd hxp (h x hx)
    · exact absurd hk (yujadMaftuh_ne_N l)
    · rfl

/-- **النطاق:** قائمةُ قيم، وشهادةُ استنفادٍ اختياريّة — `mustanfad` يقتضي أنّ كلَّ قيمةٍ من النوع في القائمة. -/
structure Nitaq (D : Type) where
  qaima : List D
  mustanfad : Bool
  sahih : mustanfad = true → ∀ d : D, d ∈ qaima

/-- الإسقاطُ على نطاق: مغلقٌ بشهادة الاستنفاد، ومفتوحٌ بدونها. -/
def yujadN {D : Type} (n : Nitaq D) (F : D → K3) : K3 :=
  if n.mustanfad then yujad (n.qaima.map F) else yujadMaftuh (n.qaima.map F)

/-- الترخيصُ واحدٌ في المغلق والمفتوح: قيمةٌ في القائمة مرخَّصة. -/
theorem yujadN_P {D : Type} (n : Nitaq D) (F : D → K3) : yujadN n F = P ↔ ∃ d ∈ n.qaima, F d = P := by
  unfold yujadN
  cases n.mustanfad
  · simp only [Bool.false_eq_true, ite_false, yujadMaftuh_P, List.mem_map]
    constructor
    · rintro ⟨_, ⟨d, hd, rfl⟩, h⟩
      exact ⟨d, hd, h⟩
    · rintro ⟨d, hd, h⟩
      exact ⟨F d, ⟨d, hd, rfl⟩, h⟩
  · simp only [ite_true]
    exact yujad_map_P F n.qaima

/-- **لا امتناعَ كلّيًّا إلّا بشهادة الاستنفاد وامتناعِ كلّ قيمةٍ من النوع** — لا من القائمة وحدها. -/
theorem yujadN_N {D : Type} (n : Nitaq D) (F : D → K3) :
    yujadN n F = N ↔ n.mustanfad = true ∧ ∀ d : D, F d = N := by
  unfold yujadN
  cases hm : n.mustanfad
  · simp only [Bool.false_eq_true, ite_false, false_and, iff_false]
    exact yujadMaftuh_ne_N _
  · simp only [ite_true, true_and]
    rw [yujad_map_N F n.qaima]
    constructor
    · intro h d
      exact h d (n.sahih hm d)
    · intro h d _
      exact h d

/-- **ولا امتناعَ بلا شهادة.** -/
theorem la_N_bila_istinfad {D : Type} (n : Nitaq D) (F : D → K3) (h : n.mustanfad = false) : yujadN n F ≠ N := by
  intro hn
  have := ((yujadN_N n F).1 hn).1
  rw [h] at this
  cases this

/-- نطاقُ Bool مستوعَبٌ بقيمتيه؛ ونطاقٌ من Nat قائمةٌ بلا شهادة. -/
def nitaqBool : Nitaq Bool := ⟨[false, true], true, fun _ d => by cases d <;> simp⟩
def nitaqSifr : Nitaq Nat := ⟨[0], false, fun h => by cases h⟩
def nitaqFarigh : Nitaq Nat := ⟨[], false, fun h => by cases h⟩

/-- **حدٌّ معلَن:** نطاقُ النوع الفرعيّ من قائمةٍ ما مستوعَبٌ بها أيًّا كانت؛ ونطاقُ النوع الخالي مستوعَبٌ بالقائمة الفارغة. -/
def nitaqMinQaima {α : Type} (l : List α) : Nitaq {a // a ∈ l} := ⟨l.attach, true, fun _ d => List.mem_attach l d⟩
def nitaqKhali : Nitaq Empty := ⟨[], true, fun _ d => d.elim⟩

/-- **الشهادةُ نسبيّةٌ إلى النوع:** على النوع الفرعيّ من القائمة يرجع `yujadN` إلى `yujad` المغلق بعينه، وعلى `Empty` يمتنع — فلا تعني
الشهادةُ تمامَ البدائل إلّا مع «نطاق ثابت وجرد مستقل» ومولِّدٍ تامّ (LC18 س225). -/
theorem shahada_nisbiyya {α : Type} (l : List α) (F : α → K3) :
    yujadN (nitaqMinQaima l) (fun a => F a.val) = yujad (l.map F) ∧ ∀ G : Empty → K3, yujadN nitaqKhali G = N := by
  refine ⟨?_, fun _ => rfl⟩
  show yujad (l.attach.map fun a => F a.val) = yujad (l.map F)
  rw [List.attach_map_val]

/-- **على الشاهد:** القائمةُ الفارغة في المغلق ممتنعة وفي المفتوح «لا حكم»، وكذلك قائمةٌ كلُّ ما فيها ممتنع؛ والنطاقُ المستوعَب يمتنع
بامتناع قيمتيه كلتيهما، ولا يمتنع ما لم يُستوعَب ولو امتنع كلُّ ما في قائمته. -/
theorem istinfad_shawahid :
    yujad [] = N ∧ yujadMaftuh [] = U ∧ yujad [N, N] = N ∧ yujadMaftuh [N, N] = U ∧ yujadMaftuh [N, P] = P ∧
    yujadN nitaqBool (fun _ => N) = N ∧ yujadN nitaqBool (fun b => if b then P else N) = P ∧
    yujadN nitaqSifr (fun _ => N) = U ∧ yujadN nitaqFarigh (fun _ => N) = U := by decide

/-! ## ٣. التركيبُ على منفذٍ مشترك، والسلسلة -/

/-- عاملٌ بين قيمتي منفذين. -/
abbrev Aamil (α β : Type) := α → β → K3

/-- ربطُ عاملين على قيمة المنفذ المشترك ثمّ إسقاطُها على نطاقه. -/
def tarkib {α β γ : Type} (dom : List β) (R : Aamil α β) (S : Aamil β γ) : Aamil α γ :=
  fun a c => yujad (dom.map fun b => wa (R a b) (S b c))

theorem tarkib_P {α β γ : Type} (dom : List β) (R : Aamil α β) (S : Aamil β γ) (a : α) (c : γ) :
    tarkib dom R S a c = P ↔ ∃ b ∈ dom, R a b = P ∧ S b c = P := by
  simp only [tarkib, yujad_map_P, wa_P]

theorem tarkib_N {α β γ : Type} (dom : List β) (R : Aamil α β) (S : Aamil β γ) (a : α) (c : γ) :
    tarkib dom R S a c = N ↔ ∀ b ∈ dom, R a b = N ∨ S b c = N := by
  simp only [tarkib, yujad_map_N, wa_N]

/-- عاملُ الهويّة: المنفذُ يمرّ كما هو. -/
def huwiyya {σ : Type} [DecidableEq σ] : Aamil σ σ := fun a c => if a = c then P else N

/-- السلسلة: عواملُ متتابعةٌ على منفذٍ واحدِ النوع، تُركَّب من اليسار. -/
def zanjir {σ : Type} [DecidableEq σ] (dom : List σ) : List (Aamil σ σ) → Aamil σ σ
  | [] => huwiyya
  | R :: Rs => tarkib dom R (zanjir dom Rs)

/-- مسارٌ مرخَّص: قيمٌ للمنافذ من النطاق، وكلُّ عاملٍ على مساره مرخِّص. -/
inductive MasarP {σ : Type} (dom : List σ) : List (Aamil σ σ) → σ → σ → Prop
  | nil (a : σ) : MasarP dom [] a a
  | cons {R : Aamil σ σ} {Rs : List (Aamil σ σ)} {a b c : σ} :
      b ∈ dom → R a b = P → MasarP dom Rs b c → MasarP dom (R :: Rs) a c

/-- كلُّ مسارٍ ممتنع: في كلّ مسارٍ من النطاق عاملٌ يمنع. -/
def KullMardud {σ : Type} (dom : List σ) : List (Aamil σ σ) → σ → σ → Prop
  | [], a, c => a ≠ c
  | R :: Rs, a, c => ∀ b ∈ dom, R a b = N ∨ KullMardud dom Rs b c

/-- **السلسلةُ جامعةٌ مانعة للترخيص**: مرخَّصةٌ ⟺ مسارٌ كلُّ عوامله مرخِّصة. -/
theorem zanjir_P {σ : Type} [DecidableEq σ] (dom : List σ) :
    ∀ (Rs : List (Aamil σ σ)) (a c : σ), zanjir dom Rs a c = P ↔ MasarP dom Rs a c
  | [], a, c => by
    simp only [zanjir, huwiyya]
    constructor
    · intro h; split at h
      · rename_i e; subst e; exact .nil a
      · cases h
    · intro h; cases h; simp
  | R :: Rs, a, c => by
    simp only [zanjir]
    rw [tarkib_P]
    constructor
    · rintro ⟨b, hb, h1, h2⟩; exact .cons hb h1 ((zanjir_P dom Rs b c).mp h2)
    · intro h
      cases h with
      | cons hb h1 h2 => exact ⟨_, hb, h1, (zanjir_P dom Rs _ c).mpr h2⟩

/-- **والسلسلةُ جامعةٌ مانعة للامتناع**: ممتنعةٌ ⟺ كلُّ مسارٍ فيه عاملٌ يمنع. فما سواهما «لا حكم». -/
theorem zanjir_N {σ : Type} [DecidableEq σ] (dom : List σ) :
    ∀ (Rs : List (Aamil σ σ)) (a c : σ), zanjir dom Rs a c = N ↔ KullMardud dom Rs a c
  | [], a, c => by
    simp only [zanjir, huwiyya, KullMardud]
    split
    · rename_i e; simp [e]
    · rename_i e; simp [e]
  | R :: Rs, a, c => by
    simp only [zanjir, KullMardud]
    rw [tarkib_N]
    constructor
    · intro h b hb
      rcases h b hb with h | h
      · exact Or.inl h
      · exact Or.inr ((zanjir_N dom Rs b c).mp h)
    · intro h b hb
      rcases h b hb with h | h
      · exact Or.inl h
      · exact Or.inr ((zanjir_N dom Rs b c).mpr h)

/-- **وما سواهما «لا حكم»**: لا مسارَ مرخَّصًا، وفي مسارٍ ما لا عاملَ يمنع. -/
theorem zanjir_U {σ : Type} [DecidableEq σ] (dom : List σ) (Rs : List (Aamil σ σ)) (a c : σ) :
    zanjir dom Rs a c = U ↔ ¬ MasarP dom Rs a c ∧ ¬ KullMardud dom Rs a c := by
  rw [← zanjir_P, ← zanjir_N]
  generalize zanjir dom Rs a c = k
  cases k <;> simp

/-- قيمةٌ ليست مرخَّصةً ولا ممتنعة فهي «لا حكم». -/
theorem ghayruhuma_U {k : K3} (h1 : k ≠ P) (h2 : k ≠ N) : k = U := by
  cases k <;> simp_all

/-! ## ٤. Φ على الشجرة: الربطُ ثمّ الإسقاطُ الوجوديّ في كلّ عقدة (المرفق س38، ومبرهنتُه س43–47) -/

section Shajara

variable {V D : Type} [DecidableEq V]

theorem wa_tabadul (x y : K3) : wa x y = wa y x := by cases x <;> cases y <;> rfl

/-- الربطُ يتوزّع على الفصل (الحكمُ الثلاثيّ شبكةٌ توزيعيّة). -/
theorem wa_aw_tawzi (x y c : K3) : aw (wa x c) (wa y c) = wa (aw x y) c := by
  cases x <;> cases y <;> cases c <;> rfl

theorem yujad_map_wa {β : Type} (f : β → K3) (c : K3) :
    ∀ l : List β, yujad (l.map fun b => wa (f b) c) = wa (yujad (l.map f)) c
  | [] => by cases c <;> rfl
  | b :: l => by simp only [List.map, yujad, yujad_map_wa f c l, wa_aw_tawzi]

/-- تحديثُ التكليف في متغيّرٍ واحد. -/
def tahdith (σ : V → D) (v : V) (d : D) : V → D := fun w => if w = v then d else σ w

theorem tahdith_nafsuhu (σ : V → D) (v : V) (d : D) : tahdith σ v d v = d := by simp [tahdith]

theorem tahdith_ghayr (σ : V → D) {v w : V} (h : w ≠ v) (d : D) : tahdith σ v d w = σ w := by simp [tahdith, h]

theorem tahdith_nafs (σ : V → D) (v : V) (e d : D) : tahdith (tahdith σ v e) v d = tahdith σ v d := by
  funext w; by_cases h : w = v <;> simp [tahdith, h]

theorem tahdith_tabadul (σ : V → D) {v w : V} (h : w ≠ v) (d e : D) :
    tahdith (tahdith σ w e) v d = tahdith (tahdith σ v d) w e := by
  funext u; by_cases hu : u = v <;> by_cases hw : u = w <;> simp_all [tahdith]

/-- الإسقاطُ الوجوديّ على قائمة متغيّرات، بقيمٍ من النطاق. -/
def yujadV (dom : List D) : List V → ((V → D) → K3) → (V → D) → K3
  | [], F, σ => F σ
  | v :: vs, F, σ => yujad (dom.map fun d => yujadV dom vs F (tahdith σ v d))

/-- العاملُ لا يتعلّق بالمتغيّرات ws. -/
def LaYataallaq (F : (V → D) → K3) (ws : List V) : Prop :=
  ∀ σ w d, w ∈ ws → F (tahdith σ w d) = F σ

theorem yujadV_append (dom : List D) (ws : List V) (F : (V → D) → K3) :
    ∀ vs : List V, yujadV dom (vs ++ ws) F = yujadV dom vs (yujadV dom ws F)
  | [] => rfl
  | v :: vs => by
    funext σ
    simp only [List.cons_append, yujadV, yujadV_append dom ws F vs]

/-- ما لا يتعلّق به العاملُ لا يتعلّق به إسقاطُه. -/
theorem yujadV_la_yataallaq (dom : List D) (F : (V → D) → K3) (w : V)
    (hF : ∀ σ d, F (tahdith σ w d) = F σ) :
    ∀ (vs : List V) (σ : V → D) (e : D), yujadV dom vs F (tahdith σ w e) = yujadV dom vs F σ
  | [], σ, e => hF σ e
  | v :: vs, σ, e => by
    simp only [yujadV]
    congr 1
    apply List.map_congr_left
    intro d _
    by_cases h : w = v
    · subst h; rw [tahdith_nafs]
    · rw [tahdith_tabadul σ h d e]
      exact yujadV_la_yataallaq dom F w hF vs (tahdith σ v d) e

/-- الإسقاطُ يتوزّع على ربطٍ بعاملٍ لا يتعلّق بالمُسقَط. -/
theorem yujadV_wa (dom : List D) (F G : (V → D) → K3) :
    ∀ vs : List V, LaYataallaq G vs →
      ∀ σ, yujadV dom vs (fun τ => wa (F τ) (G τ)) σ = wa (yujadV dom vs F σ) (G σ)
  | [], _, _ => rfl
  | v :: vs, hG, σ => by
    have hG' : LaYataallaq G vs := fun τ w d h => hG τ w d (List.mem_cons_of_mem _ h)
    calc yujadV dom (v :: vs) (fun τ => wa (F τ) (G τ)) σ
        = yujad (dom.map fun d => wa (yujadV dom vs F (tahdith σ v d)) (G σ)) := by
          simp only [yujadV]
          congr 1
          apply List.map_congr_left
          intro d _
          rw [yujadV_wa dom F G vs hG' (tahdith σ v d), hG σ v d (by simp)]
      _ = wa (yujadV dom (v :: vs) F σ) (G σ) := yujad_map_wa _ _ _

/-- شجرةُ العوامل: ورقةٌ عاملٌ، وعقدةٌ تربط ولدين ثمّ تُسقط متغيّراتٍ مسمّاة (ما خرج عن واجهتها). -/
inductive Shajara (V D : Type) where
  | waraqa (F : (V → D) → K3)
  | aqda (l r : Shajara V D) (hadhf : List V)

/-- **Φ بالعَوْد** (المرفق س38): في كلّ عقدةٍ ربطُ الولدين ثمّ الإسقاطُ الوجوديّ لما خرج عن الواجهة. -/
def phi (dom : List D) : Shajara V D → (V → D) → K3
  | .waraqa F => F
  | .aqda l r hs => yujadV dom hs (fun σ => wa (phi dom l σ) (phi dom r σ))

/-- ربطُ العوامل كلّها على تكليفٍ واحد. -/
def kullAwamil : Shajara V D → (V → D) → K3
  | .waraqa F => F
  | .aqda l r _ => fun σ => wa (kullAwamil l σ) (kullAwamil r σ)

/-- أوراقُ الشجرة. -/
def awraq : Shajara V D → List ((V → D) → K3)
  | .waraqa F => [F]
  | .aqda l r _ => awraq l ++ awraq r

/-- المتغيّراتُ المُسقَطة في الشجرة كلّها. -/
def mahdhuf : Shajara V D → List V
  | .waraqa _ => []
  | .aqda l r hs => hs ++ (mahdhuf l ++ mahdhuf r)

/-- **شرطُ الواجهة** (بقراءة البنّاء لقول المرفق س55 «كل متغير مشترك داخل V_l وV_r محفوظ في Sep»): ما يُسقَط داخل
    ولدٍ لا يتعلّق به ربطُ عوامل الآخر (`kullAwamil`). ويكفي له أن لا يتعلّق به عاملٌ منها (`awraq_la_yataallaq`). -/
def Wajiha : Shajara V D → Prop
  | .waraqa _ => True
  | .aqda l r _ => Wajiha l ∧ Wajiha r ∧ LaYataallaq (kullAwamil r) (mahdhuf l) ∧ LaYataallaq (kullAwamil l) (mahdhuf r)

/-- ما لا يتعلّق به كلُّ عاملٍ لا يتعلّق به ربطُها. -/
theorem awraq_la_yataallaq (ws : List V) : ∀ t : Shajara V D,
    (∀ F ∈ awraq t, LaYataallaq F ws) → LaYataallaq (kullAwamil t) ws
  | .waraqa F, h => h F (by simp [awraq])
  | .aqda l r _, h => by
    have hl := awraq_la_yataallaq ws l fun F hF => h F (by simp [awraq, hF])
    have hr := awraq_la_yataallaq ws r fun F hF => h F (by simp [awraq, hF])
    intro σ w d hw
    simp only [kullAwamil, hl σ w d hw, hr σ w d hw]

/-- **Φ بالعَوْد = إسقاطٌ واحدٌ لربط العوامل كلّها** على كلّ ما أُسقط في الشجرة، بشرط الواجهة. -/
theorem phi_awd (dom : List D) : ∀ (t : Shajara V D), Wajiha t →
    ∀ σ, phi dom t σ = yujadV dom (mahdhuf t) (kullAwamil t) σ
  | .waraqa _, _, _ => rfl
  | .aqda l r hs, ⟨hl, hr, hrl, hlr⟩, σ => by
    have el : phi dom l = yujadV dom (mahdhuf l) (kullAwamil l) := funext (phi_awd dom l hl)
    have er : phi dom r = yujadV dom (mahdhuf r) (kullAwamil r) := funext (phi_awd dom r hr)
    have inner : (fun ρ => wa (kullAwamil l ρ) (yujadV dom (mahdhuf r) (kullAwamil r) ρ)) =
        yujadV dom (mahdhuf r) (fun ρ => wa (kullAwamil l ρ) (kullAwamil r ρ)) := by
      funext ρ
      have e : (fun τ => wa (kullAwamil l τ) (kullAwamil r τ)) = (fun τ => wa (kullAwamil r τ) (kullAwamil l τ)) :=
        funext fun τ => wa_tabadul _ _
      rw [e, yujadV_wa dom (kullAwamil r) (kullAwamil l) (mahdhuf r) hlr ρ, wa_tabadul]
    have hG : LaYataallaq (yujadV dom (mahdhuf r) (kullAwamil r)) (mahdhuf l) :=
      fun τ w d hw => yujadV_la_yataallaq dom (kullAwamil r) w (fun ρ e => hrl ρ w e hw) (mahdhuf r) τ d
    have key : (fun τ => wa (yujadV dom (mahdhuf l) (kullAwamil l) τ) (yujadV dom (mahdhuf r) (kullAwamil r) τ)) =
        yujadV dom (mahdhuf l) (yujadV dom (mahdhuf r) (fun ρ => wa (kullAwamil l ρ) (kullAwamil r ρ))) := by
      funext τ
      rw [← yujadV_wa dom (kullAwamil l) (yujadV dom (mahdhuf r) (kullAwamil r)) (mahdhuf l) hG τ, inner]
    simp only [phi, mahdhuf, kullAwamil, el, er, yujadV_append]
    rw [key]

/-- مدُّ التكليف على المُسقَطات: يطابق σ خارجها، وقيمُه فيها من النطاق. -/
def Imtidad (dom : List D) (vs : List V) (σ τ : V → D) : Prop :=
  (∀ w, w ∉ vs → τ w = σ w) ∧ ∀ v ∈ vs, τ v ∈ dom

theorem imtidad_cons (dom : List D) (v : V) (vs : List V) (σ τ : V → D) :
    Imtidad dom (v :: vs) σ τ ↔ ∃ d ∈ dom, Imtidad dom vs (tahdith σ v d) τ := by
  constructor
  · rintro ⟨h1, h2⟩
    refine ⟨τ v, h2 v (List.mem_cons_self ..), fun w hw => ?_, fun u hu => h2 u (List.mem_cons_of_mem _ hu)⟩
    by_cases hv : w = v
    · subst hv; rw [tahdith_nafsuhu]
    · rw [tahdith_ghayr σ hv]
      exact h1 w (by simp [hv, hw])
  · rintro ⟨d, hd, h1, h2⟩
    refine ⟨fun w hw => ?_, fun u hu => ?_⟩
    · have hv : w ≠ v := fun e => hw (by simp [e])
      have hw' : w ∉ vs := fun e => hw (List.mem_cons_of_mem _ e)
      rw [h1 w hw', tahdith_ghayr σ hv]
    · rcases List.mem_cons.mp hu with rfl | hu
      · by_cases hin : u ∈ vs
        · exact h2 u hin
        · rw [h1 u hin, tahdith_nafsuhu]; exact hd
      · exact h2 u hu

theorem yujadV_P (dom : List D) (F : (V → D) → K3) :
    ∀ (vs : List V) (σ : V → D), yujadV dom vs F σ = P ↔ ∃ τ, Imtidad dom vs σ τ ∧ F τ = P
  | [], σ => by
    simp only [yujadV]
    constructor
    · intro h; exact ⟨σ, ⟨fun _ _ => rfl, fun _ h => by simp at h⟩, h⟩
    · rintro ⟨τ, ⟨h1, _⟩, h⟩
      have : τ = σ := funext fun w => h1 w (by simp)
      subst this; exact h
  | v :: vs, σ => by
    simp only [yujadV, yujad_map_P, yujadV_P dom F vs, imtidad_cons]
    constructor
    · rintro ⟨d, hd, τ, hτ, h⟩; exact ⟨τ, ⟨d, hd, hτ⟩, h⟩
    · rintro ⟨τ, ⟨d, hd, hτ⟩, h⟩; exact ⟨d, hd, τ, hτ, h⟩

theorem yujadV_N (dom : List D) (F : (V → D) → K3) :
    ∀ (vs : List V) (σ : V → D), yujadV dom vs F σ = N ↔ ∀ τ, Imtidad dom vs σ τ → F τ = N
  | [], σ => by
    simp only [yujadV]
    constructor
    · rintro h τ ⟨h1, _⟩
      have : τ = σ := funext fun w => h1 w (by simp)
      subst this; exact h
    · intro h; exact h σ ⟨fun _ _ => rfl, fun _ h => by simp at h⟩
  | v :: vs, σ => by
    simp only [yujadV, yujad_map_N, yujadV_N dom F vs, imtidad_cons]
    constructor
    · rintro h τ ⟨d, hd, hτ⟩; exact h d hd τ hτ
    · intro h d hd τ hτ; exact h τ ⟨d, hd, hτ⟩

omit [DecidableEq V] in
theorem kullAwamil_P : ∀ (t : Shajara V D) (τ : V → D), kullAwamil t τ = P ↔ ∀ F ∈ awraq t, F τ = P
  | .waraqa F, τ => by simp [kullAwamil, awraq]
  | .aqda l r _, τ => by
    simp only [kullAwamil, awraq, wa_P, kullAwamil_P l τ, kullAwamil_P r τ, List.mem_append]
    constructor
    · rintro ⟨h1, h2⟩ F (hF | hF)
      · exact h1 F hF
      · exact h2 F hF
    · intro h; exact ⟨fun F hF => h F (Or.inl hF), fun F hF => h F (Or.inr hF)⟩

omit [DecidableEq V] in
theorem kullAwamil_N : ∀ (t : Shajara V D) (τ : V → D), kullAwamil t τ = N ↔ ∃ F ∈ awraq t, F τ = N
  | .waraqa F, τ => by simp [kullAwamil, awraq]
  | .aqda l r _, τ => by
    simp only [kullAwamil, awraq, wa_N, kullAwamil_N l τ, kullAwamil_N r τ, List.mem_append]
    constructor
    · rintro (⟨F, hF, h⟩ | ⟨F, hF, h⟩)
      · exact ⟨F, Or.inl hF, h⟩
      · exact ⟨F, Or.inr hF, h⟩
    · rintro ⟨F, hF | hF, h⟩
      · exact Or.inl ⟨F, hF, h⟩
      · exact Or.inr ⟨F, hF, h⟩

/-- **Φ جامعةٌ مانعة للترخيص** (المرفق س43–47 في الحكم الثلاثيّ): بشرط الواجهة، مرخِّصةٌ ⟺ يوجد مدٌّ للمُسقَطات من النطاق
    يُرخِّص فيه كلُّ عامل. -/
theorem shajara_P (dom : List D) (t : Shajara V D) (hw : Wajiha t) (σ : V → D) :
    phi dom t σ = P ↔ ∃ τ, Imtidad dom (mahdhuf t) σ τ ∧ ∀ F ∈ awraq t, F τ = P := by
  rw [phi_awd dom t hw σ, yujadV_P]
  simp only [kullAwamil_P]

/-- **وجامعةٌ مانعة للامتناع**: ممتنعةٌ ⟺ في كلّ مدٍّ للمُسقَطات عاملٌ يمنع. -/
theorem shajara_N (dom : List D) (t : Shajara V D) (hw : Wajiha t) (σ : V → D) :
    phi dom t σ = N ↔ ∀ τ, Imtidad dom (mahdhuf t) σ τ → ∃ F ∈ awraq t, F τ = N := by
  rw [phi_awd dom t hw σ, yujadV_N]
  simp only [kullAwamil_N]

/-- **وما سواهما «لا حكم»**: لا مدَّ يرخِّص فيه الكلّ، ولا يمتنع كلُّ مدّ. -/
theorem shajara_U (dom : List D) (t : Shajara V D) (hw : Wajiha t) (σ : V → D) :
    phi dom t σ = U ↔ ¬ (∃ τ, Imtidad dom (mahdhuf t) σ τ ∧ ∀ F ∈ awraq t, F τ = P) ∧
      ¬ (∀ τ, Imtidad dom (mahdhuf t) σ τ → ∃ F ∈ awraq t, F τ = N) := by
  rw [← shajara_P dom t hw σ, ← shajara_N dom t hw σ]
  generalize phi dom t σ = k
  cases k <;> simp

end Shajara

/-! ## ٥. ضرورةُ الواجهة: المثالان المضادّان في المرفق (س64–65)، على الشاهد -/

/-- التكاليفُ الثمانية لثلاثة متغيّراتٍ ثنائيّة. -/
def thulathiyyat : List (Bool × Bool × Bool) :=
  [false, true].flatMap fun a => [false, true].flatMap fun b => [false, true].map fun c => (a, b, c)

/-- القانونُ الثلاثيّ: a ⊕ b ⊕ c = 0. -/
def xor3 (t : Bool × Bool × Bool) : Bool := !(t.1 ^^ t.2.1 ^^ t.2.2)

/-- **المثالُ الأوّل** (س64): حلولُ a⊕b⊕c=0 أربعةٌ بأعيانها، وربطُ إسقاطاته الزوجيّة يقبل الثمانية — فعلى هذا الشاهد يزيد إسقاطُ
    متغيّرٍ مشتركٍ قبل الربط أربعةَ حلولٍ زائفة. (على قوائم `Bool`، لا على `phi`.) -/
theorem wajiha_daruriyya :
    thulathiyyat.filter xor3 = [(false, false, false), (false, true, true), (true, false, true), (true, true, false)] ∧
    (thulathiyyat.filter fun t =>
        (thulathiyyat.any fun u => xor3 u && u.1 == t.1 && u.2.1 == t.2.1) &&
        (thulathiyyat.any fun u => xor3 u && u.2.1 == t.2.1 && u.2.2 == t.2.2) &&
        (thulathiyyat.any fun u => xor3 u && u.1 == t.1 && u.2.2 == t.2.2)).length = 8 := by decide

/-- عاملٌ يتطلّب key=0 (المتغيّر 0). -/
def miftah0 : (Nat → Nat) → K3 := fun σ => if σ 0 = 0 then P else N
/-- وعاملٌ يتطلّب key=1. -/
def miftah1 : (Nat → Nat) → K3 := fun σ => if σ 0 = 1 then P else N
/-- عاملٌ يرخِّص كلَّ تكليف. -/
def tarkhisKull : (Nat → Nat) → K3 := fun _ => P

/-- الصحيح: key محفوظٌ في الواجهة حتّى الربط، ثمّ يُسقَط. -/
def shajaraSahiha : Shajara Nat Nat := .aqda (.waraqa miftah0) (.waraqa miftah1) [0]
/-- الخاطئ: key يُسقَط من كلّ ولدٍ قبل الربط. -/
def shajaraKhatia : Shajara Nat Nat :=
  .aqda (.aqda (.waraqa miftah0) (.waraqa tarkhisKull) [0]) (.aqda (.waraqa miftah1) (.waraqa tarkhisKull) [0]) []

/-- **المثالُ الثاني** (س65) على `phi` نفسِها: الشجرةُ الصحيحة تستوفي شرطَ الواجهة (فتقع تحت `shajara_N`) وهي ممتنعة (لا حلّ)،
    والخاطئةُ مرخِّصةٌ زورًا وتخالف الشرط. -/
theorem mithal_miftah :
    Wajiha shajaraSahiha ∧ phi [0, 1] shajaraSahiha (fun _ => 0) = N ∧ phi [0, 1] shajaraKhatia (fun _ => 0) = P ∧
    ¬ Wajiha shajaraKhatia := by
  refine ⟨by simp [Wajiha, shajaraSahiha, mahdhuf, LaYataallaq], by decide, by decide, ?_⟩
  intro h
  obtain ⟨-, -, h3, -⟩ := h
  have := h3 (fun _ => 0) 0 1 (by simp [mahdhuf])
  exact absurd this (by decide)

/-! ## ٦. العقدُ حالةٌ من Φ: مراتبُ `kull_ma_kull` الثلاث تُستخرج من `tarkib_P`/`tarkib_N` -/

/-- مرتبةُ الحكم: المرخَّصُ P، والممتنعُ N، و«لا حكم» U — تُسقط القراءةَ واسمَ السبب. -/
def rutba {α : Type} : Hukm α → K3
  | .murakhkhas _ => P
  | .mumtani _ => N
  | .laHukm => U

theorem rutba_P {α : Type} (h : Hukm α) : rutba h = P ↔ ∃ q, h = .murakhkhas q := by cases h <;> simp [rutba]
theorem rutba_N {α : Type} (h : Hukm α) : rutba h = N ↔ ∃ s, h = .mumtani s := by cases h <;> simp [rutba]
theorem rutba_U {α : Type} (h : Hukm α) : rutba h = U ↔ h = .laHukm := by cases h <;> simp [rutba]

instance (A : Aqd) (x : List Nat) (r m : Nat) : Decidable (Mashhud A x r m) := by
  unfold Mashhud; infer_instance

/-- عاملُ القانون (المواصفة): مرخِّصٌ أو ممتنع. -/
def amilQanun (A : Aqd) (x : List Nat) : K3 := if A.qanun x then P else N
/-- عاملُ المانع: يمنع المدلولَ إن رُفع بتُّه، وإلّا رخّص (حقلُ بيانات، واحدٌ في الطرفين). -/
def amilMani (A : Aqd) (x : List Nat) (m : Nat) : K3 := if (A.mani x).testBit m then N else P
/-- عاملُ الجذر (المواصفة): المرشَّحُ مرخِّص، وغيرُه «لا حكم» لا ممتنع. -/
def amilJidhr (A : Aqd) (x : List Nat) (r : Nat) : K3 := if A.jidhr x = some r then P else U
/-- عاملُ الشاهد (المواصفة `Mashhud`): المشهودُ مرخِّص، وغيرُه «لا حكم» — الغيابُ ليس امتناعًا. -/
def amilShahid (A : Aqd) (x : List Nat) (r m : Nat) : K3 := if Mashhud A x r m then P else U

/-- عاملُ القانون (المنفّذ `qanunB`). -/
def amilQanunB (A : Aqd) (x : List Nat) : K3 := if A.qanunB x then P else N
/-- عاملُ الجذر (المنفّذ `jidhrB`). -/
def amilJidhrB (A : Aqd) (x : List Nat) (r : Nat) : K3 := if A.jidhrB x = some r then P else U
/-- عاملُ الشاهد (المنفّذ: بتُّ `mustawa`). -/
def amilShahidB (A : Aqd) (x : List Nat) (r m : Nat) : K3 := if (mustawa A x r).testBit m then P else U

theorem amilQanun_P (A : Aqd) (x : List Nat) : amilQanun A x = P ↔ A.qanun x = true := by
  cases h : A.qanun x <;> simp [amilQanun, h]
theorem amilQanun_N (A : Aqd) (x : List Nat) : amilQanun A x = N ↔ A.qanun x = false := by
  cases h : A.qanun x <;> simp [amilQanun, h]
theorem amilMani_P (A : Aqd) (x : List Nat) (m : Nat) : amilMani A x m = P ↔ (A.mani x).testBit m = false := by
  cases h : (A.mani x).testBit m <;> simp [amilMani, h]
theorem amilMani_N (A : Aqd) (x : List Nat) (m : Nat) : amilMani A x m = N ↔ (A.mani x).testBit m = true := by
  cases h : (A.mani x).testBit m <;> simp [amilMani, h]
theorem amilJidhr_P (A : Aqd) (x : List Nat) (r : Nat) : amilJidhr A x r = P ↔ A.jidhr x = some r := by
  by_cases h : A.jidhr x = some r <;> simp [amilJidhr, h]
/-- الجذرُ غيرُ المرشَّح لا يمنع. -/
theorem amilJidhr_ghayr_N (A : Aqd) (x : List Nat) (r : Nat) : amilJidhr A x r ≠ N := by
  by_cases h : A.jidhr x = some r <;> simp [amilJidhr, h]
theorem amilShahid_P (A : Aqd) (x : List Nat) (r m : Nat) : amilShahid A x r m = P ↔ Mashhud A x r m := by
  by_cases h : Mashhud A x r m <;> simp [amilShahid, h]
/-- غيابُ الشاهد لا يمنع. -/
theorem amilShahid_ghayr_N (A : Aqd) (x : List Nat) (r m : Nat) : amilShahid A x r m ≠ N := by
  by_cases h : Mashhud A x r m <;> simp [amilShahid, h]

/-- **عواملُ المنفّذ تساوي عواملَ المواصفة** بحقول العقد (`qanun_sawa`، `jidhr_sawa`) و`mustawa_iff`. -/
theorem amil_sawa (A : Aqd) (x : List Nat) (r m : Nat) :
    amilQanunB A x = amilQanun A x ∧ amilJidhrB A x r = amilJidhr A x r ∧ amilShahidB A x r m = amilShahid A x r m := by
  refine ⟨by simp only [amilQanunB, amilQanun, A.qanun_sawa x], by simp only [amilJidhrB, amilJidhr, A.jidhr_sawa x], ?_⟩
  unfold amilShahidB amilShahid
  by_cases h : Mashhud A x r m
  · have h' := (mustawa_iff A x r m).mpr h
    simp [h, h']
  · have h' : ¬ (mustawa A x r).testBit m = true := fun e => h ((mustawa_iff A x r m).mp e)
    simp [h, h']

/-- **Φ على العقد** (المواصفة): القانونُ والمانعُ مربوطان بتركيبِ عاملِ الجذر وعاملِ الشاهد على منفذ الجذر (`tarkib` بعينه). -/
def phiAqd (A : Aqd) (x : List Nat) (m : Nat) (judhur : List Nat) : K3 :=
  wa (amilQanun A x) (wa (amilMani A x m)
    (tarkib judhur (fun (_ : Unit) r => amilJidhr A x r) (fun r (_ : Unit) => amilShahid A x r m) () ()))

/-- وΦ على عوامل المنفّذ. -/
def phiAqdB (A : Aqd) (x : List Nat) (m : Nat) (judhur : List Nat) : K3 :=
  wa (amilQanunB A x) (wa (amilMani A x m)
    (tarkib judhur (fun (_ : Unit) r => amilJidhrB A x r) (fun r (_ : Unit) => amilShahidB A x r m) () ()))

theorem phiAqdB_sawa (A : Aqd) (x : List Nat) (m : Nat) (judhur : List Nat) :
    phiAqdB A x m judhur = phiAqd A x m judhur := by
  have e2 : ∀ r, amilJidhrB A x r = amilJidhr A x r := fun r => (amil_sawa A x r m).2.1
  have e3 : ∀ r, amilShahidB A x r m = amilShahid A x r m := fun r => (amil_sawa A x r m).2.2
  simp only [phiAqdB, phiAqd, (amil_sawa A x 0 m).1, e2, e3]

/-- **شجرةُ العقد**: أربعُ أوراقٍ على متغيّرٍ واحد هو منفذُ الجذر (`()`)، يُسقَط في عقدة الجذر والشاهد. -/
def shajaraAqd (A : Aqd) (x : List Nat) (m : Nat) : Shajara Unit Nat :=
  .aqda (.waraqa fun _ => amilQanun A x)
    (.aqda (.waraqa fun _ => amilMani A x m)
      (.aqda (.waraqa fun σ => amilJidhr A x (σ ())) (.waraqa fun σ => amilShahid A x (σ ()) m) [()]) []) []

/-- **`phiAqd` (المواصفة) هي Φ على شجرة العقد** (لكلّ نطاقٍ وتكليف)، وشجرتُه تستوفي شرطَ الواجهة، فتقع عليها
    `shajara_P`/`shajara_N`/`shajara_U`. والمنفّذُ يصلها بـ`aqd_phi` (`hukmB_shajara_mashru` على `Mashru`). -/
theorem phiAqd_shajara (A : Aqd) (x : List Nat) (m : Nat) (judhur : List Nat) (σ : Unit → Nat) :
    Wajiha (shajaraAqd A x m) ∧ phi judhur (shajaraAqd A x m) σ = phiAqd A x m judhur := by
  refine ⟨by simp [Wajiha, shajaraAqd, mahdhuf, LaYataallaq, kullAwamil], ?_⟩
  simp [phi, shajaraAqd, yujadV, phiAqd, tarkib, tahdith]

/-- **المنفّذُ يحسب Φ**: مرتبةُ `hukmB` هي Φ على عوامل المنفّذ، لكلّ عقدٍ ولكلّ نطاقٍ غيرِ فارغ يحوي مرشَّحَ المنفّذ —
    من تعريف `hukmB` و`tarkib_P`/`tarkib_N`، بلا `kull_ma_kull`. -/
theorem hukmB_phiB (A : Aqd) (x : List Nat) (m : Nat) (judhur : List Nat)
    (hd : ∀ r, A.jidhrB x = some r → r ∈ judhur) (hne : judhur ≠ []) :
    rutba (hukmB A x m) = phiAqdB A x m judhur := by
  have hTN : tarkib judhur (fun (_ : Unit) r => amilJidhrB A x r) (fun r (_ : Unit) => amilShahidB A x r m) () () ≠ N := by
    rw [Ne, tarkib_N]
    intro h
    cases judhur with
    | nil => exact hne rfl
    | cons r _ =>
      rcases h r (List.mem_cons_self ..) with h1 | h1
      · by_cases hj : A.jidhrB x = some r <;> simp [amilJidhrB, hj] at h1
      · by_cases hs : (mustawa A x r).testBit m = true <;> simp [amilShahidB, hs] at h1
  have wPP : ∀ k, wa P (wa P k) = k := by intro k; cases k <;> rfl
  unfold hukmB phiAqdB
  by_cases hq : A.qanunB x = false
  · rw [ite_eq_left hq]; simp [rutba, amilQanunB, hq, wa]
  · rw [ite_eq_right hq]
    have eQ : amilQanunB A x = P := by simp_all [amilQanunB]
    by_cases hn : (A.mani x).testBit m = true
    · rw [ite_eq_left hn, eQ]; simp [rutba, amilMani, hn, wa]
    · rw [ite_eq_right hn]
      have eM : amilMani A x m = P := by simp_all [amilMani]
      rw [eQ, eM, wPP]
      cases hj : A.jidhrB x with
      | none =>
        refine (ghayruhuma_U ?_ hTN).symm
        rw [Ne, tarkib_P]
        rintro ⟨b, _, h1, _⟩
        simp [amilJidhrB, hj] at h1
      | some r =>
        by_cases hs : (mustawa A x r).testBit m = true
        · dsimp only; rw [ite_eq_left hs]; simp only [rutba]
          symm
          rw [tarkib_P]
          exact ⟨r, hd r hj, by simp [amilJidhrB, hj], by simp [amilShahidB, hs]⟩
        · dsimp only; rw [ite_eq_right hs]; simp only [rutba]
          refine (ghayruhuma_U ?_ hTN).symm
          rw [Ne, tarkib_P]
          rintro ⟨b, _, h1, h2⟩
          have hb : r = b := by simpa [amilJidhrB, hj] using h1
          subst hb
          simp [amilShahidB, hs] at h2

/-- **العقدُ حالةٌ من Φ** (المواصفة): لكلّ عقد، مرتبةُ `hukmB` هي Φ على عوامل المواصفة، بنطاقٍ غيرِ فارغ يحوي كلَّ مرشَّح. -/
theorem aqd_phi (A : Aqd) (x : List Nat) (m : Nat) (judhur : List Nat)
    (hd : ∀ r, A.jidhr x = some r → r ∈ judhur) (hne : judhur ≠ []) :
    rutba (hukmB A x m) = phiAqd A x m judhur := by
  rw [hukmB_phiB A x m judhur (fun r h => hd r (by rw [← A.jidhr_sawa x]; exact h)) hne, phiAqdB_sawa]

theorem phiAqd_P (A : Aqd) (x : List Nat) (m : Nat) (judhur : List Nat)
    (hd : ∀ r, A.jidhr x = some r → r ∈ judhur) :
    phiAqd A x m judhur = P ↔ Murakhkhas A x m := by
  simp only [phiAqd, wa_P, tarkib_P, amilQanun_P, amilMani_P, amilJidhr_P, amilShahid_P, Murakhkhas]
  constructor
  · rintro ⟨hq, hn, r, _, hj, hs⟩; exact ⟨hq, hn, r, hj, hs⟩
  · rintro ⟨hq, hn, r, hj, hs⟩; exact ⟨hq, hn, r, hd r hj, hj, hs⟩

theorem phiAqd_N (A : Aqd) (x : List Nat) (m : Nat) (judhur : List Nat) (hne : judhur ≠ []) :
    phiAqd A x m judhur = N ↔ Mumtani A x m := by
  simp only [phiAqd, Mumtani, wa_N, tarkib_N, amilQanun_N, amilMani_N]
  have hy : ¬ ∀ r ∈ judhur, amilJidhr A x r = N ∨ amilShahid A x r m = N := by
    intro h
    cases judhur with
    | nil => exact hne rfl
    | cons r _ =>
      rcases h r (List.mem_cons_self ..) with h1 | h1
      · exact amilJidhr_ghayr_N A x r h1
      · exact amilShahid_ghayr_N A x r m h1
  constructor
  · rintro (h | h | h)
    · exact Or.inl h
    · exact Or.inr h
    · exact absurd h hy
  · rintro (h | h)
    · exact Or.inl h
    · exact Or.inr (Or.inl h)

/-- **حدٌّ معلَن (§٢أ):** `phiAqd` على نطاق جذورٍ فارغ ممتنعٌ من الخلوّ لا من القانون ولا المانع — فلا يمنعه إلّا فرضُ `hne` في
    مبرهنات العقد، و`hd` حين يوجد مرشّح، لا التعريف. وعليه يسقط اختبارُ LC19 المضادّ (س238). -/
theorem phiAqd_farigh (A : Aqd) (x : List Nat) (m : Nat) : phiAqd A x m [] = N := by
  unfold phiAqd tarkib
  cases amilQanun A x <;> cases amilMani A x m <;> rfl

/-- **مراتبُ `kull_ma_kull` الثلاث مشتقّةٌ من Φ** (لا من `kull_ma_kull`): لكلّ عقدٍ ودالٍّ ومدلول، ونطاقُ الجذور مرشَّحُ الدالّ
    (أو 0). ولا يشمل شطرَه الرابع (القراءة `QiraaSahiha`) ولا اسمَ السبب (`mumtani_asbab`): `rutba` تُسقطهما. -/
theorem kull_ma_kull_min_phi (A : Aqd) (x : List Nat) (m : Nat) :
    ((∃ q, hukmB A x m = .murakhkhas q) ↔ Murakhkhas A x m) ∧
    ((∃ s, hukmB A x m = .mumtani s) ↔ Mumtani A x m) ∧
    (hukmB A x m = .laHukm ↔ ¬ Murakhkhas A x m ∧ ¬ Mumtani A x m) := by
  have hd : ∀ r, A.jidhr x = some r → r ∈ [(A.jidhr x).getD 0] := fun r h => by simp [h]
  have E := aqd_phi A x m [(A.jidhr x).getD 0] hd (by simp)
  have hP := phiAqd_P A x m _ hd
  have hN := phiAqd_N A x m [(A.jidhr x).getD 0] (by simp)
  refine ⟨(rutba_P _).symm.trans (by rw [E]; exact hP), (rutba_N _).symm.trans (by rw [E]; exact hN), ?_⟩
  rw [← rutba_U, E, ← hP, ← hN]
  generalize phiAqd A x m [(A.jidhr x).getD 0] = k
  cases k <;> simp

/-- **نطاقُ جذور Mashru**: كلُّ مرشَّحٍ دون 32768 (حقولُ خمسة بتّاتٍ ثلاثة). -/
theorem jidhr_hadd (n : JadwalLuzum.Naw) (x : List Nat) (r : Nat) (h : (Mashru n).jidhr x = some r) : r < 32768 := by
  obtain ⟨hs, hr⟩ := jidhr_salim n x r h
  have hl : x.length = 3 := by
    simp only [Mashru] at h
    split at h
    · rename_i hc; exact hc.1
    · cases h
  match x, hl with
  | [a, b, c], _ =>
    subst hr
    have ha := (hs (Jisr.JisrDal.harf a) (by simp)).1
    have hb := (hs (Jisr.JisrDal.harf b) (by simp)).1
    have hc := (hs (Jisr.JisrDal.harf c) (by simp)).1
    simp only [List.map, ramz32, List.foldl]
    omega

/-- **عقدُ Mashru حالةٌ من Φ** بنطاق الجذور 32768. -/
theorem aqd_phi_mashru (n : JadwalLuzum.Naw) (x : List Nat) (m : Nat) :
    rutba (hukmB (Mashru n) x m) = phiAqd (Mashru n) x m (List.range 32768) :=
  aqd_phi (Mashru n) x m (List.range 32768)
    (fun r h => List.mem_range.mpr (jidhr_hadd n x r h)) (by simp)

/-- **حكمُ المحرّك على `Mashru` هو Φ على شجرة العقد** بنطاق الجذور 32768، لكلّ تكليف: `aqd_phi_mashru` ثمّ `phiAqd_shajara`. -/
theorem hukmB_shajara_mashru (n : JadwalLuzum.Naw) (x : List Nat) (m : Nat) (σ : Unit → Nat) :
    rutba (hukmB (Mashru n) x m) = phi (List.range 32768) (shajaraAqd (Mashru n) x m) σ := by
  rw [(phiAqd_shajara (Mashru n) x m (List.range 32768) σ).2, aqd_phi_mashru]

/-- **شاهدان** (نقلٌ عبر `aqd_phi_mashru` من `kataba_ilm_taraduf` و`kataba_luzum_la_hukm`): كَتَبَ ← «علم» ترادفًا مرخَّصٌ في Φ،
    ولزومًا «لا حكم» — الغيابُ ليس امتناعًا. -/
theorem kataba_phi :
    phiAqd (Mashru .taraduf) kataba (ramzNass "علم") (List.range 32768) = P ∧
    phiAqd (Mashru .luzum) kataba (ramzNass "علم") (List.range 32768) = U := by
  obtain ⟨q, hq, _⟩ := kataba_ilm_taraduf
  refine ⟨?_, ?_⟩
  · rw [← aqd_phi_mashru, hq]; rfl
  · rw [← aqd_phi_mashru, kataba_luzum_la_hukm]; rfl

end Phi
end Nizam
