# -*- coding: utf-8 -*-
"""
Created on Thu Mar 10 20:01:32 2022

@author: FreeA7

这是不知道为什么惹你生气之前写的代码，其实是在之前的代码基础上优化的
功能是：
    对于一个公司同一年的所有发明人构建网络，然后计算网络的参数
    但是这里有两种数据
        Knowledge Embeddedness within Firm_2000-2004_3.31.xlsx
        Knowledge Embeddedness within RP_2000-2004_3.31.xlsx
    其中的区别我已经记不清了，不过后来想起来这两个处理的代码是有区别的
    但是我这里当成一样的逻辑处理了，所以你说算出来值是一样的很奇怪
    需要你告诉我两个逻辑区别，然后重新跑一下，我这里把primary_key可用的字段做成可配置的
    就是因为两个文件的逻辑不同
    但是不知道我还有没有机会帮你改啦
    (ಥ﹏ಥ)

这个代码按顺序来说是最后完善的代码，所以整体结构和写法都更成熟标准
如果你坚持按我说的顺序看到现在的话，这里的代码你应该一眼就能看懂了
这里的特色是try，，，catch
"""
import datetime

SEP = '\t'
NUM_WORKERS = 8

FILENAME = 'sep_t_Final-Sample_1985-1999_Pharma_424-514_with-components'

OUTPUT_SEQ = ['degree_centrality', 'degree_centrality_normal', 'degree_centrality_weight',
              'between_centrality', 'between_centrality_normal',
              'closeness_centrality', 'closeness_centrality_nx_normal', 'closeness_centrality_smy_normal',
              'clustering_coefficient', 'clustering_without_zero', 'clustering_weight',
              'average_path_length', 'density']

GRAPH_SEQ = ['clustering_without_zero', 'clustering_coefficient',
             'clustering_weight', 'average_path_length', 'density']

# primary_key可以使用的字段变成可配置的
PRIMARY_KEYS = ['appyear', 'pdpass']

TARGET = 'uspc_components'




import multiprocessing
import logging

from utils import *

# from smy_code_20220408.utils import *


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[logging.FileHandler(filename='./root.log', encoding='utf-8', mode='w')],
)


def pre_process(path):
    data = defaultdict(list)
    line_count = 1
    # ava_count = 0

    keyss = defaultdict(set)

    with open(path, 'r', encoding='utf-8') as f:
        headers_line = f.readline()
        headers = {v: i for i, v in enumerate(split_line(headers_line, SEP))}
        while 1:
            line = f.readline()
            line_count += 1
            if not line:
                break
            line = split_line(line, SEP)
            # 这里使用字符串而不是tuple作为primary_key其实没什么区别，不过我这里将primary可以用的字段变成可配置的，可以在全局参数中增减
            primary_key = '&'.join((get_field(key, line, headers) for key in PRIMARY_KEYS))

            # 去重
            patent = get_field('patent', line, headers)
            if patent in keyss[primary_key]:
                continue
            else:
                keyss[primary_key].add(patent)

            # # 筛选目标行是否为1
            # if not get_field(filter_col, line, headers):
            #     continue

            # # 筛选行业为424 514
            # if get_field('uspc_components', line, headers)[:3] not in ('424', '514'):
            #     continue

            inventors = split_class(get_field(TARGET, line, headers))
            if not inventors:
                continue

            # ava_count += 1

            # if ava_count <= caled_num:
            #     continue

            data[primary_key].append(inventors)
            res_input_queue.put((line, inventors, line_count))

    return data, headers, headers_line


def generate_graphs(data, pid):
    while not graph_input_queue.empty():
        try:
            G = nx.Graph()
            primary_key = graph_input_queue.get()

            logging.debug('[%d/%d][generate_graphs] 开始生成图 %s' % (pid, NUM_WORKERS, primary_key))
            for nodes in data.get(primary_key):
                build_graph(G, nodes)
            logging.debug('[%d/%d][generate_graphs] 图生成完毕 %s' % (pid, NUM_WORKERS, primary_key))
            res = cal_graph_index(G)
            logging.debug('[%d/%d][generate_graphs] 图计算完毕 %s' % (pid, NUM_WORKERS, primary_key))
            graph_output_queue.put((primary_key, res))
            logging.debug('[%d/%d][generate_graphs] 图保存完毕 %s' % (pid, NUM_WORKERS, primary_key))
        except Exception as e:
            # 捕获异常，使子进程的运行不受到报错打断
            logging.error('[%d/%d][generate_graphs] 图生成错误 %s' % (pid, NUM_WORKERS, primary_key))
            logging.exception(e)

    graph_output_queue.put(1)


