import Jisr.TabaqatQawaid
import Dal.Jumla

/-!
# الإبدالُ في الواو والياء من ألفيّة ابن مالك: قيودٌ على الخلايا فوق آلة القانون

**الطلب.** رسالةُ المالك 2026-10-28: صدرُها في سجلّ الجلسة مقطوعًا عند نحو مئتي حرف، وباقيها ووقتُها (12:11 بتوقيت عمّان) وإجاباتُه
من ملخّص الجلسة بعد ضغطها. ولفظُها فيه:
«حاول مرة أخرى تنظيم الانتروبيا انت تدير مجموعة وكلاء … وتحويل الالفية الى lean داخل الشيفرة الام وفق افضل الممارسات»
ثمّ اختار من أسئلةٍ متعدّدة الخيارات نصُّها من البنّاء: «أبوابُ الصوت والبنية (موصى به)»، و«على آلة القانون وخلاياها (موصى به)»، و«موصى به»
وسمُ البنّاء. واختيارُ هذه الأحكام قطعةً أولى، وتصميمُها، قرارُ البنّاء: هي ما يُكتب من الباب على الخلايا وحدها بلا خرقٍ في المصحف، في
تقريرٍ لوكيلٍ خبيرٍ بأسطر الألفيّة (غيرِ مودَع).

**المصدرُ والنطاق:** `alfiyya.txt` (بصمتُه `13b351a0…`)، الأسطر 1216–1217 و1222 و1224 و1225–1226 و1238–1239 من باب الإبدال. وهي
على ضابطٍ مجمَّد (`tahaqquq/dawabit/ibdal/wasf.md`): كُتبت هذه الشفرةُ قبل أن يقرأ البنّاءُ الحالات (`4ad7b9a`)؛ وأُعيدت بعد
قراءتها كتابةُ براهين خمسٍ تكتب نصَّ التعريف، بلا تغيير عبارةٍ ولا تعريف (`natija_2.json`)؛ ثمّ بعد مراجعة `murajii` برهانُ
`akhir_sinf_khatima`، وزيدت أربعُ مبرهنات (`tasmahBaad_khatima`، `yaBadDamma_akhir`، `sinf_wawYa_fatha_damma`، `yaWaw_yamna`)، وصُحّح هذا
الرأسُ وتوثيقان، بلا تغيير تعريف (`natija_3.json`)؛ ثمّ بعد المراجعتين الثانية والثالثة هذا الرأسُ، ومبرهنتان (`haraka_sinfIshtibah`،
`madd_la_ghayrMamnu`)، بلا تغيير تعريف (`natija_4.json`). وما رآه البنّاءُ وما كُتب
بعد القراءة في `tahaqquq/dawabit/ibdal/mulhaq_1.md`.

**المدخل:** خلايا كلمةٍ واحدة كما يقرؤها القارئ في الوصل (`qari --khalaya`). ولا يُعطى المحرّكُ أصلَ الكلمة ولا وزنَها ولا معناها.

**الحكم** (`hukm`): أهو `mamnu` (بسببه)، أو `ghayrMamnu`، أو `laHukm`:
- **`mamnu .qanun`:** يردّها القانونُ (`SLGE.Law`، موقوفًا عليها، كما في القارئ). ومنه حكما الألف في النطاق، فالقانونُ يمنعهما أصلًا
  (`alif_baad_ghayr_fatha`): الألفُ بعد الكسرة وبعد ياء التصغير (1216)، والألفُ بعد الضمّة (1222). وما يردّه القانونُ لسببٍ خارج النطاق
  يُعدّ هنا `mamnu .qanun` كذلك، والمواصفةُ تجعل ما لا يمنعه النطاقُ `غير_ممنوع` (تعيينٌ أدناه).
- **`mamnu .yaBadDamma`** (1222 «ويا كموقن»، و1224): ياءٌ ساكنةٌ بعد ضمّة، لا تليها ياءٌ متحرّكة (`qaydMuqin`).
- **`mamnu .wawYa`** (1238–1239): واوٌ ساكنةٌ بعد فتحةٍ أو كسرةٍ تليها ياءٌ متحرّكة، أو ياءٌ ساكنةٌ بعد فتحةٍ أو ضمّةٍ تليها واوٌ متحرّكة (`qaydWawYa`).
- **`mamnu .akhirWaw`** (1216 «بواو ذا افعلا»، و1217 «في آخر»): واوٌ متحرّكةٌ بعد كسرةٍ آخرَ الكلمة (`qaydAkhirWaw`).
- **`mamnu .akhirYa`** (1225 «لام فعل»): ياءٌ متحرّكةٌ بعد ضمّةٍ آخرَ الكلمة (`qaydAkhirYa`).
- **`laHukm`** (`qaydIshtibah`): موضعٌ لا تفرّق فيه الخلايا بين ما يمنعه النطاقُ وما لا يمنعه:
  - الواوُ المدّ بعد الضمّة تليها ياءٌ متحرّكة، والياءُ المدّ بعد الكسرة تليها واوٌ متحرّكة: يستثني البيتُ ما سكونُه عارض («ومن عروض»،
    1238)، والمدُّ في الخلايا سواءٌ أكان عارضًا أم أصليًّا.
  - الواوُ المتحرّكة بعد كسرةٍ، والياءُ المتحرّكة بعد ضمّة، في غير آخر الخلايا: لا تفرّق الخلايا بين آخر الكلمة قبل ضميرٍ متّصل أو تاءِ
    تأنيث أو زيادتي «فعلان»، وغيرِ الآخر. وجعلُه في كلّ موضعٍ غيرِ آخرٍ أيًّا كانت الخليّةُ بعده تعيينٌ (أدناه): فـ«عِوَضٌ» و«مُيَسِّرٌ»
    «لا حكم» والخليّةُ بعد الحرف ضادٌ أو سينٌ لا يبدأ بها ضميرٌ ولا تاءٌ ولا «ان».
- **`ghayrMamnu`:** ما سوى ذلك: لا يمنعه النطاق. وليس حكمًا بصحّة الكلمة عربيّةً.
والترتيبُ: القانونُ ثمّ القواعدُ الأربع ثمّ الاشتباه؛ فالممنوعُ بموضعٍ لا يرفعه اشتباهٌ في موضعٍ آخر.

