# -*- coding: utf-8 -*-
"""
Created on Thur Apr  7 11:22:19 2022

@author: FreeA7


按照你所给的Patent_id抓取相关信息并计算模糊度
目前爬虫部分我已经调试完毕，但是模糊度计算特别慢
我觉得是因为描述都特别长导致的
"""

import multiprocessing
import requests
import logging
import re
import time

from bs4 import BeautifulSoup
from collections import defaultdict

from nltk.tokenize import sent_tokenize
from nltk.tokenize import word_tokenize
from nltk.corpus import cmudict

NUM_WORKERS = 1
SEP = '\t'
HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,'
              'application/signed-exchange;v=b3;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive',
    'Host': 'patft.uspto.gov',
    'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="97", "Chromium";v="97"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Referer': 'https://patft.uspto.gov/netacgi/nph-Parser',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/97.0.4692.99 Safari/537.36 '
}

OUTPUT_SEQ = ['patent', 'patent_id', 'inv', 'inv_date', 'abstract',
              'inventors', 'assignee', 'family_id', 'appl_no', 'filed',
              'related_patents', 'current_us_class', 'current_cpc_class',
              'current_international_class', 'field_of_search',
              'us_cited_patents', 'foreign_cited_patents', 'description',
              'mohudu', 'keduxing', 'mohudu_fog']

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[logging.FileHandler(filename='./root.log', encoding='utf-8', mode='w')],
)


def getSyllablesNum(word):
    """
    从当年写的代码搬运过来的
    """
    return [len(list(y for y in x if y[-1].isdigit())) for x in cmudict.dict()[word]][0]


def get_ambiguity_from_description(description):
    """
    从当年写的代码搬运过来的
    """
    syllables_num = sentences_num = words_num = fuzadanci = 0
    paragraph = description.strip().lower()
    words = word_tokenize(paragraph)
    for word in words:
        try:
            syllables_num += getSyllablesNum(word)
            if getSyllablesNum(word) >= 3:
                fuzadanci += 1
            words_num += 1
        except KeyError:
            continue
    sentences = sent_tokenize(paragraph)
    for _ in sentences:
        sentences_num += 1
    if sentences_num == 0:
        pingjunjuchang = 0
    else:
        pingjunjuchang = words_num / sentences_num
    if words_num == 0:
        pingjunyinjie = 0
    else:
        pingjunyinjie = syllables_num / words_num
    mohudu = 11.8 * pingjunyinjie + 0.39 * pingjunjuchang - 15.59
    keduxing = 206.835 - 1.105 * pingjunjuchang - 84.6 * pingjunyinjie
    mohudu_fog = (pingjunjuchang + fuzadanci / words_num) * 0.4
    return mohudu, keduxing, mohudu_fog


