/-
  Aql/TashfirAzmina.lean — جسرُ المعلومة المعمَّم (الرابع): طيُّ وفكُّ Aql.Azmina.Izaha (الإزاحةُ عن الآن:
  عددٌ صحيحٌ من وحدة)، باستعمال `zigzag`/`unzigzag` من Madlul/TashfirMadda.lean للحقل الصحيح وحدَه، وترميزِ
  تعدادٍ صغيرٍ جديدٍ لـ`Wahda` (خمسُ قيم) على نمط Khawass.

  السند: نفسُ تفويض المالك 2026-10-17 22:55؛ azmina من الاسم الثمانيّ. اختيرت رابعةً لأنّها تكشف فرقًا بنائيًّا
  لم تُحتَجه القطعتان السابقتان: لـ`Izaha` **حقلٌ صحيحٌ طليقٌ واحدٌ فقط** (`adad : Int`) مع تعدادٍ صغيرٍ محدودٍ
  مرافقٍ (`wahda : Wahda`، خمسُ قيم) — لا حقلانِ طليقانِ فأكثر كـMadda (ثلاثةٌ) وMirsat (أربعة). ولمّا كان
  `SLGE.mixEnc B C o k₁ k₂` الفعليُّ (`(o*B+k₁)*C+k₂`) لا يشترط حدًّا على `o` أصلًا (مبرهنةُ الفكّ
  `mixDec_enc` بلا فرضٍ عليه، فرضاها فقط على `k₁<B`،`k₂<C`) — فحقلُ Izaha الصحيحُ الوحيدُ يوضَع في موضع
  `o` غيرِ المقيَّد، والتعدادُ الصغيرُ (محدودٌ بخمسةٍ بالفعل، لا يحتاج BOUND خارجيًّا) في موضع `k₁` المقيَّد
  بـ5، وصفرٌ في `k₂` المقيَّد بـ1. **النتيجة: لا شرطَ Sahih ولا Subtype ولا Classical.choice هنا أصلًا —
  رغم وجود حقلٍ Int طليقٍ** (بخلاف Madda/Mirsat اللذين احتاجا BOUND خارجيًّا لأنّ لهما حقلين فأكثر طليقين
  يتزاحمان على مواضع mixEnc المقيَّدة، فلا يكفي أحدُهما وحده موضعَ `o` غيرَ المقيَّد). هذا فرقٌ بنائيٌّ بين
  «حقلٌ طليقٌ واحد» و«حقلانِ طليقانِ فأكثر» لا رأيٌ، مؤكَّدٌ بـ`#print axioms` (لا `Classical.choice` في أيٍّ
  من الخمس) تمامًا كما تأكَّد عكسُه (الحاجةُ الحقيقيّةُ إلى Classical.choice) في Mirsat.

  ما يُبرهن هنا: `wahda_dec_enc`/`wahdaEnc_lt` (التعدادُ)، `izaha_dec_enc` (نقلٌ مباشرٌ لـ`SLGE.mixDec_enc`
  مرّةً و`zigzag_unzigzag` مرّةً — طبقةٌ واحدةٌ لا طبقتان، لحقلٍ طليقٍ واحد)، `tayyIzaha_la_yudi` (`Tayy Izaha
  Nat` مباشرةً — لا Unit/Subtype، كـKhawass لا كMadda/Mirsat)، وعلى الشاهد `izaha_asma_tudi`: طيُّ وفكُّ
  **كلِّ** الإزاحات الستّ عشرة المسمَّاة في `Aql.Azmina.asma` بأسمائها (الآن، أمس، الغد، بعد غد، عام أوّل، عام
  قابل، …) — لا شاهدًا مبنيًّا جديدًا، بل الأسماءُ الموجودةُ في الملفّ نفسِه، أشملُ وأوثقُ من شواهدَ مبنيّةٍ
  لهذه القطعة بعينها.

  مؤجَّلٌ: alaqat/hawass/awwaliyyat/makan/isnad (خمسةٌ من ثمانيةٍ فُوِّضت تبقى)، وجسورُ العوامل/الإسناد/Itar3.
  ملاحظةُ البوّابة الكاملة (`bawwaba.py`، ساعتان+ لا تكفي محليًّا لـ175 طفرةً الآن) مكرَّرةٌ من البندين
  السابقين؛ الاعتمادُ هنا أيضًا على `lake build`/`lake env lean Audit.lean` المباشرَين وتجريبِ الطفرات يدويًّا.
