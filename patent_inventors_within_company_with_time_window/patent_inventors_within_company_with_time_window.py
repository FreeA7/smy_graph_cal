# -*- coding: utf-8 -*-
"""
Created on Thu Mar 10 00:31:08 2022

@author: FreeA7

3月10日帮你写的，功能是：
    公司时间数据：Relational Embeddedness within Firm_2004.xlsx
    公司专利时间发明人数据：Building Knowledge Network, Firm Sample_2000-2004 & their Patents in 424-514_1991-2004.xlsx
    每一个专利，使用本公司发明这个专利过去5年内的所有专利的发明人构建网络
    然后计算这个网络的相关参数

从这个代码开始我把公共函数都提取到utils.py中了
因为我意识到你这个还可能有很多需要写的哈哈哈
我果然没猜错，后续一直在沿用这个utils.py
你可以看到把公共函数提取出来之后的代码非常简洁精炼，可读性和可拓展性都大大提高
你也可以的，加油！
ヾ(◍°∇°◍)ﾉﾞ
"""

SEP = '\t'
NUM_WORKERS = 8
FLUSH_DATA = True


if FLUSH_DATA:
    import pandas as pd

    data = pd.read_excel('./Relational Embeddedness within Firm_2004_0728.xlsx',
                         sheet_name = 0, dtype = str)
    data.to_csv('./company_time.csv', sep = SEP, encoding = 'utf-8', index = 0)

    with open('./company_time.csv', 'r', encoding='utf-8') as f:
        while 1:
            line = f.readline()
            if not line:
                break
            if len(line.split(SEP)) != 10:
                print(line)

    data = pd.read_excel('./Building Knowledge Network, Firm Sample_2000-2004 & their Patents in 424-514_1991-2004_0728.xlsx',
                         sheet_name = '424-514, 1996-2004', dtype = str)
    data.to_csv('./company_patent_time_inventor.csv', sep = SEP, encoding = 'utf-8', index = 0)

    with open('./company_patent_time_inventor.csv', 'r', encoding='utf-8') as f:
        while 1:
            line = f.readline()
            if not line:
                break
            if len(line.split(SEP)) != 35:
                print(line)



import multiprocessing
from utils import *
import networkx as nx
import logging


OUTPUT_SEQ = ['degree_centrality', 'degree_centrality_normal', 'degree_centrality_weight',
              'between_centrality', 'between_centrality_normal',
              'closeness_centrality', 'closeness_centrality_nx_normal', 'closeness_centrality_smy_normal',
              'clustering_coefficient', 'clustering_without_zero', 'clustering_weight',
              'average_path_length', 'density']

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[logging.FileHandler(filename='./root.log', encoding='utf-8', mode='w')],
)


def return_defaultdict():
    # 内层默认字典的函数，本来可以直接用 lambda : defaultdict(list) 表示的，但是多进程不支持匿名函数
    return defaultdict(list)


def process(input_queue, output_queue, secondary_table, pid):
    """
    子进程执行的函数
    """
    while not input_queue.empty():
        try:
            line, pdpass, gyear, inventors = input_queue.get()
            gyear = int(gyear)
            G = nx.Graph()

            logging.debug('[%d/%d] 开始生成图 %s - %d' % (pid, NUM_WORKERS, pdpass, gyear))
            # 获取本公司内部过去5年的专利信息建立图
            for i in range(5):
                for nodes in secondary_table[pdpass][str(gyear - i)]:
                    build_graph(G, nodes)
            logging.debug('[%d/%d] 图生成完毕 %s - %d' % (pid, NUM_WORKERS, pdpass, gyear))

            # 计算单层图的指标，详细解释可见utils.py
            res = cal_one_layer_graph_index(G, inventors)
            logging.debug('[%d/%d] 图计算完毕 %s - %d' % (pid, NUM_WORKERS, pdpass, gyear))

            output_queue.put((line, res))
            logging.info('[%d/%d] 图处理完成 %s - %d' % (pid, NUM_WORKERS, pdpass, gyear))
        except Exception as e:
            logging.error('[%d/%d] 图处理错误 %s - %d' % (pid, NUM_WORKERS, pdpass, gyear))
            logging.exception(e)

    output_queue.put(1)


if __name__ == '__main__':
    """
    这里的secondary_table是一个双重默认字典，也就是默认返回的还是一个字典，内层字典默认返回一个列表
    这么做的目的是 第一层的key是pdpass 第二层的key是gyear
    也就是我们可以快速的获取一个pdpass在某一个gyear的所有专利的发明人信息
    secondary_table[pdpass][gyear]
    """
    secondary_table = defaultdict(return_defaultdict)

    # 这里应该对应其他代码的pre_process的，当时好像写high了直接写在main里了
    with open('./company_patent_time_inventor.csv', 'r', encoding='utf-8') as f:
        # 这也是一种header : index的写法，这个代码写的比较早，这么写就很丑，不够优雅
        secondary_table_headers = split_line(f.readline(), SEP)
        secondary_table_headers = dict(zip(secondary_table_headers, range(len(secondary_table_headers))))

        while 1:
            line = f.readline()
            if not line:
                break
            line = split_line(line, SEP)

            pdpass = get_field('pdpass', line, secondary_table_headers)
            gyear = get_field('gyear', line, secondary_table_headers)
            inventors = split_name(get_field('发明人', line, secondary_table_headers))

            secondary_table[pdpass][gyear].append(inventors)

    manager = multiprocessing.Manager()
    input_queue = manager.Queue()
    output_queue = manager.Queue()

    # 每行是一个patent_id，pdpass，gyear，inventors，对应输出的一行
    with open('./company_time.csv', 'r', encoding='utf-8') as f:
        headers_line = f.readline()
        primary_headers = split_line(headers_line, SEP)
        primary_headers = dict(zip(primary_headers, range(len(primary_headers))))

        while 1:
            line = f.readline()
            if not line:
                break
            line = split_line(line, SEP)

            pdpass = get_field('pdpass', line, primary_headers)
            gyear = get_field('gyear', line, primary_headers)
            inventors = get_field('发明人', line, primary_headers)

            inventors = split_name(inventors)

            input_queue.put((line, pdpass, gyear, inventors))

    num_of_input = input_queue.qsize()

    # process(input_queue, output_queue, secondary_table, 1)

    pool = multiprocessing.Pool(NUM_WORKERS)
    for i in range(NUM_WORKERS):
        pool.apply_async(process, args=(input_queue, output_queue, secondary_table, i + 1))
    pool.close()

    with open('output.txt', 'w', encoding='utf-8') as f:
        f.write(headers_line[:-1] + SEP + SEP.join(OUTPUT_SEQ) + '\n')

    worker_count = 0
    finish_count = 0

    while 1:
        if not output_queue.empty():
            con = output_queue.get()
            if isinstance(con, int):
                worker_count += con
                if worker_count == NUM_WORKERS:
                    break
            elif isinstance(con, tuple):
                # 这里line一直传递下来目的是把原始的一行保留，后续代码感觉没必要就没删了
                line, res = con
                with open('output.txt', 'a', encoding='utf-8') as f:
                    f.write(SEP.join(line))
                    for key in OUTPUT_SEQ:
                        f.write(SEP + num2str(res.get(key)))
                    f.write('\n')
                finish_count += 1
                logging.info('[main] %d/%d 已处理' % (finish_count, num_of_input))
            else:
                logging.error('Unavailable Type!')
                raise TypeError('Unavailable Type!')
