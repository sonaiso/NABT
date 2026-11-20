import SLGE.Wad
import SLGE.Maqam
import Aql.Mirsat

/-!
# أسماءُ الإشارة في قطر الندى (س132–135) والألفية (س137–144)

**الطلب.** قولُ المالك 2026-10-28 (لفظُه ووقتُه، 00:33 بتوقيت عمّان، من ملخّص الجلسة بعد ضغطها):
«يجب الاستفادة من ما لم نغطه وموجود في المراجع سواء استنتجته انت او موجود في المرفق وعمل lean له شرط ان يكون متناسق ومتكامل ومترابط مع البرهان واالحساب وفق الدستور وأفضل الممارسات … نفذ انت والوكلاء  و»
و«ما لم نغطه» من تحليل البنّاء قبله في الجلسة لمرفقٍ رفعه المالك، ومنه أنّ أسماء الإشارة في
`SLGE.Wad.ishara` قائمةُ ألفاظٍ بلا حكم. واختيارُ هذه القطعة أوّلًا، ونطاقُها، قرارُ البنّاء.

**المصدر.** `qatr.txt` المختوم (`2d9241be…`) الأسطر 132–135، و`alfiyya.txt` المختوم (`13b351a0…`) الأسطر 137–144 (والسطرُ 141 علامةُ صفحة).
والاقتباساتُ في `asanid` قطعٌ حرفيّة، يفحصها `tahaqquq/test_ishara.py` على المودَعين موصولةَ الأسطر.

**المدخل** (حقولُ مواصفة الضابط المجمَّد `tahaqquq/dawabit/ishara/wasf.md` بأعيانها): الأصلُ `Asl` بلا «ها» ولا لامٍ ولا كاف، والمشارُ إليه
`Mushar`، والموضعُ `Mawdi`، والمسافةُ المقصودة `Bud`، و«ها» التنبيه واللامُ والكاف. **والمدخلُ تحليلٌ يُعطى، لا مُخرَجُ قارئٍ من النصّ**:
فكُّ «هذا» و«ذلك» و«أولئك» إلى أصلٍ ولواحق يحتاج قاعدةَ رسمٍ ليست في النطاق.

**المخرج** `Hukm`: `maqbul` أو `khata` أو `laHukm`.

**الحكم** (`hukm`)، بالترتيب:
1. الأصلُ لا يوافق المشارَ إليه أو الموضع (`yuwafiq`): خطأ. «ذا للمذكر، وذي وذه وتي وته وتا للمؤنث، وذان وتان للمثنى بالألف رفعا وبالياء
   جرا ونصبا، وأولاء لجمعهما» (قطر س132–133)، و«بذا لمفرد مذكر أشر … وذان تان للمثنى المرتفع ... وفي سواه ذين تين اذكر … وبأولى أشر لجمع
   مطلقا» (ألفيّة س138–140)، و«وبهنا أو ههنا أشر إلى ... داني المكان … أو بثم فه» (س143–144). والخطأُ لما لم يُذكر بمفتاح الصورة في المواصفة
   («الصورةُ في استعمالٍ يذكر النطاقُ له صورةً غيرها ولا يذكرها»).
2. اللامُ بلا كاف: خطأ. اللامُ في النطاق مقرونةٌ بالكاف وحدها («مجردة من اللام … أو مقرونة بها»، «بالكاف حرفا دون لام أو معه»).
3. «ها» مع «ثم» للبعيد بلا كاف: لا حكم (قراءةُ البنّاء، في التعيين أدناه). وما سوى ذلك منها حكمُه حكمُ «ثم» بلا «ها» (خطأ)، ومنه «ها» واللامُ
   («واللام إن قدمت هاممتنعة»، ألفيّة س142).
4. المسافة (`hukmBud`):
   - **غيرُ المكان:** القريبُ بلا كاف، وبـ«ها» لا حكم؛ والبعيدُ بالكاف («والبعيد بالكاف»، قطر س133؛ «ولدى البعد انطقا بالكاف»، ألفيّة
     س140–142)، بلا لامٍ مطلقًا ولو تقدّمته «ها»، وباللام إلّا في المثنّى، والممدودةِ «أولاء»، وما تقدّمته «ها» («إلا في المثنى مطلقا وفي
     الجمع في لغة من مده وفيما تقدمته ها التنبيه»، قطر س134–135؛ «واللام إن قدمت هاممتنعة»، ألفيّة س142).
   - **«هنا»:** للقريب بلا كاف، وبـ«ها» («وبهنا أو ههنا أشر إلى ... داني المكان»، س143)؛ وللبعيد بالكاف («وبه الكاف صلا في البعد»، س143–144) وباللام
     والكاف («أو بهنالك انطقن»، س144) إلّا بعد «ها»؛ وبلا كافٍ للبعيد لا حكم («أو هنا»، س144، بلا ضبط).
   - **«ثم»:** للبعيد بلا كاف («أو بثم فه»، س144)، وما سوى ذلك خطأ.

