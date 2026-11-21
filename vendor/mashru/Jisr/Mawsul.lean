import SLGE.Wad
import SLGE.Maqam
import Nizam.Phi
import SLGE.TarkibExt

/-!
# الموصولُ وصلتُه في قطر الندى (س137–143) والألفية (س146–157)

**الطلب.** قولُ المالك 2026-10-28 (لفظُه ووقتُه، 00:33 بتوقيت عمّان، من ملخّص الجلسة بعد ضغطها): «يجب الاستفادة من ما لم نغطه وموجود في المراجع سواء
استنتجته انت او موجود في المرفق وعمل lean له شرط ان يكون متناسق ومتكامل ومترابط مع البرهان واالحساب وفق الدستور وأفضل الممارسات …
نفذ انت والوكلاء  و». والموصولُ في Lean القائمة (ملفّاتُ المالك في `SLGE/`) قائمةُ ألفاظٍ (`SLGE.Wad.mawsul`)، وسماتُ الخاصّ منه وشرطُ العائد
(`SLGE.Maqam.mawsulKhass`، `SLGE.Maqam.silaOK`)، وترخيصُ الموصول بصلته إطارًا في التركيب (`SLGE.TarkibExt.mawsulOK`، ويستعمله `SLGE.Kull`)، والعائدُ
مؤشّرًا في الكلام (`SLGE.Simat2.discOK2`)؛ بلا حكمٍ على صورة اللفظ بموضعه. وفي موضعين خلافٌ بينها وبين هذا الملفّ، معلَنٌ بمبرهنتين («الصلة بقطع
Lean القائمة» أدناه). واختيارُ هذه القطعة بعد الضمير، ونطاقُها، قرارُ البنّاء.

**المصدر.** `qatr.txt` المختوم (`2d9241be…`) الأسطر 137–143، و`alfiyya.txt` المختوم (`13b351a0…`) الأسطر 146–157. وما بعدها من الباب (س159–165:
إعرابُ «أي» وشروطُ حذف العائد) خارجَ النطاق. والاقتباساتُ في `asanid` قطعٌ حرفيّة، يفحصها `tahaqquq/test_mawsul.py` على المودَعين موصولةَ الأسطر.

**المدخل** (حقولُ مواصفة الضابط المجمَّد `tahaqquq/dawabit/mawsul/wasf.md` بأعيانها): اللفظ `Lafz`، وما يقع عليه `Sima`، والموضع، وتشديدُ النون،
واللغة، وما قبله، والإلغاء، ونوعُ الصلة `Sila`، والعائد `Aid` وسمتُه. **والمدخلُ تحليلٌ يُعطى، لا مُخرَجُ قارئٍ من النصّ.**

**المخرج** `Jawab`: الحكم (`maqbul` أو `khata` أو `laHukm`)، والدرجةُ قائمةً (`qalil`، `nazr`، `lugha`، `bila`)؛ وحين لا يكون الحكمُ «مقبولًا»
فالدرجةُ `[bila]` (`ghayr_maqbul_bila`). و`qalil` لا يُخرجه `jawab` بعد تعديله (`la_qalil`): موضعُه الوحيد صلةُ «أل» فعلًا معربًا في الألفية، وهو
«لا حكم» لاختلاف المصدرين.

**الحكم** (`jawab`):
1. **البوّابة:** الحقولُ غيرُ المتّسقة (`muttasiq`: التشديدُ في لفظٍ آخرُه نون، و«لا عائد» في العائد وسمتِه معًا) والإلغاءُ في أيّ لفظٍ «لا حكم»
   (`bawwaba_la_hukm`): «إذا لم تلغ» قيدٌ في «ذا»، والملغاةُ ليست موصولًا؛ والإلغاءُ في غيرها حقولٌ تخالف المواصفة.
2. **وإلّا فربطُ أربعة أحكام** بـ`wa`، وهو ربطُ `Nizam.Phi.K3.wa` على الأحكام (`wa_k3`، `jawab_k3`): يكفي خطأٌ في أحدها ليكون الجوابُ خطأً
   (`khata_yakfi`)، ولا قبولَ إلّا بقبولها كلِّها بدرجاتها المذكورة، وما سواهما «لا حكم».
3. **اللفظ** (`lafzJ`):
   - «الذي» للمفرد المذكّر و«التي» للمفرد المؤنّث («وهو الذي والتي»، قطر س137؛ «موصول الأسماء الذي الأنثى التي»، ألفيّة س147).
   - «اللذان» و«اللتان» رفعًا، و«اللذين» و«اللتين» جرًّا ونصبًا («واللذان واللتان بالألف رفعا وبالياء جرا ms03 ونصبا»، س137–138). و«اللذيان» و«اللتيان»
     خطأ («واليا إذا ما ثنيا لا تثبت»، س147).
   - «الذين» لجمع المذكّر في المواضع كلّها («الذين بالياء مطلقا»، قطر س138؛ «الذين مطلقا»، ألفيّة س150)، و«اللذون» رفعًا لغة («وبعضهم بالواو رفعا
     نطقا»، س150)؛ و«الألى» لجمع المذكّر (س138، س150).
   - «اللائي» و«اللاتي» لجمع المؤنّث (قطر س138–139)، و«اللات» و«اللاء» كذلك (ألفيّة س151)، و«اللاء» لجمع المذكّر نزر («واللاء كالذين نزرا
     وقعا»، س151).
   - «من» و«ما» و«أي» و«أل» لكلّ معنى («وبمعنى الجميع من وما وأي، وأل»، قطر س139؛ «ومن وما وأل تساوي ما ذكره»، ألفيّة س152).
   - «ذو» لكلّ معنى في لغة طيئ (في القطر تحت «وبمعنى الجميع»: «وذو في لغة طي»، س139–140؛ «وهكذا ذو عند طيئ شهر»، س152)، و«ذات» للمفرد المؤنّث و«ذوات» لجمع المؤنّث عندهم
     («وكالتي أيضا لديهم ذات ... وموضع اللاتي أتى ذوات»، س153).
   - «ذا» لكلّ معنى بعد «ما» أو «من» الاستفهاميّتين («وذا بعد ما أو من الاستفهاميتين»، قطر س140؛ «ومثل ماذا بعدما استفهام ... أومن»، س154).
   - وما سوى ذلك خطأ: لفظٌ لمعنًى أو موضعٍ جعل النطاقُ له غيرَه، ومنه «ذو» و«ذات» و«ذوات» في غير طيئ، و«ذا» في غير ما بعد الاستفهاميّتين
     (`qayd_khata`): القيدُ يُخرج ما خرج عنه إلى ألفاظٍ أخرى من النطاق (مفتاحُ الصورة في المواصفة).
