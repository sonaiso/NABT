/-!
# سلسلةُ القرار: خوارزميّةُ المحاكمة على منهج النبهانيّ (ADR ٥٧)

الأركانُ بأسطرها من المختومات (عباراتُها في `slge.mayaatir_table`، تُطابَق هناك بـ`--check`):

* الإدراك نقلُ الحسّ بالواقع ومعلوماتٌ سابقة (التفكير س32) ⟹ **ما لم يُحسّ واقعُه فلا حكم** (`laHukm`).
* «تبقى فكراً صائباً حتى يتبين خطؤها» (س38) ⟹ **المعارضُ المودَع يُسقط الدعوى** (`khata`)، وغيابُه يُبقيها صائبة.
* «إن كانت مما يتعلق بوجود الشيء… فإنها أفكار قطعية… أو صفته… فإنها أفكار ظنية» (س38) ⟹ `qati` للوجود، `zanni`
  للحقيقة والصفة.
* «المنطق تبنى نتائجه على مقدمات، وكذب هذه المقدمات… ليس من السهل إدراكه» (س72) ⟹ **ما بُني على أصلٍ ساقطٍ ساقط**
  (`saqit`)، وما بُني على ظنّيٍّ لا يكون قطعيًّا.
* «فلو توقف… للزم الدور، وهذا باطل» (ج3 س483) ⟹ أصلٌ لم يسبق في السلسلة دورٌ (`dawr`).
* «محاكمة الدليل… معرفة سلامته من المعارض بناء على وجوب البحث عنه، وهي متوقفة على استقراء الأدلة» (ج1 س421)
  ⟹ حقلُ `muarid` نتيجةُ استقراءٍ في المودَعات، يُملأ قبل الحكم.

**الخوارزميّة** (`judge1`، `run`): تُمرّ الدعاوى بترتيب السلسلة، ولكلّ دعوى بالترتيب: أصولُها ← الحسّ ← المعارض ←
الدرجة. والمبرهَن هنا لكلّ سلسلة: لا صوابَ بلا حسٍّ ولا مع معارض، ولا صوابَ على أصلٍ غيرِ صائب، ولا قطعَ إلّا للوجود
وعلى أصولٍ قطعيّة. وعلى الشاهدين (سلسلتا المرفقين المحاكَمين في الجلسة) الأحكامُ بالحساب. وما في الحقول من حسٍّ
ومعارضٍ مدخلٌ يملؤه المحاكِم بشاهده، لا يستنتجه Lean (المادّة ١٧).
-/

set_option autoImplicit false

namespace A116.Qarar

/-- الحكمُ: صائبٌ قطعيّ، أو صائبٌ ظنّيّ، أو خاطئٌ بمعارض، أو ساقطٌ بأصله، أو دورٌ، أو لا حكم. -/
inductive Hukm where
  | qati | zanni | khata | saqit | dawr | laHukm
  deriving DecidableEq, Repr

def Hukm.sawab : Hukm → Bool
  | .qati | .zanni => true
  | _ => false

def Hukm.fallen : Hukm → Bool
  | .khata | .saqit | .dawr => true
  | _ => false

/-- الدعوى في السلسلة. -/
structure Daawa where
  id : Nat
  /-- حكمٌ على وجود الشيء، لا على حقيقته أو صفته. -/
  wujud : Bool
  /-- وقع الحسُّ على واقعها: شاهدٌ مودَعٌ قُرئ. -/
  mahsus : Bool
  /-- وُجد لها معارضٌ مودَعٌ بعد الاستقراء. -/
  muarid : Bool
  /-- ما بُنيت عليه من دعاوى السلسلة. -/
  usul : List Nat
  deriving DecidableEq, Repr

/-- أحكامُ الأصول كما سبقت في السلسلة. -/
def premises (prior : List (Nat × Hukm)) (c : Daawa) : List (Option Hukm) :=
  c.usul.map fun u => prior.lookup u

/-- **حكمُ الدعوى** بعد ما سبقها. -/
def judge1 (prior : List (Nat × Hukm)) (c : Daawa) : Hukm :=
  if (premises prior c).any (·.isNone) then .dawr
  else if (premises prior c).any (fun o => o.any Hukm.fallen) then .saqit
  else if (premises prior c).any (· == some .laHukm) || !c.mahsus then .laHukm
  else if c.muarid then .khata
  else if c.wujud && (premises prior c).all (· == some .qati) then .qati
  else .zanni

def runAux : List (Nat × Hukm) → List Daawa → List (Nat × Hukm)
  | acc, [] => acc
  | acc, c :: cs => runAux (acc ++ [(c.id, judge1 acc c)]) cs

