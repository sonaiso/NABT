/-
# من النصّ إلى الإطار لستّة أشكالٍ من ل1 على ضابطها المجمَّد — النتيجةُ على الشفرة الحاليّة

**ما يُقارَن** (`Jisr/NassItarDabit.lean`، بنصّ المواصفة `tahaqquq/dawabit/nass/wasf.md` §القياس): لكلّ حالةٍ من `Dabit.halat` (كتبها مؤلّفٌ
مستقلٌّ إجرائيًّا من المواصفة والنطاق، وفي سياقه ما حُقن آليًّا — `taalif.md` —، وجُمّدت ببصمتها في `tahaqquq/dawabit/nass/tajmid.json` قبل
الشفرة): حقلُ الحكم دائمًا (`hukmNass` على خلايا الجملة كما قرأها القارئ)، وحقلُ الإطار حيث المتوقَّعُ «مقبول» وحكمُ المحرّك «مقبول»
(`maqbula`).

**الوسم.** عشرُ مبرهناتٍ بالمعيار الموحَّد (`Nizam/Asas.lean`): ستٌّ على الشاهد (`majal`، `natija`، `natija_fia`، `akhta_1`، `azwaj_1`،
`asbab_akhta`)، والعدُّ بها «مبرهن على الشاهد» (`decide` على الحالات المجمَّدة)؛ وثلاثٌ لكلّ (`waslBase_khanat`، `khana_hala`، `waslBase_khalal`)
وواحدةٌ تعريفيّة (`khalalKhana_nil`): `Utur.waslBase` مكوّناتُ خاناتها، وخللُ الحال حالان مختلفان، ولا تمتنع إلّا بخللٍ مسمًّى.
ومعنى العدّ موافقةُ الشفرة لقراءةٍ مستقلّةٍ للنطاق، لا تغطيةُ اللغة: الحالاتُ مؤلَّفة لا عيّنةٌ من استعمال.

**انحرافٌ عن المنهج §٤-ج** (`hawkama/منهج_الضوابط.md`: «والبنّاءُ لا يقرأ الحالات ولا وصفَ التأليف حتى تُدفع الشفرة»): قرأ البنّاءُ من
`taalif.md` أسطرَه 1–25 (ما قرأه المؤلّف وما لم يقرأه وما حُقن، بلا حالة) قبل دفع الشفرة، وذكره `tajmid.json` (`qabl_shifra`)، وتوجيهُ المؤلّف
أذن به (`tawjih_muallif.md`)؛ والتفصيلُ في `tahaqquq/dawabit/nass/mulhaq_1.md` (ضبطه المراجع المستقلّ).

**التشغيلات.** المبرهناتُ هنا على الشفرة الحاليّة دائمًا. وسجلُّ كلّ تشغيلٍ ملفٌّ في `tahaqquq/dawabit/nass/` (`natija_1.json` …).
- `natija_1.json`: التشغيلُ الأوّل على الشفرة المجمَّدة في `ecf92e2`، قبل أن يقرأ البنّاءُ الحالات: 61 صوابًا من 71. وأُودع أوّلَ مرّةٍ في `75fe3e6`
  بعد قراءة الحالات، فكونُه قبلها قائمٌ على بصمات الشفرة فيه وقول البنّاء (الملحق §٤).
- `natija_2.json`: على مادّةٍ مكشوفة، بعد تصحيح توثيق `Jisr/NassItar.lean` في `8ddf814` — الرأس وتوثيقا `yudaf` و`haraka_tughayyir`، بلا
  تغييرٍ في الشفرة: اقتباسُ القطر L343 مُدَّ إلى مستثناه، وأُعلن في الرأس وفي `yudaf` أنّ المستثنى لم يُبنَ (وكتب الرأسُ «ضُبط بالحالة N45»:
  إعلانٌ كُتب بعد قراءة الحالات)، وإحالةٌ إلى مبرهنةٍ لا وجودَ لها صُحّحت، وسندُ L92–94 صار L92–93، وعدُّ المبرهنات وتصنيفُ المساعدات الخاصّة.
  الأعدادُ نفسُها.
