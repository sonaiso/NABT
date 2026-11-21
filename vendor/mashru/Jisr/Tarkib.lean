/-
  Jisr/Tarkib.lean — الجملة الاسمية والفعلية وشبه الجملة (الظرفية) بأقسام الكلم، ومركزها الإسناد: على مودَعين مختومين.

  المودَعان: «مغني اللبيب» لابن هشام (الباب الثاني: في تفسير الجملة وذكر أقسامها وأحكامها، L8682–8742 في النصّ المودَع)
  و«متن قطر الندى» له (L73–74). وجدول الأزواج عند المالك في حزمته (SLGE/Ladder2.lean: `ifada_pairs`، `nec_compose`،
  `fil_needs_ism`؛ SLGE/Category.lean: `three_structs`؛ SLGE/Wad.lean: `kalam_min_matches` على القطر).

  ما يُنقل من المغني (شاهدٌ لا نتيجة):
  * الجملة: الفعلُ وفاعله (قام زيد)، والمبتدأُ وخبره (زيد قائم)، وما كان بمنزلة أحدهما (L8684–8686) — فمركزُها الإسناد.
  * انقسامها (L8719–8724): الاسمية ما صدرها اسم، والفعلية ما صدرها فعل، والظرفية المصدَّرة بظرف أو مجرور «إذا قدرت زيدا
    فاعلا بالظرف والجار والمجرور لا بالاستقرار المحذوف» (L8724–8726) — فهي ظرفيةٌ بتقديرٍ واسميةٌ بتقديرٍ آخر: لا حكمَ بينهما.
  * «مرادنا بصدر الجملة المسند أو المسند إليه فلا عبرة بما تقدم عليهما من الحروف» (L8732–8733): أقائم الزيدان، لعل أباك منطلق،
    ما زيد قائما: اسمية؛ أقام زيد، إن قام زيد، قد قام زيد، هلا قمت: فعلية (L8733–8734).
  * «والمعتبر أيضا ما هو صدر في الأصل»: كيف جاء زيد فعليةٌ «لأن هذه الأسماء في نية التأخير» (L8736–8739: أسماء الاستفهام
    والمقدَّم من مفعول وحال)، ويا عبد الله فعليةٌ «والتقدير أدعو زيدا» (L8739–8742).
  * ما لا حكم فيه بنصّه: «أفي الدار زيد» اسميةٌ أو فعليةٌ أو ظرفيةٌ بثلاثة تقديرات (L8755–8758)؛ و«إذا قام زيد فأنا أكرمه» مبنيٌّ
    على الخلاف في عامل إذا: اسميةٌ أو فعلية (L8745–8754)، ومثلُها لو (L8712–8713) — فالشرط غير الجازم (11) بلا حكمٍ واحد.
  * الظرفية «بظرف أو مجرور» (L8724): الظرفُ اسمٌ لا يعرفه هذا المستوى (أقسام الكلم وأصناف العوامل)، فلا يُعرف منها إلّا المجرور
    بعد الجارّ (الصنف 7)؛ «أعندك زيد» فجوةٌ معلَنة.
  * القطر (L73–74): «وأقل ائتلافه من اسمين كزيد قائم، أو فعل واسم كقام زيد» — وهو عند المالك `Wad.kalam_min_matches`.

  ما يُبنى هنا: صدرُ الجملة (أوّل كلمةٍ ليست حرفًا ولا أداةَ شرطٍ أو استفهامٍ — في نية التأخير)، ونوعُها بصدرها، والشاهدُ
  بأمثلة المغني نفسها بأقسام الكلم وأصناف العوامل (Jisr/Awamil.lean)، وجدولُ ما يلي العاملَ الحرفيّ من الأقسام
  (العاملُ قبل معموله: من معادلات المالك).
-/
import Jisr.Awamil
import SLGE.Wad

namespace Jisr
namespace Tarkib
open SLGE.Cat (Kind)

/-- كلمة في التركيب: قسمها (اسم/فعل/حرف)، وصنفُها في جدول العوامل المئة إن كانت عاملًا (0 إن لم تكن). -/
structure Kalima where
  qism : Kind
  sinf : Nat := 0
