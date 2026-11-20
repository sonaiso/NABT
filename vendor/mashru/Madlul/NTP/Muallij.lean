/-
  Madlul/NTP/Muallij.lean — معالجُ NTP (Neurological Thinking Processing) على قاعدة Mashru: شبكةُ أجناسٍ ذوات خواصّ وقابليّات،
  مربوطةٌ جبريًّا بالـ116 عن طريق رقم جذر اللفظ الجامد، مرخَّصةٌ تدريجيًّا، وتنتشر فيها القوّةُ انتشارًا مفسَّرًا (صندوقٌ أبيض).

  السند (أقوال المالك 2026-11-16، بنصّها مختصرًا): «الوجود الذي له تواتر بالشهود … الماء حقيقة ويشهد أن له خاصية السيولة»؛
  «الإنسان والحيوان والنبات كائن حي من خواصه أن يحتاج الماء»؛ «قابلية الإنسان أن يكون متغذّيًا على الماء يكسبه صفة شارب وكذلك
  باقي الكائنات الحية»؛ «الزيتون والتفاح لا يتحرك لكنه له خاصية احتياج السائل»؛ «لا يوجد إلا كائنات حية تدخل السلسلة أو كائنات
  جماد وهذا رأس الهرم»؛ «لا يسمح لدخول جنس إلا وفق شهادة متواترة»؛ «الوجود يقين ولكن الصفات والقابليات يدخلها الاحتمال»؛
  «تبقى مرتبطة جبريًّا مع 116 والعلاقات قابلة للتشفير».
  ومن Mashru (مقروءة في الجلسة، لا منقولة): `Aql.martaba` (التفكير 65: الحكم بالوجود قطعيّ وبالحقيقة أو الصفة ظنّيّ)،
  `Madlul.Wiratha.battQ` (الفصل يبتّ ما تركه الجنس «لا حكم» ولا يناقضه)، `Madlul.Fard116.ramz`/`licB` (رقمُ الجذر وآلةُ ترخيصه).

  الخوارزميات (كلٌّ بمبرهناتها هنا):
  ١. القبولُ بالتواتر `yuqbal`: عددُ المصادر المستقلّة (لا عددُ الشهادات) ≥ K. مصدرٌ واحد — OpenCyc أو غيره — لا يُدخل شيئًا متى K ≥ 2.
  ٢. المرتبة `rutba`: يقينٌ للوجود المتواتر وحده؛ وكلُّ خاصّةٍ وقابليّةٍ وصفةٍ ظنٌّ بقوّةٍ هي عددُ شهودها؛ وموافقتُها `Aql.martaba`.
  ٣. رأسُ الهرم `far`: كلُّ عقدةٍ تحت «حيّ» أو «جماد» لا غير، وعقدةٌ آباؤها في الفرعين «لا حكم» (تُرفض).
  ٤. الوراثةُ متعدّدةُ الآباء `qima`: ما اتّفق عليه الآباء يُورَّث ولا ينقضه الفصل، وما اختلفوا فيه «لا حكم» يبتّه الفصل.
  ٥. المعالج `tashghil`: انتشارُ القوّة بالأدنى على المقدّمات والأعلى على القوانين (min-max)؛ رتيب، محدود، كلُّ زيادةٍ فيه
     منسوبةٌ إلى قانونٍ مسمّى مقدّماتُه كلُّها ليست أضعف منها، والوجودُ لا يُشتقّ.
  ٦. التشفير `shifra`/`fakk`: كلُّ علاقةٍ رقمٌ واحد يُفكّ إلى نفسها (تقابل)، وطرفاها رقما جذرين من آلة الـ116.

  حدود (معلنة): الشاهد في §٨ مبنيٌّ للبرهان لا مودَع؛ أعدادُ شهوده مفروضة لا مقيسة؛ وجذورُ ألفاظه تعيينُ البنّاء (الرقمُ من آلة
  المشروع بترتيب المخارج `Nabt.makharijCarriers`). مفتاحُ العقدة هنا رقمُ الجذر وحده، فلفظان من جذرٍ واحد (حيّ/حيوان) يتصادمان:
  المفتاحُ الصحيح رقمُ الكلمة = رقمُ الجذر × عددُ الأوزان + رقمُ الوزن (`SLGE/Root.lean`)، ولم يُبنَ هنا.
  وانتهاءُ المعالج إلى نقطةٍ ثابتة لم يُبرهَن (برهنتُ الرتابة والحدّ، وهما مقدّمتاه)، والتشغيلُ بوقودٍ معلَن.
  بلا sorry ولا axiom ولا native_decide.
-/
import Madlul.Wiratha
import Madlul.Fard116
import Aql.Aqliyya

namespace NTP
open Madlul.Tayin (Qima)

/-! ## ١. الشاهدُ والتواتر -/

/-- شاهدٌ: رقمُ مصدره المستقلّ في سجلّ المصادر، وبصمةُ موضعه. -/
structure Shahid where
  masdar : Nat
  basma  : String
deriving DecidableEq, Repr

/-- المصادرُ المتمايزة (بلا تكرار). -/
def mutamayyiz : List Nat → List Nat
  | [] => []
  | x :: xs => if x ∈ mutamayyiz xs then mutamayyiz xs else x :: mutamayyiz xs

