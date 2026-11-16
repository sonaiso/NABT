"""Fine-grained discourse and inferential dependencies for the retained Q2:282 source."""
from dataclasses import dataclass
from hashlib import sha256

from tools.lexical_training import ayat_questions
from tools.mantuq_inference.evaluator import SLOTS, ROLES, guard_verdict
from .operations import ROOT

POLICY_SOURCE = "evidence/mantuq_mafhum/sources/shakhsiyya3.txt"
POLICY_SHA = "42e8a6a98a73d513bfdb0f984a63846499d380216a1870eb95ce6225e2ca1703"
CONTEXT = {
    "quran_attribution":("إسناد الخطاب القرآني إلى الله في مقام قراءة القرآن","إحالة المصحف، البقرة ٢٨٢"),
    "species_instinct":("يربط النموذج غريزة النوع بكيفية التكاثر","تصنيف صاحب النموذج لجنس الإنسان"),
    "religious_instinct":("يربط النموذج غريزة التدين بالتقديس وإدراك الحاجة","تصنيف صاحب النموذج لجنس الإنسان"),
    "cognitive_faculty":("لجنس الإنسان في النموذج ملكة إدراك الكون والإنسان والحياة","ملكة إدراكية مستقلة في تصنيف صاحب النموذج"),
    "language_bridge":("اللغة جسر اشتراك البشر في التعبير عن المفاهيم وفهمها","مقدمة صاحب النموذج في التواصل"),
    "human_disposition":("للإنسان غريزة البقاء","مقدمة تصورية صرّح بها صاحب السؤال"),
    "ownership_manifestation":("التملّك من مظاهر غريزة البقاء","مقدمة تفسيرية صرّح بها صاحب السؤال"),
    "human_audience":("المخاطبون في نموذج هذه الواقعة بشر","تعيين الجنس في نموذج المخاطَب الذي اقترحه صاحب السؤال"),
}


@dataclass(frozen=True)
class Claim:
    key: str
    family: str
    title: str
    scope: str
    value: str
    words: tuple = ()
    needs: tuple = ()
    role: str = "content"


