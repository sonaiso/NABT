/-
  Aql/WaqiShawahid.lean — شواهدُ الحكم على الدفعة الأولى من «الواقع المختوم» (`Aql/WaqiJadwal.lean`، مولَّدٌ من waqi_001.tsv).

  الشواهدُ على سجلّين: `qabl` بلا قيدٍ «واقع مختوم» (حالُ الدفعة وهي مرشّحة، وكلُّ سجلٍّ مثلِه بـ `Waqi.la_mafhum_bila_khatm`)، و`bad`
  بقيدٍ واحد هو بصمتُها «واقعًا مختومًا». وقد خُتمت بإذن المالك 2026-10-22 (07:51)، فقيدُها في سجلّ الفاحص (`mudaat/sijill.tsv`)؛
  والحكمُ على كلّ سجلٍّ فيه قيدُها هو حكمُها على `bad` (`hukm_ala_kull_sijill`، `ihsa_ala_kull_sijill` أدناه).

  بالمعيار الموحَّد في `Nizam/Asas.lean`: 10 مبرهنات — 8 «على الشاهد» (`decide +kernel` على الجدول المولَّد) و2 لكلّ سجلّ:
  * `adad`: 50 مشاهدة، 21 قياسًا و29 رواية.
  * `ihsa`: القضايا المتمايزة 47 — قبل الختم كلُّها معلومة؛ وبعده مفهوم 20 (كلُّها بقياس) ومعلومة 27، ولا «لا حكم».
  * `python_yahsub`: بايثون يُخرج 5 لـ print(2+3) — قياسٌ بالتشغيل: معلومةٌ قبل الختم، مفهومٌ بعده.
  * `lean_yaqbal_wa_yarud`: Lean يقبل «2 + 3 = 5» (خروج 0) ويردّ «2 + 3 = 6» (خروج 1) — قياسان: مفهومان بعد الختم.
  * `basma_bihassatayn`: بصمةُ CLAUDE.md بحاسّتين (sha256sum وhashlib) متطابقتين — مفهومٌ بعد الختم.
  * `isdar_ahad`: إصدارُ Lean 4.34.1 من lean وlake — مصدرٌ واحد (حزمةٌ واحدة)، وإصدارُ بايثون 3.13.16 من python3 مرّتين — معلومتان
    ولو خُتمت الدفعة: الآحادُ لا يرفع، والتكرارُ لا يرفع.
  * `github_riwaya`: ما يرويه GitHub وحده (الفرع الافتراضيّ main) معلومةٌ ولو خُتمت؛ و«master» لا حكم، لا «ممتنع».
  * `jisr_haqiqi`: في `Maratib` بعد الختم: «بايثون يُخرج 5» مفهوم، و«إصدارُ بايثون» معلومة؛ وقبل الختم معلومة.
  * لكلّ سجلّ: `hukm_ala_kull_sijill` (حكمُ كلّ قضيّةٍ على سجلٍّ فيه قيدُ الدفعة حكمُها على `bad`)، و`ihsa_ala_kull_sijill` (على كلّ سجلٍّ
    يحوي `(basma, .waqiMakhtum)`: مفهوم 20 ومعلومة 27). وأنّ السجلّ الحقيقيّ يحويه يفحصه `tahaqquq/test_waqi.py` على `mudaat/sijill.tsv`.
  بلا sorry ولا axiom ولا native_decide.
-/
import Aql.WaqiJadwal

namespace Waqi.Shawahid

open Waqi Waqi.Jadwal

/-- سجلٌّ بلا قيدٍ «واقع مختوم» (حالُ الدفعة وهي مرشّحة، قبل ختمها 2026-10-22). -/
def qabl : List (String × Idaa.Naw) := []

/-- سجلٌّ فيه بصمةُ الدفعة «واقعًا مختومًا». -/
def bad : List (String × Idaa.Naw) := [(basma, .waqiMakhtum)]

/-- بصمةُ كلّ دفعة: دفعةٌ واحدة هنا. -/
def B : Nat → String := fun _ => basma

/-- القضايا المتمايزة في الجدول. -/
def qadaya : List (String × String × String) := (jadwal.map fun r => (r.mawdu, r.sifa, r.qima)).eraseDups

def hukmQ (S : List (String × Idaa.Naw)) (k : String × String × String) : Hukm := hukm S B jadwal k.1 k.2.1 k.2.2

theorem adad :
    jadwal.length = 50 ∧ (jadwal.filter (·.wajh == .qiyas)).length = 21 ∧
    (jadwal.filter (·.wajh == .riwaya)).length = 29 := by decide +kernel