**ما هو تعيينُ البنّاء** (لا نصُّ النطاق):
- «للمثنى» بلا جنس: الأصولُ الأربعة للمثنّى المذكّر والمؤنّث سواء (`muthanna_bila_jins`). ولا ينصّ النطاقُ على أنّ «ذان» للمذكّر و«تان» للمؤنّث.
- الموضعُ لا أثرَ له في غير المثنّى (`mawdi_la_yughayyir`). والنطاقُ يذكر الموضعَ للمثنّى وحده.
- الكافُ للقريب، والبعيدُ بلا كاف، خطأٌ في غير المكان (`hukmBud`): بالمقابلة بين «والبعيد بالكاف» وما قبله، وبمفتاح الصورة. و`kaf_lil_baid`
  تثبت أنّهما ليسا مقبولين، لا أنّهما خطأ.
- «ها» مع البعيد لا أثرَ لها إلّا مع اللام، في غير «ثم» (`ha_baid_la_yughayyir`): «مجردة من اللام مطلقا» يشمل ما تقدّمته «ها»، والاستثناءُ
  منه اللامُ وحدها («وفيما تقدمته ها التنبيه»، «إن قدمت ها»). وهذا التعليلُ أُخذ بعد قراءة الحالات من `taliq` الحالة I07 (انظر «ما غُيّر»).
  و«مجردة من اللام مطلقا» من القطر، والقطرُ لا يذكر «هنا»: فقبولُ «ها» و«هنا» والكاف للبعيد («ههناك») قراءةُ «وبه الكاف صلا» (س143–144) أنّ الضميرَ
  لـ«هنا أو ههنا» معًا.
- «ها» مع «ثم» للبعيد بلا كاف «لا حكم»: النطاقُ لا يذكر «ها» مع «ثم» ولا يمنعها، على قراءة البنّاء أنّ «ها» ليست صورةً للأصل (أدناه في «ما غُيّر»)؛
  وس143 يعدّ «ههنا» صورةً للقريب، فعلى صفّ الصورة في مفتاح المواصفة قد يكون الحكمُ خطأ. ولا حالةَ تمسّ هذا المدخل.
- «إلا في المثنى مطلقا» (القطر) خاصٌّ يُقدَّم على عموم الألفيّة «بالكاف حرفا دون لام أو معه» (`muthanna_lam_khata`).
- «ته» من القطر وحده، وتُقبل للمؤنّث. والألفيّةُ لا تذكرها ولا تمنعها؛ وقراءةُ «على الأنثى اقتصر» قصرًا لما ذكرته على المؤنّث، لا حصرًا للمؤنّث فيه،
  قراءةُ البنّاء.
- «أولى» المقصورة باللام مقبولة: القطرُ يستثني من اللام الجمعَ «في لغة من مده» وحدها (`madd_lam_khata`، `shahid_qasr`).
- ما لا يذكره النطاقُ للمكان («ثم» للقريب، و«ثم» بالكاف، وأصلٌ غيرُ مكانيٍّ للمكان، ومكانيٌّ لغيره) خطأٌ بمفتاح الصورة.

**الصلة بقطع Lean القائمة:**
- `asma_qatr`: أصولُ القطر التسعة بألفاظها هي `SLGE.Wad.ishara` بعينها (قائمةُ المالك، وتعليقُها «L132–134»)، وثالثةُ `SLGE.Wad.maarif`
  «الإشارة».
- `mirsat_maqbul`: المبهمُ في `Aql/Mirsat.lean` («هذا» تقريبًا، «ذاك» تبعيدًا بالمسافة من هنا) يُقرأ هنا «ذا» قريبًا و«ذا»+كاف بعيدًا،
  فحكمُه بهذه القراءة مقبولٌ عند كلّ مرساةٍ وحدٍّ وموضع، ومسافتُه مسافةُ `mubhamOf`. وهذه القراءةُ (`mubhamDakhil`) تعيينُ البنّاء. و«ها» في «هذا» لا يحكم فيها
  هذا النطاق مع القريب (`la_hukm_iff`).
- `maqam_ishara`: قائمةُ المالك `SLGE.Maqam.ishara` (الألفاظُ التسعة بسماتها) مقبولةٌ هنا كلُّها للقريب رفعًا بلا لواحق، كلُّ لفظٍ لمشارٍ إليه من
  سمته. **والعكسُ لا يصدق:**
  سمةُ «ذان» عند المالك مذكّرٌ و«تان» مؤنّث، و`muthanna_bila_jins` هنا تقبل كلًّا منهما للجنسين. فالمبرهنةُ تثبت أنّ ما في قائمته لا يُردّ هنا، ولا
  تثبت أنّ تعيينَه الجنسَ للمثنّى من النطاق؛ وهذا الفرقُ قرارُك.
