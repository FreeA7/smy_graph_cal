# -*- coding: utf-8 -*-
"""
Created on Mon Mar  7 23:32:16 2022

@author: FreeA7

3月5日帮你写的，功能是：
    从判决书中获取除了基础信息外你要的所有信息：
        1. synopsis
        2. memorandum
        3. patent
        4. plaintiff
        5. defendant
    但是由于例外情况很多，代码已经完成但是准确率一言难尽，所以放弃使用
    不过其中的代码可以参考学习
    获取基础信息时我们对所有字段所处的大致位置是有预期的，所以是对预期范围字段进行遍历
    这里的5个信息可能存在在任意一个段落中，所以要逐一段落进行遍历，规则严格按照了你的说明：
    --------------------------------------------------------------------------------------------------
        我现在是要从这种文件中提取一些特定的段落和文字出来，总结了一下大概是这样子：
        1.有无synosis，若有，提取synosis后面的段落
        2.有无memorandum/opinion/District Judge，若有，提取memorandum/opion后面的首段
        3.按照单词
        (1) 出现"U.S. patent(s)"以及数字，且没有"U.S. Patent and Trademark Office"或"United States Patent and Trademark Office"的第一段，提取段落和"U.S. patent(s)"所在的句子
        (2) 出现"United States patent(s)"以及数字，且没有"U.S. Patent and Trademark Office"或"United States Patent and Trademark Office"的第一段，提取段落和"United States patent(s)"所在的句子
        (3) 出现"patent(s) No."以及数字，且没有"U.S. Patent and Trademark Office"或"United States Patent and Trademark Office"的第一段，提取段落和"Patent(s) No."所在的句子
        4.提取其他信息：
        (1) 标题及日期
        (2) 第一次出现plaintiff(s)且不是"for plaintiff(s)"的段落
        (3) 第一次出现defendant(s)且不是"for defendant(s)"的段落
    --------------------------------------------------------------------------------------------------
"""


import os
import re
from docx import Document


SEP = '\t'


file_list = []
abs_path = os.path.abspath('./data') + '/'
for root, dirs, files in os.walk('./data/'):
    for f in files:
        if f.endswith('.docx') and not f.startswith('~'):
            file_list.append(abs_path + f)


def para_pre_handle(p):
    return re.sub(r'\t', '', p.text.lower())


count = 0

for file in file_list:
    document = Document(file)
    all_paragraphs = document.paragraphs
    
    synopsis = ''
    memorandum = ''
    patent = ''
    plaintiff = ''
    defendant = ''
    for i, p in enumerate(all_paragraphs):
        p = re.sub(r'\t', ' ', p.text)
        p_lower = p.lower()

        # synopsis值为空，且本段包含synopsis，那么取下一段为结果
        if not synopsis and 'synopsis' in p_lower:
            synopsis = all_paragraphs[i + 1].text
        
        if not plaintiff and 'plaintiff' in p_lower and 'for plaintiff' not in p_lower:
            plaintiff = p
            
        if not defendant and 'defendant' in p_lower and 'for defendant' not in p_lower:
            defendant = p
            
        if not memorandum and ('memorandum' in p_lower or 'district judge' in p_lower):
            memorandum = p
          
        if not patent:
            patent_re_res = re.search(r'u\.s\. patents{0,1} \d+', p_lower)
            if patent_re_res and 'u.s. patent and trademark office' not in p_lower and 'united states patent and trademark office' not in p_lower:
                patent = p
                continue
            
            patent_re_res = re.search(r'united states patents{0,1} \d+', p_lower)
            if patent_re_res and 'u.s. patent and trademark office' not in p_lower and 'united states patent and trademark office' not in p_lower:
                patent = p
                continue
            
            patent_re_res = re.search(r'patents{0,1} no\.\d+', p_lower)
            if patent_re_res and 'u.s. patent and trademark office' not in p_lower and 'united states patent and trademark office' not in p_lower:
                patent = p
                continue
            
    with open('./output.txt', 'a', errors = 'ignore') as f:
        f.write(os.path.basename(file) + SEP + synopsis + SEP + memorandum + SEP + patent + SEP + plaintiff + SEP + defendant + '\n')

