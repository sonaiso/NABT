/-
  Jisr/QiraaSimat.lean — قراءةُ السمات من الرقم: (الشخص، الجنس، العدد) من خلايا الضمير المنفصل، وفحصُ السمات الملصقة من رقم الجملة وحدَه

  **السبب** (ملاحظةُ المالك 2026-10-17، 17:31): «الخللُ عدمُ قراءة unit SLGE من الـbinary، وإلّا كان هناك حلولٌ إبداعيّةٌ للمدلول؛
  فإنّ الباينري والتشفير يتيح معادلاتٍ معظمُها لم تُفكّ ليُقرأ منها مدلولٌ من SLGE».

  **ما في SLGE** (ملفّات المالك، لا تُعدَّل): `Simat.annEnc f ats ws = pair (sEnc f ws) (encS (ats.map attrCode))` — فالسماتُ
  `Attr` (الزمن، التعريف، (الشخص، الجنس، العدد)، البناء) إحداثيٌّ ثانٍ يُقرن بالخلايا `ws`، و`Simat.attr_value` يستردّها لأنّها
  وُضعت؛ ولا دالّةَ في SLGE مدخلُها خلايا ومخرجُها `Attr` أو `Feat` (`slotAttrOK`/`linkOK` تفحص السماتِ ولا تقرؤها؛ و`Maqam.refEnc`
  يقرن `featCode` بالرقم بالنمط نفسه). ونصّ المالك في `Maqam.dal_underdetermines_maqam`: «أنتَ/أنتِ سلسلةٌ واحدة لا تفرّقها إلّا
  الحالة؛ فالموضعُ في المقام يميّز ما لا يميّزه الحاملُ وحده» — وجدولُه `Maqam.damair` بالحوامل وحدَها.

  **ما يُبنى هنا** (يُبرهن على الشاهد ما نصّ عليه المالك، ويكتب فحصًا من الرقم). الخليةُ `cellEnc c s` تساوي `4c + s`
  (`JisrDal.khaliya_malik`)، ففيها معادلتان: الحاملُ `n / 4` والحالةُ `n % 4`. **جدولُ الضمائر خلايا** `damairKhalaya` وضعٌ مودَعٌ من
  البنّاء: حواملُه وسماتُه جدولُ المالك بعينه (`hawamil_malik`) والحالاتُ تعيينُه من الرسم المشكول المتداول (حرفُ المدّ ساكن: CLAUDE.md
  الغانم، القانون الواحد، ADR ٣: «فحرفُ المدّ خانةٌ ساكنةٌ دورُها `v`»؛ والمدغَمُ خليتان أولاهما ساكنة). فالسمةُ تُقرأ من جدول وضعٍ
  مفتاحُه الخلايا، والمعادلةُ المقروءة من الرقم الحالةُ `n % 4`. والقارئ `qiraa` حكمٌ ثلاثيّ `Q`: معيَّن، أو محتمَلٌ بقائمته، أو لا حكم.
  (١) اتّساقُ القارئ مع جدوله (`qiraa_salima`، `qiraaH_salima`؛ شبهُ دائريّ: يُفحص القارئُ على الجدول الذي بُني منه).
  (٢) الحالةُ تزيد ما يعيّنه الحامل: بالحوامل 8 من 14 وبالخلايا 10 (`hawamil_8`، `khalaya_10`، `anta_anti`)؛ و«هما»/«أنتما» محتمَلتان
  في الدالّ نفسه (`huma_baqiya`)، فلا دالّةَ في الخلايا تستردّ سمةَ كلّ ضمير (`la_dalla_tasturidd`).
  (٣) القراءةُ من الرقم: من رقم الكلمة (`qiraa_min_raqm`)، ومن الإحداثيّ الأوّل لـ`annEnc` أيًّا كانت السماتُ المقرونة
  (`qiraa_min_annEnc`)؛ والفاحصُ `fahsRaqm` يأخذ الرقمَ وحدَه فيفكّ إحداثيّيه ويحكم بموافقة كلّ سمةٍ لقراءة كلمتها (`fahs_min_raqm`،
  لكلّ جملةٍ في الأطر)، وشاهدُه «أنتِ» مقرونةً بسمة المخاطَب المذكّر (`kashf_tanaqud`).
  (٤) مكوّنُ (الشخص، الجنس، العدد) من الإحداثيّ الثاني فائضٌ حيث يعيّن القارئُ كلَّ كلمة: سماتٌ موافقةٌ تتساوى (`ihtizal`)، ورقمانِ
  لجملةٍ واحدةٍ بسماتٍ تتّفق فيما سوى ذلك المكوّن ويقبلهما الفاحص متساويان (`ihtizal_annEnc`).

  **حدُّه:** يقرأ (الشخص، الجنس، العدد) من الضمائر المنفصلة الأربعة عشر وحدَها؛ والزمنُ والتعريفُ والبناء، والضمائرُ المتّصلة،
  وحروفُ المضارعة لم تُبنَ (`QIRAA_DAMAIR_ONLY`)؛ والحالاتُ تعيين البنّاء (`HALAT_BINA`)؛ وأنّ ما يرفع احتمالَ «هما» المرجعُ أو المقام
  رأيٌ لم يُربط بـ`Maqam.refOK` (`HUMA_BI_MARJI_NOT_LINKED`).