- و`Jisr/SakkJumla.lean` يحكم في مرجع «هذا» و«ذاك» (ومنه `ishara_ithnan_la_hukm` بقرارك)، ولا يستورده هذا الملفّ ولا يستورد هذا.

**المنهج.** الشفرةُ المجمَّدة كُتبت قبل أن يقرأ البنّاءُ حالاتِ الضابط، وجُمّدت الحالاتُ قبلها (`tahaqquq/dawabit/ishara/tajmid.json`؛
`hawkama/منهج_الضوابط.md`)، ودُفعت في `0446d1e`، والتشغيلُ الأوّل عليها في `natija_1.json` (42/49). ونتيجتُها على الضابط في
`Jisr/IsharaQiyas.lean`، لا هنا. وهذا الملفُّ عُدّل بعدها (أدناه).

**ما غُيّر بعد قراءة الحالات** (فالتشغيلُ الثاني وما بعده على مادّةٍ مكشوفة)، أخذًا بقراءة المؤلّف في الموضعين:
- **«ها» مع القريب بلا كافٍ في غير المكان «لا حكم»** (كان مقبولًا): النطاقُ لا يذكر «ها» مع القريب إلّا في «ههنا» (س143)، ويذكرها مع البعيد
  مستثنيًا اللام؛ فما لم يتعرّض له «لا حكم» بالجملة التي بعد جدول المفتاح في المواصفة (`wasf.md` س87)، لا بصفٍّ فيه. وآخرُ صفوف الجدول (`خطأ`
  للصورة في استعمالٍ يذكر النطاقُ له صورةً غيرها) لا يُطبَّق على «ها» قراءةً للبنّاء: «ها» ليست صورةً للأصل ولا قسمًا في تقسيم القرب والبعد،
  والنطاقُ يذكرها مع البعيد مستثنيًا اللام وحده. أمّا الكافُ فقسمُ البعيد بنصّه («والبعيد بالكاف»)، فالكافُ للقريب صورةٌ لقسمٍ ذكر النطاقُ له
  غيرها، وحكمُها خطأٌ بذلك الصفّ. **وكان في الشفرة المجمَّدة** «ها» لا أثرَ لها إلّا مع اللام
  (`ha_la_yughayyir`، حُذفت). الحالاتُ: I08 وI12 وI22 وI27 وI36.
- **«هنا» بلا كافٍ للبعيد «لا حكم»** (كان مقبولًا): «أو هنا … أو هنا» في س144 بلا ضبط، ويفرّقها عن «هنا» القريب ضبطٌ لا يظهر في حروف
  النطاق، وهذا تعريفُ `غموض` في المواصفة نفسِها، والمحرّكُ لا يختار. الحالتان: I48 وI49.
- `mubhamDakhil` «هذا» صار «ذا» بلا «ها»، وحُذفت `hukmBud_ne_laHukm` (صار حكمُ المسافة يُخرج «لا حكم»)، وتغيّرت `la_hukm_iff` وصارت «تعريفيّة»
  (وكانت «لكلّ» لاستدعائها `hukmBud_ne_laHukm`)، وحلّت `ha_baid_la_yughayyir` (في البعيد بلا لام) محلَّ `ha_la_yughayyir` (بلا لام، قريبًا وبعيدًا)
  وهي أضيق؛ وفي `shawahid` صار شطرُ «هنا» بلا كافٍ للبعيد «لا حكم» (وكان مقبولًا)، وزيد شطرُ «ها» مع القريب؛ وتغيّر في الرأس نصُّ قاعدة «هنا»
  وتوثيقُ `mirsat_maqbul` وقراءتُه.
- وتعليلُ تعيين «ها» مع البعيد تغيّر أيضًا: كان في `0446d1e` «النطاقُ يذكرها متقدّمةً … ولا يمنعها إلّا مع اللام»، وصار «مجردة من اللام مطلقا يشمل
  ما تقدّمته ها، والاستثناءُ منه اللامُ وحدها»، وهو لفظُ `taliq` الحالة I07 تقريبًا («يشمل ما تقدمته ها، والاستثناءُ بها للّام وحدها»)، أُخذ بعد
  قراءة الحالات.
