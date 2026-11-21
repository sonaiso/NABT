import SLGE.Tarkib
import SLGE.Maqam

/-!
# أُطرٌ مركّبة على القانون نفسه: الشرطُ جملتان، والنداء، والاستفهام، وضميرُ الشأن، والموصولُ بصلته

كلُّ إطارٍ مركّبٍ هنا مكوَّنٌ من أُطر ‎Tarkib.framesL‎ مع قيمٍ زائدة (أداة، رابط، نوع منادى، موضع، سمة، عائد)،
لكلٍّ قانونٌ (ابتداء/وصل/وقف) يرخّصه، ورقمٌ يحمل مكوّناته كلَّها فلا يسقط منها شيء — ظاهرًا كان أو مقدَّرًا.
والشواهد (القطر، الألفيّة، المغني، سيبويه، QAC) تشهد ولا تبني.
-/

set_option synthInstance.maxSize 8192
set_option synthInstance.maxHeartbeats 0
set_option maxRecDepth 100000

namespace SLGE
namespace TarkibExt

open Tarkib Maqam

theorem fIdx_inj (f g : Frame) (hf : f ∈ framesL) (hg : g ∈ framesL) (h : fIdx f = fIdx g) : f = g := by
  have a := idxOf_getD f hf; have b := idxOf_getD g hg
  unfold fIdx at h; rw [← a, ← b, h]

/-! ## ١. الشرطُ إطارٌ ذو جملتين

الأدوات: ‎0‎ إنْ … ‎9‎ (الجازمة العشر في المرفق)، ‎10‎ إذا، ‎11‎ لو، ‎12‎ لولا، ‎13‎ لوما.
الرابط: ‎0‎ لا، ‎1‎ الفاء، ‎2‎ إذا الفجائيّة، ‎3‎ اللام (لجواب لو ولولا).
**القانون:** فعلُ الشرط جملةٌ فعليّة (إلّا بعد لولا: اسميّةٌ خبرُها محذوف)؛ والجوابُ إن لم يكن فعليّةً لزمه رابط؛
وإذا الفجائيّةُ مع إنْ وفي الاسميّة وحدها؛ ولا وقفَ على الشرط بلا جواب إلّا أن يدلّ عليه كلامٌ سابق. -/

def lawlaC1 : Frame := (0, 0, [(0, 0, 0), (1, 1, 0)])

def rabitOK (adat : Nat) (g : Frame) (rabit : Nat) : Bool :=
  rabit ≤ 3 && (g.1 == 1 || rabit == 1 || rabit == 2) && (rabit != 2 || (adat == 0 && g.1 == 0)) &&
  (rabit != 3 || adat == 11 || adat == 12)

def shartOK (adat : Nat) (c1 : Frame) (c2 : Option Frame) (rabit : Nat) (prev : Bool) : Bool :=
  adat ≤ 13 && framesL.contains c1 && (if adat == 12 then c1 == lawlaC1 else c1.1 == 1) &&
  match c2 with
  | none => prev && rabit == 0
  | some g => framesL.contains g && rabitOK adat g rabit

def jazim (adat : Nat) : Bool := adat < 10

/-- **معادلةُ الجزم** (‎Awamil.eqs 10‎): فعلُ الشرط مجزوم، والجوابُ الفعليّ بلا رابطٍ مجزوم، وبالرابط في محلّ جزم. -/
def shartState (adat rabit : Nat) : Option Nat × Option Nat :=
  if jazim adat then (some 3, if rabit == 0 then some 3 else none) else (none, none)

def c2Code : Option Frame → Nat
  | none => 0
  | some g => fIdx g + 1

def shEnc (adat : Nat) (c1 : Frame) (c2 : Option Frame) (rabit : Nat) : Nat :=
  pair adat (pair (fIdx c1) (pair (c2Code c2) rabit))

