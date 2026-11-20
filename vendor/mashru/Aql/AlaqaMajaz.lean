/-
  Aql/AlaqaMajaz.lean — شرط شرعيّة العلاقة التي يستهلكها haml (QawaninDalala.lean) لإصدار .majaz:
  شاهدٌ من واقعٍ مختوم باسمها، لا Bool مجرّد؛ ومسجَّلٌ خصّيصًا لهويّة دعواها هي، لا لمجرّد مصدرٍ
  يشاركه غيرُها. ومخالفةُ معلومةٍ مقيسةٍ (رياضية أو فيزيائية، نوعها maalumatSabiqa لا waqiMakhtum)
  لا تحقّق هذا الشرط أصلًا.

  السند (البناء الأصل، 2026-10-19): فجوةٌ أقرّها المالك صريحًا بعد نقدي مقترح «مصفوفة المحاذاة
  الارتكازية» (رضا-النبهاني) الذي حاول حقن مخالفة حقائق رياضية/فيزيائية بوّابةً سابقةً تُسقط رتبة
  الوضع، وبعد نقاشٍ في أساس ثلاث ملكاتٍ معرفيّة ميّز النبهاني بينها بثلاثة نصوص (الوضع بالنقل، ج3
  729؛ الرياضيّ بالضرورة/عالميّته، ج1 789 و865؛ الحقيقة الخارجية بالحسّ المشهود، Aqliyya/Maratib/
  Hawass). سأل المالك عن سند عبارة «مدركه الحسّ والضرورة»، فقلتُ لا أجدها بالحرف؛ فأجاب: «لا يوجد
  عندي لكنّها فجوةٌ في النظام نحتاج علاجًا لها». هذا الملفّ علاجُها.

  haml مبرهنةٌ بالفعل ألّا تصدر .majaz قبل استنفاد الحقائق الثلاث (QawaninDalala.la_majaz_qabl_istinfad)،
  وبعد الاستنفاد التامّ (الثلاث .la) تتبع alaqa : Bool وحده (majaz_bad_istinfad). فالثغرة ليست في
  منطق haml؛ الثغرة أنّ alaqa عارٍ من اسمٍ أو شاهد — فلو حُسب خارج haml من مطابقةٍ آليّةٍ (كجدول
  مقارنةٍ ثابت) لا من مودَعٍ مختوم، لم يمنعه من الدخول شيء. البناء الأصل يُسمّي الشرط الناقص
  (AlaqaMajaz، شاهدٌ لا Bool) ويبرهن أنّ علاقةً شاهدُها من مودَعٍ غير مختوم (نوعه maalumatSabiqa،
  وهو نوعُ جداول نظام الفيزياء/الرياضيات في Jamad.lean نفسِها: علميٌّ يُقيَّد مقيسًا لا شاهدَ واقع)
  لا تحقّق الشرط، فلا تُنتج .majaz عبر haml في أيّ تشكيلٍ للحقائق الثلاث.

  تحديثٌ (2026-10-19، بإذن المالك: اختار «تخصيص التسجيل بالدعوى» من ثلاثة مسارات عرضتُها عليه، بعد وثيقتَي
  تدقيقٍ خارجيّتين رفعهما): mashrua في البناء الأصل لم تقرأ ism أصلًا، فشاهدٌ مختومٌ اعتُمد لدعوى كان يشرّع أيّ
  دعوى أخرى تشارك مصدره ونوعه. فهذا التحديث يضيف هويّةً للدعوى (DawaMajaz: الاسم، والمعنى الحقيقيّ، والمعنى
  المجازيّ — فهرسا Maana كما في QawaninDalala.Qadiyya) وقيدَ تسجيلٍ (QaydTasjil: بصمة، نوع، دعوى)، وتشترط
  mashrua قيدًا بهويّة الدعوى نفسِها، ولا تقبل قيدًا بصمته فارغة (كانت تطابق كلّ شاهد: كلّ نصٍّ يبدأ بالفارغ).
  ومبرهنتا haml العامّتان (٣) تأخذان سقوطَ alaqaOf فرضًا (hf)؛ ومنهما تُشتقّ الطرفيّات لكلّ سبب (٤) عبر تعريف
  alaqaOf نفسِه، فلو انفصلت alaqaOf عن mashrua سقط برهانها. لا تعديل على waqiMakhtum ولا على Qaida.lean أو
  QawaninDalala.lean. ولا AlaqaMajaz حقيقيّةٌ مسجَّلةٌ في المستودع بعدُ — فالمبرهنات هنا، كما في البناء الأصل،
  على شاهدٍ عامّ مجرَّد، لا على مثالٍ معجميٍّ معتمد؛ تعميرُ أمثلةٍ حقيقيّةٍ عملٌ منفصل. وما يبقى خارج Lean
  بطبيعته: أنّ نصّ الشاهد يقول الدعوى فعلًا — نقلٌ يُقرأ ويُراجَع، لا يُبرهَن.

  بناؤه الأصل يُعيد نسق Maratib.la_mafhum_bila_waqi وHawass.shahid_ghayr_mudaa_la_yuthir على alaqa
  بدل الشاهد الحسّيّ. لا جدول خارجيّ لهذه القطعة ولا مرآة بايثون، كـ SababShartMani.lean. بلا sorry
  ولا axiom ولا native_decide.
