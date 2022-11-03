# -*- coding: utf-8 -*-
"""
Created on Mon Mar  7 00:23:22 2022

@author: FreeA7

3月7日帮你写的，功能是：
    将你发的所有doc转换为docx，因为python包只支持docx的处理
    其中win32com为三方包，需要进行安装：
        pip3 install pypiwin32
"""


from win32com import client as wc
from time import sleep
import os


def doSaveAas(file_name):
    """
    网上找的固定写法，不需要修改
    功能是在原doc目录下转换成新的docx
    """
    word = wc.Dispatch('Word.Application')
    # 踩坑记录：这里的文件名必须传入绝对路径，相对路径会报错
    doc = word.Documents.Open(file_name)
    file_name += 'x'
    # 踩坑记录：这里的文件名必须传入绝对路径，相对路径会报错
    doc.SaveAs(file_name, 12, False, "", True, "", False, False, False, False)  
    doc.Close()
    word.Quit()
    return file_name


if __name__ == '__main__':
    file_list = []
    abs_path = os.path.abspath('./data') + '/'
    for root, dirs, files in os.walk('./data/'):
        for f in files:
            # 判断是否是doc文件
            if f.endswith('.doc'):
                file_list.append(abs_path + f)
    
    for file in file_list:
        file = doSaveAas(file)
        '''
        踩坑记录：每个文件转换后需要sleep
        因为是异步执行的，如果没执行完就执行下一个就会报错，经统计基本1s都能转换完
        '''
        sleep(1)