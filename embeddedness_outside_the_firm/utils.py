# -*- coding: utf-8 -*-
"""
Created on Thu Mar 10 14:35:31 2022

@author: FreeA7

3月10日帮你写的，功能是：
    后续各个网络的通用函数
"""

import networkx as nx
from itertools import combinations
from collections import defaultdict
import re


def clear_str(s):
    """
    将字符串中的非字母数字全部删除，用于：
        1. 外国名字净化处理
        2. 美国分类（已划分）净化处理
    """
    return re.sub(r'[^a-z0-9]', '', s.lower())


def split_name(s):
    """
    对发明人这样的字符串进行处理
    将字符串按序进行以下操作：
        1. 按照 | 进行分隔成列表（split）
        2. 删除列表中的空字符串（filter）
        3. 将列表中的字符串都进行净化（clear_str)
    """
    return [clear_str(i) for i in filter(None, s.split('|'))]


def split_class(s):
    """
    对美国分类（已划分）这样的字符串进行处理：
     将字符串按序进行以下操作：
        1. 按照 | 进行分隔成列表（split）
        2. 删除列表中的空字符串（filter）
        3. 将列表中的字符串使用 / 进行分隔并取第2个字符串，并将字符串净化（clear_str）
    """
    return [clear_str(i.split('/')[1]) for i in filter(None, s.split('|'))]


def split_line(line, sep):
    """
    将一行文本以分隔符sep切分成列表，[-1]是为了去除每一行末尾的换行符\n
    """
    return line[:-1].split(sep)


def get_field(field_name, line, headers):
    """
    以headers为索引，获取line这一行中列名为field_name的值
    :param field_name: 需要取值的列名
    :param line: 这一行的list
    :param headers: 列名 => 列index 的索引dict
    :return: 目标值
    """
    return line[headers[field_name]]


def num2str(i):
    """
    将计算结果转换为字符串便于写入文件
    """
    if isinstance(i, float):
        # 浮点类型的转换为保留三位
        return '%.3f' % i
    elif isinstance(i, int):
        # 整型直接返回
        return str(i)
    elif not i:
        # i不存在则返回0
        return str(0)
    else:
        # 除 浮点型/整型/空值 外不做任何处理
        return i


def build_graph(G, nodes):
    """
    向图G添加nodes之间的两两关系
    也就是nodes中每两个node之间都增加一个边或者对现存的边增加权重1
    """
    if len(nodes) == 1:
        # 如果只有一个点则只增加这个点，不增加边
        if not G.has_node(nodes[0]):
            G.add_node(nodes[0])
    # 使用组合获取边
    for link in combinations(nodes, 2):
        for node in link:
            if not G.has_node(node):
                G.add_node(node)
        u, v = link
        if G.has_edge(u, v):
            G[u][v]['weight'] += 1
        else:
            G.add_weighted_edges_from([(u, v, 1)])


def get_average_shortest_path_length(G):
    """
    获取图G的平均最短路径长度的指标
    是按照我们讨论的，对平均最短路径求倒数
    这样1就是代表图的平均路径长度无限大
    越接近0就说明平均路径长度越小，关系越密切
    所以确切的说这里求的不是平均最大长度，而是可以指示平均最大长度的指标
    这么算的原因是networkx并不支持点和点之间没有连接，也就是长度无限长的图的平均最大长度的计算
    """
    path_sum = 0
    for i, j in combinations(G.nodes, 2):
        # 判断是否存在路径，如果存在则求和
        if nx.has_path(G, i, j):
            path_sum += 1 / nx.shortest_path_length(G, i, j)
    if len(G.nodes) > 1:
        return path_sum / (len(G.nodes) * (len(G.nodes) - 1))
    else:
        return 1