- `natija_3.json`: على مادّةٍ مكشوفة، بعد مراجعة `murajii` الأولى (توثيقٌ في `Jisr/NassItar.lean` و`Jisr/NassItarDabit.lean`، وشاهدُ حدٍّ
  `haykal_fil_la_itar`؛ والشفرةُ الحاكمة كما هي): الأعدادُ نفسُها، ومعها عدُّ الأزواج التي يصيب طرفاها (10).
- `natija_4.json`: على مادّةٍ مكشوفة، بعد وصل القارئ بالتحصيل (`Dal/QiraaTahsil.lean`، الإيداع `690d963`)، وصارت SHIFRA تشمل
  `Dal/QiraaTahsil.lean` و`Dal/Tahsil.lean`: خلايا الحالات الخمسين من القارئ هي هي، والشفرةُ الحاكمة كما هي؛ الأعدادُ نفسُها.

**الإخفاقاتُ العشرة** (`akhta_1`)، وأسبابُها على إطاراتها مبرهنةٌ على الشاهد (`asbab_akhta`: `hukmSitta` و`asbabLaHukm` و`qiraaSitta`
و`waslBase` وخللُها بموضع خانته `khalal`، لكلّ إطار)، وقراءتُها بالمصدر (القطر، وحدودُ `Utur` و`QawaidSitta`) قراءةُ البنّاء:
- **N04، N21، N24، N28، N35** (الياءُ أو الألفُ آخرَ الفاعل المضاف: «جَاءَ أَبِي الْوَلَدِ»، «حَمِي»، «هَنَا»، «فَا»، «ذَا»؛ المتوقَّع خطأ): حرفُ علّةٍ
  آخرًا في موضع الرفع تُقدَّر عليه الحركة (`Utur.illaMuqaddara`؛ القطر L92–93) فـ«لا حكم» بسببه المسمّى (`illaAkhir`)؛ وصفُّ الأسماء الستّة لا
  يخطّئ إلّا موضعَ الواو بعد ضمّةٍ رفعًا بلا رخصةٍ ولا وقف (`qiraaSitta`)، فلا يرفعه إلى خطأ. والإطارُ الآخر (مفعولٌ بعد الفاعل) ممتنعٌ من
  `waslBase` بخللٍ واحد: كسرةُ الكلمة الثالثة (المضافِ إليه في الإطار الأوّل) في خانة المفعول والمطلوبُ النصب. والجمعُ «لا حكم».
- **N34، N36، N38** («ذُو/ذَا/ذِي الْمَالِ»؛ المتوقَّع مقبول): رخصةُ «ذو» مشروطةٌ بالصحبة وهي لا تُقرأ من الدالّ (`QawaidSitta.dhu_la_rukhsa`)،
  فيبقى سببُ `Utur`: الإعرابُ بالحرف في N34، وحرفُ العلّة آخرًا في N36 وN38.
- **N45** («جَاءَ الضَّارِبُ الرَّجُلِ»؛ المتوقَّع مقبول): مستثنى القطر L344–345 لم يُبنَ (رأسُ `Jisr/NassItar.lean`)، فلا إطارَ بمضافٍ إليه، والإطارُ
  الباقي ممتنعٌ من `waslBase` بخللٍ واحد: «الرَّجُلِ» مكسورٌ في خانة المفعول والمطلوبُ النصب.
- **N46** («جَاءَ أَبًا»، خارج؛ المتوقَّع «لا حكم»، لاحتمال القصر عند المؤلّف): الإطارُ ممتنعٌ من `waslBase` بخللٍ واحد: الحالُ المقروءةُ
  من «أَبًا» (`Utur.halaIrab`) الفتحة، في خانة الفاعل والمطلوبُ الرفع، فخطأ؛ وقراءةُ الستّة فيه مرخَّصة — وهو الحدُّ المعلَن في `Utur` للمقصور المنوَّن («ذَهَبَ فَتًى»
  ممتنعة، `shahid_baqi`).
ولم تُغيَّر الشفرةُ الحاكمة لأيٍّ منها: كلُّ تغييرٍ بعد قراءة الحالات تشغيلٌ على مادّةٍ مكشوفة لا يشهد للضابط.
-/
import Jisr.NassItarDawabit

namespace Jisr
namespace NassItar
namespace Qiyas

