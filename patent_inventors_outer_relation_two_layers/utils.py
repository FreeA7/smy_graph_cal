# -*- coding: utf-8 -*-
"""
Created on Fri Feb 25 18:41:22 2022

@author: FreeA7

2月25日帮你写的，功能是：
    定义Patent这个类，便于进程之间通讯使用
    为何要单独拿出来放一个文件是因为只有这样这种自定义的数据结构才能在进程之间通信传递
"""


from collections import namedtuple

"""
这里使用了namedtuple这种数据格式，你可以将这个理解为一个好写和使用的class，等同于：
class Patent:
    def __init__(self, id, time, company):
        self.id = id
        self.time = time
        self.company = company
"""
Patent = namedtuple('Patent', ['id', 'time', 'company', 'focal_patent_inventors', 'cited_patent_inventors', 'references', 'references_inventors'])

