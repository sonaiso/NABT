# فهرس تدقيق مصادر التراكيب

التفسير وحدود النقل في [CONSTRUCTIONS_SOURCE_AUDIT.md](../../docs/CONSTRUCTIONS_SOURCE_AUDIT.md). يحفظ [السجل الآلي](source_audit.json) الإيداعات والبصمات والنوافذ والمقدمات وما لا يثبته كل عقد. هذا فهرس مصادر، لا نتيجة قياس للقارئ أو تشغيل جديد لبراهين المصادر.

## النطاق

- جرد عام أول في 2026-10-23T18:42:22.898349+00:00: 24 شجرة كاملة، محفوظ كما التقط في ذلك الوقت.
- اكتمل [تجديد مصادق للحسابين](source_access_refresh_v2.json) في 2026-10-23T19:41:33.527615+00:00: 41 مستودعًا، منها 24 عامًا و17 خاصًا، و40 شجرة كاملة ومستودع فارغ ثبت برسالة 409 وحجم صفر؛ دون إخفاق جلب أو ملفات Lean خاصة. نطاقه الفروع الافتراضية المتاحة، ولا ينشر أسماء خاصة. طابق [فحص الاستمرارية](source_audit_access_validation.json) رؤوس العامة ومسارات Lean بينها وبين الجرد الأول.
- حُفظ [التجديد الأول v1](source_access_refresh_v1.json) دون تصحيح بايتاته. حقل `tree_sha` القديم فيه وفي الجرد العام ليس بصمة شجرة جذرية محققة؛ يجلب v2 `commit.tree.sha` ثم يطلب تلك الشجرة ويطابق هويتها.
- مطابقة 292 ملف Lean خارجي مع Git blobs المثبتة؛ 120 Mashru، و165 Alghanem، و6 Salehan، و1 constitution.
- 26 سجل عقد، و43 نافذة Lean، و40 نافذة في أربعة نصوص أصلية، و13 فئة مطلوبة.
- السياسة الحالية ذات 17 مقطعًا؛ أضيفت ثلاثة شواهد للعشرات وشاهد للرسم بألف النصب أثناء التطوير قبل تجميد التنفيذ، وحفظت [السياسة الأولى ذات 13 مقطعًا وفحصها](source_policy_initial_v1/manifest.json) دون تغيير. بقية النوافذ التفسيرية ليست قواعد تشغيل مضافة.
- يحفظ [ملحق المستقبل والرفع](source_audit_future_v2.json) نافذتين قائمتيْن من سياسة الخطاب: سيبويه 18510–18520 وقطر الندى 96–98؛ لم تضف قاعدة ثامنة عشرة إلى سياسة التراكيب.

## عقود Lean المختارة

| معرف السجل | المصدر والمسار | الأسطر |
|---|---|---|
| `alghanem_awamil` | `Saleh1967/Alghanem/formal/a116/A116/Awamil.lean` | 1–28, 35–117 |
| `alghanem_awamil_data` | `Saleh1967/Alghanem/formal/a116/A116/AwamilData.lean` | 1–45 |
| `alghanem_role_case` | `Saleh1967/Alghanem/formal/a116/A116/Amil.lean` | 160–205 |
| `alghanem_time` | `Saleh1967/Alghanem/formal/a116/A116/Istiqama.lean` | 25–115, 151–205 |
| `mashru_literal_governors` | `Saleh1967/Mashru/SLGE/Wad.lean` | 43–117 |
| `mashru_governor_equations` | `Saleh1967/Mashru/SLGE/Awamil.lean` | 15–97 |
| `mashru_governor_owner_assignment` | `Saleh1967/Mashru/Jisr/Awamil.lean` | 1–32, 66–110, 130–158 |
| `mashru_frames` | `Saleh1967/Mashru/SLGE/Tarkib.lean` | 28–65, 99–151, 167–182, 218–251 |
| `mashru_reduced_particles` | `Saleh1967/Mashru/SLGE/TarkibExt.lean` | 183–215 |
| `mashru_hal_tamyiz_idafa` | `Saleh1967/Mashru/Jisr/Mulhaqat.lean` | 32–49, 118–174, 258–325, 640–687 |
| `mashru_dependents` | `Saleh1967/Mashru/Jisr/Mulhaqat.lean` | 365–445, 731–764, 792–807 |
| `mashru_declared_coverage` | `Saleh1967/Mashru/Jisr/Mulhaqat.lean` | 844–908 |
| `mashru_style_inventory` | `Saleh1967/Mashru/Jisr/Ikhbar.lean` | 1–98 |
| `mashru_table_force` | `Saleh1967/Mashru/Jisr/AwamilUslub.lean` | 1–45 |
| `mashru_nisab` | `Saleh1967/Mashru/Jisr/Nisab.lean` | 1–70 |
| `mashru_clause_type` | `Saleh1967/Mashru/Jisr/Tarkib.lean` | 1–75, 78–140 |
| `mashru_zanna_cancellation` | `Saleh1967/Mashru/Jisr/KhulasaIkhbar.lean` | 1–29, 106–128 |
| `mashru_time_coordinates` | `Saleh1967/Mashru/Aql/Azmina.lean` | 98–133, 164–217, 286–312 |
| `mashru_place_coordinates` | `Saleh1967/Mashru/Aql/Makan.lean` | 176–224, 344–373 |
| `other:sonaiso/Salehan19-6-67:research/formal/lean/CoreJudgment.lean` | `sonaiso/Salehan19-6-67/research/formal/lean/CoreJudgment.lean` | 1–36 |
| `other:sonaiso/Salehan19-6-67:research/formal/lean/NoIllicitCertification.lean` | `sonaiso/Salehan19-6-67/research/formal/lean/NoIllicitCertification.lean` | 1–98 |
| `other:sonaiso/Salehan19-6-67:research/formal/lean/RankSoundness.lean` | `sonaiso/Salehan19-6-67/research/formal/lean/RankSoundness.lean` | 1–96 |
| `other:sonaiso/Salehan19-6-67:research/formal/lean/ResidualCalculus.lean` | `sonaiso/Salehan19-6-67/research/formal/lean/ResidualCalculus.lean` | 1–174 |
| `other:sonaiso/Salehan19-6-67:research/formal/lean/TriadClosure.lean` | `sonaiso/Salehan19-6-67/research/formal/lean/TriadClosure.lean` | 1–48 |
| `other:sonaiso/Salehan19-6-67:research/formal/lean/TypedResiduals.lean` | `sonaiso/Salehan19-6-67/research/formal/lean/TypedResiduals.lean` | 1–40 |
| `other:Saleh1967/alghanem-constitution:legacy/RecoveryMetric.lean` | `Saleh1967/alghanem-constitution/legacy/RecoveryMetric.lean` | 1–228 |

