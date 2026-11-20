import Dal.Makharij
import Dal.Adad
import Aql.Mawsua
import Aql.Maratib
import Nabt.Bridges
import Nabt.LicensedDerivation
import Nabt.RationalInquiry

/-!
# الجسر المحلي إلى NABT المثبّت

يربط هذا الملف تعريفات Mashru الفعلية بمكتبة `Nabt/` في Mashru (منقولةٌ من sonaiso/NABT@3dbe335؛
كانت حزمةً مضمَّنة في `integrations/nabt`). لا يساوي الرقمين الخامّين: ترتيب المخارج في Mashru
غير الترتيب الأبجدي في NABT. يثبت النقل والفكّ وحفظ الاسم والحركة والترتيب
والعدد المشروط بترميزه، ثم يستعمل جبر الاشتقاق المرخّص على خلايا Mashru نفسها.

الاشتقاق مشروط بالمخزون والتأويلات المعطاة في `Context`. لا يحوّل هذا الملف
الترقيم إلى شاهد لغوي، ولا الفحص المنطقي إلى ختم مودَع، ولا الترخيص الشرطي
إلى حكم على الواقع. ترتيب الوسم وطريقة البحث وشواهد الواقع من تعريفات Mashru
القائمة؛ الشواهد والتصنيفات في واجهة الفحص فروض مصرّح بها وليست سلطة مكتسبة.

براهين الجداول المنتهية مسمّاة صراحة؛ براهين القوائم والأشجار عامة في طولها.
تظل SLGE ومراتب المعنى الأصلية دون تعديل.
نطاق النقل هنا خلايا `Dal.Khaliya`: رمز حدّ الكلمة 116 خارج هذا النوع.
مواضع المصدر مواضع خلايا معلنة؛ ليست إحداثيات بايت أو محارف Unicode مستنتجة.
-/

namespace Jisr.NabtBridge

/-! ## ١. الخلية الحقيقية، لا رقم بلا أبجدية -/

def cellToNabt (cell : Dal.Khaliya) : Nabt.Atom :=
  Nabt.Bridges.convertCell .mashruDal .nabt (Dal.n cell)

def cellFromNabt (atom : Nabt.Atom) : Dal.Khaliya :=
  Dal.fakk (Nabt.Bridges.convertCell .nabt .mashruDal atom)

theorem cell_roundtrip (cell : Dal.Khaliya) :
    cellFromNabt (cellToNabt cell) = cell := by
  simp only [cellFromNabt, cellToNabt, Nabt.Bridges.convertCell_inverse, Dal.fakk_n]

theorem atom_roundtrip (atom : Nabt.Atom) :
    cellToNabt (cellFromNabt atom) = atom := by
  simp only [cellToNabt, cellFromNabt, Dal.n_fakk, Nabt.Bridges.convertCell_inverse]

theorem cell_transport_injective : Function.Injective cellToNabt := by
  intro left right same
  have restored := congrArg cellFromNabt same
  simpa only [cell_roundtrip] using restored

/-- مطابقة جدول NABT المعلن إلى جدول Mashru الفعلي، بكل حوامل الجدول. -/
theorem carrier_names : ∀ carrier : Dal.Hamil,
    Nabt.canonicalCarriers.getD
        (Nabt.Bridges.toCanonicalCarrier .mashruDal carrier).val "" =
      String.singleton (Dal.harf carrier) := by
  decide

theorem cell_decode_native (cell : Dal.Khaliya) :
    Nabt.Cell.decode (Dal.n cell) = ⟨cell.hamil, cell.hala⟩ := by
  change Nabt.Cell.decode (Nabt.Cell.encode ⟨cell.hamil, cell.hala⟩) = _
  exact Nabt.Cell.decode_encode _

theorem cell_preserves_mark (cell : Dal.Khaliya) :
    (Nabt.Cell.decode (cellToNabt cell)).mark = cell.hala := by
  rw [cellToNabt, Nabt.Bridges.convertCell_preserves_mark, cell_decode_native]

theorem cell_preserves_name (cell : Dal.Khaliya) :
    Nabt.canonicalCarriers.getD (Nabt.Cell.decode (cellToNabt cell)).carrier.val "" =
      String.singleton (Dal.harf cell.hamil) := by
  simp only [cellToNabt, Nabt.Bridges.convertCell, Nabt.Bridges.encodeCell,
    Nabt.Cell.decode_encode, Nabt.Bridges.fromCanonicalCarrier,
    Nabt.Bridges.decodeCell, cell_decode_native]
  exact carrier_names cell.hamil

