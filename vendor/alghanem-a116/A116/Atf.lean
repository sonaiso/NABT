import A116.Mufrad

/-!
# حروفُ العطف علاقاتٌ منقولةٌ بمعانيها، لا بوّاباتٌ منطقيّة (ADR ٨٢)

أمرُ المالك (2026-10-16): «الأدواتُ المنطقيّة (و، أو، أم، ف، ثمّ)… ج3 يعدّها حروفَ العطف ويذكر معانيها، فتُبنى
علاقاتٍ منقولةً بمعانيها، لا بوّاباتِ and/or/xor مفروضةً عليها».

## السند (منقولٌ بلفظه؛ أرقامُ الأسطر في شرح ابن عقيل المختوم، والمراسي مفحوصةٌ في `tests/test_atf.py`)

* الحرفُ لا يستقلّ بمعناه (ج3، `Mufrad.harf_iff`)؛ وعطفُ النسق «التابعُ المتوسّطُ بينه وبين متبوعه أحدُ الحروف»
  (س6441) — فالعطفُ علاقةٌ بين معطوفٍ عليه ومعطوف.
* «ما يُشرك المعطوفَ مع المعطوف عليه مطلقًا أي لفظًا وحكمًا وهي الواو … وثمّ … والفاء … وحتّى … وأم … وأو»
  (س6446)؛ «هذه الثلاثة [بل، لا، لكن] تُشرك الثاني مع الأوّل في إعرابه لا في حكمه» (س6452).
* «فالواو لمطلق الجمع … واحتمل كونُ عمرو جاء بعد زيد أو جاء قبله أو جاء مصاحبًا له، وإنّما يتبيّن ذلك
  بالقرينة» (س6457–6459)؛ ج3: «لا تفيد ترتيبًا ولا معيّة».
* «تدلّ الفاء على تأخّر المعطوف عن المعطوف عليه متّصلًا به، وثمّ على تأخّره عنه منفصلًا» (س6470)؛ ج3: الفاء
  «الترتيب والتعقيب»، وثمّ «الترتيب والتراخي».
* حتّى: «أن يكون بعضًا ممّا قبله وغايةً له» (س6483)؛ ج3: «تفيد الترتيب».
* «اختصّت الواو … بأنّها يُعطف بها حيث لا يُكتفى بالمعطوف عليه نحو اختصم زيدٌ وعمرو … فلا تقول اختصم زيدٌ
  فعمرو» (س6465–6468).
* أم «متّصلةٌ وهي التي تقع بعد همزة التسوية … والتي تقع بعد همزةٍ مغنيةٍ عن أيّ» (س6486)؛ وإلّا «فهي منقطعةٌ
  وتفيد الإضرابَ كبل» (س6499)؛ ج3: «تعليقُ الحكم بأحد المذكورين … مع العلم بأحدهما والشكّ في تعيينه».
* أو «للتخيير … وللإباحة … والفرقُ بين الإباحة والتخيير أنّ الإباحة لا تمنع الجمعَ والتخييرُ يمنعه، وللتقسيم …
  وللإبهام … وللشكّ … وللإضراب» (س6504–6509)؛ ج3: «تعليقُ الحكم بأحد المذكورين».

## ما يُبرهَن

١. **الواو أعمُّ الحروف ترتيبًا**: كلُّ رتبةٍ يجيزها حرفُ عطفٍ يجيزها الواو (`wa_aamm`)، وهو لا يعيّن الترتيب —
   يجيز السابقَ واللاحق — فتعيينُه بالقرينة (`wa_la_tartib`).
٢. **الفاءُ وثمّ** ترتيبٌ كلاهما ويفترقان بالاتّصال والانفصال (`fa_thumma`).
٣. **البوّابةُ الثنائيّة عمياءُ عن المعاني**: الواو والفاء وثمّ وحتّى جدولُ صدقها على الحكم واحد (الجمع)،
   ورتبُها مختلفة — فلا دالّةَ في جدول الصدق تفصلها (`and_blind`).
٤. **«أو» ليست بوّابةً واحدة**: التخييرُ يمنع الجمع والإباحةُ لا تمنعه، وهما معنيان لحرفٍ واحد — فلا دالّةَ
   بوليّةٌ واحدةٌ هي «أو» (`aw_not_one_gate`)؛ وتعيينُ المعنى بالسياق.
٥. **أم** متّصلةٌ بعد الهمزة ومنقطعةٌ (إضرابٌ) دونها (`am_hamza`)، والمنقطعةُ تشارك «بل» إضرابَها.
٦. **اختصاصُ الواو**: فعلُ المشاركة لا يُعطف معه إلّا بالواو (`ikhtisam_wa`).
٧. **الإشراك**: الستّةُ تُشرك لفظًا وحكمًا، والثلاثةُ لفظًا فقط (`ishrak_count`)؛ وكلُّها تُشرك في الإعراب.
٨. **حرفُ العطف حرف**: لا يستقلّ بمعناه (`atf_harf`)، ولا عطفَ بلا طرفين (بنيةُ `Atf`).

