import multiprocessing
import logging
from utils import *

citations_file_name = 'sep_t_citations.csv'
patents_file_name = 'sep_t_inventing-patent_internal1_424-514.csv'

SEP = '\t'
NUM_WORKERS = 8

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[logging.FileHandler(filename='./root.log', encoding='utf-8', mode='w')],
)


def pre_process():
    with open(citations_file_name, 'r', encoding='-utf-8') as f:
        citations_headers = {v: i for i, v in enumerate(split_line(f.readline(), SEP))}
        while 1:
            line = f.readline()
            if not line:
                break
            else:
                line = split_line(line, SEP)
                cited = get_field('cited', line, citations_headers)
                citing = get_field('citing', line, citations_headers)
                citing_appyear = get_field('citing_appyear', line, citations_headers)
                citing_pdpass = get_field('citing_pdpass', line, citations_headers)

                citing_ob = {'citing': citing, 'citing_appyear': citing_appyear, 'citing_pdpass': citing_pdpass}
                if cited not in cite_relation:
                    cite_relation[cited] = []

                cite_relation[cited].append(citing_ob)


    with open(patents_file_name, 'r', encoding='utf-8') as f:
        patents_headers = {v: i for i, v in enumerate(split_line(f.readline(), SEP))}
        while 1:
            line = f.readline()
            if not line:
                break
            else:
                line = split_line(line, SEP)
                patent_internal1 = get_field('patent_internal1', line, patents_headers)
                w_begin1 = get_field('w_begin1', line, patents_headers)
                w_end1 = get_field('w_en.d1', line, patents_headers)

                input_queue.put((patent_internal1, w_begin1, w_end1))


def process(pid):
    while not input_queue.empty():
        patent_internal1, w_begin1, w_end1 = input_queue.get()
        input_queue.get()






if __name__ == '__main__':
    manager = multiprocessing.Manager()
    input_queue = manager.Queue()
    output_queue = manager.Queue()
    cite_relation = manager.dict()