def cal_one_layer_graph_index(G, nodes):
    """
    计算单层图的指数
    单层图：只计算节点直接连接的权重信息，不计算间接连接的信息
    """
    res = defaultdict(int)

    # 基础信息
    num_of_graph_nodes = len(G.nodes)
    num_of_nodes = len(nodes)

    if not num_of_graph_nodes:
        return res

    # 图通用信息
    # clustering = nx.clustering(G)
    # clustering_weight = nx.clustering(G, weight='weight')
    # try:
    #     res['clustering_without_zero'] = nx.average_clustering(G, count_zeros=False)
    # except ZeroDivisionError:
    #     res['clustering_without_zero'] = 0
    # res['clustering_coefficient'] = sum((clustering.get(node) for node in clustering.keys())) / num_of_graph_nodes
    # res['clustering_weight'] = sum(
    #     (clustering_weight.get(node) for node in clustering_weight.keys())) / num_of_graph_nodes
    # res['average_path_length'] = get_average_shortest_path_length(G)
    # res['density'] = nx.density(G)

    # 一个人发明专利
    if num_of_nodes == 1:
        return res

    # 节点信息
    centrality = nx.degree_centrality(G)
    weight_centrality = G.degree(weight='weight')
    between_centrality = nx.betweenness_centrality(G, normalized=False)
    between_centrality_normal = nx.betweenness_centrality(G)
    closeness_centrality = nx.closeness_centrality(G)

    # 目标节点指标计算
    res['degree_centrality_normal'] = sum((centrality.get(node) for node in nodes)) / num_of_nodes
    res['degree_centrality'] = sum((centrality.get(node) for node in nodes)) / num_of_nodes * (num_of_graph_nodes - 1)
    res['degree_centrality_weight'] = sum((weight_centrality[node] for node in nodes)) / num_of_nodes
    res['between_centrality'] = sum((between_centrality.get(node) for node in nodes)) / num_of_nodes
    res['between_centrality_normal'] = sum((between_centrality_normal.get(node) for node in nodes)) / num_of_nodes
    res['closeness_centrality_nx_normal'] = sum(closeness_centrality.get(node) for node in nodes) / num_of_nodes
    if res['closeness_centrality_nx_normal']:
        res['closeness_centrality'] = (num_of_graph_nodes - 1) / res['closeness_centrality_nx_normal']
        res['closeness_centrality_smy_normal'] = 1 / res['closeness_centrality_nx_normal']
    else:
        res['closeness_centrality'] = res['closeness_centrality_smy_normal'] = 0

    return res


def bfs(G, node):
    """
    获取所有直接与间接连接的关系
    """
    # 使用set可以自动去重
    neis = set()
    for n in G.neighbors(node):
        # 直接关系
        neis.add(n)
        # yield 可以理解为 return，但是相当于逐次返回，可以把这个函数变成一个可迭代对象
        yield (node, n)
    for ne in neis:
        for n in G.neighbors(ne):
            # 直接关系的直接关系 => 间接关系
            if n == node:
                continue
            yield (ne, n)


"""
计算两层图的指标的函数，本来也想放在这，后来那个就算了一次，就没迁移了
"""
# def cal_two_layer_graph_index(G, nodes, primey_key, output_queue):
#     output_queue.put('开始计算权重 %s' % primey_key)
#     G_weight_matrix = [[0] * len(nodes) for _ in range(len(nodes))]
#     node_index = dict(zip(nodes, range(len(nodes))))
#
#     for i, node in enumerate(nodes):
#         for edge in bfs(G, node):
#             edge = list(edge)
#             if node in edge:
#                 edge.remove(node)
#                 G_weight_matrix[node_index[node]][node_index[edge[0]]] += G[node][edge[0]]['weight'] * 2 / 3 / 2
#                 G_weight_matrix[node_index[edge[0]]][node_index[node]] += G[node][edge[0]]['weight'] * 2 / 3 / 2
#             else:
#                 G_weight_matrix[node_index[node]][node_index[edge[1]]] += G[node][edge[0]]['weight'] / 2 / 3 / 2
#                 G_weight_matrix[node_index[edge[1]]][node_index[node]] += G[node][edge[0]]['weight'] / 2 / 3 / 2
#
#                 G_weight_matrix[node_index[node]][node_index[edge[1]]] += G[edge[0]][edge[1]]['weight'] / 2 / 3 / 2
#                 G_weight_matrix[node_index[edge[1]]][node_index[node]] += G[edge[0]][edge[1]]['weight'] / 2 / 3 / 2
#
#     output_queue.put('权重计算完毕 %s' % primey_key)
#     G_weight_matrix = cal_weight(G_weight_matrix, p, node_index)
#     logging.info('权重为%.3f|%.3f %s——%s' % (G_weight[0], G_weight[1], p.id, p.company))
#     output.put('权重为%.3f|%.3f %s——%s' % (G_weight[0], G_weight[1], p.id, p.company))
#     logging.debug(G_output)
#     return G_weight
#
#
# def cal_weight(G_output, p, node_index):
#     sum_weight_all = 0
#     sum_weight_not_null = 0
#     logging.debug(p.references_inventors)
#     for references_inventors in p.references_inventors:
#         reference_weight = 0
#         count = 0
#         for i in p.focal_patent_inventors:
#             for j in references_inventors:
#                 logging.debug((i, j))
#                 try:
#                     weight = G_output[node_index[i]][node_index[j]]
#                     reference_weight += weight
#                     if weight:
#                         count += 1
#                 except KeyError:
#                     pass
#         if not reference_weight:
#             continue
#         else:
#             sum_weight_all += reference_weight / (len(p.focal_patent_inventors) * len(references_inventors))
#             sum_weight_not_null += reference_weight / count
#     return (sum_weight_all, sum_weight_not_null)