open Jisr.Utur Dabit

/-- أعدادُ المجال بترتيبٍ ثابت (يحسبها `tahaqquq/test_nass.py` من `cases.json` بالترتيب نفسه): الحالات؛ ثمّ الحكمُ المتوقَّع: مقبول، خطأ،
    «لا حكم»، بديلان؛ ثمّ الإطاراتُ البديلة؛ ثمّ ذواتُ الزوج؛ ثمّ الفئاتُ: موجب، حدّ، خارج، عموم، غموض. -/
def majalAadad : List Nat :=
  [halat.length] ++
  [Hukm.murakhkhas, .mumtani, .laHukm].map (fun d => (halat.filter (·.hukm == [d])).length) ++
  [(halat.filter (fun h => decide (2 ≤ h.hukm.length))).length,
   (halat.filter (fun h => decide (2 ≤ h.itar.length))).length,
   (halat.filter (·.zawj.isSome)).length] ++
  [Fia.mujib, .hadd, .kharij, .umum, .ghumud].map (fun f => (halat.filter (·.fia == f)).length)

/-- **المجالُ غيرُ فارغ ولا مائلٍ إلى «لا حكم»:** 50 حالة. والمتوقَّع: مقبول 25، وخطأ 20، و«لا حكم» 5، ولا بديلين في حكمٍ ولا في إطار؛
    و34 حالةً في 17 زوجًا. والفئات: موجب 19، وحدّ 20، وخارج 5، وعموم 6، وغموض 0 (بحث المؤلّفُ فلم يجد، `taalif.md`). -/
theorem majal : majalAadad = [50, 25, 20, 5, 0, 0, 34, 19, 20, 5, 6, 0] := by
  decide +kernel

/-- **النتيجة:** 61 صوابًا من 71 حقلًا (50 حكمًا و21 إطارًا): 8 نقوص تغطية، وتجاوزٌ واحد، وردٌّ خاطئٌ واحد؛ ولا قبولَ خاطئ، ولا خطأَ
    إطار، ولا رفضَ من القارئ. -/
theorem natija : ihsa (natayij halat) = ⟨61, 8, 1, 0, 1, 0, 0, 0, 0⟩ := by
  decide +kernel

/-- **بالفئات:** موجب 30 ونقوصٌ ثلاثة وردٌّ واحد، وحدّ 15 ونقوصٌ خمسة، وخارج 4 وتجاوزٌ واحد، وعموم 12، وغموض لا شيء. -/
theorem natija_fia :
    [Fia.mujib, .hadd, .kharij, .umum, .ghumud].map (fun f => ihsa ((natayij halat).filter (·.2.1 == f))) =
      [⟨30, 3, 0, 0, 1, 0, 0, 0, 0⟩, ⟨15, 5, 0, 0, 0, 0, 0, 0, 0⟩, ⟨4, 0, 1, 0, 0, 0, 0, 0, 0⟩, ⟨12, 0, 0, 0, 0, 0, 0, 0, 0⟩,
       ⟨0, 0, 0, 0, 0, 0, 0, 0, 0⟩] := by
  decide +kernel

/-- **والإخفاقاتُ العشرة بأسمائها**، كلُّها في حقل الحكم. -/
theorem akhta_1 :
    akhta (natayij halat) = [("N04", .hukm, .naqsTaghtiya), ("N21", .hukm, .naqsTaghtiya), ("N24", .hukm, .naqsTaghtiya),
      ("N28", .hukm, .naqsTaghtiya), ("N34", .hukm, .naqsTaghtiya), ("N35", .hukm, .naqsTaghtiya),
      ("N36", .hukm, .naqsTaghtiya), ("N38", .hukm, .naqsTaghtiya), ("N45", .hukm, .raddKhati), ("N46", .hukm, .tajawuz)] := by
  decide +kernel

/-- حقلُ الحكم في الحالة صواب. -/
def sawabHukm (i : String) : Bool := (natayij halat).any fun x => x.1 == i && x.2.2.1 == Haql.hukm && x.2.2.2 == Natija.sawab

