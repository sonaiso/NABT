/-
  Madlul/TasisDalala.lean — شبكةُ الدلالة: الدورُ والتأسيس.

  **السند.** قولُ المالك في الجلسة (2026-10-26)، بعد مقترحٍ ألصقه فيه جداولُ SQL وحلقةُ تعريفٍ من أرض إلى سفل إلى قرر إلى أرض تُعرض
  شبكةً مغلقةً بنفسها:
  «حلل واستنتج وابنش شبكة الدلالة انت خبير واستعمل الوكلاء بعمق لإيجاد حل تصميمي مبرهن»
  ولفظُه ووصفُ المقترح كلاهما من ملخّص الجلسة بعد ضغطها: نصُّ المقترح الخامّ لم يُرَ، ووقتُ الرسالة منه فلم يُكتب. والتصميمُ قرارُ البنّاء.

  **المسألة.** المعجمُ يعرّف لفظًا بألفاظ، فمتى يُعرَّف لفظٌ من أساسٍ معلوم؟ التعريفُ هنا (`Muarraf`) قريبٌ من تعريف مقال "The Latent
  Structure of Dictionaries" (arXiv:1411.0129)، ويخالفه في موضعٍ واحد. وفي المقال، بنقل أداة الجلب من قسم Grounding Sets (لم يُطابَق
  بنصّ المقال، والرمزُ U فيه 𝑈): "We say that u is definable from U if all predecessors of u either belong to U or are definable from U".
  فعلى حرفها ما لا سابقَ له معرَّفٌ بلا شرط. وأساسُ التأسيس (grounding set) عندهم هو feedback vertex set، وأصغرُه MinSet، نحو 1% من المعجم
  كما يصفه ملخّصُه بنقل الأداة نفسِها.
  **والمخالفةُ تعيينُ البنّاء:** `Muarraf` يفرّق بين ما لا مدخلَ له (`none`) وما حدُّه فارغ (`some []`). الثاني معرَّفٌ بلا شرطٍ كحرف المقال،
  والأوّلُ لا يُعرَّف إلّا أساسًا (`bila_madkhal`)، لأنّ جدولنا ناقص فغيابُ المدخل فيه ليس بدائيّة. وعليه تقوم نتائجُ §٣: أصغرُ أساسٍ للصفوف
  الثلاثين 18 (الأوراقُ وعضوٌ من الدور)، وبحرف المقال (`defMaqal`) جذرٌ واحد (`maqal_aql_kafin`، `maqal_dawr`). فالـ18 ليست MinSet بمعنى المقال.

  **ما يثبت لكلّ معجمٍ وأساس (§١):**
  - الدورُ الذي لا يمسّ الأساس لا يُعرَّف منه شيء (`dawr_la_yuarraf`)، وأعمُّ منه المجموعةُ الموقوفة (`mawqufa_la_yuarraf`).
  - المعرَّفُ هو ما لا تحيط به مجموعةٌ موقوفةٌ لا تمسّ الأساس (`muarraf_iff`).
  - الأساسُ يعرّف الكلَّ إذا وفقط إذا مسّ كلَّ مجموعةٍ موقوفةٍ غيرِ فارغة (`asl_kafin_iff`).
  - لا تعريفَ بلا أساس: معجمٌ ليس فيه مدخلٌ فارغ لا يُعرَّف منه شيءٌ بأساسٍ فارغ (`la_tarif_bila_asl`). فلا يؤسّس المعجمُ نفسَه إلّا
    بلفظٍ حدُّه فارغ.
  - ما لا مدخلَ له لا يُعرَّف إلّا بكونه في الأساس (`bila_madkhal`).
  **والحساب على معجمٍ منتهٍ (§٢):**
  - الإغلاقُ `iqfal` صادق (`iqfal_sahih`)، ويضمّ الأساس (`asl_fi_iqfal`).
  - وهو تامٌّ عند الثبات: إذا كان كلُّ ذي مدخلٍ في الألفاظ `V`، وثبتت قائمةٌ تحت الخطوة واحتوت الأساس، فكلُّ معرَّفٍ فيها (`thabit_tamm`،
    `kharij_thabit`). فالإغلاقُ الثابت هو المعرَّفُ بعينه (`iqfal_iff`).
  - فحصُ الدور `dawrB` صادق (`dawrB_sahih`).
  **والجدول (§٣):** `defJ` لا يُخرج مدخلًا فارغًا (`defJ_ghayr_farigh`)، فلا يُعرَّف من أيّ جدولٍ صفوفُه على صيغة `Saff` شيءٌ بأساسٍ فارغ
  (`la_tarif_bila_asl_defJ`).
  **والشاهد على جدول اللزوم (§٣؛ صفوفُه الثلاثون في `Madlul/JadwalLuzumData.lean`):**
  - دورٌ فيه من اللسان: {{lisan.txt:236712}} «وفهمت الشيء: عقلته وعرفته.» و{{lisan.txt:209627}} «وعقل الشيء يعقله عقلا: فهمه.»
    (`dawr_fahm_aql`). فلا يُعرَّف «فهم» ولا «عقل» في هذا الجدول من أساسٍ لا يضمّ أحدَهما (`fahm_aql_la_yuarraf`).
  - من {{lisan.txt:23989}} «الكتاب: معروف» أساسًا وحده لا يُعرَّف في هذا الجدول إلّا «كتب» (`min_kataba`).
  - كلُّ أساسٍ يعرّف ألفاظَ الشبكة يضمّ أوراقَها السبعَ عشرةَ (ألفاظَها التي لا مدخلَ لها: `awraq`)، و«فهم» أو «عقل» (`kafin_yahwi`).
    فالأوراقُ و«عقل» (`asasAdna`) أساسٌ يعرّفها كلَّها (`asasAdna_kafin`)، وهو أصغرُها عددًا (`asasAdna_asghar`)، ولا يكفي إن نقص منه عضو
    (`asasAdna_adna`).
  - وبحرف المقال يعرّف «عقل» وحده ألفاظَ الشبكة (`maqal_aql_kafin`)، ولا يعرّفها الأساسُ الفارغ لبقاء الدور (`maqal_dawr`).

  **النصّ: الأساسُ من خارج الشبكة.** المبرهناتُ تثبت أنّ معجمًا بلا مدخلٍ فارغ لا يؤسّس نفسَه، ولا تقول من أين يأتي الأساس. وعند النبهاني:
  - {{a2.txt:729}} «وأما العقل فلا ينفع في معرفة اللغة العربية، ولا قيمة له؛ لأن المسألة مسألة نقل عمن وضع اللغة، وليست مسألة الإدراك، ولأن العقل إنما يستقل بوجوب الواجبات، واستحالة المستحيلات. وأما وقوع أحد الجائزين فلا يهتدي إليه العقل، واللغات من هذا القبيل؛ لأنها متوقفة على الوضع، إذ وضع لفظ معين لمعنى معين من الممكنات، والعقل لا يمكن أن يستقل بإدراك أن الواضع وضع هذا اللفظ أو ذاك لهذا المعنى أو لذاك، فإنه يتوقف على النقل عن الواضع؛ ومن هنا لا محل للعقل في اللغة، بل تتوقف معرفتها على النقل عن الواضع.»
  - {{a3.txt:37}} «بل لا بد من وجود معلومات سابقة عند الإنسان يفسر بواسطتها الواقع الذي أحس به حتى يحصل فكر.»
  - {{a3.txt:39}} «ولكن إذا أعطيناه اسم كل منها تجاه واقعه، أو تجاه صورة الواقع، وربطناه بها، حتى حفظ الأسماء مربوطاً كل اسم منها بواقعه، فإنه حينئذ يدرك كل شيء باسمه، أي يدرك ما هو هذا الشيء هل هو أسد ام ميزان، ولا يخطىء.»
  - {{a3.txt:52}} «فالمعلومات السابقة شرط أساسي ورئيسي للعملية العقلية.»
  وجعلُ النقلِ والاسمِ المربوطِ بواقعه أساسَ الشبكة قراءةُ البنّاء؛ لا تقرؤه المبرهنات.

  **التعيينات (تعيينُ البنّاء):**
  - المدخلُ للجذر: صفوفُ المعجمين ومعانيه كلُّها مدخلٌ واحد (`defJ`). فالشبكةُ أخشنُ من المعاني، والمشتركُ فيها عقدةٌ واحدة.
  - صفوفُ التعليل (luzum) ليست حدًّا: وجهُ تسميةٍ لا معرِّف.
  - «معروف» في المعجم أساسٌ مرشّحٌ بقراءة البنّاء، ومصادرُ الأساس قرارُ المالك.
  **ما لا يُدّعى:** المبرهناتُ خواصُّ هذا النموذج للتعريف لا خواصُّ اللغة، والشاهدُ على الصفوف الثلاثين وحدها؛ والملفُّ غيرُ موصولٍ
  بالمحرّك.

  **وعلى الجدول الكامل** (`luzum_mujam.tsv` المرشّح، 141,144 صفًّا؛ عدُّ أداةٍ بـ`shabaka/tasis_dalala.py`، بلا وسم):
  - العقدُ 8,640 (المواد ومعرِّفاتُها بلا التعليل، كـ`kalimat`). وأساسُ «معروف» من عناوين اللسان 61 جذرًا، منها في العقد 59.
  - المعرَّفُ منه 83 (0.96%): الأساسُ نفسُه 59، وجديدٌ 24. والبالغُ إليه بطريقٍ 8,467 (98.00%). ومن أساسٍ فارغ 0،
    كما تقضي `la_tarif_bila_asl_defJ` على كلّ جدول؛ والجدولُ الكامل لم يُصَغ في Lean.
  - وبحرف المقال (ما لا مدخلَ له معرَّف؛ 168 عقدة): من أساسٍ فارغ 171 = 168 + جديدٌ 3، ومن أساس «معروف» 254 = 168 + الأساسُ 59
    + جديدٌ 27. فالجديدُ 27 بحرف المقال مقابل 24 بتعيين البنّاء.
  - النواةُ بإجراء المقال 3,973 (45.98%)، منها 119 بلا مدخل؛ فلا تُقابَل بنحو 10% في ملخّصه: العقدُ هنا جذورٌ لا كلمات، والجدولُ ناقص.
  - وأساسٌ جشعٌ يعرّف العقدَ كلَّها 1,733 (20.06%): حدٌّ أعلى، لا أصغرُ أساس.
  - وفي الجدول ضجيجُ المستخرِج، ومنه في الأربعة والعشرين الجديدة:
    - «حج» و«رم» معرِّفُهما «ربع»، من {{maqayis.txt:8793}} «الحاء والجيم أصول أربعة.» ومن {{maqayis.txt:14915}} «الراء والميم أربعة أصول».
    - «شغزن» من {{lisan.txt:253482}} «شغزن: رباعي.»
    - و«ربع» نفسُه في الأساس من {{lisan.txt:146592}} «الأربعة والأربعون من العدد: معروف.»
  - والحلقةُ التي في المقترح ليس منها في الجدول إلّا ءرض ← سفل، وصلةً على الجذر من معنًى آخر:
    {{lisan.txt:129999}} «والأرض: سفلة البعير والدابة وما ولي الأرض منه». ولا صفَّ سفل ← قرر، ولا قرر ← ءرض.

  **التصنيف (المعيار الموحَّد في `Nizam/Asas.lean`):** 26 مبرهنة.
  - لكلّ 20:
    - `dawr_mawqufa`، `mawqufa_la_yuarraf`، `dawr_la_yuarraf`، `ghayr_muarraf_mawqufa`، `muarraf_iff`، `la_tarif_bila_asl`، `asl_kafin_iff`،
      `iqfal_sahih`، `asl_fi_iqfal`، `thabit_tamm`، `iqfal_iff`، `dawrB_sahih`، `kharij_thabit`، `defJ_madakhil`، `defJ_ghayr_farigh`،
      `la_tarif_bila_asl_defJ`.
    - وعلى هذا الجدول، عمومُها على مساعدٍ على الشاهد: `fahm_aql_la_yuarraf`، `min_kataba`، `kafin_yahwi`، `asasAdna_asghar`.
  - تعريفيّة 1: `bila_madkhal`.
  - على الشاهد 5، خارجَ حرف المعيار (decide ثمّ نقلٌ بمبرهنةٍ من §١–§٢، معلَن): `dawr_fahm_aql`، `asasAdna_kafin`، `asasAdna_adna`،
    `maqal_aql_kafin`، `maqal_dawr`.
