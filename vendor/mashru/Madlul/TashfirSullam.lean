/-
  Madlul/TashfirSullam.lean — تعميمُ آلة الطيّ والفكّ (Aql/Mawsua.lean: Tayy) على سلّم SLGE كلِّه
  (SLGE/Ladder.lean: مخرج ← حامل ← خانة ← مقطع ← كلمة ← جملة)، بدالّةٍ واحدةٍ تُفهرَس بدرجة السلّم n،
  لا بمثالٍ واحدٍ لكلّ انتقال (كما كان Madlul/Tashfir.lean: مثالٌ واحدٌ على حدّ المعجم/الجنس وحده).

  السند: طلب المالك 2026-10-17 (ردًّا على فشل CI في جسرٍ إلى SLGE: «هناك خلل في قراءة binary وعمل
  جسور الى slge يحتاج فهم للجبر المرخص المتدرج او قراءة الرياضيات من lean مباشرة وعمل دالة تحليل لل
  units = n») تعميم الطيّ على «unit = n» — أي دالّةٌ واحدةٌ تعمل على كلّ درجةٍ من درجات السلّم، لا
  أمثلةٌ متفرّقة لكلّ انتقال؛ وبقراءة رياضيّات Lean مباشرةً من SLGE/Ladder.lean لا بإعادة برهانٍ عليها.
  أكّد المالك عبر AskUserQuestion: الدالّةُ معمَّمةٌ على درجة السلّم n (لا واحدةٌ لكلّ انتقال)، وتُبنى
  الآن فوق مراقبة CI.

  كلّ درجةٍ من درجات SLGE.Ladder (0 المخرج←الحامل، 1 الحامل والحالة←الخانة، 2 الخانات←المقطع،
  3 المقاطع←الكلمة، 4 الكلمات←الجملة) لها حاملٌ خاصّ (Nat×Nat عند 0 و1، Syl عند 2، List Syl عند 3،
  List (List Syl) عند 4) وشرطُ صحّةٍ خاصّ تحتاجه مبرهنةُ الفكّ في SLGE نفسِه (carrier_dec_enc،
  cell_dec_enc، syl_dec_enc، word_dec_enc، sent_dec_enc على الترتيب، بنصّها دون تغيير) — وTayy يحتاج
  فكًّا غيرَ مشروط (∀ a، لا بشرط). فالحلّ: حاملُ كلّ درجةٍ هنا هو حاملُ SLGE الخامّ مقيَّدًا بشرط صحّته
  (Subtype)، لا حاملَه الخامّ وحده؛ وفكُّ الدرجة يفحص الشرط على المُفكوك الخامّ (الصحّةُ قرارٌ على
  مسنداتٍ كلّها من حدود Nat واقتراناتها وكمّياتها الشاملة على قوائم — قرارٌ بالضرورة الكلاسيكيّة لا
  حسابًا، فاستُعمل Classical.propDecidable وحده دون آلةٍ جديدة؛ وهو مبنيٌّ على Classical.choice
  المسلَّمِ المرخَّص في الدستور أصلًا، فلا مسلَّمةٌ جديدة).

  ما يُبرهن هنا:
  ١. فكُّ كلّ درجةٍ يعيد أصلها الخامّ بعينه بشرط صحّته (fakkRaw_tawiRaw)، على الخمس درجاتٍ بدالّةٍ واحدة
     مطابقةً لنمط مبرهنات SLGE الخمس — كلّ حالةٍ نقلٌ مباشرٌ لمبرهنة SLGE بعينها، بلا decide ولا إعادة
     برهانٍ على شاهد.
  ٢. ففكُّ الطيّ على الحامل المقيَّد يعيد أصله بعينه (fakkOf_tawiOf)، نتيجةً مباشرة للأولى.
  ٣. فـTayy (SlgeUnit n) Nat لكلّ درجةٍ n، بتركيبةٍ واحدة (tayyOf) — نظيرُ Madlul/Tashfir.lean (مثالٌ
     واحدٌ على Qism) ممتدٌّ إلى السلّم كلِّه: خمس درجاتٍ بدالّةٍ واحدةٍ لا بخمس دوالّ متفرّقة.
-/
import Aql.Mawsua
import SLGE.Ladder

namespace Madlul.TashfirSullam

open Mawsua SLGE

/-- حاملُ كلّ درجة، خامًّا (بلا شرط صحّة) — نفسُ أنواع SLGE.Ladder بعينها: 0 المخرج/الرتبة (Nat×Nat)،
1 الحامل/الحالة (Nat×Nat)، 2 المقطع (Syl)، 3 الكلمة (List Syl)، 4 الجملة (List (List Syl)). -/
def Carrier : Fin 5 → Type
  | 0 => Nat × Nat
  | 1 => Nat × Nat
  | 2 => Syl
  | 3 => List Syl
  | 4 => List (List Syl)

/-- شرطُ الصحّة الذي تحتاجه مبرهنةُ الفكّ في كلّ درجة، بنصّه في SLGE/Ladder.lean نفسِه حرفيًّا: حدّا
carrier_dec_enc، شرط cell_dec_enc، Valid لـsyl_dec_enc، وتعميمُها الشامل على القوائم لـword_dec_enc
وsent_dec_enc. -/
def Sahih : (n : Fin 5) → Carrier n → Prop
  | 0 => fun p => p.1 < 15 ∧ p.2 < makharijSizes.getD p.1 0
  | 1 => fun p => p.2 < 4
  | 2 => fun x => Valid x
  | 3 => fun (w : List Syl) => ∀ x ∈ w, Valid x
  | 4 => fun (S : List (List Syl)) => ∀ w ∈ S, ∀ x ∈ w, Valid x