/-- **تبديلُ علامة الإعراب** (الأزواجُ السبعة عشر): يتغيّر حكمُ المحرّك في ستّة عشر منها، ولا يتغيّر في N34/N35؛ **ويصيب الطرفان معًا
    في عشرة** — وفي ستّةٍ ممّا تغيّر صار أحدُ الطرفين «لا حكم» لا المتوقَّعَ (N03/N04، N20/N21، N23/N24، N27/N28، N36/N37، N38/N39؛
    ضبطه المراجع المستقلّ). ولا رفضَ من القارئ. -/
theorem azwaj_1 :
    (azwaj halat).length = 17 ∧ ((azwaj halat).filter (·.2.2)).length = 16 ∧
    (azwaj halat).filter (!·.2.2) = [("N34", "N35", false)] ∧
    ((azwaj halat).filter fun p => sawabHukm p.1 && sawabHukm p.2.1).length = 10 ∧ rafd halat = [] := by
  decide +kernel

section
open SLGE SLGE.Law SLGE.Tarkib SLGE.Simat SLGE.Kull SLGE.Awwalan Dal

/-- مكوّناتُ `waslBase` في خانةٍ ظاهرة: اكتمالُ كلمتها (`kamila`)، وحالُها المقروءة (`hala`، `halaIrab`) والمطلوبة (`matlub`، `reqState`)،
    وشرطُ الحال كلُّه (`halaSaliha`: غيرُ معربة، أو لا حالَ مطلوبة، أو الحالان سواء، أو تقدير `muqaddar`)، وقسمُ المدلول (`qism`). -/
structure Khana where
  kamila : Bool
  hala : Nat
  matlub : Option Nat
  halaSaliha : Bool
  qism : Bool
  deriving DecidableEq, Repr

/-- مكوّناتُ الخانة `i` بنصّ `waslBase` (`none` إن غابت كلمتُها أو مدلولُها). وشرطُ الحال يُحسب من القيمتين `h` و`q` اللتين يُملأ بهما
    حقلا `hala` و`matlub`، ومعهما سمةُ البناء (`t.2.2.2`) والتقدير (`muqaddar`)؛ ويربطه بالحقلين `khana_hala` حين يسقط. -/
def khana (u : Itar3) (i : Nat) : Option Khana :=
  let r := Mulhaqat.roleOf u.jisr.ud.f i
  let t := attrAt u.jisr.ud.ats i
  match u.kalimat[overtIdx u i]?, u.maani[overtIdx u i]? with
  | some w, some m =>
    let h := halaIrab (isNom r) w.khalaya
    let q := reqState u.jisr.ud.f.1 u.jisr.ud.f.2.1 r
    some ⟨complete' (ibtida w), h, q,
      t.2.2.2 || (match q with
                  | some x => h == x || muqaddar (isNom r) [x] w (mudafAlayh u i) | none => true),
      SLGE.Cat.kindOfMadlul m == qismDawr u.jisr.ud.f.2.1 r⟩
  | _, _ => none

/-- **خللُ الحال حالان مختلفان:** إن سقط شرطُ الحال في خانةٍ فلها حالٌ مطلوبة غيرُ حالها المقروءة. -/
theorem khana_hala (u : Itar3) (i : Nat) (k : Khana) (hk : khana u i = some k) (hs : k.halaSaliha = false) :
    ∃ x, k.matlub = some x ∧ k.hala ≠ x := by
  unfold khana at hk
  split at hk
  · simp only [Option.some.injEq] at hk
    subst hk
    simp only [Bool.or_eq_false_iff] at hs
    obtain ⟨_, hs⟩ := hs
    split at hs
    · rename_i x hx
      refine ⟨x, hx, fun he => ?_⟩
      simp only [Bool.or_eq_false_iff, beq_eq_false_iff_ne] at hs
      exact hs.1 he
    · simp at hs
  · simp at hk

/-- خاناتُ الإطار الأصليّة بالترتيب: أهي مملوءةٌ ضمنًا (`fillAt ≠ 0`)، ومكوّناتُها. -/
def khanat (u : Itar3) : List (Bool × Option Khana) :=
  (List.range (nB u)).map fun i => (fillAt (baseSlots u) i != 0, khana u i)