/-- **السلسلة**: الأحكامُ بالترتيب. -/
def run (cs : List Daawa) : List (Nat × Hukm) := runAux [] cs

/-! ## المبرهَن لكلّ سلسلة -/

/-- **مواصفةُ الصواب**: الدعوى الصائبة محسوسةٌ بلا معارض، وكلُّ أصلٍ لها سبق حكمُه صائبًا. -/
theorem sawab_spec (p : List (Nat × Hukm)) (c : Daawa) (h : (judge1 p c).sawab = true) :
    c.mahsus = true ∧ c.muarid = false ∧ ∀ o ∈ premises p c, ∃ k, o = some k ∧ k.sawab = true := by
  unfold judge1 at h
  by_cases h1 : (premises p c).any (·.isNone) = true
  · simp only [h1, ↓reduceIte, Hukm.sawab] at h; exact absurd h (by decide)
  by_cases h2 : (premises p c).any (fun o => o.any Hukm.fallen) = true
  · simp only [h1, h2, ↓reduceIte, Hukm.sawab, Bool.false_eq_true] at h
  by_cases h3 : ((premises p c).any (· == some .laHukm) || !c.mahsus) = true
  · simp only [h1, h2, h3, ↓reduceIte, Hukm.sawab, Bool.false_eq_true] at h
  by_cases h4 : c.muarid = true
  · simp only [h1, h2, h3, h4, ↓reduceIte, Hukm.sawab, Bool.false_eq_true] at h
  refine ⟨?_, ?_, ?_⟩
  · cases hm : c.mahsus
    · exact absurd (by simp [hm]) h3
    · rfl
  · cases hm : c.muarid
    · rfl
    · exact absurd hm h4
  · intro o ho
    cases o with
    | none => exact absurd (List.any_eq_true.mpr ⟨none, ho, rfl⟩) h1
    | some k =>
      refine ⟨k, rfl, ?_⟩
      have hf : ¬ (Option.any Hukm.fallen (some k) = true) := fun e =>
        h2 (List.any_eq_true.mpr ⟨some k, ho, e⟩)
      have hl : ¬ ((some k == some Hukm.laHukm) = true) := fun e =>
        h3 (by rw [Bool.or_eq_true]; exact Or.inl (List.any_eq_true.mpr ⟨some k, ho, e⟩))
      cases k <;> first | rfl | exact absurd rfl hf | exact absurd rfl hl

/-- لا صوابَ بلا حسّ. -/
theorem sawab_needs_mahsus (p : List (Nat × Hukm)) (c : Daawa) (h : (judge1 p c).sawab = true) :
    c.mahsus = true := (sawab_spec p c h).1

/-- لا صوابَ مع معارض. -/
theorem sawab_needs_no_muarid (p : List (Nat × Hukm)) (c : Daawa) (h : (judge1 p c).sawab = true) :
    c.muarid = false := (sawab_spec p c h).2.1

/-- **لا صوابَ على أصلٍ غيرِ صائب**: كلُّ أصلٍ لدعوى صائبةٍ سبق حكمُه صائبًا. -/
theorem sawab_needs_sawab_premises (p : List (Nat × Hukm)) (c : Daawa)
    (h : (judge1 p c).sawab = true) : ∀ u ∈ c.usul, ∃ k, p.lookup u = some k ∧ k.sawab = true :=
  fun u hu => (sawab_spec p c h).2.2 _ (List.mem_map.mpr ⟨u, hu, rfl⟩)

/-- **لا قطعَ إلّا للوجود**، وعلى أصولٍ قطعيّةٍ كلِّها. -/
theorem qati_needs_wujud (p : List (Nat × Hukm)) (c : Daawa) (h : judge1 p c = .qati) :
    c.wujud = true ∧ ∀ u ∈ c.usul, p.lookup u = some .qati := by
  unfold judge1 at h
  by_cases h1 : (premises p c).any (·.isNone) = true
  · simp only [h1, ↓reduceIte] at h; exact absurd h (by decide)
  by_cases h2 : (premises p c).any (fun o => o.any Hukm.fallen) = true
  · simp only [h1, h2, ↓reduceIte, Bool.false_eq_true] at h; exact absurd h (by decide)
  by_cases h3 : ((premises p c).any (· == some .laHukm) || !c.mahsus) = true
  · simp only [h1, h2, h3, ↓reduceIte, Bool.false_eq_true] at h; exact absurd h (by decide)
  by_cases h4 : c.muarid = true
  · simp only [h1, h2, h3, h4, ↓reduceIte, Bool.false_eq_true] at h; exact absurd h (by decide)
  by_cases h5 : (c.wujud && (premises p c).all (· == some .qati)) = true
  · simp only [Bool.and_eq_true, List.all_eq_true, beq_iff_eq] at h5
    exact ⟨h5.1, fun u hu => h5.2 _ (List.mem_map.mpr ⟨u, hu, rfl⟩)⟩
  · simp only [h1, h2, h3, h4, h5, ↓reduceIte, Bool.false_eq_true] at h; exact absurd h (by decide)

