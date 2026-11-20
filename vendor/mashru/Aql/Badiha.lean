/-
  Aql/Badiha.lean — «سرعة البديهة» للنبهاني (ذو القعدة 1396)، مصوغةً لطبقة الحكم.

  السند: أسطر الملف المحوَّل badiha.txt (بصمة الأصل docx: 483cf19f…).
  * 61: الذكاء سرعة الإحساس وسرعة الربط.
  * 97: سرعة الربط تأتي طبيعية إذا وُجدت المعلومات؛ وسرعة الإحساس تأتي من الانتباه.
  * 99: الانتباه أن تتقصّد فحص الشيء المحسّ ومعرفته.
  * 205: سرعة البديهة لا تأتي إلّا من سرعة الإدراك، وسرعة الإدراك لا تستلزمها (مثال عمر).
  * 259–263: حقيقتها سرعة الإدراك ثم سرعة الحكم؛ والإدراك يهيّئ للحكم.
  * 37، 215، 245–247: التعريفات والأحكام الشرعية والأمور الفنية والسياسة والدلالات لا تُحلّ إلّا
    بالتفكير ولا يصحّ أن تدخلها البديهة؛ والآليّات (الكرسي) يكفي فيها ذكر الاسم؛ والمفاجآت والأسئلة
    الخبيثة والعاجل لا بدّ لها من البديهة؛ والظروف هي الحَكَم.
  * 55: السرعة إن لم تصطدم بحائط أنتجت الحكم فورًا، وإن اصطدمت فالأمر يحتاج درسًا.
  * 287–293: معرفة القصد من واقع الحال وحده ناقصة وهي «سرعة ملاحظة»؛ والبديهة ربطٌ بالجامع.
  * 297–299: تعمية الفعل أو الكلام مع قصد واحد = ملاحظة؛ تعمية القصد مع دلالات عدّة = بديهة.

  وصلُ «الجامع» بالمحرّك: الجامع هنا هو القاعدة الواحدة (Aql/Qaida.lean)؛ فالبديهة المقبولة في
  المحرّك حكمٌ مرخَّص بسلسلة يقبلها الفاحص، والملاحظة حكمٌ ظنّيّ ناقص لا يُرفع إلى مرخَّص.
  بلا sorry ولا axiom ولا native_decide.
-/
import Aql.Qaida

namespace Badiha

/-! ## ١. الذكاء والإدراك والحكم -/

structure Hal where
  intibah   : Bool   -- تقصّد فحص الشيء المحسّ (99)
  maalumat  : Bool   -- وجود معلومات سابقة عنه (97)
  saraTafkir : Bool  -- سرعة التفكير (191)

/-- سرعة الإحساس من الانتباه، وسرعة الربط من وجود المعلومات (97). -/
def saraIhsas (h : Hal) : Bool := h.intibah
def saraRabt (h : Hal) : Bool := h.maalumat

/-- الذكاء المستعمَل: سرعة الإحساس وسرعة الربط معًا (61). -/
def dhaka (h : Hal) : Bool := saraIhsas h && saraRabt h

/-- سرعة الإدراك: استعمال الذكاء (73، 103). -/
def saraIdrak (h : Hal) : Bool := dhaka h

/-- لا ذكاء مستعمَل بلا انتباه، ولا بلا معلومات سابقة (97–99). -/
theorem la_dhaka_bila_intibah (h : Hal) (hi : h.intibah = false) : dhaka h = false := by
  simp [dhaka, saraIhsas, hi]

theorem la_dhaka_bila_maalumat (h : Hal) (hm : h.maalumat = false) : dhaka h = false := by
  simp [dhaka, saraRabt, hm]

/-! ## ٢. المسار بحسب الموضوع والظرف (37، 215، 245–247، 55) -/

/-- نوع الموضوع كما يعدّه النصّ. -/
inductive Mawdu
  | aali         -- الواضح الذي يكفيه ذكر اسمه: الكرسي والصحن (29، 245)
  | tarif        -- التعريفات (37)
  | hukmShari    -- الأحكام الشرعية (37)
  | fanni        -- الأمور الفنية (37)
  | siyasaDalala -- التفكير في السياسة وفي الدلالات (215)
  | mufajaa      -- المفاجآت والأسئلة الخبيثة والعاجل (37)
deriving DecidableEq, Repr

inductive Tariq
  | dhikrIsm   -- يكفي ذكر الاسم، بلا درس
  | dars       -- درس وتمحيص: التفكير
  | badiha     -- سرعة البديهة
deriving DecidableEq, Repr

/-- الظرف: هل يتّسع للتفكير؟ (33، 247) -/
def tariq (m : Mawdu) (dharfMuwat : Bool) : Tariq :=
  match m with
  | .aali => .dhikrIsm
  | .tarif | .hukmShari | .fanni | .siyasaDalala => .dars
  | .mufajaa => if dharfMuwat then .dars else .badiha

