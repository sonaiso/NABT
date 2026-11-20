/-!
# المدلولُ أوّلًا: أسبقُ من الوضع، وأسبقُ من الدالّ، والمعجمُ شاهدُ مطابقةٍ لا برهان

السند ج3: «لأن الوضع للشيء فرع عن تصوره»؛ «الأشياء الموضوعة لها هذه الألفاظ فهي المعاني الذهنية دون الخارجية»؛
«فالألفاظ ليست دلالة على الحقائق، وإنما هي تعبير عما في الذهن». والتفكير: المعلوماتُ السابقة شرطُ الحكم.

**موضعُه في سلسلة الاستيراد:** هذا الملفّ لا يستورد شيئًا، و‎Category.lean‎ يستورده ويعرّف القسمَ
(اسم/فعل/حرف) دالّةً فيه (‎Cat.kindOfMadlul‎) — فالمدلولُ قبل القسم في البرهان المغلق نفسه، لا في التعليق.

الصورةُ الرياضيّة: `Madlul` نوعٌ لا يذكر اللفظ؛ `Wad` دالّةٌ **من** المدلول إلى اللفظ (فلا تُعرَّف بلا مدلول)؛
والحكمُ (كلّيّ/جزئيّ، متواطئ/مشكّك) دالّةٌ في `Madlul` وحده؛ و`Shahid` شيءٌ خارجيٌّ لا يدخل في تعريف الحكم.

**تصحيحٌ عن v10:** كانت ‎kulli‎ تُقرأ من عدد الأفراد (فردٌ واحد ⇒ جزئيّ)، وهذا يخالف نصّ ج3:
«فالكلي هو الذي لا يمنع نفس تصوره من وقوع الشركة فيه، سواء وقعت الشركة كالحيوان … أم لم تقع مع إمكانها
كالشمس، أم لم تقع مع استحالتها كالإله». فالكلّيّةُ حقلٌ في التصوّر (‎yamnaShirka‎) لا عددٌ في الخارج —
ومبرهنةُ ‎shams‎ أدناه تُثبت أنّ التعريفين يفترقان.
-/

namespace SLGE
namespace Awwalan

/-- المدلولُ وحده: حقيقةٌ (رقمُ ماهيّة) وخواصُّ وعلاقاتٌ وقابليّاتٌ وأفرادٌ في التصوّر، و«هل يمنع تصوّرُه الشركة»،
و«معنًى في نفسه» (‎ind‎) و«زمانٌ بهيئته» (‎tim‎) — ولا لفظ. -/
structure Madlul where
  haqiqa : Nat
  khawass : List Nat
  alaqat : List (Nat × Nat)
  qabiliyyat : List Nat
  afrad : List Nat
  yamnaShirka : Bool := false
  ind : Bool := true
  tim : Bool := false
  deriving DecidableEq, Repr

inductive Kulliyya | juzi | kulli
  deriving DecidableEq, Repr
inductive Tawatu | mutawati | mushakkik | laHukm
  deriving DecidableEq, Repr

/-- «الكلي هو الذي لا يمنع نفس تصوره من وقوع الشركة فيه». -/
def kulli (m : Madlul) : Kulliyya := if m.yamnaShirka then .juzi else .kulli

/-- «إن استوى معناه في أفراده … فهو المتواطئ … وأما إن اختلف … فهو المشكك» — حكمٌ على أفراد التصوّر. -/
def tawatu (m : Madlul) : Tawatu :=
  match m.afrad with
  | [] => .laHukm
  | [_] => .laHukm
  | a :: rest => if rest.all (· == a) then .mutawati else .mushakkik

/-- الوضع: دالّةٌ من المدلول إلى اللفظ (‎Lafz‎ نوعٌ ما). -/
def Wad (Lafz : Type) := Madlul → Lafz

/-- **لا وضعَ بلا مدلول:** إن خلا نوعُ المدلول فكلُّ وضعٍ فارغٌ — لا يُسمّي لفظًا واحدًا. -/
theorem la_wad_bila_madlul {Lafz : Type} (h : Madlul → False) (w : Wad Lafz) :
    ¬ ∃ m : Madlul, ∃ l : Lafz, w m = l := fun ⟨m, _, _⟩ => h m

/-- **والمدلولُ لا يفتقر إلى اللفظ:** يُبنى مدلولٌ بلا أيّ نوعِ لفظ. -/
def insan : Madlul := { haqiqa := 0, khawass := [1], alaqat := [], qabiliyyat := [], afrad := [1, 1, 1] }
theorem madlul_bila_lafz : tawatu insan = .mutawati ∧ kulli insan = .kulli := by decide

