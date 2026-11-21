/-
  Aql/SababShartMani.lean — السببُ والشرطُ والمانعُ عند النبهاني (خطابُ الوضع)، فوق ركنِ الواقع في Aql/Aqliyya.lean.

  المناسبة: نقدُ شفرةٍ قدّمها المالك (`LogicalChecker`، فرعٌ رابعٌ فيها يستنبط من غياب الفاعل اللفظيّ
  («حُملت الجبال») حكمًا معيَّنًا: «الفاعل المحذوف هو الله حتمًا». هذا الملفّ يصوغ القيدَ الذي يمنع ذلك
  صوريًّا: السببُ الشرعيّ عند النبهاني لا يكون إلّا على وصفٍ ظاهر، فإذا غاب الوصفُ غاب ركنُ الواقع نفسُه
  (`Aql.Arkan.waqi = none`)، وقد ثبت هناك (`Aql.la_hukm_bila_waqi`) أنّ غياب الواقع يُسقط كلَّ حكمٍ من
  `aqliyya` أيًّا كانت المعلوماتُ السابقة أو القاعدة.

  **السند**: الشخصيّة الإسلاميّة، الجزء الثالث (أصول الفقه) — تقي الدين النبهاني. كان مرشّحًا منذ جلسة 2026-10-15
  (بصمة الأصل docx: 360f7653…)، وخُتم بإذن المالك الصريح («أوافق ان تنفذ الختم وفق افضل الممارسات»، الجلسة
  2026-10-17 12:14 بتوقيت عمّان؛ هذا بعد أن وُجد في `mudaat/sijill.json` إذنُ ختمٍ سابقٌ منسوبٌ إليه حرفيًّا لا
  أثر له في محادثة الجلسة، فأُزيل وأُعيد الختمُ بالأداة `mudaat/idaa.py sajjil` على الملفّ الأصل مباشرةً — انظر
  سجلّ «ما ضُبطتُ عليه» في CLAUDE.md). أسطر الاقتباس هنا من تحويلٍ نصّيٍّ لنسخةٍ مِن الملفّ نفسِه رُفعت في هذه
  الجلسة (2026-10-17) — **لا** من ملفّ `a2.txt` المسجَّل في السِجلّ لتلك الجلسة الأولى (غيرُ متوفّرٍ حين كُتبت
  هذه الأسطر؛ حضر لاحقًا في هذه الجلسة نفسِها بمسار `docs/a2.txt` بنفس البصمة المسجَّلة، ولم تُراجَع أسطرُ هذا
  الملفّ عليه بعد)؛ فرقمُ السطر هنا خاصٌّ بهذا التحويل لا بذاك.
  * س241: «السبب، في اصطلاح المتشرّعين، هو كلّ وصفٍ ظاهرٍ منضبطٍ دلّ الدليلُ السمعيّ على كونه معرِّفًا
    لوجود الحكم لا لتشريع الحكم … فالسببُ ليس موجِبًا للحكم، وإنّما هو معرِّفٌ لوجوده».
  * س243: «الشرطُ هو ما كان وصفًا مكمِّلًا لمشروطه … وقد عُرِف الشرطُ بأنّه ما يلزم من عدمه العدمُ، ولا
    يلزم من وجوده وجود».
  * س247–250: «المانعُ يكون مانعَ حكمٍ، ويكون مانعَ سبب … مانعُ الحكم … وصفٌ ظاهرٌ منضبطٌ يستلزم وجودُه عكسَ
    ما يقتضيه الحكم … ومانعُ السبب … يستلزم وجودُه عكسَ ما يقتضيه السبب».

  **البناء**: السببُ دالّةٌ على وصفٍ قد يظهر أو لا (`Option`)، لا تحكم إلّا على ما ظهر؛ فحكمُها عند الغياب
  "لا حكم" بالبناء لا بالتزامٍ إضافيّ — وهذا هو عينُ `Aql.Arkan.waqi` في Aqliyya.lean، فالمبرهنةُ المركزيّةُ
  هنا تطبيقٌ مباشرٌ لِـ`Aql.la_hukm_bila_waqi` على هذه القراءة. الشرطُ والمانعُ مبنيّان على عالَمِ شواهدَ
  صغيرٍ مبنيٍّ (لا نوعٍ مجرَّدٍ غيرِ مقيَّد) ليبقى القيدُ الذي يصفانه («لا يلزم من وجوده وجود»، «عكسُ ما
  يقتضيه السبب») صادقًا بالبناء لا دعوى.

  الوسم: مبرهن لكلّ ما سُمّي كذلك (حولَ أنواعٍ مجرَّدة أو نماذجَ مبنيّة، بلا اعتمادٍ على سند النبهاني في
  البرهان نفسِه؛ السندُ تسميةٌ وسياقٌ لا مقدّمة). الكتابُ مرشّحٌ لا مختوم، فلا نتيجةَ هنا توسَم «مطابَق»
  لسندٍ فيه. بلا sorry ولا axiom ولا native_decide.
-/
import Aql.Aqliyya

namespace SababShartMani
open Aql

variable {α β H : Type}

/-! ## ١. السببُ: وصفٌ ظاهرٌ، لا حكمَ على غيابه (ج3 س241) -/

/-- **السببُ الظاهر**: دالّةُ وصفٍ (`wasf`) قد تظهر على المدخل أو لا، ودالّةُ حكمٍ على ما ظهر وحده.
«معرِّفٌ لوجود الحكم لا لتشريعه» (س241): `hukm` تقرأ الوصفَ الظاهرَ، ولا تُستدعى على غيابه. -/
structure SababZahir (α β H : Type) where
  wasf : α → Option β
  hukm : β → H

/-- تشغيلُ السبب الظاهر: حكمُ الحاضر بدالّة `hukm`، وحكمُ الغائب «لا حكم» — بالبناء، لا بشرطٍ يُفرَض. -/
def SababZahir.run (s : SababZahir α β H) (a : α) : Option H :=
  match s.wasf a with
  | some w => some (s.hukm w)
  | none => none

/-- **غيابُ الوصف الظاهر لا يُخرِج حكمًا على الإطلاق**: بالبناء، أيًّا كانت `hukm` أو المدخل. -/
theorem ghiyab_la_yunshi_hukm (s : SababZahir α β H) (a : α) (h : s.wasf a = none) :
    s.run a = none := by simp [SababZahir.run, h]

/-- **لا يمكن حكمٌ معيَّنٌ مع غياب الوصف**: لو أخرج سببٌ ظاهرٌ حكمًا معيَّنًا (`some h'`) على مدخلٍ غاب
فيه وصفُه، لزم تناقضٌ — فإخراجُ فرعِ «الفاعل المحذوف هو الله حتمًا» حكمًا معيَّنًا من غياب الفاعل يناقض
كونَه سببًا ظاهرًا على هذا التعريف؛ فهو تخمينٌ مُلبَسٌ لباسَ الاستنباط، لا استنباطٌ. -/
theorem la_yumkin_hukm_muayyan_maa_ghiyab (s : SababZahir α β H) (a : α) (h : s.wasf a = none)
    (h' : H) (hc : s.run a = some h') : False := by
  rw [ghiyab_la_yunshi_hukm s a h] at hc; cases hc

/-! ## ٢. الوصلُ بركن الواقع: الغيابُ غيابُ واقعٍ لا حكم (Aql/Aqliyya.lean) -/

/-- **كلُّ سببٍ ظاهرٍ أركانُه ركنُ واقعٍ**: نموذجُ الأركان (`Arkan Unit β`) الذي واقعُه هو الوصفُ الظاهر
نفسُه؛ وإذا غاب (`waqi = none`) فحكمُ `aqliyya` «لا حكم» بمقتضى المبرهنة العامّة `Aql.la_hukm_bila_waqi`
نفسِها — لا بمبرهنةٍ جديدة، بل هو نفسُ ركنِ الواقع مطبَّقًا هنا. -/
theorem sabab_zahir_arkan_waqi (t : Unit → β → Bool) (q : Qaida Unit β H) (a : Arkan Unit β)
    (h : a.waqi = none) : aqliyya t q a = [] :=
  la_hukm_bila_waqi t q a h

/-! ## ٣. شاهدٌ مبنيّ: «حُملت الجبال»، فاعلٌ محذوف -/

/-- نموذجٌ مبنيّ: المدخل هو الفاعل نفسُه (`Option String`، `none` = محذوف)، والوصفُ الظاهرُ قراءتُه
المباشرة (`id`)، وحكمُه حين يظهر نصٌّ ثابت — لا يَهمّ أيُّ نصٍّ، فالمقصودُ حالُ الغياب. -/
def sababFail : SababZahir (Option String) String String := ⟨id, fun _ => "صدقٌ عقديّ"⟩

/-- **على الشاهد**: «حُملت الجبال» (فاعلٌ محذوف، أي المدخل `none`) — السببُ الظاهرُ حكمُه هنا «لا حكم»
(`none`)، لا «صدقٌ عقديّ». -/
theorem shahid_hummilat_aljibal : sababFail.run none = none := by decide

/-! ## ٤. الشرطُ: لازمٌ من العدم، غيرُ كافٍ من الوجود (ج3 س243) -/

/-- **الشرطُ**: على عالَمِ شواهدَ `ω`، شرطٌ ومشروطٌ هما وصفان؛ عدمُ الشرط يلزمه عدمُ المشروط في كلّ شاهد
(«ما يلزم من عدمه العدم»)، ووجودُه لا يلزمه وجودُ المشروط — بل يوجَد شاهدٌ فيه الشرطُ موجودٌ والمشروطُ معدومٌ
(«ولا يلزم من وجوده وجود»، س243). -/
structure Shart (ω : Type) (shart mashrut : ω → Prop) : Prop where
  lazim_min_adam : ∀ w, ¬ shart w → ¬ mashrut w
  la_yalzam_min_wujud : ∃ w, shart w ∧ ¬ mashrut w

/-- **الشرطُ وحدَه لا يحكم بوجود مشروطه**: من تعريف الشرط نفسِه — ليس زيادةً عليه. -/
theorem shart_wahdahu_la_yahkum {ω : Type} {shart mashrut : ω → Prop} (h : Shart ω shart mashrut) :
    ∃ w, shart w ∧ ¬ mashrut w := h.la_yalzam_min_wujud

/-- عالَمُ شواهدَ الوضوء والصلاة: ثلاثُ حالاتٍ ممكنةً وحدها (بعبارة البنّاء: لا صلاةَ بلا وضوء — قيدٌ على
العالَم نفسِه، لا نتيجةً تُستنبَط من فراغ؛ س243: «فلا توجد الصلاة إذا لم توجد الطهارة، ولكن قد توجَد الطهارة
ولا توجد الصلاة»). -/
inductive HalWudu | laWuduLaSalaa | wuduBilaSalaa | wuduWaSalaa
deriving DecidableEq

def HalWudu.wudu : HalWudu → Bool
  | .laWuduLaSalaa => false
  | .wuduBilaSalaa => true
  | .wuduWaSalaa => true

def HalWudu.salaa : HalWudu → Bool
  | .laWuduLaSalaa => false
  | .wuduBilaSalaa => false
  | .wuduWaSalaa => true

/-- شاهدٌ مبنيّ: الوضوءُ شرطٌ في الصلاة. -/
theorem shartWudu : Shart HalWudu (fun h => h.wudu = true) (fun h => h.salaa = true) where
  lazim_min_adam := by intro w; cases w <;> decide
  la_yalzam_min_wujud := ⟨.wuduBilaSalaa, by decide, by decide⟩

/-! ## ٥. المانعُ: عكسُ ما يقتضيه السببُ أو الحكمُ (ج3 س247–250) -/

/-- **مانعُ السبب**: وصفٌ ظاهرٌ منضبطٌ، وجودُه مع السبب في شاهدٍ يستلزم نقيضَ الحكم الذي يقتضيه السببُ
هناك («يستلزم وجودُه عكسَ ما يقتضيه السبب»، س250). -/
structure Mani (ω : Type) (sabab mani hukm : ω → Prop) : Prop where
  yaqlib : ∀ w, sabab w → mani w → ¬ hukm w

/-- **المانعُ، إذ وُجد مع السبب، يُسقط الحكم في ذلك الشاهد** — من تعريف المانع نفسِه، لا زيادةً عليه. -/
theorem mani_yusqit_bisabab {ω : Type} {sabab mani hukm : ω → Prop} (h : Mani ω sabab mani hukm)
    (w : ω) (hs : sabab w) (hm : mani w) : ¬ hukm w := h.yaqlib w hs hm

/-- عالَمُ شواهدَ النصاب والدَّين والزكاة: ثلاثُ حالاتٍ ممكنةً (بعبارة البنّاء: من بلغ النصابَ ودان دَينًا
كثيرًا فلا زكاةَ عليه — قيدٌ على العالَم نفسِه؛ س250: «[الدَّين] مانعٌ من وجوب الزكاة، على من كان عنده النصاب
وحال عليه الحول؛ لأنّ الدَّين مانعٌ من بقاء النصاب … مكتملًا»). -/
inductive HalZakat | dunaNisab | nisabBilaDaynKathir | nisabWaDaynKathir
deriving DecidableEq

def HalZakat.nisab : HalZakat → Bool
  | .dunaNisab => false
  | .nisabBilaDaynKathir => true
  | .nisabWaDaynKathir => true

def HalZakat.daynKathir : HalZakat → Bool
  | .dunaNisab => false
  | .nisabBilaDaynKathir => false
  | .nisabWaDaynKathir => true

def HalZakat.zakat : HalZakat → Bool
  | .dunaNisab => false
  | .nisabBilaDaynKathir => true
  | .nisabWaDaynKathir => false

/-- شاهدٌ مبنيّ: الدَّينُ الكثيرُ مانعُ سببٍ في الزكاة. -/
theorem maniDayn : Mani HalZakat (fun h => h.nisab = true) (fun h => h.daynKathir = true)
    (fun h => h.zakat = true) where
  yaqlib := by intro w; cases w <;> decide

end SababShartMani
