"""Local, single-text clients over the independently replayed public gateway."""
from html import escape
from pathlib import Path
import sys
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

from tools.evidence_lifecycle_v1 import ResourceLimit
from . import gateway

LABELS = (("understood", "ما فُهم"), ("why", "لماذا؟"), ("unresolved", "ما الذي لم يُحسم؟"))
MAX_FORM = 3 * 8192 + 16


def checked_view(text):
    request = {"schema": gateway.REQUEST_SCHEMA, "route": "text.read", "payload": {"text": text}}
    receipt = gateway.run(request)
    if receipt["status"] != "EXECUTED":
        return {"verified": False, "error": "تعذّر تنفيذ الفحص: " + receipt["status"]}
    verification = gateway.accept_output(receipt, expected_request=request)
    if not verification["valid"]:
        return {"verified": False, "error": "تعذّر التحقق من النتيجة: " + verification["status"]}
    result = receipt["execution"]["owner_result"]
    return {"verified": True, "cards": result["cards"], "grammar_stop_ar": result["grammar_stop_ar"],
            "source": result["source"], "world_truth_established": result["world_truth_established"],
            "request_sha256": receipt["request_sha256"]}


def as_text(view):
    if not view["verified"]:
        return view["error"]
    lines = []
    for c in view["cards"]:
        lines.append(c["degree"])
        lines.extend(label + " — " + c[key] for key, label in LABELS)
        lines.append("")
    lines.append("آخر مرحلة بلغها المسار النحوي الأصلي: " + view["grammar_stop_ar"])
    return "\n".join(lines)


def page(text="", view=None, error=""):
    panels = []
    if view and view["verified"]:
        for c in view["cards"]:
            fields = "".join("<dt>"+label+"</dt><dd>"+escape(c[key])+"</dd>" for key, label in LABELS)
            panels.append("<article><h2>"+escape(c["degree"])+"</h2><dl>"+fields+"</dl></article>")
        panels.append("<p>آخر مرحلة بلغها المسار النحوي الأصلي: "+escape(view["grammar_stop_ar"])+"</p>")
    if error or (view and not view["verified"]):
        panels.append("<p role='alert'>"+escape(error or view["error"])+"</p>")
    template = Path(__file__).with_name("data") / "text_reader.html"
    form = (
        "<form method='post' action='/'><label for='text'>النص العربي</label>"
        "<textarea id='text' name='text' required rows='4' dir='auto' placeholder='زيد حكيم'>"
        + escape(text) + "</textarea><button>اقرأ النص</button></form>" + "".join(panels))
    return template.read_text(encoding="utf-8").replace("<!--FORM-->", form)


def application(environ, start_response):
    status = "200 OK"
    text = ""
    host = environ.get("HTTP_HOST", "").split(":")[0]
    if host and host not in ("127.0.0.1", "localhost"):
        status, body = "403 Forbidden", page(error="استخدم عنوان نبط المحلي.")
    elif environ["PATH_INFO"] != "/":
        status, body = "404 Not Found", page(error="العنوان غير موجود.")
    elif environ["REQUEST_METHOD"] == "GET":
        body = page()
    elif environ["REQUEST_METHOD"] == "POST" and (
            environ.get("HTTP_SEC_FETCH_SITE") == "cross-site" or
            (environ.get("HTTP_ORIGIN") and environ["HTTP_ORIGIN"] != "http://" + environ.get("HTTP_HOST", ""))):
        status, body = "403 Forbidden", page(error="أرسل النص من صفحة نبط المحلية.")
    elif environ["REQUEST_METHOD"] == "POST":
        try:
            if environ.get("CONTENT_TYPE", "").split(";")[0] != "application/x-www-form-urlencoded":
                raise ValueError("صيغة الطلب غير مدعومة.")
            length = int(environ.get("CONTENT_LENGTH") or 0)
            if not 0 < length <= MAX_FORM:
                raise ValueError("الطلب فارغ أو يتجاوز حجم المدخل المتاح.")
            fields = parse_qs(environ["wsgi.input"].read(length).decode("utf-8"), strict_parsing=True,
                              keep_blank_values=True, errors="strict", max_num_fields=1)
            if set(fields) != {"text"}:
                raise ValueError("أدخل نصًا واحدًا.")
            text, = fields["text"]
            view = checked_view(text)
            body = page(text, view)
            if not view["verified"]:
                status = "503 Service Unavailable"
        except ResourceLimit:
            status, body = "413 Payload Too Large", page(text, error="تجاوز النص ميزانية القراءة.")
        except ValueError as e:
            status, body = "400 Bad Request", page(text, error=str(e))
    else:
        status, body = "405 Method Not Allowed", page(error="طريقة الطلب غير مدعومة.")
    data = body.encode()
    start_response(status, [("Content-Type", "text/html; charset=utf-8"),
                            ("Content-Length", str(len(data))), ("Cache-Control", "no-store")])
    return [data]


def command(args):
    if args.request or args.receipt:
        raise ValueError("Use the text field for the reader")
    if args.action == "read":
        if args.port is not None:
            raise ValueError("--port requires serve")
        text = args.text if args.text is not None else sys.stdin.buffer.read(8193).decode("utf-8")
        return checked_view(text)
    if args.text is not None or args.output:
        raise ValueError("gateway serve takes only --port")
    port = args.port if args.port is not None else 8765
    if not 0 <= port <= 65535:
        raise ValueError("Invalid loopback port")
    with make_server("127.0.0.1", port, application) as server:
        print(f"http://127.0.0.1:{server.server_port}/", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
