"""Local interactive verse reader. Every page is rendered from a freshly replay-verified NABT receipt."""
import argparse
from html import escape
from pathlib import Path
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

from tools.grammar_catalog import gateway
from tools.grammar_catalog.ayat_al_dayn import source


def checked(withdraw=(),context=(),question=None,scene=None):
    request={"schema":gateway.REQUEST_SCHEMA,"route":"ayat.read","payload":{"text":source(),"withdraw":list(withdraw)}}
    if context:
        request["payload"]["withdraw_context"]=list(context)
    if question:
        request["payload"]["question"]=question
    if scene is not None:
        request["payload"]["scene"]=scene
    receipt=gateway.run(request)
    verification=gateway.accept_output(receipt,expected_request=request)
    if not verification["valid"]:
        raise ValueError("تعذرت إعادة التحقق من إيصال البوابة")
    return receipt["execution"]["owner_result"],receipt["request_sha256"]


STYLE = """
*{box-sizing:border-box}body{margin:0;background:#f7f5ee;color:#172b29;font:17px/1.8 system-ui,sans-serif}
main{max-width:1050px;margin:auto;padding:26px}header{border-bottom:3px solid #197064}h1{font:700 2.5rem/1.4 serif;margin:.4em 0}
h2{margin-top:1.6em}p{margin:.45em 0 1em}.verse{font:1.45rem/2.2 serif;background:white;padding:18px 22px}
li{margin:.6em 0}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,295px),1fr));gap:12px}
article,details,form{background:white;border:1px solid #d6dcd3;border-radius:8px;padding:12px 16px}
article h3{margin:0;font-size:1.05em;color:#185e55}article p{margin:.3em 0}small{color:#49625e}
details{margin:5px 0}summary{cursor:pointer}input,button,select{font:inherit;padding:4px 10px;max-width:100%}
button{background:#135e54;color:white;border:0;border-radius:4px;cursor:pointer}code{overflow-wrap:anywhere}
a{color:#075f83}.debt{color:#854a23}input[type=number]{width:7em}footer{margin:24px 0}bdi{direction:ltr}
"""


SCENARIOS = {
    "unspecified":("لم تعيَّن واقعة",{}),
    "debt_term":("دين إلى أجل مسمّى",{"debt":True,"specified_term":True}),
    "no_debt":("انتفاء الدين في الفرض",{"debt":False}),
    "present_sale":("بيع وتجارة حاضرة مدارة",{"sale":True,"present_trade":True,"circulated_between_parties":True}),
}
STATE_AR={"UNKNOWN_SCENE":"تنتظر مقدمة","ACTIVE_IN_ASSUMED_SCENE":"متحقق في الفرض",
          "THIS_BRANCH_INACTIVE":"شرط الفرع غير متحقق","TEXT_SUPPORT_WITHDRAWN":"سُحب شاهد النص"}


