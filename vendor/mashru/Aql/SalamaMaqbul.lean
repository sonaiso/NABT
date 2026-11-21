/-
  Aql/SalamaMaqbul.lean — الجسر من قبول الفاحص إلى الصدق في نموذج الدلالة: ما تقبله دالّةُ Lean `Qaida.maqbul` (التي يستعملها
  الفاحص التنفيذيّ faahis) صادقٌ في نموذج تفسير المدلول (`tafsir`)، متى كانت قوانين القاعدة على الهيئات المرخَّصة (`hq`)، وكانت
  أصولها صادقة (`hA`)، وكانت البنيةُ تُعدّي الاحتواء (`htadiya`).

  السند: تدقيقٌ خارجيّ رفعه المالك (2026-10-19) طلب بناء «مبرهنة حفظ الدليل في الاشتقاق المرخَّص» من الصفر؛ وفحصتُ
  فوجدتُها تركيبًا لمبرهنتين قائمتين: `Qaida.maqbul_murakhkhas` (المقبول مرخَّص) و`QawaninDalala.salama` (المرخَّص صادقٌ
  متى صدقت أصوله)؛ و`jawab_sadiq` تركيبُ `Qaida.jawab_sahih` مع `salama`. فلا تزيد الوحدةُ شيئًا على المبرهنات القائمة إلّا
  تسميةَ التركيب وتثبيتَه. بُني التركيب أوّلًا خارج المستودع (`lake env lean`، مسلّماته propext وQuot.sound)، وأذن المالك بنقله
  (2026-10-19 16:11: «أوافق على نقل المبرهنات وفق افضل الممارسات للمشروع»). وحدةٌ جديدة لا تعدّل Qaida.lean ولا
  QawaninDalala.lean.

  الحدّ (معلَن): المبرهنة مشروطة بالفروض الثلاثة. ولا مبرهنةَ أنّ القاعدة التي يقرؤها faahis من ملفٍّ تحقّق `hq` (يرشّح
  القوانين بـ `shakl` عند القراءة، `Faahis/Lib.lean`)، والوحدةُ خارج المحرّك في الأطلس. وفرضُ صدق الأصول `hA` لا تُخرجه
  هذه الوحدة ولا غيرها في Lean: أنّ ما سُجِّل أصلًا يقول
  فعلًا ما يُدّعى نقلٌ يُقرأ ويُراجَع (وسمه «مطابَق»)، لا عقلٌ يُبرهَن (ج3 729: اللغة تُعرف بالنقل لا بالعقل).
  فالجسر يحيل كلّ ثقةٍ في النتيجة إلى ثقةٍ في الأصول وحدها — لا أكثر.
-/
import Aql.Qaida
import Aql.QawaninDalala

namespace SalamaMaqbul
open Qaida QawaninDalala Dalala

section
variable {L α : Type} (W : Wad L α) (Z : Luzum α) (lf : Nat → L) (mn : Nat → Maana α)
  (Fi Taht : Nat → Nat → Prop)

/-- **المقبولُ صادق**: ادّعاءٌ قبل الفاحصُ سلسلتَه، في قاعدةٍ قوانينُها على الهيئات المرخَّصة، وأصولٌ صادقةٌ في النموذج، وبنيةٌ
    تُعدّي الاحتواء — قولُه صادقٌ في النموذج. -/
theorem maqbul_sadiq (q : Qaida.Qaida Qadiyya) (aslB : Qadiyya → Bool) (c : Iddia Qadiyya)
    (hq : ∀ r ∈ q.qawanin, shakl r = true)
    (hA : ∀ a, aslB a = true → tafsir W Z lf mn Fi Taht a)
    (htadiya : ∀ z c p, Taht z c → Fi c p → Taht z p)
    (h : maqbul q aslB c = true) :
    tafsir W Z lf mn Fi Taht c.qawl :=
  salama W Z lf mn Fi Taht q hq (fun a => aslB a = true) hA htadiya (maqbul_murakhkhas q aslB c h)

/-- **الجوابُ صادقٌ كلُّه**: كلّ قولٍ في جوابٍ بالقاعدة q (`Jawab`: ادّعاءاتٌ كلّها مقبولة بالفاحص) صادقٌ في النموذج، بالشروط
    نفسِها. -/
theorem jawab_sadiq (q : Qaida.Qaida Qadiyya) (aslB : Qadiyya → Bool) (j : Jawab q aslB)
    (hq : ∀ r ∈ q.qawanin, shakl r = true)
    (hA : ∀ a, aslB a = true → tafsir W Z lf mn Fi Taht a)
    (htadiya : ∀ z c p, Taht z c → Fi c p → Taht z p) :
    ∀ c ∈ j.iddiaat, tafsir W Z lf mn Fi Taht c.qawl :=
  fun c hc => salama W Z lf mn Fi Taht q hq (fun a => aslB a = true) hA htadiya (jawab_sahih j c hc)

end

end SalamaMaqbul
