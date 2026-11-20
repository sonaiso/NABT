/-
  Aql/WaqiRibt.lean — أوّلُ «مفهوم» من واقعٍ مختوم: الحكمُ على أسطر «جدول الربط — القطعة الأولى».

  **القرار.** قولُ المالك في الجلسة 2026-10-29 (02:05 بتوقيت عمّان): «إيداع جدول ربطٍ مختوم بين المعنى وقضيّة الواقع، حتى يظهر
  أول «مفهوم» حقيقيّ … انت مفوض بشكل مطلق … نفذ واكمل البرهان استعدادا للاطلاق التجريبي»، والبندُ الأوّل من جواب البنّاء ألصقه.
  والتصميمُ قرارُ البنّاء: الجدولُ مولَّدٌ آليًّا (`scripts/bina_ribt.py`) من «جدول التعريفات» المختوم (عمودُ صفوف الواقع الشاهدة)
  ومن «الواقع المختوم — الدفعة الأولى» (`Waqi.Jadwal`)، فلا يختار البنّاءُ صفًّا؛ وخُتم «وضعًا» في `mudaat/sijill.json`، وأسطرُه أسطرُ
  `shahid` في `mudaat/sijill.tsv` المختوم (`Faahis.sijillMakhtum`).

  **الصورة.** تحت أيّ سجلٍّ يختم الدفعةَ «واقعًا» (`makhtum_jadwal`) يكون الحكمُ على قضيّةٍ هو حكمُها على صفوف الدفعة بلا شرط ختم
  (`hukm_jadwal`). فعلى أسطر الربط الواحد والثلاثين: عشرةُ معانٍ «مفهوم» وأربعةٌ «معلومة» (`mafahim_ribt`، `maalumat_ribt`)، ومعنى
  الصفّ الأوّل («Mashru») مفهومٌ بقياس «معرّف الإيداع المرصود» (`mafhum_mashru`)؛ وحكمُ السطر هو `Waqi.hukm` تحت كلّ سجلٍّ يختم الدفعة
  (`hukm_satr`)؛ وبلا ختم الدفعة لا مفهوم (`la_mafhum_bila_khatm_dafa`، من `Waqi.la_mafhum_bila_khatm`).

  **حدُّه.** أنّ `Faahis.shuhudBina` على `tahmil sijillMakhtum` يمرّر هذه الأسطرَ بعينها وهذا السجلّ مفحوصٌ بالتشغيل
  (`mawsua/test_mawsua.py` §١٩) لا مبرهن: تحليلُ أسطر السجلّ في النواة لا يُحسب هنا؛ وكذلك أنّ حذفَ أسطر الربط يُسقط المفهوم. والربطُ (أيُّ قضيّةٍ واقعُ أيِّ معنى) تعيينٌ
  مختومٌ لا يُبرهن.
-/
import Aql.WaqiJadwal
import Aql.WaqiRibtJadwal

namespace Waqi.Ribt

open Waqi

/-- كلُّ نصٍّ يبدأ بنفسه. -/
theorem startsWith_nafsuh (s : String) : s.startsWith s = true := by
  show s.toSlice.startsWith s = true
  rw [String.Slice.startsWith_string_eq_startsWith_toSlice]
  simp

/-- السجلُّ الذي يختم الدفعةَ «واقعًا» يجعل كلَّ صفوفها مختومة. -/
theorem makhtum_jadwal (sijill : List (String × Idaa.Naw)) (hs : (Jadwal.basma, Idaa.Naw.waqiMakhtum) ∈ sijill) :
    makhtum sijill Jadwal.basma = true := by
  unfold makhtum
  refine List.any_eq_true.mpr ⟨_, hs, ?_⟩
  rw [startsWith_nafsuh]
  simp [Jadwal.basma]

/-- **الحكمُ تحت الختم حكمُ الصفوف**: لا يُسقط الختمُ صفًّا من الدفعة. -/
theorem hukm_jadwal (sijill : List (String × Idaa.Naw)) (hs : (Jadwal.basma, Idaa.Naw.waqiMakhtum) ∈ sijill)
    (T : List Mushahada) (m s q : String) :
    hukm sijill (fun _ => Jadwal.basma) T m s q =
      if fiihiQiyas (mutabiq T m s q) || tawatur (mutabiq T m s q) then .mafhum
      else if (mutabiq T m s q).isEmpty then .laHukm else .maaluma := by
  have : makhtuma sijill (fun _ => Jadwal.basma) (mutabiq T m s q) = mutabiq T m s q := by
    simp [makhtuma, makhtum_jadwal sijill hs]
  simp only [hukm, this]

/-- حكمُ السطر: حكمُ قضيّته على صفوف الدفعة بلا شرط ختم؛ وهو حكمُها تحت كلّ سجلٍّ يختم الدفعة (`hukm_satr`). -/
def hukmSatr (r : String × String × String × String) : Hukm :=
  let l := mutabiq Jadwal.jadwal r.2.1 r.2.2.1 r.2.2.2
  if fiihiQiyas l || tawatur l then .mafhum else if l.isEmpty then .laHukm else .maaluma

