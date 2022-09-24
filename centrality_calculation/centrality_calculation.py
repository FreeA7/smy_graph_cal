# -*- coding: utf-8 -*-
"""
Created on Sat Sep 24 14:01:24 2022

@author: c30004771
"""

from utils import *
import multiprocessing
import logging
import networkx as nx


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[logging.FileHandler(filename='./root.log', encoding='utf-8', mode='w')],
)


relation_file_name = 'sep_t_collaborated_inventions_1981-1999patents.csv'
net_file_name = 'sep_t_Sample-Cited_1985-1999_with-inventors.csv'

SEP = '\t'

begin_time = 1985
last_time = 15
time_window = 5

def pre_process():
    with open(relation_file_name, 'r', encoding='utf-8') as f:
        relation_headers = {v: i for i, v in enumerate(split_line(f.readline(), SEP))}
        while 1:
            line = f.readline()
            if not line:
                break
            line = split_line(line, SEP)
            primary_key = get_field('focal_patent', line, relation_headers) + '&' + get_field('focal_pdpass', line, relation_headers)
            if primary_key not in relation_info.keys():
                relation_info[primary_key] = set()
                res_input_queue.put(primary_key)

            year_info[primary_key] = int(get_field('focal_appyear', line, relation_headers))

            focal_inventors = split_class(get_field('focal_lowers', line, relation_headers))
            cited_inventors = split_class(get_field('cited_lowers', line, relation_headers))
            for focal_inventor in focal_inventors:
                for cited_inventor in cited_inventors:
                    relation_info[primary_key].add(tuple(sorted([focal_inventor, cited_inventor])))

    with open(net_file_name, 'r', encoding='utf-8') as f:
        net_headers = {v: i for i, v in enumerate(split_line(f.readline(), SEP))}
        while 1:
            line = f.readline()
            if not line:
                break
            line = split_line(line, SEP)
            inventors = split_class(get_field('lowers', line, net_headers))
            year = int(get_field('appyear', line, net_headers))
            for i in range(time_window):
                if 1985 <= (year + time_window) <= 1999:
                    build_graph(graph_info[year - time_window], inventors)


def process():
    while not res_input_queue.empty():
        try:
            primary_key = res_input_queue.get()
            appyear = year_info.get(primary_key)
            relation = relation_info.get(primary_key)
            graph = graph_info.get(appyear)

            weight_matrix_one_layer, node_index_one_layer = cal_graph_weight_matrix(graph, 1)
            result_one_layer = cal_weight_matrix_index(relation, weight_matrix_one_layer, node_index_one_layer)

            del weight_matrix_one_layer, node_index_one_layer

            weight_matrix_two_layer, node_index_two_layer = cal_graph_weight_matrix(graph, 2)
            result_two_layer = cal_weight_matrix_index(relation, weight_matrix_two_layer, node_index_two_layer)

            del weight_matrix_two_layer, node_index_two_layer

            res_output_queue.put(tuple(primary_key.split('&') + [result_one_layer, result_two_layer]))

        except:
            





if __name__ == '__main__':

    manager = multiprocessing.Manager()
    res_input_queue = manager.Queue()
    res_output_queue = manager.Queue()

    relation_info = manager.dict()
    graph_info = manager.dict()
    year_info = manager.dict()

    for i in range(begin_time, begin_time + last_time):
        graph_info[i] = nx.Graph()



