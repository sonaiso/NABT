/-
  Nizam/Silsila.lean — الجسرُ الجامع: سلسلةُ شهاداتٍ موصولةٌ لكلّ انتقال، من مقاطع التحصيل إلى حكم الجملة.

  **القول.** رسالةُ المالك 2026-10-29، ووقتُها (11:10 بتوقيت عمّان) وصدرُها من ملخّص الجلسة بعد ضغطها (لا الرسالةُ الخامّ)؛ وصدرُها فيه بنصّه:
  «الجسر الجامع المطلوب لكل انتقال هو شهادة مرتبطة بالعملية نفسها: صحة المدخل ∧ مقدمات القاعدة المكتسبة ∧ مطابقة المصدر والمقام ⟹ صحة
  المخرج ضمن النطاق؛ وتحمل كل عقدة: مصدرها وموضعها، والمدخل والمخرج، وهوية القاعدة، وشهادات مقدماتها، والبدائل الباقية، وحدود الدعوى»؛
  وفيها أولويّاتٌ خمس، بمعناها من الملخّص لا بلفظها: إغلاقُ التحصيل، ووصلُ السمات بالإطار وعائلةُ الأسماء الستّة، ووصلُ القرائن بشهاداتٍ
  وتمييزُ أنّ المانع غيرُ موجود عن أنّه لم يُفحص وجودُه، ووصلُ التحليل بصكّ الجملة، والقياسُ على مراجع مستقلّة؛ وآخرُها بنصّه: «ابني البرهان
  والشيفرة المتكاملة والمترابطة والمتناسقة لتحقيق الذكاء الاصطناعي التفسيري». والتصميمُ وتعييناتُه قرارُ البنّاء.

  **ما كان.** العقدُ (`Nizam/Shahada.lean`) مطبَّقٌ على مقاطع التحصيل وحدها (`Dal.Tahsil.shahada`)، والقارئُ يحمل لكلّ خليّةٍ شهادةَ مقطعها
  (`Dal.QiraaTahsil.qiraa_shahada`). أمّا الكلمةُ والإطارُ وحكمُ الأسماء الستّة (`Jisr.QawaidSitta.hukmSitta`) وحكمُ الجملة
  (`Jisr.NassItar.hukmNass`) فأحكامٌ ثلاثيّةٌ بلا شهادة: «لا حكم» فيها لا يفرّق بين مانعٍ فُحص فانتفى ومقدّمةٍ لم تُفحص، ولا يصل الحكمُ بمقدّمات
  مدخله.

  **ما صار.**
  * **الرفع** (`rafa`): حكمُ الفاحص على عقدةٍ ابنٍ يصير مقدّماتِ «صحّة المدخل» في أبيها: المرخَّصُ مشهود، والمعلَّقُ مقدّماتٌ لم تُفحص بأسماء
    نقصه مسبوقةً باسم الابن، وما سواهما (ومنه عدمُ الانطباق) منفيٌّ باسم سببه — فيصير الأبُ «مدخلًا فاسدًا» باسمه (تعيينٌ: كلمةٌ ردّها القارئ مدخلٌ
    فاسدٌ للجملة). فـ**الترخيصُ لا يعلو أبناءه** (`abna_murakhkhas`)، و**النقصُ ظاهرٌ باسمه** (`naqs_zahir`)، و**الحكمُ الحاسمُ يسمّي مقدّمتَه**
    (`hasim_ism`).
  * **عقدةُ الكلمة** (`uqdaKalima`): شهاداتُ مقاطع تحصيلها مرفوعةً، وقراءةُ القارئ شرطًا (`kalima_murakhkhas`).
  * **عقدةُ الإطار** (`uqdaItar`): كلماتُ الجملة مرفوعةً، وحدُّ الطبقة (`Utur.fiHadd`) شرطًا، ومكوّناتُ `hukmSitta` الستّة موانعَ بأسمائها؛ وحالُ المانع
    **تعيينُ البنّاء** (`halUtur`): المكوّنُ المرخِّص مانعٌ فُحص فانتفى، والممتنعُ مشهود، و«لا حكم» لم يُفحص — وقد يكون لـ«لا حكم» المكوّن سببٌ مسمّى
    عند `Jisr.Utur` (`SababLaHukm`)، فـ«لم يُفحص» هنا أنّ المانعَ لم يُحسم، لا أنّ شيئًا لم يُنظر فيه. وبفرض ربط العقدة وكلماتٍ مرخَّصةٍ غيرِ فارغة،
    حكمُ الفاحص هو `hukmSitta` في الترخيص والامتناع (`itar_murakhkhas`، `itar_mumtani`)، و«لا حكم» فيه عدمُ انطباقٍ أو تعليق (`itar_laHukm`)؛
    وأيُّهما وبأيّ اسمٍ من `itar_ahwal`.
  * **عقدةُ الجملة** (`uqdaJumla`): كلماتُها مرفوعةً، ثمّ إطاراتُها **بأحكام الفاحص على شهاداتها** (`uturNatija`): إطارٌ مرخَّصٌ شرطًا مشهودًا ومخرجُه
    أدوارُه والبدائلُ الباقيةُ أدوارُ الإطارات الأخرى غيرِ الممتنعة؛ وإلّا الإطاراتُ كلُّها ممتنعةٌ مانعًا مشهودًا، أو لا إطارَ شرطًا منفيًّا، أو الإطاراتُ
    غيرُ الممتنعة مرفوعةً بشهاداتها (`rafaItar`: المعلَّقُ شروطٌ لم تُفحص بأسماء نقصه، وغيرُ المنطبق شرطٌ منفيّ). وبالفروض نفسِها حكمُها هو `jamaa`
    على أحكام إطاراتها الثلاثيّة إذا قابلتها أحكامُ الفاحص (`jumla_natija`، `jumla_jamaa`).
  * **السلسلةُ التامّة من النصّ** (`silsila_murakhkhas`): بفرض ربط الجملة وكلماتها، ترخيصُ الجملة هو أن تكون لها كلمة، وكلُّ مقطعٍ من كلّ كلمةٍ مرخَّصًا،
    وكلُّ كلمةٍ مقروءة، و`hukmNass` مقبولًا. وربطُ الإطار ربطُ الجملة (`uqdaU_marbut`).

  **حدُّه.** الرفعُ والعقدُ بناءٌ على أحكامٍ قائمة: لا قاعدةَ لغويّةً جديدة، ولا يرفع «لا حكم» إلى حكم؛ وإنّما يسمّي ما نقص ويمنع ترخيصًا بلا
  مقدّماته. وصحّةُ الأحكام نفسِها لغةً ما شهدت به قطعُها (الضوابطُ المجمَّدة وحدودُها)، فمخرجُ الجملة (أدوارُ الإطار) سلوكُ المحرّك لا تعيينٌ صحيحٌ
  للأدوار. والكلمةُ تُقرأ في الوصل وحده؛ وربطُ الكلمات فرضٌ يطبعه التنفيذيّ؛ والإطاراتُ من `Jisr.NassItar.itarat` داخلَ الحدّ فيما رُصد، ففرعُ
  الإطار غيرِ المنطبق في الجملة لم يمسّه نصّ. وتنفيذُ السلسلة على النصّ `Qari/Silsila.lean` (التنفيذيّ `silsila`)، ويفحصه `tahaqquq/test_silsila.py`.
-/
import Jisr.NassItar
import Dal.QiraaTahsil

namespace Nizam.Silsila

open Nizam.Shahada
open Jisr.Utur (Hukm damm ofBool fiHadd ibtida3 waqf3 hukmTarkib waslMadlul)

/-! ## ١. الرفع: حكمُ الابن مقدّماتٌ في أبيه -/

def sanadRafa : String := "Nizam.Silsila.rafa"

/-- **الرفع:** حكمُ الابن المسمّى `ism` مقدّماتُ «صحّة المدخل» في أبيه. -/
def rafa (ism : String) : Natija → List Muqaddima
  | .murakhkhas => [⟨ism, .madkhal, .mashhud, sanadRafa⟩]
  | .muallaq l => (if l.isEmpty then [ism] else l.map (fun x => ism ++ " ← " ++ x)).map
      fun x => ⟨x, .madkhal, .ghayrMafhus, sanadRafa⟩
  | .madkhalFasid x => [⟨ism ++ " ← " ++ x, .madkhal, .manfi, sanadRafa⟩]
  | .mumtani x => [⟨ism ++ " ← " ++ x, .madkhal, .manfi, sanadRafa⟩]
  | .laTantabiq x => [⟨ism ++ " ← " ++ x, .madkhal, .manfi, sanadRafa⟩]
  | .ghayrMarbut => [⟨ism ++ " ← غير مربوط", .madkhal, .manfi, sanadRafa⟩]

/-- رفعُ الأبناء جميعًا بترتيبهم. -/
def rafaKull (cs : List (String × Natija)) : List Muqaddima := cs.flatMap fun c => rafa c.1 c.2

theorem rafa_naw (s : String) (v : Natija) : ∀ m ∈ rafa s v, m.naw = .madkhal := by
  intro m hm
  cases v <;> simp [rafa] at hm
  all_goals first
    | (rcases hm with rfl; rfl)
    | (subst hm; rfl)
    | (split at hm <;> simp at hm <;> (try obtain ⟨_, _, rfl⟩ := hm) <;> (try subst hm) <;> rfl)

theorem rafa_ne (s : String) (v : Natija) : rafa s v ≠ [] := by
  cases v <;> simp [rafa]
  split <;> simp_all

