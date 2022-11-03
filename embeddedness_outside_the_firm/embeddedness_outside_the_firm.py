# -*- coding: utf-8 -*-
"""
Created on Tue Sep 13 22:27:22 2022

@author: FreeA7

Embeddedness outside the Firm
通过专利在公司外的中心度衡量嵌入性
"""


SEP = '\t'
NUM_WORKERS = 8
FILENAME = 'sep_tab_1985_1999_A-Sample'
TARGET_FIELD = 'USPC-Derwent'
YEAR_FIELD = 'focal_yeart'
PANTENT_FIELD = 'focal_patent'
PDPASS_FIELD = 'focal_pdpass'


import logging
import multiprocessing
from utils import *
import datetime


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s',
    handlers=[logging.FileHandler(filename='./root.log', encoding='utf-8', mode='w')],
)


OUTPUT_SEQ = ['degree_centrality', 'degree_centrality_normal', 'degree_centrality_weight',
              'between_centrality', 'between_centrality_normal',
              'closeness_centrality', 'closeness_centrality_nx_normal', 'closeness_centrality_smy_normal',
              'clustering_coefficient', 'clustering_without_zero', 'clustering_weight',
              'average_path_length', 'density']

GRAPH_SEQ = ['clustering_without_zero', 'clustering_coefficient',
             'clustering_weight', 'average_path_length', 'density']


def pre_process(year_com_inv):
    patents = set()
    with open('%s.csv' % FILENAME, 'r', encoding='utf-8') as f:
        headers = {v: i for i, v in enumerate(split_line(f.readline(), SEP))}
        while 1:
            line_org = f.readline()
            if not line_org:
                break
            line = split_line(line_org, SEP)

            # 筛选行业为424 514
            # if get_field(TARGET_FIELD, line, headers)[:3] not in ('424', '514'):
            #     continue

            patent = get_field(PANTENT_FIELD, line, headers)
            if patent in patents:
                continue
            else:
                patents.add(patent)

            appyear = int(get_field(YEAR_FIELD, line, headers))
            pdpass = get_field(PDPASS_FIELD, line, headers)
            inventors = split_class(get_field(TARGET_FIELD, line, headers))

            if appyear not in year_com_inv.keys():
                year_com_inv[appyear] = dict()
            if pdpass not in year_com_inv[appyear].keys():
                year_com_inv[appyear][pdpass] = list()
            year_com_inv[appyear][pdpass].append(inventors)

            input_queue.put((line_org, patent, appyear, pdpass, inventors))



def process(year_com_inv, pid):
    while not input_queue.empty():
        line_org, patent, appyear, pdpass, inventors = input_queue.get()
        try:
            logging.debug('[%d/%d] - 开始构建专利图 %s -' % (pid, NUM_WORKERS, patent))
            G = nx.Graph()

            # 不同公司的专利构图
            for com in year_com_inv[appyear].keys():
                if com != pdpass:
                    for inv in year_com_inv[appyear][com]:
                        build_graph(G, inv)

            # 本专利构图
            build_graph(G, inventors)
            logging.debug('[%d/%d] - 专利图构建完毕 %s 有 %d 节点 -' % (pid, NUM_WORKERS, patent, len(G.nodes)))

            logging.debug('[%d/%d] - 开始计算专利图 %s -' % (pid, NUM_WORKERS, patent))
            res = cal_one_layer_graph_index(G, inventors)
            logging.debug('[%d/%d] - 专利图计算完毕 %s -' % (pid, NUM_WORKERS, patent))

            output_queue.put((line_org, res))
        except Exception as e:
            logging.error('[%d/%d] - 专利图处理错误 %s -' % (pid, NUM_WORKERS, patent))
            logging.exception(e)

    output_queue.put(1)


if __name__ == '__main__':
    manager = multiprocessing.Manager()
    input_queue = manager.Queue()
    output_queue = manager.Queue()
    year_com_inv = dict()

    logging.info('[main] 开始进行预处理')
    pre_process(year_com_inv)
    logging.info('[main] 预处理完成')

    num_of_input = input_queue.qsize()

    logging.info('[main] 开始创建子进程')

    # process(year_com_inv, 1)

    pool = multiprocessing.Pool(NUM_WORKERS)
    for i in range(NUM_WORKERS):
        pool.apply_async(process, args=(year_com_inv, i + 1))
    pool.close()
    logging.info('[main] 子进程创建完成')

    with open('%s.csv' % FILENAME, 'r', encoding='utf-8') as fo:
        with open('output_%s.csv' % FILENAME, 'w', encoding='utf-8') as f:
            f.write('%s%s%s%s%s%s' % (fo.readline()[:-1], SEP, SEP.join(OUTPUT_SEQ), SEP, SEP.join(GRAPH_SEQ), '\n'))

    worker_count = 0
    finish_count = 0

    end_time_l = end_time_r = 0

    logging.info('[main] 开始获取结果')

    while 1:
        if not output_queue.empty():
            end_time_l = datetime.datetime.now()
            con = output_queue.get()
            if isinstance(con, int):
                worker_count += con
                if worker_count == NUM_WORKERS:
                    break
            elif isinstance(con, tuple):
                line_org, res = con
                with open('output_%s.csv' % FILENAME, 'a', encoding='utf-8') as f:
                    f.write(line_org[:-1])
                    for key in OUTPUT_SEQ:
                        f.write(SEP + num2str(res.get(key)))
                    for key in GRAPH_SEQ:
                        f.write(SEP + num2str(res.get(key)))
                    f.write('\n')
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
