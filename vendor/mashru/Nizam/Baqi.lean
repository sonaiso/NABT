/-
  Nizam/Baqi.lean — المتبقّي: عائلةُ المتطلّبات الدنيا لصيغةٍ موجبة، سليمةً تامّةً دنيا، وإسقاطُها حكمٌ ثلاثيّ هو `K3` في `Nizam/Phi.lean`.

  قولُ المالك (2026-10-21، 22:11 بتوقيت عمّان)، مع مرفقين عن حزمة «Mashru Flow 0.2» (README_AR.md وverification_summary.json؛ وشيفرتُها لم
  تُرفع): «حلل هذا يغير إطار العمل بشكل كبير وتطوره انت خبير بل أنت مجموعة وكلاء وخبراء حلل وطبق افضل الممارسات». والمرفقُ يعرّف قوانين
  المتبقّي (README س115–121: M(True) = {∅}، M(False) = ∅، M(a) = {{a}} للذرّة المجهولة، M(A AND B) = Min{X ∪ Y}، M(A OR B) = Min(M(A) ∪ M(B))،
  و«Min» بالاحتواء س123)، ويفحصها بتعدادٍ منتهٍ في بايثون، ويجعل أوّلَ ما يُبنى فوقه «إثبات الجسر الجبري في Lean» (س193). وهنا يُبرهَن
  ما يقابل الكفايةَ والشمولَ والدنيويّةَ والإسقاطَ لتعريف البنّاء `baqi` على أقنعة البتّات، لكلّ صيغة؛ ووصلُه بـ`residual.py` (لم يُرفع) وبالفاحص
  الرسميّ على المصدر (معيارُ القبول في س193) لم يُبنَ. وتعيينُ البنّاء: الذرّةُ رقمُ بتّ، والمجموعةُ قناع، والمعلومُ K والمنفيُّ D قناعان؛ والمنفيُّ
  يعطي ∅ (لا إكمال) — وليس في قوانين س115–121 بندٌ له، فهو قراءةُ البنّاء لـ«بعد تثبيت المعلوم» (س113) مع M(False) = ∅ —، وتقديمُ K على D
  حين تجتمع الذرّةُ فيهما ترتيبٌ معلَن (`taarud_yukhfa`):

  ١. **سليم** (`baqi_sahih`): كلُّ مجموعةٍ في المتبقّي تُكمل الصيغةَ فوق المعلوم، ولا تمسّ المنفيّ.
  ٢. **تامّ** (`baqi_kamil`): كلُّ إكمالٍ لا يمسّ المنفيَّ يحوي مجموعةً من المتبقّي.
  ٣. **أدنى** (`baqi_adna`): لا تحوي مجموعةٌ منه أخرى منه إلّا أن تكونها (`adna`: الاحتواءُ الحقيقيّ يُصغّر العدد، `dimn_asghar`، فالأدنى موجود).
  ٤. **إسقاطُ الحكم** (`hukm_k3`): ∅ في المتبقّي P، وفراغُ المتبقّي N، وما سواهما U — والمرفقُ يسمّي الإسقاطَ ولا يعرّفه (س37 «مع إسقاط الحكم
     إلى `P/N/U`»، س185 «قانوني إسقاط K3»)، فهذا التعريفُ قراءةُ البنّاء؛ وهو تقويمُ الصيغة بـ`K3.wa`/`K3.aw` من Phi بعينه (`k3`؛ المعلومُ P
     والمنفيُّ N والمجهولُ U). وP ⟺ الصيغةُ صادقةٌ بالمعلوم وحده (`P_iff`)، وN ⟺ كاذبةٌ ولو صدقت كلُّ ذرّةٍ معلومةٍ أو غيرِ منفيّة (`N_iff`) —
     وهو N الذي يسمّيه المرفق «للترخيص المغلق» (س131)؛ والنطاقُ المفتوح (N يصير U) في `Phi.yujadMaftuh` ولم يُوصل هنا.
  ٥. **التعارضُ حالٌ خارج K3** (`Natija`، `natija`؛ المرفق س125: «ولا يضيف قيمة رابعة إلى `Phi`»): بلا تعارضٍ في ذرّات الصيغة فالنتيجةُ حكمُها
     الثلاثيّ (`natija_hukm`، لكلّ صيغة)؛ و`taarud_yukhfa` شاهدُ أنّ `k3` وحده يُقوّم الذرّةَ المعلومةَ المنفيّةَ معًا P بالترتيب، فلا بدّ من تسميتها خارجه.
  ٦. **الجسرُ إلى #68** (`Nizam/QawaidB.lean`): متبقّي صيغة R⁺ فوق أصول الموضع هو `naqsB` بعينه (`naqsB_baqi`، لكلّ قانونٍ قناعُه في البتّات
     الأربع)، فرخصةُ الصفّ على الأعداد قانونٌ ينتج الكلمةَ وصيغةُ مقدّماته P بـ`K3` (`rukhsaB_k3`، لكلّ موضعٍ **على هذا الجدول**: عمومُها على
     المساعد `talab_sghir` على الشاهد، وصحّتُها على جدولٍ آخر تحتاجه عليه).
  وعلى الشاهد: مثالُ المرفق C معلومٌ في C ∧ (A ∨ B) فالمطلوبُ {{A}، {B}} (س123، `mithal_badilan`)؛ وشاهدٌ يمرّ بالتصغير Min (A ∨ (A ∧ B)
  فالمطلوبُ {{A}} وحده، `mithal_tasghir`)؛ و«ذو» (`mithal_dhu`): الناقصُ الصحبةُ وحدها والحكمُ U ثمّ ∅ وP بثبوتها (س64)، ونفيُ الصحبة فلا
  إكمال وN مثالُ البنّاء (والنفيُ في المرفق على الإضافة، س70، ونتيجتُه N في س155).

  29 مبرهنة بالمعيار الموحَّد (`Nizam/Asas.lean`): 24 لكلّ (`dimn_iff`، `dimn_nafs`، `dimn_trans`، `dimn_asghar`، `dimn_sifr`، `dimn_aw`،
  `adna_min`، `adna_kamil`، `adna_silsila`، `qima_ratiba`، `qima_dharrat`، `baqi_sahih`، `baqi_kamil`، `baqi_adna`، `P_iff`، `qinaMin_bit`،
  `N_iff`، `k3_P`، `k3_N`، `hukm_k3`، `natija_hukm`، `usulB_sghir`، `naqsB_baqi`، و`rukhsaB_k3` على هذا الجدول)، ولا تعريفيّة، و5 على الشاهد (`taarud_yukhfa`، `baqi_talab`
  — decide على القناعين في البتّات الأربع —، `mithal_badilan`، `mithal_tasghir`، `mithal_dhu`). ومساعدتان خاصّتان غيرُ معدودتين: `bit_wahid'` لكلّ،
  و`talab_sghir` على الشاهد (decide على جدول #68). طفراتُها P426–P433 في `tahaqquq/tafrat.json` تُفشل `lake build`؛ لا جدولَ خارجيًّا فلا
  مرآة بايثون.

  لا يُدّعى: أنّ شيفرة الحزمة تطابق هذا (لم تُرفع ولم تُشغَّل)؛ ولا السحبُ وسجلُّ الأحداث وإعادةُ التشغيل والمترجم (لم يُبنَ منها شيء)؛ ولا
  أنّ المتبقّي يُحسب بكلفةٍ محدودة (العائلةُ قد تنمو أسّيًّا، والمرفقُ يقيّدها بميزانية، س127)؛ ولا قيودُ مجالٍ تمنع اجتماعَ متطلّبين؛ والقائمةُ
  قد تتكرّر عناصرُها، والمقصودُ مجموعتُها. والمعلومُ والمنفيُّ هنا قناعان معطيان؛ ودستورُ Mashru يشترط لكلّ أصلٍ مودَعًا مختومًا، فوصلُهما
  بالمودَعات لم يُبنَ.
  بلا sorry ولا axiom ولا native_decide.
-/
import Nizam.Phi
import Nizam.QawaidB

namespace Nizam
namespace Baqi

open Nizam.Phi
open Nizam.Phi.K3

/-! ## ١. الاحتواءُ بين الأقنعة -/

/-- x ⊆ y بالبتّات. -/
def dimn (x y : Nat) : Bool := x &&& y == x

theorem dimn_iff (x y : Nat) : dimn x y = true ↔ ∀ i, x.testBit i = true → y.testBit i = true := by
  unfold dimn
  rw [beq_iff_eq]
  constructor
  · intro h i hx
    have := congrArg (fun n => n.testBit i) h
    simp only [Nat.testBit_and, hx, Bool.true_and] at this
    exact this
  · intro h
    apply Nat.eq_of_testBit_eq
    intro i
    rw [Nat.testBit_and]
    cases hx : x.testBit i
    · rfl
    · simp [h i hx]

theorem dimn_nafs (x : Nat) : dimn x x = true := (dimn_iff x x).2 fun _ h => h

theorem dimn_trans {x y z : Nat} (h1 : dimn x y = true) (h2 : dimn y z = true) : dimn x z = true :=
  (dimn_iff x z).2 fun i hx => (dimn_iff y z).1 h2 i ((dimn_iff x y).1 h1 i hx)

/-- الاحتواءُ الحقيقيّ يُصغّر العدد: فالأدنى بالاحتواء موجودٌ بالاستقراء على العدد. -/
theorem dimn_asghar {x y : Nat} (h : dimn x y = true) (hne : x ≠ y) : x < y := by
  unfold dimn at h
  rw [beq_iff_eq] at h
  have : x ≤ y := h ▸ Nat.and_le_right
  omega

theorem dimn_sifr {x : Nat} (h : dimn x 0 = true) : x = 0 := by
  unfold dimn at h
  rw [beq_iff_eq, Nat.and_zero] at h
  exact h.symm

theorem dimn_aw {x y s : Nat} (hx : dimn x s = true) (hy : dimn y s = true) : dimn (x ||| y) s = true :=
  (dimn_iff _ s).2 fun i h => by
    rw [Nat.testBit_or, Bool.or_eq_true] at h
    rcases h with h | h
    · exact (dimn_iff x s).1 hx i h
    · exact (dimn_iff y s).1 hy i h

/-! ## ٢. الأدنى بالاحتواء -/

/-- يبقى من القائمة ما لا تحويه مجموعةٌ أصغرُ منه فيها (قد تتكرّر عناصرُها؛ والمقصودُ مجموعتُها). -/
def adna (l : List Nat) : List Nat := l.filter fun x => !l.any fun y => dimn y x && y != x

theorem adna_min {l : List Nat} {x : Nat} (h : x ∈ adna l) : x ∈ l := (List.mem_filter.1 h).1

theorem adna_kamil (l : List Nat) : ∀ x, x ∈ l → ∃ y ∈ adna l, dimn y x = true := by
  intro x
  induction x using Nat.strongRecOn with
  | ind x ih =>
    intro hx
    by_cases hany : (l.any fun y => dimn y x && y != x) = true
    · obtain ⟨y, hy, hyx⟩ := List.any_eq_true.1 hany
      rw [Bool.and_eq_true, bne_iff_ne] at hyx
      obtain ⟨z, hz, hzy⟩ := ih y (dimn_asghar hyx.1 hyx.2) hy
      exact ⟨z, hz, dimn_trans hzy hyx.1⟩
    · refine ⟨x, List.mem_filter.2 ⟨hx, ?_⟩, dimn_nafs x⟩
      simpa using hany

theorem adna_silsila {l : List Nat} {x y : Nat} (hx : x ∈ adna l) (hy : y ∈ adna l) (h : dimn x y = true) : x = y := by
  apply Classical.byContradiction
  intro hne
  have hf := (List.mem_filter.1 hy).2
  simp only [Bool.not_eq_true', List.any_eq_false, Bool.and_eq_true, bne_iff_ne, not_and, ne_eq] at hf
  exact hf x (adna_min hx) h hne

/-! ## ٣. الصيغة الموجبة وقيمتُها -/

/-- صيغةٌ موجبة على ذرّاتٍ مرقّمة. -/
inductive Sigha
  | sadiq
  | kadhib
  | dharra (i : Nat)
  | wa (a b : Sigha)
  | aw (a b : Sigha)
deriving DecidableEq, Repr

/-- قيمتُها على تعيينٍ للذرّات. -/
def qima (p : Nat → Bool) : Sigha → Bool
  | .sadiq => true
  | .kadhib => false
  | .dharra i => p i
  | .wa a b => qima p a && qima p b
  | .aw a b => qima p a || qima p b

/-- الصيغةُ الموجبة رتيبة: ما صدق على تعيينٍ صدق على كلّ تعيينٍ أوسع. -/
theorem qima_ratiba (p q : Nat → Bool) (h : ∀ i, p i = true → q i = true) : ∀ f, qima p f = true → qima q f = true
  | .sadiq, _ => rfl
  | .kadhib, hf => hf
  | .dharra i, hf => h i hf
  | .wa a b, hf => by
    simp only [qima, Bool.and_eq_true] at hf ⊢
    exact ⟨qima_ratiba p q h a hf.1, qima_ratiba p q h b hf.2⟩
  | .aw a b, hf => by
    simp only [qima, Bool.or_eq_true] at hf ⊢
    exact hf.elim (fun h1 => Or.inl (qima_ratiba p q h a h1)) (fun h2 => Or.inr (qima_ratiba p q h b h2))

/-- ذرّاتُ الصيغة. -/
def dharrat : Sigha → List Nat
  | .dharra i => [i]
  | .wa a b => dharrat a ++ dharrat b
  | .aw a b => dharrat a ++ dharrat b
  | _ => []

/-- قيمتُها لا تتعلّق إلّا بذرّاتها. -/
theorem qima_dharrat (p q : Nat → Bool) : ∀ f, (∀ i ∈ dharrat f, p i = q i) → qima p f = qima q f
  | .sadiq, _ => rfl
  | .kadhib, _ => rfl
  | .dharra i, h => h i (by simp [dharrat])
  | .wa a b, h => by
    simp only [qima]
    rw [qima_dharrat p q a (fun i hi => h i (by simp [dharrat, hi])),
      qima_dharrat p q b (fun i hi => h i (by simp [dharrat, hi]))]
  | .aw a b, h => by
    simp only [qima]
    rw [qima_dharrat p q a (fun i hi => h i (by simp [dharrat, hi])),
      qima_dharrat p q b (fun i hi => h i (by simp [dharrat, hi]))]

/-! ## ٤. المتبقّي M(·) -/

/-- **المتبقّي**: عائلةُ المجموعات الدنيا التي تُكمل الصيغةَ فوق المعلوم K، بلا ذرّةٍ من المنفيّ D (قوانين README س115–121؛ وبندُ المنفيّ
وتقديمُ K عليه تعيينُ البنّاء). -/
def baqi (K D : Nat) : Sigha → List Nat
  | .sadiq => [0]
  | .kadhib => []
  | .dharra i => if K.testBit i then [0] else if D.testBit i then [] else [1 <<< i]
  | .wa a b => adna ((baqi K D a).flatMap fun x => (baqi K D b).map fun y => x ||| y)
  | .aw a b => adna (baqi K D a ++ baqi K D b)

private theorem bit_wahid' (r j : Nat) : (1 <<< r).testBit j = decide (j = r) := by
  apply Bool.eq_iff_iff.2
  rw [Aqd.bit_wahid, decide_eq_true_iff]

/-- **سليم:** كلُّ مجموعةٍ في المتبقّي تُكمل الصيغة، ولا تمسّ المنفيّ. -/
theorem baqi_sahih (K D : Nat) : ∀ f, ∀ x ∈ baqi K D f,
    qima (fun i => (K ||| x).testBit i) f = true ∧ x &&& D = 0
  | .sadiq, x, hx => by
    simp only [baqi, List.mem_singleton] at hx; subst hx; simp [qima]
  | .kadhib, x, hx => by simp [baqi] at hx
  | .dharra i, x, hx => by
    simp only [baqi] at hx
    split at hx
    · rename_i hk; simp only [List.mem_singleton] at hx; subst hx; simp [qima, hk]
    · split at hx
      · simp at hx
      · rename_i _ hd
        simp only [List.mem_singleton] at hx; subst hx
        refine ⟨by simp [qima, Nat.testBit_or], ?_⟩
        apply Nat.eq_of_testBit_eq; intro j
        rw [Nat.testBit_and, bit_wahid', Nat.zero_testBit]
        by_cases hj : j = i
        · subst hj; simp [hd]
        · simp [hj]
  | .wa a b, x, hx => by
    have hx' := adna_min hx
    simp only [List.mem_flatMap, List.mem_map] at hx'
    obtain ⟨y, hy, z, hz, rfl⟩ := hx'
    obtain ⟨qa, da⟩ := baqi_sahih K D a y hy
    obtain ⟨qb, db⟩ := baqi_sahih K D b z hz
    refine ⟨?_, ?_⟩
    · simp only [qima, Bool.and_eq_true]
      refine ⟨qima_ratiba _ _ (fun i h => ?_) a qa, qima_ratiba _ _ (fun i h => ?_) b qb⟩
      · simp only [Nat.testBit_or, Bool.or_eq_true] at h ⊢; rcases h with h | h <;> simp [h]
      · simp only [Nat.testBit_or, Bool.or_eq_true] at h ⊢; rcases h with h | h <;> simp [h]
    · apply Nat.eq_of_testBit_eq; intro j
      have h1 := congrArg (fun n => n.testBit j) da
      have h2 := congrArg (fun n => n.testBit j) db
      simp only [Nat.testBit_and, Nat.zero_testBit] at h1 h2
      simp only [Nat.testBit_and, Nat.testBit_or, Nat.zero_testBit]
      cases hy' : y.testBit j <;> cases hz' : z.testBit j <;> cases hd' : D.testBit j <;> simp_all
  | .aw a b, x, hx => by
    have hx' := adna_min hx
    rcases List.mem_append.1 hx' with h | h
    · obtain ⟨q, d⟩ := baqi_sahih K D a x h
      exact ⟨by simp only [qima, Bool.or_eq_true]; exact Or.inl q, d⟩
    · obtain ⟨q, d⟩ := baqi_sahih K D b x h
      exact ⟨by simp only [qima, Bool.or_eq_true]; exact Or.inr q, d⟩

/-- **تامّ:** كلُّ إكمالٍ لا يمسّ المنفيَّ يحوي مجموعةً من المتبقّي. -/
theorem baqi_kamil (K D : Nat) : ∀ f, ∀ s, s &&& D = 0 → qima (fun i => (K ||| s).testBit i) f = true →
    ∃ x ∈ baqi K D f, dimn x s = true
  | .sadiq, s, _, _ => ⟨0, by simp [baqi], by simp [dimn]⟩
  | .kadhib, s, _, h => by simp [qima] at h
  | .dharra i, s, hd, h => by
    simp only [qima, Nat.testBit_or, Bool.or_eq_true] at h
    simp only [baqi]
    split
    · exact ⟨0, by simp, by simp [dimn]⟩
    · rename_i hk
      have hs : s.testBit i = true := h.resolve_left hk
      split
      · rename_i hD
        have := congrArg (fun n => n.testBit i) hd
        simp [Nat.testBit_and, hs, hD] at this
      · refine ⟨1 <<< i, by simp, (dimn_iff _ _).2 fun j hj => ?_⟩
        rw [bit_wahid', decide_eq_true_iff] at hj
        subst hj; exact hs
  | .wa a b, s, hd, h => by
    simp only [qima, Bool.and_eq_true] at h
    obtain ⟨y, hy, hys⟩ := baqi_kamil K D a s hd h.1
    obtain ⟨z, hz, hzs⟩ := baqi_kamil K D b s hd h.2
    obtain ⟨w, hw, hwyz⟩ := adna_kamil ((baqi K D a).flatMap fun x => (baqi K D b).map fun y => x ||| y) (y ||| z)
      (List.mem_flatMap.2 ⟨y, hy, List.mem_map.2 ⟨z, hz, rfl⟩⟩)
    exact ⟨w, hw, dimn_trans hwyz (dimn_aw hys hzs)⟩
  | .aw a b, s, hd, h => by
    simp only [qima, Bool.or_eq_true] at h
    rcases h with h | h
    · obtain ⟨y, hy, hys⟩ := baqi_kamil K D a s hd h
      obtain ⟨w, hw, hwy⟩ := adna_kamil _ y (List.mem_append_left _ hy)
      exact ⟨w, hw, dimn_trans hwy hys⟩
    · obtain ⟨y, hy, hys⟩ := baqi_kamil K D b s hd h
      obtain ⟨w, hw, hwy⟩ := adna_kamil _ y (List.mem_append_right _ hy)
      exact ⟨w, hw, dimn_trans hwy hys⟩

/-- **أدنى:** لا تحوي مجموعةٌ من المتبقّي أخرى منه إلّا أن تكونها. -/
theorem baqi_adna (K D : Nat) : ∀ f, ∀ x ∈ baqi K D f, ∀ y ∈ baqi K D f, dimn x y = true → x = y
  | .sadiq, x, hx, y, hy, _ => by simp [baqi] at hx hy; rw [hx, hy]
  | .kadhib, x, hx, _, _, _ => by simp [baqi] at hx
  | .dharra i, x, hx, y, hy, _ => by
    simp only [baqi] at hx hy
    split at hx <;> split at hy <;> simp_all
  | .wa _ _, _, hx, _, hy, h => adna_silsila hx hy h
  | .aw _ _, _, hx, _, hy, h => adna_silsila hx hy h


/-! ## ٥. إسقاطُ الحكم الثلاثيّ -/

/-- **P:** ∅ في المتبقّي ⟺ الصيغةُ صادقةٌ بالمعلوم وحده. -/
theorem P_iff (K D : Nat) (f : Sigha) : 0 ∈ baqi K D f ↔ qima (fun i => K.testBit i) f = true := by
  constructor
  · intro h
    have := (baqi_sahih K D f 0 h).1
    simpa using this
  · intro h
    obtain ⟨x, hx, hx0⟩ := baqi_kamil K D f 0 (by simp) (by simpa using h)
    rw [dimn_sifr hx0] at hx
    exact hx

/-- قناعُ ذرّاتٍ من قائمةٍ ليست في المنفيّ. -/
def qinaMin (D : Nat) (l : List Nat) : Nat := l.foldl (fun m i => if D.testBit i then m else m ||| 1 <<< i) 0

theorem qinaMin_bit (D j : Nat) : ∀ (l : List Nat) (m : Nat),
    (l.foldl (fun m i => if D.testBit i then m else m ||| 1 <<< i) m).testBit j =
      (m.testBit j || (l.contains j && !D.testBit j))
  | [], m => by simp
  | i :: l, m => by
    rw [List.foldl_cons, qinaMin_bit D j l, List.contains_cons]
    cases hD : D.testBit i
    · simp only [Bool.false_eq_true, ↓reduceIte]
      rw [Nat.testBit_or, bit_wahid']
      by_cases hji : j = i
      · subst hji; simp [hD]
      · have hb : (j == i) = false := beq_false_of_ne hji
        simp [hb, hji]
    · simp only [↓reduceIte]
      by_cases hji : j = i
      · subst hji; simp [hD]
      · have hb : (j == i) = false := beq_false_of_ne hji
        simp [hb]

/-- **N (في المغلق):** المتبقّي فارغ ⟺ الصيغةُ كاذبةٌ ولو صدقت كلُّ ذرّةٍ معلومةٍ أو غيرِ منفيّة. -/
theorem N_iff (K D : Nat) (f : Sigha) :
    baqi K D f = [] ↔ qima (fun i => K.testBit i || !D.testBit i) f = false := by
  constructor
  · intro h
    cases hq : qima (fun i => K.testBit i || !D.testBit i) f
    · rfl
    · exfalso
      have hbit : ∀ j, (qinaMin D (dharrat f)).testBit j = ((dharrat f).contains j && !D.testBit j) := by
        intro j; unfold qinaMin; rw [qinaMin_bit]; simp
      have hs : qinaMin D (dharrat f) &&& D = 0 := by
        apply Nat.eq_of_testBit_eq; intro j
        rw [Nat.testBit_and, hbit, Nat.zero_testBit]
        cases D.testBit j <;> simp
      have hq' : qima (fun i => (K ||| qinaMin D (dharrat f)).testBit i) f = true := by
        rw [qima_dharrat _ (fun i => K.testBit i || !D.testBit i) f (fun i hi => by
          rw [Nat.testBit_or, hbit, List.contains_iff_mem.2 hi, Bool.true_and])]
        exact hq
      obtain ⟨x, hx, _⟩ := baqi_kamil K D f _ hs hq'
      rw [h] at hx
      simp at hx
  · intro h
    cases hb : baqi K D f with
    | nil => rfl
    | cons x xs =>
      exfalso
      obtain ⟨q, d⟩ := baqi_sahih K D f x (by rw [hb]; exact List.mem_cons_self)
      have hm := qima_ratiba _ (fun i => K.testBit i || !D.testBit i) (fun i hi => by
        rw [Nat.testBit_or, Bool.or_eq_true] at hi
        rcases hi with hk | hx
        · simp [hk]
        · have := congrArg (fun n => n.testBit i) d
          simp only [Nat.testBit_and, hx, Bool.true_and, Nat.zero_testBit] at this
          simp [this]) f q
      rw [h] at hm
      exact Bool.false_ne_true hm

/-- تقويمُ الصيغة بالحكم الثلاثيّ: المعلومُ P، والمنفيُّ N، وما سواهما U، والربطُ والفصلُ `K3.wa`/`K3.aw` من `Nizam/Phi.lean`. -/
def k3 (K D : Nat) : Sigha → K3
  | .sadiq => .P
  | .kadhib => .N
  | .dharra i => if K.testBit i then .P else if D.testBit i then .N else .U
  | .wa a b => K3.wa (k3 K D a) (k3 K D b)
  | .aw a b => K3.aw (k3 K D a) (k3 K D b)

theorem k3_P (K D : Nat) : ∀ f, k3 K D f = .P ↔ qima (fun i => K.testBit i) f = true
  | .sadiq => by simp [k3, qima]
  | .kadhib => by simp [k3, qima]
  | .dharra i => by
    simp only [k3, qima]
    by_cases hk : K.testBit i = true
    · simp [hk]
    · by_cases hd : D.testBit i = true <;> simp [hk, hd]
  | .wa a b => by simp only [k3, qima, wa_P, Bool.and_eq_true, k3_P K D a, k3_P K D b]
  | .aw a b => by simp only [k3, qima, aw_P, Bool.or_eq_true, k3_P K D a, k3_P K D b]

theorem k3_N (K D : Nat) : ∀ f, k3 K D f = .N ↔ qima (fun i => K.testBit i || !D.testBit i) f = false
  | .sadiq => by simp [k3, qima]
  | .kadhib => by simp [k3, qima]
  | .dharra i => by
    simp only [k3, qima]
    by_cases hk : K.testBit i = true
    · simp [hk]
    · by_cases hd : D.testBit i = true <;> simp [hk, hd]
  | .wa a b => by simp only [k3, qima, wa_N, Bool.and_eq_false_iff, k3_N K D a, k3_N K D b]
  | .aw a b => by simp only [k3, qima, aw_N, Bool.or_eq_false_iff, k3_N K D a, k3_N K D b]

/-- حكمُ المتبقّي: ∅ فيه P، وفراغُه N، وما سواهما U. -/
def hukmBaqi (K D : Nat) (f : Sigha) : K3 :=
  if (baqi K D f).contains 0 then .P else if (baqi K D f).isEmpty then .N else .U

/-- **إسقاطُ الحكم:** حكمُ المتبقّي هو تقويمُ الصيغة بـ`K3.wa`/`K3.aw` بعينه، لكلّ صيغةٍ ومعلومٍ ومنفيّ. -/
theorem hukm_k3 (K D : Nat) (f : Sigha) : hukmBaqi K D f = k3 K D f := by
  unfold hukmBaqi
  cases h0 : (baqi K D f).contains 0
  · cases he : (baqi K D f).isEmpty
    · simp only [Bool.false_eq_true, ↓reduceIte]
      cases hk : k3 K D f
      · have := List.contains_iff_mem.2 ((P_iff K D f).2 ((k3_P K D f).1 hk))
        rw [h0] at this; exact absurd this Bool.false_ne_true
      · have := List.isEmpty_iff.2 ((N_iff K D f).2 ((k3_N K D f).1 hk))
        rw [he] at this; exact absurd this Bool.false_ne_true
      · rfl
    · simp only [Bool.false_eq_true, ↓reduceIte]
      exact ((k3_N K D f).2 ((N_iff K D f).1 (List.isEmpty_iff.1 he))).symm
  · simp only [↓reduceIte]
    exact ((k3_P K D f).2 ((P_iff K D f).1 (List.contains_iff_mem.1 h0))).symm

/-! ## ٦. التعارضُ حالٌ خارج K3 -/

/-- النتيجة: حكمٌ ثلاثيّ، أو تعارضٌ بقناع الذرّات المعلومة المنفيّة معًا في الصيغة. -/
inductive Natija
  | hukm (k : K3)
  | taarud (qina : Nat)
deriving DecidableEq, Repr

def natija (K D : Nat) (f : Sigha) : Natija :=
  if K &&& D &&& qinaMin 0 (dharrat f) = 0 then .hukm (hukmBaqi K D f) else .taarud (K &&& D &&& qinaMin 0 (dharrat f))

/-- **لا تعارضَ في ذرّات الصيغة ⇒ النتيجةُ حكمُها الثلاثيّ** (لكلّ صيغةٍ ومعلومٍ ومنفيّ). -/
theorem natija_hukm (K D : Nat) (f : Sigha) (h : K &&& D &&& qinaMin 0 (dharrat f) = 0) : natija K D f = .hukm (k3 K D f) := by
  unfold natija
  simp [h, hukm_k3]

/-- **الحكمُ الثلاثيّ وحده يُخفي التعارض** (على الشاهد): الذرّةُ 0 معلومةٌ منفيّةٌ معًا فتُقوَّم P بالترتيب، والنتيجةُ تسمّيها تعارضًا؛ والصيغةُ
الذرّةُ 1 والتعارضُ في الذرّة 0 فالنتيجةُ حكمُها U. -/
theorem taarud_yukhfa : k3 1 1 (.dharra 0) = .P ∧ natija 1 1 (.dharra 0) = .taarud 1 ∧ natija 1 1 (.dharra 1) = .hukm .U := by decide

/-! ## ٧. الجسرُ إلى صفّ الأسماء الستّة (`Nizam/QawaidB.lean`) -/

/-- صيغةُ قناع المتطلّبات R⁺ (بتّاتُه 0–3): ربطُ ذرّاته. -/
def sighaTalab (t : Nat) : Sigha :=
  [0, 1, 2, 3].foldr (fun i f => if t.testBit i then .wa (.dharra i) f else f) .sadiq

/-- متبقّي صيغة R⁺ فوق أصولٍ P (بلا منفيّ) هو R⁺ ∖ P وحده، لكلّ قناعين في البتّات الأربع. -/
theorem baqi_talab : ∀ t < 16, ∀ p < 16, baqi p 0 (sighaTalab t) = [t ^^^ (t &&& p)] := by decide

theorem usulB_sghir (a h : Nat) : QawaidB.usulB a h < 16 := by
  unfold QawaidB.usulB
  split <;> split <;> decide

/-- **`naqsB` هو المتبقّي** لصيغة القانون فوق أصول الموضع. -/
theorem naqsB_baqi (a : Nat) (q : QawaidB.QanunB) (ht : q.talab < 16) :
    baqi (QawaidB.usulB a q.hala) 0 (sighaTalab q.talab) = [QawaidB.naqsB a q] := by
  rw [baqi_talab q.talab ht _ (usulB_sghir a q.hala)]
  rfl

private theorem talab_sghir : ∀ q ∈ QawaidB.qawaninB, q.talab < 16 := by decide

/-- **الرخصةُ على الأعداد تقويمٌ ثلاثيّ:** قانونٌ ينتج الكلمةَ وصيغةُ مقدّماته P بـ`K3` على أصول الموضع — لكلّ موضعٍ على هذا الجدول (عمومُها على
`talab_sghir` على الشاهد). -/
theorem rukhsaB_k3 (k : Option Nat) (a : Nat) :
    QawaidB.rukhsaB k a = QawaidB.qawaninB.any (fun q =>
      QawaidB.yuntijB k a q && k3 (QawaidB.usulB a q.hala) 0 (sighaTalab q.talab) == .P) := by
  unfold QawaidB.rukhsaB
  apply Bool.eq_iff_iff.2
  simp only [List.any_eq_true, Bool.and_eq_true, beq_iff_eq]
  constructor <;> rintro ⟨q, hq, hy, h⟩ <;> refine ⟨q, hq, hy, ?_⟩
  · rw [← hukm_k3]; unfold hukmBaqi
    rw [naqsB_baqi a q (talab_sghir q hq), h]; rfl
  · rw [← hukm_k3] at h; unfold hukmBaqi at h
    rw [naqsB_baqi a q (talab_sghir q hq)] at h
    by_cases hn : QawaidB.naqsB a q = 0
    · exact hn
    · exfalso
      simp [Ne.symm hn] at h

/-! ## ٨. على الشاهد: مثالا README وشاهدُ التصغير -/

/-- README §4: C معلومٌ في C ∧ (A ∨ B)، فالمطلوبُ {{A}، {B}} لا {A، B}. -/
theorem mithal_badilan : baqi 1 0 (.wa (.dharra 0) (.aw (.dharra 1) (.dharra 2))) = [2, 4] := by decide

/-- **التصغير Min:** A ∨ (A ∧ B) فالمطلوبُ {{A}} وحده؛ ولولا التصغيرُ لبقي {A، B} معه. -/
theorem mithal_tasghir : baqi 0 0 (.aw (.dharra 0) (.wa (.dharra 0) (.dharra 1))) = [1] := by decide

/-- مثالُ README س48–64: أصلٌ (0) وإضافةٌ (1) ثابتان، فالناقصُ الصحبةُ (2) وحدها والحكمُ U، وبثبوتها ∅ (س64)؛ ونفيُ الصحبة (مثالُ البنّاء) فلا
إكمال وN في المغلق. -/
theorem mithal_dhu :
    baqi 3 0 (.wa (.dharra 0) (.wa (.dharra 1) (.dharra 2))) = [4] ∧
    k3 3 0 (.wa (.dharra 0) (.wa (.dharra 1) (.dharra 2))) = .U ∧
    baqi 7 0 (.wa (.dharra 0) (.wa (.dharra 1) (.dharra 2))) = [0] ∧
    baqi 3 4 (.wa (.dharra 0) (.wa (.dharra 1) (.dharra 2))) = [] ∧
    k3 3 4 (.wa (.dharra 0) (.wa (.dharra 1) (.dharra 2))) = .N := by decide

end Baqi
end Nizam
