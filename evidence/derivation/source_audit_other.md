# تدقيق مصادر الاشتقاق: المستودعات الأخرى

تاريخ الفحص: 2026-10-23. هذا الجزء محصور في المستودعات السبعة الواردة في الجرد السابق؛ تدقيق Mashru وAlghanem في جزأين منفصلين. فُحصت الشجرات المثبتة وقرئت المقاطع من كائنات Git الأصلية، دون تشغيل شيفرة المصادر أو فتح تنفيذ الاشتقاق الجديد في NABT.

## النتيجة التنفيذية

ليس في هذه الشجرات السبع عقد Lean لقوالب الاشتقاق المطلوبة. يوجد ملف Lean واحد: `legacy/RecoveryMetric.lean`، ومجاله الاسترجاع والمترية؛ يصرح بأن نتائجه لا تثبت اكتمال صرف العربية. أما الجداول والمصنفات الصرفية المفيدة هنا فهي Python أو CSV أو وثائق قوانين. ينبغي حملها إلى NABT بوصفها مصادر اقتراح أو شروطًا تصرح بحدودها، ثم إنشاء العقد المناسب والتحقق منه محليًا.

الرؤوس الحالية المتاحة للمستودعات الخمسة الأولى تساوي اللقطات المثبتة. أعاد الاتصال بـ Qeyas وalasmaa حالة 404؛ لذلك لا ينسب إليهما هذا التدقيق حكمًا على الفرع الحالي، ولا يستنتج الحذف أو عدم الوجود. ملاحظاتهما على اللقطة المحلية المثبتة فقط.

## الجرد ونطاق التحقق

| المستودع | الالتزام المقروء | الملفات المتعقبة | ملفات Lean | فحص الرأس الحالي |
|---|---|---:|---:|---|
| Saleh1967/alghanem-constitution | `f75a43b9f4ed3df059f1feb832f48d96e6f846ba` | 52 | 1 | main مطابق |
| Saleh1967/dal-madlul-constitution | `0c2ca948de44bd44f1f61c2e44ea01896ff5ad1d` | 27 | 0 | main مطابق |
| Saleh1967/hamil-constitution | `3fd531b87fba4f5312cd911c1038db38e3f84618` | 50 | 0 | main مطابق |
| Saleh1967/hamil-hala-zaman-program | `232821b7a19498da4727fd731d2859eb45d14ef9` | 201 | 0 | main مطابق |
| sonaiso/Taaqol-GPT | `91dad107a7d56e6e05cce4ab54c3d63e5bdf5482` | 627 | 0 | main مطابق |
| sonaiso/Qeyas | `f20c1ee1cd7f8f3fb8e1c90c79bb8bf6f1138cc7` | 515 | 0 | 404؛ حالة الرأس غير متاحة |
| sonaiso/alasmaa | `ad4207ce51f621c97d10f689dd35d03db21a2dea` | 1259 | 0 | 404؛ حالة الرأس غير متاحة |

عدد Lean هو تعداد المسارات المتعقبة ذات الامتداد `.lean` في الشجرة المعينة، وليس دعوى عن جميع النسخ أو الفروع. لا تتضمن الأشجار السبع ملف `lean-toolchain` متعقبًا. لم يُعَد بناء الملف الوحيد ضمن هذا الجزء؛ وصف البرهان قائم على قراءة نصه. انعدام الملفات هنا لا يشمل المستودعين اللذين يراجعهما المساران الآخران.

توجد بصمات SHA-256 ومواضع الملفات وروابط الالتزامات وأحجامها في [source_audit_other.json](source_audit_other.json). وُسم ما اقتصر العمل فيه على البصمة ولم تعتمد عليه النتائج بـ `HASHED_NOT_RELIED_ON`. لا تعني قائمة المقاطع أن جميع وظائف المستودع دُققت.

## ما يستفاد منه وما لا يثبت

### OTH-F01 — Recovery only

**نوع الدليل: LEAN_SOURCE_CONTRACT.** The only tracked Lean file in the seven trees is legacy/RecoveryMetric.lean. It proves generic edit restoration (including recorded shadda, tanwin, hamza and ilal edits), separation needed for recovery, and metric/stream results. The file explicitly excludes completeness of Arabic morphology. It supplies no derivation-template inventory, inverse parser, productive lexeme licensing or semantic classifier.

