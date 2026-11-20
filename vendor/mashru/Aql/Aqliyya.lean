/-
  Aql/Aqliyya.lean — العقل والعقلية عند النبهاني، طبقة «الحكم» في المنظومة.

  السند (أسطر الملفّات المحوَّلة: التفكير = a3.txt، ج1 = a1.txt):
  * التفكير 55: العقل «نقل الحسّ بالواقع بواسطة الحواسّ إلى الدماغ، ووجود معلومات سابقة يُفسَّر
    بواسطتها هذا الواقع». ج1 317: لا بحث عقليّ إن فُقد واحد من الأربعة.
  * التفكير 37: الإحساس وحده لا يُنتج فكرًا ولو تكرّر.
  * التفكير 39–41: المعلومات السابقة يجب أن تكون عن الواقع أو متعلّقة به.
  * ج1 29: العقلية «الكيفية التي يُربط فيها الواقع بالمعلومات، أو المعلومات بالواقع، بقياسها إلى
    قاعدة واحدة أو قواعد معيّنة»؛ «ومن هنا يأتي اختلاف العقليات».
  * ج1 35: العقل مفطور، والعقلية تتكوّن بفعل الإنسان، وللقاعدة الأثر الأكبر في تكوينها.
  * ج1 57: إن تعدّدت القواعد كانت الشخصية «لا لون لها».
  * التفكير 65: الحكم بوجود الشيء قطعيّ، وبحقيقته أو صفته ظنّيّ.
  * ج1 27: المعنى «مفهوم» إن كان له واقع محسوس أو مسلَّم به عن محسوس، وإلّا «معلومة».

  الفرق بين العقل والعقلية في هذا الملف: العقل = اجتماع الأركان الأربعة وتعلّق المعلومة بالواقع
  (`aql`)؛ والعقلية = ذلك مقيسًا إلى قاعدة (`aqliyya`). القاعدة معامل، فلا عقلية بلا قاعدة معيّنة.
  و§٧ (2026-10-21، ويستورد `Aql.Qaida`): مثالٌ من القاعدة يُبنى من فاحص المحرّك `Qaida.maqbul` (`qaidaMurakhkhasa`).
  بلا sorry ولا axiom ولا native_decide.
-/
import Aql.Qaida

namespace Aql

variable {W M H : Type}   -- الواقع، المعلومة السابقة، الحكم

/-- الأركان الأربعة (التفكير 55؛ ج1 317). الواقع قد يغيب، والمعلومات قائمة قد تفرغ. -/
structure Arkan (W M : Type) where
  waqi     : Option W
  hiss     : Bool
  dimagh   : Bool
  maalumat : List M

/-- تعلّق المعلومة بالواقع (التفكير 39–41)، والقاعدة التي يُقاس إليها الربط (ج1 29). -/
structure Qaida (W M H : Type) where
  qis : W → M → Option H

/-- المعلومات التي يُفسَّر بها الواقع: المتعلّقة به وحدها. -/
def mufassira (taalluq : W → M → Bool) (w : W) (ms : List M) : List M :=
  ms.filter (taalluq w)

/-- العقل: هل قام الإدراك؟ الأركان الأربعة، ومعلومةٌ واحدة على الأقلّ متعلّقة بالواقع. -/
def aql (taalluq : W → M → Bool) (a : Arkan W M) : Bool :=
  a.hiss && a.dimagh &&
    match a.waqi with
    | none => false
    | some w => !(mufassira taalluq w a.maalumat).isEmpty

/-- العقلية: الربط مقيسًا إلى قاعدة؛ مخرجه الأحكام. -/
def aqliyya (taalluq : W → M → Bool) (q : Qaida W M H) (a : Arkan W M) : List H :=
  if a.hiss && a.dimagh then
    match a.waqi with
    | none => []
    | some w => (mufassira taalluq w a.maalumat).filterMap (q.qis w)
  else []

