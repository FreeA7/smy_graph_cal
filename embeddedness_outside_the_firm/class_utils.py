# -*- coding: utf-8 -*-
"""
Created on Tue Mar 15 00:25:29 2022

@author: FreeA7

类似于之前的，一个namedtuple，其实就是个类，懒得定义类就用这个
"""


from collections import namedtuple

Patent = namedtuple('Patent', ['patent', 'pdpass', 'inventors'])