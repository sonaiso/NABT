import A116.Bawwabat

/-!
# الحقائقُ الثلاث والمجازُ بقرينته (ADR ٩٢، أمرُ المالك 2026-10-17: «أنت أوجد حلًّا»)

المرفقُ اقترح ترتيبَ بوّاباتٍ: الشرعيّةُ أوّلًا، ثمّ العرفيّة، ثمّ اللغويّة، والمجازُ مقفلٌ إلّا عند جدار الامتناع.
والحلُّ هنا من نصّ الشخصيّة ج3 المختوم بعينه (الأسطرُ 1-based):

* س439: «ألفاظُ اللغة العربيّة لا تخرج عن هذه الثلاث: إمّا حقيقةٌ لغويّة، وإمّا حقيقةٌ شرعيّة، وإمّا حقيقةٌ عرفيّة».
* س420: الحقيقةُ الشرعيّة «اللفظُ الذي وضعه الشرع لمعنًى بحيث يدلّ عليه بلا قرينة».
* س441–445: العرفيّةُ عامّةٌ (الدابّة، الغائط) وخاصّةٌ (اصطلاحُ النحاة على الرفع والنصب والجرّ)، والأوّلُ «هُجر».
* س448: «النقلُ خلافُ الأصل… فالأصلُ عدمُ النقل».
* س449: «الأسماءُ الشرعيّة قد وُجد نقلُها، ولكنّ الحروف لم يوجد نقلُها».
* س453: الاحتمالاتُ الخمسة «كلُّ واحدٍ منها مرجوحٌ بالنسبة إلى كلّ ما بعده، راجحٌ على ما قبله، إلّا الإضمارَ والمجازَ
  فهما سيّان»؛ وس458: «المجازُ أولى من النقل»؛ وس461: «فلا يُحمل على أحدهما ما لم توجد قرينة».
* س599: المجازُ «اللفظُ المستعمل في غير ما وُضع له لقرينةٍ تمنع من إرادة المعنى الأصليّ».

## ما يُبنى

* **ليس ترتيبَ طبقات.** الحقيقةُ الشرعيّة والعرفيّة نقلٌ ثابت يُقرأ من مودَع (`naql`)، وما ليس فيه فهو على الأصل: لغويّة.
* **المجازُ لا يكون إلّا بقرينةٍ مانعة** في الكلام. والامتناعُ في الواقع وحدَه ليس قرينة: «حملتُ الجبل» يبقى حقيقةً لغويّةً
  مستقيمةً كاذبة، كما صنّفه سيبويه (ADR ٨٨) والسيرافيّ (ADR ٨٩).
* **الترجيحُ بين الاحتمالات** رتبٌ، والتساوي «لا حكم» لا ترجيحٌ بلا دليل.
* **المخرجُ ثلاثيّ**: حقيقةٌ بنوعها، أو مجازٌ أو إضمارٌ بقرينته، أو «لا حكم».

وما لا يُبرهَن: أنّ هذا قانونُ العربيّة. ذلك مرويُّ ج3 بأسطره. والقرينةُ مُدخَل (`QARINA_IS_INPUT`).
-/

namespace A116.Haqaiq

/-! ## الحقائقُ الثلاث -/

inductive Urf | amma | khassa
  deriving DecidableEq, Repr

/-- الحقيقةُ: لغويّةٌ أو شرعيّةٌ أو عرفيّة (س439). -/
inductive Naw
  | lughawiyya
  | shariyya
  | urfiyya (u : Urf)
  deriving DecidableEq, Repr

/-- **لا رابعة** (س439). -/
theorem la_rabia (n : Naw) :
    n = .lughawiyya ∨ n = .shariyya ∨ n = .urfiyya .amma ∨ n = .urfiyya .khassa := by
  cases n with
  | lughawiyya => simp
  | shariyya => simp
  | urfiyya u => cases u <;> simp

/-! ## مودَعُ المنقول: صفوفٌ من أسطر ج3 بأعيانها -/