-/
import SLGE.Simat
import Jisr.JisrDal

set_option autoImplicit false

namespace Jisr
namespace QiraaSimat
open SLGE SLGE.Maqam

/-! ## ١. الحكمُ الثلاثيّ والموافقة -/

inductive Q (α : Type) where
  | qad (a : α)
  | muhtamal (as : List α)
  | laHukm
  deriving DecidableEq, Repr

def isQad {α : Type} : Q α → Bool
  | .qad _ => true
  | _ => false

/-- السمةُ توافق القراءة: تساوي المعيَّن، أو في قائمة المحتمَل، أو لا قيدَ مع «لا حكم». -/
def muwafiq : Q Feat → Feat → Bool
  | .qad a, x => x == a
  | .muhtamal as, x => as.contains x
  | .laHukm, _ => true

def nub (l : List Feat) : List Feat := l.foldr (fun x acc => if acc.contains x then acc else x :: acc) []

def hukmOf (fs : List Feat) : Q Feat :=
  match nub fs with
  | [] => .laHukm
  | [f] => .qad f
  | gs => .muhtamal gs

/-! ## ٢. الضمائرُ خلايا -/

open JisrDal (kh harf hala)

/-- الضمائرُ المنفصلة الأربعة عشر خلايا (حامل × حالة)، بترتيب جدول المالك وسماته. -/
def damairKhalaya : List (String × List Nat × Feat) :=
  [("هُوَ", [kh 1 1, kh 28 0], (3, 0, 0)), ("هُمَا", [kh 1 1, kh 27 0, kh 2 3], (3, 0, 1)),
   ("هُمْ", [kh 1 1, kh 27 3], (3, 0, 2)),
   ("هِيَ", [kh 1 2, kh 11 0], (3, 1, 0)), ("هُمَا", [kh 1 1, kh 27 0, kh 2 3], (3, 1, 1)),
   ("هُنَّ", [kh 1 1, kh 14 3, kh 14 0], (3, 1, 2)),
   ("أَنْتَ", [kh 0 0, kh 14 3, kh 18 0], (2, 0, 0)),
   ("أَنْتُمَا", [kh 0 0, kh 14 3, kh 18 1, kh 27 0, kh 2 3], (2, 0, 1)),
   ("أَنْتُمْ", [kh 0 0, kh 14 3, kh 18 1, kh 27 3], (2, 0, 2)),
   ("أَنْتِ", [kh 0 0, kh 14 3, kh 18 2], (2, 1, 0)),
   ("أَنْتُمَا", [kh 0 0, kh 14 3, kh 18 1, kh 27 0, kh 2 3], (2, 1, 1)),
   ("أَنْتُنَّ", [kh 0 0, kh 14 3, kh 18 1, kh 14 3, kh 14 0], (2, 1, 2)),
   ("أَنَا", [kh 0 0, kh 14 0, kh 2 3], (1, 2, 0)), ("نَحْنُ", [kh 14 0, kh 4 3, kh 14 1], (1, 2, 2))]

