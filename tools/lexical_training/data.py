"""Pinned dictionary entry correspondence. Root identity is a WEAK label.

It identifies a bibliographic entry, not equivalent senses or true sentences.
Source bytes are never normalized. Only the retrieval view is normalized.
"""
import gzip
import hashlib
import json
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
LISAN_SHA = '34fa56710a5b701532a34cb70f8fe440b261e80ae3c40d9667d18b65be7ed86d'
MAQAYIS_SHA = '7f71af0dfe056cb84e7da24657fa13edc6e8061ca1980eed7f6c196bd18b5689'
LISAN_BLOB = '9f6bfb332bdf8ed25ff6c7b50400ea258bbe0b7b'
LISAN_GZIP_SHA = 'ed42d51af8a4a72ba43959b9a0a34953b88dca9c8729e5661cf0b2f5935f351a'
LISAN_REV = '056df249d6619b428a78f1d69a8ab2851b97b0a6'
MAQAYIS_REV = '5bb6966d8df2ed22b1bff5cdbe29bb9c24f3ca29'
LISAN_URL = ('https://raw.githubusercontent.com/Saleh1967/Alghanem/'
 '9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/corpora/lisan/'
 '0711IbnManzurIfriqi.LisanCarab.Shamela0001687-ara1.mARkdown.gz')

def digest(data):
    return hashlib.sha256(data).hexdigest()

def fetch_lisan(path):
    path = Path(path)
    if path.exists():
        data = path.read_bytes()
    else:
        with urllib.request.urlopen(LISAN_URL, timeout=120) as response:
            compressed = response.read(12_000_001)
        if len(compressed) > 12_000_000:
            raise ValueError('compressed source exceeds pinned bound')
        if digest(compressed) != LISAN_GZIP_SHA:
            raise ValueError('compressed Lisan identity mismatch')
        data = gzip.decompress(compressed)
    if len(data) != 30670791 or digest(data) != LISAN_SHA:
        raise ValueError('Lisan source identity mismatch')
    if hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest() != LISAN_BLOB:
        raise ValueError('Lisan upstream git blob mismatch')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return data

def normalize(s):
    s = re.sub(r'[\u064b-\u065f\u0670\u0640]', '', s)
    return s.translate(str.maketrans('أإآٱى', 'ااااي'))

def root_key(s):
    s = normalize(s)
    if not re.fullmatch('[ء-غف-ي]{2,3}', s):
        return None
    return s + s[-1] if len(s) == 2 else s

def entries(data, book):
    # Byte offsets retain exact source identity, including OpenITI markup.
    pattern = rb'^### \$ ([^:\n]+):' if book == 'lisan' else rb'^### \| \(([^)\n]+)\)\s*\n'
    heads = list(re.finditer(pattern, data, re.M))
    all_heads = list(re.finditer(rb'^### ', data, re.M))
    next_heading = {h.start(): (all_heads[i+1].start() if i+1<len(all_heads) else len(data))
                    for i,h in enumerate(all_heads)}
    result = {}
    for h in heads:
        root = h.group(1).decode().strip()
        key = root_key(root)
        if key is None:
            continue
        end = next_heading.get(h.start(), len(data))
        record = {'root':root, 'key':key, 'start_byte':h.start(), 'end_byte':end,
                  'text':data[h.end():end].decode()}
        result.setdefault(key, []).append(record)
    # Normalization collisions/duplicate entry headings are not silently selected.
    return {k:v[0] for k,v in result.items() if len(v)==1}

LETTERS = set('الهمزة الألف الباء التاء الثاء الجيم الحاء الخاء الدال الذال الراء الزاي السين الشين الصاد الضاد الطاء الظاء العين الغين الفاء القاف الكاف اللام الميم النون الهاء الواو الياء'.split())
LETTERS = {normalize(x) for x in LETTERS}

def view(entry, max_tokens=128):
    s = re.sub(r'PageV\d+P\d+|ms\d+', ' ', entry['text'])
    # Bounded dictionary prose, not a generated Quran/paraphrase benchmark.
    s = re.split(r'وفي التنزيل|قال الله|قوله تعالى|وفي حديث|قال الشاعر|وأنشد|\{', s)[0]
    words = re.findall('[ء-غف-ي]+', normalize(s))
    root = entry['key']
    def is_root_spelling(w):
        return root in w or (len(root)==3 and root[1]==root[2] and root[:2] in w)
    words = [w for w in words if w.removeprefix('و') not in LETTERS
             and w not in LETTERS and not is_root_spelling(w)]
    return ' '.join(words[:max_tokens])

def paired_data(lisan_path):
    lisan = fetch_lisan(lisan_path)
    maqayis = (ROOT/'evidence/classical_language/sources/maqayis.txt').read_bytes()
    if digest(maqayis) != MAQAYIS_SHA:
        raise ValueError('Maqayis source identity mismatch')
    ls, ms = entries(lisan, 'lisan'), entries(maqayis, 'maqayis')
    pairs = []
    for key in sorted(ls.keys() & ms.keys()):
        a, b = view(ls[key]), view(ms[key])
        if len(a.split()) < 8 or len(b.split()) < 8:
            continue
        pairs.append({'key':key,'lisan':ls[key], 'maqayis':ms[key], 'query':a, 'document':b})
    # Exact normalized view duplicates cannot cross splits or inflate retrieval.
    from collections import Counter
    ac,bc=Counter(x['query'] for x in pairs),Counter(x['document'] for x in pairs)
    pairs=[x for x in pairs if ac[x['query']]==1 and bc[x['document']]==1]
    for x in pairs:
        bucket=int(hashlib.sha256(('nabt-lexical-root-split-v1:'+x['key']).encode()).hexdigest()[:8],16)%10
        x['split']='test' if bucket==0 else 'dev' if bucket==1 else 'train'
    return pairs

def save_json(path,value):
    if isinstance(value,list):
        content='[\n'+',\n'.join('  '+json.dumps(row,ensure_ascii=False,sort_keys=True) for row in value)+'\n]\n'
    else:
        content=json.dumps(value,ensure_ascii=False,indent=2)+'\n'
    Path(path).write_text(content)
