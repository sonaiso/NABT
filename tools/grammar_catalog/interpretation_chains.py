"""Source-relative timelines and a typed method index. No external occurrence is asserted."""
from collections import defaultdict
from hashlib import sha256
import re

from tools import epistemic_measurement as epistemic
from tools.lexical_training.reasoning_curriculum import FOUNDATION, MATRICES
from . import scoped_composition, temporal

LAW = "nabt.interpretation-chains.v1"
NAME = r"[ء-ي][ء-يـ َ-ْ]{0,39}"
DAY = r"[0-9٠-٩]{1,6}"
HEADER = re.compile(rf"سلسلة «(?P<entity>{NAME})» من نوع «(?P<kind>{NAME})» في «(?P<place>{NAME})»\.")
OBS = rf"رصد «(?P<observer>{NAME})» اليوم"
SAY = rf"أخبر «(?P<speaker>{NAME})» «(?P<recipient>{NAME})» عن اليوم"
HEAR = rf"تلقى «(?P<listener>{NAME})» من «(?P<sender>{NAME})» عن اليوم"
ROW = re.compile(rf"(?:{OBS}|{SAY}|{HEAR}) (?P<day>{DAY}): (?P<axis>[ء-ي ]+) = (?P<value>[^.\n]{{1,36}})\.")
METHOD = re.compile(r"ما منهج «([^«»\n]{1,50})»[؟?]?")
COUNT = re.compile(rf"({DAY}) \[(فرد|جزء|قطعة)\]")
MAX_RECORDS = 12
SLOTS = {
    "الطور": ({"مادة"}, {"صلب","سائل","غاز"}),
    "الحركة": ({"جسم","كائن حي","إنسان","مادة"}, {"ساكن","متحرك"}),
    "الاتصال": ({"زوج","جماعة","جسم"}, {"متحد","منفصل"}),
    "الصحة": ({"إنسان","كائن حي"}, {"مريض","صحيح"}),
    "الألم": ({"إنسان","كائن حي"}, {"متألم","غير متألم"}),
    "الحياة": ({"إنسان","كائن حي"}, {"حي","ميت"}),
    "النشاط": ({"إنسان"}, {"ينطق","يفكر","يتواصل"}),
    "العدد": ({"جماعة","زوج","مجموعة","جسم"}, set()),
}
LIMITS = {"type_membership":"AS_DESCRIBED_IN_HEADER","identity_scope":"ONE_SOURCE_HEADER",
          "comparison_scope":"RECORDED_ENDPOINTS","unobserved_interval_established":False,
          "external_event_established":False,"cause_established":False,"speaker_intent_established":False,
          "source_independence_established":False,"all_arabic_complete":False}