4. **التشديد** (`tashdidJ`): «والنون إن تشدد فلا ملامه» (ألفيّة س148) في نون المثنّى، وسياقُها تثنيةُ الذي والتي (س147)؛ فهو لا يغيّر الجوابَ في المثنّى
   (`tashdid_la_yughayyir`)، وفي غيره «لا حكم» (`tashdid_ghayr_muthanna`: لا يُقبل).
5. **الصلة** (`silaJ`)، بقراءة كلّ مصدرٍ وحده: ما اتّفقا عليه حكمُه، وما اختلفا فيه «لا حكم» (`ikhtilaf_masdarayn`):
   - القطر (`silaQatr`): لـ«أل» الوصف («وأل في وصف صريح لغير تفضيل»، س139؛ «وصلة أل الوصف»، س140)، ولغيرها الجملةُ الخبريّة والظرفُ والجارُّ
     والمجرورُ التامّان («وصلة غيرها إما جملة خبرية … أو ظرف أو جار ومجرور تامان»، س141–143)؛ وما سواها خطأ.
   - الألفية (`silaAlfiyya`): لـ«أل» الصفةُ الصريحة والفعلُ المعرب قليل («وصفة صريحة صلة أل ... وكونها بمعرب الأفعال قل»، س157)، ولغيرها الجملةُ وشبهُها
     («وجملة أو شبهها الذي وصل»، س156)؛ وما سواها خطأ.
   - فالفعلُ المعرب صلةً لـ«أل» والجملةُ الإنشائيّة صلةً لغيرها «لا حكم» (`silat_al`، `silat_ghayriha`)؛ ولا موصولَ بلا صلة («وكلها يلزم ms03 بعده صله»،
     س155؛ `bila_sila`).
6. **العائد** (`aidJ`):
   - لا صلةَ بلا ضميرٍ يعود («ذات ضمير طبق للموصول يسمى عائدا»، قطر س141؛ «على ضمير لائق مشتمله»، ألفيّة س155؛ `la_aid_khata`)، والمحذوفُ في الجملة
     مقبول («وقد يحذف»، س141)، وفي غيرها «لا حكم».
   - والعائدُ على سمة المعنى: في اللفظ الخاصّ خطأٌ إن خالفها؛ وفي المشترك («من» وأخواتها) خطأٌ إن خالف المعنى واللفظَ (المفردَ المذكّر) معًا، و«لا حكم»
     إن وافق اللفظَ دون المعنى: «طبق للموصول» لا يقول أيُّهما.

**ما هو تعيينُ البنّاء** (لا نصُّ النطاق):
- اللغةُ قيدٌ على «ذو» و«ذات» و«ذوات» وحدها (`lugha_la_tughayyir`)؛ وما قبله والموضعُ لا أثرَ لهما إلّا في «ذا» والمثنّى و«اللذون».
- «ذات» و«ذوات» لما ذُكرتا له وحده (و«ذو» عند طيئ لكلّ معنى نصًّا: هي في القطر تحت «وبمعنى الجميع»، س139–140).
- في اللفظ يُؤخذ ما في أحد المصدرين إذا سكت الآخر عنه أو أطلق بلفظٍ لا ينفيه، ولا يُعدّ ذلك اختلافًا («لا حكم» للاختلاف في الصلة وحدها): «اللذون»
  رفعًا لغةٌ والقطرُ يقول «الذين بالياء مطلقا»، و«اللاء» لجمع المذكّر نزرٌ والقطرُ لا يذكرها (وهي قراءةُ المؤلّف في M14 وM16).
- «شبهُها» في الألفية الظرفُ والجارُّ التامّان، لا الناقصان.
- «طبق للموصول» في المشترك: الموافقُ للمعنى مقبول، والموافقُ للّفظ وحده «لا حكم».
- المحذوفُ في غير الجملة «لا حكم»: «وقد يحذف» في سياق الجملة الخبريّة.
- البوّابةُ والربطُ بـ`K3.wa`، والدرجاتُ في القبول درجاتُ الأحكام الأربعة المذكورة.

**ما غُيّر بعد قراءة الحالات** (على مادّةٍ مكشوفة؛ الشفرةُ المجمَّدة في `e13b5a0`). أخذًا بقراءة المؤلّف في المواضع التسعة التي أخفقت فيها الشفرةُ
المجمَّدة كلِّها (`tahaqquq/dawabit/mawsul/mulhaq_1.md`)، وتطبيقًا لكلّ قاعدةٍ على ما تشمله عبارتُها:
- «ذو» و«ذات» و«ذوات» في غير طيئ، و«ذا» في غير ما بعد الاستفهاميّتين: كانت «لا حكم»، وصارت خطأ (M29، M31، M36).
- التشديدُ في غير المثنّى («الذين»، «اللذون»): كان لا يغيّر الجواب، وصار «لا حكم» (M13، M47).
- الجملةُ الإنشائيّةُ صلةً لغير «أل»: كانت خطأً (بالقطر)، وصارت «لا حكم» (M56، M57)؛ والفعلُ المعربُ صلةً لـ«أل»: كان مقبولًا قليلًا (بالألفية)، وصار
  «لا حكم» (M58، M59): المصدران يختلفان، والمواصفةُ تجعل ذلك غموضًا.
