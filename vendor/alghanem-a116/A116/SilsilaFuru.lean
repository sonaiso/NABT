import A116.Silsila
import A116.SilsilaQurra
import A116.Naql
import A116.Iqtiran
import A116.Itar

/-!
# فروعُ السلسلة، وحملُ الحرف، والوضعُ بشهادة المعجم (ADR ١١٥، تصحيحُ المالك 2026-10-19)

قال المالك (2026-10-19 02:01 بتوقيت عمّان): «هناك خلل في فهم الوضع شهادة المعجم على الوضع كافي لبناء lean المفهوم الوضع
حسب النبهاني شهادة كافية سواء احاد او تواتر تكفي لبناء مفهوم عن حقيقة لغوية بالوضع»؛ وقال (02:04): «موجود معنى الحرف في
الشخصية الجزء الثالث وموجود في سيبويه وقطر الندى ومغني اللبيب معنى الحرف». ثمّ نقل (02:06) خطّةَ التصحيح التي كتبها
البنّاءُ في جوابه (لا لفظَ المالك: لا معنى لحرفٍ من خارج المودَع، ولا نقلَ للحرف فحملُه لغويٌّ أبدًا، والمحتمَلُ لا يُختار منه)
وقال: «اصلح كل المطلوب وقم بايداع كل ما يلزم».

## ما يُبنى

١. **الفروع** (`ahkam_append`، `far_mushtarak`): السلسلةُ فرعان من طبقاتٍ مشتركة، وكلُّ فرعٍ سلسلةٌ خطّيّةٌ بعينها
   (`pre ++ br`)، فمبرهناتُ `Silsila` قائمةٌ عليه؛ وأحكامُ الطبقات المشتركة واحدةٌ في الفرعين. ففرعُ الوضع
   (الشهادة ← القسم ← الحمل) لا يمرّ بالجنس، وفرعُ الجنس (الشهادة ← القسم ← الجذر ← الجنس) لا يمرّ بالحمل.
٢. **الحملُ بشهادة المعجم** (`hamlWad`): لكلّ جذرٍ شهدت له المعاجمُ لأحد مفاتيح الكلمة نوعُ حقيقة اللفظ
   (`SilsilaQurra.nawOf`) وحكمُ جسر الوضع على شهاداته (`Naql.jisrWad`)؛ فالشاهدُ الواحدُ من مودَع «وضع» يكفي مفهومًا ظنّيًّا
   (`Naql.wahid_yakfi`)، ولا قطعَ إلّا بحكم تواترٍ يُدخله المالك.
٣. **حملُ الحرف** (`maaniHarf`، `hamlHarf`، `nawHarf`): معاني الحرف من مودَعه وحدَه (`corpora/huruf/maani.tsv`: ج3 س468–507
   بترقيم الغانم، وشاهدُ «الكتاب» JK006989 حيث وُجد)، معيَّنًا بمعنًى واحد ومحتمَلًا بقائمته بلا ترجيح (`Iqtiran.mantuq`)،
   ونوعُ حقيقته لغويّةٌ أبدًا على المنقول المودَع لأنّ «الحروف لم يوجد نقلها» (ج3 س449) — من `Haqaiq.huruf_la_tunqal`.
٤. **مرشَّحو التقشير** (`qashr`): الكلمةُ نفسُها أوّلًا، ثمّ بلا «وَ/فَ»، ثمّ بلا «بِ/لِ/كَ/لَ»، وما بدأ بعده بساكنٍ غيرِ اللام
   رُدّت إليه همزةُ الوصل مكسورةً («لا يبتدأ بساكن»، ابن عقيل س9173 بترقيم الغانم؛ والاسمُ من الأسماء ذوات همزة الوصل
   س9187–9188؛ والكسرُ «لأنها مكسورة أبدا في الأسماء والأفعال إلا في الفعل المضموم الثالث»، «الكتاب» JK006989 س17573)،
   فـ«بِسْمِ» مرشَّحاها «بِسْمِ» و«ءِسْمِ». والقائمةُ المغلقة تعيينُ البنّاء (`PREFIX_LIST_DECLARED`).
