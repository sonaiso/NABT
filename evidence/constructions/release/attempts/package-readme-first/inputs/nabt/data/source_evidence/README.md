# Arabic source evidence fixtures

This directory contains three complete, unchanged OpenITI text files and a small
authored index into their original UTF-8 bytes. It supports a bounded experiment:
extract six explicit grammatical prescriptions and replay three examples quoted
by Sībawayhi. The fixtures do not constitute an Arabic parser, a new source seal,
an independently sampled test set, or a proof of the grammatical interpretations.

## Files and status

| File | Role |
| --- | --- |
| `qatr.txt`, `alfiyya.txt`, `sibawayhi.txt` | Complete original source bytes, with headers and OpenITI markup preserved |
| `source_manifest.json` | Immutable upstream references, full-file and passage hashes, original line/byte spans, and the Mashru citation audit |
| `pilot_examples.json` | Six prescriptions and three quoted examples, with separate cue, target, and marker spans |
| `pilot_conditions.json` | Authored index of rule conditions, preferences, and alternate-use contexts; it supplies no truth values for new examples |
| `license_evidence.json`, `LICENSE-DATA.md` | Primary-source license evidence and attribution notice |

All offsets are absolute UTF-8 **byte** offsets in the complete source file,
zero-based, with an inclusive start and exclusive end. They are not character
offsets in an extracted or normalized passage. For every span,
`source_bytes[start:end].decode("utf-8")` must equal the recorded `text`. Full
source hashes and approved context hashes must be checked before using spans.

The originals have not been cleaned, vocalized, transliterated, or given new
final newlines. The manifest's `normalized_view` only removes the original line
prefixes `# ` or `~~` and joins those lines for inspection. That display view is
not the input for byte offsets or numeric text identity. Local filenames are
shorter than the full OpenITI version URIs; the manifest retains the full names.

## Immutable sources and attribution

The source headers retain the complete metadata supplied by OpenITI. Short author
names below identify the works; the metadata are evidence of the digital edition
and are not an independent bibliographic reconstruction.

### Qatr al-Nada

