import A116.Qism

/-!
# الممنوعُ من الصرف: دالّةُ العلل، وكشفُ الشكل، والقراءةُ بالعامل المتّصل (ADR ٥٥)

الأبياتُ من الألفيّة في شرح ابن عقيل المختوم (`corpora/ibn-aqil/sharh-alfiyya.txt.gz`، بأرقام أسطره):

* «الصرف تنوين أتى مبينا معنى به يكون الاسم أمكنا» (س7178) — فما ظهر فيه التنوينُ منصرفٌ (`tanwin_munsarif`).
* علّةٌ تكفي وحدَها: «فألف التأنيث مطلقا منع صرف الذي حواه» (س7202)، «وكن لجمع مشبه مفاعلا أو المفاعيل
  بمنع كافلا» (س7254).
* الوصفُ مع ثانية: «وزائدا فعلان في وصف» (س7207)، «ووصف أصلي ووزن أفعلا» (س7218)، «ومنع عدل مع وصف معتبر في
  لفظ مثنى وثلاث وأخر» (س7241).
* العلَمُ مع ثانية: التركيبُ المزجيّ (س7280)، زائدا فعلان (س7286)، التأنيث (س7290–7293)، العجمةُ مع الزيادة على
  الثلاث (س7307)، وزنُ الفعل (س7315)، العدل (س7343)؛ «وأصرفن ما نكرا من كل ما التعريف فيه أثرا» (س7360).
* والممنوعُ يُجرّ بالفتحة «ما لم يضف أو يك بعد أل» (س641) — أل والإضافةُ تُخرجانه إلى الصحيح.

**الدالّة** `mamnu`: علّةٌ قويّة (ألفُ التأنيث، منتهى الجموع)، أو وصفٌ مع (فعلان، أفعل، عدل)، أو علَمٌ مع (تركيب،
فعلان، تأنيث، عجمةٍ فوق الثلاث، وزنِ فعل، عدل) — بشرط ألّا يظهر تنوينٌ ولا أل. **مبرهن**: العلّةُ القويّة تكفي
(`strong_alone`)، والوصفُ وحدَه والعلَميّةُ وحدَها لا يمنعان (`wasf_alone`، `alam_alone`)، وزوالُ التعريف
يصرف ما منعتْه العلَميّة (`nakira_munsarif`)، والتنوينُ وأل يصرفان (`tanwin_munsarif`، `al_munsarif`).

**الشكلُ** على (حرف، حركة): منتهى الجموع مَفَاعِل/مَفَاعِيل (`muntahaShape`)، أَفْعَل (`afalShape`)، فَعْلَان
(`falanShape`)، بشواهد (`shape_witnesses`).

**القراءةُ بالعامل المتّصل**: حرفُ جرٍّ متّصلٌ بالاسم (بِ، لِ، كَ، وواوُ القسم وتاؤه) — «هاك حروف الجر» (س4635) —
يعيّن الجرَّ: `readJ` سليمٌ (`readJ_sound`)، ويقرأ فتحةَ الممنوع جرًّا حيث يمتنع القارئُ بالصنف (`mamnu_needs_amil`)،
ويقرأ كلَّ زوجٍ مجرورٍ في الجدول (`readJ_all_jarr`).
-/

namespace A116.Mamnu

open A116.Qism

/-! ## دالّةُ العلل -/

structure Sifat where
  alam : Bool
  wasf : Bool
  tanithAlif : Bool
  muntaha : Bool
  falan : Bool
  afal : Bool
  adl : Bool
  tarkib : Bool
  tanith : Bool
  ajamiOver3 : Bool
  waznFil : Bool
  tanwin : Bool
  al : Bool
  deriving DecidableEq, Repr

def strong (s : Sifat) : Bool := s.tanithAlif || s.muntaha

def wasfPair (s : Sifat) : Bool := s.wasf && (s.falan || s.afal || s.adl)

def alamPair (s : Sifat) : Bool :=
  s.alam && (s.tarkib || s.falan || s.tanith || s.ajamiOver3 || s.waznFil || s.adl)

def mamnu (s : Sifat) : Bool := !s.tanwin && !s.al && (strong s || wasfPair s || alamPair s)

theorem strong_alone (s : Sifat) (h : strong s = true) (ht : s.tanwin = false) (ha : s.al = false) :
    mamnu s = true := by
  simp [mamnu, h, ht, ha]

