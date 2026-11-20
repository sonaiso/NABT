import A116.Tawafiq
import A116.Awamil
import A116.Fractal

/-!
# نقدُ مرفق «برهان الاتّساق الفراكتاليّ» صوريًّا، ومقابلُه القائم (ADR ٧٩، طلبُ المالك «حلّل وبرهن»)

المرفقُ شفرةُ Lean تدّعي «إثباتَ الاتّساق الكامل» و«تشغيلًا لا يحتاج سجلَّ الأرقام». فُحص بالآلة فكان:

1. **لا يُترجَم**: `proof_text_continuity` يفكّك `ih2` — وهو `∃ e, s2 = s2` (قضيّة) — ويعطيه حيث يُنتظر `PhoneticLink`
   (نوع)؛ خطأُ نوعٍ في سطر `exists s1, e2`. فدعوى «الشفرة البرهانيّة الكاملة» كاذبةٌ بالترجمة.
2. **ولو تُرجم فهو فارغ**: مبرهنتاه من صورة `∃ x, x = x`. نُعيد كتابتهما هنا بأنواع المرفق نفسِها ونُبرهنهما **بلا**
   الفرض `isLicensed g = true` وبلا استقراء (`continuity_without_hypothesis`، `closure_without_hypothesis`)، بل
   لأيّ نوعٍ مسكون (`continuity_is_about_nothing`): المبرهنةُ لا تذكر العربيّة ولا الترخيص ولا الحدّ.
3. **بوّابتُه ثلاثةُ بتّات**: `isLicensed` دالّةٌ في (سبب، شرط، مانع) بلا خانة؛ فهي تقبل «كلمةً» بلا حروف وترفض
   أخرى بالبتّات نفسِها لأيّ محتوًى (`gate_ignores_cells`) — نظيرُ `Sigha.Naqd.verify_ignores_structure`.
4. **فضاؤه 29 × 4 × 29 = 3,364** (`PhoneticLink`): يعدّ الألفَ حاملَ ابتداء والسكونَ حركة، وهو العددُ الذي أسقطه
   `Tawafiq.not_3364` — ليس عددَ طول.
5. **حروفُه بوّاباتٌ منطقيّة** (And/Or/Xor/IfThen): ليست في المودَع؛ العطفُ في جدول العوامل المرسى ثمانيةُ أحرف
   أثرُها التبعيّة لا منطقٌ ثنائيّ (`Awamil.tabi_no_effect`)، ولا «Xor» في ثلاثةَ عشرَ صنفًا (`no_xor_in_awamil`).
6. **«الاستقراءُ الفراكتاليّ»** فيه لا يستعمل فرضَي الاستقراء إلّا ليُهملهما؛ والقائمُ في الشجرة فراكتالٌ بمعناه:
   `Fractal.fractal_succ` (كلُّ طبقةٍ رفعُ ما تحتها)، `fractal_append` (الوصلُ تركيبُ الأثرين)، `fractal_flat`
   (الطبقةُ n تُسطَّح إلى الصفر)، `sitta_kull_tabaqa` (القوانينُ الستّة في كلّ طبقة) — مبرهناتٌ على بنيةٍ لا على `x = x`.
7. **«بلا سجلّ الأرقام»**: ما يُبرهَن هنا لا يُغني عن القياس؛ الدستورُ م٦ وم١٧: Lean يُبرهن المرويَّ المودَع، والقياسُ على
   المرجع المحجوب شيءٌ آخر.

الحكم: المرفقُ **بحثٌ منطقيٌّ** بلا واقع (الدستور م١٤): لا مودَعَ مختومًا، ولا مدخلَ ينقله، ولا جدولَ قبل القراءة؛
مبرهناتُه رياضيًّا صحيحةٌ بعد الإصلاح وفارغةٌ لغويًّا. لا يدخل منه شيء (`ATTACHMENT_FRACTAL_REJECTED`).
-/

namespace A116.NaqdFractal

open A116 A116.Ladder A116.Hadd

/-! ## أنواعُ المرفق بأعيانها -/

inductive Movement | Fatha | Damma | Kasra | Sukun
  deriving DecidableEq, Repr

structure PhoneticLink where
  char1 : Fin 29
  move : Movement
  char2 : Fin 29

structure LicensingGate where
  cause : Bool
  condition : Bool
  barrier : Bool

