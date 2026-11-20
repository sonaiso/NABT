/-
  Nizam/Rabt.lean — ربطُ السلسلة على قراءة الجملة بالعوامل (`Jisr.Tahlil`): لكلّ قراءةٍ مرخَّصة جدولُ إعرابها (الدورُ والحالةُ والعامل)،
  ونِسَبُ أدوارها، وإسنادُها، وقوّتُها، وإحالةُ ضمائرها، وقيدُها ومفهومُها، ودلالةُ ألفاظها على جدول اللزوم.

  **الطلب:** قولُ المالك 2026-10-31 (ووقتُه 12:48 بتوقيت عمّان ولفظُه من ملخّص الجلسة بعد ضغطها): «… يوجد كود للعوامل لم يوظف … يوجد كود ياسر الإعراب لم
  يوظف يوجد كود للاسناد والمسند إليه لم يوظف الاسناد ولا التضمن ولا التقييد ويوجد كود للدلالة المطابقة ودلالة التضمن ودلالة ودلالة الالتزام لم
  توظف ويوجد كود للاحالة والاسماء المبنيات لم يوظف … وانت مفوض بالحل وليس التشخيص»؛ وفيه: «… واما الإيداع والختم يمكن عمل تحفظ ولكن نكمل
  العمل ونضع ملاحظة ان الجدول مثلا للرسم يحتاج ختم ولا نجعل كل شيء deffer …». والتصميمُ وتعييناتُه قرارُ البنّاء.

  **العُقَد** (كلٌّ على قطعةٍ قائمة في المشروع):
  1. **العامل** (`amilOf`): الجازمُ والناصبُ وحرفُ الجرّ صفوفُ جدول العوامل المختوم (`Awamil.table`، بصفّ الوحدة)؛ والمضارعُ بلا ناصبٍ ولا
     جازم مرفوعٌ بالتجرّد (القطر L96 «يرفع المضارع خاليا من ناصب وجازم»؛ الألفية L883 «رفع مضارعا إذا يجرد ... من ناصب وجازم»)؛ والفاعلُ
     بالفعل (القطر L220 «ولا يتأخر عامله عنه»، والألفية L312 «وبعد فعل فاعل»)، والمفعولُ به (الألفية L361 «فانصب به مفعوله»)؛ والمبتدأُ بالابتداء
     والخبرُ بالمبتدأ (الألفية L181 «ورفعوا مبتدأ بالابتدا ... كذاك رفع خبر بالمبتدا»)؛ والمضافُ إليه بالإضافة (القطر L339 «أو بإضافة إلى اسم»؛
     الألفية L508 «والثاني اجرر»)؛ والماضي والأمرُ مبنيّان (القطر L55، L59)، والحرفُ مبنيّ (القطر L71–72 «وجميع الحروف مبنية»).
  2. **الحالة** (`halaOf`): الحالةُ التي يطلبها موضعُ الوحدة في إطار المالك (`Tahlil.matlub`) وفي حالات خلاياها؛ والمقدَّرُ والمبنيُّ ومحلُّه؛
     والمضارعُ مع نون النسوة مبنيٌّ (القطر L67–68 «ويسكن آخره مع نون النسوة … ويعرب فيما عدا ذلك»)، وجعلُه في محلّ ما يطلبه موضعُه تعيينُ البنّاء.
  3. **النسبة** (`nisba`): تعيينُ `Jisr.Nisab.nisbaOf` على علاقات المالك (`Simat.semOf`) الذي أمضاه المالك 2026-10-16، والمضافُ إليه الإضافيّة
     (كـ`Nizam.Athar.nisbaDawr`).
  4. **الإسناد** (`isnadOf`): «هذا باب المسند والمسند إليه … فمن ذلك الاسم المبتدأ والمبنى عليه … ومثل ذلك يذهب عبد الله» (الكتاب س234–237):
     المسندُ الفعلُ أو الخبر، والمسندُ إليه الفاعلُ أو المبتدأ؛ والفاعلُ الضميرُ بارزٌ متّصل (لاحقةُ الفعل) أو مستتر — وجوبًا في المضارع للمتكلّم
     والمخاطب وجوازًا للغائب (القطر L124–125: «مستتر كالمقدر وجوبا في نحو "أقوم" و "تقوم" أو جوازا فشي [كذا] نحو "زيد يقوم"»)؛ ولاحقةُ المضارع
     ألفُ الاثنين وواوُ الجماعة ونونُ النسوة وياءُ المخاطبة (`lahiqaFail`)، فـ«نَكْتُبُ» فاعلُه مستترٌ وجوبًا (`shahid_mudari_damir`).
  5. **القوّة** (`quwwaOf`): من صفّ الصدر بعمود الأسلوب (`Nizam.Athar.quwwaSufuf`)؛ و«لن» و«لا» النافية نفيٌ **تعيينًا**: صورتاهما صورتا النفي في
     `Aql.Awwaliyyat.nafy` («لا يفعل» الكتاب س9786، و«لن يفعل» س9787)، ولا مبرهنةَ تصل `quwwaOf` بها (`nafy_suwar` مساواةُ نصّين). **وخلافٌ معلَن:**
     `Nizam.Athar.quwwaSufuf` يجعل صفَّ «لن» (63) «لا حكم» (أداةٌ لم يُبنَ أثرُها في القوّة)، فأداتا `athar` و`rabt` تختلفان في قوّة «لن يفعل».
     والأمرُ إنشاء (القطر L59: «ويعرف بدلالته على الطلب»)، وما سواها خبرٌ مثبت (`SakkJumla.awwal`).
  6. **الإحالة** (`ihalat`): ضميرُ المتكلّم والمخاطب إلى الحضور، والغائبُ إلى مرشَّحين قبله بمطابقة العدد (تعيينُ البنّاء: الجنسُ لا تحمله الحروف).
  7. **القيدُ والمفهوم** (`qaydR`، `mafahim`): عناصرُ البنية من الوحدات بأدوارها على `Jisr.QaydMafhum.unsurQayd` (الغايةُ من «إلى» حرفَ جرّ، والعددُ
     من المثنّى، والاسمُ من ذي الأداة ومن كلّ اسمٍ بلا أداةٍ ولا إضافة، ومنه العلمُ والمثنّى والجمع)، والجسرُ `Jisr.MantuqMafhum.jisr` بعد ربطه بالبنية (`bilBunya`)
     على ودائعَ تُعطى معاملًا. **والودائعُ المرشَّحة** (`wadaMurashshaha`) تحتاج ختمًا: الحملُ على الحقيقة اللغويّة لكلّ كلمةٍ جذرُها مشهود
     (`QawaninDalala.haml` بلا حقيقةٍ شرعيّةٍ ولا عرفيّةٍ مودَعة)، ولا خروجَ مخرجَ الأغلب، ولا نصَّ معطِّل. وعلى المختومة وحدها لا حملَ مودَعًا لكلمة،
     فلا يُخرج الجسرُ مفهومًا (`mafahim_makhtuma`، من `MantuqMafhum.la_mafhum_bila_haml`).
  8. **الدلالة** (`iddiaOf`): صفُّ جدول اللزوم (`JadwalLuzum.Saff`) ادّعاءٌ بسلسلته على قاعدة الجدول نفسِه (`JadwalLuzum.qaidaOf`): الترادفُ مطابقة،
     والجزءُ والأصلُ تضمّن، والتعليلُ التزام، والخارجُ مطابقةُ اللفظ لمعناه (لا صلتُه بما في عمود B). **وأصولُ السلسلة صفوفُ الجدول نفسِه** (`aslB T`)،
     فقبولُ `Qaida.maqbul` لها (`iddia_maqbul`، لكلّ جدولٍ وكلّ صفٍّ فيه) فحصٌ لشكل السلسلة لا لصدق الجدول؛ وصدقُها في النموذج بفرض صدق الأصول
     (`dalala_sadiqa`، فرضُ `hA`). والفاحصُ التنفيذيّ `faahis` لا يقبل أصلًا إلّا بسندٍ أوّلُه بصمةُ مودَعٍ مختوم، والجدولُ في `rabt`
     (`luzum_mujam.tsv`، `520dffc8…` في `mudaat/sijill.json`) مرشَّحٌ «يحتاج ختمًا»، ولا تفحص الأداةُ بصمتَه.

  **حدُّه:** العُقَدُ على القراءات المرخَّصة وحدها؛ والإحالةُ مرشَّحون لا تعيين؛ والودائعُ المرشَّحة فرضٌ معلَن؛ وجذرُ الاسم على أوزانٍ ثمانيةٍ تعيينًا،
  ومفاتيحُ الجذر في الجدول مرشَّحون من عنوانٍ مرمَّزٍ واوُه قد تكون همزةً أو ألفًا (`mafatih`): فـ«شَيْءٍ» مفاتيحُه «شوو» و«شءو» و«شوء» و«شيو» و«شيء»
  (`shahid_mafatih`)، ولا يُعيَّن منها شيء؛ وجذورُ الفعل جذورُ قراءته (`Wahda.judhurQ`، `shahid_lafif_jidhr`): كلُّ جذرٍ مشهودٍ على وزنها (ومع الواو
  بعد ضمّةٍ آخرَ الجذع ما لامُه واو إن شُهد)، فقد تكون أكثرَ من واحد («لَمْ يَعِدْ»: «عود» و«عيد»)؛ ولا جذرَ في السلسلة لقراءةٍ «محتمَلة» (لا تُرخِّص).

  **المبرهنات** بالمعيار الموحَّد (`Nizam/Asas.lean`): 38 — 26 لكلّ (§٩: `tayyT_hafiz`، `tayyT_dakhil`، `foldl_tayyT_hafiz`، `foldl_tayyT_tamm`،
  `maqbulaT_tamm`، `foldl_tayyT_min`، `maqbulaT_murakhkhas`، `maqbulaT_nil`، `hukmTafsir_laQiraa`، `siyaq_la_yatba_tartib`، `siyaq_shahid`؛ و`irabAux_tamm`، `irab_tamm`، `mem_irabAux`، `wahdaFi_mem`، `amilOf_fil`،
  `amil_fil_fi_jumla`، `hala_matluba`، `murashshah_mutabiq`، `mafhum_wahda`، `qanun_raqm`، `asl_sahih`، `iddia_maqbul`، `dalala_sadiqa`،
  `hamlWahda_qiyam`، `mafahim_makhtuma`)، و3 تعريفيّة (`isnad_fil`، `nafy_suwar`، `marji_hudur`)، و9 على الشاهد (`nisba_qiyam`، `shahid_lam`،
  `shahid_lamAmr`، `shahid_ismiyya`، `shahid_mudari_damir`، `shahid_ya`، `shahid_mafatih`، `shahid_lafif_jidhr`، `shahid_dalala`).
