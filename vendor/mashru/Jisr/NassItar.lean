/-
  Jisr/NassItar.lean — من النصّ إلى الإطار في ل1 (الأسماءُ الستّة في الجملة): الحزمةُ P4 من `hawkama/خطة_الإطلاق_التجريبي.md`
  («من النصّ إلى الإطار في ل1، بلا إطارٍ يُدخَل يدويًّا»). المدخلُ كلماتُ الجملة خلايا كما يسلّمها القارئ (`Dal.Kalima`)، والمخرجُ
  إطاراتُها (`Utur.Itar3`) بأدوار كلماتها، وحكمُ كلّ إطارٍ بصفّ الأسماء الستّة (`QawaidSitta.hukmSitta`)، وحكمُ الجملة منها.

  **الطلب:** بندُ «تحويلُ النصّ المشكول إلى بنيةٍ تُقرأ آليًّا (P4)» من قائمة رسالة المالك 2026-10-25 (والقائمةُ تبدو جوابًا للبنّاء
  ألصقه؛ وأمرُه فيها «ابني ونفذ وفق افضل الممارسات»؛ ولفظُها من ملخّص الجلسة بعد ضغطها، والرسالةُ الخامّ ليست في سجلّ الجلسة)، وعلى ضابطٍ مجمَّد (`tahaqquq/dawabit/nass/`). وفي الخطّة «P3 وP4 بعد P2»،
  وذلك ترتيبُ البنّاء المقترَح؛ وP4 هنا قبلهما، ولا يستعمل شيئًا منهما.

  **المجال** (معلَنٌ في المواصفة قبل الحالات وقبل هذه الشفرة، `tahaqquq/dawabit/nass/wasf.md`): ستّةُ أشكال —
  فعل فاعل؛ فعل فاعل مضاف_إليه؛ فعل فاعل مفعول_به؛ فعل فاعل مفعول_به مضاف_إليه؛ حرف_جر مجرور؛ حرف_جر مجرور مضاف_إليه.

  **القراءة** (تعيينُ البنّاء، معلَن):
  * **حرفُ الجرّ** كلمةٌ هيكلُها (حواملُها بلا حالاتها) هيكلُ واحدٍ من الخمسة الأُوَل في `SLGE.Wad.jarrF` (القطر L338 «وهو من وإلى وعن
    وعلى وفي واللام والباء للقسم وغيره»، واللامُ والباءُ تتّصلان بما بعدهما فخارجَ المجال؛ `hurufJarr_wad`). و«فِي» حرفٌ في أوّل الجملة وإن طابق هيكلُها جرَّ «فم» في جدول القواعد.
  * **الاسمُ في أوّل الجملة** (فلا إطارَ في المجال): كلمةٌ بأل، أو منوَّنة (آخرُها نونٌ ساكنة بعد متحرّك، كما يكتب القارئ التنوين في
    الوصل)، أو هيكلُها هيكلُ صورةٍ من صور الأسماء الستّة في الجدول المختوم (`QawaidJadwal.sitta`). **وما سواهما فعل** — لا معجمَ
    للأفعال هنا. **وحدٌّ معلَن:** فعلٌ يطابق هيكلُه صورةً من الستّة يُعدّ اسمًا فلا إطار، و«لا حكم»: «حَمَى الرَّجُلُ أَبَا الْوَلَدِ»،
    «أَبَى الرَّجُلُ الطَّعَامَ»، «حَمِيَ الْمَاءُ»، وهي من المجال (`wasf.md` س45 «ماضٍ مجرّد»، وس58 «الألفُ المقصورة «ى» جائزة»). و«أَبَى» خلاياه
    خلايا «أَبَا» بعينها فلا يفرّقهما الدالّ، و«حَمِيَ» هيكلُه هيكلُ «حَمِي» وتخالفها حركةُ الآخر (`haykal_fil_la_itar`؛ ضبطه المراجع المستقلّ).
  * **المركَّبُ الاسميّ** كلمةٌ، أو كلمةٌ ومضافٌ إليه بأل بعدها؛ والمضافُ لا أل فيه ولا تنوين (القطر L343 «ولا تجامع الإضافة تنوينا ولا نونا
    تالية للإعراب مطلقا، ولا أل إلا في نحو»، والمستثنى L344–345 «"الضاربا زيد، والضاربو زيد، والضارب الرجل، والضارب رأس الرجل، وبالرجل
    الضارب غلامه"»). **والمستثنى
    لم يُبنَ:** الوصفُ بأل مضافًا لا يُميَّز من غيره بلا معجم، فالقراءةُ تمنع إضافةَ ذي أل كلَّه، و«جَاءَ الضَّارِبُ الرَّجُلِ» تُردّ خطأً
    (ضُبط بالحالة N45، `tahaqquq/dawabit/nass/`). ولا مضافَ إليه إلّا لآخر اسم: الحدُّ المعلَن في `Utur.haddMuallan` (الملحقُ يرسو على آخر
    خانةٍ ظاهرة).
  * **الإطاراتُ** إطاراتُ المالك نفسُها: الفعلُ والفاعل `Mulhaqat.darabaZayd` (والمنوَّنُ بسمته هو `Mulhaqat.jaaRajul`: إطارُ «ذَهَبَ وَلَدٌ» في `yuid_shawahid`)، والمفعولُ `Mulhaqat.daraba`،
    والجارُّ والمجرور `Mulhaqat.bikam`، وتعريفُ الاسم من صورته (المنوَّنُ نكرة، وغيرُه معرفة)؛ والمضافُ إليه ملحقٌ كما في شواهد `Utur`.
  * **المدلولُ مفروض:** مدلولاتُ شواهد `Utur` نفسُها (`dhahab`، `darab`، `walad`، `fi`، `dar`) وإسنادُها. فالنصُّ لا
    يحمل المدلول، والحكمُ هنا حكمُ الدالّ والبنية بصفّ الأسماء الستّة، والمدلولُ المفروض يستوفي ما تقرؤه الطبقةُ من المدلول في كلّ إطار
    (`fard_madlul`، على `madlulYamurr`: نقلُ البنّاء لشروط المدلول في `waslBase` و`waslMl` و`jisrMadlul` ووصلِ المدلول وابتدائه ووقفه). وأنّ
    ما في `hukmSitta` من امتناعٍ أو «لا حكم» على هذه الإطارات ليس منه قراءةٌ للبنّاء، لا مبرهنة: لا مبرهنةَ تصل `madlulYamurr` بـ`hukmSitta`.
  * **حكمُ الجملة** (`hukmNass`): مقبولٌ إن قُبل إطارٌ منها، وخطأٌ إن كان لها إطارٌ وامتنعت إطاراتُها كلُّها، و«لا حكم» فيما سوى ذلك
    (ومنه: لا إطار). وهو كإسقاط الوجود `Phi.yujad` في `Nizam/Phi.lean` على غير الفارغ؛ والفارغُ هنا «لا حكم» (كـ`yujadMaftuh`) وهناك ممتنع
    (قراءةُ البنّاء).

  **العدّ** بالمعيار الموحَّد (`Nizam/Asas.lean`): 14 مبرهنة — 8 لكلّ (`itarat_mem`، `itarat_kalimat`، `jamaa_murakhkhas`، `jamaa_mumtani`،
  `hukmNass_murakhkhas`، `hukmNass_mumtani`، `maqbula_iff`، `fard_madlul`)، و1 تعريفيّة (`la_itar_la_hukm`)، و5 على الشاهد (`hurufJarr_wad`،
  `yuid_shawahid`، `haraka_tughayyir`، `itar_min_hukm`، `haykal_fil_la_itar`). ومساعداتٌ خاصّةٌ غيرُ معدودة ولا مدقّقة بأسمائها في `Audit.lean` (ومسلّماتُها داخلةٌ في
  تدقيق ما يستعملها)، مصنَّفةً بالمعيار: `itarFail_def`، `itarMaful_def`، `itarJarr_def`، `madlul_eq` تعريفيّة (cases وsimp بالتعريفات وبالفروض).
  وعمومُ `fard_madlul` من `madlul_eq`: المدلولُ لا يقرأ الكلمات، فيكفي قالبٌ لكلّ إطار.
-/
import Jisr.QawaidSitta

namespace Jisr
namespace NassItar
open Jisr.Utur Jisr.QawaidSitta Dal SLGE.Simat

/-! ## ١. الكلمة -/

/-- أدوارُ الكلمات في المجال. -/
inductive Dawr | fil | fail | maful | harfJarr | majrur | mudafIlayh
  deriving DecidableEq, Repr

/-- هيكلُ الكلمة: حواملُها بلا حالاتها. -/
def haykal (w : Kalima) : List Nat := w.khalaya.map (· / 4)

/-- هيكلُ نصٍّ غير مشكول: الهمزاتُ بمقاعدها «ء» والمقصورةُ ألف، وما ليس حاملًا يسقط. -/
def nassHaykal (s : String) : List Nat :=
  s.toList.filterMap fun c =>
    let c := if c == 'أ' || c == 'إ' || c == 'آ' then 'ء' else if c == 'ى' then 'ا' else c
    hawamil.idxOf? c

/-- حروفُ الجرّ كلماتٍ: «من»، «إلى»، «عن»، «على»، «في». -/
def hurufJarr : List (List Nat) := [[27, 14], [0, 13, 2], [3, 14], [3, 13, 2], [25, 11]]

/-- **هياكلُ حروف الجرّ الخمسة هي الخمسةُ الأُوَل من `Wad.jarrF`** (القطر L338)؛ و«اللام» و«الباء» بعدها تتّصلان بما بعدهما فخارجَ المجال. -/
theorem hurufJarr_wad : (SLGE.Wad.jarrF.take 5).map (fun a => nassHaykal a.name) = hurufJarr := by decide +kernel

/-- منوَّنة: آخرُ خلاياها نونٌ ساكنة (59) بعد حرفٍ متحرّك. -/
def munawwan (w : Kalima) : Bool :=
  match w.khalaya.reverse with
  | 59 :: a :: _ => a < 116 && a % 4 < 3
  | _ => false

/-- هيكلُها هيكلُ صورةٍ من صور الأسماء الستّة في الجدول المختوم. -/
def haykalSitta (w : Kalima) : Bool :=
  Jisr.QawaidJadwal.sitta.any fun s => [s.raf, s.nasb, s.jarr].any fun c => c.map (· / 4) == haykal w

/-- اسمٌ بعلامته: أل، أو تنوين، أو هيكلُ صورةٍ من الستّة. -/
def ismi (w : Kalima) : Bool := w.al || munawwan w || haykalSitta w

/-- يقبل أن يكون مضافًا: لا أل فيه ولا تنوين (القطر L343؛ ومستثناه في L344–345 لم يُبنَ: الرأس). -/
def yudaf (w : Kalima) : Bool := !w.al && !munawwan w

/-- تعريفُ الاسم من صورته: المنوَّنُ نكرة (0)، وغيرُه معرفة (1). -/
def tarif (w : Kalima) : Nat := if munawwan w then 0 else 1

/-! ## ٢. الإطارات -/

/-- المضافُ إليه ملحقًا راسيًا على الخانة `m`، كما في شواهد `Utur` (`dhahabaMudaf`، `darabaMudaf`، `fiAfdalAdDur`). -/
def mudafIlayhi (m : Nat) : Mulhaqat.Mulhaq := { dawr := .mudafIlayhi, marsa := m, naw := 0, t := noun 1 0 0, q := 2 }

/-- فعلٌ وفاعل، وللفاعل مضافٌ إليه إن كان `mi`. -/
def itarFail (v s : Kalima) (mi : Option Kalima) : List Dawr × Itar3 :=
  let ud : SLGE.Kull.UD := { Mulhaqat.darabaZayd with ats := [past 0 0, noun (tarif s) 0 0] }
  match mi with
  | none => ([.fil, .fail], { jisr := { ud := ud }, kalimat := [v, s], maani := [dhahab, walad],
                              isnad := ⟨walad, .qabiliyya 10, .isnadiyya⟩ })
  | some m => ([.fil, .fail, .mudafIlayh],
               { jisr := { ud := ud, ml := [mudafIlayhi 1] }, kalimat := [v, s, m], maani := [dhahab, walad, walad],
                 isnad := ⟨walad, .qabiliyya 10, .isnadiyya⟩ })

/-- فعلٌ وفاعلٌ ومفعول، وللمفعول مضافٌ إليه إن كان `mi`. -/
def itarMaful (v s o : Kalima) (mi : Option Kalima) : List Dawr × Itar3 :=
  let ud : SLGE.Kull.UD := { Mulhaqat.daraba with ats := [past 0 0, noun (tarif s) 0 0, noun (tarif o) 0 0] }
  match mi with
  | none => ([.fil, .fail, .maful], { jisr := { ud := ud }, kalimat := [v, s, o], maani := [darab, walad, walad],
                                       isnad := ⟨walad, .qabiliyya 10, .isnadiyya⟩ })
  | some m => ([.fil, .fail, .maful, .mudafIlayh],
               { jisr := { ud := ud, ml := [mudafIlayhi 2] }, kalimat := [v, s, o, m], maani := [darab, walad, walad, walad],
                 isnad := ⟨walad, .qabiliyya 10, .isnadiyya⟩ })

/-- حرفُ جرٍّ ومجرور، وللمجرور مضافٌ إليه إن كان `mi`. -/
def itarJarr (p n : Kalima) (mi : Option Kalima) : List Dawr × Itar3 :=
  let ud : SLGE.Kull.UD := { Mulhaqat.bikam with ats := [harfA, noun (tarif n) 0 0, harfA] }
  match mi with
  | none => ([.harfJarr, .majrur], { jisr := { ud := ud }, kalimat := [p, n], maani := [fi, dar],
                                      isnad := ⟨walad, .alaqa 1 30, .idafiyya⟩ })
  | some m => ([.harfJarr, .majrur, .mudafIlayh],
               { jisr := { ud := ud, ml := [mudafIlayhi 1] }, kalimat := [p, n, m], maani := [fi, dar, dar],
                 isnad := ⟨walad, .alaqa 1 30, .idafiyya⟩ })

/-- **الإطاراتُ من الكلمات وحدها:** بالكلمة الأولى (حرفُ جرٍّ أو اسمٌ أو فعل) ثمّ بعدد ما بعدها. ولا مبرهنةَ أنّها كلُّ ما يحتمله الدالّ في
    المجال: فعلٌ يطابق هيكلُه صورةً من الستّة لا إطارَ له (`haykal_fil_la_itar`). -/
def itarat : List Kalima → List (List Dawr × Itar3)
  | [] => []
  | w :: r =>
    if hurufJarr.contains (haykal w) then
      match r with
      | [n] => [itarJarr w n none]
      | [n, m] => if yudaf n && m.al then [itarJarr w n (some m)] else []
      | _ => []
    else if ismi w then []
    else
      match r with
      | [s] => [itarFail w s none]
      | [s, x] => (if yudaf s && x.al then [itarFail w s (some x)] else []) ++ [itarMaful w s x none]
      | [s, o, m] => if yudaf o && m.al then [itarMaful w s o (some m)] else []
      | _ => []

/-! ## ٣. الحكم -/

/-- جمعُ أحكام الإطارات: مقبولٌ إن كان فيها مقبول، وممتنعٌ إن لم تخلُ وكلُّها ممتنع، وإلّا «لا حكم». -/
def jamaa (hs : List Hukm) : Hukm :=
  if hs.contains .murakhkhas then .murakhkhas
  else if hs ≠ [] ∧ hs.all (· == .mumtani) = true then .mumtani else .laHukm

/-- **حكمُ الجملة:** جمعُ أحكام إطاراتها بصفّ الأسماء الستّة. -/
def hukmNass (ws : List Kalima) : Hukm := jamaa ((itarat ws).map fun x => hukmSitta x.2)

/-- أدوارُ الإطارات المقبولة. -/
def maqbula (ws : List Kalima) : List (List Dawr) :=
  ((itarat ws).filter fun x => hukmSitta x.2 == .murakhkhas).map (·.1)

/-! ## ٤. خواصُّ القراءة (لكلّ: خواصُّ التعيين على مجاله، كلماتٍ أيًّا كانت) -/

/-- الأشكالُ الستّة في المواصفة. -/
def ashkal : List (List Dawr) :=
  [[.fil, .fail], [.fil, .fail, .mudafIlayh], [.fil, .fail, .maful], [.fil, .fail, .maful, .mudafIlayh],
   [.harfJarr, .majrur], [.harfJarr, .majrur, .mudafIlayh]]

private theorem itarFail_def (v s : Kalima) (mi : Option Kalima) :
    (itarFail v s mi).2.kalimat = [v, s] ++ mi.toList ∧ (itarFail v s mi).1.length = 2 + mi.toList.length ∧
    (itarFail v s mi).1 ∈ ashkal := by
  cases mi <;> simp [itarFail, ashkal]

private theorem itarMaful_def (v s o : Kalima) (mi : Option Kalima) :
    (itarMaful v s o mi).2.kalimat = [v, s, o] ++ mi.toList ∧ (itarMaful v s o mi).1.length = 3 + mi.toList.length ∧
    (itarMaful v s o mi).1 ∈ ashkal := by
  cases mi <;> simp [itarMaful, ashkal]

private theorem itarJarr_def (p n : Kalima) (mi : Option Kalima) :
    (itarJarr p n mi).2.kalimat = [p, n] ++ mi.toList ∧ (itarJarr p n mi).1.length = 2 + mi.toList.length ∧
    (itarJarr p n mi).1 ∈ ashkal := by
  cases mi <;> simp [itarJarr, ashkal]

/-- **كلُّ إطارٍ واحدٌ من الثلاثة:** جارٌّ ومجرور، أو فعلٌ وفاعل، أو فعلٌ وفاعلٌ ومفعول — على كلمات الجملة بترتيبها، بمضافٍ إليه
    أو بدونه. -/
theorem itarat_mem (ws : List Kalima) (x : List Dawr × Itar3) (h : x ∈ itarat ws) :
    (∃ p n mi, ws = [p, n] ++ Option.toList mi ∧ x = itarJarr p n mi) ∨
    (∃ v s mi, ws = [v, s] ++ Option.toList mi ∧ x = itarFail v s mi) ∨
    (∃ v s o mi, ws = [v, s, o] ++ Option.toList mi ∧ x = itarMaful v s o mi) := by
  rcases ws with _ | ⟨w, _ | ⟨a, _ | ⟨b, _ | ⟨c, _ | ⟨d, r⟩⟩⟩⟩⟩
  · simp [itarat] at h
  · simp only [itarat] at h; split at h <;> (try split at h) <;> simp at h
  · simp only [itarat] at h
    split at h
    · simp only [List.mem_singleton] at h; exact Or.inl ⟨w, a, none, rfl, h⟩
    · split at h
      · simp at h
      · simp only [List.mem_singleton] at h; exact Or.inr (Or.inl ⟨w, a, none, rfl, h⟩)
  · simp only [itarat] at h
    split at h
    · split at h
      · simp only [List.mem_singleton] at h; exact Or.inl ⟨w, a, some b, rfl, h⟩
      · simp at h
    · split at h
      · simp at h
      · simp only [List.mem_append, List.mem_singleton] at h
        rcases h with h | h
        · split at h
          · simp only [List.mem_singleton] at h; exact Or.inr (Or.inl ⟨w, a, some b, rfl, h⟩)
          · simp at h
        · exact Or.inr (Or.inr ⟨w, a, b, none, rfl, h⟩)
  · simp only [itarat] at h
    split at h
    · simp at h
    · split at h
      · simp at h
      · split at h
        · simp only [List.mem_singleton] at h; exact Or.inr (Or.inr ⟨w, a, b, some c, rfl, h⟩)
        · simp at h
  · simp only [itarat] at h; split at h <;> (try split at h) <;> simp at h

/-- **كلُّ إطارٍ على كلمات الجملة نفسِها بترتيبها، بدورٍ لكلّ كلمة، وأدوارُه شكلٌ من الستّة:** لا كلمةَ تُزاد ولا تُحذف ولا يُغيَّر
    ترتيبُها. -/
theorem itarat_kalimat (ws : List Kalima) (x : List Dawr × Itar3) (h : x ∈ itarat ws) :
    x.2.kalimat = ws ∧ x.1.length = ws.length ∧ x.1 ∈ ashkal := by
  rcases itarat_mem ws x h with ⟨p, n, mi, rfl, rfl⟩ | ⟨v, s, mi, rfl, rfl⟩ | ⟨v, s, o, mi, rfl, rfl⟩
  · have := itarJarr_def p n mi; refine ⟨this.1, ?_, this.2.2⟩; rw [this.2.1]; simp; omega
  · have := itarFail_def v s mi; refine ⟨this.1, ?_, this.2.2⟩; rw [this.2.1]; simp; omega
  · have := itarMaful_def v s o mi; refine ⟨this.1, ?_, this.2.2⟩; rw [this.2.1]; simp; omega

theorem jamaa_murakhkhas (hs : List Hukm) : jamaa hs = .murakhkhas ↔ .murakhkhas ∈ hs := by
  unfold jamaa
  by_cases h1 : hs.contains .murakhkhas = true
  · simp only [h1, ite_true, true_iff]; exact List.contains_iff_mem.mp h1
  · simp only [h1, Bool.false_eq_true, ite_false]
    have hm : Hukm.murakhkhas ∉ hs := fun hm => h1 (List.contains_iff_mem.mpr hm)
    simp only [hm, iff_false]
    split <;> simp

theorem jamaa_mumtani (hs : List Hukm) : jamaa hs = .mumtani ↔ hs ≠ [] ∧ ∀ h ∈ hs, h = .mumtani := by
  unfold jamaa
  by_cases h1 : hs.contains .murakhkhas = true
  · have hm := List.contains_iff_mem.mp h1
    simp only [h1, ite_true]
    constructor
    · intro e; cases e
    · rintro ⟨-, ha⟩; cases ha _ hm
  · simp only [h1, Bool.false_eq_true, ite_false]
    by_cases h2 : (hs ≠ [] ∧ hs.all (· == .mumtani) = true)
    · rw [ite_eq_left h2]
      refine ⟨fun _ => ⟨h2.1, fun h hh => ?_⟩, fun _ => rfl⟩
      have := List.all_eq_true.mp h2.2 h hh; simpa using this
    · rw [ite_eq_right h2]
      constructor
      · intro e; cases e
      · rintro ⟨hn, ha⟩; exact absurd ⟨hn, List.all_eq_true.mpr fun h hh => by simp [ha h hh]⟩ h2

/-- **حكمُ الجملة مقبول** ⟺ لها إطارٌ مقبول. -/
theorem hukmNass_murakhkhas (ws : List Kalima) :
    hukmNass ws = .murakhkhas ↔ ∃ x ∈ itarat ws, hukmSitta x.2 = .murakhkhas := by
  simp [hukmNass, jamaa_murakhkhas]

/-- **حكمُ الجملة خطأ** ⟺ لها إطار، وامتنعت إطاراتُها كلُّها. -/
theorem hukmNass_mumtani (ws : List Kalima) :
    hukmNass ws = .mumtani ↔ itarat ws ≠ [] ∧ ∀ x ∈ itarat ws, hukmSitta x.2 = .mumtani := by
  rw [hukmNass, jamaa_mumtani]
  constructor
  · rintro ⟨hn, ha⟩
    exact ⟨fun h0 => hn (by simp [h0]), fun x hx => ha _ (List.mem_map.mpr ⟨x, hx, rfl⟩)⟩
  · rintro ⟨hn, ha⟩
    refine ⟨fun h0 => hn (List.map_eq_nil_iff.mp h0), fun h hh => ?_⟩
    obtain ⟨x, hx, rfl⟩ := List.mem_map.mp hh; exact ha x hx

/-- **ولا إطارَ فلا حكم:** ما لا إطارَ له في المجال «لا حكم» لا «خطأ». -/
theorem la_itar_la_hukm (ws : List Kalima) (h : itarat ws = []) : hukmNass ws = .laHukm := by
  simp [hukmNass, h, jamaa]

/-- **الإطاراتُ المقبولة** هي أدوارُ ما قُبل من الإطارات. -/
theorem maqbula_iff (ws : List Kalima) (r : List Dawr) :
    r ∈ maqbula ws ↔ ∃ x ∈ itarat ws, x.1 = r ∧ hukmSitta x.2 = .murakhkhas := by
  simp only [maqbula, List.mem_map, List.mem_filter, beq_iff_eq]
  constructor
  · rintro ⟨x, ⟨hx, he⟩, rfl⟩; exact ⟨x, hx, rfl, he⟩
  · rintro ⟨x, hx, rfl, he⟩; exact ⟨x, ⟨hx, he⟩, rfl⟩

/-! ## ٥. المدلولُ المفروض -/

/-- قسمُ مدلول كلّ خانةٍ ظاهرةٍ قسمُ دورها، ومدلولُ كلّ ملحقٍ ظاهرٍ اسم: جزءُ المدلول من `waslBase` و`waslMl` نقلًا من البنّاء، بلا شرط وجود الكلمة الذي فيهما. -/
def qismMuwafiq (u : Itar3) : Bool :=
  ((List.range (nB u)).all fun i =>
    SLGE.Tarkib.fillAt (baseSlots u) i != 0 ||
    (match u.maani[overtIdx u i]? with
     | some m => SLGE.Cat.kindOfMadlul m == qismDawr u.jisr.ud.f.2.1 (Mulhaqat.roleOf u.jisr.ud.f i)
     | none => false)) &&
  ((List.range (zawahirMl u).length).all fun k =>
    match u.maani[zawahirBase u + k]? with
    | some md => SLGE.Cat.kindOfMadlul md == .ism
    | none => false)

/-- ما يقرؤه حكمُ الطبقة من المدلول: مدلولٌ لكلّ كلمة، وقسمُه قسمُ موضعه، والجسرُ، ووصلُ المدلول، والابتداءُ به، والوقف. -/
def madlulYamurr (u : Itar3) : Bool :=
  u.maani.length == u.kalimat.length && qismMuwafiq u && jisrMadlul u && waslMadlul u.isnad == .murakhkhas &&
  ibtidaMadlul u.isnad && (if u.jisr.ud.f.1 == 2 then u.isnad.nisba == .idafiyya else waqfMadlul u.isnad)

private theorem madlul_eq (u u' : Itar3) (hf : u.jisr.ud.f = u'.jisr.ud.f) (hl : u.jisr.ml = u'.jisr.ml)
    (hm : u.maani = u'.maani) (hi : u.isnad = u'.isnad) (hk : u.kalimat.length = u'.kalimat.length) :
    madlulYamurr u = madlulYamurr u' := by
  unfold madlulYamurr qismMuwafiq jisrMadlul musnadIlayhIdx musnadIdx madlulOf nB baseSlots overtIdx zawahirMl
    zawahirBase
  simp only [baseSlots, hf, hl, hm, hi, hk]

/-- كلمةٌ فارغةٌ تملأ القالب: المدلولُ لا يقرأ الكلمات. -/
private def k0 : Kalima := ⟨[], false, false⟩

/-- **المدلولُ المفروض يمرّ في كلّ إطارٍ تُخرجه القراءة** (لكلّ جملة): مدلولٌ لكلّ كلمة، وقسمُه قسمُ موضعه، والجسرُ، ووصلُ المدلول، والابتداءُ
    به، والوقف. وأنّ ما في `hukmSitta` على هذه الإطارات من امتناعٍ أو «لا حكم» ليس منه قراءةٌ لا تثبتها هذه المبرهنة (الرأس). -/
theorem fard_madlul (ws : List Kalima) (x : List Dawr × Itar3) (h : x ∈ itarat ws) : madlulYamurr x.2 = true := by
  rcases itarat_mem ws x h with ⟨p, n, mi, -, rfl⟩ | ⟨v, s, mi, -, rfl⟩ | ⟨v, s, o, mi, -, rfl⟩
  · cases mi with
    | none => rw [madlul_eq (itarJarr p n none).2 (itarJarr k0 k0 none).2 rfl rfl rfl rfl rfl]; decide
    | some m => rw [madlul_eq (itarJarr p n (some m)).2 (itarJarr k0 k0 (some k0)).2 rfl rfl rfl rfl rfl]; decide
  · cases mi with
    | none => rw [madlul_eq (itarFail v s none).2 (itarFail k0 k0 none).2 rfl rfl rfl rfl rfl]; decide
    | some m => rw [madlul_eq (itarFail v s (some m)).2 (itarFail k0 k0 (some k0)).2 rfl rfl rfl rfl rfl]; decide
  · cases mi with
    | none => rw [madlul_eq (itarMaful v s o none).2 (itarMaful k0 k0 k0 none).2 rfl rfl rfl rfl rfl]; decide
    | some m => rw [madlul_eq (itarMaful v s o (some m)).2 (itarMaful k0 k0 k0 (some k0)).2 rfl rfl rfl rfl rfl]; decide

/-! ## ٦. الشواهد (على الشاهد) -/

/-- **الإطاراتُ المُدخَلةُ باليد في شواهد ل1 تُستخرج من كلماتها:** مواضعُ شواهد `QawaidSitta` الثمانية عشر (`mawadiShawahid`) وشواهدُ `Utur`
    الخمسة («ذَهَبَ الْوَلَدُ»، «ذَهَبَ وَلَدٌ»، «فِي الدَّارِ»، «ضَرَبَ الْفَتَى الْقَاضِي»، «ذَهَبَ أَبُو الْوَلَدِ»): لكلٍّ منها إطارٌ تُخرجه
    `itarat` من كلماته وحدها هو هو بعينه (الإطارُ النحويّ والكلماتُ والمدلولُ المفروض والإسناد). -/
theorem yuid_shawahid :
    mawadiShawahid.all (fun x => (itarat x.1.kalimat).any (·.2 == x.1)) = true ∧
    [dhahabaAlWalad, dhahabaWaladun, fiDar, darabaFata alQadi, abuAlWalad].all
      (fun u => (itarat u.kalimat).any (·.2 == u)) = true := by
  decide +kernel

/-- **تبديلُ علامة الإعراب يغيّر الحكم** (أزواجٌ من شواهد `Utur`): «ضَرَبَ الْوَلَدُ أَبَا الْوَلَدِ» مقبولة و«… أَبُو الْوَلَدِ» خطأ؛ و«فِي أَبِي
    الدُّورِ» مقبولة و«فِي أَبُو الدُّورِ» خطأ؛ و«ذَهَبَ الْوَلَدُ» مقبولة و«ذَهَبَ الْوَلَدَ» خطأ. **وما لا يتغيّر إلى خطأ:** «ذَهَبَ أَبُو
    الْوَلَدِ» مقبولة و«ذَهَبَ أَبِي الْوَلَدِ» «لا حكم» — الياءُ رفعًا تُقدَّر عليها الضمّة (`Utur.illaMuqaddara`، القطر L92–93)، فلا يُفرَّق
    من المنقوص بلا معجم. -/
theorem haraka_tughayyir :
    hukmNass [darabaK, alWalad, abaK, alWaladi] = .murakhkhas ∧ hukmNass [darabaK, alWalad, abuK, alWaladi] = .mumtani ∧
    hukmNass [fiK, abiK, adDurK] = .murakhkhas ∧ hukmNass [fiK, abuK, adDurK] = .mumtani ∧
    hukmNass [dhahaba, alWalad] = .murakhkhas ∧ hukmNass [dhahaba, alWaladaK] = .mumtani ∧
    hukmNass [dhahaba, abuK, alWaladi] = .murakhkhas ∧ hukmNass [dhahaba, abiK, alWaladi] = .laHukm := by
  decide +kernel

/-- **الإطارُ من الحكم:** «ذَهَبَ أَبُو الْوَلَدِ» لها إطاران (فاعلٌ ومضافٌ إليه، أو فاعلٌ ومفعول)، والمقبولُ الأوّلُ وحده؛ و«ضَرَبَ الْفَتَى
    الْقَاضِي» لها إطارٌ واحد: ذو أل لا يُضاف (القطر L343؛ ومستثناه L344–345 لم يُبنَ)؛ و«أَبُو الْوَلَدِ» في أوّل الجملة اسمٌ فلا إطارَ في المجال. -/
theorem itar_min_hukm :
    (itarat [dhahaba, abuK, alWaladi]).map (·.1) = [[.fil, .fail, .mudafIlayh], [.fil, .fail, .maful]] ∧
    maqbula [dhahaba, abuK, alWaladi] = [[.fil, .fail, .mudafIlayh]] ∧
    (itarat [darabaK, alFata, alQadi]).map (·.1) = [[.fil, .fail, .maful]] ∧
    itarat [abuK, alWaladi, dhahaba] = [] ∧ hukmNass [abuK, alWaladi, dhahaba] = .laHukm := by
  decide +kernel

/-- **حدٌّ معلَن: فعلٌ يطابق هيكلُه صورةً من الستّة يُعدّ اسمًا** (ضبطه المراجع المستقلّ): «حَمَى الرَّجُلُ أَبَا الْوَلَدِ» و«أَبَى الرَّجُلُ
    الطَّعَامَ» و«حَمِيَ الْمَاءُ» — والثلاثُ من المجال (`wasf.md` س45، س58) — لا إطارَ لها، فـ«لا حكم» (`la_itar_la_hukm`). و«أَبَى» خلاياه
    خلايا «أَبَا» (`QawaidSitta.abaK`) بعينها؛ و«حَمِيَ» آخرُه ياءٌ مفتوحة وهيكلُه هيكلُ «حَمِي». والخلايا كما يقرؤها القارئ (`qari --khalaya`). -/
theorem haykal_fil_la_itar :
    let alRajul : Kalima := ⟨[63, 60, 37, 53], true, true⟩
    itarat [⟨[16, 108, 11], false, false⟩, alRajul, abaK, alWaladi] = [] ∧
    itarat [⟨[0, 104, 11], false, false⟩, alRajul, ⟨[67, 64, 12, 11, 108], true, true⟩] = [] ∧
    itarat [⟨[16, 110, 44], false, false⟩, ⟨[55, 108, 11, 1], true, true⟩] = [] ∧
    (⟨[0, 104, 11], false, false⟩ : Kalima) = abaK := by
  decide +kernel

end NassItar
end Jisr