/-- عددُ المصادر المستقلّة — لا عددُ الشهادات: ألفُ سطرٍ من مصدرٍ واحد شاهدٌ واحد. -/
def adad (sh : List Shahid) : Nat := (mutamayyiz (sh.map (·.masdar))).length

theorem mutamayyiz_wahid (c : Nat) :
    ∀ l : List Nat, (∀ x ∈ l, x = c) → mutamayyiz l = [] ∨ mutamayyiz l = [c]
  | [], _ => Or.inl rfl
  | x :: xs, h => by
    have hx : x = c := h x (by simp)
    have ih := mutamayyiz_wahid c xs (fun y hy => h y (by simp [hy]))
    subst hx
    rcases ih with e | e <;> simp [mutamayyiz, e]

/-- مصدرٌ واحدٌ مهما كثرت شهاداتُه عددُه واحدٌ على الأكثر. -/
theorem adad_masdar_wahid (c : Nat) (sh : List Shahid) (h : ∀ s ∈ sh, s.masdar = c) : adad sh ≤ 1 := by
  unfold adad
  have h' : ∀ x ∈ sh.map (·.masdar), x = c := by
    intro x hx
    simp only [List.mem_map] at hx
    obtain ⟨s, hs, rfl⟩ := hx
    exact h s hs
  rcases mutamayyiz_wahid c _ h' with e | e <;> simp [e]

/-- **القبول بالتواتر:** لا يدخل الشبكةَ جنسٌ (ولا علاقة) إلّا بعددٍ من المصادر المستقلّة لا يقلّ عن العتبة K. -/
def yuqbal (K : Nat) (sh : List Shahid) : Bool := decide (K ≤ adad sh) && decide (0 < adad sh)

/-- رقمُ OpenCyc في سجلّ المصادر (تعيين). -/
def cyc : Nat := 0

/-- **مصدرٌ واحدٌ لا يصنع تواترًا** (ومنه OpenCyc): متى كانت العتبة اثنين فأكثر، فشهاداتُ مصدرٍ واحدٍ لا تُدخل شيئًا. -/
theorem masdar_wahid_la_yudkhil (K c : Nat) (hK : 2 ≤ K) (sh : List Shahid) (h : ∀ s ∈ sh, s.masdar = c) :
    yuqbal K sh = false := by
  have := adad_masdar_wahid c sh h
  unfold yuqbal
  have : ¬ K ≤ adad sh := by omega
  simp [this]

theorem cyc_wahdahu_la_yudkhil (K : Nat) (hK : 2 ≤ K) (sh : List Shahid) (h : ∀ s ∈ sh, s.masdar = cyc) :
    yuqbal K sh = false := masdar_wahid_la_yudkhil K cyc hK sh h

/-! ## ٢. المرتبة: الوجودُ يقين، والصفاتُ والقابليّاتُ ظنٌّ بقوّة -/

inductive Naw | wujud | taht | khassa | qabiliyya | ihtiyaj | sifa
deriving DecidableEq, Repr

/-- المرتبة: «لا حكم» بلا شاهد (الغيابُ ليس امتناعًا)، ويقينٌ للوجود المتواتر وحده، وظنٌّ بقوّة c فيما عداه. -/
inductive Rutba | laHukm | zann (quwwa : Nat) | yaqin
deriving DecidableEq, Repr

def rutba (K : Nat) (n : Naw) (c : Nat) : Rutba :=
  if c = 0 then .laHukm else if n = .wujud ∧ K ≤ c then .yaqin else .zann c

theorem yaqin_iff (K : Nat) (n : Naw) (c : Nat) : rutba K n c = .yaqin ↔ n = .wujud ∧ K ≤ c ∧ c ≠ 0 := by
  unfold rutba
  by_cases h0 : c = 0 <;> by_cases h1 : (n = .wujud ∧ K ≤ c) <;> simp_all

/-- **لا يقين لغير الوجود:** الخاصّةُ والقابليّةُ والاحتياجُ والصفةُ والتصنيفُ ظنٌّ أبدًا، مهما كثر شهودها. -/
theorem ghayr_wujud_la_yaqin (K c : Nat) (n : Naw) (hn : n ≠ .wujud) : rutba K n c ≠ .yaqin :=
  fun h => hn ((yaqin_iff K n c).1 h).1

theorem la_shahid_la_hukm (K : Nat) (n : Naw) : rutba K n 0 = .laHukm := by simp [rutba]

def nawHukm : Naw → Aql.NawHukm
  | .wujud => .wujud
  | _ => .haqiqaAwSifa

def Rutba.martaba : Rutba → Aql.Martaba
  | .yaqin => .qati
  | _ => .zanni

/-- **الموافقة مع `Aql.martaba` القائمة في Mashru** (التفكير 65): القطعُ للوجود عن حسٍّ متواتر وحده. -/
theorem muwafaqat_aqliyya (K : Nat) (n : Naw) (c : Nat) :
    (rutba K n c).martaba = Aql.martaba (nawHukm n) (decide (K ≤ c ∧ c ≠ 0)) := by
  cases n <;> by_cases h0 : c = 0 <;> by_cases h1 : K ≤ c <;>
    simp_all [rutba, Rutba.martaba, nawHukm, Aql.martaba]

/-! ## ٣. رأسُ الهرم: حيٌّ أو جماد -/

inductive Ras | hayy | jamad
deriving DecidableEq, Repr

