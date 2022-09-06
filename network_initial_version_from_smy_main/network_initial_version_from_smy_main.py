# -*- coding: utf-8 -*-
"""
Created on Fri Feb 18 20:15:21 2022

@author: FreeA7

2月18日帮你写的，功能是：
    把你给我的main.py改成多进程，加快你计算网络的速度
    原始数据在./data中，有好几千个excel。当时跑完我觉得占空太大了就给删了
"""


import pandas as pd
import networkx as nx
import os
from itertools import combinations
from collections import Counter, defaultdict
import multiprocessing


# 默认8进程
NUM_WORKERS = 8
OUTPUT_NAME = 'Network Output_2001-2004.xlsx'


def worker(args):
    """
    你的原始代码，来自main.py，完全没改动
    """
    file_wait_handle = args[0]
    """
    defaultdict是默认字典，普通的字典需要先给key放入value后才能取值，默认字典设置默认值，这样即使没有给key放入过value，直接调用key也会获取到默认值
    比如这里defaultdict(list)，默认值为list，也就是任何一个key都会获取到一个空的list，那么后续就可以直接使用key获取值后进行append，不用value初始化
    """
    data = defaultdict(list)
    data_s = defaultdict(list)
    while not file_wait_handle.empty():
        file = file_wait_handle.get()
        G = nx.Graph()
        # 我定位出来的dtype的bug，^_^
        df = pd.read_excel(file, sheet_name=0, dtype=str)
        name = list(df['Y&G&RP'])[0]
        links = []
        node_all = []
        cl = df.columns.values
        start_box = 0
        for i in range(df.shape[1]):
            if cl[i] == 'ego':
                start_box = i + 1
                break
        for row in df.itertuples():
            L = []
            for i in range(start_box, df.shape[1]):
                if str(row[i]) != 'nan':
                    L.append(str(row[i]))
            node_all += L
            if len(L) > 1:
                combi = list(combinations(L, 2))
                for l in combi:
                    if l[0] > l[1]:
                        links.append(l[1] + '-' + l[0])
                    else:
                        links.append(l[0] + '-' + l[1])
        node_all = list(set(node_all))
        for n in node_all:
            G.add_node(n)
        LL = dict(Counter(links))
        LLL = []
        for l in LL:
            LLL.append((l.split('-')[0], l.split('-')[1], LL[l]))
        G.add_weighted_edges_from(LLL)
        length = 0
        k = 0
        for n in G.nodes():
            l = nx.shortest_path_length(G, source=n)
            for nn in l:
                if nn > n and l[nn] > 0:
                    length += l[nn]
                    k += 1
        if k > 0:
            length = length / k
        try:
            cluster1 = nx.average_clustering(G)
        except:
            cluster1 = 0
        try:
            cluster2 = nx.average_clustering(G, count_zeros=False)
        except:
            cluster2 = 0
        degree = nx.degree_centrality(G)
        weight_degree = nx.degree(G, weight='weight')
        B = nx.betweenness_centrality(G)
        BB = nx.betweenness_centrality(G, normalized=False)
        C = nx.closeness_centrality(G)
    
        for n in node_all:
            # '网络名称' 这个 key没有被初始化，但是可以直接调用然后append，就是因为默认值是空的list
            data['网络名称'].append(name)
            data['节点（专利子类）名称'].append(n)
            data['Network average path length'].append(length)
            data['Network clustering (1)'].append(cluster1)
            data['Network clustering (2)'].append(cluster2)
    
            if n in G.nodes():
                data['Degree centrality (非标准化的)'].append(nx.degree(G, n))
                data['Degree centrality (标准化的)'].append(degree[n])
                data['Weighted degree centrality'].append(weight_degree[n])
                data['betweenness centrality'].append(BB[n])
                data['betweenness centrality normalized'].append(B[n])
                data['closeness centrality'].append(C[n])
            else:
                data['Degree centrality (非标准化的)'].append(0)
                data['Degree centrality (标准化的)'].append(0)
                data['Weighted degree centrality'].append(0)
                data['betweenness centrality'].append(0)
                data['betweenness centrality normalized'].append(0)
                data['closeness centrality'].append(0)
    
        for item in list(df['PatentN']):
            data_s['网络名称'].append(name)
            data_s['专利名称'].append(str(item))
            data_s['Network average path length'].append(length)
            data_s['Network clustering (1)'].append(cluster1)
            data_s['Network clustering (2)'].append(cluster2)

    return (data, data_s)

    
if __name__ == '__main__':
    """
    我这里使用Queue进行进程间通信，需要是主进程和子进程之间的通信
    Queue是一个队列，先进先出，也就是先进入的数据会先处理，即按顺序处理
    多进程之间的Queue要使用multiprocessing提供的Manager进行初始化
    """
    manager = multiprocessing.Manager()
    file_wait_handle = manager.Queue()
    for root, dirs, files in os.walk('./data'):
        for file in files:
            if file.endswith('.xlsx'):
                # 将需要处理的excel逐个塞入Queue队列，后续每个进程只需要从Queue中取数据即可
                file_wait_handle.put('./data/' + file)

    # 使用进程池Pool进行进程初始化
    with multiprocessing.Pool(NUM_WORKERS) as p:
        # p.map是同步进程，也就是主进程会等子进程全部处理完成后在继续向后运行
        output = p.map(worker, [(file_wait_handle,) for _ in range(NUM_WORKERS)])

    data = defaultdict(list)
    data_s = defaultdict(list)

    # 把每一个进程返回的结果合并到一个dict中
    for d, ds in output:
        for key in d.keys():
            data[key] += d[key]
        for key in ds.keys():
            data_s[key] += ds[key]

    # 生成excel
    d_data = pd.DataFrame(data)
    d_data_s = pd.DataFrame(data_s)
    writer = pd.ExcelWriter(OUTPUT_NAME)
    d_data.to_excel(writer, sheet_name='nodes', index=False)
    d_data_s.to_excel(writer, sheet_name='专利', index=False)
    writer.save()
    
    