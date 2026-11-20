/-
# «هذا باب الجزاء» عند سيبويه (الكتاب، س9190–9304)

**المصدر.** `sibawayhi.txt` المختوم (`a160f940…`)، الأسطر 9190–9304: من العنوان «هذا باب الجزاء» إلى ما قبل «هذا باب
الأسماء التي يجازي بها وتكون بمنزلة الذي». ورقمُ السطر خاصٌّ بهذا الملفّ. والاقتباسات في `asanid` أدناه قطعٌ حرفيّة، يفحصها
`tahaqquq/test_jaza.py` على المودَع: على النصّ موصولَ الأسطر بحذف البادئة وعلامات الصفحات والمخطوط وتوحيد البياض، و16 منها تعبر
سطرين.

**المدخل.** `Jumla`: الأداةُ بلفظ الكتاب بلا تشكيل، والترتيبُ، ولامُ القسم قبل الأداة، وصورةُ فعل الشرط، وصورةُ الجواب
كما كُتبا. وهي حقولُ مواصفة الضابط المجمَّد (`tahaqquq/dawabit/jaza/wasf.md`) بأعيانها. **والمدخلُ تحليلٌ للتركيب يُعطى،
لا مُخرَجُ قارئٍ من النصّ** (P4 لم يُبنَ).

**المخرج.** `Hukm`: درجةُ التركيب في الكلام وفي الشعر، كلٌّ من أربع: `maqbul`، `qabih`، `khata`، `laHukm`. والدرجاتُ الثلاث
الأولى من ألفاظ الباب بمفتاح المواصفة (تقول/جاز/حسن ← مقبول؛ قبيح/لا يحسن/مستكرهة ← قبيح؛ لا يكون/لم يجز/خطأ ← خطأ).
و`laHukm` ما لا يحكم فيه الباب. **فالغيابُ هنا ليس امتناعًا**: ما لم يذكره الباب لا يُردّ.

**ما هو تعيينُ البنّاء** (لا نصُّ الباب):
- **العموم.** أحكامُ الجواب مضروبةٌ في الباب بأمثلةٍ على «إن» في الغالب. وعمّمتُها على كلّ أداةٍ في `adawatJaza`، بعبارة الباب
  العامّة: «واعلم أن حروف الجزاء تجزم الأفعال» (س9242–9243)، و«لا يكون جواب الجزاء إلا بفعل أو بالفاء» (س9248)، و«أن تعمل إن
  أو شىء من حروف الجزاء» (س9274).
- **الفاءُ والفعلُ في «إلا بفعل أو بالفاء» (س9248) بمعيارين.**
  - أمثلةُ «الجواب بالفعل» مضارعةٌ (س9248–9249).
  - وللفاء في الجزاء ثلاثُ صور: اسميّةٌ («إن تأتني فأنا صاحبك»، س9250)، وأمرٌ («إذ ما أتيت على الرسول فقل له»، س9196)،
    ومضارعٌ مرفوع (س9301–9304).
  - فقبلتُ الفاءَ وبعدها غيرُ الاسميّة والمضارع (`faGhayr`) بعموم «أو بالفاء»، وأقربُ شاهدٍ له س9196.
  - وجعلتُ الماضي جوابًا بلا رابط (`Jawab.madi`) «لا حكم»، ولا مثالَ منطوقًا له في الباب لأداةٍ يُجازى بها. **لكنّ الباب يضعه موضعَ
    الجواب** في تفسير الخليل لـ«إذا هم يقنطون»: «وهذا هاهنا في موضع قنطوا» (س9255)، وأعاده الباب: «كما كان هذا بمنزلة قنطوا» (س9293). وفي
    الشعر جوابًا لـ«إذا» («إذا قصرت أسيافنا كان وصلها»، س9236). فـ«لا حكم» اختياري مع هذا الشاهد، ومرشَّحٌ لـ«مقبول» في إصدارٍ تالٍ.
  - والتفريقُ اختياري، والعبارةُ واحدة.
- **الشرطُ الماضي** يأخذ أحكامَ الجواب التي ضُربت على المجزوم، وسندُ التسوية «لأن هذا في موضع الفعل المجزوم» (س9295). إلّا في
  موضعين: الرفعُ بعده مقبول («وقد تقول إن أتيتني آتيك»، س9281)، واللامُ بعده مقبولةٌ وبعد المجزوم قبيحة (س9269–9273).
