# -*- coding: utf-8 -*-
"""
Created on Thu Feb 24 11:41:51 2022

@author: FreeA7

2月24日帮你写的，功能是：
    第一次写的双层网络（直接+间接）代码：
        将一个专利与其他所有非此公司的专利（focal_patent_inventors）生成一个图
        然后计算这个专利的相关参数（focal_patent_inventors与references_inventors之间两两的直接+间接关系）
    不过当时以为只会写一次，所以可拓展性以及重复利用性比较差
    SEP/NUM_WORKERS/FLUSH_DATA这些全局参数可以像我这样写在最开始
    因为这样后续调试的话修改这些参数就有统一的入口，并不会乱

    这里我使用了多进程的经典形式 master-slover 这里进行以下解释：
        一个主进程master对多个工人进程slover
        主进程和工人进程之间使用Queue进行通信
        我这里主进程负责读取所有要处理的数据，然后启动工人进程
        工人进程将一条Patent处理完成后将结果返回给主进程
        主进程对拿到的结果进行处理后放入output文件
        这样避免了多个子进程都要对同一文件进行操作可能出现的IO异常，也可以不使用锁，好写好debug，对于这种计算密集而非IO密集型的代码非常实用
        所以这里设计了两个Queue，一个input_queue，一个output_queue
        input_queue负责将主进程读取到的需要处理的数据依次传给工人进程进行处理
        output_queue负责将工人进程处理完毕的结果返回给主进程
        我这里所有的子进程在input_queue空了，也就是数据全部处理完成后会向output_queue中放一个整型1
        这里1就代表我这个进程处理完毕了，要结束了
        这样当主进程收到和预设子进程数量相等的1的时候就说明所有进程都处理完毕了，程序可以结束了
        我这里子进程还会向queue中放字符串，这样主进程拿到后可以直接打印出来，知道代码运行状况
        但是其实这里是我比较蠢才用这种办法，其实不用的，充分说明了我当时对多进程编程的不熟悉
"""

SEP = '\t'
NUM_WORKERS = 8
FLUSH_DATA = True

# 我习惯处理csv的数据，所以将你发我的所有excel都转换成txt
if FLUSH_DATA:
    import pandas as pd

    data = pd.read_excel('Sample-FS_2000-2004 with Backward Citation & Inventors.xlsx', sheet_name=0, dtype=str)
    data.to_csv('patent_inventors_input.csv', header=0, sep=SEP, encoding='utf-8', index=0)

    """
    后续有很多代码都会有以下这个结构，目的是判断每一行的数据样式是否是所预计的
    因为我以前总做数据清洗，所以入口数据质量很差，就会用这样的形式进行基础的清洗
    我会把你excel里边认为没有用的数据列删除，留下有用的
    """
    with open('patent_inventors_input.csv', 'r', encoding='utf-8') as f:
        while 1:
            line = f.readline()
            if not line:
                break
            if len(line.split(SEP)) != 562:
                print(line)

import networkx as nx
import logging
import re
from utils import Patent
from itertools import combinations
import multiprocessing

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s',
                    filename='./root.log')


def get_names(s):
    """
    这里第一次写的时候还没有写专门的utils，这里的功能是将发明人拆分
    对传入的字符串依序执行以下操作：
        1. 将字符串以 | 进行拆分为列表（split）
        2. 对拆分后的列表中的每一个字符串依次执行以下操作：
            (1 字符串转换为小写（lower）
            (2 删除字符串中的非字母（re.sub)
        3. 对拆分后的列表去除其中的空值（filter）
        4. 将filter的结果转换为list，filter返回的默认结果是一个可迭代对象，转换为列表便于后续使用
    """
    return list(filter(None, [re.sub(r'[^a-z]', '', i.lower()) for i in s.split('|')]))


def read_line(line):
    """
    这里也比较蠢，将csv中的一行读取出来之后进行拆分
    然后以Patent的形式返回回来
    Patent我是定义在同目录下的utils.py中的，详细可以过去了解
    这里我还使用的是下标的方式获取目标数据，这样你的表发生变化的话下标也需要重新写，很麻烦，是个偷懒的办法
    后边就是用get_field的方法替代了
    """
    line = line.split(SEP)
    return Patent(line[0], line[1], line[2],
                  get_names(line[3]), get_names(line[4]), get_names(line[5]),
                  list(filter(None, [get_names(inventors) for inventors in line[6:]])))


def pre_process(path):
    """
    对数据进行预处理，将每一行都读取成一个Patent对象
    然后使用字典来保存这个对象便于后续使用 patent_id : patent
    """
    data = {}
    logging.debug('开始进行数据预处理')
    with open(path, 'r', encoding='utf-8') as f:
        while 1:
            line = f.readline()
            if not line:
                break
            p = read_line(line)
            data[p.id] = p
    logging.debug('数据预处理结束')
    return data


def process(args):
    """
    多进程实际执行的方法
    """
    all_sheet, lines, output = args
    while not lines.empty():
        G = nx.Graph()
        nodes = []
        line = lines.get()
        # 每一行生成一个Patent，每次从Queue中取出来一个Patent进行生成网络以及计算
        p = read_line(line)
        logging.debug('开始生成图 %s——%s' % (p.id, p.company))
        # 遍历所有的Patent去寻找合适的Patent生成网络
        for patent in all_sheet.keys():
            another_p = all_sheet[patent]
            # 如果同一个公司，那么只有patent_id相同才会计入网络，也就是Patent自己
            if another_p.company == p.company and another_p.id != p.id:
                continue
            # 先添加节点
            for node in another_p.focal_patent_inventors:
                if node not in nodes:
                    G.add_node(node)
                    nodes.append(node)
            # 存在连接的话增加权重，没有的话进行连接
            for link in combinations(another_p.focal_patent_inventors, 2):
                if G.has_edge(link[0], link[1]):
                    G[link[0]][link[1]]['weight'] += 1
                else:
                    G.add_weighted_edges_from([(link[0], link[1], 1)])
        logging.debug('图生成完毕 %s——%s' % (p.id, p.company))
        # 将计算结果返回给主进程通过output这个queue
        output.put((p, get_output(G, nodes, p, output)))
    # 数据全部处理完毕的结束符
    output.put(1)


