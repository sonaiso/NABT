# تدقيق المستودعات الأخرى في المرحلة الاسمية والعددية

## نطاق الجرد

أحصيت **31 مستودعا محليا** خارج `Alghanem` و`Mashru` و`NABT`. يوجد بينها **7 ملفات Lean فقط**: ملف في `alghanem-constitution` وستة في `Salehan19-6-67`. فحصت التصريحات في الملفات السبعة ووجدت **100 تصريح** يتعلق باستعادة التمثيل أو حوكمة الشهادة والرتب والبقايا. لا يعرف أي منها حسابا عربيا خاصا بالجنس أو العدد أو المنقوص واللفيف. لم أعد بناء المنبع.

للمستودعات الأخرى أُنجز مسح نصي للإنتاج المتتبع (`.py/.lean/.ts/.js` حتى500000 بايت، مع استبعاد مسارات الاختبارات والاعتماديات)، ثم قراءة مركزة للدوال المذكورة أدناه. **نتيجة البحث ليست قراءة دلالية شاملة لكل الشيفرة أو الملفات النثرية.** يحفظ [السجل الآلي](source_audit_other.json) الاستعلام وملفات الإصابة وبصماتها؛ ويثبت الملفات المتطابقة بايتيا بين الأشجار ذات القرابة، دون عد النسخ المكررة أدلة مستقلة.

الجرد الموحد: **34 نسخة محلية،24 مستودعا عاما حاليا،22 مشتركا،36 في الاتحاد،12 في الذاكرة المحلية فقط،2 عامان بلا نسخة محلية**. جرد العامين الأخيرين يثبت عدم وجود Lean في شجرتهما الظاهرة، ولا يعني أن شيفرتهما خضعت هنا للقراءة. البيانات الكاملة في [المحلي](source_inventory_cached.json) و[المباشر](source_inventory_remote.json). العام الحالي لا يعني حصر المستودعات الخاصة أو الفروع القديمة.

## المستودعات المحلية المشمولة

