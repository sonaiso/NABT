import A116.Iqtiran
import A116.TashkilData

/-!
# تشكيلُ النصّ غير المشكول بمرشَّحي الوضع، بلا تخمين (ADR ١٠٣)

أمرُ المالك (2026-10-17): «تشكيل النصّ غير المشكول: خارج النطاق حتى الآن، قرارك. اعمل lean نفذ».

## ما يُبنى

التشكيلُ اقترانٌ (ADR ٩٨) على مستوى الدالّ:
* الهيكلُ بلا علامات دالٌّ ناقص.
* مرشَّحوه صورُه المشكولةُ التامّة كما وردت في المدوّنتين المختومتين: المصحف والصحيحان. هذا هو المعجم
  (`corpora/tashkil/mujam.tsv.gz`، `tools/gen_tashkil.py`).
* والحكمُ ثلاثيّ (`Iqtiran.mantuq`):
  * صورةٌ واحدة: معيَّن.
  * أكثرُ من صورة: محتمَلٌ بقائمته، لا يُختار منها شيء.
  * لا صورة: «لا حكم».

مبرهناتُه لكلّ معجمٍ وهيكل:
* `muayyan_min_mujam`: المعيَّنُ صورةٌ من صور هيكله في المعجم.
* `la_takhmin`: والمعيَّنُ لا يكون إلّا والصورةُ واحدة.
* `la_tashkil_bila_wad`: هيكلٌ لا صورةَ له «لا حكم».
* `qayd_la_yazid`: كلُّ قيدٍ يُضاف (حركاتٌ معلومة، عامل، صيغة) لا يزيد المرشَّحين، فيقطعهم ولا يخترع.

وعلى الشاهد (`decide`): «قال» معيَّنٌ «قَالَ»، و«كتب» محتمَلٌ بخمس صور، وقيدُ الحركة على الحرف الأوّل يقطعه إلى
«كَتَبَ» وحدَها.

والقياسُ المسجَّل مسبقًا على تشكيلٍ بشريٍّ محجوب (`qiyas`):
* المعيَّنُ 26.74٪ من الألفاظ، وصورتُه هي الذهبيّةُ بعينها في 62.04٪ منه.
* وبلا علامة الحرف الأخير، أي البنيةُ دون الإعراب: المعيَّنُ 47.29٪، والمطابقةُ 81.79٪.
-/

namespace A116.Tashkil

/-- المعجم: هيكلٌ ← صورُه. -/
abbrev Mujam := List (String × List String)

/-- مرشَّحو الهيكل: صورُه في المعجم، وإلّا لا شيء. -/
def marashshahun (mj : Mujam) (s : String) : List String :=
  ((mj.find? (·.1 == s)).map (·.2)).getD []

/-- التشكيلُ الثلاثيّ مع قيودٍ تقطع المرشَّحين. -/
def tashkil (mj : Mujam) (quyud : List (Iqtiran.Qayd String)) (s : String) : Iqtiran.Mantuq String :=
  Iqtiran.mantuq (Iqtiran.iqtiran (marashshahun mj s) quyud)

/-- **لا تشكيلَ بلا وضع**: هيكلٌ لا صورةَ له في المعجم «لا حكم». -/
theorem la_tashkil_bila_wad (mj : Mujam) (q : List (Iqtiran.Qayd String)) (s : String)
    (h : marashshahun mj s = []) : tashkil mj q s = .laHukm := by
  simp [tashkil, h, Iqtiran.iqtiran, Iqtiran.mantuq]

/-- **المعيَّنُ من المعجم**: صورةُ المعيَّن إحدى صور هيكله، وتستوفي كلَّ قيد. -/
theorem muayyan_min_mujam (mj : Mujam) (q : List (Iqtiran.Qayd String)) (s f : String)
    (h : tashkil mj q s = .muayyan f) :
    f ∈ marashshahun mj s ∧ ∀ r ∈ q, r.yaqbal f = true := by
  have hl := Iqtiran.la_takhmin _ f h
  have hf : f ∈ Iqtiran.iqtiran (marashshahun mj s) q := by rw [hl]; exact List.mem_singleton_self f
  exact (Iqtiran.iqtiran_iff _ _ _).mp hf

