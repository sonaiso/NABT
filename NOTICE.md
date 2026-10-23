# Third-party code and source material

The native `nabt.learning` modules and the `Nabt.RuleLearning` and
`Nabt.PropertyEvidence` Lean modules adapt code from `sonaiso/Qeyas`, commit
`0ac045125f3d4ed9a984ab2f78a787fe9d014cd9` (including its predecessor
`6af5840128f685e45ed5ae1070e606303985fb9a`). The original MIT notice follows.
NABT's own MIT license does not replace this notice.

MIT License

Copyright (c) 2024 sonaiso

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Arabic source data

The unchanged OpenITI book fixtures under `src/nabt/data/source_evidence/`
have their own **CC BY-NC-SA 4.0** attribution and data license. Read the
`LICENSE-DATA.md` and source manifest there. These texts are not relicensed as
MIT, and their inclusion is not a verification of historical transmission.

## Prior mathematical designs

The versioned upstream definitions consulted and their scopes are recorded
in `docs/PROVENANCE.md` and `docs/INTEGRATION.md`. Reimplementation or a
reference to a theorem does not import an upstream runtime, authority or
unproved linguistic premise into NABT.

## Mashru inference design

`formal/Nabt/SemanticInference.lean` adapts the generic licensed-rule and replay
pattern from `Saleh1967/Mashru` commit
`e4c801ffe9171dadedcc3aae23051ea0953ae361`, `Aql/Qaida.lean`.
The source-relative contracts are reimplemented in native NABT; no upstream
runtime or source-truth authority is imported. Its MIT notice is retained:

`formal/Nabt/Governors.lean` and the finite inventory in
`src/nabt/data/governors.json` also adapt the governor equations and table from
the same pinned repository: `Jisr/Awamil.lean`, `Jisr/AwamilJadwal.lean`,
`SLGE/Awamil.lean`, `SLGE/AwamilTable.lean`, and `SLGE/Wad.lean`.
Their native re-proved contracts preserve the original scope and the same
MIT notice below. Historical source attribution and inventory limits are
recorded separately in `docs/MASHRU_AWAMIL_AUDIT.md`.

MIT License

Copyright (c) 2026 Saleh1967

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