-/

import Madlul.JadwalLuzum

namespace TasisDalala

variable {α : Type}

/-! ## ١. التعريف من أساس -/

/-- المعرَّفُ في معجمٍ `Def` من أساسٍ `G`: لكلّ مدخلٍ `v` قائمةُ معرِّفاته `Def v = some ds` (و`none`: لا مدخلَ له).
    المؤسَّسُ معرَّف؛ وما له مدخلٌ عُرفت معرِّفاتُه كلُّها معرَّف. -/
inductive Muarraf (Def : α → Option (List α)) (G : α → Prop) : α → Prop
  | asl {g : α} : G g → Muarraf Def G g
  | tarif {v : α} {ds : List α} : Def v = some ds → (∀ d ∈ ds, Muarraf Def G d) → Muarraf Def G v

/-- مجموعةٌ موقوفة: كلُّ عضوٍ فيها لا مدخلَ له، أو في مدخله معرِّفٌ منها. -/
def Mawqufa (Def : α → Option (List α)) (C : α → Prop) : Prop :=
  ∀ v, C v → ∀ ds, Def v = some ds → ∃ d ∈ ds, C d

/-- الدور: مجموعةٌ كلُّ عضوٍ فيها له مدخلٌ فيه معرِّفٌ منها. -/
def Dawr (Def : α → Option (List α)) (C : α → Prop) : Prop :=
  ∀ v, C v → ∃ ds, Def v = some ds ∧ ∃ d ∈ ds, C d