-/
import Jisr.Tahlil
import Nizam.Athar
import Madlul.JadwalLuzum
import Aql.SalamaMaqbul
import Jisr.QabiliyyaJins

namespace Nizam
namespace Rabt

open Jisr.Tahlil (Wahda Dawr Naw Murashshah)

/-! ## ١. الإعراب: الدورُ والحالةُ والعامل -/

inductive Amil
  /-- صفٌّ في جدول العوامل. -/
  | saff (i : Nat)
  /-- التجرّدُ من الناصب والجازم. -/
  | tajarrud
  /-- الفعلُ في الكلمة k. -/
  | fil (k : Nat)
  | ibtida
  /-- المبتدأُ في الكلمة k. -/
  | mubtada (k : Nat)
  /-- المضافُ في الكلمة k. -/
  | idafa (k : Nat)
  | bina
  | kharij
  deriving DecidableEq, Repr

inductive Hala
  /-- حالةٌ ظاهرةٌ تنفرد بها خلاياها. -/
  | zahira (h : Nat)
  /-- حالةٌ يطلبها الموضع، وعلامتُها مشتركةٌ بين الحالات hs. -/
  | mushtaraka (h : Nat) (hs : List Nat)
  | muqaddara
  /-- مبنيٌّ في محلّ h. -/
  | mahall (h : Nat)
  | mabni
  /-- حالاتُ الخلايا ولا يطلب الموضعُ حالة. -/
  | ghayrMatluba (hs : List Nat)
  | laHala
  deriving DecidableEq, Repr

structure Irab where
  wahda : Wahda
  dawr : Dawr
  hala : Hala
  amil : Amil
  deriving Repr

/-- الوحدةُ الأولى في دورٍ من أدوار المرشَّح. -/
def wahdaFi (m : Murashshah) (d : Dawr) : Option Wahda := (m.adwar.find? (·.2 == d)).map (·.1)

/-- الصدرُ الجازمُ أو الناصب. -/
def sadrOf (m : Murashshah) : Option Wahda := (m.adwar.find? fun p => p.2 == .jazim || p.2 == .nasib).map (·.1)

/-- عاملُ الفعل: المضارعُ بصفّ الصدر أو بالتجرّد، والماضي والأمرُ مبنيّان. -/
def amilFil (m : Murashshah) (w : Wahda) : Amil :=
  if w.sima.1 == 1 then
    match sadrOf m with
    | some s => match s.saff with | some i => .saff i | none => .kharij
    | none => .tajarrud
  else .bina

/-- **العامل** في الوحدة بدورها، و`prev` الوحدةُ قبلها في النطق (الجارُّ قبل المجرور، والمضافُ قبل المضاف إليه). -/
def amilOf (m : Murashshah) (prev : Option Wahda) (p : Wahda × Dawr) : Amil :=
  match p.2 with
  | .fil => amilFil m p.1
  | .fail => match wahdaFi m .fil with | some v => .fil v.kalima | none => .kharij
  | .maful => match wahdaFi m .fil with | some v => .fil v.kalima | none => .kharij
  | .mubtada => .ibtida
  | .khabar => match wahdaFi m .mubtada with | some v => .mubtada v.kalima | none => .kharij
  | .majrur => match prev with | some j => (match j.saff with | some i => .saff i | none => .kharij) | none => .kharij
  | .mudafIlayh => match prev with | some x => .idafa x.kalima | none => .kharij
  | .kharij => .kharij
  | _ => .bina

def khanaOf (m : Murashshah) (w : Wahda) : Option (Wahda × Option Nat × Nat) := m.khanat.find? (·.1 == w)

/-- المضارعُ مع نون النسوة (الغائباتُ والمخاطَبات): مبنيٌّ (القطر L67 «ويسكن آخره مع نون النسوة»)، وسمتُه عند المالك سمةُ المعرب
    (`Simat.slotAttrOK`)، فيُعرف هنا بسمته. -/
def nunNiswa (w : Wahda) : Bool := w.naw == .fil && w.sima.1 == 1 && w.sima.2.2.1.1 != 1 && w.sima.2.2.1.2 == (1, 2)

/-- **الحالة:** المقدَّرةُ «مقدَّرة»؛ والفعلُ المبنيّ مبنيّ، والاسمُ والضميرُ المبنيّان والمضارعُ مع نون النسوة في محلّ ما يطلبه موضعُه؛ والمعربُ بأوّل
    حالةٍ من حالات خلاياها يطلبها الموضع — ظاهرةً إن انفردت بها خلاياها، ومشتركةً إن احتملت غيرَها (المقصورُ والمنقوصُ والمضافُ إلى الياء والأمثلةُ
    الخمسة). -/
def halaOf (m : Murashshah) (w : Wahda) : Hala :=
  match khanaOf m w with
  | none => .laHala
  | some x =>
    let ms := Jisr.Tahlil.matlub m x
    if w.taqdir then .muqaddara
    else if w.sima.2.2.2 then (if w.naw == .fil then .mabni else match ms.head? with | some h => .mahall h | none => .mabni)
    else if nunNiswa w then (match ms.head? with | some h => .mahall h | none => .mabni)
    else match w.halat.find? (ms.contains ·) with
      | some h => if w.halat.length == 1 then .zahira h else .mushtaraka h w.halat
      | none => .ghayrMatluba w.halat

def irabAux (m : Murashshah) : Option Wahda → List (Wahda × Dawr) → List Irab
  | _, [] => []
  | prev, p :: r => ⟨p.1, p.2, halaOf m p.1, amilOf m prev p⟩ :: irabAux m (some p.1) r

/-- **جدولُ الإعراب** بترتيب النطق. -/
def irab (m : Murashshah) : List Irab := irabAux m none m.adwar

theorem irabAux_tamm (m : Murashshah) (prev : Option Wahda) (l : List (Wahda × Dawr)) :
    (irabAux m prev l).map (fun e => (e.wahda, e.dawr)) = l := by
  induction l generalizing prev with
  | nil => rfl
  | cons p r ih => simp only [irabAux, List.map_cons, ih]

/-- **الإعرابُ لا يُسقط وحدةً ولا يزيدها ولا يغيّر دورها.** -/
theorem irab_tamm (m : Murashshah) : (irab m).map (fun e => (e.wahda, e.dawr)) = m.adwar := irabAux_tamm m none m.adwar

theorem mem_irabAux (m : Murashshah) {prev : Option Wahda} {l : List (Wahda × Dawr)} {e : Irab} (h : e ∈ irabAux m prev l) :
    ∃ p ∈ l, ∃ q, e = ⟨p.1, p.2, halaOf m p.1, amilOf m q p⟩ := by
  induction l generalizing prev with
  | nil => cases h
  | cons p r ih =>
    simp only [irabAux, List.mem_cons] at h
    rcases h with h | h
    · exact ⟨p, List.mem_cons_self, prev, h⟩
    · obtain ⟨p', hp', q, he⟩ := ih h
      exact ⟨p', List.mem_cons_of_mem _ hp', q, he⟩

theorem wahdaFi_mem (m : Murashshah) (d : Dawr) {v : Wahda} (h : wahdaFi m d = some v) : (v, d) ∈ m.adwar := by
  unfold wahdaFi at h
  cases hf : m.adwar.find? (·.2 == d) with
  | none => rw [hf] at h; cases h
  | some x =>
    rw [hf] at h
    simp only [Option.map_some, Option.some.injEq] at h
    have hm := List.mem_of_find?_eq_some hf
    have hp := List.find?_some hf
    simp only [beq_iff_eq] at hp
    rw [← h, ← hp]
    exact hm

/-- إن كان العاملُ فعلًا في الكلمة k ففي المرشَّح فعلٌ في الكلمة k. -/
theorem amilOf_fil (m : Murashshah) (q : Option Wahda) (p : Wahda × Dawr) (k : Nat) (h : amilOf m q p = .fil k) :
    ∃ v, (v, Dawr.fil) ∈ m.adwar ∧ v.kalima = k := by
  unfold amilOf at h
  split at h
  · unfold amilFil at h
    split at h
    · split at h
      · split at h <;> cases h
      · cases h
    · cases h
  all_goals first
    | (cases hv : wahdaFi m .fil with
        | none => rw [hv] at h; cases h
        | some v => rw [hv] at h; cases h; exact ⟨v, wahdaFi_mem m .fil hv, rfl⟩)
    | (split at h <;> (try split at h) <;> cases h)
    | cases h

/-- **العاملُ الفعلُ فعلٌ في القراءة نفسِها:** كلُّ مدخلٍ في جدول الإعراب عاملُه فعلٌ في الكلمة k ففي المرشَّح فعلٌ في الكلمة k. -/
theorem amil_fil_fi_jumla (m : Murashshah) {e : Irab} (he : e ∈ irab m) {k : Nat} (ha : e.amil = .fil k) :
    ∃ v, (v, Dawr.fil) ∈ m.adwar ∧ v.kalima = k := by
  obtain ⟨p, _, q, rfl⟩ := mem_irabAux m he
  exact amilOf_fil m q p k ha

/-- **الحالةُ الظاهرةُ والمشتركة حالةٌ يطلبها الموضعُ ومن حالات الخلايا.** -/
theorem hala_matluba (m : Murashshah) (w : Wahda) {h : Nat} (hh : halaOf m w = .zahira h ∨ ∃ hs, halaOf m w = .mushtaraka h hs) :
    ∃ x ∈ m.khanat, x.1 = w ∧ h ∈ w.halat ∧ h ∈ Jisr.Tahlil.matlub m x := by
  unfold halaOf at hh
  cases hk : khanaOf m w with
  | none => rw [hk] at hh; simp at hh
  | some x =>
    rw [hk] at hh
    have hx := List.mem_of_find?_eq_some hk
    have hxw : x.1 = w := by simpa using List.find?_some hk
    dsimp only at hh
    by_cases ht : w.taqdir = true
    · simp [ht] at hh
    · simp only [ht, Bool.false_eq_true, ↓reduceIte] at hh
      by_cases hb : w.sima.2.2.2 = true
      · simp only [hb, ↓reduceIte] at hh
        revert hh
        split
        · simp
        · cases (Jisr.Tahlil.matlub m x).head? <;> simp
      · simp only [hb, Bool.false_eq_true, ↓reduceIte] at hh
        by_cases hn : nunNiswa w = true
        · simp only [hn, ↓reduceIte] at hh
          revert hh
          cases (Jisr.Tahlil.matlub m x).head? <;> simp
        simp only [hn, Bool.false_eq_true, ↓reduceIte] at hh
        split at hh
        · rename_i h' hf
          have hh' : h' = h := by
            by_cases hl : (w.halat.length == 1) = true
            · simp only [hl, ↓reduceIte] at hh
              rcases hh with hh | ⟨hs, hh⟩
              · exact Hala.zahira.inj hh
              · cases hh
            · simp only [hl, Bool.false_eq_true, ↓reduceIte] at hh
              rcases hh with hh | ⟨hs, hh⟩
              · cases hh
              · exact (Hala.mushtaraka.inj hh).1
          subst hh'
          have hc := List.find?_some hf
          exact ⟨x, hx, hxw, List.mem_of_find?_eq_some hf, by simpa using hc⟩
        · simp at hh

