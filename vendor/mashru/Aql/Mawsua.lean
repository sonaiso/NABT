/-
  Aql/Mawsua.lean — الطيّ والفكّ، والمخزن، والوسم، والترجيح، والطريقة: طبقة الموسوعة.

  السند:
  * ج3 729: اللغة اصطلاح العرب، «فطريق معرفتها أخذها عنهم» — المعجم مصدر الحقيقة اللغوية لا ذيلٌ لها.
  * ج3 826: الأصل في الكلام الحقيقة، والحقيقي أولى من المجازي.
  * ج3 892: النقل خلاف الأصل؛ إذا احتمل اللفظ النقلَ وعدمه فالأصل عدم النقل.
  * ج3 912: المجاز أولى من النقل.
  * ج3 1423: الدلالة تتّضح وضعًا أو عرفًا أو شرعًا — ثلاثة مصادر متقابلة، لا سلّم مراتب.
  * التفكير 61، 72: الطريقة العقلية وحدها أساس التفكير، والعلمية أسلوب متفرّع عنها.
  * التفكير 68، 76: العلمية لا تكون إلّا في المواد المحسوسة بالتجربة.
  * التفكير 107: العلمية ظنّيّة.
  * الدستور (CLAUDE.md): الوسم بقدر السند.

  ما يُبرهن هنا:
  ١. الطيّ المعتبر لا يُضيع شيئًا: له فكٌّ يعيد الأصل؛ ويتركّب؛ ويمتدّ إلى السلاسل.
     ومنه طيّ الخلية (الدال وحده) إلى سبع خانات من صفر/واحد وفكّها.
  ٢. المخزن لا يدخله إلّا ادّعاء يقبله الفاحص؛ والاسترجاع منه جوابٌ مرخَّص بنوعه.
  ٣. وسم الادّعاء لا يعلو أضعف ما في سلسلته.
  ٤. الترجيح: الحقيقة ثم المجاز ثم النقل.
  ٥. أساس الطريقة عقليّ دائمًا، والأسلوب العلميّ للمادّيّ وحده ونتيجته ظنّيّة.
  بلا sorry ولا axiom ولا native_decide.
-/
import Aql.Qaida
import Dal.Khaliya

namespace Mawsua

/-! ## ١. الطيّ والفكّ -/

/-- طيٌّ معتبر: كلّ مطويٍّ يُفكّ إلى أصله بعينه. -/
structure Tayy (A C : Type) where
  tawi : A → C
  fakk : C → Option A
  fakk_tawi : ∀ a, fakk (tawi a) = some a

variable {A B C : Type}

/-- الطيّ المعتبر لا يجمع مختلفين في مطويٍّ واحد. -/
theorem Tayy.injective (t : Tayy A C) {a b : A} (h : t.tawi a = t.tawi b) : a = b := by
  have h1 := t.fakk_tawi a
  have h2 := t.fakk_tawi b
  rw [h, h2] at h1
  exact (Option.some.inj h1).symm

/-- فمن طوى مختلفَين إلى خانة واحدة (كخانة «تخيّل» تجمع ما لا شاهد له) فطيُّه لا يُفكّ. -/
theorem la_tayy_maa_jam (f : A → C) {a b : A} (hne : a ≠ b) (h : f a = f b) :
    ¬ ∃ t : Tayy A C, t.tawi = f := by
  rintro ⟨t, rfl⟩
  exact hne (t.injective h)

/-- تركيب طيّين طيٌّ معتبر. -/
def Tayy.tarkib (s : Tayy A B) (t : Tayy B C) : Tayy A C where
  tawi a := t.tawi (s.tawi a)
  fakk c := (t.fakk c).bind s.fakk
  fakk_tawi a := by simp [t.fakk_tawi, s.fakk_tawi]

def fakkKull (f : C → Option A) : List C → Option (List A)
  | [] => some []
  | c :: cs => match f c, fakkKull f cs with
    | some a, some as => some (a :: as)
    | _, _ => none

