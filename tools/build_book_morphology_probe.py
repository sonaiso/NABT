"""Freeze an authored transfer probe before neural training, from exact quotes.

Editorial vocalization is distinct from source bytes and is NOT independently
reviewed gold. These examples never enter training or model selection.
"""
import json
from pathlib import Path
import sys
import unicodedata
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.arabic_training.data import sha


def build():
    specs = []
    def add(book, quote, surface, target, task, gold):
        specs.append((book, quote, surface, target, task, gold))
    for plain, vocalized, form in [
        ('ذهب','ذَهَبَ','past'), ('سمع','سَمِعَ','past'), ('مكث','مَكُثَ','past'), ('حمد','حَمِدَ','past'),
        ('اذهب','اِذْهَبْ','imperative'), ('اقتل','اُقْتُلْ','imperative'), ('اضرب','اِضْرِبْ','imperative'),
        ('يقتل','يَقْتُلُ','present'), ('يذهب','يَذْهَبُ','present'), ('يضرب','يَضْرِبُ','present')]:
        add('sibawayhi',plain,vocalized,0,'verb_form',form)
    for plain, vocalized in [('رجل','رَجُلٌ'),('فرس','فَرَسٌ'),('حائط','حَائِطٌ')]:
        add('sibawayhi',plain,vocalized,0,'word_class','noun')
    for quote, surface, target, gold in [
        ('رأيت زيدا','رَأَيْتُ زَيْدًا',1,'منصوب'), ('مررت بزيد','مَرَرْتُ بِزَيْدٍ',1,'مجرور'),
        ('هذا\n~~زيد','هَذَا زَيْدٌ',1,'مرفوع'), ('لن\n~~يفعل','لَنْ يَفْعَلَ',1,'منصوب'),
        ('سيفعل','سَيَفْعَلُ',0,'مرفوع'), ('لم يفعل','لَمْ يَفْعَلْ',1,'مجزوم')]:
        add('sibawayhi',quote,surface,target,'case_mood',gold)
    for plain, vocalized, form in [
        ('ضربوا','ضَرَبُوا','past'), ('ضربت','ضَرَبْتُ','past'), ('نعم','نِعْمَ','past'), ('بئس','بِئْسَ','past'),
        ('عسى','عَسَى','past'), ('ليس','لَيْسَ','past'), ('اغز','اُغْزُ','imperative'),
        ('اخش','اِخْشَ','imperative'), ('ارم','اِرْمِ','imperative'), ('قوما','قُومَا','imperative'),
        ('قوموا','قُومُوا','imperative'), ('قومي','قُومِي','imperative'),
        ('نقوم','نَقُومُ','present'), ('أقوم','أَقُومُ','present'), ('يقوم','يَقُومُ','present'),
        ('تقوم','تَقُومُ','present'), ('يدحرج','يُدَحْرِجُ','present'), ('يكرم','يُكْرِمُ','present'),
        ('يستخرج','يَسْتَخْرِجُ','present')]:
        add('qatr',plain,vocalized,0,'verb_form',form)
    records=[]
    for i,(book,quote,surface,target,task,gold) in enumerate(specs,1):
        path=ROOT/'src/nabt/data/source_evidence'/f'{book}.txt'
        raw=path.read_bytes()
        # Restrict location to the grammar chapters actually read, not metadata.
        lines=raw.splitlines(keepends=True)
        first,last=(102,126) if book=='sibawayhi' else (54,71)
        offset=sum(map(len,lines[:first-1])); window=b''.join(lines[first-1:last])
        start=offset+window.index(quote.encode()); end=start+len(quote.encode())
        original=' '.join(quote.replace('\n~~',' ').split())
        plain=''.join(c for c in surface if not unicodedata.combining(c))
        if original != plain:
            raise ValueError('editorial vocalization must preserve source letters')
        records.append(dict(id=f'BOOK-{i:03}',book=book,source_path=str(path.relative_to(ROOT)),
                            source_sha256=sha(raw),start_byte=start,end_byte=end,quote=quote,
                            quote_sha256=sha(raw[start:end]),editorial_surface=surface,target_word=target,
                            task=task,expected=gold,independent_human_review=False))
    return dict(schema='nabt.authored-book-transfer-probe.v1',
                status='AUTHORED_DEVELOPMENT_TRANSFER_PROBE_NOT_BLIND_GOLD',
                note='Original quotes are largely unvocalized. Editorial vowels and target interpretations are separately attributed, not asserted to be source bytes. Never used for fitting or selection.',cases=records)


if __name__=='__main__':
    target=ROOT/'evidence/source_morphology_training/book_probe.json'
    target.write_text(json.dumps(build(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