/-! ## ٢. النِّسَب والإسناد -/

/-- رمزُ الدور في أطر المالك. -/
def ramz : Dawr → Option Nat
  | .mubtada => some 0 | .khabar => some 1 | .fil => some 2 | .fail => some 3 | .maful => some 4
  | .harfJarr => some 5 | .majrur => some 6 | _ => none

/-- **نسبةُ الدور** على علاقات المالك، والمضافُ إليه الإضافيّة. -/
def nisba (d : Dawr) : Option Jisr.Nisab.Nisba :=
  match d with
  | .mudafIlayh => some .idafiyya
  | _ => (ramz d).bind fun r => Jisr.Nisab.nisbaOf (SLGE.Simat.semOf r)

/-- المبتدأُ والخبرُ والفعلُ والفاعلُ إسناديّة، والمفعولُ تقييديّ، والمجرورُ والمضافُ إليه إضافيّان، والحروفُ عواملُ بلا نسبة. -/
theorem nisba_qiyam :
    [Dawr.mubtada, .khabar, .fil, .fail, .maful, .harfJarr, .majrur, .mudafIlayh, .rabit, .jazim, .nasib, .nafiya, .kharij].map nisba =
      [some .isnadiyya, some .isnadiyya, some .isnadiyya, some .isnadiyya, some .taqyidiyya, none, some .idafiyya, some .idafiyya,
       none, none, none, none, none] := by
  decide

inductive Sura | zahir | bariz | mustatar
  deriving DecidableEq, Repr

/-- الإسناد: المسندُ (الفعلُ أو الخبر؛ و`none` شبهُ الجملة خبرًا)، والمسندُ إليه الظاهر (أو لا شيء والفاعلُ ضمير)، وصورتُه، وسماتُه، والاستتارُ
    وجوبًا أو جوازًا (في المضارع وحده). -/
structure Isnad where
  musnad : Option Wahda
  ilayh : Option Wahda
  sura : Sura
  ft : SLGE.Maqam.Feat
  wujub : Option Bool
  deriving Repr

/-- لاحقةُ الفعل ضميرُ رفعٍ بارز: الماضي بغير الغائب المفرد وتاء التأنيث، والمضارعُ بألف الاثنين وواو الجماعة ونون النسوة وياء المخاطبة (لا المتكلّم:
    «نَكْتُبُ» بلا لاحقة)، والأمرُ بغير المفرد المذكّر. -/
def lahiqaFail (v : Wahda) : Bool :=
  let ft := v.sima.2.2.1
  if v.sima.1 == 0 then !(ft == (3, 0, 0) || ft == (3, 1, 0))
  else if v.sima.1 == 1 then (ft.1 != 1 && ft.2.2 != 0) || ft == (2, 1, 0)
  else ft != (2, 0, 0)

def isnadOf (m : Murashshah) : Option Isnad :=
  match wahdaFi m .fil with
  | some v =>
    match wahdaFi m .fail with
    | some f => some ⟨some v, some f, .zahir, f.sima.2.2.1, none⟩
    | none =>
      let ft := v.sima.2.2.1
      if lahiqaFail v then some ⟨some v, none, .bariz, ft, none⟩
      else some ⟨some v, none, .mustatar, ft, if v.sima.1 == 1 then some (decide (ft.1 ≤ 2)) else none⟩
  | none =>
    match wahdaFi m .mubtada with
    | some mb => some ⟨wahdaFi m .khabar, some mb, .zahir, mb.sima.2.2.1, none⟩
    | none => none

/-- **في كلّ إسنادٍ فعليٍّ المسندُ هو الفعل،** والمسندُ إليه الظاهرُ إن كان هو الفاعل. -/
theorem isnad_fil (m : Murashshah) (v : Wahda) (hv : wahdaFi m .fil = some v) {i : Isnad} (hi : isnadOf m = some i) :
    i.musnad = some v ∧ i.ilayh = wahdaFi m .fail := by
  unfold isnadOf at hi
  rw [hv] at hi
  simp only at hi
  cases hf : wahdaFi m .fail with
  | some f => rw [hf] at hi; cases hi; exact ⟨rfl, rfl⟩
  | none =>
    rw [hf] at hi
    simp only at hi
    split at hi <;> cases hi <;> exact ⟨rfl, rfl⟩

/-! ## ٣. القوّة -/

open Jisr.SakkJumla (Quwwa)

/-- **قوّةُ القراءة** بسندها. -/
def quwwaOf (m : Murashshah) : Quwwa × String :=
  match m.adwar.find? (fun p => p.2 == .jazim || p.2 == .nasib || p.2 == .nafiya) with
  | some (s, d) =>
    if d == .nafiya then (.nafy, "«لا» نافيةً: «لا يفعل» صورةُ نفي المستقبل (Aql.Awwaliyyat.nafy؛ الكتاب س9786) — تعيين")
    else match s.saff with
      | some 63 => (.nafy, "«لن»: «لن يفعل» صورةُ نفي المستقبل المنفَّس (Aql.Awwaliyyat.nafy؛ الكتاب س9787) — تعيين، وفي Nizam.Athar «لا حكم»")
      | some i => (Nizam.Athar.quwwaSufuf [i], "صفّ الجدول " ++ toString i ++ " بعمود الأسلوب (Nizam.Athar.quwwaSufuf)")
      | none => (.laHukm, "صدرٌ بلا صفّ")
  | none =>
    match wahdaFi m .fil with
    | some v =>
      if v.sima.1 == 2 then (.insha, "الأمرُ «بدلالته على الطلب» (القطر L59)")
      else (Jisr.SakkJumla.awwal ⟨.laShay, .laQawl, .laQawl, .amma⟩, "لا أداةَ في الصدر (Jisr.SakkJumla.awwal)")
    | none => (Jisr.SakkJumla.awwal ⟨.laShay, .laQawl, .laQawl, .amma⟩, "لا أداةَ في الصدر (Jisr.SakkJumla.awwal)")

/-- صورتا النفي في الأزمنة الخمسة: «لا يفعل» للمستقبل و«لن يفعل» للمنفَّس (`Aql.Awwaliyyat.nafy`). مساواةُ نصّين، لا تصل `quwwaOf` بهما. -/
theorem nafy_suwar : Aql.Awwaliyyat.nafy .mustaqbal = "لا يفعل" ∧ Aql.Awwaliyyat.nafy .mustaqbalMunaffas = "لن يفعل" := ⟨rfl, rfl⟩

/-! ## ٤. الإحالة -/

inductive Marji
  | hudur
  /-- مرشَّحون: (الجملة، الكلمة)، الأقربُ أوّلًا. -/
  | murashshahun (l : List (Nat × Nat))
  deriving DecidableEq, Repr

structure Ihala where
  kalima : Nat
  sura : Sura
  ft : SLGE.Maqam.Feat
  marji : Marji
  deriving Repr

/-- قيدُ السياق: (الجملة، الكلمة، العدد) — اسمٌ ظاهرٌ شهدت له قراءةٌ مقبولة (`siyaqJumla`)، لا وحدةُ قراءةٍ بعينها. -/
abbrev Siyaq := List (Nat × Nat × Nat)

/-- المرشَّحون للغائب: الأسماءُ الظاهرة قبله بعدده، الأقربُ أوّلًا (تعيين). -/
def murashshahunIhala (qabl : Siyaq) (ft : SLGE.Maqam.Feat) : List (Nat × Nat) :=
  ((qabl.filter fun p => p.2.2 == ft.2.2).map fun p => (p.1, p.2.1)).reverse

def marjiOf (qabl : Siyaq) (ft : SLGE.Maqam.Feat) : Marji :=
  if ft.1 ≤ 2 then .hudur else .murashshahun (murashshahunIhala qabl ft)

/-- **الإحالات في القراءة** `m` من الجملة `j`، و`qabl` أسماءُ ما قبلها: الفاعلُ الضميرُ (بارزًا أو مستترًا)، والضمائرُ المتّصلة المنصوبةُ والمجرورة. -/
def ihalat (qabl : Siyaq) (j : Nat) (m : Murashshah) : List Ihala :=
  let fail := match isnadOf m with
    | some i => match i.sura, i.musnad with
      | .zahir, _ => []
      | s, some v => [⟨v.kalima, s, i.ft, marjiOf qabl i.ft⟩]
      | _, none => []
    | none => []
  let damair := (List.range m.adwar.length).filterMap fun n =>
    match m.adwar[n]? with
    | some (w, _) =>
      if w.naw == .damir then
        let qablFi := (m.adwar.take n).filterMap fun p =>
          if p.1.naw == .ism && p.1.kalima != w.kalima then some (j, p.1.kalima, p.1.sima.2.2.1.2.2) else none
        some ⟨w.kalima, .bariz, w.sima.2.2.1, marjiOf (qabl ++ qablFi) w.sima.2.2.1⟩
      else none
    | none => none
  fail ++ damair

/-- **ضميرُ المتكلّم والمخاطب يحيل إلى الحضور** (والغائبُ إلى مرشَّحين بعدده: `murashshah_mutabiq`). -/
theorem marji_hudur (qabl : Siyaq) (ft : SLGE.Maqam.Feat) (h : ft.1 ≤ 2) : marjiOf qabl ft = .hudur := by
  unfold marjiOf; simp [h]

/-- **كلُّ مرشَّحٍ قيدٌ في السياق بعدد الضمير** (وشهودُ القيد في `siyaq_shahid`). -/
theorem murashshah_mutabiq (qabl : Siyaq) (ft : SLGE.Maqam.Feat) {p : Nat × Nat}
    (hp : p ∈ murashshahunIhala qabl ft) : (p.1, p.2, ft.2.2) ∈ qabl := by
  unfold murashshahunIhala at hp
  rw [List.mem_reverse, List.mem_map] at hp
  obtain ⟨⟨a, k, n⟩, hm, he⟩ := hp
  rw [List.mem_filter] at hm
  simp only [beq_iff_eq] at hm
  cases he
  rw [← hm.2]
  exact hm.1