- **وبعد مراجعة `murajii` (لا بحالة):** «ها» مع «ثم» صارت «لا حكم» للبعيد بلا كافٍ وحده، وكانت «لا حكم» في كلّ مدخلٍ بعد الموافقة وبعد فحص اللام
  بلا كاف؛ فما سواه منها
  حكمُه حكمُ «ثم» بلا «ها» (خطأ)، ومنه «ها» واللامُ والكاف («واللام إن قدمت هاممتنعة»، س142). خمسةَ عشرَ مدخلًا من «لا حكم» إلى «خطأ»، لا تمسّها
  حالة. وزال من `ha_lam_khata` قيدُه: في غير «ثمّ»، وزيد في `shawahid` ثلاثةُ أشطرٍ لـ«ها» مع «ثم»، وزيدت `maqam_ishara`.
- **وما تغيّر في المجال كلّه** (قارن البنّاءُ بـ`#eval` في الجلسة، ولا يحفظه المستودع، حكمَ الشفرة المجمَّدة بحكم هذه على كلّ مدخلٍ من
  4704): 48 مدخلًا من «مقبول» إلى «لا حكم»: 42 «ها» مع القريب، و6 «هنا» بلا كافٍ للبعيد (بـ«ها» وبلا «ها»، في المواضع الثلاثة)؛
  تمسّ الحالاتُ سبعةً منها، فـ49/49 لا تشهد للأحد والأربعين الباقية. وصار المجالُ: مقبول 168، وخطأ 4470، و«لا حكم» 66 (وكان 216، و4470،
  و18)؛ وبعد المراجعة: مقبول 168، وخطأ 4485، و«لا حكم» 51.

**المبرهنات** (بالمعيار الموحَّد في `Nizam/Asas.lean`)، وهي خواصُّ هذا التعيين على مجاله، لا قوانينُ في اللغة:
- تعريفيّة (11): `ghayr_muwafiq_khata`، `lam_bila_kaf_khata`، `la_hukm_iff`، `ha_lam_khata`، `muthanna_lam_khata`، `madd_lam_khata`،
  `kaf_lil_baid`، `ha_baid_la_yughayyir`، `mawdi_la_yughayyir`، `muthanna_bila_jins`، `mirsat_maqbul`. وبرهانُها فكُّ التعريفات وتفكيكُ الحالات، فلا
  «لكلّ» بحرف المعيار. وهي مكمَّمةٌ على المدخل، إلّا `madd_lam_khata` (الأصلُ واللامُ مثبَّتان، والباقي مكمَّم)، و`mirsat_maqbul` (على الحدّ والمرساة
  والإزاحة، مجالٌ غيرُ منتهٍ، وتفكيكُها على شرط المسافة).
- على الشاهد (4): `asma_qatr`، `maqam_ishara`، `shawahid`، `shahid_qasr`.

**حدُّه.** المدخلُ تحليلٌ يُعطى؛ والكافُ لمخاطَبٍ واحدٍ مذكّر؛ ولا حكمَ في التنوّع (أشهرُ اللغتين، والتفضيلُ «والمد أولى» لا يُقاس)؛ ولا وصلَ
بالقارئ ولا بالمحرّك.
-/

namespace Jisr
namespace Ishara

/-! ## المدخل والمخرج -/

/-- أصلُ اسم الإشارة بلا «ها» ولا لامٍ ولا كاف، كما يكتبه النطاق. -/
inductive Asl
  | dha | dhi | dhih | ti | tih | ta | dhan | tan | dhayn | tayn | ulaa | ula | huna | thamma
  deriving DecidableEq, Repr

/-- لفظُ الأصل كما في المواصفة. -/
def Asl.lafz : Asl → String
  | .dha => "ذا" | .dhi => "ذي" | .dhih => "ذه" | .ti => "تي" | .tih => "ته" | .ta => "تا"
  | .dhan => "ذان" | .tan => "تان" | .dhayn => "ذين" | .tayn => "تين" | .ulaa => "أولاء" | .ula => "أولى"
  | .huna => "هنا" | .thamma => "ثم"

/-- أصولُ المثنّى الأربعة. -/
def Asl.muthanna : Asl → Bool
  | .dhan | .tan | .dhayn | .tayn => true
  | _ => false

/-- أصلا المكان. -/
def Asl.makan : Asl → Bool
  | .huna | .thamma => true
  | _ => false

inductive Mushar
  | mufradMudhakkar | mufradMuannath | muthannaMudhakkar | muthannaMuannath | jamMudhakkar | jamMuannath | makan
  deriving DecidableEq, Repr

inductive Mawdi
  | raf | nasb | jarr
  deriving DecidableEq, Repr

inductive Bud
  | qarib | baid
  deriving DecidableEq, Repr

structure Dakhil where
  asl : Asl
  mushar : Mushar
  mawdi : Mawdi
  bud : Bud
  ha : Bool
  lam : Bool
  kaf : Bool
  deriving DecidableEq, Repr