/-- **الرفعُ يحفظ الترخيص وحده:** مقدّماتُ الابن المرفوعةُ على مطلوبها كلُّها إذا وفقط إذا كان مرخَّصًا. -/
theorem rafa_matlub (s : String) (v : Natija) :
    (∀ m ∈ rafa s v, m.halFiil = matlub m.naw) ↔ v = .murakhkhas := by
  constructor
  · intro h
    cases v with
    | murakhkhas => rfl
    | muallaq l =>
      exfalso
      obtain ⟨m, hm⟩ := List.exists_mem_of_ne_nil _ (rafa_ne s (.muallaq l))
      have := h m hm
      rw [rafa_naw s _ m hm] at this
      simp only [rafa, List.mem_map] at hm
      obtain ⟨x, _, rfl⟩ := hm
      simp [Muqaddima.halFiil, matlub, sanadRafa] at this
    | madkhalFasid x =>
      have := h _ (List.mem_singleton_self _); simp [Muqaddima.halFiil, matlub, sanadRafa] at this
    | mumtani x =>
      have := h _ (List.mem_singleton_self _); simp [Muqaddima.halFiil, matlub, sanadRafa] at this
    | laTantabiq x =>
      have := h _ (List.mem_singleton_self _); simp [Muqaddima.halFiil, matlub, sanadRafa] at this
    | ghayrMarbut =>
      have := h _ (List.mem_singleton_self _); simp [Muqaddima.halFiil, matlub, sanadRafa] at this
  · rintro rfl m hm
    simp only [rafa, List.mem_singleton] at hm
    subst hm
    simp [Muqaddima.halFiil, matlub, sanadRafa]

theorem mem_rafaKull {cs : List (String × Natija)} {c : String × Natija} (hc : c ∈ cs) :
    ∀ m ∈ rafa c.1 c.2, m ∈ rafaKull cs := fun _ hm => List.mem_flatMap.2 ⟨c, hc, hm⟩

/-- **الترخيصُ لا يعلو أبناءه:** عقدةٌ مقدّماتُها أبناؤها مرفوعين ثمّ ما شاءت، إن رُخِّصت فكلُّ ابنٍ لها مرخَّص. -/
theorem abna_murakhkhas {α β : Type} (n : Naqla α β) (cs : List (String × Natija)) (r : List Muqaddima)
    (hm : n.muqaddimat = rafaKull cs ++ r) (hk : hukm n = .murakhkhas) : ∀ c ∈ cs, c.2 = .murakhkhas := by
  intro c hc
  have hall := ((murakhkhas_iff n).1 hk).2.2
  refine (rafa_matlub c.1 c.2).1 fun m hmr => hall m ?_
  rw [hm]
  exact List.mem_append_left _ (mem_rafaKull hc m hmr)

/-- **النقصُ ظاهرٌ باسمه:** ابنٌ معلَّقٌ بمقدّمةٍ لم تُفحص يمنع ترخيصَ أبيه، وتبقى في مقدّمات الأب مقدّمةً لم تُفحص باسمها مسبوقًا باسم
    الابن. -/
theorem naqs_zahir {α β : Type} (n : Naqla α β) (cs : List (String × Natija)) (r : List Muqaddima)
    (hm : n.muqaddimat = rafaKull cs ++ r) (c : String × Natija) (hc : c ∈ cs) (l : List String) (hl : c.2 = .muallaq l)
    (x : String) (hx : x ∈ l) :
    hukm n ≠ .murakhkhas ∧ ∃ m ∈ n.muqaddimat, m.ism = c.1 ++ " ← " ++ x ∧ m.halFiil = .ghayrMafhus := by
  have hne : l.isEmpty = false := by cases l <;> simp_all
  have hmem : (⟨c.1 ++ " ← " ++ x, .madkhal, .ghayrMafhus, sanadRafa⟩ : Muqaddima) ∈ n.muqaddimat := by
    rw [hm]
    refine List.mem_append_left _ (mem_rafaKull hc _ ?_)
    rw [hl]
    simp only [rafa, hne, Bool.false_eq_true, ite_false, List.map_map, List.mem_map, Function.comp_def]
    exact ⟨x, hx, rfl⟩
  refine ⟨fun hk => ?_, _, hmem, rfl, by simp [Muqaddima.halFiil, sanadRafa]⟩
  have := ((murakhkhas_iff n).1 hk).2.2 _ hmem
  simp [Muqaddima.halFiil, matlub, sanadRafa] at this

/-- أبناءٌ مرخَّصون: مقدّماتُهم المرفوعةُ مدخلٌ مشهود. -/
theorem rafaKull_mashhud {cs : List (String × Natija)} (h : ∀ c ∈ cs, c.2 = .murakhkhas) :
    ∀ m ∈ rafaKull cs, m.naw = .madkhal ∧ m.halFiil = .mashhud := by
  intro m hm
  obtain ⟨c, hc, hmc⟩ := List.mem_flatMap.1 hm
  rw [h c hc] at hmc
  simp only [rafa, List.mem_singleton] at hmc
  subst hmc
  simp [Muqaddima.halFiil, sanadRafa]

theorem rafaKull_madkhal {cs : List (String × Natija)} (hk : cs ≠ []) : ∃ m ∈ rafaKull cs, m.naw = .madkhal := by
  obtain ⟨c, hc⟩ := List.exists_mem_of_ne_nil _ hk
  obtain ⟨m, hm⟩ := List.exists_mem_of_ne_nil _ (rafa_ne c.1 c.2)
  exact ⟨m, mem_rafaKull hc m hm, rafa_naw _ _ m hm⟩

/-! ## ٢. أدواتٌ على الفاحص: المدخلُ المشهود ثمّ ما بعده -/

/-- مدخلٌ مشهودٌ كلُّه: الحكمُ بعده بالموانع والشروط وما لم يُفحص. -/
theorem hukm_madkhal_salim {α β : Type} (n : Naqla α β) (hb : n.marbut = true)
    (hex : ∃ m ∈ n.muqaddimat, m.naw = .madkhal)
    (hall : ∀ m ∈ n.muqaddimat, m.naw = .madkhal → m.halFiil = .mashhud) :
    hukm n = hukmMarbut none [] (awwalNaqid n .mani) (awwalNaqid n .shart) (naqisa n) := by
  have hd : awwalNaqid n .madkhal = none :=
    (awwalNaqid_none n .madkhal).2 fun m hm hk => by rw [hall m hm hk]; simp [naqid]
  have hdq : naqisaMadkhal n = [] :=
    (naqisaMadkhal_nil n).2 ⟨hex, fun m hm hk => by rw [hall m hm hk]; simp⟩
  simp only [hukm, hb, ite_true, hd, hdq]

theorem awwalNaqid_mani_none {α β : Type} (n : Naqla α β) :
    awwalNaqid n .mani = none ↔ ∀ m ∈ n.muqaddimat, m.naw = .mani → m.halFiil ≠ .mashhud :=
  awwalNaqid_none n .mani

theorem awwalNaqid_shart_none {α β : Type} (n : Naqla α β) :
    awwalNaqid n .shart = none ↔ ∀ m ∈ n.muqaddimat, m.naw = .shart → m.halFiil ≠ .manfi :=
  awwalNaqid_none n .shart

/-- بعد مدخلٍ مشهود لا يبقى إلّا أربعة: ترخيصٌ، أو امتناعٌ، أو عدمُ انطباق، أو تعليق. -/
theorem baad_madkhal (m s : Option String) (q : List String) :
    hukmMarbut none [] m s q = .murakhkhas ∨ (∃ x, hukmMarbut none [] m s q = .mumtani x) ∨
      (∃ x, hukmMarbut none [] m s q = .laTantabiq x) ∨ ∃ l, hukmMarbut none [] m s q = .muallaq l := by
  cases m <;> cases s <;> by_cases hq : q = [] <;> simp [hukmMarbut, hq]

/-- **الحكمُ الحاسمُ يسمّي مقدّمتَه:** الامتناعُ باسمِ مانعٍ مشهودٍ في المقدّمات، وعدمُ الانطباق باسمِ شرطٍ منفيٍّ فيها. -/
theorem hasim_ism {α β : Type} (n : Naqla α β) (x : String) :
    (hukm n = .mumtani x → ∃ m ∈ n.muqaddimat, m.ism = x ∧ m.naw = .mani ∧ m.halFiil = .mashhud) ∧
    (hukm n = .laTantabiq x → ∃ m ∈ n.muqaddimat, m.ism = x ∧ m.naw = .shart ∧ m.halFiil = .manfi) := by
  have key : ∀ k, awwalNaqid n k = some x → ∃ m ∈ n.muqaddimat, m.ism = x ∧ m.naw = k ∧ m.halFiil = naqid k := by
    intro k h
    simp only [awwalNaqid, Option.map_eq_some_iff] at h
    obtain ⟨m, hf, rfl⟩ := h
    have hp := List.find?_some hf
    simp only [Bool.and_eq_true, beq_iff_eq] at hp
    exact ⟨m, List.mem_of_find?_eq_some hf, rfl, hp.1, hp.2⟩
  constructor
  · intro h
    cases hb : n.marbut <;> simp only [hukm, hb] at h
    · cases h
    · simp only [ite_true, hukmMarbut_mumtani] at h
      exact key .mani h.2.2
  · intro h
    cases hb : n.marbut <;> simp only [hukm, hb] at h
    · cases h
    · simp only [ite_true, hukmMarbut_laTantabiq] at h
      exact key .shart h.2.2.2

/-! ## ٣. الموانعُ بأحوالها الثلاث: «انتفى» غيرُ «لم يُفحص» -/

/-- حالُ مانعٍ من مكوّنٍ ثلاثيّ: المرخِّصُ مانعٌ فُحص فانتفى، والممتنعُ مانعٌ مشهود، و«لا حكم» مانعٌ لم يُفحص. -/
def halUtur : Hukm → Hal
  | .murakhkhas => .manfi
  | .mumtani => .mashhud
  | .laHukm => .ghayrMafhus

def sanadMani : String := "Jisr.QawaidSitta.hukmSitta"