/-! ## ٥. القيدُ والمفهوم -/

open Jisr.QaydMafhum (Unsur unsurQayd)
open Jisr.MantuqMafhum (Qayd sinfOf Mudaa Mafhum jisr)

/-- عناصرُ البنية من الوحدة بدورها: حرفُ الجرّ بصفّه، والاسمُ مثنًّى (بابُ المثنّى) وبـ«ال» (ذو الأداة، المعرفةُ الخامسة)، وبلا «ال» ولا إضافة
    اسمَ جنس (`Unsur.ismJins`؛ ومنه العلمُ المنوَّن، إذ العلميّةُ لا تحملها الحروف — تعيين). -/
def anasirWahda (w : Wahda) (d : Dawr) : List Unsur :=
  (if d == .harfJarr then (match w.saff with | some i => [Unsur.adat i] | none => []) else []) ++
  (if w.naw == .ism then
     (if w.sima.2.2.1.2.2 == 1 then [Unsur.bab .muthanna] else []) ++
     (if w.sima.2.1 == 1 then [Unsur.marifa 4] else if !w.idafa then [Unsur.ismJins] else [])
   else [])

def bunyaR (m : Murashshah) : List Unsur := m.adwar.flatMap fun p => anasirWahda p.1 p.2

def qaydat (m : Murashshah) : List (Qayd × Wahda) :=
  m.adwar.flatMap fun p => (anasirWahda p.1 p.2).filterMap fun u => (unsurQayd u).map (·, p.1)

/-- **قيدُ القراءة** بـ`Nizam.Athar.qaydMin`: أوّلُ قيدٍ له صنفُ مخالفة، وإلّا أوّلُ قيد. -/
def qaydR (m : Murashshah) : Option (Qayd × Wahda) := Nizam.Athar.qaydMin (qaydat m)

structure Wada where
  haml : List QawaninDalala.Mahmul
  aghlab : Bool
  muattil : Bool
  deriving Repr

def mudaaR (m : Murashshah) (W : Wada) : Mudaa Unit (Qayd × Nat) where
  kalimat := fun _ => W.haml
  qayd := fun _ => (qaydR m).map (·.1)
  mufhim := fun _ => false
  siyaqAdad := fun _ => false
  innama := fun _ => false
  aghlab := fun _ => W.aghlab
  muattil := fun _ => W.muattil
  naqid := fun _ => (qaydR m).map fun p => (p.1, p.2.kalima)
  muwafiq := fun _ => []
  iqtida := fun _ => []
  tanbih := fun _ => []
  ishara := fun _ => []

/-- **المفهوم:** جسرُ `MantuqMafhum` على المودَع بعد ربطه ببنية القراءة. -/
def mafahim (m : Murashshah) (W : Wada) : List (Mafhum Unit (Qayd × Nat)) :=
  jisr (Jisr.QaydMafhum.bilBunya (mudaaR m W) (fun _ => bunyaR m)) [()]

/-- **كلُّ مفهومِ مخالفةٍ تحمله وحدةٌ في دورها:** قيدُه يشهد له عنصرٌ من بنية وحدةٍ في القراءة (`QaydMafhum.mukhalafa_mashuda`). -/
theorem mafhum_wahda (m : Murashshah) (W : Wada) {f : Mafhum Unit (Qayd × Nat)} {k : SLGE.Madlul.Mukhalafa}
    (h : f ∈ mafahim m W) (hk : f.naw = .mukhalafa k) :
    ∃ p ∈ m.adwar, ∃ u ∈ anasirWahda p.1 p.2, ∃ q, unsurQayd u = some q ∧ sinfOf q = some k := by
  obtain ⟨q, u, _, hs, hu, hq⟩ := Jisr.QaydMafhum.mukhalafa_mashuda (mudaaR m W) (fun _ => bunyaR m) h hk
  simp only [bunyaR, List.mem_flatMap] at hu
  obtain ⟨p, hp, hu⟩ := hu
  exact ⟨p, hp, u, hu, q, hq, hs⟩

/-! ## ٦. الجذرُ والدلالة -/

open Jisr.Tahlil (Q Wazn wazn judhur mashhud kh)

/-- **أوزانُ جذع الاسم** (تعيينُ البنّاء): فَعْل وفَعَل وأخواتُهما، وفاعِل، وفَعال وفَعِيل وفَعُول، ومَفْعَل، ومَفْعُول، ومُفَعِّل. -/
def awzanIsm : List Wazn :=
  [([.any, .any, .any], [0, 1, 2]), ([.v, .h (kh 2 3), .v, .any], [0, 2, 3]),
   ([.v, .v, .h (kh 2 3), .any], [0, 1, 3]), ([.v, .v, .h (kh 11 3), .any], [0, 1, 3]), ([.v, .v, .h (kh 28 3), .any], [0, 1, 3]),
   ([.h (kh 27 0), .s, .v, .any], [1, 2, 3]), ([.h (kh 27 0), .s, .v, .h (kh 28 3), .any], [1, 2, 4]),
   ([.h (kh 27 1), .v, .sx, .v, .any], [1, 2, 4])]

/-- جذعُ الاسم: بلا «ال» ولا تنوين ولا علامة التثنية والجمع. -/
def jidhIsm (w : Wahda) : List Nat :=
  let a := if w.sima.2.1 == 1 then w.khalaya.drop 1 else w.khalaya
  let b := if a.getLast? == some 59 then a.dropLast else a
  if w.sima.2.2.1.2.2 != 0 then b.take (b.length - (if w.idafa then 1 else 2)) else b

def mashhudat (ws : List Wazn) (b : List Nat) : List (List Nat) :=
  ws.flatMap fun (p, ms) => if wazn b p then (judhur b ms).filter mashhud else []

/-- **جذورُ الوحدة المشهودة في عناوين اللسان:** الفعلُ بجذور قراءته وحدها (`Wahda.judhurQ`: كلُّ جذرٍ مشهودٍ على وزنها وجذعها — ومع الواو بعد ضمّةٍ
آخرَه ما لامُه واو إن شُهد: `Jisr.Tahlil.judhurFil` —، فلـ«يُرُونَ» «رءي» لا «روي»، ولـ«لَمْ يَعِدْ» الأجوفُ «عود» و«عيد»: `shahid_lafif_jidhr`)، وفعلٌ
بلا قراءة (`judhurQ = none`) لا جذرَ له، ووحداتُ الفعل التي يبنيها القارئ (`Jisr.Tahlil.filQiraat`) تحمل قراءتها بالبناء (قراءةُ البنّاء للشفرة، بلا
مبرهنة)؛ والاسمُ بأوزانه. -/
def judhurWahda (w : Wahda) : List (List Nat) :=
  (match w.naw with
   | .fil => w.judhurQ.getD []
   | .ism => mashhudat awzanIsm (jidhIsm w)
   | _ => []).eraseDups

def harf (c : Nat) : Char := Dal.hawamil.getD c ' '

/-- الجذرُ نصًّا بحروف عناوين المعجم (`shabaka/jadwal_luzum.py` R1: الهمزةُ «ء»). -/
def jidhrNass (r : List Nat) : String := String.ofList (r.map harf)

/-- **مفاتيحُ الجذر في جدول اللزوم:** الجذرُ `r` عنوانٌ مرمَّزٌ مشهود في اللسان (`judhurWahda`)، والواوُ فيه قد تكون واوًا أو همزةً أو ألفًا
    (`Tahlil.asl`: «الهمزةُ همزةٌ أو ألف»، والألفُ في العنوان تُرمَّز واوًا)؛ وعنوانُ الجدول بالهمزة (`shabaka/jadwal_luzum.py` R1). فإن كان في
    خلايا الوحدة همزةٌ فالمفاتيحُ `r` وكلُّ صورةٍ منه بهمزةٍ مكانَ واوٍ واحدة. وكلُّ مفتاحٍ مرشَّحُ جذر، لا تعيين. -/
def mafatih (w : Wahda) (r : List Nat) : List String :=
  (if w.khalaya.any (· / 4 == 0) then
     [r] ++ (List.range r.length).filterMap (fun i => if r[i]? == some 28 then some (r.set i 0) else none)
   else [r]).eraseDups.map jidhrNass

open JadwalLuzum QawaninDalala

def raqmT (T : List Saff) (q : Qaida.Qanun Qadiyya) : Nat := (qaidaOf T).qawanin.idxOf q

/-- **ادّعاءُ الصفّ بسلسلته** على قاعدة الجدول: الترادفُ مطابقة، والجزءُ والأصلُ تضمّن، والتعليلُ التزام، والخارجُ مطابقةُ مدلول اللفظ. -/
def iddiaOf (T : List Saff) (r : Saff) : Qaida.Iddia Qadiyya :=
  let l := ism T (lafz r); let m := ism T (maana r); let b := ism T r.b
  match r.naw with
  | .taraduf => ⟨.mutabaqa l b, [.asl (.wad l b), .qanun (raqmT T (qMutabaqa l b))]⟩
  | .juz | .asl => ⟨.tadammun l b, [.asl (.wad l m), .qanun (raqmT T (qMutabaqa l m)), .asl (.juz b m),
      .qanun (raqmT T (qTadammun l m b))]⟩
  | .luzum => ⟨.iltizam l b, [.asl (.wad l m), .qanun (raqmT T (qMutabaqa l m)), .asl (.kharij b m), .asl (.luzum m b),
      .qanun (raqmT T (qIltizam l m b))]⟩
  | .kharij => ⟨.mutabaqa l m, [.asl (.wad l m), .qanun (raqmT T (qMutabaqa l m))]⟩

theorem qanun_raqm (T : List Saff) (r : Saff) (hr : r ∈ T) {q : Qaida.Qanun Qadiyya} (hq : q ∈ qawaninOf T r) :
    (qaidaOf T).qawanin[raqmT T q]? = some q := by
  have hm : q ∈ (qaidaOf T).qawanin := List.mem_flatMap.mpr ⟨r, hr, hq⟩
  have hl := List.idxOf_lt_length_of_mem hm
  unfold raqmT
  rw [List.getElem?_eq_getElem hl, List.getElem_idxOf hl]

theorem asl_sahih (T : List Saff) (r : Saff) (hr : r ∈ T) {p : Qadiyya} (hp : p ∈ aslOf T r) : aslB T p = true :=
  (aslB_iff T p).mpr ⟨r, hr, hp⟩

