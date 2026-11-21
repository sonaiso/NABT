import Lean

-- 1. تسمية الحالات الأربع للخلية اللفظية (Cell States)
inductive CellState
  | SifrWahid    -- دال محض (خلايا الصفر والواحد من الدال)
  | Wasl         -- حالة الوصل (الحركة الإعرابية الظاهرة لفظاً)
  | Waqf         -- حالة الوقف (السكون العارض المخفي لفظاً)
  | Muhmal       -- مهمل لا وضع له دلالياً

-- 2. مراتب المخرج الثلاث المقيدة (المادة 15 من الدستور)
inductive NatijaRank
  | MinHaythuHi  -- مادة محسوسة عادية (من حيث هي)
  | Maluma       -- معلومة مجردة (تخيلات وفروض بلا شاهد واقعي)
  | Mafhum       -- مفهوم حقيقي له مرساة في الواقع المحسوس (المرتبة 0)

-- بنية النتيجة المركبة المطورة بعد إسقاط الأحكام العائمة
structure Natija where
  id : Nat
  rank : NatijaRank
  is_cleaned : Bool -- شرط التصفية الشاملة من التصحيف (is_cleaned = true)

-- 3. بنية الجداول المودعة والمختومة كشواهد مطابقة
structure LetterMakhraj where
  letter : String
  position : String -- حلقي، لهوي، شجري (سيبويه)

structure IbnFarisMeasure where
  root : String
  is_luzum : Bool   -- مقياس اللزوم والتعدية الصرفية (ابن فارس)

-- 4. محرك الفحص والفرز الميكانيكي الحتمي للنتيجة
def evaluate_natija (nt : Natija) (state : CellState) : Bool :=
  if nt.is_cleaned == false then false
  else
    match state with
    | CellState.Muhmal => false -- المهمل معزول ميكانيكياً ولا ينتج حكماً أبداً
    | _ =>
        match nt.rank with
        | NatijaRank.Mafhum => true -- المفهوم الحقيقي المقيد وحده يعبر بوابات المأقول
        | _ => false
/-- المبرهنة تصحّ بسطر، لكنّها تقول: «العَلَمان اللذان كتبهما المُدخِل صحيحان». -/
theorem natija_islah (nt : Natija) (state : CellState) :
  evaluate_natija nt state = true → (nt.is_cleaned = true ∧ nt.rank = NatijaRank.Mafhum) := by
  intro h; unfold evaluate_natija at h
  cases hc : nt.is_cleaned <;> cases state <;> cases hr : nt.rank <;> simp_all
/-- «مفهوم» يُقبل بلا أيّ شاهد واقع: الرتبة عَلَمٌ معلَن لا محسوب (ضدّ م16). -/
theorem naqd_mafhum_bila_shahid : evaluate_natija ⟨0, .Mafhum, true⟩ .Wasl = true := rfl
/-- «من حيث هي» تُرفض دائمًا، مع أنّها المرتبة الأولى في م15 لا رتبةً مرفوضة. -/
theorem naqd_min_haythu_hiya_marfuda (i : Nat) (c : Bool) (s : CellState) :
    evaluate_natija ⟨i, .MinHaythuHi, c⟩ s = false := by
  cases c <;> cases s <;> rfl
#print axioms natija_islah
#print axioms naqd_mafhum_bila_shahid
#print axioms naqd_min_haythu_hiya_marfuda
