/-
  Nizam/Asas.lean — النواةُ المبرهنةُ للمنظومة الموحّدة (م0 في `hawkama/البروتوكول.md`؛ قرار المالك 2026-10-18، 19:39: «نفذ»).
  لا تستورد شيئًا. أطلسُ الطبقات `Nizam/atlas.tsv`؛ وصوغُ جسور المحرّك عليها وتركيبُها سلسلةً واحدة م3.

  ما هنا خواصُّ صوريّةٌ لكلّ جسرٍ يُصاغ على `Nizam.Jisr`، لا لجسور المحرّك القائمة (لها أنواعُ أحكامٍ خاصّة: `Utur.Hukm`،
  `HukmDal`، `Hawass.Hukm`؛ ولا يقع تحت هذه المبرهنات منها شيءٌ حتّى يُعاد صوغُه عليها — م3). العدّ بالمعيار الموحَّد (جدولُ توجيهٍ رفعه المالك 2026-10-19 18:02 وأمر بتنفيذه: «توحيد تصنيف المبرهنات» — «موافق، مع فصل البرهان الرياضي عن الاختبار على شاهد» (س198)؛ وصياغةُ المعيار قراءةُ البنّاء): «على الشاهد» قضيّةٌ مغلقةٌ على معطياتٍ معيّنة برهانُها decide؛ و«تعريفيّة» برهانُها فكُّ التعريفات وتفكيكُ الحالات (unfold، cases، split، by_cases، subst، rfl، funext، simp/simp_all بمجموعته الافتراضيّة وبالتعريفات)، ولا يستدعي من المبرهنات المسمّاة إلّا قائمةً محصورة: ite_eq_left/ite_eq_right وite_true/ite_false، وBool.and_eq_true وBool.false_eq_true وbeq_iff_eq وdecide_eq_true_iff، ومعادلاتِ دالّةٍ على منشئ (Option.map_some، Option.bind_some)، وحقنَ المنشئات (Option.some.injEq، Natija.qima.inj)، وEq.symm/Eq.trans، وabsurd؛ ويُستعمل فرضُه بإعادة الكتابة، أو حدًّا مباشرًا (exact h، ⟨h, …⟩، Or.inl h)، أو لنفي حالةٍ ولو طُبّق على برهان (h1 h.symm) — فلا مبرهنةَ من الملفّ، ولا استقراء، ولا تطبيقَ فرضٍ كمّيٍّ أو دالّيٍّ على معطيات (h k)؛ و«لكلّ» ما سواهما من مبرهنةٍ عامّة. والتطبيقُ يدويٌّ بقائمة البنّاء؛ لا مصنِّفَ آليًّا: 12 مبرهنة —
  5 لكلّ (`salama_tatarakkab`، `tasduq_iff`، `tasduq_bi_mukhalifat`، `mukhalifat_dunya`، `mukhalifat_mukhalif`)، و7 تعريفيّة
  (`tarkib_huwiyya_yamin`، `tarkib_huwiyya_yasar`، `tarkib_tajmii`، `la_tarkhis_bila_ma_qablahu`، `la_hukm_yasri`، `mumtani_yasri`،
  `la_ilhaq_bila_illa`)، ولا شيء على الشاهد. (كان العدُّ «4 لكلّ بمقدّمات و8 فكُّ تعريف» بمعيارٍ لم يطّرد: خمسٌ من الثماني تستعمل
  فرضها، و`mukhalifat_mukhalif` تستدعي `List.mem_filter`.)
  ١. التركيب: `tarkib` تجميعيّ وله محايد، والسلامةُ تتركّب معه (`salama_tatarakkab`).
  ٢. «شرطُ الإمكان» بتعريف `bind`: لا ترخيصَ إلّا بترخيص ما قبله، و«لا حكم» والممتنعُ يسريان.
  ٣. الاستقراءُ على مودَعٍ مسمّى (قرار المالك ١): `tasduq_bi_mukhalifat` خاصّيّةٌ صوريّةٌ تصدق على **أيّ** قاعدةٍ وأيّ
     مودَع — فهي لا تقول شيئًا عن قاعدةٍ بعينها؛ ومعناها أنّ صيغةَ الادّعاء «تصدق على م بمخالفاتها» تُصدَق دائمًا بشرط أن
     تُسرد المخالفاتُ كلُّها؛ و`mukhalifat_dunya` تمنع إخفاءَ مخالفٍ (كلُّ استثناءٍ مُصدِقٍ يحويها)، و`mukhalifat_mukhalif` تمنع
     عدَّ ما ليس مخالفًا مخالفًا (كلُّ عنصرٍ فيها مندرجٌ لا يأخذ الحكم). فالفائدةُ في المخالفات
     المسرودة (تُحسب على المودَع بـ decide: «مبرهن على الشاهد»)، لا في الصدق. وسندُ قصر الدعوى على المشهود ج3 س964:
     «استقراء الشريعة يدل على أنه توجد في الشريعة أحكام معللة، ولا يدل على أن جميع أحكام الشريعة جاءت معللة».
     أمّا «القاعدة الكلّيّة» عند النبهاني فمستنبطةٌ من النصّ لا مستقرأة («تستنبط من النص الشرعي … إلا أن
     الدليل فيها يتضمن معنى بمثابة العلة»، س1037)، والنصُّ المخالف عنده يلغيها («فيعمل بالنص، وتلغى القاعدة»، س1037)، و«لا يقاس عليها قياساً، بل تندرج جزئياته تحتها» (س1037)؛ فأخذُ
     البنية `QaidaKulliya` (لفظٌ كلّيّ وحكمٌ وما يخرج عنه) من حدّها، وسردُ المخالف بدل الإلغاء، قراءةُ البنّاء لقرار المالك ١ بلا شاهد.
  ومعها القياس (ج3 س845): لا إلحاقَ بلا علّةٍ لها دليل (`la_ilhaq_bila_illa`؛ س870 «لا يأتي قياس حكم على حكم لمجرد التشابه»).
  بلا sorry ولا axiom ولا native_decide.
