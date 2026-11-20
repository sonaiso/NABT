import A116.Itar
import A116.Wazn
import A116.Wad

/-!
# قراءةُ المدلول من الكلمة: الصيغةُ من القالب، والجنسُ من الوضع، بلا تخمين (ADR ١٠٥)

أمرُ المالك (2026-10-18): «الخطوةَ التالية الأقربَ إلى الهدف فهي البند الأوّل: دالّةٌ تقرأ الجنس والصيغة من الكلمة عبر
الوضع والقرينة». كان المدلولُ في `Itar` مُعطًى كلُّه (`ITAR_MADLUL_FIELDS_ARE_INPUT`)؛ وهنا تُقرأ الصيغةُ والجنسُ والدورُ
من الخانات على معجمٍ شاهد. وما زال مُدخَلًا: قسمُ الكلمة، والاستعمال، وجدولُ المصدر، وربطُ الجذر بالجنس.

## ما يُبنى

١. **الصيغةُ** (`sigha`): مرشَّحوها أزواجُ (جذر، نوع) تكون الكلمةُ فيها تقييمَ قالبٍ على جذرٍ من الوضع (`Wazn.fillC`).
   * القوالب: الماضي المعلومُ والمجهولُ من جدول الأوزان المودَع (`Wazn.thulathi` الصفوف 0، 1، 2، 4، 11، 13)، واسما
     الفاعل والمفعول من الثلاثيّ (الألفيّة في شرح ابن عقيل المختوم س5653: «كفاعل صغ اسم فاعل … من ذى ثلاثة»،
     وس5691: «زنة مفعول»).
   * الجذورُ من الوضع وحدَه، فلا جذرَ من خارجه (`sigha_wad`).
   * آخرُ الاسم موضعُ الإعراب فلا تُطابَق حركتُه (`akhirEq`؛ `Amil`: أثرُ العامل في الموضع الأخير وحدَه)، وآخرُ الماضي
     مبنيٌّ على الفتح فيُطابَق (س368: «الماضي وهو مبني على الفتح»؛ والمجهولُ س3329: «فأول الفعل اضممن … بالآخر اكسر»،
     وواوُ فُوعِلَ س9355: «وفي ضارب ضورب»).
٢. **الجنسُ** (`jins`): الكلمةُ بلا أداة التعريف هيكلًا، فجذورُها من الوضع (هياكلُ ابن فارس)، فالجنسُ صفٌّ مودَعٌ لجذرها.
٣. **المصدرُ** (`masdarOf`): جذرُ الفعل ← مصدرٌ من مصادر `Khawass`، وما ليس فيها لا شرطَ له مودَعًا.
٤. **القراءةُ** (`qiraa`): فعلٌ ثمّ اسم. الدورُ من نوع الفعل لا مُدخَل: المعلومُ فاعلُه، والمجهولُ نائبُه مفعولٌ في
   المعنى (`dawr_min_naw`). والقابليّةُ شرطُ المصدر في دوره على الجنس الموروث. والقراءةُ لا تقوم إلّا والصيغةُ معيَّنة
   والجنسُ معيَّنٌ والمصدرُ مودَع (`qiraa_la_takhmin`).
٥. **الجسرُ إلى الإطار** (`hukmQ`): ما قُرئ مدلولُه حُكم بـ`Itar.hukm3` عليه بعينه (`hukmQ_qiraa`)، وما لم يُقرأ «لا حكم»
   والترخيصُ قائم (`hukmQ_bila_qiraa`).

## ما ليس هنا

* القرينةُ موضعُها قيودٌ في المعجم تقطع مرشَّحي الصيغة والجنس (`Mujam.qSigha`، `Mujam.qJins`؛ `qarina_la_tazid`). ولا
  قيدَ مودَعًا فيها بعد: قرينةُ المخصَّص بالعضويّة قيسَت فلم تُفِد (ADR ٥٩). فالمحتمَلُ يبقى محتمَلًا
  (`QARINA_NOT_DEPOSITED_HERE`).