inductive Hukm
  | maqbul | khata | laHukm
  deriving DecidableEq, Repr

/-! ## الحكم -/

/-- الأصلُ يوافق المشارَ إليه والموضع (قطر س132–133؛ ألفيّة س138–140، س143–144). -/
def yuwafiq (a : Asl) (m : Mushar) (w : Mawdi) : Bool :=
  match a with
  | .dha => m == .mufradMudhakkar
  | .dhi | .dhih | .ti | .tih | .ta => m == .mufradMuannath
  | .dhan | .tan => (m == .muthannaMudhakkar || m == .muthannaMuannath) && w == .raf
  | .dhayn | .tayn => (m == .muthannaMudhakkar || m == .muthannaMuannath) && w != .raf
  | .ulaa | .ula => m == .jamMudhakkar || m == .jamMuannath
  | .huna | .thamma => m == .makan

/-- حكمُ المسافة واللواحق، بعد الموافقة. -/
def hukmBud (d : Dakhil) : Hukm :=
  match d.asl, d.bud with
  | .thamma, .qarib => .khata
  | .thamma, .baid => if d.kaf then .khata else .maqbul
  | .huna, .qarib => if d.kaf then .khata else .maqbul
  | .huna, .baid => if !d.kaf then .laHukm else if d.lam && d.ha then .khata else .maqbul
  | _, .qarib => if d.kaf then .khata else if d.ha then .laHukm else .maqbul
  | a, .baid =>
    if !d.kaf then .khata
    else if !d.lam then .maqbul
    else if a.muthanna || a == .ulaa || d.ha then .khata
    else .maqbul

/-- حكمُ النطاق في استعمال اسم الإشارة. -/
def hukm (d : Dakhil) : Hukm :=
  if !yuwafiq d.asl d.mushar d.mawdi then .khata
  else if d.lam && !d.kaf then .khata
  else if d.ha && d.asl == .thamma && d.bud == .baid && !d.kaf then .laHukm
  else hukmBud d

/-! ## الأسانيد (قطعٌ حرفيّة؛ يفحصها `tahaqquq/test_ishara.py` موصولةَ الأسطر) -/

/-- (المفتاح، المصدر، أوّلُ سطر، آخرُ سطر، النصّ). -/
def asanid : List (String × String × Nat × Nat × String) := [
  ("dhaMudhakkar", "قطر", 132, 132, "ذا للمذكر"),
  ("muannath", "قطر", 132, 132, "وذي وذه وتي وته وتا للمؤنث"),
  ("muthanna", "قطر", 132, 133, "وذان وتان للمثنى بالألف رفعا وبالياء جرا ونصبا"),
  ("jam", "قطر", 133, 133, "وأولاء لجمعهما"),
  ("baid", "قطر", 133, 134, "والبعيد بالكاف مجردة من اللام مطلقا أو مقرونة بها"),
  ("illa", "قطر", 134, 135, "إلا في المثنى مطلقا وفي الجمع في لغة من مده وفيما تقدمته ها التنبيه"),
  ("mufradA", "ألفية", 138, 138, "بذا لمفرد مذكر أشر ... بذي وذه تي تا على الأنثى اقتصر"),
  ("muthannaA", "ألفية", 139, 139, "وذان تان للمثنى المرتفع ... وفي سواه ذين تين اذكر تطع"),
  ("jamA", "ألفية", 140, 140, "وبأولى أشر لجمع مطلقا ... والمد أولى"),
  ("baidA", "ألفية", 140, 142, "ولدى البعد انطقا بالكاف حرفا دون لام أو معه"),
  ("haA", "ألفية", 142, 142, "واللام إن قدمت هاممتنعة"),
  ("hunaQarib", "ألفية", 143, 143, "وبهنا أو ههنا أشر إلى ... داني المكان"),
  ("hunaBaid", "ألفية", 143, 144, "وبه الكاف صلا في البعد أو بثم فه أو هنا ... أو بهنالك انطقن أو هنا")]

/-! ## مبرهنات (خواصُّ التعيين على مجاله؛ والضابطُ يشهد أنّه غيرُ فارغ: `Jisr/IsharaQiyas.lean`) -/

/-- **ما لا يوافق خطأ** (تعريفيّة). -/
theorem ghayr_muwafiq_khata (d : Dakhil) (h : yuwafiq d.asl d.mushar d.mawdi = false) : hukm d = .khata := by
  unfold hukm
  simp [h]

/-- **اللامُ بلا كافٍ خطأ** (تعريفيّة). -/
theorem lam_bila_kaf_khata (d : Dakhil) (hl : d.lam = true) (hk : d.kaf = false) : hukm d = .khata := by
  unfold hukm
  cases h : yuwafiq d.asl d.mushar d.mawdi <;> simp [hl, hk]