theorem wasf_alone (s : Sifat) (hs : strong s = false) (ha : s.alam = false)
    (h : s.falan = false ∧ s.afal = false ∧ s.adl = false) : mamnu s = false := by
  obtain ⟨h1, h2, h3⟩ := h
  simp [mamnu, hs, wasfPair, alamPair, ha, h1, h2, h3]

theorem alam_alone (s : Sifat) (hs : strong s = false) (hw : s.wasf = false)
    (h : s.tarkib = false ∧ s.falan = false ∧ s.tanith = false ∧ s.ajamiOver3 = false ∧
      s.waznFil = false ∧ s.adl = false) : mamnu s = false := by
  obtain ⟨h1, h2, h3, h4, h5, h6⟩ := h
  simp [mamnu, hs, wasfPair, alamPair, hw, h1, h2, h3, h4, h5, h6]

/-- «وأصرفن ما نكرا»: ما منعتْه العلَميّةُ وحدَها يُصرف إذا زال التعريف. -/
theorem nakira_munsarif (s : Sifat) (hs : strong s = false) (hw : wasfPair s = false) :
    mamnu { s with alam := false } = false := by
  have h1 : strong { s with alam := false } = strong s := rfl
  have h2 : wasfPair { s with alam := false } = wasfPair s := rfl
  simp [mamnu, h1, h2, hs, hw, alamPair]

theorem tanwin_munsarif (s : Sifat) (h : s.tanwin = true) : mamnu s = false := by
  simp [mamnu, h]

theorem al_munsarif (s : Sifat) (h : s.al = true) : mamnu s = false := by
  simp [mamnu, h]

/-! ## الشكل -/

inductive V | a | u | i | o | none
  deriving DecidableEq, Repr

abbrev Word := List (Char × V)

/-- مَفَاعِل ومَفَاعِيل: مفتوحان، ثمّ ألفٌ ساكنة، ثمّ مكسور، ثمّ (ياءٌ ساكنة) ثمّ الآخر. -/
def muntahaShape : Word → Bool
  | [(_, .a), (_, .a), ('ا', .o), (_, .i), _] => true
  | [(_, .a), (_, .a), ('ا', .o), (_, .i), ('ي', .o), _] => true
  | _ => false

/-- أَفْعَل: همزةٌ مفتوحة، ساكن، مفتوح، الآخر. -/
def afalShape : Word → Bool
  | [('ء', .a), (_, .o), (_, .a), _] => true
  | _ => false

/-- فَعْلَان: مفتوح، ساكن، مفتوح، ألفٌ ساكنة، نون. -/
def falanShape : Word → Bool
  | [(_, .a), (_, .o), (_, .a), ('ا', .o), ('ن', _)] => true
  | _ => false

theorem shape_witnesses :
    muntahaShape [('م', .a), ('س', .a), ('ا', .o), ('ج', .i), ('د', .a)] = true ∧
    muntahaShape [('م', .a), ('ص', .a), ('ا', .o), ('ب', .i), ('ي', .o), ('ح', .u)] = true ∧
    muntahaShape [('ك', .i), ('ت', .a), ('ا', .o), ('ب', .u)] = false ∧
    afalShape [('ء', .a), ('ك', .o), ('ب', .a), ('ر', .u)] = true ∧
    afalShape [('ء', .i), ('ص', .o), ('ب', .a), ('ع', .u)] = false ∧
    falanShape [('س', .a), ('ك', .o), ('ر', .a), ('ا', .o), ('ن', .a)] = true ∧
    falanShape [('ع', .u), ('ث', .o), ('م', .a), ('ا', .o), ('ن', .a)] = false := by decide

/-! ## القراءةُ بالعامل المتّصل -/

/-- حرفُ جرٍّ متّصل: الحالةُ جرٌّ إن كان الصنفُ يُظهر الجرَّ بذلك الآخر. -/
def readJ (c : Cls) (e : Ending) : Option Irab :=
  if ending c .jarr == some e then some .jarr else none

theorem readJ_sound (c : Cls) (e : Ending) (i : Irab) (h : readJ c e = some i) :
    i = .jarr ∧ ending c .jarr = some e := by
  unfold readJ at h
  split at h
  · rename_i hc; cases h; exact ⟨rfl, beq_iff_eq.1 hc⟩
  · cases h

theorem mamnu_needs_amil :
    read₁ classV .iMamnu .fatha = none ∧ readJ .iMamnu .fatha = some .jarr := by decide

theorem readJ_all_jarr : ∀ c ∈ classes, ∀ e ∈ endings, ending c .jarr = some e →
    readJ c e = some .jarr := by decide

end A116.Mamnu