-/
import Madlul.TashfirMadda
import Aql.Azmina

set_option autoImplicit false

namespace Aql.TashfirAzmina

open Mawsua Madlul.TashfirMadda Aql.Azmina

/-- ترميزُ الوحدات الخمس: الساعة 0 … السنة 4. -/
def wahdaEnc : Wahda → Nat
  | .saa => 0 | .yawm => 1 | .usbu => 2 | .shahr => 3 | .sana => 4

def wahdaDec : Nat → Wahda
  | 0 => .saa | 1 => .yawm | 2 => .usbu | 3 => .shahr | _ => .sana

theorem wahda_dec_enc (w : Wahda) : wahdaDec (wahdaEnc w) = w := by cases w <;> rfl
theorem wahdaEnc_lt (w : Wahda) : wahdaEnc w < 5 := by cases w <;> decide

/-- **الطيّ**: الحقلُ الصحيحُ الطليقُ في موضع `o` غيرِ المقيَّد، والوحدةُ في `k₁` المقيَّد بـ5. طبقةٌ واحدةٌ. -/
def izahaEnc (i : Izaha) : Nat := SLGE.mixEnc 5 1 (zigzag i.adad) (wahdaEnc i.wahda) 0

/-- **الفكّ**. -/
def izahaDec (n : Nat) : Izaha :=
  match SLGE.mixDec 5 1 n with
  | (adadC, wahdaC, _) => { adad := unzigzag adadC, wahda := wahdaDec wahdaC }

/-- **الفكُّ يعيد الأصل بلا شرطٍ أصلًا** — لا Sahih هنا: حقلٌ طليقٌ واحدٌ يكفيه موضعُ `o` غيرُ المقيَّد. -/
theorem izaha_dec_enc (i : Izaha) : izahaDec (izahaEnc i) = i := by
  simp only [izahaDec, izahaEnc,
    SLGE.mixDec_enc 5 1 (zigzag i.adad) (wahdaEnc i.wahda) 0 (wahdaEnc_lt i.wahda) Nat.zero_lt_one,
    zigzag_unzigzag, wahda_dec_enc]

/-- **الطيّ Tayy مباشرةً على Izaha نفسِه** — لا Unit/Subtype، كـ`TashfirKhawass.tayyKhawass` لا كـ
`TashfirMadda.tayyMadda`/`TashfirMirsat.tayyMirsat` (الحاجة إلى Subtype هناك من تزاحم حقلين طليقين فأكثر على
مواضع mixEnc المقيَّدة، لا من وجود حقلٍ طليقٍ بذاته). -/
def tayyIzaha : Tayy Izaha Nat where
  tawi := izahaEnc
  fakk := fun n => some (izahaDec n)
  fakk_tawi := fun i => by rw [izaha_dec_enc]

theorem tayyIzaha_la_yudi (i : Izaha) : tayyIzaha.fakk (tayyIzaha.tawi i) = some i :=
  tayyIzaha.fakk_tawi i

/-- على الشاهد: الإزاحاتُ الستّ عشرة المسمَّاةُ كلُّها في `Aql.Azmina.asma` — طيُّها وفكُّها يعيدها بعينها. -/
theorem izaha_asma_tudi : asma.map (fun p => izahaDec (izahaEnc p.2)) = asma.map (fun p => p.2) := by
  simp [izaha_dec_enc]

end Aql.TashfirAzmina
