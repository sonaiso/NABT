import A116.Khawass
import A116.Haqaiq

/-!
# الحكمُ الموحَّد: حقيقة أو مجاز أو «لا حكم» من القابليّة الموروثة (ADR ١٠٢)

أمرُ المالك (2026-10-17): «دالّة قرار حقيقة/مجاز موحَّدة من القابليّة الموروثة (المقترح ٣): لم تُبنَ، موجودةٌ أجزاؤها
فقط … موافق على التنفيذ».

## الأجزاءُ القائمة، وما تجمعه هذه الدالّة

* `Qabil` (ADR ٩٥): الحقيقةُ ربطان (`Qabil.jam`): الصيغةُ على دورها، والمصدرُ على جنسٍ يقبله. والقابليّةُ صفٌّ مودَع.
* `Khawass` (ADR ٩٦): الجنسُ يحمل خواصّه، والمصدرُ يشترط خاصّةً في دوره. والوراثةُ درجةٌ واحدة (`isa`).
* `Majaz` (ADR ٩٤): لا مجازَ بلا وضعٍ أوّل ولا علاقةٍ عربيّة (س399، س415).
* `Haqaiq` (ADR ٩٢): المجازُ بقرينةٍ مانعة (س599).

## ما يُبنى

١. **القابليّةُ الموروثة** (`maurutha`): شجرةُ أجناس (أبُ كلّ جنس)، وقابليّةٌ محلّيّة (صفٌّ يذكر الجنسَ بعينه). والموروثةُ
   أوّلُ صفٍّ على سلسلة الجنس وآبائه.
   * الأخصُّ يغلب (`khass_yaghlib`).
   * وما لا صفَّ له يرث أباه (`yarith`).
   * ولا صفَّ على السلسلة فلا قابليّة (`la_saff`). وهذا عالمٌ مفتوح: الغيابُ ليس نفيًا.
٢. **الحكمُ الموحَّد** (`hukm`):
   * الصيغةُ والقابليّةُ الموروثة يحكمان بالأصل (`Qabil.jam`).
   * ثمّ ما خالف الأصلَ لا يكون مجازًا إلّا بوضعٍ أوّلٍ وعلاقةٍ عربيّة (`Majaz.imkanMajaz`).
   * وانتفاءُ القابليّة المودَعُ هو القرينةُ المانعة (ADR ٩٥: «وقد علم أنّ الضرب لا يُضرب»).
   * وما لم يستوفِ ذلك «لا حكم» باسمه، لا مجازٌ بالتخمين.
٣. **المثولات**:
   * `Qabil` بلا وراثة: الحكمُ الموحَّد يساويه حيث تقوم العلاقة (`qabil_mithal`).
   * و`Khawass.hukm` هو القابليّةُ الموروثة على شجرة `isa` بدرجة واحدة، على صفوفه كلِّها ومصادره وأدواره
     (`khawass_mithal`).
٤. **ما يصحّحه الجمع** (`dimagh_la_majaz`):
   * `Qabil` يحكم على «الدماغ ينعكس» بالمجاز لأنّ الصفَّ منفيّ.
   * والتفكير س14 ينفي القابليّةَ نفيًا، ولا علاقةَ مودَعة، فالموحَّدُ «لا حكم».
   * فالانتفاءُ وحدَه لا يكفي للمجاز (`la_majaz_bila_alaqa`).
-/

namespace A116.HukmMuwahhad

open A116.Majaz (Hukm Istimal imkanMajaz)
open A116.Qabil (Dawr jam)

/-! ## ١. القابليّةُ الموروثة -/

/-- شجرةُ الأجناس: أبُ كلّ جنس، أو لا أب. -/
abbrev Shajara := String → Option String

/-- سلسلةُ الوراثة: الجنسُ ثمّ آباؤه إلى عمق `n`. -/
def silsila (abb : Shajara) : Nat → String → List String
  | 0, j => [j]
  | n + 1, j => j :: match abb j with
    | some p => silsila abb n p
    | none => []