/-! ## ١. لا حكم إن نقص ركن -/

theorem la_hukm_bila_waqi (t : W → M → Bool) (q : Qaida W M H) (a : Arkan W M)
    (h : a.waqi = none) : aqliyya t q a = [] := by
  unfold aqliyya; rw [h]; split <;> rfl

theorem la_hukm_bila_hiss (t : W → M → Bool) (q : Qaida W M H) (a : Arkan W M)
    (h : a.hiss = false) : aqliyya t q a = [] := by
  unfold aqliyya; simp [h]

theorem la_hukm_bila_dimagh (t : W → M → Bool) (q : Qaida W M H) (a : Arkan W M)
    (h : a.dimagh = false) : aqliyya t q a = [] := by
  unfold aqliyya; simp [h]

theorem la_hukm_bila_maalumat (t : W → M → Bool) (q : Qaida W M H) (a : Arkan W M)
    (h : a.maalumat = []) : aqliyya t q a = [] := by
  unfold aqliyya; rw [h]; split
  · cases a.waqi <;> rfl
  · rfl

/-! ## ٢. المعلومة غير المتعلّقة بالواقع لا تفسّره (التفكير 39–41) -/

theorem ghayr_mutaalliq_la_yufassir (t : W → M → Bool) (q : Qaida W M H) (a : Arkan W M) (w : W)
    (hw : a.waqi = some w) (h : ∀ m ∈ a.maalumat, t w m = false) : aqliyya t q a = [] := by
  have : mufassira t w a.maalumat = [] := by
    unfold mufassira; rw [List.filter_eq_nil_iff]; intro m hm; simp [h m hm]
  unfold aqliyya; rw [hw]; split
  · simp [this]
  · rfl

/-- ولا يقوم عقلٌ بلا معلومة متعلّقة. -/
theorem la_aql_bila_taalluq (t : W → M → Bool) (a : Arkan W M) (w : W)
    (hw : a.waqi = some w) (h : ∀ m ∈ a.maalumat, t w m = false) : aql t a = false := by
  have : mufassira t w a.maalumat = [] := by
    unfold mufassira; rw [List.filter_eq_nil_iff]; intro m hm; simp [h m hm]
  unfold aql; rw [hw]; simp [this]

/-! ## ٣. التكرار لا يُنشئ فكرًا (التفكير 37)
    الإحساس بالواقع n مرّة بلا معلومات سابقة: لا حكم واحد، أيًّا كان n. -/

theorem takrar_la_yunshi_fikran (t : W → M → Bool) (q : Qaida W M H) (a : Arkan W M)
    (h : a.maalumat = []) (n : Nat) :
    ((List.replicate n a).flatMap (aqliyya t q)) = [] := by
  induction n with
  | zero => rfl
  | succ k ih => simp [List.replicate_succ, List.flatMap_cons, la_hukm_bila_maalumat t q a h, ih]

/-! ## ٤. الأحكام كلّها مقيسة إلى القاعدة: لا حكم يخرج من غيرها (ج1 29) -/

theorem kull_hukm_min_alqaida (t : W → M → Bool) (q : Qaida W M H) (a : Arkan W M) (h : H)
    (hh : h ∈ aqliyya t q a) :
    ∃ w m, a.waqi = some w ∧ m ∈ a.maalumat ∧ t w m = true ∧ q.qis w m = some h := by
  unfold aqliyya at hh
  split at hh
  · rcases hw : a.waqi with _ | w
    · rw [hw] at hh; simp at hh
    · rw [hw] at hh
      simp only [List.mem_filterMap, mufassira, List.mem_filter] at hh
      obtain ⟨m, ⟨hm, ht⟩, hq⟩ := hh
      exact ⟨w, m, rfl, hm, ht, hq⟩
  · simp at hh

/-! ## ٥. اختلاف العقليات من القاعدة، وتعدّد القواعد يُفقد اللون (ج1 29، 57) -/

