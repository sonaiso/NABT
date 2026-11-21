/-
  Aql/Qaida.lean — قاعدة المحرّك: جبرٌ مرخَّص تدريجيًّا، واحد، له إصدار.

  السند: ج1 29 (العقلية ربطٌ مقيسٌ إلى قاعدة)، ج1 57 (تعدّد القواعد يُفقد اللون)،
  وقرار المالك (15 أكتوبر 2026): أن يكون الحكم كلّه جبريًّا مرخَّصًا.

  التصميم:
  * القاعدة = إصدار + قائمة قوانين مسمّاة. القانون: اسم، ومقدّمات، ونتيجة.
  * المرخَّص = ما كان أصلًا مودَعًا، أو نتيجةَ قانونٍ من القاعدة مقدّماته كلّها مرخَّصة.
  * البرهان = سلسلة خطوات (أصل، أو تطبيق قانون برقمه). `fahs` يفحصها آليًّا.
    مبرهنة `fahs_sahih`: ما قبله الفاحص مرخَّصٌ حقًّا. فكلّ ادّعاء في الجواب يحمل سلسلته،
    ويعيد فحصَها أيُّ أحدٍ بالفاحص نفسه — وهذا هو «الجواب المتتبَّع».
  * الجواب مفهرَس بالقاعدة في نوعه: `Jawab q` لا يحوي إلّا أحكامًا بالقاعدة q،
    فخلط قاعدتين في جواب واحد لا يُكتب أصلًا (ج1 57).
  * التدرّج: كلّ قانون مقدّماته أدنى رتبةً من نتيجته؛ فما كان في الرتبة صفر لا يكون إلّا أصلًا.
  * الخطوةُ بمحتوى القانون (2026-10-21): `fahsM` يكافئ `fahs` في اللقطة الواحدة في الاتّجاهين، وما قبله يبقى
    مقبولًا بزيادة القوانين وإعادة ترتيبها.
  * الفاحصُ على مصفوفة القوانين (آخر الملفّ، س1، 2026-10-24): `maqbulA` هو `maqbul` حين تكون القائمةُ قائمةَ المصفوفة
    (`tatbiqA_eq`، `fahsA_eq`، `maqbulA_eq`)؛ يأخذ القانون بموضعه في زمنٍ ثابت، وبه يُنفَّذ الفاحص التنفيذيّ.
  بلا sorry ولا axiom ولا native_decide.
-/
namespace Qaida

variable {P : Type}

structure Qanun (P : Type) where
  ism        : String
  muqaddimat : List P
  natija     : P
deriving DecidableEq, Repr

structure Qaida (P : Type) where
  isdar   : String
  qawanin : List (Qanun P)

/-- المرخَّص في القاعدة q على أصولٍ A. -/
inductive Murakhkhas (q : Qaida P) (A : P → Prop) : P → Prop
  | asl {p : P} : A p → Murakhkhas q A p
  | qanun (r : Qanun P) : r ∈ q.qawanin →
      (∀ m ∈ r.muqaddimat, Murakhkhas q A m) → Murakhkhas q A r.natija

/-! ## البرهان سلسلةً، والفاحص -/

inductive Khatwa (P : Type)
  | asl (p : P)
  | qanun (i : Nat)

variable [DecidableEq P]

/-- خطوة واحدة على ما ثبت: تُقبل أو تُرفض. -/
def tatbiq (q : Qaida P) (aslB : P → Bool) (thabit : List P) : Khatwa P → Option (List P)
  | .asl p => if aslB p then some (thabit ++ [p]) else none
  | .qanun i =>
    match q.qawanin[i]? with
    | none => none
    | some r => if r.muqaddimat.all (fun m => decide (m ∈ thabit)) then some (thabit ++ [r.natija]) else none

/-- الفاحص: يمرّ على الخطوات بالترتيب. -/
def fahs (q : Qaida P) (aslB : P → Bool) : List P → List (Khatwa P) → Option (List P)
  | thabit, [] => some thabit
  | thabit, k :: ks =>
    match tatbiq q aslB thabit k with
    | none => none
    | some t => fahs q aslB t ks

theorem tatbiq_sahih (q : Qaida P) (aslB : P → Bool) (thabit out : List P) (k : Khatwa P)
    (hth : ∀ x ∈ thabit, Murakhkhas q (fun y => aslB y = true) x)
    (h : tatbiq q aslB thabit k = some out) :
    ∀ x ∈ out, Murakhkhas q (fun y => aslB y = true) x := by
  cases k with
  | asl p =>
    simp only [tatbiq] at h
    split at h
    · rename_i hp
      cases h
      intro x hx
      rcases List.mem_append.mp hx with hx | hx
      · exact hth x hx
      · simp at hx; subst hx; exact Murakhkhas.asl hp
    · cases h
  | qanun i =>
    simp only [tatbiq] at h
    split at h
    · cases h
    · rename_i r hr
      split at h
      · rename_i hall
        cases h
        intro x hx
        rcases List.mem_append.mp hx with hx | hx
        · exact hth x hx
        · simp at hx; subst hx
          refine Murakhkhas.qanun r (List.mem_of_getElem? hr) ?_
          intro m hm
          have := List.all_eq_true.mp hall m hm
          exact hth m (of_decide_eq_true this)
      · cases h

