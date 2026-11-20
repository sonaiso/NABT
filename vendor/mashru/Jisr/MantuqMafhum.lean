/-
  Jisr/MantuqMafhum.lean — الجسرُ من المنطوق إلى المفهوم: حسابُ الالتزام بشروطه وموانعه.

  أمرُ المالك (2026-10-18): «فالهدف الصحيح القابل للبرهان: كل كلمة وكل جملة تُصنَّف 100% المنطوق مع جسر راجح الى المفهوم».

  **السند** (ج3 = الشخصية الإسلامية ج3، `a2.docx` المختوم `360f7653…`؛ الأسطر من `scripts/tahwil_docx.py`، فقرةٌ بسطر):
  * س548 المنطوق: «ما دل عليه اللفظ قطعاً في محل النطق»؛ «فما دل عليه اللفظ مطابقة أو تضمناً هو المنطوق»؛ وحملُه:
    «الأصل في دلالتها هو المعنى الشرعي، ثم المعنى العرفي، ثم المعنى اللغوي» — مبنيٌّ في `QawaninDalala.haml`.
  * س550 المفهوم: «ما دل عليه مدلول اللفظ، يعني المعنى الذي دل عليه معنى اللفظ»؛ «فالمفهوم هو دلالة الالتزام»؛
    «فتكون دلالة اللفظ محصورة بالمنطوق والمفهوم» — مبنيٌّ في `SLGE.Madlul.no_third` و`mafhum_iff_iltizam`.
  * س552 الاقتضاء: «بأن يكون شرطاً للمعنى المدلول عليه بالمطابقة. واللازم قد يكون العقل يقتضيه، وقد يكون الشرع
    يقتضيه، إما لضرورة صدق المتكلم، وإما لصحة وقوع الملفوظ به».
  * س554 التنبيه والإيماء: «إنما تقع فيما يدل على العلية»؛ «التعليل لازماً من مدلول اللفظ وضعاً».
  * س556 الإشارة: «سيق لبيان حكم … ولكنه يفهم منه حكم آخر … مع أن هذا الحكم الآخر لم يكن مقصوداً من الكلام».
  * س558–564 الموافقة: من التركيب لا من الأولويّة (قولُ الآمدي في س558 وردُّه في س560)، و«لا توجد دلالة قياسية» (س564)؛ وشرطُها في
    س560: «بأن لا يكون شرطا للمعنى المطابقي بل تابعا له»، و«يشترط فيه أن يكون المعنى لازما للمعنى المدلول عليه وتابعا له».
  * س566 المخالفة: «مدلـول اللفظ في محل السكوت مخالفاً لمدلوله في محل النطق»؛ س568 الصفة: «وشرطه أن تكون تلك
    الصفة وصفاً مفهماً»؛ س580 العدد: «استكمل شرطين»؛ س582 «فلا يعمل بمفهوم الاسم مطلقاً»؛ س583 الوصف غير المفهم؛
    س584 «إنما»؛ س585 «الأعم الأغلب»؛ س586 «إذا ورد نص من الكتاب أو السنة يعطله»؛ س587 «محصور في الأصناف الأربعة
    ليس غير».

  **البناء:** المنطوقُ مُدخَلٌ بكلماته المحمولة (`Mahmul` من حمل الخطاب) وبمودَعٍ «معلومات سابقة» لكلّ منطوق: قيدُه،
  وكونُ الوصف مفهمًا، والسياق، والموانع، واللوازم المودَعة لكلّ نوع. والجسرُ `jisr` يُخرج المفاهيم من المنطوقات وحدها.
  هذا الملفّ **لا يستنتج لازمًا**: اللازمُ مودَعٌ (ج3 س396: «لا محل للعقل في اللغة»)؛ وإنما يبرهن **البوّابات**: متى
  يُرخَّص لازمٌ مفهومًا بنوعه، ومتى يُمنع، وأنّه لا مفهومَ بلا منطوقٍ محمول.

  المبرهن لكلّ مودَع: `mafhum_min_mantuq`، `la_mafhum_bila_haml`، `mukhalafa_min_qayd`، `mukhalafa_shurut`،
  `mani_yamna_mukhalafa`، `ism_la_mukhalafa`، `mukhalafa_wahida`، `iqtida_shart_lil_mutabaqa`، `muwafaqa_tabia` (س560)،
  `adad_mafahim` (حسابُ الالتزام: عددُ مفاهيم المنطوق صيغةٌ مغلقة). وإعادةُ مبرهنة المالك: `tariq_mafhum` (لا تذكر المودَع).
  وعلى الشاهد: من أمثلة ج3 بأسطرها `shawahid_mafhum`، `shawahid_la_mafhum`، `muwafaqa_bila_awlawiyya`؛ ومبنيّان: `shahid_la_haml`،
  `shahid_tabia`.
  **حدُّ الوسم:** مبرهناتُ «لكلّ» فكٌّ لتعريف الجسر: تثبت أنّ البوّابة تحترم الشروطَ كما رُمِّزت هنا، لا أنّ الترميزَ نفسَه
  مطابقٌ للنبهاني — المطابقةُ قراءةُ البنّاء بالأسطر المذكورة (رأيٌ معروضٌ على المالك). وتعيينُ البنّاء: الإشارةُ والتنبيهُ والموافقةُ
  يُبنى منها هنا: حملُ المنطوق، وإيداعُ اللازم بنوعه، وأنّ الموافقةَ ليست شرطًا للمطابقيّ (س560: ما أُودع اقتضاءً لا يخرج موافقةً).
  **وأُغفل معلَنًا** (داخلٌ في الإيداع لا يُفحص هنا): موافقةُ المنطوق «في الإيجاب والسلب» (س550)؛ وشروطُ التنبيه في س554 (التعليلُ
  «لازما من مدلول اللفظ وضعا، لا أن يكون اللفظ دالا بوضعه على التعليل»، ونفيُه إن «كان جامدا، أو كان وصفا ولكنه غير مناسب»)؛
  وآلةُ الشرط والغاية (س573، س578) — وشهادةُ القيد من بنية المنطوق (جدول العوامل وجرد القطر) تحت `bilBunya` في `Jisr/QaydMafhum.lean`.
  وحصرُ وسيلتَي التنبيه في الفاء والوصف المناسب تعيينُ البنّاء من مثالَي س554 («مثال ذلك»)، لا حصرٌ في
  النصّ. والشرطُ والغايةُ لا شرطَ زائدًا هنا: س573–579 لا تذكر شرطًا كالوصف المفهم، غير أنّ علّةَ شرطَي س580 وس583 عامّة («اللزوم
  الذهني»)، فإطلاقُ ذلك عليهما تعيين. والإشارةُ لا تشترط نصَّين: تعريفُ س556 «الكلام»، وشاهدُه آيةٌ واحدةٌ بعبارتين («فالآن باشروهن»
  مع «حتى يتبين لكم الخيط الأبيض من الخيط الأسود من الفجر»). الترجيحُ بين مفهومَين متعارضَين ليس هنا.
  الطفرات P163–P166 تقتلها Lean. بلا sorry ولا axiom ولا native_decide.