/-- أصلٌ لم يسبق في السلسلة دور. -/
theorem missing_premise_dawr (p : List (Nat × Hukm)) (c : Daawa) (u : Nat) (hu : u ∈ c.usul)
    (hn : p.lookup u = none) : judge1 p c = .dawr := by
  unfold judge1
  have : (premises p c).any (·.isNone) = true :=
    List.any_eq_true.mpr ⟨_, List.mem_map.mpr ⟨u, hu, rfl⟩, by simp [hn]⟩
  simp [this]

/-! ## الشاهدان: سلسلتا المرفقين كما حوكمتا في الجلسة (2026-10-13) -/

def d (i : Nat) (w s m : Bool) (us : List Nat := []) : Daawa := ⟨i, w, s, m, us⟩

/-- «الشوط الأول — `seal_l0.py`»: م١…م١٤ بالترتيب. -/
def sealL0 : List Daawa :=
  [ d 1 true true true,          -- م١ المصدرُ حاوياتٌ تُستخرج — يعارضه ج1 المختوم
    d 2 true true true,          -- م٢ j2 من مصادر L0 — يعارضه حدُّ الفصل
    d 3 false true false,        -- م٣ القواعدُ بياناتٌ ببصمة
    d 4 false true true,         -- م٤ «كالوحي» — قياسٌ شموليّ (التفكير س241)
    d 5 true true true,          -- م٥ «خمسٌ لا سادسة» — جدولُه ستّة
    d 6 false false false,       -- م٦ «الترتيبُ جزءٌ من الحكم» — لا واقعَ يُحسّ
    d 7 true true true [1],      -- م٧ N1/N2 — مبنيّةٌ على م١، ولا رقمَ في الفصل
    d 8 false false false,       -- م٨ N6 — اختيارٌ لا واقع
    d 9 true true false,         -- م٩ العنوانان حدّان وحيدان
    d 10 false true true,        -- م١٠ نسخةٌ ثانيةٌ تُختم — يعارضها المختوم
    d 11 false true false,       -- م١١ لا بصمةَ قبل التشغيل
    d 12 false true true,        -- م١٢ وقتٌ في السجلّ — يعارضه `--check`
    d 13 false true false [1, 2],-- م١٣ محرّكُ PDF — مبنيٌّ على م١ وم٢
    d 14 false true true ]       -- م١٤ «عموم اللفظ» لأرقام الصفحات — خروجٌ عن الموضوع

theorem sealL0_verdicts : (run sealL0).map (·.2) =
    [.khata, .khata, .zanni, .khata, .khata, .laHukm, .saqit, .laHukm, .qati, .khata, .zanni,
     .khata, .saqit, .khata] := by decide

/-- «الجامدُ للأجناس والمشتقُّ للصفات وعامودُ النسب»: ج١…ج١٠. -/
def jamid : List Daawa :=
  [ d 21 false true false,       -- الكلّيُّ جنسٌ ومشتقّ (ج3 ف406)
    d 22 false true false,       -- الجزئيُّ علمٌ وضمير، فيُستثنى العلم (ف407)
    d 23 false true true,        -- «الفاعليّة والمفعوليّة لا يحملهما إلّا المشتقّ» — ف393: «بين المفردات بضمّ بعضها إلى بعض»
    d 24 false true true [23],   -- المشتقُّ نسبةٌ محمولةٌ في مفردٍ لا تحتاج جملة
    d 25 false false false,      -- التقييديّةُ عمودُها الباء، والإضافيّةُ الحرف — لا نصّ
    d 26 false true false [24],  -- كثافةٌ إسناديّة بعدد المشتقّات
    d 27 true true true,         -- «أنيت الثماني» صورُ النسبة — `isnad_layer.py`: حروفٌ × حالتين، لا دعوى معجميّة
    d 28 true true true,         -- «الغرضُ من الوضع إفادةُ النسب» في ج1 — هو في ج3 لا ج1
    d 29 false true false [21, 24], -- N7: الجامدُ عقدة والمشتقُّ وتر
    d 30 false true true ]       -- «التحكيمُ المطابقةُ أوّلًا» — لا نصّ، ويعارضه ف551 والترجيحُ العشر

theorem jamid_verdicts : (run jamid).map (·.2) =
    [.zanni, .zanni, .khata, .saqit, .laHukm, .saqit, .khata, .khata, .saqit, .khata] := by decide

end A116.Qarar