- **الجوابُ المقدَّم بعد شرطٍ ماضٍ** مقبول («ألا ترى أنك تقول آتيك إن أتيتني»، س9275–9276). **وفي الباب حكمٌ ثانٍ على الحقول نفسها:**
  «ولو قلت آتيك إن احمر البسر كان قبيحا فإن أبدا مبهمة وكذلك حروف الجزاء» (س9227–9228). والفارقُ معنى الشرط (مبهمٌ أو وقتٌ
  معلوم)، ولا تحمله الحقول. فاخترتُ حكمَ س9275–9276، وتركتُ الآخر.
- **«كيف»** قبيحةٌ في الكلام بكلّ صورها، تعميمًا لمثالٍ واحد («كيف تصنع أصنع»، س9223).
- **«إذا ما»** صنفُ «إذا»، بمثال كعب («وإذا ما تشاء تبعث منها»، س9242).
- **ألفاظٌ ليست في مفتاح المواصفة:**
  - «فصارت إذا هاهنا جوابا» (س9260) والاحتجاجُ بالآية (س9253–9254) ← مقبول.
  - «ولا تقول آتيك إن تأتني إلا في شعر» (س9276) ← قبيحٌ في الكلام، بـ«وقبح في الكلام» قبلها (س9274)، ومقبولٌ في الشعر.
- **الشعر.** ما قُبل في الكلام قُبل في الشعر (`maqbul_kalam_maqbul_shir`). وما لم يذكر الباب الشعرَ فيه، وهو غيرُ مقبولٍ في
  الكلام، فحكمُه في الشعر `laHukm`.
- **أسماءُ الأدوات وصورُ كتابتها.** «إذ ما» (س9192) و«إذما» (س9195)، و«أياما» (س9221)، وصورتُه المفصولة «أيا ما» تعيين، و«إن ما» (س9219) و«إما» (س9209). و«أي» بقوله «وبمنزلتها مع أي» (س9220).
- **«حيث تكون أكون»** مقبولةٌ بالرفع صلةً لا جزاءً (س9204). ولا حكمَ لغير هذه الصورة في «حيث» و«إذ» ما لم تُجزم.

**المنهج.** جُمّدت هذه الشفرة في `b442a34` قبل أن يقرأ البنّاءُ حالاتِ الضابط. كتبها مؤلّفٌ مستقلٌّ إجرائيًّا من الباب، وفي سياقه ما حُقن آليًّا وتوجيهُ البنّاء (`mulhaq_1.md`)، وجُمّدت
ببصمتها في `tahaqquq/dawabit/jaza/tajmid.json` قبل الشفرة (المنهج: `hawkama/منهج_الضوابط.md`، في طلبه). ونتيجتُها على الضابط في
`Jisr/BabJazaQiyas.lean`، لا هنا. **وبعد قراءة الحالات** أُكمل الرأسُ وتعليقاتُ المبرهنات وتوثيقُ `suraQatr`، وصُحّح مدى سندٍ في `asanid`
(س9268–9269 ← س9269)، بمراجعة `murajii` في أربع جولات، بلا تغييرٍ في الأحكام. فالتشغيلاتُ الثاني إلى الخامس (`natija_2.json` …
`natija_5.json`) على مادّةٍ مكشوفة.
-/
import Jisr.KhulasaIkhbar
import Jisr.QaydMafhum

namespace Jisr
namespace BabJaza

/-! ## المدخل والمخرج -/

inductive Tartib
  | shartAwwalan | jawabAwwalan
  deriving DecidableEq, Repr

/-- صورةُ فعل الشرط كما كُتب. -/
inductive Shart
  | mudariMajzum | mudariMarfu | madi
  deriving DecidableEq, Repr

/-- صورةُ الجواب كما كُتب. -/
inductive Jawab
  | mudariMajzum | mudariMarfu | madi
  | faIsmiyya | faMudariMarfu | faMudariMajzum | faGhayr
  | idhaIsmiyya | faIdha | ismiyya | waw | thumma | lamQasam
  deriving DecidableEq, Repr

structure Jumla where
  adat : String
  tartib : Tartib
  lamQasam : Bool
  shart : Shart
  jawab : Jawab
  deriving DecidableEq, Repr

