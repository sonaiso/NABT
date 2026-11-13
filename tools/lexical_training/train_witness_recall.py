"""Fit two small class-balanced ridge heads on the existing frozen byte GRU."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from . import shared_encoder as shared, witness_recall as recall

TRAIN=shared.ROOT/"evidence/question_cognition_v1/train.tsv"
CUES={"instrument":["بالمفتاح","بالقلم","دون استعمال المفتاح","دون استعمال القلم"],
      "arrival_condition":["إذا وصل المفتاح","إذا وصل القلم","دون اشتراط وصول المفتاح","دون اشتراط وصول القلم"]}


def fit():
    import numpy as np
    encoder,fingerprint=shared.load_model()
    q=[line.split("\t",1) for line in TRAIN.read_text().splitlines() if line.split("\t",1)[0] in recall.LABELS]
    cues=[(label,text) for label,texts in CUES.items() for text in texts]
    def weights(rows,labels):
        x=np.asarray([recall.vector(encoder,text)+[1.] for label,text in rows])
        y=np.array([[float(gold==label) for label in labels] for gold,text in rows])
        w=np.array([1./sum(other==label for other,_ in rows) for label,_ in rows])
        # Positive ridge penalty includes the intercept to keep the fixed small-sample fit identifiable.
        return np.linalg.solve((x.T*w)@x+.1*np.eye(x.shape[1]),(x.T*w)@y).T.round(10).tolist()
    return {"schema":"nabt.witness-readout.v1","encoder_sha256":fingerprint,"alpha":0.1,
            "question_labels":list(recall.LABELS),"cue_labels":list(recall.AXES),
            "question_rows":len(q),"cue_rows":len(cues),"training_sha256":sha256(json.dumps([q,cues],ensure_ascii=False).encode()).hexdigest(),
            "question":weights(q,recall.LABELS),"cue":weights(cues,recall.AXES)}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--output",type=Path,required=True)
    with p.parse_args().output.open("x",encoding="utf-8") as f:
        json.dump(fit(),f,sort_keys=True,ensure_ascii=False,separators=(",",":"));f.write("\n")