/-- **حواملُ الجدول هي جدولُ المالك بعينه** (`Maqam.damair`) — الخلايا تزيد الحالةَ ولا تغيّر حاملًا ولا سمة؛ وكلُّها دون 116. -/
theorem hawamil_malik :
    damairKhalaya.map (fun d => (d.2.1.map harf, d.2.2)) = damair.map (fun d => (d.2.1, d.2.2)) ∧
    damairKhalaya.all (fun d => d.2.1.all (· < 116)) = true := by decide

/-! ## ٣. القارئ: من الخلايا، ومن الحوامل وحدَها -/

/-- **القارئُ من الخلايا:** سماتُ كلّ ضميرٍ خلاياه هذه. -/
def qiraa (w : List Nat) : Q Feat := hukmOf ((damairKhalaya.filter (·.2.1 == w)).map (·.2.2))

/-- **القارئُ من الحوامل وحدَها** (`n / 4`) على جدول المالك. -/
def qiraaH (h : List Nat) : Q Feat := hukmOf ((damair.filter (·.2.1 == h)).map (·.2.2))

/-- **القارئُ سليم:** كلُّ ضميرٍ تُوافق سمتُه قراءةَ خلاياه، وقراءةَ حوامله. -/
theorem qiraa_salima : damairKhalaya.all (fun d => muwafiq (qiraa d.2.1) d.2.2) = true := by decide

theorem qiraaH_salima : damair.all (fun d => muwafiq (qiraaH d.2.1) d.2.2) = true := by decide

/-- **الحالةُ تزيد التعيين:** بالحوامل يتعيّن 8 من 14، وبالخلايا 10. -/
theorem hawamil_8 : (damair.filter (fun d => isQad (qiraaH d.2.1))).length = 8 := by decide

theorem khalaya_10 : (damairKhalaya.filter (fun d => isQad (qiraa d.2.1))).length = 10 := by decide

/-- **«أنتَ» و«أنتِ»:** حاملاهما واحد فالحواملُ تحتمل، وحالةُ التاء (`n % 4`) تعيّن كلًّا. -/
theorem anta_anti :
    qiraaH [0, 14, 18] = .muhtamal [(2, 0, 0), (2, 1, 0)] ∧
    qiraa [kh 0 0, kh 14 3, kh 18 0] = .qad (2, 0, 0) ∧
    qiraa [kh 0 0, kh 14 3, kh 18 2] = .qad (2, 1, 0) := by decide

/-- **«هما» و«أنتما» محتمَلان في الدالّ نفسه** (وأنّ ما يرفعه المرجعُ أو المقام رأي: `HUMA_BI_MARJI_NOT_LINKED`). -/
theorem huma_baqiya :
    qiraa [kh 1 1, kh 27 0, kh 2 3] = .muhtamal [(3, 0, 1), (3, 1, 1)] ∧
    qiraa [kh 0 0, kh 14 3, kh 18 1, kh 27 0, kh 2 3] = .muhtamal [(2, 0, 1), (2, 1, 1)] := by decide

/-- وخلايا ليست في الجدول «لا حكم» — لا تخمين. -/
theorem ghayr_damir : qiraa [kh 8 0, kh 18 0, kh 26 0] = .laHukm := by decide

/-! ## ٤. القراءةُ من الرقم -/

/-- **من رقم الكلمة:** قراءةُ فكّ `encS w` هي قراءةُ `w` لكلّ كلمة. -/
theorem qiraa_min_raqm (w : List Nat) : qiraa (decS (encS w)) = qiraa w := by rw [decS_encS]

/-- **من رقم الجملة المسمّاة:** كلماتُ إحداثيّها الأوّل تُقرأ كما هي، أيًّا كانت السماتُ الملصقة في الثاني. -/
theorem qiraa_min_annEnc (f : Tarkib.Frame) (hf : f ∈ Tarkib.framesL) (ats : List Simat.Attr)
    (ws : List (List Nat)) :
    (Tarkib.sDec (unpair (Simat.annEnc f ats ws)).1).2.map qiraa = ws.map qiraa := by
  unfold Simat.annEnc; rw [unpair_pair, Tarkib.s_dec_enc f hf]