-/

namespace Nizam

/-! ## ١. الحكم الثلاثيّ والجسر -/

/-- مخرجُ كلّ طبقة: مرخَّصٌ بقيمته، أو لا حكم (غيابُ الشاهد)، أو ممتنعٌ باسم سببه. -/
inductive Hukm (α : Type) where
  | murakhkhas (a : α)
  | laHukm
  | mumtani (sabab : String)
  deriving DecidableEq, Repr

namespace Hukm
def bind {α β : Type} : Hukm α → (α → Hukm β) → Hukm β
  | murakhkhas a, f => f a
  | laHukm, _ => laHukm
  | mumtani s, _ => mumtani s
end Hukm

/-- الجسرُ من طبقةٍ إلى التي تليها. -/
abbrev Jisr (α β : Type) := α → Hukm β

def huwiyya {α : Type} : Jisr α α := Hukm.murakhkhas

/-- تركيبُ جسرين: الثاني لا يعمل إلّا على ما رخّصه الأوّل. -/
def tarkib {α β γ : Type} (f : Jisr α β) (g : Jisr β γ) : Jisr α γ := fun a => (f a).bind g

theorem tarkib_huwiyya_yamin {α β : Type} (f : Jisr α β) : tarkib f huwiyya = f := by
  funext a; unfold tarkib huwiyya; cases f a <;> rfl

theorem tarkib_huwiyya_yasar {α β : Type} (f : Jisr α β) : tarkib huwiyya f = f := by
  funext a; rfl

/-- التركيبُ تجميعيّ: سلسلةُ الطبقات واحدةٌ أيًّا كان تجميعُها. -/
theorem tarkib_tajmii {α β γ δ : Type} (f : Jisr α β) (g : Jisr β γ) (h : Jisr γ δ) :
    tarkib (tarkib f g) h = tarkib f (tarkib g h) := by
  funext a; unfold tarkib; cases f a <;> rfl

/-! ## ٢. السلامة وشرط الإمكان -/

/-- الجسرُ سليمٌ بين شرطَي طبقتيه: ما صحّ في الأولى لا يُرخَّص منه في الثانية إلّا صحيح. -/
def Salim {α β : Type} (P : α → Prop) (Q : β → Prop) (f : Jisr α β) : Prop :=
  ∀ a b, P a → f a = .murakhkhas b → Q b