/-- القابليّةُ الموروثة: أوّلُ صفٍّ على السلسلة. -/
def maurutha (abb : Shajara) (n : Nat) (q : String → Option Bool) (j : String) : Option Bool :=
  (silsila abb n j).findSome? q

/-- **الأخصُّ يغلب**: صفُّ الجنس نفسِه يحكم ولو خالفه أبوه. -/
theorem khass_yaghlib (abb : Shajara) (n : Nat) (q : String → Option Bool) (j : String) (b : Bool)
    (h : q j = some b) : maurutha abb n q j = some b := by
  cases n <;> simp [maurutha, silsila, h]

/-- **الوراثة**: ما لا صفَّ له يرث أباه. -/
theorem yarith (abb : Shajara) (n : Nat) (q : String → Option Bool) (j p : String)
    (hj : q j = none) (hp : abb j = some p) : maurutha abb (n + 1) q j = maurutha abb n q p := by
  simp [maurutha, silsila, hj, hp]

/-- **لا صفَّ على السلسلة فلا قابليّة**: الغيابُ ليس نفيًا. -/
theorem la_saff (abb : Shajara) (n : Nat) (q : String → Option Bool) (j : String)
    (h : ∀ x ∈ silsila abb n j, q x = none) : maurutha abb n q j = none := by
  unfold maurutha
  generalize silsila abb n j = l at h
  induction l with
  | nil => rfl
  | cons x xs ih =>
    simp only [List.findSome?, h x List.mem_cons_self]
    exact ih (fun y hy => h y (List.mem_cons_of_mem _ hy))

/-! ## ٢. الحكمُ الموحَّد -/

/-- القابليّةُ حكمًا: ثبوتُها حقيقة، وانتفاؤها مجازٌ بالأصل، وغيابُها «لا حكم». -/
def ofQ : Option Bool → Hukm
  | some true => .haqiqa
  | some false => .majaz
  | none => .laHukm

/-- الحكمُ الموحَّد: الأصلُ من الصيغة والقابليّة الموروثة؛ وما خالف الأصلَ مجازٌ إن أمكن بوضعٍ وعلاقة، وإلّا «لا حكم».
وانتفاءُ القابليّة المودَعُ هو القرينةُ المانعة. -/
def hukm (abb : Shajara) (n : Nat) (q : String → Option Bool) (sigha : Hukm) (i : Istimal)
    (j : String) : Hukm :=
  match jam sigha (ofQ (maurutha abb n q j)) with
  | .haqiqa => .haqiqa
  | .laHukm => .laHukm
  | .majaz => if imkanMajaz i then .majaz else .laHukm

/-- **الحقيقةُ ⟺ الصيغةُ حقيقة والقابليّةُ الموروثة ثابتة**. -/
theorem haqiqa_iff (abb : Shajara) (n : Nat) (q : String → Option Bool) (s : Hukm) (i : Istimal)
    (j : String) :
    hukm abb n q s i j = .haqiqa ↔ s = .haqiqa ∧ maurutha abb n q j = some true := by
  unfold hukm
  cases hm : maurutha abb n q j with
  | none => cases s <;> simp [ofQ, jam]
  | some b =>
    cases b <;> cases s <;> simp [ofQ, jam] <;> split <;> simp

/-- **المجازُ ⟺ خلافُ الأصل بصيغةٍ أو قابليّةٍ معلومتين، ووضعٌ أوّلٌ وعلاقة**. -/
theorem majaz_iff (abb : Shajara) (n : Nat) (q : String → Option Bool) (s : Hukm) (i : Istimal)
    (j : String) :
    hukm abb n q s i j = .majaz ↔
      jam s (ofQ (maurutha abb n q j)) = .majaz ∧ imkanMajaz i = true := by
  unfold hukm
  cases hj : jam s (ofQ (maurutha abb n q j)) <;> cases imkanMajaz i <;> simp