/-- حاملُ الدرجة مقيَّدًا بصحّته: هذا حاملُ الطيّ A في Tayy A Nat لكلّ درجة. -/
def SlgeUnit (n : Fin 5) : Type := {a : Carrier n // Sahih n a}

/-- الطيّ الخامّ: رقمُ كلّ درجةٍ بدالّة SLGE نفسِها (carrierEnc...sentEnc)، بدالّةٍ واحدةٍ تُفهرَس بالدرجة. -/
def tawiRaw : (n : Fin 5) → Carrier n → Nat
  | 0 => fun p => carrierEnc p.1 p.2
  | 1 => fun p => cellEnc p.1 p.2
  | 2 => fun x => sylEnc x
  | 3 => fun w => wordEnc w
  | 4 => fun S => sentEnc S

/-- الفكُّ الخامّ: من الرقم إلى حامل الدرجة، بدالّة SLGE نفسِها (carrierDec...sentDec). -/
def fakkRaw : (n : Fin 5) → Nat → Carrier n
  | 0 => carrierDec
  | 1 => cellDec
  | 2 => sylDec
  | 3 => wordDec
  | 4 => sentDec

/-- **الفكُّ الخامّ يعيد الأصل** على كلّ درجةٍ بشرط صحّتها — نقلٌ مباشرٌ لمبرهنات SLGE الخمس
(carrier_dec_enc، cell_dec_enc، syl_dec_enc، word_dec_enc، sent_dec_enc)، بدالّةٍ واحدةٍ تُفهرَس
بالدرجة، بلا decide ولا إعادة برهان. -/
theorem fakkRaw_tawiRaw (n : Fin 5) (a : Carrier n) (h : Sahih n a) :
    fakkRaw n (tawiRaw n a) = a := by
  match n, a, h with
  | 0, (m, k), ⟨hm, hk⟩ => exact carrier_dec_enc m k hm hk
  | 1, (c, s), hs => exact cell_dec_enc c s hs
  | 2, x, hx => exact syl_dec_enc x hx
  | 3, w, hw => exact word_dec_enc w hw
  | 4, S, hS => exact sent_dec_enc S hS

/-- الطيّ على مستوى الدرجة المقيَّدة: رقمُ العنصر بدالّة SLGE الخامّة. -/
def tawiOf (n : Fin 5) (a : SlgeUnit n) : Nat := tawiRaw n a.1

/-- الفكّ على مستوى الدرجة المقيَّدة: يفكّ خامًّا ثمّ يفحص صحّة المفكوك (قرارٌ كلاسيكيّ لا حسابيّ؛
Classical.propDecidable وحده، على Classical.choice المسلَّم أصلًا) فيعيد بعض `SlgeUnit n` أو لا شيء. -/
noncomputable def fakkOf (n : Fin 5) (code : Nat) : Option (SlgeUnit n) :=
  @dite (Option (SlgeUnit n)) (Sahih n (fakkRaw n code)) (Classical.propDecidable _)
    (fun h => some ⟨fakkRaw n code, h⟩) (fun _ => none)

/-- **فكُّ الطيّ يعيد الأصل بعينه**، لكلّ درجةٍ، بدالّةٍ واحدة — نتيجةٌ مباشرة لـ`fakkRaw_tawiRaw`. -/
theorem fakkOf_tawiOf (n : Fin 5) (a : SlgeUnit n) : fakkOf n (tawiOf n a) = some a := by
  obtain ⟨a1, ha1⟩ := a
  show fakkOf n (tawiRaw n a1) = some ⟨a1, ha1⟩
  have heq : fakkRaw n (tawiRaw n a1) = a1 := fakkRaw_tawiRaw n a1 ha1
  unfold fakkOf
  rw [heq, dite_eq_left ha1]

/-- **الدالّةُ المعمَّمة**: طيٌّ معتبر (Mawsua.Tayy) على كلّ درجةٍ n من سلّم SLGE، بدالّةٍ واحدةٍ تُفهرَس
بالدرجة — لا بمثالٍ واحدٍ لكلّ انتقال كما في Madlul/Tashfir.lean (مثالُ Qism وحده على حدّ المعجم). -/
noncomputable def tayyOf (n : Fin 5) : Tayy (SlgeUnit n) Nat where
  tawi := tawiOf n
  fakk := fakkOf n
  fakk_tawi := fakkOf_tawiOf n

/-- لكلّ درجةٍ من الخمس: الطيُّ لا يُضيع شيئًا — شاهدٌ أنّ الدالّة المعمَّمة تغطّي السلّم كلَّه بفعلٍ
لا قولًا، مستمَدٌّ من `Tayy.fakk_tawi` نفسِها (Aql/Mawsua.lean) على كلّ درجة. -/
theorem tayyOf_la_yudi (n : Fin 5) (a : SlgeUnit n) :
    (tayyOf n).fakk ((tayyOf n).tawi a) = some a :=
  (tayyOf n).fakk_tawi a

end Madlul.TashfirSullam
