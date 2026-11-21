-- 1. فضاء الإحساس والانتباه المتقصّد
structure SensoryAttention where
  reality_anchor : String
  is_sensed      : Bool
  intibah_level  : Nat   -- مستوى التقصّد والالتفات الميكانيكي لكنه الشيء (المرتبة 0)

-- 2. وعاء المعلومات السابقة (المرتبط بالجامع العقائدي كفكر سياسي)
structure IdeologicalPrior where
  rule_bits       : String
  is_political_thought : Bool -- تحويل الأحكام إلى أفكار سياسية لرعاية الشؤون
  is_cleaned      : Bool -- تصفية أخطاء الرقمنة حتماً

inductive AmbiguityType
  | VerbalSurface -- تعمية اللفظ أو الفعل (تنتج سرعة ملاحظة)
  | IntentHidden  -- تعمية القصد والغاية (تنتج سرعة بديهة)

inductive VerdictSpeed
  | NaturalBadihah  -- سرعة بديهة طبيعية عفوية حتمية
  | MulahedhahOnly  -- سرعة ملاحظة سطحية
  | SlowStall       -- تفكير بطيء مشلول (فلسفة آلية ملوثة)

structure BadihahEngine where
  attention : SensoryAttention
  prior     : IdeologicalPrior
  ambiguity : AmbiguityType
  is_urgent : Bool -- ظرف مفاجئ أو عاجل يمنع التروي والدرس

-- 3. محرك ديناميكية القرار الخاطف
def evaluate_badihah_verdict (eng : BadihahEngine) : VerdictSpeed :=
  -- إذا انعدم الانتباه والتقصد (intibah_level = 0) سقط الفكر ووقع الضرر والبطء
  if eng.attention.intibah_level == 0 || eng.prior.is_cleaned == false then 
    VerdictSpeed.SlowStall
  else
    if eng.is_urgent then
      match eng.ambiguity with
      | AmbiguityType.VerbalSurface => VerdictSpeed.MulahedhahOnly
      | AmbiguityType.IntentHidden => 
          -- سرعة البديهة تشترط ربط الواقع بالحكم كفكر سياسي منبثق عن العقيدة
          if eng.prior.is_political_thought then VerdictSpeed.NaturalBadihah
          else VerdictSpeed.SlowStall
    else
      -- إذا لم يكن الظرف عاجلاً، فالأصل هو الدرس والتمحيص الموضوعي غير المشلول
      VerdictSpeed.SlowStall

/-- نقض مبرهنة المرفق: الشرط is_sensed لا يقرؤه الخطّ أصلًا، فالمبرهنة كاذبة. -/
theorem naqd_badihah_closure : ¬ ∀ (eng : BadihahEngine),
    evaluate_badihah_verdict eng = VerdictSpeed.NaturalBadihah →
    (eng.attention.is_sensed = true ∧ eng.prior.is_political_thought = true) := by
  intro h
  have := h ⟨⟨"x", false, 1⟩, ⟨"r", true, true⟩, .IntentHidden, true⟩ rfl
  simp at this
#print axioms naqd_badihah_closure