| المستودع | ختم النسخة | ملفات Lean | مدى القراءة الدلالية |
|---|---|---:|---|
| `Saleh1967/Algebra` | `5d131b565e9f` | 0 | ON20, ON21, ON22 |
| `Saleh1967/alghanem-constitution` | `f75a43b9f4ed` | 1 | ON01 |
| `Saleh1967/dal-madlul-constitution` | `0c2ca948de44` | 0 | جرد Lean ومسح إنتاج موجّه؛ لا حكم شامل على باقي الملفات |
| `Saleh1967/hamil-constitution` | `3fd531b87fba` | 0 | جرد Lean ومسح إنتاج موجّه؛ لا حكم شامل على باقي الملفات |
| `Saleh1967/hamil-hala-zaman-program` | `232821b7a194` | 0 | جرد Lean ومسح إنتاج موجّه؛ لا حكم شامل على باقي الملفات |
| `sonaiso/-` | `987813e57cbc` | 0 | جرد Lean ومسح إنتاج موجّه؛ لا حكم شامل على باقي الملفات |
| `sonaiso/12Rabi-2nd` | `f096138a47fc` | 0 | ON03, ON04, ON05 |
| `sonaiso/1stAdam` | `57f2e3b9b2bb` | 0 | جرد Lean ومسح إنتاج موجّه؛ لا حكم شامل على باقي الملفات |
| `sonaiso/33-repo-` | `e319bae35a46` | 0 | ON09, ON10 |
| `sonaiso/7-4-26-mahdi` | `6eb0fa69bd0f` | 0 | ON19 |
| `sonaiso/ARAI` | `0b3ae6ddc270` | 0 | جرد Lean ومسح إنتاج موجّه؛ لا حكم شامل على باقي الملفات |
| `sonaiso/Allai` | `f12774755129` | 0 | جرد Lean ومسح إنتاج موجّه؛ لا حكم شامل على باقي الملفات |
| `sonaiso/Bayan` | `ac7ebd954341` | 0 | ON18 |
| `sonaiso/Binary-` | `ff472cdc8adc` | 0 | جرد Lean ومسح إنتاج موجّه؛ لا حكم شامل على باقي الملفات |
| `sonaiso/Eqratech_Hussein_Hiyassat_Project` | `7829b478a4a0` | 0 | جرد Lean ومسح إنتاج موجّه؛ لا حكم شامل على باقي الملفات |
| `sonaiso/Huda-27-4-26` | `1beef9d577a9` | 0 | ON06, ON07, ON08 |
| `sonaiso/MOBEEN` | `f42e846d853d` | 0 | جرد Lean ومسح إنتاج موجّه؛ لا حكم شامل على باقي الملفات |
| `sonaiso/Mahdi-27-5` | `b89ffe6ee0f5` | 0 | جرد Lean ومسح إنتاج موجّه؛ لا حكم شامل على باقي الملفات |
| `sonaiso/Mahdi-27-5v2` | `89c5933f532b` | 0 | جرد Lean ومسح إنتاج موجّه؛ لا حكم شامل على باقي الملفات |
| `sonaiso/Nahda-` | `d9d8dd12a76c` | 0 | جرد Lean ومسح إنتاج موجّه؛ لا حكم شامل على باقي الملفات |
| `sonaiso/Qeyas` | `f20c1ee1cd7f` | 0 | ON17 |
| `sonaiso/Saleh-` | `d24f44a171ce` | 0 | جرد Lean ومسح إنتاج موجّه؛ لا حكم شامل على باقي الملفات |
| `sonaiso/Salehan19-6-67` | `2118e15ce8d2` | 6 | ON02, ON15, ON16 |
| `sonaiso/Taaqol-GPT` | `91dad107a7d5` | 0 | جرد Lean ومسح إنتاج موجّه؛ لا حكم شامل على باقي الملفات |
| `sonaiso/Tebyan` | `2eb87173280b` | 0 | جرد Lean ومسح إنتاج موجّه؛ لا حكم شامل على باقي الملفات |
| `sonaiso/agi-23-12` | `c1d46ccb1048` | 0 | جرد Lean ومسح إنتاج موجّه؛ لا حكم شامل على باقي الملفات |
| `sonaiso/alasmaa` | `ad4207ce51f6` | 0 | ON11, ON12, ON13, ON14 |
| `sonaiso/diana` | `315403854880` | 0 | جرد Lean ومسح إنتاج موجّه؛ لا حكم شامل على باقي الملفات |
| `sonaiso/masaq-eqra` | `6d10eb9e6867` | 0 | جرد Lean ومسح إنتاج موجّه؛ لا حكم شامل على باقي الملفات |
| `sonaiso/nashmi_v2` | `46eba9414df1` | 0 | جرد Lean ومسح إنتاج موجّه؛ لا حكم شامل على باقي الملفات |
| `sonaiso/sfsg67` | `1437922f2bf1` | 0 | جرد Lean ومسح إنتاج موجّه؛ لا حكم شامل على باقي الملفات |

## العقود والأمثلة المضادة

### ON01 — الإعادة العامة تحفظ البقايا فقط