# The parent links below organize QUESTIONS. They do not license subclass
# inheritance, causality, metaphysical commitments, or linguistic rulings.
FAMILIES = {
    "scope": (None,"الوجود والموجودات","تعيين موضوع البحث ومجاله ونمط وجود مرجعه وشاهد الدعوى."),
    "domain": ("scope","الكون والإنسان والحياة","تعيين مجال الوصف؛ يكون الإنسان حيًا وقد يحمله أكثر من تصنيف."),
    "ontology": ("domain","الهوية والوراثة","تعيين معنى الأصل والفرع ونوع الوراثة وشاهد الحافة."),
    "state": ("domain","الحالات والتغير","تعيين الحامل والمحور والمكان وزمني المقارنة في السجل نفسه."),
    "agency": ("domain","الفعل والقابلية","تحديد الحامل والفعل والتأهيل والشروط والموانع وشاهد الوقوع."),
    "epistemic": ("scope","الخبر والمعرفة","تعيين القائل والمخاطب والقضية والرصد والمجال."),
    "inference": ("scope","الحكم والاستدلال","تعيين المقدمات ونسخة القاعدة ونطاقها ووجه الدلالة وموانعها."),
}
# id, parent, names, existing registry coordinate, actual treatment in THIS slice, evidence obligation
OPERATIONS = (
    ("domain","domain","الكون|الإنسان|الحياة|الموجودات|الوجود","existence","METHOD","تحديد المرجع ونمط وجوده. نسبة الفرد إلى مجال لا تثبت جميع خواصه."),
    ("beyond","domain","ما قبلها وما بعدها|ما قبل الكون|ما بعد الحياة","temporal_relation","METHOD","يميَّز السؤال الزمني عن التفسيري أو الغيبي، وتعيّن جهة الدليل لكل دعوى."),
    ("identity","ontology","الأجناس|الخواص|الصفات|العلاقات|الأفراد","kind_nature","EXISTING_DEFINITION_OWNER","مرجع مستقل لكل معنى، وشاهد لكل علاقة بين الأصل والفرع."),
    ("ancestry","ontology","الأصل","origin","EXISTING_OWNERS","عيّن هل الأصل جنس موروث أم أصل قياس أم أصل معجمي؛ لكل انتقال قاعدته."),
    ("branch","ontology","الفرع","branch","EXISTING_OWNERS","تعيين وجه انتماء هذا الفرع أو علة نقل الحكم إليه، مع موانعه ومنافساته."),
    ("time","state","قبل|بعد|التعاقب|التوقف|ينتقل|يتوقف|الحركة","temporal_relation","ENDPOINTS","الزمان والمكان والحامل ومرجع الحركة. الموضع النسبي وتفاصيل المسار تحتاج أدلة إضافية."),
    ("phase","state","الأطوار|صلب|سائل|غازي|التحول","change","ENDPOINTS","هوية العينة والطور الموصوف لكل وقت. تفسير آلية التحول يحتاج قانونًا وشروط انطباق."),
    ("quantity","state","العدد|الوحدة والكثرة|واحد|كثير|يزيد|ينقص","change","ENDPOINTS","جماعة أو حامل واحد ووحدة واحدة وقراءتان مرتبتان. للعدد صفر وواحد وما فوق الواحد."),
    ("assembly","state","يتحد|ينفصل|لا يتحد|الاتحاد والانفصال","change","ENDPOINTS","تعيين الزوج أو الجماعة. وصف الانفصال لا يثبت امتناع الاتحاد أو سببه."),
    ("vital","state","يتألم|يتعافى|يصح|يمرض|يموت|الألم|الصحة","change","ENDPOINTS","هوية الكائن وشاهد الحالة في وقتها. الانتقال بين وصفين لا يشخّص سببًا."),
    ("reproduction","agency","يتكاثر|التكاثر","causal_relation","METHOD","شاهد حدوث التكاثر وعلاقة الأصل بالنسل؛ الزيادة العددية تحتمل دخول أفراد من الخارج."),
    ("capability","agency","القابليات|القابلية","property","EXISTING_CONDITIONAL_OWNER","تعيين الفعل وحامله وما يتوقف عليه إمكانه، ثم فحص انطباق القابلية على الفرد."),
    ("condition","agency","الشرط","condition","EXISTING_CONDITIONAL_OWNER","تعيين ما يتوقف عليه الحكم. تحقق الشرط وحده لا يكفي لإثبات حصول المشروط."),
    ("blocker","agency","المانع","blocker","EXISTING_CONDITIONAL_OWNER","تعيين الحكم الذي يمنعه وشاهد قيامه. غياب الشاهد عليه لا يثبت انتفاءه."),
    ("cause","agency","السبب|المسبب|العلة","cause","METHOD","حدّد جهة السببية، وقانونها ومقدماتها وشاهد انطباقها على الواقعة. التعاقب وحده يرخص الترتيب."),
    ("cognition","epistemic","يتواصل|ينطق|يعقل|يفكر","cognitive_concept","METHOD","عيّن رسالةً أو أداءً منسوبًا إلى حامل؛ الصفة الذهنية العامة وصدق الاعتقاد يحتاجان دليلًا آخر."),
    ("testimony","epistemic","يخبر|يتلقى الخبر|يصيب|يخطئ|الموافق|المخالف","discrimination","REPORT_COMPARISON","يُفحص صدور الخبر وتلقّيه وتأييده أو معارضته في السجل. خطأ قضية لا يثبت تعمّد الكذب."),
    ("scope_general","inference","العام","generality","EXISTING_SCOPED_OWNER","عيّن مجال الكم وشاهد التخصيص والاستثناء. فرد واحد لا يسوّغ حكمًا على المجال كله."),
    ("particular","inference","الخاص","specificity","EXISTING_SCOPED_OWNER","تعيين ما خصّص المجال وأي الأفراد تبقى داخله."),
    ("absolute","inference","المطلق","unrestricted","EXISTING_SCOPED_OWNER","تعيين جهة الإطلاق في النص وتوثيق سبب الحمل عند اتصال خطاب آخر."),
    ("scope_limit","inference","المقيد","restricted","EXISTING_SCOPED_OWNER","عيّن الوصف المقيّد ونطاقه وعلاقة الخطابين التي تجيز حمل أحدهما على الآخر."),
    ("validity","inference","الباطل|الفاسد|الصحيح","reason_primitives","METHOD","عيّن اصطلاح الحاكم والمجال وشروط الصحة والأثر المترتب. تعارض الرصد لا يحكم بالفساد الاصطلاحي."),
    ("congruence","inference","مفهوم الموافقة|مفهوم المخالفة","mafhum","METHOD","عيّن وجه الاتفاق أو المخالفة وشاهد النقل والشرط والمانع في استعمال النص المعين."),
    ("sign","inference","الإشارة|دلالة الإشارة","mafhum","METHOD","ميّز إحالة اسم الإشارة عن دلالة الإشارة؛ عيّن المعنى التابع ووجه لزومه للنص."),
    ("hint","inference","الإيماء|الإيماء والتنبيه","mafhum","METHOD","عيّن الوصف والحكم وقرينة ربطهما في المقام. تتابع اللفظين وحده لا يثبت العلة."),
    ("presupposition","inference","الاقتضاء|دلالة الاقتضاء","mafhum","METHOD","عيّن ما يتوقف عليه استقامة الكلام في هذا الوجه وقرينة تقديره والبدائل الممكنة."),
)


