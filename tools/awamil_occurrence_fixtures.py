"""Frozen hand-labelled occurrences, with byte spans reconstructed only from literal text."""
import csv
from hashlib import sha256
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]/"evidence/awamil_occurrence_v1/manual.tsv"
SOURCE_SHA256 = "b363c8b5871e1a76ae41fdbded516f72f81b238326f61d7df0c7bc7b38044588"


def one_span(text, surface):
    raw, part = text.encode(), surface.encode()
    if raw.count(part) != 1:
        raise ValueError("Manual witness must have one occurrence: "+text)
    start = raw.index(part)
    return [start, start+len(part)]


def fixtures():
    raw=SOURCE.read_bytes()
    if sha256(raw).hexdigest()!=SOURCE_SHA256:
        raise ValueError("Manual fixture identity changed")
    out=[]
    for r in csv.DictReader(raw.decode().splitlines(),delimiter="\t"):
        text, principal = r["text"], r["principal"]
        span=one_span(text,principal)
        g=None if r["operator"]=="-" else one_span(text,r["operator"])
        prefix=r["sign_prefix"]
        mark=None
        if prefix!="-":
            if not principal.startswith(prefix):
                raise ValueError("Manual sign not in labelled principal")
            end=span[0]+len(prefix.encode())
            mark=[end-len(prefix[-1].encode()),end]
        out.append({"factor":int(r["id"]),"text":text,"operator_span":g,"principal_span":span,
                    "case":r["case"],"mark_span":mark})
    if [r["factor"] for r in out]!=list(range(1,101)):
        raise ValueError("Manual inventory coverage differs")
    return out


def agrees(row, gold):
    operators=row["factors"]
    if len(operators)!=1 or row["factor"]!=gold["factor"] or operators[0]["id"]!=f"jurjani:{gold['factor']:03}":
        return False
    surf=operators[0]["occurrence"]
    if (surf["utf8_span"] if surf else None)!=gold["operator_span"] or row["principal_span"]!=gold["principal_span"]:
        return False
    for s in row["signs"]:
        if row["bindings"][s["role"]]["utf8_span"]!=gold["principal_span"]:
            continue
        if gold["case"]=="raf_local":
            return s.get("local_case")=="raf" and s["utf8_span"] is None and s["observed"] is None
        if s.get("utf8_span")==gold["mark_span"] and s["conditional_sign"]["case_name"]==gold["case"]:
            return True
    return False
