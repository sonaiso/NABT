import A116.Malumat

/-!
# الاستقامةُ من اللفظ (ADR ٨٨، أمرُ المالك 2026-10-17)

السندُ «الكتاب» المختوم (JK006989، الأسطرُ 1-based)، ومراسيه في `marasi`:

* س261–262: «هذا باب الاستقامة من الكلام والإحالة، فمنه مستقيم حسن ومحال ومستقيم كذب ومستقيم قبيح وما هو محال كذب».
* س263–267 الشواهدُ الخمسة:
  * المستقيمُ الحسن «أتيتك أمس وسآتيك غدا».
  * المحالُ «أن تنقض أوّل كلامك بآخره، فتقول أتيتك غدا وسآتيك أمس».
  * المستقيمُ الكذب «حملت الجبل وشربت ماء البحر».
  * المستقيمُ القبيح «أن تضع اللفظ في غير موضعه، نحو قولك قد زيدا رأيت، وكي زيد يأتيك».
  * المحالُ الكذب «سوف أشرب ماء البحر أمس».
* س350: «ذهبت أمس وسأذهب غدا»، شاهدٌ سادسٌ للحسن.
* س1045: «فممّا لا يليه الفعلُ إلّا مظهرًا قد وسوف ولمّا».
* س9757: «قد لا يفصل بينها وبين الفعل بغيره»، وس9760–9761: «سوف… بمنزلة السين التي في قولك سيفعل».

## ما يُبنى

* **الإحالةُ نقضُ أوّل الكلام بآخره داخلَ الجملة الواحدة.** زمنُ الفعل (الماضي قبل «الآن»، وذو السين أو سوف بعده)
  يناقض الظرفَ في جملته (أمسِ قبل «الآن»، وغدًا بعده). والنسبةُ إلى «الآن» هي `Malumat.nisba`، فنقلُ «الآن» لا يغيّر
  الحكم (`muhal_shift`). والعطفُ يفصل الجمل، فشاهدُ الحسن ليس محالًا.
* **القبحُ وضعُ اللفظ في غير موضعه.** حرفٌ لا يليه إلّا الفعل وليه غيرُه.
* **الكذبُ ليس من اللفظ.** الاستقامةُ عمياءُ عنه (`istiqama_amya`)، والأقسامُ الخمسة حاصلُ الاستقامة والكذب
  (`sinf`)، والكذبُ لا يغيّر الإحالة (`kadhib_la_yughayyir`).

أوصافُ الكلمات (فعلٌ بزمنه، ظرف، حرفٌ، اسم، عطف) مُدخَلٌ منقول، لا مستخرجٌ من الخانات (`ISTIQAMA_FEATURES_ARE_INPUT`).
فشواهدُ الكتاب غيرُ مشكولة ولا تمرّ بالبوّابة (`KITAB_EXAMPLES_UNVOCALIZED`).
-/

namespace A116.Istiqama

open A116.Malumat

/-- زمنُ الفعل بهيئته: الماضي، والمضارع، وذو السين المتّصلة. -/
inductive Zaman | madi | mudari | mustaqbal
  deriving DecidableEq, Repr

/-- الظرفُ الزمانيّ: أمسِ وغدًا (ج3 س373: اسمٌ يدلّ على الزمان بذاته). -/
inductive Waqt | ams | ghad
  deriving DecidableEq, Repr

/-- الكلمةُ بوصفها. `harfFil n istiqbal`: حرفٌ لا يليه إلّا الفعل، و`istiqbal` إن كان كسوف يجعل المضارعَ مستقبلًا. -/
inductive Juz
  | fil (z : Zaman)
  | zarf (w : Waqt)
  | harfFil (ism : String) (istiqbal : Bool)
  | ism
  | atf
  deriving DecidableEq, Repr

/-- الكلامُ: الكلماتُ برسمها في الكتاب ووصفها. -/
abbrev Kalam := List (String × Juz)

/-- الجملُ: يفصلها العطف. -/
def jumal : List Juz → List (List Juz)
  | [] => [[]]
  | .atf :: t => [] :: jumal t
  | j :: t => match jumal t with
    | [] => [[j]]
    | c :: cs => (j :: c) :: cs

/-- مواضعُ أزمنة الأفعال من «الآن»: قبلُ (−1) أو بعدُ (1)، والمضارعُ وحدَه بلا موضع. -/
def awqatFil : List Juz → List Int
  | .harfFil _ true :: .fil .mudari :: t => 1 :: awqatFil t
  | .fil .madi :: t => -1 :: awqatFil t
  | .fil .mustaqbal :: t => 1 :: awqatFil t
  | _ :: t => awqatFil t
  | [] => []