def process(headers, graph_info, pid):
    while not res_input_queue.empty():
        try:
            line, inventors, count = res_input_queue.get()
            primary_key = '&'.join((get_field(key, line, headers) for key in PRIMARY_KEYS))

            G_info = graph_info[primary_key]

            res = cal_one_layer_graph_index(G_info, inventors)
            logging.debug('[%d/%d][process] 图计算完毕 %s 行号为 %d' % (pid, NUM_WORKERS, primary_key, count))

            for key in GRAPH_SEQ:
                res[key] = G_info[key]

            res_output_queue.put((line, res))
            logging.debug('[%d/%d][process] 图处理完毕 %s 行号为 %d' % (pid, NUM_WORKERS, primary_key, count))

        except Exception as e:
            # 捕获异常，使子进程的运行不受到报错打断
            logging.error('[%d/%d][process] 图处理错误 %s 行号为 %d' % (pid, NUM_WORKERS, primary_key, count))
            logging.error(line)
            logging.exception(e)

    res_output_queue.put(1)


if __name__ == '__main__':
    # for i in range(15):
    #     filter_col = 'w_begin%d' % (1981 + i)
    #
    #     logging.info('[main] -----------* 开始进行 %s *-----------' % filter_col)
    #
    #     output_file = 'output_%s_%s_1.2.2.csv' % (filter_col, FILENAME)

        # # 断点继续
        # caled_num = 0
        # if os.path.exists(output_file):
        #     with open(output_file, 'r', encoding='utf-8') as f:
        #         line = f.readline()
        #         while 1:
        #             line = f.readline()
        #             if not line:
        #                 break
        #             else:
        #                 caled_num += 1

    output_file = 'output_%s_1.2.1.csv' % FILENAME

    manager = multiprocessing.Manager()
    res_input_queue = manager.Queue()
    res_output_queue = manager.Queue()

    graph_input_queue = manager.Queue()
    graph_output_queue = manager.Queue()

    graph_info = dict()

    logging.info('[main] ----------- 开始进行数据预处理 -----------')
    data, headers, headers_line = pre_process('./%s.csv' % FILENAME)
    res_num_of_input = res_input_queue.qsize()
    logging.info('[main] ----------- 数据预处理完成，需要处理的数据有%d -----------' % res_num_of_input)

    for key in data.keys():
        graph_input_queue.put(key)
    graph_num_of_input = graph_input_queue.qsize()

    logging.info('[main] ----------- 开始构建图并计算总体信息，需要处理的图有%d -----------' % graph_num_of_input)

    # generate_graphs(data, 1)

    pool = multiprocessing.Pool(NUM_WORKERS)
    for i in range(NUM_WORKERS):
        pool.apply_async(generate_graphs, args=(data, i + 1))
    pool.close()

    worker_count = 0
    finish_count = 0

    end_time_l = end_time_r = 0

    while 1:
        if not graph_output_queue.empty():
            end_time_l = datetime.datetime.now()
            con = graph_output_queue.get()
            if isinstance(con, int):
                worker_count += con
                if worker_count == NUM_WORKERS:
                    break
            elif isinstance(con, tuple):
                primary_key, res = con
                graph_info[primary_key] = res
                finish_count += 1
                logging.info('[main] %d/%d 已处理' % (finish_count, graph_num_of_input))
            else:
                raise TypeError('Unavailable Type!')
        else:
            if not end_time_l:
                end_time_l = datetime.datetime.now()
            else:
                end_time_r = datetime.datetime.now()
                if (end_time_r - end_time_l).seconds > 120:
                    break

    logging.info('[main] ----------- 所有图构建完成 -----------')

    del data
    del graph_input_queue
    del graph_output_queue

    logging.info('[main] ----------- 开始计算最终结果 -----------')

    # process(headers, res_input_queue, res_output_queue, 1)

    pool = multiprocessing.Pool(NUM_WORKERS)
    for i in range(NUM_WORKERS):
        pool.apply_async(process, args=(headers, graph_info, i + 1))
    pool.close()

    # if not caled_num:
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(headers_line[:-1] + SEP + SEP.join(OUTPUT_SEQ) + '\n')

    worker_count = 0
    finish_count = 0

    end_time_l = end_time_r = 0

    while 1:
        if not res_output_queue.empty():
            end_time_l = datetime.datetime.now()
            con = res_output_queue.get()
            if isinstance(con, int):
                worker_count += con
                if worker_count == NUM_WORKERS:
                    break
            elif isinstance(con, tuple):
                line, res = con
                with open(output_file, 'a', encoding='utf-8') as f:
                    f.write(SEP.join(line))
                    for key in OUTPUT_SEQ:
                        f.write(SEP + num2str(res.get(key)))
                    f.write('\n')
                finish_count += 1
                logging.info('[main] %d/%d 已处理' % (finish_count, res_num_of_input))
            else:
                raise TypeError('Unavailable Type!')
        else:
            if not end_time_l:
                end_time_l = datetime.datetime.now()
            else:
                end_time_r = datetime.datetime.now()
                if (end_time_r - end_time_l).seconds > 120:
                    break

    logging.info('[main] ----------- 最终结果计算完成 -----------')
