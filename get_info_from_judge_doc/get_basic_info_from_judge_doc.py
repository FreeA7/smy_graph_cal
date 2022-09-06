# -*- coding: utf-8 -*-
"""
Created on Sat Mar  5 23:08:06 2022

@author: FreeA7

3月5日帮你写的，功能是：
    从判决书中获取
        1. 判决号
        2. 法院
        3. 案名
        4. 审判时间
    这四个是有相对来说固定格式的基本信息，所以可以用代码获取
    其中docx是三方包，需要安装：
        pip3 install python-docx
    总结一下这个代码完全是特征匹配，一遍又一遍debug完善异常情况写的，比较麻烦
"""

import os
import re
from docx import Document

# 我习惯最开始将分隔符设置为全局变量，便于修改
SEP = '\t'

file_list = []
abs_path = os.path.abspath('./data') + '/'
for root, dirs, files in os.walk('./data/'):
    for f in files:
        # 获取docx，但是~开头的说明是打开docx看的时候word自动生成的临时文件，进行排除
        if f.endswith('.docx') and not f.startswith('~'):
            file_list.append(abs_path + f)


def para_pre_handle(p):
    """
    将段落p格式化：
        将p转换成小写
        并将其中的Tab制表符全部删除，防止与全局分隔符冲突
    """
    return re.sub(r'\t', '', p.text.lower())


for file in file_list:
    document = Document(file)
    all_paragraphs = document.paragraphs

    # 我一个一个总结出来的日期格式，用正则表达式表示
    date_patterns = [r'[a-z]{3}\. \d{1,2}, \d{4}\.',
                     r'\d{1,2}\/\d{1,2}\/\d{4}',
                     r'[a-z]+ \d{1,2}, \d{4}']

    date = ''
    # [9:55]这个段落范围是我一个一个debug测试出来的，也就是所有的判决日期都是在第10段到第55段
    for date_i, p in enumerate(all_paragraphs[9:55]):
        p_con = para_pre_handle(p)
        # 格式化后段落如果有文本
        if p_con:
            # 使用日期格式的每一个去匹配查看是否存在日期
            for pattern in date_patterns:
                res = re.search(pattern, p_con)
                if res:
                    date = res.group()
                    break
            if date:
                break
    # 由于使用[9:55]进行遍历，所以只有加上9才是all_paragraphs中的真实index
    date_i += 9

    # 如果日期此时为空，说明日期不在[9:55]，而是在[:9]，即第10段之前
    if not date:
        for date_i, p in enumerate(all_paragraphs[:9]):
            p_con = para_pre_handle(p)
            if p_con:
                for pattern in date_patterns:
                    res = re.search(pattern, p_con)
                    if res:
                        date = res.group()
                        break
                if date:
                    break
    """
    上边为什么要先遍历[9:55]，后[:9]：
        发现符合日期格式的不止判决日期，可能会有其他的日期
        尤其干扰项都存在在第10段之前
        所以我们优先去取[9:55]的时间，这个范围内没有再去取[:9]
        经过我的测试，你发我的所有判决书都适用
    """

    # 我一个一个总结出来的判决号格式，用正则表达式表示
    id_patterns = [r'nos\.',
                   r'no\.',
                   r'no:',
                   r'\d{4}[–-]\d{4}',
                   r'\d+-cv',
                   r'cv \d+',
                   r'\d+ civ\.',
                   r'c\.a\. \d+']

    idd = ''
    # 经测试发现所有的判决号都在日期之前，所以遍历范围为[:date_i]
    for id_index, p in enumerate(all_paragraphs[:date_i]):
        p_con = para_pre_handle(p)
        if p_con:
            # 使用判决号格式的每一个去匹配查看是否存在判决号
            for pattern in id_patterns:
                res = re.search(pattern, p_con)
                if res:
                    idd = p.text
                    break
            if idd:
                break

    # 一个一个总结出来的判决法院格式，用正则表达式表示
    court_special = ['united states district court',
                     'united states court of',
                     'supreme court of the united states',
                     'united states judicial panel on multidistrict litigation.']

    court = ''
    # 经测试发现所有的判决法院都在判决号之前，所以遍历范围为[:id_index]
    for court_index, p in enumerate(all_paragraphs[:id_index]):
        p_con = para_pre_handle(p)
        if p_con:
            # 使用判决法院格式的每一个去匹配查看是否存在判决法院
            for c in court_special:
                if c in p_con:
                    court = p.text
                    break
            if court:
                break

    # 发现法院名称可能写多行，这种情况都是以逗号结尾，将所有的名称连上
    while court and court.endswith(','):
        court += all_paragraphs[court_index + 1].text
        court_index += 1

    title = ''
    # 经测试发现判决法院和判决号之间一定是案名
    for p in all_paragraphs[court_index + 1:id_index]:
        title += p.text + ' '

    with open('./output.txt', 'a', errors='ignore') as f:
        f.write(os.path.basename(file) + SEP + idd + SEP + date + SEP + court + SEP + title + '\n')