/-- التعريفات والأحكام والأمور الفنية والدلالات لا يدخلها مسار البديهة، أيًّا كان الظرف (37، 215). -/
theorem la_badiha_fi_alahkam (m : Mawdu) (d : Bool)
    (hm : m = .tarif ∨ m = .hukmShari ∨ m = .fanni ∨ m = .siyasaDalala) :
    tariq m d = .dars := by
  rcases hm with rfl | rfl | rfl | rfl <;> rfl

/-- الآليّات لا تُدرس ولا تُمحَّص (245). -/
theorem aali_bila_dars (d : Bool) : tariq .aali d ≠ .dars := by simp [tariq]

/-- المفاجأة في ظرف لا يتّسع للتفكير مسارُها البديهة (33، 37). -/
theorem mufajaa_dayyiqa_badiha : tariq .mufajaa false = .badiha := rfl

/-- المسار السريع مع الرجوع (55): يُجرَّب، فإن اصطدم بحائط رُجع إلى الدرس. -/
def masarSari {α : Type} (sari : Option α) (dars : Unit → Option α) : Option α :=
  match sari with
  | some x => some x
  | none => dars ()

/-- إن لم يصطدم المسار السريع بحائط فحكمه هو الحكم؛ وإن اصطدم فالحكم ما يعطيه الدرس، لا غيره. -/
theorem masarSari_sahih {α : Type} (s : Option α) (d : Unit → Option α) (x : α)
    (h : masarSari s d = some x) : s = some x ∨ (s = none ∧ d () = some x) := by
  cases s with
  | some y => simp [masarSari] at h; exact Or.inl (by rw [h])
  | none => exact Or.inr ⟨rfl, h⟩

/-! ## ٣. البديهة والملاحظة (205، 287–299) -/

inductive Tamiya | filWaKalam | qasd deriving DecidableEq, Repr
inductive Naw | mulahaza | badiha | la deriving DecidableEq, Repr

/-- البديهة: إدراك سريع، والتعمية في القصد، والربط بالجامع. ما نقصه الربط ملاحظة؛ وما نقصه الإدراك لا شيء. -/
def naw (h : Hal) (t : Tamiya) (rabtBilJami : Bool) : Naw :=
  if saraIdrak h then
    if t = .qasd && rabtBilJami then .badiha else .mulahaza
  else .la

/-- لا بديهة بلا سرعة إدراك (205). -/
theorem badiha_min_idrak (h : Hal) (t : Tamiya) (r : Bool) (hb : naw h t r = .badiha) :
    saraIdrak h = true := by
  unfold naw at hb; split at hb
  · assumption
  · cases hb

/-- لا بديهة بلا ربطٍ بالجامع؛ يبقى ملاحظة (293). -/
theorem la_badiha_bila_rabt (h : Hal) (t : Tamiya) (hd : saraIdrak h = true) :
    naw h t false = .mulahaza := by
  simp [naw, hd]

/-- تعمية الفعل أو الكلام تعطي ملاحظة لا بديهة (297–299). -/
theorem tamiyat_alfil_mulahaza (h : Hal) (r : Bool) (hd : saraIdrak h = true) :
    naw h .filWaKalam r = .mulahaza := by
  simp [naw, hd]

/-- سرعة التفكير لا تستلزم البديهة: شاهد عمر (191، 205، 225).
    سريع التفكير، والتعمية في القصد، لكن لم يحصل له الربط في الحادثة. -/
theorem saraTafkir_la_tastalzim :
    ¬ ∀ (h : Hal) (t : Tamiya) (r : Bool), h.saraTafkir = true → naw h t r = .badiha := by
  intro hall
  have := hall ⟨true, true, true⟩ .qasd false rfl
  simp [naw, saraIdrak, dhaka, saraIhsas, saraRabt] at this

/-! ## ٤. الوصل بالقاعدة: البديهة في المحرّك حكمٌ مرخَّص (ج1 29؛ badiha 293) -/

open Qaida in
/-- إن كان «الربط بالجامع» هو قبول الفاحص لسلسلة الحكم على القاعدة، فكلّ حكم بديهيّ مرخَّص. -/
theorem badiha_murakhkhas {P : Type} [DecidableEq P] (q : Qaida.Qaida P) (aslB : P → Bool)
    (h : Hal) (t : Tamiya) (c : Iddia P)
    (hb : naw h t (maqbul q aslB c) = .badiha) :
    Murakhkhas q (fun y => aslB y = true) c.qawl := by
  have hr : maqbul q aslB c = true := by
    unfold naw at hb
    split at hb
    · split at hb
      · rename_i hc; simp at hc; exact hc.2
      · cases hb
    · cases hb
  exact maqbul_murakhkhas q aslB c hr

end Badiha
