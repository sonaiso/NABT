# Derivation / weak-law / source surface: frozen acceptance contract v1

Status: independently authored, exposed preimplementation acceptance contract.
Base: NABT e9f83a3f6c678fb45ba618800cebf65310427e97. This is not a blind
experiment, Arabic completeness proof, new Lean theorem or lexical attestation.
The expected examples are written from the installed source scope and declared
representation contract before the new implementation is available.

## Existing owners and authority

The bridge delegates template filling to `nabt.derivation.generate_derivation`,
A116 parsing/rendering to `nabt.alphabet`, and the conditional operation to
`nabt.classical_laws.evaluate('WEAK-MOVE-TO-ALIF', frame)`. Preserve each complete
owner result. The bridge must not reimplement template filling or weak-law
control/rewrite, alter source inventories, or edit their frozen owners.

The source inventory's WEAK-MOVE-TO-ALIF passage is Ibn Aqil lines 9402–9415:
قال and باع, original motion and the adjacent preceding fatha; transferred
motion and following context have restrictions. WEAK-AFWAL-BLOCK lines
9416–9419 supplies the contrast عور/أعور. The I.i/I.u examples in this
acceptance set are explicitly constructed conditional hypotheses, not claims
that those lexical past forms are attested. Freeze literal expectations;
never obtain the gold by running the new bridge.

## API and request

`tools.derivation_surface_bridge.evaluate_derivation_surface(text, request,
*, source_id='input', scope='default')`.

`verify_derivation_surface(report, *, text, request, source_id='input',
scope='default')` freshly replays independently supplied inputs and compares
the complete typed canonical result. Do not use embedded requests as authority.

Request exact keys:

```
{schema:'nabt.derivation-surface-request.v1',
 profile:'medial-alif-unmarked.v1',
 span:{start,end}, root, pattern_id, ending:'َ',
 hypotheses:{context:'ordinary'|'afal_quality'|null,
             origin:'original'|'transferred'|null}}
```

`text` is exact str or UTF-8 bytes. Span coordinates are original UTF-8 bytes,
actual integers (not bool), and select one complete `_scan` written_run.
A substring, quotation interior, incomplete scalar or empty span is invalid.
SourceBlob and `_source` retain their existing identity/UTF-8/scope requirements.

Supported profile: only `past.I.a`, `past.I.i`, `past.I.u`, ending fatha,
three radicals, medial waw/yaa, and sound outer radicals excluding waw/yaa/hamza.
An otherwise well-typed unsupported profile/root/pattern/ending/context/origin
produces DEFER/OUTSIDE_PROFILE, retaining the original request. Missing (null)
context/origin within the profile produces DEFER/MISSING_PREMISES and no guessed
frame. Missing required keys, extra keys, wrong schema/types or invalid spans
are invalid input. Unknown values are not proof of Arabic impossibility.

The validated request alone supplies conditional hypotheses. It cannot establish
lexical class, root, original vowel, meaning or grammar. Do not merge alternatives
with the same resulting surface or infer a unique lexical reading.

## Complete application result

Required schema `nabt.derivation-surface-report.v1`; authority
`SOURCE_BOUND_CONDITIONAL_SURFACE_APPLICATION`.

Required fields: source={source_id,source_sha256,scope,raw_text,byte_length},
original_request, occurrence={span:complete SourceSpan,surface}, generation,
input_cells, classical_receipt, surface_alternatives, status, reason,
missing_hypotheses, unresolved, attested_root, application_established,
grammar_certified, grants_language_license, world_truth.
The four flags are false; world_truth is NOT_ESTABLISHED. Source hashes are
identity checks, not proof of interpretation or of the external world.

Inside profile generation is the complete original owner result, even with
missing hypotheses. input_cells={alphabet_id:'nabt.a116.v1',ids:[...],
morphophonemic:[[carrier,vowel],...]}; scalar-to-cell conversion is explicit.
Outside profile generation/input_cells/classical_receipt are null and
surface_alternatives is empty. Missing hypotheses leave classical_receipt null.
missing_hypotheses lists absent context/origin in that order. unresolved remains
nonempty, explicitly retaining lexical/morphological and CertifiedBridge debts.

For a supplied complete frame call the existing facade. Its receipt, including
application_established=false and all source spans, remains byte-for-byte
canonical-equivalent to the owner result. The derived frame has index=1,
position='ayn', lexeme='', and cells computed from the generated shape; callers
cannot supply cells/index/position or overwrite receipt authority.

Each surface alternative contains action, canonical_marked_surface,
realized_surface, omitted_mark, cell_alignment, exact_source_match. Only the
sukun of the medial alif PRODUCED by to_alif is omitted. No generic normalization,
mark completion, alif/hamza folding or global sukun stripping is allowed.