## النوافذ الأصلية

| المعرف | النص | الأسطر |
|---|---|---|
| `policy:kana_sisters` | `alfiyya` | 209–224 |
| `policy:inna_sisters` | `qatr` | 187–200 |
| `policy:zanna_sisters` | `sibawayhi` | 398–418 |
| `policy:kada_complement` | `alfiyya` | 235–246 |
| `policy:tense_aspect` | `sibawayhi` | 102–110 |
| `policy:naat_agreement` | `qatr` | 374–383 |
| `policy:hal_attachment` | `alfiyya` | 441–467 |
| `policy:tamyiz_measure` | `qatr` | 313–317 |
| `policy:tamyiz_nisba` | `qatr` | 318–325 |
| `policy:badal_identity` | `qatr` | 409–412 |
| `policy:tawkeed_reference` | `alfiyya` | 677–692 |
| `policy:idafa_chain` | `qatr` | 337–345 |
| `policy:temporal_spatial_attachment` | `qatr` | 297–300 |
| `policy:counted_tens_forms` | `qatr` | 82–85 |
| `policy:counted_tens_specification` | `alfiyya` | 952–953 |
| `policy:counted_tens_paradigm` | `sibawayhi` | 5986–5999 |
| `policy:attested_accusative_alif` | `qatr` | 440–446 |
| `qatr_nominal_time_predicate` | `qatr` | 158–167 |
| `qatr_kana_complete` | `qatr` | 169–180 |
| `qatr_zanna_suspension` | `qatr` | 208–217 |
| `qatr_hal_owner` | `qatr` | 307–312 |
| `qatr_tens_inflection` | `qatr` | 82–85 |
| `qatr_tawkeed` | `qatr` | 384–395 |
| `alfiyya_time_place` | `alfiyya` | 405–413 |
| `alfiyya_tamyiz` | `alfiyya` | 469–479 |
| `alfiyya_tens_tamyiz` | `alfiyya` | 945–953 |
| `alfiyya_idafa` | `alfiyya` | 506–517 |
| `alfiyya_naat` | `alfiyya` | 660–675 |
| `alfiyya_badal` | `alfiyya` | 731–739 |
| `sibawayhi_time_consistency` | `sibawayhi` | 261–267 |
| `sibawayhi_kana_senses` | `sibawayhi` | 475–494 |
| `sibawayhi_zanna_scope` | `sibawayhi` | 1246–1264 |
| `sibawayhi_zanna_other_sense` | `sibawayhi` | 1314–1316 |
| `sibawayhi_adverbs` | `sibawayhi` | 18510–18520 |
| `sibawayhi_tens_tamyiz` | `sibawayhi` | 5986–5999 |
| `ibn_aqil_kada_phases` | `ibn_aqil` | 2202–2228 |
| `ibn_aqil_kada_disagreement` | `ibn_aqil` | 2229–2246 |
| `ibn_aqil_an_policies` | `ibn_aqil` | 2249–2278 |
| `ibn_aqil_kada_inflection` | `ibn_aqil` | 2279–2298 |
| `ibn_aqil_badal_relations` | `ibn_aqil` | 6617–6655 |

## الإيصالات

- [الجرد العام وهويات الملفات](source_audit_inventory.json).
- [خريطة كل مطلب](source_coverage.json).
- [مطابقة بايتات السياسة](source_audit_policy_validation.json).
- [فحص الهويات والنوافذ والمراجع](source_audit_validation.json).
- تبقى رخصة نصوص OpenITI ونسبتها كما في [LICENSE-DATA.md](../../src/nabt/data/source_evidence/LICENSE-DATA.md).
