/-
  Madlul/Tarjih.lean — ترجيحُ معنى اللفظ عند النبهاني: الاحتمالاتُ الخمسة وأولويّاتُها العشر، وتعيينُ المعنى بالأصل والعلاقة والقرينة.

  السند: الشخصية الإسلامية ج3 (a2.docx المختوم `360f7653…`، والأسطرُ من تحويل `scripts/tahwil_docx.py`: فقرةٌ بسطر):
  * س484: «الخلل الحاصل في فهم مراد المتكلم يحصل من احتمالات خمسة وهي: الاشتراك، والنقل، والمجاز، والإضمار، والتخصيص».
  * س485: «يقع على عشرة أوجه، وضابطه أن يؤخذ كل واحد مع ما بعده».
  * س486–495: «النقل أولى من الاشتراك»، «المجاز أولى من الاشتراك»، «الإضمار أولى من الاشتراك»، «التخصيص أولى من الاشتراك»،
    «المجاز أولى من النقل»، «الإضمار أولى من النقل»، «التخصيص أولى من النقل»، «الإضمار مثل المجاز، ولا يترجح أحدهما على الآخر
    إلا بدليل»، «التخصيص أولى من المجاز»، «التخصيص أولى من الإضمار»؛ وحجّتُه في الرابع والسابع والعاشر: «الخير من الخير خير».
  * س421: «الأصل عدم الاشتراك … تعيين معنى اللفظ المشترك، وتخصيصه بأحد معانيه مفتقراً إلى قرينة»؛ س422: «يجوز استعمال المشترك في
    جميع معانيه معاً»؛ س487: المجاز «إن كان معه قرينة تدل على إرادة المجاز أعملناه فيه، وإلا أعملناه في الحقيقة».

  * مبرهن لكلّ: `khayr_min_khayr` (التعدّي)، `awla_la_yaksis` (لا يتعاكس)، `kull_zawj_marra` (العشرة كلُّ الأزواج)، و`tarjih`:
    `bila_qarina_haqiqa`، `qarina_tusrif`، `la_ishtirak_maa_alaqa`، `mushtarak_bila_qarina`.
  * على الشاهد: `ashara_awjuh` (الأوجه العشرة بأحكامها)، و«درس» (`dars_dirasa`، `dars_bila_siyaq`) بشواهد المقاييس واللسان المختومين.
  * ج3 س417: `sibawayhi_nabhani` (مبرهن لكلّ: السباعيّ يفصّل قسمة سيبويه، `Madlul/Ishtirak.lean`)، و`dars_laysa_mushtarak`.
  بلا sorry ولا axiom ولا native_decide.
-/

import Madlul.Ishtirak

namespace Tarjih

/-! ## ١. الاحتمالات الخمسة وأولويّاتها (ج3 س484–495) -/

inductive Ihtimal | ishtirak | naql | majaz | idmar | takhsis
  deriving DecidableEq, Repr

/-- رتبةُ الاحتمال: التخصيص فوق المجاز والإضمار (وهما سواء)، وهما فوق النقل، والنقل فوق الاشتراك. -/
def rutba : Ihtimal → Nat
  | .ishtirak => 0 | .naql => 1 | .majaz => 2 | .idmar => 2 | .takhsis => 3

/-- «أولى»: أعلى رتبة. -/
def awla (a b : Ihtimal) : Bool := decide (rutba b < rutba a)

/-- حكمُ الوجه: أولى، أو مثلُه («لا يترجح أحدهما على الآخر إلا بدليل»). -/
inductive Hukm | awla | mithl
  deriving DecidableEq, Repr

def hukm (a b : Ihtimal) : Option Hukm :=
  if awla a b then some .awla else if rutba a = rutba b then some .mithl else none

/-- الأوجهُ العشرة بنصّها (س486–495): (الأوّل، الثاني، الحكم). -/
def awjuh : List (Ihtimal × Ihtimal × Hukm) :=
  [(.naql, .ishtirak, .awla), (.majaz, .ishtirak, .awla), (.idmar, .ishtirak, .awla), (.takhsis, .ishtirak, .awla),
   (.majaz, .naql, .awla), (.idmar, .naql, .awla), (.takhsis, .naql, .awla), (.idmar, .majaz, .mithl),
   (.takhsis, .majaz, .awla), (.takhsis, .idmar, .awla)]