/-- **كلُّ ادّعاءٍ من صفٍّ يقبله `Qaida.maqbul` على قاعدة جدوله وأصولُها صفوفُه**، لكلّ جدولٍ ولكلّ صفٍّ فيه: فحصٌ لشكل السلسلة لا لصدق الجدول. -/
theorem iddia_maqbul (T : List Saff) (r : Saff) (hr : r ∈ T) : Qaida.maqbul (qaidaOf T) (aslB T) (iddiaOf T r) = true := by
  unfold iddiaOf
  cases hn : r.naw <;>
  · simp only [Qaida.maqbul, Qaida.fahs, Qaida.tatbiq]
    have hA : ∀ p ∈ aslOf T r, aslB T p = true := fun p hp => asl_sahih T r hr hp
    have hQ : ∀ q ∈ qawaninOf T r, (qaidaOf T).qawanin[raqmT T q]? = some q := fun q hq => qanun_raqm T r hr hq
    simp only [aslOf, qawaninOf, hn, List.mem_cons, List.not_mem_nil, or_false, forall_eq_or_imp, forall_eq] at hA hQ
    simp only [hA, hQ, ite_true]
    simp [qMutabaqa, qTadammun, qIltizam]

/-- **والادّعاءُ صادقٌ في النموذج** بفروض `QawaninDalala.salama`: الأصولُ صادقة (`hA`، نقلٌ يُراجَع)، والاحتواءُ متعدٍّ. -/
theorem dalala_sadiqa {L α : Type} (W : Dalala.Wad L α) (Z : Dalala.Luzum α) (lf : Nat → L) (mn : Nat → Dalala.Maana α)
    (Fi Taht : Nat → Nat → Prop) (T : List Saff) (r : Saff) (hr : r ∈ T)
    (hA : ∀ a, aslB T a = true → tafsir W Z lf mn Fi Taht a)
    (htadiya : ∀ z c p, Taht z c → Fi c p → Taht z p) :
    tafsir W Z lf mn Fi Taht (iddiaOf T r).qawl :=
  SalamaMaqbul.maqbul_sadiq W Z lf mn Fi Taht (qaidaOf T) (aslB T) (iddiaOf T r) (qaidaOf_shakl T) hA htadiya
    (iddia_maqbul T r hr)

/-! ## ٧. الودائعُ المرشَّحة (تحتاج ختمًا) -/

/-- حملُ الكلمة: حقيقةٌ لغويّة إن شُهد جذرُها، بلا حقيقةٍ شرعيّةٍ ولا عرفيّةٍ مودَعة (مرشَّح)؛ وإلّا «لا حكم». -/
def hamlWahda (w : Wahda) : Mahmul :=
  haml .la .la (if !(judhurWahda w).isEmpty && !w.taqdir then .naam else .ghayr) false none false

def wadaMurashshaha (m : Murashshah) : Wada :=
  ⟨(m.adwar.filter fun p => p.1.naw == .fil || p.1.naw == .ism).map (hamlWahda ·.1), false, false⟩

/-- الحملُ المرشَّح حقيقةٌ لغويّةٌ أو «لا حكم»، لا مجازٌ ولا اشتراك. -/
theorem hamlWahda_qiyam (w : Wahda) : hamlWahda w = .haqiqa .lughawiyya ∨ hamlWahda w = .laHukm := by
  unfold hamlWahda
  split <;> decide

/-- **الودائعُ على المختومة وحدها:** لا حملَ مودَعًا لكلمة («لا حكم» لكلّ كلمة)، ولا أغلبَ ولا معطِّل. -/
def wadaMakhtuma (m : Murashshah) : Wada :=
  ⟨(wadaMurashshaha m).haml.map fun _ => .laHukm, false, false⟩

/-- **وعلى المختومة وحدها لا مفهوم** ما دامت في القراءة كلمةٌ فعلٌ أو اسم (`MantuqMafhum.la_mafhum_bila_haml`). -/
theorem mafahim_makhtuma (m : Murashshah) (h : (wadaMurashshaha m).haml ≠ []) : mafahim m (wadaMakhtuma m) = [] := by
  unfold mafahim
  simp only [Jisr.MantuqMafhum.jisr, List.flatMap_cons, List.flatMap_nil, List.append_nil]
  apply Jisr.MantuqMafhum.la_mafhum_bila_haml
  obtain ⟨a, l, hl⟩ := List.exists_cons_of_ne_nil h
  simp [Jisr.MantuqMafhum.mahmul, Jisr.QaydMafhum.bilBunya, mudaaR, wadaMakhtuma, hl]

/-! ## ٨. الشواهد -/

open Jisr.Tahlil (lamW yaktubJ zaydun falyaktub wallahu bikulli shayin alimun naktubuW yaktubnaW murashshahun hukmM)

/-- القراءاتُ المرخَّصة بلا تكرار أدوار. -/
def maqbula (ws : List Dal.Kalima) : List Murashshah :=
  ((murashshahun ws).filter fun m => hukmM ws m == .murakhkhas).foldl
    (fun acc m => if acc.any (fun x => x.adwar.map (·.2) == m.adwar.map (·.2)) then acc else acc ++ [m]) []

def irabQiyam (m : Murashshah) : List (Dawr × Hala × Amil) := (irab m).map fun e => (e.dawr, e.hala, e.amil)

/-- **«لَمْ يَكْتُبْ زَيْدٌ»:** الجازمُ مبنيٌّ، والفعلُ مجزومٌ بصفّ «لم» (58)، والفاعلُ مرفوعٌ بالفعل؛ والقوّةُ نفي. -/
theorem shahid_lam :
    (maqbula [lamW, yaktubJ, zaydun]).map irabQiyam =
      [[(.jazim, .mabni, .bina), (.fil, .zahira 3, .saff 58), (.fail, .zahira 1, .fil 1)]] ∧
    (maqbula [lamW, yaktubJ, zaydun]).map (·|> quwwaOf |>.1) = [.nafy] := by
  decide +kernel

/-- **«فَلْيَكْتُبْ»:** الفعلُ مجزومٌ بلام الأمر (61)، والقوّةُ إنشاء (عمودُ الأسلوب «الطلب»)، والفاعلُ مستترٌ مرشَّحوه ما قبله (ولا شيءَ قبله هنا). -/
theorem shahid_lamAmr :
    (maqbula [falyaktub]).map irabQiyam = [[(.rabit, .laHala, .bina), (.jazim, .mabni, .bina), (.fil, .zahira 3, .saff 61)]] ∧
    (maqbula [falyaktub]).map (·|> quwwaOf |>.1) = [.insha] ∧
    (maqbula [falyaktub]).map (fun m => (ihalat [] 0 m).map fun i => (i.sura, i.marji)) = [[(.mustatar, .murashshahun [])]] := by
  decide +kernel

/-- **«وَاللَّهُ بِكُلِّ شَيْءٍ عَلِيمٌ»:** عاملُ المبتدأ الابتداء، والمجرورِ الباء (40)، والمضافِ إليه الإضافة، والخبرِ المبتدأ؛ والقوّةُ خبرٌ مثبت. -/
theorem shahid_ismiyya :
    (maqbula [wallahu, bikulli, shayin, alimun]).map (fun m => (irab m).map (·.amil)) =
      [[.bina, .ibtida, .bina, .saff 40, .idafa 1, .mubtada 0]] ∧
    (maqbula [wallahu, bikulli, shayin, alimun]).map (·|> quwwaOf |>.1) = [.ithbat] := by
  decide +kernel

/-- **«نَكْتُبُ»:** المضارعُ للمتكلّم بلا لاحقة، ففاعلُه مستترٌ وجوبًا (القطر L124–125)؛ و**«يَكْتُبْنَ»:** المضارعُ مع نون النسوة مبنيّ (القطر L67–68
    «ويسكن آخره مع نون النسوة … ويعرب فيما عدا ذلك»)، في محلّ رفع (تعيينُ المحلّ)، وعاملُه التجرّد (L96)، وفاعلُه ضميرٌ بارز. -/
theorem shahid_mudari_damir :
    (maqbula [naktubuW]).map (fun m => (isnadOf m).map fun i => (i.sura, i.wujub)) = [some (.mustatar, some true)] ∧
    (maqbula [yaktubnaW]).map (fun m => (irabQiyam m, (isnadOf m).map (·.sura))) =
      [([(.fil, .mahall 1, .tajarrud)], some .bariz)] := by
  decide +kernel

def kitabiW : Dal.Kalima := ⟨[34, 72, 11, 106, 47], false, false⟩                -- كِتَابِي
def jadidunW : Dal.Kalima := ⟨[36, 70, 47, 69, 59], false, false⟩               -- جَدِيدٌ

/-- **«كِتَابِي جَدِيدٌ»:** الاسمُ قبل ياء المتكلّم مقدَّرُ الحركات (القطر L92) مبتدأٌ بالابتداء، والياءُ مضافٌ إليه مبنيٌّ في محلّ جرّ بالإضافة (الكلمة 0)،
    والخبرُ بالمبتدأ؛ وضميرُ المتكلّم يحيل إلى الحضور. -/
theorem shahid_ya :
    (maqbula [kitabiW, jadidunW]).map irabQiyam =
      [[(.mubtada, .mushtaraka 1 [0, 1, 2], .ibtida), (.mudafIlayh, .mahall 2, .idafa 0), (.khabar, .zahira 1, .mubtada 0)]] ∧
    (maqbula [kitabiW, jadidunW]).map (fun m => (ihalat [] 0 m).map (·.marji)) = [[.hudur]] := by
  decide +kernel

/-- **مفاتيحُ «شَيْءٍ»:** عنوانا اللسان المرمَّزان «شوو» و«شيو» (الواوُ همزةٌ أو ألفٌ أو واو)، وصورُهما بالهمزة، ومنها «شيء». -/
theorem shahid_mafatih :
    (maqbula [wallahu, bikulli, shayin, alimun]).map (fun m => m.adwar.flatMap fun p => (judhurWahda p.1).flatMap (mafatih p.1)) =
      [["كلل", "شوو", "شءو", "شوء", "شيو", "شيء", "علم"]] := by
  decide +kernel