/-- **لا مجازَ بلا علاقة** (س399): ولو انتفت القابليّة. -/
theorem la_majaz_bila_alaqa (abb : Shajara) (n : Nat) (q : String → Option Bool) (s : Hukm)
    (i : Istimal) (j : String) (h : i.alaqa = none) : hukm abb n q s i j ≠ .majaz := by
  intro hm
  have := ((majaz_iff abb n q s i j).mp hm).2
  simp [imkanMajaz, h] at this

/-- **ولا مجازَ بلا وضعٍ أوّل** (س415). -/
theorem la_majaz_bila_wad (abb : Shajara) (n : Nat) (q : String → Option Bool) (s : Hukm)
    (i : Istimal) (j : String) (h : i.wad = none) : hukm abb n q s i j ≠ .majaz := by
  intro hm
  have := ((majaz_iff abb n q s i j).mp hm).2
  simp [imkanMajaz, h] at this

/-- **لا حكمَ بلا صفٍّ على السلسلة**: الغيابُ لا يصير حقيقةً ولا مجازًا. -/
theorem la_hukm_bila_saff (abb : Shajara) (n : Nat) (q : String → Option Bool) (s : Hukm)
    (i : Istimal) (j : String) (h : ∀ x ∈ silsila abb n j, q x = none) :
    hukm abb n q s i j = .laHukm := by
  have hm := la_saff abb n q j h
  unfold hukm; rw [hm]
  cases s <;> rfl

/-- **المجازُ الموحَّد مجازٌ في `Majaz`**: بالقرينة المودَعة (انتفاءُ القابليّة) يوافق `Majaz.hukm`. -/
theorem majaz_mithal (abb : Shajara) (n : Nat) (q : String → Option Bool) (s : Hukm) (i : Istimal)
    (j : String) (h : hukm abb n q s i j = .majaz) : Majaz.hukm { i with qarina := true } = .majaz := by
  have := ((majaz_iff abb n q s i j).mp h).2
  have h2 : imkanMajaz { i with qarina := true } = true := this
  simp only [Majaz.hukm, h2]; rfl

/-! ## ٣. المثولات -/

/-- شجرةٌ بلا آباء. -/
def bilaAbb : Shajara := fun _ => none

/-- **`Qabil` بلا وراثة**: حيث تقوم العلاقةُ والوضع، الحكمُ الموحَّد هو `Qabil.jam` على صفوفه بعينه. -/
theorem qabil_mithal (rows : List Qabil.Saff) (m : String) (d : Dawr) (s : Hukm) (i : Istimal)
    (j : String) (hi : imkanMajaz i = true) :
    hukm bilaAbb 0 (fun x => (Qabil.lookup rows x m d).map (·.ijab)) s i j =
      jam s (Qabil.hukmQ rows j m d) := by
  have hq : ofQ (maurutha bilaAbb 0 (fun x => (Qabil.lookup rows x m d).map (·.ijab)) j) =
      Qabil.hukmQ rows j m d := by
    simp only [maurutha, silsila, List.findSome?]
    unfold Qabil.hukmQ
    cases hl : Qabil.lookup rows j m d with
    | none => rfl
    | some r => cases hr : r.ijab <;> simp [ofQ, hr]
  unfold hukm; rw [hq]
  cases hj : jam s (Qabil.hukmQ rows j m d) <;> simp [hi]

/-- شجرةُ `Khawass`: أبُ الجنس من صفّ `isa`. -/
def khawassAbb : Shajara := fun j =>
  match Khawass.saffOf j with
  | some ⟨_, _, .isa p, _, _⟩ => some p
  | _ => none

/-- قابليّةُ `Khawass` المحلّيّة لمصدرٍ في دوره: صفُّ الجنس نفسِه، لا صفُّ الوراثة. -/
def khawassQ (m : Khawass.Masdar) (d : Dawr) (j : String) : Option Bool :=
  match Khawass.saffOf j with
  | some ⟨_, _, .isa _, _, _⟩ => none
  | some r => match Khawass.shart m d with
    | some true => some r.aqil
    | some false => some true
    | none => none
  | none => none