ما لا يُبرهَن: أنّ هذه معاني العربيّة — ذلك مرويُّ الشرح وج3 بأسطرها (`ATF_MAANI_ARE_NAQL`)؛ ولا تُقرأ الحروفُ
ولا معانيها من الخانات (`ATF_NOT_IN_GATE`).
-/

namespace A116.Atf

open A116.Mufrad

/-- حروفُ العطف التسعة (س6443، س6451؛ ج3). -/
inductive Harf where
  | wa | fa | thumma | hatta | aw | am | la | bal | lakin
  deriving DecidableEq, Repr

def huruf : List Harf := [.wa, .fa, .thumma, .hatta, .aw, .am, .la, .bal, .lakin]

/-- العطفُ علاقةٌ بين معطوفٍ عليه ومعطوف، بحرفٍ بينهما (س6441). -/
structure Atf (α : Type) where
  matufAlayh : α
  harf : Harf
  matuf : α

/-- رتبةُ المعطوف من المعطوف عليه في الحكم (س6455، س6458، س6470). -/
inductive Rutba where
  | sabiq | musahib | lahiqMuttasil | lahiqMunfasil
  deriving DecidableEq, Repr

/-- الرتبُ التي يجيزها الحرف؛ وما لا ترتيبَ فيه (أو، أم، لا، بل، لكن) لا رتبةَ له. -/
def rutab : Harf → List Rutba
  | .wa => [.sabiq, .musahib, .lahiqMuttasil, .lahiqMunfasil]
  | .fa => [.lahiqMuttasil]
  | .thumma => [.lahiqMunfasil]
  | .hatta => [.lahiqMuttasil, .lahiqMunfasil]
  | _ => []

/-- الحكمُ بين الطرفين: جمعٌ، أو أحدُهما، أو خلاف (س6446، س6452؛ ج3). -/
inductive Hukm where
  | jam | ahad | khilaf
  deriving DecidableEq, Repr

def hukm : Harf → Hukm
  | .wa | .fa | .thumma | .hatta => .jam
  | .aw | .am => .ahad
  | .la | .bal | .lakin => .khilaf

/-- الإشراك: لفظًا وحكمًا، أو لفظًا فقط (س6446، س6452). -/
inductive Ishrak where
  | lafzWaHukm | lafzFaqat
  deriving DecidableEq, Repr

def ishrak : Harf → Ishrak
  | .la | .bal | .lakin => .lafzFaqat
  | _ => .lafzWaHukm

/-! ## ١–٢. الترتيب -/

/-- **الواو أعمّ**: كلُّ رتبةٍ لحرفٍ رتبةٌ للواو. -/
theorem wa_aamm : ∀ h ∈ huruf, ∀ r ∈ rutab h, r ∈ rutab .wa := by decide

/-- **الواو لا تفيد ترتيبًا**: تجيز السابقَ واللاحقَ والمصاحب، فلا يتعيّن إلّا بقرينة. -/
theorem wa_la_tartib : Rutba.sabiq ∈ rutab .wa ∧ Rutba.musahib ∈ rutab .wa ∧
    Rutba.lahiqMuttasil ∈ rutab .wa ∧ 1 < (rutab .wa).length := by decide

/-- **الفاءُ وثمّ** ترتيبٌ (لا سابقَ ولا مصاحب) ويفترقان بالاتّصال. -/
theorem fa_thumma : rutab .fa = [.lahiqMuttasil] ∧ rutab .thumma = [.lahiqMunfasil] ∧
    rutab .fa ≠ rutab .thumma ∧ Rutba.sabiq ∉ rutab .fa ∧ Rutba.sabiq ∉ rutab .thumma := by decide

/-! ## ٣. البوّابةُ الثنائيّة عمياء -/

/-- جدولُ الصدق على الحكم: أيُّ الطرفين يثبت له الحكم (الأوّل، الثاني). -/
def sidq : Hukm → List (Bool × Bool)
  | .jam => [(true, true)]
  | .ahad => [(true, false), (false, true), (true, true)]
  | .khilaf => [(true, false), (false, true)]

/-- **AND عمياءُ عن الترتيب**: الواو والفاء وثمّ وحتّى جدولُ صدقها واحد، ورتبُها متباينة مثنى مثنى. -/
theorem and_blind :
    sidq (hukm .wa) = sidq (hukm .fa) ∧ sidq (hukm .fa) = sidq (hukm .thumma) ∧
    sidq (hukm .thumma) = sidq (hukm .hatta) ∧
    rutab .wa ≠ rutab .fa ∧ rutab .wa ≠ rutab .thumma ∧ rutab .fa ≠ rutab .thumma ∧
    rutab .hatta ≠ rutab .wa ∧ rutab .hatta ≠ rutab .fa := by decide