theorem ras_hasr (r : Ras) : r = .hayy ∨ r = .jamad := by cases r <;> simp

/-- الشبكة: العُقَدُ أرقامُ جذور ألفاظها الجامدة (من آلة الـ116). -/
structure Shabaka where
  aba    : Nat → List Nat        -- آباءُ العقدة
  ras    : Nat → Option Ras      -- عقدتا رأس الهرم
  fasl   : Nat → Nat → Qima      -- ما تزيده العقدة في الخاصّة p
  shuhud : Nat → List Shahid     -- شهودُ وجود الجنس

/-- اتّفاقُ الآباء على فرعٍ واحد، وإلّا لا شيء. -/
def ittifaq : List (Option Ras) → Option Ras
  | [] => none
  | x :: xs => if xs.all (· == x) then x else none

theorem ittifaq_tanaqud (l : List (Option Ras)) (h1 : some Ras.hayy ∈ l) (h2 : some Ras.jamad ∈ l) :
    ittifaq l = none := by
  cases l with
  | nil => simp at h1
  | cons x xs =>
    show (if xs.all (· == x) then x else none) = none
    split
    · rename_i hall
      simp only [List.all_eq_true, beq_iff_eq] at hall
      have e1 : some Ras.hayy = x := by
        rcases List.mem_cons.1 h1 with h | h
        · exact h
        · exact hall _ h
      have e2 : some Ras.jamad = x := by
        rcases List.mem_cons.1 h2 with h | h
        · exact h
        · exact hall _ h
      rw [← e2] at e1; cases e1
    · rfl

/-- فرعُ العقدة في رأس الهرم (بوقودٍ يحدّ العمق). -/
def far (sh : Shabaka) : Nat → Nat → Option Ras
  | 0, _ => none
  | k + 1, n =>
    match sh.ras n with
    | some r => some r
    | none => ittifaq ((sh.aba n).map (far sh k))

/-- **عقدةٌ آباؤها في الفرعين لا تدخل:** ما يجمع حيًّا وجمادًا (كما في شبكة Cyc متعدّدة الآباء) «لا حكم». -/
theorem far_tanaqud (sh : Shabaka) (k n a b : Nat) (hr : sh.ras n = none)
    (ha : a ∈ sh.aba n) (hb : b ∈ sh.aba n) (fa : far sh k a = some .hayy) (fb : far sh k b = some .jamad) :
    far sh (k + 1) n = none := by
  simp only [far, hr]
  apply ittifaq_tanaqud
  · exact List.mem_map.2 ⟨a, ha, fa⟩
  · exact List.mem_map.2 ⟨b, hb, fb⟩

/-- الدخولُ في الشبكة: تواترُ الوجود، وفرعٌ في رأس الهرم. -/
def yadkhul (sh : Shabaka) (K k n : Nat) : Bool := yuqbal K (sh.shuhud n) && (far sh k n).isSome

theorem dakhil_tahta_ras (sh : Shabaka) (K k n : Nat) (h : yadkhul sh K k n = true) :
    yuqbal K (sh.shuhud n) = true ∧ ∃ r, far sh k n = some r := by
  simp only [yadkhul, Bool.and_eq_true, Option.isSome_iff_exists] at h
  exact h

/-! ## ٤. الوراثةُ متعدّدةُ الآباء -/

/-- جمعُ قيم الآباء: فارغ، أو قيمةٌ واحدة اتّفقوا عليها، أو تناقض. -/
inductive Jam | farigh | wahid (v : Qima) | tanaqud
deriving DecidableEq, Repr

def jamKhatwa : Jam → Qima → Jam
  | j, .laHukm => j
  | .farigh, v => .wahid v
  | .wahid u, v => if u = v then .wahid u else .tanaqud
  | .tanaqud, _ => .tanaqud

def jam : List Qima → Jam
  | [] => .farigh
  | x :: xs => jamKhatwa (jam xs) x

def damj (l : List Qima) : Qima :=
  match jam l with
  | .wahid v => v
  | _ => .laHukm

theorem jam_farigh : ∀ l : List Qima, jam l = .farigh → ∀ x ∈ l, x = .laHukm
  | [], _ => by simp
  | x :: xs, h => by
    cases x with
    | laHukm =>
      have : jam xs = .farigh := by simpa [jam, jamKhatwa] using h
      intro y hy
      rcases List.mem_cons.1 hy with e | e
      · exact e
      · exact jam_farigh xs this y e
    | naam => cases hj : jam xs <;> simp [jam, jamKhatwa, hj] at h <;> split at h <;> cases h
    | la => cases hj : jam xs <;> simp [jam, jamKhatwa, hj] at h <;> split at h <;> cases h