/-- طيّ العنصر يمتدّ إلى السلسلة. -/
def Tayy.qaima (t : Tayy A C) : Tayy (List A) (List C) where
  tawi := List.map t.tawi
  fakk := fakkKull t.fakk
  fakk_tawi as := by
    induction as with
    | nil => rfl
    | cons a as ih => simp [fakkKull, t.fakk_tawi, ih]

/-! ### من الخلية إلى صفر/واحد -/

def ilaBits : Nat → Nat → List Bool
  | 0, _ => []
  | k + 1, v => (v % 2 == 1) :: ilaBits k (v / 2)

def minBits : List Bool → Nat
  | [] => 0
  | b :: bs => (if b then 1 else 0) + 2 * minBits bs

theorem ilaBits_tul (k v : Nat) : (ilaBits k v).length = k := by
  induction k generalizing v with
  | zero => rfl
  | succ k ih => simp [ilaBits, ih]

theorem minBits_ilaBits (k v : Nat) (h : v < 2 ^ k) : minBits (ilaBits k v) = v := by
  induction k generalizing v with
  | zero => simp at h; simp [ilaBits, minBits]; omega
  | succ k ih =>
    simp only [ilaBits, minBits]
    rw [ih (v / 2) (by rw [Nat.pow_succ] at h; omega)]
    rcases Nat.mod_two_eq_zero_or_one v with hv | hv <;> simp [hv] <;> omega

/-- طيّ رقم الخلية (أقلّ من 116) إلى سبع خانات ثنائيّة، وفكّها. -/
def tayyBits : Tayy (Fin 116) (List Bool) where
  tawi m := ilaBits 7 m.val
  fakk bs := if bs.length = 7 then
      (if h : minBits bs < 116 then some ⟨minBits bs, h⟩ else none) else none
  fakk_tawi m := by
    have hm : minBits (ilaBits 7 m.val) = m.val := minBits_ilaBits 7 m.val (by have := m.isLt; omega)
    simp [ilaBits_tul, hm]

/-- طيّ الخلية إلى رقمها (Dal/Khaliya.lean). -/
def tayyKhaliya : Tayy Dal.Khaliya (Fin 116) where
  tawi := Dal.n
  fakk m := some (Dal.fakk m)
  fakk_tawi k := by simp [Dal.fakk_n]

/-- من الدال وحده إلى صفر/واحد: كلّ سلسلة خلايا تُطوى ثنائيًّا وتُفكّ إلى نفسها. -/
def tayySifrWahid : Tayy (List Dal.Khaliya) (List (List Bool)) :=
  (tayyKhaliya.tarkib tayyBits).qaima

theorem sifrWahid_la_yudi (ks : List Dal.Khaliya) :
    tayySifrWahid.fakk (tayySifrWahid.tawi ks) = some ks :=
  tayySifrWahid.fakk_tawi ks

/-! ## ٢. المخزن: لا يدخله إلّا مرخَّص، والاسترجاع جوابٌ مرخَّص -/

open Qaida

variable {P : Type} [DecidableEq P]

/-- مدخل الموسوعة: ادّعاء بسلسلته، وسنده في المودَع (بصمة وموضع؛ يفحصه جانب الإيداع). -/
structure Madkhal (P : Type) where
  iddia : Iddia P
  sanad : String

/-- المخزن بالقاعدة q: كلّ مدخل فيه مقبول بالفاحص. -/
structure Makhzan (q : Qaida.Qaida P) (aslB : P → Bool) where
  madakhil : List (Madkhal P)
  kulluha : madakhil.all (fun m => maqbul q aslB m.iddia) = true

def Makhzan.faregh (q : Qaida.Qaida P) (aslB : P → Bool) : Makhzan q aslB := ⟨[], rfl⟩

