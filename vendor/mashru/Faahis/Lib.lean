/-
  Faahis/Lib.lean — الفاحص التنفيذيّ (المكتبة المشتركة بين faahis وqari): يقرأ سجلّ المودَعات والمخزن، ويُجري عليهما الدوالّ المبرهنة نفسها.

  * القضايا قضايا الدلالة الأولى `QawaninDalala.Qadiyya` على معرّفات؛ الألفاظ والمعاني والعناوين تُرقَّم عند القراءة.
  * القاعدة مغلقة: لا يُقبل قانون إلّا إن كان مثالًا لقوانين Aql/QawaninDalala.lean (`shakl`)؛
    وسلامتها بالنسبة إلى نموذج المدلول مبرهنة (`salama`)، وتدرّجها (`shakl_mutadarrija`).
  * القبول = `Qaida.maqbul` (`maqbul_murakhkhas`)؛ الوسم المحسوب = `Mawsua.quwwatSilsila` على وسم الأصل بعد
    قيد طريقته (`Mawsua.qayd`) وقيد نوع مودَعه (`Idaa.qaydMudaa`)؛ لا أصل إلّا من مودَع مسجَّل (`Idaa.aslMusajjal`).
  * التنفيذ (س1، 2026-10-24): القبولُ يُجرى بـ `Qaida.maqbulA` على مصفوفة القوانين `Bina.qs`، وهو `maqbul` بعينه
    (`Qaida.maqbulA_eq` بـ `Bina.hq`)؛ والأصلُ من `jadwalUsul`، وهو أوّلُ أصلٍ للقضيّة كما في `find?` (`jadwalUsul_find`،
    `bina_asl`، `bina_aslB`، `bina_aslW`). فحقولُ البناء التي يقبل بها الفاحص ويحسب الوسم هي نظائرُها على `find?` والقائمة، والزمنُ
    وحده تغيّر: نموُّه عند مضاعفة المخزن ليس تربيعيًّا (tahaqquq/test_sura.py)، والأصلُ المكرَّر أوّلُه أصلُه (mawsua/test_mawsua.py §١٦).
  * السؤال (`--sual`): المخزن يُبنى بـ `Makhzan.udkhulA` (`udkhul` بعينه: `Mawsua.udkhulA_eq`)، ويُسأل بـ `Mawsua.sual`؛ وكلّ قولٍ يُطبع بسلسلته وبمراتب
    مخرجه الثلاث (`Maratib.mukhraj`): القضيّة «من حيث هي»، ومعانيها «معلومة» أو «مفهوم» بشواهد واقعٍ في مودَع
    «واقع مختوم» وحده (`Maratib.shuhudMutabara`).

  الملفّان (TAB بين الحقول؛ والسطر الفارغ والسطر أوّلُه «#» يُتجاوزان):
  * سجلُّ المودَعات (الملفّ الأوّل) لا يحمل إلّا أسطر `mudaa` و`shahid`؛ وهو السلطة وحده (`tahmil`، `tahmil_mudaat`، `tahmil_shawahid`).
  * المحتوى (بقيّة الملفّات) يحمل ما سوى ذلك؛ وسطرُ `mudaa` أو `shahid` فيه خطأٌ باسمه (`muhtawa_la_yudif_mudaa`، `muhtawa_la_yashhad`).
  * **الشاهدُ بقضيّته لا برقم صفّه** (الحزمة P2-أ، والقرار ٢-أ في `hawkama/قرارات_التفويض.md`): سطرُ `shahid` يربط معنًى بقضيّةٍ (شيء، خاصّة،
    قيمة) في جدول «الواقع المختوم» المضمَّن (`Waqi.Jadwal`)، وشواهدُ المعنى هي `Waqi.shuhud` على تلك القضيّة بسجلّ المودَعات (`bina_shuhud`):
    لا موضعَ يُكتب، ولا شاهدَ إلّا لقضيّةٍ حكمُها «مفهوم» في الجدول نفسِه.
    mudaa   <sha256>  <النوع: واقع-مختوم|وضع|معلومات-سابقة|مرجع-محجوب>  <الاسم>      (في السجلّ وحده)
    isdar   <الإصدار>
    qanun   <الاسم>  <مقدّمة|مقدّمة…>  <النتيجة>  <الوسم>
    asl     <القضيّة>  <الوسم>  <السند>  [<الطريقة: عقلي|علمي>]
    iddia   <القضيّة>  <الوسم المعلَن>  <خطوة|خطوة…>  <السند>
    shahid  <المعنى>  <الشيء>  <الخاصّة>  <القيمة>                      (في السجلّ وحده)
  القضيّة: نوع:أ:ب حيث النوع أحد: wad juz kharij luzum mutabaqa tadammun iltizam fi taht.
  الخطوة: a=<قضيّة> أو q=<رقم القانون>. السند: <أوّل 12 من البصمة>@<الموضع>…
  التشغيل: faahis <سجلّ> <محتوى>…   |   faahis --sual <بادئة القضيّة> <سجلّ> <محتوى>…
-/
import Std.Data.HashMap
import Aql.Qaida
import Aql.Mawsua
import Aql.Idaa
import Aql.QawaninDalala
import Aql.Maratib
import Aql.WaqiJadwal
import Faahis.SijillMakhtum

open Qaida Mawsua QawaninDalala Maratib

/-! ## القراءة -/

def wasmMin : String → Option Wasm
  | "رأي" => some .ray
  | "تقدير" => some .taqdir
  | "مقيس" => some .maqis
  | "مفحوص" => some .mafhus
  | "مطابق" => some .mutabaq
  | "مبرهن-على-الشاهد" => some .mubarhanShahid
  | "مبرهن" => some .mubarhan
  | _ => none

def wasmIsm : Nat → String
  | 0 => "رأي" | 1 => "تقدير" | 2 => "مقيس" | 3 => "مفحوص"
  | 4 => "مطابق" | 5 => "مبرهن-على-الشاهد" | _ => "مبرهن"

def nawMin : String → Option Idaa.Naw
  | "واقع-مختوم" => some .waqiMakhtum
  | "وضع" => some .wad
  | "معلومات-سابقة" => some .maalumatSabiqa
  | "مرجع-محجوب" => some .marjaMahjub
  | _ => none

def tariqaMin : String → Option Tariqa
  | "عقلي" => some .aqliyya
  | "علمي" => some .ilmiyya
  | _ => none

def bad12 (s : String) : String := String.ofList (s.toList.take 12)

/-- جدول المعرّفات: كلّ ذرّة (لفظ، معنى، عنوان) رقمٌ عند أوّل ورود. -/
structure Dhurrat where
  asma : Array String := #[]
  arqam : Std.HashMap String Nat := {}

def Dhurrat.raqm (d : Dhurrat) (s : String) : Dhurrat × Nat :=
  match d.arqam[s]? with
  | some n => (d, n)
  | none =>
    let ⟨asma, arqam⟩ := d
    let n := asma.size
    (⟨asma.push s, arqam.insert s n⟩, n)

def Dhurrat.ism (d : Dhurrat) (n : Nat) : String := d.asma.getD n s!"#{n}"

/-- قراءة قضيّة. جدول المعرّفات يُعاد دائمًا (ولو فشلت القراءة) ليبقى فريد المرجع. -/
def qadiyyaMin (d : Dhurrat) (s : String) : Dhurrat × Option Qadiyya :=
  match s.splitOn ":" with
  | [k, a, b] =>
    let (d, x) := d.raqm a
    let (d, y) := d.raqm b
    let q : Option Qadiyya := match k with
      | "wad" => some (.wad x y) | "juz" => some (.juz x y) | "kharij" => some (.kharij x y)
      | "luzum" => some (.luzum x y) | "mutabaqa" => some (.mutabaqa x y) | "tadammun" => some (.tadammun x y)
      | "iltizam" => some (.iltizam x y) | "fi" => some (.fi x y) | "taht" => some (.taht x y)
      | _ => none
    (d, q)
  | _ => (d, none)

def qadiyyaIsm (d : Dhurrat) : Qadiyya → String
  | .wad a b => s!"wad:{d.ism a}:{d.ism b}" | .juz a b => s!"juz:{d.ism a}:{d.ism b}"
  | .kharij a b => s!"kharij:{d.ism a}:{d.ism b}" | .luzum a b => s!"luzum:{d.ism a}:{d.ism b}"
  | .mutabaqa a b => s!"mutabaqa:{d.ism a}:{d.ism b}" | .tadammun a b => s!"tadammun:{d.ism a}:{d.ism b}"
  | .iltizam a b => s!"iltizam:{d.ism a}:{d.ism b}" | .fi a b => s!"fi:{d.ism a}:{d.ism b}"
  | .taht a b => s!"taht:{d.ism a}:{d.ism b}"

def qadayaMin (d : Dhurrat) (s : String) : Dhurrat × Option (List Qadiyya) :=
  (s.splitOn "|").foldl (fun (d, acc) t =>
    match acc with
    | none => (d, none)
    | some qs =>
      let (d, q) := qadiyyaMin d t
      (d, q.map fun q => qs ++ [q])) (d, some [])

def khatawatMin (d : Dhurrat) (s : String) : Dhurrat × Option (List (Khatwa Qadiyya)) :=
  (s.splitOn "|").foldl (fun (d, acc) t =>
    match acc with
    | none => (d, none)
    | some ks =>
      -- «a=» رأسٌ والباقي قضيّةٌ قد يحمل معناها «=» (شطرا بيتٍ في شرح المعجم: سطرا makhzan_kamil 138997 و139031،
      -- كانا خطأَي «سلسلة لا تُقرأ» يُسقطهما القارئ بصمت حتّى صار التحميلُ محقَّقًا)
      match t.splitOn "=" with
      | "a" :: baqi@(_ :: _) => let (d, q) := qadiyyaMin d ("=".intercalate baqi); (d, q.map fun q => ks ++ [.asl q])
      | ["q", i] => (d, i.toNat?.map fun i => ks ++ [.qanun i])
      | _ => (d, none)) (d, some [])

structure Asl where
  qadiyya : Qadiyya
  wasm    : Wasm
  tariqa  : Tariqa
  sanad   : String

structure Hal where
  dh      : Dhurrat := {}
  mudaat  : Array (String × Idaa.Naw) := #[]
  isdar   : Option String := none
  qawanin : Array (Qanun Qadiyya × Wasm) := #[]
  usul    : Array Asl := #[]
  iddiaat : Array (Nat × Qadiyya × Wasm × List (Khatwa Qadiyya) × String) := #[]
  shawahid : Array (Nat × String × String × String) := #[]
  akhta   : Array String := #[]

def khata (h : Hal) (n : Nat) (s : String) : Hal :=
  let ⟨dh, mudaat, isdar, qawanin, usul, iddiaat, shawahid, akhta⟩ := h
  ⟨dh, mudaat, isdar, qawanin, usul, iddiaat, shawahid, akhta.push s!"سطر {n}: {s}"⟩

/-- قراءة سطر. الحال تُفكّك إلى حقولها فتبقى مصفوفاتها فريدة المرجع وتُضاف إليها في مكانها
    (لا نسخَ للمصفوفة عند كلّ سطر). -/
def qira (h0 : Hal) (n : Nat) (line : String) : Hal :=
  let ⟨dh, mudaat, isdar, qawanin, usul, iddiaat, shawahid, akhta⟩ := h0
  if line.isEmpty then ⟨dh, mudaat, isdar, qawanin, usul, iddiaat, shawahid, akhta⟩ else
  match line.splitOn "\t" with
  | ["mudaa", basma, naw, _] =>
    match nawMin naw with
    | some k => if basma.length == 64 then ⟨dh, mudaat.push (bad12 basma, k), isdar, qawanin, usul, iddiaat, shawahid, akhta⟩
                else ⟨dh, mudaat, isdar, qawanin, usul, iddiaat, shawahid, akhta.push s!"سطر {n}: بصمة ليست sha256"⟩
    | none => ⟨dh, mudaat, isdar, qawanin, usul, iddiaat, shawahid, akhta.push s!"سطر {n}: نوع مودَع مجهول (الدستور م12)"⟩
  | ["isdar", v] => ⟨dh, mudaat, some v, qawanin, usul, iddiaat, shawahid, akhta⟩
  | ["qanun", ism, ms, nat, w] =>
    let (d, muq) := qadayaMin dh ms
    let (d, nat) := qadiyyaMin d nat
    match muq, nat, wasmMin w with
    | some muq, some nat, some w =>
      let r : Qanun Qadiyya := ⟨ism, muq, nat⟩
      if shakl r then ⟨d, mudaat, isdar, qawanin.push (r, w), usul, iddiaat, shawahid, akhta⟩
      else ⟨d, mudaat, isdar, qawanin, usul, iddiaat, shawahid, akhta.push s!"سطر {n}: قانون خارج القاعدة: {ism}"⟩
    | _, _, _ => ⟨d, mudaat, isdar, qawanin, usul, iddiaat, shawahid, akhta.push s!"سطر {n}: قانون لا يُقرأ"⟩
  | ["asl", p, w, s] | ["asl", p, w, s, _] =>
    let t : Option String := match line.splitOn "\t" with | [_, _, _, _, t] => some t | _ => none
    let (d, q) := qadiyyaMin dh p
    match q, wasmMin w, (t.map tariqaMin).getD (some .aqliyya) with
    | some q, some w, some t => ⟨d, mudaat, isdar, qawanin, usul.push ⟨q, w, t, s⟩, iddiaat, shawahid, akhta⟩
    | none, _, _ => ⟨d, mudaat, isdar, qawanin, usul, iddiaat, shawahid, akhta.push s!"سطر {n}: قضيّة لا تُقرأ"⟩
    | _, _, _ => ⟨d, mudaat, isdar, qawanin, usul, iddiaat, shawahid, akhta.push s!"سطر {n}: وسم أو طريقة مجهولة"⟩
  | ["iddia", p, w, ks, s] =>
    let (d, q) := qadiyyaMin dh p
    let (d, ks) := khatawatMin d ks
    match q, wasmMin w, ks with
    | some q, some w, some ks => ⟨d, mudaat, isdar, qawanin, usul, iddiaat.push (n, q, w, ks, s), shawahid, akhta⟩
    | _, _, none => ⟨d, mudaat, isdar, qawanin, usul, iddiaat, shawahid, akhta.push s!"سطر {n}: سلسلة لا تُقرأ"⟩
    | _, _, _ => ⟨d, mudaat, isdar, qawanin, usul, iddiaat, shawahid, akhta.push s!"سطر {n}: ادّعاء لا يُقرأ"⟩
  | ["shahid", m, mw, sf, qm] =>
    let (d, x) := dh.raqm m; ⟨d, mudaat, isdar, qawanin, usul, iddiaat, shawahid.push (x, mw, sf, qm), akhta⟩
  | "shahid" :: _ => ⟨dh, mudaat, isdar, qawanin, usul, iddiaat, shawahid, akhta.push s!"سطر {n}: شاهد لا يُقرأ (المعنى والشيء والخاصّة والقيمة)"⟩
  | _ => ⟨dh, mudaat, isdar, qawanin, usul, iddiaat, shawahid, akhta.push s!"سطر {n}: سجلّ لا يُعرف"⟩

/-! ## التحميل المحقَّق: السلطة من سجلّ المودَعات وحده (خطّة الإطلاق التجريبي، الحزمة P1-أ)

  كان الفاحص والقارئ يصلان أسطر الملفّات كلّها في سيلٍ واحد، فيقبلان سطر `mudaa` من أيّ ملفّ: محتوًى يُفحص كان يستطيع
  أن يسجّل لنفسه مودَعًا «واقعًا مختومًا» ببصمةٍ مصطنعة، ثمّ يستشهد به فيرفع معنًى إلى «مفهوم» (أُعيدت التجربة على
  1bff783؛ مثالُه `mawsua/fasid_haqn.tsv`). فصار للسطر مصدر: السجلُّ لا يحمل إلّا `mudaa` (`sijill_la_muhtawa`)، والمحتوى لا يحمل
  `mudaa` (`tahmil_mudaat`). وخطأُ التحميل يُسلَّم إلى الواجهات باسمه (`muhaqqaq`) فلا تجيب على قاعدةٍ جزئيّة بصمت.
  وما لا يسدّه هذا القسم: شاهدُ `shahid` بموضعٍ في مودَعٍ مسجَّلٍ حقًّا يُقبل بلا فحصٍ لوجود الموضع ولا لقضيّته، فيرفع معنًى إلى
  «مفهوم» من المحتوى (P2-أ)؛ والسجلّ هو الملفّ الذي يمرّره المستدعي أوّلًا، لا يُفحص أنّه `mudaat/sijill.tsv` المختوم (P1-ج). -/

/-- مصدرُ السطر: سجلُّ المودَعات (السلطة)، أو المحتوى الذي يُفحص. -/
inductive Masdar | sijill | muhtawa
deriving DecidableEq, Repr

/-- رأسُ السطر: حقلُه الأوّل قبل أوّل TAB. -/
def raas (line : String) : String := (line.splitOn "\t").headD ""

/-- سطرٌ يُتجاوز: فارغٌ، أو تعليقٌ أوّلُه «#». -/
def mutajawaz (line : String) : Bool := line.isEmpty || line.startsWith "#"

/-- قراءةُ سطرٍ بحسب مصدره: السجلُّ لا يحمل إلّا `mudaa` و`shahid`، والمحتوى لا يحمل أيًّا منهما؛ وما سوى ذلك `qira` نفسُها. -/
def qiraMin (m : Masdar) (h : Hal) (n : Nat) (line : String) : Hal :=
  if mutajawaz line then h
  else match m with
    | .sijill =>
      if raas line == "mudaa" || raas line == "shahid" then qira h n line
      else khata h n "السجلّ لا يحمل إلّا مودَعات (mudaa) وشواهد (shahid)"
    | .muhtawa =>
      if raas line == "mudaa" then khata h n "المحتوى لا يسجّل مودَعًا: السلطة في سجلّ المودَعات وحده"
      else if raas line == "shahid" then khata h n "المحتوى لا يربط معنًى بواقع: الربطُ في سجلّ المودَعات وحده"
      else qira h n line

/-- **لا يزيد `qira` المودَعاتِ إلّا من سطر `mudaa`**: سطرٌ رأسُه غيرُه يترك المودَعات كما هي. -/
theorem qira_mudaat (h : Hal) (n : Nat) (line : String) (hr : raas line ≠ "mudaa") :
    (qira h n line).mudaat = h.mudaat := by
  obtain ⟨dh, mudaat, isdar, qawanin, usul, iddiaat, shawahid, akhta⟩ := h
  unfold raas at hr
  unfold qira
  by_cases he : line.isEmpty = true
  · simp only [he, ite_true]
  · simp only [he, Bool.false_eq_true, ite_false]
    generalize line.splitOn "\t" = parts at hr ⊢
    split
    · simp at hr
    all_goals (repeat' split) <;> rfl

theorem khata_mudaat (h : Hal) (n : Nat) (s : String) : (khata h n s).mudaat = h.mudaat := by
  cases h; rfl

/-- **لا يزيد `qira` الشواهدَ إلّا من سطر `shahid`**. -/
theorem qira_shawahid (h : Hal) (n : Nat) (line : String) (hr : raas line ≠ "shahid") :
    (qira h n line).shawahid = h.shawahid := by
  obtain ⟨dh, mudaat, isdar, qawanin, usul, iddiaat, shawahid, akhta⟩ := h
  unfold raas at hr
  unfold qira
  by_cases he : line.isEmpty = true
  · simp only [he, ite_true]
  · simp only [he, Bool.false_eq_true, ite_false]
    generalize line.splitOn "\t" = parts at hr ⊢
    split <;> (try simp at hr) <;> (repeat' split) <;> rfl

theorem khata_shawahid (h : Hal) (n : Nat) (s : String) : (khata h n s).shawahid = h.shawahid := by
  cases h; rfl

/-- **سطرُ المحتوى لا يسجّل مودَعًا**، أيًّا كان. -/
theorem muhtawa_la_yudif_mudaa (h : Hal) (n : Nat) (line : String) :
    (qiraMin .muhtawa h n line).mudaat = h.mudaat := by
  unfold qiraMin
  by_cases hm : mutajawaz line = true
  · simp only [hm, ite_true]
  · simp only [hm, Bool.false_eq_true, ite_false]
    by_cases hr : raas line = "mudaa"
    · simp only [hr, beq_self_eq_true, ite_true, khata_mudaat]
    · have : (raas line == "mudaa") = false := by simpa using hr
      simp only [this, Bool.false_eq_true, ite_false]
      split
      · exact khata_mudaat h n _
      · exact qira_mudaat h n line hr

/-- **سطرُ المحتوى لا يربط معنًى بواقع** (القرار ٢-أ)، أيًّا كان: شواهدُ الحال بعده شواهدُها قبله. -/
theorem muhtawa_la_yashhad (h : Hal) (n : Nat) (line : String) :
    (qiraMin .muhtawa h n line).shawahid = h.shawahid := by
  unfold qiraMin
  by_cases hm : mutajawaz line = true
  · simp only [hm, ite_true]
  · simp only [hm, Bool.false_eq_true, ite_false]
    split
    · exact khata_shawahid h n _
    · split
      · exact khata_shawahid h n _
      · rename_i hs
        exact qira_shawahid h n line (by simpa using hs)

/-- ما يحمله المحتوى من الحال: الإصدار والقوانين والأصول والادّعاءات (لا المودَعات ولا الشواهد ولا الأخطاء ولا جدول المعرّفات). -/
def Hal.muhtawa (h : Hal) :
    Option String × Array (Qanun Qadiyya × Wasm) × Array Asl ×
      Array (Nat × Qadiyya × Wasm × List (Khatwa Qadiyya) × String) :=
  (h.isdar, h.qawanin, h.usul, h.iddiaat)

/-- **سطرا `mudaa` و`shahid` لا يحملان محتوى**: `qira` عليهما لا تغيّر إصدارًا ولا قانونًا ولا أصلًا ولا ادّعاءً. -/
theorem qira_mudaa_muhtawa (h : Hal) (n : Nat) (line : String) (hr : raas line = "mudaa" ∨ raas line = "shahid") :
    (qira h n line).muhtawa = h.muhtawa := by
  obtain ⟨dh, mudaat, isdar, qawanin, usul, iddiaat, shawahid, akhta⟩ := h
  unfold raas at hr
  unfold qira
  by_cases he : line.isEmpty = true
  · simp only [he, ite_true]
  · simp only [he, Bool.false_eq_true, ite_false]
    generalize line.splitOn "\t" = parts at hr ⊢
    split <;> (try simp at hr) <;> (repeat' split) <;> first | rfl | (simp at hr)

/-- **سطرُ السجلّ لا يحمل محتوى**، أيًّا كان. -/
theorem sijill_la_yahmil_muhtawa (h : Hal) (n : Nat) (line : String) :
    (qiraMin .sijill h n line).muhtawa = h.muhtawa := by
  unfold qiraMin
  by_cases hm : mutajawaz line = true
  · simp only [hm, ite_true]
  · simp only [hm, Bool.false_eq_true, ite_false]
    split
    · rename_i hr
      exact qira_mudaa_muhtawa h n line (by simpa [Bool.or_eq_true] using hr)
    · cases h; rfl

/-- التحميلُ من مصدرٍ واحد، بترقيم أسطره من 1. -/
def tahmilMin (m : Masdar) (h : Hal) (lines : List String) : Hal :=
  (lines.zipIdx 1).foldl (fun h (l, n) => qiraMin m h n l) h

/-- **المحتوى كلُّه لا يسجّل مودَعًا**: أيًّا كانت أسطره، تبقى مودَعات الحال كما كانت قبله. -/
theorem tahmil_muhtawa_mudaat (h : Hal) (lines : List String) :
    (tahmilMin .muhtawa h lines).mudaat = h.mudaat := by
  unfold tahmilMin
  generalize lines.zipIdx 1 = ps
  induction ps generalizing h with
  | nil => rfl
  | cons p ps ih => simp only [List.foldl_cons]; rw [ih, muhtawa_la_yudif_mudaa]

/-- **السجلُّ كلُّه لا يحمل محتوى**: أيًّا كانت أسطره، يبقى محتوى الحال كما كان قبله. -/
theorem tahmil_sijill_muhtawa (h : Hal) (lines : List String) :
    (tahmilMin .sijill h lines).muhtawa = h.muhtawa := by
  unfold tahmilMin
  generalize lines.zipIdx 1 = ps
  induction ps generalizing h with
  | nil => rfl
  | cons p ps ih => simp only [List.foldl_cons]; rw [ih, sijill_la_yahmil_muhtawa]

/-- **السجلُّ لا يحمل إلّا `mudaa` و`shahid`**: تحميلُه وحده لا يُدخل إصدارًا ولا قانونًا ولا أصلًا ولا ادّعاءً. -/
theorem sijill_la_muhtawa (lines : List String) :
    (tahmilMin .sijill {} lines).muhtawa = (none, #[], #[], #[]) := by
  rw [tahmil_sijill_muhtawa]; rfl

/-- التحميل: السجلُّ أوّلًا (وأخطاؤه تُسمّى «السجلّ»)، ثمّ المحتوى؛ ولكلٍّ ترقيمُه. -/
def tahmil (sijill muhtawa : List String) : Hal :=
  let h0 := tahmilMin .sijill {} sijill
  tahmilMin .muhtawa { h0 with akhta := h0.akhta.map ("السجلّ، " ++ ·) } muhtawa

/-- **المودَعاتُ مودَعاتُ السجلّ وحده**: لا يغيّرها المحتوى أيًّا كان. -/
theorem tahmil_mudaat (sijill muhtawa : List String) :
    (tahmil sijill muhtawa).mudaat = (tahmilMin .sijill {} sijill).mudaat := by
  unfold tahmil
  rw [tahmil_muhtawa_mudaat]

/-- **المحتوى كلُّه لا يربط معنًى بواقع**. -/
theorem tahmil_muhtawa_shawahid (h : Hal) (lines : List String) :
    (tahmilMin .muhtawa h lines).shawahid = h.shawahid := by
  unfold tahmilMin
  generalize lines.zipIdx 1 = ps
  induction ps generalizing h with
  | nil => rfl
  | cons p ps ih => simp only [List.foldl_cons]; rw [ih, muhtawa_la_yashhad]

/-- **الشواهدُ شواهدُ السجلّ وحده** (القرار ٢-أ): لا يغيّرها المحتوى أيًّا كان. -/
theorem tahmil_shawahid (sijill muhtawa : List String) :
    (tahmil sijill muhtawa).shawahid = (tahmilMin .sijill {} sijill).shawahid := by
  unfold tahmil
  rw [tahmil_muhtawa_shawahid]

/-- **بلا سجلّ لا مودَع**، أيًّا كان المحتوى. ومنه، استنتاجًا لا مبرهنةً على `bina`: لا أصلَ يُقبل (`Idaa.sijill_faregh`)،
    ولا شاهدَ يرفع معنًى إلى «مفهوم» (`Maratib.la_mafhum_bila_waqi`). -/
theorem bila_sijill_la_mudaa (muhtawa : List String) : (tahmil [] muhtawa).mudaat = #[] := by
  rw [tahmil_mudaat]; rfl

/-! ### السجلُّ المعتمد (الحزمة P1-ج)

  كان السجلُّ هو الملفّ الذي يمرّره المستدعي أوّلًا، بلا فحصٍ أنّه `mudaat/sijill.tsv` المختوم: فسجلٌّ آخر يمنح سلطته. فصار يُطابَق بأسطر
  `sijillMakhtum` (مولَّدٌ منه، `scripts/bina_sijill_makhtum.py --check`)، وغيرُه خطأُ تحميلٍ باسمه إلّا بـ`--ikhtibar` معلَنًا في الاستدعاء
  (سجلّاتُ الاختبار). -/

def khataSijillGhayrMutamad : String :=
  "السجلّ ليس سجلَّ المودَعات المختوم (mudaat/sijill.tsv): السلطةُ للمعتمد وحده، أو --ikhtibar معلَنًا"

/-- التحميلُ بالسجلّ المعتمد: `tahmil` بعينه، ومعه خطأٌ باسمه إن خالف السجلُّ المعتمدَ ولم يُعلَن الاختبار. -/
def tahmilMutamad (ikhtibar : Bool) (sijill muhtawa : List String) : Hal :=
  let h := tahmil sijill muhtawa
  if ikhtibar || sijill == sijillMakhtum then h else { h with akhta := h.akhta.push khataSijillGhayrMutamad }

/-- ما يُسلَّم إلى الواجهات: الحالُ إن خلت من أخطاء التحميل، وإلّا الأخطاءُ بأسمائها — وخطأُ التحميل غيرُ «لا حكم». -/
def muhaqqaq (h : Hal) : Except (Array String) Hal :=
  if h.akhta.isEmpty then .ok h else .error h.akhta

/-- لا تُسلَّم حالٌ فيها خطأ تحميل. -/
theorem muhaqqaq_salim (h h' : Hal) (hk : muhaqqaq h = .ok h') : h' = h ∧ h.akhta = #[] := by
  unfold muhaqqaq at hk
  split at hk
  · rename_i he; cases hk; exact ⟨rfl, Array.isEmpty_iff.mp he⟩
  · cases hk

/-- **لا تُسلَّم حالٌ بسجلٍّ غيرِ معتمد** إلّا بالاختبار المعلَن: إن سلّم `muhaqqaq` حالَ `tahmilMutamad false` فالسجلُّ هو المختومُ بأسطره،
    والحالُ حالُ `tahmil` نفسِها. -/
theorem mutamad_salim (sijill muhtawa : List String) (h : Hal) (hk : muhaqqaq (tahmilMutamad false sijill muhtawa) = .ok h) :
    sijill = sijillMakhtum ∧ h = tahmil sijill muhtawa := by
  unfold tahmilMutamad at hk
  by_cases he : (sijill == sijillMakhtum) = true
  · rw [if_pos (by simp [he])] at hk
    exact ⟨by simpa using he, (muhaqqaq_salim _ _ hk).1⟩
  · rw [if_neg (by simpa using he)] at hk
    have := (muhaqqaq_salim _ _ hk).2
    simp [Array.push] at this

/-- **والاختبارُ المعلَن لا يزيد على `tahmil`**: هو هو. -/
theorem ikhtibar_tahmil (sijill muhtawa : List String) : tahmilMutamad true sijill muhtawa = tahmil sijill muhtawa := by
  simp [tahmilMutamad]

/-! ## البناء -/

/-! ### جدولُ الأصول (س1؛ قولُ المالك 2026-10-24، 18:07)

  كان الأصلُ يُطلب بـ `h.usul.find?` في كلّ سؤالٍ عنه، أي مرورًا على ما قبله من الأصول. `jadwalUsul` يبنيها مرّةً جدولَ تجزئةٍ،
  وأوّلُ أصلٍ لكلّ قضيّةٍ هو الباقي (`insertIfNew`)، كما في `find?`: `jadwalUsul_find` لكلّ مصفوفة أصول، و`bina_asl` على
  `bina` نفسِها. فالبحثُ واحدٌ بالطريقين، والزمنُ وحده يتغيّر. -/

deriving instance Hashable for QawaninDalala.Qadiyya

/-- جدولُ الأصول بالقضيّة: أوّلُ أصلٍ لكلّ قضيّة. -/
def jadwalUsul (usul : Array Asl) : Std.HashMap Qadiyya Asl :=
  usul.foldl (fun m a => m.insertIfNew a.qadiyya a) ∅

/-- الطيُّ على قائمة: الجدولُ بعده ما كان فيه، وإلّا أوّلُ أصلٍ في القائمة لتلك القضيّة. -/
theorem jadwalUsul_foldl (l : List Asl) (m : Std.HashMap Qadiyya Asl) (p : Qadiyya) :
    (l.foldl (fun m a => m.insertIfNew a.qadiyya a) m)[p]? = (m[p]?).or (l.find? (·.qadiyya == p)) := by
  induction l generalizing m with
  | nil => simp
  | cons a l ih =>
    rw [List.foldl_cons, ih, List.find?_cons, Std.HashMap.getElem?_insertIfNew]
    by_cases hp : a.qadiyya = p
    · subst hp
      by_cases hm : a.qadiyya ∈ m <;> simp [hm]
    · have hb : (a.qadiyya == p) = false := by simpa using hp
      simp [hb]

/-- **التكافؤ:** البحثُ في الجدول هو `find?` على الأصول. -/
theorem jadwalUsul_find (usul : Array Asl) (p : Qadiyya) :
    (jadwalUsul usul)[p]? = usul.find? (·.qadiyya == p) := by
  rw [jadwalUsul, ← Array.foldl_toList, jadwalUsul_foldl, Std.HashMap.getElem?_empty, Option.none_or,
    Array.find?_toList]

structure Bina where
  q    : Qaida.Qaida Qadiyya
  /-- القوانينُ مصفوفةً، وقائمتُها قائمةُ القاعدة (`hq`): بها يُفحص (`Qaida.maqbulA_eq`). -/
  qs   : Array (Qaida.Qanun Qadiyya)
  hq   : q.qawanin = qs.toList
  aslB : Qadiyya → Bool
  aslW : Qadiyya → Wasm
  qW   : Nat → Wasm
  asl? : Qadiyya → Option Asl
  shuhud : Nat → List ShahidWaqi

/-- المودَعُ يطابق السند: بصمتُه غيرُ فارغة، والسندُ يبدأ بها. -/
def mutabiqSanad (s : String) (m : String × Idaa.Naw) : Bool := !m.1.isEmpty && s.startsWith m.1

/-- مودَعُ السند: أوّلُ مودَعٍ مسجَّلٍ يطابق السندَ (`mutabiqSanad`). -/
def mudaaSanad? (mudaat : Array (String × Idaa.Naw)) (s : String) : Option (String × Idaa.Naw) :=
  mudaat.toList.find? (mutabiqSanad s)

/-- نوعُ مودَعِ السند (سقفُ وسمه): نوعُ `mudaaSanad?`، وإلّا «مرجع محجوب» (أدنى السقوف). -/
def nawSanadMin (mudaat : Array (String × Idaa.Naw)) (s : String) : Idaa.Naw :=
  ((mudaaSanad? mudaat s).map (·.2)).getD .marjaMahjub

/-- **مودَعُ السند يُوجد حيث يُقبل السند، لا غير**: وجودُ `mudaaSanad?` هو قبولُ `Idaa.aslMusajjal` للسند على بصمات
    المودَعات نفسِها. -/
theorem nawSanad_aslMusajjal (mudaat : Array (String × Idaa.Naw)) (s : String) :
    (mudaaSanad? mudaat s).isSome =
      Idaa.aslMusajjal (fun _ : Unit => some s) (mudaat.toList.map (·.1)) () := by
  unfold mudaaSanad? Idaa.aslMusajjal
  apply Bool.eq_iff_iff.mpr
  rw [List.find?_isSome, List.any_eq_true]
  constructor
  · rintro ⟨m, hm, hp⟩; exact ⟨m.1, List.mem_map_of_mem hm, hp⟩
  · rintro ⟨b, hb, hp⟩
    obtain ⟨m, hm, rfl⟩ := List.mem_map.mp hb
    exact ⟨m, hm, hp⟩

/-- **لا سقفَ فوق «مرجع محجوب» إلّا لسندٍ مقبول**: إن أعطى `nawSanadMin` نفسُه سندًا نوعًا غيرَ «مرجع محجوب» فـ
    `Idaa.aslMusajjal` يقبله. (والعكسُ لا يلزم: سندٌ مقبولٌ مودَعُه «مرجع محجوب» نوعُه «مرجع محجوب».) -/
theorem nawSanad_sanad (mudaat : Array (String × Idaa.Naw)) (s : String)
    (h : nawSanadMin mudaat s ≠ .marjaMahjub) :
    Idaa.aslMusajjal (fun _ : Unit => some s) (mudaat.toList.map (·.1)) () = true := by
  rw [← nawSanad_aslMusajjal]
  unfold nawSanadMin at h
  cases hm : mudaaSanad? mudaat s with
  | none => rw [hm] at h; exact absurd rfl h
  | some m => rfl

/-- **السندُ الفارغ لا يأخذ نوعًا** (على الشاهد): سندٌ فارغٌ مع سجلٍّ فيه بصمةٌ سليمةٌ وأخرى فارغة يبقى «مرجع محجوب». -/
theorem nawSanad_sanad_farigh : nawSanadMin #[("", .wad), ("abc", .wad)] "" = .marjaMahjub := by
  decide +kernel

/-- **القيدُ الفارغ لا يعطي سندًا نوعَه** (على الشاهد): قيدٌ فارغٌ من نوع «وضع» قبل القيد الحقيقيّ لا يرفع سندًا من «مرجع
    محجوب» إلى سقف «وضع». -/
theorem nawSanad_basma_farigha :
    nawSanadMin #[("", .wad), ("abc", .marjaMahjub)] "abc@1" = .marjaMahjub ∧
    nawSanadMin #[("abc", .wad)] "abc@1" = .wad := by
  decide +kernel

/-- **شواهدُ المعنى من قضاياه** (P2-أ): لكلّ قضيّةٍ يربطها السجلُّ بالمعنى، `Waqi.shuhud` عليها في جدول «الواقع المختوم» المضمَّن
    (`Waqi.Jadwal`) بسجلّ المودَعات؛ فلا شاهدَ إلّا لقضيّةٍ حكمُها «مفهوم» هناك، ومواضعُ الشواهد صفوفُها بعينها. -/
def shuhudBina (h : Hal) (m : Nat) : List ShahidWaqi :=
  (h.shawahid.filter (·.1 == m)).toList.flatMap fun r =>
    Waqi.shuhud h.mudaat.toList (fun _ => Waqi.Jadwal.basma) Waqi.Jadwal.jadwal r.2.1 r.2.2.1 r.2.2.2

def bina (h : Hal) (isdar : String) : Bina :=
  let jadwal := jadwalUsul h.usul
  let asl? (p : Qadiyya) : Option Asl := jadwal[p]?
  let sijill := (h.mudaat.map (·.1)).toList
  let nawSanad (s : String) : Idaa.Naw := nawSanadMin h.mudaat s
  let qs := h.qawanin.map (·.1)
  { q := ⟨isdar, qs.toList⟩
    qs := qs
    hq := rfl
    aslB := fun p => Idaa.aslMusajjal (fun x => (asl? x).map (·.sanad)) sijill p
    aslW := fun p => ((asl? p).map fun a => qayd a.tariqa (Idaa.qaydMudaa (nawSanad a.sanad) a.wasm)).getD .ray
    qW := fun i => ((h.qawanin[i]?).map (·.2)).getD .ray
    asl? := asl?
    shuhud := shuhudBina h }

/-- **شواهدُ الفاحص هي `Waqi.shuhud`** على القضايا التي يربطها السجلُّ بالمعنى (بوابة P2-أ). -/
theorem bina_shuhud (h : Hal) (isdar : String) (m : Nat) :
    (bina h isdar).shuhud m = (h.shawahid.filter (·.1 == m)).toList.flatMap fun r =>
      Waqi.shuhud h.mudaat.toList (fun _ => Waqi.Jadwal.basma) Waqi.Jadwal.jadwal r.2.1 r.2.2.1 r.2.2.2 := rfl

/-- **كلُّ شاهدٍ صفٌّ لقضيّته في الجدول المختوم**: لكلّ شاهدٍ لمعنًى ربطٌ في الحال لذلك المعنى بقضيّة، وصفٌّ في `Waqi.Jadwal` يطابقها
    شيئًا وخاصّةً وقيمة، والشاهدُ بصمةُ الدفعة وموضعُ ذلك الصفّ؛ وحكمُ القضيّة في الجدول «مفهوم». فلا موضعَ مكتوب، ولا صفَّ لقضيّةٍ أخرى. -/
theorem shuhud_saff (h : Hal) (isdar : String) (m : Nat) (w : ShahidWaqi) (hw : w ∈ (bina h isdar).shuhud m) :
    ∃ r ∈ h.shawahid.toList, r.1 = m ∧
      Waqi.hukm h.mudaat.toList (fun _ => Waqi.Jadwal.basma) Waqi.Jadwal.jadwal r.2.1 r.2.2.1 r.2.2.2 = .mafhum ∧
      ∃ s ∈ Waqi.Jadwal.jadwal, s.mawdu = r.2.1 ∧ s.sifa = r.2.2.1 ∧ s.qima = r.2.2.2 ∧
        w = ⟨Waqi.Jadwal.basma, s.raqm⟩ := by
  rw [bina_shuhud, List.mem_flatMap] at hw
  obtain ⟨r, hr, hw⟩ := hw
  rw [Array.toList_filter, List.mem_filter] at hr
  refine ⟨r, hr.1, by simpa using hr.2, ?_⟩
  unfold Waqi.shuhud at hw
  split at hw
  · rename_i hh
    refine ⟨hh, ?_⟩
    rw [List.mem_map] at hw
    obtain ⟨s, hs, rfl⟩ := hw
    unfold Waqi.makhtuma Waqi.mutabiq at hs
    rw [List.mem_filter, List.mem_filter] at hs
    obtain ⟨⟨hs, hm⟩, _⟩ := hs
    simp only [Bool.and_eq_true, beq_iff_eq] at hm
    exact ⟨s, hs, hm.1.1, hm.1.2, hm.2, rfl⟩
  · simp at hw

/-- أصلُ القضيّة في البناء هو أوّلُ أصلٍ لها في الأصول، كما كان بـ `find?` (س1). -/
theorem bina_asl (h : Hal) (isdar : String) (p : Qadiyya) :
    (bina h isdar).asl? p = h.usul.find? (·.qadiyya == p) :=
  jadwalUsul_find h.usul p

/-- وحكمُ «مودَع» على الأصل (`aslB`، وبه يقبل الفاحص) هو حكمُه على أوّل أصلٍ للقضيّة بـ `find?`، كما كان (س1). -/
theorem bina_aslB (h : Hal) (isdar : String) (p : Qadiyya) :
    (bina h isdar).aslB p =
      Idaa.aslMusajjal (fun x => (h.usul.find? (·.qadiyya == x)).map (·.sanad)) (h.mudaat.map (·.1)).toList p := by
  simp only [bina, jadwalUsul_find]

/-- ووسمُ الأصل (`aslW`، وبه تُحسب قوّة السلسلة) هو وسمُ أوّل أصلٍ للقضيّة بـ `find?` بعد قيدَيه، كما كان (س1). -/
theorem bina_aslW (h : Hal) (isdar : String) (p : Qadiyya) :
    (bina h isdar).aslW p =
      ((h.usul.find? (·.qadiyya == p)).map fun a =>
        qayd a.tariqa (Idaa.qaydMudaa (nawSanadMin h.mudaat a.sanad) a.wasm)).getD .ray := by
  simp only [bina, jadwalUsul_find]

/-- وقاعدةُ البناء قوانينُ المحتوى بترتيبها، بإصدارها (س1: الفحصُ على `qs` يكافئها بـ `hq`). -/
theorem bina_q (h : Hal) (isdar : String) :
    (bina h isdar).q = ⟨isdar, (h.qawanin.map (·.1)).toList⟩ := rfl

def tatabbu (h : Hal) (b : Bina) (c : Iddia Qadiyya) : IO Unit := do
  let d := h.dh
  IO.println s!"  القول: {qadiyyaIsm d c.qawl}  — وسمه المحسوب: {wasmIsm (quwwatSilsila b.aslW b.qW c.silsila)}"
  for k in c.silsila do
    match k with
    | .asl p =>
      match b.asl? p with
      | some a => IO.println s!"    أصل  {qadiyyaIsm d p}  [{wasmIsm (b.aslW p).quwwa}]  سند: {a.sanad}"
      | none => IO.println s!"    أصل  {qadiyyaIsm d p}  [غير مودَع]"
    | .qanun i =>
      match h.qawanin[i]? with
      | some (r, w) =>
        IO.println s!"    قانون {i} «{r.ism}»: {" + ".intercalate (r.muqaddimat.map (qadiyyaIsm d))} ⊢ {qadiyyaIsm d r.natija}  [{wasmIsm w.quwwa}]"
      | none => IO.println s!"    قانون {i}  [غير موجود]"
  -- مراتب المخرج الثلاث (م15)
  for x in mukhraj b.shuhud c.qawl do
    match x with
    | .minHaythuHiya _ => IO.println s!"    مرتبة القضيّة: من حيث هي"
    | .maaluma m => IO.println s!"    المعنى «{d.ism m}»: معلومة (لا شاهد واقعٍ مودَع)"
    | .mafhum m sh _ => IO.println s!"    المعنى «{d.ism m}»: مفهوم (شواهد واقع: {sh.length})"

def faahis (h : Hal) (b : Bina) (isdar : String) : IO UInt32 := do
  let mut marfud := 0
  for (n, p, w, ks, _) in h.iddiaat do
    let quwwa := quwwatSilsila b.aslW b.qW ks
    -- `maqbulA` على مصفوفة القوانين هو `maqbul b.q` بعينه (`Qaida.maqbulA_eq` بـ `b.hq`)
    if !(maqbulA b.qs b.aslB ⟨p, ks⟩) then
      IO.println s!"{n}\tمرفوض\tسلسلة لا يقبلها الفاحص"; marfud := marfud + 1
    else if w.quwwa > quwwa then
      IO.println s!"{n}\tمرفوض\tوسم فوق سنده"; marfud := marfud + 1
    else
      IO.println s!"{n}\tمقبول\t{quwwa}"
  for e in h.akhta do IO.println s!"خطأ\t{e}"
  IO.println s!"القاعدة {isdar}: مودَعات {h.mudaat.size}، قوانين {h.qawanin.size}، أصول {h.usul.size}، ادّعاءات {h.iddiaat.size}، مرفوض {marfud}، أخطاء {h.akhta.size}"
  return (if marfud == 0 && h.akhta.isEmpty then 0 else 1)

def sualMain (h : Hal) (b : Bina) (badia : String) : IO UInt32 := do
  -- `udkhulA` هو `udkhul` بعينه (`Mawsua.udkhulA_eq`)
  let s := h.iddiaat.foldl (fun (s : Makhzan b.q b.aslB) (_, p, _, ks, sn) =>
    s.udkhulA b.qs b.hq ⟨⟨p, ks⟩, sn⟩) (Makhzan.faregh b.q b.aslB)
  match sual s (fun p => (qadiyyaIsm h.dh p).startsWith badia) with
  | .laHukm =>
    IO.println s!"لا حكم: لا مدخل في المخزن يوافق «{badia}». الغياب ليس امتناعًا."
    return 0
  | .hukm j _ =>
    IO.println s!"حكم ({j.iddiaat.length}) بالقاعدة {b.q.isdar}:"
    for c in j.iddiaat do tatabbu h b c
    let (a, m, f) := ihsa (j.iddiaat.flatMap fun c => mukhraj b.shuhud c.qawl)
    IO.println s!"الفهرس: من حيث هي {a}، معلومة {m}، مفهوم {f}"
    return 0