/-- **`waslBase` هي مكوّناتُ خاناتها:** تصدق إن وفقط إن كانت كلُّ خانةٍ مملوءةً ضمنًا أو مكوّناتُها الثلاثة صادقة. -/
theorem waslBase_khanat (u : Itar3) :
    waslBase u = (khanat u).all fun x => x.1 || (x.2.map fun k => k.kamila && k.halaSaliha && k.qism).getD false := by
  unfold waslBase khanat khana
  rw [List.all_map]
  congr 1
  funext i
  simp only [Function.comp]
  split <;> simp_all <;> rfl

/-- خللُ خانةٍ ظاهرة في `waslBase`: غيابُ كلمتها أو مدلولها (`ghaib`)، أو نقصُ كلمتها، أو — والكلمةُ معربة — حالٌ مقروءةٌ (`hala`) غيرُ
    المطلوبة (`matlub`) بلا تقدير، أو قسمُ مدلولٍ غيرُ قسم دورها. -/
inductive Khalal where
  | ghaib
  | naqis
  | hala (h : Nat) (m : Option Nat)
  | qism
  deriving DecidableEq, Repr

/-- خللُ خانةٍ بمكوّناتها (لا خللَ في المملوءة ضمنًا). -/
def khalalKhana (x : Bool × Option Khana) : List Khalal :=
  if x.1 then [] else
  match x.2 with
  | none => [.ghaib]
  | some k => (if k.kamila then [] else [.naqis]) ++ (if k.halaSaliha then [] else [.hala k.hala k.matlub]) ++
      (if k.qism then [] else [.qism])

/-- خللُ الإطار: كلُّ خللٍ بموضع خانته. -/
def khalal (u : Itar3) : List (Nat × Khalal) :=
  (khanat u).zipIdx.flatMap fun p => (khalalKhana p.1).map (p.2, ·)

theorem khalalKhana_nil (x : Bool × Option Khana) :
    (x.1 || (x.2.map fun k => k.kamila && k.halaSaliha && k.qism).getD false) = true ↔ khalalKhana x = [] := by
  obtain ⟨f, o⟩ := x
  cases f <;> cases o <;> simp [khalalKhana]
  rename_i k
  cases k.kamila <;> cases k.halaSaliha <;> cases k.qism <;> simp

/-- **لا يمتنع `waslBase` إلّا بخللٍ مسمًّى:** تصدق إن وفقط إن خلا الإطارُ من الخلل. -/
theorem waslBase_khalal (u : Itar3) : waslBase u = true ↔ khalal u = [] := by
  rw [waslBase_khanat, khalal, List.all_eq_true, List.flatMap_eq_nil_iff]
  constructor
  · intro h p hp
    have := (khalalKhana_nil p.1).1 (h p.1 (List.mem_of_getElem? (List.mem_zipIdx_iff_getElem?.1 hp)))
    simp [this]
  · intro h x hx
    obtain ⟨j, hj⟩ := List.getElem?_of_mem hx
    have := h (x, j) (List.mem_zipIdx_iff_getElem?.2 hj)
    exact (khalalKhana_nil x).2 (List.map_eq_nil_iff.1 this)

end

/-- أسبابُ الحكم على إطار: الأدوار، و`hukmSitta`، و`asbabLaHukm`، و`qiraaSitta`، و`waslBase`، وخللُها بموضع خانته (`khalal`). -/
structure SababItar where
  adwar : List Dawr
  hukm : Hukm
  asbab : List SababLaHukm
  qiraa : Hukm
  wasl : Bool
  khalal : List (Nat × Khalal)
  deriving DecidableEq, Repr

/-- أسبابُ الحكم على كلّ إطارٍ في حالة. -/
def sababIkhfaq (i : String) : List SababItar :=
  match (halat.find? (·.ism == i)).bind (·.kalimat) with
  | some ws => (itarat ws).map fun x =>
      ⟨x.1, QawaidSitta.hukmSitta x.2, asbabLaHukm x.2, QawaidSitta.qiraaSitta x.2, waslBase x.2, khalal x.2⟩
  | none => []