- الضمُّ: كان أوّلُ ما ليس مقبولًا هو الجواب، وصار ربطَ `K3.wa` (الخطأُ يغلب «لا حكم»). و«ذا» الملغاةُ: كانت «لا حكم» من اللفظ، وصارت «لا حكم» في البوّابة.
- على المجال كلّه (2,782,080 مدخلًا، عدُّ أداةٍ في الجلسة بمقابلة `jawab` بنسخة الشفرة المجمَّدة) تغيّر جوابُ 44,610، وكلُّ مدخلٍ في أوّل صنفٍ يصدق
  عليه بهذا الترتيب: التشديدُ في الجمع 360 (168 من مقبول و192 من خطأ إلى «لا حكم»)، و«ذو» وأختاها في غير طيئ 30,780 (من «لا حكم» إلى خطأ)، و«ذا» في
  غير ما بعد الاستفهاميّتين 6,840 (كذلك)، والإنشائيّةُ 6,414 (من خطأ إلى «لا حكم»)، والفعلُ المعرب لـ«أل» 216 (من مقبول إلى «لا حكم»)؛ ولا مدخلَ تغيّر
  خارج هذه الأصناف (فلم يتغيّر بالضمّ ولا بالبوّابة وحدهما شيء)، ولا مدخلَ تغيّرت درجتُه وحدها. تمسّ الحالاتُ منها تسعةً (الإخفاقات)، ولا حالةَ تمسّ
  الباقي، فـ«88 من 88» لا تشهد له.

**الصلة بقطع Lean القائمة:**
- `Nizam.Phi.K3.wa`: ربطُ الأحكام (`wa_k3`).
- **خلافٌ معلَن مع `SLGE.TarkibExt.mawsulOK`** (ملفُّ المالك، لا يُعدَّل هنا): لا يرخّص صلةً إطارُها شبهُ جملة (`sila.1 != 2`)، فيردّ الظرفَ والجارَّ صلةً؛
  والقطر س143 «أو ظرف أو جار ومجرور تامان» يقبلهما، وكذلك `jawab` (`khilaf_mawsulOK`). والقرارُ للمالك.
- **خلافٌ معلَن مع `SLGE.Maqam.silaOK`** (ملفُّ المالك): يقبل لـ«من» المشتركة أيَّ عائدٍ غائب (سمةُ الموصول فيه لا تحمل معناه)؛ و`jawab` يردّ
  العائدَ المخالفَ لمعنى «من» وللفظها معًا («ذات ضمير طبق للموصول»، القطر س141) (`khilaf_silaOK`). والقرارُ للمالك.
- `asma_qatr`: ألفاظُ `SLGE.Wad.mawsul` الأربعةَ عشرَ ألفاظٌ هنا، و«الموصول» رابعةُ `SLGE.Wad.maarif`.
- `maqam_khass`: كلُّ لفظٍ في `SLGE.Maqam.mawsulKhass` مقبولٌ هنا لمعنًى من سمته، بصلةٍ خبريّةٍ وعائدٍ مستترٍ موافق.

**المنهج.** شفرةُ هذا الملفّ كُتبت أوّلًا قبل أن يقرأ البنّاءُ حالاتِ الضابط، وجُمّدت الحالاتُ قبلها (`tahaqquq/dawabit/mawsul/tajmid.json`؛
`hawkama/منهج_الضوابط.md`)، ثمّ غُيّرت بعد قراءتها كما أعلاه. ونتيجتُها على الضابط في `Jisr/MawsulQiyas.lean`، لا هنا.

**المبرهنات** (بالمعيار الموحَّد في `Nizam/Asas.lean`)، وهي خواصُّ هذا التعيين على مجاله، لا قوانينُ في اللغة:
- تعريفيّة (11): `bawwaba_la_hukm`، `wa_k3`، `bila_sila`، `silat_al`، `silat_ghayriha`، `ikhtilaf_masdarayn`، `la_aid_khata`، `tashdid_la_yughayyir`،
  `lugha_la_tughayyir`، `qayd_khata`، `khilaf_mawsulOK_amm`. وبرهانُها فكُّ التعريفات وتفكيكُ الحالات.
- لكلّ (5): `jawab_k3` (تستدعي `wa_k3`)، `khata_yakfi` (تستدعي `jawab_k3` و`Nizam.Phi.wa_N`)، `tashdid_ghayr_muthanna` (تستدعي `jawab_k3`)،
  `ghayr_maqbul_bila` (تستدعي مساعدًا خاصًّا: سلامةُ الربط)، `la_qalil` (تستدعي مساعداتٍ خاصّة و`List.mem_filter`).
- على الشاهد (5): `asma_qatr`، `maqam_khass`، `khilaf_mawsulOK`، `khilaf_silaOK`، `shawahid`.
- والأربعُ `khilaf_mawsulOK_amm` و`khilaf_mawsulOK` و`khilaf_silaOK` و`la_qalil` زيدت بعد مراجعة `murajii` الأولى، بلا تغييرٍ في `jawab`.

**حدُّه.** المدخلُ تحليلٌ يُعطى؛ ولا إعرابَ لـ«أي» ولا شروطَ لحذف العائد (س159–165)؛ ولا تفريقَ بين العاقل وغيره؛ و«لا حكم» في الاختلاف لا يحمل
البديلين (هما في `silaQatr` و`silaAlfiyya`)؛ ولا وصلَ بالقارئ ولا بالمحرّك.
-/

namespace Jisr
namespace Mawsul

inductive Lafz
  | alladhi | allati | alladhani | allatani | alladhayni | allatayni | alladhiyani | allatiyani | alladhina | alladhuna
  | alula | allai | allati_j | allat | allaa | man | ma | ayy | al | dhu | dhat | dhawat | dha
  deriving DecidableEq, Repr

/-- اللفظُ كما في المواصفة. -/
def Lafz.nass : Lafz → String
  | .alladhi => "الذي" | .allati => "التي" | .alladhani => "اللذان" | .allatani => "اللتان" | .alladhayni => "اللذين"
  | .allatayni => "اللتين" | .alladhiyani => "اللذيان" | .allatiyani => "اللتيان" | .alladhina => "الذين" | .alladhuna => "اللذون"
  | .alula => "الألى" | .allai => "اللائي" | .allati_j => "اللاتي" | .allat => "اللات" | .allaa => "اللاء" | .man => "من"
  | .ma => "ما" | .ayy => "أي" | .al => "أل" | .dhu => "ذو" | .dhat => "ذات" | .dhawat => "ذوات" | .dha => "ذا"

/-- آخرُه نون. -/
def Lafz.nun : Lafz → Bool
  | .alladhani | .allatani | .alladhayni | .allatayni | .alladhiyani | .allatiyani | .alladhina | .alladhuna => true
  | _ => false

/-- المشترك: لكلّ معنى. -/
def Lafz.mushtarak : Lafz → Bool
  | .man | .ma | .ayy | .al | .dhu | .dha => true
  | _ => false