inductive Daraja
  | maqbul | qabih | khata | laHukm
  deriving DecidableEq, Repr

structure Hukm where
  kalam : Daraja
  shir : Daraja
  deriving DecidableEq, Repr

/-! ## الأدوات -/

/-- ما يُجازى به: «فما يجازي به من الأسماء غير الظروف من وما وأيهم وما يجازي به من الظروف أي حين ومتى وأين وأنى وحيثما
    ومن غيرهما إن وإذ ما» (س9191–9192)؛ و«مهما» (س9217)، و«متى ما» و«إن ما» و«أينما» و«أياما» بـ«ما» لغوًا (س9218–9221).
    وصورُ الكتابة تعيين (الرأس). -/
def adawatJaza : List String :=
  ["من", "ما", "أيهم", "أي", "أي حين", "متى", "أين", "أنى", "حيثما", "إن", "إذ ما", "إذما",
   "مهما", "متى ما", "إن ما", "إما", "أينما", "أيا ما", "أياما"]

inductive Sinf
  /-- يُجازى به. -/
  | jaza
  /-- «حيث» و«إذ»: «ولا يكون الجزاء في حيث ولا في إذ حتى يضم إلى كل واحد منهما ما» (س9192–9193). -/
  | haythuIdh
  /-- «كيف»: «هي مستكرهة وليست من حروف الجزاء» (س9223–9224). -/
  | kayfa
  /-- «إذا»: «ما منعهم أن يجازوا بها» (س9225)، «وقد جازوا بها في الشعر مضطرين» (س9233–9234). -/
  | idha
  /-- ما سوى ذلك: الباب لا يحكم فيه. -/
  | ghayr
  deriving DecidableEq, Repr

def sinfOf (a : String) : Sinf :=
  if adawatJaza.contains a then .jaza
  else if a == "حيث" || a == "إذ" then .haythuIdh
  else if a == "كيف" then .kayfa
  else if a == "إذا" || a == "إذا ما" then .idha
  else .ghayr

/-! ## الحكم -/

def laHukm : Hukm := ⟨.laHukm, .laHukm⟩
def maqbul : Hukm := ⟨.maqbul, .maqbul⟩

/-- «حيث» و«إذ». -/
def hukmHaythuIdh (j : Jumla) : Hukm :=
  if j.shart = .mudariMajzum then ⟨.khata, .laHukm⟩
  -- «أنك تقول حيث تكون أكون فتكون وصل لها» (س9204)
  else if j.adat = "حيث" ∧ j.tartib = .shartAwwalan ∧ !j.lamQasam ∧ j.shart = .mudariMarfu ∧
      j.jawab = .mudariMarfu then maqbul
  else laHukm

/-- «إذا». -/
def hukmIdha (j : Jumla) : Hukm :=
  if j.lamQasam then laHukm
  -- «وقد جازوا بها في الشعر مضطرين» (س9233–9234)؛ «فهذا اضطرار وهو في الكلام خطأ» (س9240–9241)
  else if j.shart = .mudariMajzum ∨ j.jawab = .mudariMajzum then ⟨.khata, .maqbul⟩
  -- «ولكن الجيد قول كعب» … «وإذا ما تشاء تبعث منها» (س9241–9242)
  else if j.tartib = .shartAwwalan ∧ j.shart = .mudariMarfu ∧ j.jawab = .mudariMarfu then maqbul
  -- «لو قلت أتيك إذا احمر البسر كان حسنا» (س9227)
  else if j.tartib = .jawabAwwalan ∧ j.shart = .madi ∧ j.jawab = .mudariMarfu then maqbul
  else laHukm

/-- جوابٌ مقدَّم: «ألا ترى أنك تقول آتيك إن أتيتني ولا تقول آتيك إن تأتني إلا في شعر» (س9275–9276)، وقبله «وقبح في الكلام
    أن تعمل إن أو شىء من حروف الجزاء في الأفعال حتى تجزمه في اللفظ ثم لا يكون لها جواب بنجزم بما قبله» (س9274–9275). -/
def hukmMuqaddam (j : Jumla) : Hukm :=
  if j.lamQasam || j.jawab != .mudariMarfu then laHukm
  else match j.shart with
    | .madi => maqbul
    | .mudariMajzum => ⟨.qabih, .maqbul⟩
    | .mudariMarfu => laHukm

