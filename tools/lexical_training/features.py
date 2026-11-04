"""Shared retrieval-view features; never alter source bytes."""
from collections import Counter
import zlib


def features(text, buckets):
    values = []
    for word in text.split():
        values.append('w:' + word)
        word = '^' + word + '$'
        for n in [3, 4]:
            values.extend('c:' + word[i:i+n] for i in range(len(word)-n+1))
    return Counter(zlib.crc32(x.encode()) % buckets for x in values)