inductive Sima
  | mufradMudhakkar | mufradMuannath | muthannaMudhakkar | muthannaMuannath | jamMudhakkar | jamMuannath
  deriving DecidableEq, Repr

inductive Mawdi | raf | nasb | jarr
  deriving DecidableEq, Repr

inductive Lugha | ghayrMadhkura | tayyi
  deriving DecidableEq, Repr

inductive Qabl | maIstifham | manIstifham | ghayruhuma
  deriving DecidableEq, Repr

inductive Sila
  | jumlaKhabariyya | jumlaInshaiyya | zarfTamm | zarfNaqis | jarrTamm | jarrNaqis | wasfSarih | ismTafdil | filMurab | laSila
  deriving DecidableEq, Repr

inductive Aid | zahir | mustatir | mahdhuf | laAid
  deriving DecidableEq, Repr

structure Dakhil where
  lafz : Lafz
  marji : Sima
  mawdi : Mawdi
  tashdid : Bool
  lugha : Lugha
  qabl : Qabl
  mulgha : Bool
  sila : Sila
  aid : Aid
  aidSima : Option Sima   -- `none`: «لا عائد»
  deriving DecidableEq, Repr

inductive Hukm | maqbul | khata | laHukm
  deriving DecidableEq, Repr

inductive Daraja | qalil | nazr | lugha | bila
  deriving DecidableEq, Repr

structure Jawab where
  hukm : Hukm
  daraja : List Daraja
  deriving DecidableEq, Repr

def maqbulJ (ds : List Daraja) : Jawab := ⟨.maqbul, ds⟩
def khataJ : Jawab := ⟨.khata, [.bila]⟩
def laHukmJ : Jawab := ⟨.laHukm, [.bila]⟩

/-- اتّساقُ الحقول: التشديدُ في لفظٍ آخرُه نون، و«لا عائد» في العائد وسمتِه معًا. (والإلغاءُ يُردّ «لا حكم» في `jawab` في كلّ لفظ.) -/
def muttasiq (d : Dakhil) : Bool :=
  (!d.tashdid || d.lafz.nun) && (decide (d.aid = .laAid) == d.aidSima.isNone)

/-- المثنّى. -/
def Lafz.muthanna : Lafz → Bool
  | .alladhani | .allatani | .alladhayni | .allatayni | .alladhiyani | .allatiyani => true
  | _ => false

def muthannaM (m : Sima) : Bool := decide (m = .muthannaMudhakkar)
def muthannaF (m : Sima) : Bool := decide (m = .muthannaMuannath)

/-- حكمُ اللفظ بمعناه وموضعه ولغته وما قبله. -/
def lafzJ (d : Dakhil) : Jawab :=
  let yes (b : Bool) : Jawab := if b then maqbulJ [.bila] else khataJ
  match d.lafz with
  | .alladhi => yes (decide (d.marji = .mufradMudhakkar))
  | .allati => yes (decide (d.marji = .mufradMuannath))
  | .alladhani => yes (muthannaM d.marji && decide (d.mawdi = .raf))
  | .allatani => yes (muthannaF d.marji && decide (d.mawdi = .raf))
  | .alladhayni => yes (muthannaM d.marji && decide (d.mawdi ≠ .raf))
  | .allatayni => yes (muthannaF d.marji && decide (d.mawdi ≠ .raf))
  | .alladhiyani | .allatiyani => khataJ
  | .alladhina | .alula => yes (decide (d.marji = .jamMudhakkar))
  | .alladhuna => if decide (d.marji = .jamMudhakkar) && decide (d.mawdi = .raf) then maqbulJ [.lugha] else khataJ
  | .allai | .allati_j | .allat => yes (decide (d.marji = .jamMuannath))
  | .allaa =>
    if decide (d.marji = .jamMuannath) then maqbulJ [.bila]
    else if decide (d.marji = .jamMudhakkar) then maqbulJ [.nazr]
    else khataJ
  | .man | .ma | .ayy | .al => maqbulJ [.bila]
  | .dhu => yes (decide (d.lugha = .tayyi))
  | .dhat => yes (decide (d.lugha = .tayyi) && decide (d.marji = .mufradMuannath))
  | .dhawat => yes (decide (d.lugha = .tayyi) && decide (d.marji = .jamMuannath))
  | .dha => yes (decide (d.qabl ≠ .ghayruhuma))

/-- حكمُ التشديد: «فلا ملامه» في نون المثنّى وحدها، وفي غيرها «لا حكم». -/
def tashdidJ (d : Dakhil) : Jawab :=
  if d.tashdid && !d.lafz.muthanna then laHukmJ else maqbulJ [.bila]

/-- الصلةُ في قطر الندى: لـ«أل» الوصف، ولغيرها الجملةُ الخبريّة والظرفُ والجارُّ التامّان (س139–143). -/
def silaQatr (l : Lafz) (s : Sila) : Jawab :=
  match l, s with
  | .al, .wasfSarih => maqbulJ [.bila]
  | .al, _ => khataJ
  | _, .jumlaKhabariyya | _, .zarfTamm | _, .jarrTamm => maqbulJ [.bila]
  | _, _ => khataJ

/-- الصلةُ في الألفية: لـ«أل» الصفةُ الصريحة، والفعلُ المعرب قليل؛ ولغيرها الجملةُ وشبهُها (س155–157)، و«شبهُها» التامّ. -/
def silaAlfiyya (l : Lafz) (s : Sila) : Jawab :=
  match l, s with
  | .al, .wasfSarih => maqbulJ [.bila]
  | .al, .filMurab => maqbulJ [.qalil]
  | .al, _ => khataJ
  | _, .jumlaKhabariyya | _, .jumlaInshaiyya | _, .zarfTamm | _, .jarrTamm => maqbulJ [.bila]
  | _, _ => khataJ

/-- حكمُ الصلة: ما اتّفق عليه المصدران، وما اختلفا فيه «لا حكم». -/
def silaJ (l : Lafz) (s : Sila) : Jawab :=
  if silaQatr l s = silaAlfiyya l s then silaQatr l s else laHukmJ