/-- الرتبةُ تعيد الأوجهَ العشرة بأحكامها بعينها. -/
theorem ashara_awjuh : awjuh.all (fun w => hukm w.1 w.2.1 == some w.2.2) = true := by decide

def khamsa : List Ihtimal := [.ishtirak, .naql, .majaz, .idmar, .takhsis]

/-- الأزواجُ غيرُ المرتّبة من الخمسة: كلُّ واحدٍ مع ما بعده. -/
def azwaj : List (Ihtimal × Ihtimal) :=
  (khamsa.zip (List.range 5)).flatMap fun p => (khamsa.drop (p.2 + 1)).map fun b => (p.1, b)

def adadFi (p : Ihtimal × Ihtimal) : Nat :=
  (awjuh.filter fun w => (w.1 == p.1 && w.2.1 == p.2) || (w.1 == p.2 && w.2.1 == p.1)).length

/-- «يؤخذ كل واحد مع ما بعده»: العشرةُ هي الأزواجُ غيرُ المرتّبة من الخمسة، كلٌّ مرّةً واحدة. -/
theorem kull_zawj_marra : azwaj.length = 10 ∧ awjuh.length = 10 ∧ azwaj.all (fun p => adadFi p == 1) = true := by decide

/-- «الخير من الخير خير»: الأولويّة متعدّية. -/
theorem khayr_min_khayr (a b c : Ihtimal) (h1 : awla a b = true) (h2 : awla b c = true) : awla a c = true := by
  unfold awla at *
  simp only [decide_eq_true_eq] at *
  omega

/-- ولا تتعاكس. -/
theorem awla_la_yaksis (a b : Ihtimal) (h : awla a b = true) : awla b a = false := by
  unfold awla at *
  simp only [decide_eq_true_eq, decide_eq_false_iff_not] at *
  omega

/-! ## ٢. تعيينُ معنى اللفظ (ج3 س421–422، س487، س548) -/

/-- معنًى للّفظ: موضوعٌ له أوّلًا (الحقيقة اللغوية — أصلُ ابن فارس)، أو مأخوذٌ منه بعلاقةٍ مشهودة (المجاز/النقل)، وقرينةٌ في السياق. -/
structure Mana where
  ism : String
  awwal : Bool
  alaqa : Bool
  qarina : Bool
  deriving DecidableEq, Repr

inductive Natija | mana (s : String) | mushtarak (l : List String) | laHukm
  deriving DecidableEq, Repr

/-- الترجيح: إن كان للّفظ معنًى أوّلٌ واحد وسائرُ معانيه مأخوذةٌ منه بعلاقة فليس مشتركًا (المجاز والنقل أولى من الاشتراك):
    بقرينةٍ تعيّن مأخوذًا واحدًا يُعمل فيه، وإلّا فالحقيقة («وإلا أعملناه في الحقيقة»)؛ وإن كان فيه معنيان فأكثرُ بلا علاقة فهو مشترك
    لا يتعيّن أحدُ معانيه إلّا بقرينة، وبقرائنَ لأكثرَ من معنًى يُستعمل فيها جميعًا. -/
def tarjih (ms : List Mana) : Natija :=
  match ms.filter (·.awwal) with
  | [a] =>
    if ms.all (fun m => m.awwal || m.alaqa) then
      match ms.filter (fun m => !m.awwal && m.qarina) with
      | [m] => .mana m.ism
      | [] => .mana a.ism
      | q => .mushtarak (q.map (·.ism))
    else
      match (ms.filter (fun m => m.awwal || !m.alaqa)).filter (·.qarina) with
      | [m] => .mana m.ism
      | [] => .mushtarak ((ms.filter (fun m => m.awwal || !m.alaqa)).map (·.ism))
      | q => .mushtarak (q.map (·.ism))
  | [] => .laHukm
  | aw =>
    match aw.filter (·.qarina) with
    | [m] => .mana m.ism
    | [] => .mushtarak (aw.map (·.ism))
    | q => .mushtarak (q.map (·.ism))