/-- سلامة الفاحص: كلّ ما قبله مرخَّص حقًّا. -/
theorem fahs_sahih (q : Qaida P) (aslB : P → Bool) :
    ∀ (ks : List (Khatwa P)) (thabit out : List P),
    (∀ x ∈ thabit, Murakhkhas q (fun y => aslB y = true) x) →
    fahs q aslB thabit ks = some out →
    ∀ x ∈ out, Murakhkhas q (fun y => aslB y = true) x := by
  intro ks
  induction ks with
  | nil => intro thabit out hth h; simp [fahs] at h; subst h; exact hth
  | cons k ks ih =>
    intro thabit out hth h
    simp only [fahs] at h
    split at h
    · cases h
    · rename_i t ht
      exact ih t out (tatbiq_sahih q aslB thabit t k hth ht) h

/-! ## الجواب المتتبَّع، مفهرَسًا بالقاعدة -/

/-- ادّعاء مع سلسلته. -/
structure Iddia (P : Type) where
  qawl    : P
  silsila : List (Khatwa P)

/-- الادّعاء مقبول إن قبل الفاحصُ سلسلتَه من لا شيء، وكان القول بين ما ثبت. -/
def maqbul (q : Qaida P) (aslB : P → Bool) (c : Iddia P) : Bool :=
  match fahs q aslB [] c.silsila with
  | none => false
  | some out => decide (c.qawl ∈ out)

/-- كلّ ادّعاء مقبول مرخَّصٌ في القاعدة. -/
theorem maqbul_murakhkhas (q : Qaida P) (aslB : P → Bool) (c : Iddia P)
    (h : maqbul q aslB c = true) : Murakhkhas q (fun y => aslB y = true) c.qawl := by
  unfold maqbul at h
  split at h
  · cases h
  · rename_i out hout
    exact fahs_sahih q aslB c.silsila [] out (by simp) hout c.qawl (of_decide_eq_true h)

/-- الجواب بالقاعدة q: ادّعاءات، كلّها مقبولة بالفاحص على هذه القاعدة وحدها. -/
structure Jawab (q : Qaida P) (aslB : P → Bool) where
  iddiaat : List (Iddia P)
  kulluha : iddiaat.all (maqbul q aslB) = true

/-- ضمّ جوابين بالقاعدة نفسها جوابٌ بها. ولا دالّة تضمّ جوابين بقاعدتين. -/
def damm {q : Qaida P} {aslB : P → Bool} (a b : Jawab q aslB) : Jawab q aslB :=
  ⟨a.iddiaat ++ b.iddiaat, by simp [List.all_append, a.kulluha, b.kulluha]⟩

/-- كلّ قولٍ في الجواب مرخَّص. -/
theorem jawab_sahih {q : Qaida P} {aslB : P → Bool} (j : Jawab q aslB) :
    ∀ c ∈ j.iddiaat, Murakhkhas q (fun y => aslB y = true) c.qawl := by
  intro c hc
  exact maqbul_murakhkhas q aslB c (List.all_eq_true.mp j.kulluha c hc)

/-! ## الإصدار والتدرّج -/