/-- **على الشواهد:** ‎إن تجتهدْ تنجحْ‎؛ ‎إن يمسسْك بخيرٍ فهو على كلّ شيءٍ قدير‎ (اسميّةٌ بالفاء)؛ ‎إذا هم يقنطون‎ (إذا الفجائيّة)؛
‎لولا الماءُ لهلك الزرعُ‎؛ ولا يُوقَف على الشرط بلا جواب، ولا تُقرن الاسميّةُ بلا رابط. -/
theorem shart_frames :
    shartOK 0 (1, 0, [(2, 0, 0), (3, 1, hudur)]) (some (1, 0, [(2, 0, 0), (3, 1, hudur)])) 0 false = true ∧
    shartOK 0 (1, 0, [(2, 0, 0), (3, 0, 0), (4, 0, 0)]) (some (0, 0, [(0, 0, 0), (1, 0, 0)])) 1 false = true ∧
    shartOK 0 (1, 0, [(2, 0, 0), (3, 0, 0), (4, 0, 0)]) (some (0, 0, [(0, 0, 0), (1, 0, 0)])) 2 false = true ∧
    shartOK 12 lawlaC1 (some (1, 0, [(2, 0, 0), (3, 0, 0)])) 3 false = true ∧
    shartOK 0 (1, 0, [(2, 0, 0), (3, 1, hudur)]) none 0 false = false ∧
    shartOK 0 (1, 0, [(2, 0, 0), (3, 0, 0), (4, 0, 0)]) (some (0, 0, [(0, 0, 0), (1, 0, 0)])) 0 false = false ∧
    shartOK 0 (0, 0, [(0, 0, 0), (1, 0, 0)]) (some (1, 0, [(2, 0, 0), (3, 0, 0)])) 0 false = false ∧
    shartOK 3 (1, 0, [(2, 0, 0), (3, 0, 0), (4, 0, 0)]) (some (0, 0, [(0, 0, 0), (1, 0, 0)])) 2 false = false := by
  decide +kernel

/-- **الإحالةُ بين جملتي الشرط:** فاعلُ الجواب المستتر يحيل إلى جملة الشرط قبله، ولو كان الشرطُ أوّلَ الكلام. -/
theorem shart_internal_ihala :
    shartOK 2 (1, 0, [(2, 0, 0), (3, 1, hudur), (4, 0, 0)]) (some (1, 0, [(2, 0, 0), (3, 1, sabiq)])) 0 false = true ∧
    shartState 2 0 = (some 3, some 3) ∧ shartState 0 1 = (some 3, none) ∧ shartState 11 3 = (none, none) := by
  decide +kernel

/-- **الاستنفاد في الجواب:** لكلّ أداةٍ جازمة، أزواجُ (جواب، رابط) المرخَّصة: ‎594‎ مع إنْ (لها إذا الفجائيّة)،
و‎426‎ مع غيرها؛ وفعلُ الشرط ‎128‎ إطارًا فعليًّا. -/
theorem shart_count :
    ((framesL.flatMap fun g => [0, 1, 2, 3].map fun r => (g, r)).filter fun p => rabitOK 0 p.1 p.2).length = 594 ∧
    ((framesL.flatMap fun g => [0, 1, 2, 3].map fun r => (g, r)).filter fun p => rabitOK 1 p.1 p.2).length = 426 ∧
    (framesL.filter (·.1 == 1)).length = 128 := by decide +kernel

/-- **الرقمُ يحمل الجملتين والأداةَ والرابط:** إطاران شرطيّان مرخَّصان رقمُهما واحد هما إطارٌ واحد. -/
theorem shart_value (a a' : Nat) (c1 c1' : Frame) (c2 c2' : Option Frame) (r r' : Nat)
    (h1 : shartOK a c1 c2 r false = true) (h2 : shartOK a' c1' c2' r' false = true)
    (h : shEnc a c1 c2 r = shEnc a' c1' c2' r') : a = a' ∧ c1 = c1' ∧ c2 = c2' ∧ r = r' := by
  unfold shEnc at h
  obtain ⟨ha, h⟩ := pair_injective h
  obtain ⟨hc1, h⟩ := pair_injective h
  obtain ⟨hc2, hr⟩ := pair_injective h
  unfold shartOK at h1 h2
  simp only [Bool.and_eq_true, List.contains_iff_mem] at h1 h2
  refine ⟨ha, fIdx_inj _ _ h1.1.1.2 h2.1.1.2 hc1, ?_, hr⟩
  cases c2 with
  | none => cases c2' with
    | none => rfl
    | some g' => simp at h1
  | some g => cases c2' with
    | none => simp at h2
    | some g' =>
      simp only [Bool.and_eq_true, List.contains_iff_mem] at h1 h2
      simp only [c2Code] at hc2
      exact congrArg some (fIdx_inj _ _ h1.2.1 h2.2.1 (by omega))