/-- كلُّ دورٍ موقوف (المدخلُ واحدٌ لكلّ لفظ). -/
theorem dawr_mawqufa (Def : α → Option (List α)) (C : α → Prop) (h : Dawr Def C) : Mawqufa Def C := by
  intro v hv ds hds
  obtain ⟨ds', hds', d, hd, hcd⟩ := h v hv
  rw [hds] at hds'
  cases hds'
  exact ⟨d, hd, hcd⟩

/-- **الموقوفُ لا يُعرَّف:** مجموعةٌ موقوفة لا تمسّ الأساس لا يُعرَّف شيءٌ منها. -/
theorem mawqufa_la_yuarraf (Def : α → Option (List α)) (G C : α → Prop) (hC : Mawqufa Def C)
    (hG : ∀ g, G g → ¬ C g) : ∀ v, Muarraf Def G v → ¬ C v := by
  intro v h
  induction h with
  | asl hg => exact hG _ hg
  | tarif hds _ ih =>
    intro hv
    obtain ⟨d, hd, hcd⟩ := hC _ hv _ hds
    exact ih d hd hcd

/-- **الدورُ الذي لا يمسّ الأساس لا يُعرَّف منه شيء.** -/
theorem dawr_la_yuarraf (Def : α → Option (List α)) (G C : α → Prop) (hC : Dawr Def C)
    (hG : ∀ g, G g → ¬ C g) : ∀ v, Muarraf Def G v → ¬ C v :=
  mawqufa_la_yuarraf Def G C (dawr_mawqufa Def C hC) hG

