"""Versioned correction: CNN pooling ignores padded character positions."""
import torch
from torch import nn
from .model import MorphologyModel


class MaskedMorphologyModel(MorphologyModel):
    def forward(self, words, chars, lengths):
        b,t,c=chars.shape
        flat=chars.reshape(b*t,c)
        embedded=self.char_embedding(flat).transpose(1,2)
        features=torch.relu(self.char_conv(embedded))
        valid=flat!=0
        encoded=features.masked_fill(~valid.unsqueeze(1),float('-inf')).amax(dim=2)
        encoded=encoded.masked_fill(~valid.any(dim=1,keepdim=True),0).reshape(b,t,48)
        values=self.dropout(torch.cat([self.word_embedding(words),encoded],dim=-1))
        packed=nn.utils.rnn.pack_padded_sequence(values,lengths.cpu(),batch_first=True,enforce_sorted=False)
        result,_=self.context(packed)
        result,_=nn.utils.rnn.pad_packed_sequence(result,batch_first=True,total_length=t)
        result=self.dropout(result)
        return {**{task:head(result) for task,head in self.heads.items()},'affixes':self.affix_head(result)}