/-- تناقض حكمين، يعطيه المودَع (نفي وإثبات لشيء واحد مثلًا). -/
def Mutasiq (tanaqud : H → H → Prop) (hs : List H) : Prop :=
  ∀ x ∈ hs, ∀ y ∈ hs, ¬ tanaqud x y

/-- شاهد: الأركان نفسها، وقاعدتان؛ كلٌّ منهما متّسقة وحدها، وجمعهما متناقض.
    حكما الشاهد: true = «يُقبل»، false = «يُرفض»، والتناقض اختلافهما. -/
def wShahid : Arkan Unit Unit := ⟨some (), true, true, [()]⟩
def qAkhdh : Qaida Unit Unit Bool := ⟨fun _ _ => some true⟩
def qRadd  : Qaida Unit Unit Bool := ⟨fun _ _ => some false⟩
def tAll : Unit → Unit → Bool := fun _ _ => true
def tanaqudB (x y : Bool) : Prop := x ≠ y

theorem ikhtilaf_alaqliyyat :
    aqliyya tAll qAkhdh wShahid ≠ aqliyya tAll qRadd wShahid := by decide

theorem qaida_wahida_mutasiqa :
    Mutasiq tanaqudB (aqliyya tAll qAkhdh wShahid) ∧ Mutasiq tanaqudB (aqliyya tAll qRadd wShahid) := by
  refine ⟨?_, ?_⟩ <;> intro x hx y hy <;> simp [aqliyya, wShahid, qAkhdh, qRadd, tAll, mufassira] at hx hy <;>
    subst hx <;> subst hy <;> simp [tanaqudB]

theorem taaddud_alqawaid_la_lawn :
    ¬ Mutasiq tanaqudB (aqliyya tAll qAkhdh wShahid ++ aqliyya tAll qRadd wShahid) := by
  intro h
  exact h true (by decide) false (by decide) (by simp [tanaqudB])

/-! ## ٦. مرتبة الحكم ومرتبة المعنى (التفكير 65؛ ج1 27) -/

inductive NawHukm | wujud | haqiqaAwSifa deriving DecidableEq, Repr
inductive Martaba | qati | zanni deriving DecidableEq, Repr

/-- الحكم بالوجود عن حسٍّ قطعيّ؛ والحكم بالحقيقة أو الصفة ظنّيّ دائمًا. -/
def martaba : NawHukm → Bool → Martaba
  | .wujud, true => .qati
  | _, _ => .zanni

theorem haqiqa_zanniyya (hiss : Bool) : martaba .haqiqaAwSifa hiss = .zanni := rfl

inductive MartabaMana | mafhum | maaluma deriving DecidableEq, Repr

/-- المفهوم ما له شاهد واقع (محسوس أو مسلَّم به عن محسوس)، وإلّا فمعلومة. -/
def martabaMana (shuhud : List String) : MartabaMana :=
  if shuhud.isEmpty then .maaluma else .mafhum

theorem la_mafhum_bila_shahid : martabaMana [] = .maaluma := rfl

theorem mafhum_bishahid (s : String) (ss : List String) : martabaMana (s :: ss) = .mafhum := rfl