# A topic can have a state-reading component and a stronger interpretation
# with different evidence. Expose the narrower boundary for the actual term.
TERM_OBLIGATIONS = {
    "يموت": ("ENDPOINTS","يوثَّق الوصف في زمنين؛ يبقى وقت الموت الدقيق وسببه محتاجين إلى دليل."),
    "يتعافى": ("ENDPOINTS","الوصول إلى وصف صحيح بعد مريض فرق بين طرفين؛ آلية التعافي وتشخيصه يحتاجان شاهدين مستقلين."),
    "يتحد": ("ENDPOINTS","التحقق هنا من وصف حالة الزوج عند زمنين؛ يحتاج نوع الاتحاد وآليته إلى شاهد."),
    "لا يتحد": ("METHOD","عيّن هل النفي يخص واقعة في زمن أم امتناعًا تحت شروط عامة؛ بقاء الطرفين منفصلين لا يثبت الامتناع."),
    "ينتقل": ("ENDPOINTS","تجوز مقارنة وصف الحركة والسكون. تعيين مسار مكاني يحتاج الموضعين والإطار المرجعي."),
    "ينطق": ("REPORTED_ACTIVITY","تعيين زمن وصف النطق وهوية حامله. لا يستفاد من الصوت وحده صدق الخبر."),
    "يتواصل": ("REPORTED_ACTIVITY","يمكن تسجيل وصف التواصل. إثبات تبليغ محتوى معيّن وتلقّيه يحتاج شاهدًا لكل جهة."),
    "يفكر": ("REPORTED_ACTIVITY","يحفظ النص نسبة النشاط إلى صاحبه. تحقق العملية الذهنية في الخارج يحتاج شاهدا مستقلا."),
    "يعقل": ("METHOD","تمييز الأهلية العامة من أداء مهمة بعينها، مع تعريف المهمة وقرينة تحققها."),
}


def method(term):
    for key,(parent,title,obligation) in FAMILIES.items():
        if term==title:
            path=[title]
            while parent is not None:
                parent,label,_=FAMILIES[parent]
                path.append(label)
            return {"id":key,"question_path":list(reversed(path)),
                    "registry":[],"treatment":"METHOD","evidence_required":obligation,"application_established":False}
    for key,parent,words,coord,status,obligation in OPERATIONS:
        if term not in words.split("|"):
            continue
        status,obligation=TERM_OBLIGATIONS.get(term,(status,obligation))
        root=[]
        while parent is not None:
            parent,title,_=FAMILIES[parent]
            root.append(title)
        coordinates=[{"collection":name,"id":r[0],"label":r[1]} for name,rs in
                     (("foundation",FOUNDATION),("matrices",MATRICES)) for r in rs if r[0]==coord]
        return {"id":key,"question_path":list(reversed(root)),"registry":coordinates,"treatment":status,
                "evidence_required":obligation,"application_established":False}
    return None


def witness(text,start,stop):
    return {"text":text[start:stop],"utf8_span":[len(text[:start].encode()),len(text[:stop].encode())]}


def identifier(s):
    return sha256(s.encode()).hexdigest()