/-- السلامةُ تتركّب: برهانُ كلّ جسرٍ وحده يكفي لبرهان السلسلة كلّها. -/
theorem salama_tatarakkab {α β γ : Type} {P : α → Prop} {Q : β → Prop} {R : γ → Prop}
    {f : Jisr α β} {g : Jisr β γ} (hf : Salim P Q f) (hg : Salim Q R g) : Salim P R (tarkib f g) := by
  intro a c hp h
  unfold tarkib at h
  cases hfa : f a with
  | murakhkhas b => rw [hfa] at h; exact hg b c (hf a b hp hfa) h
  | laHukm => rw [hfa] at h; cases h
  | mumtani s => rw [hfa] at h; cases h

/-- شرطُ الإمكان: لا ترخيصَ في السلسلة إلّا بترخيص الطبقة السابقة بعينه. -/
theorem la_tarkhis_bila_ma_qablahu {α β γ : Type} (f : Jisr α β) (g : Jisr β γ) (a : α) (c : γ)
    (h : tarkib f g a = .murakhkhas c) : ∃ b, f a = .murakhkhas b ∧ g b = .murakhkhas c := by
  unfold tarkib at h
  cases hfa : f a with
  | murakhkhas b => rw [hfa] at h; exact ⟨b, rfl, h⟩
  | laHukm => rw [hfa] at h; cases h
  | mumtani s => rw [hfa] at h; cases h

/-- «لا حكم» يسري: غيابُ الشاهد في طبقةٍ لا يصير فوقها ترخيصًا ولا امتناعًا. -/
theorem la_hukm_yasri {α β γ : Type} (f : Jisr α β) (g : Jisr β γ) (a : α) (h : f a = .laHukm) :
    tarkib f g a = .laHukm := by
  unfold tarkib; rw [h]; rfl

/-- والممتنعُ يسري باسم سببه نفسه. -/
theorem mumtani_yasri {α β γ : Type} (f : Jisr α β) (g : Jisr β γ) (a : α) (s : String)
    (h : f a = .mumtani s) : tarkib f g a = .mumtani s := by
  unfold tarkib; rw [h]; rfl

/-! ## ٣. الدعوى المستقرأة على مودَعٍ بمخالفاتها (قرار المالك ١؛ ج3 س964). البنيةُ من حدّ القاعدة الكلّيّة (س1034) بقراءة البنّاء -/

/-- القاعدة: لفظٌ كلّيّ تندرج تحته الجزئيّات، وحكمٌ منسوبٌ إليه، واستثناءٌ (في دعوى المودَع: مخالفاتُه المشهودة `mukhalifat`). -/
structure QaidaKulliya (α : Type) where
  kulli : α → Bool
  hukm : α → Bool
  istithna : List α

variable {α : Type} [DecidableEq α]

/-- صدقُ القاعدة على مودَع: كلُّ مشهودٍ مندرجٍ غيرِ مستثنى يأخذ الحكم. -/
def tasduq (q : QaidaKulliya α) (m : List α) : Bool :=
  m.all fun x => !q.kulli x || decide (x ∈ q.istithna) || q.hukm x