* وربطُ جذر الجنس بالجنس (ءنس ← الإنسان) معلَن: `ajnas.tsv` بلا عمود جذر (`JIDHR_JINS_MAP_DECLARED`)، فكلُّ ما جذرُه
  ءنس يُقرأ جنسُه «الإنسان».
* الاستعمالُ (الوضعُ الأوّل والعلاقة) مُدخَل (`ALAQA_IS_INPUT`).
* أداةُ التعريف تُقشَّر بقاعدةٍ معلَنة (`RULE_AL_DECLARED`)، والقوالبُ ثمانيةٌ للثلاثيّ الصحيح وحدَه (`QAWALIB_EIGHT`).
* جذرُ الفعل إلى مصدره جدولٌ معلَن، ثلاثةُ صفوفٍ في الشاهد (`MASDAR_TABLE_DECLARED`).
-/

namespace A116.QiraaMadlul

open A116 A116.Wazn A116.Tarkib
open A116.Majaz (Istimal)
open A116.Qabil (Dawr)
open A116.Khawass (Naw Masdar)

/-! ## ١. الآخرُ والهيكل -/

/-- تطابقٌ إلّا حركةَ الآخر: الآخرُ موضعُ الإعراب. -/
def akhirEq : List Cell → List Cell → Bool
  | [], [] => true
  | [a], [b] => a.carrier == b.carrier
  | a :: as, b :: bs => a == b && akhirEq as bs
  | _, _ => false

/-- الهيكل: الحواملُ حروفًا، بلا حالات. -/
def haykal (w : List Cell) : String := String.ofList (w.map fun c => Field112.carrierChar c.carrier)

/-- أداةُ التعريف (`RULE_AL_DECLARED`): «ءَلْ» ابتداءً، و«لْ» وصلًا، والقمريّةُ المدغمةُ أوّلُ مثلين ساكنٌ وصلًا. -/
def stripAl : List Cell → List Cell
  | c :: d :: rest =>
    if c == ⟨Ladder.carrierOf 'ء', .fatha⟩ && d == ⟨Ladder.carrierOf 'ل', .sukun⟩ then rest
    else if c == ⟨Ladder.carrierOf 'ل', .sukun⟩ then d :: rest
    else if c.haraka == .sukun && c.carrier == d.carrier then d :: rest
    else c :: d :: rest
  | w => w

/-! ## ٢. الصيغة -/

/-- القالب: نوعُ الصيغة ووزنُها وحركةُ آخره — مبنيّةٌ معلومة، أو `none` لموضع الإعراب. -/
structure Qalib where
  naw : Naw
  wazn : WaznC 3
  akhir : Option Haraka

/-- صورةُ القالب على الجذر، وحركةُ الآخر لا تُقرأ. -/
def surat (q : Qalib) (r : String) : List Cell :=
  fillC q.wazn.body (Wad.ofStr3 r) ++ [⟨Wad.ofStr3 r q.wazn.last, q.akhir.getD .fatha⟩]

/-- المطابقة: تامّةٌ إن كان الآخرُ مبنيًّا، وإلّا إلّا حركةَ الآخر. -/
def yutabiq (q : Qalib) (r : String) (w : List Cell) : Bool :=
  if q.akhir.isSome then surat q r == w else akhirEq (surat q r) w

/-- مرشَّحو الصيغة: كلُّ (جذر، نوع) من الوضع والقوالب تقييمُه الكلمة. -/
def sighaCands (qs : List Qalib) (judhur : List String) (w : List Cell) : List (String × Naw) :=
  (qs.flatMap fun q => (judhur.filter fun r => yutabiq q r w).map fun r => (r, q.naw)).eraseDups

def sigha (qs : List Qalib) (judhur : List String) (w : List Cell) : Iqtiran.Mantuq (String × Naw) :=
  Iqtiran.mantuq (sighaCands qs judhur w)

