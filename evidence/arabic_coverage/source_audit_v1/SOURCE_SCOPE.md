# Supplementary inception source: attribution and granted scope

## Finding

The pinned Ibn ʿAqīl text does not explicitly list `شرع` as an inception
auxiliary. Its enumeration names `جعل، طفق، أخذ، علق، أنشأ`. The full file's
occurrences of `شرع` are narrative `شرع في` expressions. This is a result about
that exact digital version, not all manuscripts, printings or editorial notes.

The separate primary attestation is **al-Ṣabbān, Ḥāshiya on al-Ashmūnī**, volume
1, page 386. Al-Ṣabbān's commentary says:

> أقول يجب أن يعد منها شرع في نحو شرع زيد يأكل

This is the commentator's explicit proposed addition and constructed example.
It must not be attributed to Ibn ʿAqīl, presented as unanimous doctrine, or
described as an observed early natural-corpus utterance. The work metadata
attributes al-Ṣabbān's death to 1206 AH; this is later testimony than Ibn ʿAqīl.
The [primary page](https://shamela.ws/book/11539/383) and
[edition record](https://shamela.ws/book/11539) corroborate the pinned file.

## Exact transmission

The reviewed OpenITI repository is `OpenITI/1225AH`, commit
`4ec30fc763750fc1233d3774c4416b28c5c8b886`. The complete source is
`1206IbnCaliSabbanShafici.HashiyaCalaSharhAshmuni.Shamela0011539-ara1`, with SHA-256
`8b9e86da786cf65e7b32498b2524ee48a8dcf9f61b59e1bbc32b99ce7db5b396` and Git blob
`0627e5e730863f4886b9be6e771edea0cd41fcf0`. It contains 5,332,827 bytes. The
reviewed window occupies physical lines 13746–13771 and byte interval
`[1548056, 1550778)`, with SHA-256
`c3b67d249404dd16299c04e7891df94b815a6ef141404108424ce9d8a6d5d25b`.
The explicit addition occurs at lines 13768–13769. Raw text, offsets, source URL
and provenance are retained in [sharaa_review.json](sharaa_review.json).

The pinned [version metadata](https://github.com/OpenITI/1225AH/blob/4ec30fc763750fc1233d3774c4416b28c5c8b886/data/1206IbnCaliSabbanShafici/1206IbnCaliSabbanShafici.HashiyaCalaSharhAshmuni/1206IbnCaliSabbanShafici.HashiyaCalaSharhAshmuni.Shamela0011539-ara1.yml)
marks this as `PRIMARY_VERSION, CLEANED_VERSION`. It records removal of
paratextual elements by HRH and MGR in OpenITI's 2023 cleaning operation.
Accordingly, “unchanged” here means exact unchanged bytes of that pinned OpenITI
version. It does not mean a diplomatic transcription of every printed page or
that modern editorial content remains intact. The file header supplies the
printed edition attribution; the author YAML is a largely unfilled template
and is not treated as independent biographical verification.

## License and attribution

The complete pinned repository tree contains no `LICENSE` or `COPYING` file;
its root README only names the repository. No repository-specific license grant
was inferred from those files. OpenITI's
[official corpus documentation](https://openiti.org/documentation/#how-can-i-use-openiti-what-license-is-used)
declares **CC BY-NC-SA 4.0**, and its
[citation guidance](https://openiti.org/documentation/#how-do-i-cite-openiti-texts)
asks users to identify the specific file URI. This declaration was checked on
2026-10-24. It is a corpus-level upstream declaration, not an independent rights
audit of every printed edition or editorial contribution.

Preserve the author's name, title, Shamela provider identifier, OpenITI version
URI, pinned commit, full-source hash and corpus license notice. The existing
NABT code license and any MIT license of a code repository do not relicense this
source text. Metadata responses are retained in
[sabban_pinned_metadata.json](sabban_pinned_metadata.json), separately from the
original three-source evidence manifest.

## What this source may license

This evidence can support a declared supplementary grammar entry for the
**inception sense** of `شرع` in a complete auxiliary-plus-imperfect frame. The
already documented inception-family rules still need their own evidence: a
qualified auxiliary reading, name and complement, compatible person/agreement,
the internal verb's independently licensed mood, and exclusion of `أن` in that
inception use. A new parser branch which checks those premises is an
implementation authored in NABT.

The passage does not determine the subject, object, referent, attachment,
polarity, time or answer of any new target sentence. It does not establish
every lexical sense or inflection of `شرع`, make every occurrence of that
spelling an auxiliary, or prove that a new sentence satisfies the frame.
The onset qualification must remain in the semantic result; the source does
not authorize replacing onset with bare occurrence or completion of the
embedded event. Hash equality establishes faithful byte identity, not the
linguistic adequacy of the interpretation or the truth of the resulting claim.
