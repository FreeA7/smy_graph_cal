# -*- coding: utf-8 -*-
"""
Created on Sat Jun  4 23:23:26 2022

@author: FreeA7
"""
import json

from utils import *
from nltk.tokenize import sent_tokenize
from nltk.tokenize import word_tokenize

from datetime import datetime

SEP = '\t'
SYLL_DICT = json.load(open('syll_dict.json', 'r', encoding='utf-8'))
SEEN = set(json.load(open('seen.json', 'r', encoding='utf-8')))

HEAD = ['num_of_word_abstract', 'abstract_flesch', 'abstract_gunning', 'abstract_kincaid',
        'num_of_word_description', 'description_flesch', 'description_gunning', 'description_kincaid',
        'num_of_word_all', 'all_flesch', 'all_gunning', 'all_kincaid']


def cal_syllables(s):
    num_of_sentences = 0
    num_of_words = 0
    num_of_sylls = 0
    num_of_long_words = 0
    for paragraph in s.split('||'):
        for sentence in sent_tokenize(paragraph):
            num_of_sentences += 1
            for word in word_tokenize(sentence):
                word = word.strip().lower()
                if word in SEEN:
                    syll = SYLL_DICT[word]
                    num_of_words += 1
                    num_of_sylls += syll
                    if syll >= 3:
                        num_of_long_words += 1
    try:
        ave_word_of_sen = num_of_words / num_of_sentences
        ave_syll_of_word = num_of_sylls / num_of_words
        pro_of_long = num_of_long_words / num_of_words
        flesch = 206.835 - (1.015 * ave_word_of_sen) - (84.6 * ave_syll_of_word)
        gunning = (ave_word_of_sen + pro_of_long) * 0.4
        kincaid = (11.8 * ave_syll_of_word) + (0.39 * ave_word_of_sen) - 15.59
        return [num_of_words, flesch, gunning, kincaid]
    except ZeroDivisionError:
        print('ERROR!!!!!!!!!!!!!!!')
        return [num_of_words, 0, 0, 0]



if __name__ == '__main__':
    count = 0
    out = open('last_output.txt', 'w', encoding='utf-8')

    with open('output.txt', 'r', encoding='utf-8') as f:
        line_org = f.readline()
        # out.write(line_org[:-1])
        out.write(SEP + SEP.join(HEAD) + '\n')
        out.flush()
        headers = {v: i for i, v in enumerate(split_line(line_org, SEP))}
        while 1:
            line_org = f.readline()
            # out.write(line_org[:-1])
            if not line_org:
                break
            line = split_line(line_org, SEP)
            start = datetime.now()
            ab_res = cal_syllables(get_field('abstract', line, headers))
            de_res = cal_syllables(get_field('description', line, headers))
            all_res = cal_syllables(get_field('abstract', line, headers) + ' || ' + get_field('description', line, headers))
            out.write(SEP + SEP.join([num2str(r) for r in ab_res]))
            out.write(SEP + SEP.join([num2str(r) for r in de_res]))
            out.write(SEP + SEP.join([num2str(r) for r in all_res]) + '\n')
            end = datetime.now()
            count += 1
            print('%d : %s' % (count, str(end - start)))
    out.close()