/-- لامُ القسم في الجواب، بلامٍ قبل الأداة («لئن») أو بلا لام. -/
def hukmLam (s : Shart) : Hukm :=
  match s with
  -- «فلو قلت إن أتيتني لأكرمنك … جاز لأنه في معنى لئن أتيتني لأكرمنك» (س9270–9271)
  | .madi => maqbul
  -- بلا لام: «أنه لا يحسن في الكلام إن تأتني لأفعلن» (س9269)؛ وباللام: «فإن قلت لئن تفعل لأفعلن قبح» (س9273)
  | .mudariMajzum => ⟨.qabih, .laHukm⟩
  | .mudariMarfu => laHukm

/-- الجوابُ بعد شرطٍ مجزومٍ أو ماضٍ، والشرطُ أوّلًا بلا لام. -/
def hukmJawab (s : Shart) : Jawab → Hukm
  -- «إن تأتني آتك» (س9244، س9249)؛ «وقد يقال إن أتيتني آتك» (س9294–9295)
  | .mudariMajzum => maqbul
  -- «وقد تقول إن أتيتني آتيك» (س9281)؛ «ولا يحسن إن تأتني آتيك» … «وقد جاء في الشعر» (س9283)
  | .mudariMarfu => if s = .madi then maqbul else ⟨.qabih, .maqbul⟩
  -- لا مثالَ منطوقًا له في الباب، وهو في موضع الجواب في س9255 (تعيين؛ الرأس)
  | .madi => laHukm
  -- «وأما الجواب بالفاء فقولك إن تأتني فأنا صاحبك» (س9249–9250)
  | .faIsmiyya => maqbul
  -- «إن تأتني فأكرمك أي فأنا أكرمك فلا بد من رفع فأكرمك» (س9300–9301)
  | .faMudariMarfu => maqbul
  | .faMudariMajzum => ⟨.khata, .laHukm⟩
  -- «لا يكون جواب الجزاء إلا بفعل أو بالفاء» (س9248)؛ عمومٌ (تعيين)
  | .faGhayr => maqbul
  -- «وإن تصبهم سيئة بما قدمت أيديهم إذا هم يقنطون» (س9253–9254)، «فصارت إذا هاهنا جوابا» (س9260)
  | .idhaIsmiyya => maqbul
  -- «وزعم الخليل أن إدخال الفاء على إذا قبيح» (س9258–9259)
  | .faIdha => ⟨.qabih, .laHukm⟩
  -- «إن تأتني أنا كريم فقال لا يكون هذا إلا أن يضطر شاعر» (س9261–9262)
  | .ismiyya => ⟨.khata, .maqbul⟩
  -- «ولو أدخلت الواو وثم في هذا الموضع تريد الجواب لم يجز» (س9252–9253)
  | .waw => ⟨.khata, .laHukm⟩
  | .thumma => ⟨.khata, .laHukm⟩
  | .lamQasam => hukmLam s

/-- ما يُجازى به. -/
def hukmJaza (j : Jumla) : Hukm :=
  match j.tartib with
  | .jawabAwwalan => hukmMuqaddam j
  | .shartAwwalan =>
    if j.shart = .mudariMarfu then laHukm
    else if j.lamQasam then
      (if j.jawab = .lamQasam then hukmLam j.shart else laHukm)
    else hukmJawab j.shart j.jawab

def hukm (j : Jumla) : Hukm :=
  match sinfOf j.adat with
  | .jaza => hukmJaza j
  | .haythuIdh => hukmHaythuIdh j
  | .kayfa => ⟨.qabih, .laHukm⟩
  | .idha => hukmIdha j
  | .ghayr => laHukm

/-! ## الأسانيد

قطعٌ حرفيّةٌ من الكتاب بأسطرها (من، إلى)، على النصّ موصولَ الأسطر بحذف البادئة وعلامات الصفحات والمخطوط. يفحصها
`tahaqquq/test_jaza.py` على المودَع. -/

