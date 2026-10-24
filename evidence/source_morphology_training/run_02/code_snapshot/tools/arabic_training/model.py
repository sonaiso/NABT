"""Character CNN + contextual BiLSTM; only surface words are network inputs."""
import numpy as np
import torch
from torch import nn
from .data import TASKS


class MorphologyModel(nn.Module):
    def __init__(self, vocab):
        super().__init__()
        self.word_embedding = nn.Embedding(len(vocab['words']), 48, padding_idx=0)
        self.char_embedding = nn.Embedding(len(vocab['chars']), 16, padding_idx=0)
        self.char_conv = nn.Conv1d(16, 48, 3, padding=1)
        self.context = nn.LSTM(96, 64, batch_first=True, bidirectional=True)
        self.dropout = nn.Dropout(0.2)
        self.heads = nn.ModuleDict({task: nn.Linear(128, len(vocab['labels'][task])) for task in TASKS})
        self.affix_head = nn.Linear(128, len(vocab['affixes']))

    def forward(self, words, chars, lengths):
        b, t, c = chars.shape
        embedded = self.char_embedding(chars.reshape(b*t, c)).transpose(1, 2)
        encoded = torch.relu(self.char_conv(embedded)).amax(dim=2).reshape(b, t, 48)
        values = self.dropout(torch.cat([self.word_embedding(words), encoded], dim=-1))
        packed = nn.utils.rnn.pack_padded_sequence(values, lengths.cpu(), batch_first=True, enforce_sorted=False)
        result, _ = self.context(packed)
        result, _ = nn.utils.rnn.pad_packed_sequence(result, batch_first=True, total_length=t)
        result = self.dropout(result)
        return {**{task: head(result) for task, head in self.heads.items()}, 'affixes': self.affix_head(result)}


def save_weights(model, path):
    # Never serialize Python pickles or optimizer executable objects.
    np.savez_compressed(path, **{k: v.detach().cpu().numpy() for k, v in model.state_dict().items()})


def load_weights(model, path):
    with np.load(path, allow_pickle=False) as arrays:
        expected = model.state_dict()
        if set(arrays.files) != set(expected):
            raise ValueError('weight key mismatch')
        values = {}
        for key, target in expected.items():
            value = arrays[key]
            if value.shape != tuple(target.shape) or value.dtype != np.float32 or not np.isfinite(value).all():
                raise ValueError('invalid weight tensor')
            values[key] = torch.from_numpy(value.copy())
        model.load_state_dict(values, strict=True)