-/
import Aql.QawaninDalala
import Aql.Maratib

namespace AlaqaMajaz
open QawaninDalala Maratib

/-- هويّة الدعوى المجازيّة: اسم العلاقة (كالسببيّة والمشابهة)، ومعناها الحقيقيّ والمجازيّ —
    فهرسا Maana كما في Qadiyya. لا تتماثل دعويان إلّا بتماثل الثلاثة معًا؛ فاسمٌ واحدٌ بين معنيين
    مختلفين دعويان لا دعوى. -/
structure DawaMajaz where
  ism    : String
  haqiqi : Nat
  majazi : Nat
deriving DecidableEq, Repr

/-- علاقةٌ مجازيّةٌ مسمّاة (من علاقات ج3: سببيّة بأقسامها، مسببيّة، مشابهة...): هويّةُ دعواها،
    وشاهدُ واقعها — لا Bool مجرّد. -/
structure AlaqaMajaz where
  dawa   : DawaMajaz
  shahid : ShahidWaqi
deriving DecidableEq, Repr

/-- قيدُ تسجيلٍ: بصمةُ مودَعٍ ونوعُه (الدستور م12)، وهويّةُ الدعوى الوحيدة التي اعتُمد شاهدًا لها.
    لا يُقرأ قيدٌ شاهدًا لدعوى غير التي سُجِّل لها، ولو شارك بصمةً ونوعًا. -/
structure QaydTasjil where
  basma : String
  naw   : Idaa.Naw
  dawa  : DawaMajaz
deriving DecidableEq, Repr

/-- شرعيّةُ العلاقة: قيدٌ بصمتُه غيرُ فارغةٍ يبدأ بها شاهدُها، نوعُه «واقعٌ مختوم» بعينه (نسق
    Maratib.shuhudMutabara)، مسجَّلٌ خصّيصًا لهويّة دعواها هي. -/
def mashrua (sijill : List QaydTasjil) (a : AlaqaMajaz) : Bool :=
  sijill.any fun q => !q.basma.isEmpty && a.shahid.basma.startsWith q.basma && q.naw == .waqiMakhtum && q.dawa == a.dawa

/-- إسقاطُها إلى Bool ليُغذَّى به haml.alaqa — فقط إن شُرعت. -/
def alaqaOf (sijill : List QaydTasjil) (a : AlaqaMajaz) : Bool :=
  mashrua sijill a

/-! ## ١. أسبابُ سقوط الشرعيّة -/

/-- **المعلومات السابقة لا تُشرِّع**: شاهدٌ من مودَعٍ كلُّه من نوعٍ آخر غير waqiMakhtum (كجداول نظام
    الفيزياء/الرياضيات — علميٌّ يُقيَّد مقيسًا، لا شاهدَ واقعٍ مختوم) لا يحقّق mashrua، أيًّا كانت
    العلاقة أو دعواها. -/
theorem mashrua_bila_waqi_makhtum
    (sijill : List QaydTasjil) (hs : ∀ q ∈ sijill, q.naw ≠ .waqiMakhtum)
    (a : AlaqaMajaz) : mashrua sijill a = false := by
  simp only [mashrua, Bool.not_eq_true, List.any_eq_false]
  intro q hq
  have := hs q hq
  cases h : q.naw <;> simp_all

/-- **عدم انتقال الشهادة بين دعويين**: إن لم يكن في السجلّ قيدٌ يطابق شاهدَ العلاقة (بصمةٌ غير فارغةٍ يبدأ بها،
    ونوعٌ waqiMakhtum) مسجَّلٌ لهويّة دعواها بعينها، فلا تُشرَّع — ولو كانت بصمةُ شاهدها نفسُها مسجَّلةً مختومةً
    لدعوى أخرى. فالشرطُ قاصرٌ على القيود المطابقة: ما سُجِّل لغير دعواها لا يشرّعها، وما لم يطابق لا شأن له. -/