/-- لا دالّةَ في جدول الصدق تفصل الواو من الفاء: كلُّ ما يُحسب من `sidq ∘ hukm` واحدٌ عليهما. -/
theorem no_gate_separates (f : List (Bool × Bool) → Bool) :
    f (sidq (hukm .wa)) = f (sidq (hukm .fa)) := rfl

/-! ## ٤. «أو» معانٍ لا بوّابة -/

/-- معاني «أو» (س6504–6509). -/
inductive MaanaAw where
  | takhyir | ibaha | taqsim | ibham | shakk | idrab
  deriving DecidableEq, Repr

/-- ما يجيزه المعنى من ثبوت الحكم للطرفين: التخييرُ يمنع الجمع، والإباحةُ لا تمنعه (س6505). -/
def jawaz : MaanaAw → List (Bool × Bool)
  | .takhyir => [(true, false), (false, true)]
  | .ibaha => [(true, false), (false, true), (true, true)]
  | _ => [(true, false), (false, true), (true, true)]

/-- **«أو» ليست بوّابةً واحدة**: معنيان لها بجدولين مختلفين، فلا دالّةَ بوليّةٌ واحدةٌ تساويهما معًا. -/
theorem aw_not_one_gate :
    jawaz .takhyir ≠ jawaz .ibaha ∧ (true, true) ∉ jawaz .takhyir ∧ (true, true) ∈ jawaz .ibaha := by
  decide

/-! ## ٥. أم -/

/-- قسما أم (س6486، س6499). -/
inductive AmQism where
  | muttasila | munqatia
  deriving DecidableEq, Repr

/-- المتّصلةُ بعد همزة التسوية أو الهمزة المغنية عن أيّ، وإلّا فمنقطعة. -/
def amQism (hamza : Bool) : AmQism := if hamza then .muttasila else .munqatia

/-- المنقطعةُ للإضراب «كبل»، والمتّصلةُ لتعليق الحكم بأحدهما. -/
def amHukm : AmQism → Hukm
  | .muttasila => hukm .am
  | .munqatia => hukm .bal

theorem am_hamza :
    amQism true = .muttasila ∧ amQism false = .munqatia ∧
    amHukm (amQism true) = .ahad ∧ amHukm (amQism false) = hukm .bal := by decide

/-! ## ٦. اختصاصُ الواو -/

/-- ما يجوز مع فعل المشاركة (اختصم، اصطفّ، تشارك): ما يجيز المصاحبةَ ويُشرك حكمًا. -/
def maaMusharaka (h : Harf) : Bool := (rutab h).contains .musahib && hukm h == .jam

theorem ikhtisam_wa : ∀ h ∈ huruf, maaMusharaka h = true ↔ h = .wa := by decide

/-! ## ٧. الإشراك -/

theorem ishrak_count :
    (huruf.filter (ishrak · == .lafzWaHukm)).length = 6 ∧
    (huruf.filter (ishrak · == .lafzFaqat)).length = 3 ∧
    ∀ h ∈ huruf, ishrak h = .lafzFaqat ↔ hukm h = .khilaf := by decide

/-! ## ٨. حرفُ العطف حرف -/

/-- صفاتُ حرف العطف في قسمة ج3: لا يستقلّ بمعناه. -/
def sifat : Sifat := ⟨false, false, false, false⟩

theorem atf_harf : qismOf sifat = .harf ∧ Haja.taalluq ∈ haja sifat := by decide

/-- كلُّ عطفٍ له طرفان والحرفُ بينهما: لا عطفَ بحرفٍ وحدَه. -/
theorem atf_atraf {α : Type} (a : Atf α) : ∃ x y, a = ⟨x, a.harf, y⟩ := ⟨a.matufAlayh, a.matuf, rfl⟩

/-! ## المراسي -/

/-- أسطرُ السند في شرح ابن عقيل المختوم ونصٌّ منها؛ يفحصها `tests/test_atf.py` على الملفّ ببصمته. -/
def marasi : List (Nat × String) :=
  [ (6441, "عطف النسق: هو التابع"),
    (6446, "ما يشرك المعطوف مع المعطوف عليه مطلقا أي لفظا وحكما"),
    (6452, "هذه الثلاثة تشرك الثاني مع الأول في إعرابه لا في حكمه"),
    (6457, "فالواو لمطلق الجمع"),
    (6459, "وإنما يتبين ذلك بالقرينة"),
    (6465, "اختصت الواو من بين حروف العطف"),
    (6470, "أي تدل الفاء على تأخر المعطوف عن المعطوف عليه متصلا به وثم على تأخره"),
    (6483, "يشترط في المعطوف بحتى أن يكون بعضا مما قبله وغاية له"),
    (6486, "ومتصلة وهي التي تقع بعد همزة التسوية"),
    (6499, "أي إذا لم يتقدم على أم همزة التسوية"),
    (6504, "أي تستعمل أو للتخيير"),
    (6505, "والفرق بين الإباحة والتخيير أن الإباحة لا تمنع الجمع") ]

end A116.Atf