omit [DecidableEq P] in
/-- إضافة قوانين في إصدار لاحق لا تُسقط ما رُخِّص في السابق. -/
theorem ziyada_la_tusqit (q q' : Qaida P) (A : P → Prop)
    (hsub : ∀ r ∈ q.qawanin, r ∈ q'.qawanin) {p : P} (h : Murakhkhas q A p) : Murakhkhas q' A p := by
  induction h with
  | asl ha => exact Murakhkhas.asl ha
  | qanun r hr _ ih => exact Murakhkhas.qanun r (hsub r hr) ih

/-- القاعدة متدرّجة: مقدّمات كلّ قانون أدنى رتبةً من نتيجته، ولا قانون بلا مقدّمة. -/
def Mutadarrija (q : Qaida P) (rutba : P → Nat) : Prop :=
  ∀ r ∈ q.qawanin, r.muqaddimat ≠ [] ∧ ∀ m ∈ r.muqaddimat, rutba m < rutba r.natija

omit [DecidableEq P] in
/-- في القاعدة المتدرّجة، ما رتبته صفر لا يُرخَّص إلّا أصلًا مودَعًا. -/
theorem rutba_sifr_asl (q : Qaida P) (rutba : P → Nat) (A : P → Prop)
    (hq : Mutadarrija q rutba) {p : P} (h : Murakhkhas q A p) (h0 : rutba p = 0) : A p := by
  cases h with
  | asl ha => exact ha
  | qanun r hr _ =>
    obtain ⟨hne, hlt⟩ := hq r hr
    obtain ⟨m, hm⟩ := List.exists_mem_of_ne_nil _ hne
    have := hlt m hm
    omega

/-- التدرّج الضعيف: لا قانون بلا مقدّمة، ولا قانون نتيجته في الرتبة صفر، ومقدّماته لا تعلو نتيجته.
    يكفي لحفظ الرتبة صفر للأصول، ويسمح بقوانين تنقل داخل الرتبة الواحدة (كتعدية الاحتواء). -/
def MutadarrijaDaifa (q : Qaida P) (rutba : P → Nat) : Prop :=
  ∀ r ∈ q.qawanin, r.muqaddimat ≠ [] ∧ 0 < rutba r.natija ∧ ∀ m ∈ r.muqaddimat, rutba m ≤ rutba r.natija

omit [DecidableEq P] in
theorem mutadarrija_daifa (q : Qaida P) (rutba : P → Nat) (h : Mutadarrija q rutba) :
    MutadarrijaDaifa q rutba := by
  intro r hr
  obtain ⟨hne, hlt⟩ := h r hr
  refine ⟨hne, ?_, fun m hm => Nat.le_of_lt (hlt m hm)⟩
  obtain ⟨m, hm⟩ := List.exists_mem_of_ne_nil _ hne
  have := hlt m hm
  omega

omit [DecidableEq P] in
/-- وفي القاعدة المتدرّجة ضعيفًا أيضًا، ما رتبته صفر لا يُرخَّص إلّا أصلًا. -/
theorem rutba_sifr_asl_daifa (q : Qaida P) (rutba : P → Nat) (A : P → Prop)
    (hq : MutadarrijaDaifa q rutba) {p : P} (h : Murakhkhas q A p) (h0 : rutba p = 0) : A p := by
  cases h with
  | asl ha => exact ha
  | qanun r hr _ =>
    obtain ⟨_, hpos, _⟩ := hq r hr
    omega

/-! ## شاهد: قاعدة صغيرة بقانون واحد «الإنسان ⊢ الحيوان» (تضمّن)، وأصل «الإنسان» -/

def qShahid : Qaida String := ⟨"شاهد-1", [⟨"تضمّن-الإنسان", ["الإنسان"], "الحيوان"⟩]⟩
def aslShahid (p : String) : Bool := p == "الإنسان"

/-- سلسلة صحيحة: أصل ثم القانون رقم 0 — يقبلها الفاحص. -/
theorem shahid_maqbul : maqbul qShahid aslShahid ⟨"الحيوان", [.asl "الإنسان", .qanun 0]⟩ = true := by decide

/-- القانون قبل مقدّمته — يرفضها الفاحص. -/
theorem shahid_marfud_tartib : maqbul qShahid aslShahid ⟨"الحيوان", [.qanun 0, .asl "الإنسان"]⟩ = false := by decide

/-- أصلٌ غير مودَع — يرفضه الفاحص. -/
theorem shahid_marfud_asl : maqbul qShahid aslShahid ⟨"الحيوان", [.asl "الحيوان"]⟩ = false := by decide

/-! ## الخطوةُ بمحتوى القانون لا برقمه (قرار المالك 2026-10-21، 09:51)

  `Khatwa.qanun i` تسمّي القانونَ بموضعه في `q.qawanin`. فإن أُدرج قانونٌ قبله في إصدارٍ لاحق، أشار الرقمُ نفسُه إلى غيره،
  فقد تُرفض السلسلةُ المخزونة مع أنّ ما رخّصته باقٍ مرخَّصًا: `ziyada_la_tusqit` على `Murakhkhas` لا على السلسلة. شاهدُه
  `shahid_raqm_yabtul`. أمّا `KhatwaM.qanun r` فتسمّيه بمحتواه (اسمِه ومقدّماتِه ونتيجتِه)، ويقبلها `fahsM` إن كان r في القاعدة.

  **فاحصان متكافئان في اللقطة الواحدة** (تعريفان بعوديّتين مستقلّتين، ولكلٍّ سلامتُه): السلسلةُ بالأرقام هي السلسلةُ بالمحتوى
  مقروءةً في لقطة القاعدة (`tatbiq_tarjama`، `fahs_tarjama`، `fahs_tarjama_none`، `maqbul_tarjama`)؛ وكلُّ سلسلةٍ بالمحتوى يقبلها
  `fahsM` هي قراءةُ سلسلةٍ بالأرقام يقبلها `fahs` في اللقطة نفسها (`tatbiqM_min_tatbiq`، `fahsM_min_fahs`، `maqbulM_min_maqbul`)؛
  فما يُقبل من الأقوال فيهما واحد (`maqbul_takafu`). وسلامةُ `fahsM` كسلامة `fahs` (`fahsM_sahih`، `maqbulM_murakhkhas`).
  **وما يزيده المحتوى:** السلسلةُ المقبولة تبقى مقبولةً في كلّ قاعدةٍ تحوي قوانينَ الأولى كلَّها، بأيّ ترتيبٍ وبأيّ إصدار
  (`fahsM_ihtiwa`، `maqbulM_ihtiwa`، `maqbulM_tartib`)؛ وكلُّ سلسلةٍ بالأرقام قُبلت في لقطةٍ لها قراءةٌ بالمحتوى مقبولةٌ في كلّ قاعدةٍ
  تحوي قوانينَ تلك اللقطة كلَّها (`maqbul_naql`).

  **ما لا يتغيّر هنا:** المخزنُ القائم (`mawsua/makhzan.tsv`، الخطوة `q=i`) والفاحصُ التنفيذيّ يبقيان بالأرقام، صحيحَين نسبةً إلى
  لقطتهما المختومة (`mawsua/makhzan.sha256`). ونقلُ التخزين إلى المحتوى مقترحُ البنّاء (في الإصدار ٤ من الخطّة، طلبُ دمجٍ منفصل)، يُقرّره
  المالك مع جدول القواعد (§١٠) وختمِه؛ فإن قُرّر كان فاحصُ الجدول `fahsM`، ويكافئ `fahs` في اللقطة (`maqbul_takafu`). و`Mawsua.quwwatSilsila` تأخذ قوّة القانون برقمه (`qW : Nat → Wasm`)؛ وقراءتُها بالمحتوى لم تُبنَ.
-/

/-- خطوةٌ تسمّي القانونَ بمحتواه. -/
inductive KhatwaM (P : Type)
  | asl (p : P)
  | qanun (r : Qanun P)
deriving DecidableEq, Repr

/-- خطوةٌ بالمحتوى على ما ثبت: القانونُ من القاعدة، ومقدّماتُه كلُّها ثابتة. -/
def tatbiqM (q : Qaida P) (aslB : P → Bool) (thabit : List P) : KhatwaM P → Option (List P)
  | .asl p => if aslB p = true then some (thabit ++ [p]) else none
  | .qanun r =>
    if decide (r ∈ q.qawanin) && r.muqaddimat.all (fun m => decide (m ∈ thabit)) then some (thabit ++ [r.natija])
    else none

/-- الفاحصُ على الخطوات بالمحتوى، بالترتيب. -/
def fahsM (q : Qaida P) (aslB : P → Bool) : List P → List (KhatwaM P) → Option (List P)
  | thabit, [] => some thabit
  | thabit, k :: ks =>
    match tatbiqM q aslB thabit k with
    | none => none
    | some t => fahsM q aslB t ks

/-- ادّعاءٌ مع سلسلته بالمحتوى. -/
structure IddiaM (P : Type) where
  qawl    : P
  silsila : List (KhatwaM P)

def maqbulM (q : Qaida P) (aslB : P → Bool) (c : IddiaM P) : Bool :=
  match fahsM q aslB [] c.silsila with
  | none => false
  | some out => decide (c.qawl ∈ out)

theorem tatbiqM_sahih (q : Qaida P) (aslB : P → Bool) (thabit out : List P) (k : KhatwaM P)
    (hth : ∀ x ∈ thabit, Murakhkhas q (fun y => aslB y = true) x)
    (h : tatbiqM q aslB thabit k = some out) :
    ∀ x ∈ out, Murakhkhas q (fun y => aslB y = true) x := by
  cases k with
  | asl p =>
    simp only [tatbiqM] at h
    split at h
    · rename_i hp
      cases h
      intro x hx
      rcases List.mem_append.mp hx with hx | hx
      · exact hth x hx
      · simp at hx; subst hx; exact Murakhkhas.asl hp
    · cases h
  | qanun r =>
    simp only [tatbiqM] at h
    split at h
    · rename_i hc
      cases h
      rw [Bool.and_eq_true] at hc
      obtain ⟨hr, hall⟩ := hc
      intro x hx
      rcases List.mem_append.mp hx with hx | hx
      · exact hth x hx
      · simp at hx; subst hx
        refine Murakhkhas.qanun r (of_decide_eq_true hr) ?_
        intro m hm
        exact hth m (of_decide_eq_true (List.all_eq_true.mp hall m hm))
    · cases h

/-- سلامةُ الفاحص بالمحتوى: كلُّ ما قبله مرخَّص. -/
theorem fahsM_sahih (q : Qaida P) (aslB : P → Bool) :
    ∀ (ks : List (KhatwaM P)) (thabit out : List P),
    (∀ x ∈ thabit, Murakhkhas q (fun y => aslB y = true) x) →
    fahsM q aslB thabit ks = some out →
    ∀ x ∈ out, Murakhkhas q (fun y => aslB y = true) x := by
  intro ks
  induction ks with
  | nil => intro thabit out hth h; simp [fahsM] at h; subst h; exact hth
  | cons k ks ih =>
    intro thabit out hth h
    simp only [fahsM] at h
    split at h
    · cases h
    · rename_i t ht
      exact ih t out (tatbiqM_sahih q aslB thabit t k hth ht) h

theorem maqbulM_murakhkhas (q : Qaida P) (aslB : P → Bool) (c : IddiaM P)
    (h : maqbulM q aslB c = true) : Murakhkhas q (fun y => aslB y = true) c.qawl := by
  unfold maqbulM at h
  split at h
  · cases h
  · rename_i out hout
    exact fahsM_sahih q aslB c.silsila [] out (by simp) hout c.qawl (of_decide_eq_true h)

/-- قراءةُ خطوةٍ بالرقم في لقطة القاعدة q: الرقمُ اسمٌ للقانون الذي في موضعه، ولا قراءةَ لرقمٍ خارج القائمة. -/
def tarjama (q : Qaida P) : Khatwa P → Option (KhatwaM P)
  | .asl p => some (.asl p)
  | .qanun i => q.qawanin[i]?.map KhatwaM.qanun

def tarjamaKull (q : Qaida P) : List (Khatwa P) → Option (List (KhatwaM P))
  | [] => some []
  | k :: ks =>
    match tarjama q k, tarjamaKull q ks with
    | some k', some ks' => some (k' :: ks')
    | _, _ => none

/-- الخطوةُ بالرقم هي الخطوةُ بالمحتوى مقروءةً في لقطتها. -/
theorem tatbiq_tarjama (q : Qaida P) (aslB : P → Bool) (thabit : List P) (k : Khatwa P) :
    tatbiq q aslB thabit k = match tarjama q k with
      | none => none
      | some k' => tatbiqM q aslB thabit k' := by
  cases k with
  | asl p => simp [tatbiq, tarjama, tatbiqM]
  | qanun i =>
    simp only [tatbiq, tarjama]
    cases hr : q.qawanin[i]? with
    | none => rfl
    | some r =>
      have hm : r ∈ q.qawanin := List.mem_of_getElem? hr
      simp [tatbiqM, hm]

/-- والسلسلةُ بالأرقام هي السلسلةُ بالمحتوى مقروءةً في لقطتها. -/
theorem fahs_tarjama (q : Qaida P) (aslB : P → Bool) :
    ∀ (ks : List (Khatwa P)) (ks' : List (KhatwaM P)) (thabit : List P),
    tarjamaKull q ks = some ks' → fahs q aslB thabit ks = fahsM q aslB thabit ks' := by
  intro ks
  induction ks with
  | nil => intro ks' thabit h; simp [tarjamaKull] at h; subst h; rfl
  | cons k ks ih =>
    intro ks' thabit h
    simp only [tarjamaKull] at h
    split at h
    · rename_i k' ks'' hk hks
      cases h
      have ht : tatbiq q aslB thabit k = tatbiqM q aslB thabit k' := by
        rw [tatbiq_tarjama, hk]
      simp only [fahs, fahsM, ht]
      cases tatbiqM q aslB thabit k' with
      | none => rfl
      | some t => exact ih ks'' t hks
    · cases h

/-- وما لا يُقرأ في اللقطة لا يقبله الفاحص بالأرقام أيضًا. -/
theorem fahs_tarjama_none (q : Qaida P) (aslB : P → Bool) :
    ∀ (ks : List (Khatwa P)) (thabit : List P),
    tarjamaKull q ks = none → fahs q aslB thabit ks = none := by
  intro ks
  induction ks with
  | nil => intro thabit h; simp [tarjamaKull] at h
  | cons k ks ih =>
    intro thabit h
    simp only [fahs, tatbiq_tarjama]
    cases hk : tarjama q k with
    | none => rfl
    | some k' =>
      dsimp only
      cases ht : tatbiqM q aslB thabit k' with
      | none => rfl
      | some t =>
        apply ih t
        simp only [tarjamaKull, hk] at h
        cases hks : tarjamaKull q ks with
        | none => rfl
        | some ks'' => simp [hks] at h

/-- قبولُ الادّعاء بالأرقام هو قبولُه بالمحتوى في اللقطة نفسِها. -/
theorem maqbul_tarjama (q : Qaida P) (aslB : P → Bool) (c : Iddia P) :
    maqbul q aslB c = match tarjamaKull q c.silsila with
      | none => false
      | some ks' => maqbulM q aslB ⟨c.qawl, ks'⟩ := by
  cases h : tarjamaKull q c.silsila with
  | none => simp [maqbul, fahs_tarjama_none q aslB c.silsila [] h]
  | some ks' => simp [maqbul, maqbulM, fahs_tarjama q aslB c.silsila ks' [] h]

theorem tatbiqM_ihtiwa (q q' : Qaida P) (aslB : P → Bool) (hsub : ∀ r ∈ q.qawanin, r ∈ q'.qawanin)
    (thabit out : List P) (k : KhatwaM P) (h : tatbiqM q aslB thabit k = some out) :
    tatbiqM q' aslB thabit k = some out := by
  cases k with
  | asl p => simpa [tatbiqM] using h
  | qanun r =>
    simp only [tatbiqM] at h ⊢
    split at h
    · rename_i hc
      rw [Bool.and_eq_true] at hc
      have hc' : (decide (r ∈ q'.qawanin) && r.muqaddimat.all (fun m => decide (m ∈ thabit))) = true := by
        rw [Bool.and_eq_true]
        exact ⟨decide_eq_true (hsub r (of_decide_eq_true hc.1)), hc.2⟩
      simp only [hc', ↓reduceIte]
      exact h
    · cases h

/-- السلسلةُ المقبولة بالمحتوى تبقى مقبولةً في كلّ قاعدةٍ تحوي قوانينَ الأولى، بأيّ ترتيبٍ وبأيّ إصدار. -/
theorem fahsM_ihtiwa (q q' : Qaida P) (aslB : P → Bool) (hsub : ∀ r ∈ q.qawanin, r ∈ q'.qawanin) :
    ∀ (ks : List (KhatwaM P)) (thabit out : List P),
    fahsM q aslB thabit ks = some out → fahsM q' aslB thabit ks = some out := by
  intro ks
  induction ks with
  | nil => intro thabit out h; simpa [fahsM] using h
  | cons k ks ih =>
    intro thabit out h
    simp only [fahsM] at h ⊢
    split at h
    · cases h
    · rename_i t ht
      rw [tatbiqM_ihtiwa q q' aslB hsub thabit t k ht]
      exact ih t out h

theorem maqbulM_ihtiwa (q q' : Qaida P) (aslB : P → Bool) (hsub : ∀ r ∈ q.qawanin, r ∈ q'.qawanin)
    (c : IddiaM P) (h : maqbulM q aslB c = true) : maqbulM q' aslB c = true := by
  unfold maqbulM at h ⊢
  split at h
  · cases h
  · rename_i out hout
    rw [fahsM_ihtiwa q q' aslB hsub c.silsila [] out hout]
    exact h

/-- قاعدتان قوانينُهما واحدة بأيّ ترتيب: القبولُ بالمحتوى فيهما واحد. -/
theorem maqbulM_tartib (q q' : Qaida P) (aslB : P → Bool)
    (hq : ∀ r, r ∈ q.qawanin ↔ r ∈ q'.qawanin) (c : IddiaM P) :
    maqbulM q aslB c = maqbulM q' aslB c := by
  cases h : maqbulM q aslB c with
  | true => exact (maqbulM_ihtiwa q q' aslB (fun r hr => (hq r).1 hr) c h).symm
  | false =>
    cases h' : maqbulM q' aslB c with
    | false => rfl
    | true =>
      have := maqbulM_ihtiwa q' q aslB (fun r hr => (hq r).2 hr) c h'
      rw [h] at this
      cases this

/-- **النقل:** كلُّ ادّعاءٍ بالأرقام قُبل في لقطةٍ له قراءةٌ بالمحتوى فيها، مقبولةٌ في كلّ قاعدةٍ تحوي قوانينَها. -/
theorem maqbul_naql (q : Qaida P) (aslB : P → Bool) (c : Iddia P) (h : maqbul q aslB c = true) :
    ∃ ks', tarjamaKull q c.silsila = some ks' ∧
      ∀ q' : Qaida P, (∀ r ∈ q.qawanin, r ∈ q'.qawanin) → maqbulM q' aslB ⟨c.qawl, ks'⟩ = true := by
  rw [maqbul_tarjama] at h
  cases hk : tarjamaKull q c.silsila with
  | none => rw [hk] at h; cases h
  | some ks' =>
    rw [hk] at h
    exact ⟨ks', rfl, fun q' hsub => maqbulM_ihtiwa q q' aslB hsub _ h⟩

/-- **العكس، خطوةً:** كلُّ خطوةٍ بالمحتوى يقبلها `tatbiqM` قراءةٌ لخطوةٍ بالرقم يقبلها `tatbiq` في اللقطة نفسها. -/
theorem tatbiqM_min_tatbiq (q : Qaida P) (aslB : P → Bool) (thabit out : List P) (k' : KhatwaM P)
    (h : tatbiqM q aslB thabit k' = some out) :
    ∃ k, tarjama q k = some k' ∧ tatbiq q aslB thabit k = some out := by
  cases k' with
  | asl p =>
    refine ⟨.asl p, rfl, ?_⟩
    rw [tatbiq_tarjama]
    exact h
  | qanun r =>
    have hr : r ∈ q.qawanin := by
      simp only [tatbiqM] at h
      split at h
      · rename_i hc
        rw [Bool.and_eq_true] at hc
        exact of_decide_eq_true hc.1
      · cases h
    obtain ⟨i, hi⟩ := List.mem_iff_getElem?.mp hr
    have ht : tarjama q (.qanun i) = some (.qanun r) := by simp [tarjama, hi]
    refine ⟨.qanun i, ht, ?_⟩
    rw [tatbiq_tarjama, ht]
    exact h

/-- **العكس، سلسلةً:** كلُّ سلسلةٍ بالمحتوى يقبلها `fahsM` قراءةٌ لسلسلةٍ بالأرقام يقبلها `fahs` في اللقطة نفسها. -/
theorem fahsM_min_fahs (q : Qaida P) (aslB : P → Bool) :
    ∀ (ks' : List (KhatwaM P)) (thabit out : List P),
    fahsM q aslB thabit ks' = some out →
    ∃ ks, tarjamaKull q ks = some ks' ∧ fahs q aslB thabit ks = some out := by
  intro ks'
  induction ks' with
  | nil => intro thabit out h; exact ⟨[], rfl, h⟩
  | cons k' ks' ih =>
    intro thabit out h
    simp only [fahsM] at h
    split at h
    · cases h
    · rename_i t ht
      obtain ⟨k, hk, htk⟩ := tatbiqM_min_tatbiq q aslB thabit t k' ht
      obtain ⟨ks, hks, hf⟩ := ih t out h
      refine ⟨k :: ks, ?_, ?_⟩
      · simp [tarjamaKull, hk, hks]
      · simp only [fahs, htk]
        exact hf

theorem maqbulM_min_maqbul (q : Qaida P) (aslB : P → Bool) (c' : IddiaM P) (h : maqbulM q aslB c' = true) :
    ∃ c : Iddia P, c.qawl = c'.qawl ∧ tarjamaKull q c.silsila = some c'.silsila ∧ maqbul q aslB c = true := by
  unfold maqbulM at h
  split at h
  · cases h
  · rename_i out hout
    obtain ⟨ks, hks, hf⟩ := fahsM_min_fahs q aslB c'.silsila [] out hout
    refine ⟨⟨c'.qawl, ks⟩, rfl, hks, ?_⟩
    simp only [maqbul, hf]
    exact h

/-- **التكافؤ في اللقطة:** القولُ مقبولٌ بسلسلةٍ بالأرقام إن وفقط إن كان مقبولًا بسلسلةٍ بالمحتوى، في القاعدة نفسها. -/
theorem maqbul_takafu (q : Qaida P) (aslB : P → Bool) (p : P) :
    (∃ ks, maqbul q aslB ⟨p, ks⟩ = true) ↔ (∃ ks', maqbulM q aslB ⟨p, ks'⟩ = true) := by
  constructor
  · rintro ⟨ks, h⟩
    rw [maqbul_tarjama] at h
    cases hk : tarjamaKull q ks with
    | none => rw [hk] at h; cases h
    | some ks' => rw [hk] at h; exact ⟨ks', h⟩
  · rintro ⟨ks', h⟩
    obtain ⟨⟨qawl, sil⟩, hc, _, hm⟩ := maqbulM_min_maqbul q aslB ⟨p, ks'⟩ h
    simp only at hc
    subst hc
    exact ⟨sil, hm⟩

/-- مثالٌ مبنيٌّ للبرهان (لا قولٌ لغويٌّ مودَع): الإصدارُ الثاني يُدرج قانونًا قبل قانون `qShahid`. -/
def qShahid2 : Qaida String :=
  ⟨"شاهد-2", [⟨"تضمّن-الحيوان", ["الحيوان"], "الجسم"⟩, ⟨"تضمّن-الإنسان", ["الإنسان"], "الحيوان"⟩]⟩

/-- السلسلةُ بالرقم التي قُبلت في الإصدار الأوّل (`shahid_maqbul`) تُرفض في الثاني: الرقمُ 0 صار قانونًا آخر. -/
theorem shahid_raqm_yabtul :
    maqbul qShahid2 aslShahid ⟨"الحيوان", [.asl "الإنسان", .qanun 0]⟩ = false := by decide

/-- وقراءتُها بالمحتوى في الإصدار الأوّل مقبولةٌ في الإصدارين. -/
theorem shahid_muhtawa_yabqa :
    tarjamaKull qShahid [.asl "الإنسان", .qanun 0] =
      some [.asl "الإنسان", .qanun ⟨"تضمّن-الإنسان", ["الإنسان"], "الحيوان"⟩] ∧
    maqbulM qShahid aslShahid ⟨"الحيوان", [.asl "الإنسان", .qanun ⟨"تضمّن-الإنسان", ["الإنسان"], "الحيوان"⟩]⟩ = true ∧
    maqbulM qShahid2 aslShahid ⟨"الحيوان", [.asl "الإنسان", .qanun ⟨"تضمّن-الإنسان", ["الإنسان"], "الحيوان"⟩]⟩ = true := by
  decide

/-! ## الفاحصُ على مصفوفة القوانين: التنفيذُ السريع مكافئًا (س1؛ قولُ المالك 2026-10-24، 18:07 «نفذ وفق افضل الممارسات»)

  `tatbiq` يأخذ القانونَ بموضعه من `q.qawanin`، وهي `List`: فالوصولُ إلى القانون i يمرّ على ما قبله، وفحصُ مخزنٍ قوانينُه
  بالآلاف يصير أبطأ من عدد ادّعاءاته. `tatbiqA` يأخذه بموضعه من `Array`، وهو هو حين تكون القائمةُ قائمةَ المصفوفة
  (`tatbiqA_eq`، `fahsA_eq`، `maqbulA_eq`، لكلّ مصفوفةٍ وقاعدةٍ بهذا الشرط). فلا فاحصَ ثانٍ: ما يقبله `maqbulA` هو ما يقبله
  `maqbul`، وسلامتُه `maqbul_murakhkhas` بإعادة الكتابة. وما يُكسب في الزمن تقديرٌ يُرصد خارج هذا الملفّ، لا مبرهنة. -/

/-- خطوةٌ على ما ثبت، والقانونُ من المصفوفة بموضعه. -/
def tatbiqA (qs : Array (Qanun P)) (aslB : P → Bool) (thabit : List P) : Khatwa P → Option (List P)
  | .asl a => if aslB a then some (thabit ++ [a]) else none
  | .qanun i =>
    match qs[i]? with
    | none => none
    | some r => if r.muqaddimat.all (fun x => decide (x ∈ thabit)) then some (thabit ++ [r.natija]) else none

/-- الفاحصُ على المصفوفة: يمرّ على الخطوات بالترتيب. -/
def fahsA (qs : Array (Qanun P)) (aslB : P → Bool) : List P → List (Khatwa P) → Option (List P)
  | thabit, [] => some thabit
  | thabit, k :: ks =>
    match tatbiqA qs aslB thabit k with
    | none => none
    | some t => fahsA qs aslB t ks

/-- القبولُ على المصفوفة. -/
def maqbulA (qs : Array (Qanun P)) (aslB : P → Bool) (c : Iddia P) : Bool :=
  match fahsA qs aslB [] c.silsila with
  | none => false
  | some out => decide (c.qawl ∈ out)

/-- الخطوةُ على المصفوفة هي الخطوةُ على القاعدة التي قائمتُها قائمةُ المصفوفة. -/
theorem tatbiqA_eq (q : Qaida P) (qs : Array (Qanun P)) (hq : q.qawanin = qs.toList) (aslB : P → Bool)
    (thabit : List P) (k : Khatwa P) : tatbiqA qs aslB thabit k = tatbiq q aslB thabit k := by
  cases k with
  | asl p => rfl
  | qanun i => simp only [tatbiqA, tatbiq, hq, Array.getElem?_toList]

/-- والسلسلةُ كذلك، من أيّ ثابتٍ بُدئ. -/
theorem fahsA_eq (q : Qaida P) (qs : Array (Qanun P)) (hq : q.qawanin = qs.toList) (aslB : P → Bool) :
    ∀ (ks : List (Khatwa P)) (thabit : List P), fahsA qs aslB thabit ks = fahs q aslB thabit ks := by
  intro ks
  induction ks with
  | nil => intro thabit; rfl
  | cons k ks ih =>
    intro thabit
    simp only [fahsA, fahs, tatbiqA_eq q qs hq]
    cases tatbiq q aslB thabit k with
    | none => rfl
    | some t => exact ih t

/-- **التكافؤ:** قبولُ الادّعاء على المصفوفة هو قبولُه بالفاحص `maqbul`. -/
theorem maqbulA_eq (q : Qaida P) (qs : Array (Qanun P)) (hq : q.qawanin = qs.toList) (aslB : P → Bool)
    (c : Iddia P) : maqbulA qs aslB c = maqbul q aslB c := by
  simp only [maqbulA, maqbul, fahsA_eq q qs hq]

end Qaida