theorem tasduq_iff (q : QaidaKulliya α) (m : List α) :
    tasduq q m = true ↔ ∀ x ∈ m, q.kulli x = true → x ∉ q.istithna → q.hukm x = true := by
  unfold tasduq
  simp only [List.all_eq_true, Bool.or_eq_true, Bool.not_eq_true', decide_eq_true_eq]
  constructor
  · intro h x hx hk hi
    rcases h x hx with (h1 | h1) | h1
    · rw [hk] at h1; cases h1
    · exact absurd h1 hi
    · exact h1
  · intro h x hx
    by_cases hk : q.kulli x = true
    · by_cases hi : x ∈ q.istithna
      · exact Or.inl (Or.inr hi)
      · exact Or.inr (h x hx hk hi)
    · exact Or.inl (Or.inl (by simpa using hk))

/-- المخالفاتُ المشهودة: مندرجٌ في المودَع لا يأخذ الحكم. -/
def mukhalifat (q : QaidaKulliya α) (m : List α) : List α :=
  m.filter fun x => q.kulli x && !q.hukm x

/-- كلُّ قاعدةٍ تصدق على مودَعها إذا كانت مخالفاتُها المشهودةُ استثناءها. -/
theorem tasduq_bi_mukhalifat (q : QaidaKulliya α) (m : List α) :
    tasduq { q with istithna := mukhalifat q m } m = true := by
  rw [tasduq_iff]
  intro x hx hk hi
  by_cases hh : q.hukm x = true
  · exact hh
  · exfalso; apply hi
    unfold mukhalifat
    simp only [List.mem_filter]
    exact ⟨hx, by simp_all⟩

/-- وهي أصغرُ استثناءٍ يُصدِقها: كلُّ استثناءٍ يُصدِق القاعدة يحوي المخالفاتِ المشهودة كلَّها.
    فالاستقراءُ لا يُخفي مخالفًا (والاتّجاهُ الآخر في `mukhalifat_mukhalif`). -/
theorem mukhalifat_dunya (q : QaidaKulliya α) (m : List α) (E : List α)
    (h : tasduq { q with istithna := E } m = true) : ∀ x ∈ mukhalifat q m, x ∈ E := by
  intro x hx
  unfold mukhalifat at hx
  simp only [List.mem_filter, Bool.and_eq_true, Bool.not_eq_true'] at hx
  obtain ⟨hm, hk, hh⟩ := hx
  rw [tasduq_iff] at h
  by_cases hE : x ∈ E
  · exact hE
  · have := h x hm hk hE
    simp_all

omit [DecidableEq α] in
/-- ولا يُعدّ مخالفًا ما ليس مخالفًا: كلُّ عنصرٍ في المخالفات مشهودٌ في المودَع، مندرجٌ تحت الكلّيّ، ولا يأخذ الحكم. -/
theorem mukhalifat_mukhalif (q : QaidaKulliya α) (m : List α) (x : α) (hx : x ∈ mukhalifat q m) :
    x ∈ m ∧ q.kulli x = true ∧ q.hukm x = false := by
  unfold mukhalifat at hx
  simp only [List.mem_filter, Bool.and_eq_true, Bool.not_eq_true'] at hx
  exact ⟨hx.1, hx.2.1, hx.2.2⟩

/-! ## ٤. القياس بأركانه (ج3 س845، س868–س870) -/

/-- العلّةُ وصفٌ له دليلٌ في النقل (وإلّا فهو شبهٌ لا علّة). -/
structure Illa (α : Type) where
  wasf : α → Bool
  dalil : List String

/-- القياس: أصلٌ وحكمُه وعلّةٌ جامعة؛ وحكمُ الفرع ثمرتُه لا ركنُه. -/
structure Qiyas (α β : Type) where
  asl : α
  hukmAsl : β
  illa : Illa α

/-- الإلحاق: يُرخَّص حكمُ الأصل للفرع إن كانت للعلّة دليلٌ وتحقّقت في الأصل والفرع؛ وبلا دليلٍ لا حكم. -/
def ilhaq {β : Type} (q : Qiyas α β) (far : α) : Hukm β :=
  if q.illa.dalil = [] then .laHukm
  else if q.illa.wasf q.asl && q.illa.wasf far then .murakhkhas q.hukmAsl else .laHukm

omit [DecidableEq α] in
/-- لا إلحاقَ بلا علّةٍ لها دليل، ولا بعلّةٍ لم تتحقّق في الفرع: «لا يأتي قياس حكم على حكم لمجرد التشابه» (س870). -/
theorem la_ilhaq_bila_illa {β : Type} (q : Qiyas α β) (far : α) (b : β) (h : ilhaq q far = .murakhkhas b) :
    q.illa.dalil ≠ [] ∧ q.illa.wasf q.asl = true ∧ q.illa.wasf far = true ∧ b = q.hukmAsl := by
  unfold ilhaq at h
  split at h
  · cases h
  · rename_i hd
    split at h
    · rename_i hw
      simp only [Bool.and_eq_true] at hw
      cases h
      exact ⟨hd, hw.1, hw.2, rfl⟩
    · cases h

end Nizam
