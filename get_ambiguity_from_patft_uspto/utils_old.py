# -*- coding: utf-8 -*-
"""
Created on Wed Apr  1 14:17:22 2020

@author: FreeA7
"""

from nltk.tokenize import sent_tokenize
from nltk.tokenize import word_tokenize
from nltk.corpus import cmudict

import datetime
import os

from config import SENTIMENT_BAN_LIST, SENTIMENT_WORDS_DIR, SENTIMENT_LIST
from config import SENTIMENT_POSITIVE_LIST, SENTIMENT_NEGATIVE_LIST

from config import PARAGRAPH_CHARACTERS
from config import PROGRAM_NAME

import numpy as np

class Utils(object):
    CMUDICT = cmudict.dict()
    if not os.path.exists('./logs/'):
        os.mkdir('./logs/')
    with open('./logs/%s.log'%PROGRAM_NAME, 'a+') as f:
        f.write('\n'+('-'*10)+' %s : %s '%(PROGRAM_NAME, 
                   datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))+('-'*10)+'\n')
    
    def log(info, level=0):
        if level == 0:
            level = 'Info'
        elif level == 1:
            level = 'Warning'
        elif level == -1:
            level = 'Error'
        print('%s: %s'%(level, str(info)))
        with open('./logs/%s.log'%PROGRAM_NAME, 'a+', errors='ignore') as f:
            f.write('%s: %s\n'%(level, str(info)))
    
    @classmethod
    def getSyllablesNum(cls, word):
        return [len(list(y for y in x if y[-1].isdigit())) for x in cls.CMUDICT[word]][0]
    
    def getBlockNums(text):
        num = 0
        for character in text:
            if character == ' ': num += 1
        return num
    
    @classmethod
    def getParagraphInfo(cls, sentiment_paragraphs, paragraphs):
        for paragraph_index in sentiment_paragraphs.keys():
            syllables_num = sentences_num = words_num = fuzadanci = 0
            paragraph = paragraphs[paragraph_index].strip().lower()
            words = word_tokenize(paragraph)
            for word in words:
                try:
                    syllables_num += cls.getSyllablesNum(word)
                    if cls.getSyllablesNum(word)>=3:
                        fuzadanci +=1
                    words_num += 1
                except KeyError:
                    continue
            sentences = sent_tokenize(paragraph)
            for sentence in sentences:
                sentences_num += 1
            if sentences_num == 0:
                pingjunjuchang = 0
            else:
                pingjunjuchang = words_num/sentences_num
            if words_num == 0:
                pingjunyinjie = 0
            else:
                pingjunyinjie = syllables_num/words_num
            mohudu = 11.8*pingjunyinjie+0.39*pingjunjuchang-15.59
            keduxing = 206.835-1.105*pingjunjuchang-84.6*pingjunyinjie
            mohudu_fog = (pingjunjuchang+fuzadanci/words_num)*0.4
            sentiment_paragraphs[paragraph_index]['words_num'] = words_num
            sentiment_paragraphs[paragraph_index]['syllables_num'] = syllables_num
            sentiment_paragraphs[paragraph_index]['sentences_num'] = sentences_num
            sentiment_paragraphs[paragraph_index]['mohudu'] = mohudu
            sentiment_paragraphs[paragraph_index]['keduxing'] = keduxing
            sentiment_paragraphs[paragraph_index]['mohudu_fog'] = mohudu_fog
        
    @classmethod
    def judgeIsParagraphOrNot(cls, text):
        # 1.Null String
        if text == '':
            return False
        # 2.Not Sentence
#        if '.' not in text:
#            if len(text) > 100:
#                cls.log('2=>%s'%text, 1)
#            return False
        # 3.Too Short 
        if cls.getBlockNums(text) < 6:
#            if len(text) > 100:
#                cls.log('3=>%s'%text, 1)
            return False
        # 4.Not start with an upper letter or a number 
#        if text[0] not in PARAGRAPH_START_CHARACTERS:
#            if len(text) > 100:
#                cls.log('4=>%s'%text, 1)
#            return False
        # 5.No any letter
        character_flag = 0
        for character in PARAGRAPH_CHARACTERS:
            if character in text:
                character_flag = 1
                break
        if not character_flag:
            return False
        # May be a paragraph
        return True
