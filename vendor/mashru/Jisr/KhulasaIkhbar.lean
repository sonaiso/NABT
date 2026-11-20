/-
  Jisr/KhulasaIkhbar.lean — خلاصةُ أسلوب الإخبار: الثمانيةُ بنودٍ الباقيةُ في `Jisr/حصر_الإخبار_والعوامل.md` (السطر 48–56)،
  جردًا حاصرًا لا يُضمّ إليه بندٌ تاسع (`bund_thamaniya`)، وكلُّ بندٍ فيه حالتُه الآن (`Hala`) قابلةٌ للتحديث دون تغيير
  الجردِ نفسِه — وهذا معنى «نبقيها قابلة لإضافةِ تفاصيلَ لاحقًا» (قولُ المالك 2026-10-17، ردًّا على سؤال تحديد
  «المرحلة التالية لأساليب الإخبار»؛ اختار «الثمانية كلّها»).

  **السند.** حصرُ البنود الثمانية بأسمائها وأسطرها من `Jisr/حصر_الإخبار_والعوامل.md` نفسِه، المقروء كاملًا في الجلسة
  (قُرئ قبل كتابة هذا الملفّ). ونصُّ قطر الندى لكلّ بندٍ مقروءٌ هو أيضًا في الجلسة من `qatr.txt` (مودَع مختوم، L41–452)
  لا منقولًا من ذاك الحصر وحده.

  **تصحيحٌ على الحصر** (وُجد في هذه الجلسة، قبل أن يُبنى عليه شيء): البندُ (٥) «الإعرابُ بالحروف والتقديرُ وما لا
  ينصرف» **مستوفًى فعلًا** بـ `Jisr/JisrDal.lean` (مدموجٌ main، PR #23، 22 مبرهنة) — والحصرُ نفسُه أقدمُ من ذلك
  الدمج فلم يُحدَّث. وكذلك «صورةُ المجهول في الدالّ» من البند (٨) مستوفاةٌ بالملفّ نفسِه (`majhul_huruf`,
  `majhul_tul`, `majhul_dun_116`, `majhul_marfud`, `shawahid_majhul`, `intilaq_wasl`). البندان الباقيان من (٨)
  — اختصاصُ حروف الجرّ بالظاهر، وما لا يجامع الإضافة — لم يستوفِهما ذاك الملفّ (شأنُهما طبقةُ العامل والمعمول
  على الكلمة، لا جسرَ الإعراب وحده) فبُني أحدُهما هنا.

  **الوسم.** 18 مبرهنةً كلُّها «مبرهن على الشاهد» (`decide` على قوائم صريحة محدودة؛ 15 منها حكمٌ على بندٍ من
  الثمانية [٢: 1، ٣: 2، ٤: 1، ٦: 4، ٧: 4، ٨: 3]، و3 حقائقُ بنيويّةٌ عن الجردِ نفسِه `Bund.all`/`halaOf`
  [`bund_thamaniya`, `bund_mutamayiza`, `tasnif_al_bunud_tamm`]). ولا «مبرهن» عامّ في هذا الملفّ: كلُّ حكمٍ
  هنا على بندٍ محدودٍ بالعدّ من قطر، فحقُّه «على الشاهد» لا «لكلّ» (`Mawsua.Wasm.tartib`).

  **ما بُني هنا من كلّ بندٍ مفتوح** (البنود (٢)(٣)(٤)(٦)(٧)(٨) جزئيًّا؛ انظر `halaOf` لكلّ بندٍ وتفصيله):
  - (٢) إلغاءُ ظنّ برجحان موقع فعلها من مفعوليها (القطر L212–214).
  - (٣) مواضعُ وجوب حذف الخبر الأربعة (القطر L165–167).
  - (٤) جوازُ الوجهين في تأنيث الفعل مع فاعله، وجمعا التصحيح وحدهما بلا جواز (القطر L222–230)؛ أمّا ترتيبُ الفاعل
    مع المفعول فبُني على فرعٍ آخر (`jisr/tartib-mamul`) لم يُدمَج بعدُ في main — لا يُستشهَد به هنا كمستوفًى.
  - (٦) قرنُ جواب الشرط بالفاء أو بإذا الفجائية إذا لم يصلح لمباشرة الأداة (القطر L119–121)؛ وعدُّ عوامل جوازم
    الفعلين الغائبة عن جدول المئة عدًّا مباشرًا على `Jisr.Awamil.table` (تصحيحٌ لعدِّ الحصر: انظر أدناه).
  - (٧) تأخيرُ اللقب عن الاسم وحالتاه (تابعٌ مطلقًا، أو مخفوضٌ بالإضافة إن أُفرد اللقبُ) (القطر L129–131).
  - (٨) اختصاصُ سبعةِ أحرفِ جرٍّ بالظاهر دون الضمير، من `SLGE.Wad.jarrF` نفسِه بعدّ سطريه 338/339 (القطر L337–339).

  **البندُ (١) وبقيّةُ المعنويّين في (٤) و(٦):** عوامل خارج جدول المئة (ما/لا/لات الحجازيات، لا النافية للجنس،
  غير/سوى/ليس/لا يكون، نعم وبئس، وبعضُ جوازم الفعلين) تحتاج قرارَ المالك بإلحاقها بالجدول المودَع أو ببناء جدولٍ
  ثانٍ (نصُّ الحصر نفسِه، البند ٢.١) — لم يُعطَ هذا القرارُ بعدُ، فلا بناءَ عليها هنا (`yantaziruQararAlMalik`).

  **تعيينُ البنّاء** (يُعرض على المالك): «المنفصلُ» في تأنيث الفاعل قُيِّس على نصّ القطر فقط (الحقيقيُّ المنفصل
  والمجازيُّ الظاهر وجمعُ غيرِ التصحيح وبابُ نعم وبئس المتصل) بلا توسيعٍ بالقياس على نظائر غير مذكورة؛ وعدُّ
  البند (١) على **أسماء** `Jisr.Awamil.table` كما ورد نصُّها في القطر L115 بلا تشكيل (فروقُ التشكيل بين "إنْ"
  هناك و"إن" في متن القطر لم تُطابَق حرفيًّا، فالنتيجة حرفيّةٌ لا صوتيّة: انظر الشاهد).
-/
import Jisr.AwamilJadwal
import SLGE.Wad

namespace Jisr
namespace KhulasaIkhbar

open SLGE.Wad

/-! ### ١. الجردُ الثمانيُّ وحالاتُه -/

/-- الثمانيةُ بنودٍ من «خلاصة الإخبار» (`حصر_الإخبار_والعوامل.md` السطر 48–56)، بترتيبها هناك. -/
inductive Bund
  | amilGhairMia       -- ١: عواملُ القطر الغائبةُ عن جدول المئة
  | nawasikhDakhiliyya -- ٢: أحكامُ النواسخ الداخلية
  | mubtadaKhabar      -- ٣: أحكامُ المبتدأ والخبر
  | faail              -- ٤: الفاعل
  | irabWaTaqdir       -- ٥: الإعرابُ بالحروف والتقديرُ وما لا ينصرف
  | shartWaIdhmar      -- ٦: شروطُ إضمار أنْ وأدواتُ الشرط وقرنُ الجواب
  | maarif             -- ٧: المعارف
  | majhulWaJarr       -- ٨: صورةُ المجهول واختصاصُ حروف الجرّ وما لا يجامع الإضافة
  deriving DecidableEq, Repr

def Bund.all : List Bund :=
  [.amilGhairMia, .nawasikhDakhiliyya, .mubtadaKhabar, .faail,
   .irabWaTaqdir, .shartWaIdhmar, .maarif, .majhulWaJarr]

/-- حالةُ بندٍ: مستوفًى بملفٍّ آخر مدموج، أو منتظرٌ قرارًا لم يُعطَ، أو جزءٌ بُني هنا وجزءٌ باقٍ باسمه. -/
inductive Hala
  | mustawfa (masdar : String)
  | yantaziruQararAlMalik (sabab : String)
  | juzzi (mabni baqiya : String)
  deriving Repr

def halaOf : Bund → Hala
  | .amilGhairMia => .yantaziruQararAlMalik
      "إلحاقُ عوامل القطر الغائبة بجدول المئة المودَع، أو بناءُ جدولٍ ثانٍ — نصُّ الحصر ٢.١؛ لم يُعطَ المالك قرارَه"
  | .nawasikhDakhiliyya => .juzzi
      "ilghaZannBimawqi (إلغاءُ ظنّ برجحان موقع فعلها، 3 مواقع)"
      "كان: التمامُ والزيادةُ وتوسّطُ الخبر وحذفُ النون؛ إنّ: المخفّفاتُ وما الكافّةُ وكسرُها ولامُ الابتداء"
  | .mubtadaKhabar => .juzzi
      "asbabWujubHadhfAlKhabar (مواضعُ وجوب حذف الخبر الأربعة)"
      "تعدّدُ الخبر، ومسوّغاتُ النكرة بالعموم والتخصيص (والوصفُ المعتمدُ يُغني عن الخبر بُني في Jisr/Khabar.lean على ضابطٍ مجمَّد)"
  | .faail => .juzzi
      "hukmTanithFaail (جوازُ الوجهين في تأنيث الفعل مع فاعله)؛ وترتيبُه مع المفعول بُني على فرعٍ آخر \
      (jisr/tartib-mamul) لم يُدمَج بعدُ"
      "نعم وبئس (خارجَ جدول المئة؛ ينتظر قرارَ المالك كالبند ١)"
  | .irabWaTaqdir => .mustawfa "Jisr/JisrDal.lean، مدموجٌ main (PR #23)؛ 22 مبرهنة"
  | .shartWaIdhmar => .juzzi
      "suwarQarnAlJawab (قرنُ جواب الشرط بالفاء أو بإذا الفجائية)؛ وعدُّ الغائب عن جدول المئة من جوازم \
      الفعلين (ghaibunAnAlJadwalL115)"
      "شروطُ إضمار أنْ بتفصيلها (لام الجحود، حتى، فاء السببية وواو المعية)؛ وأدواتُ الشرط الغائبةُ عن المئة \
      تحتاج قرارَ المالك كالبند ١"
  | .maarif => .juzzi
      "rutbatAlLaqab (تأخيرُ اللقب عن الاسم، وحالتاه: تابعٌ أو مخفوضٌ بالإضافة)"
      "الضميرُ اتصالًا وانفصالًا، وصلةُ الموصول وعائدُها، وأنواعُ أل الثلاثة حكمًا"
  | .majhulWaJarr => .juzzi
      "ikhtisasBizahir على SLGE.Wad.jarrF (اختصاصُ سبعةِ أحرفِ جرٍّ بالظاهر)؛ وصورةُ المجهول مستوفاةٌ \
      (Jisr/JisrDal.lean)"
      "ما لا يجامع الإضافة: التنوينُ والنونُ وأل (القطر L343)"

theorem bund_thamaniya : Bund.all.length = 8 := by decide
theorem bund_mutamayiza : Bund.all.Nodup := by decide

/-! ### ٢. البندُ (٢) — إلغاءُ ظنّ برجحان الموقع (القطر L212–214) -/

/-- موقعُ فعل ظنّ من مفعوليه. القطر L212–214: «ويلغين برجحان إن تأخرن ... وبمساواة إن توسطن» — والتقدّمُ
    (الترتيبُ الأصليّ) لم يُذكر فالإعمالُ هو الأصلُ فيه، فلا إلغاءَ. -/
inductive MawqiFiilZann
  | qablAlMafulayn   -- الفعلُ قبل مفعوليه (الأصل)
  | baynaAlMafulayn  -- الفعلُ بينهما (توسّط)
  | baadAlMafulayn   -- الفعلُ بعدهما (تأخّر)
  deriving DecidableEq, Repr

def MawqiFiilZann.all : List MawqiFiilZann := [.qablAlMafulayn, .baynaAlMafulayn, .baadAlMafulayn]

inductive DarajatIlgha
  | mumtani | musawin | rajihun
  deriving DecidableEq, Repr

def ilghaZannBimawqi : MawqiFiilZann → DarajatIlgha
  | .qablAlMafulayn => .mumtani
  | .baynaAlMafulayn => .musawin
  | .baadAlMafulayn => .rajihun

/-- المواقعُ الثلاثةُ تُفضي إلى درجاتٍ ثلاثٍ متمايزة (لا يتساوى موقعان في حكم إلغاء ظنّ). -/
theorem darajat_ilgha_thalath_mukhtalifa :
    (MawqiFiilZann.all.map ilghaZannBimawqi).Nodup := by decide

/-! ### ٣. البندُ (٣) — وجوبُ حذف الخبر (القطر L165–167) -/

/-- أسبابُ وجوب حذف الخبر الأربعةُ، بلفظ القطر. -/
inductive SababWujubHadhfKhabar
  | jawabLawla | jawabQasamSarih | halMumtanaKhabar | wawMusahabaSariha
  deriving DecidableEq, Repr

def SababWujubHadhfKhabar.all : List SababWujubHadhfKhabar :=
  [.jawabLawla, .jawabQasamSarih, .halMumtanaKhabar, .wawMusahabaSariha]

/-- شاهدُ كلّ سببٍ، بلفظ القطر L165–167. -/
def shahidWujub : SababWujubHadhfKhabar → String
  | .jawabLawla => "لولا أنتم لكنا مؤمنين"
  | .jawabQasamSarih => "لعمرك لأفعلن"
  | .halMumtanaKhabar => "وضربي زيدا قائما"
  | .wawMusahabaSariha => "كل رجل وضيعته"

theorem arbaa_asbab : SababWujubHadhfKhabar.all.length = 4 := by decide

/-- شواهدُ الأسباب الأربعة مستقلّةٌ بعضُها عن بعض (لا تكرار). -/
theorem shawahid_arbaa_mustaqilla :
    (SababWujubHadhfKhabar.all.map shahidWujub).Nodup := by decide

/-! ### ٤. البندُ (٤) — جوازُ الوجهين في تأنيث الفاعل (القطر L222–230) -/

/-- سياقُ الفاعل المؤنّث الذي تلحق فعلَه علامةُ تأنيثٍ، بلفظ القطر L222–230. -/
inductive SiyaqTanithFaail
  | haqiqiMuttasilGhairNimaBisa  -- "قامت هند" — خارجَ نعم وبئس
  | majaziZahirAltanith          -- "جاءتكم موعظة"
  | haqiqiMunfasil               -- "حضرت القاضي امرأة"
  | nimaBisaMuttasil             -- "نعمت المرأة هند"
  | jamGhairTashih               -- "قالت الأعراب"
  | jamTashihMudhakkar           -- "قام الزيدون"
  | jamTashihMuannath            -- "قامت الهندات"
  | ghairMuannath                -- الفاعلُ غيرُ مؤنّث
  deriving DecidableEq, Repr

def SiyaqTanithFaail.all : List SiyaqTanithFaail :=
  [.haqiqiMuttasilGhairNimaBisa, .majaziZahirAltanith, .haqiqiMunfasil, .nimaBisaMuttasil,
   .jamGhairTashih, .jamTashihMudhakkar, .jamTashihMuannath, .ghairMuannath]

inductive HukmTanith
  | wajibMuthbat | wajibManfi | jaizWajhan
  deriving DecidableEq, Repr

/-- حكمُ تأنيث فعل الفاعل: جمعا التصحيح «كمفرديهما» (وجوبٌ لا جواز)، وما عداهما من مواضع الجواز الأربعة
    جائزٌ الوجهان، والحقيقيُّ المتصلُ خارجَ هذه المواضع واجبُ التأنيث، وغيرُ المؤنّث لا تلحقه العلامة. -/
def hukmTanithFaail : SiyaqTanithFaail → HukmTanith
  | .haqiqiMuttasilGhairNimaBisa => .wajibMuthbat
  | .majaziZahirAltanith => .jaizWajhan
  | .haqiqiMunfasil => .jaizWajhan
  | .nimaBisaMuttasil => .jaizWajhan
  | .jamGhairTashih => .jaizWajhan
  | .jamTashihMudhakkar => .wajibManfi
  | .jamTashihMuannath => .wajibMuthbat
  | .ghairMuannath => .wajibManfi

/-- جمعا التصحيح وحدهما بلا جوازِ الوجهين (القطر L226: «إلا جمعي التصحيح فكمفرديهما»). -/
theorem jamay_tashih_bila_jawaz :
    ∀ s ∈ SiyaqTanithFaail.all, hukmTanithFaail s = .jaizWajhan →
      s ≠ .jamTashihMudhakkar ∧ s ≠ .jamTashihMuannath := by decide

/-! ### ٦. البندُ (٦) — قرنُ جواب الشرط، وعدُّ جوازم الفعلين الغائبة عن المئة -/

/-- هل يصلح جوابُ الشرط لمباشرة أداته (أي يُجزَم بها مباشرةً)؟ القطر L119–121. -/
inductive SalahiyyatMubasharatAlAdah
  | yaslahu | laYaslahu
  deriving DecidableEq, Repr

inductive SurahQarnJawab
  | bilaQarn | bilFa | biIdhaFujaiyya
  deriving DecidableEq, Repr

/-- صورُ قرن الجواب الممكنة: إذا صلح فبلا قرنٍ فقط، وإذا لم يصلح قُرن بالفاء أو بإذا الفجائية. -/
def suwarQarnAlJawab : SalahiyyatMubasharatAlAdah → List SurahQarnJawab
  | .yaslahu => [.bilaQarn]
  | .laYaslahu => [.bilFa, .biIdhaFujaiyya]

theorem yaslahu_khiyar_wahid : (suwarQarnAlJawab .yaslahu).length = 1 := by decide
theorem laYaslahu_khiyaran : (suwarQarnAlJawab .laYaslahu).length = 2 := by decide

/-- بلا قرنٍ لا يكون إلّا حين يصلح الجوابُ لمباشرة الأداة. -/
theorem bilaQarn_khas_bi_yaslahu :
    ∀ h ∈ [SalahiyyatMubasharatAlAdah.yaslahu, .laYaslahu],
      .bilaQarn ∈ suwarQarnAlJawab h → h = .yaslahu := by decide

/-- عدُّ جوازم الفعلين (القطر L115، بلفظه بلا تشكيل) الغائبة عن أسماء `Jisr.Awamil.table` (جدول المئة
    المودَع) — عدًّا مباشرًا هنا، تصحيحًا لعدِّ الحصر الذي عدّ خمسةً فسمّى بينها «أنى» خطأً (حاضرةٌ) ولم
    يسمِّ «إن» (غائبةٌ). الشاهدُ حرفيّ: فروقُ التشكيل بين النصّين لم تُطابَق. -/
def qatrL115 : List String :=
  ["إن", "إذ", "إذما", "أي", "أين", "أنى", "أيان", "متى", "مهما", "من", "ما", "حيثما"]

def ghaibunAnAlJadwalL115 : List String :=
  qatrL115.filter (fun w => (Awamil.table.map Prod.fst).all (· ≠ w))

theorem ghaib_L115_khamsa : ghaibunAnAlJadwalL115 = ["إن", "إذ", "إذما", "أي", "أيان"] := by decide

/-! ### ٧. البندُ (٧) — تأخيرُ اللقب عن الاسم (القطر L129–131) -/

inductive SinfAlAlam
  | ism | laqab | kunya
  deriving DecidableEq, Repr

/-- رتبةُ صنف العلم في الذكر: الاسمُ أوّلًا، واللقبُ والكنيةُ بعده (القطر L130: «ويؤخر اللقب عن الاسم»؛
    لم يفصل القطر هنا بين اللقب والكنية رتبةً). -/
def rutbatAlLaqab : SinfAlAlam → Nat
  | .ism => 0
  | .laqab => 1
  | .kunya => 1

theorem ism_yataqaddam_laqab : rutbatAlLaqab .ism < rutbatAlLaqab .laqab := by decide
theorem ism_yataqaddam_kunya : rutbatAlLaqab .ism < rutbatAlLaqab .kunya := by decide
theorem laqab_la_yataqaddam_ism : ¬ rutbatAlLaqab .laqab < rutbatAlLaqab .ism := by decide

/-- حالتا اللقب مع الاسم الذي قبله: تابعٌ مطلقًا (الأصل)، أو مخفوضٌ بإضافة الاسم إليه إن أُفرد اللقب
    (القطر L131: «أو مخفوضا بإضافته إن أفرد ك"سعيد كرز"»). -/
inductive HalaLaqabMaAlIsm
  | tabiMutlaqan | makhfudBiIdafatIlayh
  deriving DecidableEq, Repr

/-- شاهدُ «سعيد كرز» نصّيٌّ (القطر L131 يذكره بعينه لحالة الإضافة). وشاهدُ «زين العابدين» بالاستنتاج لا
    بالنصّ: القطر (L129) يذكره مثالًا على كون اللفظ لقبًا لا على حكم تبعيّته؛ استُعمل هنا لأنّه لقبٌ مركّبٌ
    (غيرُ مُفردٍ) فلا يستوفي شرط «إن أُفرد» لحالة الإضافة، فيبقى تحت الأصل «تابعًا مطلقًا» بالاستبعاد لا بنصٍّ
    مباشر — فجوةٌ من جنس فجوةِ رتبة الكنية أعلاه. -/
def shahidHalaLaqab : HalaLaqabMaAlIsm → String
  | .tabiMutlaqan => "زين العابدين"
  | .makhfudBiIdafatIlayh => "سعيد كرز"

theorem halatay_laqab_mustaqillatan :
    shahidHalaLaqab .tabiMutlaqan ≠ shahidHalaLaqab .makhfudBiIdafatIlayh := by decide

/-! ### ٨. البندُ (٨) — اختصاصُ حروف الجرّ بالظاهر (القطر L337–339)، على `SLGE.Wad.jarrF` نفسِه -/

/-- حرفُ الجرّ مختصٌّ بالظاهر إن كان من سطر القطر 339 (لا 338، سطرُ المشترَك)، كما سُجِّلا في `Wad.jarrF`. -/
def ikhtisasBizahir (a : SLGE.Wad.Amil) : Bool := a.line == 339

def mukhtassaBizahir : List SLGE.Wad.Amil := SLGE.Wad.jarrF.filter ikhtisasBizahir
def mushtaraka : List SLGE.Wad.Amil := SLGE.Wad.jarrF.filter (fun a => !ikhtisasBizahir a)

theorem mukhtassa_sabaa : mukhtassaBizahir.length = 7 := by decide
theorem mushtaraka_sabaa : mushtaraka.length = 7 := by decide

/-- القسمةُ تامّةٌ: كلُّ حرفِ جرٍّ في `Wad.jarrF` مشترَكٌ أو مختصٌّ بالظاهر، لا ثالث. -/
theorem qismat_jarr_tamma :
    mukhtassaBizahir.length + mushtaraka.length = SLGE.Wad.jarrF.length := by decide

/-! ### ٩. تصنيفُ البنود الثمانية بحالتها الآن -/

def mustawfaCount : Nat :=
  (Bund.all.filter (fun b => match halaOf b with | .mustawfa _ => true | _ => false)).length
def yantaziruCount : Nat :=
  (Bund.all.filter (fun b => match halaOf b with | .yantaziruQararAlMalik _ => true | _ => false)).length
def juzziCount : Nat :=
  (Bund.all.filter (fun b => match halaOf b with | .juzzi _ _ => true | _ => false)).length

/-- كلُّ بندٍ من الثمانية يقع في حالةٍ واحدةٍ من الثلاث، وتعدادُها يستوفي الثمانية (لا بندَ بلا حالة،
    ولا بندَ في حالتين). -/
theorem tasnif_al_bunud_tamm : mustawfaCount + yantaziruCount + juzziCount = 8 := by decide

end KhulasaIkhbar
end Jisr