/-- وعكسُه: ما لا يُعرَّف تحيط به مجموعةٌ موقوفة لا تمسّ الأساس (مجموعةُ ما لا يُعرَّف نفسُها). -/
theorem ghayr_muarraf_mawqufa (Def : α → Option (List α)) (G : α → Prop) (v : α) (h : ¬ Muarraf Def G v) :
    ∃ C : α → Prop, C v ∧ Mawqufa Def C ∧ ∀ g, G g → ¬ C g := by
  refine ⟨fun u => ¬ Muarraf Def G u, h, ?_, ?_⟩
  · intro u hu ds hds
    apply Classical.byContradiction
    intro hno
    apply hu
    apply Muarraf.tarif hds
    intro d hd
    apply Classical.byContradiction
    intro hnd
    exact hno ⟨d, hd, hnd⟩
  · intro g hg hng
    exact hng (Muarraf.asl hg)

/-- **المعرَّفُ هو ما لا تحيط به مجموعةٌ موقوفة لا تمسّ الأساس.** -/
theorem muarraf_iff (Def : α → Option (List α)) (G : α → Prop) (v : α) :
    Muarraf Def G v ↔ ¬ ∃ C : α → Prop, C v ∧ Mawqufa Def C ∧ ∀ g, G g → ¬ C g := by
  constructor
  · intro h ⟨C, hv, hC, hG⟩
    exact mawqufa_la_yuarraf Def G C hC hG v h hv
  · intro h
    apply Classical.byContradiction
    intro hn
    exact h (ghayr_muarraf_mawqufa Def G v hn)