/-- **السلامةُ والتمام**: المرشَّحُ ⟺ قالبٌ بنوعه وجذرٌ من الوضع تقييمُهما الكلمة. -/
theorem sighaCands_iff (qs : List Qalib) (judhur : List String) (w : List Cell) (r : String) (n : Naw) :
    (r, n) ∈ sighaCands qs judhur w ↔
      ∃ q ∈ qs, q.naw = n ∧ r ∈ judhur ∧ yutabiq q r w = true := by
  simp only [sighaCands, List.mem_eraseDups, List.mem_flatMap, List.mem_map, List.mem_filter,
    Prod.mk.injEq]
  constructor
  · rintro ⟨q, hq, r', ⟨hr, he⟩, rfl, rfl⟩; exact ⟨q, hq, rfl, hr, he⟩
  · rintro ⟨q, hq, rfl, hr, he⟩; exact ⟨q, hq, r, ⟨hr, he⟩, rfl, rfl⟩

/-- **لا جذرَ من خارج الوضع**. -/
theorem sigha_wad (qs : List Qalib) (judhur : List String) (w : List Cell) (r : String) (n : Naw)
    (h : sigha qs judhur w = .muayyan (r, n)) : r ∈ judhur := by
  have hl := Iqtiran.la_takhmin _ _ h
  have : (r, n) ∈ sighaCands qs judhur w := by rw [hl]; exact List.mem_singleton_self _
  obtain ⟨_, _, _, hr, _⟩ := (sighaCands_iff _ _ _ _ _).1 this
  exact hr

/-! ## ٣. الجنس -/

/-- الجنسُ: هيكلُ الكلمة بلا أداة ← جذورُها في الوضع ← الأجناسُ المودَعة لها. -/
def jinsCands (hayakil : List (String × List String)) (ajnas : List (String × String)) (w : List Cell) :
    List String :=
  let judhur := ((hayakil.find? (·.1 == haykal (stripAl w))).map (·.2)).getD []
  (ajnas.filter fun a => judhur.contains a.1).map (·.2) |>.eraseDups

def jins (hayakil : List (String × List String)) (ajnas : List (String × String)) (w : List Cell) :
    Iqtiran.Mantuq String :=
  Iqtiran.mantuq (jinsCands hayakil ajnas w)

/-- **لا جنسَ من خارج المودَع**. -/
theorem jins_mudaa (hy : List (String × List String)) (aj : List (String × String)) (w : List Cell)
    (g : String) (h : g ∈ jinsCands hy aj w) : ∃ r, (r, g) ∈ aj := by
  simp only [jinsCands, List.mem_eraseDups, List.mem_map, List.mem_filter] at h
  obtain ⟨⟨r, g'⟩, ⟨hm, _⟩, rfl⟩ := h
  exact ⟨r, hm⟩

/-- **هيكلٌ بلا وضعٍ لا جنسَ له**. -/
theorem jins_bila_wad (hy : List (String × List String)) (aj : List (String × String)) (w : List Cell)
    (h : hy.find? (·.1 == haykal (stripAl w)) = none) : jins hy aj w = .laHukm := by
  have : (aj.filter fun _ => false) = [] := by induction aj <;> simp_all [List.filter]
  simp [jins, jinsCands, h, this, Iqtiran.mantuq, List.eraseDups]

/-! ## ٤. القراءة -/

/-- الدورُ من نوع الفعل: المعلومُ يُسند إلى فاعله، والمجهولُ إلى نائبه وهو مفعولٌ في المعنى. -/
def dawrOf : Naw → Option Dawr
  | .filMaloom => some .faail
  | .filMajhul => some .mafool
  | _ => none

/-- **الدورُ مقروءٌ لا مُدخَل**. -/
theorem dawr_min_naw : dawrOf .filMaloom = some .faail ∧ dawrOf .filMajhul = some .mafool ∧
    dawrOf .ismFaail = none := ⟨rfl, rfl, rfl⟩