/-! ## ٢. النداء: المنادى يُثبت المخاطَبَ في المقام، ومحلُّه نصبٌ وإن بُني

الحرف: ‎0‎ يا، ‎1‎ أيا، ‎2‎ هيا، ‎3‎ آ، ‎4‎ أ. المنادى: ‎0‎ علمٌ مفرد، ‎1‎ نكرةٌ مقصودة (اسمُ الجنس)، ‎2‎ مضاف، ‎3‎ شبيهٌ بالمضاف،
‎4‎ نكرةٌ غير مقصودة، ‎5‎ اسمُ إشارة، ‎6‎ مضمر، ‎7‎ مندوب، ‎8‎ مستغاث (القطر L268–287).

**حذفُ الحرف مدرَّجٌ لا ثنائيّ** (الألفيّة L744–745: «وغيرَ مندوبٍ ومضمرٍ وما جا مستغاثًا قد يعرى … وذاك في اسم الجنس
والمشار له قلّ، ومن يمنعه فانصر عاذله»): ‎0‎ ممتنع (المندوب، المضمر، المستغاث)، ‎1‎ قليل (اسم الجنس، المشار إليه)،
‎2‎ جائز (العلم، المضاف، الشبيه به)، ‎3‎ غيرُ مصرَّح (النكرةُ غيرُ المقصودة: لا حكمَ، لا امتناع). والمحذوفُ ‎يا‎ وحدها. -/

def nidaDrop (mtype : Nat) : Nat :=
  if mtype == 6 || mtype == 7 || mtype == 8 then 0
  else if mtype == 1 || mtype == 5 then 1
  else if mtype == 4 then 3 else 2

def nidaOK (harf fill mtype : Nat) : Bool :=
  harf ≤ 4 && fill ≤ 1 && mtype ≤ 8 && (fill == 0 || (harf == 0 && (nidaDrop mtype == 1 || nidaDrop mtype == 2)))

/-- حالةُ الدالّ في آخر المنادى (‎none‎: مبنيٌّ أصلًا)، ومحلُّه نصبٌ دائمًا. -/
def nidaDal (mtype : Nat) : Option Nat :=
  if mtype ≤ 1 || mtype == 7 then some 1 else if mtype ≤ 4 then some 0 else if mtype == 8 then some 2 else none
def nidaMahall : Nat := 0

/-- **الحذفُ مدرَّج (شاهدُه الألفيّة):** ممتنعٌ في ثلاثة، قليلٌ في اثنين، جائزٌ في ثلاثة، وغيرُ مصرَّحٍ في واحد — ولا يُستنتج الامتناعُ
من غياب النصّ. **والاستنفاد:** ‎50‎ رأسَ نداءٍ مرخَّصًا (‎45‎ بحرفٍ ظاهر و‎5‎ بمقدَّر). **والمحلُّ غيرُ الدالّ:** العلمُ المفرد والنكرةُ
المقصودة دالُّهما ضمّة ومحلُّهما نصب، والمستغاثُ مجرورُ اللفظ منصوبُ المحلّ. -/
theorem nida_heads :
    (List.range 9).map nidaDrop = [2, 1, 2, 2, 3, 1, 0, 0, 0] ∧
    (((List.range 5).flatMap fun h => (List.range 2).flatMap fun f => (List.range 9).map fun m => (h, f, m)).filter
      (fun x => nidaOK x.1 x.2.1 x.2.2)).length = 50 ∧
    nidaDal 0 ≠ some nidaMahall ∧ nidaDal 1 ≠ some nidaMahall ∧ nidaDal 8 ≠ some nidaMahall ∧
    nidaDal 2 = some nidaMahall ∧ nidaDal 4 = some nidaMahall := by decide

