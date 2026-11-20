/-
  Madlul/JadwalLuzum.lean — جدولُ اللزوم من شبكة المعاجم: أصولُ الرتبة صفر لقوانين الدلالة الثلاثة.

  أمرُ المالك (2026-10-18): «جدولُ اللزوم من مقاييس/لسان … نفذ وفق أفضل الممارسات»، وشبكتُه: كتب، درس، قلم، علم، فهم،
  طلب، عقل. وفي `Aql/QawaninDalala.lean` الوضعُ والجزءُ والخارجُ واللزومُ أصولٌ مودَعة أبدًا (`naql_la_aql`، ج3 729):
  هذا الملفّ يملؤها من المودَعين المختومين «مقاييس اللغة» و«لسان العرب» بصفوفٍ لكلٍّ منها سطرُه، ولا يزيد قانونًا.

  القراءةُ (تعيينُ البنّاء المعلن، قواعدُ `shabaka/jadwal_luzum.py`):
  * تفسيرُ اللسان «W: G» بجذورٍ متعدّدة (`juz`): W موضوعٌ لمدلول G في سطره، وكلُّ جذرٍ في G جزءٌ منه.
  * تفسيرٌ بجذرٍ واحد (`taraduf`): W موضوعٌ لمعنى ذلك الجذر نفسِه.
  * نقيضٌ/ضدٌّ/خلاف (`kharij`): ذلك المعنى خارجٌ عن مدلول W.
  * أصلُ ابن فارس (`asl`): الجذرُ لفظًا موضوعٌ لأصله، وجذورُ الأصل أجزاؤه.
  * جملةُ تسميةٍ معلَّلة (`luzum`، `TAALIL_KHARIJ`): اللفظُ المسمّى موضوعٌ لمدلوله، والسببُ لازمٌ له خارجٌ عنه —
    «سُمّي بذلك لـ…» تذكر وجهَ التسمية لا المسمّى.

  المبرهن لكلّ جدول (لا لهذا الجدول وحده):
  * `qaidaOf_shakl`: قوانينُ الجدول كلُّها على الهيئة المغلقة في QawaninDalala؛ فـ`salama` تنطبق عليه.
  * `asl_rutba_sifr`: كلُّ ما يودعه صفٌّ رتبتُه صفر — لا صفَّ يودع مطابقةً أو تضمّنًا أو التزامًا.
  * `iltizam_min_taalil`: لا التزامَ مرخَّصًا إلّا وفي الجدول صفُّ تعليل؛ `tadammun_min_juz`: ولا تضمّن إلّا بصفّ جزءٍ أو أصل.
  وعلى الشاهد: مثالُ «الفهم» بالدلالات الثلاث من صفوفه، وصلاتُ الشبكة المباشرة الستّ.
  بلا sorry ولا axiom ولا native_decide.
-/
import Aql.QawaninDalala
import Madlul.JadwalLuzumData

namespace JadwalLuzum
open Qaida QawaninDalala

/-! ## ١. الأسماء والمعرّفات -/

/-- اللفظ «A/W»، ومدلولُه في سطره «م:A/W@n». -/
def lafz (r : Saff) : String := r.a ++ "/" ++ r.w
def maana (r : Saff) : String := "م:" ++ r.a ++ "/" ++ r.w ++ "@" ++ toString r.satr

/-- فهرسُ الأسماء: معرّفاتُ `Qadiyya` مواضعُ في قائمة أسماء الجدول (كما في QawaninDalala: أرقامُ مواضع لا ألفاظ). -/
def asma (T : List Saff) : List String := (T.flatMap fun r => [lafz r, maana r, r.b]).eraseDups
def ism (T : List Saff) (s : String) : Nat := (asma T).idxOf s

/-! ## ٢. الأصولُ والقوانين من الصفّ -/