/-- شاهد مضاد لاستعمال رقم Mashru بوصفه رقم NABT: كَ = 32 هنا و84 هناك. -/
theorem numeric_identity_is_wrong :
    Dal.n (⟨8, 0⟩ : Dal.Khaliya) = 32 ∧
    cellToNabt (⟨8, 0⟩ : Dal.Khaliya) = 84 ∧
    cellToNabt (⟨8, 0⟩ : Dal.Khaliya) ≠ Dal.n (⟨8, 0⟩ : Dal.Khaliya) := by
  decide

def cellsToNabt (cells : List Dal.Khaliya) : List Nabt.Atom := cells.map cellToNabt
def cellsFromNabt (atoms : List Nabt.Atom) : List Dal.Khaliya := atoms.map cellFromNabt

theorem cells_roundtrip (cells : List Dal.Khaliya) :
    cellsFromNabt (cellsToNabt cells) = cells := by
  simp [cellsFromNabt, cellsToNabt, List.map_map, Function.comp_def, cell_roundtrip]

theorem atoms_roundtrip (atoms : List Nabt.Atom) :
    cellsToNabt (cellsFromNabt atoms) = atoms := by
  simp [cellsFromNabt, cellsToNabt, List.map_map, Function.comp_def, atom_roundtrip]

theorem cells_length (cells : List Dal.Khaliya) :
    (cellsToNabt cells).length = cells.length := by simp [cellsToNabt]

theorem cells_append (left right : List Dal.Khaliya) :
    cellsToNabt (left ++ right) = cellsToNabt left ++ cellsToNabt right := by
  simp [cellsToNabt]

theorem cells_injective : Function.Injective cellsToNabt := by
  intro left right same
  have restored := congrArg cellsFromNabt same
  simpa only [cells_roundtrip] using restored

/-- القانون الحسابي في Dal.Adad، متصل بالتعريف الفعلي في NABT. -/
theorem little_number_native (atoms : List Nabt.Atom) :
    Nabt.Sequence.little atoms = Dal.Adad.adadR (atoms.map Fin.val) := by
  induction atoms with
  | nil => rfl
  | cons atom atoms ih =>
    simp only [Nabt.Sequence.little, List.map_cons, Dal.Adad.adadR, ih]
    omega

theorem number_native (atoms : List Nabt.Atom) :
    Nabt.Bridges.encodeNumber .mashruAdad atoms =
      Dal.Adad.adad (atoms.map Fin.val) := by
  simp only [Nabt.Bridges.encodeNumber, Nabt.Bridges.orient,
    Nabt.Sequence.encode, Dal.Adad.adad, little_number_native, List.map_reverse]

theorem number_transport (cells : List Dal.Khaliya) :
    Nabt.Bridges.convertNumber .mashruAdad .nabtB116
        (Dal.Adad.adad (cells.map (fun cell => (Dal.n cell).val))) =
      Nabt.Sequence.encode (cellsToNabt cells) := by
  have native := number_native (cells.map Dal.n)
  simp only [List.map_map, Function.comp_def] at native
  rw [← native]
  unfold Nabt.Bridges.convertNumber
  rw [Nabt.Bridges.decodeNumber_encodeNumber]
  simp only [Nabt.Bridges.NumberCodec.alphabet, Nabt.Bridges.encodeNumber,
    Nabt.Bridges.orient, Nabt.Bridges.convertCells, List.map_map,
    cellsToNabt, Function.comp_def]
  rfl

/-! ## ٢. مصدر كامل وحدود ثابتة، مع تغيير تمثيل خلاياه فقط -/

def mapSource (convert : α → β) (source : Nabt.UnitDiscovery.Source α) :
    Nabt.UnitDiscovery.Source β :=
  ⟨source.sourceId, source.revision, source.scopeId, source.atomizationId,
    source.atoms.map convert⟩

def sourceToNabt := mapSource cellToNabt
def sourceFromNabt := mapSource cellFromNabt