def maniOf (x : String × Hukm) : Muqaddima := ⟨x.1, .mani, halUtur x.2, sanadMani⟩

theorem maniOf_hal (x : String × Hukm) : (maniOf x).halFiil = halUtur x.2 := by
  simp [maniOf, Muqaddima.halFiil, sanadMani]

/-- ضمُّ المكوّنات كلّها. -/
def dammKull (hs : List Hukm) : Hukm := hs.foldr damm .murakhkhas

theorem dammKull_murakhkhas (hs : List Hukm) : dammKull hs = .murakhkhas ↔ ∀ h ∈ hs, h = .murakhkhas := by
  induction hs with
  | nil => simp [dammKull]
  | cons a hs ih =>
    simp only [dammKull, List.foldr_cons] at ih ⊢
    rw [Jisr.Utur.damm_murakhkhas, ih]
    simp

theorem dammKull_mumtani (hs : List Hukm) : dammKull hs = .mumtani ↔ Hukm.mumtani ∈ hs := by
  induction hs with
  | nil => simp [dammKull]
  | cons a hs ih =>
    simp only [dammKull, List.foldr_cons] at ih ⊢
    rw [Jisr.Utur.damm_mumtani, ih, List.mem_cons]
    constructor <;> rintro (h | h) <;> simp_all

/-- الثالثُ المرفوع على الأحكام الثلاثيّة. -/
theorem hukm_thalath (h : Hukm) : h = .laHukm ↔ h ≠ .murakhkhas ∧ h ≠ .mumtani := by
  cases h <;> simp

/-- **عقدةٌ بمدخلٍ مشهود تقابل حكمًا ثلاثيًّا** إن قابلته في الترخيص والامتناع: و«لا حكم» فيه عدمُ انطباقٍ أو تعليقٌ في الشهادة. -/
theorem laHukm_min_ithnayn {α β : Type} (n : Naqla α β) (h : Hukm)
    (hbaad : ∃ m s q, hukm n = hukmMarbut none [] m s q)
    (h1 : hukm n = .murakhkhas ↔ h = .murakhkhas) (h2 : (∃ x, hukm n = .mumtani x) ↔ h = .mumtani) :
    h = .laHukm ↔ (∃ x, hukm n = .laTantabiq x) ∨ ∃ l, hukm n = .muallaq l := by
  obtain ⟨m, s, q, he⟩ := hbaad
  rw [hukm_thalath, ne_eq, ne_eq, ← h1, ← h2]
  rcases baad_madkhal m s q with e | ⟨x, e⟩ | ⟨x, e⟩ | ⟨l, e⟩ <;> rw [← he] at e <;> simp [e]

/-! ## ٤. عقدةُ الإطار: حكمُ الأسماء الستّة بمقدّماته -/

open Jisr.QawaidSitta (hukmSitta qiraaSitta)

/-- مكوّناتُ `hukmSitta` الستّة بأسمائها (داخلَ الحدّ)؛ والاسمُ اسمُ المانع، وسندُه المكوّنُ في Lean. -/
def ajzaSitta (u : Jisr.Utur.Itar3) : List (String × Hukm) :=
  [("خلل الابتداء (Jisr.Utur.ibtida3)", ofBool (ibtida3 u)),
   ("خلل التركيب (Jisr.Utur.hukmTarkib)", hukmTarkib (Dal.rakkib u.kalimat)),
   ("خلل الوصل بخانات المالك (Jisr.Utur.waslBase، waslMl، jisrMadlul)",
     ofBool (Jisr.Utur.waslBase u && Jisr.Utur.waslMl u && Jisr.Utur.jisrMadlul u)),
   ("خلل قراءة الأسماء الستّة (Jisr.QawaidSitta.qiraaSitta)", qiraaSitta u),
   ("خلل وصل المدلول (Jisr.Utur.waslMadlul)", waslMadlul u.isnad),
   ("خلل الوقف (Jisr.Utur.waqf3)", ofBool (waqf3 u))]

/-- **`hukmSitta` ضمُّ مكوّناته** داخلَ الحدّ (تبديلُ ترتيب الضمّ). -/
theorem hukmSitta_ajza (u : Jisr.Utur.Itar3) :
    hukmSitta u = if fiHadd u then dammKull ((ajzaSitta u).map (·.2)) else .laHukm := by
  unfold hukmSitta
  split
  · simp only [ajzaSitta, dammKull, List.map_cons, List.map_nil, List.foldr_cons, List.foldr_nil]
    generalize ofBool (ibtida3 u) = a
    generalize hukmTarkib (Dal.rakkib u.kalimat) = b
    generalize ofBool (Jisr.Utur.waslBase u && Jisr.Utur.waslMl u && Jisr.Utur.jisrMadlul u) = c
    generalize qiraaSitta u = d
    generalize waslMadlul u.isnad = e
    generalize ofBool (waqf3 u) = f
    cases a <;> cases b <;> cases c <;> cases d <;> cases e <;> cases f <;> rfl
  · rfl

def ismHadd : String := "حدّ الطبقة (Jisr.Utur.fiHadd)"
def sanadHadd : String := "Jisr.Utur.asbabKharij"

/-- اسمُ سببِ الخروج عن الحدّ: اسمُه في Lean. -/
def sababIsm : Jisr.Utur.SababLaHukm → String
  | .itarThani => "itarThani" | .mulhaqMutaqaddim => "mulhaqMutaqaddim" | .amilIsmi => "amilIsmi"
  | .naibMajrur => "naibMajrur" | .mawdiNutq => "mawdiNutq" | .mulhaqGhayrMufrad => "mulhaqGhayrMufrad"
  | .musnadGhayrZahir => "musnadGhayrZahir" | .musnadIlayhGhayrZahir => "musnadIlayhGhayrZahir"
  | .filMurabKharij => "filMurabKharij" | .ismGhayrMufrad => "ismGhayrMufrad" | .laTamthil => "laTamthil"
  | .itarYarudd => "itarYarudd" | .illaAkhir => "illaAkhir" | .fathaJarr => "fathaJarr" | .irabBilHarf => "irabBilHarf"
  | .tarkib => "tarkib" | .madlul => "madlul"

/-- مقدّماتُ الإطار بعد كلماته: داخلَ الحدّ الحدُّ شرطًا مشهودًا ثمّ مكوّناتُ `hukmSitta` موانعَ؛ وخارجَه الحدُّ شرطًا منفيًّا باسم
    أسبابه. -/
def baqiItar (u : Jisr.Utur.Itar3) : List Muqaddima :=
  if fiHadd u then ⟨ismHadd, .shart, .mashhud, sanadHadd⟩ :: (ajzaSitta u).map maniOf
  else [⟨ismHadd ++ ": " ++ ", ".intercalate ((Jisr.Utur.asbabKharij u).map sababIsm), .shart, .manfi, sanadHadd⟩]

/-- **عقدةُ الإطار:** مصدرُها وموضعُها، ومدخلُها الكلماتُ ومخرجُها الأدوار، وهويّةُ قاعدتها `hukmSitta`، ومقدّماتُها، وحدُّها. -/
def uqdaItar (src : Nabt.UnitDiscovery.Source Char) (sp : Nabt.UnitDiscovery.Span) (madkhal adwar : String)
    (kalimat : List (String × Natija)) (u : Jisr.Utur.Itar3) : Naqla String String :=
  ⟨src, sp, madkhal, adwar, ⟨"Jisr.QawaidSitta.hukmSitta", 1⟩, rafaKull kalimat ++ baqiItar u, [],
    "الدالُّ والبنيةُ بصفّ الأسماء الستّة، والمدلولُ مفروض (Jisr.NassItar)"⟩

/-- كلُّ ما في مقدّماتٍ أوّلُها مدخلٌ مشهودٌ وما بعده بلا مدخل يحقّق ما يحقّقه ما بعده. -/
theorem kull_baqi (pre r : List Muqaddima) (P : Muqaddima → Prop) (hp : ∀ m ∈ pre, P m) :
    (∀ m ∈ pre ++ r, P m) ↔ ∀ m ∈ r, P m := by
  constructor
  · intro h m hm; exact h m (List.mem_append_right _ hm)
  · intro h m hm
    rcases List.mem_append.1 hm with hm | hm
    · exact hp m hm
    · exact h m hm

theorem baqiItar_naw (u : Jisr.Utur.Itar3) : ∀ m ∈ baqiItar u, m.naw ≠ .madkhal := by
  intro m hm
  unfold baqiItar at hm
  split at hm
  · simp only [List.mem_cons, List.mem_map] at hm
    rcases hm with rfl | ⟨x, _, rfl⟩ <;> simp [maniOf]
  · simp only [List.mem_singleton] at hm; subst hm; simp

/-- مقدّماتُ عقدةٍ: أبناءٌ مرخَّصون ثمّ ما ليس مدخلًا — فالمدخلُ مشهودٌ والحكمُ بعده. -/
theorem uqda_madkhal {α β : Type} (n : Naqla α β) (cs : List (String × Natija)) (r : List Muqaddima)
    (hm : n.muqaddimat = rafaKull cs ++ r) (hb : n.marbut = true) (hk : cs ≠ [])
    (hall : ∀ c ∈ cs, c.2 = .murakhkhas) (hr : ∀ m ∈ r, m.naw ≠ .madkhal) :
    hukm n = hukmMarbut none [] (awwalNaqid n .mani) (awwalNaqid n .shart) (naqisa n) := by
  have hrk := rafaKull_mashhud hall
  refine hukm_madkhal_salim n hb ?_ ?_
  · obtain ⟨m, hm', hn⟩ := rafaKull_madkhal hk
    exact ⟨m, by rw [hm]; exact List.mem_append_left _ hm', hn⟩
  · rw [hm, kull_baqi _ _ (fun m => m.naw = .madkhal → m.halFiil = .mashhud) (fun m hm' _ => (hrk m hm').2)]
    intro m hm' hn; exact absurd hn (hr m hm')