/-- **حكمُ السطر هو حكمُ `Waqi.hukm`** تحت كلّ سجلٍّ يختم الدفعة. -/
theorem hukm_satr (sijill : List (String × Idaa.Naw)) (hs : (Jadwal.basma, Idaa.Naw.waqiMakhtum) ∈ sijill)
    (r : String × String × String × String) :
    hukm sijill (fun _ => Jadwal.basma) Jadwal.jadwal r.2.1 r.2.2.1 r.2.2.2 = hukmSatr r := by
  rw [hukm_jadwal sijill hs]; rfl

/-- معنى الصفّ `i` (برقمه نصًّا) من جدول التعريفات كما يسمّيه الجدول. -/
def maana (i : String) : String := "ما عرّفه جدول التعريفات في صفّه " ++ i

/-- **المعاني المفهومة**: ما له في الجدول سطرٌ حكمُ قضيّته «مفهوم». -/
def mafahim : List String :=
  ((ribt.filter fun r => hukmSatr r == .mafhum).map (·.1)).eraseDups

/-- **المعاني المعلومة**: ما كلُّ سطرٍ له في الجدول حكمُه «معلومة». -/
def maalumat : List String :=
  ((ribt.map (·.1)).eraseDups).filter fun m => (ribt.filter (·.1 == m)).all fun r => hukmSatr r == .maaluma

set_option maxRecDepth 100000 in
/-- **عشرةُ معانٍ مفهومة** بأسطر الجدول (على الشاهد؛ وتحت كلّ سجلٍّ يختم الدفعة بـ`hukm_satr`). -/
theorem mafahim_ribt : mafahim = ["1", "8", "9", "12", "13", "14", "18", "20", "21", "22"].map maana := by
  simp [mafahim, ribt, hukmSatr, mutabiq, Jadwal.jadwal, fiihiQiyas, tawatur, maana, List.eraseDups_cons]

set_option maxRecDepth 100000 in
/-- **وأربعةٌ معلومة**: كلُّ أسطرها «معلومة» (على الشاهد). وأنّ قضاياها رواياتٌ من مصدرٍ واحد قراءةُ صفوف الدفعة، لا تقولها المبرهنة. -/
theorem maalumat_ribt : maalumat = ["11", "15", "16", "17"].map maana := by
  simp [maalumat, mafahim, ribt, hukmSatr, mutabiq, Jadwal.jadwal, fiihiQiyas, tawatur, maana, List.eraseDups_cons]

/-- **أوّلُ مفهوم**: «Mashru» (معنى الصفّ الأوّل) مربوطٌ بقضيّة «معرّف الإيداع المرصود»، وحكمُها «مفهوم» تحت كلّ سجلٍّ يختم الدفعة —
    بقياسٍ واحدٍ (الصفّ 2) عبر `Waqi.qiyas_makhtum_mafhum`. -/
theorem mafhum_mashru (sijill : List (String × Idaa.Naw)) (hs : (Jadwal.basma, Idaa.Naw.waqiMakhtum) ∈ sijill) :
    (maana "1", "مستودع:Mashru", "معرّف الإيداع المرصود", "2608833b25594379e87b580878ab7556b42c18ad") ∈ ribt ∧
    hukm sijill (fun _ => Jadwal.basma) Jadwal.jadwal "مستودع:Mashru" "معرّف الإيداع المرصود"
      "2608833b25594379e87b580878ab7556b42c18ad" = .mafhum := by
  refine ⟨by simp [ribt, maana], ?_⟩
  exact qiyas_makhtum_mafhum sijill _ Jadwal.jadwal
    ⟨1, 2, "git", "git: حسابٌ محلّيّ", "مستودع:Mashru", "معرّف الإيداع المرصود",
      "2608833b25594379e87b580878ab7556b42c18ad", .qiyas⟩
    (by unfold Jadwal.jadwal; exact List.Mem.tail _ (List.Mem.head _)) rfl (makhtum_jadwal sijill hs)

/-- **وبلا ختمِ الدفعة لا مفهوم** لأيّ قضيّةٍ عليها (`Waqi.la_mafhum_bila_khatm` على هذه الدفعة). وختمُ جدول الربط نفسِه لا يمثّله Lean:
    أنّ حذفَ أسطره من السجلّ يُسقط المفهومَ مفحوصٌ (`mawsua/test_mawsua.py` §١٩). -/
theorem la_mafhum_bila_khatm_dafa (sijill : List (String × Idaa.Naw)) (hs : ∀ e ∈ sijill, e.2 ≠ .waqiMakhtum)
    (r : String × String × String × String) :
    hukm sijill (fun _ => Jadwal.basma) Jadwal.jadwal r.2.1 r.2.2.1 r.2.2.2 ≠ .mafhum :=
  la_mafhum_bila_khatm sijill hs _ _ _ _ _

end Waqi.Ribt