- Author and work: Jamāl al-Dīn Ibn Hishām, **متن قطر الندى وبل الصدى**.
- OpenITI version URI: `0761JamalDinIbnHisham.MatnQatrNada.Shamela0011376-ara1`.
- Source collection: al-Maktaba al-Shāmila, `Shamela_0011376` in the preserved header.
- Repository: `OpenITI/0775AH`.
- [Exact file at commit `61b0c7891699554aeff8dffdb8b1a2a59d2d22ab`](https://github.com/OpenITI/0775AH/blob/61b0c7891699554aeff8dffdb8b1a2a59d2d22ab/data/0761JamalDinIbnHisham/0761JamalDinIbnHisham.MatnQatrNada/0761JamalDinIbnHisham.MatnQatrNada.Shamela0011376-ara1).
- Git blob SHA-1: `daccba5aea480c1b3676c17a86e5bde3231e3d4d`.
- SHA-256: `2d9241beca1b138187ace8f6782d5eed68f3864f402ec1d5fc90fdeb306ceb9d`.
- Size: 40,168 bytes; 453 physical lines.

### Alfiyyat Ibn Malik

- Author and work: Jamāl al-Dīn Ibn Mālik, **ألفية ابن مالك**.
- OpenITI version URI: `0672IbnMalik.Alfiyya.Shamela0008522-ara1`.
- Source collection: al-Maktaba al-Shāmila, `Shamela_0008522` in the preserved header.
- Repository: `OpenITI/0675AH`.
- [Exact file at commit `4b1d2886508b435eb0377ccab96e1da96cc8ee0a`](https://github.com/OpenITI/0675AH/blob/4b1d2886508b435eb0377ccab96e1da96cc8ee0a/data/0672IbnMalik/0672IbnMalik.Alfiyya/0672IbnMalik.Alfiyya.Shamela0008522-ara1).
- Git blob SHA-1: `6e5b9fb177c8f4b477c0f848a93409578187bb00`.
- SHA-256: `13b351a0a02d9060fdedbb5db568544718eb4e89bef323f5572b8a26c0921ca0`.
- Size: 97,798 bytes; 1,292 physical lines.

### Kitab Sibawayhi

- Author and work: Abū Bishr ʿAmr ibn ʿUthmān ibn Qanbar Sībawayhi, **كتاب سيبويه**.
- OpenITI version URI: `0180Sibawayhi.KitabSibawayhi.JK006989-ara1`.
- Source collection: al-Jāmiʿ al-Kabīr, `JK_006989` in the preserved header.
- The header names editor ʿAbd al-Salām Muḥammad Hārūn and publisher Dār al-Jīl, Beirut.
- Repository: `OpenITI/0200AH`.
- [Exact file at commit `599f22fe249871f602efe2e0ddc801d3742960a3`](https://github.com/OpenITI/0200AH/blob/599f22fe249871f602efe2e0ddc801d3742960a3/data/0180Sibawayhi/0180Sibawayhi.KitabSibawayhi/0180Sibawayhi.KitabSibawayhi.JK006989-ara1).
- Git blob SHA-1: `5252a722c3ec1ebb6839911ae492d9c3912f948c`.
- SHA-256: `a160f940bb194e6fe7e6655d2c7f28e41f1fc648c4c5e340cc4e42306d5cb625`.
- Size: 2,639,395 bytes; 21,893 physical lines.

Qatr and the Alfiyya were retrieved as complete GitHub file bytes. Sībawayhi's
identical bytes were recovered by decompressing the copy in Alghanem commit
`9d8fa03a51f894416e0abaf3b6821c5ae6441dcd`, path
`corpora/kitab/0180Sibawayhi.KitabSibawayhi.JK006989-ara1.gz`. GitHub separately
returned the blob identity for the pinned OpenITI file. Both the SHA-256 and the
Git blob SHA-1, computed over the entire recovered file, match the original.
Acquisition is recorded per document; no different edition was substituted.

## Prescriptions, observations, and conditions

The six `prescription` records extract three case-to-letter instructions from
Qatr lines 78–79 and three from the Alfiyya line 75. Their `marker` spans contain
the **letter names** `واو`, `ألف`, and `ياء`. A named, authored lexical mapping is
needed to interpret those words as marker tags. They are explicit author rules,
so successful reconstruction demonstrates rule extraction and source replay.
It is not evidence of discovering a rule from independently labeled usage.

The three `observed_example` records come from Sībawayhi lines 12349–12350:

| Record | Separate literal cue | Target | Actual observed marker |
| --- | --- | --- | --- |
| `sibawayhi_han_hadha` | `هذا` | `هنوك` | `و` before `ك` |
| `sibawayhi_han_raaytu` | `رأيت` | `هناك` | `ا` before `ك` |
| `sibawayhi_han_marartu_ba` | `مررت` and the attached `ب` | `هنيك` within `بهنيك` | `ي` before `ك` |

The third cue has two spans in `cue_parts`; the file does not invent a contiguous
`مررت ب` substring. Cue extraction reads separate bytes from ending extraction.
An observed record's identifier contains its literal cue rather than a case
label. The original is unvocalized at these examples. Their contextual reading
as examples of **هن**, including the interpretation of `هناك`, is an explicit
authored passage-level assumption. A bare occurrence elsewhere is not covered.

These are examples quoted by one grammarian in one passage. The text attributes
the usage to some Arabs. They can expose an overbroad candidate that predicts the
same ending for all three, then support a revision conditioned on the separate
cues. Such a run measures behavior on these source examples; it supplies neither
an independent heldout accuracy estimate nor a universal account of Arabic case.

The condition index separately preserves companionship meaning for **ذو**,
absence of mīm for the relevant **فم** form, idafa, the first-person-yā exception,
the preference concerning **هن**, qasr variants, and a relative-pronoun context
for **ذو**. The raw Alfiyya idafa verse contains the fused spelling `للياكجا`;
no silent correction is made. Interpretation of that clause is authored. A
preference is not a prohibition, and a condition stated in a rule is not evidence
that an arbitrary new example satisfies it. Singular and non-diminutive
requirements are not established for arbitrary inputs by these selected
excerpts and are explicitly left unestablished in the index.

## Relationship to Mashru and the trust boundary

Mashru was audited at commit
`e4c801ffe9171dadedcc3aae23051ea0953ae361`. All three source hashes match its
recorded source deposits. The manifest retains that provenance result and says
`new_seal_created: false`. This does not confer any new authority on the sources.

The audit also checked all 42 quoted citations in the six rows of Mashru's
`Jisr/QawaidJadwal.lean` against the corresponding exact original lines. Those
quotes match. This checks literal citation fidelity, not every interpretation
encoded in the generated table. The manifest's `generated_table.path` is a path
in the pinned Mashru repository, not in Qeyas.

The original `qawaid.tsv` deposit is **absent**. Its recorded SHA-256 is
`0e5941ae1d66a2fa907fe6d6373d7e3913f2923abf04a04940c841cb2e598dbf`.
No replacement TSV has been fabricated, and this fixture directory does not
claim to reproduce that missing deposit or its complete generation history.

The manifest and example JSON are inspectable provenance, not self-authorizing
certificates. A deployment policy must separately choose accepted immutable
sources, passage scopes, extraction rules, and interpretations. Recomputing a
hash after editing a source cannot make that content an approved source.
Numeric identity, correct byte spans, source authority, and linguistic truth are
separate obligations.

## License

These source data retain OpenITI's stated **CC BY-NC-SA 4.0** license. The
[official OpenITI documentation](https://openiti.org/documentation/#how-can-i-use-openiti-what-license-is-used)
and its [citation guidance](https://openiti.org/documentation/#how-do-i-cite-openiti-texts)
were checked on 2026-10-22. This is a corpus-level upstream declaration; the
audit did not establish a separate license grant for each printed edition or
audit every editorial contribution in each book.

See [LICENSE-DATA.md](LICENSE-DATA.md), the
[official license deed](https://creativecommons.org/licenses/by-nc-sa/4.0/), and
the [legal code](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.en).
The repository's code license does not relicense these text fixtures. Original
sources are unchanged; the selection, segmentation, interpretation notes, and
provenance records are additions for this pilot. No endorsement is claimed.