CLAIMS = (
    Claim("speaker","maqam","المتكلّم","مقام قرآني","المتكلّم هو الله بحسب نسبة الآية إلى مصدرها القرآني.",needs=("ctx/quran_attribution",)),
    Claim("believers","maqam","المخاطَب وصفته","منطوق","المخاطَب في النداء مَن وُصفوا بالإيمان.",(1,2,3,4),role="force"),
    Claim("address","maqam","هوية خطاب النداء","مقام ومنطوق","المتكلم في المقام القرآني يخاطب الذين آمنوا.",needs=("speaker","believers")),
    Claim("human","ontology","جنس المخاطَب","نموذج مفهومي","يحمل المخاطَب وصف الإنسانية في النموذج المعطى.",needs=("believers","ctx/human_audience")),
    Claim("survival","ontology","غريزة البقاء","مقدمة المستخدم","تُسند غريزة البقاء إلى الإنسان ضمن النظرية المفترضة.",needs=("human","ctx/human_disposition")),
    Claim("ownership","ontology","خاصية التملّك","مشروط بنظرية المستخدم","يُفسَّر التملّك في النموذج بأنه مظهر لغريزة البقاء. يظل التعيين الخارجي لكل فرد مفتوحًا.",needs=("survival","ctx/ownership_manifestation")),
    Claim("capacity","ontology","قابلية التعامل بالدَّين","تصوّر المشهد الشرطي","يُتصوَّر المخاطبون أطرافًا محتملة للتداين. إثبات الملك أو الأهلية أو وقوع الدين لشخص معين يحتاج شاهدًا مستقلًا.",(5,6,7),("believers",)),
    Claim("reproduction","ontology","غريزة النوع ومظهرها","جنس الإنسان في النموذج","ينسب النموذج كيفية التكاثر إلى غريزة النوع على مستوى الجنس.",needs=("ctx/species_instinct",)),
    Claim("sanctification","ontology","غريزة التدين ومظهرها","جنس الإنسان في النموذج","يربط النموذج التقديس بإدراك الحاجة على مستوى الجنس.",needs=("ctx/religious_instinct",)),
    Claim("understanding","ontology","الإنسان فاهم ومفهوم","جنس الإنسان في النموذج","يحمل الإنسان ملكة الإدراك، ويمكن أن يقع الإنسان نفسه موضوعًا للإدراك.",needs=("ctx/cognitive_faculty",)),
    Claim("sharing","ontology","جسر الاشتراك في الفهم","نموذج التواصل","يتشارك فاهمان مفهومًا بالتعبير اللغوي عنه وفهم النسبة المسندة في مقامها.",needs=("understanding","ctx/language_bridge")),
    Claim("if_debt","condition","الشرط المنطوق","منطوق","إذا تداين المخاطبون بدينٍ؛ وقوعه معلّق في الخطاب.",(5,6,7)),
    Claim("term","endpoint","قيد الدين الزمني","منطوق","الدَّين في هذا الموضع مقيّد بأجلٍ مسمّى.",(7,8,9,10)),
    Claim("write","force","الأمر بالكتابة","إنشاء طلبي","«فاكتبوه» طلب كتابة الدين المذكور؛ واو الجماعة للمخاطبين والهاء تعود إلى الدين.",(7,11),role="force"),
    Claim("if_then","condition","تعليق الطلب بالشرط","نسبة شرطية","في حال التداين إلى أجل مسمى توجّه إلى المخاطبين طلب توثيق الدَّين كتابة.",needs=("believers","if_debt","term","write")),
    Claim("scribe","force","الكاتب وقيد العدل","إنشاء طلبي","كاتبٌ يكتب بين المتداينين بالعدل؛ ورد «كاتبٌ» مفردًا في بيان الدور، ولم يرد حصر عدد الكتّاب في واحد.",(12,13,14,15),role="force"),
    Claim("dictator","force","صاحب الإملال","إنشاء طلبي","الذي عليه الحق يملي. تميّزه صلته بالحق عن الكاتب المكلف بالكتابة.",(25,26,27,28),role="force"),
    Claim("guardian","condition","بديل الإملال","منطوق","عند أحد الأوصاف المذكورة يسند جواب الشرط الإملال إلى وليّه بالعدل.",tuple(range(36,53))),
    Claim("two","number","عدد المطلوب ابتداءً","منطوق عددي","طلب استشهاد شهيدين من رجال المخاطبين.",(53,54,55,56)),
    Claim("alternative","number","عدد البديل وقيده","منطوق شرطي عددي","إذا لم يكونا رجلين ذُكر رجل وامرأتان ممن ترضون من الشهداء.",tuple(range(57,67))),
    Claim("witness_duty","force","حال الشاهد عند الدعوة","إنشاء نهي","النهي عن إباء الشهداء عند دعوتهم.",tuple(range(73,79)),role="force"),
    Claim("rationale","force","خبر عن وجوه التوثيق","خبر في سياق الطلب","يصف النص ذلك بأنه أقسط عند الله وأقوم للشهادة وأدنى ألّا ترتابوا.",tuple(range(88,97)),role="force"),
    Claim("exception","condition","التجارة الحاضرة","استثناء مصرح به","ورد رفع الجناح عن ترك كتابة التجارة الحاضرة المدارة بين الأطراف.",tuple(range(97,109))),
    Claim("sale","force","الإشهاد في البيع","إنشاء طلبي","أمر الإشهاد عند التبايع له شاهد مستقل عن جملة الاستثناء في الكتابة.",(109,110,111),role="force"),
    Claim("harm","force","الكاتب والشهيد","إنشاء نهي","يتعلق النهي عن المضارّة بالكاتب والشهيد. تبقى جهة الضرر ضمن أوجه القراءة.",tuple(range(112,117)),role="force"),
    Claim("closing_command","force","الأمر بالتقوى","إنشاء طلبي","«واتقوا الله» طلب موجّه إلى المخاطبين.",(122,123),role="force"),
    Claim("closing_report","force","الإخبار بالتعليم والعلم","خبر","ورد الخبر بتعليم الله للمخاطبين وبعلمه بكل شيء. تعيين رابطة سببية من الواو وحدها مؤجّل.",tuple(range(124,130)),role="force"),
)


@dataclass(frozen=True)
class Inquiry:
    key: str
    family: str
    policy: str
    title: str
    base: str
    silent: str
    bridge: str
    alternative: str