deriving DecidableEq, Repr

/-- أنواع الجملة الثلاثة (المغني L8719). -/
inductive Naw | ismiyya | filiyya | zarfiyya
deriving DecidableEq, Repr

/-- لا يُعدّ صدرًا: الحرفُ (L8732–8733)، واسمُ الاستفهام (12) «في نية التأخير» (L8736–8739). -/
def laYusaddar (w : Kalima) : Bool := w.qism == .harf || (w.qism == .ism && w.sinf == 12)

/-- صدر الجملة: أوّل كلمة تُعدّ صدرًا (المسند أو المسند إليه)، مع ما قبلها مباشرةً. -/
def sadr : List Kalima → Option (Option Kalima × Kalima)
  | [] => none
  | [w] => if laYusaddar w then none else some (none, w)
  | w :: v :: ws => if laYusaddar w then (match sadr (v :: ws) with
      | some (none, s) => some (some w, s)
      | r => r) else some (none, w)

/-- نوع الجملة بصدرها. ما أوّلُه نداء (13) فعليةٌ بالتقدير «أدعو» (L8739–8742)؛ وما أوّلُه شرطٌ غير جازم (11) اسميةٌ أو فعلية
على الخلاف (L8745–8754) — الاثنتان لا حكم بينهما؛ واسمُ الشرط الجازم (10) صدرًا لا نصَّ فيه فلا حكم؛ والصدرُ الاسمُ بعد جارٍّ (7)
ظرفيةٌ أو فعليةٌ أو اسميةٌ بثلاثة تقديرات (L8755–8758). -/
def naw (ws : List Kalima) : List Naw :=
  match ws.head?.map (·.sinf) with
  | some 13 => [.filiyya]
  | some 11 => [.filiyya, .ismiyya]
  | _ =>
    match sadr ws with
    | some (qabl, s) =>
      match s.qism with
      | .fil => [.filiyya]
      | .ism => if s.sinf == 10 then []
                else if (qabl.map (·.sinf)) == some 7 then [.zarfiyya, .filiyya, .ismiyya] else [.ismiyya]
      | .harf => []
    | none => []

/-- **ثلاثة لا رابع:** ما لنوعه حكمٌ فمن الثلاثة (بالبناء). -/
theorem naw_thalatha (ws : List Kalima) (n : Naw) (h : n ∈ naw ws) :
    n = .ismiyya ∨ n = .filiyya ∨ n = .zarfiyya := by
  cases n <;> simp

/-! ## الشواهد: أمثلة المغني بعينها (L8720–8742) بأقسام الكلم وأصناف العوامل -/

def N : Kalima := ⟨.ism, 0⟩
def V : Kalima := ⟨.fil, 0⟩
def H : Kalima := ⟨.harf, 0⟩
def kana : Kalima := ⟨.fil, 1⟩          -- كان: فعلٌ ناسخ
def laalla : Kalima := ⟨.harf, 2⟩       -- لعلّ
def zanna : Kalima := ⟨.fil, 3⟩         -- ظنّ
def jarr : Kalima := ⟨.harf, 7⟩         -- في
def inShart : Kalima := ⟨.harf, 10⟩     -- إنْ الشرطية
def hamzaIst : Kalima := ⟨.harf, 12⟩    -- الهمزة
def kayfa : Kalima := ⟨.ism, 12⟩        -- كيف (اسم استفهام)
def ya : Kalima := ⟨.harf, 13⟩          -- يا
def idha : Kalima := ⟨.harf, 11⟩        -- إذا (شرط غير جازم)
def manShart : Kalima := ⟨.ism, 10⟩     -- مَن الشرطية