/-- صفُّ نقل: اللفظ، ونوعُ حقيقته المنقولة، وهل هو حرف، وسطرُ شاهده. -/
structure Manqul where
  lafz : String
  naw : Naw
  harf : Bool
  satr : Nat
  deriving DecidableEq, Repr

/-- المنقولُ الثابت كما في النصّ: الشرعيّة (س417)، والعرفيّةُ العامّة (س442–443)، والخاصّة (س445). -/
def naql : List Manqul :=
  [⟨"الصلاة", .shariyya, false, 417⟩, ⟨"الزكاة", .shariyya, false, 417⟩,
   ⟨"الصوم", .shariyya, false, 417⟩, ⟨"الإيمان", .shariyya, false, 417⟩,
   ⟨"الدابة", .urfiyya .amma, false, 442⟩, ⟨"الغائط", .urfiyya .amma, false, 443⟩,
   ⟨"الرفع", .urfiyya .khassa, false, 445⟩, ⟨"النصب", .urfiyya .khassa, false, 445⟩,
   ⟨"الجر", .urfiyya .khassa, false, 445⟩]

/-- **الحروفُ لم يوجد نقلُها** (س449): لا صفَّ حرفٍ في المودَع. -/
theorem huruf_la_tunqal : ∀ r ∈ naql, r.harf = false := by decide

/-- لا صفَّ لغويٌّ في مودَع المنقول: المنقولُ شرعيٌّ أو عرفيٌّ وحدَه (س447). -/
theorem manqul_ghayr_lughawi : ∀ r ∈ naql, r.naw ≠ .lughawiyya := by decide

def lookup (rows : List Manqul) (l : String) : Option Naw :=
  (rows.find? (·.lafz == l)).map (·.naw)

/-! ## الاحتمالاتُ الخمسة وترجيحُها (س452–461) -/

inductive Ihtimal | ishtirak | naqlI | majaz | idmar | takhsis
  deriving DecidableEq, Repr

/-- الرتبة: كلٌّ مرجوحٌ بما بعده، والمجازُ والإضمارُ سيّان (س453). -/
def rutba : Ihtimal → Nat
  | .ishtirak => 0
  | .naqlI => 1
  | .majaz => 2
  | .idmar => 2
  | .takhsis => 3

/-- الترجيح: الأعلى رتبة، و«لا حكم» عند التساوي بين مختلفين («لا يترجح أحدُهما على الآخر إلّا بدليل»، س461). -/
def tarjih (a b : Ihtimal) : Option Ihtimal :=
  if a = b then some a
  else if rutba b < rutba a then some a
  else if rutba a < rutba b then some b
  else none

def ihtimalat : List Ihtimal := [.ishtirak, .naqlI, .majaz, .idmar, .takhsis]

/-- أزواجُ التعارض: «يُؤخذ كلُّ واحدٍ مع ما بعده». -/
def azwaj : List (Ihtimal × Ihtimal) :=
  [(.ishtirak, .naqlI), (.ishtirak, .majaz), (.ishtirak, .idmar), (.ishtirak, .takhsis),
   (.naqlI, .majaz), (.naqlI, .idmar), (.naqlI, .takhsis),
   (.majaz, .idmar), (.majaz, .takhsis), (.idmar, .takhsis)]

/-- **عشرةُ أوجه** (س453)، تسعةٌ محسومةٌ وواحدٌ «لا حكم»: المجازُ والإضمار. -/
theorem ashara_awjuh :
    azwaj.length = 10 ∧ (azwaj.filter (fun p => (tarjih p.1 p.2).isSome)).length = 9 ∧
    tarjih .majaz .idmar = none := by decide

/-- كلُّ زوجٍ حُسم حُسم لما بعده: «مرجوحٌ بالنسبة إلى كلّ ما بعده». -/
theorem marjuh_bima_badahu :
    ∀ p ∈ azwaj, tarjih p.1 p.2 = some p.2 ∨ tarjih p.1 p.2 = none := by decide