**حد الاستفادة في NABT:** Lossless transformation trace is a useful proof obligation; restoring a recorded transformation does not establish when that linguistic transformation is licensed.

[Saleh1967/alghanem-constitution/legacy/RecoveryMetric.lean:1–86](https://github.com/Saleh1967/alghanem-constitution/blob/f75a43b9f4ed3df059f1feb832f48d96e6f846ba/legacy/RecoveryMetric.lean#L1-L86) · [Saleh1967/alghanem-constitution/legacy/RecoveryMetric.lean:186–228](https://github.com/Saleh1967/alghanem-constitution/blob/f75a43b9f4ed3df059f1feb832f48d96e6f846ba/legacy/RecoveryMetric.lean#L186-L228)

### OTH-F02 — Template extraction waiting on a publication

**نوع الدليل: SUSPENDED_PYTHON.** dal-madlul-constitution's suspended slge_wazun describes extracting cells from a supplied vocalized publication and comparing with a freeze. Its missing-publication path exits successfully while explicitly withholding lexical closure. This is a suspended source-extraction interface, not a verified conjugation inventory.

**حد الاستفادة في NABT:** Require a deposited source with exact location before treating extracted patterns as source-backed.

[Saleh1967/dal-madlul-constitution/suspended/src__slge__slge_wazun.py:1–42](https://github.com/Saleh1967/dal-madlul-constitution/blob/0c2ca948de44bd44f1f61c2e44ea01896ff5ad1d/suspended/src__slge__slge_wazun.py#L1-L42)

### OTH-F03 — Root and verb data

**نوع الدليل: LEXICAL_DATA.** hamil-constitution carries 4,576 Maqayis data records (4,577 logical CSV rows including the header) and 7,953 verb data records (7,954 tab-delimited rows including the header). The verb table supplies a written verb, root, conjugation-class field, T field and id; it does not itself prove morphology or discover roots from new text. One verb record has an empty conjugation-class field. The README's 7,954 wording counts differently from the actual data-record count.

**حد الاستفادة في NABT:** Possible individually linked lexical witnesses after source extraction/validation; never runtime policy answers or a blanket root-attestation oracle.

[Saleh1967/hamil-constitution/data/maqayis_by_root_csv_999.csv:1–1](https://github.com/Saleh1967/hamil-constitution/blob/3fd531b87fba4f5312cd911c1038db38e3f84618/data/maqayis_by_root_csv_999.csv#L1-L1) · [Saleh1967/hamil-constitution/data/verb_triliteral.csv:1–4](https://github.com/Saleh1967/hamil-constitution/blob/3fd531b87fba4f5312cd911c1038db38e3f84618/data/verb_triliteral.csv#L1-L4) · [Saleh1967/hamil-constitution/README.md:9–20](https://github.com/Saleh1967/hamil-constitution/blob/3fd531b87fba4f5312cd911c1038db38e3f84618/README.md#L9-L20) · [Saleh1967/hamil-constitution/data/CARD.md:1–12](https://github.com/Saleh1967/hamil-constitution/blob/3fd531b87fba4f5312cd911c1038db38e3f84618/data/CARD.md#L1-L12)

### OTH-F04 — Verb forms I–XV

**نوع الدليل: PYTHON_TABLE_AND_AVAILABILITY_FLAGS.** hamil-hala-zaman-program's algebra_engine.T stores 15 past-shaped templates. Its 15-by-8 PARADIGM records availability symbols for past active/passive, imperfect active/passive, imperative, masdar, active participle and passive participle. The cells are flags produced by paradigm_cell, not generated surfaces or separate fully specified templates for all 120 cells. Form-I masdar is marked as source-dependent; broad intransitivity exclusions are declared assumptions of that table.

**حد الاستفادة في NABT:** Source-labelled shape candidates and a visible coverage ledger; do not promote availability flags into completed conjugation or universal productivity.

[Saleh1967/hamil-hala-zaman-program/algebra_engine.py:59–84](https://github.com/Saleh1967/hamil-hala-zaman-program/blob/232821b7a19498da4727fd731d2859eb45d14ef9/algebra_engine.py#L59-L84)

### OTH-F05 — Exact matching and ambiguity

**نوع الدليل: PYTHON_PATTERN_MATCHER.** awzan_engine compares letters, vowel states and shadda; separate layers free the final state and peel listed prefixes. hit returns the first matched weight/root plus a count, so it does not preserve the full analysis set. Main match appends every radical-position character without a repeated-slot binding map; equality binding appears in the diagnostic diag_match path. These are boundaries to address before reuse, not a proof of completeness.

**حد الاستفادة في NABT:** Keep literal comparison and explicit boundaries; enumerate all candidates, enforce repeated slots, retain occurrence bytes and do not peel prefixes by spelling alone.

[Saleh1967/hamil-hala-zaman-program/awzan_engine.py:1–27](https://github.com/Saleh1967/hamil-hala-zaman-program/blob/232821b7a19498da4727fd731d2859eb45d14ef9/awzan_engine.py#L1-L27) · [Saleh1967/hamil-hala-zaman-program/awzan_engine.py:73–120](https://github.com/Saleh1967/hamil-hala-zaman-program/blob/232821b7a19498da4727fd731d2859eb45d14ef9/awzan_engine.py#L73-L120) · [Saleh1967/hamil-hala-zaman-program/awzan_engine.py:123–165](https://github.com/Saleh1967/hamil-hala-zaman-program/blob/232821b7a19498da4727fd731d2859eb45d14ef9/awzan_engine.py#L123-L165)

### OTH-F06 — Verb-shape cues

**نوع الدليل: PYTHON_MEASUREMENT.** sigha_gate declares six surface cue families crossed with seven apparent root-condition families. Its documentation explicitly says the bare-past cue is not morphological analysis, reports false positives, and quarantines imperfect cells because the judge reuses that cue. Thus its reported corpus numbers are internal measurements, not independent gold or Lean theorems.

**حد الاستفادة في NABT:** Freeze comparison cells before measuring; separate cue recognition from word-class activation, and do not count the same rule on both sides as evidence.

[Saleh1967/hamil-hala-zaman-program/sigha_gate.py:1–44](https://github.com/Saleh1967/hamil-hala-zaman-program/blob/232821b7a19498da4727fd731d2859eb45d14ef9/sigha_gate.py#L1-L44) · [Saleh1967/hamil-hala-zaman-program/sigha_gate.py:69–137](https://github.com/Saleh1967/hamil-hala-zaman-program/blob/232821b7a19498da4727fd731d2859eb45d14ef9/sigha_gate.py#L69-L137) · [Saleh1967/hamil-hala-zaman-program/SIGHA.md:85–170](https://github.com/Saleh1967/hamil-hala-zaman-program/blob/232821b7a19498da4727fd731d2859eb45d14ef9/SIGHA.md#L85-L170)

### OTH-F07 — Sources and statistical generation

**نوع الدليل: NAME_DISAMBIGUATION.** masadir_gate audits sources_manifest.tsv and source roles: masadir here means sources, not Arabic verbal nouns. tawlid_gate produces statistical surface samples and explicitly disclaims Arabic grammatical validity; it is not root-and-template conjugation.

**حد الاستفادة في NABT:** Use the source-role and borrowed-evidence discipline, not filename-based claims of morphological coverage.

[Saleh1967/hamil-hala-zaman-program/masadir_gate.py:45–55](https://github.com/Saleh1967/hamil-hala-zaman-program/blob/232821b7a19498da4727fd731d2859eb45d14ef9/masadir_gate.py#L45-L55) · [Saleh1967/hamil-hala-zaman-program/masadir_gate.py:101–132](https://github.com/Saleh1967/hamil-hala-zaman-program/blob/232821b7a19498da4727fd731d2859eb45d14ef9/masadir_gate.py#L101-L132) · [Saleh1967/hamil-hala-zaman-program/tawlid_gate.py:39–55](https://github.com/Saleh1967/hamil-hala-zaman-program/blob/232821b7a19498da4727fd731d2859eb45d14ef9/tawlid_gate.py#L39-L55) · [Saleh1967/hamil-hala-zaman-program/tawlid_gate.py:241–306](https://github.com/Saleh1967/hamil-hala-zaman-program/blob/232821b7a19498da4727fd731d2859eb45d14ef9/tawlid_gate.py#L241-L306)

### OTH-F08 — Weight families, not a surface classifier

**نوع الدليل: PYTHON_DECLARATIVE_SCHEMA.** Taaqol's formal_shape_weight_pattern registers 12 families: bare/augmented verb, bare/augmented masdar, nominal-derived, active/passive participle, sifa mushabbaha, instrument, time/place, jamid and gendered weights. Definitions are textual values with schema checks, Rank.CANDIDATE and residuals. define_weight_pattern_shape validates supplied definition fields; it does not parse raw Arabic or prove those descriptions in Lean.

**حد الاستفادة في NABT:** Adopt the separation of pattern, semantic direction and syntactic role as explicit NABT obligations; do not relabel Python validation as a Lean proof.

[sonaiso/Taaqol-GPT/src/taaqqul_slot_geometry/weight/formal_shape_weight_pattern.py:1–38](https://github.com/sonaiso/Taaqol-GPT/blob/91dad107a7d56e6e05cce4ab54c3d63e5bdf5482/src/taaqqul_slot_geometry/weight/formal_shape_weight_pattern.py#L1-L38) · [sonaiso/Taaqol-GPT/src/taaqqul_slot_geometry/weight/formal_shape_weight_pattern.py:177–327](https://github.com/sonaiso/Taaqol-GPT/blob/91dad107a7d56e6e05cce4ab54c3d63e5bdf5482/src/taaqqul_slot_geometry/weight/formal_shape_weight_pattern.py#L177-L327) · [sonaiso/Taaqol-GPT/src/taaqqul_slot_geometry/weight/formal_shape_weight_pattern.py:330–537](https://github.com/sonaiso/Taaqol-GPT/blob/91dad107a7d56e6e05cce4ab54c3d63e5bdf5482/src/taaqqul_slot_geometry/weight/formal_shape_weight_pattern.py#L330-L537) · [sonaiso/Taaqol-GPT/src/taaqqul_slot_geometry/weight/formal_shape_weight_pattern.py:857–1178](https://github.com/sonaiso/Taaqol-GPT/blob/91dad107a7d56e6e05cce4ab54c3d63e5bdf5482/src/taaqqul_slot_geometry/weight/formal_shape_weight_pattern.py#L857-L1178)

### OTH-F09 — Jamid identity and pre-weight gates

**نوع الدليل: PYTHON_CARRIERS_AND_LAW_ONLY_DOCUMENT.** Taaqol pre_weight explicitly contains carriers rather than stage operations. G0 document 77 declares itself law-only and separates a bare jamid identity anchor from masdar, participles, derived instrument/time/place and discourse operations. Its separate lexical JSON has 25 hand-specified candidate records with source-entry references; these are references to attestations, not independently reverified dictionary contents in this audit.

**حد الاستفادة في NABT:** A source-specific ontology of jamid must retain its identity. It cannot silently replace the other source's classification of a masdar as jamid meaning.

[sonaiso/Taaqol-GPT/src/taaqqul_slot_geometry/weight/pre_weight.py:1–64](https://github.com/sonaiso/Taaqol-GPT/blob/91dad107a7d56e6e05cce4ab54c3d63e5bdf5482/src/taaqqul_slot_geometry/weight/pre_weight.py#L1-L64) · [sonaiso/Taaqol-GPT/docs/77_G0_BARE_JAMID_STEM_IDENTITY_ANCHOR_LAW.md:1–92](https://github.com/sonaiso/Taaqol-GPT/blob/91dad107a7d56e6e05cce4ab54c3d63e5bdf5482/docs/77_G0_BARE_JAMID_STEM_IDENTITY_ANCHOR_LAW.md#L1-L92) · [sonaiso/Taaqol-GPT/data/lexical_evidence/lex_data_1_jamid_roots.json:1–38](https://github.com/sonaiso/Taaqol-GPT/blob/91dad107a7d56e6e05cce4ab54c3d63e5bdf5482/data/lexical_evidence/lex_data_1_jamid_roots.json#L1-L38)

### OTH-F10 — Canonical derivation recipes

**نوع الدليل: PYTHON_RECIPE_SCHEMA.** Qeyas template_dsl supplies 20 recipe records: ten verb forms I–X, active/passive participles, one masdar shape, two instrument shapes, place, time, adjective, comparative and intensive. The recipes include constraint and operation-hook names. The file serializes declarations; it has no pattern-instantiation implementation. Its terminology enum also lists diminutive, but that is not an additional canonical recipe in this list.

**حد الاستفادة في NABT:** A source of candidate recipes after spelling and side-condition audit, not proof that every listed hook is implemented or every root has that derivative.

[sonaiso/Qeyas/qeyas/schema_graph/template_dsl.py:82–129](https://github.com/sonaiso/Qeyas/blob/f20c1ee1cd7f8f3fb8e1c90c79bb8bf6f1138cc7/qeyas/schema_graph/template_dsl.py#L82-L129) · [sonaiso/Qeyas/qeyas/schema_graph/template_dsl.py:153–310](https://github.com/sonaiso/Qeyas/blob/f20c1ee1cd7f8f3fb8e1c90c79bb8bf6f1138cc7/qeyas/schema_graph/template_dsl.py#L153-L310) · [sonaiso/Qeyas/qeyas/schema_graph/morphology.py:20–52](https://github.com/sonaiso/Qeyas/blob/f20c1ee1cd7f8f3fb8e1c90c79bb8bf6f1138cc7/qeyas/schema_graph/morphology.py#L20-L52)

### OTH-F11 — Jamid, diminutive and comparative

**نوع الدليل: PYTHON_PRIORS_AND_BRANCHES.** Qeyas has eight jamid base templates and ten feature branches. The kernel pairs base candidates by radical count and a soft prior rather than a full vowel-template match. Diminutive branches can emit subtemplates from root size; tafdil needs an allow_tafdil lexeme flag. These are ranked candidate mechanisms, not evidence from raw shape that a lexical item is jamid, diminutive or comparative.

**حد الاستفادة في NABT:** Keep generation proposals and constraints visible. In NABT, a caller flag must not stand in for a source-linked lexical witness.

[sonaiso/Qeyas/qeyas/jamid/templates.py:195–351](https://github.com/sonaiso/Qeyas/blob/f20c1ee1cd7f8f3fb8e1c90c79bb8bf6f1138cc7/qeyas/jamid/templates.py#L195-L351) · [sonaiso/Qeyas/qeyas/jamid/kernel.py:325–350](https://github.com/sonaiso/Qeyas/blob/f20c1ee1cd7f8f3fb8e1c90c79bb8bf6f1138cc7/qeyas/jamid/kernel.py#L325-L350) · [sonaiso/Qeyas/qeyas/jamid/kernel.py:417–519](https://github.com/sonaiso/Qeyas/blob/f20c1ee1cd7f8f3fb8e1c90c79bb8bf6f1138cc7/qeyas/jamid/kernel.py#L417-L519)

### OTH-F12 — Augmentation meaning is defeasible

**نوع الدليل: PYTHON_SEMANTIC_HINT_TABLE.** Qeyas masdar.ops contains nine augmentation operation records for II–X and a vowel-change hint. They explicitly represent weighted semantic/transitivity deltas rather than absolute rules. Its conventional template labels are useful suggestions but do not license causativity, transitivity or an event for an unseen stem.

**حد الاستفادة في NABT:** Keep semantic evidence separate from structural augmentation.

[sonaiso/Qeyas/qeyas/masdar/ops.py:1–15](https://github.com/sonaiso/Qeyas/blob/f20c1ee1cd7f8f3fb8e1c90c79bb8bf6f1138cc7/qeyas/masdar/ops.py#L1-L15) · [sonaiso/Qeyas/qeyas/masdar/ops.py:135–230](https://github.com/sonaiso/Qeyas/blob/f20c1ee1cd7f8f3fb8e1c90c79bb8bf6f1138cc7/qeyas/masdar/ops.py#L135-L230)

### OTH-F13 — Defaults must not become proof

**نوع الدليل: PYTHON_HEURISTIC_PARSER.** Qeyas regex matching accepts caller-defined regexes/root positions and returns scored candidates; its separate tahlil analyzer strips vowels, uses priority-ordered spelling rules, falls back to primitive, infers tense from a prefix and defaults past. These behaviors do not support complete or sound raw-text semantic classification. They also motivate adversarial cases for prefixes, missing vowels, ambiguity and unsupported readings.

**حد الاستفادة في NABT:** Use bounded candidate extraction with exact literal checks and defer without an adequate witness; never import the default primitive/past/role answers.

[sonaiso/Qeyas/qeyas/morphology/patterns_v3.py:35–60](https://github.com/sonaiso/Qeyas/blob/f20c1ee1cd7f8f3fb8e1c90c79bb8bf6f1138cc7/qeyas/morphology/patterns_v3.py#L35-L60) · [sonaiso/Qeyas/qeyas/morphology/root_pattern_matcher_v3.py:42–120](https://github.com/sonaiso/Qeyas/blob/f20c1ee1cd7f8f3fb8e1c90c79bb8bf6f1138cc7/qeyas/morphology/root_pattern_matcher_v3.py#L42-L120) · [sonaiso/Qeyas/qeyas/tahlil/morphological.py:525–658](https://github.com/sonaiso/Qeyas/blob/f20c1ee1cd7f8f3fb8e1c90c79bb8bf6f1138cc7/qeyas/tahlil/morphological.py#L525-L658)

### OTH-F14 — 115 pattern rows with category collisions

**نوع الدليل: CSV_CANDIDATE_PATTERNS.** alasmaa awzan_minimalist_v0.csv has 115 populated data rows, plus a header and two empty rows. It is useful as a candidate pattern inventory, but its own cells mix labels: miftaah is in intensive, minshar/miknasah in place_noun, and both akbar/ahmar in elative; descriptions themselves name instrument/colour. Therefore the category field is not independent semantic gold. Some duplicate pattern strings occur intentionally across categories.

**حد الاستفادة في NABT:** Audit patterns as forms, preserve collisions and require independent descriptive evidence for semantic types.

[sonaiso/alasmaa/data/awzan_minimalist_v0.csv:1–66](https://github.com/sonaiso/alasmaa/blob/ad4207ce51f621c97d10f689dd35d03db21a2dea/data/awzan_minimalist_v0.csv#L1-L66) · [sonaiso/alasmaa/data/awzan_minimalist_v0.csv:84–118](https://github.com/sonaiso/alasmaa/blob/ad4207ce51f621c97d10f689dd35d03db21a2dea/data/awzan_minimalist_v0.csv#L84-L118)

### OTH-F15 — Pattern discovery vs Arabic spelling and meaning

**نوع الدليل: PYTHON_EMPIRICAL_HEURISTICS.** alasmaa PatternGenerator clusters by invariant/variable counts and a binned preservation fraction, then builds K/V slot lists; it is not a vocalized Arabic template compiler. DerivationEngine takes descriptor feature signatures and scores, applies semantic heuristics and a taxon fallback, and emits proposed records. Its optional pattern/convention reference lookup can return None; the introductory statement of prerequisites is stronger than this function's actual guards.

**حد الاستفادة في NABT:** Borrow hypothesis provenance and observed-support accounting, not threshold-based semantic answers.

[sonaiso/alasmaa/alasmaa/morphology/pattern_generator.py:149–223](https://github.com/sonaiso/alasmaa/blob/ad4207ce51f621c97d10f689dd35d03db21a2dea/alasmaa/morphology/pattern_generator.py#L149-L223) · [sonaiso/alasmaa/alasmaa/morphology/derivation_engine.py:56–119](https://github.com/sonaiso/alasmaa/blob/ad4207ce51f621c97d10f689dd35d03db21a2dea/alasmaa/morphology/derivation_engine.py#L56-L119) · [sonaiso/alasmaa/alasmaa/morphology/derivation_engine.py:131–189](https://github.com/sonaiso/alasmaa/blob/ad4207ce51f621c97d10f689dd35d03db21a2dea/alasmaa/morphology/derivation_engine.py#L131-L189)

### OTH-F16 — Two nominal readings are not general derivation

**نوع الدليل: PYTHON_SURFACE_LOCKED_READING.** alasmaa Stage 14 first requires nominal_path and then recognizes exactly two normalized spellings, muhammad and rasul, as derived. The jamid lexicon CSV has two data records. Neither is a general root-and-template classifier or a source of lexical truth for new spellings.

**حد الاستفادة في NABT:** Keep exact-source lexical readings distinct from generic pattern fits.

[sonaiso/alasmaa/alasmaa/integration/adjudication/stage14_derived_vs_jamid_batch_a.py:1–83](https://github.com/sonaiso/alasmaa/blob/ad4207ce51f621c97d10f689dd35d03db21a2dea/alasmaa/integration/adjudication/stage14_derived_vs_jamid_batch_a.py#L1-L83) · [sonaiso/alasmaa/data/jamid_lexicon_v0.csv:1–3](https://github.com/sonaiso/alasmaa/blob/ad4207ce51f621c97d10f689dd35d03db21a2dea/data/jamid_lexicon_v0.csv#L1-L3)

### OTH-F17 — Tense and voice boundaries

**نوع الدليل: PYTHON_VERB_VIEW_HEURISTICS.** alasmaa Stage 11 requires a supplied prior verb classification and primary_wazn; it does not extract roots or patterns. _detect_tense_form labels an initial ya/ta/nun present and otherwise defaults past, except a declared passive prefix. _detect_voice and _detect_verb_class also inspect prefixes. Although the documentation allows imperative, this function has no branch returning imperative. A pattern such as ta'allama therefore needs a regression case against prefix-only tense inference.

**حد الاستفادة في NABT:** Represent perfect/imperfect/imperative shape separately from actual temporal reference; future markers do not create a new root-template tense.

[sonaiso/alasmaa/alasmaa/integration/naa_adapter/verbal_deep_analysis_stage11_view.py:73–139](https://github.com/sonaiso/alasmaa/blob/ad4207ce51f621c97d10f689dd35d03db21a2dea/alasmaa/integration/naa_adapter/verbal_deep_analysis_stage11_view.py#L73-L139) · [sonaiso/alasmaa/alasmaa/integration/naa_adapter/verbal_deep_analysis_stage11_view.py:176–243](https://github.com/sonaiso/alasmaa/blob/ad4207ce51f621c97d10f689dd35d03db21a2dea/alasmaa/integration/naa_adapter/verbal_deep_analysis_stage11_view.py#L176-L243) · [sonaiso/alasmaa/docs/STAGE_11_VERBAL_DEEP_ANALYSIS_V0_RULE_INVENTORY.md:59–79](https://github.com/sonaiso/alasmaa/blob/ad4207ce51f621c97d10f689dd35d03db21a2dea/docs/STAGE_11_VERBAL_DEEP_ANALYSIS_V0_RULE_INVENTORY.md#L59-L79)

## تغطية جميع الأبواب المطلوبة

عمود المواد التالية يصف الموجود في المستودعات السبعة فقط. لا يحمل أي صف ادعاء وجود قالب Lean للاشتقاق فيها.

| الباب | مواد قابلة للفحص | الحد الذي يجب حفظه |
|---|---|---|
| الجامد | OTH-F09, OTH-F11, OTH-F16 | Lexical/source-specific classification; failure to find a template or one supplied jamid label cannot prove jamid. |
| المصدر | OTH-F04, OTH-F08, OTH-F10, OTH-F12, OTH-F14 | Pattern candidates and lexical masdar witnesses; no unique Form-I masdar from a root or a past form alone. masadir_gate is source auditing. |
| اسم الفاعل | OTH-F08, OTH-F10, OTH-F14 | Shape does not license semantic agency or a syntactic subject. |
| اسم المفعول | OTH-F08, OTH-F10, OTH-F14 | Shape does not license patienthood, an object, or unrestricted passive productivity. |
| اسم الآلة | OTH-F08, OTH-F10, OTH-F14 | Require independent instrument meaning; table category collisions must remain visible. |
| اسم المكان / الزمان | OTH-F08, OTH-F10, OTH-F14 | Shared shapes do not choose place versus time versus other readings. |
| الصفة المشبهة | OTH-F08, OTH-F10, OTH-F14 | Stable-attribute reading needs evidence separate from fa'il/fa'il-like spelling. |
| التصغير | OTH-F11 | Qeyas branch declarations offer shapes; root size alone does not establish an observed diminutive or its lexical status. |
| التفضيل | OTH-F10, OTH-F11, OTH-F14 | Af'al overlaps colour/defect and verb spellings; a caller allow_tafdil flag is not an evidential premise. |
| الفعل المجرد والمزيد | OTH-F04, OTH-F05, OTH-F10, OTH-F12, OTH-F14 | Record radical mapping and additions; forms I–XV table presence is not every tense/voice realization. |
| الماضي المعلوم والمجهول | OTH-F04, OTH-F06, OTH-F17 | Vocalized pattern evidence must be checked; availability flags and prefixes are weaker than a complete form. |
| المضارع المعلوم والمجهول | OTH-F04, OTH-F06, OTH-F14, OTH-F17 | A past stem alone does not supply a missing imperfect vowel class. Taaqol inflection definitions concern marks/declension, not conjugation tables. |
| الأمر | OTH-F04, OTH-F06, OTH-F17 | A named imperative enum/availability cell is not an implemented imperative branch or a licensed weak-form operation. |
| المستقبل | OTH-F17 | Keep sawfa/sa segmentation and bounded attachment separate from imperfect pattern. Temporal reference is not a fourth radical-template tense. |
| الإنتاجية والعلل | OTH-F01, OTH-F04, OTH-F11, OTH-F12, OTH-F15 | Observed cells count as observed cells; no universal productivity from a finite sample. Weak/doubled/hamza/quad forms need named traceable operations. |

## قرار النقل المقترح

تُنقل أولًا العلاقة الصورية بين جذر مصرح به وقالب مصرح به وسطح مطابق، مع حرفية الزوائد واتفاق الخانات المكررة. ويُفصل عنها تحليل سطح جديد إلى جميع المرشحين؛ فنجاح البناء من معطيات كاملة لا يثبت اكتشاف تلك المعطيات من النص. كذلك تُفصل الشواهد الدلالية والترخيص المعجمي والإنتاجية عن نجاح المطابقة.

لا يصير الجذر المعاد من قالب جذرًا مستعملًا في العربية بمجرد المطابقة؛ ولا يصير الاسم جامدًا لأن المحلل لم يجد له قالبًا، ولا مشتقًا دلاليًا لأنه وافق وزن فاعل أو مفعول. شاهد واحد على الماضي لا يثبت غياب المضارع والأمر. والشواهد المصرح بها على خلايا التصريف تُحصى بوصفها خلايا مشهودة، دون تعميم إنتاجية غير محدودة.

أما `سـ` و`سوف` فمكانهما وصف علامة زمنية وربطها بالمضارع ضمن حد سياقي مصرح؛ لا تنشأ منهما صيغة جذرية رابعة اسمها المستقبل. والمضارع الصرفي قد يقع في سياق لم أو لن؛ لا يُبدَّل قالبه لأن المرجع الزمني تغير.

## أخطار قابلة للاختبار قبل التنفيذ

- زيادة حرفية غير مطابقة لا يجوز أن يتخطاها الاستخراج؛ يلزم فحص القالب كاملًا.
- الخانة الجذرية المكررة تربط الحرف نفسه، في حين أن الجذر الرباعي ــ إن دخل نطاقًا لاحقًا ــ يحتاج خانة رابعة مستقلة.
- تصادم الأوزان يجب أن يحفظ جميع الجذور المرشحة؛ أول نتيجة أو أعلى درجة ليست يقينًا.
- حرف التاء في أول الماضي المزيد لا يجعله مضارعًا، وبادئة `ال` في التقى ليست تعريفًا بمجرد الرسم.
- الوزن `أفعل` لا يكفي للتفضيل، وجدول يدرج أحمر معه يبين ضرورة الفصل بين الشكل والمعنى.
- بيانات التشكيل الناقصة لا تُستكمل خفية، ولا تُسوّى الهمزات أو ترتيب العلامات بلا ملف تحويل معلن يحفظ الأصل.
- اسم حقل أو تعداد أنواع أو علامة إتاحة أو توثيق يقول «مكتمل» لا يحل محل مسار تنفيذ أو مبرهنة.

هذه الملاحظات أساس مصفوفة حالات مستقلة مؤلفة قبل قراءة التنفيذ. ليست مدونة خارجية محجوبة، ولا نتائج قياس، ولا شهادة صحة لغوية عامة. تبقى صحة الجداول العربية وشروط الاستعمال بحاجة إلى شواهدها المحددة.