**تعييناتُ البنّاء** (قراءتُه للأبيات، تنتظر إمضاءَ المالك):
- الياءُ الساكنة بعد الضمّة تليها ياءٌ متحرّكة (المدغمة) لا تُمنع: مثالُ البيت «موقن» ياءٌ مفردة.
- السكونُ غيرُ المدّ في الخلايا أصليٌّ، فلا يُستثنى بـ«ومن عروض».
- «في آخر» آخرُ الخلايا. والتنوينُ خليّةُ نونٍ ساكنةٍ بعد الحرف، فالحرفُ قبله ليس آخرًا (فيقع في الاشتباه).
- الضمّةُ والكسرة قبل الحرف حركةُ الخليّة قبله أيًّا كان حاملُها.
- ما يردّه القانونُ لسببٍ خارج النطاق `mamnu .qanun`، والمواصفةُ تجعله `غير_ممنوع`.
- «لام فعل» (1225): كلُّ ياءٍ متحرّكةٍ بعد ضمّةٍ آخرَ الخلايا تُمنع، فعلًا كانت أو اسمًا؛ والمواصفةُ تشترط `لامَ «فَعُل»` («التَّرَامُيُ» ممنوعةٌ
  هنا، ولا يمنعها النطاق).
- «بواو ذا افعلا» … «في آخر» (1216–1217): الواوُ المتحرّكةُ وحدها؛ والساكنةُ بعد كسرةٍ آخرَ الخلايا غيرُ ممنوعة، والبيتُ لا يشترط الحركة.
- الاشتباهُ في كلّ موضعٍ غيرِ آخرٍ للحرف المتحرّك بعد الحركة، أيًّا كانت الخليّةُ بعده.

**ما بُرهن:**
- **القواعدُ على آلة القانون:** كلُّ قاعدةٍ من الأربع `Qayd` من `Jisr/TabaqatQawaid.lean`. فالآلتان معًا لا توسّعان (`qanun_qaida_le`)، وكلُّ
  قاعدةٍ تحذف من كلمات القانون بطول مثالها (`muqin_yahdhif`، `wawYa_yahdhif`، `akhirWaw_yahdhif`، `akhirYa_yahdhif`).
- **الحكمُ على كلّ كلمة:** `hukm` غيرُ ممنوعٍ إذا وفقط إذا قبلها القانونُ وسمحت بها القواعدُ الأربع ولم يقع فيها اشتباه (`ghayrMamnu_iff`)؛ وهو
  ممنوعٌ إذا وفقط إذا ردّها القانونُ أو قاعدة (`mamnu_iff`). والقانونُ هنا هو `alaMashru false` (`qanun_sawa`).
- **الموضعُ الممنوع يردّ الكلمة حيثما وقع:** الياءُ الساكنة بعد الضمّة قبل غير ياءٍ متحرّكة (`yaBadDamma_yamna`) وآخرَ الكلمة
  (`yaBadDamma_akhir`)؛ والواوُ الساكنة بعد فتحةٍ أو كسرةٍ تليها ياءٌ متحرّكة (`wawYa_yamna`)، والياءُ الساكنة بعد فتحةٍ أو ضمّةٍ تليها واوٌ
  متحرّكة (`yaWaw_yamna`)؛ والواوُ المتحرّكة بعد الكسرة والياءُ المتحرّكة بعد الضمّة آخرًا (`akhir_yamna`). والمدُّ خارجها: الواوُ بعد الضمّة
  والياءُ بعد الكسرة تليهما الأخرى متحرّكةً لا تكون الكلمةُ بهما غيرَ ممنوعة (`madd_la_ghayrMamnu`)، فهي «لا حكم» أو ممنوعةٌ بغيره (وشاهدُ
  «لا حكم» «بُويِعَ» في `shawahid_hukm`).

**المبرهنات** (35، بالمعيار الموحَّد في `Nizam/Asas.lean`):
- لكلّ 24: `run_sawa`، `run_lt`، `run_le`، `qanun_sawa`، `ghayrMamnu_maan`، `alif_baad_ghayr_fatha`، `sira_snoc`، `tasmah_mamnu_hukm`،
  `tasmahBaad_khatima`، `yaBadDamma_yamna`، `yaBadDamma_akhir`، `sinf_wawYa_haraka`، `sinf_wawYa_fatha_damma`، `wawYa_yamna`، `yaWaw_yamna`،
  `akhir_sinf_haraka`، `akhir_sinf_khatima`، `tasmahBaad_akhir`، `tasmah_akhir`، `akhir_yamna`، `haraka_sinfIshtibah`، `madd_la_ghayrMamnu`،
  `fakkN_mem`، `yahdhif`.
- تعريفيّة 4: `ghayrMamnu_iff`، `mamnu_iff`، `sinf_muqin_damma`، `akhir_mamnu`.
- على الشاهد 7: `la_wahid_baad_haraka` و`alif_mayyit` (`decide` على حالات القانون الـ97 وخلاياه)، و`shawahid_hukm`؛ و`muqin_yahdhif`
  و`wawYa_yahdhif` و`akhirWaw_yahdhif` و`akhirYa_yahdhif` خارجَ حرف المعيار (`decide` على كلمة المثال ثمّ نقلٌ بـ`yahdhif`).
وهي خواصُّ تعيين البنّاء على مجاله (الكلماتُ خلايا)، لا قوانينُ لغة.

**ما لا تقوله.** أنّ ما لا تمنعه القواعدُ صحيحٌ لغةً؛ ولا الصورةَ التي يوجبها البيتُ مكانَ الممنوعة (القيدُ يردّ ولا يُخرج صورة)؛ ولا ما في
النطاق ممّا يحتاج معرفةَ الجمع أو البناء أو الزائد (كسرُ المضموم في «هيم» مكانَ قلب الياء واوًا، و«قبل تا التأنيث» و«زيادتي فعلان»
في غير الآخر). ولا ما يحذفه كلُّ قيدٍ من معدّل النموّ.
-/

namespace Jisr.IbdalAlfiyya

open Jisr.TabaqatQawaid Jisr.Intrubiya

/-! ## ١. الخلايا: الحامل والحالة (`Dal/Makharij.lean`: الألف 2، الياء 11، الواو 28؛ والحالات: فتحة 0، ضمّة 1، كسرة 2، سكون 3) -/

/-- حالةُ الخليّة. -/
def hala (k : Dal.Khaliya) : Nat := k.hala.val

def yaSakina (k : Dal.Khaliya) : Bool := k.hamil.val == 11 && k.hala.val == 3
def wawSakina (k : Dal.Khaliya) : Bool := k.hamil.val == 28 && k.hala.val == 3
def yaMutaharrika (k : Dal.Khaliya) : Bool := k.hamil.val == 11 && k.hala.val != 3
def wawMutaharrika (k : Dal.Khaliya) : Bool := k.hamil.val == 28 && k.hala.val != 3