**EXISTING_LEAN**؛ `Saleh1967/alghanem-constitution`. [legacy/RecoveryMetric.lean:1–89](https://github.com/Saleh1967/alghanem-constitution/blob/f75a43b9f4ed3df059f1feb832f48d96e6f846ba/legacy/RecoveryMetric.lean#L1-L89).

**Declarations:** `RecoveryMetric.edit_roundtrip`, `RecoveryMetric.tanwin_restore`, `RecoveryMetric.ilal_edit_restore`, `RecoveryMetric.no_seat_recovery_from_hamza_alone`, `RecoveryMetric.restoration_forces_fiber_separation`.

**Implemented:** Generic restoration and noninjective erasure results, with Mathlib metric/coding results later in the same file.

**Boundary:** No noun/gender/number/weak-class analyzer; linguistic licensing is explicitly outside these edit-restoration instantiations.

### ON02 — شهادة الحوكمة مشروطة برايات معطاة

**EXISTING_LEAN**؛ `sonaiso/Salehan19-6-67`. [research/formal/lean/ResidualCalculus.lean:36–174](https://github.com/sonaiso/Salehan19-6-67/blob/2118e15ce8d21ecf9a125ebf1555145d03f9553a/research/formal/lean/ResidualCalculus.lean#L36-L174).

**Declarations:** `Residual`, `GovernanceState`, `resolvedByEvidence`, `residual_persistence`, `state_residual_persistence`, `certificateAllowed`, `no_illicit_certification`, `unresolved_conflict_blocks_certificate`.

**Implemented:** Typed residuals and certificate gating from supplied flags. All six Lean files in this repo concern the judgment/governance/rank model.

**Boundary:** No Arabic morphology objects. residual_persistence assumes the preservation condition it concludes; other theorems enforce declared gating, not truth of the flags.

### ON03 — التعريف في12Rabi: معجم وقرينة وافتراض نهائي

**EXISTING_NON_LEAN_CODE**؛ `sonaiso/12Rabi-2nd`. [src/layers/definiteness_layer.py:1–190](https://github.com/sonaiso/12Rabi-2nd/blob/f096138a47fc5d52137d4e3084a64fae6aa18f4b/src/layers/definiteness_layer.py#L1-L190).

**Declarations:** `_classify_definiteness`.

**Implemented:** Supplied proper/pronoun POS, fixed pronoun/demonstrative sets and article-like prefix produce definite/ambiguous records; otherwise the default is indefinite and closed.

**Boundary:** No Lean proof. No general idafa analysis in this function; absence of article is not a licensed negative fact.

**Concrete consequences of the inspected code:**

- An unlisted unmarked proper noun without its POS receipt falls through to indefinite.

### ON04 — الجنس في12Rabi متعدد الحقول لكن لا استقلال لمصدره

**EXISTING_NON_LEAN_CODE**؛ `sonaiso/12Rabi-2nd`. [src/layers/gender_layer.py:43–96](https://github.com/sonaiso/12Rabi-2nd/blob/f096138a47fc5d52137d4e3084a64fae6aa18f4b/src/layers/gender_layer.py#L43-L96)؛ [src/layers/gender_layer.py:108–255](https://github.com/sonaiso/12Rabi-2nd/blob/f096138a47fc5d52137d4e3084a64fae6aa18f4b/src/layers/gender_layer.py#L108-L255).

**Declarations:** `_FEMININE_UNMARKED`, `_NATURAL_FEMININE`, `_has_feminine_marker`, `_classify_gender`.

**Implemented:** Finite lexical exceptions, a supplied morph.gender feature and suffixes ة/ات/ى/اء determine several output gender axes; some unknowns remain unresolved.

**Boundary:** The named axes are useful data separation, but a supplied feature or marker is often copied into lexical/syntactic/referential fields. No semantic inference or source attestation is proved.

**Concrete consequences of the inspected code:**

- A nonlexicalized word ending اء can be marked feminine even when its suffix belongs to a masculine plural or original root.

### ON05 — العدد في12Rabi لا يفحص معظم قواعده المسماة

**EXISTING_NON_LEAN_CODE**؛ `sonaiso/12Rabi-2nd`. [src/layers/number_layer.py:164–232](https://github.com/sonaiso/12Rabi-2nd/blob/f096138a47fc5d52137d4e3084a64fae6aa18f4b/src/layers/number_layer.py#L164-L232)؛ [src/layers/number_layer.py:385–428](https://github.com/sonaiso/12Rabi-2nd/blob/f096138a47fc5d52137d4e3084a64fae6aa18f4b/src/layers/number_layer.py#L385-L428)؛ [src/layers/number_layer.py:432–514](https://github.com/sonaiso/12Rabi-2nd/blob/f096138a47fc5d52137d4e3084a64fae6aa18f4b/src/layers/number_layer.py#L432-L514).

**Declarations:** `_has_dual_suffix`, `_evaluate_agreement`, `_classify_number`, `_fill_counted_from_next`, `_finalize`.

**Implemented:** Digit/numeral tables and next-token morphology fill count records;3..10 checks a finaltaa against supplied counted gender. Other ranges mainly return rule names.

**Boundary:** No Lean. n>=20 is uniformly tamyiz in _finalize, contradicting100/1000. The n20..90 gender branch includes nondecades, and n91..99 reaches the100plus label. Compound unit/ten readings and noun gender-of-singular are not acquired.

**Concrete consequences of the inspected code:**

- noun مسلمين or بساتين passes the ين dual heuristic and yields size2.
- n=100 gets tamyiz in _finalize but a genitive-idafa label in _evaluate_agreement.
- n=21 is labeled gender-neutral; n=91 reaches100plus.

### ON06 — قواعدL12 افتراضات شكلية لا إسناد معجمي

**EXISTING_NON_LEAN_CODE**؛ `sonaiso/Huda-27-4-26`. [src/orchestrator/l12_gender_number.py:137–280](https://github.com/sonaiso/Huda-27-4-26/blob/1beef9d577a9dd74216ff1e73f6883891f9c3f95/src/orchestrator/l12_gender_number.py#L137-L280).

**Declarations:** `_has_nominal_family_cues`, `_grammatical_family`, `_apply_gender_rules`, `_apply_number_rules`.

**Implemented:** Uses upstream kind/derivation plus prefix/suffix cues; noun ة or named weights→feminine, otherwise masculine; ان/ون/ات→dual/plural, some ين unresolved, otherwise singular.

**Boundary:** No Lean; upstream feature receipt and heuristic defaults must remain distinguishable. The default is not an acquired negative fact.

**Concrete consequences of the inspected code:**

- حمزة ends in ة but is a masculine proper-name reading.
- شمس/يد with no supplied lexical gender reach the masculine fallback.
- أبيات ends ات but its taa is original, so suffix alone cannot establish sound feminine plural.

### ON07 — إزالة الحركات تمحو تمييز ين

**EXISTING_NON_LEAN_CODE**؛ `sonaiso/Huda-27-4-26`. [src/fvafk/c2b/morphology_flags.py:127–156](https://github.com/sonaiso/Huda-27-4-26/blob/1beef9d577a9dd74216ff1e73f6883891f9c3f95/src/fvafk/c2b/morphology_flags.py#L127-L156)؛ [src/fvafk/c2b/morphology_flags.py:205–278](https://github.com/sonaiso/Huda-27-4-26/blob/1beef9d577a9dd74216ff1e73f6883891f9c3f95/src/fvafk/c2b/morphology_flags.py#L205-L278).

**Declarations:** `MorphologyFlagsExtractor._extract_definiteness`, `MorphologyFlagsExtractor._extract_number`, `MorphologyFlagsExtractor._extract_gender`.

**Implemented:** Article-prefix Bool, suffix number extractor checking stripped dual suffixes before plural suffixes, then masculine/singular defaults.

**Boundary:** No Lean; after stripping vowels the dual ين case wins before any masculine-plural ين reading can be considered.

**Concrete consequences of the inspected code:**

- مُسْلِمِينَ and مُسْلِمَيْنِ lose their distinguishing vowels and both enter the dual branch.
- The lack of initial ال is represented as definiteness=False even for a proper name or pronoun.

### ON08 — المنقوص أمثلة مودعة في جدول

**EXISTING_NON_LEAN_CODE**؛ `sonaiso/Huda-27-4-26`. [src/engines/morphology/ism_manqus_engine.py:1–21](https://github.com/sonaiso/Huda-27-4-26/blob/1beef9d577a9dd74216ff1e73f6883891f9c3f95/src/engines/morphology/ism_manqus_engine.py#L1-L21).

**Declarations:** `IsmManqusEngine.make_df`.

**Implemented:** A short DataFrame seed for قاض/داع/ماض with supplied roots and descriptive features, passed through reconstruction.

**Boundary:** Not an independent manqus classifier; seed labels and morphological statements are source data, not a theorem about any new word.

### ON09 — التصنيف الصريح للّفيفPython ويخلط الهمزة بالعلة

**EXISTING_NON_LEAN_CODE**؛ `sonaiso/33-repo-`. [src/taaqqul_slot_geometry/core/arabic_muttasil.py:45–59](https://github.com/sonaiso/33-repo-/blob/e319bae35a4613eff969cc520904f3f26a50f255/src/taaqqul_slot_geometry/core/arabic_muttasil.py#L45-L59)؛ [src/taaqqul_slot_geometry/core/arabic_muttasil.py:166–214](https://github.com/sonaiso/33-repo-/blob/e319bae35a4613eff969cc520904f3f26a50f255/src/taaqqul_slot_geometry/core/arabic_muttasil.py#L166-L214)؛ [src/taaqqul_slot_geometry/core/arabic_muttasil.py:318–420](https://github.com/sonaiso/33-repo-/blob/e319bae35a4613eff969cc520904f3f26a50f255/src/taaqqul_slot_geometry/core/arabic_muttasil.py#L318-L420).

**Declarations:** `WEAK_CONSONANTS`, `WeakRootClass`, `classify_root`, `generate_weak_past`, `generate_weak_present`.

**Implemented:** Classifies supplied root positions, then generates specialized strings. The weak set includesو/ي plus four hamza shapes; unusual position combinations can fall back to SAHIH.

**Boundary:** Do not transfer this weak set, fallback or unconditional generation. Most weak-past/present branches ignore the requested form and supplied lexical bab is absent.

**Concrete consequences of the inspected code:**

- سأل is labeled AJWAF because أ belongs to WEAK_CONSONANTS.
- أكل is labeled MITHAL.
- Positions(0,1) fall back to SAHIH while weak_positions remains nonempty.
- All AJWAF present forms use longو in this implementation; this does not cover باع→يبيع.

### ON10 — مولد الجمع يركب صيغة معطاة ولا يثبتها معجميا

**EXISTING_NON_LEAN_CODE**؛ `sonaiso/33-repo-`. [src/taaqqul_slot_geometry/core/arabic_morphology_generator.py:633–692](https://github.com/sonaiso/33-repo-/blob/e319bae35a4613eff969cc520904f3f26a50f255/src/taaqqul_slot_geometry/core/arabic_morphology_generator.py#L633-L692).

**Declarations:** `generate_sound_plural_masc`, `generate_sound_plural_fem`, `generate_broken_plural`.

**Implemented:** Appends ون/ات to a generated active-participle stem; broken-plural generation uses one فُعَلاء template from a supplied triliteral root.

**Boundary:** Not general singular-to-plural inversion, no noun eligibility or lexical plural attestation, no masculine/feminine semantics proof.

### ON11 — alasmaa: صفوف مقفلة لا تعميم جنس وعدد

**EXISTING_NON_LEAN_CODE**؛ `sonaiso/alasmaa`. [alasmaa/integration/adjudication/stage15_gender_batch_a.py:1–83](https://github.com/sonaiso/alasmaa/blob/ad4207ce51f621c97d10f689dd35d03db21a2dea/alasmaa/integration/adjudication/stage15_gender_batch_a.py#L1-L83).

**Declarations:** `build_stage15_gender_batch_a_view`.

**Implemented:** Only nominal_path plus exact normalized الصالحات→feminine or رحماء→masculine activates a gender result.

**Boundary:** No Lean. Locked lexical witnesses are reusable as explicit source descriptions, not general induction.

### ON12 — alasmaa: العدد النحوي في صفين

**EXISTING_NON_LEAN_CODE**؛ `sonaiso/alasmaa`. [alasmaa/integration/adjudication/stage16_number_batch_a.py:1–89](https://github.com/sonaiso/alasmaa/blob/ad4207ce51f621c97d10f689dd35d03db21a2dea/alasmaa/integration/adjudication/stage16_number_batch_a.py#L1-L89).

**Declarations:** `build_stage16_number_batch_a_view`.

**Implemented:** The same two normalized surfaces get plural; stage15_gender is intentionally ignored for activation.

**Boundary:** Good field separation, but only two deposited readings; no general dual/singular/plural parser.

### ON13 — alasmaa: علاقة العدد والمعدود في سياق مقفل

**EXISTING_NON_LEAN_CODE**؛ `sonaiso/alasmaa`. [alasmaa/integration/adjudication/stage17_number_count_batch_a.py:1–112](https://github.com/sonaiso/alasmaa/blob/ad4207ce51f621c97d10f689dd35d03db21a2dea/alasmaa/integration/adjudication/stage17_number_count_batch_a.py#L1-L112)؛ [alasmaa/integration/adjudication/stage17_number_count_batch_a.py:128–192](https://github.com/sonaiso/alasmaa/blob/ad4207ce51f621c97d10f689dd35d03db21a2dea/alasmaa/integration/adjudication/stage17_number_count_batch_a.py#L128-L192).

**Declarations:** `build_stage17_number_count_batch_a_view`.

**Implemented:** Four locked context rows for ثلاثة أيام, سبعة in the specified context, and a ten-token tract ending تلك عشرة كاملة; stage16 ignored.

**Boundary:** Does not implement general number parsing, compositional agreement, or counting entities. Keep exact contextual provenance.

### ON14 — alasmaa: تصريف اسمي ومعجم محدود وعكس يختار الأول

**EXISTING_NON_LEAN_CODE**؛ `sonaiso/alasmaa`. [alasmaa/language_engine/morphological.py:1173–1258](https://github.com/sonaiso/alasmaa/blob/ad4207ce51f621c97d10f689dd35d03db21a2dea/alasmaa/language_engine/morphological.py#L1173-L1258)؛ [alasmaa/language_engine/morphological.py:1467–1557](https://github.com/sonaiso/alasmaa/blob/ad4207ce51f621c97d10f689dd35d03db21a2dea/alasmaa/language_engine/morphological.py#L1467-L1557).

**Declarations:** `_DUAL_SUFFIX`, `_inflect_noun_raw`, `_inflect_noun_entry`, `_build_reverse_index`.

**Implemented:** Caller-supplied case/definiteness/number/gender choose suffixes, or a deposited NounEntry chooses a stem; reverse index uses setdefault for one reading.

**Boundary:** Raw API does not license a plural class; dual oblique suffix has kasra beforeya instead of the expectedfatha+sukun. Entry API appends ordinary vowel/tanwin to every dual/plural base. setdefault loses colliding readings.

**Concrete consequences of the inspected code:**

- The table _DUAL_SUFFIX uses KASRA+ين for oblique dual.
- A dual entry base ending ان receives the ordinary singular tanwin through _inflect_noun_entry.

### ON15 — Salehan: جدول جمع التكسير يتضمن جمعا سالما

**EXISTING_NON_LEAN_CODE**؛ `sonaiso/Salehan19-6-67`. [src/mcd/morphosemantics/broken_plural_transformer.py:1–104](https://github.com/sonaiso/Salehan19-6-67/blob/2118e15ce8d21ecf9a125ebf1555145d03f9553a/src/mcd/morphosemantics/broken_plural_transformer.py#L1-L104).

**Declarations:** `BrokenPluralTransformer`, `BrokenPluralTransformer.transform`.

**Implemented:** Exact dictionary lookup over known singular/plural pairs, optionally augmented fromJSON; returnsNone if unknown.

**Boundary:** No Lean generation or lexical theorem; certainty is stored/default numeric data. The class name does not certify all rows as broken plurals.

**Concrete consequences of the inspected code:**

- The known dictionary includes كَلِمة→كَلِمات in BrokenPluralTransformer.

### ON16 — Salehan: agreement يفحص الحالة والعلامة فقط

**EXISTING_NON_LEAN_CODE**؛ `sonaiso/Salehan19-6-67`. [src/mcd/murab/agreement_engine.py:1–40](https://github.com/sonaiso/Salehan19-6-67/blob/2118e15ce8d21ecf9a125ebf1555145d03f9553a/src/mcd/murab/agreement_engine.py#L1-L40).

**Declarations:** `AgreementEngine.check_agreement`.

**Implemented:** The executable comparison checks irab_case and irab_marker.

**Boundary:** Despite the docstring naming gender/number/case, it does not read gender or number; do not count it as their implemented checker.

### ON17 — Qeyas يميز الجنس والعقل لكن من معجم مسبق

**EXISTING_NON_LEAN_CODE**؛ `sonaiso/Qeyas`. [qeyas/jamid/lexeme_rules.py:1–190](https://github.com/sonaiso/Qeyas/blob/f20c1ee1cd7f8f3fb8e1c90c79bb8bf6f1138cc7/qeyas/jamid/lexeme_rules.py#L1-L190).

**Declarations:** `GenderValue`, `RationalityValue`, `LexemeFeatureSet`, `LexemeGroup`, `LexemeRules.lookup`.

**Implemented:** Distinct grammatical-gender/rationality values and fixed lemma groups, plus soft priors for ambiguous groups; lookup returns first matching group.

**Boundary:** No Lean. Useful axis separation, but category labels/weights are supplied lexicon priors. A normalization match does not prove the intended reading.

### ON18 — Bayan يودع صيغ الجمع كأوزان

**EXISTING_NON_LEAN_CODE**؛ `sonaiso/Bayan`. [src/bayan/morphology/pattern_library.py:446–520](https://github.com/sonaiso/Bayan/blob/ac7ebd9543419cd8db36024e14a12ebc034ee250/src/bayan/morphology/pattern_library.py#L446-L520).

**Declarations:** `sound plural and broken plural pattern entries`.

**Implemented:** Named sound-plural suffix patterns and ten common broken-plural shape patterns with noun/plural metadata.

**Boundary:** Non-Lean pattern declarations; matching a shape does not establish noun sense, lexical plurality, gender or a singular-plural correspondence.

### ON19 — دستور الاسم فيMahdi يحول خواصا معطاة

**EXISTING_NON_LEAN_CODE**؛ `sonaiso/7-4-26-mahdi`. [arabic_engine/noun/constitution_v1.py:130–176](https://github.com/sonaiso/7-4-26-mahdi/blob/6eb0fa69bd0fbab18c7ce8670b8e28bd579e3141/arabic_engine/noun/constitution_v1.py#L130-L176)؛ [arabic_engine/noun/constitution_v1.py:309–341](https://github.com/sonaiso/7-4-26-mahdi/blob/6eb0fa69bd0fbab18c7ce8670b8e28bd579e3141/arabic_engine/noun/constitution_v1.py#L309-L341).

**Declarations:** `_NUMBER_MAP`, `_GENDER_MAP`, `_DEF_MAP`, `determine_inflection`.

**Implemented:** Maps closure.features strings for number,gender,definiteness to enums; absent keys becomeUNKNOWN.

**Boundary:** No Lean and no text acquisition. The construct label maps to a definite-idafa value without checking its complement in this function.

### ON20 — Algebra يعيد حساب إيداع العدد

**EXISTING_NON_LEAN_CODE**؛ `Saleh1967/Algebra`. [examples/rasm/run_number_ladder.py:1–86](https://github.com/Saleh1967/Algebra/blob/5d131b565e9fd953cbb625b538aae050ce1fef5d/examples/rasm/run_number_ladder.py#L1-L86).

**Declarations:** `EXPECTED`, `read_table`, `outcomes`.

**Implemented:** Reads a deposited four-row count table, derives outcome distributions from prescribed class-to-counted-form labels, then computes entropy/refinements.

**Boundary:** Non-Lean and explicitly no new measurement. The expected grammatical outputs are inputs to the count construction, not learned from new texts.

### ON21 — Algebra يختبر قرائن المناوبة على مدونة

**EXISTING_NON_LEAN_CODE**؛ `Saleh1967/Algebra`. [examples/rasm/run_neutral_witness.py:1–39](https://github.com/Saleh1967/Algebra/blob/5d131b565e9fd953cbb625b538aae050ce1fef5d/examples/rasm/run_neutral_witness.py#L1-L39)؛ [examples/rasm/run_neutral_witness.py:56–108](https://github.com/Saleh1967/Algebra/blob/5d131b565e9fd953cbb625b538aae050ce1fef5d/examples/rasm/run_neutral_witness.py#L56-L108).

**Declarations:** `SHORTENED`, `EXTENDED`, `PROCLITICS`, `AGREEMENT`.

**Implemented:** Regex-based corpus protocol collects long/short hollow-like alternating frames, includes deletion as an observed witness, and reports prefix-stripping ambiguity.

**Boundary:** Research measurement code, not a Lean theorem or exact lexical classifier. The protocol explicitly admits clitic/root ambiguity; no fresh run or accuracy claim here.

### ON22 — Algebra: ناقص الفعل في المناوبة لا المنقوص الاسمي

**EXISTING_NON_LEAN_CODE**؛ `Saleh1967/Algebra`. [examples/rasm/run_naqis_witness.py:1–34](https://github.com/Saleh1967/Algebra/blob/5d131b565e9fd953cbb625b538aae050ce1fef5d/examples/rasm/run_naqis_witness.py#L1-L34)؛ [examples/rasm/run_naqis_witness.py:55–96](https://github.com/Saleh1967/Algebra/blob/5d131b565e9fd953cbb625b538aae050ce1fef5d/examples/rasm/run_naqis_witness.py#L55-L96).

**Declarations:** `PROCLITICS`, `AGREEMENT`, `MADD_LAM`.

**Implemented:** Collects final-radical appearance/deletion alternations in explicit regex scope.

**Boundary:** Distinct from nominal manqus; corpus coverage and broad claims are not revalidated by this static audit.

## خلاصة النقل

يوجد عمل قابل للاستفادة: فصل الجنس والعقل في Qeyas، إبقاء UNKNOWN عند غياب بعض الخواص في Mahdi، عدم ربط تنشيط صف العدد بتنشيط صف الجنس في alasmaa، والإفصاح عن التباس نزع السوابق في تجارب Algebra. هذه خصائص تصميم محددة؛ لا تثبت صحة المعجم أو أن تصنيفا معطى صار مكتسبا من النص.

العيوب التي يمنع نقلها واضحًا هي الافتراضات «لا علامة→مذكر/مفرد/نكرة»، إلحاق الهمزة بحروف العلة، فحص ين بعد طمس حركاتها ثم اختيار فرع واحد، تسوية جميع القيم>=100 في حكم واحد، أخذ اسم دالة أو صنف كدليل على أنها تنفذ حقول الجنس والعدد، وضياع القراءة الثانية في قاموس عكس يكتفي بـ `setdefault`.

مصادر وصفية محددة يمكن قبولها بوصفها شهادة مصدر لا حكم سياسة. كل قراءة تبقى مع معرفها وألفاظها وخواصها؛ ولا تجمع خواص قراءتين مشتركتين في السطح لتصنع قراءة ثالثة.