/-- **جذرُ الفعل من قراءته** (`Wahda.judhurQ`): مفتاحُ «يَدْعُو» و«لَمْ يَدْعُ» في قراءتهما المرخَّصة «دعو»، ومفتاحُ الأمر «قُمْ» «قوم»، ومفتاحُ «يُرُونَ» «رءي» (`mahmuzAyn`) لا «روي»؛ ومفتاحا
«لَنْ يَقُونَ» «قون» و«قين» (النونُ آخرُ الجذع: `nunAsl` في `Jisr.Tahlil.mudariQiraat`)؛ ومفتاحا «لَمْ يَعِدْ» «عود» و«عيد»: قراءتُها المرخَّصة الأجوف،
وجذورُها كلُّ مشهودٍ على وزنها، لا «وعد» (المثالُ «محتمَل»: `Jisr.Tahlil.shahid_hadd_ayn`)؛ ولا قراءةَ مرخَّصةً لـ«يَقُونَ» و«قُوا» و«يَكُونَ» (اللفيفُ
«محتمَل»: `Jisr.Tahlil.shahid_lafif`)، فلا جذرَ لها في السلسلة. -/
theorem shahid_lafif_jidhr :
    (maqbula [Jisr.Tahlil.yaduW]).map (fun m => m.adwar.flatMap fun p => (judhurWahda p.1).flatMap (mafatih p.1)) = [["دعو"]] ∧
    (maqbula [Jisr.Tahlil.yurunaW]).map (fun m => m.adwar.flatMap fun p => (judhurWahda p.1).flatMap (mafatih p.1)) = [["رءي"]] ∧
    (maqbula [Jisr.Tahlil.lanW, Jisr.Tahlil.yaqunaW]).map (fun m => m.adwar.flatMap fun p => (judhurWahda p.1).flatMap (mafatih p.1)) =
      [["قون", "قين"]] ∧
    (maqbula [Jisr.Tahlil.lamW, Jisr.Tahlil.yaidW]).map (fun m => m.adwar.flatMap fun p => (judhurWahda p.1).flatMap (mafatih p.1)) =
      [["عود", "عيد"]] ∧
    (maqbula [Jisr.Tahlil.qumW]).map (fun m => m.adwar.flatMap fun p => (judhurWahda p.1).flatMap (mafatih p.1)) = [["قوم"]] ∧
    (maqbula [Jisr.Tahlil.lamW, Jisr.Tahlil.yadu]).map (fun m => m.adwar.flatMap fun p => (judhurWahda p.1).flatMap (mafatih p.1)) =
      [["دعو"]] ∧
    maqbula [Jisr.Tahlil.yaqunaW] = [] ∧ maqbula [Jisr.Tahlil.quwaW] = [] ∧ maqbula [Jisr.Tahlil.yakunaW] = [] := by
  decide +kernel

/-- **الدلالةُ على صفوف «كتب» الأربعة في `JadwalLuzum.jadwal`:** كلُّ صفٍّ ادّعاءٌ يقبله `Qaida.maqbul` على قاعدة الصفوف الأربعة وأصولُها هي
    (`iddia_maqbul` على الشاهد): ترادفان مطابقةً لمعنى «علم»،
    وجزءٌ تضمّنًا لـ«علم»، وأصلُ ابن فارس تضمّنًا لـ«جمع». -/
theorem shahid_dalala :
    let T := jadwal.filter (·.a == "كتب")
    (T.map fun r => Qaida.maqbul (qaidaOf T) (aslB T) (iddiaOf T r)) = [true, true, true, true] ∧
    (T.map fun r => (iddiaOf T r).qawl) = [.mutabaqa 0 2, .mutabaqa 3 2, .tadammun 3 2, .tadammun 6 8] := by
  decide

/-! ## ٩. التفسيرُ الجامع والسياقُ من القراءات المقبولة كلِّها

**ما ضُبط (مراجعةُ المالك 2026-11-03، قراءةً للشفرة على `5e9a38e`):** `maqbula` تدمج القراءاتِ المرخَّصة إذا تساوت قوائمُ أدوارها وحدَها، وتساوي
الأدوار لا يُثبت تساويَ الحالات والعوامل والإسناد والقوّة والقيد والجذور؛ و`Qari.Rabt.main` كان يبني سياقَ الإحالة من **أوّل** قراءةٍ مقبولة (`ms.head?`)،
فتصير الإحالةُ التالية مبنيّةً على اختيارٍ لم يُحسم؛ و`hukmJumla` جمعٌ وجوديّ (`NassItar.jamaa`: مرخَّصٌ إن رُخّص مرشَّح) فلا يقول أتّفقت
القراءاتُ أم اختلفت.

**فههنا ثلاثةٌ**، كلٌّ مبرهَنٌ لكلّ مُدخَل:
1. `tafsirOf`: هويّةُ ما يستهلكه ما بعد القبول — الإعرابُ والإسنادُ والقوّةُ والقيدُ والجذور — و`maqbulaT` تطوي القراءاتِ المرخَّصة **بتكافؤ التفسير**
   لا بتشابه الأدوار، ولا تُسقط قراءة: لكلّ مرخَّصةٍ ممثّلٌ بتفسيرها (`maqbulaT_tamm`)، وكلُّ ممثّلٍ مرخَّص (`maqbulaT_murakhkhas`).
2. `hukmTafsir`: حكمٌ ثانٍ **فوق** حكم الجملة: لا قراءة، أو تفسيرٌ واحد (وكم طُوي فيه)، أو `k` تفسيراتٍ مختلفة من `n` مرخَّصة — **اختلافٌ معلَن
   لا يُحسم بالترتيب**؛ ويتّفق مع حكم الجملة في الخلوّ (`hukmTafsir_laQiraa`).
3. `siyaqJumla`: سياقُ الإحالة من القراءات المقبولة **كلِّها**، دالّةٌ في مجموعتها: تبديلُ ترتيبها لا يغيّره (`siyaq_la_yatba_tartib`)، وكلُّ قيدٍ فيه
   يشهد له اسمٌ في قراءةٍ منها (`siyaq_shahid`).

**حدُّه:** تمايزُ ممثّلي `maqbulaT` (لا ممثّلان بتفسيرٍ واحد) غيرُ مبرهَن، وعددُ المطويّ شاهدٌ من الحساب لا مبرهنة؛ وهويّةُ التفسير تعيينُ البنّاء لما
يستهلكه `rabt` اليوم، فما يُزاد على السلسلة يُزاد فيها. -/

/-- **هويّةُ تفسير القراءة** — ما يستهلكه ما بعد القبول: الإعرابُ بدوره وحالته وعامله، والإسنادُ، والقوّةُ، والقيدُ، وجذورُ كلّ وحدةٍ بكلمتها. فقراءتان
    تتساويان فيه متكافئتان لما يحتاجه التفسير — لا بمجرّد تساوي أدوارهما. -/
abbrev Tafsir :=
  List (Dawr × Hala × Amil) × Option (Option Wahda × Option Wahda × Sura × SLGE.Maqam.Feat × Option Bool) × Quwwa ×
    Option (Qayd × Nat) × List (Nat × List (List Nat))

def tafsirOf (m : Murashshah) : Tafsir :=
  (irabQiyam m, (isnadOf m).map fun i => (i.musnad, i.ilayh, i.sura, i.ft, i.wujub), (quwwaOf m).1,
   (qaydR m).map fun p => (p.1, p.2.kalima), m.adwar.map fun p => (p.1.kalima, judhurWahda p.1))

/-- القراءاتُ المرخَّصة كلُّها، بلا دمج. -/
def murakhkhasa (ws : List Dal.Kalima) : List Murashshah := (murashshahun ws).filter fun m => hukmM ws m == .murakhkhas

/-- خطوةُ الطيّ: قراءةٌ تفسيرُها في الحاصل تُعدّ على ممثّلها، وإلّا تُضاف ممثّلًا بعدّ 1. -/
def tayyT (acc : List (Murashshah × Nat)) (m : Murashshah) : List (Murashshah × Nat) :=
  if acc.any (fun x => tafsirOf x.1 == tafsirOf m) then acc.map fun x => if tafsirOf x.1 == tafsirOf m then (x.1, x.2 + 1) else x
  else acc ++ [(m, 1)]

/-- **المقبولُ بالتفسير:** ممثّلٌ لكلّ تفسيرٍ من القراءات المرخَّصة، ومعه عددُ ما طُوي فيه. -/
def maqbulaT (ws : List Dal.Kalima) : List (Murashshah × Nat) := (murakhkhasa ws).foldl tayyT []

theorem tayyT_hafiz (acc : List (Murashshah × Nat)) (m : Murashshah) :
    ∀ x ∈ acc, ∃ y ∈ tayyT acc m, tafsirOf y.1 = tafsirOf x.1 := by
  intro x hx
  unfold tayyT
  split
  · refine ⟨if tafsirOf x.1 == tafsirOf m then (x.1, x.2 + 1) else x, List.mem_map.mpr ⟨x, hx, rfl⟩, ?_⟩
    split <;> rfl
  · exact ⟨x, List.mem_append_left _ hx, rfl⟩

theorem tayyT_dakhil (acc : List (Murashshah × Nat)) (m : Murashshah) : ∃ y ∈ tayyT acc m, tafsirOf y.1 = tafsirOf m := by
  unfold tayyT
  split
  · rename_i h
    obtain ⟨x, hx, he⟩ := List.any_eq_true.mp h
    have he' : tafsirOf x.1 = tafsirOf m := beq_iff_eq.mp he
    refine ⟨(x.1, x.2 + 1), List.mem_map.mpr ⟨x, hx, ?_⟩, he'⟩
    simp [he]
  · exact ⟨(m, 1), List.mem_append_right _ (List.mem_singleton.mpr rfl), rfl⟩

theorem foldl_tayyT_hafiz (l : List Murashshah) :
    ∀ acc, ∀ x ∈ acc, ∃ y ∈ l.foldl tayyT acc, tafsirOf y.1 = tafsirOf x.1 := by
  induction l with
  | nil => intro acc x hx; exact ⟨x, hx, rfl⟩
  | cons a l ih =>
    intro acc x hx
    rw [List.foldl_cons]
    obtain ⟨y, hy, hy'⟩ := tayyT_hafiz acc a x hx
    obtain ⟨z, hz, hz'⟩ := ih (tayyT acc a) y hy
    exact ⟨z, hz, hz'.trans hy'⟩

theorem foldl_tayyT_tamm (l : List Murashshah) :
    ∀ acc, ∀ m ∈ l, ∃ y ∈ l.foldl tayyT acc, tafsirOf y.1 = tafsirOf m := by
  induction l with
  | nil => intro acc m hm; simp at hm
  | cons a l ih =>
    intro acc m hm
    rw [List.foldl_cons]
    rcases List.mem_cons.mp hm with rfl | hm
    · obtain ⟨y, hy, hy'⟩ := tayyT_dakhil acc m
      obtain ⟨z, hz, hz'⟩ := foldl_tayyT_hafiz l (tayyT acc m) y hy
      exact ⟨z, hz, hz'.trans hy'⟩
    · exact ih (tayyT acc a) m hm

/-- **لا تُسقط قراءةٌ مرخَّصة:** لكلٍّ ممثّلٌ في `maqbulaT` بتفسيرها. -/
theorem maqbulaT_tamm (ws : List Dal.Kalima) : ∀ m ∈ murakhkhasa ws, ∃ y ∈ maqbulaT ws, tafsirOf y.1 = tafsirOf m :=
  foldl_tayyT_tamm (murakhkhasa ws) []