/-! ## ٥. لا دالّةَ في الخلايا تستردّ السمة -/

/-- **«هما» خلاياها واحدةٌ وسمتاها مختلفتان**، فلا دالّةَ من الخلايا تُخرج سمةَ كلّ ضميرٍ في الجدول — لكلّ دالّة. -/
theorem la_dalla_tasturidd (g : List Nat → Feat) : ¬ (damairKhalaya.all (fun d => g d.2.1 == d.2.2) = true) := by
  intro h
  have h1 : g [kh 1 1, kh 27 0, kh 2 3] = (3, 0, 1) := by
    have := List.all_eq_true.mp h ("هُمَا", [kh 1 1, kh 27 0, kh 2 3], (3, 0, 1)) (by decide)
    simpa using this
  have h2 : g [kh 1 1, kh 27 0, kh 2 3] = (3, 1, 1) := by
    have := List.all_eq_true.mp h ("هُمَا", [kh 1 1, kh 27 0, kh 2 3], (3, 1, 1)) (by decide)
    simpa using this
  rw [h1] at h2; simp at h2

/-! ## ٦. الفحصُ من الرقم وحدَه -/

/-- فكُّ `Simat.attrCode` بـ`unpair`. -/
def attrDec (z : Nat) : Simat.Attr :=
  let a := unpair z; let b := unpair a.2; let c := unpair b.2; let d := unpair c.1; let e := unpair d.2
  (a.1, b.1, (d.1, e.1, e.2), c.2 == 1)

theorem attrDec_attrCode (t : Simat.Attr) : attrDec (Simat.attrCode t) = t := by
  obtain ⟨a, b, ⟨p, g, n⟩, m⟩ := t
  cases m <;> simp [attrDec, Simat.attrCode, unpair_pair]

def featOf (t : Simat.Attr) : Feat := t.2.2.1

/-- موافقةُ سمات الجملة لقراءة كلماتها، كلمةً كلمة. -/
def muwafiqJumla : List (List Nat) → List Simat.Attr → Bool
  | w :: ws, t :: ts => muwafiq (qiraa w) (featOf t) && muwafiqJumla ws ts
  | _, _ => true

/-- **الفاحصُ يأخذ الرقمَ وحدَه:** يفكّ الكلماتِ من الإحداثيّ الأوّل والسماتِ من الثاني ويحكم. -/
def fahsRaqm (n : Nat) : Bool :=
  muwafiqJumla (Tarkib.sDec (unpair n).1).2 ((decS (unpair n).2).map attrDec)

theorem map_attrDec (ats : List Simat.Attr) : (ats.map Simat.attrCode).map attrDec = ats := by
  induction ats with
  | nil => rfl
  | cons t ts ih => simp only [List.map_cons, attrDec_attrCode]; simpa using ih

/-- **حكمُ الفاحص على رقم الجملة هو حكمُ الموافقة على كلماتها وسماتها** — لكلّ إطارٍ في الأطر ولكلّ كلماتٍ وسمات. -/
theorem fahs_min_raqm (f : Tarkib.Frame) (hf : f ∈ Tarkib.framesL) (ats : List Simat.Attr)
    (ws : List (List Nat)) : fahsRaqm (Simat.annEnc f ats ws) = muwafiqJumla ws ats := by
  unfold fahsRaqm Simat.annEnc; rw [unpair_pair, Tarkib.s_dec_enc f hf, decS_encS, map_attrDec]

/-- **كشفُ التناقض من الرقم** (على الشاهد): رقمٌ يقرن «أنتِ» بسمة المخاطَب المذكّر يرفضه الفاحصُ من الرقم وحدَه،
ويقبل الرقمَ نفسَه بسمة المخاطَبة. -/
theorem kashf_tanaqud (f : Tarkib.Frame) (hf : f ∈ Tarkib.framesL) :
    fahsRaqm (Simat.annEnc f [Simat.pron 2 0 0] [[kh 0 0, kh 14 3, kh 18 2]]) = false ∧
    fahsRaqm (Simat.annEnc f [Simat.pron 2 1 0] [[kh 0 0, kh 14 3, kh 18 2]]) = true := by
  rw [fahs_min_raqm f hf, fahs_min_raqm f hf]; decide