def parse(text):
    lines=text.split("\n")
    head=HEADER.fullmatch(lines[0])
    if not head or len(lines)==1:return "OUTSIDE_GRAMMAR",None,[]
    if len(lines)-1>MAX_RECORDS:return "RESOURCE_LIMIT",None,[]
    entity=head.groupdict()
    entity["witness"]=witness(text,0,len(lines[0]))
    for k in ("entity","kind","place"):
        if not entity[k].strip() or entity[k]!=entity[k].strip():return "INVALID_IDENTITY",None,[]
    records=[]
    pos=len(lines[0])+1
    for line in lines[1:]:
        m=ROW.fullmatch(line)
        if not m:return "OUTSIDE_GRAMMAR",None,[]
        axis,value=m["axis"],m["value"]
        if axis not in SLOTS or entity["kind"] not in SLOTS[axis][0]:return "OUTSIDE_PROFILE",None,[]
        unit="حالة"
        if axis=="العدد":
            number=COUNT.fullmatch(value)
            if not number:return "OUTSIDE_PROFILE",None,[]
            value,unit=int(number[1]),number[2]
        elif value not in SLOTS[axis][1]:return "OUTSIDE_PROFILE",None,[]
        who=m["observer"] or m["speaker"] or m["sender"]
        to=m["recipient"] or m["listener"]
        if any(x!=x.strip() or not x for x in [who]+([to] if to is not None else [])):
            return "INVALID_IDENTITY",None,[]
        # Same witness keeps its identity if another line is withdrawn or reordered.
        # Ordinals distinguish repeated identical clauses within this header.
        ordinal=1+sum(r["witness"]["text"]==line for r in records)
        rid="r_"+identifier(lines[0]+"\n"+line)[:32]+"_"+str(ordinal)
        record={"id":rid,"kind":"observation" if m["observer"] else "report" if m["speaker"] else "reception",
                "origin":who,"recipient":to,"day":int(m["day"]),"axis":axis,"unit":unit,"value":value,
                "witness":witness(text,pos,pos+len(line)),
                "fields":{k:witness(text,pos+m.start(k),pos+m.end(k)) for k,v in m.groupdict().items() if v is not None}}
        records.append(record)
        pos+=len(line)+1
    return "PARSED",entity,records


def dimension_gaps(records):
    # Preserve both observations even when their units cannot be compared.
    units=defaultdict(set)
    for r in records:
        if r["kind"]=="observation":units[r["axis"]].add(r["unit"])
    return [{"axis":axis,"reason":"DIFFERENT_UNITS","units":sorted(group)}
            for axis,group in units.items() if len(group)>1]


def slice_key(r):
    return r["axis"],r["unit"],r["day"]


def same_message(a,b):
    return all(a[k]==b[k] for k in ("axis","unit","day","value","origin","recipient"))


def observation_groups(records):
    groups=defaultdict(lambda:defaultdict(list))
    for r in records:
        if r["kind"]=="observation":groups[r["axis"],r["unit"]][r["day"]].append(r)
    return groups


def conflicting_cells(groups):
    result=[]
    for (axis,unit),days in groups.items():
        for day,rows in sorted(days.items()):
            values=list(dict.fromkeys(r["value"] for r in rows))
            if len(values)>1:
                result.append({"axis":axis,"unit":unit,"day":day,"values":values,
                               "dependencies":[r["id"] for r in rows],"status":"CONFLICT"})
    return result