theorem ihsa :
    qadaya.length = 47 ∧ (qadaya.map (hukmQ qabl)).count .maaluma = 47 ∧
    (qadaya.map (hukmQ bad)).count .mafhum = 20 ∧ (qadaya.map (hukmQ bad)).count .maaluma = 27 ∧
    (qadaya.map (hukmQ bad)).count .laHukm = 0 := by decide +kernel

theorem python_yahsub :
    hukm qabl B jadwal "Python" "يُخرج لـ print(2+3)" "5" = .maaluma ∧
    hukm bad B jadwal "Python" "يُخرج لـ print(2+3)" "5" = .mafhum := by decide +kernel

theorem lean_yaqbal_wa_yarud :
    hukm bad B jadwal "Lean" "رمزُ الخروج لـ «example : 2 + 3 = 5 := by decide»" "0" = .mafhum ∧
    hukm bad B jadwal "Lean" "رمزُ الخروج لـ «example : 2 + 3 = 6 := by decide»" "1" = .mafhum := by decide +kernel

theorem basma_bihassatayn :
    hukm bad B jadwal "ملفّ:CLAUDE.md@2608833" "بصمة sha256"
      "9579ffeab4b3caeb2a5989c7a73be043c2b594e5e6a5695abd47fef363faeb93" = .mafhum ∧
    (mutabiq jadwal "ملفّ:CLAUDE.md@2608833" "بصمة sha256"
      "9579ffeab4b3caeb2a5989c7a73be043c2b594e5e6a5695abd47fef363faeb93").map (·.hassa) =
      ["sha256sum", "python3-hashlib"] := by decide +kernel

theorem isdar_ahad :
    hukm bad B jadwal "Lean" "الإصدار" "4.34.1" = .maaluma ∧
    (mutabiq jadwal "Lean" "الإصدار" "4.34.1").map (·.masdar) =
      ["حزمة Lean (lean وlake بناءٌ واحد)", "حزمة Lean (lean وlake بناءٌ واحد)"] ∧
    hukm bad B jadwal "Python" "الإصدار" "3.13.16" = .maaluma ∧
    (mutabiq jadwal "Python" "الإصدار" "3.13.16").length = 2 := by decide +kernel

theorem github_riwaya :
    hukm bad B jadwal "مستودع:Mashru" "الفرع الافتراضيّ" "main" = .maaluma ∧
    hukm bad B jadwal "مستودع:Mashru" "الفرع الافتراضيّ" "master" = .laHukm := by decide +kernel

theorem jisr_haqiqi :
    (Maratib.martabatMaana 0 (Maratib.shuhudMutabara bad
      (shuhud bad B jadwal "Python" "يُخرج لـ print(2+3)" "5"))).ism = "مفهوم" ∧
    (Maratib.martabatMaana 0 (Maratib.shuhudMutabara bad
      (shuhud bad B jadwal "Python" "الإصدار" "3.13.16"))).ism = "معلومة" ∧
    (Maratib.martabatMaana 0 (Maratib.shuhudMutabara qabl
      (shuhud qabl B jadwal "Python" "يُخرج لـ print(2+3)" "5"))).ism = "معلومة" := by decide +kernel

/-- **الحكمُ واحدٌ على كلّ سجلٍّ فيه قيدُ الدفعة:** إذا كانت بصمتُها مختومةً «واقعًا» في سجلٍّ ما، فحكمُ كلّ قضيّةٍ فيه حكمُها على `bad`. -/
theorem hukm_ala_kull_sijill (R : List (String × Idaa.Naw)) (h : makhtum R basma = true) (m s q : String) :
    hukm R B jadwal m s q = hukm bad B jadwal m s q := by
  have hb : makhtum bad basma = true := by decide +kernel
  unfold hukm makhtuma
  simp only [B, h, hb]

/-- **على كلّ سجلٍّ يحوي قيدَ الدفعة «واقعًا مختومًا»** (والسجلُّ الحقيقيّ بعد ختمها منها): مفهوم 20 ومعلومة 27. -/
theorem ihsa_ala_kull_sijill (R : List (String × Idaa.Naw)) (hR : (basma, Idaa.Naw.waqiMakhtum) ∈ R) :
    (qadaya.map (hukmQ R)).count .mafhum = 20 ∧ (qadaya.map (hukmQ R)).count .maaluma = 27 := by
  have h : makhtum R basma = true := by
    unfold makhtum
    exact List.any_eq_true.mpr ⟨_, hR, by decide +kernel⟩
  have e : qadaya.map (hukmQ R) = qadaya.map (hukmQ bad) := by
    apply List.map_congr_left
    intro k _
    simp only [hukmQ]
    exact hukm_ala_kull_sijill R h _ _ _
  rw [e]
  exact ⟨ihsa.2.2.1, ihsa.2.2.2.1⟩

end Waqi.Shawahid