٥. **مفتاحُ الحرف** (`harfKey`): حواملُ الخانات والمثلان المدغمان حاملٌ واحد — هيكلٌ بلا حركةٍ ولا شدّة، لأنّ ج3 غيرُ مشكول
   (`HARF_KEY_UNVOCALIZED`: «إِلَى» و«إِلَّا» و«أَلَا» مفتاحٌ واحد، فحملُها محتمَلٌ بمعانيها جميعًا).
-/

namespace A116.SilsilaFuru

open A116 A116.Silsila

/-! ## ١. الفروع -/

/-- **أحكامُ الموصول**: أحكامُ الطبقات الأولى، ثمّ أحكامُ ما بعدها على آخر حكمٍ منها. لكلّ كلمةٍ وطبقات. -/
theorem ahkam_append (w : String) (a : Hal) (ts us : List Tabaqa) :
    ahkam w a (ts ++ us) = ahkam w a ts ++ ahkam w ((ahkam w a ts).getLast?.getD a) us := by
  induction ts generalizing a with
  | nil => simp [ahkam]
  | cons t ts ih =>
    simp only [List.cons_append, ahkam, ih]
    cases hh : ahkam w (khutwa w a t) ts with
    | nil => simp
    | cons x xs => simp [List.getLast?_cons]