/-- **‎يا زيدُ قُمْ‎:** النداءُ مرخَّص، والفاعلُ المستتر في ‎قُمْ‎ مخاطَبٌ يحيل إلى المنادى أو إلى المقام؛
و‎رجلُ أقبِلْ‎ (حذفٌ مع اسم الجنس) مرخَّصٌ قليلًا، و‎وا زيداه‎ لا يُحذف حرفُه، وحذفُه مع النكرة غيرِ المقصودة لا حكمَ له. -/
theorem nida_mukhatab :
    nidaOK 0 0 0 = true ∧ (1, 0, [(2, 0, 0), (3, 1, hudur)]) ∈ framesL ∧
    refOK (2, 0, 0) 1 [(2, 0, 0)] false false false = true ∧ refOK (2, 0, 0) hudur [] false false false = true ∧
    nidaOK 0 1 1 = true ∧ nidaDrop 1 = 1 ∧ nidaOK 0 1 7 = false ∧ nidaDrop 7 = 0 ∧
    nidaOK 0 1 4 = false ∧ nidaDrop 4 = 3 := by decide +kernel

def nidaEnc (harf fill mtype : Nat) (f : Frame) (ws : List (List Nat)) : Nat :=
  pair (pair harf (pair fill mtype)) (sEnc f ws)

/-- **الحرفُ المقدَّر قيمةٌ في ‎n‎:** ‎يا زيدُ‎ و‎زيدُ‎ (بحرفٍ مقدَّر) رقمان مختلفان للكلمات نفسِها. -/
theorem nida_value (f : Frame) (ws : List (List Nat)) : nidaEnc 0 0 0 f ws ≠ nidaEnc 0 1 0 f ws := by
  intro h; have := (pair_injective (pair_injective (pair_injective h).1).2).1; simp at this

/-! ## ٣. الاستفهام: له الصدارة، فيُلجئ إلى التقديم

الأدوات: ‎0‎ هل، ‎1‎ الهمزة (حرفان يدخلان على الجملة كلّها)؛ ‎2‎ مَن، ‎3‎ ما، ‎4‎ ماذا، ‎5‎ أيّ، ‎6‎ كم (أسماءٌ في دورٍ من أدوار الإطار)،
‎7‎ كيف، ‎8‎ أين، ‎9‎ متى (خبرٌ أو فضلة). -/

def istRoles (t : Nat) : List Nat := if t ≤ 1 then [] else if t ≤ 6 then [0, 1, 4] else [1, 4]

def istOK (t : Nat) (f : Frame) (i : Nat) : Bool :=
  t ≤ 9 && framesL.contains f &&
  (if t ≤ 1 then i == 0
   else i == 0 && (f.2.2.getD i (99, 9, 0)).2.1 == 0 && (istRoles t).contains (f.2.2.getD i (99, 9, 0)).1)

/-- **الصدارة:** ‎مَن رأيتَ؟‎ (المفعولُ مقدَّم) مرخَّص و‎رأيتَ مَن؟‎ لا؛ ‎كيف حالُك؟‎ خبرٌ مقدَّم؛ ‎مَن قام؟‎ مبتدأٌ خبرُه جملة؛
والاسمُ الاستفهاميّ لا يكون مقدَّرًا. -/
theorem istifham_sadara :
    istOK 2 (1, 0, [(4, 0, 0), (2, 0, 0), (3, 1, hudur)]) 0 = true ∧
    istOK 2 (1, 0, [(2, 0, 0), (3, 1, hudur), (4, 0, 0)]) 2 = false ∧
    istOK 2 (0, 0, [(0, 0, 0), (1, 0, 0)]) 1 = false ∧
    istOK 7 (0, 0, [(1, 0, 0), (0, 0, 0)]) 0 = true ∧
    istOK 7 (0, 0, [(0, 0, 0), (1, 0, 0)]) 0 = false ∧
    istOK 2 (0, 0, [(0, 0, 0), (2, 0, 0), (3, 1, 1)]) 0 = true ∧
    istOK 2 (0, 0, [(0, 1, 0), (1, 0, 0)]) 0 = false ∧
    istOK 0 (1, 0, [(2, 0, 0), (3, 1, hudur)]) 0 = true := by decide +kernel

