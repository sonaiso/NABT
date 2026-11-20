import Lean

-- 1. تعريف المستند المودع ووسم التختيم
structure IngestedDocument where
  doc_id       : Nat
  title        : String
  is_cleaned   : Bool  -- شرط التصفية من التصحيف (is_cleaned = true)
  kernel_hash  : Nat     -- البصمة البرهانية الفريدة للتختيم

inductive KnowledgeAsset
  | LugDynamic   -- حقيقة لغوية/شاهد (سيبويه، قطر الندى، المخصص)
  | FormalRule   -- قاعدة صورية/برمجية (بايثون، رياضيات)
  | EmpiricalFact-- حقيقة مادية/علمية (فيزياء، كيمياء)

inductive WasmRank
  | AslMuqaddas  -- أصل مودع قطعي
  | Taqdeer      -- تقدير ظني (للمادة التجريبية)
  | Mabarhan     -- مبرهن حتمياً بسلسلة تراخيص

structure KnowledgeMatrix where
  doc       : IngestedDocument
  asset     : KnowledgeAsset
  rank      : WasmRank
  has_fault : Bool

-- 2. محرك التختيم والفرز الميكانيكي للبوابة
def execute_idaa_gate (matrix : KnowledgeMatrix) : Bool :=
  if matrix.doc.is_cleaned == false || matrix.has_fault == true then false
  else
    match matrix.asset with
    | KnowledgeAsset.LugDynamic => 
        -- الحقائق اللغوية تشترط التختيم بالأصل المأخوذ اصطلاحاً عن العرب
        match matrix.rank with
        | WasmRank.AslMuqaddas => true
        | WasmRank.Taqdeer => true
        | _ => false
    | KnowledgeAsset.FormalRule => 
        -- القواعد الصورية والبرمجية (بايثون/الرياضيات) تقبل الوسم البرهاني القطعي
        match matrix.rank with
        | WasmRank.Mabarhan => true
        | _ => false
    | KnowledgeAsset.EmpiricalFact => 
        -- الفيزياء والعلوم المادية لا تعلو فوق وسم "تقدير/مقيس" (التفكير 107)
        match matrix.rank with
        | WasmRank.Taqdeer => true
        | _ => false

theorem idaa_gate_safety_islah (matrix : KnowledgeMatrix) :
  execute_idaa_gate matrix = true →
  (matrix.doc.is_cleaned = true ∧ matrix.has_fault = false) := by
  intro h
  unfold execute_idaa_gate at h
  cases hc : matrix.doc.is_cleaned <;> cases hf : matrix.has_fault <;> simp_all

/-- دليل بايثون (قاعدة صوريّة) يُقبل «مبرهنًا» بلا أيّ برهان: الوسم معلَنٌ من المُدخِل. -/
theorem naqd_python_mubarhan :
    execute_idaa_gate ⟨⟨1, "دليل بايثون", true, 0⟩, .FormalRule, .Mabarhan, false⟩ = true := rfl

/-- البصمة لا تُقرأ: وثيقتان ببصمتين مختلفتين حكمُهما واحد. -/
theorem naqd_basma_muhmala (i : Nat) (t : String) (h1 h2 : Nat) (a : KnowledgeAsset) (r : WasmRank) :
    execute_idaa_gate ⟨⟨i, t, true, h1⟩, a, r, false⟩ = execute_idaa_gate ⟨⟨i, t, true, h2⟩, a, r, false⟩ := rfl

/-- خبرٌ لغويّ يُقبل «أصلًا قطعيًّا» دون أن يُسأل: متواتر أم آحاد؟ -/
theorem naqd_lugha_qati :
    execute_idaa_gate ⟨⟨2, "قول الأصمعي وحده", true, 0⟩, .LugDynamic, .AslMuqaddas, false⟩ = true := rfl
#print axioms idaa_gate_safety_islah
#print axioms naqd_python_mubarhan
#print axioms naqd_basma_muhmala
#print axioms naqd_lugha_qati
