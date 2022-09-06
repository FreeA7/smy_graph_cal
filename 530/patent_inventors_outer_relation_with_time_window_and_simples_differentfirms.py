# -*- coding: utf-8 -*-
"""
Created on Mon Feb 28 00:00:10 2022

@author: FreeA7

2月28日帮你写的，功能是：
    有三个文件：
        关系表：※Inventors & US-Cited Inventors of Focal Patents.xlsx
        图表：Building Knowledge Network, Firm Sample_2000-2004 & their Patents in 424-514_1991-2004.xlsx
        样本表：Sampling of  Pdpass.xlsx
    关系表中每一个focal_patent需要使用图表中的focal_patent的发明年份gyear过去五年中非自己公司与以及的发明人数据构建图
    然后对关系表中的所有不同公司且在样本集中且2000-2004发表数量大于门槛k的cited_patent的关系计算指标
    这个当时最后算出来的结果0很多，所以本来说让你多做几个行业的
    当时还有测试，就是有的cited_pdpass为空，当时算了一个考虑这些空pdpass关系的，一个没考虑的
"""

SEP = '\t'
NUM_WORKERS = 8
FLUSH_DATA = False


if FLUSH_DATA:
    import pandas as pd

    data = pd.read_excel('./※Inventors & US-Cited Inventors of Focal Patents.xlsx',
                         sheet_name='竖向-US with pdpass by pat76-06', dtype=str)
    data.to_csv('./relation_table.csv', sep=SEP, encoding='utf-8', index=0)

    with open('./relation_table.csv', 'r', encoding='utf-8') as f:
        while 1:
            line = f.readline()
            if not line:
                break
            if len(line.split(SEP)) != 44:
                print(line)

    data = pd.read_excel(
        './Building Knowledge Network, Firm Sample_2000-2004 & their Patents in 424-514_1991-2004.xlsx',
        sheet_name='424-514, 1996-2004', dtype=str)
    data.to_csv('./graph_table.csv', sep=SEP, encoding='utf-8', index=0)

    with open('./graph_table.csv', 'r', encoding='utf-8') as f:
        while 1:
            line = f.readline()
            if not line:
                break
            if len(line.split(SEP)) != 35:
                print(line)

    data = pd.read_excel('./Sampling of  Pdpass.xlsx', sheet_name='Sheet2', dtype=str)
    data.to_csv('./simple_table.csv', sep=SEP, encoding='utf-8', index=0)

    with open('./simple_table.csv', 'r', encoding='utf-8') as f:
        while 1:
            line = f.readline()
            if not line:
                break
            if len(line.split(SEP)) != 3:
                print(line)


import logging
import multiprocessing
import sys
sys.path.append('..')

from utils import *

from class_utils import Patent 


# 增加了编码utf-8这样可以打印汉字，mode='w'代表每一次执行日志都会被覆盖，不会在上一次的执行结果后进行追加
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s',
    handlers=[logging.FileHandler(filename='./root.log', encoding='utf-8', mode='w')],
)

# 需要输出的字段以及顺序
OUTPUT_HEADERS = ['patent', 'pdpass',
                  'one_layer_sum_divide', 'one_layer_divide_sum',
                  'one_layer_sum_divide_except_null', 'one_layer_divide_sum_except_null',
                  'two_layer_sum_divide', 'two_layer_divide_sum',
                  'two_layer_sum_divide_except_null', 'two_layer_divide_sum_except_null']


