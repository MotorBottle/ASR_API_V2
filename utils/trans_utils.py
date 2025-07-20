#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# Copyright FunASR (https://github.com/alibaba-damo-academy/FunClip). All Rights Reserved.
#  MIT License  (https://opensource.org/licenses/MIT)

import numpy as np

def convert_pcm_to_float(data):
    """Convert PCM data to float64 format"""
    if isinstance(data, np.ndarray):
        if data.dtype == np.int16:
            return data.astype(np.float64) / 32768.0
        elif data.dtype == np.int32:
            return data.astype(np.float64) / 2147483648.0
        elif data.dtype == np.float32:
            return data.astype(np.float64)
        elif data.dtype == np.float64:
            return data
        else:
            return data.astype(np.float64)
    else:
        return np.array(data, dtype=np.float64)

def pre_proc(text):
    """Preprocess text for matching"""
    PUNC_LIST = ['，', '。', '！', '？', '、', ',', '.', '?', '!']
    res = ''
    for i in range(len(text)):
        if text[i] in PUNC_LIST:
            continue
        if '\u4e00' <= text[i] <= '\u9fff':
            if len(res) and res[-1] != " ":
                res += ' ' + text[i]+' '
            else:
                res += text[i]+' '
        else:
            res += text[i]
    if res and res[-1] == ' ':
        res = res[:-1]
    return res

def proc(raw_text, timestamp, dest_text, lang='zh'):
    """Process text matching with timestamps"""
    ld = len(dest_text.split())
    mi, ts = [], []
    offset = 0
    while True:
        fi = raw_text.find(dest_text, offset, len(raw_text))
        ti = raw_text[:fi].count(' ')
        if fi == -1:
            break
        offset = fi + ld
        mi.append(fi)
        ts.append([timestamp[ti][0]*16, timestamp[ti+ld-1][1]*16])
    return ts

def proc_spk(dest_spk, sd_sentences):
    """Process speaker-based text matching"""
    ts = []
    for d in sd_sentences:
        d_start = d['timestamp'][0][0]
        d_end = d['timestamp'][-1][1]
        spkid = dest_spk[3:]  # Remove 'spk' prefix
        if str(d['spk']) == spkid and d_end - d_start > 999:
            ts.append([d_start*16, d_end*16])
    return ts

def write_state(state, path):
    """Write state to file (placeholder for compatibility)"""
    pass

def load_state(path):
    """Load state from file (placeholder for compatibility)"""
    return {}