/-- الخليّةُ من رقمها (`Dal.n`)، كما يُخرجها القارئ. -/
def fakkN (m : Nat) : Dal.Khaliya := Dal.fakk ⟨m % 116, Nat.mod_lt _ (by decide)⟩

/-! ## ٢. القواعدُ الأربع -/

/-- صنفُ الخليّة في قاعدة «موقن»: 1 إن كانت مضمومة، وإلّا 0. -/
def sinfDamma (a : Dal.Khaliya) : Fin 3 := if a.hala.val == 1 then 1 else 0

/-- **الياءُ الساكنة بعد الضمّة** (1222 «ويا كموقن بذا لها اعترف»، و1224): ممنوعةٌ ما لم تلها ياءٌ متحرّكة. والصنفُ 2 ياءٌ ساكنةٌ بعد ضمّة. -/
def qaydMuqin : Qayd Dal.Khaliya where
  k := 3
  awwalSinf := sinfDamma
  sinf := fun c a => if c.val == 1 && yaSakina a then 2 else sinfDamma a
  mamnu := fun c a => c.val == 2 && !yaMutaharrika a
  bidaya := fun _ => false
  khatima := fun c => c.val == 2

/-- صنفُ الحركة: 1 فتحة، 2 ضمّة، 3 كسرة، 0 سكون. -/
def sinfHaraka (a : Dal.Khaliya) : Fin 6 :=
  if a.hala.val == 0 then 1 else if a.hala.val == 1 then 2 else if a.hala.val == 2 then 3 else 0

/-- **الواوُ والياءُ متّصلتين والأولى ساكنة** (1238–1239): الصنفُ 4 واوٌ ساكنةٌ بعد فتحةٍ أو كسرة، و5 ياءٌ ساكنةٌ بعد فتحةٍ أو ضمّة؛ والمدُّ خارجهما. -/
def qaydWawYa : Qayd Dal.Khaliya where
  k := 6
  awwalSinf := sinfHaraka
  sinf := fun c a =>
    if (c.val == 1 || c.val == 3) && wawSakina a then 4
    else if (c.val == 1 || c.val == 2) && yaSakina a then 5
    else sinfHaraka a
  mamnu := fun c a => (c.val == 4 && yaMutaharrika a) || (c.val == 5 && wawMutaharrika a)
  bidaya := fun _ => false
  khatima := fun _ => false

/-- صنفُ قاعدة الآخر: 1 خليّةٌ بالحركة المطلوبة قبل الحرف، و2 أو 3 الحرفُ المتحرّكُ بعدها (3 إن كانت حركتُه هي المطلوبة أيضًا). -/
def sinfAkhir (h : Nat) (harf : Dal.Khaliya → Bool) (c : Fin 4) (a : Dal.Khaliya) : Fin 4 :=
  if (c.val == 1 || c.val == 3) && harf a then (if a.hala.val == h then 3 else 2)
  else if a.hala.val == h then 1 else 0

/-- قاعدةُ الآخر: الحرفُ المتحرّكُ بعد الحركة `h` لا يكون آخرَ الكلمة. -/
def qaydAkhir (h : Nat) (harf : Dal.Khaliya → Bool) : Qayd Dal.Khaliya where
  k := 4
  awwalSinf := fun a => if a.hala.val == h then 1 else 0
  sinf := sinfAkhir h harf
  mamnu := fun _ _ => false
  bidaya := fun _ => false
  khatima := fun c => c.val == 2 || c.val == 3

/-- **الواوُ المتحرّكة بعد الكسرة آخرًا** (1216 «بواو ذا افعلا»، و1217 «في آخر»). والساكنةُ خارجها: تعيين. -/
def qaydAkhirWaw : Qayd Dal.Khaliya := qaydAkhir 2 wawMutaharrika

/-- **الياءُ المتحرّكة بعد الضمّة آخرًا** (1225 «وواوا اثر الضم رد اليا متى ... ألفي لام فعل»)، فعلًا كانت أو اسمًا: تعيين. -/
def qaydAkhirYa : Qayd Dal.Khaliya := qaydAkhir 1 yaMutaharrika

/-- القواعدُ الأربع. -/
def qawaid : List (Qayd Dal.Khaliya) := [qaydMuqin, qaydWawYa, qaydAkhirWaw, qaydAkhirYa]

/-! ## ٣. الاشتباه: ما لا تفرّقه الخلايا -/

/-- حركةُ صنف الاشتباه: 0–3 حركةُ الخليّة، و4 واوٌ مدٌّ بعد ضمّة، و5 ياءٌ مدٌّ بعد كسرة، و6–8 واوٌ متحرّكةٌ بعد كسرة (بحركتها)،
و9–11 ياءٌ متحرّكةٌ بعد ضمّة (بحركتها). -/
def haraktuSinf (c : Fin 12) : Nat :=
  if c.val < 4 then c.val else if c.val < 6 then 3 else if c.val < 9 then c.val - 6 else c.val - 9

def sinfIshtibah (c : Fin 12) (a : Dal.Khaliya) : Fin 12 :=
  if haraktuSinf c == 1 && wawSakina a then 4
  else if haraktuSinf c == 2 && yaSakina a then 5
  else if haraktuSinf c == 2 && wawMutaharrika a then ⟨6 + a.hala.val % 3, by omega⟩
  else if haraktuSinf c == 1 && yaMutaharrika a then ⟨9 + a.hala.val % 3, by omega⟩
  else ⟨a.hala.val, by have := a.hala.isLt; omega⟩

/-- **الاشتباه:** المدُّ تليه الأخرى متحرّكة، والحرفُ المتحرّكُ بعد الحركة في غير آخر الخلايا. -/
def qaydIshtibah : Qayd Dal.Khaliya where
  k := 12
  awwalSinf := fun a => ⟨a.hala.val, by have := a.hala.isLt; omega⟩
  sinf := sinfIshtibah
  mamnu := fun c a => 6 ≤ c.val || (c.val == 4 && yaMutaharrika a) || (c.val == 5 && wawMutaharrika a)
  bidaya := fun _ => false
  khatima := fun _ => false

/-! ## ٤. الحكم -/

/-- القانونُ على الخلايا موقوفًا عليها، كما في القارئ (`Fwaqf ∘ run`). -/
def qanunYaqbal (xs : List Dal.Khaliya) : Bool :=
  SLGE.Law.Fwaqf (SLGE.Law.run 0 (xs.map fun k => (Dal.n k).val))

inductive Sabab where
  | qanun | yaBadDamma | wawYa | akhirWaw | akhirYa
  deriving DecidableEq, Repr

inductive Hukm where
  | mamnu (s : Sabab)
  | ghayrMamnu
  | laHukm
  deriving DecidableEq, Repr

