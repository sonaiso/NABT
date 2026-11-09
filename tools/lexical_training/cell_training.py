"""Train the installed shared GRU implementation on the kernel's A116 codes.

Authored morphology diagnostics, held-out roots and personal suffix stem. No
dictionary meanings, world properties, or annotation authority are inferred.
"""
import argparse
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from nabt.alphabet import parse_word, ALPHABET_ID
from . import shared_encoder as runtime, shared_training as training

PROTOCOL={"id":"nabt.shared-cell-reading-training.v1","seed":116,"epochs":160,
          "learning_rate":0.015,"train_roots":["ضرب","فتح","حمل","حفظ","رفع","جمع"],
          "test_roots":["كتب","غسل"],"heldout_stem":"قم",
          "selection":"FIXED_FINAL_EPOCH_NO_TEST_TUNING","authority":"AUTHORED_PEDAGOGICAL_LABELS"}

def dataset():
    sets={"train":[],"test":[]}
    for split in sets:
        for root in PROTOCOL[split+"_roots"]:
            a,b,c=root
            words=[(a+"َ"+b+"َ"+c+"َ","faala_marks","active_past","agent"),
                   (a+"ُ"+b+"ِ"+c+"َ","fuila_marks","passive_past","patient_subject")]
            for mark,reading,morph,attach in [("ُ","suffix_tu","speaker","speaker_suffix"),
                    ("َ","suffix_ta","addressee_male","addressee_suffix"),
                    ("ِ","suffix_ti","addressee_female","addressee_suffix")]:
                words.append((a+"َ"+b+"َ"+c+"ْت"+mark,reading,morph,attach))
            for text,reading,morph,attach in words:
                sets[split].append({"text":text,"root":root,"cells":list(parse_word(text)),
                    "labels":{"reading":reading,"morphology":morph,"attachment":attach},
                    "provenance":"AUTHORED_NOT_LEXICAL_ATTESTATION"})
    for mark,reading,morph,attach in [("ُ","suffix_tu","speaker","speaker_suffix"),
            ("َ","suffix_ta","addressee_male","addressee_suffix"),("ِ","suffix_ti","addressee_female","addressee_suffix")]:
        text="قُمْت"+mark
        sets["test"].append({"text":text,"root":"قوم","cells":list(parse_word(text)),
            "labels":{"reading":reading,"morphology":morph,"attachment":attach},"provenance":"AUTHORED_HELDOUT_STEM"})
    assert not {r['root'] for r in sets['train']} & {r['root'] for r in sets['test']}
    return sets

def train_run(directory):
    import torch
    torch.set_num_threads(1);torch.manual_seed(PROTOCOL["seed"]);torch.use_deterministic_algorithms(True)
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
    sets=dataset();train,test=sets['train'],sets['test']
    labels={h:sorted({r['labels'][h] for r in train}) for h in runtime.CELL_HEADS}
    training.save(directory/'protocol.json',PROTOCOL)
    for split,rows in sets.items():training.save(directory/(split+'.json'),rows)
    model=training.torch_model(labels,vocabulary=117,tokenizer=runtime.cell_ids)
    initial=deepcopy(model.state_dict());optimizer=torch.optim.Adam(model.parameters(),lr=PROTOCOL['learning_rate'])
    targets={h:torch.tensor([labels[h].index(r['labels'][h]) for r in train]) for h in labels}
    for _ in range(PROTOCOL['epochs']):
        optimizer.zero_grad();scores=model([r['cells'] for r in train])
        loss=sum(torch.nn.functional.cross_entropy(scores[h],targets[h]) for h in labels)/len(labels)
        loss.backward();optimizer.step()
    exported={"schema":runtime.CELL_SCHEMA,"alphabet_id":ALPHABET_ID,"architecture":{
        "embedding":runtime.EMBEDDING,"hidden":runtime.HIDDEN,"vocabulary":117,"max_cells":64,"pad":0,"cell_offset":1},
        "labels":labels,"parameters":{k:v.detach().tolist() for k,v in model.state_dict().items()},
        "training_sha256":sha256(training.wire(train)).hexdigest(),"protocol":PROTOCOL,"authority":"NONE"}
    training.save(directory/'model.json',exported);portable,identity=runtime.load_cell_model(directory/'model.json')
    model.eval()
    with torch.no_grad():scores=model([r['cells'] for r in test])
    rows=[];error=0.
    for i,row in enumerate(test):
        values=runtime.cell_logits(portable,row['cells'])
        predicted={h:labels[h][max(range(len(labels[h])),key=lambda j:values[h][j])] for h in labels}
        for h in labels:error=max(error,max(abs(a-b) for a,b in zip(values[h],scores[h][i].tolist())))
        rows.append({**row,'predicted':predicted})
    report={'protocol':PROTOCOL,'train_rows':len(train),'test_rows':len(test),
            'metrics':{h:{'n':len(test),'correct':sum(r['labels'][h]==r['predicted'][h] for r in rows)} for h in labels},
            'portable_max_abs_error':error,'weights_sha256':identity,'torch_version':torch.__version__,
            'parameter_delta_l2':float(sum((v-initial[k]).square().sum() for k,v in model.state_dict().items()).sqrt()),
            'all_arabic_complete':False,'world_truth_established':False,'independent_semantic_review':False}
    if error>=1e-4:raise ValueError('Portable shared GRU differs from training')
    training.save(directory/'test_predictions.json',rows);training.save(directory/'FIRST_TEST.json',report)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output-dir',required=True)
    args=p.parse_args();print(train_run(args.output_dir))