def aslOf (T : List Saff) (r : Saff) : List Qadiyya :=
  let l := ism T (lafz r); let m := ism T (maana r); let b := ism T r.b
  match r.naw with
  | .juz | .asl => [.wad l m, .juz b m]
  | .taraduf => [.wad l b]
  | .kharij => [.wad l m, .kharij b m]
  | .luzum => [.wad l m, .luzum m b, .kharij b m]

def qawaninOf (T : List Saff) (r : Saff) : List (Qanun Qadiyya) :=
  let l := ism T (lafz r); let m := ism T (maana r); let b := ism T r.b
  match r.naw with
  | .juz | .asl => [qMutabaqa l m, qTadammun l m b]
  | .taraduf => [qMutabaqa l b]
  | .kharij => [qMutabaqa l m]
  | .luzum => [qMutabaqa l m, qIltizam l m b]

def qaidaOf (T : List Saff) : Qaida.Qaida Qadiyya := ⟨"جدول-اللزوم-0.1", T.flatMap (qawaninOf T)⟩
def aslB (T : List Saff) (p : Qadiyya) : Bool := decide (p ∈ T.flatMap (aslOf T))

/-! ## ٣. المبرهن لكلّ جدول -/

theorem qawaninOf_shakl (T : List Saff) (r : Saff) : ∀ q ∈ qawaninOf T r, shakl q = true := by
  intro q hq
  cases hn : r.naw <;> simp [qawaninOf, hn] at hq <;>
    first
    | (rcases hq with rfl | rfl <;> simp [shakl, qMutabaqa, qTadammun, qIltizam])
    | (subst hq; simp [shakl, qMutabaqa])

/-- قوانينُ الجدول على الهيئة المغلقة: فالتدرّجُ والسلامةُ في QawaninDalala تنطبقان عليه. -/
theorem qaidaOf_shakl (T : List Saff) : ∀ q ∈ (qaidaOf T).qawanin, shakl q = true := by
  intro q hq
  simp only [qaidaOf, List.mem_flatMap] at hq
  obtain ⟨r, _, hr⟩ := hq
  exact qawaninOf_shakl T r q hr

theorem qaidaOf_mutadarrija (T : List Saff) : MutadarrijaDaifa (qaidaOf T) rutba :=
  shakl_mutadarrija _ (qaidaOf_shakl T)

/-- لا صفَّ يودع مطابقةً ولا تضمّنًا ولا التزامًا: كلُّ أصلٍ في الرتبة صفر. -/
theorem asl_rutba_sifr (T : List Saff) (r : Saff) : ∀ p ∈ aslOf T r, rutba p = 0 := by
  intro p hp
  cases hn : r.naw <;> simp [aslOf, hn] at hp <;> rcases hp with rfl | rfl | rfl <;> rfl

theorem luzum_min_taalil (T : List Saff) (r : Saff) {m k : Nat} (h : Qadiyya.luzum m k ∈ aslOf T r) :
    r.naw = .luzum := by
  cases hn : r.naw <;> simp [aslOf, hn] at h ⊢

theorem juz_min_hadd (T : List Saff) (r : Saff) {j m : Nat} (h : Qadiyya.juz j m ∈ aslOf T r) :
    r.naw = .juz ∨ r.naw = .asl := by
  cases hn : r.naw <;> simp [aslOf, hn] at h ⊢

theorem aslB_iff (T : List Saff) (p : Qadiyya) : aslB T p = true ↔ ∃ r ∈ T, p ∈ aslOf T r := by
  simp [aslB, List.mem_flatMap]

/-- **لا التزامَ بلا تعليل**: كلُّ التزامٍ مرخَّصٍ في قاعدة الجدول وراءه صفُّ تعليلٍ في الجدول نفسِه —
    لا يُستنتج اللزومُ من انتساب اللفظين إلى جذرٍ ولا من قربهما في الشبكة. -/