INQUIRIES = (
    Inquiry("iqtida","requirement","requirement","الاقتضاء","write","هل يفتقر الطلب إلى تقدير لفظ محذوف؟","إثبات توقف صحة الكلام أو صدقه على مقدَّر محدد.","مرجع هاء «فاكتبوه» له شاهد في «بدين»؛ حلّ الإحالة وحده لا يستدعي إضمار حكم."),
    Inquiry("ima","alert","alert","التنبيه والإيماء","guardian","هل يصلح العجز عن الإملال علةً متعدّية في واقعة أخرى؟","إثبات أن اقتران الوصف بالطلب للتعليل وتحرير نطاق الوصف.","المقروء مباشرة ترتيب إملال الولي على الشرط. يمكن فهم البديل في محله قبل تعيين علة للنقل."),
    Inquiry("attribute_contrast","opposition","opposition","مفهوم الصفة","believers","هل يخرج غير المؤمن من كل حكم للتوثيق؟","إثبات احتراز الوصف في الحكم المقصود وانتفاء الموانع.","تعيين المخاطَب في النداء ينسجم مع بقاء حكم غيره محتاجًا إلى دليل آخر."),
    Inquiry("condition_contrast","condition","opposition","مفهوم الشرط","if_then","هل ينتفي طلب الكتابة في كل معاملة لا تستوفي هذا الشرط؟","إثبات كون الشرط لازمًا لهذا الحكم في محل المقابلة وفحص الاستثناء والمعارض.","يمكن أن تسكت هذه الجملة عن معاملة أخرى تتعلق بها قاعدة أخرى."),
    Inquiry("endpoint_contrast","endpoint","opposition","مفهوم الغاية","term","هل يسقط حق الدائن أو حجية الكتاب عند حلول الأجل؟","تعيين الحكم المغيّا وثبوت أن الغاية حدٌّ له.","حلول موعد الدين ينسجم مع بقاء حق أو وثيقة. المذكور هنا أجل الدَّين."),
    Inquiry("number_contrast","number","opposition","مفهوم العدد","two","هل ينفي العدد كل صورة أخرى من صور الإثبات؟","تعيين محل الحصر وفحص البديل الصريح والموانع وسائر الأدلة.","ورد البديل بشرط مستقل. ذكر العدد في الطلب وحده لا يفصل سائر أبواب الإثبات."),
    Inquiry("concordance","agreement","agreement","مفهوم الموافقة / فحوى الخطاب","harm","هل تلحق صورة مسكوت عنها من الإضرار بالكاتب أو الشهيد بهذا النهي؟","تعيين صورة خارجة عن عموم اللفظ، ووجه الموافقة المستفاد من التركيب في الحكم.","إذا دخلت الصورة المراد اختبارها في لفظ المضارّة نفسه فهي من تطبيق عموم المنطوق."),
    Inquiry("opposition","opposition","opposition","مفهوم المخالفة / لحن الخطاب","if_then","ما حكم حال مسكوت عنها ينتفي فيها القيد المذكور؟","تسمية المسكوت عنه والحكم المقابل، وإثبات لزوم القيد وانتفاء الموانع.","توقف تطبيق هذا المسار الشرطي في حالة جديدة يترك إمكان حكم مستقل فيها مفتوحًا."),
)


def policy_record():
    raw=(ROOT/POLICY_SOURCE).read_bytes()
    if sha256(raw).hexdigest()!=POLICY_SHA:
        raise ValueError("Changed retained methodological source")
    return {"name":"الشخصية الإسلامية، الجزء الثالث، بحسب النص المودع في NABT","source":POLICY_SOURCE,
            "sha256":POLICY_SHA,"lines":[2,3,4,5,6,9,10,11],"agreement_alias":"فحوى الخطاب",
            "opposition_alias":"لحن الخطاب","alternative_convention":
            "في اصطلاح آخر تُسمّى الموافقة المساوية لحن الخطاب، والأولوية فحوى الخطاب. يحفظ التطبيق اسم المنهج عند العرض."}


def build(g, words, source_sha):
    """Populate the existing DAG before the neural or symbolic withdrawal calculation."""
    g.owners["cognitive_context"]={}
    g.owners["cognitive_claims"]={}
    for key,(value,provenance) in CONTEXT.items():
        owner={"value":value,"provenance":provenance,"type":"SOURCE_ATTRIBUTION" if key=="quran_attribution" else "USER_MODEL_PREMISE"}
        if key=="quran_attribution":
            owner.update(source_id=g.report["source_id"],source_sha256=source_sha)
        g.owners["cognitive_context"][key]=owner
        g.node("ctx/"+key,"sense",value,["cognitive_context",key],[],"concept",scope=owner["type"])
    lines=[]
    for c in CLAIMS:
        idx=list(c.words)
        tokens=[{"position":i,"surface":words[i-1]["surface"],"utf8_span":words[i-1]["utf8_span"]} for i in idx]
        parents=[p if p.startswith("ctx/") else "cog/"+p for p in c.needs]+["sign/"+str(i-1) for i in idx]
        key="cog/"+c.key
        record={"id":key,"family":c.family,"name":c.title,"scope":c.scope,"proposition":c.value,
                "prerequisites":parents,"text_witnesses":tokens,"source_sha256":source_sha}
        g.owners["cognitive_claims"][c.key]=record
        pos=[tokens[0]["utf8_span"][0],tokens[-1]["utf8_span"][1]] if tokens else None
        g.node(key,c.role,c.value,["cognitive_claims",c.key],parents,"joint" if idx else "concept",pos,scope=c.scope)
        lines.append(record)
    return lines