theorem jam_wahid : ∀ (l : List Qima) (v : Qima), jam l = .wahid v →
    v ≠ .laHukm ∧ ∀ x ∈ l, x ≠ .laHukm → x = v
  | [], _, h => by simp [jam] at h
  | x :: xs, v, h => by
    by_cases hx : x = .laHukm
    · subst hx
      have h' : jam xs = .wahid v := by simpa [jam, jamKhatwa] using h
      obtain ⟨hv, hall⟩ := jam_wahid xs v h'
      refine ⟨hv, fun y hy hyl => ?_⟩
      rcases List.mem_cons.1 hy with e | e
      · exact absurd e hyl
      · exact hall y e hyl
    · have hjk : jam (x :: xs) = jamKhatwa (jam xs) x := rfl
      cases hj : jam xs with
      | farigh =>
        have hxv : x = v := by
          rw [hjk, hj] at h
          cases x <;> simp_all [jamKhatwa]
        subst hxv
        refine ⟨hx, fun y hy hyl => ?_⟩
        rcases List.mem_cons.1 hy with e | e
        · exact e
        · exact absurd (jam_farigh xs hj y e) hyl
      | wahid u =>
        obtain ⟨hu, hall⟩ := jam_wahid xs u hj
        have hux : u = x ∧ u = v := by
          rw [hjk, hj] at h
          cases x <;> simp_all [jamKhatwa] <;> split at h <;> simp_all
        obtain ⟨e1, e2⟩ := hux
        subst e2
        refine ⟨hu, fun y hy hyl => ?_⟩
        rcases List.mem_cons.1 hy with e | e
        · rw [e, e1]
        · exact hall y e hyl
      | tanaqud =>
        rw [hjk, hj] at h
        cases x <;> simp [jamKhatwa] at h

/-- **ما بتّه الدمجُ لا يخالفه أبٌ باتّ.** -/
theorem damj_la_yunaqid (l : List Qima) (v : Qima) (hv : damj l = v) (hne : v ≠ .laHukm) :
    ∀ x ∈ l, x ≠ .laHukm → x = v := by
  unfold damj at hv
  split at hv
  · rename_i w hw; subst hv; exact (jam_wahid l w hw).2
  · exact absurd hv.symm hne

theorem jam_ittifaq (v : Qima) (hv : v ≠ .laHukm) :
    ∀ l : List Qima, l ≠ [] → (∀ x ∈ l, x = v) → jam l = .wahid v
  | [], h, _ => absurd rfl h
  | [x], _, h => by
    have : x = v := h x (by simp)
    subst this
    cases x <;> simp_all [jam, jamKhatwa]
  | x :: y :: ys, _, h => by
    have ih := jam_ittifaq v hv (y :: ys) (by simp) (fun z hz => h z (List.mem_cons_of_mem _ hz))
    have : x = v := h x (by simp)
    subst this
    show jamKhatwa (jam (y :: ys)) x = .wahid x
    rw [ih]
    cases x <;> simp_all [jamKhatwa]

/-- قيمةُ الخاصّة p في العقدة n بالوراثة (بوقود k): دمجُ الآباء، ثمّ يبتّ الفصلُ ما بقي «لا حكم» (`Wiratha.battQ`). -/
def qima (sh : Shabaka) : Nat → Nat → Nat → Qima
  | 0, n, p => sh.fasl n p
  | k + 1, n, p => Madlul.Wiratha.battQ (damj ((sh.aba n).map (fun a => qima sh k a p))) (sh.fasl n p)

/-- **ما اتّفق عليه الآباءُ يُورَّث ولا ينقضه الفصل** (الزيتونُ والتفّاحُ يرثان احتياجَ الماء وإن لم يتحرّكا). -/
theorem warith_la_yunqad (sh : Shabaka) (k n p : Nat) (v : Qima) (hv : v ≠ .laHukm)
    (hne : sh.aba n ≠ []) (hall : ∀ a ∈ sh.aba n, qima sh k a p = v) :
    qima sh (k + 1) n p = v := by
  have hd : damj ((sh.aba n).map (fun a => qima sh k a p)) = v := by
    unfold damj
    rw [jam_ittifaq v hv _ (by simpa using hne)]
    intro x hx
    obtain ⟨a, ha, rfl⟩ := List.mem_map.1 hx
    exact hall a ha
  simp only [qima, hd]
  cases v <;> first | rfl | exact absurd rfl hv

/-- **الفصلُ يبتّ ما تركه الآباء «لا حكم»** (ومنه ما تناقضوا فيه). -/
theorem fasl_yabutt (sh : Shabaka) (k n p : Nat)
    (h : damj ((sh.aba n).map (fun a => qima sh k a p)) = .laHukm) :
    qima sh (k + 1) n p = sh.fasl n p := by
  simp only [qima, h]; rfl

/-! ## ٥. المعالج: انتشارُ القوّة على العلاقات -/

inductive Alaqa | wujud | taht | khassa | qabMafool | ihtiyaj | sifa
deriving DecidableEq, Repr

/-- العلاقة: نوعُها وطرفاها (رقما جذرين، والطرفُ الثاني قد يكون رقمَ خاصّةٍ أو فعل). -/
structure Haqiqa where
  alaqa : Alaqa
  a : Nat
  b : Nat
deriving DecidableEq, Repr

def Haqiqa.naw (h : Haqiqa) : Naw :=
  match h.alaqa with
  | .wujud => .wujud
  | .taht => .taht
  | .khassa => .khassa
  | .qabMafool => .qabiliyya
  | .ihtiyaj => .ihtiyaj
  | .sifa => .sifa

structure Qanun where
  ism : String
  muqaddimat : List Haqiqa
  natija : Haqiqa

/-- أدنى القوى (ولا شيء من قانونٍ بلا مقدّمات). -/
def minL : List Nat → Nat
  | [] => 0
  | [x] => x
  | x :: y :: ys => min x (minL (y :: ys))