def asanid : List (String × Nat × Nat × String) := [
  ("adawatJaza", 9191, 9192, "فما يجازي به من الأسماء غير الظروف من وما وأيهم وما يجازي به من الظروف أي حين ومتى وأين وأنى وحيثما ومن غيرهما إن وإذ ما"),
  ("adawatJaza", 9195, 9195, "فمما كان من الجزاء بإذما"),
  ("adawatJaza", 9209, 9209, "وصارت بمنزلة إما"),
  ("adawatJaza", 9217, 9217, "وسألت الخليل عن مهما"),
  ("adawatJaza", 9218, 9218, "متى ما تأتني آتك"),
  ("adawatJaza", 9219, 9219, "إن ما تأتني آتك"),
  ("adawatJaza", 9220, 9220, "وبمنزلتها مع أي إذا قلت"),
  ("adawatJaza", 9220, 9220, "أينما تكونوا"),
  ("adawatJaza", 9221, 9221, "أياما تدعوا"),
  ("haythuIdh", 9192, 9193, "ولا يكون الجزاء في حيث ولا في إذ حتى يضم إلى كل واحد منهما ما"),
  ("haythuIdh", 9204, 9204, "أنك تقول حيث تكون أكون فتكون وصل لها"),
  ("kayfa", 9223, 9224, "هي مستكرهة وليست من حروف الجزاء"),
  ("idha", 9225, 9225, "ما منعهم أن يجازوا بها"),
  ("idha", 9227, 9227, "لو قلت أتيك إذا احمر البسر كان حسنا"),
  ("idha", 9233, 9234, "وقد جازوا بها في الشعر مضطرين"),
  ("idha", 9240, 9241, "فهذا اضطرار وهو في الكلام خطأ"),
  ("idha", 9241, 9241, "ولكن الجيد قول كعب اين زهير"),
  ("idha", 9242, 9242, "وإذا ما تشاء تبعث منها"),
  ("umum", 9242, 9243, "واعلم أن حروف الجزاء تجزم الأفعال"),
  ("umum", 9248, 9248, "لا يكون جواب الجزاء إلا بفعل أو بالفاء"),
  ("umum", 9274, 9275, "وقبح في الكلام أن تعمل إن أو شىء من حروف الجزاء في الأفعال حتى تجزمه في اللفظ ثم لا يكون لها جواب بنجزم بما قبله"),
  ("mudariMajzum", 9244, 9244, "إذا قلت إن تأتني آتك"),
  ("mudariMajzum", 9294, 9295, "وقد يقال إن أتيتني آتك"),
  ("mudariMarfu", 9275, 9276, "ألا ترى أنك تقول آتيك إن أتيتني ولا تقول آتيك إن تأتني إلا في شعر"),
  ("mudariMarfu", 9281, 9281, "وقد تقول إن أتيتني آتيك"),
  ("mudariMarfu", 9283, 9283, "ولا يحسن إن تأتني آتيك من قبل أن إن هي العاملة وقد جاء في الشعر"),
  ("faIsmiyya", 9249, 9250, "وأما الجواب بالفاء فقولك إن تأتني فأنا صاحبك"),
  ("faMudariMarfu", 9300, 9301, "إن تأتني فأكرمك أي فأنا أكرمك فلا بد من رفع فأكرمك"),
  ("waw", 9250, 9250, "ولا يكون الجواب في هذا الموضع بالواو ولا بثم"),
  ("waw", 9252, 9253, "ولو أدخلت الواو وثم في هذا الموضع تريد الجواب لم يجز"),
  ("idhaIsmiyya", 9253, 9254, "وإن تصبهم سيئة بما قدمت أيديهم إذا هم يقنطون"),
  ("idhaIsmiyya", 9260, 9260, "فصارت إذا هاهنا جوابا"),
  ("faIdha", 9258, 9259, "وزعم الخليل أن إدخال الفاء على إذا قبيح"),
  ("ismiyya", 9261, 9262, "إن تأتني أنا كريم فقال لا يكون هذا إلا أن يضطر شاعر"),
  ("lamQasam", 9269, 9269, "أنه لا يحسن في الكلام إن تأتني لأفعلن"),
  ("lamQasam", 9270, 9271, "إن أتيتني لأكرمنك وإن لم تأتني لأغمنك جاز لأنه في معنى لئن أتيتني لأكرمنك"),
  ("lamQasam", 9273, 9273, "فإن قلت لئن تفعل لأفعلن قبح")]

/-! ## المبرهنات على كلّ `Jumla` (تعريفيّة)

