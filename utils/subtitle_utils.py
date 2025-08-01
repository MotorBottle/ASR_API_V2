#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# Copyright FunASR (https://github.com/alibaba-damo-academy/FunClip). All Rights Reserved.
#  MIT License  (https://opensource.org/licenses/MIT)

import re

def time_convert(ms):
    """Convert milliseconds to SRT time format"""
    ms = int(ms)
    tail = ms % 1000
    s = ms // 1000
    mi = s // 60
    s = s % 60
    h = mi // 60
    mi = mi % 60
    h = "00" if h == 0 else str(h)
    mi = "00" if mi == 0 else str(mi)
    s = "00" if s == 0 else str(s)
    tail = str(tail).zfill(3)  # Pad milliseconds to 3 digits
    if len(h) == 1: h = '0' + h
    if len(mi) == 1: mi = '0' + mi
    if len(s) == 1: s = '0' + s
    return "{}:{}:{},{}".format(h, mi, s, tail)

def str2list(text):
    """Convert text to list of tokens"""
    pattern = re.compile(r'[\u4e00-\u9fff]|[\w-]+', re.UNICODE)
    elements = pattern.findall(text)
    return elements

class Text2SRT():
    """Convert text and timestamp to SRT format"""
    
    def __init__(self, text, timestamp, offset=0):
        self.token_list = text
        self.timestamp = timestamp
        start, end = timestamp[0][0] - offset, timestamp[-1][1] - offset
        self.start_sec, self.end_sec = start, end
        self.start_time = time_convert(start)
        self.end_time = time_convert(end)
    
    def text(self):
        """Get text content"""
        if isinstance(self.token_list, str):
            return self.token_list
        else:
            res = ""
            for word in self.token_list:
                if '\u4e00' <= word <= '\u9fff':
                    res += word
                else:
                    res += " " + word
            return res.lstrip()
    
    def srt(self, acc_ost=0.0):
        """Generate SRT subtitle entry"""
        return "{} --> {}\n{}\n".format(
            time_convert(self.start_sec+acc_ost*1000),
            time_convert(self.end_sec+acc_ost*1000), 
            self.text())
    
    def time(self, acc_ost=0.0):
        """Get time range"""
        return (self.start_sec/1000+acc_ost, self.end_sec/1000+acc_ost)

def generate_srt(sentence_list, merge_threshold=8000):
    """
    Generate SRT subtitles, merging consecutive utterances from the same speaker.
    
    :param sentence_list: List of recognized sentences with 'text', 'timestamp' and optional 'spk' fields
    :param merge_threshold: Time interval threshold for merging consecutive utterances (milliseconds)
    :return: Merged SRT string
    """
    srt_total = ''
    index = 1

    if not sentence_list:
        return srt_total

    # Initialize merging variables for the first entry
    current_spk = sentence_list[0].get('spk', None)
    
    # Handle different timestamp formats
    first_timestamp = sentence_list[0]['timestamp']
    if isinstance(first_timestamp, list) and len(first_timestamp) > 0:
        if isinstance(first_timestamp[0], (list, tuple)) and len(first_timestamp[0]) >= 2:
            current_start = first_timestamp[0][0]  # First word start time
            current_end = first_timestamp[-1][1]   # Last word end time
        else:
            # If timestamp is a flat list [start, end]
            current_start = first_timestamp[0] if len(first_timestamp) > 0 else 0
            current_end = first_timestamp[1] if len(first_timestamp) > 1 else 0
    else:
        # Fallback if timestamp format is unexpected
        current_start = 0
        current_end = 0
    
    
    current_text = sentence_list[0]['text']

    for sent in sentence_list[1:]:
        sent_spk = sent.get('spk', None)
        
        # Handle different timestamp formats consistently
        sent_timestamp = sent['timestamp']
        if isinstance(sent_timestamp, list) and len(sent_timestamp) > 0:
            if isinstance(sent_timestamp[0], (list, tuple)) and len(sent_timestamp[0]) >= 2:
                sent_start = sent_timestamp[0][0]    # First word start time
                sent_end = sent_timestamp[-1][1]     # Last word end time
            else:
                # If timestamp is a flat list [start, end]
                sent_start = sent_timestamp[0] if len(sent_timestamp) > 0 else 0
                sent_end = sent_timestamp[1] if len(sent_timestamp) > 1 else 0
        else:
            # Fallback if timestamp format is unexpected
            sent_start = 0
            sent_end = 0
            
        sent_text = sent['text']

        # Check if it meets merging conditions with current entry
        same_speaker = (sent_spk == current_spk)
        time_gap = sent_start - current_end

        if same_speaker and time_gap <= merge_threshold:
            # Merge text and time - ensure we use the latest end time
            current_end = sent_end  # Always update to the latest sentence's end time
            current_text += ' ' + sent_text
        else:
            # Write current merged entry
            t2s = Text2SRT(current_text, [(current_start, current_end)])
            if current_spk is not None:
                # Standard SRT format: speaker ID in text content
                srt_content = t2s.srt().replace(current_text, f"[spk{current_spk}] {current_text}")
                srt_total += "{}\n{}\n".format(index, srt_content)
            else:
                srt_total += "{}\n{}\n".format(index, t2s.srt())
            index += 1

            # Re-initialize merging variables
            current_spk = sent_spk
            current_start = sent_start
            current_end = sent_end
            current_text = sent_text

    # Write the last merged entry
    t2s = Text2SRT(current_text, [(current_start, current_end)])
    if current_spk is not None:
        # Standard SRT format: speaker ID in text content
        srt_content = t2s.srt().replace(current_text, f"[spk{current_spk}] {current_text}")
        srt_total += "{}\n{}\n".format(index, srt_content)
    else:
        srt_total += "{}\n{}\n".format(index, t2s.srt())

    return srt_total