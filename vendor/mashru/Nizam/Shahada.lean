import Nabt.UnitDiscovery

/-!
# عقدُ الشهادة على الانتقال

**الطلب.** رسالةُ المالك 2026-10-27 (وقتُها 15:36 بتوقيت عمّان من ملخّص الجلسة بعد ضغطها). صدرُها بنصّه كما حفظه سجلُّ الجلسة،
مقطوعًا فيه عند مئتي حرف، بصيغ LaTeX كما هي:
«الجسر الجامع المطلوب لكل انتقال هو شهادة مرتبطة بالعملية نفسها: \[ \text{صحة المدخل} \;\land\; \text{مقدمات القاعدة المكتسبة} \;\land\; \text{مطابقة المصدر والمقام} \;\Longrightarrow\; \text{صحة المخر…»
وباقيها بمعناه من ملخّص الجلسة لا بلفظه: لكلّ عقدةٍ مصدرُها وموضعُها، والمدخلُ والمخرج، وهويّةُ القاعدة، وشهاداتُ مقدّماتها، والبدائلُ
الباقية، وحدودُ الدعوى؛ وأساسُ العقد في `CertifiedBridge`، والمهمّةُ التالية شواهدُه التنفيذيّة لقواعد عربيّة محدّدة؛ وأولويّاتٌ خمس أوّلُها
إغلاقُ تحصيل النصّ ومحاذاته قبل أيّ ترقيةٍ دلاليّة؛ وآخرُها أمرُه بالتنفيذ. وصيغةُ صدرها (LaTeX) صيغةُ نصٍّ مُعَدٍّ أُلصق، ومُعِدُّه غيرُ معلوم؛
فلا يُنسب إلى المالك إلّا أنّه أرسله وأمر بتنفيذه. والتصميمُ هنا قرارُ البنّاء.

**الأساس.** `Nabt.RecursiveSourceBridge.CertifiedBridge` (`Nabt/RecursiveSourceBridge.lean`): عقدٌ يجمع ترخيصَ
المصدر (`sourceLicense : Licensed`، وهو ربطُ العقدة بمصدرٍ في جرد السياق بمعرّفاته وذرّاتها الخامّة، وشواهدُ موجبةٌ كلُّها ولا سالب، وجاهزيّةٌ
لغويّة)، وترخيصَ كلّ مضيف، وشهادةَ النحو، ومطابقةَ المنطوق. ومنه أُخذ هنا:
- الربطُ شرطٌ أوّل (`marbut`): الموضعُ صالحٌ في المصدر (`Nabt.UnitDiscovery.validSpan` نفسُه)، والقاعدةُ مسمّاة. وهو أضيقُ من ربط NABT:
  لا جردَ للمصادر هنا، فالفاحصُ يقبل أيَّ مصدرٍ تحمله الشهادة؛ وأنّ ذرّاتِ المدخل هي ذرّاتُ الموضع لا يفحصه الفاحص العامّ، بل يُفرض في
  `sahihMadkhal` ويُبرهن في التحصيل (`Dal/Tahsil.lean`، `mawdi_sahih`).
- المانعُ المشهود يمنع ولا يخفيه شاهدٌ موجب (`mani_mashhud_yamna`؛ نظيرُ `known_negative_blocks_source_only`)، بشرطٍ ليس في نظيره: أن
  تكون للمدخل مقدّمةٌ واحدةٌ على الأقلّ، ومقدّماتُه كلُّها مشهودة.
- لا ترخيصَ بلا شاهدٍ لكلّ مقدّمة (`murakhkhas_iff`؛ نظيرُ `licensed_all_nodes_have_premises`).
- والنتائجُ منفصلة: ربطٌ فاسد، مدخلٌ فاسد، امتناعٌ لغويّ، قاعدةٌ لا تنطبق، تعليقٌ باسم الناقص، ترخيص:
  - المدخلُ الفاسد ليس حكمًا لغويًّا (`madkhal_awwalan`).
  - في انتقالٍ مربوطٍ لا مقدّمةَ مدخلٍ فيه منقوضة، مقدّمةُ مدخلٍ واحدةٌ لم تُفحص تعلِّق قبل أيّ حكم (`madkhal_ghayrMafhus_yuallaq`)؛ وانتقالٌ
    لا مقدّمةَ فيه للمدخل أصلًا يعلِّق باسم `madkhalGhaib` (`bila_madkhal_yuallaq`).
  - لا يصدر ترخيصٌ ولا امتناعٌ ولا عدمُ انطباقٍ إلّا عن انتقالٍ له مقدّمةُ مدخلٍ ومقدّماتُ مدخله كلُّها مشهودة (`hukm_bi_madkhal_mashhud`).

**العقد.** `Naqla` تحمل الحقولَ الستّة التي في الطلب، و`hukm` فاحصُها التنفيذيّ. و`Qaida` قاعدةٌ بمعناها وعقدِها: صحّةُ المدخل (ومنها مطابقةُ
المصدر والموضع) ∧ مقدّماتُها ⇒ صحّةُ المخرج بمعنى القاعدة. و`shahada_salima` بثلاثة فروض: أمانةُ الشهادة لقاعدتها (`Amin`)، وصدقُ الشواهد
(`Sidq`)، وصحّةُ المدخل (`sahihMadkhal`)؛ فإن رخّصها الفاحص فمخرجُها صحيحٌ بعقد القاعدة.

**حدُّه.**
- `Sidq` و`sahihMadkhal` فرضان في العقد العامّ لا يفحصهما الفاحص (نظيرُ `interpreted` في NABT و`hA` في `QawaninDalala.salama`)؛ وفي التحصيل
  يُبرهنان لأنّ الشواهدَ دوالُّ فحصٍ فيه.
- السندُ أيُّ نصٍّ غيرِ فارغ: لا يُفحص أنّه اسمُ مبرهنةٍ أو صفٍّ أو دالّة (كما لم يُفحص في البصمة غيرُ عدمِ الفراغ).
- الحكمُ الحاسم يسمّي سببَه وحده، فلا يُسمّى معه ما لم يُفحص: المدخلُ الفاسد يسمّي مقدّمتَه المنفيّة، والامتناعُ مانعَه المشهود، وعدمُ
  الانطباق شرطَه المنفيّ.
- البدائلُ الباقية حقلٌ لا يحكم فيه الفاحص. وصحّةُ المخرج معنى القاعدة نفسِها، لا صحّةُ اللغة.

**المبرهنات** (21، بالمعيار الموحَّد في `Nizam/Asas.lean`):
- لكلّ (12): `awwalNaqid_none`، `naqisa_nil`، `naqisaMadkhal_nil`، `madkhal_mashhud`، `murakhkhas_iff`، `ghayrMafhus_la_yurakhkhis`،
  `hukm_bi_madkhal_mashhud`، `madkhal_ghayrMafhus_yuallaq`، `bila_madkhal_yuallaq`، `mani_mashhud_yamna`، `muallaq_asma`، `shahada_salima`.
- تعريفيّة (8): `hal_thalath`، `hukmMarbut_murakhkhas`، `hukmMarbut_muallaq`، `hukmMarbut_mumtani`، `hukmMarbut_laTantabiq`، `ghayrMarbut_awwalan`،
  `la_shahada_bila_sanad`، `madkhal_awwalan`.
- على الشاهد (1): `shahid_mani`.
-/

namespace Nizam.Shahada

open Nabt.UnitDiscovery

/-- نوعُ المقدّمة. -/
inductive Naw
  /-- صحّةُ المدخل. -/
  | madkhal
  /-- مقدّمةُ القاعدة. -/
  | shart
  /-- مانعٌ يلزم انتفاؤه. -/
  | mani
  deriving DecidableEq, Repr

/-- حالُ المقدّمة بعد الفحص. -/
inductive Hal
  /-- ثبتت بشاهد. -/
  | mashhud
  /-- فُحصت فانتفت. -/
  | manfi
  /-- لم تُفحص. -/
  | ghayrMafhus
  deriving DecidableEq, Repr

structure Muqaddima where
  ism : String
  naw : Naw
  hal : Hal
  /-- اسمُ الشاهد: مبرهنةٌ، أو صفُّ جدول، أو دالّةُ فحص. -/
  sanad : String
  deriving DecidableEq, Repr

/-- **لا شهادةَ بلا سند:** حالٌ مشهودةٌ أو منفيّةٌ بلا سندٍ تُعدّ غيرَ مفحوصة. -/
def Muqaddima.halFiil (m : Muqaddima) : Hal :=
  if m.sanad.isEmpty then .ghayrMafhus else m.hal

/-- هويّةُ القاعدة: اسمُها وإصدارُها. -/
structure Hawiyya where
  ism : String
  isdar : Nat
  deriving DecidableEq, Repr

/-- **الانتقال المشهود:** المصدرُ وموضعُه، والمدخلُ والمخرج، وهويّةُ القاعدة، وشهاداتُ مقدّماتها، والبدائلُ الباقية، وحدودُ الدعوى. -/
structure Naqla (α β : Type) where
  masdar : Source Char
  mawdi : Span
  madkhal : α
  makhraj : β
  qaida : Hawiyya
  muqaddimat : List Muqaddima
  badail : List β
  hadd : String

/-- نتيجةُ الفاحص. -/
inductive Natija
  /-- الموضعُ لا يقع في المصدر، أو القاعدةُ بلا اسم. -/
  | ghayrMarbut
  /-- مقدّمةُ صحّة المدخل منفيّة (باسمها): مدخلٌ فاسد، لا حكمٌ لغويّ. -/
  | madkhalFasid (ism : String)
  /-- مانعٌ مشهود (باسمه): امتناعٌ. -/
  | mumtani (ism : String)
  /-- شرطٌ منفيّ (باسمه): القاعدةُ لا تنطبق، لا امتناع. -/
  | laTantabiq (ism : String)
  /-- مقدّماتٌ لم تُفحص، بأسمائها. -/
  | muallaq (asma : List String)
  | murakhkhas
  deriving DecidableEq, Repr

variable {α β : Type}

def Naqla.marbut (n : Naqla α β) : Bool := validSpan n.masdar n.mawdi && !n.qaida.ism.isEmpty

/-- المطلوبُ من المقدّمة لتُرخِّص: المدخلُ والشرطُ مشهودان، والمانعُ منفيّ. -/
def matlub : Naw → Hal
  | .madkhal => .mashhud
  | .shart => .mashhud
  | .mani => .manfi

/-- ما ينقضها: المدخلُ والشرطُ منفيّان، والمانعُ مشهود. -/
def naqid : Naw → Hal
  | .madkhal => .manfi
  | .shart => .manfi
  | .mani => .mashhud

/-- أوّلُ مقدّمةٍ من نوعٍ حالُها نقيضُ مطلوبها. -/
def awwalNaqid (n : Naqla α β) (k : Naw) : Option String :=
  (n.muqaddimat.find? (fun m => m.naw == k && m.halFiil == naqid k)).map (·.ism)

/-- المقدّماتُ التي لم تُفحص، بأسمائها. -/
def naqisa (n : Naqla α β) : List String :=
  (n.muqaddimat.filter (fun m => m.halFiil == .ghayrMafhus)).map (·.ism)

/-- اسمُ التعليق حين لا مقدّمةَ لصحّة المدخل أصلًا. -/
def madkhalGhaib : String := "صحة المدخل"

def fihiMadkhal (n : Naqla α β) : Bool := n.muqaddimat.any (fun m => m.naw == .madkhal)

/-- مقدّماتُ صحّة المدخل التي لم تُفحص، بأسمائها؛ وإن لم تكن للمدخل مقدّمةٌ أصلًا فـ`madkhalGhaib`. -/
def naqisaMadkhal (n : Naqla α β) : List String :=
  if fihiMadkhal n then (n.muqaddimat.filter (fun m => m.naw == .madkhal && m.halFiil == .ghayrMafhus)).map (·.ism)
  else [madkhalGhaib]

/-- الحكمُ بعد الربط: المدخلُ المنقوض فاسد؛ ثمّ مقدّمةُ مدخلٍ واحدةٌ لم تُفحص، أو لا مقدّمةَ للمدخل، تعلِّق قبل أيّ حكمٍ آخر (`dq`)؛ ثمّ
    المانعُ المشهود، ثمّ الشرطُ المنفيّ، ثمّ ما لم يُفحص؛ وإلّا ترخيص. -/
def hukmMarbut (d : Option String) (dq : List String) (m s : Option String) (q : List String) : Natija :=
  match d with
  | some x => .madkhalFasid x
  | none =>
    if dq = [] then
      match m, s with
      | some x, _ => .mumtani x
      | none, some x => .laTantabiq x
      | none, none => if q = [] then .murakhkhas else .muallaq q
    else .muallaq dq

/-- **الفاحص.** -/
def hukm (n : Naqla α β) : Natija :=
  if n.marbut then
    hukmMarbut (awwalNaqid n .madkhal) (naqisaMadkhal n) (awwalNaqid n .mani) (awwalNaqid n .shart) (naqisa n)
  else .ghayrMarbut

/-! ## خواصُّ الفاحص -/

/-- كلُّ حالٍ فعليّةٍ لمقدّمةٍ إمّا مطلوبُها، أو نقيضُه، أو أنّها لم تُفحص. -/
theorem hal_thalath (m : Muqaddima) :
    m.halFiil = matlub m.naw ∨ m.halFiil = naqid m.naw ∨ m.halFiil = .ghayrMafhus := by
  cases hn : m.naw <;> cases hh : m.halFiil <;> simp [matlub, naqid]

theorem awwalNaqid_none (n : Naqla α β) (k : Naw) :
    awwalNaqid n k = none ↔ ∀ m ∈ n.muqaddimat, m.naw = k → m.halFiil ≠ naqid k := by
  simp only [awwalNaqid, Option.map_eq_none_iff, List.find?_eq_none, Bool.and_eq_true, beq_iff_eq]
  constructor
  · intro h m hm hk hh
    exact h m hm ⟨hk, hh⟩
  · intro h m hm ⟨hk, hh⟩
    exact h m hm hk hh

theorem naqisa_nil (n : Naqla α β) :
    naqisa n = [] ↔ ∀ m ∈ n.muqaddimat, m.halFiil ≠ .ghayrMafhus := by
  simp [naqisa, List.filter_eq_nil_iff]

theorem naqisaMadkhal_nil (n : Naqla α β) :
    naqisaMadkhal n = [] ↔ (∃ m ∈ n.muqaddimat, m.naw = .madkhal) ∧
      ∀ m ∈ n.muqaddimat, m.naw = .madkhal → m.halFiil ≠ .ghayrMafhus := by
  unfold naqisaMadkhal
  by_cases h : fihiMadkhal n = true
  · have hex : ∃ m ∈ n.muqaddimat, m.naw = .madkhal := by
      simpa [fihiMadkhal, List.any_eq_true] using h
    simp [h, hex, List.filter_eq_nil_iff]
  · have hex : ¬ ∃ m ∈ n.muqaddimat, m.naw = .madkhal := by
      simpa [fihiMadkhal, List.any_eq_true] using h
    simp [h, hex]

theorem hukmMarbut_murakhkhas (d : Option String) (dq : List String) (m s : Option String) (q : List String) :
    hukmMarbut d dq m s q = .murakhkhas ↔ d = none ∧ dq = [] ∧ m = none ∧ s = none ∧ q = [] := by
  cases d <;> by_cases hd : dq = [] <;> cases m <;> cases s <;> by_cases hq : q = [] <;> simp [hukmMarbut, hd, hq]

theorem hukmMarbut_muallaq (d : Option String) (dq : List String) (m s : Option String) (q l : List String) :
    hukmMarbut d dq m s q = .muallaq l ↔
      d = none ∧ ((dq ≠ [] ∧ dq = l) ∨ (dq = [] ∧ m = none ∧ s = none ∧ q ≠ [] ∧ q = l)) := by
  cases d <;> by_cases hd : dq = [] <;> cases m <;> cases s <;> by_cases hq : q = [] <;> simp [hukmMarbut, hd, hq]

theorem hukmMarbut_mumtani (d : Option String) (dq : List String) (m s : Option String) (q : List String) (x : String) :
    hukmMarbut d dq m s q = .mumtani x ↔ d = none ∧ dq = [] ∧ m = some x := by
  cases d <;> by_cases hd : dq = [] <;> cases m <;> cases s <;> by_cases hq : q = [] <;> simp [hukmMarbut, hd, hq]

theorem hukmMarbut_laTantabiq (d : Option String) (dq : List String) (m s : Option String) (q : List String)
    (x : String) : hukmMarbut d dq m s q = .laTantabiq x ↔ d = none ∧ dq = [] ∧ m = none ∧ s = some x := by
  cases d <;> by_cases hd : dq = [] <;> cases m <;> cases s <;> by_cases hq : q = [] <;> simp [hukmMarbut, hd, hq]

/-- **الربطُ أوّلًا:** موضعٌ لا يقع في المصدر لا يُحكم عليه بشيءٍ آخر. -/
theorem ghayrMarbut_awwalan (n : Naqla α β) (h : n.marbut = false) : hukm n = .ghayrMarbut := by
  simp [hukm, h]

/-- مدخلٌ له مقدّمة، ولا مقدّمةَ منه منقوضةٌ ولا غيرُ مفحوصة: مقدّماتُه كلُّها مشهودة. -/
theorem madkhal_mashhud (n : Naqla α β) (hd : awwalNaqid n .madkhal = none) (hdq : naqisaMadkhal n = []) :
    (∃ m ∈ n.muqaddimat, m.naw = .madkhal) ∧ ∀ m ∈ n.muqaddimat, m.naw = .madkhal → m.halFiil = .mashhud := by
  refine ⟨((naqisaMadkhal_nil n).1 hdq).1, ?_⟩
  intro m hm hk
  rcases hal_thalath m with e | e | e
  · rw [e, hk]; rfl
  · exact absurd (by rw [e, hk]) ((awwalNaqid_none n .madkhal).1 hd m hm hk)
  · exact absurd e (((naqisaMadkhal_nil n).1 hdq).2 m hm hk)

/-- **الترخيصُ بكلّ المقدّمات:** يُرخِّص الفاحصُ إذا وفقط إذا كان الانتقالُ مربوطًا، وله مقدّمةُ مدخلٍ واحدةٌ على الأقلّ، وكلُّ مقدّمةٍ على
    مطلوبها بشاهدٍ ذي سند. -/
theorem murakhkhas_iff (n : Naqla α β) :
    hukm n = .murakhkhas ↔ n.marbut = true ∧ (∃ m ∈ n.muqaddimat, m.naw = .madkhal) ∧
      ∀ m ∈ n.muqaddimat, m.halFiil = matlub m.naw := by
  have hk : hukm n = .murakhkhas ↔ n.marbut = true ∧ awwalNaqid n .madkhal = none ∧ naqisaMadkhal n = [] ∧
      awwalNaqid n .mani = none ∧ awwalNaqid n .shart = none ∧ naqisa n = [] := by
    cases hb : n.marbut <;> simp [hukm, hb, hukmMarbut_murakhkhas]
  rw [hk]
  constructor
  · rintro ⟨hb, hd, hdq, hm, hs, hq⟩
    refine ⟨hb, ((naqisaMadkhal_nil n).1 hdq).1, ?_⟩
    intro m hmem
    have nq := (naqisa_nil n).1 hq m hmem
    rcases hal_thalath m with e | e | e
    · exact e
    · exfalso
      cases hk : m.naw
      · exact (awwalNaqid_none n .madkhal).1 hd m hmem hk (by rw [e, hk])
      · exact (awwalNaqid_none n .shart).1 hs m hmem hk (by rw [e, hk])
      · exact (awwalNaqid_none n .mani).1 hm m hmem hk (by rw [e, hk])
    · exact absurd e nq
  · rintro ⟨hb, hex, hall⟩
    have nonaqid : ∀ k, awwalNaqid n k = none := by
      intro k
      refine (awwalNaqid_none n k).2 ?_
      intro m hmem hk he
      have := hall m hmem
      rw [he, hk] at this
      cases k <;> simp [matlub, naqid] at this
    have hq : naqisa n = [] := by
      refine (naqisa_nil n).2 ?_
      intro m hmem he
      have := hall m hmem
      rw [he] at this
      cases hk : m.naw <;> simp [hk, matlub] at this
    have hdq : naqisaMadkhal n = [] := by
      refine (naqisaMadkhal_nil n).2 ⟨hex, ?_⟩
      intro m hmem _
      exact (naqisa_nil n).1 hq m hmem
    exact ⟨hb, nonaqid _, hdq, nonaqid _, nonaqid _, hq⟩

/-- **ما لم يُفحص لا يُرخِّص:** مقدّمةٌ واحدةٌ لم تُفحص — مدخلًا أو شرطًا أو مانعًا — تمنع الترخيص. فالمانعُ المنفيُّ بفحصٍ غيرُ المانع
    الذي لم يُفحص. -/
theorem ghayrMafhus_la_yurakhkhis (n : Naqla α β) (m : Muqaddima) (hm : m ∈ n.muqaddimat)
    (hg : m.halFiil = .ghayrMafhus) : hukm n ≠ .murakhkhas := by
  intro h
  have := ((murakhkhas_iff n).1 h).2.2 m hm
  rw [hg] at this
  cases hk : m.naw <;> simp [hk, matlub] at this

/-- **لا حكمَ بلا مدخلٍ مشهود:** الترخيصُ والامتناعُ وعدمُ الانطباق لا تصدر إلّا عن انتقالٍ مربوطٍ له مقدّمةُ مدخلٍ واحدةٌ على الأقلّ،
    ومقدّماتُ مدخله كلُّها مشهودة. -/
theorem hukm_bi_madkhal_mashhud (n : Naqla α β)
    (h : hukm n = .murakhkhas ∨ (∃ x, hukm n = .mumtani x) ∨ (∃ x, hukm n = .laTantabiq x)) :
    n.marbut = true ∧ (∃ m ∈ n.muqaddimat, m.naw = .madkhal) ∧
      ∀ m ∈ n.muqaddimat, m.naw = .madkhal → m.halFiil = .mashhud := by
  cases hb : n.marbut
  · simp [hukm, hb] at h
  · refine ⟨rfl, madkhal_mashhud n ?_ ?_⟩ <;>
    · simp only [hukm, hb, ite_true, hukmMarbut_murakhkhas, hukmMarbut_mumtani, hukmMarbut_laTantabiq] at h
      rcases h with h | ⟨_, h⟩ | ⟨_, h⟩
      · first | exact h.1 | exact h.2.1
      · first | exact h.1 | exact h.2.1
      · first | exact h.1 | exact h.2.1

/-- **المدخلُ الذي لم يُفحص يعلِّق قبل كلّ حكم:** في انتقالٍ مربوطٍ لا مقدّمةَ مدخلٍ فيه منقوضة، مقدّمةُ مدخلٍ واحدةٌ لم تُفحص تُخرج
    التعليقَ بأسماء ما لم يُفحص من المدخل، أيًّا كانت الموانعُ والشروط. -/
theorem madkhal_ghayrMafhus_yuallaq (n : Naqla α β) (hb : n.marbut = true) (hd : awwalNaqid n .madkhal = none)
    (m : Muqaddima) (hm : m ∈ n.muqaddimat) (hk : m.naw = .madkhal) (hg : m.halFiil = .ghayrMafhus) :
    hukm n = .muallaq (naqisaMadkhal n) := by
  have hne : naqisaMadkhal n ≠ [] := fun e => ((naqisaMadkhal_nil n).1 e).2 m hm hk hg
  simp [hukm, hb, hd, hukmMarbut, hne]

/-- **لا مدخلَ بلا مقدّمة:** انتقالٌ مربوطٌ لا مقدّمةَ فيه لصحّة المدخل يعلِّق باسم `madkhalGhaib`، أيًّا كانت الموانعُ والشروط. -/
theorem bila_madkhal_yuallaq (n : Naqla α β) (hb : n.marbut = true) (h : ∀ m ∈ n.muqaddimat, m.naw ≠ .madkhal) :
    hukm n = .muallaq [madkhalGhaib] := by
  have hd : awwalNaqid n .madkhal = none := (awwalNaqid_none n .madkhal).2 (fun m hm hk _ => h m hm hk)
  have hf : fihiMadkhal n = false := by
    simpa [fihiMadkhal, List.any_eq_true] using h
  simp [hukm, hb, hd, hukmMarbut, naqisaMadkhal, hf]

/-- **لا شهادةَ بلا سند.** -/
theorem la_shahada_bila_sanad (m : Muqaddima) (h : m.sanad = "") : m.halFiil = .ghayrMafhus := by
  simp [Muqaddima.halFiil, h]

/-- **المدخلُ الفاسد ليس حكمًا لغويًّا:** في انتقالٍ مربوط، مقدّمةُ مدخلٍ منفيّةٌ تُخرج المدخلَ الفاسد باسمها أيًّا كانت الموانع والشروط. -/
theorem madkhal_awwalan (n : Naqla α β) (hb : n.marbut = true) (s : String) (hd : awwalNaqid n .madkhal = some s) :
    hukm n = .madkhalFasid s := by
  simp [hukm, hb, hd, hukmMarbut]

/-- **المانعُ المعروف يمنع:** في انتقالٍ مربوطٍ له مقدّمةُ مدخلٍ ومقدّماتُ مدخله كلُّها مشهودة، مانعٌ مشهودٌ يُخرج الامتناعَ، ولا يُخفيه شاهدٌ آخر. -/
theorem mani_mashhud_yamna (n : Naqla α β) (hb : n.marbut = true) (hex : ∃ m ∈ n.muqaddimat, m.naw = .madkhal)
    (hmad : ∀ m ∈ n.muqaddimat, m.naw = .madkhal → m.halFiil = .mashhud)
    (m : Muqaddima) (hm : m ∈ n.muqaddimat) (hk : m.naw = .mani) (hh : m.halFiil = .mashhud) :
    ∃ s, hukm n = .mumtani s := by
  have hd : awwalNaqid n .madkhal = none := by
    refine (awwalNaqid_none n .madkhal).2 ?_
    intro m' hm' hk' e
    rw [hmad m' hm' hk'] at e; cases e
  have hdq : naqisaMadkhal n = [] := by
    refine (naqisaMadkhal_nil n).2 ⟨hex, ?_⟩
    intro m' hm' hk' e
    rw [hmad m' hm' hk'] at e; cases e
  cases hmn : awwalNaqid n .mani with
  | none =>
      exact absurd hh ((awwalNaqid_none n .mani).1 hmn m hm hk)
  | some s => exact ⟨s, by simp [hukm, hb, hd, hdq, hmn, hukmMarbut]⟩

/-- **التعليقُ يسمّي ما لم يُفحص:** غيرُ فارغ، وكلُّ اسمٍ فيه مقدّمةٌ لم تُفحص، أو `madkhalGhaib` حين لا مقدّمةَ للمدخل؛ وهو ما لم يُفحص من
    المدخل إن كان فيه ذلك، وإلّا ما لم يُفحص كلُّه. -/
theorem muallaq_asma (n : Naqla α β) (l : List String) (h : hukm n = .muallaq l) :
    (l = naqisaMadkhal n ∨ l = naqisa n) ∧ l ≠ [] ∧
      ∀ s ∈ l, (∃ m ∈ n.muqaddimat, m.ism = s ∧ m.halFiil = .ghayrMafhus) ∨
        (s = madkhalGhaib ∧ ∀ m ∈ n.muqaddimat, m.naw ≠ .madkhal) := by
  cases hb : n.marbut <;> simp only [hukm, hb] at h
  · simp at h
  · simp only [ite_true, hukmMarbut_muallaq] at h
    rcases h.2 with ⟨hne, rfl⟩ | ⟨_, _, _, hne, rfl⟩
    · refine ⟨Or.inl rfl, hne, ?_⟩
      intro s hs'
      unfold naqisaMadkhal at hs'
      by_cases hf : fihiMadkhal n = true
      · simp only [hf, ite_true, List.mem_map, List.mem_filter, Bool.and_eq_true, beq_iff_eq] at hs'
        obtain ⟨m, ⟨hmem, _, hg⟩, rfl⟩ := hs'
        exact Or.inl ⟨m, hmem, rfl, hg⟩
      · simp only [hf, Bool.false_eq_true, ite_false, List.mem_singleton] at hs'
        refine Or.inr ⟨hs', ?_⟩
        intro m hm hk
        exact hf (List.any_eq_true.2 ⟨m, hm, by simp [hk]⟩)
    · refine ⟨Or.inr rfl, hne, ?_⟩
      intro s hs'
      simp only [naqisa, List.mem_map, List.mem_filter, beq_iff_eq] at hs'
      obtain ⟨m, ⟨hmem, hg⟩, rfl⟩ := hs'
      exact Or.inl ⟨m, hmem, rfl, hg⟩

/-! ## القاعدةُ بمعناها، وسلامةُ الشهادة -/

/-- **قاعدةٌ بمعناها:** هويّتُها، ومقدّماتُها بأسمائها وأنواعها، وتطبيقُها، ومعنى صحّة المدخل (ومنها مطابقةُ المصدر والموضع)
    وصدقِ كلّ مقدّمةٍ وصحّةِ المخرج ضمن النطاق؛ وعقدُها. -/
structure Qaida (α β : Type) where
  hawiyya : Hawiyya
  asma : List (String × Naw)
  tatbiq : α → β
  sahihMadkhal : Source Char → Span → α → Prop
  sadiq : String → α → Prop
  sahihMakhraj : Source Char → Span → α → β → Prop
  /-- **العقد:** صحّةُ المدخل ∧ ثبوتُ المدخل والشروط ∧ انتفاءُ الموانع ⇒ صحّةُ المخرج. -/
  aqd : ∀ src sp x, sahihMadkhal src sp x →
    (∀ p ∈ asma, p.2 ≠ .mani → sadiq p.1 x) → (∀ p ∈ asma, p.2 = .mani → ¬ sadiq p.1 x) →
    sahihMakhraj src sp x (tatbiq x)

/-- **أمانةُ الشهادة لقاعدتها:** الهويّةُ هي هي، والمخرجُ تطبيقُها، والمقدّماتُ مقدّماتُها بأسمائها وأنواعها وترتيبها. -/
def Amin (q : Qaida α β) (n : Naqla α β) : Prop :=
  n.qaida = q.hawiyya ∧ n.makhraj = q.tatbiq n.madkhal ∧ n.muqaddimat.map (fun m => (m.ism, m.naw)) = q.asma

/-- **صدقُ الشواهد:** المشهودةُ صادقةٌ والمنفيّةُ كاذبة على المدخل. فرضٌ على مؤوِّل الشواهد. -/
def Sidq (q : Qaida α β) (n : Naqla α β) : Prop :=
  ∀ m ∈ n.muqaddimat, (m.halFiil = .mashhud → q.sadiq m.ism n.madkhal) ∧
    (m.halFiil = .manfi → ¬ q.sadiq m.ism n.madkhal)

/-- **سلامةُ الشهادة:** شهادةٌ أمينةٌ لقاعدتها، صادقةُ الشواهد، مدخلُها صحيح، يرخّصها الفاحص ⇒ مخرجُها صحيحٌ بعقد القاعدة. -/
theorem shahada_salima (q : Qaida α β) (n : Naqla α β) (amin : Amin q n) (sidq : Sidq q n)
    (madkhal : q.sahihMadkhal n.masdar n.mawdi n.madkhal) (h : hukm n = .murakhkhas) :
    q.sahihMakhraj n.masdar n.mawdi n.madkhal n.makhraj := by
  obtain ⟨_, hout, hasma⟩ := amin
  have hall := ((murakhkhas_iff n).1 h).2.2
  rw [hout]
  apply q.aqd _ _ _ madkhal
  · intro p hp hk
    rw [← hasma] at hp
    obtain ⟨m, hmem, rfl⟩ := List.mem_map.1 hp
    have e := hall m hmem
    have hm : m.halFiil = .mashhud := by
      cases hn : m.naw
      · simpa [hn, matlub] using e
      · simpa [hn, matlub] using e
      · exact absurd hn hk
    exact (sidq m hmem).1 hm
  · intro p hp hk
    rw [← hasma] at hp
    obtain ⟨m, hmem, rfl⟩ := List.mem_map.1 hp
    have e := hall m hmem
    have hm : m.halFiil = .manfi := by
      simp only at hk
      simpa [hk, matlub] using e
    exact (sidq m hmem).2 hm

/-! ## شاهدٌ على الفرق بين ما لم يُفحص وما نُفي بفحص -/

def masdarShahid : Source Char := ⟨1, 1, 1, 1, ['ك']⟩
def mawdiShahid : Span := ⟨1, 1, 1, 1, 0, 1⟩

/-- انتقالٌ مثالٌ مانعُه بحالٍ معطاة. -/
def naqlaShahid (h : Hal) : Naqla (List Char) (List Nat) :=
  ⟨masdarShahid, mawdiShahid, ['ك'], [32], ⟨"mithal", 1⟩,
   [⟨"مدخل", .madkhal, .mashhud, "s"⟩, ⟨"شرط", .shart, .mashhud, "s"⟩, ⟨"مانع", .mani, h, "s"⟩], [], "مثال"⟩

/-- المانعُ نفسُه: منفيًّا يُرخِّص، وغيرَ مفحوصٍ يعلِّق باسمه، ومشهودًا يمنع؛ وبسندٍ فارغ لا يُعدّ منفيًّا. وبلا مقدّمةٍ للمدخل يعلِّق
    باسم `madkhalGhaib` ولو نُفي المانع؛ ومدخلٌ لم يُفحص يعلِّق باسمه ولو شُهد المانع. -/
theorem shahid_mani :
    hukm (naqlaShahid .manfi) = .murakhkhas ∧
    hukm (naqlaShahid .ghayrMafhus) = .muallaq ["مانع"] ∧
    hukm (naqlaShahid .mashhud) = .mumtani "مانع" ∧
    hukm { naqlaShahid .manfi with
      muqaddimat := [⟨"مدخل", .madkhal, .mashhud, "s"⟩, ⟨"شرط", .shart, .mashhud, "s"⟩, ⟨"مانع", .mani, .manfi, ""⟩] } =
      .muallaq ["مانع"] ∧
    hukm { naqlaShahid .manfi with muqaddimat := [⟨"شرط", .shart, .mashhud, "s"⟩, ⟨"مانع", .mani, .manfi, "s"⟩] } =
      .muallaq ["صحة المدخل"] ∧
    hukm { naqlaShahid .mashhud with
      muqaddimat := [⟨"مدخل", .madkhal, .ghayrMafhus, ""⟩, ⟨"شرط", .shart, .mashhud, "s"⟩, ⟨"مانع", .mani, .mashhud, "s"⟩] } =
      .muallaq ["مدخل"] := by
  decide

end Nizam.Shahada