theorem la_intiqal
    (sijill : List QaydTasjil) (a : AlaqaMajaz)
    (hd : ∀ q ∈ sijill, q.basma.isEmpty = false → a.shahid.basma.startsWith q.basma = true →
      q.naw = .waqiMakhtum → q.dawa ≠ a.dawa) :
    mashrua sijill a = false := by
  simp only [mashrua, Bool.not_eq_true, List.any_eq_false]
  intro q hq
  have := hd q hq
  cases h0 : q.basma.isEmpty <;> cases h1 : a.shahid.basma.startsWith q.basma <;>
    cases h2 : (q.naw == .waqiMakhtum) <;> cases h3 : (q.dawa == a.dawa) <;> simp_all

/-- **قيدٌ بصمتُه فارغةٌ لا يُشرّع**: كلّ نصٍّ يبدأ بالفارغ، فقيدٌ بلا بصمةٍ كان يطابق كلّ شاهد؛ والآن لا يشرّع
    علاقةً وحدَه، أيًّا كان نوعُه ودعواه. -/
theorem basma_farigha_la_tushri (n : Idaa.Naw) (d : DawaMajaz) (a : AlaqaMajaz) :
    mashrua [⟨"", n, d⟩] a = false := by
  simp [mashrua]

/-! ## ٢. العامّتان: سقوطُ alaqaOf لأيّ سببٍ لا يُنتج .majaz -/

/-- بعد استنفاد الحقائق الثلاث (الثلاث .la): سقوطُ alaqaOf (بأيّ سببٍ) يُنتج لا حكم، لا مجازًا (من
    majaz_bad_istinfad المستوردة بلا تعديل). -/
theorem ghayr_mashrua_la_hukm
    (sijill : List QaydTasjil) (a : AlaqaMajaz) (hf : alaqaOf sijill a = false)
    (sabq : Bool) (qarina : Option NawHaqiqa) :
    haml .la .la .la sabq qarina (alaqaOf sijill a) = .laHukm := by
  rw [hf]
  exact (majaz_bad_istinfad sabq qarina).2

/-- سقوطُ alaqaOf (بأيّ سببٍ) لا يُنتج .majaz عبر haml، أيًّا كانت شهادات الحقائق الثلاث — إمّا حقيقةٌ (إن شهدت
    واحدةٌ، la_majaz_qabl_istinfad المستوردة)، أو لا حكم (الباقي: ghayr_yuqif المستوردة، أو ghayr_mashrua_la_hukm
    إن شهدت الثلاث كلّها بالسلب التامّ). -/
theorem ghayr_mashrua_la_tunshi_majaz
    (sijill : List QaydTasjil) (a : AlaqaMajaz) (hf : alaqaOf sijill a = false)
    (s1 s2 s3 : Shahada) (sabq : Bool) (qarina : Option NawHaqiqa) :
    haml s1 s2 s3 sabq qarina (alaqaOf sijill a) ≠ .majaz := by
  by_cases h : s1 = .naam ∨ s2 = .naam ∨ s3 = .naam
  · exact la_majaz_qabl_istinfad s1 s2 s3 sabq qarina (alaqaOf sijill a) h
  · by_cases hg : s1 = .ghayr ∨ s2 = .ghayr ∨ s3 = .ghayr
    · rw [ghayr_yuqif s1 s2 s3 sabq qarina (alaqaOf sijill a) h hg]
      decide
    · have e1 : s1 = .la := by rcases s1 with _ | _ | _ <;> simp_all
      have e2 : s2 = .la := by rcases s2 with _ | _ | _ <;> simp_all
      have e3 : s3 = .la := by rcases s3 with _ | _ | _ <;> simp_all
      subst e1; subst e2; subst e3
      rw [ghayr_mashrua_la_hukm sijill a hf sabq qarina]
      decide

/-! ## ٣. الطرفيّات: من السبب إلى الحكم، عبر تعريف alaqaOf نفسِه

العامّتان تأخذان «alaqaOf … = false» فرضًا فلا تربطان alaqaOf بـ mashrua؛ هذه تربطهما — تشتقّ ذلك الفرض من السبب
عبر تعريف alaqaOf، فلو انفصلت alaqaOf عن mashrua (كأن تُعيد true دائمًا) سقط برهانها. -/

/-- بلا واقعٍ مختوم: بعد الاستنفاد التامّ لا حكم (صيغةُ main نفسُها بفرضها hs). -/
theorem alaqaOf_ghayr_mashrua_la_hukm
    (sijill : List QaydTasjil) (hs : ∀ q ∈ sijill, q.naw ≠ .waqiMakhtum)
    (a : AlaqaMajaz) (sabq : Bool) (qarina : Option NawHaqiqa) :
    haml .la .la .la sabq qarina (alaqaOf sijill a) = .laHukm :=
  ghayr_mashrua_la_hukm sijill a (mashrua_bila_waqi_makhtum sijill hs a) sabq qarina