def hukm (xs : List Dal.Khaliya) : Hukm :=
  if !qanunYaqbal xs then .mamnu .qanun
  else if !qaydMuqin.tasmah xs then .mamnu .yaBadDamma
  else if !qaydWawYa.tasmah xs then .mamnu .wawYa
  else if !qaydAkhirWaw.tasmah xs then .mamnu .akhirWaw
  else if !qaydAkhirYa.tasmah xs then .mamnu .akhirYa
  else if !qaydIshtibah.tasmah xs then .laHukm
  else .ghayrMamnu

/-- الحكمُ على الكلمة كما يسلّمها القارئ (`Dal.Kalima`): على صورة الابتداء (`Dal.ibtida`، همزةُ الوصل بحركتها)، كما يحكم القارئ بالقانون. -/
def hukmKalima (w : Dal.Kalima) : Hukm := hukm ((Dal.ibtida w).map fakkN)

/-- **غيرُ الممنوع:** يقبله القانونُ وتسمح به القواعدُ الأربع ولا اشتباه فيه. -/
theorem ghayrMamnu_iff (xs : List Dal.Khaliya) :
    hukm xs = .ghayrMamnu ↔
      qanunYaqbal xs = true ∧ (∀ r ∈ qawaid, r.tasmah xs = true) ∧ qaydIshtibah.tasmah xs = true := by
  unfold hukm
  cases h0 : qanunYaqbal xs <;> cases h1 : qaydMuqin.tasmah xs <;> cases h2 : qaydWawYa.tasmah xs <;>
    cases h3 : qaydAkhirWaw.tasmah xs <;> cases h4 : qaydAkhirYa.tasmah xs <;> cases h5 : qaydIshtibah.tasmah xs <;>
    simp [qawaid, h1, h2, h3, h4]

/-- **الممنوع:** ما ردّه القانونُ أو قاعدةٌ من الأربع. -/
theorem mamnu_iff (xs : List Dal.Khaliya) :
    (∃ s, hukm xs = .mamnu s) ↔ qanunYaqbal xs = false ∨ ∃ r ∈ qawaid, r.tasmah xs = false := by
  unfold hukm
  cases h0 : qanunYaqbal xs <;> cases h1 : qaydMuqin.tasmah xs <;> cases h2 : qaydWawYa.tasmah xs <;>
    cases h3 : qaydAkhirWaw.tasmah xs <;> cases h4 : qaydAkhirYa.tasmah xs <;> cases h5 : qaydIshtibah.tasmah xs <;>
    simp [qawaid, h1, h2, h3, h4]

/-! ## ٥. القانونُ هنا هو آلةُ القانون على خلايا Mashru -/

theorem run_sawa : ∀ (xs : List Dal.Khaliya) (q : Nat), q < 97 →
    (alaMashru false).run q xs = SLGE.Law.run q (xs.map fun k => (Dal.n k).val)
  | [], _, _ => rfl
  | k :: xs, q, hq => by
    have hs := alaMashru_step false q hq k
    have hlt : SLGE.Law.δ q (Dal.n k).val < 97 := SLGE.Law.fin_close q hq _ (by have := (Dal.n k).isLt; omega)
    show (alaMashru false).run ((alaMashru false).step q k) xs = SLGE.Law.run (SLGE.Law.δ q (Dal.n k).val) _
    rw [hs]
    exact run_sawa xs _ hlt

theorem run_lt : ∀ (xs : List Dal.Khaliya) (q : Nat), q < 97 → (alaMashru false).run q xs < 97
  | [], _, hq => hq
  | k :: xs, q, hq => by
    show (alaMashru false).run ((alaMashru false).step q k) xs < 97
    rw [alaMashru_step false q hq k]
    exact run_lt xs _ (SLGE.Law.fin_close q hq _ (by have := (Dal.n k).isLt; omega))

/-- **القانونُ في الحكم هو `alaMashru false` نفسُها** (موقوفًا عليها)، فتنطبق عليه مبرهناتُ طبقة القواعد. -/
theorem qanun_sawa (xs : List Dal.Khaliya) :
    (alaMashru false).final ((alaMashru false).run 0 xs) = qanunYaqbal xs := by
  have hlt := run_lt xs 0 (by decide)
  have hn : Nabt.Law.finalWaqf ((alaMashru false).run 0 xs) = SLGE.Law.Fwaqf ((alaMashru false).run 0 xs) :=
    (nihaya_nabt_huwa_slge ⟨_, hlt⟩).1
  show Nabt.Law.finalWaqf ((alaMashru false).run 0 xs) = _
  rw [hn, run_sawa xs 0 (by decide)]
  rfl

/-- **غيرُ الممنوع تقبله آلةُ القانون مع كلّ قاعدةٍ من الأربع.** -/
theorem ghayrMamnu_maan (xs : List Dal.Khaliya) (h : hukm xs = .ghayrMamnu) :
    ∀ r ∈ qawaid, (maan (alaMashru false) r.ala).final ((maan (alaMashru false) r.ala).run (0, .awwal) xs) = true := by
  intro r hr
  obtain ⟨h0, h1, _⟩ := (ghayrMamnu_iff xs).1 h
  rw [maan_tasmah, qanun_sawa, h0, h1 r hr]
  rfl

/-! ## ٦. حكما الألف: القانونُ يمنعهما أصلًا (1216، 1222) -/

theorem la_wahid_baad_haraka : ∀ q < 97, ∀ a < 116, a % 4 ≠ 0 → SLGE.Law.δ q a ≠ 1 := by decide +kernel

theorem alif_mayyit : ∀ q < 97, q ≠ 1 → SLGE.Law.δ q 11 = 96 := by decide +kernel

theorem run_le : ∀ (l : List Nat) (q : Nat), q ≤ 96 → SLGE.Law.run q l ≤ 96
  | [], _, hq => hq
  | a :: l, q, _ => run_le l _ (SLGE.Law.δ_le q a)

/-- الألفُ الساكنة (الخليّةُ 11). -/
def alifSakina : Dal.Khaliya := Dal.fakk ⟨11, by decide⟩

