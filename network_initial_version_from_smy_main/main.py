
import pandas as pd
import networkx as nx
import os
from itertools import combinations
from collections import Counter, defaultdict

file_list = []
for root, dirs, files in os.walk('data'):
    for f in files:
        if f.endswith('.xlsx'):
            file_list.append('./data/' + f)

data = defaultdict(list)
data_s = defaultdict(list)

for path in file_list:
    G = nx.Graph()
    df = pd.read_excel(path, sheet_name=0, dtype=str)
    name = list(df['Y&G&RP'])[0]
    links = []
    node_all = []
    for row in df.itertuples():
        L = []
        for i in range(2, df.shape[1]):
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

d_data = pd.DataFrame(data)
d_data_s = pd.DataFrame(data_s)

writer = pd.ExcelWriter('结果.xlsx')
d_data.to_excel(writer, sheet_name='nodes', index=False)
d_data_s.to_excel(writer, sheet_name='专利', index=False)
writer.save()