/-- الشواهد: النقلُ أولى من الاشتراك (س454)، والمجازُ أولى من النقل (س458)، والإضمارُ أولى من النقل (س459)،
والتخصيصُ أولى من النقل (س460) ومن المجاز (س462) ومن الإضمار (س463). -/
theorem shawahid_tarjih :
    tarjih .ishtirak .naqlI = some .naqlI ∧ tarjih .naqlI .majaz = some .majaz ∧
    tarjih .naqlI .idmar = some .idmar ∧ tarjih .naqlI .takhsis = some .takhsis ∧
    tarjih .majaz .takhsis = some .takhsis ∧ tarjih .idmar .takhsis = some .takhsis := by decide

/-- **«الخيرُ من الخير خير»** (س460): الترجيحُ متعدٍّ. -/
theorem khayr_min_khayr (a b c : Ihtimal) (h1 : tarjih a b = some b) (h2 : tarjih b c = some c) :
    tarjih a c = some c := by
  cases a <;> cases b <;> cases c <;> simp_all [tarjih, rutba]

/-- **«المساوي للخير خير»** (س459): ما ساوى المجازَ رتبةً يغلب ما يغلبه المجاز. -/
theorem musawi_lil_khayr (x : Ihtimal) (h : rutba x = rutba .majaz) (hx : x ≠ .naqlI) :
    tarjih .naqlI x = some x := by
  cases x <;> simp_all [tarjih, rutba]

/-! ## الحمل: من اللفظ وقرينته إلى الحقيقة أو المجاز -/

/-- القرينة: مانعةٌ من المعنى الأصليّ (س599)، تعيّن وجهًا أو لا تعيّنه. -/
inductive Qarina
  | mania (wajh : Option Ihtimal)
  deriving DecidableEq, Repr

inductive Haml
  | haqiqa (n : Naw)
  | majaz
  | idmar
  | laHukm
  deriving DecidableEq, Repr

/-- الحمل: القرينةُ المانعة تصرف عن الأصل إلى ما عيّنته، وإن لم تعيّن بين سيّين فـ«لا حكم» (س461)؛ وبلا قرينة:
المنقولُ الثابت حقيقتُه بلا قرينة (س420)، وإلّا فالأصلُ عدمُ النقل: لغويّة (س448). -/
def haml (rows : List Manqul) (l : String) : Option Qarina → Haml
  | some (.mania (some .majaz)) => .majaz
  | some (.mania (some .idmar)) => .idmar
  | some (.mania _) => .laHukm
  | none => match lookup rows l with
    | some n => .haqiqa n
    | none => .haqiqa .lughawiyya

/-- **الأصلُ عدمُ النقل** (س448): ما ليس في المودَع لغويّ. -/
theorem asl_adam_naql (rows : List Manqul) (l : String) (h : lookup rows l = none) :
    haml rows l none = .haqiqa .lughawiyya := by simp [haml, h]

/-- **لا شرعيّةَ ولا عرفيّةَ بلا نقلٍ مودَع.** -/
theorem la_naql_bila_mawda (rows : List Manqul) (l : String) (n : Naw)
    (h : haml rows l none = .haqiqa n) (hn : n ≠ .lughawiyya) : lookup rows l = some n := by
  unfold haml at h
  cases hl : lookup rows l with
  | none => simp [hl] at h; exact absurd h.symm hn
  | some m => simp [hl] at h; simp [h]

/-- **لا مجازَ بلا قرينةٍ مانعةٍ تعيّنه** (س599). -/
theorem majaz_bi_qarina (rows : List Manqul) (l : String) (q : Option Qarina)
    (h : haml rows l q = .majaz) : q = some (.mania (some .majaz)) := by
  rcases q with _ | ⟨_ | w⟩
  · simp only [haml] at h; split at h <;> simp at h
  · simp [haml] at h
  · cases w <;> simp_all [haml]

/-- والحقيقةُ الشرعيّة بلا قرينة (س420): المنقولُ لا يحتاج قرينة. -/
theorem shariyya_bila_qarina :
    haml naql "الصلاة" none = .haqiqa .shariyya := by decide