/-- **لا تعريفَ بلا أساس:** معجمٌ ليس فيه مدخلٌ فارغ لا يُعرَّف منه شيءٌ بأساسٍ فارغ. فلا يؤسّس المعجمُ نفسَه إلّا بلفظٍ حدُّه فارغ. -/
theorem la_tarif_bila_asl (Def : α → Option (List α)) (h : ∀ v ds, Def v = some ds → ds ≠ []) :
    ∀ v, ¬ Muarraf Def (fun _ => False) v := by
  intro v hv
  induction hv with
  | asl hg => exact hg
  | @tarif v ds hds _ ih =>
    obtain ⟨d, hd⟩ := List.exists_mem_of_ne_nil ds (h v ds hds)
    exact ih d hd

/-- ما لا مدخلَ له لا يُعرَّف إلّا بكونه في الأساس. -/
theorem bila_madkhal (Def : α → Option (List α)) (G : α → Prop) (v : α) (h : Def v = none)
    (hv : Muarraf Def G v) : G v := by
  cases hv with
  | asl hg => exact hg
  | tarif hds _ => rw [h] at hds; cases hds

/-- **الأساسُ يؤسّس الكلَّ إذا وفقط إذا مسّ كلَّ مجموعةٍ موقوفةٍ غيرِ فارغة.** -/
theorem asl_kafin_iff (Def : α → Option (List α)) (G : α → Prop) :
    (∀ v, Muarraf Def G v) ↔ ∀ C : α → Prop, Mawqufa Def C → (∃ v, C v) → ∃ g, G g ∧ C g := by
  constructor
  · intro hall C hC ⟨v, hv⟩
    apply Classical.byContradiction
    intro hno
    exact mawqufa_la_yuarraf Def G C hC (fun g hg hc => hno ⟨g, hg, hc⟩) v (hall v) hv
  · intro h v
    apply Classical.byContradiction
    intro hn
    obtain ⟨C, hv, hC, hG⟩ := ghayr_muarraf_mawqufa Def G v hn
    obtain ⟨g, hg, hc⟩ := h C hC ⟨v, hv⟩
    exact hG g hg hc

/-! ## ٢. الحسابُ على معجمٍ منتهٍ -/

variable [DecidableEq α]

/-- خطوةٌ: يُضاف من الألفاظ `V` ما له مدخلٌ معرِّفاتُه كلُّها معروفة. -/
def khatwa (V : List α) (Def : α → Option (List α)) (K : List α) : List α :=
  K ++ V.filter (fun v => !K.contains v && match Def v with
    | some ds => ds.all (K.contains ·)
    | none => false)

/-- الإغلاقُ بعد n خطوة من الأساس. -/
def iqfal (V : List α) (Def : α → Option (List α)) (G : List α) : Nat → List α
  | 0 => G
  | n + 1 => khatwa V Def (iqfal V Def G n)

/-- **الحسابُ صادق:** كلُّ ما في الإغلاق معرَّفٌ من الأساس. -/
theorem iqfal_sahih (V : List α) (Def : α → Option (List α)) (G : List α) :
    ∀ n, ∀ v ∈ iqfal V Def G n, Muarraf Def (· ∈ G) v := by
  intro n
  induction n with
  | zero => intro v hv; exact Muarraf.asl hv
  | succ n ih =>
    intro v hv
    simp only [iqfal, khatwa, List.mem_append, List.mem_filter, Bool.and_eq_true] at hv
    rcases hv with hv | ⟨_, _, hdef⟩
    · exact ih v hv
    · cases hd : Def v with
      | none => rw [hd] at hdef; simp at hdef
      | some ds =>
        rw [hd] at hdef
        apply Muarraf.tarif hd
        intro d hdm
        rw [List.all_eq_true] at hdef
        exact ih d (by simpa using hdef d hdm)

/-- الأساسُ في الإغلاق بعد كلّ خطوة. -/
theorem asl_fi_iqfal (V : List α) (Def : α → Option (List α)) (G : List α) :
    ∀ n, ∀ g ∈ G, g ∈ iqfal V Def G n := by
  intro n
  induction n with
  | zero => intro g hg; exact hg
  | succ n ih => intro g hg; simp only [iqfal, khatwa, List.mem_append]; exact Or.inl (ih g hg)

/-- **والحسابُ تامّ عند الثبات:** إذا كان كلُّ ذي مدخلٍ في الألفاظ `V`، وثبتت قائمةٌ `K` تحت الخطوة واحتوت الأساس، فكلُّ معرَّفٍ
    من الأساس في `K`. -/