/-- أحوالُ الفاحص على مقدّماتٍ أوّلُها أبناءٌ مرخَّصون: الشرطُ والمانعُ وما لم يُفحص فيما بعدهم. -/
theorem ahwal_baqi {α β : Type} (n : Naqla α β) (cs : List (String × Natija)) (r : List Muqaddima)
    (hm : n.muqaddimat = rafaKull cs ++ r) (hall : ∀ c ∈ cs, c.2 = .murakhkhas) :
    (awwalNaqid n .mani = none ↔ ∀ m ∈ r, m.naw = .mani → m.halFiil ≠ .mashhud) ∧
    (awwalNaqid n .shart = none ↔ ∀ m ∈ r, m.naw = .shart → m.halFiil ≠ .manfi) ∧
    (naqisa n = [] ↔ ∀ m ∈ r, m.halFiil ≠ .ghayrMafhus) := by
  have hrk := rafaKull_mashhud hall
  refine ⟨?_, ?_, ?_⟩
  · rw [awwalNaqid_mani_none, hm, kull_baqi _ _ _ (fun m hm' hn => by rw [(hrk m hm').1] at hn; cases hn)]
  · rw [awwalNaqid_shart_none, hm, kull_baqi _ _ _ (fun m hm' hn => by rw [(hrk m hm').1] at hn; cases hn)]
  · rw [naqisa_nil, hm, kull_baqi _ _ _ (fun m hm' => by rw [(hrk m hm').2]; simp)]

theorem baad_murakhkhas (M S : Option String) (Q : List String) :
    hukmMarbut none [] M S Q = .murakhkhas ↔ M = none ∧ S = none ∧ Q = [] := by
  rw [hukmMarbut_murakhkhas]; simp

theorem baad_mumtani (M S : Option String) (Q : List String) :
    (∃ x, hukmMarbut none [] M S Q = .mumtani x) ↔ M ≠ none := by
  cases M <;> simp [hukmMarbut_mumtani]

theorem halUtur_mashhud (h : Hukm) : halUtur h = .mashhud ↔ h = .mumtani := by cases h <;> simp [halUtur]
theorem halUtur_ghayr (h : Hukm) : halUtur h = .ghayrMafhus ↔ h = .laHukm := by cases h <;> simp [halUtur]

theorem la_mumtani_la_laHukm (hs : List Hukm) :
    Hukm.mumtani ∉ hs ∧ Hukm.laHukm ∉ hs ↔ ∀ h ∈ hs, h = .murakhkhas := by
  constructor
  · rintro ⟨h1, h2⟩ h hh
    cases h
    · rfl
    · exact absurd hh h2
    · exact absurd hh h1
  · intro h
    exact ⟨fun hm => (by have := h _ hm; cases this), fun hm => (by have := h _ hm; cases this)⟩

/-- أحوالُ الموانع الستّة: مانعٌ مشهودٌ إذا وفقط إذا امتنع مكوّن، وما لم يُفحص إذا وفقط إذا كان مكوّنٌ «لا حكم». -/
theorem ajza_ahwal (sh : Muqaddima) (cs : List (String × Hukm)) (hn : sh.naw = .shart) (hh : sh.halFiil = .mashhud) :
    ((∀ m ∈ sh :: cs.map maniOf, m.naw = .mani → m.halFiil ≠ .mashhud) ↔ Hukm.mumtani ∉ cs.map (·.2)) ∧
    (∀ m ∈ sh :: cs.map maniOf, m.naw = .shart → m.halFiil ≠ .manfi) ∧
    ((∀ m ∈ sh :: cs.map maniOf, m.halFiil ≠ .ghayrMafhus) ↔ Hukm.laHukm ∉ cs.map (·.2)) := by
  refine ⟨⟨fun h hm => ?_, fun h m hm hk => ?_⟩, fun m hm hk => ?_, ⟨fun h hm => ?_, fun h m hm => ?_⟩⟩
  · obtain ⟨x, hx, e⟩ := List.mem_map.1 hm
    exact h (maniOf x) (List.mem_cons_of_mem _ (List.mem_map_of_mem hx)) rfl (by rw [maniOf_hal, e]; rfl)
  · rcases List.mem_cons.1 hm with rfl | hm
    · rw [hn] at hk; cases hk
    · obtain ⟨x, hx, rfl⟩ := List.mem_map.1 hm
      rw [maniOf_hal]
      intro e
      exact h (List.mem_map.2 ⟨x, hx, (halUtur_mashhud _).1 e⟩)
  · rcases List.mem_cons.1 hm with rfl | hm
    · rw [hh]; simp
    · obtain ⟨x, hx, rfl⟩ := List.mem_map.1 hm
      cases hk
  · obtain ⟨x, hx, e⟩ := List.mem_map.1 hm
    exact h (maniOf x) (List.mem_cons_of_mem _ (List.mem_map_of_mem hx)) (by rw [maniOf_hal, e]; rfl)
  · rcases List.mem_cons.1 hm with rfl | hm
    · rw [hh]; simp
    · obtain ⟨x, hx, rfl⟩ := List.mem_map.1 hm
      rw [maniOf_hal]
      intro e
      exact h (List.mem_map.2 ⟨x, hx, (halUtur_ghayr _).1 e⟩)