/-- **لا تخمين**: المعيَّنُ لا يكون إلّا والمرشَّحُ الباقي واحد. -/
theorem la_takhmin (mj : Mujam) (q : List (Iqtiran.Qayd String)) (s f : String)
    (h : tashkil mj q s = .muayyan f) : Iqtiran.iqtiran (marashshahun mj s) q = [f] :=
  Iqtiran.la_takhmin _ f h

/-- **القيدُ لا يزيد**: ما بقي بعد قيدٍ مضاف كان باقيًا قبله. -/
theorem qayd_la_yazid (mj : Mujam) (q : List (Iqtiran.Qayd String)) (r : Iqtiran.Qayd String)
    (s f : String) (h : f ∈ Iqtiran.iqtiran (marashshahun mj s) (q ++ [r])) :
    f ∈ Iqtiran.iqtiran (marashshahun mj s) q :=
  Iqtiran.qayd_la_yazid _ q r f h

/-! ## الشواهد -/

def mujam : Mujam := TashkilData.shawahid

/-- قيدُ الحرف الأوّل بحركته: الصورةُ تبدأ بالحرف ثمّ الحركة. -/
def qaydAwwal (harf haraka : Char) : Iqtiran.Qayd String :=
  ⟨"الحرفُ الأوّل", fun f => f.toList.take 2 == [harf, haraka]⟩

/-- **الشواهد**: «قال» معيَّنٌ «قَالَ»؛ و«كتب» محتمَلٌ بخمس صور؛ وفتحةُ الكاف تقطعه إلى «كَتَبَ»؛ و«والله» محتمَلٌ
بإعرابيه؛ وهيكلٌ ليس في الشواهد «لا حكم». -/
theorem shawahid :
    tashkil mujam [] "قال" = .muayyan "قَالَ" ∧
    (marashshahun mujam "كتب").length = 5 ∧
    tashkil mujam [qaydAwwal 'ك' 'َ'] "كتب" = .muayyan "كَتَبَ" ∧
    tashkil mujam [] "والله" = .muhtamal ["وَاللَّهُ", "وَاللَّهِ"] ∧
    tashkil mujam [] "غول" = .laHukm := by decide +kernel

/-- **القياسُ المسجَّل** (`docs/tashkil/PREREG.md`، `docs/tashkil/result.json`) على تشكيل Fadel المحجوب (106,775 لفظًا):
(البسط، المقام) لكلّ مقياس. والمعيَّنُ ليس إصابةً في كلّه: المعجمُ منتهٍ، فالصورةُ الواحدةُ فيه ليست الصورةَ الوحيدةَ
في اللغة (`MUJAM_NOT_EXHAUSTIVE`). -/
theorem qiyas :
    TashkilData.muayyan = (28552, 106775) ∧ TashkilData.muhtamal = (55547, 106775) ∧
    TashkilData.laHukm = (22676, 106775) ∧ TashkilData.exact = (17714, 28552) ∧
    TashkilData.inSet = (39813, 55547) ∧ TashkilData.coreMuayyan = (50494, 106775) ∧
    TashkilData.coreExact = (41297, 50494) ∧
    TashkilData.muayyan.1 + TashkilData.muhtamal.1 + TashkilData.laHukm.1 = TashkilData.muayyan.2 ∧
    TashkilData.exact.1 < TashkilData.exact.2 := by decide

/-- عددُ هياكل المعجم كلِّه وما له صورةٌ واحدة. -/
theorem mujam_count : TashkilData.haykalCount = 49412 ∧ TashkilData.wahidCount = 39154 := by decide

end A116.Tashkil