/-- **الألفُ بعد غير الفتحة يردّها القانون** حيثما وقعت: بعد الضمّة والكسرة (1216، 1222)، وبعد الساكن ومنه ياءُ التصغير (1216). -/
theorem alif_baad_ghayr_fatha (pre : List Dal.Khaliya) (c : Dal.Khaliya) (post : List Dal.Khaliya)
    (hc : c.hala.val ≠ 0) : qanunYaqbal (pre ++ c :: alifSakina :: post) = false := by
  unfold qanunYaqbal
  rw [List.map_append, SLGE.Law.run_append]
  have hq := run_le (pre.map fun k => (Dal.n k).val) 0 (by decide)
  generalize SLGE.Law.run 0 (pre.map fun k => (Dal.n k).val) = q at hq
  have hdead : SLGE.Law.δ (SLGE.Law.δ q (Dal.n c).val) 11 = 96 := by
    by_cases h96 : q = 96
    · subst h96; rw [SLGE.Law.δ_big _ (Nat.le_refl 96), SLGE.Law.δ_big _ (Nat.le_refl 96)]
    · have hq' : q < 97 := by omega
      have hn : (Dal.n c).val % 4 ≠ 0 := by simp only [Dal.n]; omega
      have hnl : (Dal.n c).val < 116 := (Dal.n c).isLt
      have h1 := la_wahid_baad_haraka q hq' _ hnl hn
      have hle := SLGE.Law.δ_le q (Dal.n c).val
      by_cases h96' : SLGE.Law.δ q (Dal.n c).val = 96
      · rw [h96']; exact SLGE.Law.δ_big _ (Nat.le_refl 96)
      · exact alif_mayyit _ (by omega) h1
  show SLGE.Law.Fwaqf (SLGE.Law.run (SLGE.Law.δ (SLGE.Law.δ q (Dal.n c).val) (Dal.n alifSakina).val) _) = false
  have ha : (Dal.n alifSakina).val = 11 := by decide
  rw [ha, hdead, SLGE.Law.run_dead]
  rfl

/-! ## ٧. الموضعُ الممنوع يردّ الكلمة حيثما وقع -/

theorem sira_snoc {A : Type} (r : Qayd A) (c : Fin r.k) (xs : List A) (a : A) :
    r.sira c (xs ++ [a]) = r.sinf (r.sira c xs) a := by
  simp only [Qayd.sira, List.foldl_append, List.foldl_cons, List.foldl_nil]

theorem tasmah_mamnu_hukm (xs : List Dal.Khaliya) (r : Qayd Dal.Khaliya) (hr : r ∈ qawaid) (h : r.tasmah xs = false) :
    ∃ s, hukm xs = .mamnu s :=
  (mamnu_iff xs).2 (Or.inr ⟨r, hr, h⟩)

/-- القيدُ لا يسمح بكلمةٍ تنتهي على صنفٍ خاتمته `true`. -/
theorem tasmahBaad_khatima {A : Type} (r : Qayd A) : ∀ (pre : List A) (c : Fin r.k) (x : A),
    r.khatima (r.sinf (r.sira c pre) x) = true → r.tasmahBaad c (pre ++ [x]) = false
  | [], c, x, h => by
    simp [Qayd.tasmahBaad, Qayd.sira] at h ⊢
    simp [h]
  | y :: pre, c, x, h => by
    simp only [List.cons_append, Qayd.tasmahBaad]
    rw [tasmahBaad_khatima r pre (r.sinf c y) x h, Bool.and_false]

/-- صنفُ «موقن» بعد خليّةٍ مضمومة: 1 أيًّا كان ما قبلها. -/
theorem sinf_muqin_damma (c : Fin qaydMuqin.k) (a : Dal.Khaliya) (ha : a.hala.val = 1) :
    (qaydMuqin.sinf c a).val = 1 := by
  have hy : yaSakina a = false := by simp [yaSakina, ha]
  simp [qaydMuqin, hy, sinfDamma, ha]

/-- **الياءُ الساكنة بعد الضمّة، لا تليها ياءٌ متحرّكة، تُمنع حيثما وقعت** (1222). -/
theorem yaBadDamma_yamna (pre : List Dal.Khaliya) (c y d : Dal.Khaliya) (post : List Dal.Khaliya)
    (hc : c.hala.val = 1) (hy : yaSakina y = true) (hd : yaMutaharrika d = false) :
    ∃ s, hukm (pre ++ c :: y :: d :: post) = .mamnu s := by
  apply tasmah_mamnu_hukm _ qaydMuqin (by simp [qawaid])
  have hm : ∀ c0 : Fin qaydMuqin.k, c0.val = 1 → qaydMuqin.mamnu (qaydMuqin.sinf c0 y) d = true := by
    intro c0 h0
    have h2 : (qaydMuqin.sinf c0 y).val = 2 := by
      simp [qaydMuqin, h0, hy]
    generalize qaydMuqin.sinf c0 y = x at h2
    simp [qaydMuqin, h2, hd]
  cases pre with
  | nil =>
    have hs : (qaydMuqin.awwalSinf c).val = 1 := by
      show (sinfDamma c).val = 1
      simp [sinfDamma, hc]
    have := tasmah_mamnu qaydMuqin c [y] d post (hm _ hs)
    simpa using this
  | cons a pre =>
    have := tasmah_mamnu qaydMuqin a (pre ++ [c, y]) d post (by
      rw [show pre ++ [c, y] = (pre ++ [c]) ++ [y] by simp, sira_snoc, sira_snoc]
      exact hm _ (sinf_muqin_damma _ _ hc))
    simpa using this

/-- **الياءُ الساكنة بعد الضمّة آخرَ الكلمة تُمنع** (1222): لا ياءَ متحرّكةً بعدها. -/
theorem yaBadDamma_akhir (pre : List Dal.Khaliya) (c y : Dal.Khaliya) (hc : c.hala.val = 1) (hy : yaSakina y = true) :
    ∃ s, hukm (pre ++ [c, y]) = .mamnu s := by
  apply tasmah_mamnu_hukm _ qaydMuqin (by simp [qawaid])
  have hk : ∀ c0 : Fin qaydMuqin.k, c0.val = 1 → qaydMuqin.khatima (qaydMuqin.sinf c0 y) = true := by
    intro c0 h0
    have h2 : (qaydMuqin.sinf c0 y).val = 2 := by
      simp [qaydMuqin, h0, hy]
    generalize qaydMuqin.sinf c0 y = x at h2
    simp [qaydMuqin, h2]
  cases pre with
  | nil =>
    have hs : (qaydMuqin.awwalSinf c).val = 1 := by
      show (sinfDamma c).val = 1
      simp [sinfDamma, hc]
    have := tasmahBaad_khatima qaydMuqin [] (qaydMuqin.awwalSinf c) y (hk _ hs)
    simp only [List.nil_append] at this
    simp [Qayd.tasmah, this]
  | cons a pre =>
    have := tasmahBaad_khatima qaydMuqin (pre ++ [c]) (qaydMuqin.awwalSinf a) y (by
      rw [sira_snoc]
      exact hk _ (sinf_muqin_damma _ _ hc))
    simp only [List.append_assoc, List.singleton_append] at this
    simp [Qayd.tasmah, this]

/-- صنفُ قاعدة الواو والياء بعد خليّةٍ مفتوحةٍ أو مكسورة: 1 أو 3 أيًّا كان ما قبلها. -/
theorem sinf_wawYa_haraka (c : Fin qaydWawYa.k) (a : Dal.Khaliya) (ha : a.hala.val = 0 ∨ a.hala.val = 2) :
    (qaydWawYa.sinf c a).val = 1 ∨ (qaydWawYa.sinf c a).val = 3 := by
  have hw : wawSakina a = false := by rcases ha with h | h <;> simp [wawSakina, h]
  have hy : yaSakina a = false := by rcases ha with h | h <;> simp [yaSakina, h]
  rcases ha with h | h <;> simp [qaydWawYa, hw, hy, sinfHaraka, h] <;> decide

/-- **الواوُ الساكنة بعد فتحةٍ أو كسرة، تليها ياءٌ متحرّكة، تُمنع حيثما وقعت** (1238–1239). -/
theorem wawYa_yamna (pre : List Dal.Khaliya) (c w y : Dal.Khaliya) (post : List Dal.Khaliya)
    (hc : c.hala.val = 0 ∨ c.hala.val = 2) (hw : wawSakina w = true) (hy : yaMutaharrika y = true) :
    ∃ s, hukm (pre ++ c :: w :: y :: post) = .mamnu s := by
  apply tasmah_mamnu_hukm _ qaydWawYa (by simp [qawaid])
  have hm : ∀ c0 : Fin qaydWawYa.k, c0.val = 1 ∨ c0.val = 3 → qaydWawYa.mamnu (qaydWawYa.sinf c0 w) y = true := by
    intro c0 h0
    have h4 : (qaydWawYa.sinf c0 w).val = 4 := by
      rcases h0 with h | h <;> simp [qaydWawYa, h, hw] <;> decide
    generalize qaydWawYa.sinf c0 w = x at h4
    simp [qaydWawYa, h4, hy]
  cases pre with
  | nil =>
    have hs : (qaydWawYa.awwalSinf c).val = 1 ∨ (qaydWawYa.awwalSinf c).val = 3 := by
      show (sinfHaraka c).val = 1 ∨ (sinfHaraka c).val = 3
      rcases hc with h | h <;> simp [sinfHaraka, h] <;> decide
    have := tasmah_mamnu qaydWawYa c [w] y post (hm _ hs)
    simpa using this
  | cons a pre =>
    have := tasmah_mamnu qaydWawYa a (pre ++ [c, w]) y post (by
      rw [show pre ++ [c, w] = (pre ++ [c]) ++ [w] by simp, sira_snoc, sira_snoc]
      exact hm _ (sinf_wawYa_haraka _ _ hc))
    simpa using this

/-- صنفُ قاعدة الواو والياء بعد خليّةٍ مفتوحةٍ أو مضمومة: 1 أو 2 أيًّا كان ما قبلها. -/
theorem sinf_wawYa_fatha_damma (c : Fin qaydWawYa.k) (a : Dal.Khaliya) (ha : a.hala.val = 0 ∨ a.hala.val = 1) :
    (qaydWawYa.sinf c a).val = 1 ∨ (qaydWawYa.sinf c a).val = 2 := by
  have hw : wawSakina a = false := by rcases ha with h | h <;> simp [wawSakina, h]
  have hy : yaSakina a = false := by rcases ha with h | h <;> simp [yaSakina, h]
  rcases ha with h | h <;> simp [qaydWawYa, hw, hy, sinfHaraka, h] <;> decide

/-- **الياءُ الساكنة بعد فتحةٍ أو ضمّة، تليها واوٌ متحرّكة، تُمنع حيثما وقعت** (1238–1239؛ جهةُ «سَيْوِد»). -/
theorem yaWaw_yamna (pre : List Dal.Khaliya) (c y w : Dal.Khaliya) (post : List Dal.Khaliya)
    (hc : c.hala.val = 0 ∨ c.hala.val = 1) (hy : yaSakina y = true) (hw : wawMutaharrika w = true) :
    ∃ s, hukm (pre ++ c :: y :: w :: post) = .mamnu s := by
  apply tasmah_mamnu_hukm _ qaydWawYa (by simp [qawaid])
  have hws : wawSakina y = false := by
    simp [yaSakina] at hy
    simp [wawSakina, hy.1]
  have hm : ∀ c0 : Fin qaydWawYa.k, c0.val = 1 ∨ c0.val = 2 → qaydWawYa.mamnu (qaydWawYa.sinf c0 y) w = true := by
    intro c0 h0
    have h5 : (qaydWawYa.sinf c0 y).val = 5 := by
      rcases h0 with h | h <;> simp [qaydWawYa, h, hy, hws] <;> decide
    generalize qaydWawYa.sinf c0 y = x at h5
    simp [qaydWawYa, h5, hw]
  cases pre with
  | nil =>
    have hs : (qaydWawYa.awwalSinf c).val = 1 ∨ (qaydWawYa.awwalSinf c).val = 2 := by
      show (sinfHaraka c).val = 1 ∨ (sinfHaraka c).val = 2
      rcases hc with h | h <;> simp [sinfHaraka, h] <;> decide
    have := tasmah_mamnu qaydWawYa c [y] w post (hm _ hs)
    simpa using this
  | cons a pre =>
    have := tasmah_mamnu qaydWawYa a (pre ++ [c, y]) w post (by
      rw [show pre ++ [c, y] = (pre ++ [c]) ++ [y] by simp, sira_snoc, sira_snoc]
      exact hm _ (sinf_wawYa_fatha_damma _ _ hc))
    simpa using this

theorem akhir_mamnu (h : Nat) (harf : Dal.Khaliya → Bool) (c : Fin (qaydAkhir h harf).k) (a : Dal.Khaliya) :
    (qaydAkhir h harf).mamnu c a = false := rfl

/-- قاعدةُ الآخر: بعد خليّةٍ بالحركة `h` الصنفُ 1 أو 3 أيًّا كان ما قبلها. -/
theorem akhir_sinf_haraka (h : Nat) (harf : Dal.Khaliya → Bool) (c : Fin (qaydAkhir h harf).k) (a : Dal.Khaliya)
    (ha : a.hala.val = h) : ((qaydAkhir h harf).sinf c a).val = 1 ∨ ((qaydAkhir h harf).sinf c a).val = 3 := by
  show (sinfAkhir h harf c a).val = 1 ∨ (sinfAkhir h harf c a).val = 3
  unfold sinfAkhir
  by_cases hb : ((c.val == 1 || c.val == 3) && harf a) = true <;> simp [hb, ha] <;> decide

/-- قاعدةُ الآخر: الحرفُ المتحرّكُ بعد الصنف 1 أو 3 يُدخل صنفًا لا تنتهي عليه الكلمة. -/
theorem akhir_sinf_khatima (h : Nat) (harf : Dal.Khaliya → Bool) (c : Fin (qaydAkhir h harf).k) (a : Dal.Khaliya)
    (hc : c.val = 1 ∨ c.val = 3) (ha : harf a = true) :
    (qaydAkhir h harf).khatima ((qaydAkhir h harf).sinf c a) = true := by
  have hs : ((qaydAkhir h harf).sinf c a).val = 2 ∨ ((qaydAkhir h harf).sinf c a).val = 3 := by
    show (sinfAkhir h harf c a).val = 2 ∨ (sinfAkhir h harf c a).val = 3
    unfold sinfAkhir
    rcases hc with hc | hc <;> by_cases hh : a.hala.val = h <;> simp [hc, ha, hh] <;> decide
  generalize (qaydAkhir h harf).sinf c a = x at hs
  rcases hs with hs | hs <;> simp [qaydAkhir, hs]

theorem tasmahBaad_akhir (h : Nat) (harf : Dal.Khaliya → Bool) :
    ∀ (pre : List Dal.Khaliya) (c0 : Fin (qaydAkhir h harf).k) (c a : Dal.Khaliya), c.hala.val = h → harf a = true →
      (qaydAkhir h harf).tasmahBaad c0 (pre ++ [c, a]) = false
  | [], c0, c, a, hc, ha => by
    simp only [List.nil_append, Qayd.tasmahBaad, akhir_mamnu,
      akhir_sinf_khatima h harf _ a (akhir_sinf_haraka h harf c0 c hc) ha]
    rfl
  | x :: pre, c0, c, a, hc, ha => by
    simp only [List.cons_append, Qayd.tasmahBaad, akhir_mamnu, tasmahBaad_akhir h harf pre _ c a hc ha]
    rfl

theorem tasmah_akhir (h : Nat) (harf : Dal.Khaliya → Bool) (pre : List Dal.Khaliya) (c a : Dal.Khaliya)
    (hc : c.hala.val = h) (ha : harf a = true) : (qaydAkhir h harf).tasmah (pre ++ [c, a]) = false := by
  cases pre with
  | nil =>
    have hs : ((qaydAkhir h harf).awwalSinf c).val = 1 ∨ ((qaydAkhir h harf).awwalSinf c).val = 3 := by
      simp [qaydAkhir, hc]
    simp only [List.nil_append, Qayd.tasmah, Qayd.tasmahBaad, akhir_mamnu, akhir_sinf_khatima h harf _ a hs ha]
    rfl
  | cons x pre =>
    simp only [List.cons_append, Qayd.tasmah, tasmahBaad_akhir h harf pre _ c a hc ha]
    rfl

/-- **الحرفُ المتحرّكُ بعد الحركة آخرَ الكلمة يُمنع** في قاعدتي الآخر: الواوُ بعد الكسرة (1216–1217) والياءُ بعد الضمّة (1225). -/
theorem akhir_yamna (pre : List Dal.Khaliya) (c a : Dal.Khaliya) :
    (c.hala.val = 2 → wawMutaharrika a = true → ∃ s, hukm (pre ++ [c, a]) = .mamnu s) ∧
    (c.hala.val = 1 → yaMutaharrika a = true → ∃ s, hukm (pre ++ [c, a]) = .mamnu s) :=
  ⟨fun hc ha => tasmah_mamnu_hukm _ qaydAkhirWaw (by simp [qawaid]) (tasmah_akhir 2 wawMutaharrika pre c a hc ha),
    fun hc ha => tasmah_mamnu_hukm _ qaydAkhirYa (by simp [qawaid]) (tasmah_akhir 1 yaMutaharrika pre c a hc ha)⟩

/-! ## ٧ب. المدُّ تليه الأخرى متحرّكةً ليس غيرَ ممنوع (الاشتباه) -/

/-- حركةُ صنف الاشتباه بعد خليّةٍ غيرِ ساكنة هي حركتُها، أيًّا كان ما قبلها. -/
theorem haraka_sinfIshtibah (c0 : Fin 12) (a : Dal.Khaliya) (ha : a.hala.val ≠ 3) :
    haraktuSinf (sinfIshtibah c0 a) = a.hala.val := by
  have hw : wawSakina a = false := by simp [wawSakina, ha]
  have hy : yaSakina a = false := by simp [yaSakina, ha]
  have hlt := a.hala.isLt
  unfold sinfIshtibah
  simp only [hw, hy, Bool.and_false, Bool.false_eq_true, ite_false]
  repeat' split
  all_goals simp only [haraktuSinf]
  all_goals (repeat' split) <;> omega

/-- **المدُّ تليه الأخرى متحرّكةً لا يكون غيرَ ممنوع** (`qaydIshtibah`؛ 1238 «ومن عروض»): الواوُ الساكنة بعد الضمّة تليها ياءٌ متحرّكة، والياءُ
    الساكنة بعد الكسرة تليها واوٌ متحرّكة؛ فالحكمُ «لا حكم» أو ممنوعٌ بغيره. -/
theorem madd_la_ghayrMamnu (pre : List Dal.Khaliya) (c m d : Dal.Khaliya) (post : List Dal.Khaliya)
    (h : (c.hala.val = 1 ∧ wawSakina m = true ∧ yaMutaharrika d = true) ∨
      (c.hala.val = 2 ∧ yaSakina m = true ∧ wawMutaharrika d = true)) :
    hukm (pre ++ c :: m :: d :: post) ≠ .ghayrMamnu := by
  intro hg
  have hi := ((ghayrMamnu_iff _).1 hg).2.2
  have hc3 : c.hala.val ≠ 3 := by rcases h with ⟨h1, _⟩ | ⟨h1, _⟩ <;> omega
  have hm : ∀ c1 : Fin qaydIshtibah.k, haraktuSinf c1 = c.hala.val →
      qaydIshtibah.mamnu (qaydIshtibah.sinf c1 m) d = true := by
    intro c1 h1
    rcases h with ⟨hc, hw, hy⟩ | ⟨hc, hy, hw⟩
    · have h4 : (qaydIshtibah.sinf c1 m).val = 4 := by
        show (sinfIshtibah c1 m).val = 4
        simp [sinfIshtibah, h1, hc, hw] <;> decide
      generalize qaydIshtibah.sinf c1 m = x at h4
      simp [qaydIshtibah, h4, hy]
    · have hws : wawSakina m = false := by
        simp [yaSakina] at hy
        simp [wawSakina, hy.1]
      have h5 : (qaydIshtibah.sinf c1 m).val = 5 := by
        show (sinfIshtibah c1 m).val = 5
        simp [sinfIshtibah, h1, hc, hy, hws] <;> decide
      generalize qaydIshtibah.sinf c1 m = x at h5
      simp [qaydIshtibah, h5, hw]
  have hf : qaydIshtibah.tasmah (pre ++ c :: m :: d :: post) = false := by
    cases pre with
    | nil =>
      have hs : haraktuSinf (qaydIshtibah.awwalSinf c) = c.hala.val := by
        show haraktuSinf ⟨c.hala.val, _⟩ = c.hala.val
        have := c.hala.isLt
        simp only [haraktuSinf]; split <;> omega
      have := tasmah_mamnu qaydIshtibah c [m] d post (hm _ hs)
      simpa using this
    | cons a pre =>
      have := tasmah_mamnu qaydIshtibah a (pre ++ [c, m]) d post (by
        rw [show pre ++ [c, m] = (pre ++ [c]) ++ [m] by simp, sira_snoc, sira_snoc]
        exact hm _ (haraka_sinfIshtibah _ _ hc3))
      simpa using this
  rw [hf] at hi
  exact Bool.false_ne_true hi

/-! ## ٨. شواهدُ الأبيات: خلايا الكلمات كما يُخرجها القارئ (`qari --khalaya`؛ يقابلها `tahaqquq/test_ibdal.py`) -/

def k (l : List Nat) : List Dal.Khaliya := l.map fakkN

/-- أمثلةُ الأبيات وأصولُها قبل الإبدال، وصورٌ يحكم فيها البيتُ أو يستثنيها؛ بخلاياها وحكمِها المتوقَّع من الشفرة. -/
def shawahid : List (String × List Nat × Hukm) := [
  ("مُوقِنٌ", [109, 115, 30, 57, 59], .ghayrMamnu),
  ("مُيْقِنٌ", [109, 47, 30, 57, 59], .mamnu .yaBadDamma),
  ("هِيمٌ", [6, 47, 109, 59], .ghayrMamnu),
  ("هُيْمٌ", [5, 47, 109, 59], .mamnu .yaBadDamma),
  ("سَيِّدٌ", [80, 47, 46, 69, 59], .ghayrMamnu),
  ("سَيْوِدٌ", [80, 47, 114, 69, 59], .mamnu .wawYa),
  ("طَيٌّ", [64, 47, 45, 59], .ghayrMamnu),
  ("طَوْيٌ", [64, 115, 45, 59], .mamnu .wawYa),
  ("رَضِيَ", [60, 50, 44], .ghayrMamnu),
  ("رَضِوَ", [60, 50, 112], .mamnu .akhirWaw),
  ("نَهُوَ", [56, 5, 112], .ghayrMamnu),
  ("نَهُيَ", [56, 5, 44], .mamnu .akhirYa),
  ("زُيِّنَ", [77, 47, 46, 56], .ghayrMamnu),
  ("بُويِعَ", [105, 115, 46, 12], .laHukm),
  ("ضُارِبَ", [49, 11, 62, 104], .mamnu .qanun)]

/-- **الحكمُ على شواهد الأبيات** كما في الجدول. -/
theorem shawahid_hukm : shawahid.all (fun s => hukm (k s.2.1) == s.2.2) = true := by decide +kernel

/-! ## ٩. كلُّ قاعدةٍ تحذف من كلمات القانون بطول مثالها -/

theorem fakkN_mem (m : Nat) : fakkN m ∈ khalayaKull := by
  unfold khalayaKull fakkN
  exact List.mem_map.2 ⟨_, List.mem_finRange _, rfl⟩

theorem yahdhif (r : Qayd Dal.Khaliya) (l : List Nat) (hq : qanunYaqbal (k l) = true) (hr : r.tasmah (k l) = false) :
    lenCount (maan (alaMashru false) r.ala) khalayaKull l.length (0, .awwal) < lawCount false l.length := by
  have hle := qanun_qaida_le false r l.length
  have hne : lenCount (maan (alaMashru false) r.ala) khalayaKull l.length (0, .awwal) ≠ lawCount false l.length := by
    intro he
    have := (qanun_qaida_eq_iff false r l.length).1 he (k l) (by simp [k])
      (fun a ha => by
        obtain ⟨m, _, rfl⟩ := List.mem_map.1 ha
        exact fakkN_mem m)
      (by rw [qanun_sawa]; exact hq)
    rw [hr] at this
    exact Bool.false_ne_true this
  omega

/-- «مُيْقِنٌ» (1222): قاعدةُ «موقن» تحذف من كلمات القانون ذات الخمس خلايا. -/
theorem muqin_yahdhif :
    lenCount (maan (alaMashru false) qaydMuqin.ala) khalayaKull 5 (0, .awwal) < lawCount false 5 :=
  yahdhif qaydMuqin [109, 47, 30, 57, 59] (by decide +kernel) (by decide +kernel)

/-- «سَيْوِدٌ» (1238): قاعدةُ الواو والياء تحذف من كلمات القانون ذات الخمس خلايا. -/
theorem wawYa_yahdhif :
    lenCount (maan (alaMashru false) qaydWawYa.ala) khalayaKull 5 (0, .awwal) < lawCount false 5 :=
  yahdhif qaydWawYa [80, 47, 114, 69, 59] (by decide +kernel) (by decide +kernel)

/-- «رَضِوَ» (1216–1217): قاعدةُ الواو آخرًا تحذف من كلمات القانون ذات الثلاث خلايا. -/
theorem akhirWaw_yahdhif :
    lenCount (maan (alaMashru false) qaydAkhirWaw.ala) khalayaKull 3 (0, .awwal) < lawCount false 3 :=
  yahdhif qaydAkhirWaw [60, 50, 112] (by decide +kernel) (by decide +kernel)

/-- «نَهُيَ» (1225): قاعدةُ الياء آخرًا تحذف من كلمات القانون ذات الثلاث خلايا. -/
theorem akhirYa_yahdhif :
    lenCount (maan (alaMashru false) qaydAkhirYa.ala) khalayaKull 3 (0, .awwal) < lawCount false 3 :=
  yahdhif qaydAkhirYa [56, 5, 44] (by decide +kernel) (by decide +kernel)

end Jisr.IbdalAlfiyya
