# Source-bound sound imperative subject paradigm

The law `nabt.sound-imperative-paradigm.v1` adds four written forms and five
correlated person profiles to the existing singular masculine imperative
bridge. For an independently acquired, fully observed **يَكْتُبُ**, the existing
reader can now return **اُكْتُبِي، اُكْتُبَا، اُكْتُبُوا، اُكْتُبْنَ**. The dual
surface retains both masculine and feminine readings. These possibilities do
not identify a real addressee, establish target attestation, or supply a lexical
sense or an object capacity.

The entry point is the existing `person_candidates(surface, lexical_model=…)`.
It replays original source receipts, preserves the source bytes and exclusions,
and returns no productive reading if its lexical source is withdrawn. The old
`nabt.productive-sound-imperative.v1` law and its 2MS export are unchanged.

## Exact scope

The source must pass the previous conservative Form-I active imperfect law:
three distinct radical letters, none weak or hamzated, an observed internal
vowel, complete canonical vocalization, a qualified source person profile and
an independent complete bare lexical witness. Repeated radicals are excluded
conservatively, including repetitions beyond the usual adjacent geminate case.
Passive voice, derived patterns, weak/hamzated/geminate verbs, missing target
marks, and emphatic nun are outside this law. The 2FP output of a nun-final root is also deferred: radical nun plus feminine nun needs an independent idgham surface law and a representation that preserves both roles on one shadda cluster. Both اُسْكُنْنَ and اُسْكُنَّ therefore receive no productive 2FP reading here; the other profiles of سكن remain licensed.

| Subject | Ending at third radical | Following letters | Reading distinction |
|---|---|---|---|
| 2FS | kasra | ي | Subject pronoun; no inflection nun |
| 2MD | fatha | ا | Masculine dual possibility |
| 2FD | fatha | ا | Feminine dual possibility, same surface |
| 2MP | damma | وا | Subject waw plus orthographic separator alif |
| 2FP | sukun | نَ | Feminine-subject nun retained |

The initial vowel is calculated from the **original medial imperfect vowel**,
not the third radical's new inflectional vowel. Thus اِضْرِبُوا keeps initial
kasra despite the damma before plural waw. Long-vowel carriers and separator
alif have the canonical written geometry used by this law; alternative writing
and recitation systems are not inferred.

## Source and interpretation boundary

`src/nabt/data/source_evidence/imperative_paradigm_v1.json` pins full source
hashes and exact byte spans for five passages:

- Qatr al-Nada, lines 59–63: imperative sukun and the dual/plural/feminine
  singular forms built on absence of inflection nun.
- Sibawayhi, lines 17502–17533: initial wasl and its original-vowel conditions.
- Sibawayhi, lines 14440–14446: the invariant consonant before feminine nun.
- Ibn Aqil, lines 760–776, volume 1 pages 94–95: the explicit imperative
  paradigm اضربي، اضربا، اضربوا، اضربن, with overt subject pronouns.
- Qatr al-Nada, lines 440–446: the orthographic separator after plural waw.

The fully vocalized productive projection is an explicitly labeled author
interpretation of these passages. It is **not** an assertion that every text
in these books has been formalized or independently adjudicated. The source
checker validates hashes and spans; it does not prove the interpretation from
Arabic prose. Ibn Aqil's words are kept distinct from modern editorial
supplements to that edition.

## Object attachment

The new law does not append arbitrary object pronouns. The existing attachment
bridge still requires a separately witnessed complete attached source word and
a matching independently supported host (same lemma, root, voice, aspect and
subject). A newly generated 2MP host can supply that independent host. Only in
this witnessed comparison can the separator alif be absent before an object:
اُكْتُبُوا → اُكْتُبُوهُ. The recorded generated bare host remains اُكْتُبُوا;
the observed attached host and word are separate fields. Removing the imperfect
source leaves the attached word as an unlicensed source annotation, rather than
pretending that the attested bytes vanished or that a syntactic role was proved.

## Formal scope and verification

`formal/Nabt/ImperativeParadigm.lean` proves 16 theorems: recovery of the stem,
stem injectivity for a fixed subject, radical preservation, initial-vowel
independence from subject, equality of the two dual surfaces alongside distinct
profiles, feminine nun and plural separator retention, exact enumeration,
source withdrawal, the nun-collision licensing guard, and preservation of source bytes and witness identities.
These theorems are about the declared symbolic functions under their explicit
premises. They do not certify acoustic realization or completeness of Arabic.

`ExportImperativeParadigm.lean` exports all five rows. Run:

```sh
python tools/check_imperative_paradigm.py --lake /path/to/lake
PYTHONPATH=src:tests python -m unittest test_imperative_paradigm
python tools/imperative_paradigm_evaluation.py --output /new/path/result.json
```

The checker also accepts `--lean-export` for an export obtained with the pinned
Lean `--run` driver. Such a run is reported separately from a standard Lake
native build.

The first authored diagnostic contained 12 positive surfaces, 12 source-withdrawal controls, and 19 contradictory/unsupported forms (43 cases). Review found that a nun-final root needs a separate 2FP assimilation rule. Diagnostic v2 retains those 43 reference targets and labels, adds an independent يسكن source, three eligible subject forms and their withdrawal controls, and two deferred 2FP surfaces. Its denominator is 51 cases: 15 positive surfaces, 15 withdrawals and 21 unsupported/contradictory surfaces. The shared source profile changes explicitly; these are separate versioned measurements. The
runtime never receives reference labels. A separate raw-source checker verifies
source receipts and independent literal target references after execution, and
mutation tests reject altered source identities, profiles, and authority flags.
Raw outputs, code/source/reference hashes and exact profile sets are saved.
The denominator is the declared versioned case set, not all Arabic. No global language
coverage percentage follows from it. A blind independently adjudicated corpus
and broader source classes remain separate work.
