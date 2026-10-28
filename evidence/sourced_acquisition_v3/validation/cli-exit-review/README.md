# CLI proof-replay failure exit status

PR 57 review identified that pronunciation SHAPE_CHECK_FAILED returned process status 0. The pre-fix test reproduces all 4 onset/display combinations; ordinary DEFER remains 0. After adding the failure status to the error set, both tests pass. The test injects a failed certificate replay after a synthetic verified acquisition handoff; it does not claim new linguistic coverage or a native source attestation. Reader, formal modules, gold and measured producer outputs are unchanged.