/-- **بلا قرينة فالحقيقة**: أصلٌ واحد ومعانٍ مأخوذةٌ منه بعلاقة، ولا قرينةَ لمأخوذ ← المعنى الأوّل. -/
theorem bila_qarina_haqiqa (a : Mana) (rest : List Mana) (ha : a.awwal = true)
    (hr : ∀ m ∈ rest, m.awwal = false ∧ m.alaqa = true ∧ m.qarina = false) : tarjih (a :: rest) = .mana a.ism := by
  have h1 : (a :: rest).filter (·.awwal) = [a] := by
    simp only [List.filter_cons, ha, if_true]
    congr 1
    exact List.filter_eq_nil_iff.mpr (fun m hm => by simp [(hr m hm).1])
  have h2 : (a :: rest).all (fun m => m.awwal || m.alaqa) = true := by
    simp only [List.all_cons, ha, Bool.true_or, Bool.true_and, List.all_eq_true]
    intro m hm; simp [(hr m hm).2.1]
  have h3 : (a :: rest).filter (fun m => !m.awwal && m.qarina) = [] := by
    apply List.filter_eq_nil_iff.mpr
    intro m hm
    rcases List.mem_cons.mp hm with rfl | hm
    · simp [ha]
    · simp [(hr m hm).2.2]
  unfold tarjih; rw [h1]; simp only [h2, if_true, h3]

/-- **القرينةُ تصرف إلى المأخوذ**: أصلٌ واحد ومعانٍ مأخوذةٌ بعلاقة، وقرينةٌ لمأخوذٍ واحدٍ بعينه ← هو. -/
theorem qarina_tusrif (a m : Mana) (ha : a.awwal = true) (hm : m.awwal = false ∧ m.alaqa = true ∧ m.qarina = true) :
    tarjih [a, m] = .mana m.ism := by
  obtain ⟨h1, h2, h3⟩ := hm
  simp [tarjih, ha, h1, h2, h3]

/-- **لا اشتراك مع العلاقة**: أصلٌ واحد وكلُّ ما سواه مأخوذٌ منه بعلاقة، وقرينةٌ لمأخوذٍ واحدٍ على الأكثر ← معنًى واحدٌ لا «مشترك». -/
theorem la_ishtirak_maa_alaqa (a : Mana) (rest : List Mana) (ha : a.awwal = true)
    (hr : ∀ m ∈ rest, m.awwal = false ∧ m.alaqa = true)
    (hq : ((a :: rest).filter (fun m => !m.awwal && m.qarina)).length ≤ 1) : ∃ s, tarjih (a :: rest) = .mana s := by
  have h1 : (a :: rest).filter (·.awwal) = [a] := by
    simp only [List.filter_cons, ha, if_true]
    congr 1
    exact List.filter_eq_nil_iff.mpr (fun m hm => by simp [(hr m hm).1])
  have h2 : (a :: rest).all (fun m => m.awwal || m.alaqa) = true := by
    simp only [List.all_cons, ha, Bool.true_or, Bool.true_and, List.all_eq_true]
    intro m hm; simp [(hr m hm).2]
  unfold tarjih; rw [h1]; simp only [h2, if_true]
  generalize (a :: rest).filter (fun m => !m.awwal && m.qarina) = q at hq ⊢
  match q, hq with
  | [], _ => exact ⟨a.ism, rfl⟩
  | [m], _ => exact ⟨m.ism, rfl⟩

/-- **المشتركُ بلا قرينة لا يتعيّن**: معنيان أوّلان بلا قرينة ← «مشترك» بهما. -/
theorem mushtarak_bila_qarina (a b : Mana) (ha : a.awwal = true ∧ a.qarina = false) (hb : b.awwal = true ∧ b.qarina = false) :
    tarjih [a, b] = .mushtarak [a.ism, b.ism] := by
  simp [tarjih, ha.1, ha.2, hb.1, hb.2]

/-! ## ٣. على الشاهد: «درس»

  * الأوّل: المقاييس س12989 «الدال والراء والسين أصل واحد يدل على خفاء وخفض وعفاء … يقال درس المنزل: عفا»؛ واللسان س115033
    «درس الشيء والرسم يدرس دروسا: عفا».
  * المأخوذُ بعلاقة: المقاييس س12997 «ومن الباب درست القرآن وغيره. وذلك أن الدارس يتتبع ما كان قرأ، كالسالك للطريق يتتبعه»
    (علاقةُ المشابهة، ج3 س434)؛ واللسان س115054–115055 «ودرس الكتاب يدرسه درسا ودراسة ودارسه، من ذلك، كأنه عانده حتى انقاد لحفظه».
    والمصدرُ يفرّقهما (دروس / درس ودراسة) كما فرّق سيبويه الموجدة والوجدان (الكتاب س247–251).
  * القرينة: «الكتاب» في سياق اللفظ (س115054 «ودرس الكتاب»)، وشبكةُ المالك فيها «كتب». -/