def compare_days(groups):
    pairs=[]
    for (axis,unit),days in groups.items():
        ordered=sorted(days)
        for a,b in zip(ordered,ordered[1:]):
            pairs.append((axis,unit,a,b,days[a],days[b]))
    requests=[{"op":"check","relation":"before","left":{"first":a,"last":a},"right":{"first":b,"last":b}}
              for _,_,a,b,_,_ in pairs]
    order=temporal.native(requests)
    changes=[]
    for i,(axis,unit,a,b,before,after) in enumerate(pairs):
        deps=[r["id"] for r in before+after]
        row={"axis":axis,"unit":unit,"from_day":a,"to_day":b,"dependencies":deps,"status":"VERIFICATION_UNAVAILABLE"}
        values=[[v["value"] for v in rs] for rs in (before,after)]
        row.update(from_values=values[0],to_values=values[1],
                   from_alternatives=list(dict.fromkeys(values[0])),to_alternatives=list(dict.fromkeys(values[1])))
        row["verification_failure"]="temporal"
        if order["available"] and order["calls"][i]["response"]["verdict"]=="CONFIRMED":
            row["verification_failure"]=None
            row["order_check"]=i
            if any(len(set(v))!=1 for v in values):row["status"]="CONFLICT"
            else:
                first,last=values[0][0],values[1][0]
                if axis=="العدد":
                    expr=f"{last}-{first}"
                    checked=scoped_composition.evaluate({"schema":scoped_composition.SCHEMA,"profile":"arithmetic","text":expr})
                    receipt=checked["native_check"]
                    row["arithmetic_check"]={"expression":expr,"status":checked["status"],"receipt":receipt}
                    if checked["chain_complete"] and checked["status"]=="COMPUTED" and receipt and receipt["native_checked"]:
                        delta=int(checked["projection"]["result"]["value"]["numerator"])
                        row.update(difference=delta,multiplicity=["ZERO" if n==0 else "ONE" if n==1 else "MANY" for n in (first,last)])
                        row["status"]="INCREASED" if delta>0 else "DECREASED" if delta<0 else "SAME_ENDPOINTS"
                    else:
                        row["verification_failure"]="arithmetic"
                else:row["status"]="SAME_ENDPOINTS" if first==last else "CHANGED"
        changes.append(row)
    return changes,order


def check_report(entity,records,report):
    facts=[r for r in records if r["kind"]=="observation" and slice_key(r)==slice_key(report)]
    claim={"axis":"recorded_observation","entity":entity["entity"],"predicate":report["axis"],"value":str(report["value"]),
           "unit":report["unit"],"context":entity["kind"],"time":str(report["day"]),"place":entity["place"]}
    def speaker_id(person):
        return "person_"+identifier(person)[:24]
    src=[{"identity":r["id"],"revision":identifier(r["witness"]["text"]),"content":r["witness"]["text"]} for r in facts]
    tags=[{"id":r["id"],"source":s,"key":claim,"positive":r["value"]==report["value"],"kind":"observation",
           "origin":speaker_id(r["origin"]),"ancestry":[speaker_id(r["origin"])]} for r,s in zip(facts,src,strict=True)]
    origins=sorted({speaker_id(report["origin"])}|{r["origin"] for r in tags})
    req={"query":{"key":claim,"positive":True,"origin":speaker_id(report["origin"])},
         "active_sources":src,"origins":[{"id":o,"parents":[]} for o in origins],
         "interpretations":tags,"budget":MAX_RECORDS,"certificate":None}
    owner=epistemic.execute_request(req)
    receivers=[r["id"] for r in records if r["kind"]=="reception" and same_message(r,report)]
    return {"claim":report["id"],"receipt_evidence":receivers,"observation_check":owner["status"],
            "native_checked":owner["native_checked"],"certificate_checked":owner["certificate_checked"],
            "observation_support":owner["observed"],"checker_sha256":owner["execution"]["native_sha256"],
            "error":owner["execution"]["error"],"possible_observations":[r["id"] for r in facts],
            "single_value_premise":"EXCLUSIVE_RECORDED_VALUE_PER_ENTITY_AXIS_UNIT_DAY_PLACE",
            "reception_scope":"MATCHED_REPORTED_CONTENT_NOT_UNIQUE_UTTERANCE"}


def analyze(text):
    query=METHOD.fullmatch(text)
    if query:
        entry=method(query[1])
        return {"schema":LAW,"status":"METHOD_FOUND" if entry else "UNKNOWN_METHOD","method":entry,
                "source_sha256":identifier(text),"limits":LIMITS}
    if not text.startswith("سلسلة «"):return None
    if len(text.encode())>4096:return {"schema":LAW,"status":"RESOURCE_LIMIT","limits":LIMITS}
    status,entity,rows=parse(text)
    res={"schema":LAW,"status":status,"source_sha256":identifier(text),"subject":entity,
         "records":rows,"changes":[],"reports":[],"conflicts":[],"limits":LIMITS}
    if status!="PARSED":return res
    groups=observation_groups(rows)
    res["conflicts"]=conflicting_cells(groups)
    res["comparison_gaps"]=dimension_gaps(rows)
    try:
        res["changes"],res["order_check"]=compare_days(groups)
    except (OSError,ValueError) as exc:
        res["order_error"]=type(exc).__name__
    res["reports"]=[check_report(entity,rows,r) for r in rows if r["kind"]=="report"]
    res["status"]="SOURCE_RELATIVE_CHAIN"
    if ("order_error" in res or any(v["status"]=="VERIFICATION_UNAVAILABLE" for v in res["changes"])
            or any(not v["native_checked"] for v in res["reports"])):
        res["status"]="PARTIAL_VERIFICATION"
    return res


