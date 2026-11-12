"""Retrieve source cards, bind a bounded request, execute owners, cite results.

The answer renderer is deterministic. A future language model may propose a
typed request, but neither similarity nor generated text authorizes execution.
"""
from __future__ import annotations

from copy import deepcopy
import os
import re
import signal
import subprocess
import tempfile

from tools.entropy_framework.reuse_run import entry_command
from tools.evidence_lifecycle_v1 import ResourceLimit, _encoded, strict_loads, wire
from .operations import OperationSearchIndex, ROOT, digest, source_snapshot
from .operation_runtime import execute, validate_inputs

REQUEST_SCHEMA = "nabt.operation-rag.request.v1"
RESULT_SCHEMA = "nabt.operation-rag.result.v1"
MAX_REQUEST = 128 * 1024
MAX_RESULT = 8 * 1024 * 1024
WORKER_SECONDS = 30


def gateway_worker_limits(route):
    """Installed budgets, not caller-selected limits.

    Orchestration replays at most 16 conditional sources through six owners.
    The original one-owner budget is insufficient for that bounded workload.
    """
    return (120, 180) if route in ('cognitive.orchestrate', 'text.read') else (20, WORKER_SECONDS)
# Inherited by Lean checkers too: their allocator can reserve a 1 GiB arena
# before resident use. A 1 GiB address-space cap changes valid native outcomes.
MAX_ADDRESS_SPACE = 4 * 1024**3


def request_from_bytes(raw):
    return validate_request(strict_loads(raw, maximum_bytes=MAX_REQUEST))


def validate_request(request):
    _encoded(request, MAX_REQUEST)
    allowed = {"schema", "query", "operation", "inputs", "limit"}
    if type(request) is not dict or set(request) - allowed or request.get("schema") != REQUEST_SCHEMA:
        raise ValueError("Unknown operation RAG request schema or fields")
    query = request.get("query")
    if type(query) is not str or not query.strip() or len(query.encode()) > 16384:
        raise ValueError("A nonempty bounded query is required")
    if type(request.get("limit", 5)) is not int or not 1 <= request.get("limit", 5) <= 13:
        raise ValueError("Display limit must be in 1..13")
    if ("operation" in request) != ("inputs" in request):
        raise ValueError("An explicit operation and inputs must be supplied together")
    if "operation" in request:
        validate_inputs(request["operation"], request["inputs"])
    return deepcopy(request)


def _bind(request):
    if "operation" in request:
        return {"operation": request["operation"], "inputs": request["inputs"],
                "basis": "CALLER_TYPED_REQUEST", "query_spans": [],
                "free_text_intent_established": False}
    query = request["query"]
    # Full matches only. Quotes, marks and raw byte positions remain unchanged.
    prefixes = {"رمّز": "encode", "رمز": "encode", "احسب أثر": "effect",
                "حلل شكل": "analyse", "حلل اشتقاق": "derivation"}
    operation, values, matches = None, None, []
    for prefix, identifier in prefixes.items():
        match = re.fullmatch(re.escape(prefix) + r" «([^«»]+)»", query)
        if match:
            operation, values, matches = identifier, {"text": match.group(1)}, [match.span(1)]
            break
    if re.fullmatch(r"قارن «[^«»]+»(?: و«[^«»]+»){1,7}", query):
        quoted = list(re.finditer(r"«([^«»]+)»", query))
        operation, values, matches = "contrast", {"texts": [m.group(1) for m in quoted]}, [m.span(1) for m in quoted]
    count = re.fullmatch(r"احسب عدد الأشكال للوزن ([0-9]{1,2})", query)
    if count:
        operation, values, matches = "count", {"weight": int(count.group(1))}, [count.span(1)]
    if operation is None:
        return None
    validate_inputs(operation, values)
    return {"operation": operation, "inputs": values, "basis": "EXACT_COMMAND_GRAMMAR_V1",
            "free_text_intent_established": False,
            "query_spans": [{"text": query[a:b], "codepoint_span": [a, b],
                             "utf8_span": [len(query[:a].encode()), len(query[:b].encode())]} for a, b in matches]}


def worker(payload):
    """Internal fixed dispatch endpoint. Resource limits also cover descendants."""
    import resource
    resource.setrlimit(resource.RLIMIT_CPU, (20, 21))
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_RESULT, MAX_RESULT))
    resource.setrlimit(resource.RLIMIT_AS, (MAX_ADDRESS_SPACE, MAX_ADDRESS_SPACE))
    return execute_bound(payload)