/-- المعجمُ: القوالبُ، والجذورُ، والهياكلُ، والأجناسُ، والمصادر. -/
structure Mujam where
  qawalib : List Qalib
  judhur : List String
  hayakil : List (String × List String)
  ajnas : List (String × String)
  masdarOf : String → Option Masdar
  qSigha : List (Iqtiran.Qayd (String × Naw)) := []
  qJins : List (Iqtiran.Qayd String) := []

/-- المقروء: المدلولُ والقابليّةُ التي يشترطها مصدرُه. -/
structure Maqru where
  madlul : Itar.Madlul
  masdar : Masdar
  dawr : Dawr

/-- **القراءة**: فعلٌ ثمّ اسم؛ والصيغةُ معيَّنة، والجنسُ معيَّن، والمصدرُ مودَع، والدورُ من النوع — وإلّا لا قراءة. -/
def qiraa (mj : Mujam) (i : Istimal) : Tarkib → Option Maqru
  | [f, s] =>
    match Iqtiran.mantuq (Iqtiran.iqtiran (sighaCands mj.qawalib mj.judhur f.cells) mj.qSigha),
      Iqtiran.mantuq (Iqtiran.iqtiran (jinsCands mj.hayakil mj.ajnas s.cells) mj.qJins) with
    | .muayyan (r, n), .muayyan g =>
      match mj.masdarOf r, dawrOf n with
      | some m, some d => some ⟨⟨g, Khawass.sighaLink n d, i⟩, m, d⟩
      | _, _ => none
    | _, _ => none
  | _ => none

/-- **لا تخمين**: ما قُرئ فصيغتُه وجنسُه معيَّنان بمرشَّحٍ واحدٍ بعد القرائن. -/
theorem qiraa_la_takhmin (mj : Mujam) (i : Istimal) (f s : Kalima) (q : Maqru)
    (h : qiraa mj i [f, s] = some q) :
    (∃ x, Iqtiran.iqtiran (sighaCands mj.qawalib mj.judhur f.cells) mj.qSigha = [x]) ∧
      Iqtiran.iqtiran (jinsCands mj.hayakil mj.ajnas s.cells) mj.qJins = [q.madlul.jins] := by
  simp only [qiraa] at h
  split at h
  · rename_i r n g h1 h2
    split at h
    · rename_i m d _ _
      cases h
      exact ⟨⟨(r, n), Iqtiran.la_takhmin _ _ h1⟩, Iqtiran.la_takhmin _ _ h2⟩
    · cases h
  · cases h

/-- **القرينةُ تقطع ولا تزيد**: كلُّ جنسٍ يبقى بعد قرينةٍ مضافة كان مرشَّحًا من الوضع قبلها. -/
theorem qarina_la_tazid (mj : Mujam) (r : Iqtiran.Qayd String) (w : List Cell) (g : String)
    (h : g ∈ Iqtiran.iqtiran (jinsCands mj.hayakil mj.ajnas w) (mj.qJins ++ [r])) :
    g ∈ Iqtiran.iqtiran (jinsCands mj.hayakil mj.ajnas w) mj.qJins :=
  Iqtiran.qayd_la_yazid _ _ r g h

/-- القابليّة: شرطُ المصدر في دوره على عقل الجنس الموروث من شجرة المخصَّص. -/
def qabiliyya (m : Masdar) (d : Dawr) (j : String) : Option Bool :=
  match Khawass.shart m d with
  | some true => AjnasMukhassas.aqil j
  | some false => some true
  | none => none

/-- **الحكمُ على الجملة من خاناتها**: ما قُرئ مدلولُه حُكم عليه بالإطار، وما لم يُقرأ «لا حكم» والترخيصُ قائم. -/
def hukmQ (mj : Mujam) (i : Istimal) (p : ExhaustPause.AWA) (t : Tarkib) : Itar.Natija :=
  match qiraa mj i t with
  | some q => Itar.hukm3 AjnasMukhassas.abb 1 (qabiliyya q.masdar q.dawr) p ⟨t, q.madlul⟩
  | none =>
    let tr := Itar.dal p (t.map Kalima.cells)
    ⟨tr, if tr then some .laHukm else none⟩