theorem source_roundtrip (source : Nabt.UnitDiscovery.Source Dal.Khaliya) :
    sourceFromNabt (sourceToNabt source) = source := by
  cases source
  simp [sourceFromNabt, sourceToNabt, mapSource, List.map_map, Function.comp_def, cell_roundtrip]

theorem canonical_source_roundtrip (source : Nabt.UnitDiscovery.Source Nabt.Atom) :
    sourceToNabt (sourceFromNabt source) = source := by
  cases source
  simp [sourceFromNabt, sourceToNabt, mapSource, List.map_map, Function.comp_def, atom_roundtrip]

theorem source_metadata (source : Nabt.UnitDiscovery.Source Dal.Khaliya) :
    (sourceToNabt source).sourceId = source.sourceId ∧
    (sourceToNabt source).revision = source.revision ∧
    (sourceToNabt source).scopeId = source.scopeId ∧
    (sourceToNabt source).atomizationId = source.atomizationId := by
  exact ⟨rfl, rfl, rfl, rfl⟩

theorem source_injective : Function.Injective sourceToNabt := by
  intro left right same
  have restored := congrArg sourceFromNabt same
  simpa only [source_roundtrip] using restored

/-- النقل خلية بخلية؛ لا يغيّر التقطيع المعلن ولا يَحذف فراغًا من المصدر. -/
theorem valid_span_iff (source : Nabt.UnitDiscovery.Source Dal.Khaliya)
    (span : Nabt.UnitDiscovery.Span) :
    Nabt.UnitDiscovery.ValidSpan (sourceToNabt source) span ↔
      Nabt.UnitDiscovery.ValidSpan source span := by
  simp [Nabt.UnitDiscovery.ValidSpan, sourceToNabt, mapSource]

theorem span_atoms (source : Nabt.UnitDiscovery.Source Dal.Khaliya)
    (span : Nabt.UnitDiscovery.Span) :
    Nabt.UnitDiscovery.spanAtoms (sourceToNabt source) span =
      cellsToNabt (Nabt.UnitDiscovery.spanAtoms source span) := by
  simp [Nabt.UnitDiscovery.spanAtoms, sourceToNabt, mapSource, cellsToNabt]

/-! ## ٣. الاشتقاق المرخّص على خلايا Mashru الأصلية -/

abbrev NativeTree := Nabt.LicensedDerivation.Tree Dal.Khaliya
abbrev NativeContext := Nabt.LicensedDerivation.Context Dal.Khaliya

/-- سجل يحمل السياق والشجرة والبرهان الشرطي، لا وسم قبول يمرره المستدعي. -/
structure NativeCertificate where
  context : NativeContext
  tree : NativeTree
  licensed : Nabt.LicensedDerivation.Licensed context tree

theorem certificate_source (certificate : NativeCertificate) :
    certificate.tree.source ∈ certificate.context.inventory :=
  Nabt.LicensedDerivation.licensed_source_member _ _ certificate.licensed

theorem certificate_reconstruct (certificate : NativeCertificate) :
    certificate.tree.reconstruct = certificate.tree.source.atoms :=
  Nabt.LicensedDerivation.licensed_reconstruct _ _ certificate.licensed

theorem certificate_bounds (certificate : NativeCertificate) :
    certificate.tree.start < certificate.tree.stop ∧
    certificate.tree.stop ≤ certificate.tree.source.atoms.length :=
  Nabt.LicensedDerivation.licensed_bounds _ _ certificate.licensed

theorem certificate_transport_reconstruct (certificate : NativeCertificate) :
    cellsToNabt certificate.tree.reconstruct =
      (sourceToNabt certificate.tree.source).atoms := by
  rw [certificate_reconstruct]
  rfl

/-- يبقى الشرط مستقلًا عن ترخيص الدال الصوتي أو نجاح ترميز العدد. -/
theorem no_composite_without_evidence (context : NativeContext) (tree : NativeTree)
    (empty : context.offered = []) (composite : tree ∈ tree.steps)
    (mandatory : 0 ∈ tree.required) :
    ¬ Nabt.LicensedDerivation.Licensed context tree :=
  Nabt.LicensedDerivation.no_offered_composite_license context tree empty composite mandatory

theorem certificate_join_boundary (context : NativeContext)
    (tag : Nabt.LicensedDerivation.Tag) (left right : NativeTree)
    (licensed : Nabt.LicensedDerivation.Licensed context (.join tag left right)) :
    left.source = right.source ∧ left.stop = right.start :=
  Nabt.LicensedDerivation.licensed_join_original_adjacency context tag left right licensed