def process(input_queue, output_queue, pid):
    all = input_queue.qsize()
    count = 0

    s = requests.Session()
    s.get('https://patft.uspto.gov/netacgi/nph-Parser', headers=HEADERS)
    while input_queue.qsize():
        try:
            start_time = time.time()
            patent = input_queue.get()
            payload = {
                'Sect1': 'PTO1',
                'Sect2': 'HITOFF',
                'u': '/netahtml/PTO/srchnum.htm',
                'd': 'PALL',
                'r': '1',
                'p': '1',
                'f': 'G',
                'l': '50',
                's1': '%s.PN.' % patent,
                'OS': 'PN/%s' % patent,
                'RS': 'PN/%s' % patent
            }
            res = s.get('https://patft.uspto.gov/netacgi/nph-Parser', headers=HEADERS, params=payload)
            logging.info('[%d/%d] %s专利请求成功，url : %s' % (pid, NUM_WORKERS, patent, res.url))

            # 爬取网站之后使用bs4进行解析
            soup = BeautifulSoup(res.text, 'html.parser')

            info = defaultdict(str)

            info['patent'] = patent
            info['patent_id'] = soup.find(text=re.compile(r'United States Patent[^:]')).findNext().text
            try:
                info['inv'] = soup.find(text=re.compile(
                    r'United States Patent[^:]')).findNext().findNext().findNext().findNext().findNext().findNext().findNext().findAll(
                    'td')[0].text
            except IndexError:
                count += 1
                logging.warning(
                    '[%d/%d] %s专利没有信息，url : %s' % (pid, NUM_WORKERS, patent, res.url))
                print('[%d/%d] %s专利没有信息，url : %s' % (pid, NUM_WORKERS, patent, res.url))
                with open('output.txt', 'a', encoding='utf-8') as f:
                    f.write(SEP.join([re.sub(r'[\t\n]', ' ', info[key]).strip() for key in OUTPUT_SEQ]) + '\n')
                continue
            info['inv_date'] = soup.find(text=re.compile(
                r'United States Patent[^:]')).findNext().findNext().findNext().findNext().findNext().findNext().findNext().findAll(
                'td')[1].text
            try:
                info['abstract'] = soup.find(text='Abstract').findNext().text
            except AttributeError:
                logging.warning(
                    '[%d/%d] %s专利没有找到 Abstract 信息，url : %s' % (pid, NUM_WORKERS, patent, res.url))
            try:
                info['inventors'] = soup.find(text='Inventors:').findNext().text
            except AttributeError:
                logging.warning(
                    '[%d/%d] %s专利没有找到 Inventors 信息，url : %s' % (pid, NUM_WORKERS, patent, res.url))
            try:
                info['assignee'] = soup.find(text='Assignee:').findNext().text
            except AttributeError:
                logging.warning(
                    '[%d/%d] %s专利没有找到 Assignee 信息，url : %s' % (pid, NUM_WORKERS, patent, res.url))
            try:
                info['family_id'] = soup.find(text=re.compile(r'Family ID:')).findNext().text
            except AttributeError:
                logging.warning(
                    '[%d/%d] %s专利没有找到 Family ID 信息，url : %s' % (pid, NUM_WORKERS, patent, res.url))
            try:
                info['appl_no'] = soup.find(text=re.compile(r'Appl. No.:')).findNext().text
            except AttributeError:
                logging.warning(
                    '[%d/%d] %s专利没有找到 Appl. No.信息，url : %s' % (pid, NUM_WORKERS, patent, res.url))
            try:
                info['filed'] = soup.find(text=re.compile(r'Filed:')).findNext().text
            except AttributeError:
                logging.warning(
                    '[%d/%d] %s专利没有找到 Filed 信息，url : %s' % (pid, NUM_WORKERS, patent, res.url))
            try:
                node = soup.find(text='Related U.S. Patent Documents').findNext().findNext()
                for row in node.findAll('tr')[1:-1]:
                    row = [n.text for n in row.findAll('td')[1:]]
                    info['related_patents'] += ' | '.join(row) + ' || '
            except AttributeError:
                logging.warning(
                    '[%d/%d] %s专利没有找到 Related U.S. Patent Documents 信息，url : %s' % (pid, NUM_WORKERS, patent, res.url))

            try:
                info['current_us_class'] = soup.find(text='Current U.S. Class:').findNext().text
            except AttributeError:
                logging.warning(
                    '[%d/%d] %s专利没有找到 Current U.S. Class 信息，url : %s' % (pid, NUM_WORKERS, patent, res.url))
            try:
                info['current_cpc_class'] = soup.find(text=re.compile(r'Current CPC Class:')).findNext().text
            except AttributeError:
                logging.warning(
                    '[%d/%d] %s专利没有找到 Current CPC Class 信息，url : %s' % (pid, NUM_WORKERS, patent, res.url))
            try:
                info['current_international_class'] = soup.find(
                    text=re.compile(r'Current International Class:')).findNext().text
            except AttributeError:
                logging.warning(
                    '[%d/%d] %s专利没有找到 Current International Class 信息，url : %s' % (pid, NUM_WORKERS, patent, res.url))
            try:
                info['field_of_search'] = soup.find(text=re.compile(r'Field of Search:')).findNext().text
            except AttributeError:
                logging.warning(
                    '[%d/%d] %s专利没有找到 Field of Search 信息，url : %s' % (pid, NUM_WORKERS, patent, res.url))

            try:
                node = soup.find(text='U.S. Patent Documents').findNext()
                for row in node.findAll('tr')[1:-1]:
                    row = [n.text for n in row.findAll('td')]
                    info['us_cited_patents'] += ' | '.join(row) + ' || '
            except AttributeError:
                logging.warning(
                    '[%d/%d] %s专利没有找到 U.S. Patent Documents 信息，url : %s' % (pid, NUM_WORKERS, patent, res.url))

            try:
                node = soup.find(text='Foreign Patent Documents').findNext()
                for row in node.findAll('tr')[1:-1]:
                    row = [n.text for n in row.findAll('td')]
                    info['foreign_cited_patents'] += ' | '.join(row) + ' || '
            except AttributeError:
                logging.warning(
                    '[%d/%d] %s专利没有找到 Foreign Patent Documents 信息，url : %s' % (pid, NUM_WORKERS, patent, res.url))

            # 按照规则出现标题description之后的部分全都是描述
            try:
                node = soup.find(text='Description')
                while node.next:
                    node = node.next
                    if node.text.strip():
                        info['description'] += node.text.strip() + ' || '
            except AttributeError:
                logging.warning(
                    '[%d/%d] %s专利没有找到 Description 信息，url : %s' % (pid, NUM_WORKERS, patent, res.url))

            # info['mohudu'], info['keduxing'], info['mohudu_fog'] = get_ambiguity_from_description(info['description'])

            end_time = time.time()

            count += 1
            logging.info(
                '[%d/%d] %d/%d %s专利已经爬取结束，花费%.2fs' % (pid, NUM_WORKERS, count, all, patent, end_time - start_time))
            print('[%d/%d] %d/%d %s专利已经爬取结束，花费%.2fs' % (pid, NUM_WORKERS, count, all, patent, end_time - start_time))

            # output_queue.put(info)

            with open('output.txt', 'a', encoding='utf-8') as f:
                f.write(SEP.join([re.sub(r'[\t\n]', ' ', info[key]).strip() for key in OUTPUT_SEQ]) + '\n')

        except Exception as e:
            logging.error('[%d/%d] %s专利信息抓取错误，url : %s' % (pid, NUM_WORKERS, patent, res.url))
            print('[%d/%d] %s专利信息抓取错误，url : %s' % (pid, NUM_WORKERS, patent, res.url))
            logging.exception(e)

    output_queue.put(1)


