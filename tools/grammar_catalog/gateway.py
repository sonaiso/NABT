"""The supported external NABT I/O boundary. Owners remain internal contracts."""
from copy import deepcopy
from hashlib import sha256

from tools.evidence_lifecycle_v1 import ResourceLimit, _encoded, strict_loads, wire
from .operations import ROOT, digest, source_snapshot
from .operation_rag import invoke_bounded, MAX_RESULT, MAX_ADDRESS_SPACE
from . import gateway_routes, gateway_links

REQUEST_SCHEMA = "nabt.io.request.v1"
RESULT_SCHEMA = "nabt.io.result.v1"
MAX_REQUEST = 2 * 1048576
POLICY = "nabt.external-io.gateway-only.v1"


def validate_request(request):
    _encoded(request, MAX_REQUEST)
    if type(request) is not dict or set(request) != {"schema", "route", "payload"} or request["schema"] != REQUEST_SCHEMA:
        raise ValueError("Expected the sole NABT I/O request envelope")
    gateway_routes.validate(request["route"], request["payload"])
    return deepcopy(request)


def request_from_bytes(raw):
    return validate_request(strict_loads(raw, maximum_bytes=MAX_REQUEST))


def snapshot():
    # Reuse source identity, including the sole current compiled catalogue.
    from tools import lexical_testimony
    value, _ = source_snapshot()
    value = deepcopy(value)
    for directory, suffix in (("tests", ".py"), ("integrations", ".mk"), (".github/workflows", ".yml")):
        for path in sorted((ROOT / directory).rglob("*"+suffix)):
            if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
                raise ValueError("I/O contract reference escapes repository")
            value["files"][path.relative_to(ROOT).as_posix()] = sha256(path.read_bytes()).hexdigest()
    # Retained testimonies live outside src/tools/formal. Bind their actual
    # bytes before and after execution, reusing the owner's fixed path table.
    lexical_sources = (str(lexical_testimony.CATALOG), "evidence/shared_cognition_v1/model.json",
                       "evidence/contextual_alignment_v1/model.json", "evidence/contextual_alignment_v1/train.json",
                       "evidence/cognitive_graph_v1/model.json", "evidence/cognitive_graph_v1/train.json",
                       "evidence/cognitive_orchestration_v1/dispatch.json") + tuple(
        path for _, _, path in lexical_testimony.SOURCES.values() if path is not None)
    for relative in ("AGENTS.md", "Makefile", "GNUmakefile", "pyproject.toml") + lexical_sources:
        path = ROOT / relative
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
            raise ValueError("I/O source reference escapes repository")
        value["files"][relative] = sha256(path.read_bytes()).hexdigest()
    value["schema"] = "nabt.io.snapshot.v1"
    return value


def worker(payload):
    import resource
    resource.setrlimit(resource.RLIMIT_CPU, (20, 21))
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_RESULT, MAX_RESULT))
    resource.setrlimit(resource.RLIMIT_AS, (MAX_ADDRESS_SPACE, MAX_ADDRESS_SPACE))
    if type(payload) is not dict or set(payload) != {"request", "snapshot_sha256"}:
        raise ValueError("Invalid internal I/O worker envelope")
    request = validate_request(payload["request"])
    if digest(snapshot()) != payload["snapshot_sha256"]:
        raise ValueError("STALE_IO_SNAPSHOT")
    result = gateway_routes.execute(request["route"], request["payload"], inside_worker=True)
    if digest(snapshot()) != payload["snapshot_sha256"]:
        raise ValueError("SOURCE_CHANGED_DURING_IO")
    _encoded(result, MAX_RESULT, floats=True)
    return {"execution_status": "EXECUTED", "owner_result": result}


def catalog():
    links = gateway_links.build()
    return {"schema": "nabt.io.catalog.v1", "policy": POLICY,
            "shared_proof_families": list(gateway_routes.SHARED_FAMILIES),
            "routes": [{"id": k, "proof_families": list(v[0])} for k,v in gateway_routes.ROUTES.items()],
            "proof_test_links": links, "internal_interfaces_are_public_outputs": False}


def run(request):
    request = validate_request(request)
    before = digest(snapshot())
    links = gateway_links.build(request["route"])
    execution = invoke_bounded("gateway-worker", {"request": request, "snapshot_sha256": before}, maximum_request=MAX_REQUEST+1024)
    if digest(snapshot()) != before:
        raise ValueError("SOURCE_CHANGED_DURING_IO")
    result = {"schema": RESULT_SCHEMA, "policy": POLICY, "request": request,
        "request_sha256": digest(request), "snapshot_sha256": before,
        "proof_test_links": links, "execution": execution, "status": execution["execution_status"],
        "limits": {"retrieval_is_proof": False, "test_references_are_runs": False,
                   "python_lean_refinement_proved": False, "semantic_rank_promoted": False,
                   "world_truth_established": False, "action_authority": "NONE"}}
    _encoded(result, MAX_RESULT, floats=True)
    return result


def accept_output(report, *, expected_request):
    """Consumer admission: no raw owner output and no self-hash-only acceptance."""
    try:
        _encoded(report, MAX_RESULT, floats=True)
        request = validate_request(expected_request)
        if type(report) is not dict or report.get("schema") != RESULT_SCHEMA or report.get("policy") != POLICY:
            raise ValueError("RAW_OR_UNKNOWN_OUTPUT_NOT_ADMITTED")
        if wire(report.get("request")) != wire(request) or report.get("request_sha256") != digest(request):
            raise ValueError("INDEPENDENT_IO_REQUEST_MISMATCH")
        if report.get("snapshot_sha256") != digest(snapshot()):
            raise ValueError("STALE_IO_SNAPSHOT")
        if report.get("status") != "EXECUTED":
            return {"valid": False, "status": "NOT_EXECUTED", "semantic_rank_promoted": False}
        fresh = run(request)
        if wire(report) != wire(fresh):
            raise ValueError("IO_OUTPUT_REPLAY_MISMATCH")
        return {"valid": True, "status": "VERIFIED_IO_REPLAY", "semantic_rank_promoted": False,
                "scope": "SAME_REQUEST_CURRENT_PROOF_TEST_SNAPSHOT_AND_ORIGINAL_OWNER_RESULT"}
    except (ResourceLimit, MemoryError) as error:
        return {"valid": False, "status": "RESOURCE_LIMIT", "message": str(error), "semantic_rank_promoted": False}
    except (ValueError, OSError, TypeError, KeyError, RecursionError) as error:
        return {"valid": False, "status": "REJECT", "message": str(error), "semantic_rank_promoted": False}


def arguments(parser):
    from pathlib import Path
    parser.add_argument("action", choices=("catalog", "run", "verify"))
    parser.add_argument("--request", type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--output", type=Path)


def cli(args):
    if args.action == "catalog":
        if args.request or args.receipt:
            raise ValueError("I/O catalogue accepts no caller evidence")
        return catalog()
    if args.request is None or (args.action == "verify") != (args.receipt is not None):
        raise ValueError("Supply --request; --receipt is required only for verify")
    with args.request.open("rb") as f:
        request = request_from_bytes(f.read(MAX_REQUEST+1))
    if args.action == "run":
        return run(request)
    with args.receipt.open("rb") as f:
        report = strict_loads(f.read(MAX_RESULT+1), maximum_bytes=MAX_RESULT, report=True)
    return accept_output(report, expected_request=request)