/-! ## ٤. الوسم وطريقة البحث من Mashru؛ لا ترقية من اسم NABT -/

/-- الفحوص فروض محسوبة من الدليل خارج هذا التعريف؛ هذه الدالة لا تصدّق مصدرها.
    الرتبتان تُحسبان من الوسمين الفعليين، وقيد الطريقة يسبق الفحص. -/
def inquiryChecks (checks : Nabt.RationalInquiry.Checks)
    (requested evidence : Mawsua.Wasm) (method : Mawsua.Tariqa) :
    Nabt.RationalInquiry.Checks :=
  { checks with
      requestedRank := requested.quwwa
      evidenceRank := (Mawsua.qayd method evidence).quwwa }

def assessInquiry (checks : Nabt.RationalInquiry.Checks)
    (requested evidence : Mawsua.Wasm) (method : Mawsua.Tariqa) :
    Nabt.RationalInquiry.Result :=
  Nabt.RationalInquiry.assess (inquiryChecks checks requested evidence method)

theorem inquiry_rank_bounded (checks : Nabt.RationalInquiry.Checks)
    (requested evidence : Mawsua.Wasm) (method : Mawsua.Tariqa) :
    (assessInquiry checks requested evidence method).authorizedRank ≤ evidence.quwwa := by
  exact Nat.le_trans
    (Nabt.RationalInquiry.authorized_rank_bounded (inquiryChecks checks requested evidence method))
    (Mawsua.qayd_la_yarfa method evidence)

theorem experimental_rank_bounded (checks : Nabt.RationalInquiry.Checks)
    (requested evidence : Mawsua.Wasm) :
    (assessInquiry checks requested evidence .ilmiyya).authorizedRank ≤
      Mawsua.Wasm.maqis.quwwa := by
  exact Nat.le_trans
    (Nabt.RationalInquiry.authorized_rank_bounded (inquiryChecks checks requested evidence .ilmiyya))
    (Mawsua.qayd_ilmi evidence)

theorem inquiry_requires_scope (checks : Nabt.RationalInquiry.Checks)
    (requested evidence : Mawsua.Wasm) (method : Mawsua.Tariqa)
    (licensed : (assessInquiry checks requested evidence method).verdict = .licensed) :
    checks.scopeCovered = true :=
  Nabt.RationalInquiry.licensed_requires_scope
    (inquiryChecks checks requested evidence method) licensed

theorem inquiry_requires_provenance (checks : Nabt.RationalInquiry.Checks)
    (requested evidence : Mawsua.Wasm) (method : Mawsua.Tariqa)
    (licensed : (assessInquiry checks requested evidence method).verdict = .licensed) :
    checks.provenance = true :=
  Nabt.RationalInquiry.licensed_requires_provenance
    (inquiryChecks checks requested evidence method) licensed

theorem inquiry_exhaustion_not_license (checks : Nabt.RationalInquiry.Checks)
    (requested evidence : Mawsua.Wasm) (method : Mawsua.Tariqa)
    (exhausted : checks.exhausted = true) :
    (assessInquiry checks requested evidence method).verdict ≠ .licensed :=
  Nabt.RationalInquiry.no_completion_from_exhaustion _ exhausted

/-- المخرج يحتفظ بالقناتين: فحص المطالبة، ومرتبة المعنى بحسب سجل Mashru.
    نتيجة الفحص لا تُضاف شاهدًا إلى سجلّ الواقع. -/
def reviewMeaning (checks : Nabt.RationalInquiry.Checks)
    (requested evidence : Mawsua.Wasm) (method : Mawsua.Tariqa)
    (registry : List (String × Idaa.Naw)) (meaning : Nat)
    (witnesses : List Maratib.ShahidWaqi) : Nabt.RationalInquiry.Result × Maratib.Mukhraj :=
  (assessInquiry checks requested evidence method,
    Maratib.martabatMaana meaning (Maratib.shuhudMutabara registry witnesses))