def jinsKhawass : List String := Khawass.sufuf.map (·.jins) ++ ["الغول"]
def masadir : List Khawass.Masdar := [.khitab, .amr, .ikhbar, .nutq, .fahm, .sujud]

/-- **`Khawass.hukm` هو القابليّةُ الموروثة** على شجرة `isa` بدرجةٍ واحدة: على صفوفه كلِّها وجنسٍ بلا صفّ، ومصادره
الستّة، ودوريه (`decide`). -/
theorem khawass_mithal :
    jinsKhawass.all (fun j => masadir.all (fun m => [Dawr.faail, .mafool].all (fun d =>
      Khawass.hukm j m d == ofQ (maurutha khawassAbb 1 (khawassQ m d) j)))) = true := by
  decide +kernel

/-! ## ٤. الشواهد -/

/-- الاستعمالُ بوضعٍ أوّلٍ وعلاقةِ مشابهة: السيرافيّ س4162 «تشبيهًا» في «رأيتهم لي ساجدين». -/
def tashbih : Istimal := ⟨some "السجود لما يعقل", some .mushabaha, true⟩
/-- وبلا علاقةٍ مودَعة. -/
def bilaAlaqa : Istimal := ⟨some "الانعكاس في المرآة", none, true⟩

def qK (m : Khawass.Masdar) (d : Dawr) := khawassQ m d

/-- **الشواهد**:
* «سجد القمر» بالتشبيه مجاز، وبلا علاقة «لا حكم».
* «الكلبُ يُخاطَب» مجازٌ بالوراثة من «ذوات الأربع».
* «الإنسانُ يتكلّم» حقيقة.
* «الغول» لا صفَّ له، فـ«لا حكم» في كلّ حال. -/
theorem shawahid :
    hukm khawassAbb 1 (qK .sujud .faail) (Khawass.sighaLink .filMaloom .faail) tashbih "القمر" = .majaz ∧
    hukm khawassAbb 1 (qK .sujud .faail) (Khawass.sighaLink .filMaloom .faail) bilaAlaqa "القمر" = .laHukm ∧
    hukm khawassAbb 1 (qK .khitab .mafool) (Khawass.sighaLink .ismMafool .mafool) tashbih "الكلب" = .majaz ∧
    maurutha khawassAbb 1 (qK .khitab .mafool) "الكلب" = some false ∧
    hukm khawassAbb 1 (qK .khitab .faail) (Khawass.sighaLink .filMaloom .faail) tashbih "الإنسان" = .haqiqa ∧
    hukm khawassAbb 1 (qK .khitab .faail) (Khawass.sighaLink .filMaloom .faail) tashbih "الغول" = .laHukm := by
  decide +kernel

/-- **ما يصحّحه الجمع**: `Qabil` يحكم على «الدماغ ينعكس» بالمجاز لأنّ صفَّه منفيّ (التفكير س14). والموحَّدُ بلا علاقةٍ
مودَعة «لا حكم»، وفي «المرآة» حقيقةٌ كما في `Qabil`. -/
theorem dimagh_la_majaz :
    Qabil.hukmQ Qabil.sufuf "الدماغ" "انعكاس" .faail = .majaz ∧
    hukm bilaAbb 0 (fun x => (Qabil.lookup Qabil.sufuf x "انعكاس" .faail).map (·.ijab))
      .haqiqa bilaAlaqa "الدماغ" = .laHukm ∧
    hukm bilaAbb 0 (fun x => (Qabil.lookup Qabil.sufuf x "انعكاس" .faail).map (·.ijab))
      .haqiqa bilaAlaqa "المرآة" = .haqiqa := by decide

end A116.HukmMuwahhad