def audit_inquiry(case,live):
    # Exercise the installed qualified inference guard with only the actually held evidence.
    policy=case.policy
    kind="opposition" if policy=="opposition" else "direct"
    needed=[]
    known=[]
    for i,slot in enumerate(SLOTS[policy]):
        role=ROLES[slot]
        atom={"value":i,"positive":role!="blocker_absence","scope":"ayat:2:282/"+case.key}
        needed.append({"slot":slot,"role":role,"atom":atom})
        if slot=="premise" and "cog/"+case.base in live:
            known.append(atom)
    verdict=guard_verdict(kind,needed,known)
    return {"id":case.key,"family":case.family,"name":case.title,"basis":"cog/"+case.base,"candidate_question":case.silent,
            "base_present":"cog/"+case.base in live,"possible_reading":case.alternative,"required_bridge":case.bridge,
            "policy":policy,"guard":verdict,"missing_slots":[r["slot"] for r in needed if r["atom"] not in known],
            "ruling":None,"status":"DEFERRED"}


def decode(lines,g,live,neural,question):
    removed=[]
    present=[]
    for c in lines:
        n=neural.get(c["id"],{})
        active=c["id"] in live
        target=g.nodes[c["id"]]
        span=target["transition"]["position"].get("utf8_span")
        view={**c,"grade":target["grade"],"utf8_span":span,"state":"SUPPORTED_IN_SCOPE" if active else "WITHDRAWN","answer_ar":c["proposition"] if active else None,
              "lost_parents":[p for p in c["prerequisites"] if p not in live],
              "loss_score":n.get("loss_score"),"vector":n.get("vector")}
        if not active:
            removed.append(view)
        else:
            present.append(view)
    inquiries=[audit_inquiry(c,live) for c in INQUIRIES]
    query=ayat_questions.rank(question) if question else None
    if query:
        for item in query["ranking"]:
            ids=[c["id"] for c in present if c["family"]==item["family"]]
            ids.extend(c["id"] for c in inquiries if c["family"]==item["family"])
            item["eligible_records"]=ids
    return {"schema":"nabt.ayat-cognitive-chain.v1","policy":policy_record(),"context":{
                k:{**v,"state":"PRESENT" if "ctx/"+k in live else "WITHDRAWN"} for k,v in g.owners["cognitive_context"].items()},
            "claims":present+removed,"inquiries":inquiries,"question_ranking":query,
            "world_truth_established":False,"derived_legal_rulings":[]}

# User-supplied scene atoms are hypothetical, individually scoped and intentionally tri-valued.
# Text may identify a condition even if the external occasion has not been observed.
SCENE_RULES = (
    ("writing_request","طلب كتابة الدين في المشهد","cog/if_then",("debt","specified_term")),
    ("guardian_dictates","إملال الولي في فرع عدم الاستطاعة","cog/guardian",("debtor_unable_to_dictate",)),
    ("alternative_witnesses","فرع رجل وامرأتين ممن ترضون","cog/alternative",("two_men_unavailable",)),
    ("trade_exception","استثناء ترك الكتابة في التجارة الحاضرة المدارة","cog/exception",("present_trade","circulated_between_parties")),
    ("sale_witnesses","طلب الإشهاد في البيع","cog/sale",("sale",)),
)
SCENE_ATOMS={k for _,_,_,atoms in SCENE_RULES for k in atoms}


def validate_scene(scene):
    if (type(scene) is not dict or not set(scene)<=SCENE_ATOMS
            or any(type(v) is not bool for v in scene.values())):
        raise ValueError("Scene expects named boolean observations; omission means unknown")


def apply_scene(scene,live):
    validate_scene(scene)
    result=[]
    for key,title,base,required in SCENE_RULES:
        missing=[k for k in required if k not in scene]
        failed=[k for k in required if scene.get(k) is False]
        if base not in live:
            state="TEXT_SUPPORT_WITHDRAWN"
        elif failed:
            state="THIS_BRANCH_INACTIVE"
        elif missing:
            state="UNKNOWN_SCENE"
        else:
            state="ACTIVE_IN_ASSUMED_SCENE"
        result.append({"id":key,"name":title,"text_basis":base,"state":state,"required":list(required),
                       "missing":missing,"negative":failed,"opposite_ruling_inferred":False})
    return {"scope":"USER_ASSUMED_SCENE","premises":dict(scene),"applications":result,"external_event_verified":False}