/-- **«لا حكم» في ثلاثة مواضع** (تعريفيّة): الأصلُ موافق، ولا لامَ بلا كاف، ثمّ «ها» مع «ثم» للبعيد بلا كاف، أو «هنا» بلا كافٍ للبعيد، أو «ها» مع القريب
    بلا كافٍ في غير المكان. -/
theorem la_hukm_iff (d : Dakhil) :
    hukm d = .laHukm ↔
      (yuwafiq d.asl d.mushar d.mawdi = true ∧ ¬(d.lam = true ∧ d.kaf = false) ∧
        ((d.ha = true ∧ d.asl = .thamma ∧ d.bud = .baid ∧ d.kaf = false) ∨ (d.asl = .huna ∧ d.bud = .baid ∧ d.kaf = false) ∨
         (d.asl.makan = false ∧ d.bud = .qarib ∧ d.kaf = false ∧ d.ha = true))) := by
  rcases d with ⟨a, m, w, b, ha, l, k⟩
  cases a <;> cases b <;> cases ha <;> cases l <;> cases k <;>
    simp [hukm, hukmBud, Asl.muthanna, Asl.makan] <;> cases m <;> cases w <;> simp [yuwafiq]

/-- **«ها» مع اللام خطأ** (تعريفيّة؛ قطر س135، ألفيّة س142). -/
theorem ha_lam_khata (d : Dakhil) (hh : d.ha = true) (hl : d.lam = true) : hukm d = .khata := by
  rcases d with ⟨a, m, w, b, ha, l, k⟩
  simp only at hh hl
  subst hh hl
  cases a <;> cases b <;> cases k <;> simp_all [hukm, hukmBud, yuwafiq, Asl.muthanna]

/-- **المثنّى باللام خطأ** (تعريفيّة؛ «إلا في المثنى مطلقا»، قطر س134). -/
theorem muthanna_lam_khata (d : Dakhil) (hm : d.asl.muthanna = true) (hl : d.lam = true) : hukm d = .khata := by
  rcases d with ⟨a, m, w, b, ha, l, k⟩
  simp only at hm hl
  subst hl
  cases a <;> simp [Asl.muthanna] at hm <;> cases b <;> cases k <;> cases ha <;> simp_all [hukm, hukmBud, Asl.muthanna]

/-- **الممدودةُ باللام خطأ** (تعريفيّة؛ «وفي الجمع في لغة من مده»، قطر س134). -/
theorem madd_lam_khata (m : Mushar) (w : Mawdi) (b : Bud) (ha k : Bool) :
    hukm ⟨.ulaa, m, w, b, ha, true, k⟩ = .khata := by
  cases m <;> cases b <;> cases ha <;> cases k <;> simp [hukm, hukmBud, yuwafiq, Asl.muthanna]

/-- **الكافُ للبعيد** (تعريفيّة): في غير المكان، ما قُبل فكافُه للبعيد وحده. -/
theorem kaf_lil_baid (d : Dakhil) (hm : d.asl.makan = false) (hq : hukm d = .maqbul) : d.kaf = true ↔ d.bud = .baid := by
  rcases d with ⟨a, m, w, b, ha, l, k⟩
  simp only at hm hq ⊢
  cases a <;> simp [Asl.makan] at hm <;> cases b <;> cases k <;> cases l <;> cases ha <;>
    simp_all [hukm, hukmBud, Asl.muthanna]

/-- **«ها» لا أثرَ لها في البعيد بلا لام** (تعريفيّة)، في غير «ثم». -/
theorem ha_baid_la_yughayyir (d : Dakhil) (hb : d.bud = .baid) (hl : d.lam = false) (ht : d.asl ≠ .thamma) :
    hukm { d with ha := true } = hukm { d with ha := false } := by
  rcases d with ⟨a, m, w, b, ha, l, k⟩
  simp only at hb hl ht
  subst hb hl
  cases a <;> cases k <;> simp_all [hukm, hukmBud]

/-- **الموضعُ لا أثرَ له في غير المثنّى** (تعريفيّة). -/
theorem mawdi_la_yughayyir (d : Dakhil) (w : Mawdi) (hm : d.asl.muthanna = false) :
    hukm { d with mawdi := w } = hukm d := by
  rcases d with ⟨a, m, w', b, ha, l, k⟩
  simp only at hm ⊢
  cases a <;> simp [Asl.muthanna] at hm <;> simp [hukm, yuwafiq, hukmBud]

