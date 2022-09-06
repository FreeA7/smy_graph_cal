# -*- coding: utf-8 -*-
"""
Created on Wed Apr  1 01:07:24 2020

@author: FreeA7
"""

from bs4 import BeautifulSoup
import requests

from utils import Utils
from config import URL_LIST, SENTIMENT_LIST


SENTIMENT_WORDS = Utils.getSentimentWords()

if __name__=='__main__':
    for url in URL_LIST:
        Utils.log('---- Url -> %s'%url)
        sentiment_paragraphs = {}
        res = requests.get(url)
        Utils.log('---- Resource is ready.')
        if url[-3:] == 'htm':
            document = BeautifulSoup(res.text, 'html.parser')
            paragraphs = document.find_all('p') + document.find_all('div')
            paragraphs = [paragraph.text for paragraph in paragraphs]
        elif url[-3:] == 'txt':
            paragraphs = res.text.split('\n\n')
            paragraphs = [paragraph.replace('\n', ' ') for paragraph in paragraphs]
            
        paragraph_index = -1
        for paragraph in paragraphs:
            if paragraph_index % 1000 == 0: Utils.log('-- %d line'%paragraph_index)
            paragraph_index += 1
            paragraph = paragraph.strip()
            if not Utils.judgeIsParagraphOrNot(paragraph):
                continue
            else:
                paragraph = paragraph.lower()
                sentiment_paragraphs[paragraph_index] = {}
                for sentiment in SENTIMENT_WORDS.keys():
                    sentiment_paragraphs[paragraph_index][sentiment] = 0
                    for word in SENTIMENT_WORDS[sentiment]:
                        if word in paragraph:
                            sentiment_paragraphs[paragraph_index][sentiment] += 1
        
        Utils.getParagraphSentiment(sentiment_paragraphs)
        Utils.getParagraphInfo(sentiment_paragraphs, paragraphs)
        
        # 你看这里只有两个变量来承接返回值
        positive_counter, negative_counter, variability_list = Utils.getDocumentOutput(sentiment_paragraphs)
        
        Utils.log('Positive:')
        for sentiment in SENTIMENT_LIST:
            Utils.log('\t%s: %d'%(sentiment, positive_counter[sentiment]))
        Utils.log('\tNumber of Word: %d'%(positive_counter['words_num']))
        Utils.log('\tAverage Length of Sentence: %f'%(positive_counter['words_num']/positive_counter['sentences_num']))
        Utils.log('\tAverage Syllable Number of Word: %f'%(positive_counter['syllables_num']/positive_counter['words_num']))
        Utils.log('\tmohudu fangcha: %f'%(positive_counter['mohudu_variability1']))
        Utils.log('\tmohudu biaozhuncha: %f'%(positive_counter['mohudu_variability2']))
        Utils.log('\tkeduxing fangcha: %f'%(positive_counter['keduxing_variability1']))
        Utils.log('\tkeduxing biaozhuncha: %f'%(positive_counter['keduxing_variability2']))
                  
        Utils.log('Negative:')
        for sentiment in SENTIMENT_LIST:
            Utils.log('\t%s: %d'%(sentiment, negative_counter[sentiment]))
        Utils.log('\tNumber of Word: %d'%(negative_counter['words_num']))
        Utils.log('\tAverage Length of Sentence: %f'%(negative_counter['words_num']/negative_counter['sentences_num']))
        Utils.log('\tAverage Syllable Number of Word: %f'%(negative_counter['syllables_num']/negative_counter['words_num']))
        Utils.log('\tmohudu fangcha: %f'%(negative_counter['mohudu_variability1']))
        Utils.log('\tmohudu biaozhuncha: %f'%(negative_counter['mohudu_variability2']))
        Utils.log('\tkeduxing fangcha: %f'%(negative_counter['keduxing_variability1']))
        Utils.log('\tkeduxing biaozhuncha: %f'%(negative_counter['keduxing_variability2']))
        
        Utils.log('All:')
        Utils.log('\tmohudufangcha_all: %f'%(variability_list[0]))
        Utils.log('\tmohudubiaozhuncha_all: %f'%(variability_list[1]))
        Utils.log('\tkeduxingfangcha_all: %f'%(variability_list[2]))
        Utils.log('\tkeduxingbiaozhuncha_all: %f'%(variability_list[3]))