theorem minL_le : ∀ (l : List Nat), ∀ y ∈ l, minL l ≤ y
  | [], _, h => by simp at h
  | [x], y, h => by simp at h; subst h; simp [minL]
  | x :: y :: ys, z, h => by
    rcases List.mem_cons.1 h with e | e
    · subst e; simp [minL]; omega
    · have := minL_le (y :: ys) z e
      simp only [minL]; omega

theorem minL_hadd (B : Nat) : ∀ l : List Nat, (∀ y ∈ l, y ≤ B) → minL l ≤ B
  | [], _ => by simp [minL]
  | x :: xs, h => Nat.le_trans (minL_le (x :: xs) x (by simp)) (h x (by simp))

/-- ما يشتقّه القانونُ للحقيقة h: أدنى قوى مقدّماته إن كانت h نتيجتَه. -/
def ishtiqaqWahid (s : Haqiqa → Nat) (h : Haqiqa) (r : Qanun) : Nat :=
  if r.natija = h then minL (r.muqaddimat.map s) else 0

def ishtiqaq (s : Haqiqa → Nat) (h : Haqiqa) : List Qanun → Nat
  | [] => 0
  | r :: rs => max (ishtiqaqWahid s h r) (ishtiqaq s h rs)

/-- خطوةُ المعالج: أعلى القوّة القائمة وما تشتقّه القوانين. -/
def khatwa (qs : List Qanun) (s : Haqiqa → Nat) (h : Haqiqa) : Nat := max (s h) (ishtiqaq s h qs)

def tashghil (qs : List Qanun) (s : Haqiqa → Nat) : Nat → Haqiqa → Nat
  | 0 => s
  | k + 1 => khatwa qs (tashghil qs s k)

/-- **رتابة:** لا تنقص قوّةُ حقيقةٍ بالمعالجة. -/
theorem khatwa_ratiba (qs : List Qanun) (s : Haqiqa → Nat) (h : Haqiqa) : s h ≤ khatwa qs s h :=
  Nat.le_max_left _ _

theorem tashghil_ratiba (qs : List Qanun) (s : Haqiqa → Nat) (h : Haqiqa) :
    ∀ k, s h ≤ tashghil qs s k h
  | 0 => Nat.le_refl _
  | k + 1 => Nat.le_trans (tashghil_ratiba qs s h k) (khatwa_ratiba qs _ h)

theorem ishtiqaq_hadd (B : Nat) (s : Haqiqa → Nat) (hs : ∀ h, s h ≤ B) (h : Haqiqa) :
    ∀ qs : List Qanun, ishtiqaq s h qs ≤ B
  | [] => Nat.zero_le _
  | r :: rs => by
    have h1 : ishtiqaqWahid s h r ≤ B := by
      unfold ishtiqaqWahid; split
      · exact minL_hadd B _ (fun y hy => by obtain ⟨m, _, rfl⟩ := List.mem_map.1 hy; exact hs m)
      · exact Nat.zero_le _
    have h2 := ishtiqaq_hadd B s hs h rs
    simp only [ishtiqaq]; omega

/-- **الحدّ:** لا يخلق المعالجُ قوّةً فوق أعلى قوّةٍ في الأصول. -/
theorem tashghil_hadd (B : Nat) (qs : List Qanun) (s : Haqiqa → Nat) (hs : ∀ h, s h ≤ B) :
    ∀ k h, tashghil qs s k h ≤ B
  | 0, h => hs h
  | k + 1, h => by
    have ih := tashghil_hadd B qs s hs k
    simp only [tashghil, khatwa]
    have := ishtiqaq_hadd B _ ih h qs
    have := ih h
    omega