/-- **المثنّى بلا جنس** (تعريفيّة): الحكمُ في المثنّى المؤنّث هو حكمُه في المذكّر. -/
theorem muthanna_bila_jins (d : Dakhil) :
    hukm { d with mushar := .muthannaMuannath } = hukm { d with mushar := .muthannaMudhakkar } := by
  rcases d with ⟨a, m, w, b, ha, l, k⟩
  cases a <;> simp [hukm, yuwafiq, hukmBud]

/-! ## الصلة بقطع Lean القائمة -/

/-- أصولُ القطر بترتيب س132–133. -/
def asulQatr : List Asl := [.dha, .dhi, .dhih, .ti, .tih, .ta, .dhan, .tan, .ulaa]

/-- **أصولُ القطر هي `SLGE.Wad.ishara`** (على الشاهد)، و«الإشارة» ثالثةُ المعارف في `SLGE.Wad.maarif`. -/
theorem asma_qatr : asulQatr.map Asl.lafz = SLGE.Wad.ishara ∧ SLGE.Wad.maarif[2]? = some "الإشارة" := by
  decide

/-- المشارُ إليه من سمة المالك في `SLGE.Maqam.ishara` (غائبٌ دائمًا): الجنسُ 2 فيها للجنسين. -/
def musharMin : SLGE.Maqam.Feat → List Mushar
  | (3, 0, 0) => [.mufradMudhakkar]
  | (3, 1, 0) => [.mufradMuannath]
  | (3, 0, 1) => [.muthannaMudhakkar]
  | (3, 1, 1) => [.muthannaMuannath]
  | (3, 2, 2) => [.jamMudhakkar, .jamMuannath]
  | _ => []

/-- الأصلُ من لفظه. -/
def aslMin (s : String) : Option Asl :=
  [Asl.dha, .dhi, .dhih, .ti, .tih, .ta, .dhan, .tan, .dhayn, .tayn, .ulaa, .ula, .huna, .thamma].find? (·.lafz == s)

/-- **قائمةُ المالك `SLGE.Maqam.ishara` مقبولةٌ هنا** (على الشاهد): كلُّ لفظٍ فيها أصلٌ هنا، وله مشارٌ إليه من سمته، وحكمُه للقريب رفعًا
    مقبول. **والعكسُ لا يصدق:** «تان» للمثنّى المذكّر مقبولةٌ هنا (`muthanna_bila_jins`)، وسمتُها عند المالك مؤنّث `(3,1,1)`، و«ذان» للمثنّى
    المؤنّث كذلك. والفرقُ معلَنٌ قرارًا للمالك. -/
theorem maqam_ishara :
    SLGE.Maqam.ishara.all (fun x => match aslMin x.1 with
      | some a => !(musharMin x.2).isEmpty &&
          (musharMin x.2).all (fun m => hukm ⟨a, m, .raf, .qarib, false, false, false⟩ == .maqbul)
      | none => false) = true ∧
    hukm ⟨.tan, .muthannaMudhakkar, .raf, .qarib, false, false, false⟩ = .maqbul ∧
    hukm ⟨.dhan, .muthannaMuannath, .raf, .qarib, false, false, false⟩ = .maqbul := by
  decide

/-- المبهمُ في `Aql/Mirsat.lean` مدخلًا هنا (تعيين): «هذا» «ذا» قريبًا بلا «ها» (و«ها» مع القريب لا يحكم فيها هذا النطاق: `la_hukm_iff`)،
    و«ذاك» «ذا»+كاف بعيدًا، لمفردٍ مذكّرٍ رفعًا. -/
def mubhamDakhil : Aql.Mirsat.Mubham → Dakhil
  | .hadha => ⟨.dha, .mufradMudhakkar, .raf, .qarib, false, false, false⟩
  | .dhaka => ⟨.dha, .mufradMudhakkar, .raf, .baid, false, false, true⟩

/-- **المبهمُ بقراءة `mubhamDakhil` («هذا» «ذا» بلا «ها»، و«ذاك» «ذا»+كاف) مقبولٌ هنا عند كلّ مرساة، ومسافتُه مسافةُ `mubhamOf`** (تعريفيّة؛ لكلّ حدٍّ
    ومرساةٍ وموضع). و«هذا» بـ«ها» للقريب «لا حكم» هنا (`la_hukm_iff`). -/
theorem mirsat_maqbul (hadd : Nat) (r : Aql.Mirsat.Mirsat) (x : Aql.Makan.Izaha3) :
    hukm (mubhamDakhil (Aql.Mirsat.mubhamOf hadd r x)) = .maqbul ∧
    (mubhamDakhil (Aql.Mirsat.mubhamOf hadd r x)).bud =
      (if Aql.Mirsat.masafa (Aql.Makan.nisba r.huna x) ≤ hadd then .qarib else .baid) := by
  unfold Aql.Mirsat.mubhamOf
  by_cases h : Aql.Mirsat.masafa (Aql.Makan.nisba r.huna x) ≤ hadd <;> simp [h, mubhamDakhil, hukm, hukmBud, yuwafiq]