/-! ## ٧. القاعدةُ المرخَّصة قاعدةً للعقليّة (قرار المالك 2026-10-21، 09:51)

  `Qaida W M H` أعلاه دالّةُ قياسٍ حرّة: أيُّ دالّةٍ تُخرج حكمًا تصلح لها، وشاهدُ ٥ يبني قاعدتين بلا قانون (`qAkhdh`، `qRadd`).
  وهذا النوعُ باقٍ كما هو. وهنا يُبنى منه مثالٌ من قاعدة المحرّك الواحدة ذات الإصدار (`_root_.Qaida.Qaida`) وفاحصِها
  (`_root_.Qaida.maqbul`)، `qaidaMurakhkhasa`: الربطُ يقترح ادّعاءً بسلسلته (`iqtirah`)، ولا يخرج حكمًا إلّا ما يقبله الفاحص،
  والحكمُ يحمل سلسلتَه. **إذا بُنيت قاعدةُ العقليّة بـ`qaidaMurakhkhasa`** فلا يخرج حكمٌ إلّا ما يقبله `maqbul`. ولا يستعملها
  المحرّك بعدُ: القارئ والفاحص التنفيذيّ لا يستدعيان `aqliyya`.
  وج1 س29 بنصّه: «الكيفية التي يُربط فيها الواقع بالمعلومات، أو المعلومات بالواقع بقياسها إلى قاعدة واحدة أو قواعد معينة».
  وجعلُ «القاعدة» فيه `Qaida.Qaida` ذاتَ الإصدار قراءةُ البنّاء، على قرار المالك (15 أكتوبر 2026) أن يكون الحكمُ كلُّه جبريًّا مرخَّصًا
  (رأس `Aql/Qaida.lean`).

  * كلُّ حكمٍ تُخرجه مقبولٌ بالفاحص (`aqliyya_maqbula`) ومرخَّصٌ في القاعدة (`aqliyya_murakhkhasa`).
  * وأحكامُها تُعبَّأ في `Jawab q aslB` واحد (`aqliyya_jawab`). وأنّ جوابًا بالقاعدة q لا يُضمّ إليه جوابٌ بقاعدةٍ أخرى فمن نوع
    `Jawab` و`Qaida.damm` (`Aql/Qaida.lean`)، لا من هذه المبرهنة؛ وضمُّ قائمتين بقاعدتين حرّتين ممكنٌ كما في §٥.
  * وإن لم يقبل الفاحصُ شيئًا ممّا يُقترح فلا حكمَ أصلًا (`iqtirah_la_yahkum`)؛ وأنّ المرفوضَ وحده لا يخرج فمن `aqliyya_maqbula`.
  * والأركانُ الأربعة باقيةٌ شرطًا: مبرهناتُ §١–§٣ عامّةٌ في كلّ `Qaida W M H`، فتصدق على هذه القاعدة بلا مبرهنةٍ جديدة.
  شاهدُه على قاعدة `Qaida.qShahid` نفسِها (`shahid_aqliyya_murakhkhasa`).
  ولا يدّعي هذا أنّ الاقتراح صحيحٌ لغةً: الاقتراحُ من الدماغ، والقبولُ من القاعدة؛ ووجهُ إخراج الاقتراح لم يُبنَ.
-/

section Murakhkhasa

variable {P : Type} [DecidableEq P]

/-- قاعدةُ العقليّة من القاعدة المرخَّصة: يخرج الادّعاءُ المقترح حكمًا إن قبله الفاحص، بسلسلته. -/
def qaidaMurakhkhasa (q : _root_.Qaida.Qaida P) (aslB : P → Bool)
    (iqtirah : W → M → Option (_root_.Qaida.Iddia P)) : Qaida W M (_root_.Qaida.Iddia P) where
  qis w m := match iqtirah w m with
    | some c => if _root_.Qaida.maqbul q aslB c = true then some c else none
    | none => none

theorem aqliyya_maqbula (t : W → M → Bool) (q : _root_.Qaida.Qaida P) (aslB : P → Bool)
    (iqtirah : W → M → Option (_root_.Qaida.Iddia P)) (a : Arkan W M) :
    ∀ c ∈ aqliyya t (qaidaMurakhkhasa q aslB iqtirah) a, _root_.Qaida.maqbul q aslB c = true := by
  intro c hc
  obtain ⟨w, m, _, _, _, hq⟩ := kull_hukm_min_alqaida t _ a c hc
  simp only [qaidaMurakhkhasa] at hq
  split at hq
  · split at hq
    · rename_i c' _ hm
      cases hq
      exact hm
    · cases hq
  · cases hq

