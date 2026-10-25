"""Surface-only CNN/BiLSTM. Reading-set and case-ranking heads have no authority."""
import torch
from torch import nn


class QatrModel(nn.Module):
    def __init__(self, vocab):
        super().__init__()
        self.word_embedding=nn.Embedding(len(vocab['words']),48,padding_idx=0)
        self.char_embedding=nn.Embedding(len(vocab['chars']),16,padding_idx=0)
        self.char_conv=nn.Conv1d(16,48,3,padding=1)
        self.context=nn.LSTM(96,64,batch_first=True,bidirectional=True)
        self.dropout=nn.Dropout(0.2)
        self.reading_head=nn.Linear(128,len(vocab['readings']))
        self.case_head=nn.Linear(128,4)

    def forward(self,words,chars,lengths):
        b,t,c=chars.shape
        flat=chars.reshape(b*t,c)
        valid=flat!=0
        features=torch.relu(self.char_conv(self.char_embedding(flat).transpose(1,2)))
        encoded=features.masked_fill(~valid.unsqueeze(1),float('-inf')).amax(dim=2)
        encoded=encoded.masked_fill(~valid.any(dim=1,keepdim=True),0).reshape(b,t,48)
        values=self.dropout(torch.cat([self.word_embedding(words),encoded],dim=-1))
        packed=nn.utils.rnn.pack_padded_sequence(values,lengths.cpu(),batch_first=True,enforce_sorted=False)
        out,_=self.context(packed)
        out,_=nn.utils.rnn.pad_packed_sequence(out,batch_first=True,total_length=t)
        out=self.dropout(out)
        return self.reading_head(out),self.case_head(out)