/-! ## شواهدُ النطاق (على الشاهد) -/

/-- **شواهدُ الأسطر**: «ذا للمذكر» قريبًا؛ «ذان … بالألف رفعا وبالياء جرا ونصبا»؛ «والبعيد بالكاف مجردة من اللام مطلقا أو مقرونة بها»؛
    «إلا في المثنى … وفيما تقدمته ها التنبيه»؛ «بهنا أو ههنا … داني المكان»؛ «وبه الكاف صلا في البعد أو بثم فه … أو بهنالك»؛ و«لا حكم»:
    «هنا» بلا كافٍ للبعيد («أو هنا» بلا ضبط)، و«ها» مع القريب في غير المكان، و«ها» مع «ثم» للبعيد بلا كاف؛ وما سواه من «ها» مع «ثم» خطأ. -/
theorem shawahid :
    hukm ⟨.dha, .mufradMudhakkar, .raf, .qarib, false, false, false⟩ = .maqbul ∧
    hukm ⟨.dha, .mufradMuannath, .raf, .qarib, false, false, false⟩ = .khata ∧
    hukm ⟨.dhan, .muthannaMudhakkar, .raf, .qarib, false, false, false⟩ = .maqbul ∧
    hukm ⟨.dhan, .muthannaMudhakkar, .jarr, .qarib, false, false, false⟩ = .khata ∧
    hukm ⟨.dhayn, .muthannaMudhakkar, .nasb, .qarib, false, false, false⟩ = .maqbul ∧
    hukm ⟨.dhayn, .muthannaMudhakkar, .raf, .qarib, false, false, false⟩ = .khata ∧
    hukm ⟨.dha, .mufradMudhakkar, .raf, .baid, false, false, true⟩ = .maqbul ∧
    hukm ⟨.dha, .mufradMudhakkar, .raf, .baid, false, true, true⟩ = .maqbul ∧
    hukm ⟨.dha, .mufradMudhakkar, .raf, .baid, false, false, false⟩ = .khata ∧
    hukm ⟨.dhan, .muthannaMudhakkar, .raf, .baid, false, false, true⟩ = .maqbul ∧
    hukm ⟨.dhan, .muthannaMudhakkar, .raf, .baid, false, true, true⟩ = .khata ∧
    hukm ⟨.dha, .mufradMudhakkar, .raf, .baid, true, false, true⟩ = .maqbul ∧
    hukm ⟨.dha, .mufradMudhakkar, .raf, .baid, true, true, true⟩ = .khata ∧
    hukm ⟨.huna, .makan, .nasb, .qarib, false, false, false⟩ = .maqbul ∧
    hukm ⟨.huna, .makan, .nasb, .qarib, true, false, false⟩ = .maqbul ∧
    hukm ⟨.huna, .makan, .nasb, .baid, false, false, true⟩ = .maqbul ∧
    hukm ⟨.huna, .makan, .nasb, .baid, false, true, true⟩ = .maqbul ∧
    hukm ⟨.huna, .makan, .nasb, .baid, false, false, false⟩ = .laHukm ∧
    hukm ⟨.dha, .mufradMudhakkar, .raf, .qarib, true, false, false⟩ = .laHukm ∧
    hukm ⟨.thamma, .makan, .nasb, .baid, false, false, false⟩ = .maqbul ∧
    hukm ⟨.thamma, .makan, .nasb, .qarib, false, false, false⟩ = .khata ∧
    hukm ⟨.thamma, .makan, .nasb, .baid, true, false, false⟩ = .laHukm ∧
    hukm ⟨.thamma, .makan, .nasb, .qarib, true, false, false⟩ = .khata ∧
    hukm ⟨.thamma, .makan, .nasb, .baid, true, false, true⟩ = .khata ∧
    hukm ⟨.thamma, .makan, .nasb, .baid, true, true, true⟩ = .khata := by
  decide

/-- **الجمعُ باللام: المقصورةُ مقبولة والممدودةُ خطأ** («وفي الجمع في لغة من مده»، قطر س134؛ «وبأولى أشر لجمع مطلقا ... والمد أولى»، ألفيّة
    س140). -/
theorem shahid_qasr :
    hukm ⟨.ula, .jamMudhakkar, .raf, .baid, false, true, true⟩ = .maqbul ∧
    hukm ⟨.ulaa, .jamMudhakkar, .raf, .baid, false, true, true⟩ = .khata ∧
    hukm ⟨.ulaa, .jamMuannath, .raf, .baid, false, false, true⟩ = .maqbul := by
  decide

end Ishara
end Jisr