/-- **الاستنفاد:** أُطرُ الاستفهام المرخَّصة لكلّ أداة. -/
theorem istifham_count :
    (List.range 10).map (fun t => (framesL.filter fun f => istOK t f 0).length) =
      [298, 298, 42, 42, 42, 42, 42, 26, 26, 26] := by decide +kernel

def istEnc (t : Nat) (f : Frame) (ws : List (List Nat)) : Nat := pair t (sEnc f ws)

/-! ## ٤. ضميرُ الشأن: الغائبُ الوحيد بلا مرجعٍ سابق — مرجعُه الجملةُ بعده

العامل: ‎0‎ الابتداء، ‎1‎ كان، ‎2‎ إنّ، ‎3‎ أنْ المخفّفة، ‎4‎ كأنْ المخفّفة.
القطر L191–194: «وأمّا أنْ فتعمل، ويجب … حذفُ اسمها ضمير الشأن، وكونُ خبرها جملةً مفصولةً — إن بُدئت بفعلٍ متصرّفٍ غير دعاء —
بقد أو تنفيسٍ أو نفيٍ أو لو. وأمّا كأنْ فتعمل ويقلّ ذكرُ اسمها، ويُفصل الفعلُ منها بلم أو قد».
الفاصل: ‎0‎ لا، ‎1‎ قد، ‎2‎ تنفيس (السين/سوف)، ‎3‎ نفي، ‎4‎ لو، ‎5‎ لم. ‎jamid‎: الفعلُ جامد (ليس، عسى) أو دعاء. -/

def faslOK (amil : Nat) (inner : Frame) (jamid : Bool) (fasl : Nat) : Bool :=
  if (amil == 3 || amil == 4) && inner.1 == 1 && !jamid then
    (if amil == 3 then fasl == 1 || fasl == 2 || fasl == 3 || fasl == 4 else fasl == 5 || fasl == 1)
  else fasl == 0

def shaanOK (amil pfill : Nat) (feat : Feat) (inner : Frame) (jamid : Bool) (fasl : Nat) : Bool :=
  amil ≤ 4 && refOK feat shaan [] false true false && framesL.contains inner &&
  (if amil == 3 then pfill == 1 else if amil == 1 || amil == 4 then pfill ≤ 1 else pfill == 0) &&
  faslOK amil inner jamid fasl

/-- **‎قل هو الله أحد‎؛ ‎عَلِمَ أنْ سيكونُ‎ (أنْ مخفّفة، شأنٌ محذوف، فاصلُ التنفيس)، ولا تُرخَّص بلا فاصل؛
‎وأنْ ليس للإنسان‎ (فعلٌ جامد بلا فاصل)؛ ‎كأنْ لم تغنَ‎ (كأنْ بلم)، ولا تُفصل بالسين؛ ولا شأنَ بجمعٍ ولا بمتكلّم.** -/
theorem shaan_frames :
    shaanOK 0 0 (3, 0, 0) (0, 0, [(0, 0, 0), (1, 0, 0)]) false 0 = true ∧
    shaanOK 3 1 (3, 0, 0) (1, 0, [(2, 0, 0), (3, 0, 0)]) false 2 = true ∧
    shaanOK 3 1 (3, 0, 0) (1, 0, [(2, 0, 0), (3, 0, 0)]) false 0 = false ∧
    shaanOK 3 1 (3, 0, 0) (1, 0, [(2, 0, 0), (3, 0, 0)]) true 0 = true ∧
    shaanOK 3 1 (3, 0, 0) (0, 0, [(0, 0, 0), (1, 0, 0)]) false 0 = true ∧
    shaanOK 4 1 (3, 0, 0) (1, 0, [(2, 0, 0), (3, 1, sabiq)]) false 5 = true ∧
    shaanOK 4 1 (3, 0, 0) (1, 0, [(2, 0, 0), (3, 1, sabiq)]) false 2 = false ∧
    shaanOK 3 0 (3, 0, 0) (1, 0, [(2, 0, 0), (3, 0, 0)]) false 2 = false ∧
    shaanOK 0 0 (3, 0, 2) (0, 0, [(0, 0, 0), (1, 0, 0)]) false 0 = false ∧
    shaanOK 0 0 (1, 2, 0) (0, 0, [(0, 0, 0), (1, 0, 0)]) false 0 = false := by decide +kernel