def pre_process(relation_table_path, graph_table_path, simple_table_path, input_queue, k):
    """
    数据预处理：
        1. 读取样本集，如果对2000-2004发明专利数量有要求则进行筛选
        2. 读取关系数据 ※Inventors & US-Cited Inventors of Focal Patents.xlsx
        3. 读取图数据 Building Knowledge Network, Firm Sample_2000-2004 & their Patents in 424-514_1991-2004.xlsx
    """
    logging.info('[main] * 开始处理样本集 *')
    # simples = set([''])
    simples = set()
    with open(simple_table_path, 'r', encoding='utf-8') as f:
        """
        这个结构将作为我后续处理数据时获取列的常见结构，这里进行详细介绍：
            我的目的是，即使你给我的表的列顺序如何变化，我都应该从不变的列名读取数据
            那么我在读取到第一行header的时候，就将header保存为一个字典，header : index
            这样后续需要用到某一个字段的时候，我就使用这个字段调用这个字典，获取这个字段的下标来获取数据
            实际使用的get_field函数你可以去我的utils.py中查看详细解释
        """
        simple_table_headers = {v: i for i, v in enumerate(split_line(f.readline(), SEP))}
        while 1:
            line = f.readline()
            if not line:
                break
            line = split_line(line, SEP)
            if int(get_field('专利发明数量2000-2004', line, simple_table_headers)) >= k:
                simples.add(get_field('pdpass', line, simple_table_headers))
    logging.info('[main] - 样本集处理完毕 -')

    logging.info('[main] * 开始处理关系数据 *')
    relations = defaultdict(list)

    with open(relation_table_path, 'r', encoding='utf-8') as f:
        relation_table_headers = {v: i for i, v in enumerate(split_line(f.readline(), SEP))}
        while 1:
            line = f.readline()
            if not line:
                break
            line = split_line(line, SEP)

            focal_patent_id = get_field('focal_patent', line, relation_table_headers)
            focal_pdpass = get_field('focal_pdpass', line, relation_table_headers)
            focal_inventors = get_field('focal_发明人', line, relation_table_headers)
            focal_inventors = split_name(focal_inventors)

            cited_pdpass = get_field('cited_pdpass', line, relation_table_headers)
            cited_inventors = get_field('Cited_发明人', line, relation_table_headers)
            cited_inventors = split_name(cited_inventors)

            """
            关系获取的原则：
                1. 不同公司
                # 2. 被引用公司在样本集中
            """
            if focal_pdpass == cited_pdpass:
                continue

            """
            主键为patent_id与focal_pdpass的联合主键
            同一行会包含多个link
            每一个主键可能存在个多个行中，每一行的cited_pdpass都是不一样的
            所以一个主键有多个links（对应不同的cited_pdpass），一个links有多个link（对应同一个cited_pdpass的不同发明者之间的关系）
            """
            primary_key = (focal_patent_id, focal_pdpass)
            links = []
            for focal_inventor in focal_inventors:
                for cited_inventor in cited_inventors:
                    # 发明者与被引用者同一人则抛弃关系
                    if focal_inventor == cited_inventor:
                        continue
                    links.append((focal_inventor, cited_inventor))
            relations[primary_key].append(links)

    # 有多少个(focal_patent_id, focal_pdpass)就有多少行结果，也就有多少次计算，所以将primary_key放入input_queue让子进程取出计算
    for primary_key in relations.keys():
        input_queue.put(primary_key)
    logging.info('[main] - 关系数据处理完毕 -')

    logging.info('[main] * 开始处理建图数据 *')
    # key是年份，因为你要按年份筛选构建图，所以gyear : inventors
    graphs = defaultdict(list)
    # 需要知道每一个patent是哪一年发明的，所以patent_id : gyear，但是其实这个gyear可以放在上边的primary_key中，但是这个需求是你后来加的我就这么偷懒处理了
    patent_gyear = dict()
    with open(graph_table_path, 'r', encoding='utf-8') as f:
        graph_table_headers = {v: i for i, v in enumerate(split_line(f.readline(), SEP))}
        while 1:
            line = f.readline()
            if not line:
                break
            line = split_line(line, SEP)
            pdpass = get_field('pdpass', line, graph_table_headers)
            patent_id = get_field('patent', line, graph_table_headers)
            gyear = int(get_field('gyear', line, graph_table_headers))
            inventors = split_name(get_field('发明人', line, graph_table_headers))

            patent_gyear[patent_id] = gyear
            graphs[gyear].append(Patent(patent_id, pdpass, inventors))
    logging.info('[main] - 建图数据处理完毕 -')

    return relations, graphs, patent_gyear


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