def bfs(G, node):
    """
    获取所有直接与间接连接的关系
    """
    neis = set()
    for n in G.neighbors(node):
        neis.add(n)
        yield (node, n)
    for ne in neis:
        for n in G.neighbors(ne):
            if n == node:
                continue
            yield (ne, n)


def get_output(G, nodes, p, output):
    """
    计算一个Patent的指标
    """
    logging.debug('开始计算权重 %s——%s' % (p.id, p.company))
    # 初始化一个全部为空的权重矩阵，就是你本来让我生成一个excel那个
    G_output = [[0] * len(nodes) for _ in range(len(nodes))]
    node_index = {}
    for i, node in enumerate(nodes):
        """
        权重矩阵很大，但是每一个node在横坐标和纵坐标的位置都是一致的
        所以这里初始化一个node : index的字典，就可以每次通过node访问这个字典获取这个node的index
        避免每次还得遍历查找，极大地减少了计算量
        """
        node_index[node] = i
    for i, node in enumerate(nodes):
        for edge in bfs(G, node):
            edge = list(edge)
            if node in edge:
                # 如果node在edge中就说明这个是直接关系，这个remove可以不要
                edge.remove(node)
                G_output[node_index[node]][node_index[edge[0]]] += G[node][edge[0]]['weight'] * 2 / 3 / 2
                G_output[node_index[edge[0]]][node_index[node]] += G[node][edge[0]]['weight'] * 2 / 3 / 2
            else:
                # 由于后续计算需要，权重矩阵应该是斜对角线对称的，所以赋值两次
                G_output[node_index[node]][node_index[edge[1]]] += G[node][edge[0]]['weight'] / 2 / 3 / 2
                G_output[node_index[edge[1]]][node_index[node]] += G[node][edge[0]]['weight'] / 2 / 3 / 2

                G_output[node_index[node]][node_index[edge[1]]] += G[edge[0]][edge[1]]['weight'] / 2 / 3 / 2
                G_output[node_index[edge[1]]][node_index[node]] += G[edge[0]][edge[1]]['weight'] / 2 / 3 / 2
    logging.debug('权重计算完毕 %s——%s' % (p.id, p.company))
    G_weight = cal_weight(G_output, p, node_index)
    logging.info('权重为%.3f|%.3f %s——%s' % (G_weight[0], G_weight[1], p.id, p.company))
    output.put('权重为%.3f|%.3f %s——%s' % (G_weight[0], G_weight[1], p.id, p.company))
    logging.debug(G_output)
    return G_weight


def cal_weight(G_output, p, node_index):
    """
    计算这个图的local_patent_inventors与references_inventors之间两两的直接+间接关系的权重
    也就是你最后要的那个东西
    这里两种算法：
        1. 所有关系加和后除以local_patent_inventors的数量乘以references_inventors的数量
        2. 所有关系加和后除以local_patent_inventors和references_inventors在权重矩阵中有两两关系的数量
            （也就是如果图中有这两个节点，那么就算是0，分母也要算上，只有两个节点中有一个节点不在图中才不算在分母中）
    """
    sum_weight_all = 0
    sum_weight_not_null = 0
    logging.debug(p.references_inventors)
    for references_inventors in p.references_inventors:
        reference_weight = 0
        count = 0
        for i in p.focal_patent_inventors:
            for j in references_inventors:
                logging.debug((i, j))
                try:
                    weight = G_output[node_index[i]][node_index[j]]
                    reference_weight += weight
                    if weight:
                        count += 1
                except KeyError:
                    pass
        if not reference_weight:
            continue
        else:
            # 算法 1
            sum_weight_all += reference_weight / (len(p.focal_patent_inventors) * len(references_inventors))
            # 算法 2
            sum_weight_not_null += reference_weight / count
    return (sum_weight_all, sum_weight_not_null)


if __name__ == '__main__':
    all_sheet = pre_process('patent_inventors_input.csv')
    manager = multiprocessing.Manager()
    # input_queue
    lines = manager.Queue()
    # output_queue
    output = manager.Queue()
    with open('patent_inventors_input.csv', 'r', encoding='utf-8') as f:
        while 1:
            line = f.readline()
            if not line:
                break
            lines.put(line)

    with multiprocessing.Pool(NUM_WORKERS) as p:
        p.map(process, [(all_sheet, lines, output) for _ in range(NUM_WORKERS)])

    '''
    本质上多进程和这样直接调用的效果是完全一样的，所以可以用这种方式来测试你的多进程代码是否正确
    验证正确时候再使用多进程避免报错
    这样也可以在报错时确定问题到底是出在子进程执行的函数还是出在多进程本身
    '''
    # process((all_sheet, lines, output))

    count = 0
    with open('./output.csv', 'w', encoding='utf-8') as f:
        while 1:
            if not output.empty():
                con = output.get()
                # 使用isinstance这种方式来判断子进程在queue中放的是需要的结果还是结束符
                if isinstance(con, str):
                    logging.info(con)
                elif isinstance(con, int):
                    count += 1
                    if count == NUM_WORKERS:
                        break
                else:
                    p, ans = con
                    f.write('%s%s%.3f%s%.3f\n' % (p.id, SEP, ans[0], SEP, ans[1]))
                    f.flush()