def afa (q : Bool) : Mana := ⟨"العفاء", true, false, q⟩
def dirasa (q : Bool) : Mana := ⟨"الدراسة", false, true, q⟩

/-- في سياقٍ فيه «الكتاب» (شبكةُ المالك): «درس» = الدراسة. -/
theorem dars_dirasa : tarjih [afa false, dirasa true] = .mana "الدراسة" := by decide

/-- وبلا سياق: «درس» = العفاء، الحقيقةُ الأولى؛ وليس مشتركًا في الحالين. -/
theorem dars_bila_siyaq : tarjih [afa false, dirasa false] = .mana "العفاء" ∧
    (∀ q, tarjih [afa false, dirasa q] ≠ .mushtarak ["العفاء", "الدراسة"]) := by
  refine ⟨by decide, ?_⟩
  intro q; cases q <;> decide


/-! ## ٤. تقسيمُ النبهاني السباعيّ يفصّل قسمةَ سيبويه (ج3 س417)

  ج3 س417: «ينقسم اللفظ باعتبار الدال والمدلول … إلى سبعة أقسام: هي المنفرد، والمتباين، والمترادف، والمشترك، والمنقول، والحقيقة،
  والمجاز»: اتحادُ اللفظ والمعنى منفرد، وتكثّرُهما متباين، وتكثّرُ اللفظ مع اتحاد المعنى مترادف، واتحادُ اللفظ مع تكثّر المعنى ثلاثةٌ
  بسبب المعنى الثاني: موضوعٌ له أوّلًا (مشترك)، أو منقولٌ إليه «واشتهر في المعنى الثاني» (منقول)، أو «نقل إلى غيره لعلاقة … لم
  يشتهر» (مجاز، والأوّل حقيقة). -/

/-- سببُ المعنى الثاني للّفظ الواحد. -/
inductive Sabab | wadAwwal | naqlIshtihar | alaqaBilaIshtihar
  deriving DecidableEq, Repr

inductive Qism7 | munfarid | mutabayin | mutaradif | mushtarak | manqul | haqiqa | majaz
  deriving DecidableEq, Repr

/-- قسمُ النبهاني للزوج (اللفظ الأوّل ومعناه، اللفظ الثاني ومعناه) بسبب المعنى الثاني. -/
def qism (a b : Ishtirak.Lafz) (sabab : Sabab) : Qism7 :=
  if a.sigha = b.sigha then
    if a.mana = b.mana then .munfarid
    else match sabab with | .wadAwwal => .mushtarak | .naqlIshtihar => .manqul | .alaqaBilaIshtihar => .majaz
  else if a.mana = b.mana then .mutaradif else .mutabayin

/-- **سيبويه أصلٌ والنبهاني تفصيل**: تباينُ سيبويه متباين، وترادفُه مترادف، والهويّةُ منفرد؛ و«اتفاق اللفظين واختلاف المعنيين»
    عنده ينقسم عند النبهاني ثلاثةً بسبب المعنى الثاني لا غير. -/
theorem sibawayhi_nabhani (a b : Ishtirak.Lafz) (s : Sabab) :
    (Ishtirak.alaqa a b = .tabayun → qism a b s = .mutabayin) ∧
    (Ishtirak.alaqa a b = .taraduf → qism a b s = .mutaradif) ∧
    (Ishtirak.alaqa a b = .huwiyya → qism a b s = .munfarid) ∧
    (Ishtirak.alaqa a b = .ishtirak → qism a b s = .mushtarak ∨ qism a b s = .manqul ∨ qism a b s = .majaz) := by
  unfold Ishtirak.alaqa qism
  by_cases h1 : a.sigha = b.sigha <;> by_cases h2 : a.mana = b.mana <;> cases s <;> simp [h1, h2]

/-- و«درس» عفاءً ودراسةً: لفظٌ واحد ومعنيان، والثاني مأخوذٌ بعلاقةٍ (المقاييس س12997، اللسان س115055) — فليس مشتركًا بل مجازًا
    إن لم يشتهر ومنقولًا إن اشتهر؛ والاشتهارُ لا يُقاس من المعجمين (ج3 س548 «إذا كثر استعمال … بحيث صار يسبق»). -/
theorem dars_laysa_mushtarak : ∀ s, s ≠ Sabab.wadAwwal →
    qism ⟨"درس", 1⟩ ⟨"درس", 2⟩ s ≠ .mushtarak := by
  intro s hs; cases s <;> simp_all [qism]

end Tarjih