def isLicensed (g : LicensingGate) : Bool := g.cause && g.condition && !g.barrier

inductive SyntacticClass | noun | verb | part
  deriving DecidableEq, Repr

inductive Phrase
  | single : SyntacticClass → Phrase
  | composite : Phrase → Phrase → Phrase

/-! ## ١–٢. المبرهنتان فارغتان: تُبرهَنان بلا الفرض وبلا استقراء -/

/-- عبارةُ المرفق الأولى بعينها، بلا `g` ولا `h` ولا استقراء؛ والشاهدُ الثاني `_e` لا يُذكر — Lean نفسُه
يحذّر من إهماله في صيغة المرفق. -/
theorem continuity_without_hypothesis (_p : Phrase) :
    ∃ s _e : PhoneticLink, s = s :=
  ⟨⟨0, .Sukun, 0⟩, ⟨0, .Sukun, 0⟩, rfl⟩

/-- عبارةُ المرفق الثانية بعينها، بلا العامل. -/
theorem closure_without_hypothesis (_c₁ c₂ : SyntacticClass) :
    ∃ r : SyntacticClass, r = r :=
  ⟨c₂, rfl⟩

/-- الدعوى صادقةٌ لأيّ نوعٍ مسكونٍ أيًّا كان: لا شيءَ فيها عن الخانات. -/
theorem continuity_is_about_nothing (α : Type) [Inhabited α] (_p : Phrase) :
    ∃ s _e : α, s = s :=
  ⟨default, default, rfl⟩

/-- الفرضُ `isLicensed g = true` لا يُستعمل: النتيجةُ نفسُها حين البوّابةُ مغلقة. -/
theorem continuity_even_when_gate_closed (p : Phrase) (g : LicensingGate)
    (_h : isLicensed g = false) : ∃ s _e : PhoneticLink, s = s :=
  continuity_without_hypothesis p

/-! ## ٣. البوّابةُ ثلاثةُ بتّات لا تقرأ خانة -/

/-- الترخيصُ دالّةٌ في البتّات الثلاثة فقط: أيُّ محتوًى يُلحق بها لا يغيّره. -/
theorem gate_ignores_cells (g : LicensingGate) (_cells : List Cell) :
    isLicensed g = (g.cause && g.condition && !g.barrier) := rfl

/-- البوّابةُ المفتوحة تقبل السلسلةَ الفارغة وأيَّ سلسلة سواء. -/
theorem open_gate_accepts_empty :
    isLicensed ⟨true, true, false⟩ = true ∧ isLicensed ⟨true, true, true⟩ = false := by decide

/-- أمّا بوّابةُ الشجرة فتقرأ الخانات: كَتَبَ مرخَّصة وكَاْاْ مرفوضةٌ وصلًا (`Hadd.strictB`) — حكمان
مختلفان على محتويين، وهو ما لا تملكه بوّابةُ المرفق. -/
theorem real_gate_reads_cells :
    Hadd.strictB (Tawafiq.shape .fatha .fatha .fatha) = true ∧
    Hadd.strictB [atom 'ك' .fatha, atom 'ا' .sukun, atom 'ا' .sukun] = false := by
  decide +kernel

/-! ## ٤. 29 × 4 × 29 ليس عددَ طول -/

theorem phonetic_link_is_blind_product : 29 * 4 * 29 = 3364 ∧ Tawafiq.wasl 1 < 3364 ∧ 3364 < Tawafiq.wasl 2 :=
  ⟨rfl, Tawafiq.not_3364.1, Tawafiq.not_3364.2⟩

/-! ## ٥. لا بوّاباتِ Xor في العوامل المرساة -/

/-- أصنافُ الأثر الثلاثةَ عشر لا «xor» فيها، والعطفُ تابعٌ بلا أثرٍ منطقيّ. -/
theorem no_xor_in_awamil : Awamil.all.length = 13 ∧ Awamil.first .tabi = none := by decide

/-! ## ٦. الفراكتالُ القائم ليس `x = x` -/

/-- شاهدٌ على أنّ الفراكتال في الشجرة يقول شيئًا: الصفرُ محايدٌ حقًّا والوصلُ تركيب. -/
theorem fractal_says_something {α σ : Type} (T : Tawrith.Tawrith α σ) (n : Nat) (s : σ) :
    Fractal.athar T n [] s = some s :=
  Fractal.zero_element_identity T n s

end A116.NaqdFractal