theorem foldl_tayyT_min (l : List Murashshah) :
    ∀ acc, ∀ y ∈ l.foldl tayyT acc, y.1 ∈ acc.map (·.1) ∨ y.1 ∈ l := by
  induction l with
  | nil => intro acc y hy; exact Or.inl (List.mem_map.mpr ⟨y, hy, rfl⟩)
  | cons a l ih =>
    intro acc y hy
    rw [List.foldl_cons] at hy
    rcases ih (tayyT acc a) y hy with h | h
    · obtain ⟨x, hx, hx'⟩ := List.mem_map.mp h
      unfold tayyT at hx
      split at hx
      · obtain ⟨z, hz, hz'⟩ := List.mem_map.mp hx
        refine Or.inl (List.mem_map.mpr ⟨z, hz, ?_⟩)
        rw [← hx', ← hz']
        split <;> rfl
      · rcases List.mem_append.mp hx with hx | hx
        · exact Or.inl (List.mem_map.mpr ⟨x, hx, hx'⟩)
        · rw [List.mem_singleton] at hx
          subst hx
          exact Or.inr (hx' ▸ List.mem_cons_self ..)
    · exact Or.inr (List.mem_cons_of_mem _ h)

/-- **كلُّ ممثّلٍ قراءةٌ مرخَّصةٌ من مرشَّحي الجملة.** -/
theorem maqbulaT_murakhkhas (ws : List Dal.Kalima) : ∀ y ∈ maqbulaT ws, y.1 ∈ murashshahun ws ∧ hukmM ws y.1 = .murakhkhas := by
  intro y hy
  rcases foldl_tayyT_min (murakhkhasa ws) [] y hy with h | h
  · simp at h
  · have := List.mem_filter.mp h
    exact ⟨this.1, by simpa using this.2⟩

theorem maqbulaT_nil (ws : List Dal.Kalima) : maqbulaT ws = [] ↔ murakhkhasa ws = [] := by
  constructor
  · intro h
    cases hm : murakhkhasa ws with
    | nil => rfl
    | cons m l =>
      obtain ⟨y, hy, -⟩ := maqbulaT_tamm ws m (hm ▸ List.mem_cons_self ..)
      simp [h] at hy
  · intro h; unfold maqbulaT; rw [h]; rfl

/-- حكمُ التفسير الجامع: فوق حكم الجملة، لا بدلًا منه. -/
inductive HukmTafsir
  | laQiraa
  /-- تفسيرٌ واحدٌ طُويت فيه n قراءةً مرخَّصة. -/
  | wahid (n : Nat)
  /-- k تفسيراتٍ مختلفة من n قراءةً مرخَّصة: اختلافٌ معلَن، لا يُحسم بالترتيب. -/
  | mukhtalif (k n : Nat)
  deriving DecidableEq, Repr

def hukmTafsir (ws : List Dal.Kalima) : HukmTafsir :=
  match maqbulaT ws with
  | [] => .laQiraa
  | [x] => .wahid x.2
  | l => .mukhtalif l.length (l.map (·.2)).sum

/-- **حكمُ التفسير يخلو حيث يخلو حكمُ الجملة من الترخيص، لا غير.** -/
theorem hukmTafsir_laQiraa (ws : List Dal.Kalima) : hukmTafsir ws = .laQiraa ↔ Jisr.Tahlil.hukmJumla ws ≠ .murakhkhas := by
  show _ ↔ ¬ (Jisr.Tahlil.hukmJumla ws = .murakhkhas)
  rw [Jisr.Tahlil.hukmJumla_murakhkhas]
  have e : hukmTafsir ws = .laQiraa ↔ maqbulaT ws = [] := by
    unfold hukmTafsir
    cases maqbulaT ws with
    | nil => simp
    | cons x l => cases l <;> simp
  rw [e, maqbulaT_nil]
  constructor
  · rintro h ⟨m, hm, hk⟩
    have : m ∈ murakhkhasa ws := List.mem_filter.mpr ⟨hm, by simp [hk]⟩
    simp [h] at this
  · intro h
    cases hm : murakhkhasa ws with
    | nil => rfl
    | cons m l =>
      have hmem : m ∈ murakhkhasa ws := hm ▸ List.mem_cons_self ..
      have := List.mem_filter.mp hmem
      exact absurd ⟨m, this.1, by simpa using this.2⟩ h

/-- الكلمةُ k اسمٌ بالعدد a في قراءةٍ من القراءات. -/
def ismFi (ms : List Murashshah) (k a : Nat) : Bool :=
  ms.any fun m => m.adwar.any fun p => p.1.naw == .ism && p.1.kalima == k && p.1.sima.2.2.1.2.2 == a

/-- **سياقُ الجملة للإحالة من قراءاتها المقبولة كلِّها**، لا من أوّلها: (الجملة، الكلمة، العدد) لكلّ كلمةٍ بترتيبها ولكلّ عددٍ شهدت له قراءة. -/
def siyaqJumla (jn n : Nat) (ms : List Murashshah) : List (Nat × Nat × Nat) :=
  (List.range n).flatMap fun k => [0, 1, 2].filterMap fun a => if ismFi ms k a then some (jn, k, a) else none

/-- **تبديلُ ترتيب القراءات لا يغيّر السياق:** دالّةٌ في مجموعتها. -/
theorem siyaq_la_yatba_tartib (jn n : Nat) {ms ms' : List Murashshah} (h : ms.Perm ms') :
    siyaqJumla jn n ms = siyaqJumla jn n ms' := by
  have e : ismFi ms = ismFi ms' := by
    funext k a
    unfold ismFi
    exact h.any_eq
  simp only [siyaqJumla, e]

/-- **كلُّ قيدٍ في السياق يشهد له اسمٌ في قراءةٍ من القراءات** بكلمته وعدده. -/
theorem siyaq_shahid (jn n : Nat) (ms : List Murashshah) {q : Nat × Nat × Nat} (hq : q ∈ siyaqJumla jn n ms) :
    q.1 = jn ∧ ∃ m ∈ ms, ∃ p ∈ m.adwar, p.1.naw = .ism ∧ p.1.kalima = q.2.1 ∧ p.1.sima.2.2.1.2.2 = q.2.2 := by
  unfold siyaqJumla at hq
  obtain ⟨k, -, hk⟩ := List.mem_flatMap.mp hq
  obtain ⟨a, -, ha⟩ := List.mem_filterMap.mp hk
  split at ha
  · rename_i hf
    cases ha
    refine ⟨rfl, ?_⟩
    unfold ismFi at hf
    obtain ⟨m, hm, hm'⟩ := List.any_eq_true.mp hf
    obtain ⟨p, hp, hp'⟩ := List.any_eq_true.mp hm'
    simp only [Bool.and_eq_true, beq_iff_eq] at hp'
    exact ⟨m, hm, p, hp, hp'.1.1, hp'.1.2, hp'.2⟩
  · simp at ha

/-! ## ١٠. الحملُ من الجنس: «ذهابُ الولد مرخَّص لأنّ الولدَ إنسانٌ والإنسانَ ينتقل» على القراءة

**الطلب:** أمرُ المالك 2026-11-04 («اعد إنتاج الهدف من pr 113 وفق ما وجدنا بعده … وطوره وحافظ على تناسق وترابط وتكامل Mashru»). النظريةُ في
`Jisr/QabiliyyaJins.lean` (من #113)، وهذا وصلُها بسلسلة القراءة: الإسنادُ (`isnadOf`) يعطي المسندَ والمسندَ إليه؛ ومفاتيحُ جذريهما
(`judhurWahda`، `mafatih` — من #122، لا من المعنى) تُقرأ في جدولين **مودَعين**: جدولِ الجنس (مفتاحُ الجذر ← القسم؛ قرارُ المالك 2026-10-29 س٢)
وجدولِ المثال (مفتاحُ الجذر ← قابليّةُ الحركة التي الحدثُ مثالُها؛ س١ وس٣). ثمّ الحكمُ `hukmMadlul` على مدلول الجنس (`Tayin.ilaMadlul`)
بالنسبة الإسناديّة. **ولا شيءَ يُستنتج من المعنى**: جنسٌ غائبٌ عن الجدول «لا جنس»، ومثالٌ غائب «لا مثال» — مُسمَّيان لا مُصفَّران.

**المبرهن لكلّ مُدخَل:** `hamlJins_murakhkhas` (لا يُرخَّص إلّا من صفٍّ في جدول الجنس وصفٍّ في جدول المثال وقابليّةٍ في فصول الجنس)،
`hamlJins_la_mumtani` (الحملُ من الجنس لا يُخترع فيه امتناع)، `hamlJins_bila_jadwal` (بلا جدول جنسٍ لا حكمَ من جنس)، و`saffMin_mem` و`mem_of_lookup`؛ وعلى الشاهد
`shahid_haml_jins`. **وحدٌّ معلَن:** اسمُ الفاعل المؤنّث («ذَاهِبَةٌ») بلا مفاتيح جذرٍ في `judhurWahda` (أوزانُ الاسم لا تقطع التاء)، فمسندٌ به «لا مثال» بمفاتيحَ فارغة. **والجدولان المرشَّحان** (`jinsMurashshah`، `mithalMurashshah`) يحتاجان ختمًا، وتقرؤهما الأداةُ `rabt` من ملفٍّ إن أُعطي. -/

open Jisr.QabiliyyaJins (hukm_qab_thulathi qab_la_mumtani)

/-- جدولُ الجنس: مفتاحُ الجذر (عنوانُ اللسان نصًّا) ← القسم. -/
abbrev JinsJadwal := List (String × Madlul.Tayin.Qism)
/-- جدولُ المثال: مفتاحُ جذر الحدث ← قابليّةُ الحركة التي هو مثالُها. -/
abbrev MithalJadwal := List (String × Madlul.Tayin.QabHaraka)

/-- حكمُ الحمل من الجنس، بأسبابه مُسمّاةً. -/
inductive HukmJins
  /-- لا إسنادَ بمسندٍ ومسندٍ إليه ظاهرين. -/
  | laIsnad
  /-- لا صفَّ في جدول الجنس لمفاتيح المسند إليه. -/
  | laJins (mafatih : List String)
  /-- لا صفَّ في جدول المثال لمفاتيح المسند. -/
  | laMithal (mafatih : List String)
  /-- الحكمُ على مدلول الجنس q بقابليّة c، بمفتاحي الصفّين. -/
  | hukm (jidhrIlayh : String) (q : Madlul.Tayin.Qism) (jidhrMusnad : String) (c : Madlul.Tayin.QabHaraka) (h : Jisr.Utur.Hukm)
  deriving DecidableEq, Repr

/-- مفاتيحُ جذور الوحدة في الجداول (من #122: جذورُ القراءة ومفاتيحُها). -/
def mafatihWahda (w : Wahda) : List String := (judhurWahda w).flatMap (mafatih w)

/-- أوّلُ مفتاحٍ له صفٌّ في جدول. -/
def saffMin {β : Type} (T : List (String × β)) (ks : List String) : Option (String × β) :=
  ks.findSome? fun k => (T.lookup k).map (k, ·)

/-- **الحملُ من الجنس على القراءة.** -/
def hamlJins (J : JinsJadwal) (M : MithalJadwal) (m : Murashshah) : HukmJins :=
  match isnadOf m with
  | none => .laIsnad
  | some i =>
    match i.musnad, i.ilayh with
    | some v, some w =>
      match saffMin J (mafatihWahda w) with
      | none => .laJins (mafatihWahda w)
      | some (k, q) =>
        match saffMin M (mafatihWahda v) with
        | none => .laMithal (mafatihWahda v)
        | some (k', c) =>
          .hukm k q k' c (Jisr.Utur.hukmMadlul ⟨Madlul.Tayin.ilaMadlul q, .qabiliyya (Madlul.Tayin.ramzQab c), .isnadiyya⟩)
    | _, _ => .laIsnad

theorem mem_of_lookup {β : Type} {T : List (String × β)} {k : String} {b : β} (h : T.lookup k = some b) : (k, b) ∈ T := by
  obtain ⟨l₁, l₂, rfl, -⟩ := List.lookup_eq_some_iff.1 h
  exact List.mem_append_right _ (List.mem_cons_self ..)

theorem saffMin_mem {β : Type} (T : List (String × β)) (ks : List String) {k : String} {b : β}
    (h : saffMin T ks = some (k, b)) : k ∈ ks ∧ (k, b) ∈ T := by
  unfold saffMin at h
  obtain ⟨k', hk', hs⟩ := List.exists_of_findSome?_eq_some h
  cases hl : T.lookup k' with
  | none => rw [hl] at hs; cases hs
  | some b' =>
    rw [hl] at hs
    simp only [Option.map_some, Option.some.injEq, Prod.mk.injEq] at hs
    obtain ⟨rfl, rfl⟩ := hs
    exact ⟨hk', mem_of_lookup hl⟩

/-- **لا يُرخَّص إلّا من الجدولين والفصول:** ترخيصٌ من الجنس ⇒ للمسند إليه صفٌّ في جدول الجنس بمفتاحٍ من مفاتيحه، وللمسند صفٌّ في جدول
المثال بمفتاحٍ من مفاتيحه، والقابليّةُ في فصول ذلك الجنس. -/
theorem hamlJins_murakhkhas (J : JinsJadwal) (M : MithalJadwal) (m : Murashshah) {k k' : String}
    {q : Madlul.Tayin.Qism} {c : Madlul.Tayin.QabHaraka}
    (h : hamlJins J M m = .hukm k q k' c .murakhkhas) :
    (k, q) ∈ J ∧ (k', c) ∈ M ∧ c ∈ (Madlul.Tayin.fusul q).qab ∧
      ∃ i, isnadOf m = some i ∧ ∃ v w, i.musnad = some v ∧ i.ilayh = some w ∧ k ∈ mafatihWahda w ∧ k' ∈ mafatihWahda v := by
  cases hi : isnadOf m with
  | none => simp [hamlJins, hi] at h
  | some i =>
    cases hv : i.musnad with
    | none => simp [hamlJins, hi, hv] at h
    | some v =>
      cases hw : i.ilayh with
      | none => simp [hamlJins, hi, hv, hw] at h
      | some w =>
        cases hp : saffMin J (mafatihWahda w) with
        | none => simp [hamlJins, hi, hv, hw, hp] at h
        | some p =>
          obtain ⟨k₀, q₀⟩ := p
          cases hp' : saffMin M (mafatihWahda v) with
          | none => simp [hamlJins, hi, hv, hw, hp, hp'] at h
          | some p' =>
            obtain ⟨k₁, c₁⟩ := p'
            simp only [hamlJins, hi, hv, hw, hp, hp', HukmJins.hukm.injEq] at h
            obtain ⟨rfl, rfl, rfl, rfl, hh⟩ := h
            obtain ⟨hk, hJ⟩ := saffMin_mem J _ hp
            obtain ⟨hk', hM⟩ := saffMin_mem M _ hp'
            refine ⟨hJ, hM, ?_, i, rfl, v, w, hv, hw, hk, hk'⟩
            rw [hukm_qab_thulathi] at hh
            by_cases hc : c₁ ∈ (Madlul.Tayin.fusul q₀).qab
            · exact hc
            · rw [if_neg hc] at hh; cases hh

/-- **ولا يُخترع امتناع:** الحملُ من الجنس لا يكون «ممتنعًا» أبدًا — إسنادُ قابليّةٍ إلى مدلول جنس. -/
theorem hamlJins_la_mumtani (J : JinsJadwal) (M : MithalJadwal) (m : Murashshah) (k k' : String)
    (q : Madlul.Tayin.Qism) (c : Madlul.Tayin.QabHaraka) : hamlJins J M m ≠ .hukm k q k' c .mumtani := by
  intro h
  cases hi : isnadOf m with
  | none => simp [hamlJins, hi] at h
  | some i =>
    cases hv : i.musnad with
    | none => simp [hamlJins, hi, hv] at h
    | some v =>
      cases hw : i.ilayh with
      | none => simp [hamlJins, hi, hv, hw] at h
      | some w =>
        cases hp : saffMin J (mafatihWahda w) with
        | none => simp [hamlJins, hi, hv, hw, hp] at h
        | some p =>
          obtain ⟨k₀, q₀⟩ := p
          cases hp' : saffMin M (mafatihWahda v) with
          | none => simp [hamlJins, hi, hv, hw, hp, hp'] at h
          | some p' =>
            obtain ⟨k₁, c₁⟩ := p'
            simp only [hamlJins, hi, hv, hw, hp, hp', HukmJins.hukm.injEq] at h
            obtain ⟨-, rfl, -, rfl, hh⟩ := h
            exact qab_la_mumtani _ _ hh

/-- **بلا جدول جنسٍ لا حكمَ من جنس:** الغيابُ يُسمّى، ولا يُستنتج جنسٌ من المعنى. -/
theorem hamlJins_bila_jadwal (M : MithalJadwal) (m : Murashshah) :
    hamlJins [] M m = .laIsnad ∨ ∃ ks, hamlJins [] M m = .laJins ks := by
  cases hi : isnadOf m with
  | none => left; simp [hamlJins, hi]
  | some i =>
    cases hv : i.musnad with
    | none => left; simp [hamlJins, hi, hv]
    | some v =>
      cases hw : i.ilayh with
      | none => left; simp [hamlJins, hi, hv, hw]
      | some w =>
        right
        refine ⟨mafatihWahda w, ?_⟩
        have hp : saffMin ([] : JinsJadwal) (mafatihWahda w) = none := by
          unfold saffMin; simp [List.lookup]
        simp [hamlJins, hi, hv, hw, hp]

/-! ### الجدولان المرشَّحان (يحتاجان ختمًا؛ قرارُ المالك 2026-10-29 س٢ وس٣) -/

/-- جدولُ الجنس المرشَّح: الولد = إنسان، والدار = جماد (المخصّص بأبوابه؛ موضعُ كلّ صفٍّ يثبّته المالك عند الختم). -/
def jinsMurashshah : JinsJadwal := [("ولد", .insan), ("دور", .jamad)]

/-- جدولُ المثال المرشَّح: ذهب مثالُ السير («ذهب = سار/مضى»؛ نصُّه في المخصّص أو اللسان يثبّته المالك عند الختم). -/
def mithalMurashshah : MithalJadwal := [("ذهب", .sayr)]

def dhahabaW : Dal.Kalima := ⟨[92, 4, 104], false, false⟩                   -- ذَهَبَ
def alwaladuW : Dal.Kalima := ⟨[55, 112, 52, 69], true, true⟩               -- الْوَلَدُ
def taraW : Dal.Kalima := ⟨[64, 11, 60], false, false⟩                       -- طَارَ
def addaruW : Dal.Kalima := ⟨[71, 68, 11, 61], true, true⟩                   -- الدَّارُ

def dhahibunW : Dal.Kalima := ⟨[92, 11, 6, 105, 59], false, false⟩          -- ذَاهِبٌ

/-- **على الشاهد:** «ذَهَبَ الْوَلَدُ» و«الْوَلَدُ ذَاهِبٌ» مرخَّصان من الجنس (ولد → إنسان، ذهب → سير، والسيرُ في فصول الإنسان)؛ و«ذَهَبَ الدَّارُ»
و«الدَّارُ ذَاهِبٌ» لا حكم (الدارُ جمادٌ لا ينتقل، وغيابُ الشاهد ليس امتناعًا)؛ و«طَارَ الْوَلَدُ» لا مثالَ لمفتاحَي «طور/طير» (الأجوفُ بجذرين)؛
وبلا جدول جنسٍ «ذَهَبَ الْوَلَدُ» لا جنس. -/
theorem shahid_haml_jins :
    (maqbulaT [dhahabaW, alwaladuW]).map (fun x => hamlJins jinsMurashshah mithalMurashshah x.1) =
      [.hukm "ولد" .insan "ذهب" .sayr .murakhkhas] ∧
    (maqbulaT [alwaladuW, dhahibunW]).map (fun x => hamlJins jinsMurashshah mithalMurashshah x.1) =
      [.hukm "ولد" .insan "ذهب" .sayr .murakhkhas] ∧
    (maqbulaT [dhahabaW, addaruW]).map (fun x => hamlJins jinsMurashshah mithalMurashshah x.1) =
      [.hukm "دور" .jamad "ذهب" .sayr .laHukm] ∧
    (maqbulaT [addaruW, dhahibunW]).map (fun x => hamlJins jinsMurashshah mithalMurashshah x.1) =
      [.hukm "دور" .jamad "ذهب" .sayr .laHukm] ∧
    (maqbulaT [taraW, alwaladuW]).map (fun x => hamlJins jinsMurashshah mithalMurashshah x.1) =
      [.laMithal ["طور", "طير"]] ∧
    (maqbulaT [dhahabaW, alwaladuW]).map (fun x => hamlJins [] mithalMurashshah x.1) = [.laJins ["ولد"]] := by
  decide +kernel

end Rabt
end Nizam