عشرٌ، كلُّها «تعريفيّة» بمعيار `Nizam/Asas.lean`: برهانُها فكُّ التعريفات وتفكيكُ الحالات، فهي تعيد قولَ التعيين أعلاه
بصيغةٍ كلّيّة، ولا تشهد له بشيءٍ من خارجه. والشاهدُ من خارجه نتيجةُ الضابط المجمَّد (`Jisr/BabJazaQiyas.lean`). -/

/-- **ما قُبل في الكلام قُبل في الشعر.** خاصّيّةُ التعيين، لا نصُّ الباب. -/
theorem maqbul_kalam_maqbul_shir (j : Jumla) :
    (hukm j).kalam = .maqbul → (hukm j).shir = .maqbul := by
  obtain ⟨a, t, l, s, w⟩ := j
  unfold hukm
  cases sinfOf a <;>
    simp only [hukmJaza, hukmMuqaddam, hukmLam, hukmJawab, hukmHaythuIdh, hukmIdha, maqbul, laHukm] <;>
    cases t <;> cases l <;> cases s <;> cases w <;> (try simp) <;> (try (by_cases h : a = "حيث" <;> simp [h]))

/-- **ما لا يعرفه الباب من الأدوات لا حكمَ فيه**، لا ردّ. -/
theorem ghayr_la_hukm (j : Jumla) (h : sinfOf j.adat = .ghayr) : hukm j = laHukm := by
  simp [hukm, h]

/-- **جوابُ الجزاء المقبول في الكلام** (والشرطُ أوّلًا بلا لام) واحدٌ من سبع صور. وهي تخالف «لا يكون جواب الجزاء إلا بفعل
    أو بالفاء» (س9248). تُخرج الماضي وهو فعل، بتعيين الرأس. وتُخرج صورتين بالفاء: المضارعَ المجزوم بعدها (خطأ، «فلا بد من رفع
    فأكرمك»، س9301) والفاءَ على «إذا» (قبيح، س9258–9259). وتُدخل «إذا» (س9260) واللامَ في معنى القسم (س9270–9271). فهي خاصّيّةُ
    التعيين لا قولُ الباب. -/
theorem jawab_bifil_aw_bilfa (j : Jumla) (hs : sinfOf j.adat = .jaza) (ht : j.tartib = .shartAwwalan)
    (hl : j.lamQasam = false) (hm : (hukm j).kalam = .maqbul) :
    j.jawab ∈ [.mudariMajzum, .mudariMarfu, .faIsmiyya, .faMudariMarfu, .faGhayr, .idhaIsmiyya, .lamQasam] := by
  obtain ⟨a, t, l, s, w⟩ := j
  simp only at hs ht hl
  subst ht hl
  simp only [hukm, hs, hukmJaza, hukmJawab, hukmLam, maqbul, laHukm] at hm
  cases s <;> cases w <;> simp_all

/-- **الواوُ وثمّ لا يكونان جوابًا** (س9252–9253) لأداةٍ يُجازى بها، والشرطُ مجزومٌ أو ماضٍ أوّلًا بلا لام. -/
theorem waw_thumma_khata (j : Jumla) (hs : sinfOf j.adat = .jaza) (ht : j.tartib = .shartAwwalan)
    (hl : j.lamQasam = false) (hsh : j.shart ≠ .mudariMarfu) (hw : j.jawab = .waw ∨ j.jawab = .thumma) :
    (hukm j).kalam = .khata := by
  obtain ⟨a, t, l, s, w⟩ := j
  simp only at hs ht hl hsh hw
  subst ht hl
  rcases hw with rfl | rfl <;> cases s <;> simp_all [hukm, hukmJaza, hukmJawab]

/-- **«فلا بد من رفع فأكرمك»** (س9301): المضارعُ المجزوم بعد الفاء لا يقبله الكلام مع أيّ أداة. -/
theorem fa_majzum_la_yuqbal (j : Jumla) (hw : j.jawab = .faMudariMajzum) : (hukm j).kalam ≠ .maqbul := by
  obtain ⟨a, t, l, s, w⟩ := j
  simp only at hw
  subst hw
  unfold hukm
  cases sinfOf a <;>
    simp only [hukmJaza, hukmMuqaddam, hukmLam, hukmJawab, hukmHaythuIdh, hukmIdha, maqbul, laHukm] <;>
    cases t <;> cases l <;> cases s <;> (try simp) <;> (try (by_cases h : a = "حيث" <;> simp [h]))