-/
import SLGE.Madlul
import Aql.QawaninDalala

namespace Jisr
namespace MantuqMafhum

open QawaninDalala

/-! ## ١. أنواع المفهوم بأقسامها (س550–587) -/

/-- لازمُ الاقتضاء يقتضيه العقلُ أو الشرع (س552 «قد يكون … وقد يكون»؛ الحصرُ في اثنين تعيينُ البنّاء). -/
inductive MasdarIqtida | aql | shar
  deriving DecidableEq, Repr

/-- غرضُه: «ضرورة صدق المتكلم» أو «صحة وقوع الملفوظ به» (س552). -/
inductive GharadIqtida | sidq | sihha
  deriving DecidableEq, Repr

/-- وسيلةُ التنبيه والإيماء بحسب وضع اللغة: الفاءُ، أو الوصفُ المناسب المقترنُ بالحكم — مثالا س554، والحصرُ فيهما تعيينُ البنّاء. -/
inductive WasilaTanbih | fa | wasfMunasib
  deriving DecidableEq, Repr

/-- أنواعُ المفهوم. والمخالفةُ بأصنافها الأربعة من `SLGE.Madlul.Mukhalafa` بعينها (س587). -/
inductive NawMafhum
  | iqtida (m : MasdarIqtida) (g : GharadIqtida)
  | tanbih (w : WasilaTanbih)
  | ishara
  | muwafaqa
  | mukhalafa (k : SLGE.Madlul.Mukhalafa)
  deriving DecidableEq, Repr

/-- قيدُ الحكم في المنطوق: الأربعةُ (س566)، والاسمُ وما في معناه كاللقب والكنية (س582). -/
inductive Qayd | sifa | shart | ghaya | adad | ism
  deriving DecidableEq, Repr

