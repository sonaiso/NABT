"""Forward an explicit request to an existing, installed NABT entry point.

The allowlist is code, not registry-supplied commands. This module neither
interprets a result nor combines the authorities of different engines. Child
stdin, stdout, stderr and exit status are preserved so that the original
receipts and diagnostics remain available for their own verifier.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from types import MappingProxyType

from .registry import FrameworkError, FrameworkResourceError

ROOT = Path(__file__).resolve().parents[2]
MAX_ARGUMENTS = 256
MAX_ARGUMENT_BYTES = 131072


@dataclass(frozen=True)
class Entry:
    module: str | None
    native_target: str | None
    description: str
    args_help: str
    scope: str


_ENTRIES = MappingProxyType({
    "core": Entry("nabt", None, "Existing package CLI: cells, readers, learning programs, inquiry and replay.", "Existing nabt arguments; use --help.", "Each selected existing command retains its declared law and scope."),
    "learned-conformance": Entry("tools.export_learned_model", None, "Existing exhaustive learned transition-model conformance check.", "--check; use --help for the existing exporter interface.", "Equivalence to the fixed transition law over the complete 97 by 116 primitive domain; no learned semantics."),
    "source-learning": Entry("tools.source_learning_experiment", None, "Existing source-replayed guard-learning experiment.", "[--sources PATH] [--output PATH].", "Declared finite hypothesis language and source judgments; consensus remains conditional."),
    "certificate-ranker": Entry("tools.train_certificate_ranker", None, "Existing CPU proposal-ranking development experiment.", "--output-dir NEW_DIRECTORY [--checker PATH].", "Changes proposal order only; every original certificate still requires the existing native checker."),
    "certificate-ranker-v2": Entry("tools.train_certificate_ranker_v2", None, "Existing hard-negative certificate proposal-ranking experiment.", "--output-dir NEW_DIRECTORY [--protocol PATH] [--checker PATH].", "Candidate ranking has no acceptance authority; the development split is not a blind Arabic benchmark."),
    "progressive": Entry(None, "progressiveUnitProbe", "Existing native progressive-unit contract probe.", "Read the original JSONL requests from stdin.", "Explicit source-bound unit/derivation contracts; not free-Arabic certification."),
    "unit-discovery": Entry(None, "unitDiscoveryProbe", "Existing native partition and unit-evidence probe.", "Read the original JSONL requests from stdin.", "Complete finite partitions and interpreted evidence within the supplied bounds."),
    "recursive": Entry("tools.recursive_bridge", None, "Existing exact-source recursive bridge adapter.", "read, verify, lean-morphology or lean-frame; use --help.", "Source-linked proposals and installed bridge checks, with semantic premises retained."),
    "recursive-native": Entry(None, "recursiveBridgeProbe", "Existing native recursive bridge probe.", "Read the original JSONL requests from stdin.", "Checks the declared bridge request; does not supply lexical meaning or CertifiedBridge premises."),
    "proof-catalog": Entry("tools.proof_catalog", None, "Rebuild and export the existing compiled Lean catalogue.", "--lake PATH [--output PATH] [--check PATH].", "Compiled declaration index only; no language or world authority."),
    "grammar-catalog": Entry("tools.grammar_catalog", None, "Existing source-linked classical rule retrieval and complete routing.", "catalog, search or route; use --help.", "Retrieval proposes; explicit supplied frames are evaluated under their own laws."),
    "licensed-inference": Entry("tools.licensed_inference", None, "Existing source/query parser and native signed closure checker.", "Existing module arguments; use --help.", "Source-relative consequence in the installed finite active-voice language."),
    "explainable-pilot": Entry("tools.explainable_pilot", None, "Existing native-checked answer, source spans and proof DAG renderer.", "Existing module arguments; use --help.", "Bounded ground reading and replay; renderer correctness is not a general Lean theorem."),
    "mantuq-inference": Entry("tools.mantuq_inference", None, "Existing mantuq/mafhum policy catalogue, evaluation and exhaustive policy scan.", "catalogue, evaluate, search or pipeline; use --help.", "Conditional assumptions and explicit gates; retrieval rank grants no authority."),
    "linguistic-truth": Entry("tools.linguistic_truth", None, "Existing source/convention/usage intake and native checks.", "Existing module arguments; use --help.", "Installed source-linked reading profiles; language truth and world truth remain distinct."),
    "lexical-testimony": Entry("tools.lexical_testimony", None, "Existing source-attributed lexical denotation assessment.", "--entry ID [--target COMPONENT ...].", "Attribution and declared denotation premises; no automatic current-occurrence disambiguation."),
    "lexical-completion": Entry("tools.lexical_completion", None, "Existing completion engine and native finite candidate checker.", "--inventory or --request PATH.", "Declared lexical slots and fixed source catalogues; no all-Arabic completeness."),
    "lexical-graph": Entry("tools.lexical_graph", None, "Existing lexical graph closure, dependency and cycle diagnostics.", "--inventory or --request PATH.", "Installed graph and explicit assumptions; no self-certifying cyclic support."),
    "acquisition": Entry("tools.acquisition_cli", None, "Existing aligned acquisition and independent source replay.", "Existing read/verify arguments; use --help.", "Versioned exact source/cell bindings, including unresolved orthography."),
    "acquired-inference": Entry("tools.acquired_inference_cli", None, "Existing acquisition-to-source-query inference bridge.", "Existing read/verify arguments; use --help.", "Both acquisition and native inference gates must close; nested success does not fill a missing bridge."),
    "article-acquisition": Entry("tools.article_acquisition_cli", None, "Existing article acquisition v2 and joined inference adapter.", "Existing command arguments; use --help.", "Finite sourced article readings; no generic alif recovery."),
    "sourced-acquisition": Entry("tools.sourced_acquisition_cli", None, "Existing sourced pronunciation, person, nominal syntax and natural lexical acquisition.", "--task TASK --text TEXT; use --help.", "Installed v3 source scope and finite aliases; no unrestricted person/reference inference."),
    "productive-clause": Entry("tools.productive_clause_cli", None, "Existing source-bound productive clause reader and verifier.", "Existing read/verify arguments; use --help.", "Finite DARABA, five nominative and five accusative forms, VSO/VOS; all existing gates retained."),
    "productive-lifecycle": Entry("tools.productive_lifecycle_cli", None, "Existing clause dependency withdrawal/reactivation and replay.", "targets, read or verify; use --help.", "Installed dependency inventory; an active grammar dependency does not establish a world observation."),
    "evidence-lifecycle": Entry("tools.evidence_lifecycle_cli", None, "Existing evidence episode evaluator and exact historical replay.", "Existing evaluate/verify arguments; use --help.", "Explicit episodes, active source ancestry and scoped decisions; supplied histories are not authenticated by naming them."),
    "meaning-preservation": Entry("tools.meaning_preservation_cli", None, "Existing finite meaning transport and productive-source adapter.", "inventory, authored, productive or verify; use --help.", "Declared joint observations and contexts; not proof of agreement among actual human interpreters."),
    "epistemic-native": Entry(None, "epistemicMeasurement", "Existing native evidence selection and exact certificate checker.", "Read the original JSON request from stdin.", "Complete supplied ledger with source, ancestry, axis, time, place and unit; no hidden-motive license."),
    "proof-lab": Entry("tools.proof_lab", None, "Existing bounded proof-lab transport and registered modes.", "Existing request/event arguments; use --help.", "Transport of the selected existing result; no additional proof or inference authority."),
})


def describe_entries() -> dict:
    """Return fresh metadata; editing it cannot change the dispatch allowlist."""
    return {name: {"module": row.module, "native_target": row.native_target,
                   "description": row.description, "args_help": row.args_help,
                   "scope": row.scope}
            for name, row in _ENTRIES.items()}


def entry_command(entry_id, arguments, *, root=ROOT):
    """Construct an argv from a code-owned entry; never execute registry data."""
    if type(entry_id) is not str or entry_id not in _ENTRIES:
        raise FrameworkError("Unknown installed reuse entry point")
    if type(arguments) not in (list, tuple):
        raise FrameworkError("Entry arguments must be an explicit string array")
    if len(arguments) > MAX_ARGUMENTS:
        raise FrameworkResourceError("Entry argument count exceeds the declared budget")
    total = 0
    for argument in arguments:
        if type(argument) is not str or "\x00" in argument:
            raise FrameworkError("Entry arguments must be scalar UTF-8 strings without NUL")
        try:
            total += len(argument.encode("utf-8", "strict"))
        except UnicodeError as error:
            raise FrameworkError("Entry argument contains non-scalar Unicode") from error
        if total > MAX_ARGUMENT_BYTES:
            raise FrameworkResourceError("Entry argument bytes exceed the declared budget")
    root = Path(root).resolve()
    entry = _ENTRIES[entry_id]
    if entry.native_target is not None:
        return [str(root / "formal/.lake/build/bin" / entry.native_target), *arguments]
    return [sys.executable, "-B", "-m", entry.module, *arguments]


def run_entry(entry_id, arguments, *, root=ROOT) -> int:
    """Preserve the existing program's streams and status without interpretation.

    The caller owns explicit arguments and any stdin redirection. No shell is
    used, no fallback engine is selected, and exit zero does not become a claim
    of proof, coverage, or linguistic success. The original program emits its
    own receipt. Capture its streams externally when recording an execution.
    """
    root = Path(root).resolve()
    command = entry_command(entry_id, arguments, root=root)
    entry = _ENTRIES[entry_id]
    if entry.native_target is not None and not Path(command[0]).is_file():
        print(json.dumps({"status": "VERIFICATION_UNAVAILABLE", "reason": "INSTALLED_NATIVE_MISSING",
                          "entrypoint_id": entry_id, "semantic_authority": "NONE"}), file=sys.stderr)
        return 69
    if entry.module is not None:
        source_root = root / "src" if entry.module.split(".")[0] == "nabt" else root
        module_path = source_root.joinpath(*entry.module.split("."))
        if not (module_path.with_suffix(".py").is_file()
                or (module_path / "__main__.py").is_file()):
            print(json.dumps({"status": "EXECUTION_UNAVAILABLE", "reason": "INSTALLED_MODULE_MISSING",
                              "entrypoint_id": entry_id, "semantic_authority": "NONE"}), file=sys.stderr)
            return 69
    env = os.environ.copy()
    # The installed source tree is first; retain dependency environment settings
    # needed by existing interfaces without using the registry as import policy.
    env["PYTHONPATH"] = os.pathsep.join((str(root / "src"), str(root)))
    try:
        execution = subprocess.run(command, cwd=root, env=env, check=False)
    except OSError:
        print(json.dumps({"status": "EXECUTION_UNAVAILABLE", "reason": "INSTALLED_ENTRY_NOT_EXECUTABLE",
                          "entrypoint_id": entry_id, "semantic_authority": "NONE"}), file=sys.stderr)
        return 69
    if execution.returncode < 0:
        # sys.exit(-15) would become 241 and erase the child's signal identity.
        # Retain the same terminating signal instead of manufacturing an
        # ordinary exit code or an interpretation receipt.
        termination_signal = -execution.returncode
        try:
            signal.signal(termination_signal, signal.SIG_DFL)
        except (OSError, ValueError):
            # SIGKILL is intentionally uncatchable; os.kill still propagates it.
            pass
        os.kill(os.getpid(), termination_signal)
    return execution.returncode