/-- حكمُ العائد. -/
def aidJ (d : Dakhil) : Jawab :=
  match d.aid, d.aidSima with
  | .laAid, _ => khataJ
  | _, none => laHukmJ
  | a, some s =>
    if decide (a = .mahdhuf) && !decide (d.sila = .jumlaKhabariyya) then laHukmJ
    else if decide (s = d.marji) then maqbulJ [.bila]
    else if d.lafz.mushtarak && decide (s = .mufradMudhakkar) then laHukmJ
    else khataJ

/-- **ربطُ جوابين** على ربط `Nizam.Phi.K3.wa`: يكفي خطأٌ ليكون الجوابُ خطأً، ولا قبولَ إلّا بقبول الطرفين بدرجاتهما المذكورة، وما سواهما
    «لا حكم». -/
def wa (a b : Jawab) : Jawab :=
  if decide (a.hukm = .khata) || decide (b.hukm = .khata) then khataJ
  else if decide (a.hukm = .maqbul) && decide (b.hukm = .maqbul) then
    let ds := (a.daraja ++ b.daraja).filter (· ≠ .bila)
    maqbulJ (if ds.isEmpty then [.bila] else ds)
  else laHukmJ

/-- **الحكم.** الحقولُ غيرُ المتّسقة و«ذا» الملغاةُ «لا حكم»؛ وإلّا فربطُ أحكام اللفظ والتشديد والصلة والعائد. -/
def jawab (d : Dakhil) : Jawab :=
  if !muttasiq d || d.mulgha then laHukmJ
  else wa (lafzJ d) (wa (tashdidJ d) (wa (silaJ d.lafz d.sila) (aidJ d)))

/-! ## الأسانيد -/

/-- الأسانيد: (القاعدة، المصدر، من سطر، إلى سطر، القطعةُ حرفيّةً بعد وصل الأسطر بمسافة). -/
def asanid : List (String × String × Nat × Nat × String) :=
  [("khass_mufrad", "qatr", 137, 137, "ثم الموصول، وهو الذي والتي،"),
   ("muthanna", "qatr", 137, 138, "واللذان واللتان بالألف رفعا وبالياء جرا ms03 ونصبا،"),
   ("jam_mudhakkar", "qatr", 138, 138, "ولجمع المذكر الذين بالياء مطلقا والألى،"),
   ("jam_muannath", "qatr", 138, 139, "ولجمع المؤنث اللائي واللاتي،"),
   ("mushtarak", "qatr", 139, 139, "وبمعنى الجميع من وما وأي،"),
   ("al", "qatr", 139, 140, "وأل في وصف صريح لغير تفضيل كالضارب والمضروب،"),
   ("dhu", "qatr", 140, 140, "وذو في لغة طي،"),
   ("dha", "qatr", 140, 140, "وذا بعد ما أو من الاستفهاميتين."),
   ("silat_al", "qatr", 140, 140, "وصلة أل الوصف،"),
   ("sila", "qatr", 141, 141, "وصلة غيرها إما جملة خبرية ذات ضمير طبق للموصول يسمى عائدا، وقد يحذف"),
   ("shibh", "qatr", 143, 143, "أو ظرف أو جار ومجرور تامان"),
   ("khass_A", "alfiyya", 147, 147, "موصول الأسماء الذي الأنثى التي ... واليا إذا ما ثنيا لا تثبت"),
   ("tashdid", "alfiyya", 148, 148, "والنون إن تشدد فلا ملامه"),
   ("jam_A", "alfiyya", 150, 150, "جمع الذى الألى الذين مطلقا ... وبعضهم بالواو رفعا نطقا"),
   ("jam_muannath_A", "alfiyya", 151, 151, "باللات واللاء التي قد جمعا ... واللاء كالذين نزرا وقعا"),
   ("mushtarak_A", "alfiyya", 152, 152, "ومن وما وأل تساوي ما ذكره ... وهكذا ذو عند طيئ شهر"),
   ("dhat", "alfiyya", 153, 153, "وكالتي أيضا لديهم ذات ... وموضع اللاتي أتى ذوات"),
   ("dha_A", "alfiyya", 154, 154, "ومثل ماذا بعدما استفهام ... أومن إذا لم تلغ في الكلام"),
   ("sila_lazima", "alfiyya", 155, 155, "وكلها يلزم ms03 بعده صله ... على ضمير لائق مشتمله"),
   ("shibh_A", "alfiyya", 156, 156, "وجملة أو شبهها الذي وصل"),
   ("al_A", "alfiyya", 157, 157, "وصفة صريحة صلة أل ... وكونها بمعرب الأفعال قل")]

/-! ## المبرهنات -/

/-- **الحقولُ غيرُ المتّسقة و«ذا» الملغاةُ «لا حكم».** -/
theorem bawwaba_la_hukm (d : Dakhil) (h : muttasiq d = false ∨ d.mulgha = true) : jawab d = laHukmJ := by
  rcases h with h | h <;> simp [jawab, h]

/-- مقابلةُ الحكم بقيم `Nizam.Phi.K3`: المقبولُ مرخَّص، والخطأُ ممتنع، و«لا حكم» لا حكم. -/
def Hukm.k3 : Hukm → Nizam.Phi.K3
  | .maqbul => .P
  | .khata => .N
  | .laHukm => .U

/-- **الربطُ هو `Nizam.Phi.K3.wa`** على الأحكام. -/
theorem wa_k3 (a b : Jawab) : (wa a b).hukm.k3 = Nizam.Phi.K3.wa a.hukm.k3 b.hukm.k3 := by
  obtain ⟨x, _⟩ := a; obtain ⟨y, _⟩ := b
  cases x <;> cases y <;> simp [wa, Hukm.k3, Nizam.Phi.K3.wa, khataJ, laHukmJ, maqbulJ] <;> split <;> rfl

/-- **الجوابُ ربطُ الأحكام الأربعة** على `Nizam.Phi.K3.wa`، في الحقول المتّسقة بلا إلغاء. -/
theorem jawab_k3 (d : Dakhil) (hm : muttasiq d = true) (hg : d.mulgha = false) :
    (jawab d).hukm.k3 = Nizam.Phi.K3.wa (lafzJ d).hukm.k3
      (Nizam.Phi.K3.wa (tashdidJ d).hukm.k3 (Nizam.Phi.K3.wa (silaJ d.lafz d.sila).hukm.k3 (aidJ d).hukm.k3)) := by
  simp [jawab, hm, hg, wa_k3]