/-- مواضعُ الظروف من «الآن». -/
def awqatZarf : List Juz → List Int
  | .zarf .ams :: t => -1 :: awqatZarf t
  | .zarf .ghad :: t => 1 :: awqatZarf t
  | _ :: t => awqatZarf t
  | [] => []

/-- «الآن» عند مقدار `n`. -/
def alAn (n : Int) : Mawqi := ⟨.alAn, n⟩

/-- الجملةُ محالٌ إن خالفت نسبةُ فعلٍ فيها إلى «الآن» نسبةَ ظرفٍ فيها إليه، و«الآن» عند `n`. -/
def muhalAt (n : Int) (c : List Juz) : Bool :=
  (awqatFil c).any (fun a => (awqatZarf c).any (fun b =>
    nisba (alAn (a + n)) (alAn n) != nisba (alAn (b + n)) (alAn n)))

/-- الكلامُ محالٌ إن كانت جملةٌ منه محالًا. -/
def muhalB (k : List Juz) : Bool := (jumal k).any (muhalAt 0)

/-- القبحُ: حرفٌ لا يليه إلّا الفعل وليه غيرُه. -/
def qabihB : List Juz → Bool
  | .harfFil _ _ :: t =>
      (match t with
       | .fil _ :: _ => false
       | _ => true) || qabihB t
  | _ :: t => qabihB t
  | [] => false

/-- حكمُ اللفظ: مستقيمٌ أو محال، وحسنٌ أو قبيح. لا معاملَ فيه للكذب. -/
structure Hukm where
  mustaqim : Bool
  hasan : Bool
  deriving DecidableEq, Repr

def istiqama (k : List Juz) : Hukm := ⟨!muhalB k, !qabihB k⟩

/-- أقسامُ سيبويه الخمسة. -/
inductive Sinf | mustaqimHasan | muhal | mustaqimKadhib | mustaqimQabih | muhalKadhib
  deriving DecidableEq, Repr

/-- القسمُ حاصلُ الاستقامة من اللفظ والكذب من خارجه. -/
def sinf (k : List Juz) (kadhib : Bool) : Sinf :=
  if muhalB k then (if kadhib then .muhalKadhib else .muhal)
  else if qabihB k then .mustaqimQabih
  else if kadhib then .mustaqimKadhib else .mustaqimHasan

def juz (k : Kalam) : List Juz := k.map (·.2)

/-! ## الشواهد برسمها في الكتاب -/

def hasan : Kalam :=
  [("أتيتك", .fil .madi), ("أمس", .zarf .ams), ("و", .atf), ("سآتيك", .fil .mustaqbal), ("غدا", .zarf .ghad)]
def muhal : Kalam :=
  [("أتيتك", .fil .madi), ("غدا", .zarf .ghad), ("و", .atf), ("سآتيك", .fil .mustaqbal), ("أمس", .zarf .ams)]
def kadhib : Kalam :=
  [("حملت", .fil .madi), ("الجبل", .ism), ("و", .atf), ("شربت", .fil .madi), ("ماء", .ism), ("البحر", .ism)]
def qabih1 : Kalam := [("قد", .harfFil "قد" false), ("زيدا", .ism), ("رأيت", .fil .madi)]
def qabih2 : Kalam := [("كي", .harfFil "كي" false), ("زيد", .ism), ("يأتيك", .fil .mudari)]
def muhalKadhib : Kalam :=
  [("سوف", .harfFil "سوف" true), ("أشرب", .fil .mudari), ("ماء", .ism), ("البحر", .ism), ("أمس", .zarf .ams)]
def hasan2 : Kalam :=
  [("ذهبت", .fil .madi), ("أمس", .zarf .ams), ("و", .atf), ("سأذهب", .fil .mustaqbal), ("غدا", .zarf .ghad)]

/-- الشواهدُ بأسطرها: (السطر، الكلام، كذبُه عند سيبويه، قسمُه عنده). -/
def shawahid : List (Nat × Kalam × Bool × Sinf) :=
  [(263, hasan, false, .mustaqimHasan), (264, muhal, false, .muhal), (265, kadhib, true, .mustaqimKadhib),
   (266, qabih1, false, .mustaqimQabih), (266, qabih2, false, .mustaqimQabih),
   (267, muhalKadhib, true, .muhalKadhib), (350, hasan2, false, .mustaqimHasan)]