/-- **الاسميّةُ بلا فاءٍ ولا «إذا»** (س9261–9262): خطأٌ في الكلام، مقبولةٌ في الشعر. -/
theorem ismiyya_bila_rabit (j : Jumla) (hs : sinfOf j.adat = .jaza) (ht : j.tartib = .shartAwwalan)
    (hl : j.lamQasam = false) (hsh : j.shart ≠ .mudariMarfu) (hw : j.jawab = .ismiyya) :
    hukm j = ⟨.khata, .maqbul⟩ := by
  obtain ⟨a, t, l, s, w⟩ := j
  simp only at hs ht hl hsh hw
  subst ht hl hw
  cases s <;> simp_all [hukm, hukmJaza, hukmJawab]

/-- **الرفعُ بعد شرطٍ مجزوم قبيحٌ في الكلام، مقبولٌ في الشعر، في الترتيبين** (س9274–9276، س9283). -/
theorem raf_baad_jazm (j : Jumla) (hs : sinfOf j.adat = .jaza) (hl : j.lamQasam = false)
    (hsh : j.shart = .mudariMajzum) (hw : j.jawab = .mudariMarfu) : hukm j = ⟨.qabih, .maqbul⟩ := by
  obtain ⟨a, t, l, s, w⟩ := j
  simp only at hs hl hsh hw
  subst hl hsh hw
  cases t <;> simp_all [hukm, hukmJaza, hukmJawab, hukmMuqaddam]

/-- **وبعد شرطٍ ماضٍ مقبول، في الترتيبين** (س9275–9276، س9281). وفي الباب حكمٌ ثانٍ بالقبح على الحقول نفسها في الترتيب الثاني
    («آتيك إن احمر البسر كان قبيحا»، س9228)، والفارقُ معنًى لا تحمله الحقول؛ فهذا اختيارُ الرأس. -/
theorem raf_baad_madi (j : Jumla) (hs : sinfOf j.adat = .jaza) (hl : j.lamQasam = false)
    (hsh : j.shart = .madi) (hw : j.jawab = .mudariMarfu) : hukm j = maqbul := by
  obtain ⟨a, t, l, s, w⟩ := j
  simp only at hs hl hsh hw
  subst hl hsh hw
  cases t <;> simp_all [hukm, hukmJaza, hukmJawab, hukmMuqaddam]

/-- **لا جزاءَ بـ«حيث» و«إذ» بلا «ما»** (س9192–9193). -/
theorem jazm_haythu_idh (j : Jumla) (hs : sinfOf j.adat = .haythuIdh) (hsh : j.shart = .mudariMajzum) :
    (hukm j).kalam = .khata := by
  simp [hukm, hs, hukmHaythuIdh, hsh]

/-- **«إذا» تُجزم في الشعر اضطرارًا، وهو في الكلام خطأ** (س9233–9234، س9240–9241). -/
theorem idha_jazm (j : Jumla) (hs : sinfOf j.adat = .idha) (hl : j.lamQasam = false)
    (h : j.shart = .mudariMajzum ∨ j.jawab = .mudariMajzum) : hukm j = ⟨.khata, .maqbul⟩ := by
  simp [hukm, hs, hukmIdha, hl, h]

/-! ## الجسر إلى القطر وإلى جدول العوامل (على الشاهد) -/

/-- حذفُ الحركات (U+064B–U+0652) للمقارنة بألفاظ جدول العوامل المشكولة. -/
def jarrid (s : String) : String :=
  String.ofList (s.toList.filter (fun c => !(0x064B ≤ c.toNat && c.toNat ≤ 0x0652)))

/-- **أدواتُ القطر L115 وأدواتُ الباب.** في القطر ولا يُجازى به في الباب: «إذ» (بلا «ما»؛ و`sinfOf` يجعلها `haythuIdh`)
    و«أيان» (لا يذكرها الباب). وفي الباب ولا لفظَ لها في القطر L115: «أيهم» و«أي حين» و«إذ ما» مفصولةً، وصورُ «ما» اللغو. -/