/-- أحوالُ عقدة الإطار بكلماتٍ مرخَّصة: داخلَ الحدّ موانعُ الستّة وحدها، وخارجَه شرطُ الحدّ منفيٌّ ولا مانع. -/
theorem itar_ahwal (src sp md ad) (kalimat : List (String × Natija)) (u : Jisr.Utur.Itar3)
    (hb : (uqdaItar src sp md ad kalimat u).marbut = true)
    (hk : kalimat ≠ []) (hall : ∀ c ∈ kalimat, c.2 = .murakhkhas) :
    ∃ M S Q, hukm (uqdaItar src sp md ad kalimat u) = hukmMarbut none [] M S Q ∧
      (fiHadd u = true → (M = none ↔ Hukm.mumtani ∉ (ajzaSitta u).map (·.2)) ∧ S = none ∧
        (Q = [] ↔ Hukm.laHukm ∉ (ajzaSitta u).map (·.2))) ∧
      (fiHadd u = false → M = none ∧ S ≠ none) := by
  refine ⟨_, _, _, uqda_madkhal _ kalimat _ rfl hb hk hall (baqiItar_naw u), ?_, ?_⟩
  · intro hf
    obtain ⟨hmn, hsh, hq⟩ := ahwal_baqi (uqdaItar src sp md ad kalimat u) kalimat (baqiItar u) rfl hall
    have hb' : baqiItar u = ⟨ismHadd, .shart, .mashhud, sanadHadd⟩ :: (ajzaSitta u).map maniOf := by
      simp [baqiItar, hf]
    rw [hb'] at hmn hsh hq
    obtain ⟨a1, a2, a3⟩ := ajza_ahwal ⟨ismHadd, .shart, .mashhud, sanadHadd⟩ (ajzaSitta u) rfl
      (by simp [Muqaddima.halFiil, sanadHadd])
    exact ⟨hmn.trans a1, hsh.2 a2, hq.trans a3⟩
  · intro hf
    obtain ⟨hmn, hsh, _⟩ := ahwal_baqi (uqdaItar src sp md ad kalimat u) kalimat (baqiItar u) rfl hall
    have hb' : baqiItar u = [⟨ismHadd ++ ": " ++ ", ".intercalate ((Jisr.Utur.asbabKharij u).map sababIsm),
        .shart, .manfi, sanadHadd⟩] := by simp [baqiItar, hf]
    rw [hb'] at hmn hsh
    refine ⟨hmn.2 (fun m hm hn => by rw [List.mem_singleton] at hm; subst hm; cases hn), fun hS => ?_⟩
    exact hsh.1 hS _ (List.mem_singleton_self _) rfl (by simp [Muqaddima.halFiil, sanadHadd])

/-- **الإطارُ المرخَّص بكلماتٍ مرخَّصة هو ما يرخّصه `hukmSitta`.** -/
theorem itar_murakhkhas (src sp md ad) (kalimat : List (String × Natija)) (u : Jisr.Utur.Itar3)
    (hb : (uqdaItar src sp md ad kalimat u).marbut = true)
    (hk : kalimat ≠ []) (hall : ∀ c ∈ kalimat, c.2 = .murakhkhas) :
    hukm (uqdaItar src sp md ad kalimat u) = .murakhkhas ↔ hukmSitta u = .murakhkhas := by
  obtain ⟨M, S, Q, he, hin, hout⟩ := itar_ahwal src sp md ad kalimat u hb hk hall
  rw [he, baad_murakhkhas, hukmSitta_ajza]
  cases hf : fiHadd u
  · simp only [Bool.false_eq_true, ite_false, reduceCtorEq, iff_false, not_and]
    exact fun _ hS => absurd hS (hout hf).2
  · obtain ⟨h1, h2, h3⟩ := hin hf
    simp only [ite_true, h2, true_and, h1, h3, dammKull_murakhkhas]
    exact la_mumtani_la_laHukm _

/-- **والممتنعُ ما يمنعه `hukmSitta`:** امتناعُ الإطار بكلماتٍ مرخَّصة مانعٌ مشهودٌ من مكوّناته. -/
theorem itar_mumtani (src sp md ad) (kalimat : List (String × Natija)) (u : Jisr.Utur.Itar3)
    (hb : (uqdaItar src sp md ad kalimat u).marbut = true)
    (hk : kalimat ≠ []) (hall : ∀ c ∈ kalimat, c.2 = .murakhkhas) :
    (∃ x, hukm (uqdaItar src sp md ad kalimat u) = .mumtani x) ↔ hukmSitta u = .mumtani := by
  obtain ⟨M, S, Q, he, hin, hout⟩ := itar_ahwal src sp md ad kalimat u hb hk hall
  rw [he, baad_mumtani, hukmSitta_ajza]
  cases hf : fiHadd u
  · simp [(hout hf).1]
  · obtain ⟨h1, _, _⟩ := hin hf
    simp only [ite_true, dammKull_mumtani, ne_eq, h1, Classical.not_not]

/-- **«لا حكم» في `hukmSitta` عدمُ انطباقٍ أو تعليقٌ في الشهادة** (بربط العقدة وكلماتٍ مرخَّصةٍ غيرِ فارغة). وأيُّهما فمن `itar_ahwal`: خارجَ الحدّ
    شرطٌ منفيٌّ باسم أسبابه، وداخلَه موانعُ «لا حكم» بأسمائها، وحالُها «لم يُفحص» بتعريف `halUtur` (`halUtur_ghayr`). -/
theorem itar_laHukm (src sp md ad) (kalimat : List (String × Natija)) (u : Jisr.Utur.Itar3)
    (hb : (uqdaItar src sp md ad kalimat u).marbut = true)
    (hk : kalimat ≠ []) (hall : ∀ c ∈ kalimat, c.2 = .murakhkhas) :
    hukmSitta u = .laHukm ↔
      (∃ x, hukm (uqdaItar src sp md ad kalimat u) = .laTantabiq x) ∨
      ∃ l, hukm (uqdaItar src sp md ad kalimat u) = .muallaq l := by
  obtain ⟨M, S, Q, he, -, -⟩ := itar_ahwal src sp md ad kalimat u hb hk hall
  exact laHukm_min_ithnayn _ _ ⟨M, S, Q, he⟩ (itar_murakhkhas src sp md ad kalimat u hb hk hall)
    (itar_mumtani src sp md ad kalimat u hb hk hall)

/-! ## ٥. عقدةُ الجملة: إطاراتُها بشهاداتها -/

def sanadNass : String := "Jisr.NassItar.hukmNass"
def ismLaItar : String := "إطارٌ في المجال (Jisr.NassItar.itarat)"
def ismKulluhaMumtani : String := "الإطاراتُ كلُّها ممتنعة"

def mumtaniB : Natija → Bool
  | .mumtani _ => true
  | _ => false

theorem mumtaniB_iff (v : Natija) : mumtaniB v = true ↔ ∃ x, v = .mumtani x := by
  cases v <;> simp [mumtaniB]

/-- **رفعُ الإطار في الجملة:** حكمُ الفاحص على شهادة الإطار — المعلَّقُ شروطٌ لم تُفحص بأسماء نقصه مسبوقةً باسم الإطار، وغيرُ المنطبق والفاسدُ
    شرطٌ منفيٌّ باسم سببه؛ والمرخَّصُ والممتنعُ لا يُرفعان هنا: لهما في `baqiJumla` فرعاهما. -/
def rafaItar (ism : String) : Natija → List Muqaddima
  | .murakhkhas => []
  | .mumtani _ => []
  | .muallaq l => (if l.isEmpty then [ism] else l.map (fun x => ism ++ " ← " ++ x)).map
      fun x => ⟨x, .shart, .ghayrMafhus, sanadNass⟩
  | .laTantabiq x => [⟨ism ++ " ← " ++ x, .shart, .manfi, sanadNass⟩]
  | .madkhalFasid x => [⟨ism ++ " ← " ++ x, .shart, .manfi, sanadNass⟩]
  | .ghayrMarbut => [⟨ism ++ " ← غير مربوط", .shart, .manfi, sanadNass⟩]

theorem rafaItar_hal (s : String) (v : Natija) :
    ∀ m ∈ rafaItar s v, m.naw = .shart ∧ (m.halFiil = .manfi ∨ m.halFiil = .ghayrMafhus) := by
  intro m hm
  cases v with
  | muallaq l =>
    simp only [rafaItar, List.mem_map] at hm
    obtain ⟨x, _, rfl⟩ := hm
    simp [Muqaddima.halFiil, sanadNass]
  | murakhkhas => simp [rafaItar] at hm
  | mumtani _ => simp [rafaItar] at hm
  | _ => simp only [rafaItar, List.mem_singleton] at hm; subst hm; simp [Muqaddima.halFiil, sanadNass]

theorem rafaItar_ne (s : String) (v : Natija) (h1 : v ≠ .murakhkhas) (h2 : mumtaniB v = false) : rafaItar s v ≠ [] := by
  cases v <;> simp_all [rafaItar, mumtaniB]
  split <;> simp_all

/-- مقدّماتُ الجملة بعد كلماتها: إطارٌ مرخَّصٌ شرطًا مشهودًا؛ وإلّا: لا إطار شرطٌ منفيّ، وكلُّها ممتنعٌ مانعٌ مشهود، وما سوى ذلك الإطاراتُ غيرُ
    الممتنعة مرفوعةً بشهاداتها (`rafaItar`). -/
def baqiJumla (fs : List (String × Natija)) : List Muqaddima :=
  match fs.find? (fun f => f.2 == .murakhkhas) with
  | some f => [⟨"إطارٌ مقبول: " ++ f.1, .shart, .mashhud, sanadNass⟩]
  | none =>
    if fs = [] then [⟨ismLaItar, .shart, .manfi, sanadNass⟩]
    else if fs.all (fun f => mumtaniB f.2) then [⟨ismKulluhaMumtani, .mani, .mashhud, sanadNass⟩]
    else fs.flatMap fun f => rafaItar ("إطار " ++ f.1) f.2

/-- **عقدةُ الجملة:** كلماتُها مرفوعةٌ ثمّ إطاراتُها بأحكام الفاحص على شهاداتها؛ والمخرجُ أدوارُ الإطار المرخَّص، والبدائلُ الباقيةُ أدوارُ
    الإطارات الأخرى غيرِ الممتنعة. -/
def uqdaJumla (src : Nabt.UnitDiscovery.Source Char) (sp : Nabt.UnitDiscovery.Span) (madkhal : String)
    (kalimat : List (String × Natija)) (fs : List (String × Natija)) : Naqla String String :=
  let makhraj := match fs.find? (fun f => f.2 == .murakhkhas) with | some f => f.1 | none => ""
  ⟨src, sp, madkhal, makhraj, ⟨"Jisr.NassItar.hukmNass", 1⟩, rafaKull kalimat ++ baqiJumla fs,
    ((fs.filter fun f => !mumtaniB f.2).map (·.1)).filter (· != makhraj),
    "حكمُ الجملة جمعُ أحكام إطاراتها (Jisr.NassItar.jamaa)"⟩

theorem baqiJumla_naw (fs : List (String × Natija)) : ∀ m ∈ baqiJumla fs, m.naw ≠ .madkhal := by
  intro m hm
  unfold baqiJumla at hm
  split at hm
  · simp only [List.mem_singleton] at hm; subst hm; simp
  · split at hm
    · simp only [List.mem_singleton] at hm; subst hm; simp
    · split at hm
      · simp only [List.mem_singleton] at hm; subst hm; simp
      · obtain ⟨f, _, hmf⟩ := List.mem_flatMap.1 hm
        rw [(rafaItar_hal _ _ m hmf).1]; simp

theorem jamaa_murakhkhas (hs : List Hukm) : Jisr.NassItar.jamaa hs = .murakhkhas ↔ Hukm.murakhkhas ∈ hs := by
  unfold Jisr.NassItar.jamaa
  by_cases h : Hukm.murakhkhas ∈ hs
  · simp [h]
  · simp only [List.contains_iff_mem, h, ite_false, iff_false]
    split <;> simp

theorem jamaa_mumtani (hs : List Hukm) :
    Jisr.NassItar.jamaa hs = .mumtani ↔ Hukm.murakhkhas ∉ hs ∧ hs ≠ [] ∧ ∀ h ∈ hs, h = .mumtani := by
  unfold Jisr.NassItar.jamaa
  by_cases h : Hukm.murakhkhas ∈ hs
  · simp [h]
  · simp only [List.contains_iff_mem, h, ite_false, not_false_eq_true, true_and]
    split
    · rename_i h'
      simp only [List.all_eq_true, beq_iff_eq] at h'
      simp only [true_iff]
      exact ⟨h'.1, fun x hx => h'.2 x hx⟩
    · rename_i h'
      simp only [List.all_eq_true, beq_iff_eq, not_and] at h'
      simp only [reduceCtorEq, false_iff, not_and]
      exact h'

/-- **حكمُ الجملة على أحكام الفاحص على إطاراتها:** بكلماتٍ مرخَّصة، تُرخَّص الجملة إذا وفقط إذا رُخِّص إطار، وتمتنع إذا وفقط إذا امتنعت
    إطاراتُها كلُّها ولم تخلُ. -/
theorem jumla_natija (src sp md) (kalimat : List (String × Natija)) (fs : List (String × Natija))
    (hb : (uqdaJumla src sp md kalimat fs).marbut = true) (hk : kalimat ≠ []) (hall : ∀ c ∈ kalimat, c.2 = .murakhkhas) :
    (hukm (uqdaJumla src sp md kalimat fs) = .murakhkhas ↔ Natija.murakhkhas ∈ fs.map (·.2)) ∧
    ((∃ x, hukm (uqdaJumla src sp md kalimat fs) = .mumtani x) ↔
      fs.map (·.2) ≠ [] ∧ ∀ v ∈ fs.map (·.2), mumtaniB v = true) := by
  have he := uqda_madkhal (uqdaJumla src sp md kalimat fs) kalimat _ rfl hb hk hall (baqiJumla_naw fs)
  obtain ⟨hmn, hsh, hq⟩ := ahwal_baqi (uqdaJumla src sp md kalimat fs) kalimat (baqiJumla fs) rfl hall
  rw [he, baad_murakhkhas, baad_mumtani]
  have hallM : (∀ v ∈ fs.map (·.2), mumtaniB v = true) ↔ fs.all (fun f => mumtaniB f.2) = true := by
    rw [List.all_eq_true]
    constructor
    · intro h f hf; exact h _ (List.mem_map.2 ⟨f, hf, rfl⟩)
    · intro h v hv; obtain ⟨f, hf, rfl⟩ := List.mem_map.1 hv; exact h f hf
  cases hf : fs.find? (fun f => f.2 == .murakhkhas) with
  | some f =>
    have hbj : baqiJumla fs = [⟨"إطارٌ مقبول: " ++ f.1, .shart, .mashhud, sanadNass⟩] := by simp [baqiJumla, hf]
    rw [hbj] at hmn hsh hq
    have hfs := List.mem_of_find?_eq_some hf
    have hf2 : f.2 = .murakhkhas := by simpa using List.find?_some hf
    have hfm : Natija.murakhkhas ∈ fs.map (·.2) := List.mem_map.2 ⟨f, hfs, hf2⟩
    have hM := hmn.2 (fun m hm hn => by rw [List.mem_singleton] at hm; subst hm; cases hn)
    have hS := hsh.2 (fun m hm _ => by rw [List.mem_singleton] at hm; subst hm; simp [Muqaddima.halFiil, sanadNass])
    have hQ := hq.2 (fun m hm => by rw [List.mem_singleton] at hm; subst hm; simp [Muqaddima.halFiil, sanadNass])
    simp [hM, hS, hQ, hfm]
    intro _
    exact ⟨_, ⟨f.1, hfs⟩, by rw [hf2]; rfl⟩
  | none =>
    have hnm : Natija.murakhkhas ∉ fs.map (·.2) := by
      simp only [List.mem_map, not_exists, not_and]
      intro f hfm e
      have := List.find?_eq_none.1 hf f hfm
      simp [e] at this
    by_cases he0 : fs = []
    · subst he0
      have hbj : baqiJumla [] = [⟨ismLaItar, .shart, .manfi, sanadNass⟩] := by simp [baqiJumla]
      rw [hbj] at hmn hsh
      have hM := hmn.2 (fun m hm hn => by rw [List.mem_singleton] at hm; subst hm; cases hn)
      have hS : awwalNaqid (uqdaJumla src sp md kalimat []) .shart ≠ none :=
        fun h => hsh.1 h _ (List.mem_singleton_self _) rfl (by simp [Muqaddima.halFiil, sanadNass])
      simp [hM, hS]
    · have hne : fs.map (·.2) ≠ [] := by simpa using he0
      by_cases ha : fs.all (fun f => mumtaniB f.2) = true
      · have hbj : baqiJumla fs = [⟨ismKulluhaMumtani, .mani, .mashhud, sanadNass⟩] := by
          simp [baqiJumla, hf, he0, ha]
        rw [hbj] at hmn
        have hM : awwalNaqid (uqdaJumla src sp md kalimat fs) .mani ≠ none :=
          fun h => hmn.1 h _ (List.mem_singleton_self _) rfl (by simp [Muqaddima.halFiil, sanadNass])
        rw [hallM]
        simp [hM, hnm, hne, ha]
      · have hbj : baqiJumla fs = fs.flatMap fun f => rafaItar ("إطار " ++ f.1) f.2 := by
          simp [baqiJumla, hf, he0, ha]
        rw [hbj] at hmn hsh hq
        obtain ⟨f, hfm, hfn⟩ : ∃ f ∈ fs, mumtaniB f.2 = false := Classical.byContradiction fun hno =>
          ha (List.all_eq_true.2 fun f hf' => by
            cases h' : mumtaniB f.2
            · exact absurd ⟨f, hf', h'⟩ hno
            · rfl)
        have hfr : f.2 ≠ .murakhkhas := fun e => by
          have := List.find?_eq_none.1 hf f hfm; simp [e] at this
        obtain ⟨m, hm⟩ := List.exists_mem_of_ne_nil _ (rafaItar_ne ("إطار " ++ f.1) f.2 hfr hfn)
        have hmm : m ∈ fs.flatMap fun f => rafaItar ("إطار " ++ f.1) f.2 := List.mem_flatMap.2 ⟨f, hfm, hm⟩
        obtain ⟨hn, hh⟩ := rafaItar_hal _ _ m hm
        have hM := hmn.2 (fun m' hm' hn' => by
          obtain ⟨g, _, hg⟩ := List.mem_flatMap.1 hm'
          rw [(rafaItar_hal _ _ m' hg).1] at hn'; cases hn')
        have hSQ : ¬ (awwalNaqid (uqdaJumla src sp md kalimat fs) .shart = none ∧
            naqisa (uqdaJumla src sp md kalimat fs) = []) := by
          rintro ⟨hS, hQ⟩
          rcases hh with hh | hh
          · exact hsh.1 hS m hmm hn (by rw [hh])
          · exact hq.1 hQ m hmm (by rw [hh])
        rw [hallM]
        simp only [hM, true_and, ne_eq, not_true_eq_false, false_iff, hnm, iff_false]
        exact ⟨hSQ, fun h => ha h.2⟩

/-- **تقابلُ أحكام الإطارات:** أحكامُ الفاحص على شهادات الإطارات (`F`) تقابل أحكامها الثلاثيّة (`G`) في الترخيص والامتناع، فـ`jamaa` على `G`
    مرخَّصٌ إذا وفقط إذا رُخِّص إطارٌ بـ`F`، وممتنعٌ إذا وفقط إذا امتنعت كلُّها بـ`F` ولم تخلُ. -/
theorem jamaa_tanazur {α : Type} (l : List α) (F : α → Natija) (G : α → Hukm)
    (h1 : ∀ a ∈ l, F a = .murakhkhas ↔ G a = .murakhkhas) (h2 : ∀ a ∈ l, mumtaniB (F a) = true ↔ G a = .mumtani) :
    (Jisr.NassItar.jamaa (l.map G) = .murakhkhas ↔ Natija.murakhkhas ∈ l.map F) ∧
    (Jisr.NassItar.jamaa (l.map G) = .mumtani ↔ l.map F ≠ [] ∧ ∀ v ∈ l.map F, mumtaniB v = true) := by
  rw [jamaa_murakhkhas, jamaa_mumtani]
  simp only [List.mem_map, ne_eq, List.map_eq_nil_iff, forall_exists_index, and_imp, forall_apply_eq_imp_iff₂]
  constructor
  · constructor
    · rintro ⟨a, ha, e⟩; exact ⟨a, ha, (h1 a ha).2 e⟩
    · rintro ⟨a, ha, e⟩; exact ⟨a, ha, (h1 a ha).1 e⟩
  · constructor
    · rintro ⟨_, hn, hall⟩; exact ⟨hn, fun a ha => (h2 a ha).2 (hall a ha)⟩
    · rintro ⟨hn, hall⟩
      refine ⟨fun ⟨a, ha, e⟩ => ?_, hn, fun a ha => (h2 a ha).1 (hall a ha)⟩
      have := (h2 a ha).1 (hall a ha); rw [e] at this; cases this

/-- **حكمُ الجملة بالشهادة هو `jamaa`:** بكلماتٍ مرخَّصة، وإطاراتٍ أحكامُ الفاحص على شهاداتها (`F`) تقابل أحكامها الثلاثيّة (`G`): ترخيصُ
    الجملة ترخيصُ `jamaa`، وامتناعُها امتناعُه، و«لا حكم» فيه عدمُ انطباقٍ أو تعليقٌ في الجملة. -/
theorem jumla_jamaa (src sp md) (kalimat : List (String × Natija)) (fs : List (String × Natija))
    {α : Type} (l : List α) (F : α → Natija) (G : α → Hukm) (hfs : fs.map (·.2) = l.map F)
    (h1 : ∀ a ∈ l, F a = .murakhkhas ↔ G a = .murakhkhas) (h2 : ∀ a ∈ l, mumtaniB (F a) = true ↔ G a = .mumtani)
    (hb : (uqdaJumla src sp md kalimat fs).marbut = true) (hk : kalimat ≠ []) (hall : ∀ c ∈ kalimat, c.2 = .murakhkhas) :
    (hukm (uqdaJumla src sp md kalimat fs) = .murakhkhas ↔ Jisr.NassItar.jamaa (l.map G) = .murakhkhas) ∧
    ((∃ x, hukm (uqdaJumla src sp md kalimat fs) = .mumtani x) ↔ Jisr.NassItar.jamaa (l.map G) = .mumtani) ∧
    (Jisr.NassItar.jamaa (l.map G) = .laHukm ↔
      (∃ x, hukm (uqdaJumla src sp md kalimat fs) = .laTantabiq x) ∨
      ∃ l, hukm (uqdaJumla src sp md kalimat fs) = .muallaq l) := by
  have hn := jumla_natija src sp md kalimat fs hb hk hall
  have ht := jamaa_tanazur l F G h1 h2
  rw [hfs] at hn
  have he := uqda_madkhal (uqdaJumla src sp md kalimat fs) kalimat _ rfl hb hk hall (baqiJumla_naw fs)
  have k1 := hn.1.trans ht.1.symm
  have k2 := hn.2.trans ht.2.symm
  exact ⟨k1, k2, laHukm_min_ithnayn _ _ ⟨_, _, _, he⟩ k1 k2⟩

/-- الرفعُ على مطلوبه كلُّه إذا وفقط إذا رُخِّص كلُّ ابن. -/
theorem rafaKull_matlub (cs : List (String × Natija)) :
    (∀ m ∈ rafaKull cs, m.halFiil = matlub m.naw) ↔ ∀ c ∈ cs, c.2 = .murakhkhas := by
  constructor
  · intro h c hc
    exact (rafa_matlub c.1 c.2).1 fun m hm => h m (mem_rafaKull hc m hm)
  · intro h m hm
    obtain ⟨c, hc, hmc⟩ := List.mem_flatMap.1 hm
    exact (rafa_matlub c.1 c.2).2 (h c hc) m hmc

theorem rafaKull_nil_madkhal {cs : List (String × Natija)} (h : ∃ m ∈ rafaKull cs, m.naw = .madkhal) : cs ≠ [] := by
  rintro rfl; obtain ⟨m, hm, _⟩ := h; simp [rafaKull] at hm

/-! ## ٦. عقدةُ الكلمة: مقاطعُ التحصيل وقراءةُ القارئ -/

open Nabt.UnitDiscovery (Source Span)

/-- مصدرُ مقاطع الكلمة: حروفُها، ونطاقُها رقمُ الكلمة في الجملة بعد الواحد (والجملةُ نطاقُ الصفر). -/
def masdarKalima (w : List Char) (i : Nat) : Source Char := ⟨0, 0, i + 1, 0, w⟩

def ismMaqta (m : Dal.Tahsil.Maqta) : String := "مقطع " ++ toString (m.i + 1) ++ " «" ++ String.ofList m.nass ++ "»"

/-- أبناءُ الكلمة: شهاداتُ مقاطع تحصيلها بأحكام الفاحص عليها. -/
def abnaKalima (w : List Char) (i : Nat) : List (String × Natija) :=
  (Dal.Tahsil.tahsil w).map fun m => (ismMaqta m, hukm (Dal.Tahsil.shahada (masdarKalima w i) m))

def ismQari : String := "قراءة القارئ على التحصيل (Dal.QiraaTahsil.qiraa)"
def sanadQari : String := "Dal.QiraaTahsil.qiraa"

def shartQari : Except String Dal.QiraaTahsil.Qiraa → Muqaddima
  | .ok _ => ⟨ismQari, .shart, .mashhud, sanadQari⟩
  | .error e => ⟨ismQari ++ ": " ++ e, .shart, .manfi, sanadQari⟩

def khalayaQari : Except String Dal.QiraaTahsil.Qiraa → List Nat
  | .ok q => q.khalaya.map (·.raqm)
  | .error _ => []

def qariOk : Except String Dal.QiraaTahsil.Qiraa → Bool
  | .ok _ => true
  | .error _ => false

def haddKalima : String :=
  "خلايا الكلمة من مقاطع تحصيلها بقراءة القارئ (Dal.QiraaTahsil.qiraa، في غير آخر الجملة كوضع الإطار)؛ لا معجمَ ولا إعراب"

/-- **عقدةُ الكلمة:** مصدرُها الجملةُ وموضعُها فيها، ومدخلُها حروفُها ومخرجُها خلايا القارئ، وقاعدتُها القارئ، ومقدّماتُها مقاطعُ التحصيل
    مرفوعةً ثمّ قراءةُ القارئ شرطًا. -/
def uqdaKalima (src : Source Char) (sp : Span) (w : List Char) (i : Nat) : Naqla (List Char) (List Nat) :=
  let q := Dal.QiraaTahsil.qiraa w false
  ⟨src, sp, w, khalayaQari q, ⟨sanadQari, 1⟩, rafaKull (abnaKalima w i) ++ [shartQari q], [], haddKalima⟩

theorem shartQari_matlub (q : Except String Dal.QiraaTahsil.Qiraa) :
    (shartQari q).halFiil = matlub (shartQari q).naw ↔ qariOk q = true := by
  cases q <;> simp [shartQari, qariOk, Muqaddima.halFiil, matlub, sanadQari]

theorem abnaKalima_murakhkhas (w : List Char) (i : Nat) :
    (∀ c ∈ abnaKalima w i, c.2 = .murakhkhas) ↔ ∀ m ∈ Dal.Tahsil.tahsil w, ∃ s ks, m.hukm = .L s ks := by
  simp only [abnaKalima, List.forall_mem_map]
  refine forall_congr' fun m => imp_congr_right fun hm => ?_
  rw [Dal.Tahsil.shahada_hukm (masdarKalima w i) m hm]
  cases m.hukm <;> simp [Dal.Tahsil.natijaOf]

/-- **الكلمةُ المرخَّصة:** مربوطةٌ، ولها مقطع، وكلُّ مقطعٍ من تحصيلها مرخَّصٌ بقاعدةٍ من الطبقة ١، وقرأها القارئ — وإلّا فلا ترخيص، والناقصُ
    يظهر في مقدّماتها باسم مقطعه وقاعدته (`naqs_zahir`). -/
theorem kalima_murakhkhas (src : Source Char) (sp : Span) (w : List Char) (i : Nat) :
    hukm (uqdaKalima src sp w i) = .murakhkhas ↔
      (uqdaKalima src sp w i).marbut = true ∧ Dal.Tahsil.tahsil w ≠ [] ∧
      (∀ m ∈ Dal.Tahsil.tahsil w, ∃ s ks, m.hukm = .L s ks) ∧ qariOk (Dal.QiraaTahsil.qiraa w false) = true := by
  rw [murakhkhas_iff]
  have hmq : (uqdaKalima src sp w i).muqaddimat =
      rafaKull (abnaKalima w i) ++ [shartQari (Dal.QiraaTahsil.qiraa w false)] := rfl
  have hex : (∃ m ∈ (uqdaKalima src sp w i).muqaddimat, m.naw = .madkhal) ↔ Dal.Tahsil.tahsil w ≠ [] := by
    rw [hmq]
    constructor
    · rintro ⟨m, hm, hn⟩
      rcases List.mem_append.1 hm with hm | hm
      · have := rafaKull_nil_madkhal ⟨m, hm, hn⟩
        simpa [abnaKalima] using this
      · rw [List.mem_singleton] at hm; subst hm
        cases h : Dal.QiraaTahsil.qiraa w false <;> simp [shartQari, h] at hn
    · intro h
      have : abnaKalima w i ≠ [] := by simpa [abnaKalima] using h
      obtain ⟨m, hm, hn⟩ := rafaKull_madkhal this
      exact ⟨m, List.mem_append_left _ hm, hn⟩
  have hall : (∀ m ∈ (uqdaKalima src sp w i).muqaddimat, m.halFiil = matlub m.naw) ↔
      (∀ m ∈ Dal.Tahsil.tahsil w, ∃ s ks, m.hukm = .L s ks) ∧ qariOk (Dal.QiraaTahsil.qiraa w false) = true := by
    rw [hmq, ← abnaKalima_murakhkhas w i, ← rafaKull_matlub, ← shartQari_matlub]
    simp only [List.mem_append, List.mem_singleton]
    constructor
    · intro h; exact ⟨fun m hm => h m (Or.inl hm), h _ (Or.inr rfl)⟩
    · rintro ⟨h1, h2⟩ m (hm | rfl)
      · exact h1 m hm
      · exact h2
  rw [hex, hall]

/-! ## ٧. السلسلةُ من النصّ: الكلماتُ والإطاراتُ والجملة -/

/-- كلمةٌ في الجملة: رقمُها، وموضعُ أوّلها، وحروفُها. -/
structure KalimaM where
  i : Nat
  a : Nat
  w : List Char
  deriving Repr

/-- تقطيعُ الجملة على الفراغ U+0020 بمواضع الكلمات. -/
def taqtiAux : List Char → Nat → List Char → Nat → List (Nat × List Char)
  | [], _, cur, st => if cur.isEmpty then [] else [(st, cur.reverse)]
  | c :: cs, k, cur, st =>
    if c == ' ' then (if cur.isEmpty then [] else [(st, cur.reverse)]) ++ taqtiAux cs (k + 1) [] (k + 1)
    else taqtiAux cs (k + 1) (c :: cur) st

def kalimatM (t : List Char) : List KalimaM :=
  let ps := taqtiAux t 0 [] 0
  ((List.range ps.length).zip ps).map fun x => ⟨x.1, x.2.1, x.2.2⟩

def masdarJumla (t : List Char) : Source Char := ⟨0, 0, 0, 0, t⟩
def spanKalima (k : KalimaM) : Span := ⟨0, 0, 0, 0, k.a, k.a + k.w.length⟩
def spanJumla (t : List Char) : Span := ⟨0, 0, 0, 0, 0, t.length⟩

def ismKalima (k : KalimaM) : String := "كلمة " ++ toString (k.i + 1) ++ " «" ++ String.ofList k.w ++ "»"

def uqdaK (t : List Char) (k : KalimaM) : Naqla (List Char) (List Nat) :=
  uqdaKalima (masdarJumla t) (spanKalima k) k.w k.i

/-- أبناءُ الجملة والإطار: الكلماتُ بأحكام الفاحص على شهاداتها. -/
def abnaJumla (t : List Char) : List (String × Natija) :=
  (kalimatM t).map fun k => (ismKalima k, hukm (uqdaK t k))

def kalimaDal (q : Dal.QiraaTahsil.Qiraa) : Dal.Kalima := ⟨q.khalaya.map (·.raqm), q.wasl, q.al⟩

/-- كلماتُ الجملة كما يسلّمها القارئ إلى الإطار (ما قُرئ منها). -/
def kalimatDal (t : List Char) : List Dal.Kalima :=
  (kalimatM t).filterMap fun k =>
    match Dal.QiraaTahsil.qiraa k.w false with
    | .ok q => some (kalimaDal q)
    | .error _ => none

def kullMaqrua (t : List Char) : Bool := (kalimatM t).all fun k => qariOk (Dal.QiraaTahsil.qiraa k.w false)

def dawrIsm : Jisr.NassItar.Dawr → String
  | .fil => "فعل" | .fail => "فاعل" | .maful => "مفعول_به" | .harfJarr => "حرف_جر" | .majrur => "مجرور"
  | .mudafIlayh => "مضاف_إليه"

def adwarIsm (ds : List Jisr.NassItar.Dawr) : String := " ".intercalate (ds.map dawrIsm)

/-- الإطاراتُ: ما تُخرجه القراءةُ (`Jisr.NassItar.itarat`) بأدوارها، ولا إطارَ إن لم تُقرأ الكلماتُ كلُّها. -/
def utur (t : List Char) : List (List Jisr.NassItar.Dawr × Jisr.Utur.Itar3) :=
  if kullMaqrua t then Jisr.NassItar.itarat (kalimatDal t) else []

def ismItar (j : Nat) (ds : List Jisr.NassItar.Dawr) : String := toString (j + 1) ++ " (" ++ adwarIsm ds ++ ")"

/-- عقدةُ الإطار من النصّ. -/
def uqdaU (t : List Char) (x : List Jisr.NassItar.Dawr × Jisr.Utur.Itar3) : Naqla String String :=
  uqdaItar (masdarJumla t) (spanJumla t) (String.ofList t) (adwarIsm x.1) (abnaJumla t) x.2

/-- تسميةُ عناصر قائمةٍ برقمها. -/
def birraqm {β γ : Type} (l : List β) (f : Nat → β → γ) : List γ :=
  ((List.range l.length).zip l).map fun x => f x.1 x.2

theorem birraqm_snd {β γ δ : Type} (l : List β) (N : Nat → β → γ) (F : β → δ) :
    (birraqm l fun i x => (N i x, F x)).map (·.2) = l.map F := by
  unfold birraqm
  simp only [List.map_map]
  suffices h : ∀ k, ((List.range' k l.length).zip l).map ((·.2) ∘ fun x => (N x.1 x.2, F x.2)) = l.map F by
    simpa [List.range_eq_range'] using h 0
  induction l with
  | nil => intro k; simp
  | cons a l ih => intro k; simp [List.range'_succ, ih (k + 1)]

/-- عقدُ الإطارات. -/
def uqadUtur (t : List Char) : List (Naqla String String) := (utur t).map (uqdaU t)

/-- الإطاراتُ بأسمائها وأحكامها بصفّ الأسماء الستّة (للعرض). -/
def uturHukm (t : List Char) : List (String × Hukm) := birraqm (utur t) fun i x => (ismItar i x.1, hukmSitta x.2)

/-- الإطاراتُ بأسمائها وأحكام الفاحص على شهاداتها: مقدّماتُ الجملة. -/
def uturNatija (t : List Char) : List (String × Natija) := birraqm (utur t) fun i x => (ismItar i x.1, hukm (uqdaU t x))

def ismLamTuqra : String := "الإطارات: لم تُحسب، فكلمةٌ لم يقرأها القارئ"

/-- **عقدةُ الجملة من النصّ:** إن قُرئت الكلماتُ كلُّها فعقدةُ الجملة على شهادات إطاراتها؛ وإلّا فالإطاراتُ مقدّمةٌ لم تُفحص باسمها. -/
def jumla (t : List Char) : Naqla String String :=
  let n := uqdaJumla (masdarJumla t) (spanJumla t) (String.ofList t) (abnaJumla t) (uturNatija t)
  if kullMaqrua t then n
  else { n with muqaddimat := rafaKull (abnaJumla t) ++ [⟨ismLamTuqra, .shart, .ghayrMafhus, ""⟩] }

theorem jumla_muqaddimat (t : List Char) : ∃ r, (jumla t).muqaddimat = rafaKull (abnaJumla t) ++ r ∧
    ∀ m ∈ r, m.naw ≠ .madkhal := by
  unfold jumla
  split
  · exact ⟨_, rfl, baqiJumla_naw _⟩
  · exact ⟨_, rfl, fun m hm => by rw [List.mem_singleton] at hm; subst hm; simp⟩

/-- ربطُ الإطار ربطُ الجملة: المصدرُ والموضعُ واحد، واسما القاعدتين غيرُ فارغين. -/
theorem uqdaU_marbut (t : List Char) (x : List Jisr.NassItar.Dawr × Jisr.Utur.Itar3) :
    (uqdaU t x).marbut = (jumla t).marbut := by
  unfold jumla
  have e1 : "Jisr.QawaidSitta.hukmSitta".isEmpty = false := by decide
  have e2 : "Jisr.NassItar.hukmNass".isEmpty = false := by decide
  split <;> simp [uqdaU, uqdaItar, uqdaJumla, Naqla.marbut, e1, e2]

theorem kullMaqrua_kalimatDal (t : List Char) (h : ∀ k ∈ kalimatM t, qariOk (Dal.QiraaTahsil.qiraa k.w false) = true) :
    kullMaqrua t = true := List.all_eq_true.2 h

/-- **السلسلةُ التامّة من النصّ:** ترخيصُ الجملة بشهادتها هو أن تكون لها كلمةٌ، وكلُّ مقطعٍ من تحصيل كلّ كلمةٍ مرخَّصًا، وكلُّ كلمةٍ مقروءةً،
    وحكمُ الأسماء الستّة على كلماتها كما يسلّمها القارئ (`Jisr.NassItar.hukmNass`) مقبولًا — بفرض الربط في الجملة وكلماتها. والإطاراتُ تدخل
    الجملةَ بأحكام الفاحص على شهاداتها (`uturNatija`)، ومقابلتُها لـ`hukmSitta` من `itar_murakhkhas` و`itar_mumtani`. -/
theorem silsila_murakhkhas (t : List Char) (hb : (jumla t).marbut = true)
    (hbk : ∀ k ∈ kalimatM t, (uqdaK t k).marbut = true) :
    hukm (jumla t) = .murakhkhas ↔
      kalimatM t ≠ [] ∧
      (∀ k ∈ kalimatM t, Dal.Tahsil.tahsil k.w ≠ [] ∧ (∀ m ∈ Dal.Tahsil.tahsil k.w, ∃ s ks, m.hukm = .L s ks) ∧
        qariOk (Dal.QiraaTahsil.qiraa k.w false) = true) ∧
      Jisr.NassItar.hukmNass (kalimatDal t) = .murakhkhas := by
  have hab : (∀ c ∈ abnaJumla t, c.2 = .murakhkhas) ↔ ∀ k ∈ kalimatM t, hukm (uqdaK t k) = .murakhkhas := by
    simp [abnaJumla]
  have hkk : (∀ k ∈ kalimatM t, hukm (uqdaK t k) = .murakhkhas) ↔
      ∀ k ∈ kalimatM t, Dal.Tahsil.tahsil k.w ≠ [] ∧ (∀ m ∈ Dal.Tahsil.tahsil k.w, ∃ s ks, m.hukm = .L s ks) ∧
        qariOk (Dal.QiraaTahsil.qiraa k.w false) = true := by
    refine forall_congr' fun k => imp_congr_right fun hk => ?_
    rw [uqdaK, kalima_murakhkhas]
    exact ⟨fun h => h.2, fun h => ⟨hbk k hk, h⟩⟩
  have hne : abnaJumla t ≠ [] ↔ kalimatM t ≠ [] := by simp [abnaJumla]
  -- الجملةُ على شهادات إطاراتها، بكلماتٍ مرخَّصة.
  have key : ∀ (hk0 : abnaJumla t ≠ []) (hall : ∀ c ∈ abnaJumla t, c.2 = .murakhkhas),
      (hukm (jumla t) = .murakhkhas ↔ Jisr.NassItar.hukmNass (kalimatDal t) = .murakhkhas) := by
    intro hk0 hall
    have hkm : kullMaqrua t = true := kullMaqrua_kalimatDal t fun k hk => (hkk.1 (hab.1 hall) k hk).2.2
    have hj : jumla t = uqdaJumla (masdarJumla t) (spanJumla t) (String.ofList t) (abnaJumla t) (uturNatija t) := by
      simp [jumla, hkm]
    have hnass : Jisr.NassItar.hukmNass (kalimatDal t) = Jisr.NassItar.jamaa ((utur t).map fun x => hukmSitta x.2) := by
      simp only [utur, hkm, ite_true]; rfl
    have hbj := hb
    rw [hj] at hbj
    have h1 : ∀ x ∈ utur t, hukm (uqdaU t x) = .murakhkhas ↔ hukmSitta x.2 = .murakhkhas := fun x _ =>
      itar_murakhkhas _ _ _ _ _ _ (by rw [← hbj, ← hj]; exact uqdaU_marbut t x) hk0 hall
    have h2 : ∀ x ∈ utur t, mumtaniB (hukm (uqdaU t x)) = true ↔ hukmSitta x.2 = .mumtani := fun x _ => by
      rw [mumtaniB_iff]
      exact itar_mumtani _ _ _ _ _ _ (by rw [← hbj, ← hj]; exact uqdaU_marbut t x) hk0 hall
    rw [hj, hnass]
    exact (jumla_jamaa _ _ _ _ _ (utur t) (fun x => hukm (uqdaU t x)) (fun x => hukmSitta x.2)
      (birraqm_snd _ _ _) h1 h2 hbj hk0 hall).1
  constructor
  · intro h
    obtain ⟨r, hr, hrn⟩ := jumla_muqaddimat t
    have hall := abna_murakhkhas _ _ r hr h
    have hk0 : abnaJumla t ≠ [] := by
      obtain ⟨_, ⟨m, hm, hn⟩, _⟩ := (murakhkhas_iff _).1 h
      rw [hr] at hm
      rcases List.mem_append.1 hm with hm | hm
      · exact rafaKull_nil_madkhal ⟨m, hm, hn⟩
      · exact absurd hn (hrn m hm)
    exact ⟨hne.1 hk0, hkk.1 (hab.1 hall), (key hk0 hall).1 h⟩
  · rintro ⟨h0, hw, hn⟩
    exact (key (hne.2 h0) (hab.2 (hkk.2 hw))).2 hn

end Nizam.Silsila