def execute_bound(payload):
    """Existing worker body; also used inside the already bounded I/O worker."""
    if type(payload) is not dict or set(payload) != {"operation", "inputs", "snapshot_sha256"}:
        raise ValueError("Invalid worker envelope")
    before, _ = source_snapshot()
    if digest(before) != payload["snapshot_sha256"]:
        raise ValueError("STALE_OPERATION_SNAPSHOT")
    result = execute(payload["operation"], payload["inputs"])
    after, _ = source_snapshot()
    if digest(after) != payload["snapshot_sha256"]:
        raise ValueError("SOURCE_CHANGED_DURING_EXECUTION")
    _encoded(result, MAX_RESULT, floats=True)
    return result


def _invoke(binding, snapshot_sha256):
    payload = {"operation": binding["operation"], "inputs": binding["inputs"],
               "snapshot_sha256": snapshot_sha256}
    return invoke_bounded("rag-worker", payload)


def invoke_bounded(command, payload, *, maximum_request=MAX_REQUEST):
    """Shared fixed worker transport; never accept command names from a request."""
    if command not in ("rag-worker", "gateway-worker"):
        raise ValueError("Unknown installed worker")
    raw = _encoded(payload, maximum_request)
    env = {key: value for key, value in os.environ.items() if not key.startswith("NABT_")}
    # Fixed installed package paths; caller input cannot select code or binaries.
    env["PYTHONPATH"] = os.pathsep.join((str(ROOT / "src"), str(ROOT)))
    argv = entry_command("grammar-catalog", [command])
    with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
        process = subprocess.Popen(argv, cwd=ROOT, env=env, stdin=subprocess.PIPE,
                                   stdout=output, stderr=errors, start_new_session=True)
        try:
            seconds = (gateway_worker_limits(payload.get('request', {}).get('route'))[1]
                       if command == 'gateway-worker' else WORKER_SECONDS)
            process.communicate(raw, timeout=seconds)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
            return {"execution_status": "RESOURCE_LIMIT", "code": "WORKER_TIMEOUT",
                    "semantic_rank_promoted": False}
        finally:
            if process.stdin is not None:
                process.stdin.close()
        output.seek(0)
        data = output.read(MAX_RESULT + 1)
        if len(data) > MAX_RESULT or process.returncode in (-signal.SIGXCPU, -signal.SIGXFSZ, -signal.SIGKILL):
            return {"execution_status": "RESOURCE_LIMIT", "code": "WORKER_BUDGET",
                    "semantic_rank_promoted": False}
        if process.returncode:
            try:
                failure = strict_loads(data, maximum_bytes=MAX_RESULT, report=True)
                if type(failure) is dict and failure.get("status") == "RESOURCE_LIMIT":
                    return {"execution_status": "RESOURCE_LIMIT", "code": "OWNER_RESOURCE_LIMIT",
                            "semantic_rank_promoted": False}
            except ValueError:
                pass
            return {"execution_status": "WORKER_ERROR", "code": "OWNER_OR_INPUT_FAILURE",
                    "exit_code": process.returncode, "semantic_rank_promoted": False}
        return strict_loads(data, maximum_bytes=MAX_RESULT, report=True)