def render(result,request_sha,*,live):
    esc=lambda s:escape(str(s),quote=True)
    counts=result["counts"]
    title="آية الدَّين · قراءة النِّسب وشواهدها"
    cuts=result["withdraw"]
    body=[f'<header><small>هوكم / تعقّل / NABT · البقرة ٢٨٢</small><h1>{title}</h1></header>',
          f'<p>{counts["positions"]} موضعًا · {counts["active"]} قراءة فعّالة من {counts["clauses"]} · إيصال تحققت منه البوابة</p>',
          '<p class="verse">'+esc(result["source"]["text"])+'</p>']
    if live:
        options=''.join(f'<option value="{w["position"]}">{w["position"]} · {esc(w["surface"])}</option>' for w in result["tokens"])
        body.append('<form method="get"><label>شاهد السحب <select name="w"><option value="">كل الشواهد حاضرة</option>'+
                    options+'</select></label> <button>أعد الحساب</button> <a href="/">استعد الأصل</a></form>')
    else:
        body.append('<p>هذه نسخة قابلة للتصفح من إيصال واحد. لتجربة سحب شاهد وإعادة الحساب شغّل القارئ المحلي المرفق.</p>')
    if cuts:
        body.append('<p>المواضع المسحوبة في هذه التجربة '+esc('، '.join(map(str,cuts)))+'</p>')
    cog=result["cognition"]
    if live:
        ctx_options="".join(f'<option value="{esc(k)}">{esc(v["value"])}</option>' for k,v in cog["context"].items())
        body.append('<form method="get"><label>افحص اعتماد الفهم على مقدمة <select name="ctx"><option value="">كل المقدمات</option>'+
                    ctx_options+'</select></label> <label>سؤال للشبكة <input name="q" maxlength="100"></label> <button>افحص</button></form>')
    body.append('<h2>سلسلة الإدراك</h2>')
    q=cog["question_ranking"]
    if q and q["ranking"]:
        body.append('<p>اقترحت الشبكة لأجل سؤالك ترتيب المسارات الآتي. يشمل العرض بقية المسارات للمراجعة.</p>')
    order={r["family"]:i for i,r in enumerate(q["ranking"])} if q else {}
    body.append('<section class="cards">')
    for c in sorted(cog["claims"],key=lambda c:order.get(c["family"],99)):
        why="، ".join(esc(w["surface"]) for w in c["text_witnesses"])
        parents="، ".join(esc(k) for k in c["prerequisites"] if not k.startswith("sign/"))
        body.append('<article><h3>'+esc(c["name"])+'</h3><small>'+esc(c["scope"])+'</small><p>'+
                    esc(c["answer_ar"] or "توقفت هذه القراءة عند سحب مقدمتها.")+'</p>')
        if why:
            body.append('<small>شاهد النص · '+why+'</small>')
        if parents:
            body.append('<p><small>المقدمات · <bdi>'+parents+'</bdi></small></p>')
        body.append('</article>')
    body.append('</section><h2>المنطوق والمسكوت عنه</h2><p>'+esc(cog["policy"]["name"])+' · '+esc(cog["policy"]["alternative_convention"])+'</p>')
    for r in sorted(cog["inquiries"],key=lambda c:order.get(c["family"],99)):
        body.append('<details><summary>'+esc(r["name"])+' · مؤجّل</summary><p>'+esc(r["candidate_question"])+
                    '</p><p>'+esc(r["possible_reading"])+'</p><p class="debt">الشاهد المطلوب · '+esc(r["required_bridge"])+'</p></details>')
    body.append('<h2>تطبيق القراءة على مشهد مفترض</h2>')
    if live:
        options="".join(f'<option value="{esc(k)}">{esc(v[0])}</option>' for k,v in SCENARIOS.items())
        body.append('<form method="get"><label>مشهد الاختبار <select name="scene">'+options+'</select></label> <button>احسب</button></form>')
    body.append('<ul>'+''.join('<li>'+esc(a['name'])+' · '+esc(STATE_AR[a['state']])+'</li>'
                              for a in result["scene_result"]["applications"])+'</ul>')
    body.append('<h2>العلاقات في سياق الآية</h2><section class="cards">')
    for c in result["cards"]:
        a,b=c["scope"]["positions"]
        body.append(f'<article><h3>{esc(c["force"])} · {a}–{b}</h3><p>{esc(c["answer_ar"] or "توقفت قراءة هذا المقطع في هذه التجربة.")}</p>')
        roles='، '.join('«'+esc(role["surface"])+'»' for role in c["roles"].values())
        body.append('<small>العبارات المرتبطة '+roles+'</small>')
        if c["debt"]:
            body.append('<p class="debt">'+esc(c["debt"])+'</p>')
        if c["predicted_loss"] is not None:
            body.append(f'<p><small>تقدير الشبكة لسقوط القراءة <bdi>{c["predicted_loss"]:.3f}</bdi></small></p>')
        body.append('</article>')
    body.append('</section><h2>التوجيه بعد التجزئة</h2><p>افتح الكلمة لترى الحامل الذي مرّ إلى مسار الجذر، ونتيجة هوكم، والقراءة الموضعية عند توافرها.</p>')
    for w in result["tokens"]:
        i=w["position"]; rev=w["review"]
        body.append(f'<details><summary>{i} · {esc(w["surface"])}</summary><p>مدى UTF-8 <bdi>{esc(w["utf8_span"])}</bdi> · مضيف التجزئة «{esc(w["source_segment"]["host_surface"] or "لا مضيف")}» · مسار الجذر <bdi>{esc(w["root_route"])}</bdi></p>')
        body.append(f'<p>صنف هوكم <bdi>{esc(w["upstream_class"] or "DEFERRED")}</bdi> · حالة جذره <bdi>{esc(w["upstream_root_state"])}</bdi></p>')
        if rev:
            body.append(f'<p>القراءة الموضعية <bdi>{esc(rev["class"])} / {esc(rev["tag"])}</bdi> · <a href="{esc(rev["source"])}">شاهد المدوّنة</a></p>')
        body.append('<p>خانات مؤجّلة <bdi>'+esc(', '.join(w['deferred_claims']) or '—')+'</bdi></p>')
        if live:
            body.append(f'<a href="/?w={i}">اسحب شاهد هذا الموضع</a>')
        body.append('</details>')
    body.append('<footer><small>مدخلات هوكم مسجّلة من تشغيل مثبت. تُحسب الرسوم والتفسيرات عند الطلب في NABT. القوالب مراجعة لهذه الآية. دور الشبكة ترتيب شواهد النص وتقدير أثر السحب. بصمة الطلب <bdi><code>'+esc(request_sha)+'</code></bdi></small></footer>')
    return '<!doctype html><html lang="ar" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+title+'</title><style>'+STYLE+'</style><main>'+''.join(body)+'</main></html>'


def application(env,start):
    status="200 OK"
    try:
        if env.get("REQUEST_METHOD")!="GET" or env.get("PATH_INFO")!="/":
            raise ValueError("مسار غير مدعوم")
        query=parse_qs(env.get("QUERY_STRING",""),max_num_fields=4)
        if set(query)-{"w","ctx","q","scene"} or any(len(v)!=1 for v in query.values()):
            raise ValueError("معامل غير متاح")
        cuts=[int(v) for v in query.get("w",[])]
        if any(not 1<=i<=129 for i in cuts):
            raise ValueError("اختر موضعًا من ١ إلى ١٢٩")
        scene_key=query.get("scene",["unspecified"])[0]
        if scene_key not in SCENARIOS:
            raise ValueError("مشهد غير متاح")
        data,ident=checked(cuts,query.get("ctx",[]),query.get("q",[None])[0],SCENARIOS[scene_key][1])
        page=render(data,ident,live=True)
    except (ValueError,TypeError) as exc:
        status="400 Bad Request"
        page=escape(str(exc))
    out=page.encode()
    start(status,[("Content-Type","text/html; charset=utf-8"),("Content-Length",str(len(out))),("Cache-Control","no-store")])
    return [out]


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export",type=Path,help="Write a browsable single-receipt HTML snapshot")
    parser.add_argument("--port",type=int,default=8282)
    args=parser.parse_args()
    if args.export:
        r,h=checked()
        args.export.write_text(render(r,h,live=False),encoding="utf-8")
    else:
        with make_server("127.0.0.1",args.port,application) as server:
            print(f"http://127.0.0.1:{server.server_port}/",flush=True)
            server.serve_forever()