/-- **الطبقاتُ المشتركة واحدةٌ في الفرعين**: أحكامُها لا تتغيّر بما بعدها. لكلّ كلمةٍ وفروع. -/
theorem far_mushtarak (w : String) (a : Hal) (pre b1 b2 : List Tabaqa) :
    (ahkam w a (pre ++ b1)).take pre.length = (ahkam w a (pre ++ b2)).take pre.length := by
  rw [ahkam_append, ahkam_append, List.take_left' (ahkam_length _ _ _),
    List.take_left' (ahkam_length _ _ _)]

/-! ## ٢. الحملُ بشهادة المعجم -/

/-- شهادةُ معجمٍ لزوج (مفتاح، جذر): الزوجُ وشهادتُه. -/
abbrev ShahadaWad := (String × String) × Naql.Shahada

/-- شهاداتُ الجذر r لأحد المفاتيح. -/
def shuhudOf (sh : List ShahadaWad) (keys : List String) (r : String) : List Naql.Shahada :=
  (sh.filter fun x => keys.contains x.1.1 && x.1.2 == r).map (·.2)

/-- جذورُ المفاتيح في الشهادات، بلا تكرار. -/
def judhurWad (sh : List ShahadaWad) (keys : List String) : List String :=
  ((sh.filter fun x => keys.contains x.1.1).map (·.1.2)).eraseDups

/-- **الحملُ بشهادة المعجم**: لكلّ جذرٍ شُهد له نوعُ حقيقة اللفظ وحكمُ جسر الوضع على شهاداته. لا يقرأ الجنس. -/
def hamlWad (rows : List Haqaiq.Manqul) (tawatur : List Naql.Shahada → Bool) (sh : List ShahadaWad)
    (l : String) (keys : List String) : List (String × Haqaiq.Naw × Naql.Hukm) :=
  (judhurWad sh keys).map fun r => (r, SilsilaQurra.nawOf rows l, Naql.jisrWad tawatur (shuhudOf sh keys r))

/-- **لا حملَ بلا شهادة**: كلُّ جذرٍ في الحمل له شهادةٌ لأحد المفاتيح. لكلّ معجمٍ ومفاتيح. -/
theorem la_haml_bila_shahada (rows : List Haqaiq.Manqul) (t : List Naql.Shahada → Bool)
    (sh : List ShahadaWad) (l : String) (keys : List String) (x : String × Haqaiq.Naw × Naql.Hukm)
    (h : x ∈ hamlWad rows t sh l keys) : ∃ k ∈ keys, ∃ s, ((k, x.1), s) ∈ sh := by
  simp only [hamlWad, judhurWad, List.mem_map, List.mem_eraseDups, List.mem_filter,
    List.contains_iff_mem] at h
  obtain ⟨r, ⟨⟨⟨k, r'⟩, s⟩, ⟨hm, hk⟩, rfl⟩, rfl⟩ := h
  exact ⟨k, hk, s, hm⟩

/-- **رتبةُ الحمل رتبةُ جسر الوضع على شهاداته بعينها**. تعريفيّ. -/
theorem rutba_jisr (rows : List Haqaiq.Manqul) (t : List Naql.Shahada → Bool) (sh : List ShahadaWad)
    (l : String) (keys : List String) (x : String × Haqaiq.Naw × Naql.Hukm)
    (h : x ∈ hamlWad rows t sh l keys) : x.2.2 = Naql.jisrWad t (shuhudOf sh keys x.1) := by
  simp only [hamlWad, List.mem_map] at h
  obtain ⟨r, _, rfl⟩ := h
  rfl

/-- **الشاهدُ الواحدُ من الوضع يكفي مفهومًا ظنّيًّا** بلا حكم تواتر (`Naql.wahid_yakfi`). لكلّ شهادة. -/
theorem wahid_mafhum (s : Naql.Shahada) (hs : s.tariq = .naql) (hm : s.mawda = .wad) (key r : String) :
    Naql.jisrWad (fun _ => false) (shuhudOf [((key, r), s)] [key] r) = .mafhum .zanni s [] := by
  simp only [shuhudOf, List.filter, List.contains_cons, beq_self_eq_true, List.contains_nil, Bool.or_false,
    Bool.and_self, List.map]
  exact Naql.wahid_yakfi s hs hm

/-! ## ٣. حملُ الحرف -/

/-- صفُّ معنى حرف: مفتاحُه (`harfKey`)، ومعناه بلفظ ج3، وشهاداتُه (ج3، و«الكتاب» حيث وُجد). -/
structure MaanaHarf where
  harf : String
  maana : String
  shuhud : List Naql.Shahada
  deriving DecidableEq, Repr

/-- صفوفُ الحرف. -/
def sufuf (rows : List MaanaHarf) (k : String) : List MaanaHarf := rows.filter (·.harf == k)

/-- معاني الحرف: كلُّ ما في صفوفه، بلا تكرار. -/
def maaniHarf (rows : List MaanaHarf) (k : String) : List String :=
  ((sufuf rows k).map (·.maana)).eraseDups

/-- **لا معنى لحرفٍ من خارج المودَع**. لكلّ مودَعٍ وحرف. -/
theorem la_maana_kharij (rows : List MaanaHarf) (k m : String) (h : m ∈ maaniHarf rows k) :
    ∃ r ∈ rows, r.harf = k ∧ r.maana = m := by
  simp only [maaniHarf, sufuf, List.mem_eraseDups, List.mem_map, List.mem_filter, beq_iff_eq] at h
  obtain ⟨r, ⟨hr, hl⟩, hm⟩ := h
  exact ⟨r, hr, hl, hm⟩

/-- نوعُ حقيقة الحرف: ما في المنقول من صفوف الحروف بعينها، وإلّا لغويّة. -/
def nawHarf (rows : List Haqaiq.Manqul) (l : String) : Haqaiq.Naw :=
  match (rows.filter (·.harf)).find? (·.lafz == l) with
  | some r => r.naw
  | none => .lughawiyya

/-- **لا نقلَ للحرف، فحملُه لغويٌّ أبدًا** على المنقول المودَع (من `Haqaiq.huruf_la_tunqal`). لكلّ لفظ. -/
theorem harf_lughawi (l : String) : nawHarf Haqaiq.naql l = .lughawiyya := by
  have : Haqaiq.naql.filter (·.harf) = [] := by
    rw [List.filter_eq_nil_iff]
    intro r hr
    simp [Haqaiq.huruf_la_tunqal r hr]
  simp [nawHarf, this]

/-- **حملُ الحرف**: المنطوقُ الثلاثيّ على معانيه، ونوعُه، وحكمُ جسر الوضع على شهادات صفوفه بلا تكرار (فالسطرُ الواحدُ
في صفوفٍ كثيرة شهادةٌ واحدة). والتكرارُ يُزال بالسطر لا بالقائل: قائلٌ بسطرين شهادتان، فما بعد الرأس عددُ أسطرٍ لا
قائلين (`SHAHADA_COUNT_IS_LINES`). -/
def hamlHarf (tawatur : List Naql.Shahada → Bool) (rows : List MaanaHarf) (k : String) :
    Iqtiran.Mantuq String × Haqaiq.Naw × Naql.Hukm :=
  (Iqtiran.mantuq (maaniHarf rows k), nawHarf Haqaiq.naql k,
    Naql.jisrWad tawatur ((sufuf rows k).flatMap (·.shuhud)).eraseDups)

/-- **المعنى الواحد معيَّن**. لكلّ مودَع. -/
theorem wahid_muayyan (t : List Naql.Shahada → Bool) (rows : List MaanaHarf) (k m : String)
    (h : maaniHarf rows k = [m]) : (hamlHarf t rows k).1 = .muayyan m := by
  simp [hamlHarf, h, Iqtiran.mantuq]

/-- **المحتمَلُ لا يُختار منه**: معانٍ فوق الواحد حكمُها «محتمَل» بقائمتها كاملة. لكلّ مودَع. -/
theorem muhtamal_la_yukhtar (t : List Naql.Shahada → Bool) (rows : List MaanaHarf) (k a b : String)
    (rest : List String) (h : maaniHarf rows k = a :: b :: rest) :
    (hamlHarf t rows k).1 = .muhtamal (a :: b :: rest) := by
  simp [hamlHarf, h, Iqtiran.mantuq]

/-- **حملُ الحرف لغويٌّ أبدًا**. لكلّ مودَعٍ وحرف. -/
theorem hamlHarf_lughawi (t : List Naql.Shahada → Bool) (rows : List MaanaHarf) (k : String) :
    (hamlHarf t rows k).2.1 = .lughawiyya := harf_lughawi k

/-- **لا حكمَ لحرفٍ بلا صفّ**. لكلّ مودَع. -/
theorem la_hukm_bila_saff (t : List Naql.Shahada → Bool) (rows : List MaanaHarf) (k : String)
    (h : sufuf rows k = []) : (hamlHarf t rows k).1 = .laHukm := by
  simp [hamlHarf, maaniHarf, h, Iqtiran.mantuq]

/-! ## ٤. مرشَّحو التقشير ومفتاحُ الحرف -/

/-- خانة حاملٍ بحركة. -/
def kh (c : Char) (h : Haraka) : Cell := ⟨Ladder.carrierOf c, h⟩

/-- السابقةُ الأولى: «وَ»، «فَ». -/
def sabiqa1 : List Cell := [kh 'و' .fatha, kh 'ف' .fatha]

/-- السابقةُ الثانية: «بِ»، «لِ»، «كَ»، «لَ». -/
def sabiqa2 : List Cell := [kh 'ب' .kasra, kh 'ل' .kasra, kh 'ك' .fatha, kh 'ل' .fatha]

/-- قشرُ سابقةٍ من قائمة، وما بقي خانتان فأكثر (فلا تُقشر «لَ» من «لَاْ»). -/
def qishr (ps : List Cell) : List Cell → Option (List Cell)
  | c :: rest => if ps.contains c && 2 ≤ rest.length then some rest else none
  | [] => none

/-- ردُّ همزة الوصل مكسورةً إلى ما بدأ بساكنٍ غيرِ اللام (واللامُ الساكنةُ أداةُ تعريفٍ يجرّدها `tajrid`). -/
def radd : List Cell → List Cell
  | c :: rest => if c.haraka == .sukun && c.carrier != Ladder.carrierOf 'ل' then kh 'ء' .kasra :: c :: rest
                 else c :: rest
  | [] => []

/-- **مرشَّحو التقشير**: الكلمةُ أوّلًا، ثمّ بلا الأولى، ثمّ بلا الثانية، ثمّ بلاهما — بلا تكرار. -/
def qashr (w : List Cell) : List (List Cell) :=
  (w :: ((qishr sabiqa1 w).toList ++ (qishr sabiqa2 w).toList ++
    ((qishr sabiqa1 w).bind (qishr sabiqa2)).toList).map radd).eraseDups

/-- **الكلمةُ نفسُها مرشَّحٌ أوّل**. لكلّ كلمة. -/
theorem qashr_awwal (w : List Cell) : w ∈ qashr w := by
  simp [qashr, List.mem_eraseDups]

theorem qishr_suffix (ps w s : List Cell) (h : qishr ps w = some s) : ∃ c, w = c :: s := by
  cases w with
  | nil => simp [qishr] at h
  | cons c rest =>
    simp only [qishr] at h
    split at h
    · cases h; exact ⟨c, rfl⟩
    · cases h

/-- **ما قُشر لاحقةٌ للكلمة**، وقد رُدّت إليها همزةُ الوصل أو لم تُردّ. لكلّ كلمة. -/
theorem qashr_lahiqa (w v : List Cell) (h : v ∈ qashr w) :
    v = w ∨ ∃ s, s <:+ w ∧ (v = s ∨ v = kh 'ء' .kasra :: s) := by
  simp only [qashr, List.mem_eraseDups, List.mem_cons, List.mem_map, List.mem_append,
    Option.mem_toList] at h
  rcases h with h | ⟨s, hs, rfl⟩
  · exact .inl h
  · right
    have hsuf : s <:+ w := by
      rcases hs with (hs | hs) | hs
      · obtain ⟨c, rfl⟩ := qishr_suffix _ _ _ hs; exact List.suffix_cons _ _
      · obtain ⟨c, rfl⟩ := qishr_suffix _ _ _ hs; exact List.suffix_cons _ _
      · cases hm : qishr sabiqa1 w with
        | none => simp [hm] at hs
        | some m =>
          simp only [hm, Option.bind_some] at hs
          obtain ⟨c, hc⟩ := qishr_suffix _ _ _ hm
          obtain ⟨d, hd⟩ := qishr_suffix _ _ _ hs
          rw [hc, hd]
          exact (List.suffix_cons _ _).trans (List.suffix_cons _ _)
    refine ⟨s, hsuf, ?_⟩
    cases s with
    | nil => exact .inl rfl
    | cons c rest =>
      simp only [radd]
      split
      · exact .inr rfl
      · exact .inl rfl

/-- **رأسُ المرشَّحين الكلمةُ نفسُها**. لكلّ كلمة. -/
theorem qashr_head (w : List Cell) : ∃ t, qashr w = w :: t := by
  simp only [qashr, List.eraseDups_cons]
  exact ⟨_, rfl⟩

/-- **المرشَّحُ المختار**: أوّلُ مرشَّحٍ يصيبه المعجم — المباشرُ أوّلًا ثمّ المقشورُ بترتيبه، على نسق
`Sawabiq.candidates_head`. -/
def awwal (hit : List Cell → Bool) (w : List Cell) : Option (List Cell) := (qashr w).find? hit

/-- **المباشرُ أوّلًا**: إن أصاب المعجمُ الكلمةَ نفسَها لم يُقشر منها شيء. لكلّ معجمٍ وكلمة. -/
theorem mubashir_awwal (hit : List Cell → Bool) (w : List Cell) (h : hit w = true) : awwal hit w = some w := by
  obtain ⟨t, ht⟩ := qashr_head w
  simp [awwal, ht, h]

/-- **لا اختيارَ من خارج المرشَّحين**. لكلّ معجمٍ وكلمة. -/
theorem awwal_mem (hit : List Cell → Bool) (w v : List Cell) (h : awwal hit w = some v) :
    v ∈ qashr w ∧ hit v = true :=
  ⟨List.mem_of_find?_eq_some h, by simpa using List.find?_some h⟩

/-- مفتاحُ الحرف: الحواملُ حروفًا، والساكنُ قبل مثله ساقط (المثلان المدغمان حاملٌ واحد). -/
def harfKey : List Cell → String
  | c :: d :: rest =>
    if c.haraka == .sukun && c.carrier == d.carrier then harfKey (d :: rest)
    else (Field112.carrierChar c.carrier).toString ++ harfKey (d :: rest)
  | [c] => (Field112.carrierChar c.carrier).toString
  | [] => ""

/-! ## ٥. الشاهد -/

def j3 (s : Nat) : Naql.Shahada := ⟨"nabhani-j3", "nabhani", .naql, .wad, s⟩
def kit (s : Nat) : Naql.Shahada := ⟨"kitab-jk006989", "sibawayh", .naql, .wad, s⟩

/-- صفوفٌ من المودَع بأعيانها (`corpora/huruf/maani.tsv`). -/
def maaniMithal : List MaanaHarf :=
  [⟨"من", "لابتداء الغاية", [j3 469, kit 18417]⟩, ⟨"من", "للتبعيض", [j3 469, kit 18419]⟩,
   ⟨"من", "لبيان الجنس", [j3 469]⟩, ⟨"من", "زائدة", [j3 469, kit 18421]⟩,
   ⟨"و", "مبدلة عن باء الإلصاق", [j3 476, kit 18343]⟩,
   ⟨"و", "لمطـلق الجـمـع لا تفيد ترتيباً ولا معية", [j3 486, kit 18333]⟩,
   ⟨"رب", "للتقليل", [j3 475]⟩]

def shWad : List ShahadaWad :=
  [(("صَ لَ اْ ت", "صلو"), ⟨"lane", "lane", .naql, .wad, 0⟩),
   (("صَ لَ اْ ت", "صلو"), ⟨"m", "ibn-manzur", .naql, .wad, 1⟩)]

/-- **الشاهد** (`decide`): «من» محتمَلةٌ بمعانيها الأربعة لغويّةً ظنّيّةً بشاهد ج3، و«رب» معيَّنةٌ بمعنًى واحد، و«إِلَى» (مفتاحُها «ءلا»)
بلا صفٍّ في هذا المثال «لا حكم»؛ و«الصلاة» شرعيّةٌ من «صلو» مفهومٌ ظنّيٌّ بشاهدين؛ و«بِسْمِ» مرشَّحاها «بِسْمِ» و«ءِسْمِ»، و«وَلَا»
مرشَّحاها «وَلَا» و«لَا»؛ ومفتاحُ «إِلَى» و«إِلَّا» واحد. -/
theorem shahid :
    (hamlHarf (fun _ => false) maaniMithal "من").1 =
      .muhtamal ["لابتداء الغاية", "للتبعيض", "لبيان الجنس", "زائدة"] ∧
    (hamlHarf (fun _ => false) maaniMithal "من").2 =
      (.lughawiyya, .mafhum .zanni (j3 469) [kit 18417, kit 18419, kit 18421]) ∧
    (hamlHarf (fun _ => false) maaniMithal "رب").1 = .muayyan "للتقليل" ∧
    (hamlHarf (fun _ => false) maaniMithal "ءلا").1 = .laHukm ∧
    (hamlWad Haqaiq.naql (fun _ => false) shWad "الصلاة" ["صَ لَ اْ ت"]).map (fun x => (x.1, x.2.1)) =
      [("صلو", .shariyya)] ∧
    (hamlWad Haqaiq.naql (fun _ => false) shWad "الصلاة" ["صَ لَ اْ ت"]).map (·.2.2) =
      [.mafhum .zanni ⟨"lane", "lane", .naql, .wad, 0⟩ [⟨"m", "ibn-manzur", .naql, .wad, 1⟩]] ∧
    qashr (Itar.k "بِسْمِ") = [Itar.k "بِسْمِ", Itar.k "ءِسْمِ"] ∧
    qashr (Itar.k "وَلَاْ") = [Itar.k "وَلَاْ", Itar.k "لَاْ"] ∧
    harfKey (Itar.k "ءِلَاْ") = "ءلا" ∧ harfKey (Itar.k "ءِلْلَاْ") = "ءلا" := by
  decide +kernel

end A116.SilsilaFuru
