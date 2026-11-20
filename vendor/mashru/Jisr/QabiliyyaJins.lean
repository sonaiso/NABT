/-
  Jisr/QabiliyyaJins.lean — الترخيصُ من خاصّة الجنس: «ذهابُ الولد مرخَّصٌ لأنّ الولدَ إنسانٌ والإنسانَ ينتقل» — نظريةً لا قائمةً.

  **الطلب:** أمرُ المالك 2026-10-28 (بلفظه في مواصفة الطلب #113): «المفهوم المحمول على الحقيقة له أوجه حمل تربط جنس الولد بخاصية الانتقال
  ذاتيًّا، فيكون مفهوم ذهاب الولد مرخَّصًا من خاصّية جنس الولد … قفزة الاستدلال تحتاج برهانًا.» وقراراتُه 2026-10-29: لا إعادةَ ترقيم؛ والجسرُ
  «الحدثُ مثالُ قابليّةِ الحركة» علاقةٌ مودَعة بنصّ معجمٍ لا استنتاجٌ من المعنى؛ وجدولُ الجنس مودَع. ثمّ أمرُه 2026-11-04: «اعد إنتاج الهدف من
  pr 113 وفق ما وجدنا بعده … وطوره وحافظ على تناسق وترابط وتكامل Mashru» — فهذا الملفُّ إعادةُ النظرية من #113 (hhiyassat) على `main` بعد
  #122، والوصلُ بسلسلة القراءة في `Nizam/Rabt.lean` §١٠.

  **الفجوةُ التي يسدّها:** `Madlul/Tayin.lean` يبرهن أنّ القابليّةَ تتبع الخاصّة (`qabiliyya_tabi_khassa`)، و`Jisr/Utur.lean` يودِع قابليّاتِ
  «الولد» قائمةً بيد الكاتب (`walad`). ولا نظريةَ تنقل خاصّةَ الجنس إلى قابليّة الكلمة؛ فهنا: الجنسُ مودَعٌ (معاملٌ)، وقابليّاتُ المدلول
  مشتقّةٌ من فصوله (`Tayin.ilaMadlul`، أو بالتوريث `madlulWarith`)، والترخيصُ مبرهَنٌ لكلّ جنسٍ وقابليّة.

  **الوسم:** ترخيص/معلومة لا «مفهوم» (`Aql/Maratib.lean` `la_mafhum_bila_waqi`). ولا يُمَسّ `walad` ولا `madlul_shawahid`.

  **المبرهنات** بالمعيار الموحَّد: 15 لكلّ (`hukmMujarrad_isnadiyya`، `hukmMujarrad_idafiyya`، `hukmMujarrad_la_intiqal`، `qabiliyyat_ilaMadlul`، `ramzQab_inj`، `qab_contains_iff`، `tarkhis_min_jins`،
  `laHukm_bila_qabiliyya`، `hukm_qab_thulathi`، `qab_la_mumtani`، `idafiyya_mumtani`, `laHukm_idha_la_intiqal`، `hukmHadath_none`،
  `madlulWarith_qab`، `tarkhis_hadath`)، و2 تعريفيّة (`madlulWarith_haqiqa`، `mem_qab_contains`)، و3 على الشاهد (`mutasiq_fusul`،
  `shawahid_hadath`، `tawafuq_shahid`). المسلّمات: الثلاثُ المسموحة.
-/
import Jisr.Utur
import Madlul.Wiratha

set_option autoImplicit false

namespace Jisr.QabiliyyaJins
open Jisr.Utur Madlul Madlul.Tayin SLGE.Awwalan

/-! ## ١. مدلولُ الجنس وقابليّاتُه -/

/-- قابليّاتُ مدلول الجنس q = قابليّاتُ حركته مرمَّزةً (مشتقّةٌ من `fusul`). -/
theorem qabiliyyat_ilaMadlul (q : Qism) :
    (Tayin.ilaMadlul q).qabiliyyat = (Tayin.fusul q).qab.map Tayin.ramzQab := rfl

/-- ترميزُ القابليّات تقابلٌ: لا رمزَ لقابليّتين. -/
theorem ramzQab_inj (a b : QabHaraka) (h : Tayin.ramzQab a = Tayin.ramzQab b) : a = b := by
  cases a <;> cases b <;> first | rfl | (simp [Tayin.ramzQab] at h)

/-- رمزُ القابليّة في قابليّات الجنس إذا وفقط إذا كانت القابليّةُ في فصوله. -/
theorem qab_contains_iff (q : Qism) (c : QabHaraka) :
    ((Tayin.fusul q).qab.map Tayin.ramzQab).contains (Tayin.ramzQab c) = true ↔ c ∈ (Tayin.fusul q).qab := by
  rw [List.contains_iff_mem, List.mem_map]
  constructor
  · rintro ⟨c', hc', he⟩
    rw [ramzQab_inj c' c he] at hc'; exact hc'
  · intro h; exact ⟨c, h, rfl⟩

/-! ## ٢. النظريةُ العامّة: الترخيصُ من الجنس، والخلوُّ بلا امتناع -/

/-- **(د) النظريةُ العامّة:** إن كان e قابليّةَ حركةٍ للجنس q بنصّ (e في قابليّات حركة q)، فإسنادُ تلك القابليّة إلى مدلول الجنس
**مرخَّص**: قفزةُ الاستدلال مبرهنةٌ لا مطابَقةٌ على قائمة. -/
theorem tarkhis_min_jins (q : Qism) (e : Nat)
    (he : ((Tayin.fusul q).qab.map Tayin.ramzQab).contains e = true) :
    hukmMadlul ⟨Tayin.ilaMadlul q, .qabiliyya e, .isnadiyya⟩ = .murakhkhas := by
  have hi : ibtidaMadlul ⟨Tayin.ilaMadlul q, .qabiliyya e, .isnadiyya⟩ = true := by
    simp [ibtidaMadlul, Tayin.ilaMadlul, SLGE.Cat.roles]
  have hw : waslMadlul ⟨Tayin.ilaMadlul q, .qabiliyya e, .isnadiyya⟩ = .murakhkhas := by
    have hf : fiHuqul (Tayin.ilaMadlul q) (.qabiliyya e) = true := by
      simp only [fiHuqul, Tayin.ilaMadlul]; exact he
    simp only [waslMadlul, nisabMahmul, List.contains, List.elem, hf]; rfl
  simp only [hukmMadlul, hukmQayd, waqfMadlul, hi, hw, ofBool, damm, beq_self_eq_true, ite_true]

/-- **(د-عكس) الحافظُ لـم13:** قابليّةُ حركةٍ ليست في قابليّات الجنس، بنسبةٍ إسناديّة ← **لا حكم** (لا ممتنع): غيابُ الشاهد ليس امتناعًا. -/
theorem laHukm_bila_qabiliyya (q : Qism) (e : Nat)
    (he : ((Tayin.fusul q).qab.map Tayin.ramzQab).contains e = false) :
    hukmMadlul ⟨Tayin.ilaMadlul q, .qabiliyya e, .isnadiyya⟩ = .laHukm := by
  have hi : ibtidaMadlul ⟨Tayin.ilaMadlul q, .qabiliyya e, .isnadiyya⟩ = true := by
    simp [ibtidaMadlul, Tayin.ilaMadlul, SLGE.Cat.roles]
  have hw : waslMadlul ⟨Tayin.ilaMadlul q, .qabiliyya e, .isnadiyya⟩ = .laHukm := by
    have hf : fiHuqul (Tayin.ilaMadlul q) (.qabiliyya e) = false := by
      simp only [fiHuqul, Tayin.ilaMadlul]; exact he
    simp only [waslMadlul, nisabMahmul, List.contains, List.elem, hf]; rfl
  simp only [hukmMadlul, hukmQayd, waqfMadlul, hi, hw, ofBool, damm, beq_self_eq_true, ite_true]

/-- **الحكمُ على قابليّةٍ بعينها ثلاثيٌّ بلا امتناع:** مرخَّصٌ إن كانت في فصول الجنس، وإلّا لا حكم. -/
theorem hukm_qab_thulathi (q : Qism) (c : QabHaraka) :
    hukmMadlul ⟨Tayin.ilaMadlul q, .qabiliyya (Tayin.ramzQab c), .isnadiyya⟩ =
      if c ∈ (Tayin.fusul q).qab then .murakhkhas else .laHukm := by
  by_cases h : c ∈ (Tayin.fusul q).qab
  · rw [if_pos h]; exact tarkhis_min_jins q _ ((qab_contains_iff q c).2 h)
  · rw [if_neg h]
    apply laHukm_bila_qabiliyya
    cases hc : ((Tayin.fusul q).qab.map Tayin.ramzQab).contains (Tayin.ramzQab c)
    · rfl
    · exact absurd ((qab_contains_iff q c).1 hc) h

/-- **ولا يُخترع امتناع:** إسنادُ قابليّةٍ إلى مدلول جنسٍ لا يكون ممتنعًا أبدًا. -/
theorem qab_la_mumtani (q : Qism) (c : QabHaraka) :
    hukmMadlul ⟨Tayin.ilaMadlul q, .qabiliyya (Tayin.ramzQab c), .isnadiyya⟩ ≠ .mumtani := by
  rw [hukm_qab_thulathi]; split <;> decide

/-- **النسبةُ تحسم أوّلًا:** القابليّةُ لا تحتمل الإضافة (`nisabMahmul`) ← ممتنعٌ ولو كان الرمزُ في القابليّات. -/
theorem idafiyya_mumtani (q : Qism) (e : Nat) :
    hukmMadlul ⟨Tayin.ilaMadlul q, .qabiliyya e, .idafiyya⟩ = .mumtani := by
  have hw : waslMadlul ⟨Tayin.ilaMadlul q, .qabiliyya e, .idafiyya⟩ = .mumtani := by
    simp only [waslMadlul, nisabMahmul, List.contains, List.elem]; rfl
  have hq : hukmQayd ⟨Tayin.ilaMadlul q, .qabiliyya e, .idafiyya⟩ = .mumtani := by
    unfold hukmQayd; exact (damm_mumtani _ _).2 (Or.inr hw)
  unfold hukmMadlul; exact (damm_mumtani _ _).2 (Or.inl hq)

/-! ## ٣. الخاصّةُ تعمل: جنسٌ لا ينتقل لا تُرخَّص عليه قابليّةُ حركة -/

/-- **اتّساقُ الجدول المودَع:** في فصول كلّ قسمٍ لا قابليّةَ حركةٍ إلّا للمنتقل ذاتيًّا (`mutasiq` على الجدول المطابَق). -/
theorem mutasiq_fusul (q : Qism) : Tayin.mutasiq (Tayin.fusul q) := by
  cases q <;> intro h <;> first | rfl | exact absurd rfl h

/-- **الخاصّةُ تعمل:** جنسٌ انتقالُه ليس «نعم» فصولُه بلا قابليّةِ حركة، فحملُ أيّ قابليّةٍ عليه «لا حكم» (م13، لا ممتنع) — عامٌّ من `mutasiq`. -/
theorem laHukm_idha_la_intiqal (q : Qism) (hm : Tayin.mutasiq (Tayin.fusul q))
    (h : (Tayin.fusul q).intiqal ≠ .naam) (e : Nat) :
    hukmMadlul ⟨Tayin.ilaMadlul q, .qabiliyya e, .isnadiyya⟩ = .laHukm := by
  have hqab : (Tayin.fusul q).qab = [] := by
    by_cases hc : (Tayin.fusul q).qab = []
    · exact hc
    · exact absurd (hm hc) h
  have he : ((Tayin.fusul q).qab.map Tayin.ramzQab).contains e = false := by rw [hqab]; rfl
  exact laHukm_bila_qabiliyya q e he

/-! ## ٤. الجسرُ المودَع: الحدثُ مثالُ قابليّةِ حركةٍ (علاقةٌ من نصّ، لا استنتاجٌ من المعنى) -/

/-- جدولُ «الحدث e مثالُ قابليّةِ الحركة c» (ذهب → سير) — صفوفُه من معجمٍ مختوم، لا من المعنى؛ بأرقام الأحداث (شواهدُ المالك). -/
abbrev MithalQab := List (Nat × Tayin.QabHaraka)

/-- **حكمُ حملِ حدثٍ** عبر الجسر: إن كان للحدث e مثالُ قابليّةٍ c مودَعٌ فحكمُه حكمُ حمل تلك القابليّة؛ وإلّا «لا حكم» (غيابُ النصّ ليس امتناعًا). -/
def hukmHadath (m : Madlul) (mq : MithalQab) (e : Nat) : Hukm :=
  match mq.lookup e with
  | some c => hukmMadlul ⟨m, .qabiliyya (Tayin.ramzQab c), .isnadiyya⟩
  | none => .laHukm

theorem hukmHadath_none (m : Madlul) (mq : MithalQab) (e : Nat) (h : mq.lookup e = none) :
    hukmHadath m mq e = .laHukm := by simp only [hukmHadath, h]

/-! ## ٥. مدلولُ الكلمة الموروث (بـ`Wiratha`، بلا مسّ `walad`) -/

/-- خواصُّ الكلمة الموروثةُ من فصول جنسها بالتوريث (`warrith`؛ فصلٌ فارغ يُبقي فصولَ الجنس — `warrith_farigh`). -/
def khawassWarith (q : Qism) : Tayin.Khawass := Wiratha.warrith (Tayin.fusul q) {}

/-- **مدلولُ الكلمة الموروث:** حقيقتُه حقيقةُ الكلمة نفسِها، وخواصُّه وقابليّاتُه موروثةٌ من فصول جنسها — بلا قائمةٍ يدًا. -/
def madlulWarith (m : Madlul) (q : Qism) : Madlul :=
  { m with khawass := Tayin.khawassNaam (khawassWarith q),
           qabiliyyat := (khawassWarith q).qab.map Tayin.ramzQab }

theorem madlulWarith_haqiqa (m : Madlul) (q : Qism) : (madlulWarith m q).haqiqa = m.haqiqa := rfl

theorem madlulWarith_qab (m : Madlul) (q : Qism) :
    (madlulWarith m q).qabiliyyat = (Tayin.fusul q).qab.map Tayin.ramzQab := by
  simp only [madlulWarith, khawassWarith, Wiratha.warrith_farigh]

theorem mem_qab_contains (q : Qism) (c : Tayin.QabHaraka) (h : c ∈ (Tayin.fusul q).qab) :
    ((Tayin.fusul q).qab.map Tayin.ramzQab).contains (Tayin.ramzQab c) = true :=
  (qab_contains_iff q c).2 h

/-- **النظريةُ العامّة للجسر:** جنسُ الكلمة q يملك قابليّةَ الحركة c، والحدثُ e مثالُها بنصّ ⇒ حملُ الحدث على المدلول الموروث **مرخَّص**. -/
theorem tarkhis_hadath (m : Madlul) (q : Qism) (e : Nat) (c : Tayin.QabHaraka) (mq : MithalQab)
    (hib : ibtidaMadlul ⟨madlulWarith m q, .qabiliyya (Tayin.ramzQab c), .isnadiyya⟩ = true)
    (hc : mq.lookup e = some c) (hcq : c ∈ (Tayin.fusul q).qab) :
    hukmHadath (madlulWarith m q) mq e = .murakhkhas := by
  have hf : fiHuqul (madlulWarith m q) (.qabiliyya (Tayin.ramzQab c)) = true := by
    simp only [fiHuqul, madlulWarith_qab]; exact mem_qab_contains q c hcq
  have hw : waslMadlul ⟨madlulWarith m q, .qabiliyya (Tayin.ramzQab c), .isnadiyya⟩ = .murakhkhas := by
    simp only [waslMadlul, nisabMahmul, List.contains, List.elem, hf]; rfl
  simp only [hukmHadath, hc, hukmMadlul, hukmQayd, waqfMadlul, hib, hw, ofBool, damm, beq_self_eq_true, ite_true]

/-! ## ٦. الشاهدُ بعينه (الذي سأل عنه المالك) — على ترميز شواهد `Utur` (ذهب 10، طار 12) -/

/-- مثالُ القابليّة على الشاهد: «ذهب» (10) مثالُ السير — بانتظار ختم نصّ «ذهب = سار/مضى» (مرشَّح). -/
def mithalShahid : MithalQab := [(10, .sayr)]

/-- **ذهابُ الولد مرخَّص، وطيرانُه لا حكم، وذهابُ الدار لا حكم** — من الجنس والخاصّة والجسر، لا من قائمة. -/
theorem shawahid_hadath :
    hukmHadath (madlulWarith Jisr.Utur.walad .insan) mithalShahid 10 = .murakhkhas ∧
    hukmHadath (madlulWarith Jisr.Utur.walad .insan) mithalShahid 12 = .laHukm ∧
    hukmHadath (madlulWarith Jisr.Utur.dar .jamad) mithalShahid 10 = .laHukm := by decide

/-- **التقاءُ الطريقين (لا تعارض):** الحكمُ المشتقُّ من الجنس على (الولد، ذهب 10) و(الولد، طار 12) يساوي حكمَ شاهد `Utur` المودَع يدًا
(`madlul_shawahid`). -/
theorem tawafuq_shahid :
    hukmHadath (madlulWarith Jisr.Utur.walad .insan) mithalShahid 10
      = hukmMadlul ⟨Jisr.Utur.walad, .qabiliyya 10, .isnadiyya⟩ ∧
    hukmHadath (madlulWarith Jisr.Utur.walad .insan) mithalShahid 12
      = hukmMadlul ⟨Jisr.Utur.walad, .qabiliyya 12, .isnadiyya⟩ := by decide

/-! ## ٧. الحكمُ المجرَّد على (جنس، مثال، نسبة) — ما تقيسه حالاتُ الضابط المجمَّد -/

/-- مخرجُ الحمل من الجنس مجرَّدًا: الحكمُ الثلاثيّ على المدلول، أو غيابُ الصفّ مُسمًّى (الجنسُ أوّلًا ثمّ المثال، قبل النسبة). -/
inductive HukmMujarrad | murakhkhas | laHukm | mumtani | laJins | laMithal
  deriving DecidableEq, Repr

def ofHukm : Hukm → HukmMujarrad
  | .murakhkhas => .murakhkhas | .laHukm => .laHukm | .mumtani => .mumtani

/-- **الحكمُ المجرَّد:** جنسُ المسند إليه في الجدول (أو غائب)، وقابليّةُ الحركة التي المسندُ مثالُها في الجدول (أو غائبة)، والنسبة. الغيابُ
يُسمّى قبل النسبة (تعيينٌ معلَن). -/
def hukmMujarrad : Option Qism → Option QabHaraka → Nisab.Nisba → HukmMujarrad
  | none, _, _ => .laJins
  | some _, none, _ => .laMithal
  | some q, some c, n => ofHukm (hukmMadlul ⟨Tayin.ilaMadlul q, .qabiliyya (Tayin.ramzQab c), n⟩)

/-- بالنسبة الإسناديّة: مرخَّصٌ إن كانت القابليّةُ في فصول الجنس، وإلّا لا حكم؛ ولا امتناع. -/
theorem hukmMujarrad_isnadiyya (q : Qism) (c : QabHaraka) :
    hukmMujarrad (some q) (some c) .isnadiyya = if c ∈ (Tayin.fusul q).qab then .murakhkhas else .laHukm := by
  simp only [hukmMujarrad, hukm_qab_thulathi]; split <;> rfl

/-- بالنسبة الإضافيّة: ممتنعٌ أيًّا كان الجنسُ والقابليّة (`idafiyya_mumtani`). -/
theorem hukmMujarrad_idafiyya (q : Qism) (c : QabHaraka) : hukmMujarrad (some q) (some c) .idafiyya = .mumtani := by
  simp only [hukmMujarrad, idafiyya_mumtani]; rfl

/-- جنسٌ لا ينتقل (الجمادُ والنبات) بالنسبة الإسناديّة: لا حكم لكلّ قابليّة. -/
theorem hukmMujarrad_la_intiqal (q : Qism) (c : QabHaraka) (h : (Tayin.fusul q).intiqal ≠ .naam) :
    hukmMujarrad (some q) (some c) .isnadiyya = .laHukm := by
  simp only [hukmMujarrad, laHukm_idha_la_intiqal q (mutasiq_fusul q) h]; rfl

end Jisr.QabiliyyaJins