/-- **يكفي خطأٌ في أحد الأربعة ليكون الجوابُ خطأً**، في الحقول المتّسقة بلا إلغاء. -/
theorem khata_yakfi (d : Dakhil) (hm : muttasiq d = true) (hg : d.mulgha = false)
    (h : (lafzJ d).hukm = .khata ∨ (tashdidJ d).hukm = .khata ∨ (silaJ d.lafz d.sila).hukm = .khata ∨ (aidJ d).hukm = .khata) :
    (jawab d).hukm = .khata := by
  have hk := jawab_k3 d hm hg
  have e : ∀ x : Hukm, x.k3 = .N ↔ x = .khata := by intro x; cases x <;> simp [Hukm.k3]
  rw [← e, hk]
  simpa [Nizam.Phi.wa_N, e] using h

/-- **لا موصولَ بلا صلة** في المصدرين. -/
theorem bila_sila (l : Lafz) : silaJ l .laSila = khataJ := by
  cases l <;> rfl

/-- **صلةُ «أل»:** الوصفُ الصريح، والفعلُ المعرب «لا حكم» (القطر يردّه والألفية تقبله قليلًا)، وما سواهما خطأ. -/
theorem silat_al (s : Sila) :
    silaJ .al s = (if s = .wasfSarih then maqbulJ [.bila] else if s = .filMurab then laHukmJ else khataJ) := by
  cases s <;> rfl

/-- **وصلةُ غيرها** الجملةُ الخبريّةُ والظرفُ والجارُّ التامّان، والإنشائيّةُ «لا حكم» (القطر يردّها والألفية تطلق «جملة»)، وما سواها خطأ. -/
theorem silat_ghayriha (l : Lafz) (s : Sila) (hl : l ≠ .al) :
    silaJ l s = (if s = .jumlaKhabariyya ∨ s = .zarfTamm ∨ s = .jarrTamm then maqbulJ [.bila]
      else if s = .jumlaInshaiyya then laHukmJ else khataJ) := by
  cases l <;> cases s <;> simp_all [silaJ, silaQatr, silaAlfiyya, khataJ, maqbulJ, laHukmJ]

/-- **ما اختلف فيه المصدران** في الصلة، بقراءة كلٍّ منهما. -/
theorem ikhtilaf_masdarayn (l : Lafz) (hl : l ≠ .al) :
    silaQatr .al .filMurab = khataJ ∧ silaAlfiyya .al .filMurab = maqbulJ [.qalil] ∧
    silaQatr l .jumlaInshaiyya = khataJ ∧ silaAlfiyya l .jumlaInshaiyya = maqbulJ [.bila] := by
  cases l <;> simp_all [silaQatr, silaAlfiyya]

/-- **لا صلةَ بلا عائد.** -/
theorem la_aid_khata (d : Dakhil) (h : d.aid = .laAid) : aidJ d = khataJ := by
  simp [aidJ, h]

/-- **التشديدُ لا يغيّر الجواب في المثنّى** («فلا ملامه»). -/
theorem tashdid_la_yughayyir (d : Dakhil) (h : d.lafz.muthanna = true) :
    jawab { d with tashdid := true } = jawab { d with tashdid := false } := by
  have hn : d.lafz.nun = true := by
    obtain ⟨lf, _⟩ := d; cases lf <;> simp_all [Lafz.muthanna, Lafz.nun]
  simp [jawab, muttasiq, h, hn, lafzJ, aidJ, silaJ, tashdidJ]