omitted_mark={mark:'ْ',cell_index:1,
coordinate_domain:'canonical_marked_surface',scalar_start:3,scalar_end:4,
byte_start:6,byte_end:8}. These are generated-surface coordinates, never a
fabricated mark occurrence in the original source.

cell_alignment has exactly three ordered records, each with cell_index and
root_index, and generated/canonical/realized local spans. Each local span has
scalar_start,scalar_end,byte_start,byte_end. source_span is the complete absolute
SourceSpan when exact_source_match is true, otherwise null. Generated and
canonical scalar spans are (0,2),(2,4),(4,6); realized spans are
(0,2),(2,3),(3,5). Their UTF-8 byte spans follow the actual strings.

Status: CONDITIONAL_MATCH iff a licensed conditional alternative exactly matches
the original occurrence; SURFACE_MISMATCH for alternatives without a match;
OUTSIDE_RULE_DOMAIN for an empty weak result; DEFER for OUTSIDE_PROFILE or
MISSING_PREMISES. reason is null for the first three states. None grants a
language license or closes CertifiedBridge. A successfully replayed DEFER
report remains deferred.

Successful verify: valid=true,status=VERIFIED,authority=DERIVATION_SURFACE_REPLAY_ONLY.
Changed reports/independent requests: valid=false,status=REJECT,
code=DERIVATION_SURFACE_REPLAY_MISMATCH. Invalid input is a NabtError with REJECT;
source failures retain INSTALLED_CONTRACT_FAILED/DEFER; limits retain
RESOURCE_LIMIT/DEFER. Verification reports owner/source/resource failure with
valid=false and its DEFER code, never success or linguistic rejection.

## Fixed limits and ordering

Source 8192 UTF-8 bytes; request 4096 canonical UTF-8 JSON bytes; report 262144
bytes. Source identity and scope are each at most 96 UTF-8 bytes, additionally
subject to the old source requirements. Request JSON depth <=24 and visited
nodes <=8192; bounded validation precedes full serialization and owner work.
Integers and booleans are not interchangeable. No caller budget changes the law.

## Existing recursive transport consumer

Add `read_recursive_applications(text, requests, *, source_id='input',
scope='default')` and `verify_recursive_applications(report, *, text, requests,
source_id='input',scope='default')` to tools/recursive_bridge.py. Preserve old
v1 entry points/default reports. These delegate to the application owner and
retain `read_recursive_source(...profile='surface_v1',with_discourse=False)`.

The new report schema is nabt.recursive-source-transport.v2, report_version=2.
Fields: source (complete transport.source), original_requests (ordered list),
limits={max_requests:16,max_aggregate_bytes:16777216}, transport (complete v1),
applications=[{request_index,request,report,occurrence_binding:{byte_span,atom_span}}],
grammar_certified=false,sense_equivalence_established=false,
grants_language_license=false,report_id.
report_id is SHA-256 of canonical complete report without report_id; replay of
all contents, not this digest, is authoritative. Extra documented fields may be
added only before implementation freeze agreement, not to change acceptance.

byte_span is the original complete SourceSpan; atom_span is exactly the existing
source_view/_atom_span result. Preserve application list order and duplicates,
even for identical requests or convergent I.a/I.i/I.u surfaces. Do not insert a
transformed result into _shape_reading, morphology_nodes, interpreted/offered or
an allegedly certified grammar tree. Binding refers to the selected original
occurrence even when its conditional surface mismatches.

Validate list type and <=16 count before source I/O or any owner; validate the
shape/size of all requests and all occurrence boundaries before evaluating the
first application. Enforce aggregate output limit before unbounded aggregate
allocation. No result may conceal a source failure, malformed later request,
or resource exhaustion as a partial successful report.

Successful wrapper verify: valid=true,status=VERIFIED. A changed request/order,
source or report returns valid=false,status=REJECT,
code=RECURSIVE_APPLICATION_REPLAY_MISMATCH. Source/resource errors retain DEFER.

Existing CLI gains read-applications/verify-applications and --applications;
verification additionally requires --report. No application-budget option.
Unsupported discourse/qac/context/probe/legacy-profile controls are rejected,
not silently ignored. Check applications input/list bound before opening source;
17 requests must report RESOURCE_LIMIT even if the source path is missing.

## Evaluation integrity

Gold is exposed and source-informed, not held out. Tests separately check positive
work, blockers, unsupported and missing premises, exact alignment, independent
replay, tampering, collisions of surface with distinct hypotheses, resource
boundaries, source failure propagation, and the actual recursive consumer.
A blanket-DEFER implementation must fail positives. Matching every surface
must fail mismatches. A self-comparison verifier must fail changed independent
inputs. A facade bypass must fail source-owner fault injection.

Frozen files, Makefile, main CI, original source inventories and original operator
receipts stay unchanged. The new tests are discovered by the existing main CI;
no altered expected result, skipped gate or timeout extension is authorized by
this acceptance contract.