/-- الإدخال: يُفحص؛ فإن رُفض بقي المخزن كما هو. -/
def Makhzan.udkhul {q : Qaida.Qaida P} {aslB : P → Bool} (s : Makhzan q aslB) (m : Madkhal P) :
    Makhzan q aslB :=
  if h : maqbul q aslB m.iddia = true then
    ⟨m :: s.madakhil, by simp [List.all_cons, h, s.kulluha]⟩
  else s

theorem udkhul_marfud {q : Qaida.Qaida P} {aslB : P → Bool} (s : Makhzan q aslB) (m : Madkhal P)
    (h : maqbul q aslB m.iddia = false) : (s.udkhul m).madakhil = s.madakhil := by
  simp [Makhzan.udkhul, h]

/-- الإدخالُ بالفاحص على مصفوفة القوانين (`Qaida.maqbulA`)، والمصفوفةُ قائمةُ القاعدة (`hq`). -/
def Makhzan.udkhulA {q : Qaida.Qaida P} {aslB : P → Bool} (s : Makhzan q aslB) (qs : Array (Qaida.Qanun P))
    (hq : q.qawanin = qs.toList) (m : Madkhal P) : Makhzan q aslB :=
  if h : maqbulA qs aslB m.iddia = true then
    have h' : maqbul q aslB m.iddia = true := (maqbulA_eq q qs hq aslB m.iddia) ▸ h
    ⟨m :: s.madakhil, by simp [List.all_cons, h', s.kulluha]⟩
  else s

/-- وهو `udkhul` بعينه: المخزنُ بعد الإدخال واحدٌ بالفاحصين (س1). -/
theorem udkhulA_eq {q : Qaida.Qaida P} {aslB : P → Bool} (s : Makhzan q aslB) (qs : Array (Qaida.Qanun P))
    (hq : q.qawanin = qs.toList) (m : Madkhal P) : s.udkhulA qs hq m = s.udkhul m := by
  have hA := maqbulA_eq q qs hq aslB m.iddia
  unfold Makhzan.udkhulA Makhzan.udkhul
  split <;> split
  · rfl
  · rename_i h1 h2; exact absurd (hA ▸ h1) h2
  · rename_i h1 h2; exact absurd (hA.symm ▸ h2) h1
  · rfl

/-- الاسترجاع بشرطٍ على القول: يعطي جوابًا بالقاعدة نفسها. -/
def Makhzan.istirja {q : Qaida.Qaida P} {aslB : P → Bool} (s : Makhzan q aslB) (f : P → Bool) :
    Jawab q aslB where
  iddiaat := (s.madakhil.filter (fun m => f m.iddia.qawl)).map Madkhal.iddia
  kulluha := by
    rw [List.all_eq_true]
    intro c hc
    simp only [List.mem_map, List.mem_filter] at hc
    obtain ⟨m, ⟨hm, _⟩, rfl⟩ := hc
    exact List.all_eq_true.mp s.kulluha m hm

/-- كلّ ما يُسترجع من المخزن مرخَّصٌ في القاعدة. -/
theorem istirja_murakhkhas {q : Qaida.Qaida P} {aslB : P → Bool} (s : Makhzan q aslB) (f : P → Bool) :
    ∀ c ∈ (s.istirja f).iddiaat, Murakhkhas q (fun y => aslB y = true) c.qawl :=
  jawab_sahih (s.istirja f)

/-! ## ٣. الوسم بقدر السند -/

/-- أوسام الدستور بترتيب ذكرها فيه، من الأضعف إلى الأقوى. -/
inductive Wasm
  | ray | taqdir | maqis | mafhus | mutabaq | mubarhanShahid | mubarhan
deriving DecidableEq, Repr

def Wasm.quwwa : Wasm → Nat
  | .ray => 0 | .taqdir => 1 | .maqis => 2 | .mafhus => 3
  | .mutabaq => 4 | .mubarhanShahid => 5 | .mubarhan => 6

/-- ترتيب الأوسام من الأقوى إلى الأضعف، كما في الدستور م2 وCLAUDE.md (قرار المالك 2026-10-15):
    مبرهن · مبرهن على الشاهد · مطابَق · مفحوص · مقيس · تقدير على عيّنة · رأي. -/
def Wasm.tartib : List Wasm := [.mubarhan, .mubarhanShahid, .mutabaq, .mafhus, .maqis, .taqdir, .ray]

theorem tartib_hasir : ∀ w : Wasm, w ∈ Wasm.tartib := by intro w; cases w <;> decide

theorem tartib_nodup : Wasm.tartib.Nodup := by decide

/-- القوّة تنزل درجةً واحدةً عند كلّ خطوة في الترتيب: فالترتيب والقوّة شيءٌ واحد. -/
theorem tartib_tanazuli : ∀ i : Fin 6, (Wasm.tartib.getD i.val .ray).quwwa = (Wasm.tartib.getD (i.val + 1) .ray).quwwa + 1 := by
  decide

/-- فلا وسمان بقوّةٍ واحدة. -/
theorem quwwa_tafriq (a b : Wasm) (h : a.quwwa = b.quwwa) : a = b := by
  cases a <;> cases b <;> simp [Wasm.quwwa] at h ⊢

/-- قوّة السلسلة: أضعف أصلٍ أو قانونٍ فيها. السلسلة الفارغة لا تُثبت شيئًا أصلًا. -/
def quwwatSilsila (aslW : P → Wasm) (qW : Nat → Wasm) : List (Khatwa P) → Nat
  | [] => 6
  | .asl p :: ks => min (aslW p).quwwa (quwwatSilsila aslW qW ks)
  | .qanun i :: ks => min (qW i).quwwa (quwwatSilsila aslW qW ks)

omit [DecidableEq P] in
/-- لا يعلو وسمُ الادّعاء وسمَ أيّ أصلٍ في سلسلته. -/
theorem wasm_la_yaalu_asl (aslW : P → Wasm) (qW : Nat → Wasm) (ks : List (Khatwa P)) (p : P)
    (hp : Khatwa.asl p ∈ ks) : quwwatSilsila aslW qW ks ≤ (aslW p).quwwa := by
  induction ks with
  | nil => cases hp
  | cons k ks ih =>
    rcases List.mem_cons.mp hp with h | h
    · subst h; simp only [quwwatSilsila]; exact Nat.min_le_left _ _
    · cases k <;> simp only [quwwatSilsila] <;> exact Nat.le_trans (Nat.min_le_right _ _) (ih h)

omit [DecidableEq P] in
/-- ولا يعلو وسمَ أيّ قانونٍ استُعمل فيها. -/
theorem wasm_la_yaalu_qanun (aslW : P → Wasm) (qW : Nat → Wasm) (ks : List (Khatwa P)) (i : Nat)
    (hi : Khatwa.qanun i ∈ ks) : quwwatSilsila aslW qW ks ≤ (qW i).quwwa := by
  induction ks with
  | nil => cases hi
  | cons k ks ih =>
    rcases List.mem_cons.mp hi with h | h
    · subst h; simp only [quwwatSilsila]; exact Nat.min_le_left _ _
    · cases k <;> simp only [quwwatSilsila] <;> exact Nat.le_trans (Nat.min_le_right _ _) (ih h)

/-! ## ٤. الترجيح بين الاحتمالات (ج3 826، 892، 912) -/

inductive Ihtimal | haqiqa | majaz | naql deriving DecidableEq, Repr

def Ihtimal.rutba : Ihtimal → Nat
  | .haqiqa => 0 | .majaz => 1 | .naql => 2

/-- يُحمل اللفظ على أعلى احتمالاته رتبةً. -/
def tarjih : List Ihtimal → Option Ihtimal
  | [] => none
  | x :: xs => match tarjih xs with
    | none => some x
    | some y => if x.rutba ≤ y.rutba then some x else some y

theorem tarjih_some (x : Ihtimal) (xs : List Ihtimal) : ∃ y, tarjih (x :: xs) = some y := by
  simp only [tarjih]
  split
  · exact ⟨_, rfl⟩
  · split <;> exact ⟨_, rfl⟩

theorem tarjih_min (xs : List Ihtimal) (y : Ihtimal) (h : tarjih xs = some y) :
    y ∈ xs ∧ ∀ x ∈ xs, y.rutba ≤ x.rutba := by
  induction xs generalizing y with
  | nil => cases h
  | cons x xs ih =>
    simp only [tarjih] at h
    split at h
    · rename_i hn
      cases h
      refine ⟨List.mem_cons_self .., fun z hz => ?_⟩
      rcases List.mem_cons.mp hz with rfl | hz
      · exact Nat.le_refl _
      · cases xs with
        | nil => cases hz
        | cons w ws => obtain ⟨_, hs⟩ := tarjih_some w ws; rw [hs] at hn; cases hn
    · rename_i y' hy'
      obtain ⟨hm, hle⟩ := ih y' hy'
      split at h <;> cases h
      · rename_i hxy
        exact ⟨List.mem_cons_self .., fun z hz => by
          rcases List.mem_cons.mp hz with rfl | hz
          · exact Nat.le_refl _
          · exact Nat.le_trans hxy (hle z hz)⟩
      · rename_i hxy
        exact ⟨List.mem_cons_of_mem _ hm, fun z hz => by
          rcases List.mem_cons.mp hz with rfl | hz
          · omega
          · exact hle z hz⟩

/-- ما دامت الحقيقة محتمَلةً لم يُحمل اللفظ على مجاز ولا نقل (826، 892). -/
theorem haqiqa_awla (xs : List Ihtimal) (hh : Ihtimal.haqiqa ∈ xs) : tarjih xs = some .haqiqa := by
  cases h : tarjih xs with
  | none => cases xs with
    | nil => cases hh
    | cons x xs => obtain ⟨_, hs⟩ := tarjih_some x xs; rw [hs] at h; cases h
  | some y =>
    have ⟨_, hle⟩ := tarjih_min xs y h
    have := hle _ hh
    cases y <;> simp [Ihtimal.rutba] at this ⊢

/-- وما دام المجاز محتمَلًا لم يُحمل على النقل (912). -/
theorem majaz_awla_min_naql (xs : List Ihtimal) (hm : Ihtimal.majaz ∈ xs) :
    tarjih xs ≠ some .naql := by
  intro h
  have := (tarjih_min xs .naql h).2 _ hm
  simp [Ihtimal.rutba] at this

/-! ## ٥. الطريقة: العقلية أساس، والعلمية أسلوب للمادّيّ وحده (التفكير 61، 68، 72، 76، 107) -/

inductive Tariqa | aqliyya | ilmiyya deriving DecidableEq, Repr

structure Bahth where
  maddaMahsusa : Bool   -- مادّة محسوسة تُخضع للتجربة

def asas (_ : Bahth) : Tariqa := .aqliyya

def uslub (b : Bahth) : Tariqa := if b.maddaMahsusa then .ilmiyya else .aqliyya

/-- نتيجة الأسلوب العلميّ لا توسم فوق «مقيس»: هي ظنّيّة، لا مبرهنة (107). -/
def sakfWasm : Tariqa → Nat
  | .aqliyya => Wasm.mubarhan.quwwa
  | .ilmiyya => Wasm.maqis.quwwa

theorem asas_aqli (b : Bahth) : asas b = .aqliyya := rfl

/-- التاريخ والفقه والمنطق وكلّ ما ليس مادّة محسوسة لا يُبحث بالأسلوب العلميّ (76). -/
theorem ghayr_maddi_la_ilmi (b : Bahth) (h : b.maddaMahsusa = false) : uslub b = .aqliyya := by
  simp [uslub, h]

theorem ilmi_zanni : sakfWasm .ilmiyya < Wasm.mubarhan.quwwa := by decide

/-! ## ٦. قيد الطريقة على الوسم (التفكير 78، 107) -/

/-- وسم الأصل بعد قيد طريقته: ما ثبت بالأسلوب العلميّ لا يعلو «مقيس»، لأنّ قابلية الخطأ أساسٌ فيه. -/
def qayd (t : Tariqa) (w : Wasm) : Wasm :=
  match t with
  | .aqliyya => w
  | .ilmiyya => if w.quwwa ≤ Wasm.maqis.quwwa then w else .maqis

theorem qayd_ilmi (w : Wasm) : (qayd .ilmiyya w).quwwa ≤ Wasm.maqis.quwwa := by
  cases w <;> decide

theorem qayd_la_yarfa (t : Tariqa) (w : Wasm) : (qayd t w).quwwa ≤ w.quwwa := by
  cases t <;> cases w <;> decide

omit [DecidableEq P] in
/-- ادّعاءٌ في سلسلته أصلٌ علميّ لا يُوسم فوق «مقيس»، مهما قويت بقيّة السلسلة. -/
theorem ilmi_fi_silsila (aslW : P → Wasm) (aslT : P → Tariqa) (qW : Nat → Wasm)
    (ks : List (Khatwa P)) (p : P) (hp : Khatwa.asl p ∈ ks) (ht : aslT p = .ilmiyya) :
    quwwatSilsila (fun x => qayd (aslT x) (aslW x)) qW ks ≤ Wasm.maqis.quwwa := by
  have h := wasm_la_yaalu_asl (fun x => qayd (aslT x) (aslW x)) qW ks p hp
  simp only [ht] at h
  exact Nat.le_trans h (qayd_ilmi _)

/-! ## ٧. السؤال: حكمٌ بسلسلته أو «لا حكم» — والغياب ليس امتناعًا (الدستور م13، م16) -/

/-- نتيجة السؤال: جوابٌ مرخَّص غير فارغ، أو «لا حكم». لا مُنشئ للنفي: غياب الشاهد لا يُنتج امتناعًا. -/
inductive Natija (q : Qaida.Qaida P) (aslB : P → Bool)
  | hukm (j : Jawab q aslB) (ghayrFaregh : j.iddiaat ≠ [])
  | laHukm

def sual {q : Qaida.Qaida P} {aslB : P → Bool} (s : Makhzan q aslB) (f : P → Bool) : Natija q aslB :=
  if h : (s.istirja f).iddiaat = [] then .laHukm else .hukm (s.istirja f) h

/-- «لا حكم» إن لم يكن في المخزن مدخلٌ يوافق السؤال، لا غير. -/
theorem sual_laHukm_iff {q : Qaida.Qaida P} {aslB : P → Bool} (s : Makhzan q aslB) (f : P → Bool) :
    (∃ j h, sual s f = .hukm j h) ↔ ∃ m ∈ s.madakhil, f m.iddia.qawl = true := by
  constructor
  · rintro ⟨j, h, hs⟩
    unfold sual at hs
    split at hs
    · cases hs
    · rename_i hne
      simp only [Makhzan.istirja, List.map_eq_nil_iff, List.filter_eq_nil_iff] at hne
      exact Classical.byContradiction fun hc => hne fun a ha hf => hc ⟨a, ha, hf⟩
  · rintro ⟨m, hm, hf⟩
    unfold sual
    split
    · rename_i he
      simp only [Makhzan.istirja, List.map_eq_nil_iff, List.filter_eq_nil_iff] at he
      have := he m hm
      simp [hf] at this
    · rename_i hne
      exact ⟨_, hne, rfl⟩

/-- حكم السؤال هو الاسترجاع من المخزن بعينه، فقوله مرخَّص بـ `istirja_murakhkhas`. -/
theorem sual_hukm_istirja {q : Qaida.Qaida P} {aslB : P → Bool} (s : Makhzan q aslB) (f : P → Bool)
    (j : Jawab q aslB) (h : j.iddiaat ≠ []) (hs : sual s f = .hukm j h) : j = s.istirja f := by
  unfold sual at hs
  split at hs
  · cases hs
  · cases hs; rfl

end Mawsua