theorem adawat_qatr :
    KhulasaIkhbar.qatrL115.filter (fun w => !adawatJaza.contains w) = ["إذ", "أيان"] ∧
    adawatJaza.filter (fun w => !KhulasaIkhbar.qatrL115.contains w) =
      ["أيهم", "أي حين", "إذ ما", "متى ما", "إن ما", "إما", "أينما", "أيا ما", "أياما"] ∧
    sinfOf "إذ" = .haythuIdh ∧ sinfOf "أيان" = .ghayr := by
  decide +kernel

/-- **أدواتُ قيد الشرط في جدول العوامل** (`QaydMafhum.adawatOf .shart`، صنفا 10 و11) **بحكم الباب.** قيدُ الشرط في المفهوم
    أعمُّ من الجزاء بالجزم: «إذا» يشهد للشرط في الجدول ولا يُجازى بها في الكلام عند سيبويه، و«كيفما» و«لو» و«لولا» و«لوما»
    لا يحكم فيها هذا الباب. -/
theorem adawat_jadwal :
    (QaydMafhum.adawatOf .shart).map (fun w => sinfOf (jarrid w)) =
      [.jaza, .jaza, .jaza, .jaza, .jaza, .jaza, .jaza, .jaza, .jaza, .ghayr, .idha, .ghayr, .ghayr, .ghayr] := by
  decide +kernel

/-- صورةُ الجواب عند القطر (`KhulasaIkhbar`، L119–121) لخمسٍ من صورنا، تعيينٌ: الفعلُ المجزوم يصلح لمباشرة الأداة، والاسميّةُ
    لا تصلح، ومعها القرنُ كما كُتب. **والمستبعَدُ ثمانٍ من ثلاث عشرة:**
    - `mudariMarfu` و`faMudariMarfu`: بالمقابلة الظاهرة (الفعلُ يصلح، والفاءُ قرن) يخالف البابُ ترميزَ القطر فيهما. فالباب يقبّح
      الرفع بعد الجزم ويقبل «فأكرمك»، والترميزُ بالعكس. وتأويلُ سيبويه «فأنا أكرمك» (س9301) يجعل الثانيةَ اسميّةً في المعنى، والحقولُ
      لا تحمله.
    - `madi`: «لا حكم» بتعيين الرأس.
    - وخمسٌ لم تُقابَل: `faGhayr`، `faIdha`، `waw`، `thumma`، `lamQasam`. -/
def suraQatr : Jawab → Option (KhulasaIkhbar.SalahiyyatMubasharatAlAdah × KhulasaIkhbar.SurahQarnJawab)
  | .mudariMajzum => some (.yaslahu, .bilaQarn)
  | .faMudariMajzum => some (.yaslahu, .bilFa)
  | .ismiyya => some (.laYaslahu, .bilaQarn)
  | .faIsmiyya => some (.laYaslahu, .bilFa)
  | .idhaIsmiyya => some (.laYaslahu, .biIdhaFujaiyya)
  | _ => none

/-- **الاتّفاقُ على الصور الخمس المختارة** في `suraQatr`: يقبل الكلامُ الجوابَ بعد «إن تفعلْ» إن وفقط إن كان قرنُه من صور
    `KhulasaIkhbar.suwarQarnAlJawab` لصلاحيّته. وفي `faMudariMajzum` يقوم الاتّفاقُ على حصر ذلك الترميز (`.yaslahu` بلا قرنٍ وحده):
    لو أجاز الفاءَ مع الصالح لقبلها الترميزُ وردّها الباب. والقطرُ L119–121 يشترط القرنَ في غير الصالح، ولا ينصّ على منعه في الصالح.
    فهذا اتّفاقُ ترميزين، لا اتّفاقُ الكتابين. -/
theorem qarn_qatr_tawafuq :
    [Jawab.mudariMajzum, .faMudariMajzum, .ismiyya, .faIsmiyya, .idhaIsmiyya].all (fun w =>
      match suraQatr w with
      | none => false
      | some (sal, qarn) =>
        decide ((hukm ⟨"إن", .shartAwwalan, false, .mudariMajzum, w⟩).kalam = .maqbul) ==
          (KhulasaIkhbar.suwarQarnAlJawab sal).contains qarn) = true := by
  decide +kernel

end BabJaza
end Jisr