theorem iltizam_min_taalil (T : List Saff) {l k : Nat}
    (h : Murakhkhas (qaidaOf T) (fun p => aslB T p = true) (.iltizam l k)) : ∃ r ∈ T, r.naw = .luzum := by
  generalize hp : Qadiyya.iltizam l k = p at h
  cases h with
  | asl ha =>
    subst hp
    obtain ⟨r, _, hr⟩ := (aslB_iff T _).mp ha
    have := asl_rutba_sifr T r _ hr
    simp [rutba] at this
  | qanun q hq hprem =>
    rcases shakl_sahih q (qaidaOf_shakl T q hq) with ⟨l', m', rfl⟩ | ⟨l', m', j', rfl⟩ | ⟨l', m', k', rfl⟩ | ⟨z, c, p', rfl⟩
    · simp [qMutabaqa] at hp
    · simp [qTadammun] at hp
    · have hl : Murakhkhas (qaidaOf T) (fun p => aslB T p = true) (.luzum m' k') :=
        hprem _ (by simp [qIltizam])
      have ha := rutba_sifr_asl_daifa _ rutba _ (qaidaOf_mutadarrija T) hl rfl
      obtain ⟨r, hrT, hr⟩ := (aslB_iff T _).mp ha
      exact ⟨r, hrT, luzum_min_taalil T r hr⟩
    · simp [qTadiya] at hp

/-- **ولا تضمّنَ بلا جزءٍ مشهود**: كلُّ تضمّنٍ مرخَّصٍ وراءه صفُّ حدٍّ (تفسيرٌ بأجزاء) أو أصلٌ لابن فارس. -/
theorem tadammun_min_juz (T : List Saff) {l j : Nat}
    (h : Murakhkhas (qaidaOf T) (fun p => aslB T p = true) (.tadammun l j)) :
    ∃ r ∈ T, r.naw = .juz ∨ r.naw = .asl := by
  generalize hp : Qadiyya.tadammun l j = p at h
  cases h with
  | asl ha =>
    subst hp
    obtain ⟨r, _, hr⟩ := (aslB_iff T _).mp ha
    have := asl_rutba_sifr T r _ hr
    simp [rutba] at this
  | qanun q hq hprem =>
    rcases shakl_sahih q (qaidaOf_shakl T q hq) with ⟨l', m', rfl⟩ | ⟨l', m', j', rfl⟩ | ⟨l', m', k', rfl⟩ | ⟨z, c, p', rfl⟩
    · simp [qMutabaqa] at hp
    · have hj : Murakhkhas (qaidaOf T) (fun p => aslB T p = true) (.juz j' m') :=
        hprem _ (by simp [qTadammun])
      have ha := rutba_sifr_asl_daifa _ rutba _ (qaidaOf_mutadarrija T) hj rfl
      obtain ⟨r, hrT, hr⟩ := (aslB_iff T _).mp ha
      exact ⟨r, hrT, juz_min_hadd T r hr⟩
    · simp [qIltizam] at hp
    · simp [qTadiya] at hp

/-- ونتيجةٌ لكلّ جدولٍ لا صفَّ تعليلٍ فيه: لا التزامَ فيه أصلًا. -/
theorem la_iltizam_bila_taalil (T : List Saff) (hT : ∀ r ∈ T, r.naw ≠ .luzum) {l k : Nat} :
    ¬ Murakhkhas (qaidaOf T) (fun p => aslB T p = true) (.iltizam l k) := by
  intro h
  obtain ⟨r, hr, hn⟩ := iltizam_min_taalil T h
  exact hT r hr hn

/-! ## ٤. على الشاهد: الجدول المولَّد من المودَعين -/

/-- رقمُ القانون في قاعدة الجدول (لسلاسل الفاحص). -/
def raqm (q : Qanun Qadiyya) : Nat := (qaidaOf jadwal).qawanin.idxOf q

def I (s : String) : Nat := ism jadwal s