/-- **وتشديدُ غير المثنّى لا يُقبل:** خطأٌ أو «لا حكم». -/
theorem tashdid_ghayr_muthanna (d : Dakhil) (ht : d.tashdid = true) (h : d.lafz.muthanna = false) :
    (jawab d).hukm ≠ .maqbul := by
  intro hq
  by_cases hg : (!muttasiq d || d.mulgha) = true
  · simp [jawab, hg, laHukmJ] at hq
  · have hm : muttasiq d = true := by cases h1 : muttasiq d <;> simp_all
    have hl : d.mulgha = false := by cases h1 : d.mulgha <;> simp_all
    have hk := jawab_k3 d hm hl
    have ht' : (tashdidJ d).hukm = .laHukm := by simp [tashdidJ, ht, h, laHukmJ]
    rw [hq, ht'] at hk
    have hU : ∀ x y : Nizam.Phi.K3, Nizam.Phi.K3.wa x (Nizam.Phi.K3.wa .U y) ≠ .P := by
      intro x y; cases x <;> cases y <;> decide
    exact hU _ _ hk.symm

/-- **اللغةُ لا تغيّر إلّا «ذو» و«ذات» و«ذوات».** -/
theorem lugha_la_tughayyir (d : Dakhil) (l : Lugha) (h : d.lafz ≠ .dhu ∧ d.lafz ≠ .dhat ∧ d.lafz ≠ .dhawat) :
    jawab { d with lugha := l } = jawab d := by
  obtain ⟨lf, m, w, t, lg, q, ml, s, a, as⟩ := d
  simp only at h
  cases lf <;> simp_all [jawab, muttasiq, lafzJ, aidJ, silaJ, tashdidJ]

/-- **القيدُ وما خرج عنه:** «ذو» و«ذات» و«ذوات» في غير طيئ، و«ذا» في غير ما بعد «ما» و«من» الاستفهاميّتين، خطأ. -/
theorem qayd_khata (d : Dakhil) :
    ((d.lafz = .dhu ∨ d.lafz = .dhat ∨ d.lafz = .dhawat) → d.lugha ≠ .tayyi → lafzJ d = khataJ) ∧
    (d.lafz = .dha → d.qabl = .ghayruhuma → lafzJ d = khataJ) := by
  obtain ⟨lf, m, w, t, lg, q, ml, s, a, as⟩ := d
  constructor
  · rintro (h | h | h) hl <;> subst h <;> simp_all [lafzJ]
  · rintro h hq; subst h; subst hq; simp [lafzJ]

private theorem lafzJ_la_qalil (d : Dakhil) : Daraja.qalil ∉ (lafzJ d).daraja := by
  obtain ⟨lf, m, w, t, lg, q, ml, s, a, as⟩ := d
  cases lf <;> simp only [lafzJ] <;> (repeat' split) <;> simp [maqbulJ, khataJ]

private theorem silaJ_la_qalil (l : Lafz) (s : Sila) : Daraja.qalil ∉ (silaJ l s).daraja := by
  cases l <;> cases s <;> simp [silaJ, silaQatr, silaAlfiyya, maqbulJ, khataJ, laHukmJ]

private theorem aidJ_la_qalil (d : Dakhil) : Daraja.qalil ∉ (aidJ d).daraja := by
  obtain ⟨lf, m, w, t, lg, q, ml, s, a, as⟩ := d
  simp only [aidJ]; (repeat' split) <;> simp [maqbulJ, khataJ, laHukmJ]

private theorem tashdidJ_la_qalil (d : Dakhil) : Daraja.qalil ∉ (tashdidJ d).daraja := by
  simp only [tashdidJ]; split <;> simp [maqbulJ, laHukmJ]

private theorem wa_la_qalil (a b : Jawab) (ha : Daraja.qalil ∉ a.daraja) (hb : Daraja.qalil ∉ b.daraja) :
    Daraja.qalil ∉ (wa a b).daraja := by
  unfold wa
  split
  · simp [khataJ]
  · split
    · simp only [maqbulJ]
      split
      · simp
      · intro hm
        rcases List.mem_append.mp (List.mem_filter.mp hm).1 with h | h
        · exact ha h
        · exact hb h
    · simp [laHukmJ]

/-- **`jawab` لا يُخرج «قليل»:** «قليل» في الألفية لصلة «أل» فعلًا معربًا وحدها، وهي «لا حكم» لاختلاف المصدرين. -/
theorem la_qalil (d : Dakhil) : Daraja.qalil ∉ (jawab d).daraja := by
  unfold jawab
  split
  · simp [laHukmJ]
  · exact wa_la_qalil _ _ (lafzJ_la_qalil d) (wa_la_qalil _ _ (tashdidJ_la_qalil d)
      (wa_la_qalil _ _ (silaJ_la_qalil _ _) (aidJ_la_qalil d)))

/-- جوابٌ سليم: ما ليس مقبولًا فدرجتُه `[bila]`. -/
def Jawab.salim (j : Jawab) : Prop := j.hukm ≠ .maqbul → j.daraja = [.bila]

private theorem wa_salim (a b : Jawab) : (wa a b).salim := by
  unfold wa Jawab.salim
  repeat' split <;> simp_all [khataJ, laHukmJ, maqbulJ]

/-- **ما ليس مقبولًا فدرجتُه `[bila]`.** -/
theorem ghayr_maqbul_bila (d : Dakhil) (h : (jawab d).hukm ≠ .maqbul) : (jawab d).daraja = [.bila] := by
  have hs : (jawab d).salim := by
    unfold jawab
    split
    · simp [Jawab.salim, laHukmJ]
    · exact wa_salim _ _
  exact hs h

/-! ## الصلة بـ SLGE -/

def lafzat : List Lafz :=
  [.alladhi, .allati, .alladhani, .allatani, .alladhayni, .allatayni, .alladhiyani, .allatiyani, .alladhina, .alladhuna,
   .alula, .allai, .allati_j, .allat, .allaa, .man, .ma, .ayy, .al, .dhu, .dhat, .dhawat, .dha]

/-- اللفظُ من نصّه. -/
def lafzMin (s : String) : Option Lafz := lafzat.find? (·.nass == s)

/-- **ألفاظُ `SLGE.Wad.mawsul` ألفاظٌ هنا، و«الموصول» رابعةُ `SLGE.Wad.maarif`.** -/
theorem asma_qatr :
    SLGE.Wad.mawsul.all (fun s => (lafzMin s).isSome) = true ∧ SLGE.Wad.maarif[3]? = some "الموصول" := by
  decide

/-- المعنى من سمة المالك (الشخصُ غائب، والجنسُ 0 مذكّر و1 مؤنّث، والعددُ 0 و1 و2). -/
def simaMin : SLGE.Maqam.Feat → Option Sima
  | (3, 0, 0) => some .mufradMudhakkar
  | (3, 1, 0) => some .mufradMuannath
  | (3, 0, 1) => some .muthannaMudhakkar
  | (3, 1, 1) => some .muthannaMuannath
  | (3, 0, 2) => some .jamMudhakkar
  | (3, 1, 2) => some .jamMuannath
  | _ => none

/-- **كلُّ لفظٍ في `SLGE.Maqam.mawsulKhass` مقبولٌ هنا لمعنى سمته**، رفعًا، بصلةٍ خبريّةٍ وعائدٍ مستترٍ يوافقه. -/
theorem maqam_khass :
    SLGE.Maqam.mawsulKhass.all (fun x => match lafzMin x.1, simaMin x.2 with
      | some l, some m => jawab ⟨l, m, .raf, false, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .mustatir, some m⟩ ==
          maqbulJ [.bila]
      | _, _ => false) = true := by
  decide

/-- **خلافٌ مع `SLGE.TarkibExt.mawsulOK`:** لا يرخّص صلةً إطارُها شبهُ جملة، في أيّ سمةٍ وعائد؛ وفي إطارات المالك إطاران من شبه الجملة. -/
theorem khilaf_mawsulOK_amm (mf : SLGE.Maqam.Feat) (sila : SLGE.Tarkib.Frame) (k : Nat) (af : SLGE.Maqam.Feat) (h : sila.1 = 2) :
    SLGE.TarkibExt.mawsulOK mf sila k af = false := by
  simp [SLGE.TarkibExt.mawsulOK, h]

/-- **والقطر يقبل الظرفَ والجارَّ التامّين صلةً، وكذلك `jawab`.** -/
theorem khilaf_mawsulOK :
    (SLGE.Tarkib.framesL.filter (·.1 == 2)).length = 2 ∧
    jawab ⟨.alladhi, .mufradMudhakkar, .raf, false, .ghayrMadhkura, .ghayruhuma, false, .jarrTamm, .mustatir,
      some .mufradMudhakkar⟩ = maqbulJ [.bila] ∧
    jawab ⟨.alladhi, .mufradMudhakkar, .raf, false, .ghayrMadhkura, .ghayruhuma, false, .zarfTamm, .mustatir,
      some .mufradMudhakkar⟩ = maqbulJ [.bila] := by
  decide +kernel

/-- **خلافٌ مع `SLGE.Maqam.silaOK`:** «من» المشتركة (سمتُها عند المالك (3، 2، 0)) تقبل عائدًا مفردًا مؤنّثًا؛ و`jawab` يردّه لـ«من» بمعنى جمع
    المؤنّث، لأنّه يخالف معناها ولفظَها معًا. -/
theorem khilaf_silaOK :
    SLGE.Maqam.silaOK (3, 2, 0) (3, 1, 0) 0 = true ∧
    jawab ⟨.man, .jamMuannath, .raf, false, .ghayrMadhkura, .ghayruhuma, false, .jumlaKhabariyya, .mustatir,
      some .mufradMuannath⟩ = khataJ := by
  decide

/-- **الشواهد:** مدخلاتٌ مبنيّة، منها مثالُ القطر س139–140 («كالضارب والمضروب»: «أل» بوصفٍ صريح)؛ وبعضُها زيد بعد قراءة الحالات لقتل طفراتٍ
    حيّة (`5b34f6d`). -/
theorem shawahid :
    let d (l : Lafz) (m : Sima) (w : Mawdi) (s : Sila) : Dakhil := ⟨l, m, w, false, .ghayrMadhkura, .ghayruhuma, false, s, .mustatir, some m⟩
    jawab (d .alladhi .mufradMudhakkar .raf .jumlaKhabariyya) = maqbulJ [.bila] ∧
    jawab (d .allati .mufradMudhakkar .raf .jumlaKhabariyya) = khataJ ∧
    jawab (d .alladhayni .muthannaMudhakkar .raf .jumlaKhabariyya) = khataJ ∧
    jawab (d .alladhayni .muthannaMudhakkar .jarr .jumlaKhabariyya) = maqbulJ [.bila] ∧
    jawab { d .alladhani .muthannaMudhakkar .raf .jumlaKhabariyya with tashdid := true } = maqbulJ [.bila] ∧
    jawab (d .alladhiyani .muthannaMudhakkar .raf .jumlaKhabariyya) = khataJ ∧
    jawab (d .alladhina .jamMudhakkar .nasb .jumlaKhabariyya) = maqbulJ [.bila] ∧
    jawab (d .alladhuna .jamMudhakkar .raf .jumlaKhabariyya) = maqbulJ [.lugha] ∧
    jawab (d .alladhuna .jamMudhakkar .jarr .jumlaKhabariyya) = khataJ ∧
    jawab (d .allaa .jamMudhakkar .raf .jumlaKhabariyya) = maqbulJ [.nazr] ∧
    jawab (d .man .jamMuannath .raf .jumlaKhabariyya) = maqbulJ [.bila] ∧
    jawab (d .al .mufradMudhakkar .raf .wasfSarih) = maqbulJ [.bila] ∧
    jawab (d .al .mufradMudhakkar .raf .ismTafdil) = khataJ ∧
    jawab (d .al .mufradMudhakkar .raf .filMurab) = laHukmJ ∧
    jawab (d .al .mufradMudhakkar .raf .jumlaKhabariyya) = khataJ ∧
    jawab (d .dhu .mufradMudhakkar .raf .jumlaKhabariyya) = khataJ ∧
    jawab { d .dhu .mufradMudhakkar .raf .jumlaKhabariyya with lugha := .tayyi } = maqbulJ [.bila] ∧
    jawab { d .dhat .mufradMuannath .raf .jumlaKhabariyya with lugha := .tayyi } = maqbulJ [.bila] ∧
    jawab { d .dha .mufradMudhakkar .raf .jumlaKhabariyya with qabl := .maIstifham } = maqbulJ [.bila] ∧
    jawab { d .dha .mufradMudhakkar .raf .jumlaKhabariyya with qabl := .maIstifham, mulgha := true } = laHukmJ ∧
    jawab (d .dha .mufradMudhakkar .raf .jumlaKhabariyya) = khataJ ∧
    jawab { d .alladhi .mufradMudhakkar .raf .jumlaKhabariyya with mulgha := true } = laHukmJ ∧
    jawab { d .dhat .mufradMudhakkar .raf .jumlaKhabariyya with lugha := .tayyi } = khataJ ∧
    jawab { d .alladhina .jamMudhakkar .nasb .jumlaKhabariyya with tashdid := true } = laHukmJ ∧
    jawab { d .alladhi .mufradMudhakkar .raf .jumlaKhabariyya with tashdid := true } = laHukmJ ∧
    jawab { d .alladhi .mufradMudhakkar .raf .jumlaKhabariyya with tashdid := true, aidSima := some .mufradMuannath } = laHukmJ ∧
    jawab { d .allatayni .muthannaMuannath .jarr .jumlaKhabariyya with tashdid := true } = maqbulJ [.bila] ∧
    jawab (d .alladhi .mufradMudhakkar .raf .jumlaInshaiyya) = laHukmJ ∧
    jawab { d .alladhi .mufradMudhakkar .raf .jumlaInshaiyya with aidSima := some .mufradMuannath } = khataJ ∧
    jawab (d .alladhi .mufradMudhakkar .raf .zarfTamm) = maqbulJ [.bila] ∧
    jawab (d .alladhi .mufradMudhakkar .raf .zarfNaqis) = khataJ ∧
    jawab (d .alladhi .mufradMudhakkar .raf .laSila) = khataJ ∧
    jawab { d .alladhi .mufradMudhakkar .raf .jumlaKhabariyya with aid := .laAid, aidSima := none } = khataJ ∧
    jawab { d .alladhi .mufradMudhakkar .raf .jumlaKhabariyya with aid := .mahdhuf } = maqbulJ [.bila] ∧
    jawab { d .alladhi .mufradMudhakkar .raf .zarfTamm with aid := .mahdhuf } = laHukmJ ∧
    jawab { d .alladhi .mufradMudhakkar .raf .jumlaKhabariyya with aid := .laAid } = laHukmJ ∧
    jawab { d .alladhi .mufradMudhakkar .raf .jumlaKhabariyya with aidSima := some .mufradMuannath } = khataJ ∧
    jawab { d .man .jamMuannath .raf .jumlaKhabariyya with aidSima := some .mufradMudhakkar } = laHukmJ := by
  decide

end Mawsul
end Jisr