theorem no_meaning_promotion_without_world_witness (checks : Nabt.RationalInquiry.Checks)
    (requested evidence : Mawsua.Wasm) (method : Mawsua.Tariqa)
    (registry : List (String × Idaa.Naw))
    (noWorld : ∀ entry ∈ registry, entry.2 ≠ .waqiMakhtum)
    (meaning : Nat) (witnesses : List Maratib.ShahidWaqi) :
    (reviewMeaning checks requested evidence method registry meaning witnesses).2 =
      .maaluma meaning :=
  Maratib.la_mafhum_bila_waqi registry noWorld meaning witnesses

/-- حتى الترخيص في القناة الأولى لا يختم شاهدًا للواقع في الثانية. -/
theorem empty_registry_stays_information (checks : Nabt.RationalInquiry.Checks)
    (requested evidence : Mawsua.Wasm) (method : Mawsua.Tariqa)
    (meaning : Nat) (witnesses : List Maratib.ShahidWaqi) :
    (reviewMeaning checks requested evidence method [] meaning witnesses).2 =
      .maaluma meaning := by
  exact no_meaning_promotion_without_world_witness checks requested evidence method []
    (by simp) meaning witnesses

/-! ## ٥. شواهد حدود معلنة، لا نتائج اكتساب -/

def katabaCells : List Dal.Khaliya := [⟨8, 0⟩, ⟨18, 0⟩, ⟨26, 0⟩]

theorem kataba_transport :
    katabaCells.map (fun cell => (Dal.n cell).val) = [32, 72, 104] ∧
    (cellsToNabt katabaCells).map Fin.val = [84, 8, 4] ∧
    Dal.Adad.adad (katabaCells.map (fun cell => (Dal.n cell).val)) = 452621 ∧
    Nabt.Sequence.encode (cellsToNabt katabaCells) = 1144809 := by
  decide

def exampleSource : Nabt.UnitDiscovery.Source Dal.Khaliya :=
  ⟨17, 1, 2, 3, katabaCells⟩

def exampleContext : NativeContext := ⟨[exampleSource], [], []⟩
def exampleFirst : NativeTree := .atom exampleSource [] ⟨8, 0⟩ [⟨18, 0⟩, ⟨26, 0⟩]
def exampleSecond : NativeTree := .atom exampleSource [⟨8, 0⟩] ⟨18, 0⟩ [⟨26, 0⟩]
def exampleThird : NativeTree := .atom exampleSource [⟨8, 0⟩, ⟨18, 0⟩] ⟨26, 0⟩ []
def exampleTag : Nabt.LicensedDerivation.Tag := ⟨1, 2, 3, []⟩

/-- الذرة تثبت موضعها فقط؛ الوصل بلا تأويلات دليل يبقى معلّقًا. -/
theorem atom_does_not_license_join :
    (Nabt.LicensedDerivation.assess exampleContext exampleFirst).status = .conditionalLicensed ∧
    (Nabt.LicensedDerivation.assess exampleContext
      (.join exampleTag exampleFirst exampleSecond)).status = .pending := by
  decide

/-- حذف الخلية الوسطى لا يجعل الأول والثالث متجاورين في المصدر. -/
theorem filtered_gap_is_invalid :
    (Nabt.LicensedDerivation.assess exampleContext
      (.join exampleTag exampleFirst exampleThird)).status = .invalid := by
  decide

/-- تطابق أرقام المصدر مع تغيير محتواه لا يثبت عضويته في المخزون. -/
theorem same_ids_different_source_is_invalid :
    (Nabt.LicensedDerivation.assess exampleContext
      (.atom { exampleSource with atoms := [⟨8, 0⟩] } [] ⟨8, 0⟩ [])).status = .invalid := by
  decide

theorem insufficient_budget_stays_exhausted :
    Nabt.UnitDiscovery.enumerateWithin 2 katabaCells = .exhausted := by
  decide

/-- هذه قيم شاهد مفروض للفاحص، لا تقرير عن كتاب أو واقعة خارجية. -/
def exampleChecks : Nabt.RationalInquiry.Checks :=
  ⟨true, true, true, true, true, false, false, false, false, 999, 999⟩

theorem supplied_numeric_rank_does_not_override_mashru :
    (assessInquiry exampleChecks .mubarhan .mafhus .aqliyya).verdict = .deferred ∧
    (assessInquiry exampleChecks .mafhus .mafhus .aqliyya).authorizedRank = 3 ∧
    (assessInquiry exampleChecks .mubarhan .mubarhan .ilmiyya).verdict = .deferred := by
  decide

end Jisr.NabtBridge
