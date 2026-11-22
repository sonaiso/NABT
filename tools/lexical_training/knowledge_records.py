"""Bounded prior-record/provenance/packing experiment; standard library only.

These engineering records are not a model of a brain, Arabic parser, or proof
that their categories are cognitive primitives. Digests check content integrity,
not authenticity or truth. provenance_mode records origin, not truth assessment.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
import zlib

KINDS = frozenset({"occurrence", "conception", "criterion", "classification",
                   "claim", "evidence", "prior", "information", "assessment", "link_audit"})
MAX_RAW = 1_048_576
MAX_RECORDS = 1000


def _json_value(value, depth=0):
    if depth > 40:
        raise ValueError("JSON nesting limit")
    if value is None or type(value) in (bool, int, str):
        return
    if type(value) is list:
        for item in value:
            _json_value(item, depth + 1)
        return
    if type(value) is dict and all(type(k) is str for k in value):
        for item in value.values():
            _json_value(item, depth + 1)
        return
    raise ValueError("Only JSON objects/lists, strings, integers, bool, null; no floats")


def canonical(value):
    _json_value(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _keys(data, expected):
    if type(data) is not dict or set(data) != set(expected.split()):
        raise ValueError("Record does not match its closed schema")


@dataclass(frozen=True, order=True)
class Ref:
    record_id: str
    version: int

    def __post_init__(self):
        if type(self.record_id) is not str or not self.record_id or type(self.version) is not int or self.version < 1:
            raise ValueError("Invalid exact reference")

    def data(self):
        return {"id": self.record_id, "version": self.version}

    @classmethod
    def read(cls, data):
        _keys(data, "id version")
        return cls(data["id"], data["version"])


@dataclass(frozen=True)
class Record:
    ref: Ref
    kind: str
    domain: str
    content_json: str
    provenance_mode: str
    dependencies: tuple[Ref, ...] = ()
    sources: tuple[Ref, ...] = ()
    residuals: tuple[str, ...] = ()
    trace: tuple[str, ...] = ()

    def __post_init__(self):
        if type(self.ref) is not Ref or any(type(s) is not str or not s.strip() for s in (self.kind, self.domain, self.provenance_mode)) or self.kind not in KINDS:
            raise ValueError("Missing record kind/domain/provenance_mode")
        if type(self.content_json) is not str:
            raise ValueError("Content must be an encoded string")
        content = json.loads(self.content_json)
        if type(content) is not dict or canonical(content) != self.content_json:
            raise ValueError("Record content must be canonical JSON")
        for field in (self.dependencies, self.sources, self.residuals, self.trace):
            if type(field) is not tuple:
                raise ValueError("Record collections must be immutable tuples")
        if any(type(r) is not Ref for r in self.dependencies + self.sources):
            raise ValueError("Dependencies and sources require exact Ref values")
        if any(type(s) is not str or not s.strip() for s in self.residuals + self.trace):
            raise ValueError("Residuals and trace identities require nonempty strings")

    @property
    def content(self):
        return json.loads(self.content_json)  # a detached value, not mutable storage

    @classmethod
    def make(cls, record_id, version, kind, domain, content, provenance_mode,
             dependencies=(), sources=(), residuals=(), trace=()):
        if type(content) is not dict:
            raise ValueError("Record content must be an object")
        return cls(Ref(record_id, version), kind, domain, canonical(content), provenance_mode,
                   tuple(dependencies), tuple(sources), tuple(residuals), tuple(trace))

    def data(self):
        return {"ref": self.ref.data(), "kind": self.kind, "domain": self.domain,
                "content": self.content, "provenance_mode": self.provenance_mode,
                "dependencies": [r.data() for r in self.dependencies],
                "sources": [r.data() for r in self.sources],
                "residuals": list(self.residuals), "trace": list(self.trace)}

    @classmethod
    def read(cls, data):
        _keys(data, "ref kind domain content provenance_mode dependencies sources residuals trace")
        if any(type(data[k]) is not list for k in ("dependencies", "sources", "residuals", "trace")):
            raise ValueError("Record collections require JSON arrays")
        ref = Ref.read(data["ref"])
        return cls.make(ref.record_id, ref.version, data["kind"], data["domain"],
                        data["content"], data["provenance_mode"],
                        [Ref.read(r) for r in data["dependencies"]],
                        [Ref.read(r) for r in data["sources"]], data["residuals"], data["trace"])


@dataclass(frozen=True)
class Operation:
    operation_id: str
    name: str
    domain: str
    inputs: tuple[Ref, ...]
    outputs: tuple[Ref, ...]
    status: str
    rule: str
    reasons: tuple[str, ...] = ()

    def __post_init__(self):
        if any(type(s) is not str or not s.strip() for s in (self.operation_id, self.name, self.domain, self.status, self.rule)):
            raise ValueError("Operation identity and metadata require nonempty strings")
        if self.status not in ("LICENSED", "DEFER", "BLOCK", "UNDEFINED"):
            raise ValueError("Unknown operation status")
        if any(type(v) is not tuple for v in (self.inputs, self.outputs, self.reasons)) or any(type(r) is not Ref for r in self.inputs + self.outputs):
            raise ValueError("Operation references require immutable Ref tuples")
        if any(type(s) is not str or not s.strip() for s in self.reasons):
            raise ValueError("Operation reasons require strings")

    def data(self):
        return {"id": self.operation_id, "name": self.name, "domain": self.domain,
                "inputs": [r.data() for r in self.inputs], "outputs": [r.data() for r in self.outputs],
                "status": self.status, "rule": self.rule, "reasons": list(self.reasons)}

    @classmethod
    def read(cls, data):
        _keys(data, "id name domain inputs outputs status rule reasons")
        if any(type(data[k]) is not list for k in ("inputs", "outputs", "reasons")):
            raise ValueError("Operation collections require JSON arrays")
        return cls(data["id"], data["name"], data["domain"],
                   tuple(Ref.read(r) for r in data["inputs"]), tuple(Ref.read(r) for r in data["outputs"]),
                   data["status"], data["rule"], tuple(data["reasons"]))


@dataclass(frozen=True)
class Outcome:
    status: str
    value: object = None
    reasons: tuple[str, ...] = ()


class Store:
    def __init__(self):
        self.records = {}
        self.operations = {}

    def add(self, record):
        if type(record) is not Record:
            raise ValueError("Store accepts Record values")
        if record.ref in self.records and self.records[record.ref] != record:
            raise ValueError("An existing version cannot be overwritten")
        self.records[record.ref] = record
        return record

    def log(self, operation):
        if type(operation) is not Operation:
            raise ValueError("Trace accepts Operation values")
        if operation.operation_id in self.operations and self.operations[operation.operation_id] != operation:
            raise ValueError("An operation identity cannot be overwritten")
        self.operations[operation.operation_id] = operation

    def retrieve(self, ref):
        if type(ref) is not Ref:
            return Outcome("BLOCK", reasons=("wrong_reference_type",))
        record = self.records.get(ref)
        return Outcome("LICENSED", record) if record is not None else Outcome("DEFER", reasons=("exact_version_missing",))


def closure(store, roots, operation_roots=()):
    record_queue, op_queue = list(roots), list(operation_roots)
    if any(type(r) is not Ref for r in record_queue) or any(type(s) is not str for s in op_queue):
        return Outcome("BLOCK", reasons=("wrong_closure_root_type",))
    records, operations = {}, {}
    while record_queue or op_queue:
        while record_queue:
            ref = record_queue.pop()
            if ref in records:
                continue
            record = store.records.get(ref)
            if record is None:
                return Outcome("DEFER", reasons=("dependency_missing:" + canonical(ref.data()),))
            records[ref] = record
            record_queue.extend(record.dependencies + record.sources)
            op_queue.extend(record.trace)
        while op_queue:
            op_id = op_queue.pop()
            if op_id in operations:
                continue
            operation = store.operations.get(op_id)
            if operation is None:
                return Outcome("DEFER", reasons=("operation_trace_missing:" + op_id,))
            operations[op_id] = operation
            record_queue.extend(operation.inputs + operation.outputs)
        if len(records) > MAX_RECORDS or len(operations) > MAX_RECORDS:
            return Outcome("BLOCK", reasons=("snapshot_record_limit",))
    return Outcome("LICENSED", (records, operations))


@dataclass(frozen=True)
class Packed:
    manifest_json: str
    compressed: bytes

    @property
    def manifest(self):
        return json.loads(self.manifest_json)


def fold(store, roots, operation_roots=()):
    roots, operation_roots = tuple(roots), tuple(operation_roots)
    selected = closure(store, roots, operation_roots)
    if selected.status != "LICENSED":
        return selected
    records, operations = selected.value
    payload = {"schema": "knowledge_snapshot/v2", "roots": [r.data() for r in roots],
               "operation_roots": list(operation_roots),
               "records": [records[r].data() for r in sorted(records)],
               "operations": [operations[r].data() for r in sorted(operations)]}
    raw = canonical(payload).encode("utf-8")
    if len(raw) > MAX_RAW:
        return Outcome("BLOCK", reasons=("snapshot_byte_limit",))
    manifest = {"schema": payload["schema"], "codec": "zlib+canonical-json-utf8/no-normalization",
                "raw_bytes": len(raw), "sha256": sha256(raw).hexdigest(),
                "roots": payload["roots"], "operation_roots": list(operation_roots)}
    return Outcome("LICENSED", Packed(canonical(manifest), zlib.compress(raw)))


def unfold(packed, max_raw=MAX_RAW):
    try:
        manifest = packed.manifest
        if type(max_raw) is not int or not 0 < max_raw <= MAX_RAW:
            return Outcome("BLOCK", reasons=("invalid_resource_limit",))
        if len(packed.compressed) > MAX_RAW or type(manifest["raw_bytes"]) is not int or not 0 <= manifest["raw_bytes"] <= max_raw:
            return Outcome("BLOCK", reasons=("decompression_resource_limit",))
        decoder = zlib.decompressobj()
        raw = decoder.decompress(packed.compressed, max_raw + 1)
        if len(raw) > max_raw or decoder.unconsumed_tail:
            return Outcome("BLOCK", reasons=("decompression_resource_limit",))
        if not decoder.eof or decoder.unused_data:
            return Outcome("BLOCK", reasons=("invalid_compressed_boundary",))
        if len(raw) != manifest["raw_bytes"] or sha256(raw).hexdigest() != manifest["sha256"]:
            return Outcome("BLOCK", reasons=("content_integrity_mismatch",))
        payload = json.loads(raw.decode("utf-8"))
        _keys(payload, "schema roots operation_roots records operations")
        if any(type(payload[k]) is not list for k in ("roots", "operation_roots", "records", "operations")):
            return Outcome("BLOCK", reasons=("invalid_snapshot_collections",))
        if canonical(payload).encode("utf-8") != raw:
            return Outcome("BLOCK", reasons=("noncanonical_payload",))
        if payload["schema"] != "knowledge_snapshot/v2" or manifest["schema"] != payload["schema"] or manifest["codec"] != "zlib+canonical-json-utf8/no-normalization":
            return Outcome("BLOCK", reasons=("schema_or_codec_mismatch",))
        if payload["roots"] != manifest["roots"] or payload["operation_roots"] != manifest["operation_roots"]:
            return Outcome("BLOCK", reasons=("manifest_root_mismatch",))
        if len(payload["records"]) > MAX_RECORDS or len(payload["operations"]) > MAX_RECORDS:
            return Outcome("BLOCK", reasons=("snapshot_record_limit",))
        restored = Store()
        for item in payload["records"]:
            restored.add(Record.read(item))
        for item in payload["operations"]:
            restored.log(Operation.read(item))
        checked = closure(restored, tuple(restored.records), tuple(restored.operations))
        if checked.status != "LICENSED":
            return Outcome("BLOCK", reasons=("snapshot_is_not_self_contained",) + checked.reasons)
        roots = tuple(Ref.read(r) for r in payload["roots"])
        checked_roots = closure(restored, roots, payload["operation_roots"])
        if checked_roots.status != "LICENSED":
            return Outcome("BLOCK", reasons=("snapshot_roots_missing",))
        return Outcome("LICENSED", restored)
    except (ValueError, TypeError, KeyError, UnicodeError, zlib.error, RecursionError) as error:
        return Outcome("BLOCK", reasons=("invalid_snapshot:" + type(error).__name__,))