theorem thabit_tamm (V : List α) (Def : α → Option (List α)) (G K : List α)
    (hV : ∀ v ds, Def v = some ds → v ∈ V) (hK : khatwa V Def K = K) (hG : ∀ g ∈ G, g ∈ K) :
    ∀ v, Muarraf Def (· ∈ G) v → v ∈ K := by
  intro v h
  induction h with
  | asl hg => exact hG _ hg
  | @tarif v ds hds _ ih =>
    apply Classical.byContradiction
    intro hvK
    have hin : v ∈ khatwa V Def K := by
      simp only [khatwa, List.mem_append, List.mem_filter, Bool.and_eq_true]
      refine Or.inr ⟨hV v ds hds, by simpa using hvK, ?_⟩
      rw [hds, List.all_eq_true]
      intro d hd
      simpa using ih d hd
    rw [hK] at hin
    exact hvK hin

/-- **فالإغلاقُ الثابت هو المعرَّفُ بعينه:** إذا كان كلُّ ذي مدخلٍ في `V`، وثبت الإغلاقُ بعد n خطوة، فالمعرَّفُ من الأساس ما في الإغلاق. -/
theorem iqfal_iff (V : List α) (Def : α → Option (List α)) (G : List α)
    (hV : ∀ v ds, Def v = some ds → v ∈ V) (n : Nat)
    (hK : khatwa V Def (iqfal V Def G n) = iqfal V Def G n) (v : α) :
    Muarraf Def (· ∈ G) v ↔ v ∈ iqfal V Def G n :=
  ⟨thabit_tamm V Def G _ hV hK (asl_fi_iqfal V Def G n) v, iqfal_sahih V Def G n v⟩

/-- فحصُ الدور على قائمةٍ منتهية: لكلّ عضوٍ مدخلٌ فيه معرِّفٌ منها. -/
def dawrB (Def : α → Option (List α)) (C : List α) : Bool :=
  C.all fun v => match Def v with
    | some ds => ds.any (C.contains ·)
    | none => false

theorem dawrB_sahih (Def : α → Option (List α)) (C : List α) (h : dawrB Def C = true) : Dawr Def (· ∈ C) := by
  intro v hv
  have hv' := List.all_eq_true.1 h v hv
  cases hd : Def v with
  | none => rw [hd] at hv'; simp at hv'
  | some ds =>
    rw [hd] at hv'
    obtain ⟨d, hdm, hc⟩ := List.any_eq_true.1 hv'
    exact ⟨ds, rfl, d, hdm, by simpa using hc⟩

/-- وما لم يبلغه إغلاقٌ ثابت لا يُعرَّف (عكسُ `thabit_tamm`). -/
theorem kharij_thabit (V : List α) (Def : α → Option (List α)) (G K : List α)
    (hV : ∀ v ds, Def v = some ds → v ∈ V) (hK : khatwa V Def K = K) (hG : ∀ g ∈ G, g ∈ K) (v : α) (hv : v ∉ K) :
    ¬ Muarraf Def (· ∈ G) v :=
  fun h => hv (thabit_tamm V Def G K hV hK hG v h)

end TasisDalala

/-! ## ٣. على جدول اللزوم (`Madlul/JadwalLuzumData.lean`) -/

namespace TasisDalala.Jadwal
open TasisDalala JadwalLuzum

/-- معرِّفاتُ الجذر من صفوف الجدول: الجذورُ الأخرى في صفوفه غيرِ صفوف التعليل (تعيين: اللزومُ وجهُ تسميةٍ لا حدّ). وبلا صفٍّ لا مدخل. -/
def defJ (T : List Saff) (a : String) : Option (List String) :=
  match (T.filter fun r => r.a == a && r.naw != .luzum).map (·.b) with
  | [] => none
  | ds => some ds

/-- مداخلُ الجدول: جذورُ موادّه. -/
def madakhil (T : List Saff) : List String := T.map (·.a)

/-- ألفاظُ شبكة التعريف: المداخلُ ومعرِّفاتُها. -/
def kalimat (T : List Saff) : List String := T.map (·.a) ++ (T.filter (·.naw != .luzum)).map (·.b)