def _answer(binding, execution, card):
    if binding is None:
        return {"text_ar": "الاسترجاع يعرض عمليات مرشحة. يلزم تحديد العملية ووسائطها لإجراء الحساب.",
                "claims": [], "next_obligation": "SUPPLY_TYPED_OPERATION_OR_EXACT_COMMAND"}
    result = execution.get("owner_result", {})
    state = execution["execution_status"]
    owner_state = result.get("status", result.get("run_status"))
    check = execution.get("owner_verification")
    if state != "EXECUTED":
        text = "لم يكتمل التنفيذ؛ تُحفظ حالة المالك أو حد الموارد كما وردت."
    elif check is not None and check.get("valid") is not True:
        text = "أعيد تقرير المالك، ولم يغلق فاحصه بوابة التحقق؛ لا يُعتمد نجاح العملية."
    elif binding["operation"] == "encode":
        text = "الترميز العددي: " + (result["numeric_code"] or result["numeric_code_hex"]) + ". النطاق: هوية التسلسل."
    elif binding["operation"] == "count":
        text = "عدد الأشكال ضمن القانون والحالة والنمط المحددين: " + result["count"] + "."
    elif binding["operation"] == "contrast":
        text = ("التمثيلات العددية متمايزة؛ لم يثبت بذلك الشخص أو البناء أو المعنى." if result["all_distinct"] is True
                else "تُحفظ نتائج كل لفظ؛ التمايز الكامل غير مثبت.")
    else:
        text = "نُفذت العملية ضمن عقدها؛ تُعرض النتيجة وآثارها وحدودها في تقرير المالك."
    if owner_state:
        text += " حالة المالك: " + str(owner_state) + "."
    return {"text_ar": text, "claims": [{"result_pointer": "/execution",
            "source_path": card["source"]["path"], "source_symbol": card["source"]["symbol"],
            "source_sha256": card["source"]["file_sha256"], "scope": card["scope"]}],
            "next_obligation": "RETAIN_OWNER_LIMITS_AND_REPLAY_AGAINST_INDEPENDENT_REQUEST"}


def run(request):
    return _run(request, _invoke)


def run_inside_worker(request):
    # Avoid a detached nested process group escaping the gateway's kill group.
    # The outer worker supplies the resource limits; the same owner body runs.
    def invoke(binding, snapshot_sha256):
        return execute_bound({"operation": binding["operation"], "inputs": binding["inputs"],
                              "snapshot_sha256": snapshot_sha256})
    return _run(request, invoke)


def _run(request, invoke):
    request = validate_request(request)
    index = OperationSearchIndex()
    retrieved = index.search(request["query"], limit=request.get("limit", 5))
    binding = _bind(request)
    card, execution = None, None
    if binding is not None:
        # An explicit request never disappears outside retrieval top-k.
        card = index.rehydrate("item", binding["operation"])
        binding["effective_inputs"] = validate_inputs(binding["operation"], binding["inputs"])
        binding["displayed_in_top_k"] = any(r["id"] == binding["operation"] for r in retrieved["candidates"])
        execution = invoke(binding, index.snapshot_sha256)
    index.assert_current()
    result = {"schema": RESULT_SCHEMA, "request": request, "request_sha256": digest(request),
        "snapshot_sha256": index.snapshot_sha256, "retrieval": retrieved, "binding": binding,
        "selected_operation": card, "execution": execution,
        "status": "NEEDS_REQUEST" if binding is None else execution["execution_status"],
        "answer": _answer(binding, execution, card),
        "limits": {"retrieval_is_proof": False, "python_lean_refinement_proved": False,
                   "neural_semantics_trained": False, "world_truth_established": False,
                   "all_arabic_complete": False, "result_cache_used": False}}
    _encoded(result, MAX_RESULT, floats=True)
    return result


def verify(report, *, expected_request):
    """Bind to an independently supplied request, refresh sources, replay all fields."""
    try:
        _encoded(report, MAX_RESULT, floats=True)
        request = validate_request(expected_request)
        if type(report) is not dict or report.get("schema") != RESULT_SCHEMA:
            raise ValueError("Unknown receipt schema")
        if wire(report.get("request")) != wire(request) or report.get("request_sha256") != digest(request):
            raise ValueError("Independent request mismatch")
        snapshot, _ = source_snapshot()
        if report.get("snapshot_sha256") != digest(snapshot):
            raise ValueError("STALE_OPERATION_SNAPSHOT")
        if report.get("status") not in ("EXECUTED", "OWNER_ERROR"):
            return {"valid": False, "status": "NOT_EXECUTED", "semantic_rank_promoted": False}
        fresh = run(request)
        if wire(report) != wire(fresh):
            raise ValueError("RAG_RECEIPT_REPLAY_MISMATCH")
        return {"valid": True, "status": "VERIFIED_REPLAY", "semantic_rank_promoted": False,
                "scope": "SAME_REQUEST_AND_INSTALLED_OWNERS; deferred owner results remain deferred"}
    except (ResourceLimit, MemoryError) as error:
        return {"valid": False, "status": "RESOURCE_LIMIT", "message": str(error), "semantic_rank_promoted": False}
    except (ValueError, OSError, KeyError, TypeError, RecursionError) as error:
        return {"valid": False, "status": "REJECT", "message": str(error), "semantic_rank_promoted": False}