/-- الشواهد: الصلاةُ شرعيّة، والدابّةُ عرفيّةٌ عامّة، والرفعُ عرفيّةٌ خاصّة، والأسدُ لغويّة (س444)،
و«هذا ابني» بقرينةٍ لا تعيّن بين المجاز والإضمار «لا حكم» (س461)، والأسدُ للشجاع مجازٌ بقرينته (س402). -/
theorem shawahid_haml :
    haml naql "الدابة" none = .haqiqa (.urfiyya .amma) ∧
    haml naql "الرفع" none = .haqiqa (.urfiyya .khassa) ∧
    haml naql "الأسد" none = .haqiqa .lughawiyya ∧
    haml naql "ابني" (some (.mania none)) = .laHukm ∧
    haml naql "الأسد" (some (.mania (some .majaz))) = .majaz := by decide

/-- «نجس» (س458): يحتمل المجازَ والنقلَ ولا نقلَ مودَع، فالمجازُ أولى: الترجيحُ يعيّن القرينةَ مجازًا. -/
theorem najas :
    lookup naql "نجس" = none ∧ tarjih .naqlI .majaz = some .majaz ∧
    haml naql "نجس" ((tarjih .naqlI .majaz).map (fun w => .mania (some w))) = .majaz := by decide

/-! ## مع الصدق (ADR ٨٩): الامتناعُ ليس قرينة -/

/-- **«حملتُ الجبل»**: بلا قرينةٍ في الكلام لا مجاز، فاللفظُ على حقيقته اللغويّة، والحكمُ عليه كذبٌ بالمسوّدة
(`SidqSirafi`) لا صرفٌ إلى «تحمّل المشقّة». فيبقى مثالُ سيبويه مستقيمًا كاذبًا. -/
theorem jabal_haqiqa_kadhib :
    haml naql "الجبل" none = .haqiqa .lughawiyya ∧
    Bawwabat.ofHukm (SidqSirafi.hukm SidqSirafi.musawwada .khabar [.fil .madi, .ism]
      (some ⟨"الإنسان", "حمل", "الجبل", true⟩) none) = some false := by decide

/-! ## المراسي -/

/-- (النصّ، السطر 1-based، النصّ بعينه). -/
def marasi : List (String × Nat × String) :=
  [("j3", 417, "الأسماء الشرعية هي الألفاظ التي استفيد من الشارع وضعها"),
   ("j3", 420, "بحيث يدل عليه بلا"),
   ("j3", 439, "وألفاظ اللغة العربية لا تخرج عن هذه الثلاث"),
   ("j3", 442, "كاختصاص لفظ الدابة بذوات الأربع عرفاً"),
   ("j3", 443, "كاسم الغائط"),
   ("j3", 444, "كالأسد للحيوان المفترس"),
   ("j3", 445, "من مثل اصطلاح النحاة على الرفع، والنصب، والجر فإنه حقيقة عرفية خاصة"),
   ("j3", 448, "فالأصل عدم النقل"),
   ("j3", 449, "ولكن الحروف لم يوجد نقلها"),
   ("j3", 453, "إلا الإضمار والمجاز فهما سيان"),
   ("j3", 454, "الأول: النقل أولى من الاشتراك"),
   ("j3", 458, "الخامس: المجاز أولى من النقل"),
   ("j3", 459, "السادس: الإضمار أولى من النقل"),
   ("j3", 460, "السابع: التخصيص أولى من النقل"),
   ("j3", 461, "فلا يحمل على أحدهما ما لم توجد قرينة"),
   ("j3", 462, "التاسع: التخصيص أولى من المجاز"),
   ("j3", 463, "العاشر: التخصيص أولى من الإضمار"),
   ("j3", 599, "والمجاز هو اللفظ المستعمل في غير ما وضع له لقرينة تمنع من إرادة المعنى الأصلي")]

end A116.Haqaiq