/-- **الشمسُ كلّيٌّ بفردٍ واحد** (ج3): الكلّيّةُ من التصوّر لا من عدد الأفراد. -/
def shams : Madlul := { haqiqa := 1, khawass := [2, 3], alaqat := [], qabiliyyat := [], afrad := [1] }
theorem shams_kulli : shams.afrad.length = 1 ∧ kulli shams = .kulli := by decide

/-- **ولا عددَ يعيّن الكلّيّة:** لكلّ قائمة أفراد مدلولٌ كلّيٌّ وآخرُ جزئيٌّ بها نفسِها. -/
theorem kulli_la_bil_adad (fs : List Nat) :
    kulli { haqiqa := 0, khawass := [], alaqat := [], qabiliyyat := [], afrad := fs } = .kulli ∧
    kulli { haqiqa := 0, khawass := [], alaqat := [], qabiliyyat := [], afrad := fs, yamnaShirka := true } = .juzi :=
  ⟨rfl, rfl⟩

/-- **الحكمُ بالمدلول وحده:** مدلولان اتّفقا في (منع الشركة، الأفراد) اتّفق حكماهما، أيًّا كانت بقيّةُ الحقول. -/
theorem hukm_bil_madlul (m m' : Madlul) (h1 : m.yamnaShirka = m'.yamnaShirka) (h2 : m.afrad = m'.afrad) :
    kulli m = kulli m' ∧ tawatu m = tawatu m' := by
  unfold kulli tawatu; rw [h1, h2]; exact ⟨rfl, rfl⟩

/-- الشاهدُ: مصدرٌ وموضعٌ وحقلٌ يطابقه — خارجَ المدلول. -/
structure Shahid where
  masdar : String
  mawdi : Nat
  haql : Nat     -- 0 حقيقة، 1 خواص، 2 علاقات، 3 قابليات، 4 أفراد
  deriving DecidableEq, Repr

/-- المطابقة: الشاهدُ يصيب حقلًا قائمًا؛ لا يُنشئه. -/
def mutabaqa (m : Madlul) (s : Shahid) : Bool :=
  match s.haql with
  | 0 => true
  | 1 => !m.khawass.isEmpty
  | 2 => !m.alaqat.isEmpty
  | 3 => !m.qabiliyyat.isEmpty
  | 4 => !m.afrad.isEmpty
  | _ => false

/-- **الشاهدُ لا يُنشئ حقلًا (عامًّا):** إن طابق شاهدٌ حقلًا غيرَ الحقيقة فذلك الحقلُ قائمٌ في المدلول قبله،
وشاهدٌ على حقلٍ لا تعرفه البنية لا يطابق أبدًا. -/
theorem mutabaqa_qaim (m : Madlul) (s : Shahid) (h : mutabaqa m s = true) :
    s.haql ≤ 4 ∧ (s.haql = 1 → m.khawass ≠ []) ∧ (s.haql = 2 → m.alaqat ≠ []) ∧
    (s.haql = 3 → m.qabiliyyat ≠ []) ∧ (s.haql = 4 → m.afrad ≠ []) := by
  unfold mutabaqa at h
  rcases s with ⟨src, p, q⟩
  simp only at h ⊢
  match q, h with
  | 0, _ => simp
  | 1, h => simp_all
  | 2, h => simp_all
  | 3, h => simp_all
  | 4, h => simp_all
  | n + 5, h => simp at h

/-- **مثالُه:** مدلولٌ بلا قابليّات لا يطابقه شاهدُ قابليّات. -/
theorem shahid_la_yunshi (h : Nat) (src : String) (p : Nat) :
    mutabaqa { haqiqa := h, khawass := [], alaqat := [], qabiliyyat := [], afrad := [] } ⟨src, p, 3⟩ = false := rfl

/-! **ملاحظةُ أمانة:** كانت في v10 مبرهنةٌ ‎hukm_mustaqill‎ صورتُها ‎x = x‎ (تحصيلُ حاصل)، فحُذفت.
أنّ الشواهد لا تدخل في الحكم أمرٌ **بالتعريف** (توقيعُ ‎kulli‎ و‎tawatu‎ لا يأخذ ‎Shahid‎) لا بمبرهنة؛
وما يُبرهَن فعلًا هو ‎mutabaqa_qaim‎ (الشاهدُ لا يُنشئ حقلًا) و‎hukm_bil_madlul‎ (الحكمُ يتعيّن بحقلين من المدلول). -/

end Awwalan
end SLGE