theorem aqliyya_murakhkhasa (t : W → M → Bool) (q : _root_.Qaida.Qaida P) (aslB : P → Bool)
    (iqtirah : W → M → Option (_root_.Qaida.Iddia P)) (a : Arkan W M) :
    ∀ c ∈ aqliyya t (qaidaMurakhkhasa q aslB iqtirah) a,
      _root_.Qaida.Murakhkhas q (fun y => aslB y = true) c.qawl :=
  fun c hc => _root_.Qaida.maqbul_murakhkhas q aslB c (aqliyya_maqbula t q aslB iqtirah a c hc)

/-- أحكامُ العقليّة بهذه القاعدة تُعبَّأ في جوابٍ واحدٍ بالقاعدة q. -/
theorem aqliyya_jawab (t : W → M → Bool) (q : _root_.Qaida.Qaida P) (aslB : P → Bool)
    (iqtirah : W → M → Option (_root_.Qaida.Iddia P)) (a : Arkan W M) :
    ∃ j : _root_.Qaida.Jawab q aslB, j.iddiaat = aqliyya t (qaidaMurakhkhasa q aslB iqtirah) a :=
  ⟨⟨aqliyya t (qaidaMurakhkhasa q aslB iqtirah) a,
    List.all_eq_true.mpr (aqliyya_maqbula t q aslB iqtirah a)⟩, rfl⟩

/-- إن لم يقبل الفاحصُ شيئًا ممّا يُقترح فلا حكمَ أصلًا. -/
theorem iqtirah_la_yahkum (t : W → M → Bool) (q : _root_.Qaida.Qaida P) (aslB : P → Bool)
    (iqtirah : W → M → Option (_root_.Qaida.Iddia P)) (a : Arkan W M)
    (h : ∀ w m c, iqtirah w m = some c → _root_.Qaida.maqbul q aslB c = false) :
    aqliyya t (qaidaMurakhkhasa q aslB iqtirah) a = [] := by
  rcases ha : aqliyya t (qaidaMurakhkhasa q aslB iqtirah) a with _ | ⟨c, cs⟩
  · rfl
  · exfalso
    have hc : c ∈ aqliyya t (qaidaMurakhkhasa q aslB iqtirah) a := by rw [ha]; exact List.mem_cons_self
    obtain ⟨w, m, _, _, _, hq⟩ := kull_hukm_min_alqaida t _ a c hc
    simp only [qaidaMurakhkhasa] at hq
    split at hq
    · rename_i c' hi
      split at hq
      · rename_i hm
        rw [h w m c' hi] at hm
        cases hm
      · cases hq
    · cases hq

end Murakhkhasa

/-- شاهدٌ على قاعدة `Qaida.qShahid` (مثالٌ مبنيٌّ للبرهان): الواقعُ واحد، والمعلومتان «الإنسان» و«الحيوان»، والدماغُ يقترح
    لـ«الإنسان» سلسلةً يقبلها الفاحص، ولـ«الحيوان» سلسلةً أصلُها غيرُ مودَع. فيخرج الحكمُ الأوّل بسلسلته، ولا يخرج الثاني. -/
def wMurakhkhas : Arkan Unit String := ⟨some (), true, true, ["الإنسان", "الحيوان"]⟩
def iqtirahShahid : Unit → String → Option (_root_.Qaida.Iddia String)
  | (), "الإنسان" => some ⟨"الحيوان", [.asl "الإنسان", .qanun 0]⟩
  | (), _ => some ⟨"الحيوان", [.asl "الحيوان"]⟩
def tKull : Unit → String → Bool := fun _ _ => true

theorem shahid_aqliyya_murakhkhasa :
    (aqliyya tKull (qaidaMurakhkhasa _root_.Qaida.qShahid _root_.Qaida.aslShahid iqtirahShahid) wMurakhkhas).map
      (fun c => (c.qawl, c.silsila.length)) = [("الحيوان", 2)] := by decide

end Aql