theorem shawahid_mughni :
    naw [N, N] = [.ismiyya] ∧                       -- زيد قائم
    naw [V, N] = [.filiyya] ∧                       -- قام زيد، ضرب اللص، يقوم زيد
    naw [kana, N, N] = [.filiyya] ∧                 -- كان زيد قائما (L8722)
    naw [zanna, N] = [.filiyya] ∧                   -- ظننته قائما
    naw [V] = [.filiyya] ∧                          -- قم (فاعله مستتر)
    naw [hamzaIst, N, N] = [.ismiyya] ∧             -- أقائم الزيدان، أزيد أخوك (L8733)
    naw [laalla, N, N] = [.ismiyya] ∧               -- لعل أباك منطلق
    naw [H, N, N] = [.ismiyya] ∧                    -- ما زيد قائما
    naw [hamzaIst, V, N] = [.filiyya] ∧             -- أقام زيد
    naw [inShart, V, N] = [.filiyya] ∧              -- إن قام زيد
    naw [H, V, N] = [.filiyya] ∧                    -- قد قام زيد
    naw [H, V] = [.filiyya] ∧                       -- هلا قمت
    naw [hamzaIst, jarr, N, N] = [.zarfiyya, .filiyya, .ismiyya] ∧   -- أفي الدار زيد: ثلاثة تقديرات (L8755–8758)
    naw [kayfa, V, N] = [.filiyya] ∧                -- كيف جاء زيد (L8737)
    naw [ya, N, N] = [.filiyya] ∧                   -- يا عبد الله: التقدير أدعو (L8740–8742)
    naw [idha, V, N, H, N, N] = [.filiyya, .ismiyya] ∧   -- إذا قام زيد فأنا أكرمه: على الخلاف (L8745–8754)
    naw [manShart, V, V] = [] ∧                     -- مَن يقم أقم: اسمُ الشرط صدرًا لا نصّ فيه — لا حكم
    naw [H] = [] ∧ naw [] = [] := by decide

/-! ## أقلّ الكلام وجدول الأزواج: عند المالك، وعلى القطر -/

/-- **الأزواج المفيدة من تسعة** (مبرهنة المالك `Ladder2.ifada_pairs` بعينها): اسمٌ واسم، اسمٌ وفعل، فعلٌ واسم؛ ولا يفيد
فعلٌ وحده ولا مع فعلٍ أو حرف (`fil_needs_ism`)؛ وبإسقاط الترتيب هي قولُ القطر «من اسمين أو فعل واسم» (`Wad.kalam_min_matches`). -/
theorem azwaj_mufida :
    ((SLGE.Cat.kinds.flatMap fun a => SLGE.Cat.kinds.map fun b => [a, b]).filter SLGE.Cat.ifada) =
      [[Kind.ism, Kind.ism], [Kind.ism, Kind.fil], [Kind.fil, Kind.ism]] ∧
    SLGE.Wad.qatrMin = [[Kind.ism, Kind.ism], [Kind.fil, Kind.ism]] :=
  ⟨SLGE.Cat.ifada_pairs, rfl⟩

/-- ما يلي العاملَ من صنف `c` مباشرةً (العاملُ قبل معموله): قسمُ أوّل أدوار معادلاته؛ وما لا معادلة له لا حكم (الاثنان). -/
def yaliAmil (c : Nat) : List Kind :=
  match Awamil.muadalat c with
  | [[]] => [.ism, .fil]
  | alts => (alts.filterMap fun alt => alt.head?.map fun (r, _) =>
      match Awamil.qismDawr r with | .ism => Kind.ism | .fil => Kind.fil).eraseDups

/-- **جدول ما يلي العامل:** النواسخ (1–3) والجارّ (7) والنداء (13) يليها اسم؛ الناصب (4) والجازم (5) والشرط الجازم (10)
يليها فعل؛ كاد (6) اسم؛ لام التعليل (9) اسمٌ أو فعل؛ والعطف (8) والشرط غير الجازم (11) والاستفهام (12) لا حكم. -/
theorem jadwal_yali :
    (List.range 14).map yaliAmil =
      [[.ism, .fil], [.ism], [.ism], [.ism], [.fil], [.fil], [.ism], [.ism], [.ism, .fil], [.ism, .fil],
       [.fil], [.ism, .fil], [.ism, .fil], [.ism]] := by decide

/-- بالتعريف: `yaliAmil` لا يُخرج حرفًا (أدوار المعادلات أسماء وأفعال، وما لا معادلة له اسمٌ أو فعل) — فلا يُعمَل في حرف. -/
theorem la_harf_bada_amil : (List.range 14).all (fun c => !(yaliAmil c).contains .harf) = true := by decide

end Tarkib
end Jisr