/-! ## ٧. الفائض -/

/-- **المعيَّنُ لا يقبل سمتين** (تعريفيّة). -/
theorem faid (a x y : Feat) (hx : muwafiq (.qad a) x = true) (hy : muwafiq (.qad a) y = true) : x = y := by
  simp only [muwafiq, beq_iff_eq] at hx hy; rw [hx, hy]

def baqiOf (t : Simat.Attr) : Nat × Nat × Bool := (t.1, t.2.1, t.2.2.2)

/-- **الاختزال:** إن تعيّنت قراءةُ كلّ كلمة، فسماتان موافقتان تتّفقان فيما سوى (الشخص، الجنس، العدد) متساويتان. -/
theorem ihtizal : ∀ (ws : List (List Nat)) (ats ats' : List Simat.Attr),
    (∀ w ∈ ws, isQad (qiraa w) = true) → ats.length = ws.length → ats'.length = ws.length →
    ats.map baqiOf = ats'.map baqiOf →
    muwafiqJumla ws ats = true → muwafiqJumla ws ats' = true → ats = ats'
  | [], [], [], _, _, _, _, _, _ => rfl
  | w :: ws, t :: ts, t' :: ts', hq, hl, hl', hb, h, h' => by
    simp only [muwafiqJumla, Bool.and_eq_true] at h h'
    simp only [List.map_cons, List.cons.injEq] at hb
    have hrest := ihtizal ws ts ts' (fun v hv => hq v (List.mem_cons_of_mem w hv))
      (by simpa using hl) (by simpa using hl') hb.2 h.2 h'.2
    have hqq := hq w (List.mem_cons_self ..)
    have hf : featOf t = featOf t' := by
      cases hw : qiraa w with
      | qad a => rw [hw] at h h'; exact faid a _ _ h.1 h'.1
      | muhtamal _ => rw [hw] at hqq; simp [isQad] at hqq
      | laHukm => rw [hw] at hqq; simp [isQad] at hqq
    obtain ⟨a, b, fe, m⟩ := t
    obtain ⟨a', b', fe', m'⟩ := t'
    simp only [baqiOf, Prod.mk.injEq] at hb
    simp only [featOf] at hf
    rw [hb.1.1, hb.1.2.1, hb.1.2.2, hf, hrest]
  | [], _ :: _, _, _, hl, _, _, _, _ => by simp at hl
  | [], [], _ :: _, _, _, hl', _, _, _ => by simp at hl'
  | _ :: _, [], _, _, hl, _, _, _, _ => by simp at hl
  | _ :: _, _ :: _, [], _, _, hl', _, _, _ => by simp at hl'

/-- **رقمان لجملةٍ واحدةٍ يقبلهما الفاحص** وسماتُهما تتّفق فيما سوى (الشخص، الجنس، العدد)، وقراءةُ كلّ كلمةٍ معيَّنة:
متساويان — فذلك المكوّنُ من الإحداثيّ الثاني لا يحمل شيئًا لا يحمله الأوّل. -/
theorem ihtizal_annEnc (f : Tarkib.Frame) (hf : f ∈ Tarkib.framesL) (ws : List (List Nat))
    (ats ats' : List Simat.Attr) (hq : ∀ w ∈ ws, isQad (qiraa w) = true)
    (hl : ats.length = ws.length) (hl' : ats'.length = ws.length) (hb : ats.map baqiOf = ats'.map baqiOf)
    (h : fahsRaqm (Simat.annEnc f ats ws) = true) (h' : fahsRaqm (Simat.annEnc f ats' ws) = true) :
    Simat.annEnc f ats ws = Simat.annEnc f ats' ws := by
  rw [fahs_min_raqm f hf] at h h'
  rw [ihtizal ws ats ats' hq hl hl' hb h h']

end QiraaSimat
end Jisr
