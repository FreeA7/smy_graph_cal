# -*- coding: utf-8 -*-
"""
Created on Fri Feb 11 17:38:07 2022

@author: FreeA7

2月13日帮你写的，功能是：
    爬取 https://patft.uspto.gov/netahtml/PTO/search-adv.htm 网站的搜索结果中的结果数量
    使用的技术是直接截获请求结果，使用python的三方包requests，如果执行代码时报错，可以用以下命令安装：
        pip3 install requests
"""

import requests
import re
import time

# 使用Session可以默认配置cookies，防止没有cookies导致请求被拦截
s = requests.Session()

'''
设置headers，此网站会对headers中关键字段进行校验
很多网站如果你使用requests进行请求如果返回为空或者返回结果非200，那么很有可能是headers检验拦截了
实际操作中你可以直接在浏览器中访问网站时按F12，查看浏览器默认配置的headers，然后直接复制过来放在这里就可以使用，比如我这里就是直接复制我的浏览器里的
不过其中的关键字段是：Host、Referer、User-Agent
'''
headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,'
              'application/signed-exchange;v=b3;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7',
    'Connection': 'keep-alive',
    'Host': 'patft.uspto.gov',
    'Referer': 'https://patft.uspto.gov/netahtml/PTO/search-adv.htm',
    'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="97", "Chromium";v="97"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/97.0.4692.99 Safari/537.36'}

'''
这里直接访问首页目的是：
使用Session进行访问主页，此时如果网页是带cookies校验的话，Session会从首页返回的cookies中进行获取配置
那么后续访问其他查询页面的时候，会带着从主页获取的cookies，防止被校验住
这个网站没有检验cookies，所以其实这个访问对于这个爬虫是没有必要的
但是如果你爬取其他网站的时候，可以写上这个，万一校验了我们也有配置，不会被拦截，所以我是写习惯了，在这里留了这个
'''
s.get('https://patft.uspto.gov/netahtml/PTO/search-adv.htm', headers=headers)

# 使用with语句进行文件IO操作比较方便，而且会自动进行close，防止文件句柄不正常关闭
with open('input.csv', 'r', encoding='utf-8') as f:
    # 将文件中的内容读取为列表，其中[:-1]是为了去除切分后最后一个空值
    keys = f.read().split(',\n')[:-1]

with open('output.csv', 'w', encoding='utf-8') as f:
    # 当时你说后边的有值前边的基本都是空值，所以为了验证代码是否正确所以我是倒叙查找的[::-1]就是从后向前遍历的意思
    for key in keys[::-1]:
        # 加上try catch是当时你说有部分查询出来结果是错的，我就把这些排除掉了
        try:
            '''
            payload 访问参数
            如 https://patft.uspto.gov/netacgi/nph-Parser?Sect1=PTO2&Sect2=HITOFF&u=%2Fnetahtml%2FPTO%2Fsearch-adv.htm&r=0&p=1&f=S&l=50&Query=CCL%2F424%2F643+AND+ISD%2F1%2F1%2F1996-%3E12%2F31%2F1996%0D%0A&d=PTXT
            其中 url为https://patft.uspto.gov/netacgi/nph-Parser
            ? 后边都是参数，参数之间使用&进行分割： Sect1=PTO2&Sect2=HITOFF&u=%2Fnetahtml%2FPTO%2Fsearch-adv.htm&r=0&p=1&f=S&l=50&Query=CCL%2F424%2F643+AND+ISD%2F1%2F1%2F1996-%3E12%2F31%2F1996%0D%0A&d=PTXT
            这里就有：
                Sect1=PTO2
                Sect2=HITOFF
                u=%2Fnetahtml%2FPTO%2Fsearch-adv.htm
                ...
            其中参数值中有很多 %xx 都是url特有的转义符，如 / 会转换成 %2F
            python的requests模块会自动将文本中需要转义的自动转义，所以无需手动替换
            对于有参数的访问，可以多访问几个网页，通过参数值的变化推测参数的含义，比如这里我发现不同的查询只有Query不同，所以我只需要给这个参数传入对应的值即可
            '''
            payload = {
                'Sect1': 'PTO2',
                'Sect2': 'HITOFF',
                'u': '/netahtml/PTO/search-adv.htm',
                'r': '0',
                'p': '1',
                'f': 'S',
                'l': '50',
                'Query': key,
                'd': 'PTXT'}
            start_time = time.time()
            # 注意要使用Session带着headers和payload访问
            res = s.get('https://patft.uspto.gov/netacgi/nph-Parser', headers=headers, params=payload)
            end_time = time.time()
            print('%d s : % s' % (end_time - start_time, res.url))
            res = res.text
            # 无查询结果
            if 'No patents have matched your query' in res:
                f.write(key + ',0\n')
                print('%s %d' % (key, 0))
            # 只有一篇
            elif '<TITLE>Single Document</TITLE>' in res:
                f.write(key + ',1\n')
                print('%s %d' % (key, 1))
            # 有不止一篇
            else:
                # 发现这里的格式是固定的，那么就可以直接使用正则表达式进行匹配，获取结果；如果内容复杂则可以使用BeautifulSoup对HTML进行解析，获取需要的结果
                res = str(re.search(
                    r'Hits <strong>(\d+)</strong> through <strong>(\d+)\n</strong> out of <strong>(\d+)</strong>',
                    res).group(3))
                f.write(key + ',' + res + '\n')
                print('%s %s' % (key, res))
            '''
            每次写入都将内容从缓存刷新到文件里，那么文件内容会实时更新
            否则文件只有在缓存区满/文件IO关闭的时候才会将内容从缓存写入文件，那么看到的文件内容就不是实时刷新的
            我写这个就只是为了看结果方便，便于调试
            '''
            f.flush()
        except:
            continue