/-- **أسبابُ الإخفاقات العشرة على إطاراتها** (شاهدُ ما في الرأس). والحالاتُ أرقامٌ: الفتحة 0، والضمّة 1، والكسرة 2، والسكون 3؛ والمطلوبةُ من
    `reqState`: الرفع 1، والنصب 0. والخانةُ برقمها من الصفر (الفعل 0، الفاعل 1، المفعول 2).
    * N04 N21 N24 N28 N35: إطارُ المضاف إليه «لا حكم» بسببه `illaAkhir` وقراءةُ الستّة فيه «لا حكم»؛ وإطارُ المفعول ممتنعٌ من `waslBase`
      بخللٍ واحد: كسرةُ الكلمة الثالثة (المضافِ إليه في الإطار الأوّل) في خانة المفعول (الخانة 2) والمطلوبُ النصب.
    * N34: «لا حكم» بسببه `irabBilHarf`؛ وإطارُ المفعول ممتنعٌ بخللين: سكونُ «ذُو» في خانة الفاعل (الخانة 1) والمطلوبُ الرفع، وكسرةُ «الْمَالِ»
      في خانة المفعول (الخانة 2). N36 N38: «لا حكم» بسببه `illaAkhir`.
    * N45: إطارٌ واحدٌ ممتنعٌ بخللٍ واحد: كسرةُ «الرَّجُلِ» في خانة المفعول (الخانة 2) والمطلوبُ النصب. N46: إطارٌ واحدٌ ممتنعٌ بخللٍ واحد: فتحةُ «أَبًا»
      في خانة الفاعل (الخانة 1) والمطلوبُ الرفع. وقراءةُ الستّة فيهما مرخَّصة.
    ولا خللَ في نقص كلمةٍ ولا في قسم مدلول؛ وأنّ الخللَ وحده سببُ الامتناع من `waslBase` هو `waslBase_khalal`، وأنّ خللَ الحال حالان مختلفان
    هو `khana_hala`. -/
theorem asbab_akhta :
    ["N04", "N21", "N24", "N28", "N35", "N34", "N36", "N38", "N45", "N46"].map sababIkhfaq =
      [[⟨[.fil, .fail, .mudafIlayh], .laHukm, [.illaAkhir], .laHukm, true, []⟩,
        ⟨[.fil, .fail, .maful], .mumtani, [], .laHukm, false, [(2, .hala 2 (some 0))]⟩],
       [⟨[.fil, .fail, .mudafIlayh], .laHukm, [.illaAkhir], .laHukm, true, []⟩,
        ⟨[.fil, .fail, .maful], .mumtani, [], .laHukm, false, [(2, .hala 2 (some 0))]⟩],
       [⟨[.fil, .fail, .mudafIlayh], .laHukm, [.illaAkhir], .laHukm, true, []⟩,
        ⟨[.fil, .fail, .maful], .mumtani, [], .laHukm, false, [(2, .hala 2 (some 0))]⟩],
       [⟨[.fil, .fail, .mudafIlayh], .laHukm, [.illaAkhir], .laHukm, true, []⟩,
        ⟨[.fil, .fail, .maful], .mumtani, [], .laHukm, false, [(2, .hala 2 (some 0))]⟩],
       [⟨[.fil, .fail, .mudafIlayh], .laHukm, [.illaAkhir], .laHukm, true, []⟩,
        ⟨[.fil, .fail, .maful], .mumtani, [], .laHukm, false, [(2, .hala 2 (some 0))]⟩],
       [⟨[.fil, .fail, .mudafIlayh], .laHukm, [.irabBilHarf], .laHukm, true, []⟩,
        ⟨[.fil, .fail, .maful], .mumtani, [], .murakhkhas, false, [(1, .hala 3 (some 1)), (2, .hala 2 (some 0))]⟩],
       [⟨[.fil, .fail, .maful, .mudafIlayh], .laHukm, [.illaAkhir], .laHukm, true, []⟩],
       [⟨[.harfJarr, .majrur, .mudafIlayh], .laHukm, [.illaAkhir], .laHukm, true, []⟩],
       [⟨[.fil, .fail, .maful], .mumtani, [], .murakhkhas, false, [(2, .hala 2 (some 0))]⟩],
       [⟨[.fil, .fail], .mumtani, [], .murakhkhas, false, [(1, .hala 0 (some 1))]⟩]] := by
  decide +kernel

end Qiyas
end NassItar
end Jisr