/-- **النتيجة الجامعة** (صيغةُ main نفسُها بفرضها hs): بلا واقعٍ مختوم لا .majaz عبر haml في أيّ تشكيل. -/
theorem alaqa_ghayr_mashrua_la_tunshi_majaz
    (sijill : List QaydTasjil) (hs : ∀ q ∈ sijill, q.naw ≠ .waqiMakhtum)
    (a : AlaqaMajaz) (s1 s2 s3 : Shahada) (sabq : Bool) (qarina : Option NawHaqiqa) :
    haml s1 s2 s3 sabq qarina (alaqaOf sijill a) ≠ .majaz :=
  ghayr_mashrua_la_tunshi_majaz sijill a (mashrua_bila_waqi_makhtum sijill hs a) s1 s2 s3 sabq qarina

/-- شاهدُ دعوى أخرى: بعد الاستنفاد التامّ لا حكم. -/
theorem dawa_ukhra_la_hukm
    (sijill : List QaydTasjil) (a : AlaqaMajaz)
    (hd : ∀ q ∈ sijill, q.basma.isEmpty = false → a.shahid.basma.startsWith q.basma = true →
      q.naw = .waqiMakhtum → q.dawa ≠ a.dawa)
    (sabq : Bool) (qarina : Option NawHaqiqa) :
    haml .la .la .la sabq qarina (alaqaOf sijill a) = .laHukm :=
  ghayr_mashrua_la_hukm sijill a (la_intiqal sijill a hd) sabq qarina

/-- **شاهدُ دعوى أخرى لا يُنتج مجازًا**: إن لم يطابق شاهدَ العلاقة قيدٌ مختومٌ مسجَّلٌ لهويّة دعواها بعينها، فلا .majaz
    عبر haml في أيّ تشكيل — ولو كانت بصمتُه مسجَّلةً لدعوى أخرى. -/
theorem dawa_ukhra_la_majaz
    (sijill : List QaydTasjil) (a : AlaqaMajaz)
    (hd : ∀ q ∈ sijill, q.basma.isEmpty = false → a.shahid.basma.startsWith q.basma = true →
      q.naw = .waqiMakhtum → q.dawa ≠ a.dawa)
    (s1 s2 s3 : Shahada) (sabq : Bool) (qarina : Option NawHaqiqa) :
    haml s1 s2 s3 sabq qarina (alaqaOf sijill a) ≠ .majaz :=
  ghayr_mashrua_la_tunshi_majaz sijill a (la_intiqal sijill a hd) s1 s2 s3 sabq qarina

/-! ## ٤. شاهدُ حالة الانتقال (مثالُ المراجع المستقلّ، مبرهنٌ على الشاهد)

مثالٌ مجرَّد: الأسماء والفهارس للتمثيل لا دعوى معجميّة. بصمةُ الشاهد مسجَّلةٌ مختومةً لدعوى D1، وفي السجلّ قيدٌ آخر
للدعوى المطلوبة D2 (من نوعٍ غير مختوم). فرضُ الصيغة الأولى لـ la_intiqal («كلّ قيدٍ دعواه غير دعوى العلاقة») منتفٍ هنا،
والصيغة المقوّاة تنطبق فتمنع الانتقال. -/

def shahidD1 : DawaMajaz := ⟨"سببية", 1, 2⟩
def shahidD2 : DawaMajaz := ⟨"مشابهة", 1, 3⟩
def shahidSijill : List QaydTasjil := [⟨"abc", .waqiMakhtum, shahidD1⟩, ⟨"abc", .maalumatSabiqa, shahidD2⟩]
def shahidAlaqa : AlaqaMajaz := ⟨shahidD2, ⟨"abcdef", 7⟩⟩

/-- فرضُ الصيغة الأولى منتفٍ على الشاهد: في السجلّ قيدٌ دعواه دعوى العلاقة نفسُها. -/
theorem shahid_fard_awwal_muntafin : ¬ (∀ q ∈ shahidSijill, q.dawa ≠ shahidAlaqa.dawa) := by decide

/-- والصيغة المقوّاة تنطبق: شاهدٌ بصمتُه مختومةٌ لدعوى أخرى لا يُشرِّع. -/
theorem shahid_intiqal : mashrua shahidSijill shahidAlaqa = false := by
  apply la_intiqal
  intro q hq _ _ hn
  simp only [shahidSijill, List.mem_cons, List.not_mem_nil, or_false] at hq
  rcases hq with rfl | rfl
  · decide
  · cases hn

end AlaqaMajaz