theorem defJ_madakhil (T : List Saff) : ∀ v ds, defJ T v = some ds → v ∈ madakhil T := by
  intro v ds h
  unfold defJ at h
  cases hf : T.filter (fun r => r.a == v && r.naw != .luzum) with
  | nil => simp [hf] at h
  | cons r rs =>
    have hr : r ∈ T.filter (fun r => r.a == v && r.naw != .luzum) := by rw [hf]; simp
    rw [List.mem_filter] at hr
    simp only [Bool.and_eq_true, beq_iff_eq] at hr
    exact List.mem_map.2 ⟨r, hr.1, hr.2.1⟩

/-- لا مدخلَ فارغًا في `defJ`: الجذرُ بلا معرِّفٍ لا مدخلَ له. -/
theorem defJ_ghayr_farigh (T : List Saff) : ∀ v ds, defJ T v = some ds → ds ≠ [] := by
  intro v ds h
  unfold defJ at h
  cases hl : (T.filter fun r => r.a == v && r.naw != .luzum).map (·.b) with
  | nil => rw [hl] at h; cases h
  | cons x xs => rw [hl] at h; cases h; exact List.cons_ne_nil x xs

/-- **فلا يُعرَّف من أيّ جدولٍ شيءٌ بأساسٍ فارغ.** -/
theorem la_tarif_bila_asl_defJ (T : List Saff) : ∀ v, ¬ Muarraf (defJ T) (fun _ => False) v :=
  la_tarif_bila_asl _ (defJ_ghayr_farigh T)

/-- دورٌ في الجدول من اللسان: {{lisan.txt:236712}} «وفهمت الشيء: عقلته وعرفته.» و{{lisan.txt:209627}} «وعقل الشيء يعقله عقلا: فهمه.» -/
theorem dawr_fahm_aql : Dawr (defJ jadwal) (· ∈ ["فهم", "عقل"]) :=
  dawrB_sahih _ _ (by decide)

/-- فلا يُعرَّف «فهم» ولا «عقل» في هذا الجدول من أيّ أساسٍ لا يضمّ أحدَهما. -/
theorem fahm_aql_la_yuarraf (G : String → Prop) (h1 : ¬ G "فهم") (h2 : ¬ G "عقل") :
    ¬ Muarraf (defJ jadwal) G "فهم" ∧ ¬ Muarraf (defJ jadwal) G "عقل" := by
  have hG : ∀ g, G g → ¬ g ∈ ["فهم", "عقل"] := by
    intro g hg hm
    simp only [List.mem_cons, List.not_mem_nil, or_false] at hm
    rcases hm with rfl | rfl
    · exact h1 hg
    · exact h2 hg
  exact ⟨fun h => dawr_la_yuarraf _ G _ dawr_fahm_aql hG _ h (by simp),
         fun h => dawr_la_yuarraf _ G _ dawr_fahm_aql hG _ h (by simp)⟩

/-- من {{lisan.txt:23989}} «الكتاب: معروف» أساسًا وحده لا يُعرَّف من الجدول إلّا «كتب». -/
theorem min_kataba : ∀ v, Muarraf (defJ jadwal) (· ∈ ["كتب"]) v → v = "كتب" := by
  intro v h
  have hK : khatwa (madakhil jadwal) (defJ jadwal) ["كتب"] = ["كتب"] := by decide
  have := thabit_tamm (madakhil jadwal) (defJ jadwal) ["كتب"] ["كتب"] (defJ_madakhil jadwal) hK (fun g hg => hg) v h
  simpa using this

/-- أوراقُ الشبكة: ألفاظُها التي لا مدخلَ لها في الجدول. -/
def awraq : List String :=
  ["عرف", "قلب", "بعد", "جعل", "سءل", "قبل", "خفا", "خفض", "عفا", "حبس", "قرب", "ءثر", "ميز", "سوا", "بره", "صلح", "جمع"]

/-- أساسٌ للجدول: الأوراقُ، وعضوٌ من الدور فهم–عقل. -/
def asasAdna : List String := awraq ++ ["عقل"]

/-- يُعرَّف منه كلُّ ألفاظ الشبكة. -/
theorem asasAdna_kafin : ∀ v ∈ kalimat jadwal, Muarraf (defJ jadwal) (· ∈ asasAdna) v := by
  intro v hv
  have hc : (kalimat jadwal).all ((iqfal (madakhil jadwal) (defJ jadwal) asasAdna 7).contains ·) = true := by decide
  exact iqfal_sahih _ _ _ 7 v (by simpa using List.all_eq_true.1 hc v hv)