def shaanEnc (amil pfill : Nat) (feat : Feat) (inner : Frame) (fasl : Nat) (ws : List (List Nat)) : Nat :=
  pair (pair amil (pair pfill (pair (featCode feat) fasl))) (sEnc inner ws)

/-! ## ٥. الموصولُ بصلته: الصلةُ إطارٌ، والعائدُ خانةٌ فيه تحيل إلى الموصول -/

/-- العائد: ‎0‎ فاعلٌ مستتر يحيل إلى السابق (الموصول)، ‎1‎ ضميرٌ متّصل بمعمولٍ ظاهر، ‎2‎ مفعولٌ محذوف. -/
def mawsulOK (mfeat : Feat) (sila : Frame) (aidKind : Nat) (aidFeat : Feat) : Bool :=
  silaOK mfeat aidFeat aidKind && framesL.contains sila && sila.1 != 2 &&
  (if aidKind == 0 then sila.2.2.contains (3, 1, sabiq)
   else if aidKind == 2 then sila.2.2.contains (4, 1, 0)
   else sila.2.2.any fun x => (x.1 == 4 || x.1 == 6) && x.2.1 == 0)

/-- **‎الذي قامَ‎** (عائدٌ مستتر) مرخَّص و‎التي قامَ‎ لا؛ **‎ما عملتْه أيديهم‎** بعائدٍ محذوف مرخَّص؛ ولا صلةَ بلا عائد. -/
theorem mawsul_frames :
    mawsulOK (3, 0, 0) (1, 0, [(2, 0, 0), (3, 1, sabiq)]) 0 (3, 0, 0) = true ∧
    mawsulOK (3, 1, 0) (1, 0, [(2, 0, 0), (3, 1, sabiq)]) 0 (3, 0, 0) = false ∧
    mawsulOK (3, 2, 0) (1, 0, [(2, 0, 0), (3, 0, 0), (4, 1, 0)]) 2 (3, 0, 0) = true ∧
    mawsulOK (3, 0, 0) (1, 0, [(2, 0, 0), (3, 0, 0)]) 0 (3, 0, 0) = false ∧
    mawsulOK (3, 0, 0) (1, 0, [(2, 0, 0), (3, 0, 0)]) 2 (3, 0, 0) = false := by decide +kernel

def mawsulEnc (mfeat : Feat) (sila : Frame) (aidKind : Nat) (aidFeat : Feat) (ws : List (List Nat)) : Nat :=
  pair (pair (featCode mfeat) (pair aidKind (featCode aidFeat))) (sEnc sila ws)

/-- **العائدُ المحذوف قيمةٌ في ‎n‎:** الصلةُ نفسُها بعائدٍ محذوفٍ وبضميرٍ متّصل رقمان مختلفان. -/
theorem aid_value (sila : Frame) (ws : List (List Nat)) :
    mawsulEnc (3, 2, 0) sila 2 (3, 0, 0) ws ≠ mawsulEnc (3, 2, 0) sila 1 (3, 0, 0) ws := by
  intro h; have := (pair_injective (pair_injective (pair_injective h).1).2).1; simp at this

end TarkibExt
end SLGE
