# -*- coding: utf-8 -*-
"""
Created on Sat Sep 24 14:01:24 2022

@author: FreeA7
"""

from utils import *
import multiprocessing
import logging
import networkx as nx
import datetime

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[logging.FileHandler(filename='./root.log', encoding='utf-8', mode='w')],
)

relation_file_name = 'sep_t_Sample424514-Cited_1985-1999_with-inventors_20221009_cited_424-514.csv'
net_file_name = 'sep_t_collaborated_inventions_1981-1999patents_20221009_cited_424-514.csv'

output_file = 'output_of_%s' % relation_file_name

SEP = '\t'

begin_time = 1985
last_time = 15
time_window = 5

NUM_WORKERS = 8

output_seq = ['patent', 'pdpass', 'appyear',
              'one_layer_result_sum_divide', 'one_layer_result_divide_sum',
              'one_layer_result_sum_divide_except_null', 'one_layer_result_divide_sum_except_null',
              'two_layer_result_sum_divide', 'two_layer_result_divide_sum',
              'two_layer_result_sum_divide_except_null', 'two_layer_result_divide_sum_except_null']


def pre_process(relation_info, graph_info, year_info):
    logging.info('[main] 开始获取关系数据')
    with open(relation_file_name, 'r', encoding='utf-8') as f:
        relation_headers = {v: i for i, v in enumerate(split_line(f.readline(), SEP))}
        while 1:
            line = f.readline()
            if not line:
                break
            line = split_line(line, SEP)
            primary_key = get_field('focal_patent', line, relation_headers) + '&' \
                          + get_field('focal_pdpass', line, relation_headers)

            if primary_key not in relation_info.keys():
                relation_info[primary_key] = list()
                res_input_queue.put(primary_key)

            year_info[primary_key] = int(get_field('focal_appyear', line, relation_headers))

            focal_inventors = split_class(get_field('focal_inventors', line, relation_headers))
            cited_inventors = split_class(get_field('cited_inventors', line, relation_headers))

            links = set()
            for focal_inventor in focal_inventors:
                for cited_inventor in cited_inventors:
                    if focal_inventor != cited_inventor:
                        links.add((focal_inventor, cited_inventor))
            relation_info[primary_key].append(links)

    logging.info('[main] 关系数据获取完成')

    logging.info('[main] 开始获取网络数据')
    count = 0
    with open(net_file_name, 'r', encoding='utf-8') as f:
        net_headers = {v: i for i, v in enumerate(split_line(f.readline(), SEP))}
        while 1:
            line = f.readline()
            if not line:
                break
            line = split_line(line, SEP)
            inventors = split_class(get_field('inventors', line, net_headers))
            year = int(get_field('appyear', line, net_headers))
            for i in range(time_window):
                if 1985 <= (year + i) <= 1999:
                    build_graph(graph_info[year + i], inventors)
            count += 1
            if count % 100 == 0:
                logging.info('[main] 网络数据加载%d' % count)
    logging.info('[main] 网络数据获取完成')


def process(relation_info, graph_info, year_info, pid):
    while not res_input_queue.empty():
        primary_key = res_input_queue.get()
        appyear = year_info.get(primary_key)
        logging.debug('[%d/%d] primany key 是 %s，appyear 是 %d，开始进行计算' % (pid, NUM_WORKERS, primary_key, appyear))

        try:
            relation = relation_info.get(primary_key)
            graph = graph_info.get(appyear)

            logging.debug('[%d/%d] primany key 是 %s 开始计算一阶权重矩阵' % (pid, NUM_WORKERS, primary_key))
            weight_matrix_one_layer, node_index_one_layer = cal_graph_weight_matrix(graph, 1)
            logging.debug('[%d/%d] primany key 是 %s 一阶权重矩阵计算完成' % (pid, NUM_WORKERS, primary_key))

            logging.debug('[%d/%d] primany key 是 %s 开始计算一阶矩阵参数' % (pid, NUM_WORKERS, primary_key))
            result_one_layer = cal_weight_matrix_index(relation, weight_matrix_one_layer, node_index_one_layer)
            logging.debug('[%d/%d] primany key 是 %s 一阶矩阵参数计算完毕' % (pid, NUM_WORKERS, primary_key))

            del weight_matrix_one_layer, node_index_one_layer

            logging.debug('[%d/%d] primany key 是 %s 二阶矩阵参数计算完毕' % (pid, NUM_WORKERS, primary_key))
            weight_matrix_two_layer, node_index_two_layer = cal_graph_weight_matrix(graph, 2)
            logging.debug('[%d/%d] primany key 是 %s 二阶矩阵参数计算完毕' % (pid, NUM_WORKERS, primary_key))

            logging.debug('[%d/%d] primany key 是 %s 二阶矩阵参数计算完毕' % (pid, NUM_WORKERS, primary_key))
            result_two_layer = cal_weight_matrix_index(relation, weight_matrix_two_layer, node_index_two_layer)
            logging.debug('[%d/%d] primany key 是 %s 二阶矩阵参数计算完毕' % (pid, NUM_WORKERS, primary_key))

            del weight_matrix_two_layer, node_index_two_layer

            res_output_queue.put(tuple(primary_key.split('&') + [appyear, result_one_layer, result_two_layer]))
        except Exception as e:
            logging.error('[%d/%d] - 专利图处理错误 %s -' % (pid, NUM_WORKERS, primary_key))
            logging.exception(e)

    res_output_queue.put(1)


if __name__ == '__main__':

    manager = multiprocessing.Manager()
    res_input_queue = manager.Queue()
    res_output_queue = manager.Queue()

    relation_info = dict()
    graph_info = {i: nx.Graph() for i in range(begin_time, begin_time + last_time)}
    year_info = dict()

    logging.info('[main] 开始进行预处理')
    pre_process(relation_info, graph_info, year_info)
    logging.info('[main] 预处理执行完成')

    num_of_input = len(relation_info.keys())

    logging.info('[main] 开始启动多进程')
    # process(relation_info, graph_info, year_info, 1)

    pool = multiprocessing.Pool(NUM_WORKERS)
    for i in range(NUM_WORKERS):
        pool.apply_async(process, args=(relation_info, graph_info, year_info, i + 1))
    pool.close()

    logging.info('[main] 多进程启动完成')

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(SEP.join(output_seq) + '\n')

    worker_count = 0
    finish_count = 0

    end_time_l = end_time_r = 0

    logging.info('[main] 开始获取结果')

    while 1:
        if not res_output_queue.empty():
            end_time_l = datetime.datetime.now()
            con = res_output_queue.get()
            if isinstance(con, int):
                worker_count += con
                if worker_count == NUM_WORKERS:
                    break
            elif isinstance(con, tuple):
                patent, pdpass, appyear, one_layer_res, two_layer_res = con

                with open(output_file, 'a', encoding='utf-8') as w:
                    w.write(patent + SEP + pdpass + SEP + str(appyear))
                    for r in one_layer_res:
                        w.write(SEP + num2str(r))
                    for r in two_layer_res:
                        w.write(SEP + num2str(r))
                    w.write('\n')

                finish_count += 1
                logging.info('[main] %d/%d 已处理' % (finish_count, num_of_input))
            else:
                raise TypeError('Unavailable Type!')
        else:
            if not end_time_l:
                end_time_l = datetime.datetime.now()
            else:
                end_time_r = datetime.datetime.now()
                if (end_time_r - end_time_l).seconds > 3000:
                    break

    logging.info('[main] 计算执行完成')