theorem hukmQ_qiraa (mj : Mujam) (i : Istimal) (p : ExhaustPause.AWA) (t : Tarkib) (q : Maqru)
    (h : qiraa mj i t = some q) :
    hukmQ mj i p t = Itar.hukm3 AjnasMukhassas.abb 1 (qabiliyya q.masdar q.dawr) p ⟨t, q.madlul⟩ := by
  simp [hukmQ, h]

/-- **بلا قراءةٍ «لا حكم»، والترخيصُ من الدالّ وحدَه**. -/
theorem hukmQ_bila_qiraa (mj : Mujam) (i : Istimal) (p : ExhaustPause.AWA) (t : Tarkib)
    (h : qiraa mj i t = none) (ht : Itar.dal p (t.map Kalima.cells) = true) :
    hukmQ mj i p t = ⟨true, some .laHukm⟩ := by
  simp [hukmQ, h, ht]

/-- **الترخيصُ لا يتغيّر بالقراءة**: ترخيصُ `hukmQ` ترخيصُ الدالّ نفسُه، قُرئ المدلولُ أو لم يُقرأ. -/
theorem tarkhis_qiraa (mj : Mujam) (i : Istimal) (p : ExhaustPause.AWA) (t : Tarkib) :
    (hukmQ mj i p t).tarkhis = Itar.dal p (t.map Kalima.cells) := by
  unfold hukmQ
  split <;> simp [Itar.hukm3]

/-! ## ٥. المعجمُ الشاهد

كلُّ صفٍّ هنا من مودَعٍ مختوم، ويفحصه `tests/test_qiraa_madlul.py`:
* الجذورُ والهياكلُ من معجم هياكل ابن فارس (`corpora/hadith/maqayis-skeletons.tsv`، ADR ٤٧).
* الأجناسُ من `corpora/mukhassas/ajnas.tsv` (ADR ١٠٤)، وجذرُ كلّ جنسٍ هيكلُه في معجم ابن فارس.
* المصادرُ: جذرُ كلّ مصدرٍ من مصادر `Khawass` (`MASDAR_TABLE_DECLARED`). -/

def cell (ch : Char) (h : Haraka) : Cell := ⟨Ladder.carrierOf ch, h⟩

/-- اسمُ الفاعل من الثلاثيّ: فَاعِل (س5653). -/
def faail : WaznC 3 := ⟨false, [.slot 0 .fatha, .lit (cell 'ا' .sukun), .slot 1 .kasra], 2⟩
/-- اسمُ المفعول من الثلاثيّ: مَفْعُول (س5691). -/
def mafool : WaznC 3 :=
  ⟨false, [.lit (cell 'م' .fatha), .slot 0 .sukun, .slot 1 .damma, .lit (cell 'و' .sukun)], 2⟩

def qawalib : List Qalib :=
  [0, 1, 2, 4].filterMap (fun i => (thulathi[i]?).map (⟨.filMaloom, ·, some .fatha⟩)) ++
  [11, 13].filterMap (fun i => (thulathi[i]?).map (⟨.filMajhul, ·, some .fatha⟩)) ++
  [⟨.ismFaail, faail, none⟩, ⟨.ismMafool, mafool, none⟩]

def mujamShahid : Mujam where
  qawalib := qawalib
  judhur := ["نطق", "خطب", "نبح", "فهم"]
  hayakil := [("ءنسان", ["ءنس"]), ("كلب", ["كلب"]), ("حجر", ["حجر"]), ("نمل", ["نمل"])]
  ajnas := [("ءنس", "الإنسان"), ("كلب", "الكلب"), ("حجر", "الحجر"), ("نمل", "النمل")]
  masdarOf := fun
    | "نطق" => some .nutq
    | "خطب" => some .khitab
    | "فهم" => some .fahm
    | _ => none

def kw (s : String) (q : Qism) : Kalima := ⟨Itar.k s, q⟩

