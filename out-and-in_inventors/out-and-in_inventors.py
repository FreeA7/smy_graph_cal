# -*- coding: utf-8 -*-
"""
Created on Sat Aug 13 12:37:23 2022

@author: FreeA7

out-and-in inventors
归去来兮
"""

from utils import split_line, get_field, clear_str
from collections import defaultdict
import re


data_file_name = './invpat_with-pdpass/original_data.csv'
primary_key = ['lower']
time_window = 3
year_field = 'appyearstr'
read_sep = ','
write_sep = '\t'


patent_of_man = defaultdict(lambda: defaultdict(set))

count = 0
with open(data_file_name, 'r') as f:
    headers = {v: i for i, v in enumerate(split_line(f.readline(), read_sep))}
    while 1:
        line = f.readline()
        if not line:
            break

        line = split_line(line, read_sep)
        inventor = '&'.join([clear_str(re.sub(r'-\d+', '', get_field(key, line, headers))) for key in primary_key])
        try:
            year = int(get_field(year_field, line, headers))
        except ValueError:
            continue
            print('\t'.join(line))
        pdpass = get_field('pdpass', line, headers)
        patent_of_man[inventor][year].add(pdpass)
        count += 1
        print(count)

count = 0
with open('./output.csv', 'w', encoding='utf-8') as f:
    f.write(write_sep.join(primary_key + ['ifornot', 'away_time', 'back_time', 'pdpass']) + '\n')
    for inventor in patent_of_man.keys():
        years = sorted(year_pdpass.keys())
        first_year = years[0]
        last_year = years[-1]
        ifornot = 0
        if last_year - first_year - 1 >= time_window:
            for year in range(first_year, last_year - time_window):
                the_year_pdpass = year_pdpass[year]
                if not year_pdpass:
                    continue
                for pdpass in the_year_pdpass:
                    pdpasses = set()
                    for year_gap in range(1, time_window + 1):
                        pdpasses |= year_pdpass[year + year_gap]
                    if pdpasses and pdpass not in pdpasses:
                        for back_year in range(year + time_window + 1, last_year + 1):
                            if pdpass in year_pdpass[back_year]:
                                ifornot = 1
                                f.write(write_sep.join(inventor.split('&') + ['1', str(year + 1), str(back_year), pdpass]) + '\n')
                                break
        # if not ifornot:
        #     f.write(write_sep.join(inventor.split('&') + ['0', '-1', '-1', '-1']) + '\n')
        count += 1
        print('%d : %s' % (count, inventor))