def cards(res):
    from .text_reading import card
    if res["status"]=="METHOD_FOUND":
        m=res["method"]
        return [card("interpretation_method","شرط النظر في هذا الباب"," ← ".join(m["question_path"])+".",
                     m["evidence_required"],"تعيين المنهج لا يثبت وقوع حالة أو صحة استدلال بعينه.",method_id=m["id"])]
    if res["status"] not in ("SOURCE_RELATIVE_CHAIN","PARTIAL_VERIFICATION"):
        return [card("chain_deferred","إرجاء","تعذرت قراءة هذه السلسلة في المجال المضبوط.",res["status"],
                     "تبقى القضية غير محسومة في هذا المسار.")]
    labels={"INCREASED":"زاد العدد","DECREASED":"نقص العدد","SAME_ENDPOINTS":"اتفق الوصف عند الطرفين",
            "CHANGED":"تغيّر الوصف بين الطرفين","CONFLICT":"تعارضت الأوصاف في السجل",
            "VERIFICATION_UNAVAILABLE":"تعذّر فحص ترتيب الطرفين"}
    out=[]
    for cell in res["conflicts"]:
        values="، ".join(map(str,cell["values"]))
        out.append(card("chain_conflict","تعارض في اليوم نفسه",
                        f'وردت للمحور «{cell["axis"]}» في اليوم {cell["day"]} القيم «{values}».',
                        "تتحد هوية الحامل والمكان والوحدة واليوم في السجل.",
                        "يبقى تعيين قيمة واحدة مؤجلاً، ولا يُعدّ اختلاف الروايات تحولًا زمنيًا.",
                        dependencies=cell["dependencies"]))
    for c in res["changes"]:
        meaning=("تعذّر فحص فرق العدد" if c["verification_failure"]=="arithmetic" else labels[c["status"]])
        out.append(card("chain_change","حكم بين رصدين",f'{c["axis"]}: {meaning} بين اليومين {c["from_day"]} و{c["to_day"]}.',
                        'الشاهد السابق «'+"، ".join(map(str,c["from_values"]))+'» واللاحق «'+"، ".join(map(str,c["to_values"]))+"». ",
                        "تبقى كيفية التحول وسببه وما وقع بين الرصدين محتاجة إلى دليل.",dependencies=c["dependencies"]))
    judgements={"SUPPORTED":"وافق سجل الرصد","REFUTED":"خالف سجل الرصد","CONFLICT":"ورد له مؤيد ومعارض","UNKNOWN":"لم يتعيّن له شاهد رصد مستقل"}
    for r in res["reports"]:
        phrase=judgements.get(r["observation_check"],"تعذّر فحص الرصد")
        message=next(row for row in res["records"] if row["id"]==r["claim"])
        reception="ذُكر تلقّي هذا المضمون." if r["receipt_evidence"] else "بقي تلقّي هذا المضمون غير مثبت."
        out.append(card("chain_report","مطابقة خبر بسجل محدد",f'خبر {message["origin"]} إلى {message["recipient"]}: {phrase}.',
                        reception,"نسبة الخبر وموافقته للسجل لا تثبتان النية أو حقيقة الواقعة خارج النص.",claim_ref=r["claim"]))
    for gap in res.get("comparison_gaps",[]):
        out.append(card("chain_scope","حد المقارنة","تُركت المقارنة بين الوحدات المختلفة مفتوحة.",
                        "الوحدات المرصودة: "+"، ".join(gap["units"])+".",
                        "يلزم شاهد يربط الوحدتين قبل طرح القيم."))
    if not out:
        out.append(card("chain_record","سجل وصفي محدود","حُفظت السجلات بمواضعها.",
                        "لم تتوافر مقارنة زمنية ضمن وحدة ومحور مشتركين.","تحتاج النتيجة إلى شواهد أخرى."))
    if res["status"]=="PARTIAL_VERIFICATION":
        out.append(card("technical","تعذّر التحقق","تعذّر فحص بعض النتائج التابعة.",
                        "تُراجَع حالة فاحص الزمن أو الحساب أو الرصد في الإيصال.","حُفظت السجلات الأصلية."))
    return out