theorem ishtiqaq_masdar (s : Haqiqa → Nat) (h : Haqiqa) :
    ∀ qs : List Qanun, ishtiqaq s h qs = 0 ∨
      ∃ r ∈ qs, r.natija = h ∧ ishtiqaq s h qs = minL (r.muqaddimat.map s)
  | [] => Or.inl rfl
  | r :: rs => by
    rcases ishtiqaq_masdar s h rs with e | ⟨r', hr', hn, he⟩
    · by_cases hn : r.natija = h
      · exact Or.inr ⟨r, by simp, hn, by simp [ishtiqaq, ishtiqaqWahid, hn, e]⟩
      · exact Or.inl (by simp [ishtiqaq, ishtiqaqWahid, hn, e])
    · by_cases hn' : r.natija = h
      · have ew : ishtiqaqWahid s h r = minL (r.muqaddimat.map s) := by
          unfold ishtiqaqWahid; simp [hn']
        by_cases hle : minL (r.muqaddimat.map s) ≤ ishtiqaq s h rs
        · exact Or.inr ⟨r', List.mem_cons_of_mem _ hr', hn, by
            simp only [ishtiqaq, ew]; rw [← he]; omega⟩
        · exact Or.inr ⟨r, by simp, hn', by simp only [ishtiqaq, ew]; omega⟩
      · have ew : ishtiqaqWahid s h r = 0 := by
          unfold ishtiqaqWahid; simp [hn']
        exact Or.inr ⟨r', List.mem_cons_of_mem _ hr', hn, by
          simp only [ishtiqaq, ew]; rw [← he]; omega⟩

/-- **التفسير (الصندوق الأبيض):** كلُّ زيادةٍ في قوّة حقيقةٍ منسوبةٌ إلى قانونٍ مسمّى نتيجتُه هي،
    وكلُّ مقدّماته ليست أضعفَ من القوّة الجديدة — فلا نتيجةَ أقوى من أضعف مقدّماتها. -/
theorem ziyada_munsuba (qs : List Qanun) (s : Haqiqa → Nat) (h : Haqiqa) (hz : s h < khatwa qs s h) :
    ∃ r ∈ qs, r.natija = h ∧ ∀ m ∈ r.muqaddimat, khatwa qs s h ≤ s m := by
  have hk : khatwa qs s h = ishtiqaq s h qs := by unfold khatwa at *; omega
  rcases ishtiqaq_masdar s h qs with e | ⟨r, hr, hn, he⟩
  · omega
  · refine ⟨r, hr, hn, fun m hm => ?_⟩
    rw [hk, he]
    exact minL_le _ _ (List.mem_map.2 ⟨m, hm, rfl⟩)

/-- **الوجودُ لا يُشتقّ:** إن لم يكن في القوانين قانونٌ نتيجتُه وجود، بقيت قوّةُ كلّ وجودٍ على شهوده. -/
theorem wujud_la_yushtaqq (qs : List Qanun) (hq : ∀ r ∈ qs, r.natija.alaqa ≠ .wujud)
    (s : Haqiqa → Nat) (h : Haqiqa) (hw : h.alaqa = .wujud) : khatwa qs s h = s h := by
  have : ishtiqaq s h qs = 0 := by
    rcases ishtiqaq_masdar s h qs with e | ⟨r, hr, hn, _⟩
    · exact e
    · exact absurd (hn ▸ hw) (hq r hr)
  simp [khatwa, this]

theorem tashghil_wujud (qs : List Qanun) (hq : ∀ r ∈ qs, r.natija.alaqa ≠ .wujud)
    (s : Haqiqa → Nat) (h : Haqiqa) (hw : h.alaqa = .wujud) : ∀ k, tashghil qs s k h = s h
  | 0 => rfl
  | k + 1 => by
    show khatwa qs (tashghil qs s k) h = s h
    rw [wujud_la_yushtaqq qs hq _ h hw, tashghil_wujud qs hq s h hw k]

/-- مرتبةُ حقيقةٍ بعد المعالجة. -/
def rutbaOf (K : Nat) (s : Haqiqa → Nat) (h : Haqiqa) : Rutba := rutba K h.naw (s h)

/-- **الصفةُ المكتسبة ظنٌّ أبدًا** مهما قويت مقدّماتها. -/
theorem sifa_zanniyya (K : Nat) (s : Haqiqa → Nat) (h : Haqiqa) (hs : h.alaqa = .sifa) :
    rutbaOf K s h ≠ .yaqin :=
  ghayr_wujud_la_yaqin K _ _ (by simp [Haqiqa.naw, hs])

/-! ## ٦. القوانينُ المولَّدة من الشبكة (قول المالك) -/

/-- اكتسابُ الصفة: من وُجد واحتاج ما وُجد وقَبِل أن يُفعَل به الفعل، اكتسب صفةَ فاعله (احتاج الماءَ والماءُ يُشرب ⇒ شارب). -/
def qIktisab (a x f : Nat) : Qanun :=
  ⟨"اكتساب-الصفة", [⟨.wujud, a, 0⟩, ⟨.wujud, x, 0⟩, ⟨.ihtiyaj, a, x⟩, ⟨.qabMafool, x, f⟩], ⟨.sifa, a, f⟩⟩

/-- وراثةُ الاحتياج: ما تحت المحتاج محتاج. -/
def qWirathaIhtiyaj (n p x : Nat) : Qanun :=
  ⟨"وراثة-الاحتياج", [⟨.taht, n, p⟩, ⟨.ihtiyaj, p, x⟩], ⟨.ihtiyaj, n, x⟩⟩

/-- تعدّي التصنيف. -/
def qTadiya (a b c : Nat) : Qanun :=
  ⟨"تعدّي-التصنيف", [⟨.taht, a, b⟩, ⟨.taht, b, c⟩], ⟨.taht, a, c⟩⟩

def qawanin (U F : List Nat) : List Qanun :=
  (U.flatMap fun a => U.flatMap fun b => U.map fun c => qTadiya a b c) ++
  (U.flatMap fun n => U.flatMap fun p => U.map fun x => qWirathaIhtiyaj n p x) ++
  (U.flatMap fun a => U.flatMap fun x => F.map fun f => qIktisab a x f)

/-- القوانينُ المولَّدة لا تُنتج وجودًا: فالوجودُ في الشبكة كلّها من التواتر وحده. -/
theorem qawanin_la_wujud (U F : List Nat) : ∀ r ∈ qawanin U F, r.natija.alaqa ≠ .wujud := by
  intro r hr
  simp only [qawanin, List.mem_append, List.mem_flatMap, List.mem_map] at hr
  rcases hr with (⟨_, _, _, _, _, _, rfl⟩ | ⟨_, _, _, _, _, _, rfl⟩) | ⟨_, _, _, _, _, _, rfl⟩ <;> simp [qTadiya, qWirathaIhtiyaj, qIktisab]

/-! ## ٧. التشفير: العلاقةُ رقمٌ واحد مربوطٌ بالـ116 -/

def Alaqa.idx : Alaqa → Nat
  | .wujud => 0 | .taht => 1 | .khassa => 2 | .qabMafool => 3 | .ihtiyaj => 4 | .sifa => 5

def Alaqa.ofIdx : Nat → Option Alaqa
  | 0 => some .wujud | 1 => some .taht | 2 => some .khassa | 3 => some .qabMafool
  | 4 => some .ihtiyaj | 5 => some .sifa | _ => none

theorem Alaqa.ofIdx_idx (r : Alaqa) : Alaqa.ofIdx r.idx = some r := by cases r <;> rfl
theorem Alaqa.idx_lt (r : Alaqa) : r.idx < 8 := by cases r <;> decide

/-- شيفرةُ العلاقة: نوعُها في ثلاث بتّات، ثمّ طرفاها بالأساس B (B = 29^k لجذور k حواملَ من آلة الـ116). -/
def shifra (B : Nat) (h : Haqiqa) : Nat := h.alaqa.idx + 8 * (h.a + B * h.b)

def fakk (B n : Nat) : Option Haqiqa :=
  (Alaqa.ofIdx (n % 8)).map fun r => ⟨r, n / 8 % B, n / 8 / B⟩

/-- **الفكّ يعيد العلاقة بعينها** (والطرفُ الأوّل دون الأساس). -/
theorem fakk_shifra (B : Nat) (h : Haqiqa) (ha : h.a < B) : fakk B (shifra B h) = some h := by
  have hB : 0 < B := Nat.lt_of_le_of_lt (Nat.zero_le _) ha
  have m8 : (h.alaqa.idx + 8 * (h.a + B * h.b)) % 8 = h.alaqa.idx := by
    rw [Nat.add_mul_mod_self_left]; exact Nat.mod_eq_of_lt (Alaqa.idx_lt _)
  have d8 : (h.alaqa.idx + 8 * (h.a + B * h.b)) / 8 = h.a + B * h.b := by
    rw [Nat.add_mul_div_left _ _ (by decide)]
    have : h.alaqa.idx / 8 = 0 := Nat.div_eq_of_lt (Alaqa.idx_lt _)
    omega
  have mB : (h.a + B * h.b) % B = h.a := by
    rw [Nat.add_mul_mod_self_left]; exact Nat.mod_eq_of_lt ha
  have dB : (h.a + B * h.b) / B = h.b := by
    rw [Nat.add_mul_div_left _ _ hB, Nat.div_eq_of_lt ha]; simp
  simp only [fakk, shifra, m8, d8, mB, dB, Alaqa.ofIdx_idx, Option.map_some]

/-- **التشفير تقابليّ:** علاقتان بشيفرةٍ واحدة علاقةٌ واحدة. -/
theorem shifra_inj (B : Nat) (h h' : Haqiqa) (ha : h.a < B) (ha' : h'.a < B)
    (e : shifra B h = shifra B h') : h = h' := by
  have := fakk_shifra B h ha
  rw [e, fakk_shifra B h' ha'] at this
  exact (Option.some.inj this).symm

/-- رقمُ العقدة: رقمُ جذر لفظها الجامد بآلة المشروع، ولا يُقبل إلّا جذرٌ مرخَّص. -/
def raqmJins (r : List Nat) : Option Nat :=
  if Madlul.Fard116.licB r then some (Madlul.Fard116.ramz r) else none

/-! ## ٨. الشاهد المبنيّ (لا مودَع: أعدادُ الشهود مفروضة، وجذورُ الألفاظ تعيينُ البنّاء بترتيب المخارج) -/

-- الحواملُ بترتيب `Nabt.makharijCarriers`: ء0 ه1 ا2 ع3 ح4 … ي11 … ل13 ن14 ر15 … د17 ت18 ز19 س20 … ف25 ب26 م27 و28
def jWujud : List Nat := [28, 9, 17]   -- و ج د
def jHayy : List Nat := [4, 11, 11]    -- ح ي ي
def jJamad : List Nat := [9, 27, 17]   -- ج م د
def jNabat : List Nat := [14, 26, 18]  -- ن ب ت
def jZayt : List Nat := [19, 11, 18]   -- ز ي ت
def jTuffah : List Nat := [18, 25, 4]  -- ت ف ح
def jIns : List Nat := [0, 14, 20]     -- ء ن س
def jMa : List Nat := [27, 28, 1]      -- م و ه
def jShurb : List Nat := [10, 15, 26]  -- ش ر ب

theorem judhur_murakhkhasa :
    [jWujud, jHayy, jJamad, jNabat, jZayt, jTuffah, jIns, jMa, jShurb].all
      (fun r => (raqmJins r).isSome) = true := by decide

def nWujud := Madlul.Fard116.ramz jWujud
def nHayy := Madlul.Fard116.ramz jHayy
def nJamad := Madlul.Fard116.ramz jJamad
def nNabat := Madlul.Fard116.ramz jNabat
def nZayt := Madlul.Fard116.ramz jZayt
def nTuffah := Madlul.Fard116.ramz jTuffah
def nIns := Madlul.Fard116.ramz jIns
def nMa := Madlul.Fard116.ramz jMa
def nShurb := Madlul.Fard116.ramz jShurb

/-- رقمُ عقدةٍ هجينةٍ مفترضة يجمع زيتونًا وماءً (مثالُ أبوّةٍ متعدّدةٍ عابرةٍ للفرعين كما في Cyc). -/
def nHajin : Nat := 1
/-- وعقدةٌ تجمع الزيتونَ والتفّاح (أبوّةٌ متعدّدةٌ في فرعٍ واحد). -/
def nMushtarak : Nat := 2

def pIhtiyajMa : Nat := 0
def pIntiqal : Nat := 1

def shabakaShahid : Shabaka where
  aba n :=
    if n = nHayy ∨ n = nJamad then [nWujud]
    else if n = nNabat ∨ n = nIns then [nHayy]
    else if n = nZayt ∨ n = nTuffah then [nNabat]
    else if n = nMa then [nJamad]
    else if n = nHajin then [nZayt, nMa]
    else if n = nMushtarak then [nZayt, nTuffah]
    else []
  ras n := if n = nHayy then some .hayy else if n = nJamad then some .jamad else none
  fasl n p :=
    if n = nHayy ∧ p = pIhtiyajMa then .naam
    else if n = nJamad ∧ p = pIhtiyajMa then .la
    else if n = nNabat ∧ p = pIntiqal then .la
    else if n = nIns ∧ p = pIntiqal then .naam
    else .laHukm
  shuhud n :=
    if n = nHajin then [⟨cyc, "opencyc:Hajin"⟩, ⟨cyc, "opencyc:Hajin-2"⟩]
    else [⟨1, "mukhassas"⟩, ⟨2, "lisan"⟩, ⟨3, "maqayis"⟩]

theorem arqam_mutamayyiza :
    [nWujud, nHayy, nJamad, nNabat, nZayt, nTuffah, nIns, nMa, nShurb, nHajin, nMushtarak].eraseDups.length = 11 := by
  decide

/-- الزيتونُ والتفّاحُ تحت «حيّ»، والماءُ تحت «جماد». -/
theorem shahid_far :
    far shabakaShahid 4 nZayt = some .hayy ∧ far shabakaShahid 4 nTuffah = some .hayy ∧
    far shabakaShahid 4 nIns = some .hayy ∧ far shabakaShahid 4 nMa = some .jamad := by decide

/-- الهجينُ العابرُ للفرعين «لا حكم»، والمشتركُ في فرعٍ واحد يدخل. -/
theorem shahid_hajin : far shabakaShahid 4 nHajin = none ∧ far shabakaShahid 4 nMushtarak = some .hayy := by decide

/-- الزيتونُ والتفّاحُ يحتاجان الماء ولا ينتقلان؛ والإنسانُ يحتاجه وينتقل؛ والماءُ لا يحتاجه. -/
theorem shahid_wiratha :
    qima shabakaShahid 4 nZayt pIhtiyajMa = .naam ∧ qima shabakaShahid 4 nZayt pIntiqal = .la ∧
    qima shabakaShahid 4 nTuffah pIhtiyajMa = .naam ∧ qima shabakaShahid 4 nTuffah pIntiqal = .la ∧
    qima shabakaShahid 4 nIns pIhtiyajMa = .naam ∧ qima shabakaShahid 4 nIns pIntiqal = .naam ∧
    qima shabakaShahid 4 nMa pIhtiyajMa = .la ∧ qima shabakaShahid 4 nMushtarak pIhtiyajMa = .naam := by decide

/-- الهجينُ لا يدخل: شاهدا مصدرٍ واحد (OpenCyc) ليسا تواترًا عند K = 2، وفرعُه «لا حكم»؛ والزيتونُ يدخل. -/
theorem shahid_dukhul : yadkhul shabakaShahid 2 4 nHajin = false ∧ yadkhul shabakaShahid 2 4 nZayt = true := by
  decide

/-- الأصولُ المودَعة (مفروضةٌ للشاهد): قوى شهودها. -/
def asl (h : Haqiqa) : Nat :=
  if h.alaqa = .wujud ∧ h.b = 0 ∧ (h.a = nIns ∨ h.a = nZayt ∨ h.a = nMa) then 3
  else if h = ⟨.ihtiyaj, nHayy, nMa⟩ then 3
  else if h = ⟨.taht, nIns, nHayy⟩ ∨ h = ⟨.taht, nZayt, nNabat⟩ ∨ h = ⟨.taht, nNabat, nHayy⟩ then 2
  else if h = ⟨.qabMafool, nMa, nShurb⟩ then 2
  else 0

def U : List Nat := [nHayy, nNabat, nZayt, nIns, nMa]

def natijatShahid : Haqiqa → Nat := tashghil (qawanin U [nShurb]) asl 3

/-- الإنسانُ والزيتونُ شاربان بقوّة 2 (أدنى مقدّماتهما)، والماءُ ليس شاربًا (لا يحتاج نفسه)،
    ووجودُ الإنسان يقين وصفتُه ظنّ. -/
theorem shahid_muallij :
    natijatShahid ⟨.sifa, nIns, nShurb⟩ = 2 ∧ natijatShahid ⟨.sifa, nZayt, nShurb⟩ = 2 ∧
    natijatShahid ⟨.sifa, nMa, nShurb⟩ = 0 ∧
    rutbaOf 2 natijatShahid ⟨.wujud, nIns, 0⟩ = .yaqin ∧
    rutbaOf 2 natijatShahid ⟨.sifa, nZayt, nShurb⟩ = .zann 2 := by
  decide +kernel

end NTP