def cal_index(primary_key, relations, weight_matrix, node_index):
    """
    计算一个primary_key的参数
    :param primary_key: (patent_id, pdpass)
    :param relations: 预处理读取的所有关系
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

    for links in relations[primary_key]:
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
    result_sum_divide /= len(relations[primary_key])

    if count_sum_divide_except_null:
        result_sum_divide_except_null /= count_sum_divide_except_null
    result_sum_divide_except_null /= len(relations[primary_key])

    return result_sum_divide, result_divide_sum, result_sum_divide_except_null, result_divide_sum_except_null


def process(relations, graphs, patent_gyear, input_queue, output_queue, pid):
    """
    子进程处理的函数
    pid就是为了打印日志的时候知道是哪个子进程打印的，这样报错的话也知道是哪个子进程出问题了
    """
    while not input_queue.empty():
        try:
            G = nx.Graph()

            primary_key = input_queue.get()
            # 便于打印日志
            str_primary_key = '%s&%s' % primary_key
            patent_id, pdpass = primary_key
            gyear = int(patent_gyear[patent_id])

            logging.debug('[%d/%d] * 开始生成图 %s *' % (pid, NUM_WORKERS, str_primary_key))
            # 过去5年
            for i in range(5):
                for patent in graphs[gyear - i]:
                    # 公司不同，或者公司相同且patent_id相同（也就是使用不同公司的patent以及自己构建图）
                    if patent.pdpass != pdpass or patent.patent == patent_id:
                        build_graph(G, patent.inventors)
            logging.debug('[%d/%d] - 图生成完毕 %s -' % (pid, NUM_WORKERS, str_primary_key))

            logging.debug('[%d/%d] * 开始计算单层图权重矩阵 %s *' % (pid, NUM_WORKERS, str_primary_key))
            weight_matrix_one_layer, node_index_one_layer = cal_graph_weight_matrix(G, 1)
            logging.debug('[%d/%d] - 单层图权重矩阵计算完毕 %s -' % (pid, NUM_WORKERS, str_primary_key))

            logging.debug('[%d/%d] * 开始计算单层图专利结果 %s *' % (pid, NUM_WORKERS, str_primary_key))
            result_one_layer = cal_index(primary_key, relations, weight_matrix_one_layer, node_index_one_layer)
            logging.debug('[%d/%d] - 单层图专利结果计算完毕 %s -' % (pid, NUM_WORKERS, str_primary_key))

            # 及时删除使用过的矩阵，因为基本都是几千维的矩阵，很吃内存
            del weight_matrix_one_layer, node_index_one_layer

            logging.debug('[%d/%d] * 开始计算双层图权重矩阵 %s *' % (pid, NUM_WORKERS, str_primary_key))
            weight_matrix_two_layer, node_index_two_layer = cal_graph_weight_matrix(G, 2)
            logging.debug('[%d/%d] - 双层图图权重矩阵计算完毕 %s -' % (pid, NUM_WORKERS, str_primary_key))

            logging.debug('[%d/%d] * 开始计算双层图专利结果 %s *' % (pid, NUM_WORKERS, str_primary_key))
            result_two_layer = cal_index(primary_key, relations, weight_matrix_two_layer, node_index_two_layer)
            logging.debug('[%d/%d] - 双层图专利结果计算完毕 %s -' % (pid, NUM_WORKERS, str_primary_key))

            del weight_matrix_two_layer, node_index_two_layer

            output_queue.put(primary_key + result_one_layer + result_two_layer)
            logging.info('[%d/%d] - 专利处理完毕 %s -' % (pid, NUM_WORKERS, str_primary_key))
        except Exception as e:
            logging.error('[%d/%d] ! 处理数据错误 %s !' % (pid, NUM_WORKERS, str_primary_key))
            logging.exception(e)

    output_queue.put(1)


if __name__ == '__main__':
    manager = multiprocessing.Manager()
    input_queue = manager.Queue()
    output_queue = manager.Queue()

    # 不同的2000-2004的门槛
    for k in [0, 5, 6, 10, 11]:
        logging.info('[main] ----------------------------- 开始处理k=%d -----------------------------' % k)
        relations, graphs, patent_gyear = pre_process('./relation_table.csv', './graph_table.csv', './simple_table.csv',
                                                  input_queue, k)


        # 获取需要处理的primary_key数量，便于打印日志知道处理进度
        num_of_input = input_queue.qsize()

        # process(relations, graphs, patent_gyear, input_queue, output_queue, 1)

        pool = multiprocessing.Pool(NUM_WORKERS)
        for i in range(NUM_WORKERS):
            # 使用异步进程，不阻塞主线进行
            pool.apply_async(process, args=(relations, graphs, patent_gyear, input_queue, output_queue, i + 1))
        pool.close()

        with open('output_%d.txt' % k, 'w', encoding='utf-8') as f:
            f.write(SEP.join(OUTPUT_HEADERS) + '\n')

        worker_count = 0
        finish_count = 0

        while 1:
            if not output_queue.empty():
                con = output_queue.get()
                # int说明为结束符，结束符足够后说明运行结束，可以计算下一个k了
                if isinstance(con, int):
                    worker_count += con
                    if worker_count == NUM_WORKERS:
                        break
                elif isinstance(con, tuple):
                    with open('output_%d.txt' % k, 'a', encoding='utf-8') as f:
                        f.write(SEP.join([num2str(res) for res in con]) + '\n')
                    finish_count += 1
                    logging.info('[main] %d/%d 已处理' % (finish_count, num_of_input))
                    print('[main] %d/%d 已处理' % (finish_count, num_of_input))
                else:
                    raise TypeError('Unavailable Type!')