/-- صنفُ المخالفة من القيد؛ والاسمُ لا صنفَ له (س582، س587). -/
def sinfOf : Qayd → Option SLGE.Madlul.Mukhalafa
  | .sifa => some .sifa
  | .shart => some .shart
  | .ghaya => some .ghaya
  | .adad => some .adad
  | .ism => none

/-! ## ٢. المودَع لكلّ منطوق («معلومات سابقة»، لا استنتاج) -/

structure Mudaa (Mn L : Type) where
  /-- كلماتُ المنطوق محمولةً بحمل الخطاب (س548؛ `QawaninDalala.haml`). -/
  kalimat : Mn → List Mahmul
  /-- قيدُ الحكم إن كان. -/
  qayd : Mn → Option Qayd
  /-- الوصفُ مفهمٌ «أي مما يفيد العلية» (س568، س583). -/
  mufhim : Mn → Bool
  /-- «أن يدل سياق الكلام على نفي الحكم عن غير العدد» (س580). -/
  siyaqAdad : Mn → Bool
  /-- القيدُ بـ«إنما» (س584). -/
  innama : Mn → Bool
  /-- «خصص محل النطق بالذكر لخروجه مخرج الأعم الأغلب» (س585). -/
  aghlab : Mn → Bool
  /-- «ورد نص من الكتاب أو السنة يعطله» (س586). -/
  muattil : Mn → Bool
  /-- مدلولُ اللفظ في محلّ السكوت مخالفًا لمدلوله في محلّ النطق (س566). -/
  naqid : Mn → Option L
  /-- ما يلزم من التركيب في محلّ السكوت موافقًا (س558–562). -/
  muwafiq : Mn → List L
  /-- لازمٌ هو «شرطا للمعنى المدلول عليه بالمطابقة»، بمصدره وغرضه (س552). -/
  iqtida : Mn → List (L × MasdarIqtida × GharadIqtida)
  /-- لازمٌ تعليليٌّ من مدلول اللفظ وضعًا، بوسيلته (س554). -/
  tanbih : Mn → List (L × WasilaTanbih)
  /-- لازمٌ غيرُ مقصودٍ من الكلام (س556). -/
  ishara : Mn → List L

/-- المفهوم: نوعُه، والمنطوقُ الذي هو مدلولُه (س550)، واللازم. -/
structure Mafhum (Mn L : Type) where
  naw : NawMafhum
  asl : Mn
  lazim : L
  deriving DecidableEq, Repr

variable {Mn L : Type} [DecidableEq L]

/-- المنطوقُ محمولٌ: لا كلمةَ فيه «لا حكم» (س548: «قطعاً في محل النطق»). -/
def mahmul (D : Mudaa Mn L) (m : Mn) : Bool :=
  (D.kalimat m).all (fun k => k != .laHukm)

/-- موانعُ المخالفة الثلاثة الخارجةُ عن القيد (س584–586). -/
def mawani (D : Mudaa Mn L) (m : Mn) : Bool :=
  D.innama m || D.aghlab m || D.muattil m

/-- شرطُ الصنف: الصفةُ مفهمةٌ (س568)، والعددُ بسياقه (س580)؛ وآلةُ الشرط والغاية (س573، س578) داخلةٌ في إيداع القيد ولا تُفحص هنا. -/
def shartSinf (D : Mudaa Mn L) (m : Mn) : Qayd → Bool
  | .sifa => D.mufhim m
  | .adad => D.siyaqAdad m
  | _ => true

/-- مفهومُ المخالفة من المنطوق: صفرٌ أو واحد. -/
def mukhalafaOf (D : Mudaa Mn L) (m : Mn) : List (Mafhum Mn L) :=
  match D.qayd m, D.naqid m with
  | some q, some l =>
    match sinfOf q with
    | some k => if shartSinf D m q && !mawani D m then [⟨.mukhalafa k, m, l⟩] else []
    | none => []
  | _, _ => []

/-- الموافقُ التابع (س560): ما أُودع موافقًا ولم يُودَع شرطًا للمطابقيّ (اقتضاءً). -/
def muwafiqTabi (D : Mudaa Mn L) (m : Mn) : List L :=
  (D.muwafiq m).filter (fun l => !(D.iqtida m).any (fun x => decide (x.1 = l)))

