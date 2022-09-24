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
    # return [clear_str(i.split('/')[1]) for i in filter(None, s.split('|'))]

    # 04166856-3|04072748-3|04166856-4|03868457-2
    # Durant, Graham J. | Ganellin, Charon R. | Owen, Geoffrey R. | Young, Rodney C.
    return [clear_str(i) for i in filter(None, s.split('|'))]


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
    clustering = nx.clustering(G)
    clustering_weight = nx.clustering(G, weight='weight')
    try:
        res['clustering_without_zero'] = nx.average_clustering(G, count_zeros=False)
    except ZeroDivisionError:
        res['clustering_without_zero'] = 0
    res['clustering_coefficient'] = sum((clustering.get(node) for node in clustering.keys())) / num_of_graph_nodes
    res['clustering_weight'] = sum(
        (clustering_weight.get(node) for node in clustering_weight.keys())) / num_of_graph_nodes
    res['average_path_length'] = get_average_shortest_path_length(G)
    res['density'] = nx.density(G)

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


def bfs_two_layer(G, node):
    """
    返回直接关系与间接关系
    """
    neighbors = set()
    for n in G.neighbors(node):
        neighbors.add(n)
        yield [node, n]
    for neighbor in neighbors:
        for n in G.neighbors(neighbor):
            if n == node:
                continue
            yield [neighbor, n]


def bfs_one_layer(G, node):
    """
    只返回直接关系
    """
    for n in G.neighbors(node):
        yield [node, n]


def cal_graph_weight_matrix(G, layer):
    """
    计算权重矩阵，需要知道要的是单层图还是双层图
    """
    if layer == 1:
        # 单层图的话就用只计算直接关系函数且直接关系权重不需要乘以2/3
        bfs = bfs_one_layer
        mult_index = 1
    elif layer == 2:
        # 双层图的话就用计算直接与间接关系函数且直接关系权重需要乘以2/3
        bfs = bfs_two_layer
        mult_index = 2 / 3
    else:
        # 虽然不可能但是严谨一点哈哈哈 ^(*￣(oo)￣)^
        raise KeyError('layer参数错误！')

    nodes = G.nodes
    weight_matrix = [[0] * len(nodes) for _ in range(len(nodes))]
    # 优化了 node : index 的字典的写法
    node_index = {v: i for i, v in enumerate(nodes)}
    for i, node in enumerate(nodes):
        for edge in bfs(G, node):
            if node in edge:
                edge.remove(node)
                weight_matrix[node_index[node]][node_index[edge[0]]] += G[node][edge[0]]['weight'] * mult_index / 2
                weight_matrix[node_index[edge[0]]][node_index[node]] = weight_matrix[node_index[node]][
                    node_index[edge[0]]]
            else:
                # 如果单层图的话就不会进入这里
                weight_matrix[node_index[node]][node_index[edge[1]]] += G[node][edge[0]]['weight'] / 2 / 3 / 2
                weight_matrix[node_index[edge[1]]][node_index[node]] = weight_matrix[node_index[node]][
                    node_index[edge[1]]]

                weight_matrix[node_index[node]][node_index[edge[1]]] += G[edge[0]][edge[1]]['weight'] / 2 / 3 / 2
                weight_matrix[node_index[edge[1]]][node_index[node]] = weight_matrix[node_index[node]][
                    node_index[edge[1]]]

    return weight_matrix, node_index


def cal_weight_matrix_index(relation, weight_matrix, node_index):
    """
    计算一个primary_key的参数
    :param relation: 预处理读取的所有关系
    :param weight_matrix: 权重矩阵（不区分单层还是双层）
    :param node_index: 权重矩阵的 node : index 的字典
    :return: 这里好多种算法一一说一下：
        1. result_sum_divide : 对于不同的cited_patent，所有关系先求和然后除以关系数量
        2. result_divide_sum : 对于不同的cited_patent，先求和这个cited_patent的关系，然后除以这个cited_patent的关系数量；然后不同的cited_patent之间计算出来的值求和
        3. result_sum_divide_except_null : 同算法1，但是分母关系中排除了一个节点不在图中这种关系
        4. result_divide_sum_except_null : 同算法2，但是每个cited_patent除以的时候分母关系排除了一个节点不在图中这种关系
    """
    result_sum_divide = result_divide_sum = result_sum_divide_except_null = result_divide_sum_except_null = 0
    count_sum_divide = count_sum_divide_except_null = 0

    for links in relation:
        # 一个links代表一个cited_patent
        links_sum = 0
        count_divide_sum_except_null = 0
        for v, u in links:
            try:
                links_sum += weight_matrix[node_index[v]][node_index[u]]
                count_sum_divide_except_null += 1
                count_divide_sum_except_null += 1
            except KeyError:
                links_sum += 0
        result_sum_divide += links_sum
        result_sum_divide_except_null += links_sum

        count_sum_divide += len(links)

        if count_divide_sum_except_null:
            result_divide_sum_except_null += links_sum / count_divide_sum_except_null

        if len(links):
            result_divide_sum += links_sum / len(links)

    if count_sum_divide:
        result_sum_divide /= count_sum_divide
    result_sum_divide /= len(relation)

    if count_sum_divide_except_null:
        result_sum_divide_except_null /= count_sum_divide_except_null
    result_sum_divide_except_null /= len(relation)

    return result_sum_divide, result_divide_sum, result_sum_divide_except_null, result_divide_sum_except_null