if __name__ == '__main__':
    manager = multiprocessing.Manager()
    input_queue = manager.Queue()
    output_queue = manager.Queue()

    seen = set()

    with open('output_20220910.txt', 'r', encoding='utf-8') as f:
        while 1:
            line = f.readline()
            if not line:
                break
            else:
                line = line.split('\t')
                seen.add(line[0])

    with open('output_2.txt', 'r', encoding='utf-8') as f:
        while 1:
            line = f.readline()
            if not line:
                break
            else:
                line = line.split('\t')
                seen.add(line[0])

    with open('./Final-Sample_patent_1985-1999.txt', 'r') as f:
        for patent in f.read().split('\n'):
            if patent not in seen:
                input_queue.put(patent)

    num_of_input = input_queue.qsize()

    with open('output.txt', 'w', encoding='utf-8') as f:
        f.write(SEP.join(OUTPUT_SEQ) + '\n')

    logging.info('[main] 预处理完毕，开始启动子进程')
    process(input_queue, output_queue, 1)

    # pool = multiprocessing.Pool(NUM_WORKERS)
    # for i in range(NUM_WORKERS):
    #     pool.apply(process, args=(input_queue, output_queue, i + 1))
    # pool.close()

    logging.info('[main] 子进程启动完毕')

    # finish_count = worker_count = 0
    #
    # while 1:
    #     if not output_queue.empty():
    #         con = output_queue.get()
    #         if isinstance(con, int):
    #             worker_count += con
    #             if con == NUM_WORKERS:
    #                 break
    #         elif isinstance(con, dict):
    #             with open('output.txt', 'a', encoding='utf-8') as f:
    #                 f.write(SEP.join([re.sub(r'[\t\n]', ' ', con[key]) for key in OUTPUT_SEQ]) + '\n')
    #             finish_count += 1
    #             logging.info('[main] %d/%d 已经抓取完毕' % (finish_count, num_of_input))
    #         else:
    #             raise TypeError('Unavailable Type!')