/-- «الفهم: معرفتك الشيء بالقلب» (اللسان س236711): الفهمُ يدلّ على المعرفة تضمّنًا. -/
theorem fahm_marifa_tadammun :
    let l := I "فهم/الفهم"; let m := I "م:فهم/الفهم@236711"; let j := I "عرف"
    maqbul (qaidaOf jadwal) (aslB jadwal)
      ⟨.tadammun l j, [.asl (.wad l m), .qanun (raqm (qMutabaqa l m)), .asl (.juz j m),
        .qanun (raqm (qTadammun l m j))]⟩ = true := by decide

/-- والسطرُ نفسُه: الفهمُ يدلّ على القلب تضمّنًا. -/
theorem fahm_qalb_tadammun :
    let l := I "فهم/الفهم"; let m := I "م:فهم/الفهم@236711"; let j := I "قلب"
    maqbul (qaidaOf jadwal) (aslB jadwal)
      ⟨.tadammun l j, [.asl (.wad l m), .qanun (raqm (qMutabaqa l m)), .asl (.juz j m),
        .qanun (raqm (qTadammun l m j))]⟩ = true := by decide

/-- «فهمه فهما … : علمه» (س236711): «فهما» يدلّ على معنى العلم مطابقةً. -/
theorem fahm_ilm_mutabaqa :
    let l := I "فهم/وفهما"; let b := I "علم"
    maqbul (qaidaOf jadwal) (aslB jadwal) ⟨.mutabaqa l b, [.asl (.wad l b), .qanun (raqm (qMutabaqa l b))]⟩ = true := by
  decide

/-- «وسمّيت عقالا لأنها تعقل عن صاحبها الطلب» (المقاييس س26425): «عقالا» يدلّ على الطلب التزامًا —
    وهو معنى «العقال» (الصدقة) لا «العقل»: الجذرُ واحدٌ والمادّةُ مشتركة (يُحمل على الشبكة بقيدٍ، انظر الترويسة). -/
theorem iqal_talab_iltizam :
    let l := I "عقل/عقالا"; let m := I "م:عقل/عقالا@26425"; let k := I "طلب"
    maqbul (qaidaOf jadwal) (aslB jadwal)
      ⟨.iltizam l k, [.asl (.wad l m), .qanun (raqm (qMutabaqa l m)), .asl (.kharij k m), .asl (.luzum m k),
        .qanun (raqm (qIltizam l m k))]⟩ = true := by decide

/-- صفوفُ «فهم» في الجدول لا تعليلَ فيها: فلا التزامَ لألفاظ «فهم» في قاعدة صفوفها (من `la_iltizam_bila_taalil`). -/
theorem fahm_la_iltizam {l k : Nat} :
    ¬ Murakhkhas (qaidaOf (jadwal.filter (·.a == "فهم"))) (fun p => aslB (jadwal.filter (·.a == "فهم")) p = true)
      (.iltizam l k) :=
  la_iltizam_bila_taalil _ (by decide)

/-- الصلةُ المباشرة: صفٌّ بين الجذرين في أيّ اتّجاه. -/
def mubashir (T : List Saff) (x y : String) : Bool := T.any fun r => (r.a == x && r.b == y) || (r.a == y && r.b == x)

/-- الصلاتُ المباشرة بين جذور الشبكة في الجدول: كتب–درس، كتب–قلم، كتب–علم، علم–فهم، فهم–عقل، طلب–عقل (الأخيرة بمادّة «عقال»). -/
theorem silat_sitt :
    [("كتب", "درس"), ("كتب", "قلم"), ("كتب", "علم"), ("علم", "فهم"), ("فهم", "عقل"), ("طلب", "عقل")].all
      (fun p => mubashir jadwal p.1 p.2) = true := by decide

/-- ولا صلةَ مباشرةَ في الجدول بين «طلب» و«علم»، ولا بين «طلب» و«كتب» أو «فهم» أو «درس» أو «قلم». -/
theorem talab_la_mubashir :
    ["علم", "كتب", "فهم", "درس", "قلم"].all (fun y => !mubashir jadwal "طلب" y) = true := by decide

end JadwalLuzum
