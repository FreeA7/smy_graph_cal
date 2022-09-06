# -*- coding: utf-8 -*-
"""
Created on Sat Jun  4 23:23:26 2022

@author: FreeA7
"""
import json

from utils import *
from curses.ascii import isdigit
from nltk.corpus import cmudict
from nltk.tokenize import sent_tokenize
from nltk.tokenize import word_tokenize

from datetime import datetime

SEP = '\t'
SYLL_DICT = dict()
SEEN = set()
D = cmudict.dict()
fc = open('null.txt', 'w', encoding='utf-8')


def nsyl(word):
    return max([len([y for y in x if isdigit(y[-1])]) for x in D[word.lower()]])


def cal_syllables(s):
    for paragraph in s.split('||'):
        for sentence in sent_tokenize(paragraph):
            for word in word_tokenize(sentence):
                word = word.strip().lower()
                if word not in SEEN:
                    try:
                        syll = nsyl(word)
                    except KeyError:
                        fc.write(word + '\n')
                        continue
                    SYLL_DICT[word] = syll
                    SEEN.add(word)


if __name__ == '__main__':
    count = 0

    with open('output.txt', 'r', encoding='utf-8') as f:
        headers = {v: i for i, v in enumerate(split_line(f.readline(), SEP))}
        while 1:
            line = f.readline()
            if not line:
                break
            line = split_line(line, SEP)
            start = datetime.now()
            cal_syllables(get_field('abstract', line, headers))
            cal_syllables(get_field('description', line, headers))
            end = datetime.now()
            count += 1
            print('%d : %s' % (count, str(end - start)))

    SEEN = list(SEEN)
    s = open('seen.json', 'w', encoding='utf-8')
    json.dump(SEEN, s)
    s.close()
    s = open('syll_dict.json', 'w', encoding='utf-8')
    json.dump(SYLL_DICT, s)
    s.close()
    fc.close()