/-- المراسي: (السطر، النصّ بعينه). -/
def marasi : List (Nat × String) :=
  [(261, "هذا باب الاستقامة من الكلام والإحالة"),
   (262, "فمنه مستقيم حسن ومحال ومستقيم كذب ومستقيم قبيح وما هو محال كذب"),
   (263, "فأما المستقيم الحسن فقولك أتيتك أمس وسآتيك غدا"),
   (263, "وأما محال فأن تنقض أول"),
   (264, "كلامك بآخره فتقول أتيتك غدا وسآتيك أمس"),
   (265, "فقولك حملت الجبل وشربت ماء البحر"),
   (266, "اللفظ في غير موضعه نحو قولك قد زيدا رأيت وكي زيد يأتيك"),
   (267, "المحال الكذب فأن تقول سوف أشرب ماء البحر أمس"),
   (350, "وتقول ذهبت أمس وسأذهب غدا"),
   (1045, "فمما لا يليه الفعل إلا مظهرا قد وسوف ولما"),
   (9757, "فمن تلك الحروف قد لا يفصل بينها وبين الفعل بغيره"),
   (9760, "ومن تلك الحروف أيضا سوف يفعل لأنها بمنزلة السين التي")]

/-- كلُّ شاهدٍ قسمُه بالقانون هو قسمُه عند سيبويه. -/
theorem shawahid_sinf : shawahid.all (fun (_, k, b, s) => sinf (juz k) b == s) = true := by decide

/-- المستقيمُ الكذب موجود: الاستقامةُ عمياءُ عن الكذب. -/
theorem istiqama_amya :
    istiqama (juz kadhib) = ⟨true, true⟩ ∧ sinf (juz kadhib) true = .mustaqimKadhib ∧
    sinf (juz kadhib) false = .mustaqimHasan := by decide

/-- الكذبُ لا يغيّر الإحالة: المحالُ محالٌ صادقًا أو كاذبًا. -/
theorem kadhib_la_yughayyir (k : List Juz) (b : Bool) :
    (sinf k b = .muhal ∨ sinf k b = .muhalKadhib) ↔ muhalB k = true := by
  unfold sinf
  cases muhalB k <;> cases qabihB k <;> cases b <;> simp

/-- والكذبُ لا يغيّر القبح. -/
theorem kadhib_la_yughayyir_qubh (k : List Juz) (b : Bool) (h : muhalB k = false) :
    sinf k b = .mustaqimQabih ↔ qabihB k = true := by
  unfold sinf
  rw [h]; cases qabihB k <;> cases b <;> simp

/-- «الآن» مرساةٌ لا إحداثيّ: نقلُها لا يغيّر الحكم. -/
theorem muhal_shift (n : Int) (c : List Juz) : muhalAt n c = muhalAt 0 c := by
  have h : ∀ a : Int, nisba (alAn (a + n)) (alAn n) = nisba (alAn (a + 0)) (alAn 0) := by
    intro a
    have e := nisba_shift .alAn a 0 n
    simp only [Int.zero_add] at e
    simp only [alAn, Int.add_zero]
    exact e
  simp only [muhalAt, h]

/-- النقضُ بلا فصل: الكلامُ كلُّه جملةٌ واحدة. -/
def muhalKull (k : List Juz) : Bool := muhalAt 0 k

/-- العطفُ يفصل الجمل: شاهدُ الحسن بلا فصلٍ محال، وبالفصل حسن. فالنقضُ داخلَ الجملة. -/
theorem atf_yafsil : muhalKull (juz hasan) = true ∧ muhalB (juz hasan) = false := by decide

/-- «قد» لا يليها إلّا الفعل: يليها اسمٌ فالكلامُ قبيح، أيًّا كان ما بعده. -/
theorem qad_ism_qabih (t : List Juz) : qabihB (.harfFil "قد" false :: .ism :: t) = true := by
  simp [qabihB]

/-- وتليها فعلٌ فلا قبحَ منها. -/
theorem qad_fil (z : Zaman) : qabihB [.harfFil "قد" false, .fil z] = false := by
  cases z <;> rfl

/-- سوف تجعل المضارعَ بعد «الآن»، فمع «أمس» محال. -/
theorem sawfa_ams : muhalB [.harfFil "سوف" true, .fil .mudari, .zarf .ams] = true := by decide

/-- والمضارعُ وحدَه بلا موضعٍ من «الآن»: لا يُحكم بإحالته مع ظرف. -/
theorem mudari_la_muhal (w : Waqt) : muhalB [.fil .mudari, .zarf w] = false := by
  cases w <;> decide

/-- الأقسامُ الخمسة كلُّها واقعةٌ في الشواهد. -/
theorem khamsa_waqia :
    [Sinf.mustaqimHasan, .muhal, .mustaqimKadhib, .mustaqimQabih, .muhalKadhib].all
      (fun s => shawahid.any (fun (_, _, _, s') => s' == s)) = true := by decide

end A116.Istiqama