/-- **الجسر** على منطوقٍ واحد. -/
def jisrMn (D : Mudaa Mn L) (m : Mn) : List (Mafhum Mn L) :=
  if mahmul D m then
    (D.iqtida m).map (fun x => ⟨.iqtida x.2.1 x.2.2, m, x.1⟩) ++
    (D.tanbih m).map (fun x => ⟨.tanbih x.2, m, x.1⟩) ++
    (D.ishara m).map (fun l => ⟨.ishara, m, l⟩) ++
    (muwafiqTabi D m).map (fun l => ⟨.muwafaqa, m, l⟩) ++
    mukhalafaOf D m
  else []

/-- **الجسر** على نصٍّ من منطوقات. -/
def jisr (D : Mudaa Mn L) (ms : List Mn) : List (Mafhum Mn L) :=
  ms.flatMap (jisrMn D)

/-! ## ٣. المبرهنات لكلّ مودَع -/

variable (D : Mudaa Mn L)

omit [DecidableEq L] in
theorem mem_mukhalafaOf {m : Mn} {f : Mafhum Mn L} (h : f ∈ mukhalafaOf D m) :
    ∃ q k l, D.qayd m = some q ∧ D.naqid m = some l ∧ sinfOf q = some k ∧
      shartSinf D m q = true ∧ mawani D m = false ∧ f = ⟨.mukhalafa k, m, l⟩ := by
  unfold mukhalafaOf at h
  split at h
  · rename_i q l hq hl
    split at h
    · rename_i k hk
      split at h
      · rename_i hc
        simp only [Bool.and_eq_true, Bool.not_eq_true'] at hc
        simp only [List.mem_singleton] at h
        exact ⟨q, k, l, hq, hl, hk, hc.1, hc.2, h⟩
      · simp at h
    · simp at h
  · simp at h

/-- فكُّ عضويّة الجسر على منطوقٍ واحد: محمولٌ، وأصلُه هو، ونوعُه أحدُ الخمسة من مودَعه. -/
theorem mem_jisrMn {m : Mn} {f : Mafhum Mn L} (h : f ∈ jisrMn D m) :
    mahmul D m = true ∧ f.asl = m ∧
      ((∃ s g, f.naw = .iqtida s g ∧ (f.lazim, s, g) ∈ D.iqtida m) ∨
       (∃ w, f.naw = .tanbih w) ∨ f.naw = .ishara ∨ f.naw = .muwafaqa ∨ f ∈ mukhalafaOf D m) := by
  unfold jisrMn at h
  cases hp : mahmul D m
  · simp [hp] at h
  · simp only [hp, ite_true, List.mem_append, List.mem_map] at h
    rcases h with (((⟨x, hx, rfl⟩ | ⟨x, _, rfl⟩) | ⟨x, _, rfl⟩) | ⟨x, _, rfl⟩) | hk
    · exact ⟨rfl, rfl, Or.inl ⟨_, _, rfl, hx⟩⟩
    · exact ⟨rfl, rfl, Or.inr (Or.inl ⟨_, rfl⟩)⟩
    · exact ⟨rfl, rfl, Or.inr (Or.inr (Or.inl rfl))⟩
    · exact ⟨rfl, rfl, Or.inr (Or.inr (Or.inr (Or.inl rfl)))⟩
    · obtain ⟨_, _, _, _, _, _, _, _, hf⟩ := mem_mukhalafaOf D hk
      exact ⟨rfl, by rw [hf], Or.inr (Or.inr (Or.inr (Or.inr hk)))⟩

theorem mem_jisr {ms : List Mn} {f : Mafhum Mn L} (h : f ∈ jisr D ms) :
    f.asl ∈ ms ∧ f ∈ jisrMn D f.asl := by
  obtain ⟨m, hm, hf⟩ := List.mem_flatMap.1 h
  obtain ⟨_, ha, _⟩ := mem_jisrMn D hf
  exact ⟨ha ▸ hm, ha ▸ hf⟩

/-- **لا مفهومَ بلا منطوقٍ محمول** (س550: المفهوم «ما دل عليه مدلول اللفظ»): كلُّ مفهومٍ يُخرجه الجسر أصلُه منطوقٌ
من النصّ، وكلماتُ ذلك المنطوق كلُّها محمولة. -/
theorem mafhum_min_mantuq {ms : List Mn} {f : Mafhum Mn L} (h : f ∈ jisr D ms) :
    f.asl ∈ ms ∧ mahmul D f.asl = true :=
  ⟨(mem_jisr D h).1, (mem_jisrMn D (mem_jisr D h).2).1⟩

/-- منطوقٌ فيه كلمةٌ «لا حكم» لا مفهومَ له. -/
theorem la_mafhum_bila_haml {m : Mn} (h : mahmul D m = false) : jisrMn D m = [] := by
  simp [jisrMn, h]

/-- مفهومُ المخالفة لا يأتي إلّا من `mukhalafaOf`. -/
theorem mukhalafa_min_mukhalafaOf {m : Mn} {f : Mafhum Mn L} {k : SLGE.Madlul.Mukhalafa}
    (h : f ∈ jisrMn D m) (hk : f.naw = .mukhalafa k) : f ∈ mukhalafaOf D m := by
  obtain ⟨_, _, ⟨_, _, he, _⟩ | ⟨_, he⟩ | he | he | hm⟩ := mem_jisrMn D h
  all_goals first | exact hm | (rw [hk] at he; cases he)

/-- **المخالفةُ من القيد وحده:** كلُّ مفهوم مخالفةٍ صنفُه صنفُ قيدٍ مودَع (س566، س587). -/
theorem mukhalafa_min_qayd {ms : List Mn} {f : Mafhum Mn L} {k : SLGE.Madlul.Mukhalafa}
    (h : f ∈ jisr D ms) (hk : f.naw = .mukhalafa k) :
    ∃ q, D.qayd f.asl = some q ∧ sinfOf q = some k := by
  have hm := mukhalafa_min_mukhalafaOf D (mem_jisr D h).2 hk
  obtain ⟨q, k', _, hq, _, hs, _, _, hf⟩ := mem_mukhalafaOf D hm
  rw [hf] at hk; cases hk
  exact ⟨q, hq, hs⟩

/-- **شروطُ المخالفة:** لا مانعَ (إنما، الأغلب، نصٌّ معطِّل: س584–586)، والصفةُ مفهمةٌ (س568)، والعددُ بسياقه (س580). -/
theorem mukhalafa_shurut {ms : List Mn} {f : Mafhum Mn L} {k : SLGE.Madlul.Mukhalafa}
    (h : f ∈ jisr D ms) (hk : f.naw = .mukhalafa k) :
    mawani D f.asl = false ∧ (k = .sifa → D.mufhim f.asl = true) ∧
      (k = .adad → D.siyaqAdad f.asl = true) := by
  have hm := mukhalafa_min_mukhalafaOf D (mem_jisr D h).2 hk
  obtain ⟨q, k', _, _, _, hs, hsh, hmw, hf⟩ := mem_mukhalafaOf D hm
  rw [hf] at hk; cases hk
  refine ⟨hmw, fun e => ?_, fun e => ?_⟩
  · subst e; cases q <;> simp only [sinfOf, Option.some.injEq, reduceCtorEq] at hs <;> exact hsh
  · subst e; cases q <;> simp only [sinfOf, Option.some.injEq, reduceCtorEq] at hs <;> exact hsh

/-- **المانعُ يمنع المخالفة:** إنما أو الأغلب أو نصٌّ معطِّل ⟹ لا مفهومَ مخالفةٍ من المنطوق (س584–586). -/
theorem mani_yamna_mukhalafa {m : Mn} (h : mawani D m = true) :
    ∀ f ∈ jisrMn D m, ∀ k, f.naw ≠ .mukhalafa k := by
  intro f hf k hk
  obtain ⟨_, _, _, _, _, _, _, hmw, _⟩ := mem_mukhalafaOf D (mukhalafa_min_mukhalafaOf D hf hk)
  rw [h] at hmw; cases hmw

/-- **لا مفهومَ للاسم** (س582: «فلا يعمل بمفهوم الاسم مطلقاً»). -/
theorem ism_la_mukhalafa {m : Mn} (h : D.qayd m = some .ism) :
    ∀ f ∈ jisrMn D m, ∀ k, f.naw ≠ .mukhalafa k := by
  intro f hf k hk
  obtain ⟨q, _, _, hq, _, hs, _, _, _⟩ := mem_mukhalafaOf D (mukhalafa_min_mukhalafaOf D hf hk)
  rw [h] at hq; cases hq; cases hs

omit [DecidableEq L] in
/-- لكلّ منطوقٍ مفهومُ مخالفةٍ واحدٌ على الأكثر. -/
theorem mukhalafa_wahida (m : Mn) : (mukhalafaOf D m).length ≤ 1 := by
  unfold mukhalafaOf
  split
  · split
    · split <;> simp
    · simp
  · simp

/-- **الاقتضاءُ شرطٌ للمعنى المطابقيّ:** لا اقتضاءَ إلّا من لازمٍ مودَعٍ بأنّه شرطٌ له، بمصدره وغرضه (س552). -/
theorem iqtida_shart_lil_mutabaqa {ms : List Mn} {f : Mafhum Mn L} {s : MasdarIqtida} {g : GharadIqtida}
    (h : f ∈ jisr D ms) (hk : f.naw = .iqtida s g) : (f.lazim, s, g) ∈ D.iqtida f.asl := by
  obtain ⟨_, _, ⟨s', g', he, hx⟩ | ⟨_, he⟩ | he | he | hm⟩ := mem_jisrMn D (mem_jisr D h).2
  · rw [hk] at he; cases he; exact hx
  · rw [hk] at he; cases he
  · rw [hk] at he; cases he
  · rw [hk] at he; cases he
  · obtain ⟨_, _, _, _, _, _, _, _, hf⟩ := mem_mukhalafaOf D hm
    rw [hf] at hk; cases hk

/-- **الموافقةُ تابعةٌ لا شرط** (س560: «بأن لا يكون شرطا للمعنى المطابقي بل تابعا له»): لازمُ الموافقة لم يُودَع شرطًا
للمطابقيّ من المنطوق نفسِه، فلا يخرج لازمٌ واحدٌ اقتضاءً وموافقةً معًا. -/
theorem muwafaqa_tabia {ms : List Mn} {f : Mafhum Mn L} (h : f ∈ jisr D ms) (hk : f.naw = .muwafaqa) :
    f.lazim ∈ D.muwafiq f.asl ∧ ∀ x ∈ D.iqtida f.asl, x.1 ≠ f.lazim := by
  have hm := (mem_jisr D h).2
  unfold jisrMn at hm
  cases hp : mahmul D f.asl
  · simp [hp] at hm
  · simp only [hp, ite_true, List.mem_append, List.mem_map] at hm
    rcases hm with (((⟨x, _, he⟩ | ⟨x, _, he⟩) | ⟨x, _, he⟩) | ⟨l, hl, he⟩) | hk'
    · rw [← he] at hk; cases hk
    · rw [← he] at hk; cases hk
    · rw [← he] at hk; cases hk
    · have hlz : f.lazim = l := by rw [← he]
      rw [hlz]
      unfold muwafiqTabi at hl
      rw [List.mem_filter] at hl
      refine ⟨hl.1, fun x hx hxl => ?_⟩
      have := hl.2
      simp only [Bool.not_eq_true', List.any_eq_false] at this
      exact this x hx (by simp [hxl])
    · obtain ⟨_, _, _, _, _, _, _, _, hf⟩ := mem_mukhalafaOf D hk'
      rw [hf] at hk; cases hk

/-- **حسابُ الالتزام:** عددُ مفاهيم المنطوق المحمول = الاقتضاءُ + التنبيه + الإشارة + الموافقة + (0 أو 1 مخالفة)؛
وغيرُ المحمول صفر. -/
theorem adad_mafahim (m : Mn) :
    (jisrMn D m).length =
      if mahmul D m then
        (D.iqtida m).length + (D.tanbih m).length + (D.ishara m).length + (muwafiqTabi D m).length +
          (mukhalafaOf D m).length
      else 0 := by
  unfold jisrMn
  split <;> simp [List.length_append, Nat.add_assoc]

/-- **المفهومُ التزامٌ لا ثالث:** كلُّ ما يُخرجه الجسرُ طريقُه «مفهوم»، ودلالتُه الالتزامُ وحده
(`SLGE.Madlul.mafhum_iff_iltizam`؛ س550). -/
theorem tariq_mafhum (d : SLGE.Madlul.Dalala) :
    SLGE.Madlul.tariq d = .mafhum ↔ d = .iltizam :=
  SLGE.Madlul.mafhum_iff_iltizam d

/-! ## ٤. الشاهد: أمثلةُ ج3 نفسُها (س552–586)

اللوازمُ هنا نصوصٌ منقولةٌ بالمعنى من أسطرها المذكورة، والمودَعُ تعيينُ البنّاء لأمثلة النصّ (معلَن)؛
والمبرهناتُ مبرهنةٌ على الشاهد. -/

/-- أمثلةُ الشاهد بأسطرها. -/
inductive Shahid
  | qatilu      -- «قاتلوا الذين يلونكم» س552: اقتضاءٌ عقليٌّ لصحّة الوقوع
  | aatiq       -- «أعتق عبدك عني بألف درهم» س552: اقتضاءٌ شرعيٌّ لصحّة الوقوع
  | wadaa       -- «إن الله وضع عن أمتي الخطأ…» س552: اقتضاءٌ شرعيٌّ لصدق المتكلّم
  | sariq       -- «والسارق والسارقة فاقطعوا» س554: تنبيهٌ بالفاء
  | ghadban     -- «لا يقضي القاضي بين اثنين وهو غضبان» س554: تنبيهٌ بالوصف المناسب
  | haml30      -- «وحمله وفصاله ثلاثون شهرا» مع «وفصاله في عامين» س556: إشارة
  | bashiru     -- «فالآن باشروهن» مع «حتى يتبين لكم الخيط الأبيض» س556: إشارةٌ من آيةٍ واحدة
  | uff         -- «فلا تقل لهما أف» س558: موافقة
  | qintar      -- «من إن تأمنه بقنطار يؤده إليك» س558: موافقةٌ بالأعلى على الأدنى
  | dharra      -- «فمن يعمل مثقال ذرة خيرا يره» س558: موافقةٌ «من باب أولى» (تصنيفُه أدنى على أعلى تعيينُ البنّاء)
  | yatama      -- «إن الذين يأكلون أموال اليتامى ظلما» س558: موافقةٌ بالمساوي
  | luqata      -- «وليحفظ عفاصها ووكاءها» س559: موافقةٌ لا أعلى ولا أدنى ولا مساوٍ
  | saima       -- «في صدقة الغنم في سائمتها» س568: مخالفة صفةٍ مفهمة
  | abyad       -- «الأبيض يشبع إذا أكل» س568: صفةٌ غير مفهمة — لا مفهوم
  | hamlNafaqa  -- «وإن كن أولات حمل فأنفقوا عليهن» س573: مخالفة شرط
  | layl        -- «ثم أتموا الصيام إلى الليل» س578: مخالفة غاية
  | mia         -- «فاجلدوا كل واحد منهما مائة جلدة» س580: مخالفة عدد بسياقه
  | qirshayn    -- «اعطني القرشين اللذين لي عليك» س580: عددٌ بلا سياق — لا مفهوم
  | ghanam      -- «في الغنم زكاة» س582: اسم — لا مفهوم
  | riba        -- «لا تأكلوا الربا أضعافا مضاعفة» س586: نصٌّ معطِّل — لا مفهوم
  deriving DecidableEq, Repr

open Shahid

/-- مودَعُ الشاهد (تعيينُ البنّاء لأمثلة ج3؛ الكلماتُ محمولةٌ حقيقةً لغويّةً تعيينًا). -/
def wit : Mudaa Shahid String where
  kalimat _ := [.haqiqa .lughawiyya]
  qayd
    | saima | abyad | riba => some .sifa
    | hamlNafaqa => some .shart
    | layl => some .ghaya
    | mia | qirshayn => some .adad
    | ghanam => some .ism
    | _ => none
  mufhim
    | saima | riba => true
    | _ => false
  siyaqAdad
    | mia => true
    | _ => false
  innama _ := false
  aghlab _ := false
  muattil
    | riba => true
    | _ => false
  naqid
    | saima => some "لا زكاة في المعلوفة"
    | abyad => some "الأسود لا يشبع"
    | hamlNafaqa => some "لا نفقة لغير الحامل"
    | layl => some "لا صيام بعد دخول الليل"
    | mia => some "تحريم ما زاد على المائة"
    | qirshayn => some "لا دين غير القرشين"
    | ghanam => some "لا زكاة في غير الغنم"
    | riba => some "حل الربا إذا لم يكن أضعافا"
    | _ => none
  muwafiq
    | uff => ["تحريم الشتم", "تحريم الضرب"]
    | qintar => ["تأدية ما دون القنطار"]
    | dharra => ["رؤية ما فوق الذرة"]
    | yatama => ["تحريم إتلاف مال اليتيم"]
    | luqata => ["حفظ ما التقط من الدنانير"]
    | _ => []
  iqtida
    | qatilu => [("الأمر بتحصيل أدوات القتال", .aql, .sihha)]
    | aatiq => [("تمليك العبد بالبيع أو الهبة", .shar, .sihha)]
    | wadaa => [("وضع حكم الخطأ والنسيان والإكراه", .shar, .sidq)]
    | _ => []
  tanbih
    | sariq => [("السرقة سبب القطع", .fa)]
    | ghadban => [("الغضب علة النهي عن القضاء", .wasfMunasib)]
    | _ => []
  ishara
    | haml30 => ["أقل مدة الحمل ستة أشهر"]
    | bashiru => ["من أصبح جنبا لم يفسد صومه"]
    | _ => []

/-- **ما يُخرجه الجسر من أمثلة ج3 بأنواعها.** -/
theorem shawahid_mafhum :
    jisrMn wit qatilu = [⟨.iqtida .aql .sihha, qatilu, "الأمر بتحصيل أدوات القتال"⟩] ∧
    jisrMn wit aatiq = [⟨.iqtida .shar .sihha, aatiq, "تمليك العبد بالبيع أو الهبة"⟩] ∧
    jisrMn wit wadaa = [⟨.iqtida .shar .sidq, wadaa, "وضع حكم الخطأ والنسيان والإكراه"⟩] ∧
    jisrMn wit sariq = [⟨.tanbih .fa, sariq, "السرقة سبب القطع"⟩] ∧
    jisrMn wit ghadban = [⟨.tanbih .wasfMunasib, ghadban, "الغضب علة النهي عن القضاء"⟩] ∧
    jisrMn wit haml30 = [⟨.ishara, haml30, "أقل مدة الحمل ستة أشهر"⟩] ∧
    jisrMn wit bashiru = [⟨.ishara, bashiru, "من أصبح جنبا لم يفسد صومه"⟩] ∧
    jisrMn wit uff = [⟨.muwafaqa, uff, "تحريم الشتم"⟩, ⟨.muwafaqa, uff, "تحريم الضرب"⟩] ∧
    jisrMn wit saima = [⟨.mukhalafa .sifa, saima, "لا زكاة في المعلوفة"⟩] ∧
    jisrMn wit hamlNafaqa = [⟨.mukhalafa .shart, hamlNafaqa, "لا نفقة لغير الحامل"⟩] ∧
    jisrMn wit layl = [⟨.mukhalafa .ghaya, layl, "لا صيام بعد دخول الليل"⟩] ∧
    jisrMn wit mia = [⟨.mukhalafa .adad, mia, "تحريم ما زاد على المائة"⟩] := by
  decide

/-- **وما يمنعه:** الصفةُ غيرُ المفهمة (س568، س583)، والعددُ بلا سياق (س580)، والاسم (س582)، والنصُّ المعطِّل (س586). -/
theorem shawahid_la_mafhum :
    jisrMn wit abyad = [] ∧ jisrMn wit qirshayn = [] ∧ jisrMn wit ghanam = [] ∧ jisrMn wit riba = [] := by
  decide

/-- **الموافقةُ بلا شرط الأولويّة** (س558–560: قولُ الآمدي وردُّه): بالأعلى على الأدنى، وبالأدنى على الأعلى، وبالمساوي،
وبما ليس واحدًا منها — كلُّها مفهومُ موافقة. -/
theorem muwafaqa_bila_awlawiyya :
    (jisrMn wit qintar).map (·.naw) = [.muwafaqa] ∧ (jisrMn wit dharra).map (·.naw) = [.muwafaqa] ∧
    (jisrMn wit yatama).map (·.naw) = [.muwafaqa] ∧ (jisrMn wit luqata).map (·.naw) = [.muwafaqa] := by
  decide

/-- منطوقٌ فيه كلمةٌ «لا حكم» لا يُخرج شيئًا ولو أُودعت لوازمُه (شاهدٌ مبنيّ على `uff`). -/
theorem shahid_la_haml :
    jisrMn { wit with kalimat := fun _ => [.haqiqa .lughawiyya, .laHukm] } uff = [] := by
  decide

/-- شاهدٌ مبنيّ لـ`muwafaqa_tabia`: لازمٌ أُودع اقتضاءً وموافقةً معًا يخرج اقتضاءً وحده. -/
theorem shahid_tabia :
    (jisrMn { wit with muwafiq := fun _ => ["الأمر بتحصيل أدوات القتال"] } qatilu).map (·.naw) =
      [.iqtida .aql .sihha] := by
  decide

end MantuqMafhum
end Jisr