def hQ (t : Tarkib) := hukmQ mujamShahid HukmMuwahhad.tashbih .wasl t

def hQbila (t : Tarkib) := hukmQ mujamShahid HukmMuwahhad.bilaAlaqa .wasl t

/-- **الشواهد** (`decide +kernel`): الصيغةُ والجنسُ والدورُ مقروءةٌ من الخانات على المعجم الشاهد، والقسمُ والاستعمالُ
مُعطَيان. و«مجاز» مشروطٌ بالاستعمال المُعطى (`HukmMuwahhad.tashbih`)، فبلا علاقةٍ مودَعة (`bilaAlaqa`) «لا حكم».
* «نَطَقَ»: صيغتُه فعلٌ معلوم من «نطق»؛ و«خُوطِبَ»: مجهولٌ من «خطب»؛ و«نَاطِقُ»: اسمُ فاعل (والتنوينُ ليس من الخانات)؛ و«نَطَقُ» بضمّ الآخر ليس ماضيًا.
* ودورُ «الْكَلْبُ» بعد «خُوطِبَ» مفعولٌ مقروءٌ من نوع الفعل.
* «الْإِنْسَانُ» جنسُه الإنسان، و«الْكَلْبُ» الكلب، و«الْغُولُ» لا حكم.
* «نَطَقَ الْإِنْسَانُ» حقيقة؛ «خُوطِبَ الْكَلْبُ» مجازٌ بالتشبيه؛ «نَطَقَ الْحَجَرُ» مجازٌ بالتشبيه، و«لا حكم» بلا علاقة.
* «نَبَحَ الْكَلْبُ» «لا حكم»: لا مصدرَ مودَعًا لـ«نبح»، فلا يُدّعى مجاز.
* «نَطَقَ الْغُولُ» «لا حكم»: لا جنس. والترخيصُ قائمٌ في الحالين. -/
theorem shawahid :
    sigha qawalib mujamShahid.judhur (Itar.k "نَطَقَ") = .muayyan ("نطق", .filMaloom) ∧
    sigha qawalib mujamShahid.judhur (Itar.k "خُوْطِبَ") = .muayyan ("خطب", .filMajhul) ∧
    sigha qawalib mujamShahid.judhur (Itar.k "نَاْطِقُ") = .muayyan ("نطق", .ismFaail) ∧
    sigha qawalib mujamShahid.judhur (Itar.k "نَطَقُ") = .laHukm ∧
    jins mujamShahid.hayakil mujamShahid.ajnas (Itar.k "لْءِنْسَاْنُ") = .muayyan "الإنسان" ∧
    jins mujamShahid.hayakil mujamShahid.ajnas (Itar.k "ءَلْكَلْبُ") = .muayyan "الكلب" ∧
    jins mujamShahid.hayakil mujamShahid.ajnas (Itar.k "لْغُوْلُ") = .laHukm ∧
    (qiraa mujamShahid HukmMuwahhad.tashbih [kw "خُوْطِبَ" .fil, kw "لْكَلْبُ" .ism]).map (·.dawr) =
      some .mafool ∧
    hQ [kw "نَطَقَ" .fil, kw "لْءِنْسَاْنُ" .ism] = ⟨true, some .haqiqa⟩ ∧
    hQ [kw "خُوْطِبَ" .fil, kw "لْكَلْبُ" .ism] = ⟨true, some .majaz⟩ ∧
    hQ [kw "نَطَقَ" .fil, kw "لْحَجَرُ" .ism] = ⟨true, some .majaz⟩ ∧
    hQbila [kw "نَطَقَ" .fil, kw "لْحَجَرُ" .ism] = ⟨true, some .laHukm⟩ ∧
    hQ [kw "نَبَحَ" .fil, kw "لْكَلْبُ" .ism] = ⟨true, some .laHukm⟩ ∧
    hQ [kw "نَطَقَ" .fil, kw "لْغُوْلُ" .ism] = ⟨true, some .laHukm⟩ := by
  decide +kernel

end A116.QiraaMadlul
