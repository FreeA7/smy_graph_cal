# -*- coding: utf-8 -*-
"""
Created on Thu Mar 10 20:01:32 2022

@author: FreeA7


"""

SEP = '\t'
NUM_WORKERS = 8

OUTPUT_SEQ = ['degree_centrality', 'degree_centrality_normal', 'degree_centrality_weight',
              'between_centrality', 'between_centrality_normal',
              'closeness_centrality', 'closeness_centrality_nx_normal', 'closeness_centrality_smy_normal',
              'clustering_coefficient', 'clustering_without_zero', 'clustering_weight',
              'average_path_length', 'density']

# primary_key可以使用的字段变成可配置的
PRIMARY_KEYS = ['pdpass', 'gyear']
FLUSH_DATA = True

if FLUSH_DATA:
    import pandas as pd

    data = pd.read_excel('./Knowledge Embeddedness within Firm_2000-2004_3.31.xlsx', sheet_name=0, dtype=str)
    data.to_csv('./knowledge_embeddedness_within_firm.csv', sep=SEP, encoding='utf-8', index=0)

import multiprocessing
import logging
import sys
sys.path.append('..')
from utils import *


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[logging.FileHandler(filename='./root.log', encoding='utf-8', mode='w')],
)


def pre_process(path, input_queue):
    data = defaultdict(list)
    logging.info('[main] 开始进行数据预处理')
    with open(path, 'r', encoding='utf-8') as f:
        headers_line = f.readline()
        headers = {v: i for i, v in enumerate(split_line(headers_line, SEP))}
        while 1:
            line = f.readline()
            if not line:
                break
            line = split_line(line, SEP)
            # 这里使用字符串而不是tuple作为primary_key其实没什么区别，不过我这里将primary可以用的字段变成可配置的，可以在全局参数中增减
            primary_key = '&'.join((get_field(key, line, headers) for key in PRIMARY_KEYS))
            # 按照 美国分类（已划分） 的 / 后的数字切分作为inventors
            inventors = split_class(get_field('美国分类 (已划分)', line, headers))
            data[primary_key].append(inventors)
            input_queue.put((line, inventors))

    logging.info('[main] 数据预处理结束')
    return data, headers, headers_line


def process(data, headers, input_queue, output_queue, pid):
    while not input_queue.empty():
        try:
            G = nx.Graph()

            line, inventors = input_queue.get()
            primary_key = '&'.join((get_field(key, line, headers) for key in PRIMARY_KEYS))

            logging.debug('[%d/%d] 开始生成图 %s' % (pid, NUM_WORKERS, primary_key))
            for nodes in data.get(primary_key):
                build_graph(G, nodes)
            logging.debug('[%d/%d] 图生成完毕 %s' % (pid, NUM_WORKERS, primary_key))

            res = cal_one_layer_graph_index(G, inventors)
            logging.debug('[%d/%d] 图计算完毕 %s' % (pid, NUM_WORKERS, primary_key))

            output_queue.put((line, res))
            logging.debug('[%d/%d] 图处理完毕 %s' % (pid, NUM_WORKERS, primary_key))

        except Exception as e:
            # 捕获异常，使子进程的运行不受到报错打断
            logging.error('[%d/%d] 图处理错误 %s' % (pid, NUM_WORKERS, primary_key))
            logging.exception(e)

    output_queue.put(1)


if __name__ == '__main__':
    manager = multiprocessing.Manager()
    input_queue = manager.Queue()
    output_queue = manager.Queue()

    for file_name in ['knowledge_embeddedness_within_firm']:
        data, headers, headers_line = pre_process('./%s.csv' % file_name, input_queue)

        num_of_input = input_queue.qsize()

        # process(data, headers, input_queue, output_queue, 1)

        pool = multiprocessing.Pool(NUM_WORKERS)
        for i in range(NUM_WORKERS):
            pool.apply_async(process, args=(data, headers, input_queue, output_queue, i + 1))
        pool.close()

        with open('output_%s.txt' % file_name, 'w', encoding='utf-8') as f:
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
                    line, res = con
                    with open('output_%s.txt' % file_name, 'a', encoding='utf-8') as f:
                        f.write(SEP.join(line))
                        for key in OUTPUT_SEQ:
                            f.write(SEP + num2str(res.get(key)))
                        f.write('\n')
                    finish_count += 1
                    logging.info('[main] %d/%d 已处理' % (finish_count, num_of_input))
                    print('[main] %d/%d 已处理' % (finish_count, num_of_input))
                else:
                    raise TypeError('Unavailable Type!')