/-- **كلُّ أساسٍ يعرّف ألفاظَ الشبكة يضمّ الأوراقَ كلَّها، و«فهم» أو «عقل».** -/
theorem kafin_yahwi (G : String → Prop) (h : ∀ v ∈ kalimat jadwal, Muarraf (defJ jadwal) G v) :
    (∀ g ∈ awraq, G g) ∧ (G "فهم" ∨ G "عقل") := by
  constructor
  · intro g hg
    have hk : awraq.all (fun g => (kalimat jadwal).contains g && defJ jadwal g == none) = true := by decide
    have h1 := List.all_eq_true.1 hk g hg
    simp only [Bool.and_eq_true, beq_iff_eq] at h1
    exact bila_madkhal _ G g h1.2 (h g (by simpa using h1.1))
  · apply Classical.byContradiction
    intro hn
    exact (fahm_aql_la_yuarraf G (fun x => hn (Or.inl x)) (fun x => hn (Or.inr x))).1 (h "فهم" (by decide))

/-- **وهو أصغرُها عددًا:** كلُّ قائمةٍ تعرّف ألفاظَ الشبكة ليست أقصرَ منه. -/
theorem asasAdna_asghar (G : List String) (h : ∀ v ∈ kalimat jadwal, Muarraf (defJ jadwal) (· ∈ G) v) :
    asasAdna.length ≤ G.length := by
  obtain ⟨h1, h2⟩ := kafin_yahwi (· ∈ G) h
  have sub : ∀ x, x ∈ G → (awraq ++ [x]) ⊆ G := by
    intro x hx y hy
    simp only [List.mem_append, List.mem_singleton] at hy
    rcases hy with hy | rfl
    · exact h1 y hy
    · exact hx
  rcases h2 with hx | hx
  · have hl : asasAdna.length = (awraq ++ ["فهم"]).length := by decide
    rw [hl]
    exact List.Nodup.length_le_of_subset (by decide) (sub _ hx)
  · exact List.Nodup.length_le_of_subset (by decide) (sub _ hx)

/-- ولا يكفي إن نقص منه عضو: لكلّ عضوٍ إغلاقٌ ثابتٌ من الباقي لا يبلغه. -/
theorem asasAdna_adna : ∀ g ∈ asasAdna, ¬ Muarraf (defJ jadwal) (· ∈ asasAdna.erase g) g := by
  intro g hg
  have hc : asasAdna.all (fun g =>
      let K := iqfal (madakhil jadwal) (defJ jadwal) (asasAdna.erase g) 7
      khatwa (madakhil jadwal) (defJ jadwal) K == K && !(K.contains g)) = true := by decide
  have h1 := List.all_eq_true.1 hc g hg
  simp only [Bool.and_eq_true, beq_iff_eq, Bool.not_eq_eq_eq_not, Bool.not_true] at h1
  apply kharij_thabit (madakhil jadwal) (defJ jadwal) (asasAdna.erase g)
    (iqfal (madakhil jadwal) (defJ jadwal) (asasAdna.erase g) 7) (defJ_madakhil jadwal) h1.1
  · exact asl_fi_iqfal _ _ _ 7
  · simpa using h1.2

/-! ### بحرف المقال -/

/-- حدُّ المقال: ما لا مدخلَ له حدُّه فارغ، فهو معرَّفٌ بلا شرط. -/
def defMaqal (T : List Saff) (a : String) : Option (List String) := some ((defJ T a).getD [])

/-- **بحرف المقال يكفي «عقل» وحده** أساسًا لألفاظ الشبكة. -/
theorem maqal_aql_kafin : ∀ v ∈ kalimat jadwal, Muarraf (defMaqal jadwal) (· ∈ ["عقل"]) v := by
  intro v hv
  have hc : (kalimat jadwal).all ((iqfal (kalimat jadwal) (defMaqal jadwal) ["عقل"] 8).contains ·) = true := by decide
  exact iqfal_sahih _ _ _ 8 v (by simpa using List.all_eq_true.1 hc v hv)

/-- **ولا يكفي بحرف المقال أساسٌ فارغ:** الدورُ فهم–عقل باقٍ. -/
theorem maqal_dawr : ¬ Muarraf (defMaqal jadwal) (fun _ => False) "عقل" := fun h =>
  dawr_la_yuarraf _ (fun _ => False) _ (dawrB_sahih (defMaqal jadwal) ["فهم", "عقل"] (by decide))
    (fun _ h => h.elim) _ h (by simp)

end TasisDalala.Jadwal
